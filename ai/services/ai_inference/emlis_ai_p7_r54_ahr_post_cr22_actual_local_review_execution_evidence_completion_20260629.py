# -*- coding: utf-8 -*-
"""Post-CR22 R54-AHR actual local-only review evidence completion helper.

EX00-EX18 intentionally create only a body-free Post-CR22 envelope:

* EX00 freezes the scope, no-touch, and non-promotion boundary for the
  Post-CR22 Actual Local-only Human Review Execution Evidence Completion line.
* EX01 intakes CR22 as support material and confirms that the current CR
  actual-review basis remains ``current_received_snapshot_264_85_258_171``.
* EX02 freezes the review session envelope and actual-source guard, so helper
  defaults / unit tests / synthetic rows cannot become actual review evidence.
* EX03 freezes local-only preflight, explicit allow, and packet request boundary
  as body-free refs only; it does not generate any body-full packet.
* EX04 intakes a local-only body-full packet generation receipt as body-free
  count / scan refs only; it does not generate or export packet body.
* EX05 freezes reviewer-person and selection-only form boundaries; it does not
  run actual human review or create review result rows.
* EX06 freezes the actual local-only human review execution protocol as
  body-free operational instructions; it does not run the review itself.
* EX07 intakes a body-free actual operation receipt when supplied and valid;
  it does not create selection/rating/question/disposal rows or complete evidence.
* EX08 checks that selection rows declare actual person local-only provenance
  before CR10-like intake; it does not sanitize rows or complete evidence.
* EX09 intakes supplied actual selection-only rows as sanitized body-free
  review result rows; it does not create rating/question/disposal rows or
  complete evidence.
* EX10 normalizes supplied sanitized rows into body-free rating rows and
  threshold summaries; it does not create question/disposal rows or complete
  evidence.
* EX11 classifies readfeel / execution / P5 / P4 blockers from body-free
  rating rows; it does not create question/disposal rows or complete evidence.
* EX12 normalizes body-free question need observation rows from actual
  sanitized/rating/blocker evidence; it does not create question text or start P8.
* EX13 guards rating-question consistency so weak ratings, blockers, or heavy
  observation cases cannot escape into P8 material; it does not complete evidence.
* EX14 intakes a supplied body-free disposal / purge receipt and verifies the
  local body-full packet lifecycle is closed; it does not create disposal body.
* EX15 performs final no-body-leak / no-question-text / no-touch validation
  across body-free artifacts; it does not complete evidence or start promotion.
* EX16 evaluates the actual review evidence complete predicate only when actual
  source, counts, disposal, consistency, and final no-leak validations are all
  present; it does not promote P5/P6/P8/R52/release.
* EX17 separates P5/P6/P8/R52 materials as candidate-only refs after evidence
  completion; it does not finalize or execute any downstream stage.
* EX18 freezes the body-free validation command matrix, result memo envelope,
  and manual next-decision hold; it does not run validations or auto-promote.

This module does not itself execute actual local human review, does not generate
or export body-full packets, does not create actual selection rows beyond EX09 sanitized intake, does not
create question text, does not create body-full disposal receipts, does not start
P8/R52/P6, does not finalize P5, does not complete P7, does not allow
release, and does not claim full backend/RN/real-device completion.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import P7_PHASE, P7_SOURCE_MODE, clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628 as cr


P7_R54_AHR_POST_CR22_EX00_SCOPE_NO_TOUCH_NON_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex00_scope_no_touch_non_promotion_boundary_freeze.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX01_CR22_SUPPORT_MATERIAL_INTAKE_CURRENT_CR_BASIS_CONFIRMATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex01_cr22_support_material_intake_current_cr_basis_confirmation.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_STEP: Final = (
    "R54-AHR-PostCR22_ActualLocalReviewExecutionEvidenceCompletion_20260629"
)
P7_R54_AHR_POST_CR22_SCOPE: Final = (
    "p7_r54_ahr_post_cr22_actual_local_only_human_review_execution_evidence_completion"
)
P7_R54_AHR_POST_CR22_POLICY_KIND: Final = (
    "r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_boundary"
)
P7_R54_AHR_POST_CR22_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postcr22_actual_local_review_session_20260629_"
    "current_received_264_85_258_171_v1"
)

P7_R54_AHR_POST_CR22_EX00_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX00_scope_no_touch_non_promotion_boundary_freeze"
)
P7_R54_AHR_POST_CR22_EX01_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX01_cr22_support_material_intake_current_cr_basis_confirmation"
)
P7_R54_AHR_POST_CR22_EX02_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX02_review_session_envelope_actual_source_guard_freeze"
)
P7_R54_AHR_POST_CR22_EX03_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX03_local_only_preflight_explicit_allow_packet_request_boundary"
)
P7_R54_AHR_POST_CR22_EX04_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX04_local_body_full_packet_generation_receipt_bodyfree_intake"
)
P7_R54_AHR_POST_CR22_EX05_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX05_reviewer_person_boundary_selection_only_form_freeze"
)
P7_R54_AHR_POST_CR22_EX06_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX06_actual_local_only_human_review_execution_protocol"
)
P7_R54_AHR_POST_CR22_EX07_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX07_actual_operation_receipt_intake"
)
P7_R54_AHR_POST_CR22_EX08_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX08_actual_selection_row_provenance_guard"
)
P7_R54_AHR_POST_CR22_EX09_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX09_sanitized_review_result_rows_intake"
)
P7_R54_AHR_POST_CR22_EX10_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX10_rating_row_normalization_threshold_summary"
)
P7_R54_AHR_POST_CR22_EX11_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX11_readfeel_execution_p5_p4_blocker_classification"
)
P7_R54_AHR_POST_CR22_EX12_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX12_question_need_observation_normalization"
)
P7_R54_AHR_POST_CR22_EX13_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX13_rating_question_consistency_guard"
)
P7_R54_AHR_POST_CR22_EX14_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX14_disposal_purge_receipt_intake"
)
P7_R54_AHR_POST_CR22_EX15_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX15_final_no_body_leak_no_question_text_no_touch_validation"
)
P7_R54_AHR_POST_CR22_EX16_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX16_actual_review_evidence_complete_predicate"
)
P7_R54_AHR_POST_CR22_EX17_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX17_p5_p6_p8_r52_candidate_only_separation"
)
P7_R54_AHR_POST_CR22_EX18_STEP_REF: Final = (
    "R54-AHR-PostCR22-EX18_validation_command_matrix_result_memo_next_decision_hold"
)

P7_R54_AHR_POST_CR22_EX_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
    P7_R54_AHR_POST_CR22_EX02_STEP_REF,
    P7_R54_AHR_POST_CR22_EX03_STEP_REF,
    P7_R54_AHR_POST_CR22_EX04_STEP_REF,
    P7_R54_AHR_POST_CR22_EX05_STEP_REF,
    P7_R54_AHR_POST_CR22_EX06_STEP_REF,
    P7_R54_AHR_POST_CR22_EX07_STEP_REF,
    P7_R54_AHR_POST_CR22_EX08_STEP_REF,
    P7_R54_AHR_POST_CR22_EX09_STEP_REF,
    P7_R54_AHR_POST_CR22_EX10_STEP_REF,
    P7_R54_AHR_POST_CR22_EX11_STEP_REF,
    P7_R54_AHR_POST_CR22_EX12_STEP_REF,
    P7_R54_AHR_POST_CR22_EX13_STEP_REF,
    P7_R54_AHR_POST_CR22_EX14_STEP_REF,
    P7_R54_AHR_POST_CR22_EX15_STEP_REF,
    P7_R54_AHR_POST_CR22_EX16_STEP_REF,
    P7_R54_AHR_POST_CR22_EX17_STEP_REF,
    P7_R54_AHR_POST_CR22_EX18_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[1:]
)
P7_R54_AHR_POST_CR22_EX01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[2:]
)

P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF: Final = cr.P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_REF
P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = (
    cr.P7_R54_AHR_CR_ACTUAL_REVIEW_BASIS_ALLOWED_REF
)
P7_R54_AHR_POST_CR22_CURRENT_CR_HELPER_REF: Final = (
    "ai/services/ai_inference/"
    "emlis_ai_p7_r54_ahr_current_received_snapshot_actual_local_review_operation_20260628.py"
)
P7_R54_AHR_POST_CR22_CR22_RESULT_MEMO_REF: Final = cr.P7_R54_AHR_CR22_DEFAULT_RESULT_MEMO_REF
P7_R54_AHR_POST_CR22_DETAILED_DESIGN_REF: Final = (
    "Cocolon_EmlisAI_P7_R54AHR_PostCR22_ActualLocalOnlyHumanReviewExecution_"
    "EvidenceCompletion_DetailedDesign_ImplementationOrder_20260629.md"
)
P7_R54_AHR_POST_CR22_PRE_DESIGN_MEMO_REF: Final = (
    "Cocolon_EmlisAI_P7_R54AHR_PostCR22_ActualLocalOnlyHumanReviewExecution_"
    "PreDesignMemo_20260629.md"
)

P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(266).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(86).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(5).zip",
    "rn_zip_ref": "Cocolon(259).zip",
    "backend_zip_ref": "mashos-api(172).zip",
}
P7_R54_AHR_POST_CR22_SUPPORT_MATERIAL_REFS: Final[dict[str, str]] = {
    "cr22_result_memo_ref": P7_R54_AHR_POST_CR22_CR22_RESULT_MEMO_REF,
    "current_cr_helper_ref": P7_R54_AHR_POST_CR22_CURRENT_CR_HELPER_REF,
    "detailed_design_ref": P7_R54_AHR_POST_CR22_DETAILED_DESIGN_REF,
    "pre_design_memo_ref": P7_R54_AHR_POST_CR22_PRE_DESIGN_MEMO_REF,
}
P7_R54_AHR_POST_CR22_CR22_RECORDED_VALIDATION_RESULTS: Final[dict[str, str]] = {
    "cr22_target_result_ref": "22_passed",
    "cr00_cr22_combined_result_ref": "837_passed",
    "cs00_cs18_selected_regression_result_ref": "450_passed",
    "cs00_cs01_ahr00_ahr01_smoke_result_ref": "102_passed",
    "compileall_result_ref": "passed",
}
P7_R54_AHR_POST_CR22_EX01_READY_STATUS_REF: Final = (
    "EX01_CR22_SUPPORT_MATERIAL_ACCEPTED_CURRENT_CR_BASIS_CONFIRMED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX01_BLOCKED_STATUS_REF: Final = (
    "EX01_CR22_SUPPORT_MATERIAL_OR_CURRENT_CR_BASIS_CONFIRMATION_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX01_READY_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX01_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX01_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex01_cr22_support_material_or_current_cr_basis_confirmation_or_stop"
)

P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "user_label_connection_runtime_changed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p8_question_api_created",
    "p8_question_db_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "actual_body_full_packet_generated_here",
    "body_full_packet_exported",
    "actual_human_review_newly_run_here",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_selection_rows_created_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_execution_allowed_here",
    "r52_reintake_execution_started_here",
    "r52_reintake_execution_completed_here",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "r52_actual_execution_confirmed",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_CR22_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "raw_body",
        "current_input_body",
        "returned_emlis_body",
        "history_surface",
        "comment_text",
        "comment_text_body",
        "reviewer_free_text",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "packet_content",
        "body_full_packet_content",
        "local_path",
        "local_absolute_path",
        "body_hash",
        "terminal_output_body",
        "stdout_body",
        "stderr_body",
        "traceback_body",
    }
)
P7_R54_AHR_POST_CR22_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_body_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "packet_content_included",
    "body_full_packet_content_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_POST_CR22_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "db_schema_changed",
    "db_write_path_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_changed",
    "user_label_connection_runtime_changed",
    "p8_question_api_created",
    "p8_question_db_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "r52_reintake_execution_started_here",
    "release_allowed",
)
P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "cr22_green_is_not_actual_human_review_complete",
    "helper_default_rows_are_not_actual_review_rows",
    "unit_test_rows_are_not_actual_review_rows",
    "synthetic_contract_rows_are_not_actual_review_rows",
    "outer_received_266_86_259_172_zip_labels_are_not_current_cr_basis_rewrite",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "r52_handoff_candidate_is_not_r52_actual_execution",
    "p5_confirmed_candidate_is_not_p5_final",
    "selected_regression_green_is_not_full_backend_suite_green",
    "rn_contract_green_is_not_rn_real_device_modal_verified",
)
P7_R54_AHR_POST_CR22_ALLOWED_CR22_COMMAND_ROW_KEY_REFS: Final[frozenset[str]] = frozenset(
    cr.P7_R54_AHR_CR22_COMMAND_ROW_REQUIRED_FIELD_REFS
)

P7_R54_AHR_POST_CR22_EX00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "postcr22_scope_confirmed",
    "no_touch_boundary_confirmed",
    "non_promotion_boundary_confirmed",
    "actual_local_review_execution_evidence_completion_selected",
    "ex00_does_not_intake_cr22_support_material",
    "ex00_does_not_confirm_current_cr_basis",
    "ex00_does_not_create_actual_source_guard",
    "ex00_does_not_generate_body_full_packet",
    "ex00_does_not_run_actual_human_review",
    "ex00_does_not_create_review_rows_rating_rows_question_rows_or_disposal",
    "p8_question_implementation_out_of_scope",
    "r52_actual_execution_out_of_scope",
    "p5_finalization_out_of_scope",
    "p6_start_out_of_scope",
    "p7_completion_out_of_scope",
    "release_decision_out_of_scope",
    "api_db_rn_runtime_public_contract_no_touch_boundary_frozen",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_CR22_EX01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex00_schema_version",
    "ex00_material_ref",
    "ex00_next_required_step",
    "ex00_postcr22_scope_confirmed",
    "ex00_no_touch_boundary_confirmed",
    "cr22_support_material_status_ref",
    "cr22_support_material_allowed_status_refs",
    "cr22_support_material_accepted",
    "cr22_support_material_step_blocker_refs",
    "cr22_support_material_step_blocker_ref_count",
    "support_material_refs",
    "support_material_ref_count",
    "cr22_result_memo_ref",
    "cr22_result_memo_ref_present",
    "current_cr_helper_ref",
    "current_cr_helper_ref_present",
    "cr22_required_command_refs",
    "cr22_required_command_ref_count",
    "cr22_required_pass_command_refs",
    "cr22_required_pass_command_ref_count",
    "cr22_required_not_claimed_command_refs",
    "cr22_required_not_claimed_command_ref_count",
    "cr22_validation_command_rows",
    "cr22_validation_command_row_count",
    "cr22_validation_command_refs",
    "cr22_validation_command_ref_count",
    "cr22_missing_required_command_refs",
    "cr22_missing_required_command_ref_count",
    "cr22_duplicate_command_refs",
    "cr22_duplicate_command_ref_count",
    "cr22_nonpassed_required_command_refs",
    "cr22_nonpassed_required_command_ref_count",
    "cr22_claimed_required_not_claimed_command_refs",
    "cr22_claimed_required_not_claimed_command_ref_count",
    "cr22_forbidden_command_row_refs",
    "cr22_forbidden_command_row_ref_count",
    "cr22_promotion_claim_command_refs",
    "cr22_promotion_claim_command_ref_count",
    "cr22_target_recorded_22_passed",
    "cr00_cr22_combined_recorded_837_passed",
    "cs00_cs18_selected_recorded_450_passed",
    "cs00_cs01_ahr00_ahr01_smoke_recorded_102_passed",
    "compileall_recorded_passed",
    "cr22_recorded_validation_results",
    "cr22_green_is_not_actual_review_complete",
    "cr22_green_is_not_actual_review_evidence_complete",
    "actual_human_review_newly_run_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_cr_actual_review_basis_ref",
    "current_cr_actual_review_basis_allowed_ref",
    "actual_basis_confirmed",
    "basis_rewrite_required_here",
    "basis_rewritten_here",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "outer_received_zip_label_difference_recorded_bodyfree",
    "current_cr_basis_remains_264_85_258_171",
    "full_backend_suite_green_unclaimed",
    "rn_contract_green_unclaimed_unless_actually_run",
    "rn_real_device_modal_verified_unclaimed",
    "p8_start_allowed",
    "r52_actual_execution_confirmed",
    "release_allowed",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_CR22_DEFAULT_REVIEW_SESSION_ID,
        max_length=180,
    )


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_CR22_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_CR22_NO_TOUCH_CONTRACT_REFS}


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS}


def _required_fields_present(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:8]}")
    unexpected = [key for key in data if key not in required]
    if unexpected:
        raise ValueError(f"{source} has unexpected fields: {unexpected[:8]}")


def _forbidden_payload_key_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_CR22_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _assert_no_payload_keys(data: Mapping[str, Any], *, source: str) -> None:
    paths = _forbidden_payload_key_paths(data, path=source)
    if paths:
        raise ValueError(f"{source} contains forbidden body/question/path/hash keys: {paths[:8]}")


def _assert_all_false(flags: Mapping[str, Any], *, source: str) -> None:
    true_keys = [str(key) for key, value in flags.items() if value is True]
    if true_keys:
        raise ValueError(f"{source} must keep all markers false: {true_keys[:8]}")


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str, allowed_true_flag_refs: tuple[str, ...] = ()
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_CR22_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_CR22_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_CR22_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != operation_step_ref or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} Git boundary changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    _assert_no_payload_keys(data, source=source)
    _assert_all_false(data.get("public_contract") or {}, source=f"{source}.public_contract")
    _assert_all_false(data.get("postcr22_no_touch_contract") or {}, source=f"{source}.no_touch_contract")
    _assert_all_false(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    allowed_true_flags = set(allowed_true_flag_refs)
    for key in P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
        if key in allowed_true_flags:
            continue
        if data.get(key) is not False:
            raise ValueError(f"{source} promoted forbidden flag: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis ref changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual review basis allowed ref changed")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError(f"{source} local received zip refs changed")
    if data.get("local_received_zip_ref_count") != len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS):
        raise ValueError(f"{source} local received zip ref count changed")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError(f"{source} local received zip refs must not become actual basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_cr_basis") is not False:
        raise ValueError(f"{source} must not rewrite current CR basis")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS:
        raise ValueError(f"{source} claim boundary refs changed")
    if data.get("claim_boundary_ref_count") != len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS):
        raise ValueError(f"{source} claim boundary ref count changed")


def _dedupe_refs(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = clean_identifier(value, max_length=220)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _duplicate_refs(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    dupes: list[str] = []
    for value in values:
        if value in seen and value not in dupes:
            dupes.append(value)
        seen.add(value)
    return dupes


def _clean_cr22_command_rows(rows: Sequence[Mapping[str, Any]] | None) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    raw_rows = list(rows) if rows is not None else cr.build_p7_r54_ahr_cr22_bodyfree_validation_command_rows_input()
    cleaned: list[dict[str, Any]] = []
    forbidden_row_refs: list[str] = []
    promotion_claim_refs: list[str] = []
    for index, row in enumerate(raw_rows):
        row_ref = f"cr22_command_row_{index + 1:02d}"
        if not isinstance(row, Mapping):
            forbidden_row_refs.append(f"{row_ref}_not_mapping")
            continue
        command_ref = clean_identifier(row.get("command_ref"), default=row_ref, max_length=160)
        extra_keys = sorted(str(key) for key in row.keys() if str(key) not in P7_R54_AHR_POST_CR22_ALLOWED_CR22_COMMAND_ROW_KEY_REFS)
        if extra_keys:
            forbidden_row_refs.append(command_ref)
        for flag_ref in (
            "raw_terminal_output_included",
            "terminal_output_body_included",
            "stdout_body_included",
            "stderr_body_included",
            "traceback_body_included",
            "local_absolute_path_included",
            "body_hash_included",
        ):
            if row.get(flag_ref) is True:
                forbidden_row_refs.append(command_ref)
        for claim_ref in (
            "actual_human_review_complete_claimed_by_command",
            "p5_final_claimed",
            "p6_start_claimed",
            "p8_start_claimed",
            "r52_actual_execution_claimed",
            "p7_complete_claimed",
            "release_allowed_claimed",
        ):
            if row.get(claim_ref) is True:
                promotion_claim_refs.append(command_ref)
        status_ref = clean_identifier(
            row.get("command_status_ref"),
            default=cr.P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
            max_length=160,
        )
        if status_ref not in cr.P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS:
            forbidden_row_refs.append(command_ref)
            status_ref = cr.P7_R54_AHR_CR22_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF
        cleaned.append(
            {
                "command_ref": command_ref,
                "command_kind_ref": clean_identifier(row.get("command_kind_ref"), default="unknown", max_length=120),
                "command_scope_ref": clean_identifier(row.get("command_scope_ref"), default="unknown", max_length=160),
                "command_display_ref": clean_identifier(row.get("command_display_ref"), default="bodyfree_command_ref", max_length=520),
                "command_status_ref": status_ref,
                "command_status_allowed_refs": list(cr.P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS),
                "passed": status_ref == cr.P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF,
                "ran_here": bool(row.get("ran_here")),
                "green_claimed": bool(row.get("green_claimed")),
                "full_backend_suite_green_claimed": bool(row.get("full_backend_suite_green_claimed")),
                "rn_contract_green_claimed": bool(row.get("rn_contract_green_claimed")),
                "rn_real_device_modal_claimed": bool(row.get("rn_real_device_modal_claimed")),
                "actual_human_review_complete_claimed_by_command": False,
                "p5_final_claimed": False,
                "p6_start_claimed": False,
                "p8_start_claimed": False,
                "r52_actual_execution_claimed": False,
                "p7_complete_claimed": False,
                "release_allowed_claimed": False,
                "raw_terminal_output_included": False,
                "terminal_output_body_included": False,
                "stdout_body_included": False,
                "stderr_body_included": False,
                "traceback_body_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "body_free": True,
            }
        )
    return cleaned, _dedupe_refs(forbidden_row_refs), _dedupe_refs(promotion_claim_refs)


def _cr22_support_blockers(
    command_rows: Sequence[Mapping[str, Any]] | None,
    *,
    result_memo_ref: Any,
    current_cr_helper_ref: Any,
) -> tuple[list[dict[str, Any]], list[str], dict[str, list[str]]]:
    rows, forbidden_row_refs, promotion_claim_refs = _clean_cr22_command_rows(command_rows)
    command_refs = [str(row["command_ref"]) for row in rows]
    duplicate_refs = _duplicate_refs(command_refs)
    missing_refs = [ref for ref in cr.P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS if ref not in command_refs]
    by_ref = {str(row["command_ref"]): row for row in rows}
    nonpassed_required_refs = [
        ref
        for ref in cr.P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS
        if by_ref.get(ref, {}).get("command_status_ref") != cr.P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
    ]
    claimed_required_not_claimed_refs = [
        ref
        for ref in cr.P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS
        if by_ref.get(ref, {}).get("command_status_ref") == cr.P7_R54_AHR_CR22_COMMAND_STATUS_PASSED_REF
        or by_ref.get(ref, {}).get("green_claimed") is True
        or by_ref.get(ref, {}).get("full_backend_suite_green_claimed") is True
        or by_ref.get(ref, {}).get("rn_contract_green_claimed") is True
        or by_ref.get(ref, {}).get("rn_real_device_modal_claimed") is True
    ]
    blocker_refs: list[str] = []
    if not clean_identifier(result_memo_ref, default=""):
        blocker_refs.append("ex01_cr22_result_memo_ref_missing")
    if not clean_identifier(current_cr_helper_ref, default=""):
        blocker_refs.append("ex01_current_cr_helper_ref_missing")
    if missing_refs:
        blocker_refs.append("ex01_cr22_required_validation_command_row_missing")
    if duplicate_refs:
        blocker_refs.append("ex01_cr22_validation_command_row_duplicate")
    if nonpassed_required_refs:
        blocker_refs.append("ex01_cr22_required_pass_command_not_passed")
    if claimed_required_not_claimed_refs:
        blocker_refs.append("ex01_cr22_required_not_claimed_command_claimed")
    if forbidden_row_refs:
        blocker_refs.append("ex01_cr22_command_matrix_forbidden_body_question_path_hash_key")
    if promotion_claim_refs:
        blocker_refs.append("ex01_cr22_command_matrix_promotion_claim_detected")
    detail = {
        "missing_refs": missing_refs,
        "duplicate_refs": duplicate_refs,
        "nonpassed_required_refs": nonpassed_required_refs,
        "claimed_required_not_claimed_refs": claimed_required_not_claimed_refs,
        "forbidden_row_refs": forbidden_row_refs,
        "promotion_claim_refs": promotion_claim_refs,
    }
    return rows, _dedupe_refs(blocker_refs), detail


def build_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build EX00 body-free scope / no-touch / non-promotion boundary material."""

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX00_SCOPE_NO_TOUCH_NON_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX00_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze_20260629",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "postcr22_scope_confirmed": True,
        "no_touch_boundary_confirmed": True,
        "non_promotion_boundary_confirmed": True,
        "actual_local_review_execution_evidence_completion_selected": True,
        "ex00_does_not_intake_cr22_support_material": True,
        "ex00_does_not_confirm_current_cr_basis": True,
        "ex00_does_not_create_actual_source_guard": True,
        "ex00_does_not_generate_body_full_packet": True,
        "ex00_does_not_run_actual_human_review": True,
        "ex00_does_not_create_review_rows_rating_rows_question_rows_or_disposal": True,
        "p8_question_implementation_out_of_scope": True,
        "r52_actual_execution_out_of_scope": True,
        "p5_finalization_out_of_scope": True,
        "p6_start_out_of_scope": True,
        "p7_completion_out_of_scope": True,
        "release_decision_out_of_scope": True,
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen": True,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_CR22_EX00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_CR22_EX00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_CR22_EX01_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX00 scope / no-touch / non-promotion boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX00_SCOPE_NO_TOUCH_NON_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX00_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX00 scope / no-touch / non-promotion boundary",
    )
    for key in (
        "postcr22_scope_confirmed",
        "no_touch_boundary_confirmed",
        "non_promotion_boundary_confirmed",
        "actual_local_review_execution_evidence_completion_selected",
        "ex00_does_not_intake_cr22_support_material",
        "ex00_does_not_confirm_current_cr_basis",
        "ex00_does_not_create_actual_source_guard",
        "ex00_does_not_generate_body_full_packet",
        "ex00_does_not_run_actual_human_review",
        "ex00_does_not_create_review_rows_rating_rows_question_rows_or_disposal",
        "p8_question_implementation_out_of_scope",
        "r52_actual_execution_out_of_scope",
        "p5_finalization_out_of_scope",
        "p6_start_out_of_scope",
        "p7_completion_out_of_scope",
        "release_decision_out_of_scope",
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX00 required true boundary changed: {key}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostCR22-EX00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostCR22-EX00 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX00 next required step changed")
    return True


def build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
    *,
    scope_no_touch_non_promotion_boundary: Mapping[str, Any] | None = None,
    cr22_validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    cr22_result_memo_ref: Any = P7_R54_AHR_POST_CR22_CR22_RESULT_MEMO_REF,
    current_cr_helper_ref: Any = P7_R54_AHR_POST_CR22_CURRENT_CR_HELPER_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX01 body-free CR22 support intake and current CR basis confirmation."""

    ex00 = dict(
        scope_no_touch_non_promotion_boundary
        or build_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze(
            review_session_id=review_session_id
        )
    )
    assert_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze_contract(ex00)
    rows, blockers, detail = _cr22_support_blockers(
        cr22_validation_command_rows,
        result_memo_ref=cr22_result_memo_ref,
        current_cr_helper_ref=current_cr_helper_ref,
    )
    actual_basis_confirmed = (
        P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF == "current_received_snapshot_264_85_258_171"
        and P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF
        == "current_received_snapshot_264_85_258_171_only"
    )
    if not actual_basis_confirmed:
        blockers.append("ex01_current_cr_actual_review_basis_not_confirmed")
    blockers = _dedupe_refs(blockers)
    accepted = not blockers
    result_memo = clean_identifier(cr22_result_memo_ref, default="", max_length=220)
    helper_ref = clean_identifier(current_cr_helper_ref, default="", max_length=220)
    material: dict[str, Any] = {
        "schema_version": (
            P7_R54_AHR_POST_CR22_EX01_CR22_SUPPORT_MATERIAL_INTAKE_CURRENT_CR_BASIS_CONFIRMATION_SCHEMA_VERSION
        ),
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX01_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_20260629",
        "review_session_id": _safe_review_session_id(review_session_id or ex00.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex00_schema_version": ex00["schema_version"],
        "ex00_material_ref": ex00["material_id"],
        "ex00_next_required_step": ex00["next_required_step"],
        "ex00_postcr22_scope_confirmed": ex00["postcr22_scope_confirmed"],
        "ex00_no_touch_boundary_confirmed": ex00["no_touch_boundary_confirmed"],
        "cr22_support_material_status_ref": (
            P7_R54_AHR_POST_CR22_EX01_READY_STATUS_REF
            if accepted
            else P7_R54_AHR_POST_CR22_EX01_BLOCKED_STATUS_REF
        ),
        "cr22_support_material_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX01_ALLOWED_STATUS_REFS),
        "cr22_support_material_accepted": accepted,
        "cr22_support_material_step_blocker_refs": blockers,
        "cr22_support_material_step_blocker_ref_count": len(blockers),
        "support_material_refs": dict(P7_R54_AHR_POST_CR22_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_CR22_SUPPORT_MATERIAL_REFS),
        "cr22_result_memo_ref": result_memo,
        "cr22_result_memo_ref_present": bool(result_memo),
        "current_cr_helper_ref": helper_ref,
        "current_cr_helper_ref_present": bool(helper_ref),
        "cr22_required_command_refs": list(cr.P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS),
        "cr22_required_command_ref_count": len(cr.P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS),
        "cr22_required_pass_command_refs": list(cr.P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS),
        "cr22_required_pass_command_ref_count": len(cr.P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS),
        "cr22_required_not_claimed_command_refs": list(cr.P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS),
        "cr22_required_not_claimed_command_ref_count": len(cr.P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS),
        "cr22_validation_command_rows": rows,
        "cr22_validation_command_row_count": len(rows),
        "cr22_validation_command_refs": [str(row["command_ref"]) for row in rows],
        "cr22_validation_command_ref_count": len(rows),
        "cr22_missing_required_command_refs": detail["missing_refs"],
        "cr22_missing_required_command_ref_count": len(detail["missing_refs"]),
        "cr22_duplicate_command_refs": detail["duplicate_refs"],
        "cr22_duplicate_command_ref_count": len(detail["duplicate_refs"]),
        "cr22_nonpassed_required_command_refs": detail["nonpassed_required_refs"],
        "cr22_nonpassed_required_command_ref_count": len(detail["nonpassed_required_refs"]),
        "cr22_claimed_required_not_claimed_command_refs": detail["claimed_required_not_claimed_refs"],
        "cr22_claimed_required_not_claimed_command_ref_count": len(detail["claimed_required_not_claimed_refs"]),
        "cr22_forbidden_command_row_refs": detail["forbidden_row_refs"],
        "cr22_forbidden_command_row_ref_count": len(detail["forbidden_row_refs"]),
        "cr22_promotion_claim_command_refs": detail["promotion_claim_refs"],
        "cr22_promotion_claim_command_ref_count": len(detail["promotion_claim_refs"]),
        "cr22_target_recorded_22_passed": True,
        "cr00_cr22_combined_recorded_837_passed": True,
        "cs00_cs18_selected_recorded_450_passed": True,
        "cs00_cs01_ahr00_ahr01_smoke_recorded_102_passed": True,
        "compileall_recorded_passed": True,
        "cr22_recorded_validation_results": dict(P7_R54_AHR_POST_CR22_CR22_RECORDED_VALIDATION_RESULTS),
        "cr22_green_is_not_actual_review_complete": True,
        "cr22_green_is_not_actual_review_evidence_complete": True,
        "actual_human_review_newly_run_here": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_cr_actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "current_cr_actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "actual_basis_confirmed": actual_basis_confirmed,
        "basis_rewrite_required_here": False,
        "basis_rewritten_here": False,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "outer_received_zip_label_difference_recorded_bodyfree": True,
        "current_cr_basis_remains_264_85_258_171": actual_basis_confirmed,
        "full_backend_suite_green_unclaimed": True,
        "rn_contract_green_unclaimed_unless_actually_run": True,
        "rn_real_device_modal_verified_unclaimed": True,
        "p8_start_allowed": False,
        "r52_actual_execution_confirmed": False,
        "release_allowed": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX01_IMPLEMENTED_STEPS
            if accepted
            else P7_R54_AHR_POST_CR22_EX00_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX01_NOT_YET_IMPLEMENTED_STEPS
            if accepted
            else P7_R54_AHR_POST_CR22_EX00_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_CR22_EX02_STEP_REF
            if accepted
            else P7_R54_AHR_POST_CR22_EX01_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX01 CR22 support / current CR basis confirmation",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=(
            P7_R54_AHR_POST_CR22_EX01_CR22_SUPPORT_MATERIAL_INTAKE_CURRENT_CR_BASIS_CONFIRMATION_SCHEMA_VERSION
        ),
        operation_step_ref=P7_R54_AHR_POST_CR22_EX01_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX01 CR22 support / current CR basis confirmation",
    )
    if data.get("ex00_schema_version") != P7_R54_AHR_POST_CR22_EX00_SCOPE_NO_TOUCH_NON_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 EX00 schema version changed")
    if data.get("ex00_next_required_step") != P7_R54_AHR_POST_CR22_EX01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 EX00 next step changed")
    if data.get("ex00_postcr22_scope_confirmed") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 EX00 scope confirmation missing")
    if data.get("ex00_no_touch_boundary_confirmed") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 EX00 no-touch confirmation missing")
    if tuple(data.get("cr22_support_material_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 allowed status refs changed")
    count_pairs = (
        ("support_material_refs", "support_material_ref_count"),
        ("cr22_required_command_refs", "cr22_required_command_ref_count"),
        ("cr22_required_pass_command_refs", "cr22_required_pass_command_ref_count"),
        ("cr22_required_not_claimed_command_refs", "cr22_required_not_claimed_command_ref_count"),
        ("cr22_validation_command_rows", "cr22_validation_command_row_count"),
        ("cr22_validation_command_refs", "cr22_validation_command_ref_count"),
        ("cr22_missing_required_command_refs", "cr22_missing_required_command_ref_count"),
        ("cr22_duplicate_command_refs", "cr22_duplicate_command_ref_count"),
        ("cr22_nonpassed_required_command_refs", "cr22_nonpassed_required_command_ref_count"),
        ("cr22_claimed_required_not_claimed_command_refs", "cr22_claimed_required_not_claimed_command_ref_count"),
        ("cr22_forbidden_command_row_refs", "cr22_forbidden_command_row_ref_count"),
        ("cr22_promotion_claim_command_refs", "cr22_promotion_claim_command_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("cr22_support_material_step_blocker_refs", "cr22_support_material_step_blocker_ref_count"),
    )
    for field, count_field in count_pairs:
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostCR22-EX01 {count_field} changed")
    if data.get("support_material_refs") != P7_R54_AHR_POST_CR22_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 support material refs changed")
    if data.get("cr22_result_memo_ref") != P7_R54_AHR_POST_CR22_CR22_RESULT_MEMO_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 CR22 result memo ref changed")
    if data.get("current_cr_helper_ref") != P7_R54_AHR_POST_CR22_CURRENT_CR_HELPER_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 current CR helper ref changed")
    if tuple(data.get("cr22_required_command_refs") or ()) != cr.P7_R54_AHR_CR22_REQUIRED_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 required CR22 command refs changed")
    if tuple(data.get("cr22_required_pass_command_refs") or ()) != cr.P7_R54_AHR_CR22_REQUIRED_PASS_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 required pass CR22 command refs changed")
    if tuple(data.get("cr22_required_not_claimed_command_refs") or ()) != cr.P7_R54_AHR_CR22_REQUIRED_NOT_CLAIMED_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 required not-claimed CR22 command refs changed")
    rows = data.get("cr22_validation_command_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("P7-R54-AHR-PostCR22-EX01 CR22 command rows must be a sequence")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-PostCR22-EX01 CR22 command row must be a mapping")
        if set(row.keys()) != set(cr.P7_R54_AHR_CR22_COMMAND_ROW_REQUIRED_FIELD_REFS):
            raise ValueError("P7-R54-AHR-PostCR22-EX01 CR22 command row fields changed")
        if tuple(row.get("command_status_allowed_refs") or ()) != cr.P7_R54_AHR_CR22_ALLOWED_COMMAND_STATUS_REFS:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 CR22 command row status refs changed")
        if row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 CR22 command row must stay body-free")
        for leak_flag in (
            "raw_terminal_output_included",
            "terminal_output_body_included",
            "stdout_body_included",
            "stderr_body_included",
            "traceback_body_included",
            "local_absolute_path_included",
            "body_hash_included",
        ):
            if row.get(leak_flag) is not False:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX01 CR22 row leak flag changed: {leak_flag}")
        for promotion_flag in (
            "actual_human_review_complete_claimed_by_command",
            "p5_final_claimed",
            "p6_start_claimed",
            "p8_start_claimed",
            "r52_actual_execution_claimed",
            "p7_complete_claimed",
            "release_allowed_claimed",
        ):
            if row.get(promotion_flag) is not False:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX01 CR22 row promotion flag changed: {promotion_flag}")
    blockers = list(data.get("cr22_support_material_step_blocker_refs") or [])
    accepted = blockers == []
    if data.get("cr22_support_material_accepted") is not accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 accepted predicate changed")
    if data.get("cr22_support_material_status_ref") != (
        P7_R54_AHR_POST_CR22_EX01_READY_STATUS_REF if accepted else P7_R54_AHR_POST_CR22_EX01_BLOCKED_STATUS_REF
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX01 status ref changed")
    for key in (
        "cr22_target_recorded_22_passed",
        "cr00_cr22_combined_recorded_837_passed",
        "cs00_cs18_selected_recorded_450_passed",
        "cs00_cs01_ahr00_ahr01_smoke_recorded_102_passed",
        "compileall_recorded_passed",
        "cr22_green_is_not_actual_review_complete",
        "cr22_green_is_not_actual_review_evidence_complete",
        "outer_received_zip_label_difference_recorded_bodyfree",
        "full_backend_suite_green_unclaimed",
        "rn_contract_green_unclaimed_unless_actually_run",
        "rn_real_device_modal_verified_unclaimed",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX01 required true field changed: {key}")
    if data.get("cr22_recorded_validation_results") != P7_R54_AHR_POST_CR22_CR22_RECORDED_VALIDATION_RESULTS:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 recorded validation results changed")
    if data.get("current_cr_actual_review_basis_ref") != P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 current CR basis ref changed")
    if data.get("current_cr_actual_review_basis_allowed_ref") != P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 current CR basis allowed ref changed")
    if data.get("actual_basis_confirmed") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 actual basis must be confirmed")
    if data.get("basis_rewrite_required_here") is not False or data.get("basis_rewritten_here") is not False:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 must not rewrite basis")
    if data.get("current_cr_basis_remains_264_85_258_171") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX01 current basis boundary changed")
    if accepted:
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX01_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX01_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 next step changed")
    else:
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX00_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX00_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX01_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX01 blocked next step changed")
    return True


# Alias names for the detailed-design wording.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_scope_no_touch_non_promotion_boundary_freeze_bodyfree(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze(
        review_session_id=review_session_id
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_scope_no_touch_non_promotion_boundary_freeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex00_scope_no_touch_non_promotion_boundary_freeze_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_cr22_support_material_intake_current_cr_basis_confirmation_bodyfree(
    *,
    scope_no_touch_non_promotion_boundary: Mapping[str, Any] | None = None,
    cr22_validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    cr22_result_memo_ref: Any = P7_R54_AHR_POST_CR22_CR22_RESULT_MEMO_REF,
    current_cr_helper_ref: Any = P7_R54_AHR_POST_CR22_CURRENT_CR_HELPER_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
        scope_no_touch_non_promotion_boundary=scope_no_touch_non_promotion_boundary,
        cr22_validation_command_rows=cr22_validation_command_rows,
        cr22_result_memo_ref=cr22_result_memo_ref,
        current_cr_helper_ref=current_cr_helper_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_cr22_support_material_intake_current_cr_basis_confirmation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(
        data
    )



# ---------------------------------------------------------------------------
# EX02-EX03 Post-CR22 body-free guard / preflight boundary
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX02_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex02_review_session_envelope_actual_source_guard_freeze.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX03_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex03_local_only_preflight_explicit_allow_packet_request_boundary.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
    P7_R54_AHR_POST_CR22_EX02_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[3:]
)
P7_R54_AHR_POST_CR22_EX03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
    P7_R54_AHR_POST_CR22_EX02_STEP_REF,
    P7_R54_AHR_POST_CR22_EX03_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[4:]
)

P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_NOT_STARTED_REF: Final = "NOT_STARTED"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PREFLIGHT_READY_REF: Final = "PREFLIGHT_READY"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PREFLIGHT_BLOCKED_REF: Final = "PREFLIGHT_BLOCKED"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PACKET_GENERATED_LOCAL_ONLY_REF: Final = (
    "PACKET_GENERATED_LOCAL_ONLY"
)
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_REVIEW_IN_PROGRESS_REF: Final = "REVIEW_IN_PROGRESS"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PAUSED_LOCAL_ONLY_REF: Final = "PAUSED_LOCAL_ONLY"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_ABORTED_BODY_PURGED_REF: Final = "ABORTED_BODY_PURGED"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_REVIEW_COMPLETED_SELECTION_ROWS_READY_REF: Final = (
    "REVIEW_COMPLETED_SELECTION_ROWS_READY"
)
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_ROWS_ACCEPTED_BODYFREE_REF: Final = "ROWS_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_DISPOSAL_VERIFIED_REF: Final = "DISPOSAL_VERIFIED"
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_EVIDENCE_COMPLETE_BODYFREE_REF: Final = (
    "EVIDENCE_COMPLETE_BODYFREE"
)
P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_EVIDENCE_BLOCKED_REF: Final = "EVIDENCE_BLOCKED"
P7_R54_AHR_POST_CR22_ALLOWED_REVIEW_SESSION_STATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_NOT_STARTED_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PREFLIGHT_BLOCKED_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PREFLIGHT_READY_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PACKET_GENERATED_LOCAL_ONLY_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_REVIEW_IN_PROGRESS_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PAUSED_LOCAL_ONLY_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_ABORTED_BODY_PURGED_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_REVIEW_COMPLETED_SELECTION_ROWS_READY_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_ROWS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_DISPOSAL_VERIFIED_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_EVIDENCE_COMPLETE_BODYFREE_REF,
    P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_EVIDENCE_BLOCKED_REF,
)
P7_R54_AHR_POST_CR22_ALLOWED_READY_SESSION_TRANSITION_REFS: Final[tuple[str, ...]] = (
    "NOT_STARTED_TO_PREFLIGHT_READY",
    "PREFLIGHT_READY_TO_PACKET_GENERATED_LOCAL_ONLY",
    "PACKET_GENERATED_LOCAL_ONLY_TO_REVIEW_IN_PROGRESS",
    "REVIEW_IN_PROGRESS_TO_REVIEW_COMPLETED_SELECTION_ROWS_READY",
    "REVIEW_COMPLETED_SELECTION_ROWS_READY_TO_ROWS_ACCEPTED_BODYFREE",
    "ROWS_ACCEPTED_BODYFREE_TO_DISPOSAL_VERIFIED",
    "DISPOSAL_VERIFIED_TO_EVIDENCE_COMPLETE_BODYFREE",
)
P7_R54_AHR_POST_CR22_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS: Final[tuple[str, ...]] = (
    "NOT_STARTED_TO_EVIDENCE_COMPLETE_BODYFREE",
    "PREFLIGHT_READY_TO_EVIDENCE_COMPLETE_BODYFREE",
    "PACKET_GENERATED_LOCAL_ONLY_TO_P8_START",
    "ROWS_ACCEPTED_BODYFREE_TO_R52_ACTUAL_EXECUTION",
    "EVIDENCE_COMPLETE_BODYFREE_TO_RELEASE_ALLOWED",
)

P7_R54_AHR_POST_CR22_EX02_GUARD_READY_STATUS_REF: Final = (
    "EX02_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_READY_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX02_GUARD_BLOCKED_STATUS_REF: Final = (
    "EX02_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX02_ALLOWED_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX02_GUARD_READY_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX02_GUARD_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX02_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex02_review_session_or_actual_source_guard_or_stop"
)

P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS: Final[tuple[str, ...]] = (
    "actual_person_local_only_review_operation_receipt",
    "actual_person_selection_only_rows_local_review",
    "actual_local_body_full_packet_generation_receipt_bodyfree",
    "actual_local_disposal_receipt_bodyfree",
)
P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS: Final[tuple[str, ...]] = (
    "helper_default_fixture_rows",
    "unit_test_contract_rows",
    "synthetic_bodyfree_rows",
    "historical_ahr_260_83_256_169_rows",
    "historical_cs_262_84_257_170_rows",
    "ai_inferred_review_rows",
    "rows_without_person_read_receipt",
)
P7_R54_AHR_POST_CR22_EX02_REQUIRED_SOURCE_GUARD_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "helper_default_rows_allowed_as_actual",
    "unit_test_rows_allowed_as_actual",
    "synthetic_rows_allowed_as_actual",
    "historical_rows_allowed_as_actual",
    "ai_inferred_rows_allowed_as_actual",
    "rows_without_person_read_receipt_allowed_as_actual",
    "helper_default_fixture_rows_allowed_as_actual",
    "unit_test_contract_rows_allowed_as_actual",
    "synthetic_bodyfree_rows_allowed_as_actual",
    "historical_ahr_rows_allowed_as_actual",
    "historical_cs_rows_allowed_as_actual",
    "actual_source_guard_materializes_actual_rows_here",
    "actual_source_guard_runs_actual_human_review_here",
)

P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_READY_STATUS_REF: Final = (
    "EX03_LOCAL_ONLY_PREFLIGHT_READY_PACKET_REQUEST_BODYFREE_REF_ONLY"
)
P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_BLOCKED_STATUS_REF: Final = (
    "EX03_LOCAL_ONLY_PREFLIGHT_BLOCKED_EXPLICIT_ALLOW_OR_POLICY_MISSING"
)
P7_R54_AHR_POST_CR22_EX03_ALLOWED_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_READY_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX03_READY_REASON_REF: Final = (
    "EX03_LOCAL_ONLY_EXPLICIT_ALLOW_RETENTION_DISPOSAL_EXPORT_DENYLIST_READY"
)
P7_R54_AHR_POST_CR22_EX03_ACTUAL_SOURCE_GUARD_NOT_READY_BLOCKER_REF: Final = "ex02_actual_source_guard_not_ready"
P7_R54_AHR_POST_CR22_EX03_LOCAL_ONLY_FALSE_BLOCKER_REF: Final = "local_only_not_confirmed"
P7_R54_AHR_POST_CR22_EX03_MUST_NOT_EXPORT_FALSE_BLOCKER_REF: Final = "must_not_export_not_confirmed"
P7_R54_AHR_POST_CR22_EX03_LOCAL_REVIEW_ROOT_MISSING_BLOCKER_REF: Final = "local_review_root_ref_missing"
P7_R54_AHR_POST_CR22_EX03_LOCAL_REVIEW_ROOT_PATH_SHAPE_BLOCKER_REF: Final = (
    "local_review_root_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX03_EXPLICIT_ALLOW_MISSING_BLOCKER_REF: Final = "explicit_allow_ref_missing"
P7_R54_AHR_POST_CR22_EX03_RETENTION_POLICY_MISSING_BLOCKER_REF: Final = "retention_policy_ref_missing"
P7_R54_AHR_POST_CR22_EX03_DISPOSAL_POLICY_MISSING_BLOCKER_REF: Final = "disposal_policy_ref_missing"
P7_R54_AHR_POST_CR22_EX03_EXPORT_DENYLIST_POLICY_MISSING_BLOCKER_REF: Final = (
    "export_denylist_policy_ref_missing"
)
P7_R54_AHR_POST_CR22_EX03_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF: Final = "body_full_packet_export_allowed"
P7_R54_AHR_POST_CR22_EX03_PACKET_REQUEST_REF_MISSING_BLOCKER_REF: Final = "packet_request_ref_missing"
P7_R54_AHR_POST_CR22_EX03_DEFAULT_LOCAL_REVIEW_ROOT_REF: Final = "POSTCR22_LOCAL_ONLY_REVIEW_ROOT_SANITIZED_REF"
P7_R54_AHR_POST_CR22_EX03_REJECTED_LOCAL_REVIEW_ROOT_PATH_SHAPE_REF: Final = (
    "POSTCR22_LOCAL_ONLY_REVIEW_ROOT_REJECTED_PATH_SHAPE_REF"
)
P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF: Final = (
    "R54_AHR_POSTCR22_CURRENT_RECEIVED_264_85_258_171_LOCAL_ONLY_REVIEW_ALLOWED"
)
P7_R54_AHR_POST_CR22_EX03_DEFAULT_RETENTION_POLICY_REF: Final = "local_body_full_packet_max_72h_or_shorter"
P7_R54_AHR_POST_CR22_EX03_DEFAULT_DISPOSAL_POLICY_REF: Final = (
    "body_full_packet_disposal_required_after_review_or_abort"
)
P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPORT_DENYLIST_POLICY_REF: Final = (
    "body_full_packet_never_exported_to_repo_docs_release_public_meta"
)
P7_R54_AHR_POST_CR22_EX03_DEFAULT_PACKET_REQUEST_REF: Final = (
    "R54_AHR_POSTCR22_CURRENT_RECEIVED_264_85_258_171_BODYFULL_PACKET_REQUEST_BODYFREE_REF"
)
P7_R54_AHR_POST_CR22_EX03_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex03_local_only_preflight_explicit_allow_packet_request_or_stop"
)

P7_R54_AHR_POST_CR22_EX02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex01_schema_version",
    "ex01_material_ref",
    "ex01_next_required_step",
    "ex01_cr22_support_material_accepted",
    "ex01_actual_basis_confirmed",
    "ex01_current_cr_basis_remains_264_85_258_171",
    "ex01_cr22_green_is_not_actual_review_complete",
    "ex01_cr22_green_is_not_actual_review_evidence_complete",
    "review_session_envelope_status_ref",
    "review_session_envelope_allowed_status_refs",
    "review_session_envelope_ready",
    "review_session_state_ref",
    "allowed_review_session_state_refs",
    "allowed_review_session_state_ref_count",
    "allowed_ready_session_transition_refs",
    "allowed_ready_session_transition_ref_count",
    "forbidden_session_promotion_transition_refs",
    "forbidden_session_promotion_transition_ref_count",
    "review_session_id_bodyfree_identifier",
    "review_session_id_has_local_path_shape",
    "review_session_id_has_question_or_body_text_shape",
    "review_session_envelope_bodyfree_only",
    "review_session_envelope_does_not_start_preflight",
    "review_session_envelope_does_not_generate_body_full_packet",
    "review_session_envelope_does_not_run_actual_human_review",
    "actual_source_guard_required",
    "actual_source_guard_status_ref",
    "actual_source_guard_allowed_status_refs",
    "actual_source_guard_ready",
    "actual_source_guard_step_blocker_refs",
    "actual_source_guard_step_blocker_ref_count",
    "allowed_actual_source_refs",
    "allowed_actual_source_ref_count",
    "forbidden_actual_source_refs",
    "forbidden_actual_source_ref_count",
    "actual_source_guard_blocks_helper_default_rows",
    "actual_source_guard_blocks_unit_test_rows",
    "actual_source_guard_blocks_synthetic_rows",
    "actual_source_guard_blocks_historical_rows",
    "actual_source_guard_blocks_ai_inferred_rows",
    "actual_source_guard_requires_person_read_receipt_later",
    "actual_source_guard_requires_operation_receipt_later",
    "actual_source_guard_requires_selection_rows_later",
    "actual_source_guard_requires_disposal_receipt_later",
    "actual_rows_source_guard_passed",
    "actual_rows_intaked_here",
    "current_cr_basis_remains_264_85_258_171",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_EX02_REQUIRED_SOURCE_GUARD_FALSE_FIELD_REFS,
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_CR22_EX03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex02_schema_version",
    "ex02_material_ref",
    "ex02_next_required_step",
    "ex02_review_session_envelope_ready",
    "ex02_actual_source_guard_ready",
    "ex02_actual_source_guard_required",
    "ex02_review_session_state_ref",
    "ex02_allowed_actual_source_refs",
    "ex02_forbidden_actual_source_refs",
    "local_only_preflight_status_ref",
    "local_only_preflight_allowed_status_refs",
    "local_only_preflight_ready",
    "local_only_preflight_reason_refs",
    "local_only_preflight_blocker_refs",
    "local_only_preflight_blocker_ref_count",
    "local_only",
    "must_not_export",
    "local_review_root_ref",
    "local_review_root_ref_present",
    "local_review_root_ref_is_bodyfree_ref",
    "local_review_root_ref_has_local_path_shape",
    "explicit_allow_ref",
    "explicit_allow_ref_present",
    "explicit_allow_ref_expected",
    "retention_policy_ref",
    "retention_policy_ref_present",
    "disposal_policy_ref",
    "disposal_policy_ref_present",
    "export_denylist_policy_ref",
    "export_denylist_policy_ref_present",
    "body_full_packet_export_allowed",
    "body_free_summary_export_allowed",
    "body_full_packet_request_boundary_ready",
    "body_full_packet_request_allowed_by_preflight",
    "body_full_packet_request_ref",
    "body_full_packet_request_ref_present",
    "body_full_packet_request_materialized_bodyfree_only",
    "body_full_packet_generation_started_here",
    "body_full_packet_generated_here",
    "body_full_packet_content_included",
    "body_full_packet_content_exported",
    "body_full_packet_never_export_to_repo_docs_release_public_meta",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "preflight_ready_all_policy_refs_present",
    "preflight_blocks_without_explicit_allow",
    "preflight_blocks_body_full_export",
    "packet_request_boundary_requires_ex02_guard_ready",
    "packet_request_boundary_does_not_generate_packet_body",
    "packet_request_boundary_does_not_materialize_local_packet",
    "packet_request_boundary_does_not_execute_actual_human_review",
    "packet_request_boundary_does_not_create_review_rows",
    "packet_request_boundary_does_not_create_disposal_receipt",
    "packet_request_boundary_keeps_request_ref_bodyfree",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _ref_has_local_path_shape(value: Any) -> bool:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return False
    text = str(value).strip()
    if not text:
        return False
    if text.startswith(("/", "~/", "./", "../", "\\\\")):
        return True
    if "\\" in text or "/" in text:
        return True
    if len(text) >= 3 and text[1] == ":" and text[2] in ("\\", "/"):
        return True
    return False


def _ex02_source_guard_blockers(ex01: Mapping[str, Any], *, review_session_id: Any) -> list[str]:
    blockers: list[str] = []
    if ex01.get("cr22_support_material_accepted") is not True:
        blockers.append("ex01_cr22_support_material_not_accepted")
    if ex01.get("actual_basis_confirmed") is not True:
        blockers.append("ex01_current_cr_actual_basis_not_confirmed")
    if ex01.get("current_cr_basis_remains_264_85_258_171") is not True:
        blockers.append("ex01_current_cr_basis_boundary_changed")
    if ex01.get("cr22_green_is_not_actual_review_complete") is not True:
        blockers.append("ex01_cr22_actual_review_claim_boundary_missing")
    if ex01.get("cr22_green_is_not_actual_review_evidence_complete") is not True:
        blockers.append("ex01_cr22_actual_review_evidence_claim_boundary_missing")
    if _ref_has_local_path_shape(review_session_id):
        blockers.append("review_session_id_has_local_path_shape")
    if not P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS:
        blockers.append("allowed_actual_source_refs_missing")
    if not P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS:
        blockers.append("forbidden_actual_source_refs_missing")
    if set(P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS).intersection(
        P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS
    ):
        blockers.append("allowed_and_forbidden_actual_source_refs_overlap")
    return _dedupe_refs(blockers)


def _ex03_preflight_packet_request_fields(
    *,
    actual_source_guard_ready: bool,
    local_only: bool,
    must_not_export: bool,
    local_review_root_ref: Any,
    explicit_allow_ref: Any,
    retention_policy_ref: Any,
    disposal_policy_ref: Any,
    export_denylist_policy_ref: Any,
    body_full_packet_export_allowed: bool,
    body_full_packet_request_ref: Any,
) -> dict[str, Any]:
    local_root_candidate = clean_identifier(local_review_root_ref, default="", max_length=180)
    local_root_candidate_has_path_shape = _ref_has_local_path_shape(local_root_candidate)
    local_root = (
        P7_R54_AHR_POST_CR22_EX03_REJECTED_LOCAL_REVIEW_ROOT_PATH_SHAPE_REF
        if local_root_candidate_has_path_shape
        else local_root_candidate
    )
    local_root_has_path_shape = (
        local_root_candidate_has_path_shape
        or local_root == P7_R54_AHR_POST_CR22_EX03_REJECTED_LOCAL_REVIEW_ROOT_PATH_SHAPE_REF
    )
    explicit_allow = clean_identifier(explicit_allow_ref, default="", max_length=220)
    retention = clean_identifier(retention_policy_ref, default="", max_length=220)
    disposal = clean_identifier(disposal_policy_ref, default="", max_length=220)
    export_denylist = clean_identifier(export_denylist_policy_ref, default="", max_length=260)
    request_ref_candidate = clean_identifier(body_full_packet_request_ref, default="", max_length=260)
    blockers: list[str] = []
    if not actual_source_guard_ready:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_ACTUAL_SOURCE_GUARD_NOT_READY_BLOCKER_REF)
    if not local_only:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_LOCAL_ONLY_FALSE_BLOCKER_REF)
    if not must_not_export:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_MUST_NOT_EXPORT_FALSE_BLOCKER_REF)
    if not local_root:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_LOCAL_REVIEW_ROOT_MISSING_BLOCKER_REF)
    if local_root_has_path_shape:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_LOCAL_REVIEW_ROOT_PATH_SHAPE_BLOCKER_REF)
    if not explicit_allow:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_EXPLICIT_ALLOW_MISSING_BLOCKER_REF)
    if not retention:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_RETENTION_POLICY_MISSING_BLOCKER_REF)
    if not disposal:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_DISPOSAL_POLICY_MISSING_BLOCKER_REF)
    if not export_denylist:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_EXPORT_DENYLIST_POLICY_MISSING_BLOCKER_REF)
    if body_full_packet_export_allowed:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_BODYFULL_EXPORT_ALLOWED_BLOCKER_REF)
    if not request_ref_candidate:
        blockers.append(P7_R54_AHR_POST_CR22_EX03_PACKET_REQUEST_REF_MISSING_BLOCKER_REF)
    blockers = _dedupe_refs(blockers)
    ready = not blockers
    request_ref = request_ref_candidate if ready else ""
    return {
        "local_only_preflight_status_ref": (
            P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_BLOCKED_STATUS_REF
        ),
        "local_only_preflight_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX03_ALLOWED_PREFLIGHT_STATUS_REFS),
        "local_only_preflight_ready": ready,
        "local_only_preflight_reason_refs": [P7_R54_AHR_POST_CR22_EX03_READY_REASON_REF] if ready else [],
        "local_only_preflight_blocker_refs": blockers,
        "local_only_preflight_blocker_ref_count": len(blockers),
        "local_only": bool(local_only),
        "must_not_export": bool(must_not_export),
        "local_review_root_ref": local_root,
        "local_review_root_ref_present": bool(local_root),
        "local_review_root_ref_is_bodyfree_ref": bool(local_root) and not local_root_has_path_shape,
        "local_review_root_ref_has_local_path_shape": local_root_has_path_shape,
        "explicit_allow_ref": explicit_allow,
        "explicit_allow_ref_present": bool(explicit_allow),
        "explicit_allow_ref_expected": P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF,
        "retention_policy_ref": retention,
        "retention_policy_ref_present": bool(retention),
        "disposal_policy_ref": disposal,
        "disposal_policy_ref_present": bool(disposal),
        "export_denylist_policy_ref": export_denylist,
        "export_denylist_policy_ref_present": bool(export_denylist),
        "body_full_packet_export_allowed": bool(body_full_packet_export_allowed),
        "body_free_summary_export_allowed": True,
        "body_full_packet_request_boundary_ready": ready,
        "body_full_packet_request_allowed_by_preflight": ready,
        "body_full_packet_request_ref": request_ref,
        "body_full_packet_request_ref_present": bool(request_ref),
        "body_full_packet_request_materialized_bodyfree_only": ready,
        "body_full_packet_generation_started_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_content_included": False,
        "body_full_packet_content_exported": False,
        "body_full_packet_never_export_to_repo_docs_release_public_meta": True,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "preflight_ready_all_policy_refs_present": ready,
        "preflight_blocks_without_explicit_allow": not bool(explicit_allow),
        "preflight_blocks_body_full_export": True,
        "packet_request_boundary_requires_ex02_guard_ready": True,
        "packet_request_boundary_does_not_generate_packet_body": True,
        "packet_request_boundary_does_not_materialize_local_packet": True,
        "packet_request_boundary_does_not_execute_actual_human_review": True,
        "packet_request_boundary_does_not_create_review_rows": True,
        "packet_request_boundary_does_not_create_disposal_receipt": True,
        "packet_request_boundary_keeps_request_ref_bodyfree": True,
    }


def build_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze(
    *,
    cr22_support_material_intake_current_cr_basis_confirmation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX02 body-free review session envelope and actual-source guard material."""

    ex01 = dict(
        cr22_support_material_intake_current_cr_basis_confirmation
        or build_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation(
            review_session_id=review_session_id
        )
    )
    assert_p7_r54_ahr_post_cr22_ex01_cr22_support_material_intake_current_cr_basis_confirmation_contract(ex01)
    session_id = _safe_review_session_id(review_session_id or ex01.get("review_session_id"))
    blockers = _ex02_source_guard_blockers(ex01, review_session_id=session_id)
    ready = not blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX02_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX02_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex01_schema_version": ex01["schema_version"],
        "ex01_material_ref": ex01["material_id"],
        "ex01_next_required_step": ex01["next_required_step"],
        "ex01_cr22_support_material_accepted": ex01["cr22_support_material_accepted"],
        "ex01_actual_basis_confirmed": ex01["actual_basis_confirmed"],
        "ex01_current_cr_basis_remains_264_85_258_171": ex01[
            "current_cr_basis_remains_264_85_258_171"
        ],
        "ex01_cr22_green_is_not_actual_review_complete": ex01["cr22_green_is_not_actual_review_complete"],
        "ex01_cr22_green_is_not_actual_review_evidence_complete": ex01[
            "cr22_green_is_not_actual_review_evidence_complete"
        ],
        "review_session_envelope_status_ref": (
            P7_R54_AHR_POST_CR22_EX02_GUARD_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX02_GUARD_BLOCKED_STATUS_REF
        ),
        "review_session_envelope_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX02_ALLOWED_GUARD_STATUS_REFS),
        "review_session_envelope_ready": ready,
        "review_session_state_ref": P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_NOT_STARTED_REF,
        "allowed_review_session_state_refs": list(P7_R54_AHR_POST_CR22_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "allowed_review_session_state_ref_count": len(P7_R54_AHR_POST_CR22_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "allowed_ready_session_transition_refs": list(P7_R54_AHR_POST_CR22_ALLOWED_READY_SESSION_TRANSITION_REFS),
        "allowed_ready_session_transition_ref_count": len(P7_R54_AHR_POST_CR22_ALLOWED_READY_SESSION_TRANSITION_REFS),
        "forbidden_session_promotion_transition_refs": list(
            P7_R54_AHR_POST_CR22_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS
        ),
        "forbidden_session_promotion_transition_ref_count": len(
            P7_R54_AHR_POST_CR22_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS
        ),
        "review_session_id_bodyfree_identifier": bool(session_id) and not _ref_has_local_path_shape(session_id),
        "review_session_id_has_local_path_shape": _ref_has_local_path_shape(session_id),
        "review_session_id_has_question_or_body_text_shape": False,
        "review_session_envelope_bodyfree_only": True,
        "review_session_envelope_does_not_start_preflight": True,
        "review_session_envelope_does_not_generate_body_full_packet": True,
        "review_session_envelope_does_not_run_actual_human_review": True,
        "actual_source_guard_required": True,
        "actual_source_guard_status_ref": (
            P7_R54_AHR_POST_CR22_EX02_GUARD_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX02_GUARD_BLOCKED_STATUS_REF
        ),
        "actual_source_guard_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX02_ALLOWED_GUARD_STATUS_REFS),
        "actual_source_guard_ready": ready,
        "actual_source_guard_step_blocker_refs": blockers,
        "actual_source_guard_step_blocker_ref_count": len(blockers),
        "allowed_actual_source_refs": list(P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS),
        "allowed_actual_source_ref_count": len(P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS),
        "forbidden_actual_source_refs": list(P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS),
        "forbidden_actual_source_ref_count": len(P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS),
        "actual_source_guard_blocks_helper_default_rows": True,
        "actual_source_guard_blocks_unit_test_rows": True,
        "actual_source_guard_blocks_synthetic_rows": True,
        "actual_source_guard_blocks_historical_rows": True,
        "actual_source_guard_blocks_ai_inferred_rows": True,
        "actual_source_guard_requires_person_read_receipt_later": True,
        "actual_source_guard_requires_operation_receipt_later": True,
        "actual_source_guard_requires_selection_rows_later": True,
        "actual_source_guard_requires_disposal_receipt_later": True,
        "actual_rows_source_guard_passed": False,
        "actual_rows_intaked_here": False,
        "current_cr_basis_remains_264_85_258_171": ex01["current_cr_basis_remains_264_85_258_171"],
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX02_IMPLEMENTED_STEPS
            if ready
            else tuple(ex01.get("implemented_steps") or P7_R54_AHR_POST_CR22_EX01_IMPLEMENTED_STEPS)
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX02_NOT_YET_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_CR22_EX01_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_CR22_EX03_STEP_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX02_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **{key: False for key in P7_R54_AHR_POST_CR22_EX02_REQUIRED_SOURCE_GUARD_FALSE_FIELD_REFS},
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX02_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX02 review session envelope / actual source guard",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX02_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX02_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX02 review session envelope / actual source guard",
    )
    if data.get("ex01_schema_version") != (
        P7_R54_AHR_POST_CR22_EX01_CR22_SUPPORT_MATERIAL_INTAKE_CURRENT_CR_BASIS_CONFIRMATION_SCHEMA_VERSION
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 EX01 schema version changed")
    if data.get("ex01_next_required_step") != P7_R54_AHR_POST_CR22_EX02_STEP_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 must follow accepted EX01")
    if data.get("ex01_cr22_support_material_accepted") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 requires EX01 support accepted")
    if data.get("ex01_actual_basis_confirmed") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 requires EX01 basis confirmed")
    if data.get("ex01_current_cr_basis_remains_264_85_258_171") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 requires current CR basis boundary")
    for key in (
        "ex01_cr22_green_is_not_actual_review_complete",
        "ex01_cr22_green_is_not_actual_review_evidence_complete",
        "review_session_envelope_bodyfree_only",
        "review_session_envelope_does_not_start_preflight",
        "review_session_envelope_does_not_generate_body_full_packet",
        "review_session_envelope_does_not_run_actual_human_review",
        "actual_source_guard_required",
        "actual_source_guard_blocks_helper_default_rows",
        "actual_source_guard_blocks_unit_test_rows",
        "actual_source_guard_blocks_synthetic_rows",
        "actual_source_guard_blocks_historical_rows",
        "actual_source_guard_blocks_ai_inferred_rows",
        "actual_source_guard_requires_person_read_receipt_later",
        "actual_source_guard_requires_operation_receipt_later",
        "actual_source_guard_requires_selection_rows_later",
        "actual_source_guard_requires_disposal_receipt_later",
        "current_cr_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX02 required true field changed: {key}")
    if data.get("review_session_id_bodyfree_identifier") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 review session id must remain body-free")
    if data.get("review_session_id_has_local_path_shape") is not False:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 review session id must not contain path shape")
    if data.get("review_session_id_has_question_or_body_text_shape") is not False:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 review session id must not carry body/question text")
    if tuple(data.get("allowed_review_session_state_refs") or ()) != P7_R54_AHR_POST_CR22_ALLOWED_REVIEW_SESSION_STATE_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 session state refs changed")
    if data.get("allowed_review_session_state_ref_count") != len(P7_R54_AHR_POST_CR22_ALLOWED_REVIEW_SESSION_STATE_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 session state count changed")
    if tuple(data.get("allowed_ready_session_transition_refs") or ()) != P7_R54_AHR_POST_CR22_ALLOWED_READY_SESSION_TRANSITION_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 ready transition refs changed")
    if data.get("allowed_ready_session_transition_ref_count") != len(P7_R54_AHR_POST_CR22_ALLOWED_READY_SESSION_TRANSITION_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 ready transition count changed")
    if tuple(data.get("forbidden_session_promotion_transition_refs") or ()) != (
        P7_R54_AHR_POST_CR22_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 forbidden transition refs changed")
    if data.get("forbidden_session_promotion_transition_ref_count") != len(
        P7_R54_AHR_POST_CR22_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 forbidden transition count changed")
    if tuple(data.get("review_session_envelope_allowed_status_refs") or ()) != (
        P7_R54_AHR_POST_CR22_EX02_ALLOWED_GUARD_STATUS_REFS
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 envelope status refs changed")
    if tuple(data.get("actual_source_guard_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX02_ALLOWED_GUARD_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 guard status refs changed")
    blockers = list(data.get("actual_source_guard_step_blocker_refs") or [])
    ready = not blockers
    if data.get("actual_source_guard_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 guard blocker count changed")
    if data.get("review_session_envelope_ready") is not ready or data.get("actual_source_guard_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 ready flags changed")
    expected_status = (
        P7_R54_AHR_POST_CR22_EX02_GUARD_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX02_GUARD_BLOCKED_STATUS_REF
    )
    if data.get("review_session_envelope_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 envelope status changed")
    if data.get("actual_source_guard_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 guard status changed")
    if tuple(data.get("allowed_actual_source_refs") or ()) != P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 allowed actual source refs changed")
    if data.get("allowed_actual_source_ref_count") != len(P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 allowed actual source count changed")
    if tuple(data.get("forbidden_actual_source_refs") or ()) != P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 forbidden actual source refs changed")
    if data.get("forbidden_actual_source_ref_count") != len(P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 forbidden actual source count changed")
    if set(data.get("allowed_actual_source_refs") or []).intersection(data.get("forbidden_actual_source_refs") or []):
        raise ValueError("P7-R54-AHR-PostCR22-EX02 allowed/forbidden actual source overlap")
    for key in P7_R54_AHR_POST_CR22_EX02_REQUIRED_SOURCE_GUARD_FALSE_FIELD_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX02 source guard false field promoted: {key}")
    if data.get("actual_rows_source_guard_passed") is not False or data.get("actual_rows_intaked_here") is not False:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 must not intake actual rows")
    if data.get("review_session_state_ref") != P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_NOT_STARTED_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX02 must leave review session not started")
    if ready:
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX02_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX02 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX02_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX02 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX02 next step changed")
    else:
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX02_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX02 blocked next step changed")
    return True


def build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
    *,
    review_session_envelope_actual_source_guard: Mapping[str, Any] | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    local_review_root_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_LOCAL_REVIEW_ROOT_REF,
    explicit_allow_ref: Any = "",
    retention_policy_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_RETENTION_POLICY_REF,
    disposal_policy_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_DISPOSAL_POLICY_REF,
    export_denylist_policy_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPORT_DENYLIST_POLICY_REF,
    body_full_packet_export_allowed: bool = False,
    body_full_packet_request_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_PACKET_REQUEST_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX03 body-free local-only preflight and packet request boundary material."""

    ex02 = dict(
        review_session_envelope_actual_source_guard
        or build_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze(
            review_session_id=review_session_id
        )
    )
    assert_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_contract(ex02)
    preflight_fields = _ex03_preflight_packet_request_fields(
        actual_source_guard_ready=ex02.get("actual_source_guard_ready") is True,
        local_only=local_only,
        must_not_export=must_not_export,
        local_review_root_ref=local_review_root_ref,
        explicit_allow_ref=explicit_allow_ref,
        retention_policy_ref=retention_policy_ref,
        disposal_policy_ref=disposal_policy_ref,
        export_denylist_policy_ref=export_denylist_policy_ref,
        body_full_packet_export_allowed=body_full_packet_export_allowed,
        body_full_packet_request_ref=body_full_packet_request_ref,
    )
    ready = preflight_fields["local_only_preflight_ready"] is True
    material: dict[str, Any] = {
        "schema_version": (
            P7_R54_AHR_POST_CR22_EX03_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION
        ),
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX03_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_20260629",
        "review_session_id": _safe_review_session_id(review_session_id or ex02.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex02_schema_version": ex02["schema_version"],
        "ex02_material_ref": ex02["material_id"],
        "ex02_next_required_step": ex02["next_required_step"],
        "ex02_review_session_envelope_ready": ex02["review_session_envelope_ready"],
        "ex02_actual_source_guard_ready": ex02["actual_source_guard_ready"],
        "ex02_actual_source_guard_required": ex02["actual_source_guard_required"],
        "ex02_review_session_state_ref": ex02["review_session_state_ref"],
        "ex02_allowed_actual_source_refs": list(ex02["allowed_actual_source_refs"]),
        "ex02_forbidden_actual_source_refs": list(ex02["forbidden_actual_source_refs"]),
        **preflight_fields,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX03_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_CR22_EX02_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX03_NOT_YET_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_CR22_EX02_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_CR22_EX04_STEP_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX03_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX03_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX03 local-only preflight / packet request boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX03_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX03_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX03 local-only preflight / packet request boundary",
    )
    if data.get("ex02_schema_version") != (
        P7_R54_AHR_POST_CR22_EX02_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX03 EX02 schema version changed")
    if data.get("ex02_next_required_step") != P7_R54_AHR_POST_CR22_EX03_STEP_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 must follow ready EX02")
    if data.get("ex02_review_session_envelope_ready") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 requires ready review session envelope")
    if data.get("ex02_actual_source_guard_ready") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 requires ready actual source guard")
    if data.get("ex02_actual_source_guard_required") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 requires actual source guard")
    if data.get("ex02_review_session_state_ref") != P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_NOT_STARTED_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 must start from not-started session state")
    if tuple(data.get("ex02_allowed_actual_source_refs") or ()) != P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 EX02 allowed source refs changed")
    if tuple(data.get("ex02_forbidden_actual_source_refs") or ()) != P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 EX02 forbidden source refs changed")
    expected = _ex03_preflight_packet_request_fields(
        actual_source_guard_ready=data.get("ex02_actual_source_guard_ready") is True,
        local_only=bool(data.get("local_only")),
        must_not_export=bool(data.get("must_not_export")),
        local_review_root_ref=data.get("local_review_root_ref"),
        explicit_allow_ref=data.get("explicit_allow_ref"),
        retention_policy_ref=data.get("retention_policy_ref"),
        disposal_policy_ref=data.get("disposal_policy_ref"),
        export_denylist_policy_ref=data.get("export_denylist_policy_ref"),
        body_full_packet_export_allowed=bool(data.get("body_full_packet_export_allowed")),
        body_full_packet_request_ref=(
            data.get("body_full_packet_request_ref") or P7_R54_AHR_POST_CR22_EX03_DEFAULT_PACKET_REQUEST_REF
        ),
    )
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX03 {key} changed")
    blockers = list(data.get("local_only_preflight_blocker_refs") or [])
    ready = not blockers
    if data.get("local_only_preflight_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX03 blocker count changed")
    if data.get("local_only_preflight_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 ready flag changed")
    if data.get("body_full_packet_request_boundary_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 packet request ready flag changed")
    if tuple(data.get("local_only_preflight_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX03_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 allowed preflight status refs changed")
    expected_status = (
        P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_BLOCKED_STATUS_REF
    )
    if data.get("local_only_preflight_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX03 preflight status changed")
    if ready:
        if data.get("local_only_preflight_reason_refs") != [P7_R54_AHR_POST_CR22_EX03_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 ready reason changed")
        if data.get("body_full_packet_request_ref_present") is not True:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 ready boundary requires packet request ref")
        if data.get("body_full_packet_request_allowed_by_preflight") is not True:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 ready boundary must allow later packet request")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX03_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX03_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 blocked material requires blockers")
        if data.get("local_only_preflight_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 blocked material cannot carry ready reasons")
        if data.get("body_full_packet_request_ref_present") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 blocked material cannot carry request ref")
        if data.get("body_full_packet_request_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 blocked material cannot allow packet request")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX02_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX02_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX03_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX03 blocked next step changed")
    for key in (
        "body_free_summary_export_allowed",
        "body_full_packet_never_export_to_repo_docs_release_public_meta",
        "preflight_blocks_body_full_export",
        "packet_request_boundary_requires_ex02_guard_ready",
        "packet_request_boundary_does_not_generate_packet_body",
        "packet_request_boundary_does_not_materialize_local_packet",
        "packet_request_boundary_does_not_execute_actual_human_review",
        "packet_request_boundary_does_not_create_review_rows",
        "packet_request_boundary_does_not_create_disposal_receipt",
        "packet_request_boundary_keeps_request_ref_bodyfree",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "current_cr_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX03 required true field changed: {key}")
    for key in (
        "body_full_packet_generation_started_here",
        "body_full_packet_generated_here",
        "body_full_packet_content_included",
        "body_full_packet_content_exported",
        "local_absolute_path_included",
        "body_hash_included",
        "terminal_output_body_included",
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "actual_review_evidence_complete",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX03 required false field changed: {key}")
    return True


# Alias names for the detailed-design wording of EX02 and EX03.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_review_session_envelope_actual_source_guard_freeze_bodyfree(
    *,
    cr22_support_material_intake_current_cr_basis_confirmation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze(
        cr22_support_material_intake_current_cr_basis_confirmation=(
            cr22_support_material_intake_current_cr_basis_confirmation
        ),
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_review_session_envelope_actual_source_guard_freeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_only_preflight_explicit_allow_packet_request_boundary_bodyfree(
    *,
    review_session_envelope_actual_source_guard: Mapping[str, Any] | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    local_review_root_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_LOCAL_REVIEW_ROOT_REF,
    explicit_allow_ref: Any = "",
    retention_policy_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_RETENTION_POLICY_REF,
    disposal_policy_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_DISPOSAL_POLICY_REF,
    export_denylist_policy_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPORT_DENYLIST_POLICY_REF,
    body_full_packet_export_allowed: bool = False,
    body_full_packet_request_ref: Any = P7_R54_AHR_POST_CR22_EX03_DEFAULT_PACKET_REQUEST_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=review_session_envelope_actual_source_guard,
        local_only=local_only,
        must_not_export=must_not_export,
        local_review_root_ref=local_review_root_ref,
        explicit_allow_ref=explicit_allow_ref,
        retention_policy_ref=retention_policy_ref,
        disposal_policy_ref=disposal_policy_ref,
        export_denylist_policy_ref=export_denylist_policy_ref,
        body_full_packet_export_allowed=body_full_packet_export_allowed,
        body_full_packet_request_ref=body_full_packet_request_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_only_preflight_explicit_allow_packet_request_boundary_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(
        data
    )


# ---------------------------------------------------------------------------
# EX04-EX05 Post-CR22 body-free packet receipt / reviewer form boundary
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX04_LOCAL_BODY_FULL_PACKET_GENERATION_RECEIPT_COMPLETENESS_EXPORT_DENYLIST_BODYFREE_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX05_REVIEWER_PERSON_BOUNDARY_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex05_reviewer_person_boundary_selection_only_form_freeze.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
    P7_R54_AHR_POST_CR22_EX02_STEP_REF,
    P7_R54_AHR_POST_CR22_EX03_STEP_REF,
    P7_R54_AHR_POST_CR22_EX04_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[5:]
)
P7_R54_AHR_POST_CR22_EX05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
    P7_R54_AHR_POST_CR22_EX02_STEP_REF,
    P7_R54_AHR_POST_CR22_EX03_STEP_REF,
    P7_R54_AHR_POST_CR22_EX04_STEP_REF,
    P7_R54_AHR_POST_CR22_EX05_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[6:]
)

P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_ACCEPTED_STATUS_REF: Final = (
    "EX04_LOCAL_PACKET_GENERATION_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_BLOCKED_STATUS_REF: Final = (
    "EX04_LOCAL_PACKET_GENERATION_RECEIPT_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX04_ALLOWED_PACKET_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_ACCEPTED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX04_READY_REASON_REF: Final = (
    "EX04_LOCAL_ONLY_PACKET_GENERATION_RECEIPT_COUNT_SCAN_EXPORT_DENYLIST_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX04_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex04_packet_generation_receipt_completeness_export_denylist_or_stop"
)
P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_GENERATION_RECEIPT_REF: Final = (
    "postcr22_local_body_full_packet_generation_receipt_ref_20260629_001_bodyfree"
)
P7_R54_AHR_POST_CR22_EX04_DEFAULT_PACKET_COMPLETENESS_SCAN_REF: Final = (
    "postcr22_packet_completeness_scan_ref_20260629_001_bodyfree"
)
P7_R54_AHR_POST_CR22_EX04_DEFAULT_EXPORT_DENYLIST_SCAN_REF: Final = (
    "postcr22_export_denylist_scan_ref_20260629_001_bodyfree"
)
P7_R54_AHR_POST_CR22_EX04_REJECTED_RECEIPT_PATH_SHAPE_REF: Final = (
    "POSTCR22_PACKET_GENERATION_RECEIPT_REJECTED_PATH_SHAPE_REF"
)
P7_R54_AHR_POST_CR22_EX04_REJECTED_SCAN_PATH_SHAPE_REF: Final = (
    "POSTCR22_PACKET_SCAN_REJECTED_PATH_SHAPE_REF"
)
P7_R54_AHR_POST_CR22_EX04_ALLOWED_ACTUAL_SOURCE_REF: Final = (
    "actual_local_body_full_packet_generation_receipt_bodyfree"
)
P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT: Final = cr.P7_R54_AHR_CR_REQUIRED_CASE_COUNT

P7_R54_AHR_POST_CR22_EX04_BLOCKER_EX03_PREFLIGHT_NOT_READY_REF: Final = "ex03_local_only_preflight_not_ready"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_PACKET_REQUEST_MISSING_REF: Final = "ex03_packet_request_ref_missing"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_RECEIPT_REF_MISSING_REF: Final = "packet_generation_receipt_ref_missing"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_RECEIPT_REF_PATH_SHAPE_REF: Final = (
    "packet_generation_receipt_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX04_BLOCKER_ACTUAL_SOURCE_REF_NOT_ALLOWED_REF: Final = (
    "packet_generation_receipt_actual_source_ref_not_allowed"
)
P7_R54_AHR_POST_CR22_EX04_BLOCKER_PACKET_COUNT_NOT_24_REF: Final = "packet_case_count_not_24"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_COMPLETENESS_SCAN_MISSING_REF: Final = "packet_completeness_scan_ref_missing"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_COMPLETENESS_SCAN_PATH_SHAPE_REF: Final = (
    "packet_completeness_scan_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX04_BLOCKER_EXPORT_DENYLIST_SCAN_MISSING_REF: Final = "export_denylist_scan_ref_missing"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_EXPORT_DENYLIST_SCAN_PATH_SHAPE_REF: Final = (
    "export_denylist_scan_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX04_BLOCKER_COMPLETENESS_SCAN_NOT_PASSED_REF: Final = "packet_completeness_scan_not_passed"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_EXPORT_DENYLIST_SCAN_NOT_PASSED_REF: Final = "export_denylist_scan_not_passed"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_PACKET_BODY_EXPORTED_REF: Final = "packet_body_exported"
P7_R54_AHR_POST_CR22_EX04_BLOCKER_FORBIDDEN_BODY_PATH_HASH_REF: Final = (
    "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_flag"
)

P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_READY_STATUS_REF: Final = (
    "EX05_REVIEWER_PERSON_SELECTION_ONLY_FORM_READY_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_BLOCKED_STATUS_REF: Final = (
    "EX05_REVIEWER_PERSON_SELECTION_ONLY_FORM_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX05_ALLOWED_REVIEWER_BOUNDARY_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_READY_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX05_READY_REASON_REF: Final = (
    "EX05_PERSON_REVIEWER_SELECTION_ONLY_FORM_FROZEN_WITHOUT_FREE_TEXT_OR_QUESTION_TEXT"
)
P7_R54_AHR_POST_CR22_EX05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex05_reviewer_person_boundary_or_selection_only_form_or_stop"
)
P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF: Final = "local_person_reviewer_ref_001_bodyfree"
P7_R54_AHR_POST_CR22_EX05_REJECTED_REVIEWER_PERSON_PATH_SHAPE_REF: Final = (
    "POSTCR22_REVIEWER_PERSON_REF_REJECTED_PATH_SHAPE_REF"
)

P7_R54_AHR_POST_CR22_EX05_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = (
    "PASS",
    "YELLOW",
    "REPAIR_REQUIRED",
    "RED",
    "BLOCKED",
    "NOT_REVIEWABLE",
)
P7_R54_AHR_POST_CR22_EX05_SANITIZED_REASON_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "record_returned_as_natural_line",
    "history_line_weak_or_generic",
    "history_line_overread_or_creepy",
    "current_input_overridden_by_history",
    "boundary_history_correctly_not_used",
    "low_information_correctly_not_deep_read",
    "free_tier_history_correctly_not_used",
    "question_may_reduce_overread_risk_later",
    "p5_surface_repair_required",
    "p4_current_surface_repair_required",
    "execution_blocker_present",
)
P7_R54_AHR_POST_CR22_EX05_READFEEL_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "history_connection_weak",
    "history_line_creepy_or_overread",
    "current_input_overridden_by_history",
    "overclaim_or_unearned_certainty",
    "self_blame_amplified",
    "shallow_repeat_or_generic",
    "wants_less_input_or_no_accumulation",
    "boundary_history_line_leak",
)
P7_R54_AHR_POST_CR22_EX05_EXECUTION_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "packet_missing",
    "packet_not_local_only",
    "case_manifest_incomplete",
    "reviewer_selection_incomplete",
    "forbidden_body_leak",
    "question_text_leak",
    "disposal_missing",
    "no_touch_violation",
)
P7_R54_AHR_POST_CR22_EX05_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = (
    "no_material_ambiguity",
    "missing_target",
    "missing_time_scope",
    "missing_emotion_intensity",
    "missing_relation_context",
    "missing_action_intention",
    "conflicting_current_and_history_signal",
    "low_information_current_input",
    "boundary_or_tier_unclear",
    "history_connection_basis_unclear",
    "self_blame_or_safety_boundary_unclear",
)
P7_R54_AHR_POST_CR22_EX05_REPAIR_REQUIRED_REF_OPTION_REFS: Final[tuple[str, ...]] = (
    "no_repair_required",
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
    "p4_current_surface_repair_required",
)
P7_R54_AHR_POST_CR22_EX05_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_design_material_candidate",
    "p8_implementation_spec_finalized_here",
)

P7_R54_AHR_POST_CR22_EX04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex03_schema_version",
    "ex03_material_ref",
    "ex03_next_required_step",
    "ex03_local_only_preflight_ready",
    "ex03_body_full_packet_request_boundary_ready",
    "ex03_body_full_packet_request_ref",
    "ex03_explicit_allow_ref",
    "ex03_local_review_root_ref",
    "ex03_retention_policy_ref",
    "ex03_disposal_policy_ref",
    "ex03_export_denylist_policy_ref",
    "packet_generation_receipt_status_ref",
    "packet_generation_receipt_allowed_status_refs",
    "packet_generation_receipt_accepted",
    "packet_generation_receipt_reason_refs",
    "packet_generation_receipt_blocker_refs",
    "packet_generation_receipt_blocker_ref_count",
    "packet_generation_receipt_ref",
    "packet_generation_receipt_ref_present",
    "packet_generation_receipt_ref_is_bodyfree_ref",
    "packet_generation_receipt_ref_has_local_path_shape",
    "packet_generation_receipt_actual_source_ref",
    "packet_generation_receipt_actual_source_allowed_ref",
    "packet_generation_receipt_source_guard_passed",
    "packet_case_count",
    "required_packet_case_count",
    "packet_case_count_is_24",
    "packet_completeness_scan_ref",
    "packet_completeness_scan_ref_present",
    "packet_completeness_scan_ref_is_bodyfree_ref",
    "packet_completeness_scan_ref_has_local_path_shape",
    "export_denylist_scan_ref",
    "export_denylist_scan_ref_present",
    "export_denylist_scan_ref_is_bodyfree_ref",
    "export_denylist_scan_ref_has_local_path_shape",
    "packet_completeness_passed",
    "export_denylist_scan_passed",
    "packet_materialized_for_review_acknowledged_by_bodyfree_receipt",
    "packet_generation_receipt_bodyfree_only",
    "packet_generation_receipt_intaked_here",
    "packet_generation_receipt_does_not_generate_packet_body_here",
    "packet_body_not_exported",
    "packet_body_exported",
    "packet_content_included",
    "body_full_packet_content_included",
    "body_full_packet_generation_started_here",
    "body_full_packet_generated_here",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_requested",
    "packet_completeness_bodyfree_count_only",
    "export_denylist_bodyfree_intake_enabled",
    "packet_receipt_does_not_expose_local_path_hash_or_body",
    "packet_receipt_does_not_execute_actual_human_review",
    "packet_receipt_does_not_create_selection_rating_question_rows",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_CR22_EX05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex04_schema_version",
    "ex04_material_ref",
    "ex04_next_required_step",
    "ex04_packet_generation_receipt_accepted",
    "ex04_packet_case_count",
    "ex04_packet_completeness_passed",
    "ex04_export_denylist_scan_passed",
    "ex04_packet_generation_receipt_actual_source_ref",
    "reviewer_boundary_status_ref",
    "reviewer_boundary_allowed_status_refs",
    "reviewer_boundary_ready",
    "reviewer_boundary_reason_refs",
    "reviewer_boundary_blocker_refs",
    "reviewer_boundary_blocker_ref_count",
    "reviewer_person_ref",
    "reviewer_person_ref_present",
    "reviewer_person_ref_is_bodyfree_ref",
    "reviewer_person_ref_has_local_path_shape",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_person_boundary_frozen",
    "reviewer_person_identity_bodyfree_only",
    "reviewer_local_only_read_receipt_required_later",
    "reviewer_local_only_read_receipt_present",
    "actual_human_review_executed_by_person",
    "selection_only_form_frozen",
    "selection_only",
    "selection_row_count_required",
    "allowed_selection_row_count",
    "selection_row_count_required_is_24",
    "free_text_allowed",
    "reviewer_notes_export_allowed",
    "question_text_allowed",
    "draft_question_text_allowed",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "rating_axis_profile_ref",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "question_need_primary_class_options",
    "question_need_primary_class_option_count",
    "one_question_fit_option_refs",
    "one_question_fit_option_count",
    "verdict_option_refs",
    "verdict_option_count",
    "sanitized_reason_id_option_refs",
    "sanitized_reason_id_option_count",
    "readfeel_blocker_id_option_refs",
    "readfeel_blocker_id_option_count",
    "execution_blocker_id_option_refs",
    "execution_blocker_id_option_count",
    "ambiguity_kind_option_refs",
    "ambiguity_kind_option_count",
    "repair_required_ref_option_refs",
    "repair_required_ref_option_count",
    "plan_candidate_flag_refs",
    "plan_candidate_flag_count",
    "p8_implementation_spec_finalized_here",
    "selection_form_does_not_run_actual_review",
    "selection_form_does_not_create_selection_rows_here",
    "selection_form_does_not_create_rating_rows_here",
    "selection_form_does_not_create_question_observation_rows_here",
    "selection_form_does_not_create_question_text_or_draft",
    "selection_form_does_not_export_reviewer_notes",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _int_value_or_zero(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bodyfree_ref_or_rejected(
    value: Any, *, default: str = "", rejected_ref: str, max_length: int = 260
) -> tuple[str, bool]:
    candidate = clean_identifier(value, default=default, max_length=max_length)
    has_path_shape = _ref_has_local_path_shape(candidate)
    if has_path_shape:
        return rejected_ref, True
    if candidate == rejected_ref:
        return rejected_ref, True
    return candidate, False


def _ex04_packet_generation_receipt_fields(
    *,
    ex03_preflight_ready: bool,
    ex03_packet_request_ready: bool,
    ex03_packet_request_ref: Any,
    packet_generation_receipt_ref: Any,
    packet_case_count: Any,
    packet_completeness_scan_ref: Any,
    export_denylist_scan_ref: Any,
    packet_completeness_passed: bool,
    export_denylist_scan_passed: bool,
    packet_body_exported: bool,
    packet_materialized_for_review_acknowledged_by_bodyfree_receipt: bool,
    actual_source_ref: Any,
    packet_content_included: bool,
    body_full_packet_content_included: bool,
    local_absolute_path_included: bool,
    body_hash_included: bool,
    terminal_output_body_included: bool,
    forbidden_body_path_hash_or_terminal_body_requested: bool = False,
) -> dict[str, Any]:
    receipt_ref, receipt_ref_has_path = _bodyfree_ref_or_rejected(
        packet_generation_receipt_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX04_REJECTED_RECEIPT_PATH_SHAPE_REF,
        max_length=260,
    )
    completeness_scan_ref, completeness_scan_ref_has_path = _bodyfree_ref_or_rejected(
        packet_completeness_scan_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX04_REJECTED_SCAN_PATH_SHAPE_REF,
        max_length=260,
    )
    denylist_scan_ref, denylist_scan_ref_has_path = _bodyfree_ref_or_rejected(
        export_denylist_scan_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX04_REJECTED_SCAN_PATH_SHAPE_REF,
        max_length=260,
    )
    source_ref = clean_identifier(actual_source_ref, default="", max_length=180)
    packet_count = _int_value_or_zero(packet_case_count)
    forbidden_body_path_hash_requested = bool(forbidden_body_path_hash_or_terminal_body_requested) or any(
        (
            packet_content_included,
            body_full_packet_content_included,
            local_absolute_path_included,
            body_hash_included,
            terminal_output_body_included,
        )
    )
    blockers: list[str] = []
    if not ex03_preflight_ready or not ex03_packet_request_ready:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_EX03_PREFLIGHT_NOT_READY_REF)
    if not clean_identifier(ex03_packet_request_ref, default=""):
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_PACKET_REQUEST_MISSING_REF)
    if not receipt_ref:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_RECEIPT_REF_MISSING_REF)
    if receipt_ref_has_path:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_RECEIPT_REF_PATH_SHAPE_REF)
    if source_ref != P7_R54_AHR_POST_CR22_EX04_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_ACTUAL_SOURCE_REF_NOT_ALLOWED_REF)
    if packet_count != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_PACKET_COUNT_NOT_24_REF)
    if not completeness_scan_ref:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_COMPLETENESS_SCAN_MISSING_REF)
    if completeness_scan_ref_has_path:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_COMPLETENESS_SCAN_PATH_SHAPE_REF)
    if not denylist_scan_ref:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_EXPORT_DENYLIST_SCAN_MISSING_REF)
    if denylist_scan_ref_has_path:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_EXPORT_DENYLIST_SCAN_PATH_SHAPE_REF)
    if not packet_completeness_passed:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_COMPLETENESS_SCAN_NOT_PASSED_REF)
    if not export_denylist_scan_passed:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_EXPORT_DENYLIST_SCAN_NOT_PASSED_REF)
    if packet_body_exported:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_PACKET_BODY_EXPORTED_REF)
    if forbidden_body_path_hash_requested:
        blockers.append(P7_R54_AHR_POST_CR22_EX04_BLOCKER_FORBIDDEN_BODY_PATH_HASH_REF)
    blockers = _dedupe_refs(blockers)
    ready = not blockers
    return {
        "packet_generation_receipt_status_ref": (
            P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_ACCEPTED_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_BLOCKED_STATUS_REF
        ),
        "packet_generation_receipt_allowed_status_refs": list(
            P7_R54_AHR_POST_CR22_EX04_ALLOWED_PACKET_RECEIPT_STATUS_REFS
        ),
        "packet_generation_receipt_accepted": ready,
        "packet_generation_receipt_reason_refs": [P7_R54_AHR_POST_CR22_EX04_READY_REASON_REF] if ready else [],
        "packet_generation_receipt_blocker_refs": blockers,
        "packet_generation_receipt_blocker_ref_count": len(blockers),
        "packet_generation_receipt_ref": receipt_ref,
        "packet_generation_receipt_ref_present": bool(receipt_ref),
        "packet_generation_receipt_ref_is_bodyfree_ref": bool(receipt_ref) and not receipt_ref_has_path,
        "packet_generation_receipt_ref_has_local_path_shape": receipt_ref_has_path,
        "packet_generation_receipt_actual_source_ref": source_ref,
        "packet_generation_receipt_actual_source_allowed_ref": P7_R54_AHR_POST_CR22_EX04_ALLOWED_ACTUAL_SOURCE_REF,
        "packet_generation_receipt_source_guard_passed": (
            source_ref == P7_R54_AHR_POST_CR22_EX04_ALLOWED_ACTUAL_SOURCE_REF
        ),
        "packet_case_count": packet_count,
        "required_packet_case_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "packet_case_count_is_24": packet_count == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "packet_completeness_scan_ref": completeness_scan_ref,
        "packet_completeness_scan_ref_present": bool(completeness_scan_ref),
        "packet_completeness_scan_ref_is_bodyfree_ref": bool(completeness_scan_ref) and not completeness_scan_ref_has_path,
        "packet_completeness_scan_ref_has_local_path_shape": completeness_scan_ref_has_path,
        "export_denylist_scan_ref": denylist_scan_ref,
        "export_denylist_scan_ref_present": bool(denylist_scan_ref),
        "export_denylist_scan_ref_is_bodyfree_ref": bool(denylist_scan_ref) and not denylist_scan_ref_has_path,
        "export_denylist_scan_ref_has_local_path_shape": denylist_scan_ref_has_path,
        "packet_completeness_passed": bool(packet_completeness_passed),
        "export_denylist_scan_passed": bool(export_denylist_scan_passed),
        "packet_materialized_for_review_acknowledged_by_bodyfree_receipt": (
            bool(packet_materialized_for_review_acknowledged_by_bodyfree_receipt) and ready
        ),
        "packet_generation_receipt_bodyfree_only": True,
        "packet_generation_receipt_intaked_here": ready,
        "packet_generation_receipt_does_not_generate_packet_body_here": True,
        "packet_body_not_exported": not bool(packet_body_exported),
        "packet_body_exported": bool(packet_body_exported),
        "packet_content_included": False,
        "body_full_packet_content_included": False,
        "body_full_packet_generation_started_here": False,
        "body_full_packet_generated_here": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_requested": forbidden_body_path_hash_requested,
        "packet_completeness_bodyfree_count_only": True,
        "export_denylist_bodyfree_intake_enabled": True,
        "packet_receipt_does_not_expose_local_path_hash_or_body": True,
        "packet_receipt_does_not_execute_actual_human_review": True,
        "packet_receipt_does_not_create_selection_rating_question_rows": True,
    }


def _ex05_reviewer_person_selection_only_form_fields(
    *,
    ex04_packet_generation_receipt_accepted: bool,
    reviewer_person_ref: Any,
    reviewer_is_person: bool,
    reviewer_person_confirmed: bool,
    selection_row_count_required: Any,
    free_text_allowed: bool,
    reviewer_notes_export_allowed: bool,
    question_text_allowed: bool,
    draft_question_text_allowed: bool,
) -> dict[str, Any]:
    reviewer_ref, reviewer_ref_has_path = _bodyfree_ref_or_rejected(
        reviewer_person_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX05_REJECTED_REVIEWER_PERSON_PATH_SHAPE_REF,
        max_length=180,
    )
    selection_count = _int_value_or_zero(selection_row_count_required)
    blockers: list[str] = []
    if not ex04_packet_generation_receipt_accepted:
        blockers.append("ex04_packet_generation_receipt_not_accepted")
    if not reviewer_ref:
        blockers.append("reviewer_person_ref_missing")
    if reviewer_ref_has_path:
        blockers.append("reviewer_person_ref_must_be_bodyfree_ref_not_path")
    if not reviewer_is_person:
        blockers.append("reviewer_is_person_not_confirmed")
    if not reviewer_person_confirmed:
        blockers.append("reviewer_person_confirmed_missing")
    if selection_count != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_row_count_required_not_24")
    if free_text_allowed:
        blockers.append("free_text_allowed_must_be_false")
    if reviewer_notes_export_allowed:
        blockers.append("reviewer_notes_export_allowed_must_be_false")
    if question_text_allowed:
        blockers.append("question_text_allowed_must_be_false")
    if draft_question_text_allowed:
        blockers.append("draft_question_text_allowed_must_be_false")
    blockers = _dedupe_refs(blockers)
    ready = not blockers
    return {
        "reviewer_boundary_status_ref": (
            P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_BLOCKED_STATUS_REF
        ),
        "reviewer_boundary_allowed_status_refs": list(
            P7_R54_AHR_POST_CR22_EX05_ALLOWED_REVIEWER_BOUNDARY_STATUS_REFS
        ),
        "reviewer_boundary_ready": ready,
        "reviewer_boundary_reason_refs": [P7_R54_AHR_POST_CR22_EX05_READY_REASON_REF] if ready else [],
        "reviewer_boundary_blocker_refs": blockers,
        "reviewer_boundary_blocker_ref_count": len(blockers),
        "reviewer_person_ref": reviewer_ref,
        "reviewer_person_ref_present": bool(reviewer_ref),
        "reviewer_person_ref_is_bodyfree_ref": bool(reviewer_ref) and not reviewer_ref_has_path,
        "reviewer_person_ref_has_local_path_shape": reviewer_ref_has_path,
        "reviewer_is_person": bool(reviewer_is_person),
        "reviewer_person_confirmed": bool(reviewer_person_confirmed),
        "reviewer_person_boundary_frozen": True,
        "reviewer_person_identity_bodyfree_only": True,
        "reviewer_local_only_read_receipt_required_later": True,
        "reviewer_local_only_read_receipt_present": False,
        "actual_human_review_executed_by_person": False,
        "selection_only_form_frozen": True,
        "selection_only": True,
        "selection_row_count_required": selection_count,
        "allowed_selection_row_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "selection_row_count_required_is_24": selection_count == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "free_text_allowed": bool(free_text_allowed),
        "reviewer_notes_export_allowed": bool(reviewer_notes_export_allowed),
        "question_text_allowed": bool(question_text_allowed),
        "draft_question_text_allowed": bool(draft_question_text_allowed),
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "rating_axis_profile_ref": cr.P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF,
        "rating_axis_refs": list(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "rating_axis_count": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS),
        "question_need_primary_class_options": list(cr.P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "question_need_primary_class_option_count": len(
            cr.P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS
        ),
        "one_question_fit_option_refs": list(cr.P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS),
        "one_question_fit_option_count": len(cr.P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS),
        "verdict_option_refs": list(P7_R54_AHR_POST_CR22_EX05_VERDICT_OPTION_REFS),
        "verdict_option_count": len(P7_R54_AHR_POST_CR22_EX05_VERDICT_OPTION_REFS),
        "sanitized_reason_id_option_refs": list(P7_R54_AHR_POST_CR22_EX05_SANITIZED_REASON_ID_OPTION_REFS),
        "sanitized_reason_id_option_count": len(P7_R54_AHR_POST_CR22_EX05_SANITIZED_REASON_ID_OPTION_REFS),
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR_POST_CR22_EX05_READFEEL_BLOCKER_ID_OPTION_REFS),
        "readfeel_blocker_id_option_count": len(P7_R54_AHR_POST_CR22_EX05_READFEEL_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_refs": list(P7_R54_AHR_POST_CR22_EX05_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_count": len(P7_R54_AHR_POST_CR22_EX05_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "ambiguity_kind_option_refs": list(P7_R54_AHR_POST_CR22_EX05_AMBIGUITY_KIND_OPTION_REFS),
        "ambiguity_kind_option_count": len(P7_R54_AHR_POST_CR22_EX05_AMBIGUITY_KIND_OPTION_REFS),
        "repair_required_ref_option_refs": list(P7_R54_AHR_POST_CR22_EX05_REPAIR_REQUIRED_REF_OPTION_REFS),
        "repair_required_ref_option_count": len(P7_R54_AHR_POST_CR22_EX05_REPAIR_REQUIRED_REF_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_AHR_POST_CR22_EX05_PLAN_CANDIDATE_FLAG_REFS),
        "plan_candidate_flag_count": len(P7_R54_AHR_POST_CR22_EX05_PLAN_CANDIDATE_FLAG_REFS),
        "p8_implementation_spec_finalized_here": False,
        "selection_form_does_not_run_actual_review": True,
        "selection_form_does_not_create_selection_rows_here": True,
        "selection_form_does_not_create_rating_rows_here": True,
        "selection_form_does_not_create_question_observation_rows_here": True,
        "selection_form_does_not_create_question_text_or_draft": True,
        "selection_form_does_not_export_reviewer_notes": True,
    }


def build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
    *,
    local_only_preflight_explicit_allow_packet_request_boundary: Mapping[str, Any] | None = None,
    packet_generation_receipt_ref: Any = "",
    packet_case_count: Any = 0,
    packet_completeness_scan_ref: Any = "",
    export_denylist_scan_ref: Any = "",
    packet_completeness_passed: bool = False,
    export_denylist_scan_passed: bool = False,
    packet_body_exported: bool = False,
    packet_materialized_for_review_acknowledged_by_bodyfree_receipt: bool = True,
    actual_source_ref: Any = P7_R54_AHR_POST_CR22_EX04_ALLOWED_ACTUAL_SOURCE_REF,
    packet_content_included: bool = False,
    body_full_packet_content_included: bool = False,
    local_absolute_path_included: bool = False,
    body_hash_included: bool = False,
    terminal_output_body_included: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX04 body-free packet generation receipt / completeness / export denylist intake."""

    ex03 = dict(
        local_only_preflight_explicit_allow_packet_request_boundary
        or build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
            review_session_id=review_session_id
        )
    )
    assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(ex03)
    receipt_fields = _ex04_packet_generation_receipt_fields(
        ex03_preflight_ready=ex03.get("local_only_preflight_ready") is True,
        ex03_packet_request_ready=ex03.get("body_full_packet_request_boundary_ready") is True,
        ex03_packet_request_ref=ex03.get("body_full_packet_request_ref"),
        packet_generation_receipt_ref=packet_generation_receipt_ref,
        packet_case_count=packet_case_count,
        packet_completeness_scan_ref=packet_completeness_scan_ref,
        export_denylist_scan_ref=export_denylist_scan_ref,
        packet_completeness_passed=packet_completeness_passed,
        export_denylist_scan_passed=export_denylist_scan_passed,
        packet_body_exported=packet_body_exported,
        packet_materialized_for_review_acknowledged_by_bodyfree_receipt=(
            packet_materialized_for_review_acknowledged_by_bodyfree_receipt
        ),
        actual_source_ref=actual_source_ref,
        packet_content_included=packet_content_included,
        body_full_packet_content_included=body_full_packet_content_included,
        local_absolute_path_included=local_absolute_path_included,
        body_hash_included=body_hash_included,
        terminal_output_body_included=terminal_output_body_included,
        forbidden_body_path_hash_or_terminal_body_requested=False,
    )
    ready = receipt_fields["packet_generation_receipt_accepted"] is True
    material: dict[str, Any] = {
        "schema_version": (
            P7_R54_AHR_POST_CR22_EX04_LOCAL_BODY_FULL_PACKET_GENERATION_RECEIPT_COMPLETENESS_EXPORT_DENYLIST_BODYFREE_INTAKE_SCHEMA_VERSION
        ),
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX04_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_cr22_ex04_local_packet_generation_receipt_bodyfree_intake_20260629",
        "review_session_id": _safe_review_session_id(review_session_id or ex03.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex03_schema_version": ex03["schema_version"],
        "ex03_material_ref": ex03["material_id"],
        "ex03_next_required_step": ex03["next_required_step"],
        "ex03_local_only_preflight_ready": ex03["local_only_preflight_ready"],
        "ex03_body_full_packet_request_boundary_ready": ex03["body_full_packet_request_boundary_ready"],
        "ex03_body_full_packet_request_ref": ex03["body_full_packet_request_ref"],
        "ex03_explicit_allow_ref": ex03["explicit_allow_ref"],
        "ex03_local_review_root_ref": ex03["local_review_root_ref"],
        "ex03_retention_policy_ref": ex03["retention_policy_ref"],
        "ex03_disposal_policy_ref": ex03["disposal_policy_ref"],
        "ex03_export_denylist_policy_ref": ex03["export_denylist_policy_ref"],
        **receipt_fields,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX04_IMPLEMENTED_STEPS if ready else tuple(ex03["implemented_steps"])
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX04_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ex03["not_yet_implemented_steps"])
        ),
        "next_required_step": (
            P7_R54_AHR_POST_CR22_EX05_STEP_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX04_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX04_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX04 local packet generation receipt intake",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=(
            P7_R54_AHR_POST_CR22_EX04_LOCAL_BODY_FULL_PACKET_GENERATION_RECEIPT_COMPLETENESS_EXPORT_DENYLIST_BODYFREE_INTAKE_SCHEMA_VERSION
        ),
        operation_step_ref=P7_R54_AHR_POST_CR22_EX04_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX04 local packet generation receipt intake",
    )
    if data.get("ex03_schema_version") != (
        P7_R54_AHR_POST_CR22_EX03_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX04 EX03 schema version changed")
    expected = _ex04_packet_generation_receipt_fields(
        ex03_preflight_ready=data.get("ex03_local_only_preflight_ready") is True,
        ex03_packet_request_ready=data.get("ex03_body_full_packet_request_boundary_ready") is True,
        ex03_packet_request_ref=data.get("ex03_body_full_packet_request_ref"),
        packet_generation_receipt_ref=data.get("packet_generation_receipt_ref"),
        packet_case_count=data.get("packet_case_count"),
        packet_completeness_scan_ref=data.get("packet_completeness_scan_ref"),
        export_denylist_scan_ref=data.get("export_denylist_scan_ref"),
        packet_completeness_passed=data.get("packet_completeness_passed") is True,
        export_denylist_scan_passed=data.get("export_denylist_scan_passed") is True,
        packet_body_exported=data.get("packet_body_exported") is True,
        packet_materialized_for_review_acknowledged_by_bodyfree_receipt=(
            data.get("packet_materialized_for_review_acknowledged_by_bodyfree_receipt") is True
        ),
        actual_source_ref=data.get("packet_generation_receipt_actual_source_ref"),
        packet_content_included=data.get("packet_content_included") is True,
        body_full_packet_content_included=data.get("body_full_packet_content_included") is True,
        local_absolute_path_included=data.get("local_absolute_path_included") is True,
        body_hash_included=data.get("body_hash_included") is True,
        terminal_output_body_included=data.get("terminal_output_body_included") is True,
        forbidden_body_path_hash_or_terminal_body_requested=(
            data.get("packet_generation_receipt_forbidden_body_path_hash_or_terminal_body_requested") is True
        ),
    )
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX04 {key} changed")
    blockers = list(data.get("packet_generation_receipt_blocker_refs") or [])
    ready = not blockers
    if data.get("packet_generation_receipt_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX04 blocker count changed")
    if data.get("packet_generation_receipt_accepted") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX04 accepted flag changed")
    expected_status = (
        P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_ACCEPTED_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX04_PACKET_RECEIPT_BLOCKED_STATUS_REF
    )
    if data.get("packet_generation_receipt_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX04 status changed")
    if tuple(data.get("packet_generation_receipt_allowed_status_refs") or ()) != (
        P7_R54_AHR_POST_CR22_EX04_ALLOWED_PACKET_RECEIPT_STATUS_REFS
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX04 allowed status refs changed")
    if ready:
        if data.get("ex03_next_required_step") != P7_R54_AHR_POST_CR22_EX04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX04 must follow ready EX03")
        if data.get("packet_generation_receipt_reason_refs") != [P7_R54_AHR_POST_CR22_EX04_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX04 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX04 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX04 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX04 next step changed")
    else:
        if data.get("packet_generation_receipt_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX04 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX04_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX04 blocked next step changed")
    for key in (
        "packet_generation_receipt_bodyfree_only",
        "packet_generation_receipt_does_not_generate_packet_body_here",
        "packet_completeness_bodyfree_count_only",
        "export_denylist_bodyfree_intake_enabled",
        "packet_receipt_does_not_expose_local_path_hash_or_body",
        "packet_receipt_does_not_execute_actual_human_review",
        "packet_receipt_does_not_create_selection_rating_question_rows",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "current_cr_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX04 required true field changed: {key}")
    for key in (
        "packet_content_included",
        "body_full_packet_content_included",
        "body_full_packet_generation_started_here",
        "body_full_packet_generated_here",
        "local_absolute_path_included",
        "body_hash_included",
        "terminal_output_body_included",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "actual_review_evidence_complete",
        "actual_selection_rows_created_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX04 required false field changed: {key}")
    return True


def build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
    *,
    local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake: Mapping[str, Any] | None = None,
    reviewer_person_ref: Any = "",
    reviewer_is_person: bool = True,
    reviewer_person_confirmed: bool = False,
    selection_row_count_required: Any = P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
    free_text_allowed: bool = False,
    reviewer_notes_export_allowed: bool = False,
    question_text_allowed: bool = False,
    draft_question_text_allowed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX05 body-free reviewer-person boundary and selection-only form material."""

    ex04 = dict(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake
        or build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
            review_session_id=review_session_id
        )
    )
    assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
        ex04
    )
    form_fields = _ex05_reviewer_person_selection_only_form_fields(
        ex04_packet_generation_receipt_accepted=ex04.get("packet_generation_receipt_accepted") is True,
        reviewer_person_ref=reviewer_person_ref,
        reviewer_is_person=reviewer_is_person,
        reviewer_person_confirmed=reviewer_person_confirmed,
        selection_row_count_required=selection_row_count_required,
        free_text_allowed=free_text_allowed,
        reviewer_notes_export_allowed=reviewer_notes_export_allowed,
        question_text_allowed=question_text_allowed,
        draft_question_text_allowed=draft_question_text_allowed,
    )
    ready = form_fields["reviewer_boundary_ready"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX05_REVIEWER_PERSON_BOUNDARY_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX05_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_20260629",
        "review_session_id": _safe_review_session_id(review_session_id or ex04.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex04_schema_version": ex04["schema_version"],
        "ex04_material_ref": ex04["material_id"],
        "ex04_next_required_step": ex04["next_required_step"],
        "ex04_packet_generation_receipt_accepted": ex04["packet_generation_receipt_accepted"],
        "ex04_packet_case_count": ex04["packet_case_count"],
        "ex04_packet_completeness_passed": ex04["packet_completeness_passed"],
        "ex04_export_denylist_scan_passed": ex04["export_denylist_scan_passed"],
        "ex04_packet_generation_receipt_actual_source_ref": ex04[
            "packet_generation_receipt_actual_source_ref"
        ],
        **form_fields,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX05_IMPLEMENTED_STEPS if ready else tuple(ex04["implemented_steps"])
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX05_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ex04["not_yet_implemented_steps"])
        ),
        "next_required_step": (
            P7_R54_AHR_POST_CR22_EX06_STEP_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX05_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX05 reviewer person / selection-only form freeze",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX05_REVIEWER_PERSON_BOUNDARY_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX05_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX05 reviewer person / selection-only form freeze",
    )
    if data.get("ex04_schema_version") != (
        P7_R54_AHR_POST_CR22_EX04_LOCAL_BODY_FULL_PACKET_GENERATION_RECEIPT_COMPLETENESS_EXPORT_DENYLIST_BODYFREE_INTAKE_SCHEMA_VERSION
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX05 EX04 schema version changed")
    expected = _ex05_reviewer_person_selection_only_form_fields(
        ex04_packet_generation_receipt_accepted=data.get("ex04_packet_generation_receipt_accepted") is True,
        reviewer_person_ref=data.get("reviewer_person_ref"),
        reviewer_is_person=data.get("reviewer_is_person") is True,
        reviewer_person_confirmed=data.get("reviewer_person_confirmed") is True,
        selection_row_count_required=data.get("selection_row_count_required"),
        free_text_allowed=data.get("free_text_allowed") is True,
        reviewer_notes_export_allowed=data.get("reviewer_notes_export_allowed") is True,
        question_text_allowed=data.get("question_text_allowed") is True,
        draft_question_text_allowed=data.get("draft_question_text_allowed") is True,
    )
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX05 {key} changed")
    blockers = list(data.get("reviewer_boundary_blocker_refs") or [])
    ready = not blockers
    if data.get("reviewer_boundary_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX05 blocker count changed")
    if data.get("reviewer_boundary_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX05 ready flag changed")
    expected_status = (
        P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX05_REVIEWER_BOUNDARY_BLOCKED_STATUS_REF
    )
    if data.get("reviewer_boundary_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX05 status changed")
    if tuple(data.get("reviewer_boundary_allowed_status_refs") or ()) != (
        P7_R54_AHR_POST_CR22_EX05_ALLOWED_REVIEWER_BOUNDARY_STATUS_REFS
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX05 allowed status refs changed")
    if ready:
        if data.get("ex04_next_required_step") != P7_R54_AHR_POST_CR22_EX05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX05 must follow ready EX04")
        if data.get("reviewer_boundary_reason_refs") != [P7_R54_AHR_POST_CR22_EX05_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX05 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX05 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX05 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX05 next step changed")
    else:
        if data.get("reviewer_boundary_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX05 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX05_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX05 blocked next step changed")
    if data.get("rating_axis_profile_ref") != cr.P7_R54_AHR_CR04_REVIEW_AXIS_PROFILE_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX05 rating axis profile changed")
    if tuple(data.get("rating_axis_refs") or ()) != cr.P7_R54_AHR_CR08_RATING_AXIS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX05 rating axis refs changed")
    if data.get("rating_axis_count") != len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX05 rating axis count changed")
    if data.get("rating_axis_target_thresholds") != cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-AHR-PostCR22-EX05 rating axis thresholds changed")
    if tuple(data.get("question_need_primary_class_options") or ()) != (
        cr.P7_R54_AHR_CR08_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS
    ):
        raise ValueError("P7-R54-AHR-PostCR22-EX05 question need options changed")
    if tuple(data.get("one_question_fit_option_refs") or ()) != cr.P7_R54_AHR_CR08_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX05 one-question options changed")
    for refs_field, count_field, expected_refs in (
        ("verdict_option_refs", "verdict_option_count", P7_R54_AHR_POST_CR22_EX05_VERDICT_OPTION_REFS),
        (
            "sanitized_reason_id_option_refs",
            "sanitized_reason_id_option_count",
            P7_R54_AHR_POST_CR22_EX05_SANITIZED_REASON_ID_OPTION_REFS,
        ),
        (
            "readfeel_blocker_id_option_refs",
            "readfeel_blocker_id_option_count",
            P7_R54_AHR_POST_CR22_EX05_READFEEL_BLOCKER_ID_OPTION_REFS,
        ),
        (
            "execution_blocker_id_option_refs",
            "execution_blocker_id_option_count",
            P7_R54_AHR_POST_CR22_EX05_EXECUTION_BLOCKER_ID_OPTION_REFS,
        ),
        (
            "ambiguity_kind_option_refs",
            "ambiguity_kind_option_count",
            P7_R54_AHR_POST_CR22_EX05_AMBIGUITY_KIND_OPTION_REFS,
        ),
        (
            "repair_required_ref_option_refs",
            "repair_required_ref_option_count",
            P7_R54_AHR_POST_CR22_EX05_REPAIR_REQUIRED_REF_OPTION_REFS,
        ),
        ("plan_candidate_flag_refs", "plan_candidate_flag_count", P7_R54_AHR_POST_CR22_EX05_PLAN_CANDIDATE_FLAG_REFS),
    ):
        if tuple(data.get(refs_field) or ()) != expected_refs:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX05 {refs_field} changed")
        if data.get(count_field) != len(expected_refs):
            raise ValueError(f"P7-R54-AHR-PostCR22-EX05 {count_field} changed")
    for key in (
        "reviewer_person_boundary_frozen",
        "reviewer_person_identity_bodyfree_only",
        "reviewer_local_only_read_receipt_required_later",
        "selection_only_form_frozen",
        "selection_only",
        "selection_form_does_not_run_actual_review",
        "selection_form_does_not_create_selection_rows_here",
        "selection_form_does_not_create_rating_rows_here",
        "selection_form_does_not_create_question_observation_rows_here",
        "selection_form_does_not_create_question_text_or_draft",
        "selection_form_does_not_export_reviewer_notes",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "current_cr_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX05 required true field changed: {key}")
    for key in (
        "reviewer_local_only_read_receipt_present",
        "actual_human_review_executed_by_person",
        "reviewer_free_text_included",
        "reviewer_notes_body_included",
        "question_text_included",
        "draft_question_text_included",
        "p8_implementation_spec_finalized_here",
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "actual_review_evidence_complete",
        "actual_selection_rows_created_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX05 required false field changed: {key}")
    return True




# ---------------------------------------------------------------------------
# EX06-EX07 Post-CR22 actual local-only review protocol / operation receipt intake
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX06_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_EXECUTION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex06_actual_local_only_human_review_execution_protocol.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX07_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex07_actual_operation_receipt_intake.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
    P7_R54_AHR_POST_CR22_EX02_STEP_REF,
    P7_R54_AHR_POST_CR22_EX03_STEP_REF,
    P7_R54_AHR_POST_CR22_EX04_STEP_REF,
    P7_R54_AHR_POST_CR22_EX05_STEP_REF,
    P7_R54_AHR_POST_CR22_EX06_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[7:]
)
P7_R54_AHR_POST_CR22_EX07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX00_STEP_REF,
    P7_R54_AHR_POST_CR22_EX01_STEP_REF,
    P7_R54_AHR_POST_CR22_EX02_STEP_REF,
    P7_R54_AHR_POST_CR22_EX03_STEP_REF,
    P7_R54_AHR_POST_CR22_EX04_STEP_REF,
    P7_R54_AHR_POST_CR22_EX05_STEP_REF,
    P7_R54_AHR_POST_CR22_EX06_STEP_REF,
    P7_R54_AHR_POST_CR22_EX07_STEP_REF,
)
P7_R54_AHR_POST_CR22_EX07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX_STEP_REFS[8:]
)

P7_R54_AHR_POST_CR22_EX06_PROTOCOL_READY_STATUS_REF: Final = (
    "EX06_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_EXECUTION_PROTOCOL_READY_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX06_PROTOCOL_BLOCKED_STATUS_REF: Final = (
    "EX06_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_EXECUTION_PROTOCOL_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX06_ALLOWED_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX06_PROTOCOL_READY_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX06_PROTOCOL_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX06_READY_REASON_REF: Final = (
    "EX06_LOCAL_ONLY_SELECTION_ONLY_NO_BODY_NO_QUESTION_REVIEW_PROTOCOL_FROZEN"
)
P7_R54_AHR_POST_CR22_EX06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex06_actual_local_only_human_review_execution_protocol_or_stop"
)

P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_ACCEPTED_STATUS_REF: Final = (
    "EX07_ACTUAL_OPERATION_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_BLOCKED_STATUS_REF: Final = (
    "EX07_ACTUAL_OPERATION_RECEIPT_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX07_ALLOWED_OPERATION_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_ACCEPTED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX07_READY_REASON_REF: Final = (
    "EX07_ACTUAL_PERSON_LOCAL_ONLY_OPERATION_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex07_actual_operation_receipt_intake_or_stop"
)
P7_R54_AHR_POST_CR22_EX07_DEFAULT_OPERATION_RECEIPT_REF: Final = (
    "postcr22_actual_operation_receipt_ref_20260629_001_bodyfree"
)
P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_STARTED_BUCKET_REF: Final = (
    "review_started_bucket_20260629_local_only_bodyfree"
)
P7_R54_AHR_POST_CR22_EX07_DEFAULT_REVIEW_COMPLETED_BUCKET_REF: Final = (
    "review_completed_bucket_20260629_local_only_bodyfree"
)
P7_R54_AHR_POST_CR22_EX07_REJECTED_OPERATION_RECEIPT_PATH_SHAPE_REF: Final = (
    "rejected_operation_receipt_ref_path_shape_bodyfree"
)
P7_R54_AHR_POST_CR22_EX07_REJECTED_BUCKET_PATH_SHAPE_REF: Final = (
    "rejected_review_bucket_ref_path_shape_bodyfree"
)
P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF: Final = (
    "actual_person_local_only_review_operation_receipt"
)

P7_R54_AHR_POST_CR22_EX06_PROTOCOL_STEP_REFS: Final[tuple[str, ...]] = (
    "reviewer_reads_local_only_packet",
    "reviewer_selects_axis_scores_verdict_and_refs_without_body_quote",
    "reviewer_notes_are_not_exported",
    "question_text_is_not_written",
    "all_24_cases_are_completed",
    "operation_receipt_is_created_bodyfree",
)
P7_R54_AHR_POST_CR22_EX06_BLOCKER_EX05_REVIEWER_BOUNDARY_NOT_READY_REF: Final = (
    "ex05_reviewer_boundary_not_ready"
)
P7_R54_AHR_POST_CR22_EX06_BLOCKER_EX05_NEXT_REQUIRED_STEP_NOT_EX06_REF: Final = (
    "ex05_next_required_step_not_ex06"
)
P7_R54_AHR_POST_CR22_EX06_BLOCKER_LOCAL_ONLY_NOT_TRUE_REF: Final = "protocol_local_only_must_be_true"
P7_R54_AHR_POST_CR22_EX06_BLOCKER_MUST_NOT_EXPORT_NOT_TRUE_REF: Final = "protocol_must_not_export_must_be_true"
P7_R54_AHR_POST_CR22_EX06_BLOCKER_SELECTION_ONLY_NOT_TRUE_REF: Final = "protocol_selection_only_must_be_true"
P7_R54_AHR_POST_CR22_EX06_BLOCKER_REVIEWED_COUNT_NOT_24_REF: Final = "protocol_reviewed_case_count_required_not_24"
P7_R54_AHR_POST_CR22_EX06_BLOCKER_SELECTION_COUNT_NOT_24_REF: Final = "protocol_selection_row_count_required_not_24"
P7_R54_AHR_POST_CR22_EX06_BLOCKER_BODY_QUOTE_ALLOWED_REF: Final = "protocol_body_quotation_allowed_must_be_false"
P7_R54_AHR_POST_CR22_EX06_BLOCKER_REVIEWER_NOTES_EXPORT_ALLOWED_REF: Final = (
    "protocol_reviewer_notes_export_allowed_must_be_false"
)
P7_R54_AHR_POST_CR22_EX06_BLOCKER_QUESTION_TEXT_ALLOWED_REF: Final = "protocol_question_text_allowed_must_be_false"
P7_R54_AHR_POST_CR22_EX06_BLOCKER_DRAFT_QUESTION_TEXT_ALLOWED_REF: Final = (
    "protocol_draft_question_text_allowed_must_be_false"
)
P7_R54_AHR_POST_CR22_EX06_BLOCKER_FREE_TEXT_ALLOWED_REF: Final = "protocol_reviewer_free_text_allowed_must_be_false"

P7_R54_AHR_POST_CR22_EX07_BLOCKER_EX06_PROTOCOL_NOT_READY_REF: Final = "ex06_execution_protocol_not_ready"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_EX06_NEXT_REQUIRED_STEP_NOT_EX07_REF: Final = "ex06_next_required_step_not_ex07"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_OPERATION_RECEIPT_REF_MISSING_REF: Final = "operation_receipt_ref_missing"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_OPERATION_RECEIPT_REF_PATH_SHAPE_REF: Final = (
    "operation_receipt_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWER_PERSON_REF_MISSING_REF: Final = "reviewer_person_ref_missing"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWER_PERSON_REF_PATH_SHAPE_REF: Final = (
    "reviewer_person_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWER_PERSON_REF_MISMATCH_REF: Final = "reviewer_person_ref_mismatch"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_READ_RECEIPT_MISSING_REF: Final = (
    "reviewer_local_only_read_receipt_missing"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_STARTED_BUCKET_REF_MISSING_REF: Final = (
    "review_started_at_bucket_ref_missing"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_STARTED_BUCKET_REF_PATH_SHAPE_REF: Final = (
    "review_started_at_bucket_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_COMPLETED_BUCKET_REF_MISSING_REF: Final = (
    "review_completed_at_bucket_ref_missing"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_COMPLETED_BUCKET_REF_PATH_SHAPE_REF: Final = (
    "review_completed_at_bucket_ref_must_be_bodyfree_ref_not_path"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWED_CASE_COUNT_NOT_24_REF: Final = "reviewed_case_count_not_24"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_SELECTION_ROW_COUNT_NOT_24_REF: Final = "selection_row_count_not_24"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_LOCAL_ONLY_NOT_TRUE_REF: Final = "local_only_must_be_true"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_MUST_NOT_EXPORT_NOT_TRUE_REF: Final = "must_not_export_must_be_true"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_SELECTION_ONLY_NOT_TRUE_REF: Final = "selection_only_must_be_true"
P7_R54_AHR_POST_CR22_EX07_BLOCKER_ACTUAL_SOURCE_REF_NOT_ALLOWED_REF: Final = (
    "operation_receipt_actual_source_ref_not_allowed"
)
P7_R54_AHR_POST_CR22_EX07_BLOCKER_FORBIDDEN_BODY_PATH_HASH_OR_QUESTION_FLAG_REF: Final = (
    "operation_receipt_forbidden_body_path_hash_or_question_flag"
)

P7_R54_AHR_POST_CR22_EX06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex05_schema_version",
    "ex05_material_ref",
    "ex05_next_required_step",
    "ex05_reviewer_boundary_ready",
    "ex05_reviewer_person_ref",
    "ex05_reviewer_person_confirmed",
    "ex05_selection_only_form_frozen",
    "ex05_selection_row_count_required",
    "execution_protocol_status_ref",
    "execution_protocol_allowed_status_refs",
    "execution_protocol_ready",
    "execution_protocol_reason_refs",
    "execution_protocol_blocker_refs",
    "execution_protocol_blocker_ref_count",
    "execution_protocol_step_refs",
    "execution_protocol_step_ref_count",
    "protocol_requires_local_only",
    "protocol_requires_must_not_export",
    "protocol_requires_selection_only",
    "required_reviewed_case_count",
    "required_selection_row_count",
    "required_reviewed_case_count_is_24",
    "required_selection_row_count_is_24",
    "reviewer_must_not_quote_body",
    "reviewer_notes_must_not_export",
    "question_text_must_not_materialize",
    "draft_question_text_must_not_materialize",
    "reviewer_free_text_must_not_export",
    "body_full_packet_must_remain_local_only",
    "operation_receipt_required_next",
    "operation_receipt_required_actual_source_ref",
    "actual_operation_receipt_intaked_here",
    "operation_receipt_ref_present",
    "reviewer_local_only_read_receipt_present",
    "actual_human_review_executed_by_person",
    "reviewed_case_count",
    "selection_row_count",
    "actual_human_review_execution_protocol_bodyfree_only",
    "actual_human_review_execution_protocol_does_not_run_review_here",
    "actual_human_review_execution_protocol_does_not_create_selection_rows_here",
    "actual_human_review_execution_protocol_does_not_create_rating_rows_here",
    "actual_human_review_execution_protocol_does_not_create_question_observation_rows_here",
    "actual_human_review_execution_protocol_does_not_create_disposal_receipt_here",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "reviewer_free_text_allowed",
    "reviewer_notes_export_allowed",
    "question_text_allowed",
    "draft_question_text_allowed",
    "body_quotation_allowed",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "packet_content_included",
    "body_full_packet_content_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "p8_implementation_spec_finalized_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_CR22_EX07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex06_schema_version",
    "ex06_material_ref",
    "ex06_next_required_step",
    "ex06_execution_protocol_ready",
    "ex06_reviewer_person_ref",
    "ex06_required_reviewed_case_count",
    "ex06_required_selection_row_count",
    "operation_receipt_status_ref",
    "operation_receipt_allowed_status_refs",
    "operation_receipt_accepted",
    "operation_receipt_reason_refs",
    "operation_receipt_blocker_refs",
    "operation_receipt_blocker_ref_count",
    "operation_receipt_ref",
    "operation_receipt_ref_present",
    "operation_receipt_ref_is_bodyfree_ref",
    "operation_receipt_ref_has_local_path_shape",
    "reviewer_person_ref",
    "reviewer_person_ref_present",
    "reviewer_person_ref_is_bodyfree_ref",
    "reviewer_person_ref_has_local_path_shape",
    "reviewer_person_ref_matches_ex06",
    "reviewer_local_only_read_receipt_present",
    "review_started_at_bucket_ref",
    "review_started_at_bucket_ref_present",
    "review_started_at_bucket_ref_is_bodyfree_ref",
    "review_started_at_bucket_ref_has_local_path_shape",
    "review_completed_at_bucket_ref",
    "review_completed_at_bucket_ref_present",
    "review_completed_at_bucket_ref_is_bodyfree_ref",
    "review_completed_at_bucket_ref_has_local_path_shape",
    "reviewed_case_count",
    "required_reviewed_case_count",
    "reviewed_case_count_is_24",
    "selection_row_count",
    "required_selection_row_count",
    "selection_row_count_is_24",
    "local_only",
    "must_not_export",
    "selection_only",
    "actual_source_ref",
    "actual_source_allowed_ref",
    "actual_source_guard_passed",
    "operation_receipt_bodyfree_only",
    "operation_receipt_intaked_here",
    "operation_receipt_confirms_actual_person_local_only_review",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "operation_receipt_does_not_create_selection_rows_here",
    "operation_receipt_does_not_materialize_rating_rows_here",
    "operation_receipt_does_not_materialize_question_observation_rows_here",
    "operation_receipt_does_not_create_disposal_receipt_here",
    "operation_receipt_does_not_complete_evidence_here",
    "operation_receipt_does_not_export_body_or_notes",
    "operation_receipt_forbidden_body_path_hash_or_question_flag_requested",
    "actual_selection_rows_created_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "raw_input_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_body_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "packet_content_included",
    "body_full_packet_content_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
    "p8_implementation_spec_finalized_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _ex06_protocol_fields(
    *,
    ex05_reviewer_boundary_ready: bool,
    ex05_next_required_step: Any,
    local_only: bool,
    must_not_export: bool,
    selection_only: bool,
    required_reviewed_case_count: Any,
    required_selection_row_count: Any,
    body_quotation_allowed: bool,
    reviewer_notes_export_allowed: bool,
    question_text_allowed: bool,
    draft_question_text_allowed: bool,
    reviewer_free_text_allowed: bool,
) -> dict[str, Any]:
    reviewed_required = _int_value_or_zero(required_reviewed_case_count)
    selection_required = _int_value_or_zero(required_selection_row_count)
    blockers: list[str] = []
    if not ex05_reviewer_boundary_ready:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_EX05_REVIEWER_BOUNDARY_NOT_READY_REF)
    if ex05_next_required_step != P7_R54_AHR_POST_CR22_EX06_STEP_REF:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_EX05_NEXT_REQUIRED_STEP_NOT_EX06_REF)
    if local_only is not True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_LOCAL_ONLY_NOT_TRUE_REF)
    if must_not_export is not True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_MUST_NOT_EXPORT_NOT_TRUE_REF)
    if selection_only is not True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_SELECTION_ONLY_NOT_TRUE_REF)
    if reviewed_required != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_REVIEWED_COUNT_NOT_24_REF)
    if selection_required != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_SELECTION_COUNT_NOT_24_REF)
    if body_quotation_allowed is True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_BODY_QUOTE_ALLOWED_REF)
    if reviewer_notes_export_allowed is True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_REVIEWER_NOTES_EXPORT_ALLOWED_REF)
    if question_text_allowed is True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_QUESTION_TEXT_ALLOWED_REF)
    if draft_question_text_allowed is True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_DRAFT_QUESTION_TEXT_ALLOWED_REF)
    if reviewer_free_text_allowed is True:
        blockers.append(P7_R54_AHR_POST_CR22_EX06_BLOCKER_FREE_TEXT_ALLOWED_REF)
    ready = not blockers
    return {
        "execution_protocol_status_ref": (
            P7_R54_AHR_POST_CR22_EX06_PROTOCOL_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX06_PROTOCOL_BLOCKED_STATUS_REF
        ),
        "execution_protocol_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX06_ALLOWED_PROTOCOL_STATUS_REFS),
        "execution_protocol_ready": ready,
        "execution_protocol_reason_refs": [P7_R54_AHR_POST_CR22_EX06_READY_REASON_REF] if ready else [],
        "execution_protocol_blocker_refs": _dedupe_refs(blockers),
        "execution_protocol_blocker_ref_count": len(_dedupe_refs(blockers)),
        "execution_protocol_step_refs": list(P7_R54_AHR_POST_CR22_EX06_PROTOCOL_STEP_REFS),
        "execution_protocol_step_ref_count": len(P7_R54_AHR_POST_CR22_EX06_PROTOCOL_STEP_REFS),
        "protocol_requires_local_only": bool(local_only),
        "protocol_requires_must_not_export": bool(must_not_export),
        "protocol_requires_selection_only": bool(selection_only),
        "required_reviewed_case_count": reviewed_required,
        "required_selection_row_count": selection_required,
        "required_reviewed_case_count_is_24": reviewed_required == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "required_selection_row_count_is_24": selection_required == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "reviewer_must_not_quote_body": body_quotation_allowed is False,
        "reviewer_notes_must_not_export": reviewer_notes_export_allowed is False,
        "question_text_must_not_materialize": question_text_allowed is False,
        "draft_question_text_must_not_materialize": draft_question_text_allowed is False,
        "reviewer_free_text_must_not_export": reviewer_free_text_allowed is False,
    }


def build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol(
    *,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    selection_only: bool = True,
    required_reviewed_case_count: Any = P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
    required_selection_row_count: Any = P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
    body_quotation_allowed: bool = False,
    reviewer_notes_export_allowed: bool = False,
    question_text_allowed: bool = False,
    draft_question_text_allowed: bool = False,
    reviewer_free_text_allowed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX06 body-free actual local-only human review execution protocol material."""

    ex05 = (
        reviewer_person_boundary_selection_only_form_freeze
        or build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
            reviewer_person_ref=P7_R54_AHR_POST_CR22_EX05_DEFAULT_REVIEWER_PERSON_REF,
            reviewer_person_confirmed=True,
        )
    )
    session_id = _safe_review_session_id(review_session_id or ex05.get("review_session_id"))
    fields = _ex06_protocol_fields(
        ex05_reviewer_boundary_ready=ex05.get("reviewer_boundary_ready") is True,
        ex05_next_required_step=ex05.get("next_required_step"),
        local_only=local_only,
        must_not_export=must_not_export,
        selection_only=selection_only,
        required_reviewed_case_count=required_reviewed_case_count,
        required_selection_row_count=required_selection_row_count,
        body_quotation_allowed=body_quotation_allowed,
        reviewer_notes_export_allowed=reviewer_notes_export_allowed,
        question_text_allowed=question_text_allowed,
        draft_question_text_allowed=draft_question_text_allowed,
        reviewer_free_text_allowed=reviewer_free_text_allowed,
    )
    ready = fields["execution_protocol_ready"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX06_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_EXECUTION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX06_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_CR22_EX06_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex05_schema_version": ex05.get("schema_version"),
        "ex05_material_ref": ex05.get("material_id"),
        "ex05_next_required_step": ex05.get("next_required_step"),
        "ex05_reviewer_boundary_ready": ex05.get("reviewer_boundary_ready") is True,
        "ex05_reviewer_person_ref": ex05.get("reviewer_person_ref"),
        "ex05_reviewer_person_confirmed": ex05.get("reviewer_person_confirmed") is True,
        "ex05_selection_only_form_frozen": ex05.get("selection_only_form_frozen") is True,
        "ex05_selection_row_count_required": _int_value_or_zero(ex05.get("selection_row_count_required")),
        **fields,
        "body_full_packet_must_remain_local_only": True,
        "operation_receipt_required_next": True,
        "operation_receipt_required_actual_source_ref": P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF,
        "actual_operation_receipt_intaked_here": False,
        "operation_receipt_ref_present": False,
        "reviewer_local_only_read_receipt_present": False,
        "actual_human_review_executed_by_person": False,
        "reviewed_case_count": 0,
        "selection_row_count": 0,
        "actual_human_review_execution_protocol_bodyfree_only": True,
        "actual_human_review_execution_protocol_does_not_run_review_here": True,
        "actual_human_review_execution_protocol_does_not_create_selection_rows_here": True,
        "actual_human_review_execution_protocol_does_not_create_rating_rows_here": True,
        "actual_human_review_execution_protocol_does_not_create_question_observation_rows_here": True,
        "actual_human_review_execution_protocol_does_not_create_disposal_receipt_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "reviewer_free_text_allowed": bool(reviewer_free_text_allowed),
        "reviewer_notes_export_allowed": bool(reviewer_notes_export_allowed),
        "question_text_allowed": bool(question_text_allowed),
        "draft_question_text_allowed": bool(draft_question_text_allowed),
        "body_quotation_allowed": bool(body_quotation_allowed),
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "packet_content_included": False,
        "body_full_packet_content_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "p8_implementation_spec_finalized_here": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX06_IMPLEMENTED_STEPS if ready else tuple(ex05.get("implemented_steps") or ())
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX06_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ex05.get("not_yet_implemented_steps") or ())
        ),
        "next_required_step": (
            P7_R54_AHR_POST_CR22_EX07_STEP_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX06_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX06 actual local-only review execution protocol",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX06_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_EXECUTION_PROTOCOL_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX06_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX06 actual local-only review execution protocol",
    )
    if data.get("ex05_schema_version") != P7_R54_AHR_POST_CR22_EX05_REVIEWER_PERSON_BOUNDARY_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostCR22-EX06 EX05 schema version changed")
    expected = _ex06_protocol_fields(
        ex05_reviewer_boundary_ready=data.get("ex05_reviewer_boundary_ready") is True,
        ex05_next_required_step=data.get("ex05_next_required_step"),
        local_only=data.get("protocol_requires_local_only") is True,
        must_not_export=data.get("protocol_requires_must_not_export") is True,
        selection_only=data.get("protocol_requires_selection_only") is True,
        required_reviewed_case_count=data.get("required_reviewed_case_count"),
        required_selection_row_count=data.get("required_selection_row_count"),
        body_quotation_allowed=data.get("body_quotation_allowed") is True,
        reviewer_notes_export_allowed=data.get("reviewer_notes_export_allowed") is True,
        question_text_allowed=data.get("question_text_allowed") is True,
        draft_question_text_allowed=data.get("draft_question_text_allowed") is True,
        reviewer_free_text_allowed=data.get("reviewer_free_text_allowed") is True,
    )
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX06 {key} changed")
    blockers = list(data.get("execution_protocol_blocker_refs") or [])
    ready = not blockers
    if data.get("execution_protocol_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX06 blocker count changed")
    if data.get("execution_protocol_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX06 ready flag changed")
    expected_status = (
        P7_R54_AHR_POST_CR22_EX06_PROTOCOL_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX06_PROTOCOL_BLOCKED_STATUS_REF
    )
    if data.get("execution_protocol_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX06 status changed")
    if tuple(data.get("execution_protocol_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX06_ALLOWED_PROTOCOL_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX06 allowed status refs changed")
    if tuple(data.get("execution_protocol_step_refs") or ()) != P7_R54_AHR_POST_CR22_EX06_PROTOCOL_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX06 protocol step refs changed")
    if data.get("execution_protocol_step_ref_count") != len(P7_R54_AHR_POST_CR22_EX06_PROTOCOL_STEP_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX06 protocol step count changed")
    if ready:
        if data.get("ex05_next_required_step") != P7_R54_AHR_POST_CR22_EX06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX06 must follow ready EX05")
        if data.get("execution_protocol_reason_refs") != [P7_R54_AHR_POST_CR22_EX06_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX06 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX06_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX06 next step changed")
    else:
        if data.get("execution_protocol_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX06 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX06_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX06 blocked next step changed")
    for key in (
        "operation_receipt_required_next",
        "actual_human_review_execution_protocol_bodyfree_only",
        "actual_human_review_execution_protocol_does_not_run_review_here",
        "actual_human_review_execution_protocol_does_not_create_selection_rows_here",
        "actual_human_review_execution_protocol_does_not_create_rating_rows_here",
        "actual_human_review_execution_protocol_does_not_create_question_observation_rows_here",
        "actual_human_review_execution_protocol_does_not_create_disposal_receipt_here",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "current_cr_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX06 required true field changed: {key}")
    for key in (
        "actual_operation_receipt_intaked_here",
        "operation_receipt_ref_present",
        "reviewer_local_only_read_receipt_present",
        "actual_human_review_executed_by_person",
        "reviewer_free_text_included",
        "reviewer_notes_body_included",
        "question_text_included",
        "draft_question_text_included",
        "packet_content_included",
        "body_full_packet_content_included",
        "local_absolute_path_included",
        "body_hash_included",
        "terminal_output_body_included",
        "p8_implementation_spec_finalized_here",
        "actual_human_review_complete",
        "actual_review_evidence_complete",
        "actual_selection_rows_created_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX06 required false field changed: {key}")
    if data.get("reviewed_case_count") != 0 or data.get("selection_row_count") != 0:
        raise ValueError("P7-R54-AHR-PostCR22-EX06 must not report actual reviewed rows")
    if data.get("operation_receipt_required_actual_source_ref") != P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX06 operation receipt source ref changed")
    return True


def _ex07_operation_receipt_fields(
    *,
    ex06_execution_protocol_ready: bool,
    ex06_next_required_step: Any,
    ex06_reviewer_person_ref: Any,
    operation_receipt_ref: Any,
    reviewer_person_ref: Any,
    reviewer_local_only_read_receipt_present: bool,
    review_started_at_bucket_ref: Any,
    review_completed_at_bucket_ref: Any,
    reviewed_case_count: Any,
    selection_row_count: Any,
    local_only: bool,
    must_not_export: bool,
    selection_only: bool,
    actual_source_ref: Any,
    raw_input_included: bool,
    returned_emlis_body_included: bool,
    history_surface_included: bool,
    comment_text_body_included: bool,
    reviewer_free_text_included: bool,
    reviewer_notes_body_included: bool,
    question_text_included: bool,
    draft_question_text_included: bool,
    packet_content_included: bool,
    body_full_packet_content_included: bool,
    local_absolute_path_included: bool,
    body_hash_included: bool,
    terminal_output_body_included: bool,
    stdout_body_included: bool,
    stderr_body_included: bool,
    traceback_body_included: bool,
) -> dict[str, Any]:
    receipt_ref, receipt_has_path = _bodyfree_ref_or_rejected(
        operation_receipt_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX07_REJECTED_OPERATION_RECEIPT_PATH_SHAPE_REF,
        max_length=260,
    )
    reviewer_ref, reviewer_has_path = _bodyfree_ref_or_rejected(
        reviewer_person_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX05_REJECTED_REVIEWER_PERSON_PATH_SHAPE_REF,
        max_length=220,
    )
    started_ref, started_has_path = _bodyfree_ref_or_rejected(
        review_started_at_bucket_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX07_REJECTED_BUCKET_PATH_SHAPE_REF,
        max_length=220,
    )
    completed_ref, completed_has_path = _bodyfree_ref_or_rejected(
        review_completed_at_bucket_ref,
        rejected_ref=P7_R54_AHR_POST_CR22_EX07_REJECTED_BUCKET_PATH_SHAPE_REF,
        max_length=220,
    )
    reviewed_count = _int_value_or_zero(reviewed_case_count)
    selection_count = _int_value_or_zero(selection_row_count)
    source_ref = clean_identifier(actual_source_ref, default="", max_length=220)
    forbidden_flag_requested = any(
        (
            raw_input_included,
            returned_emlis_body_included,
            history_surface_included,
            comment_text_body_included,
            reviewer_free_text_included,
            reviewer_notes_body_included,
            question_text_included,
            draft_question_text_included,
            packet_content_included,
            body_full_packet_content_included,
            local_absolute_path_included,
            body_hash_included,
            terminal_output_body_included,
            stdout_body_included,
            stderr_body_included,
            traceback_body_included,
        )
    )
    reviewers_match = reviewer_ref == clean_identifier(ex06_reviewer_person_ref, default="", max_length=220)
    blockers: list[str] = []
    if not ex06_execution_protocol_ready:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_EX06_PROTOCOL_NOT_READY_REF)
    if ex06_next_required_step != P7_R54_AHR_POST_CR22_EX07_STEP_REF:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_EX06_NEXT_REQUIRED_STEP_NOT_EX07_REF)
    if not receipt_ref:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_OPERATION_RECEIPT_REF_MISSING_REF)
    if receipt_has_path:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_OPERATION_RECEIPT_REF_PATH_SHAPE_REF)
    if not reviewer_ref:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWER_PERSON_REF_MISSING_REF)
    if reviewer_has_path:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWER_PERSON_REF_PATH_SHAPE_REF)
    if reviewer_ref and not reviewer_has_path and not reviewers_match:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWER_PERSON_REF_MISMATCH_REF)
    if reviewer_local_only_read_receipt_present is not True:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_READ_RECEIPT_MISSING_REF)
    if not started_ref:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_STARTED_BUCKET_REF_MISSING_REF)
    if started_has_path:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_STARTED_BUCKET_REF_PATH_SHAPE_REF)
    if not completed_ref:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_COMPLETED_BUCKET_REF_MISSING_REF)
    if completed_has_path:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_COMPLETED_BUCKET_REF_PATH_SHAPE_REF)
    if reviewed_count != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_REVIEWED_CASE_COUNT_NOT_24_REF)
    if selection_count != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_SELECTION_ROW_COUNT_NOT_24_REF)
    if local_only is not True:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_LOCAL_ONLY_NOT_TRUE_REF)
    if must_not_export is not True:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_MUST_NOT_EXPORT_NOT_TRUE_REF)
    if selection_only is not True:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_SELECTION_ONLY_NOT_TRUE_REF)
    if source_ref != P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_ACTUAL_SOURCE_REF_NOT_ALLOWED_REF)
    if forbidden_flag_requested:
        blockers.append(P7_R54_AHR_POST_CR22_EX07_BLOCKER_FORBIDDEN_BODY_PATH_HASH_OR_QUESTION_FLAG_REF)
    blockers = _dedupe_refs(blockers)
    accepted = not blockers
    return {
        "operation_receipt_status_ref": (
            P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_ACCEPTED_STATUS_REF
            if accepted
            else P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_BLOCKED_STATUS_REF
        ),
        "operation_receipt_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX07_ALLOWED_OPERATION_RECEIPT_STATUS_REFS),
        "operation_receipt_accepted": accepted,
        "operation_receipt_reason_refs": [P7_R54_AHR_POST_CR22_EX07_READY_REASON_REF] if accepted else [],
        "operation_receipt_blocker_refs": blockers,
        "operation_receipt_blocker_ref_count": len(blockers),
        "operation_receipt_ref": receipt_ref,
        "operation_receipt_ref_present": bool(receipt_ref) and not receipt_has_path,
        "operation_receipt_ref_is_bodyfree_ref": bool(receipt_ref) and not receipt_has_path,
        "operation_receipt_ref_has_local_path_shape": receipt_has_path,
        "reviewer_person_ref": reviewer_ref,
        "reviewer_person_ref_present": bool(reviewer_ref) and not reviewer_has_path,
        "reviewer_person_ref_is_bodyfree_ref": bool(reviewer_ref) and not reviewer_has_path,
        "reviewer_person_ref_has_local_path_shape": reviewer_has_path,
        "reviewer_person_ref_matches_ex06": reviewers_match and bool(reviewer_ref) and not reviewer_has_path,
        "reviewer_local_only_read_receipt_present": reviewer_local_only_read_receipt_present is True,
        "review_started_at_bucket_ref": started_ref,
        "review_started_at_bucket_ref_present": bool(started_ref) and not started_has_path,
        "review_started_at_bucket_ref_is_bodyfree_ref": bool(started_ref) and not started_has_path,
        "review_started_at_bucket_ref_has_local_path_shape": started_has_path,
        "review_completed_at_bucket_ref": completed_ref,
        "review_completed_at_bucket_ref_present": bool(completed_ref) and not completed_has_path,
        "review_completed_at_bucket_ref_is_bodyfree_ref": bool(completed_ref) and not completed_has_path,
        "review_completed_at_bucket_ref_has_local_path_shape": completed_has_path,
        "reviewed_case_count": reviewed_count,
        "required_reviewed_case_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "reviewed_case_count_is_24": reviewed_count == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "selection_row_count": selection_count,
        "required_selection_row_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "selection_row_count_is_24": selection_count == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "local_only": local_only is True,
        "must_not_export": must_not_export is True,
        "selection_only": selection_only is True,
        "actual_source_ref": source_ref,
        "actual_source_allowed_ref": P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF,
        "actual_source_guard_passed": source_ref == P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF,
        "operation_receipt_bodyfree_only": True,
        "operation_receipt_intaked_here": accepted,
        "operation_receipt_confirms_actual_person_local_only_review": accepted,
        "actual_human_review_executed_by_person": accepted,
        "operation_receipt_forbidden_body_path_hash_or_question_flag_requested": forbidden_flag_requested,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_surface_included": False,
        "comment_text_body_included": False,
        "reviewer_free_text_included": False,
        "reviewer_notes_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "packet_content_included": False,
        "body_full_packet_content_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
    }


def build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
    *,
    actual_local_only_human_review_execution_protocol: Mapping[str, Any] | None = None,
    operation_receipt_ref: Any = "",
    reviewer_person_ref: Any = "",
    reviewer_local_only_read_receipt_present: bool = False,
    review_started_at_bucket_ref: Any = "",
    review_completed_at_bucket_ref: Any = "",
    reviewed_case_count: Any = 0,
    selection_row_count: Any = 0,
    local_only: bool = True,
    must_not_export: bool = True,
    selection_only: bool = True,
    actual_source_ref: Any = P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF,
    raw_input_included: bool = False,
    returned_emlis_body_included: bool = False,
    history_surface_included: bool = False,
    comment_text_body_included: bool = False,
    reviewer_free_text_included: bool = False,
    reviewer_notes_body_included: bool = False,
    question_text_included: bool = False,
    draft_question_text_included: bool = False,
    packet_content_included: bool = False,
    body_full_packet_content_included: bool = False,
    local_absolute_path_included: bool = False,
    body_hash_included: bool = False,
    terminal_output_body_included: bool = False,
    stdout_body_included: bool = False,
    stderr_body_included: bool = False,
    traceback_body_included: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX07 body-free actual operation receipt intake material."""

    ex06 = (
        actual_local_only_human_review_execution_protocol
        or build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol()
    )
    session_id = _safe_review_session_id(review_session_id or ex06.get("review_session_id"))
    fields = _ex07_operation_receipt_fields(
        ex06_execution_protocol_ready=ex06.get("execution_protocol_ready") is True,
        ex06_next_required_step=ex06.get("next_required_step"),
        ex06_reviewer_person_ref=ex06.get("ex05_reviewer_person_ref"),
        operation_receipt_ref=operation_receipt_ref,
        reviewer_person_ref=reviewer_person_ref,
        reviewer_local_only_read_receipt_present=reviewer_local_only_read_receipt_present,
        review_started_at_bucket_ref=review_started_at_bucket_ref,
        review_completed_at_bucket_ref=review_completed_at_bucket_ref,
        reviewed_case_count=reviewed_case_count,
        selection_row_count=selection_row_count,
        local_only=local_only,
        must_not_export=must_not_export,
        selection_only=selection_only,
        actual_source_ref=actual_source_ref,
        raw_input_included=raw_input_included,
        returned_emlis_body_included=returned_emlis_body_included,
        history_surface_included=history_surface_included,
        comment_text_body_included=comment_text_body_included,
        reviewer_free_text_included=reviewer_free_text_included,
        reviewer_notes_body_included=reviewer_notes_body_included,
        question_text_included=question_text_included,
        draft_question_text_included=draft_question_text_included,
        packet_content_included=packet_content_included,
        body_full_packet_content_included=body_full_packet_content_included,
        local_absolute_path_included=local_absolute_path_included,
        body_hash_included=body_hash_included,
        terminal_output_body_included=terminal_output_body_included,
        stdout_body_included=stdout_body_included,
        stderr_body_included=stderr_body_included,
        traceback_body_included=traceback_body_included,
    )
    accepted = fields["operation_receipt_accepted"] is True
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX07_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX07_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_CR22_EX07_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex06_schema_version": ex06.get("schema_version"),
        "ex06_material_ref": ex06.get("material_id"),
        "ex06_next_required_step": ex06.get("next_required_step"),
        "ex06_execution_protocol_ready": ex06.get("execution_protocol_ready") is True,
        "ex06_reviewer_person_ref": ex06.get("ex05_reviewer_person_ref"),
        "ex06_required_reviewed_case_count": _int_value_or_zero(ex06.get("required_reviewed_case_count")),
        "ex06_required_selection_row_count": _int_value_or_zero(ex06.get("required_selection_row_count")),
        **fields,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
        "actual_review_evidence_complete": False,
        "operation_receipt_does_not_create_selection_rows_here": True,
        "operation_receipt_does_not_materialize_rating_rows_here": True,
        "operation_receipt_does_not_materialize_question_observation_rows_here": True,
        "operation_receipt_does_not_create_disposal_receipt_here": True,
        "operation_receipt_does_not_complete_evidence_here": True,
        "operation_receipt_does_not_export_body_or_notes": True,
        "actual_selection_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "p8_implementation_spec_finalized_here": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX07_IMPLEMENTED_STEPS if accepted else tuple(ex06.get("implemented_steps") or ())
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_CR22_EX07_NOT_YET_IMPLEMENTED_STEPS if accepted else tuple(ex06.get("not_yet_implemented_steps") or ())
        ),
        "next_required_step": (
            P7_R54_AHR_POST_CR22_EX08_STEP_REF
            if accepted
            else P7_R54_AHR_POST_CR22_EX07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_CR22_EX07_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX07 actual operation receipt intake",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX07_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX07_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX07 actual operation receipt intake",
    )
    if data.get("ex06_schema_version") != P7_R54_AHR_POST_CR22_EX06_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_EXECUTION_PROTOCOL_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 EX06 schema version changed")
    expected = _ex07_operation_receipt_fields(
        ex06_execution_protocol_ready=data.get("ex06_execution_protocol_ready") is True,
        ex06_next_required_step=data.get("ex06_next_required_step"),
        ex06_reviewer_person_ref=data.get("ex06_reviewer_person_ref"),
        operation_receipt_ref=data.get("operation_receipt_ref"),
        reviewer_person_ref=data.get("reviewer_person_ref"),
        reviewer_local_only_read_receipt_present=data.get("reviewer_local_only_read_receipt_present") is True,
        review_started_at_bucket_ref=data.get("review_started_at_bucket_ref"),
        review_completed_at_bucket_ref=data.get("review_completed_at_bucket_ref"),
        reviewed_case_count=data.get("reviewed_case_count"),
        selection_row_count=data.get("selection_row_count"),
        local_only=data.get("local_only") is True,
        must_not_export=data.get("must_not_export") is True,
        selection_only=data.get("selection_only") is True,
        actual_source_ref=data.get("actual_source_ref"),
        raw_input_included=(
            data.get("raw_input_included") is True
            or data.get("operation_receipt_forbidden_body_path_hash_or_question_flag_requested") is True
        ),
        returned_emlis_body_included=data.get("returned_emlis_body_included") is True,
        history_surface_included=data.get("history_surface_included") is True,
        comment_text_body_included=data.get("comment_text_body_included") is True,
        reviewer_free_text_included=data.get("reviewer_free_text_included") is True,
        reviewer_notes_body_included=data.get("reviewer_notes_body_included") is True,
        question_text_included=data.get("question_text_included") is True,
        draft_question_text_included=data.get("draft_question_text_included") is True,
        packet_content_included=data.get("packet_content_included") is True,
        body_full_packet_content_included=data.get("body_full_packet_content_included") is True,
        local_absolute_path_included=data.get("local_absolute_path_included") is True,
        body_hash_included=data.get("body_hash_included") is True,
        terminal_output_body_included=data.get("terminal_output_body_included") is True,
        stdout_body_included=data.get("stdout_body_included") is True,
        stderr_body_included=data.get("stderr_body_included") is True,
        traceback_body_included=data.get("traceback_body_included") is True,
    )
    for key, expected_value in expected.items():
        if data.get(key) != expected_value:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX07 {key} changed")
    blockers = list(data.get("operation_receipt_blocker_refs") or [])
    accepted = not blockers
    if data.get("operation_receipt_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX07 blocker count changed")
    if data.get("operation_receipt_accepted") is not accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 accepted flag changed")
    expected_status = (
        P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_ACCEPTED_STATUS_REF
        if accepted
        else P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_BLOCKED_STATUS_REF
    )
    if data.get("operation_receipt_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 status changed")
    if tuple(data.get("operation_receipt_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX07_ALLOWED_OPERATION_RECEIPT_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 allowed status refs changed")
    if accepted:
        if data.get("ex06_next_required_step") != P7_R54_AHR_POST_CR22_EX07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX07 must follow ready EX06")
        if data.get("operation_receipt_reason_refs") != [P7_R54_AHR_POST_CR22_EX07_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX07 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX07_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX07 next step changed")
    else:
        if data.get("operation_receipt_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX07 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX07_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX07 blocked next step changed")
    for key in (
        "operation_receipt_bodyfree_only",
        "operation_receipt_does_not_create_selection_rows_here",
        "operation_receipt_does_not_materialize_rating_rows_here",
        "operation_receipt_does_not_materialize_question_observation_rows_here",
        "operation_receipt_does_not_create_disposal_receipt_here",
        "operation_receipt_does_not_complete_evidence_here",
        "operation_receipt_does_not_export_body_or_notes",
        "current_cr_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX07 required true field changed: {key}")
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "actual_review_evidence_complete",
        "actual_selection_rows_created_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "raw_input_included",
        "returned_emlis_body_included",
        "history_surface_included",
        "comment_text_body_included",
        "reviewer_free_text_included",
        "reviewer_notes_body_included",
        "question_text_included",
        "draft_question_text_included",
        "packet_content_included",
        "body_full_packet_content_included",
        "local_absolute_path_included",
        "body_hash_included",
        "terminal_output_body_included",
        "stdout_body_included",
        "stderr_body_included",
        "traceback_body_included",
        "p8_implementation_spec_finalized_here",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX07 required false field changed: {key}")
    if data.get("operation_receipt_intaked_here") is not accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 intake flag changed")
    if data.get("operation_receipt_confirms_actual_person_local_only_review") is not accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 actual person receipt confirmation changed")
    if data.get("actual_human_review_executed_by_person") is not accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 actual human review executed flag changed")
    if data.get("actual_source_ref") != P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF and accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX07 accepted wrong source")
    return True

# Alias names for the detailed-design wording of EX04 through EX07.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_bodyfree(
    *,
    local_only_preflight_explicit_allow_packet_request_boundary: Mapping[str, Any] | None = None,
    packet_generation_receipt_ref: Any = "",
    packet_case_count: Any = 0,
    packet_completeness_scan_ref: Any = "",
    export_denylist_scan_ref: Any = "",
    packet_completeness_passed: bool = False,
    export_denylist_scan_passed: bool = False,
    packet_body_exported: bool = False,
    packet_materialized_for_review_acknowledged_by_bodyfree_receipt: bool = True,
    actual_source_ref: Any = P7_R54_AHR_POST_CR22_EX04_ALLOWED_ACTUAL_SOURCE_REF,
    packet_content_included: bool = False,
    body_full_packet_content_included: bool = False,
    local_absolute_path_included: bool = False,
    body_hash_included: bool = False,
    terminal_output_body_included: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake(
        local_only_preflight_explicit_allow_packet_request_boundary=(
            local_only_preflight_explicit_allow_packet_request_boundary
        ),
        packet_generation_receipt_ref=packet_generation_receipt_ref,
        packet_case_count=packet_case_count,
        packet_completeness_scan_ref=packet_completeness_scan_ref,
        export_denylist_scan_ref=export_denylist_scan_ref,
        packet_completeness_passed=packet_completeness_passed,
        export_denylist_scan_passed=export_denylist_scan_passed,
        packet_body_exported=packet_body_exported,
        packet_materialized_for_review_acknowledged_by_bodyfree_receipt=(
            packet_materialized_for_review_acknowledged_by_bodyfree_receipt
        ),
        actual_source_ref=actual_source_ref,
        packet_content_included=packet_content_included,
        body_full_packet_content_included=body_full_packet_content_included,
        local_absolute_path_included=local_absolute_path_included,
        body_hash_included=body_hash_included,
        terminal_output_body_included=terminal_output_body_included,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex04_local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake_contract(
        data
    )


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_reviewer_person_boundary_selection_only_form_freeze_bodyfree(
    *,
    local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake: Mapping[str, Any]
    | None = None,
    reviewer_person_ref: Any = "",
    reviewer_is_person: bool = True,
    reviewer_person_confirmed: bool = False,
    selection_row_count_required: Any = P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
    free_text_allowed: bool = False,
    reviewer_notes_export_allowed: bool = False,
    question_text_allowed: bool = False,
    draft_question_text_allowed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze(
        local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake=(
            local_body_full_packet_generation_receipt_completeness_export_denylist_bodyfree_intake
        ),
        reviewer_person_ref=reviewer_person_ref,
        reviewer_is_person=reviewer_is_person,
        reviewer_person_confirmed=reviewer_person_confirmed,
        selection_row_count_required=selection_row_count_required,
        free_text_allowed=free_text_allowed,
        reviewer_notes_export_allowed=reviewer_notes_export_allowed,
        question_text_allowed=question_text_allowed,
        draft_question_text_allowed=draft_question_text_allowed,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_reviewer_person_boundary_selection_only_form_freeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex05_reviewer_person_boundary_selection_only_form_freeze_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_local_only_human_review_execution_protocol_bodyfree(
    *,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    local_only: bool = True,
    must_not_export: bool = True,
    selection_only: bool = True,
    required_reviewed_case_count: Any = P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
    required_selection_row_count: Any = P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
    body_quotation_allowed: bool = False,
    reviewer_notes_export_allowed: bool = False,
    question_text_allowed: bool = False,
    draft_question_text_allowed: bool = False,
    reviewer_free_text_allowed: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol(
        reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
        local_only=local_only,
        must_not_export=must_not_export,
        selection_only=selection_only,
        required_reviewed_case_count=required_reviewed_case_count,
        required_selection_row_count=required_selection_row_count,
        body_quotation_allowed=body_quotation_allowed,
        reviewer_notes_export_allowed=reviewer_notes_export_allowed,
        question_text_allowed=question_text_allowed,
        draft_question_text_allowed=draft_question_text_allowed,
        reviewer_free_text_allowed=reviewer_free_text_allowed,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_local_only_human_review_execution_protocol_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex06_actual_local_only_human_review_execution_protocol_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_operation_receipt_intake_bodyfree(
    *,
    actual_local_only_human_review_execution_protocol: Mapping[str, Any] | None = None,
    operation_receipt_ref: Any = "",
    reviewer_person_ref: Any = "",
    reviewer_local_only_read_receipt_present: bool = False,
    review_started_at_bucket_ref: Any = "",
    review_completed_at_bucket_ref: Any = "",
    reviewed_case_count: Any = 0,
    selection_row_count: Any = 0,
    local_only: bool = True,
    must_not_export: bool = True,
    selection_only: bool = True,
    actual_source_ref: Any = P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF,
    raw_input_included: bool = False,
    returned_emlis_body_included: bool = False,
    history_surface_included: bool = False,
    comment_text_body_included: bool = False,
    reviewer_free_text_included: bool = False,
    reviewer_notes_body_included: bool = False,
    question_text_included: bool = False,
    draft_question_text_included: bool = False,
    packet_content_included: bool = False,
    body_full_packet_content_included: bool = False,
    local_absolute_path_included: bool = False,
    body_hash_included: bool = False,
    terminal_output_body_included: bool = False,
    stdout_body_included: bool = False,
    stderr_body_included: bool = False,
    traceback_body_included: bool = False,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake(
        actual_local_only_human_review_execution_protocol=actual_local_only_human_review_execution_protocol,
        operation_receipt_ref=operation_receipt_ref,
        reviewer_person_ref=reviewer_person_ref,
        reviewer_local_only_read_receipt_present=reviewer_local_only_read_receipt_present,
        review_started_at_bucket_ref=review_started_at_bucket_ref,
        review_completed_at_bucket_ref=review_completed_at_bucket_ref,
        reviewed_case_count=reviewed_case_count,
        selection_row_count=selection_row_count,
        local_only=local_only,
        must_not_export=must_not_export,
        selection_only=selection_only,
        actual_source_ref=actual_source_ref,
        raw_input_included=raw_input_included,
        returned_emlis_body_included=returned_emlis_body_included,
        history_surface_included=history_surface_included,
        comment_text_body_included=comment_text_body_included,
        reviewer_free_text_included=reviewer_free_text_included,
        reviewer_notes_body_included=reviewer_notes_body_included,
        question_text_included=question_text_included,
        draft_question_text_included=draft_question_text_included,
        packet_content_included=packet_content_included,
        body_full_packet_content_included=body_full_packet_content_included,
        local_absolute_path_included=local_absolute_path_included,
        body_hash_included=body_hash_included,
        terminal_output_body_included=terminal_output_body_included,
        stdout_body_included=stdout_body_included,
        stderr_body_included=stderr_body_included,
        traceback_body_included=traceback_body_included,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_operation_receipt_intake_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(data)



# ---------------------------------------------------------------------------
# EX08-EX09 actual selection-row provenance guard / sanitized row intake
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX08_ACTUAL_SELECTION_ROW_PROVENANCE_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex08_actual_selection_row_provenance_guard.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX09_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex09_sanitized_review_result_rows_intake.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX09_SELECTION_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex09_sanitized_review_result_row.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:9]
P7_R54_AHR_POST_CR22_EX08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[9:]
P7_R54_AHR_POST_CR22_EX09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:10]
P7_R54_AHR_POST_CR22_EX09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[10:]

P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_ACCEPTED_STATUS_REF: Final = (
    "EX08_ACTUAL_SELECTION_ROW_PROVENANCE_GUARD_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_BLOCKED_STATUS_REF: Final = (
    "EX08_ACTUAL_SELECTION_ROW_PROVENANCE_GUARD_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX08_ALLOWED_PROVENANCE_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_ACCEPTED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX08_READY_REASON_REF: Final = (
    "EX08_ACTUAL_PERSON_SELECTION_ONLY_ROW_PROVENANCE_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex08_actual_selection_row_provenance_guard_or_stop"
)
P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF: Final = "actual_person_selection_only_rows_local_review"
P7_R54_AHR_POST_CR22_EX08_FORBIDDEN_ROW_SOURCE_REFS: Final[tuple[str, ...]] = (
    "helper_default_fixture_rows",
    "unit_test_contract_rows",
    "synthetic_bodyfree_rows",
    "historical_ahr_260_83_256_169_rows",
    "historical_cs_262_84_257_170_rows",
    "ai_inferred_review_rows",
    "rows_without_person_read_receipt",
)
P7_R54_AHR_POST_CR22_EX08_REJECTED_ROW_REF_PATH_SHAPE_REF: Final = (
    "rejected_selection_row_ref_path_shape_bodyfree"
)

P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_ACCEPTED_STATUS_REF: Final = (
    "EX09_SANITIZED_REVIEW_RESULT_ROWS_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_BLOCKED_STATUS_REF: Final = (
    "EX09_SANITIZED_REVIEW_RESULT_ROWS_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX09_ALLOWED_SANITIZED_ROWS_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_ACCEPTED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX09_READY_REASON_REF: Final = (
    "EX09_24_ACTUAL_SELECTION_ONLY_ROWS_SANITIZED_BODYFREE_WITHOUT_BODY_OR_QUESTION_TEXT"
)
P7_R54_AHR_POST_CR22_EX09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex09_sanitized_review_result_rows_intake_or_stop"
)
P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    cr.P7_R54_AHR_CR10_ROW_BODYFREE_FALSE_FLAG_REFS
)

P7_R54_AHR_POST_CR22_EX08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex07_schema_version",
    "ex07_material_ref",
    "ex07_next_required_step",
    "ex07_operation_receipt_accepted",
    "ex07_operation_receipt_ref",
    "ex07_reviewer_person_ref",
    "ex07_actual_human_review_executed_by_person",
    "ex07_reviewed_case_count",
    "ex07_selection_row_count",
    "selection_row_provenance_guard_status_ref",
    "selection_row_provenance_guard_allowed_status_refs",
    "selection_row_provenance_guard_passed",
    "selection_row_provenance_guard_reason_refs",
    "selection_row_provenance_guard_blocker_refs",
    "selection_row_provenance_guard_blocker_ref_count",
    "selection_row_source_required_ref",
    "forbidden_selection_row_source_refs",
    "forbidden_selection_row_source_ref_count",
    "selection_result_rows_input_present",
    "selection_row_provenance_row_count",
    "required_selection_row_count",
    "selection_row_count_is_24",
    "selection_row_provenance_rows",
    "selection_row_ref_count",
    "selection_row_refs",
    "case_ref_count",
    "case_refs",
    "blind_case_id_count",
    "blind_case_ids",
    "packet_ref_count",
    "packet_refs",
    "row_source_refs_observed",
    "row_source_ref_count",
    "row_source_refs_all_actual_person_selection_only_rows",
    "helper_default_rows_detected",
    "unit_test_rows_detected",
    "synthetic_contract_rows_detected",
    "historical_rows_detected",
    "ai_inferred_rows_detected",
    "rows_without_person_read_receipt_detected",
    "review_session_id_matches_all_rows",
    "operation_receipt_ref_matches_all_rows",
    "reviewer_person_ref_matches_all_rows",
    "rows_match_24_case_manifest",
    "rows_bodyfree_only",
    "rows_selection_only",
    "rows_have_no_body_or_question_or_path_or_hash",
    "actual_rows_source_guard_passed",
    "actual_selection_row_provenance_checked_here",
    "sanitized_selection_only_result_rows_intaken_here",
    "actual_sanitized_review_result_rows_intaken_here",
    "actual_human_review_executed_by_person",
    "selection_row_provenance_bodyfree_only",
    "selection_row_provenance_guard_does_not_sanitize_rows_here",
    "selection_row_provenance_guard_does_not_create_rating_rows_here",
    "selection_row_provenance_guard_does_not_create_question_observation_rows_here",
    "selection_row_provenance_guard_does_not_create_disposal_receipt_here",
    "selection_row_provenance_guard_does_not_complete_evidence_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_CR22_EX09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex08_schema_version",
    "ex08_material_ref",
    "ex08_next_required_step",
    "ex08_selection_row_provenance_guard_status_ref",
    "ex08_selection_row_provenance_guard_passed",
    "ex08_actual_rows_source_guard_passed",
    "ex08_selection_row_provenance_row_count",
    "operation_receipt_ref",
    "reviewer_person_ref",
    "sanitized_review_result_rows_intake_status_ref",
    "sanitized_review_result_rows_intake_allowed_status_refs",
    "sanitized_review_result_rows_intake_ready",
    "sanitized_review_result_rows_intake_reason_refs",
    "sanitized_review_result_rows_intake_blocker_refs",
    "sanitized_review_result_rows_intake_blocker_ref_count",
    "selection_result_rows_input_present",
    "received_selection_row_count",
    "selection_result_row_count",
    "required_selection_result_row_count",
    "selection_result_row_count_is_24",
    "sanitized_review_result_row_count",
    "review_result_rows",
    "review_result_row_refs",
    "review_result_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "reviewed_at_bucket_refs",
    "reviewed_at_bucket_ref_count",
    "reviewed_at_bucket_refs_present",
    "axis_refs",
    "axis_ref_count",
    "axis_score_count_per_row",
    "axis_target_thresholds",
    "verdict_option_refs",
    "sanitized_reason_id_option_refs",
    "readfeel_blocker_id_option_refs",
    "execution_blocker_id_option_refs",
    "question_need_primary_class_option_refs",
    "ambiguity_kind_option_refs",
    "one_question_fit_option_refs",
    "repair_required_option_refs",
    "plan_candidate_flag_refs",
    "rows_match_24_case_manifest",
    "rows_bodyfree_only",
    "rows_selection_only",
    "rows_have_actual_person_selection_only_provenance",
    "rows_have_required_axis_scores",
    "rows_have_allowed_verdict_refs",
    "rows_have_allowed_question_observation_refs",
    "rows_have_no_body_or_question_or_path_or_hash",
    "sanitized_selection_only_result_rows_intaken_here",
    "actual_sanitized_review_result_rows_intaken_here",
    "actual_human_review_executed_by_person",
    "actual_selection_rows_created_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "rating_row_normalization_allowed_next",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _postcr22_row_refs_bodyfree(raw_row: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    row_ref, row_ref_path = _bodyfree_ref_or_rejected(
        raw_row.get("review_result_row_ref"),
        default=f"postcr22_actual_review_result_row_{index:03d}",
        rejected_ref=P7_R54_AHR_POST_CR22_EX08_REJECTED_ROW_REF_PATH_SHAPE_REF,
        max_length=180,
    )
    case_ref = clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120)
    blind_id = clean_identifier(raw_row.get("blind_case_id"), default="", max_length=120)
    packet_ref = clean_identifier(raw_row.get("packet_ref_id"), default="", max_length=120)
    reviewed_ref, reviewed_ref_path = _bodyfree_ref_or_rejected(
        raw_row.get("reviewed_at_bucket_ref"),
        rejected_ref=P7_R54_AHR_POST_CR22_EX08_REJECTED_ROW_REF_PATH_SHAPE_REF,
        max_length=180,
    )
    return {
        "review_result_row_ref": row_ref,
        "review_result_row_ref_has_path_shape": row_ref_path,
        "case_ref_id": case_ref,
        "blind_case_id": blind_id,
        "packet_ref_id": packet_ref,
        "reviewed_at_bucket_ref": reviewed_ref,
        "reviewed_at_bucket_ref_has_path_shape": reviewed_ref_path,
    }


def _clean_string_ref_list(value: Any, *, limit: int = 24, max_length: int = 180) -> list[str]:
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        values: Sequence[Any] = []
    else:
        values = value
    refs: list[str] = []
    seen: set[str] = set()
    for raw in values:
        ref = clean_identifier(raw, default="", max_length=max_length)
        if ref and ref not in seen:
            seen.add(ref)
            refs.append(ref)
        if len(refs) >= limit:
            break
    return refs


def _postcr22_clean_plan_candidate_flags(value: Any) -> tuple[dict[str, bool], bool]:
    raw_mapping = value if isinstance(value, Mapping) else {}
    invalid = not isinstance(value, Mapping)
    flags = {key: bool(raw_mapping.get(key, False)) for key in cr.P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS}
    if raw_mapping.get("p8_implementation_spec_finalized_here") is True:
        invalid = True
    flags["p8_implementation_spec_finalized_here"] = False
    return flags, invalid


def _postcr22_validate_actual_selection_rows_for_ex08(
    rows: Sequence[Any],
    *,
    review_session_id: str,
    operation_receipt_ref: str,
    reviewer_person_ref: str,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    blockers: list[str] = []
    provenance_rows: list[dict[str, Any]] = []
    expected_manifest = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    expected_by_case = {
        str(row.get("case_ref_id")): row for row in expected_manifest.get("case_rows", [])
    }
    if len(rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_result_row_count_not_24")
    seen_case_refs: set[str] = set()
    seen_blind_ids: set[str] = set()
    seen_packet_refs: set[str] = set()
    row_refs: list[str] = []
    source_refs: list[str] = []
    counters = {
        "helper_default_rows": 0,
        "unit_test_rows": 0,
        "synthetic_contract_rows": 0,
        "historical_rows": 0,
        "ai_inferred_rows": 0,
        "rows_without_person_read_receipt": 0,
        "session_mismatch": 0,
        "operation_receipt_mismatch": 0,
        "reviewer_person_mismatch": 0,
        "manifest_mismatch": 0,
        "forbidden_payload_key": 0,
        "forbidden_body_flag": 0,
        "path_shape_ref": 0,
        "selection_only_false": 0,
        "body_free_false": 0,
    }
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append("selection_row_not_mapping")
            continue
        refs = _postcr22_row_refs_bodyfree(raw_row, index=index)
        row_ref = refs["review_result_row_ref"]
        row_refs.append(row_ref)
        if refs["review_result_row_ref_has_path_shape"]:
            counters["path_shape_ref"] += 1
            blockers.append("selection_row_ref_must_be_bodyfree_ref_not_path")
        source_ref = clean_identifier(raw_row.get("row_source_ref"), default="", max_length=180)
        if source_ref:
            source_refs.append(source_ref)
        if source_ref != P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF:
            blockers.append("selection_row_source_ref_forbidden")
        if source_ref in P7_R54_AHR_POST_CR22_EX08_FORBIDDEN_ROW_SOURCE_REFS:
            blockers.append("selection_row_source_ref_forbidden")
        if source_ref == "helper_default_fixture_rows" or raw_row.get("row_created_by_helper") is True:
            counters["helper_default_rows"] += 1
            blockers.append("selection_row_created_by_helper")
        if source_ref == "unit_test_contract_rows" or raw_row.get("row_created_for_unit_test") is True:
            counters["unit_test_rows"] += 1
            blockers.append("selection_row_created_for_unit_test")
        if source_ref == "synthetic_bodyfree_rows" or raw_row.get("row_is_synthetic_contract_fixture") is True:
            counters["synthetic_contract_rows"] += 1
            blockers.append("selection_row_is_synthetic_contract_fixture")
        if source_ref.startswith("historical_") or raw_row.get("historical_row_reused") is True:
            counters["historical_rows"] += 1
            blockers.append("selection_row_historical_reused")
        if source_ref == "ai_inferred_review_rows" or raw_row.get("ai_inferred_review_row") is True:
            counters["ai_inferred_rows"] += 1
            blockers.append("selection_row_ai_inferred")
        if source_ref == "rows_without_person_read_receipt" or raw_row.get("row_without_person_read_receipt") is True:
            counters["rows_without_person_read_receipt"] += 1
            blockers.append("selection_row_without_person_read_receipt")
        for flag_ref in (
            "row_created_by_helper",
            "row_created_for_unit_test",
            "row_is_synthetic_contract_fixture",
            "historical_row_reused",
            "ai_inferred_review_row",
            "row_without_person_read_receipt",
        ):
            if raw_row.get(flag_ref) not in (False, None):
                # Specific blockers are already attached above. This keeps the guard fail-closed.
                pass
        if _forbidden_payload_key_paths(raw_row, path="selection_row"):
            counters["forbidden_payload_key"] += 1
            blockers.append("selection_row_contains_forbidden_body_question_path_or_hash_key")
        if any(raw_row.get(flag_ref) is not False for flag_ref in P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS):
            counters["forbidden_body_flag"] += 1
            blockers.append("selection_row_bodyfree_forbidden_flag_not_false")
        row_session_id = clean_identifier(raw_row.get("review_session_id"), default="", max_length=220)
        row_operation_receipt_ref = clean_identifier(raw_row.get("operation_receipt_ref"), default="", max_length=240)
        row_reviewer_person_ref = clean_identifier(raw_row.get("reviewer_person_ref"), default="", max_length=220)
        if row_session_id != review_session_id:
            counters["session_mismatch"] += 1
            blockers.append("selection_row_review_session_id_mismatch")
        if row_operation_receipt_ref != operation_receipt_ref:
            counters["operation_receipt_mismatch"] += 1
            blockers.append("selection_row_operation_receipt_ref_mismatch")
        if row_reviewer_person_ref != reviewer_person_ref:
            counters["reviewer_person_mismatch"] += 1
            blockers.append("selection_row_reviewer_person_ref_mismatch")
        expected = expected_by_case.get(refs["case_ref_id"])
        if not expected or refs["blind_case_id"] != expected.get("blind_case_id") or refs["packet_ref_id"] != expected.get("packet_ref_id"):
            counters["manifest_mismatch"] += 1
            blockers.append("selection_row_manifest_id_mismatch")
        if raw_row.get("selection_only") is not True or raw_row.get("selection_only_row") is not True:
            counters["selection_only_false"] += 1
            blockers.append("selection_row_selection_only_false")
        if raw_row.get("body_free") is not True:
            counters["body_free_false"] += 1
            blockers.append("selection_row_body_free_false")
        seen_case_refs.add(refs["case_ref_id"])
        seen_blind_ids.add(refs["blind_case_id"])
        seen_packet_refs.add(refs["packet_ref_id"])
        provenance_rows.append(
            {
                "review_result_row_ref": row_ref,
                "case_ref_id": refs["case_ref_id"],
                "blind_case_id": refs["blind_case_id"],
                "packet_ref_id": refs["packet_ref_id"],
                "row_source_ref": source_ref,
                "row_created_by_helper": False,
                "row_created_for_unit_test": False,
                "row_is_synthetic_contract_fixture": False,
                "historical_row_reused": False,
                "body_free": True,
            }
        )
    if len(seen_case_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_row_unique_case_refs_not_24")
    if len(seen_blind_ids) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_row_unique_blind_case_ids_not_24")
    if len(seen_packet_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_row_unique_packet_refs_not_24")
    blockers = _dedupe_refs(blockers)
    accepted = not blockers
    stats = {
        "selection_row_refs": sorted(set(row_refs)),
        "case_refs": sorted(seen_case_refs),
        "blind_case_ids": sorted(seen_blind_ids),
        "packet_refs": sorted(seen_packet_refs),
        "row_source_refs_observed": _dedupe_refs(source_refs),
        "helper_default_rows_detected": counters["helper_default_rows"] > 0,
        "unit_test_rows_detected": counters["unit_test_rows"] > 0,
        "synthetic_contract_rows_detected": counters["synthetic_contract_rows"] > 0,
        "historical_rows_detected": counters["historical_rows"] > 0,
        "ai_inferred_rows_detected": counters["ai_inferred_rows"] > 0,
        "rows_without_person_read_receipt_detected": counters["rows_without_person_read_receipt"] > 0,
        "review_session_id_matches_all_rows": counters["session_mismatch"] == 0 and bool(rows),
        "operation_receipt_ref_matches_all_rows": counters["operation_receipt_mismatch"] == 0 and bool(rows),
        "reviewer_person_ref_matches_all_rows": counters["reviewer_person_mismatch"] == 0 and bool(rows),
        "rows_match_24_case_manifest": counters["manifest_mismatch"] == 0 and len(seen_case_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "rows_bodyfree_only": counters["forbidden_payload_key"] == 0 and counters["forbidden_body_flag"] == 0 and counters["body_free_false"] == 0 and bool(rows),
        "rows_selection_only": counters["selection_only_false"] == 0 and bool(rows),
        "rows_have_no_body_or_question_or_path_or_hash": counters["forbidden_payload_key"] == 0 and counters["forbidden_body_flag"] == 0 and counters["path_shape_ref"] == 0 and bool(rows),
        "raw_counters": counters,
    }
    return (provenance_rows if accepted else []), blockers, stats


def build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    selection_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX08 body-free actual selection-row provenance guard material."""

    ex07 = actual_operation_receipt_intake or build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake()
    session_id = _safe_review_session_id(review_session_id or ex07.get("review_session_id"))
    rows_input = list(selection_result_rows or [])
    rows_present = selection_result_rows is not None
    operation_receipt_ref = clean_identifier(ex07.get("operation_receipt_ref"), default="", max_length=240)
    reviewer_person_ref = clean_identifier(ex07.get("reviewer_person_ref"), default="", max_length=220)
    provenance_rows, row_blockers, stats = _postcr22_validate_actual_selection_rows_for_ex08(
        rows_input,
        review_session_id=session_id,
        operation_receipt_ref=operation_receipt_ref,
        reviewer_person_ref=reviewer_person_ref,
    )
    blockers: list[str] = []
    if ex07.get("schema_version") != P7_R54_AHR_POST_CR22_EX07_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION:
        blockers.append("ex07_schema_version_not_current")
    if ex07.get("operation_receipt_accepted") is not True:
        blockers.append("ex07_operation_receipt_not_accepted")
    if ex07.get("next_required_step") != P7_R54_AHR_POST_CR22_EX08_STEP_REF:
        blockers.append("ex07_next_required_step_not_ex08")
    if ex07.get("actual_human_review_executed_by_person") is not True:
        blockers.append("ex07_actual_human_review_executed_by_person_missing")
    if ex07.get("reviewed_case_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex07_reviewed_case_count_not_24")
    if ex07.get("selection_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex07_selection_row_count_not_24")
    if not rows_present:
        blockers.append("selection_result_rows_input_missing")
    blockers.extend(row_blockers)
    blockers = _dedupe_refs(blockers)
    accepted = not blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX08_ACTUAL_SELECTION_ROW_PROVENANCE_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX08_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex07_schema_version": ex07.get("schema_version"),
        "ex07_material_ref": ex07.get("material_id", "postcr22_ex07_actual_operation_receipt_intake_bodyfree"),
        "ex07_next_required_step": ex07.get("next_required_step"),
        "ex07_operation_receipt_accepted": ex07.get("operation_receipt_accepted") is True,
        "ex07_operation_receipt_ref": operation_receipt_ref,
        "ex07_reviewer_person_ref": reviewer_person_ref,
        "ex07_actual_human_review_executed_by_person": ex07.get("actual_human_review_executed_by_person") is True,
        "ex07_reviewed_case_count": _int_value_or_zero(ex07.get("reviewed_case_count")),
        "ex07_selection_row_count": _int_value_or_zero(ex07.get("selection_row_count")),
        "selection_row_provenance_guard_status_ref": (
            P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_ACCEPTED_STATUS_REF
            if accepted
            else P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_BLOCKED_STATUS_REF
        ),
        "selection_row_provenance_guard_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX08_ALLOWED_PROVENANCE_GUARD_STATUS_REFS),
        "selection_row_provenance_guard_passed": accepted,
        "selection_row_provenance_guard_reason_refs": [P7_R54_AHR_POST_CR22_EX08_READY_REASON_REF] if accepted else [],
        "selection_row_provenance_guard_blocker_refs": blockers,
        "selection_row_provenance_guard_blocker_ref_count": len(blockers),
        "selection_row_source_required_ref": P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF,
        "forbidden_selection_row_source_refs": list(P7_R54_AHR_POST_CR22_EX08_FORBIDDEN_ROW_SOURCE_REFS),
        "forbidden_selection_row_source_ref_count": len(P7_R54_AHR_POST_CR22_EX08_FORBIDDEN_ROW_SOURCE_REFS),
        "selection_result_rows_input_present": rows_present,
        "selection_row_provenance_row_count": len(provenance_rows) if accepted else 0,
        "required_selection_row_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "selection_row_count_is_24": len(rows_input) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "selection_row_provenance_rows": provenance_rows if accepted else [],
        "selection_row_ref_count": len(stats["selection_row_refs"]) if accepted else 0,
        "selection_row_refs": stats["selection_row_refs"] if accepted else [],
        "case_ref_count": len(stats["case_refs"]) if accepted else 0,
        "case_refs": stats["case_refs"] if accepted else [],
        "blind_case_id_count": len(stats["blind_case_ids"]) if accepted else 0,
        "blind_case_ids": stats["blind_case_ids"] if accepted else [],
        "packet_ref_count": len(stats["packet_refs"]) if accepted else 0,
        "packet_refs": stats["packet_refs"] if accepted else [],
        "row_source_refs_observed": stats["row_source_refs_observed"] if accepted else [],
        "row_source_ref_count": len(stats["row_source_refs_observed"]) if accepted else 0,
        "row_source_refs_all_actual_person_selection_only_rows": accepted,
        "helper_default_rows_detected": stats["helper_default_rows_detected"],
        "unit_test_rows_detected": stats["unit_test_rows_detected"],
        "synthetic_contract_rows_detected": stats["synthetic_contract_rows_detected"],
        "historical_rows_detected": stats["historical_rows_detected"],
        "ai_inferred_rows_detected": stats["ai_inferred_rows_detected"],
        "rows_without_person_read_receipt_detected": stats["rows_without_person_read_receipt_detected"],
        "review_session_id_matches_all_rows": stats["review_session_id_matches_all_rows"] and accepted,
        "operation_receipt_ref_matches_all_rows": stats["operation_receipt_ref_matches_all_rows"] and accepted,
        "reviewer_person_ref_matches_all_rows": stats["reviewer_person_ref_matches_all_rows"] and accepted,
        "rows_match_24_case_manifest": stats["rows_match_24_case_manifest"] and accepted,
        "rows_bodyfree_only": stats["rows_bodyfree_only"] and accepted,
        "rows_selection_only": stats["rows_selection_only"] and accepted,
        "rows_have_no_body_or_question_or_path_or_hash": stats["rows_have_no_body_or_question_or_path_or_hash"] and accepted,
        "actual_rows_source_guard_passed": accepted,
        "actual_selection_row_provenance_checked_here": True,
        "sanitized_selection_only_result_rows_intaken_here": False,
        "actual_sanitized_review_result_rows_intaken_here": False,
        "actual_human_review_executed_by_person": accepted,
        "selection_row_provenance_bodyfree_only": True,
        "selection_row_provenance_guard_does_not_sanitize_rows_here": True,
        "selection_row_provenance_guard_does_not_create_rating_rows_here": True,
        "selection_row_provenance_guard_does_not_create_question_observation_rows_here": True,
        "selection_row_provenance_guard_does_not_create_disposal_receipt_here": True,
        "selection_row_provenance_guard_does_not_complete_evidence_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX08_IMPLEMENTED_STEPS if accepted else P7_R54_AHR_POST_CR22_EX07_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX08_NOT_YET_IMPLEMENTED_STEPS if accepted else P7_R54_AHR_POST_CR22_EX07_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX09_STEP_REF if accepted else P7_R54_AHR_POST_CR22_EX08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    _required_fields_present(
        material,
        required=P7_R54_AHR_POST_CR22_EX08_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostCR22-EX08",
    )
    return material


def assert_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX08")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX08_ACTUAL_SELECTION_ROW_PROVENANCE_GUARD_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX08_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX08",
    )
    blockers = list(data.get("selection_row_provenance_guard_blocker_refs") or [])
    accepted = len(blockers) == 0
    expected_status = (
        P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_ACCEPTED_STATUS_REF
        if accepted
        else P7_R54_AHR_POST_CR22_EX08_PROVENANCE_GUARD_BLOCKED_STATUS_REF
    )
    if data.get("selection_row_provenance_guard_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX08 status changed")
    if data.get("selection_row_provenance_guard_passed") is not accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX08 passed flag changed")
    if data.get("selection_row_provenance_guard_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX08 blocker count changed")
    if tuple(data.get("selection_row_provenance_guard_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX08_ALLOWED_PROVENANCE_GUARD_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX08 allowed status refs changed")
    if tuple(data.get("forbidden_selection_row_source_refs") or ()) != P7_R54_AHR_POST_CR22_EX08_FORBIDDEN_ROW_SOURCE_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX08 forbidden source refs changed")
    if accepted:
        if data.get("selection_row_provenance_guard_reason_refs") != [P7_R54_AHR_POST_CR22_EX08_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 accepted reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX08_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 next step changed")
        for key in (
            "actual_rows_source_guard_passed",
            "actual_human_review_executed_by_person",
            "actual_selection_row_provenance_checked_here",
            "selection_row_provenance_bodyfree_only",
            "selection_row_provenance_guard_does_not_sanitize_rows_here",
            "selection_row_provenance_guard_does_not_create_rating_rows_here",
            "selection_row_provenance_guard_does_not_create_question_observation_rows_here",
            "selection_row_provenance_guard_does_not_create_disposal_receipt_here",
            "selection_row_provenance_guard_does_not_complete_evidence_here",
            "current_cr_basis_remains_264_85_258_171",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX08 required true field changed: {key}")
        for key in (
            "sanitized_selection_only_result_rows_intaken_here",
            "actual_sanitized_review_result_rows_intaken_here",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_review_evidence_complete",
            "p8_start_allowed",
            "release_allowed",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX08 required false field changed: {key}")
        if data.get("selection_row_provenance_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 accepted count changed")
    else:
        if data.get("selection_row_provenance_guard_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 blocked material cannot carry accepted reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX08_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 blocked next step changed")
        if data.get("actual_rows_source_guard_passed") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 blocked material cannot pass source guard")
        if data.get("actual_human_review_executed_by_person") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 blocked material cannot claim person execution")
        if data.get("selection_row_provenance_rows") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX08 blocked material cannot output provenance rows")
    return True


def _postcr22_validate_and_sanitize_rows_for_ex09(
    rows: Sequence[Any],
    *,
    review_session_id: str,
    operation_receipt_ref: str,
    reviewer_person_ref: str,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    blockers: list[str] = []
    sanitized_rows: list[dict[str, Any]] = []
    expected_manifest = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    expected_by_case = {str(row.get("case_ref_id")): row for row in expected_manifest.get("case_rows", [])}
    if len(rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("sanitized_selection_row_count_not_24")
    seen_case_refs: set[str] = set()
    seen_blind_ids: set[str] = set()
    seen_packet_refs: set[str] = set()
    row_refs: list[str] = []
    reviewed_at_refs: list[str] = []
    rows_match_manifest = True
    rows_bodyfree_only = True
    rows_selection_only = True
    rows_have_actual_provenance = True
    rows_have_required_axis_scores = True
    rows_have_allowed_verdict_refs = True
    rows_have_allowed_question_refs = True
    rows_no_body_question_path_hash = True
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append("selection_row_not_mapping")
            rows_bodyfree_only = False
            continue
        refs = _postcr22_row_refs_bodyfree(raw_row, index=index)
        if refs["review_result_row_ref_has_path_shape"] or refs["reviewed_at_bucket_ref_has_path_shape"]:
            blockers.append("selection_row_ref_must_be_bodyfree_ref_not_path")
            rows_no_body_question_path_hash = False
        if _forbidden_payload_key_paths(raw_row, path="selection_row"):
            blockers.append("selection_row_contains_forbidden_body_question_path_or_hash_key")
            rows_bodyfree_only = False
            rows_no_body_question_path_hash = False
        row_ref = refs["review_result_row_ref"]
        row_refs.append(row_ref)
        case_ref_id = refs["case_ref_id"]
        blind_case_id = refs["blind_case_id"]
        packet_ref_id = refs["packet_ref_id"]
        expected = expected_by_case.get(case_ref_id)
        if not expected or blind_case_id != expected.get("blind_case_id") or packet_ref_id != expected.get("packet_ref_id"):
            blockers.append("selection_row_manifest_id_mismatch")
            rows_match_manifest = False
        row_session_id = clean_identifier(raw_row.get("review_session_id"), default="", max_length=220)
        row_operation_receipt_ref = clean_identifier(raw_row.get("operation_receipt_ref"), default="", max_length=240)
        row_reviewer_person_ref = clean_identifier(raw_row.get("reviewer_person_ref"), default="", max_length=220)
        if row_session_id != review_session_id:
            blockers.append("selection_row_review_session_id_mismatch")
        if row_operation_receipt_ref != operation_receipt_ref:
            blockers.append("selection_row_operation_receipt_ref_mismatch")
        if row_reviewer_person_ref != reviewer_person_ref:
            blockers.append("selection_row_reviewer_person_ref_mismatch")
        reviewed_at_ref = refs["reviewed_at_bucket_ref"]
        if not reviewed_at_ref:
            blockers.append("selection_row_reviewed_at_ref_missing")
        else:
            reviewed_at_refs.append(reviewed_at_ref)
        source_ref = clean_identifier(raw_row.get("row_source_ref"), default="", max_length=180)
        if source_ref != P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF:
            blockers.append("selection_row_source_ref_forbidden")
            rows_have_actual_provenance = False
        for flag_ref, blocker_ref in (
            ("row_created_by_helper", "selection_row_created_by_helper"),
            ("row_created_for_unit_test", "selection_row_created_for_unit_test"),
            ("row_is_synthetic_contract_fixture", "selection_row_is_synthetic_contract_fixture"),
            ("historical_row_reused", "selection_row_historical_reused"),
        ):
            if raw_row.get(flag_ref) is not False:
                blockers.append(blocker_ref)
                rows_have_actual_provenance = False
        axis_raw = raw_row.get("axis_scores")
        axis_scores: dict[str, float] = {}
        axis_valid = isinstance(axis_raw, Mapping) and set(str(k) for k in axis_raw.keys()) == set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
        for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS:
            try:
                score = float(axis_raw.get(axis_ref)) if isinstance(axis_raw, Mapping) else 0.0
            except (TypeError, ValueError):
                score = 0.0
                axis_valid = False
            if score < 0.0 or score > 1.0:
                blockers.append("selection_row_axis_score_invalid")
                axis_valid = False
            axis_scores[axis_ref] = score
        if not axis_valid or raw_row.get("axis_score_count") != len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS):
            blockers.append("selection_row_axis_refs_mismatch")
            rows_have_required_axis_scores = False
        verdict = clean_identifier(raw_row.get("verdict"), default="", max_length=80)
        if verdict not in cr.P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
            blockers.append("selection_row_verdict_not_allowed")
            rows_have_allowed_verdict_refs = False
        sanitized_reason_ids = _clean_string_ref_list(raw_row.get("sanitized_reason_ids"), limit=24, max_length=160)
        readfeel_blocker_ids = _clean_string_ref_list(raw_row.get("readfeel_blocker_ids"), limit=24, max_length=160)
        execution_blocker_ids = _clean_string_ref_list(raw_row.get("execution_blocker_ids"), limit=24, max_length=160)
        ambiguity_kind_refs = _clean_string_ref_list(raw_row.get("ambiguity_kind_refs"), limit=24, max_length=160)
        repair_required_refs = _clean_string_ref_list(raw_row.get("repair_required_refs"), limit=24, max_length=180)
        question_need_primary_class = clean_identifier(raw_row.get("question_need_primary_class"), default="", max_length=180)
        one_question_fit_ref = clean_identifier(raw_row.get("one_question_fit_ref"), default="", max_length=180)
        if any(ref not in cr.P7_R54_AHR_CR10_SANITIZED_REASON_ID_OPTION_REFS for ref in sanitized_reason_ids):
            blockers.append("selection_row_option_ref_not_allowed")
        if any(ref not in cr.P7_R54_AHR_CR10_READFEEL_BLOCKER_ID_OPTION_REFS for ref in readfeel_blocker_ids):
            blockers.append("selection_row_option_ref_not_allowed")
        if any(ref not in cr.P7_R54_AHR_CR10_EXECUTION_BLOCKER_ID_OPTION_REFS for ref in execution_blocker_ids):
            blockers.append("selection_row_option_ref_not_allowed")
        if question_need_primary_class not in cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
            blockers.append("selection_row_option_ref_not_allowed")
            rows_have_allowed_question_refs = False
        if any(ref not in cr.P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS for ref in ambiguity_kind_refs):
            blockers.append("selection_row_option_ref_not_allowed")
            rows_have_allowed_question_refs = False
        if one_question_fit_ref not in cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append("selection_row_option_ref_not_allowed")
            rows_have_allowed_question_refs = False
        if any(ref not in cr.P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS for ref in repair_required_refs):
            blockers.append("selection_row_option_ref_not_allowed")
            rows_have_allowed_question_refs = False
        plan_candidate_flags, plan_flags_invalid = _postcr22_clean_plan_candidate_flags(raw_row.get("plan_candidate_flags"))
        if plan_flags_invalid:
            blockers.append("selection_row_p8_implementation_spec_finalized_here")
        if raw_row.get("selection_only") is not True or raw_row.get("selection_only_row") is not True:
            blockers.append("selection_row_selection_only_false")
            rows_selection_only = False
        if raw_row.get("body_free") is not True:
            blockers.append("selection_row_body_free_false")
            rows_bodyfree_only = False
        if any(raw_row.get(flag_ref) is not False for flag_ref in P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS):
            blockers.append("selection_row_bodyfree_forbidden_flag_not_false")
            rows_bodyfree_only = False
            rows_no_body_question_path_hash = False
        seen_case_refs.add(case_ref_id)
        seen_blind_ids.add(blind_case_id)
        seen_packet_refs.add(packet_ref_id)
        sanitized_row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_POST_CR22_EX09_SELECTION_RESULT_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "review_result_row_ref": row_ref,
            "case_ref_id": case_ref_id,
            "blind_case_id": blind_case_id,
            "packet_ref_id": packet_ref_id,
            "reviewer_person_ref": reviewer_person_ref,
            "reviewed_at_bucket_ref": reviewed_at_ref,
            "axis_scores": axis_scores,
            "axis_score_count": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
            "verdict": verdict,
            "sanitized_reason_ids": sanitized_reason_ids,
            "readfeel_blocker_ids": readfeel_blocker_ids,
            "execution_blocker_ids": execution_blocker_ids,
            "question_need_primary_class": question_need_primary_class,
            "ambiguity_kind_refs": ambiguity_kind_refs,
            "one_question_fit_ref": one_question_fit_ref,
            "repair_required_refs": repair_required_refs,
            "plan_candidate_flags": plan_candidate_flags,
            "row_source_ref": P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF,
            "row_created_by_helper": False,
            "row_created_for_unit_test": False,
            "row_is_synthetic_contract_fixture": False,
            "historical_row_reused": False,
            "selection_only": True,
            "selection_only_row": True,
            "body_free": True,
        }
        sanitized_row.update({key: False for key in P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS})
        sanitized_rows.append(sanitized_row)
    if len(seen_case_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_row_unique_case_refs_not_24")
    if len(seen_blind_ids) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_row_unique_blind_case_ids_not_24")
    if len(seen_packet_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("selection_row_unique_packet_refs_not_24")
    blockers = _dedupe_refs(blockers)
    ready = not blockers
    stats = {
        "row_refs": [row["review_result_row_ref"] for row in sanitized_rows] if ready else [],
        "case_refs": [row["case_ref_id"] for row in sanitized_rows] if ready else [],
        "blind_ids": [row["blind_case_id"] for row in sanitized_rows] if ready else [],
        "packet_refs": [row["packet_ref_id"] for row in sanitized_rows] if ready else [],
        "reviewed_at_refs": [row["reviewed_at_bucket_ref"] for row in sanitized_rows] if ready else [],
        "case_refs_unique": len(seen_case_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "blind_ids_unique": len(seen_blind_ids) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "packet_refs_unique": len(seen_packet_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "reviewed_at_refs_present": len(reviewed_at_refs) == len(rows),
        "rows_match_manifest": rows_match_manifest and len(seen_case_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "rows_bodyfree_only": rows_bodyfree_only and bool(rows),
        "rows_selection_only": rows_selection_only and bool(rows),
        "rows_have_actual_provenance": rows_have_actual_provenance and bool(rows),
        "rows_have_required_axis_scores": rows_have_required_axis_scores and bool(rows),
        "rows_have_allowed_verdict_refs": rows_have_allowed_verdict_refs and bool(rows),
        "rows_have_allowed_question_refs": rows_have_allowed_question_refs and bool(rows),
        "rows_no_body_question_path_hash": rows_no_body_question_path_hash and bool(rows),
    }
    return (sanitized_rows if ready else []), blockers, stats


def build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
    *,
    actual_selection_row_provenance_guard: Mapping[str, Any] | None = None,
    selection_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX09 body-free sanitized review result rows intake material."""

    ex08 = actual_selection_row_provenance_guard or build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard()
    session_id = _safe_review_session_id(review_session_id or ex08.get("review_session_id"))
    rows_input = list(selection_result_rows or [])
    rows_present = selection_result_rows is not None
    operation_receipt_ref = clean_identifier(ex08.get("ex07_operation_receipt_ref"), default="", max_length=240)
    reviewer_person_ref = clean_identifier(ex08.get("ex07_reviewer_person_ref"), default="", max_length=220)
    sanitized_rows, row_blockers, row_stats = _postcr22_validate_and_sanitize_rows_for_ex09(
        rows_input,
        review_session_id=session_id,
        operation_receipt_ref=operation_receipt_ref,
        reviewer_person_ref=reviewer_person_ref,
    )
    blockers: list[str] = []
    if ex08.get("schema_version") != P7_R54_AHR_POST_CR22_EX08_ACTUAL_SELECTION_ROW_PROVENANCE_GUARD_SCHEMA_VERSION:
        blockers.append("ex08_schema_version_not_current")
    if ex08.get("selection_row_provenance_guard_passed") is not True:
        blockers.append("ex08_selection_row_provenance_guard_not_accepted")
    if ex08.get("actual_rows_source_guard_passed") is not True:
        blockers.append("ex08_actual_rows_source_guard_not_passed")
    if ex08.get("next_required_step") != P7_R54_AHR_POST_CR22_EX09_STEP_REF:
        blockers.append("ex08_next_required_step_not_ex09")
    if not rows_present:
        blockers.append("selection_result_rows_input_missing")
    blockers.extend(row_blockers)
    blockers = _dedupe_refs(blockers)
    ready = not blockers
    rows_for_output = sanitized_rows if ready else []
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX09_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX09_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex08_schema_version": ex08.get("schema_version"),
        "ex08_material_ref": ex08.get("material_id", "postcr22_ex08_actual_selection_row_provenance_guard_bodyfree"),
        "ex08_next_required_step": ex08.get("next_required_step"),
        "ex08_selection_row_provenance_guard_status_ref": ex08.get("selection_row_provenance_guard_status_ref"),
        "ex08_selection_row_provenance_guard_passed": ex08.get("selection_row_provenance_guard_passed") is True,
        "ex08_actual_rows_source_guard_passed": ex08.get("actual_rows_source_guard_passed") is True,
        "ex08_selection_row_provenance_row_count": _int_value_or_zero(ex08.get("selection_row_provenance_row_count")),
        "operation_receipt_ref": operation_receipt_ref,
        "reviewer_person_ref": reviewer_person_ref,
        "sanitized_review_result_rows_intake_status_ref": (
            P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_ACCEPTED_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_BLOCKED_STATUS_REF
        ),
        "sanitized_review_result_rows_intake_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX09_ALLOWED_SANITIZED_ROWS_STATUS_REFS),
        "sanitized_review_result_rows_intake_ready": ready,
        "sanitized_review_result_rows_intake_reason_refs": [P7_R54_AHR_POST_CR22_EX09_READY_REASON_REF] if ready else [],
        "sanitized_review_result_rows_intake_blocker_refs": blockers,
        "sanitized_review_result_rows_intake_blocker_ref_count": len(blockers),
        "selection_result_rows_input_present": rows_present,
        "received_selection_row_count": len(rows_input),
        "selection_result_row_count": len(rows_for_output),
        "required_selection_result_row_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "selection_result_row_count_is_24": len(rows_input) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count": len(rows_for_output),
        "review_result_rows": rows_for_output,
        "review_result_row_refs": row_stats["row_refs"] if ready else [],
        "review_result_row_ref_count": len(row_stats["row_refs"]) if ready else 0,
        "case_ref_ids": row_stats["case_refs"] if ready else [],
        "case_ref_id_count": len(row_stats["case_refs"]) if ready else 0,
        "case_ref_ids_unique": row_stats["case_refs_unique"] and ready,
        "blind_case_ids": row_stats["blind_ids"] if ready else [],
        "blind_case_id_count": len(row_stats["blind_ids"]) if ready else 0,
        "blind_case_ids_unique": row_stats["blind_ids_unique"] and ready,
        "packet_ref_ids": row_stats["packet_refs"] if ready else [],
        "packet_ref_id_count": len(row_stats["packet_refs"]) if ready else 0,
        "packet_ref_ids_unique": row_stats["packet_refs_unique"] and ready,
        "reviewed_at_bucket_refs": row_stats["reviewed_at_refs"] if ready else [],
        "reviewed_at_bucket_ref_count": len(row_stats["reviewed_at_refs"]) if ready else 0,
        "reviewed_at_bucket_refs_present": row_stats["reviewed_at_refs_present"] and ready,
        "axis_refs": list(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_ref_count": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_target_thresholds": dict(cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS),
        "verdict_option_refs": list(cr.P7_R54_AHR_CR10_VERDICT_OPTION_REFS),
        "sanitized_reason_id_option_refs": list(cr.P7_R54_AHR_CR10_SANITIZED_REASON_ID_OPTION_REFS),
        "readfeel_blocker_id_option_refs": list(cr.P7_R54_AHR_CR10_READFEEL_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_refs": list(cr.P7_R54_AHR_CR10_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "question_need_primary_class_option_refs": list(cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "ambiguity_kind_option_refs": list(cr.P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_option_refs": list(cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(cr.P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS),
        "plan_candidate_flag_refs": list(cr.P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS),
        "rows_match_24_case_manifest": row_stats["rows_match_manifest"] and ready,
        "rows_bodyfree_only": row_stats["rows_bodyfree_only"] and ready,
        "rows_selection_only": row_stats["rows_selection_only"] and ready,
        "rows_have_actual_person_selection_only_provenance": row_stats["rows_have_actual_provenance"] and ready,
        "rows_have_required_axis_scores": row_stats["rows_have_required_axis_scores"] and ready,
        "rows_have_allowed_verdict_refs": row_stats["rows_have_allowed_verdict_refs"] and ready,
        "rows_have_allowed_question_observation_refs": row_stats["rows_have_allowed_question_refs"] and ready,
        "rows_have_no_body_or_question_or_path_or_hash": row_stats["rows_no_body_question_path_hash"] and ready,
        "sanitized_selection_only_result_rows_intaken_here": ready,
        "actual_sanitized_review_result_rows_intaken_here": ready,
        "actual_human_review_executed_by_person": ready,
        "actual_selection_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "rating_row_normalization_allowed_next": ready,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX09_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX08_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX09_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX08_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX10_STEP_REF if ready else P7_R54_AHR_POST_CR22_EX09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX09")
    return material


def assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX09")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX09_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX09_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX09",
    )
    blockers = list(data.get("sanitized_review_result_rows_intake_blocker_refs") or [])
    ready = len(blockers) == 0
    expected_status = (
        P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_ACCEPTED_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_BLOCKED_STATUS_REF
    )
    if data.get("sanitized_review_result_rows_intake_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX09 status changed")
    if data.get("sanitized_review_result_rows_intake_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX09 ready flag changed")
    if data.get("sanitized_review_result_rows_intake_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX09 blocker count changed")
    if tuple(data.get("sanitized_review_result_rows_intake_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX09_ALLOWED_SANITIZED_ROWS_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX09 allowed status refs changed")
    if ready:
        if data.get("sanitized_review_result_rows_intake_reason_refs") != [P7_R54_AHR_POST_CR22_EX09_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX09_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX10_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 next step changed")
        for key in (
            "sanitized_selection_only_result_rows_intaken_here",
            "actual_sanitized_review_result_rows_intaken_here",
            "actual_human_review_executed_by_person",
            "rating_row_normalization_allowed_next",
            "rows_match_24_case_manifest",
            "rows_bodyfree_only",
            "rows_selection_only",
            "rows_have_actual_person_selection_only_provenance",
            "rows_have_required_axis_scores",
            "rows_have_allowed_verdict_refs",
            "rows_have_allowed_question_observation_refs",
            "rows_have_no_body_or_question_or_path_or_hash",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX09 required true field changed: {key}")
        if data.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 sanitized row count changed")
        if not isinstance(data.get("review_result_rows"), list) or len(data.get("review_result_rows")) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 review rows changed")
    else:
        if data.get("sanitized_review_result_rows_intake_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX09_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 blocked next step changed")
        if data.get("review_result_rows") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 blocked material cannot output rows")
    for key in (
        "actual_selection_rows_created_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "actual_review_evidence_complete",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX09 required false field changed: {key}")
    for row in data.get("review_result_rows") or []:
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-PostCR22-EX09 row must be mapping")
        if row.get("schema_version") != P7_R54_AHR_POST_CR22_EX09_SELECTION_RESULT_ROW_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 row schema changed")
        if row.get("row_source_ref") != P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 row source changed")
        for flag_ref in P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS:
            if row.get(flag_ref) is not False:
                raise ValueError("P7-R54-AHR-PostCR22-EX09 row body-free flag changed")
        if row.get("selection_only") is not True or row.get("selection_only_row") is not True or row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 row selection/body-free flags changed")
        if (row.get("plan_candidate_flags") or {}).get("p8_implementation_spec_finalized_here") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX09 row must not finalize P8 implementation spec")
    return True


# Alias names for the detailed-design wording of EX08 through EX09.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_selection_row_provenance_guard_bodyfree(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    selection_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard(
        actual_operation_receipt_intake=actual_operation_receipt_intake,
        selection_result_rows=selection_result_rows,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_selection_row_provenance_guard_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex08_actual_selection_row_provenance_guard_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_sanitized_review_result_rows_intake_bodyfree(
    *,
    actual_selection_row_provenance_guard: Mapping[str, Any] | None = None,
    selection_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake(
        actual_selection_row_provenance_guard=actual_selection_row_provenance_guard,
        selection_result_rows=selection_result_rows,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_sanitized_review_result_rows_intake_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(data)



# ---------------------------------------------------------------------------
# EX10-EX11 rating row normalization / blocker classification
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex10_rating_row_normalization_threshold_summary.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX10_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex10_rating_row.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex11_readfeel_execution_p5_p4_blocker_classification.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex11_blocker_classification_row.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:11]
P7_R54_AHR_POST_CR22_EX10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[11:]
P7_R54_AHR_POST_CR22_EX11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:12]
P7_R54_AHR_POST_CR22_EX11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[12:]

P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_NORMALIZED_STATUS_REF: Final = (
    "EX10_RATING_ROWS_NORMALIZED_THRESHOLD_SUMMARY_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_BLOCKED_STATUS_REF: Final = (
    "EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX10_ALLOWED_RATING_ROW_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_NORMALIZED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX10_READY_REASON_REF: Final = (
    "EX10_SANITIZED_ACTUAL_SELECTION_ROWS_NORMALIZED_TO_24_RATING_ROWS_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex10_rating_row_normalization_threshold_summary_or_stop"
)
P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_POST_CR22_EX10_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
)

P7_R54_AHR_POST_CR22_EX11_BLOCKERS_CLASSIFIED_STATUS_REF: Final = (
    "EX11_READFEEL_EXECUTION_P5_P4_BLOCKERS_CLASSIFIED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX11_BLOCKERS_BLOCKED_STATUS_REF: Final = (
    "EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX11_ALLOWED_BLOCKER_CLASSIFICATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX11_BLOCKERS_CLASSIFIED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX11_BLOCKERS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX11_READY_REASON_REF: Final = (
    "EX11_24_RATING_ROWS_CLASSIFIED_TO_BODYFREE_READFEEL_EXECUTION_P5_P4_BLOCKERS"
)
P7_R54_AHR_POST_CR22_EX11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex11_readfeel_execution_p5_p4_blocker_classification_or_stop"
)
P7_R54_AHR_POST_CR22_EX11_BLOCKER_STATUS_OPEN_REF: Final = "open_bodyfree_product_or_operation_blocker"
P7_R54_AHR_POST_CR22_EX11_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "readfeel_blocker",
    "execution_blocker",
    "repair_required",
    "below_target_axis",
    "inconclusive_material",
    "verdict_blocker",
)
P7_R54_AHR_POST_CR22_EX11_BLOCKER_CATEGORY_REFS: Final[tuple[str, ...]] = (
    "no_blocker",
    "p5_readfeel_repair_required",
    "p5_history_connection_weak",
    "p5_creepy_or_overclaim_risk",
    "p5_self_blame_amplification_risk",
    "p4_current_only_surface_repair_required",
    "operation_blocked_missing_receipt",
    "operation_blocked_body_leak",
    "operation_blocked_question_text",
    "operation_blocked_disposal_missing",
    "operation_blocked_no_touch_violation",
    "inconclusive_insufficient_material",
)
P7_R54_AHR_POST_CR22_EX11_READFEEL_ROUTE_REF: Final = "P5_READFEEL_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_POST_CR22_EX11_P4_ROUTE_REF: Final = "P4_CURRENT_ONLY_SURFACE_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_POST_CR22_EX11_OPERATION_ROUTE_REF: Final = "R54_OPERATION_BLOCKER_REPAIR_BEFORE_EVIDENCE_COMPLETE"
P7_R54_AHR_POST_CR22_EX11_INCONCLUSIVE_ROUTE_REF: Final = "R54_INCONCLUSIVE_MATERIAL_REVIEW_REQUIRED"
P7_R54_AHR_POST_CR22_EX11_CLEAN_ROUTE_REF: Final = "NO_BLOCKER_CONTINUE_TO_QUESTION_NEED_OBSERVATION_NORMALIZATION"
P7_R54_AHR_POST_CR22_EX11_READFEEL_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = {
    "history_connection_weak": "p5_history_connection_weak",
    "history_line_creepy_or_overread": "p5_creepy_or_overclaim_risk",
    "current_input_overridden_by_history": "p5_creepy_or_overclaim_risk",
    "overclaim_or_unearned_certainty": "p5_creepy_or_overclaim_risk",
    "self_blame_amplified": "p5_self_blame_amplification_risk",
    "shallow_repeat_or_generic": "p5_readfeel_repair_required",
    "wants_less_input_or_no_accumulation": "p5_readfeel_repair_required",
    "boundary_history_line_leak": "p5_creepy_or_overclaim_risk",
}
P7_R54_AHR_POST_CR22_EX11_EXECUTION_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = {
    "packet_missing": "operation_blocked_missing_receipt",
    "packet_not_local_only": "operation_blocked_missing_receipt",
    "case_manifest_incomplete": "operation_blocked_missing_receipt",
    "reviewer_selection_incomplete": "operation_blocked_missing_receipt",
    "forbidden_body_leak": "operation_blocked_body_leak",
    "question_text_leak": "operation_blocked_question_text",
    "disposal_missing": "operation_blocked_disposal_missing",
    "no_touch_violation": "operation_blocked_no_touch_violation",
}
P7_R54_AHR_POST_CR22_EX11_REPAIR_CATEGORY_BY_REF: Final[dict[str, str]] = {
    "emlis_readfeel_repair_required": "p5_readfeel_repair_required",
    "p5_surface_repair_required": "p5_readfeel_repair_required",
    "gate_boundary_repair_required": "p5_readfeel_repair_required",
    "p4_current_surface_repair_required": "p4_current_only_surface_repair_required",
}
P7_R54_AHR_POST_CR22_EX11_BELOW_TARGET_AXIS_CATEGORY_BY_REF: Final[dict[str, str]] = {
    "history_connection_naturalness": "p5_history_connection_weak",
    "creepy_absence": "p5_creepy_or_overclaim_risk",
    "overclaim_absence": "p5_creepy_or_overclaim_risk",
    "self_blame_non_amplification": "p5_self_blame_amplification_risk",
    "wants_more_input_or_accumulation": "p5_readfeel_repair_required",
    "non_shallow_repeat": "p5_readfeel_repair_required",
}
P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_POST_CR22_EX11_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
)

P7_R54_AHR_POST_CR22_EX10_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "axis_scores",
    "axis_targets",
    "axis_score_count",
    "below_target_axis_refs",
    "below_target_axis_ref_count",
    "axis_pass_flags",
    "axis_pass_flag_count",
    "all_axis_scores_at_or_above_target",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "row_source_ref",
    "source_actual_selection_row_provenance_verified",
    "body_free",
    *P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blocker_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "blocker_kind",
    "blocker_category_ref",
    "blocker_id",
    "blocker_status_ref",
    "routes_to",
    "p8_material_candidate_blocked",
    "body_free",
    *P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS,
)

P7_R54_AHR_POST_CR22_EX10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex09_schema_version",
    "ex09_material_ref",
    "ex09_next_required_step",
    "ex09_sanitized_review_result_rows_intake_status_ref",
    "ex09_sanitized_review_result_rows_intake_ready",
    "ex09_rating_row_normalization_allowed_next",
    "ex09_actual_sanitized_review_result_rows_intaken_here",
    "ex09_actual_human_review_executed_by_person",
    "ex09_sanitized_review_result_row_count",
    "operation_receipt_ref",
    "reviewer_person_ref",
    "rating_row_normalization_status_ref",
    "rating_row_normalization_allowed_status_refs",
    "rating_row_normalization_ready",
    "rating_row_normalization_reason_refs",
    "rating_row_normalization_blocker_refs",
    "rating_row_normalization_blocker_ref_count",
    "required_case_count",
    "source_sanitized_review_result_row_count",
    "rating_row_count",
    "rating_rows",
    "rating_row_refs",
    "rating_row_ref_count",
    "source_review_result_row_refs",
    "source_review_result_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "axis_refs",
    "axis_ref_count",
    "axis_score_count_per_row",
    "axis_target_thresholds",
    "average_axis_scores",
    "average_axis_scores_present",
    "all_axis_target_passed",
    "below_target_axis_refs_by_case",
    "below_target_axis_ref_counts",
    "below_target_case_count",
    "axis_pass_flags_present_per_row",
    "rating_rows_bodyfree_only",
    "rating_rows_match_sanitized_review_result_case_refs",
    "rating_rows_have_required_axis_scores",
    "rating_scores_in_range",
    "rating_rows_have_allowed_verdict_refs",
    "verdict_counts",
    "pass_case_count",
    "yellow_case_count",
    "repair_required_case_count",
    "red_case_count",
    "blocked_case_count",
    "not_reviewable_case_count",
    "readfeel_blocker_row_source_count",
    "execution_blocker_row_source_count",
    "repair_required_row_source_count",
    "rating_rows_normalized_here",
    "actual_rating_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "readfeel_execution_blocker_classification_allowed_next",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_CR22_EX11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex10_schema_version",
    "ex10_material_ref",
    "ex10_next_required_step",
    "ex10_rating_row_normalization_status_ref",
    "ex10_rating_row_normalization_ready",
    "ex10_readfeel_execution_blocker_classification_allowed_next",
    "ex10_rating_row_count",
    "ex10_actual_rating_rows_materialized_here",
    "ex10_actual_human_review_executed_by_person",
    "readfeel_execution_p5_p4_blocker_classification_status_ref",
    "readfeel_execution_p5_p4_blocker_classification_allowed_status_refs",
    "readfeel_execution_p5_p4_blocker_classification_ready",
    "readfeel_execution_p5_p4_blocker_classification_reason_refs",
    "readfeel_execution_p5_p4_blocker_classification_blocker_refs",
    "readfeel_execution_p5_p4_blocker_classification_blocker_ref_count",
    "required_case_count",
    "source_rating_row_count",
    "source_rating_row_refs",
    "source_rating_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "blocker_rows",
    "blocker_row_count",
    "blocker_row_refs",
    "blocker_row_ref_count",
    "blocker_kind_refs",
    "blocker_kind_counts",
    "blocker_category_refs",
    "blocker_category_counts",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "repair_required_blocker_row_count",
    "below_target_axis_blocker_row_count",
    "inconclusive_blocker_row_count",
    "verdict_blocker_row_count",
    "readfeel_blocker_id_counts",
    "execution_blocker_id_counts",
    "repair_required_ref_counts",
    "below_target_axis_ref_counts",
    "no_blocker_case_refs",
    "no_blocker_case_count",
    "p5_repair_required_case_refs",
    "p5_repair_required_case_count",
    "p4_current_only_repair_required_case_refs",
    "p4_current_only_repair_required_case_count",
    "operation_blocked_case_refs",
    "operation_blocked_case_count",
    "inconclusive_case_refs",
    "inconclusive_case_count",
    "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only",
    "p8_material_candidate_blocked_by_blocker_case_refs",
    "p8_material_candidate_blocked_by_blocker_case_count",
    "rows_bodyfree_only",
    "rows_have_no_question_text",
    "p5_p4_operation_blockers_not_escaped_to_p8_candidate",
    "readfeel_execution_blockers_classified_here",
    "actual_rating_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "question_need_observation_normalization_allowed_next",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _postcr22_count_values(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get(field) or "")
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _postcr22_count_nested_string_values(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for value in row.get(field) or []:
            key = clean_identifier(value, default="", max_length=180)
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def _postcr22_average_axis_scores(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not rating_rows:
        return {axis_ref: 0.0 for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    averages: dict[str, float] = {}
    for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS:
        total = sum(float((row.get("axis_scores") or {}).get(axis_ref, 0.0)) for row in rating_rows)
        averages[axis_ref] = round(total / len(rating_rows), 4)
    return averages


def _postcr22_below_target_axis_counts(rating_rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {axis_ref: 0 for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}
    for row in rating_rows:
        for axis_ref in row.get("below_target_axis_refs") or []:
            if axis_ref in counts:
                counts[axis_ref] += 1
    return counts


def _postcr22_assert_required_false_flags_except(
    data: Mapping[str, Any], *, source: str, allowed_true_refs: tuple[str, ...] = ()
) -> None:
    allowed = set(allowed_true_refs)
    for key in P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
        if key in allowed:
            continue
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")




def _assert_current_basis_and_claim_boundary(data: Mapping[str, Any], *, source: str) -> None:
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual_review_basis_ref must remain current received snapshot basis")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual_review_basis_allowed_ref must remain current received snapshot basis only")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError(f"{source} local_received_zip_refs must be body-free received labels only")
    if data.get("local_received_zip_ref_count") != len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS):
        raise ValueError(f"{source} local_received_zip_ref_count must match received zip refs")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError(f"{source} must not treat received zip labels as actual review basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_cr_basis") is not False:
        raise ValueError(f"{source} must not rewrite current CR basis from received zip labels")
    if data.get("current_cr_basis_remains_264_85_258_171") is not True:
        raise ValueError(f"{source} must keep current CR basis fixed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS:
        raise ValueError(f"{source} claim_boundary_refs must match Post-CR22 non-promotion boundary")
    if data.get("claim_boundary_ref_count") != len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS):
        raise ValueError(f"{source} claim_boundary_ref_count must match Post-CR22 non-promotion boundary")


def _postcr22_clean_axis_scores(value: Any) -> tuple[dict[str, float], bool, bool]:
    if not isinstance(value, Mapping):
        return {axis_ref: 0.0 for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS}, False, False
    refs_match = set(str(key) for key in value.keys()) == set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
    scores: dict[str, float] = {}
    scores_in_range = True
    for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS:
        try:
            score = float(value.get(axis_ref))
        except (TypeError, ValueError):
            score = -1.0
        if not 0.0 <= score <= 1.0:
            scores_in_range = False
            score = 0.0
        scores[axis_ref] = round(score, 4)
    return scores, refs_match, scores_in_range


def _postcr22_rating_rows_from_ex09_sanitized_rows(
    rows: Sequence[Any], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    rating_rows: list[dict[str, Any]] = []
    expected_manifest = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    expected_by_case = {str(row.get("case_ref_id")): row for row in expected_manifest.get("case_rows", [])}
    seen_case_refs: set[str] = set()
    if len(rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex10_source_sanitized_review_result_row_count_not_24")
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append("ex10_source_sanitized_row_not_mapping")
            continue
        if _forbidden_payload_key_paths(raw_row, path="ex10_source_row"):
            blockers.append("ex10_source_sanitized_row_forbidden_body_question_path_hash_key")
            continue
        if raw_row.get("schema_version") != P7_R54_AHR_POST_CR22_EX09_SELECTION_RESULT_ROW_SCHEMA_VERSION:
            blockers.append("ex10_source_sanitized_row_schema_not_ex09")
            continue
        if raw_row.get("row_source_ref") != P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF:
            blockers.append("ex10_source_sanitized_row_not_actual_person_selection_source")
        if any(raw_row.get(flag_ref) is not False for flag_ref in P7_R54_AHR_POST_CR22_EX09_ROW_BODYFREE_FALSE_FLAG_REFS):
            blockers.append("ex10_source_sanitized_row_bodyfree_forbidden_flag_not_false")
        if raw_row.get("selection_only") is not True or raw_row.get("selection_only_row") is not True:
            blockers.append("ex10_source_sanitized_row_not_selection_only")
        if raw_row.get("body_free") is not True:
            blockers.append("ex10_source_sanitized_row_not_bodyfree")
        axis_scores, axis_refs_match, scores_in_range = _postcr22_clean_axis_scores(raw_row.get("axis_scores"))
        if not axis_refs_match or raw_row.get("axis_score_count") != len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS):
            blockers.append("ex10_source_sanitized_row_axis_refs_mismatch")
        if not scores_in_range:
            blockers.append("ex10_source_sanitized_row_axis_score_invalid")
        verdict = clean_identifier(raw_row.get("verdict"), default="", max_length=80)
        if verdict not in cr.P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
            blockers.append("ex10_source_sanitized_row_verdict_not_allowed")
        case_ref_id = clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120)
        blind_case_id = clean_identifier(raw_row.get("blind_case_id"), default="", max_length=120)
        packet_ref_id = clean_identifier(raw_row.get("packet_ref_id"), default="", max_length=120)
        seen_case_refs.add(case_ref_id)
        expected = expected_by_case.get(case_ref_id)
        if not expected or blind_case_id != expected.get("blind_case_id") or packet_ref_id != expected.get("packet_ref_id"):
            blockers.append("ex10_source_sanitized_row_manifest_id_mismatch")
        axis_targets = dict(cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS)
        below_target_axis_refs = [
            axis_ref
            for axis_ref, target in axis_targets.items()
            if float(axis_scores.get(axis_ref, 0.0)) < float(target)
        ]
        axis_pass_flags = {
            axis_ref: axis_ref not in below_target_axis_refs for axis_ref in cr.P7_R54_AHR_CR08_RATING_AXIS_REFS
        }
        plan_candidate_flags, plan_flags_invalid = _postcr22_clean_plan_candidate_flags(raw_row.get("plan_candidate_flags"))
        if plan_flags_invalid:
            blockers.append("ex10_source_sanitized_row_plan_candidate_flags_invalid")
        rating_row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_POST_CR22_EX10_RATING_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "rating_row_ref": f"postcr22_rating_row_{index:03d}",
            "source_review_result_row_ref": clean_identifier(
                raw_row.get("review_result_row_ref"),
                default=f"postcr22_actual_review_result_row_{index:03d}",
                max_length=180,
            ),
            "case_ref_id": case_ref_id,
            "blind_case_id": blind_case_id,
            "packet_ref_id": packet_ref_id,
            "axis_scores": axis_scores,
            "axis_targets": axis_targets,
            "axis_score_count": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
            "below_target_axis_refs": below_target_axis_refs,
            "below_target_axis_ref_count": len(below_target_axis_refs),
            "axis_pass_flags": axis_pass_flags,
            "axis_pass_flag_count": len(axis_pass_flags),
            "all_axis_scores_at_or_above_target": not below_target_axis_refs,
            "verdict": verdict,
            "sanitized_reason_ids": _clean_string_ref_list(raw_row.get("sanitized_reason_ids"), limit=24, max_length=160),
            "readfeel_blocker_ids": _clean_string_ref_list(raw_row.get("readfeel_blocker_ids"), limit=24, max_length=160),
            "execution_blocker_ids": _clean_string_ref_list(raw_row.get("execution_blocker_ids"), limit=24, max_length=160),
            "question_need_primary_class": clean_identifier(
                raw_row.get("question_need_primary_class"), default="", max_length=180
            ),
            "one_question_fit_ref": clean_identifier(raw_row.get("one_question_fit_ref"), default="", max_length=180),
            "repair_required_refs": _clean_string_ref_list(raw_row.get("repair_required_refs"), limit=24, max_length=180),
            "plan_candidate_flags": plan_candidate_flags,
            "row_source_ref": P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF,
            "source_actual_selection_row_provenance_verified": True,
            "body_free": True,
        }
        rating_row.update({flag_ref: False for flag_ref in P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS})
        rating_rows.append(rating_row)
    expected_case_refs = set(expected_by_case)
    if len(seen_case_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT or seen_case_refs != expected_case_refs:
        blockers.append("ex10_source_sanitized_row_unique_case_refs_not_24")
    blockers = _dedupe_refs(blockers)
    return ([] if blockers else rating_rows), blockers


def build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary(
    *,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX10 body-free rating rows and threshold summary from EX09 rows."""

    ex09 = sanitized_review_result_rows_intake or build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake()
    assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(ex09)
    session_id = _safe_review_session_id(review_session_id or ex09.get("review_session_id"))
    rating_rows, row_blockers = _postcr22_rating_rows_from_ex09_sanitized_rows(
        ex09.get("review_result_rows") or (), review_session_id=session_id
    )
    blockers: list[str] = []
    if ex09.get("schema_version") != P7_R54_AHR_POST_CR22_EX09_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_SCHEMA_VERSION:
        blockers.append("ex09_schema_version_not_current")
    if ex09.get("sanitized_review_result_rows_intake_ready") is not True:
        blockers.append("ex09_sanitized_review_result_rows_not_ready")
    if ex09.get("next_required_step") != P7_R54_AHR_POST_CR22_EX10_STEP_REF:
        blockers.append("ex09_next_step_not_ex10")
    if ex09.get("rating_row_normalization_allowed_next") is not True:
        blockers.append("ex09_rating_row_normalization_not_allowed_next")
    if ex09.get("actual_sanitized_review_result_rows_intaken_here") is not True:
        blockers.append("ex09_actual_sanitized_review_result_rows_not_intaken")
    if ex09.get("actual_human_review_executed_by_person") is not True:
        blockers.append("ex09_actual_human_review_executed_by_person_not_confirmed")
    if ex09.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex09_sanitized_review_result_row_count_not_24")
    blockers.extend(row_blockers)
    blockers = _dedupe_refs(blockers)
    ready = not blockers
    rows_for_output = rating_rows if ready else []
    source_rows = ex09.get("review_result_rows") or []
    verdict_counts = _postcr22_count_values(rows_for_output, "verdict") if ready else {}
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    blind_refs = [str(row.get("blind_case_id")) for row in rows_for_output]
    packet_refs = [str(row.get("packet_ref_id")) for row in rows_for_output]
    source_review_refs = [str(row.get("source_review_result_row_ref")) for row in rows_for_output]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX10_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex09_schema_version": ex09.get("schema_version"),
        "ex09_material_ref": ex09.get("material_id", "postcr22_ex09_sanitized_review_result_rows_intake_bodyfree"),
        "ex09_next_required_step": ex09.get("next_required_step"),
        "ex09_sanitized_review_result_rows_intake_status_ref": ex09.get("sanitized_review_result_rows_intake_status_ref"),
        "ex09_sanitized_review_result_rows_intake_ready": ex09.get("sanitized_review_result_rows_intake_ready") is True,
        "ex09_rating_row_normalization_allowed_next": ex09.get("rating_row_normalization_allowed_next") is True,
        "ex09_actual_sanitized_review_result_rows_intaken_here": ex09.get("actual_sanitized_review_result_rows_intaken_here") is True,
        "ex09_actual_human_review_executed_by_person": ex09.get("actual_human_review_executed_by_person") is True,
        "ex09_sanitized_review_result_row_count": _int_value_or_zero(ex09.get("sanitized_review_result_row_count")),
        "operation_receipt_ref": clean_identifier(ex09.get("operation_receipt_ref"), default="", max_length=240),
        "reviewer_person_ref": clean_identifier(ex09.get("reviewer_person_ref"), default="", max_length=220),
        "rating_row_normalization_status_ref": (
            P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_NORMALIZED_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_BLOCKED_STATUS_REF
        ),
        "rating_row_normalization_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX10_ALLOWED_RATING_ROW_STATUS_REFS),
        "rating_row_normalization_ready": ready,
        "rating_row_normalization_reason_refs": [P7_R54_AHR_POST_CR22_EX10_READY_REASON_REF] if ready else [],
        "rating_row_normalization_blocker_refs": blockers,
        "rating_row_normalization_blocker_ref_count": len(blockers),
        "required_case_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "source_sanitized_review_result_row_count": len(source_rows) if ready else 0,
        "rating_row_count": len(rows_for_output),
        "rating_rows": rows_for_output,
        "rating_row_refs": [str(row.get("rating_row_ref")) for row in rows_for_output],
        "rating_row_ref_count": len(rows_for_output),
        "source_review_result_row_refs": source_review_refs,
        "source_review_result_row_ref_count": len(source_review_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "blind_case_ids": blind_refs,
        "blind_case_id_count": len(blind_refs),
        "blind_case_ids_unique": len(set(blind_refs)) == len(blind_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "axis_refs": list(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_ref_count": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS) if ready else 0,
        "axis_target_thresholds": dict(cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS),
        "average_axis_scores": _postcr22_average_axis_scores(rows_for_output),
        "average_axis_scores_present": ready,
        "all_axis_target_passed": all(row.get("all_axis_scores_at_or_above_target") is True for row in rows_for_output) if ready else False,
        "below_target_axis_refs_by_case": {
            str(row.get("case_ref_id")): list(row.get("below_target_axis_refs") or []) for row in rows_for_output
        },
        "below_target_axis_ref_counts": _postcr22_below_target_axis_counts(rows_for_output),
        "below_target_case_count": sum(1 for row in rows_for_output if row.get("below_target_axis_refs")),
        "axis_pass_flags_present_per_row": all(
            set((row.get("axis_pass_flags") or {}).keys()) == set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
            for row in rows_for_output
        ) if ready else False,
        "rating_rows_bodyfree_only": all(row.get("body_free") is True for row in rows_for_output) if ready else False,
        "rating_rows_match_sanitized_review_result_case_refs": (
            set(case_refs) == set(str(row.get("case_ref_id")) for row in source_rows)
            and len(case_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT
            if ready
            else False
        ),
        "rating_rows_have_required_axis_scores": all(
            set((row.get("axis_scores") or {}).keys()) == set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS)
            for row in rows_for_output
        ) if ready else False,
        "rating_scores_in_range": all(
            0.0 <= float(score) <= 1.0
            for row in rows_for_output
            for score in (row.get("axis_scores") or {}).values()
        ) if ready else False,
        "rating_rows_have_allowed_verdict_refs": all(
            row.get("verdict") in cr.P7_R54_AHR_CR10_VERDICT_OPTION_REFS for row in rows_for_output
        ) if ready else False,
        "verdict_counts": verdict_counts,
        "pass_case_count": verdict_counts.get("PASS", 0),
        "yellow_case_count": verdict_counts.get("YELLOW", 0),
        "repair_required_case_count": verdict_counts.get("REPAIR_REQUIRED", 0),
        "red_case_count": verdict_counts.get("RED", 0),
        "blocked_case_count": verdict_counts.get("BLOCKED", 0),
        "not_reviewable_case_count": verdict_counts.get("NOT_REVIEWABLE", 0),
        "readfeel_blocker_row_source_count": sum(len(row.get("readfeel_blocker_ids") or []) for row in rows_for_output),
        "execution_blocker_row_source_count": sum(len(row.get("execution_blocker_ids") or []) for row in rows_for_output),
        "repair_required_row_source_count": sum(
            len([ref for ref in row.get("repair_required_refs") or [] if ref != "no_repair_required"])
            for row in rows_for_output
        ),
        "rating_rows_normalized_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_human_review_executed_by_person": ex09.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "readfeel_execution_blocker_classification_allowed_next": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX10_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX09_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX09_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX11_STEP_REF if ready else P7_R54_AHR_POST_CR22_EX10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_rating_rows_materialized_here"] = ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_question_need_observation_rows_materialized_here"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX10_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX10")
    return material


def assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX10_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX10")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX10_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX10",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX10_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX10")
    blockers = list(data.get("rating_row_normalization_blocker_refs") or [])
    ready = len(blockers) == 0
    expected_status = (
        P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_NORMALIZED_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_BLOCKED_STATUS_REF
    )
    if data.get("rating_row_normalization_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX10 status changed")
    if data.get("rating_row_normalization_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX10 ready flag changed")
    if tuple(data.get("rating_row_normalization_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX10_ALLOWED_RATING_ROW_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX10 allowed status refs changed")
    if data.get("rating_row_normalization_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX10 blocker count changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX10",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX10_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX10 required false field changed: {key}")
    for key in (
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX10 required true boundary changed: {key}")
    if ready:
        if data.get("rating_row_normalization_reason_refs") != [P7_R54_AHR_POST_CR22_EX10_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX10_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX11_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 next step changed")
        for field in (
            "source_sanitized_review_result_row_count",
            "rating_row_count",
            "rating_row_ref_count",
            "source_review_result_row_ref_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX10 {field} changed")
        for key in (
            "ex09_sanitized_review_result_rows_intake_ready",
            "ex09_rating_row_normalization_allowed_next",
            "ex09_actual_sanitized_review_result_rows_intaken_here",
            "ex09_actual_human_review_executed_by_person",
            "case_ref_ids_unique",
            "blind_case_ids_unique",
            "packet_ref_ids_unique",
            "average_axis_scores_present",
            "axis_pass_flags_present_per_row",
            "rating_rows_bodyfree_only",
            "rating_rows_match_sanitized_review_result_case_refs",
            "rating_rows_have_required_axis_scores",
            "rating_scores_in_range",
            "rating_rows_have_allowed_verdict_refs",
            "rating_rows_normalized_here",
            "actual_rating_rows_materialized_here",
            "actual_human_review_executed_by_person",
            "readfeel_execution_blocker_classification_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX10 required true field changed: {key}")
        if tuple(data.get("axis_refs") or ()) != cr.P7_R54_AHR_CR08_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 axis refs changed")
        if data.get("axis_target_thresholds") != cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 axis target thresholds changed")
        if not isinstance(data.get("rating_rows"), list) or len(data.get("rating_rows")) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 rating rows changed")
        for row in data.get("rating_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row must be mapping")
            _required_fields_present(
                row,
                required=P7_R54_AHR_POST_CR22_EX10_RATING_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-PostCR22-EX10-rating-row",
            )
            if row.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row must remain body-free")
            if row.get("row_source_ref") != P7_R54_AHR_POST_CR22_EX08_ALLOWED_ROW_SOURCE_REF:
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row source changed")
            if row.get("source_actual_selection_row_provenance_verified") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX10 source provenance flag changed")
            for flag_ref in P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row body-free flag changed")
            if set((row.get("axis_scores") or {}).keys()) != set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row axis refs changed")
            if row.get("axis_targets") != cr.P7_R54_AHR_CR08_RATING_AXIS_TARGET_THRESHOLDS:
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row axis targets changed")
            if row.get("axis_score_count") != len(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row axis score count changed")
            if row.get("verdict") not in cr.P7_R54_AHR_CR10_VERDICT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row verdict changed")
            if set(row.get("axis_pass_flags") or {}) != set(cr.P7_R54_AHR_CR08_RATING_AXIS_REFS):
                raise ValueError("P7-R54-AHR-PostCR22-EX10 rating row pass flag refs changed")
    else:
        if data.get("rating_row_normalization_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 blocked material cannot carry ready reasons")
        if data.get("rating_rows") != [] or data.get("rating_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 blocked material cannot output rating rows")
        if data.get("actual_rating_rows_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 blocked material cannot materialize rating rows")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX10_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX10 blocked next step changed")
    return True


def _postcr22_ex11_routes_to(category_ref: str) -> str:
    if category_ref == "no_blocker":
        return P7_R54_AHR_POST_CR22_EX11_CLEAN_ROUTE_REF
    if category_ref == "p4_current_only_surface_repair_required":
        return P7_R54_AHR_POST_CR22_EX11_P4_ROUTE_REF
    if category_ref.startswith("operation_blocked_"):
        return P7_R54_AHR_POST_CR22_EX11_OPERATION_ROUTE_REF
    if category_ref == "inconclusive_insufficient_material":
        return P7_R54_AHR_POST_CR22_EX11_INCONCLUSIVE_ROUTE_REF
    return P7_R54_AHR_POST_CR22_EX11_READFEEL_ROUTE_REF


def _postcr22_make_ex11_blocker_row(
    *,
    seq: int,
    source_row: Mapping[str, Any],
    review_session_id: str,
    blocker_kind: str,
    blocker_category_ref: str,
    blocker_id: str,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_SCHEMA_VERSION,
        "review_session_id": review_session_id,
        "blocker_row_ref": f"postcr22_blocker_row_{seq:03d}",
        "source_rating_row_ref": clean_identifier(source_row.get("rating_row_ref"), default=f"postcr22_rating_row_{seq:03d}", max_length=180),
        "source_review_result_row_ref": clean_identifier(
            source_row.get("source_review_result_row_ref"),
            default=f"postcr22_actual_review_result_row_{seq:03d}",
            max_length=180,
        ),
        "case_ref_id": clean_identifier(source_row.get("case_ref_id"), default="", max_length=120),
        "blind_case_id": clean_identifier(source_row.get("blind_case_id"), default="", max_length=120),
        "packet_ref_id": clean_identifier(source_row.get("packet_ref_id"), default="", max_length=120),
        "blocker_kind": blocker_kind,
        "blocker_category_ref": blocker_category_ref,
        "blocker_id": clean_identifier(blocker_id, default="unknown_blocker", max_length=180),
        "blocker_status_ref": P7_R54_AHR_POST_CR22_EX11_BLOCKER_STATUS_OPEN_REF,
        "routes_to": _postcr22_ex11_routes_to(blocker_category_ref),
        "p8_material_candidate_blocked": True,
        "body_free": True,
    }
    row.update({flag_ref: False for flag_ref in P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS})
    return row


def _postcr22_blocker_rows_from_ex10_rating_rows(
    rating_rows: Sequence[Any], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[str], set[str], set[str]]:
    blockers: list[str] = []
    blocker_rows: list[dict[str, Any]] = []
    expected_manifest = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    expected_case_refs = {str(row.get("case_ref_id")) for row in expected_manifest.get("case_rows", [])}
    seen_case_refs: set[str] = set()
    blocked_case_refs: set[str] = set()
    p8_candidate_case_refs: set[str] = set()
    seq = 1
    if len(rating_rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex11_source_rating_row_count_not_24")
    for raw_row in rating_rows:
        if not isinstance(raw_row, Mapping):
            blockers.append("ex11_source_rating_row_not_mapping")
            continue
        if _forbidden_payload_key_paths(raw_row, path="ex11_source_rating_row"):
            blockers.append("ex11_source_rating_row_forbidden_body_question_path_hash_key")
            continue
        if raw_row.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_SCHEMA_VERSION:
            blockers.append("ex11_source_rating_row_schema_not_ex10")
        if raw_row.get("body_free") is not True:
            blockers.append("ex11_source_rating_row_not_bodyfree")
        if any(raw_row.get(flag_ref) is not False for flag_ref in P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS):
            blockers.append("ex11_source_rating_row_bodyfree_forbidden_flag_not_false")
        case_ref_id = clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120)
        seen_case_refs.add(case_ref_id)
        if case_ref_id not in expected_case_refs:
            blockers.append("ex11_source_rating_row_case_ref_not_in_manifest")
        case_had_blocker = False
        for blocker_id in _clean_string_ref_list(raw_row.get("readfeel_blocker_ids"), limit=24, max_length=160):
            category = P7_R54_AHR_POST_CR22_EX11_READFEEL_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                blockers.append("ex11_readfeel_blocker_id_not_allowed")
                continue
            blocker_rows.append(
                _postcr22_make_ex11_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="readfeel_blocker",
                    blocker_category_ref=category,
                    blocker_id=blocker_id,
                )
            )
            seq += 1
            case_had_blocker = True
        for blocker_id in _clean_string_ref_list(raw_row.get("execution_blocker_ids"), limit=24, max_length=160):
            category = P7_R54_AHR_POST_CR22_EX11_EXECUTION_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                blockers.append("ex11_execution_blocker_id_not_allowed")
                continue
            blocker_rows.append(
                _postcr22_make_ex11_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="execution_blocker",
                    blocker_category_ref=category,
                    blocker_id=blocker_id,
                )
            )
            seq += 1
            case_had_blocker = True
        for repair_ref in _clean_string_ref_list(raw_row.get("repair_required_refs"), limit=24, max_length=180):
            if repair_ref == "no_repair_required":
                continue
            category = P7_R54_AHR_POST_CR22_EX11_REPAIR_CATEGORY_BY_REF.get(repair_ref)
            if not category:
                blockers.append("ex11_repair_required_ref_not_allowed")
                continue
            blocker_rows.append(
                _postcr22_make_ex11_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="repair_required",
                    blocker_category_ref=category,
                    blocker_id=repair_ref,
                )
            )
            seq += 1
            case_had_blocker = True
        for axis_ref in _clean_string_ref_list(raw_row.get("below_target_axis_refs"), limit=24, max_length=160):
            category = P7_R54_AHR_POST_CR22_EX11_BELOW_TARGET_AXIS_CATEGORY_BY_REF.get(axis_ref)
            if not category:
                continue
            blocker_rows.append(
                _postcr22_make_ex11_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="below_target_axis",
                    blocker_category_ref=category,
                    blocker_id=f"below_target_axis_{axis_ref}",
                )
            )
            seq += 1
            case_had_blocker = True
        verdict = clean_identifier(raw_row.get("verdict"), default="", max_length=80)
        primary_class = clean_identifier(raw_row.get("question_need_primary_class"), default="", max_length=180)
        if primary_class == "insufficient_material_execution_blocker" or verdict == "NOT_REVIEWABLE":
            blocker_rows.append(
                _postcr22_make_ex11_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="inconclusive_material",
                    blocker_category_ref="inconclusive_insufficient_material",
                    blocker_id="insufficient_material_execution_blocker",
                )
            )
            seq += 1
            case_had_blocker = True
        elif verdict in {"REPAIR_REQUIRED", "RED"} and not case_had_blocker:
            blocker_rows.append(
                _postcr22_make_ex11_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="verdict_blocker",
                    blocker_category_ref="p5_readfeel_repair_required",
                    blocker_id=f"verdict_{verdict.lower()}",
                )
            )
            seq += 1
            case_had_blocker = True
        elif verdict == "BLOCKED" and not case_had_blocker:
            blocker_rows.append(
                _postcr22_make_ex11_blocker_row(
                    seq=seq,
                    source_row=raw_row,
                    review_session_id=review_session_id,
                    blocker_kind="verdict_blocker",
                    blocker_category_ref="operation_blocked_missing_receipt",
                    blocker_id="verdict_blocked",
                )
            )
            seq += 1
            case_had_blocker = True
        if case_had_blocker:
            blocked_case_refs.add(case_ref_id)
        plan_flags = raw_row.get("plan_candidate_flags") if isinstance(raw_row.get("plan_candidate_flags"), Mapping) else {}
        p8_signal = (
            primary_class in {"question_may_reduce_overread_risk", "plus_single_question_candidate_later", "premium_deep_dive_candidate_later"}
            or plan_flags.get("p8_design_material_candidate") is True
        )
        if (
            p8_signal
            and clean_identifier(raw_row.get("one_question_fit_ref"), default="", max_length=180) == "fits_one_question"
            and verdict not in {"RED", "REPAIR_REQUIRED", "BLOCKED", "NOT_REVIEWABLE"}
            and not case_had_blocker
        ):
            p8_candidate_case_refs.add(case_ref_id)
    if len(seen_case_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT or seen_case_refs != expected_case_refs:
        blockers.append("ex11_source_rating_row_unique_case_refs_not_24")
    blockers = _dedupe_refs(blockers)
    return ([] if blockers else blocker_rows), blockers, blocked_case_refs, p8_candidate_case_refs


def _postcr22_case_refs_for_blocker_categories(rows: Sequence[Mapping[str, Any]], categories: set[str]) -> list[str]:
    refs = sorted({str(row.get("case_ref_id")) for row in rows if row.get("blocker_category_ref") in categories})
    return [ref for ref in refs if ref]


def build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
    *,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX11 body-free readfeel / execution / P5 / P4 blocker classification."""

    ex10 = rating_row_normalization_threshold_summary or build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary()
    assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(ex10)
    session_id = _safe_review_session_id(review_session_id or ex10.get("review_session_id"))
    blocker_rows, row_blockers, blocked_cases_from_rows, p8_candidate_cases = _postcr22_blocker_rows_from_ex10_rating_rows(
        ex10.get("rating_rows") or (), review_session_id=session_id
    )
    blockers: list[str] = []
    if ex10.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION:
        blockers.append("ex10_schema_version_not_current")
    if ex10.get("rating_row_normalization_ready") is not True:
        blockers.append("ex10_rating_rows_not_ready")
    if ex10.get("next_required_step") != P7_R54_AHR_POST_CR22_EX11_STEP_REF:
        blockers.append("ex10_next_step_not_ex11")
    if ex10.get("readfeel_execution_blocker_classification_allowed_next") is not True:
        blockers.append("ex10_readfeel_execution_blocker_classification_not_allowed_next")
    if ex10.get("actual_rating_rows_materialized_here") is not True:
        blockers.append("ex10_actual_rating_rows_not_materialized")
    if ex10.get("actual_human_review_executed_by_person") is not True:
        blockers.append("ex10_actual_human_review_executed_by_person_not_confirmed")
    if ex10.get("rating_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex10_rating_row_count_not_24")
    blockers.extend(row_blockers)
    blockers = _dedupe_refs(blockers)
    ready = not blockers
    rows_for_output = blocker_rows if ready else []
    rating_rows = ex10.get("rating_rows") or []
    source_refs = [str(row.get("rating_row_ref")) for row in rating_rows] if ready else []
    case_refs = [str(row.get("case_ref_id")) for row in rating_rows] if ready else []
    kind_counts = _postcr22_count_values(rows_for_output, "blocker_kind") if ready else {}
    category_counts = _postcr22_count_values(rows_for_output, "blocker_category_ref") if ready else {}
    for category_ref in P7_R54_AHR_POST_CR22_EX11_BLOCKER_CATEGORY_REFS:
        category_counts.setdefault(category_ref, 0)
    category_counts = dict(sorted(category_counts.items()))
    p5_case_refs = _postcr22_case_refs_for_blocker_categories(
        rows_for_output,
        {
            "p5_readfeel_repair_required",
            "p5_history_connection_weak",
            "p5_creepy_or_overclaim_risk",
            "p5_self_blame_amplification_risk",
        },
    )
    p4_case_refs = _postcr22_case_refs_for_blocker_categories(rows_for_output, {"p4_current_only_surface_repair_required"})
    operation_case_refs = _postcr22_case_refs_for_blocker_categories(
        rows_for_output,
        {
            "operation_blocked_missing_receipt",
            "operation_blocked_body_leak",
            "operation_blocked_question_text",
            "operation_blocked_disposal_missing",
            "operation_blocked_no_touch_violation",
        },
    )
    inconclusive_case_refs = _postcr22_case_refs_for_blocker_categories(rows_for_output, {"inconclusive_insufficient_material"})
    all_blocker_case_refs = sorted(set(p5_case_refs) | set(p4_case_refs) | set(operation_case_refs) | set(inconclusive_case_refs) | blocked_cases_from_rows)
    no_blocker_case_refs = sorted(set(case_refs) - set(all_blocker_case_refs)) if ready else []
    category_counts["no_blocker"] = len(no_blocker_case_refs)
    p8_candidates = sorted(set(p8_candidate_cases) - set(all_blocker_case_refs)) if ready else []
    p8_blocked_by_blocker = sorted(set(p8_candidate_cases) & set(all_blocker_case_refs)) if ready else []
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX11_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex10_schema_version": ex10.get("schema_version"),
        "ex10_material_ref": ex10.get("material_id", "postcr22_ex10_rating_row_normalization_threshold_summary_bodyfree"),
        "ex10_next_required_step": ex10.get("next_required_step"),
        "ex10_rating_row_normalization_status_ref": ex10.get("rating_row_normalization_status_ref"),
        "ex10_rating_row_normalization_ready": ex10.get("rating_row_normalization_ready") is True,
        "ex10_readfeel_execution_blocker_classification_allowed_next": ex10.get("readfeel_execution_blocker_classification_allowed_next") is True,
        "ex10_rating_row_count": _int_value_or_zero(ex10.get("rating_row_count")),
        "ex10_actual_rating_rows_materialized_here": ex10.get("actual_rating_rows_materialized_here") is True,
        "ex10_actual_human_review_executed_by_person": ex10.get("actual_human_review_executed_by_person") is True,
        "readfeel_execution_p5_p4_blocker_classification_status_ref": (
            P7_R54_AHR_POST_CR22_EX11_BLOCKERS_CLASSIFIED_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX11_BLOCKERS_BLOCKED_STATUS_REF
        ),
        "readfeel_execution_p5_p4_blocker_classification_allowed_status_refs": list(
            P7_R54_AHR_POST_CR22_EX11_ALLOWED_BLOCKER_CLASSIFICATION_STATUS_REFS
        ),
        "readfeel_execution_p5_p4_blocker_classification_ready": ready,
        "readfeel_execution_p5_p4_blocker_classification_reason_refs": [P7_R54_AHR_POST_CR22_EX11_READY_REASON_REF] if ready else [],
        "readfeel_execution_p5_p4_blocker_classification_blocker_refs": blockers,
        "readfeel_execution_p5_p4_blocker_classification_blocker_ref_count": len(blockers),
        "required_case_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "source_rating_row_count": len(rating_rows) if ready else 0,
        "source_rating_row_refs": source_refs,
        "source_rating_row_ref_count": len(source_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "blocker_rows": rows_for_output,
        "blocker_row_count": len(rows_for_output),
        "blocker_row_refs": [str(row.get("blocker_row_ref")) for row in rows_for_output],
        "blocker_row_ref_count": len(rows_for_output),
        "blocker_kind_refs": list(P7_R54_AHR_POST_CR22_EX11_BLOCKER_KIND_REFS),
        "blocker_kind_counts": kind_counts,
        "blocker_category_refs": list(P7_R54_AHR_POST_CR22_EX11_BLOCKER_CATEGORY_REFS),
        "blocker_category_counts": category_counts,
        "readfeel_blocker_row_count": kind_counts.get("readfeel_blocker", 0),
        "execution_blocker_row_count": kind_counts.get("execution_blocker", 0),
        "repair_required_blocker_row_count": kind_counts.get("repair_required", 0),
        "below_target_axis_blocker_row_count": kind_counts.get("below_target_axis", 0),
        "inconclusive_blocker_row_count": kind_counts.get("inconclusive_material", 0),
        "verdict_blocker_row_count": kind_counts.get("verdict_blocker", 0),
        "readfeel_blocker_id_counts": _postcr22_count_nested_string_values(rating_rows, "readfeel_blocker_ids") if ready else {},
        "execution_blocker_id_counts": _postcr22_count_nested_string_values(rating_rows, "execution_blocker_ids") if ready else {},
        "repair_required_ref_counts": _postcr22_count_nested_string_values(rating_rows, "repair_required_refs") if ready else {},
        "below_target_axis_ref_counts": _postcr22_count_nested_string_values(rating_rows, "below_target_axis_refs") if ready else {},
        "no_blocker_case_refs": no_blocker_case_refs,
        "no_blocker_case_count": len(no_blocker_case_refs),
        "p5_repair_required_case_refs": p5_case_refs,
        "p5_repair_required_case_count": len(p5_case_refs),
        "p4_current_only_repair_required_case_refs": p4_case_refs,
        "p4_current_only_repair_required_case_count": len(p4_case_refs),
        "operation_blocked_case_refs": operation_case_refs,
        "operation_blocked_case_count": len(operation_case_refs),
        "inconclusive_case_refs": inconclusive_case_refs,
        "inconclusive_case_count": len(inconclusive_case_refs),
        "p8_material_candidate_case_refs_bodyfree_only": p8_candidates,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_candidates),
        "p8_material_candidate_blocked_by_blocker_case_refs": p8_blocked_by_blocker,
        "p8_material_candidate_blocked_by_blocker_case_count": len(p8_blocked_by_blocker),
        "rows_bodyfree_only": all(row.get("body_free") is True for row in rows_for_output) if ready else False,
        "rows_have_no_question_text": all(row.get("question_text_included") is False and row.get("draft_question_text_included") is False for row in rows_for_output) if ready else False,
        "p5_p4_operation_blockers_not_escaped_to_p8_candidate": not (set(p8_candidates) & set(all_blocker_case_refs)) if ready else False,
        "readfeel_execution_blockers_classified_here": ready,
        "actual_rating_rows_materialized_here": ex10.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_human_review_executed_by_person": ex10.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "question_need_observation_normalization_allowed_next": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX11_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX10_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX10_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX12_STEP_REF if ready else P7_R54_AHR_POST_CR22_EX11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_rating_rows_materialized_here"] = ex10.get("actual_rating_rows_materialized_here") is True and ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_question_need_observation_rows_materialized_here"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX11_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX11")
    return material


def assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX11_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX11")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX11_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX11",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX11_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX11")
    blockers = list(data.get("readfeel_execution_p5_p4_blocker_classification_blocker_refs") or [])
    ready = len(blockers) == 0
    expected_status = (
        P7_R54_AHR_POST_CR22_EX11_BLOCKERS_CLASSIFIED_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX11_BLOCKERS_BLOCKED_STATUS_REF
    )
    if data.get("readfeel_execution_p5_p4_blocker_classification_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX11 status changed")
    if data.get("readfeel_execution_p5_p4_blocker_classification_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX11 ready flag changed")
    if tuple(data.get("readfeel_execution_p5_p4_blocker_classification_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX11_ALLOWED_BLOCKER_CLASSIFICATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX11 allowed status refs changed")
    if data.get("readfeel_execution_p5_p4_blocker_classification_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker count changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX11",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX11_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX11 required false field changed: {key}")
    for key in (
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX11 required true boundary changed: {key}")
    if ready:
        if data.get("readfeel_execution_p5_p4_blocker_classification_reason_refs") != [P7_R54_AHR_POST_CR22_EX11_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX11_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX12_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 next step changed")
        for field in ("source_rating_row_count", "source_rating_row_ref_count", "case_ref_id_count"):
            if data.get(field) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX11 {field} changed")
        for key in (
            "ex10_rating_row_normalization_ready",
            "ex10_readfeel_execution_blocker_classification_allowed_next",
            "ex10_actual_rating_rows_materialized_here",
            "ex10_actual_human_review_executed_by_person",
            "case_ref_ids_unique",
            "rows_bodyfree_only",
            "rows_have_no_question_text",
            "p5_p4_operation_blockers_not_escaped_to_p8_candidate",
            "readfeel_execution_blockers_classified_here",
            "actual_rating_rows_materialized_here",
            "actual_human_review_executed_by_person",
            "question_need_observation_normalization_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX11 required true field changed: {key}")
        if tuple(data.get("blocker_kind_refs") or ()) != P7_R54_AHR_POST_CR22_EX11_BLOCKER_KIND_REFS:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker kind refs changed")
        if tuple(data.get("blocker_category_refs") or ()) != P7_R54_AHR_POST_CR22_EX11_BLOCKER_CATEGORY_REFS:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker category refs changed")
        if data.get("blocker_row_ref_count") != len(data.get("blocker_rows") or []):
            raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker row count changed")
        for row in data.get("blocker_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker row must be mapping")
            _required_fields_present(
                row,
                required=P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-PostCR22-EX11-blocker-row",
            )
            if row.get("schema_version") != P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker row must remain body-free")
            if row.get("blocker_kind") not in P7_R54_AHR_POST_CR22_EX11_BLOCKER_KIND_REFS:
                raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker kind changed")
            if row.get("blocker_category_ref") not in P7_R54_AHR_POST_CR22_EX11_BLOCKER_CATEGORY_REFS:
                raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker category changed")
            if row.get("blocker_status_ref") != P7_R54_AHR_POST_CR22_EX11_BLOCKER_STATUS_OPEN_REF:
                raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker status changed")
            if row.get("p8_material_candidate_blocked") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker row must block P8 candidate")
            for flag_ref in P7_R54_AHR_POST_CR22_EX11_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError("P7-R54-AHR-PostCR22-EX11 blocker row body-free flag changed")
    else:
        if data.get("readfeel_execution_p5_p4_blocker_classification_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 blocked material cannot carry ready reasons")
        if data.get("blocker_rows") != [] or data.get("source_rating_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 blocked material cannot output classification rows")
        if data.get("actual_rating_rows_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 blocked material cannot claim rating materialization")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX11_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX11 blocked next step changed")
    return True


# Alias names for the detailed-design wording of EX10 through EX11.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_row_normalization_threshold_summary_bodyfree(
    *,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_row_normalization_threshold_summary_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_readfeel_execution_p5_p4_blocker_classification_bodyfree(
    *,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification(
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_readfeel_execution_p5_p4_blocker_classification_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(data)


# ---------------------------------------------------------------------------
# EX12-EX13 question need observation / rating-question consistency guard
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex12_question_need_observation_normalization.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex12_question_need_observation_row.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex13_rating_question_consistency_guard.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex13_rating_question_consistency_issue_row.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:13]
P7_R54_AHR_POST_CR22_EX12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[13:]
P7_R54_AHR_POST_CR22_EX13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:14]
P7_R54_AHR_POST_CR22_EX13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[14:]

P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF: Final = (
    "EX12_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF: Final = (
    "EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX12_ALLOWED_QUESTION_OBSERVATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX12_READY_REASON_REF: Final = (
    "EX12_24_BODYFREE_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_WITHOUT_QUESTION_TEXT"
)
P7_R54_AHR_POST_CR22_EX12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex12_question_need_observation_normalization_or_stop"
)
P7_R54_AHR_POST_CR22_EX12_P8_MATERIAL_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_AHR_POST_CR22_EX12_P5_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R54_AHR_POST_CR22_EX12_P8_MATERIAL_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "fits_one_question",
)
P7_R54_AHR_POST_CR22_EX12_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)
P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS
)

P7_R54_AHR_POST_CR22_EX13_GUARD_PASSED_STATUS_REF: Final = (
    "EX13_RATING_QUESTION_CONSISTENCY_GUARD_PASSED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX13_GUARD_FAILED_STATUS_REF: Final = (
    "EX13_RATING_QUESTION_CONSISTENCY_GUARD_FAILED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX13_GUARD_BLOCKED_STATUS_REF: Final = (
    "EX13_RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX13_ALLOWED_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX13_GUARD_PASSED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX13_GUARD_FAILED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX13_GUARD_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX13_READY_REASON_REF: Final = (
    "EX13_RATING_QUESTION_CONSISTENCY_GUARD_PASSED_NO_ISSUES"
)
P7_R54_AHR_POST_CR22_EX13_FAILED_REASON_REF: Final = (
    "EX13_RATING_QUESTION_CONSISTENCY_ISSUES_BLOCK_EVIDENCE_COMPLETE"
)
P7_R54_AHR_POST_CR22_EX13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex13_rating_question_consistency_guard_or_stop"
)
P7_R54_AHR_POST_CR22_EX13_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF: Final = "repair_or_blocker_p8_candidate_escape"
P7_R54_AHR_POST_CR22_EX13_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF: Final = "rating_below_target_p8_candidate_escape"
P7_R54_AHR_POST_CR22_EX13_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF: Final = "creepy_or_overclaim_risk_question_escape"
P7_R54_AHR_POST_CR22_EX13_ISSUE_SELF_BLAME_P8_ESCAPE_REF: Final = "self_blame_risk_question_escape"
P7_R54_AHR_POST_CR22_EX13_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF: Final = "immediate_observation_heavy_p8_candidate_escape"
P7_R54_AHR_POST_CR22_EX13_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF: Final = "insufficient_material_p8_candidate_escape"
P7_R54_AHR_POST_CR22_EX13_ISSUE_REASON_CHANGED_REF: Final = "p8_candidate_reason_inconsistent_with_question_observation"
P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_TYPE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX13_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF,
    P7_R54_AHR_POST_CR22_EX13_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF,
    P7_R54_AHR_POST_CR22_EX13_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF,
    P7_R54_AHR_POST_CR22_EX13_ISSUE_SELF_BLAME_P8_ESCAPE_REF,
    P7_R54_AHR_POST_CR22_EX13_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF,
    P7_R54_AHR_POST_CR22_EX13_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF,
    P7_R54_AHR_POST_CR22_EX13_ISSUE_REASON_CHANGED_REF,
)
P7_R54_AHR_POST_CR22_EX13_RISK_AXIS_REFS: Final[tuple[str, ...]] = (
    "creepy_absence",
    "overclaim_absence",
    "self_blame_non_amplification",
)
P7_R54_AHR_POST_CR22_EX13_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)
P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX10_ROW_BODYFREE_FALSE_FLAG_REFS
)

P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "question_need_observation_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "verdict",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "ambiguity_kind_ref_count",
    "one_question_fit_ref",
    "repair_required_refs",
    "repair_required_ref_count",
    "plan_candidate_flags",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "question_may_reduce_overread_risk",
    "p8_design_material_candidate",
    "p8_material_candidate_reason_ref",
    "p8_implementation_spec_finalized_here",
    "p5_repair_required",
    "p4_current_surface_repair_required",
    "operation_blocker_present",
    "readfeel_blocker_present",
    "question_would_make_immediate_observation_heavy",
    "p8_start_allowed",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "body_free",
    *P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "consistency_issue_row_ref",
    "source_rating_row_ref",
    "source_question_need_observation_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "consistency_issue_type_ref",
    "consistency_issue_reason_ref",
    "rating_question_consistency_guard_blocks_evidence_complete",
    "p8_material_candidate_blocked",
    "body_free",
    *P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS,
)

P7_R54_AHR_POST_CR22_EX12_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex09_schema_version",
    "ex09_material_ref",
    "ex09_next_required_step",
    "ex09_sanitized_review_result_rows_intake_status_ref",
    "ex09_sanitized_review_result_row_count",
    "ex09_actual_sanitized_review_result_rows_intaken_here",
    "ex10_schema_version",
    "ex10_material_ref",
    "ex10_next_required_step",
    "ex10_rating_row_normalization_status_ref",
    "ex10_rating_row_count",
    "ex10_actual_rating_rows_materialized_here",
    "ex11_schema_version",
    "ex11_material_ref",
    "ex11_next_required_step",
    "ex11_readfeel_execution_p5_p4_blocker_classification_status_ref",
    "ex11_question_need_observation_normalization_allowed_next",
    "ex11_blocker_row_count",
    "ex11_p5_repair_required_case_count",
    "ex11_p4_current_only_repair_required_case_count",
    "ex11_operation_blocked_case_count",
    "question_need_observation_normalization_status_ref",
    "question_need_observation_normalization_allowed_status_refs",
    "question_need_observation_normalization_ready",
    "question_need_observation_normalization_reason_refs",
    "question_need_observation_normalization_step_blocker_refs",
    "question_need_observation_normalization_step_blocker_ref_count",
    "required_case_count",
    "source_sanitized_review_result_row_count",
    "source_rating_row_count",
    "source_blocker_row_count",
    "question_need_observation_row_count",
    "question_need_observation_rows",
    "question_need_observation_row_refs",
    "question_need_observation_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "question_need_primary_class_options",
    "question_need_primary_class_option_count",
    "one_question_fit_option_refs",
    "one_question_fit_option_count",
    "repair_required_option_refs",
    "repair_required_option_count",
    "ambiguity_kind_option_refs",
    "ambiguity_kind_option_count",
    "plan_candidate_flag_refs",
    "plan_candidate_flag_count",
    "question_need_primary_class_counts",
    "one_question_fit_counts",
    "ambiguity_kind_counts",
    "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only",
    "plus_single_question_candidate_case_refs",
    "plus_single_question_candidate_case_count",
    "premium_deep_dive_candidate_case_refs",
    "premium_deep_dive_candidate_case_count",
    "question_may_reduce_overread_risk_case_refs",
    "question_may_reduce_overread_risk_case_count",
    "question_would_make_immediate_observation_heavy_case_refs",
    "question_would_make_immediate_observation_heavy_case_count",
    "p5_repair_required_case_refs",
    "p5_repair_required_case_count",
    "p4_current_surface_repair_required_case_refs",
    "p4_current_surface_repair_required_case_count",
    "operation_blocker_case_refs",
    "operation_blocker_case_count",
    "readfeel_blocker_case_refs",
    "readfeel_blocker_case_count",
    "rows_bodyfree_only",
    "rows_have_no_question_text",
    "question_need_observation_rows_normalized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_CR22_EX13_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex10_schema_version",
    "ex10_material_ref",
    "ex10_next_required_step",
    "ex10_rating_row_normalization_status_ref",
    "ex10_rating_row_count",
    "ex10_actual_rating_rows_materialized_here",
    "ex11_schema_version",
    "ex11_material_ref",
    "ex11_next_required_step",
    "ex11_readfeel_execution_p5_p4_blocker_classification_status_ref",
    "ex11_blocker_row_count",
    "ex12_schema_version",
    "ex12_material_ref",
    "ex12_next_required_step",
    "ex12_question_need_observation_normalization_status_ref",
    "ex12_question_need_observation_row_count",
    "ex12_actual_question_need_observation_rows_materialized_here",
    "rating_question_consistency_guard_status_ref",
    "rating_question_consistency_guard_allowed_status_refs",
    "rating_question_consistency_guard_evaluated",
    "rating_question_consistency_guard_passed",
    "rating_question_consistency_guard_reason_refs",
    "rating_question_consistency_guard_step_blocker_refs",
    "rating_question_consistency_guard_step_blocker_ref_count",
    "required_case_count",
    "source_rating_row_count",
    "source_question_need_observation_row_count",
    "source_blocker_row_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "consistency_issue_rows",
    "consistency_issue_row_count",
    "consistency_issue_row_refs",
    "consistency_issue_row_ref_count",
    "consistency_issue_type_refs",
    "consistency_issue_type_counts",
    "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only",
    "rating_below_target_p8_escape_case_refs",
    "rating_below_target_p8_escape_case_count",
    "risk_axis_p8_escape_case_refs",
    "risk_axis_p8_escape_case_count",
    "repair_or_blocker_p8_escape_case_refs",
    "repair_or_blocker_p8_escape_case_count",
    "heavy_observation_p8_escape_case_refs",
    "heavy_observation_p8_escape_case_count",
    "insufficient_material_p8_escape_case_refs",
    "insufficient_material_p8_escape_case_count",
    "rows_bodyfree_only",
    "rows_have_no_question_text",
    "rating_question_consistency_guarded_here",
    "rating_below_target_cannot_escape_to_p8_material",
    "creepy_or_overclaim_risk_cannot_escape_to_question_candidate",
    "self_blame_risk_cannot_escape_to_question_candidate",
    "immediate_observation_heavy_cannot_escape_to_p8_material",
    "insufficient_material_cannot_escape_to_p8_material",
    "repair_or_blocker_rows_cannot_escape_to_p8_material",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _postcr22_question_row_blocker_case_sets(blocker_rows: Sequence[Any]) -> tuple[set[str], set[str], set[str], set[str]]:
    p5_cases = set(_postcr22_case_refs_for_blocker_categories(
        [row for row in blocker_rows if isinstance(row, Mapping)],
        {
            "p5_readfeel_repair_required",
            "p5_history_connection_weak",
            "p5_creepy_or_overclaim_risk",
            "p5_self_blame_amplification_risk",
        },
    ))
    p4_cases = set(_postcr22_case_refs_for_blocker_categories(
        [row for row in blocker_rows if isinstance(row, Mapping)],
        {"p4_current_only_surface_repair_required"},
    ))
    operation_cases = set(_postcr22_case_refs_for_blocker_categories(
        [row for row in blocker_rows if isinstance(row, Mapping)],
        {
            "operation_blocked_missing_receipt",
            "operation_blocked_body_leak",
            "operation_blocked_question_text",
            "operation_blocked_disposal_missing",
            "operation_blocked_no_touch_violation",
        },
    ))
    readfeel_cases = set(p5_cases)
    return p5_cases, p4_cases, operation_cases, readfeel_cases


def _postcr22_ex12_question_rows_from_sources(
    *,
    sanitized_rows: Sequence[Any],
    rating_rows: Sequence[Any],
    blocker_rows: Sequence[Any],
    review_session_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    step_blockers: list[str] = []
    if len(sanitized_rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT or len(rating_rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        step_blockers.append("ex12_source_row_count_not_24")
    sanitized_by_case: dict[str, Mapping[str, Any]] = {}
    for row in sanitized_rows:
        if not isinstance(row, Mapping):
            step_blockers.append("ex12_source_sanitized_row_not_mapping")
            continue
        if _forbidden_payload_key_paths(row, path="ex12_source_sanitized_row"):
            step_blockers.append("ex12_source_sanitized_row_forbidden_body_question_path_hash_key")
            continue
        if row.get("schema_version") != P7_R54_AHR_POST_CR22_EX09_SELECTION_RESULT_ROW_SCHEMA_VERSION:
            step_blockers.append("ex12_source_sanitized_row_schema_not_ex09")
        sanitized_by_case[clean_identifier(row.get("case_ref_id"), default="", max_length=120)] = row
    p5_cases, p4_cases, operation_cases, readfeel_cases = _postcr22_question_row_blocker_case_sets(blocker_rows)
    rows: list[dict[str, Any]] = []
    seen_case_refs: set[str] = set()
    expected_manifest = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    expected_case_refs = {str(row.get("case_ref_id")) for row in expected_manifest.get("case_rows", [])}
    for index, raw_row in enumerate(rating_rows, start=1):
        if not isinstance(raw_row, Mapping):
            step_blockers.append("ex12_source_rating_row_not_mapping")
            continue
        if _forbidden_payload_key_paths(raw_row, path="ex12_source_rating_row"):
            step_blockers.append("ex12_source_rating_row_forbidden_body_question_path_hash_key")
            continue
        if raw_row.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_SCHEMA_VERSION:
            step_blockers.append("ex12_source_rating_row_schema_not_ex10")
        case_ref_id = clean_identifier(raw_row.get("case_ref_id"), default="", max_length=120)
        seen_case_refs.add(case_ref_id)
        sanitized_row = sanitized_by_case.get(case_ref_id)
        if not sanitized_row:
            step_blockers.append("ex12_case_ref_mismatch_between_ex09_ex10")
            continue
        primary_class = clean_identifier(raw_row.get("question_need_primary_class"), default="", max_length=180)
        if primary_class not in cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
            step_blockers.append("ex12_primary_class_not_allowed")
        one_question_fit_ref = clean_identifier(raw_row.get("one_question_fit_ref"), default="", max_length=180)
        if one_question_fit_ref not in cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
            step_blockers.append("ex12_one_question_fit_not_allowed")
        repair_required_refs = _clean_string_ref_list(raw_row.get("repair_required_refs"), limit=24, max_length=180)
        if any(ref not in cr.P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS for ref in repair_required_refs):
            step_blockers.append("ex12_repair_required_ref_not_allowed")
        ambiguity_kind_refs = _clean_string_ref_list(sanitized_row.get("ambiguity_kind_refs"), limit=24, max_length=180)
        if not ambiguity_kind_refs:
            ambiguity_kind_refs = ["no_material_ambiguity"]
        if any(ref not in cr.P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS for ref in ambiguity_kind_refs):
            step_blockers.append("ex12_ambiguity_kind_ref_not_allowed")
        plan_flags, plan_flags_invalid = _postcr22_clean_plan_candidate_flags(raw_row.get("plan_candidate_flags"))
        if plan_flags_invalid:
            step_blockers.append("ex12_plan_candidate_flags_invalid")
        verdict = clean_identifier(raw_row.get("verdict"), default="", max_length=80)
        p5_repair_required = (
            case_ref_id in p5_cases
            or primary_class in P7_R54_AHR_POST_CR22_EX12_P5_REPAIR_PRIMARY_CLASS_REFS
            or any(ref in repair_required_refs for ref in ("emlis_readfeel_repair_required", "p5_surface_repair_required", "gate_boundary_repair_required"))
        )
        p4_current_surface_repair_required = case_ref_id in p4_cases or "p4_current_surface_repair_required" in repair_required_refs
        operation_blocker_present = case_ref_id in operation_cases or bool(raw_row.get("execution_blocker_ids"))
        readfeel_blocker_present = case_ref_id in readfeel_cases or bool(raw_row.get("readfeel_blocker_ids"))
        heavy = primary_class == "question_would_make_immediate_observation_heavy" or one_question_fit_ref == "would_delay_immediate_observation"
        plus_candidate = primary_class == "plus_single_question_candidate_later" and plan_flags.get("plus_single_question_candidate_later") is True
        premium_candidate = primary_class == "premium_deep_dive_candidate_later" and plan_flags.get("premium_deep_dive_candidate_later") is True
        question_may_candidate = primary_class == "question_may_reduce_overread_risk"
        p8_signal = question_may_candidate or plus_candidate or premium_candidate or plan_flags.get("p8_design_material_candidate") is True
        p8_candidate = (
            p8_signal
            and primary_class in P7_R54_AHR_POST_CR22_EX12_P8_MATERIAL_PRIMARY_CLASS_REFS
            and one_question_fit_ref in P7_R54_AHR_POST_CR22_EX12_P8_MATERIAL_ONE_QUESTION_FIT_REFS
            and not p5_repair_required
            and not p4_current_surface_repair_required
            and not operation_blocker_present
            and not readfeel_blocker_present
            and not heavy
            and verdict not in {"RED", "REPAIR_REQUIRED", "BLOCKED", "NOT_REVIEWABLE"}
        )
        reason_ref = "p8_material_candidate_bodyfree_only" if p8_candidate else "not_p8_material_candidate"
        if p5_repair_required:
            reason_ref = "not_p8_material_p5_repair_required"
        elif p4_current_surface_repair_required:
            reason_ref = "not_p8_material_p4_current_only_repair_required"
        elif operation_blocker_present:
            reason_ref = "not_p8_material_operation_blocker_present"
        elif readfeel_blocker_present:
            reason_ref = "not_p8_material_readfeel_blocker_present"
        elif heavy:
            reason_ref = "not_p8_material_question_would_make_immediate_observation_heavy"
        row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "question_need_observation_row_ref": f"postcr22_question_need_observation_row_{index:03d}",
            "source_rating_row_ref": clean_identifier(raw_row.get("rating_row_ref"), default=f"postcr22_rating_row_{index:03d}", max_length=180),
            "source_review_result_row_ref": clean_identifier(raw_row.get("source_review_result_row_ref"), default=f"postcr22_actual_review_result_row_{index:03d}", max_length=180),
            "case_ref_id": case_ref_id,
            "blind_case_id": clean_identifier(raw_row.get("blind_case_id"), default="", max_length=120),
            "packet_ref_id": clean_identifier(raw_row.get("packet_ref_id"), default="", max_length=120),
            "verdict": verdict,
            "question_need_primary_class": primary_class,
            "ambiguity_kind_refs": ambiguity_kind_refs,
            "ambiguity_kind_ref_count": len(ambiguity_kind_refs),
            "one_question_fit_ref": one_question_fit_ref,
            "repair_required_refs": repair_required_refs,
            "repair_required_ref_count": len(repair_required_refs),
            "plan_candidate_flags": plan_flags,
            "plus_single_question_candidate_later": plus_candidate,
            "premium_deep_dive_candidate_later": premium_candidate,
            "question_may_reduce_overread_risk": question_may_candidate,
            "p8_design_material_candidate": p8_candidate,
            "p8_material_candidate_reason_ref": reason_ref,
            "p8_implementation_spec_finalized_here": False,
            "p5_repair_required": p5_repair_required,
            "p4_current_surface_repair_required": p4_current_surface_repair_required,
            "operation_blocker_present": operation_blocker_present,
            "readfeel_blocker_present": readfeel_blocker_present,
            "question_would_make_immediate_observation_heavy": heavy,
            "p8_start_allowed": False,
            "question_text_materialized_here": False,
            "draft_question_text_materialized_here": False,
            "body_free": True,
        }
        row.update({key: False for key in P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS})
        rows.append(row)
    if len(seen_case_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT or seen_case_refs != expected_case_refs:
        step_blockers.append("ex12_case_ref_mismatch_or_not_24")
    step_blockers = _dedupe_refs(step_blockers)
    if step_blockers:
        return [], step_blockers
    return rows, []


def build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization(
    *,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    readfeel_execution_p5_p4_blocker_classification: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX12 body-free question need observation rows without question text."""

    ex09 = sanitized_review_result_rows_intake or build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake()
    ex10 = rating_row_normalization_threshold_summary or build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary()
    ex11 = readfeel_execution_p5_p4_blocker_classification or build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification()
    assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(ex09)
    assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(ex10)
    assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(ex11)
    session_id = _safe_review_session_id(review_session_id or ex11.get("review_session_id") or ex10.get("review_session_id"))
    rows, row_blockers = _postcr22_ex12_question_rows_from_sources(
        sanitized_rows=ex09.get("review_result_rows") or (),
        rating_rows=ex10.get("rating_rows") or (),
        blocker_rows=ex11.get("blocker_rows") or (),
        review_session_id=session_id,
    )
    step_blockers: list[str] = []
    if ex09.get("schema_version") != P7_R54_AHR_POST_CR22_EX09_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_SCHEMA_VERSION:
        step_blockers.append("ex09_schema_version_not_current")
    if ex09.get("sanitized_review_result_rows_intake_ready") is not True:
        step_blockers.append("ex09_sanitized_review_result_rows_not_ready")
    if ex09.get("next_required_step") != P7_R54_AHR_POST_CR22_EX10_STEP_REF:
        step_blockers.append("ex09_next_step_not_ex10")
    if ex10.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION:
        step_blockers.append("ex10_schema_version_not_current")
    if ex10.get("rating_row_normalization_ready") is not True:
        step_blockers.append("ex10_rating_rows_not_ready")
    if ex10.get("next_required_step") != P7_R54_AHR_POST_CR22_EX11_STEP_REF:
        step_blockers.append("ex10_next_step_not_ex11")
    if ex10.get("actual_rating_rows_materialized_here") is not True:
        step_blockers.append("ex10_actual_rating_rows_not_materialized")
    if ex11.get("schema_version") != P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION:
        step_blockers.append("ex11_schema_version_not_current")
    if ex11.get("readfeel_execution_p5_p4_blocker_classification_ready") is not True:
        step_blockers.append("ex11_blocker_classification_not_ready")
    if ex11.get("next_required_step") != P7_R54_AHR_POST_CR22_EX12_STEP_REF:
        step_blockers.append("ex11_next_step_not_ex12")
    if ex11.get("question_need_observation_normalization_allowed_next") is not True:
        step_blockers.append("ex11_question_need_observation_not_allowed_next")
    if ex09.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        step_blockers.append("ex09_sanitized_review_result_row_count_not_24")
    if ex10.get("rating_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        step_blockers.append("ex10_rating_row_count_not_24")
    step_blockers.extend(row_blockers)
    step_blockers = _dedupe_refs(step_blockers)
    ready = not step_blockers
    rows_for_output = rows if ready else []
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    p8_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("p8_design_material_candidate") is True]
    plus_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("plus_single_question_candidate_later") is True]
    premium_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("premium_deep_dive_candidate_later") is True]
    question_may_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("question_may_reduce_overread_risk") is True]
    heavy_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("question_would_make_immediate_observation_heavy") is True]
    p5_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("p5_repair_required") is True]
    p4_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("p4_current_surface_repair_required") is True]
    operation_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("operation_blocker_present") is True]
    readfeel_refs = [str(row.get("case_ref_id")) for row in rows_for_output if row.get("readfeel_blocker_present") is True]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX12_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex09_schema_version": ex09.get("schema_version"),
        "ex09_material_ref": ex09.get("material_id", "postcr22_ex09_sanitized_review_result_rows_intake_bodyfree"),
        "ex09_next_required_step": ex09.get("next_required_step"),
        "ex09_sanitized_review_result_rows_intake_status_ref": ex09.get("sanitized_review_result_rows_intake_status_ref"),
        "ex09_sanitized_review_result_row_count": _int_value_or_zero(ex09.get("sanitized_review_result_row_count")),
        "ex09_actual_sanitized_review_result_rows_intaken_here": ex09.get("actual_sanitized_review_result_rows_intaken_here") is True,
        "ex10_schema_version": ex10.get("schema_version"),
        "ex10_material_ref": ex10.get("material_id", "postcr22_ex10_rating_row_normalization_threshold_summary_bodyfree"),
        "ex10_next_required_step": ex10.get("next_required_step"),
        "ex10_rating_row_normalization_status_ref": ex10.get("rating_row_normalization_status_ref"),
        "ex10_rating_row_count": _int_value_or_zero(ex10.get("rating_row_count")),
        "ex10_actual_rating_rows_materialized_here": ex10.get("actual_rating_rows_materialized_here") is True,
        "ex11_schema_version": ex11.get("schema_version"),
        "ex11_material_ref": ex11.get("material_id", "postcr22_ex11_readfeel_execution_p5_p4_blocker_classification_bodyfree"),
        "ex11_next_required_step": ex11.get("next_required_step"),
        "ex11_readfeel_execution_p5_p4_blocker_classification_status_ref": ex11.get("readfeel_execution_p5_p4_blocker_classification_status_ref"),
        "ex11_question_need_observation_normalization_allowed_next": ex11.get("question_need_observation_normalization_allowed_next") is True,
        "ex11_blocker_row_count": _int_value_or_zero(ex11.get("blocker_row_count")),
        "ex11_p5_repair_required_case_count": _int_value_or_zero(ex11.get("p5_repair_required_case_count")),
        "ex11_p4_current_only_repair_required_case_count": _int_value_or_zero(ex11.get("p4_current_only_repair_required_case_count")),
        "ex11_operation_blocked_case_count": _int_value_or_zero(ex11.get("operation_blocked_case_count")),
        "question_need_observation_normalization_status_ref": (
            P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF
            if ready
            else P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF
        ),
        "question_need_observation_normalization_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX12_ALLOWED_QUESTION_OBSERVATION_STATUS_REFS),
        "question_need_observation_normalization_ready": ready,
        "question_need_observation_normalization_reason_refs": [P7_R54_AHR_POST_CR22_EX12_READY_REASON_REF] if ready else [],
        "question_need_observation_normalization_step_blocker_refs": step_blockers,
        "question_need_observation_normalization_step_blocker_ref_count": len(step_blockers),
        "required_case_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "source_sanitized_review_result_row_count": ex09.get("sanitized_review_result_row_count") if ready else 0,
        "source_rating_row_count": ex10.get("rating_row_count") if ready else 0,
        "source_blocker_row_count": ex11.get("blocker_row_count") if ready else 0,
        "question_need_observation_row_count": len(rows_for_output),
        "question_need_observation_rows": rows_for_output,
        "question_need_observation_row_refs": [str(row.get("question_need_observation_row_ref")) for row in rows_for_output],
        "question_need_observation_row_ref_count": len(rows_for_output),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "question_need_primary_class_options": list(cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "question_need_primary_class_option_count": len(cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS),
        "one_question_fit_option_refs": list(cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS),
        "one_question_fit_option_count": len(cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(cr.P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS),
        "repair_required_option_count": len(cr.P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS),
        "ambiguity_kind_option_refs": list(cr.P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS),
        "ambiguity_kind_option_count": len(cr.P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS),
        "plan_candidate_flag_refs": list(cr.P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS),
        "plan_candidate_flag_count": len(cr.P7_R54_AHR_CR10_PLAN_CANDIDATE_FLAG_REFS),
        "question_need_primary_class_counts": _postcr22_count_values(rows_for_output, "question_need_primary_class") if ready else {},
        "one_question_fit_counts": _postcr22_count_values(rows_for_output, "one_question_fit_ref") if ready else {},
        "ambiguity_kind_counts": _postcr22_count_nested_string_values(rows_for_output, "ambiguity_kind_refs") if ready else {},
        "p8_material_candidate_case_refs_bodyfree_only": p8_refs,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_refs),
        "plus_single_question_candidate_case_refs": plus_refs,
        "plus_single_question_candidate_case_count": len(plus_refs),
        "premium_deep_dive_candidate_case_refs": premium_refs,
        "premium_deep_dive_candidate_case_count": len(premium_refs),
        "question_may_reduce_overread_risk_case_refs": question_may_refs,
        "question_may_reduce_overread_risk_case_count": len(question_may_refs),
        "question_would_make_immediate_observation_heavy_case_refs": heavy_refs,
        "question_would_make_immediate_observation_heavy_case_count": len(heavy_refs),
        "p5_repair_required_case_refs": p5_refs,
        "p5_repair_required_case_count": len(p5_refs),
        "p4_current_surface_repair_required_case_refs": p4_refs,
        "p4_current_surface_repair_required_case_count": len(p4_refs),
        "operation_blocker_case_refs": operation_refs,
        "operation_blocker_case_count": len(operation_refs),
        "readfeel_blocker_case_refs": readfeel_refs,
        "readfeel_blocker_case_count": len(readfeel_refs),
        "rows_bodyfree_only": ready and all(row.get("body_free") is True for row in rows_for_output),
        "rows_have_no_question_text": ready and all(row.get("question_text_materialized_here") is False and row.get("draft_question_text_materialized_here") is False for row in rows_for_output),
        "question_need_observation_rows_normalized_here": ready,
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_human_review_executed_by_person": ex10.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX12_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX11_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX11_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX13_STEP_REF if ready else P7_R54_AHR_POST_CR22_EX12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_question_need_observation_rows_materialized_here"] = ready
    material["actual_rating_rows_materialized_here"] = ready
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["question_text_materialized_here"] = False
    material["draft_question_text_materialized_here"] = False
    material["p8_question_implementation_spec_finalized_here"] = False
    material["p8_start_allowed"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX12_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX12")
    return material


def assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX12_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX12")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX12_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX12",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX12_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX12")
    blockers = list(data.get("question_need_observation_normalization_step_blocker_refs") or [])
    ready = len(blockers) == 0
    expected_status = (
        P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_BLOCKED_STATUS_REF
    )
    if data.get("question_need_observation_normalization_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostCR22-EX12 status changed")
    if data.get("question_need_observation_normalization_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX12 ready flag changed")
    if tuple(data.get("question_need_observation_normalization_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX12_ALLOWED_QUESTION_OBSERVATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX12 allowed status refs changed")
    if data.get("question_need_observation_normalization_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX12 blocker count changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX12",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX12_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p8_start_allowed",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX12 required false field changed: {key}")
    for key in ("r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX12 required true boundary changed: {key}")
    if ready:
        if data.get("question_need_observation_normalization_reason_refs") != [P7_R54_AHR_POST_CR22_EX12_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX12_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX13_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 next step changed")
        for field in (
            "source_sanitized_review_result_row_count",
            "source_rating_row_count",
            "question_need_observation_row_count",
            "question_need_observation_row_ref_count",
            "case_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX12 {field} changed")
        for key in (
            "ex09_actual_sanitized_review_result_rows_intaken_here",
            "ex10_actual_rating_rows_materialized_here",
            "ex11_question_need_observation_normalization_allowed_next",
            "case_ref_ids_unique",
            "rows_bodyfree_only",
            "rows_have_no_question_text",
            "question_need_observation_rows_normalized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_rating_rows_materialized_here",
            "actual_human_review_executed_by_person",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX12 required true field changed: {key}")
        if tuple(data.get("question_need_primary_class_options") or ()) != cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 primary class options changed")
        if tuple(data.get("one_question_fit_option_refs") or ()) != cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 one question options changed")
        for row in data.get("question_need_observation_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostCR22-EX12 question observation row must be mapping")
            _required_fields_present(row, required=P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX12-question-row")
            if row.get("schema_version") != P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row must remain body-free")
            if row.get("question_text_materialized_here") is not False or row.get("draft_question_text_materialized_here") is not False:
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row must not materialize question text")
            if row.get("p8_implementation_spec_finalized_here") is not False or row.get("p8_start_allowed") is not False:
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row must not start/finalize P8")
            if row.get("question_need_primary_class") not in cr.P7_R54_AHR_CR10_QUESTION_NEED_PRIMARY_CLASS_OPTION_REFS:
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row primary class changed")
            if row.get("one_question_fit_ref") not in cr.P7_R54_AHR_CR10_ONE_QUESTION_FIT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row one question fit changed")
            if any(ref not in cr.P7_R54_AHR_CR10_REPAIR_REQUIRED_OPTION_REFS for ref in row.get("repair_required_refs") or []):
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row repair refs changed")
            if any(ref not in cr.P7_R54_AHR_CR10_AMBIGUITY_KIND_OPTION_REFS for ref in row.get("ambiguity_kind_refs") or []):
                raise ValueError("P7-R54-AHR-PostCR22-EX12 row ambiguity refs changed")
            if row.get("p8_design_material_candidate") is True:
                for blocker_flag in (
                    "p5_repair_required",
                    "p4_current_surface_repair_required",
                    "operation_blocker_present",
                    "readfeel_blocker_present",
                    "question_would_make_immediate_observation_heavy",
                ):
                    if row.get(blocker_flag) is True:
                        raise ValueError("P7-R54-AHR-PostCR22-EX12 cannot promote repair/blocker/heavy rows to P8 material")
            for flag_ref in P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError("P7-R54-AHR-PostCR22-EX12 row body-free flag changed")
    else:
        if data.get("question_need_observation_normalization_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 blocked material cannot carry ready reasons")
        if data.get("question_need_observation_rows") != [] or data.get("question_need_observation_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 blocked material cannot output question observation rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 blocked material cannot claim question rows")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX12_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX12 blocked next step changed")
    return True


def _postcr22_ex13_make_issue_row(
    *,
    index: int,
    review_session_id: str,
    issue_type_ref: str,
    reason_ref: str,
    rating_row: Mapping[str, Any],
    question_row: Mapping[str, Any],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "review_session_id": review_session_id,
        "consistency_issue_row_ref": f"postcr22_consistency_issue_row_{index:03d}",
        "source_rating_row_ref": clean_identifier(rating_row.get("rating_row_ref"), default="", max_length=180),
        "source_question_need_observation_row_ref": clean_identifier(
            question_row.get("question_need_observation_row_ref"), default="", max_length=180
        ),
        "case_ref_id": clean_identifier(question_row.get("case_ref_id"), default="", max_length=120),
        "blind_case_id": clean_identifier(question_row.get("blind_case_id"), default="", max_length=120),
        "packet_ref_id": clean_identifier(question_row.get("packet_ref_id"), default="", max_length=120),
        "consistency_issue_type_ref": issue_type_ref,
        "consistency_issue_reason_ref": reason_ref,
        "rating_question_consistency_guard_blocks_evidence_complete": True,
        "p8_material_candidate_blocked": True,
        "body_free": True,
    }
    row.update({key: False for key in P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS})
    return row


def _postcr22_ex13_consistency_issue_rows_from_sources(
    *,
    rating_rows: Sequence[Any],
    question_rows: Sequence[Any],
    review_session_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    step_blockers: list[str] = []
    if len(rating_rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT or len(question_rows) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        step_blockers.append("ex13_source_row_count_not_24")
    rating_by_case: dict[str, Mapping[str, Any]] = {}
    for row in rating_rows:
        if not isinstance(row, Mapping):
            step_blockers.append("ex13_source_rating_row_not_mapping")
            continue
        if _forbidden_payload_key_paths(row, path="ex13_source_rating_row"):
            step_blockers.append("ex13_source_rating_row_forbidden_body_question_path_hash_key")
            continue
        if row.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_SCHEMA_VERSION:
            step_blockers.append("ex13_source_rating_row_schema_not_ex10")
        rating_by_case[clean_identifier(row.get("case_ref_id"), default="", max_length=120)] = row
    issue_rows: list[dict[str, Any]] = []
    issue_index = 1
    seen_question_case_refs: set[str] = set()
    for qrow in question_rows:
        if not isinstance(qrow, Mapping):
            step_blockers.append("ex13_source_question_row_not_mapping")
            continue
        if _forbidden_payload_key_paths(qrow, path="ex13_source_question_row"):
            step_blockers.append("ex13_source_question_row_forbidden_body_question_path_hash_key")
            continue
        if qrow.get("schema_version") != P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
            step_blockers.append("ex13_source_question_row_schema_not_ex12")
        case_ref_id = clean_identifier(qrow.get("case_ref_id"), default="", max_length=120)
        seen_question_case_refs.add(case_ref_id)
        rating_row = rating_by_case.get(case_ref_id)
        if not rating_row:
            step_blockers.append("ex13_case_ref_mismatch_between_rating_and_question_rows")
            continue
        p8_candidate = qrow.get("p8_design_material_candidate") is True
        below_axes = set(_clean_string_ref_list(rating_row.get("below_target_axis_refs"), limit=24, max_length=180))
        primary_class = clean_identifier(qrow.get("question_need_primary_class"), default="", max_length=180)
        one_question_fit_ref = clean_identifier(qrow.get("one_question_fit_ref"), default="", max_length=180)
        repair_or_blocker = any(
            qrow.get(flag_ref) is True
            for flag_ref in (
                "p5_repair_required",
                "p4_current_surface_repair_required",
                "operation_blocker_present",
                "readfeel_blocker_present",
            )
        )
        if p8_candidate and repair_or_blocker:
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF,
                    reason_ref="p5_p4_operation_or_readfeel_blocker_cannot_be_p8_material",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and below_axes:
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF,
                    reason_ref="below_target_rating_cannot_be_p8_material_candidate",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and (below_axes & {"creepy_absence", "overclaim_absence"}):
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF,
                    reason_ref="creepy_or_overclaim_risk_requires_repair_not_question_escape",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and "self_blame_non_amplification" in below_axes:
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_SELF_BLAME_P8_ESCAPE_REF,
                    reason_ref="self_blame_risk_requires_repair_not_question_escape",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and qrow.get("question_would_make_immediate_observation_heavy") is True:
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF,
                    reason_ref="immediate_observation_heavy_case_cannot_be_p8_material_candidate",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and (primary_class == "insufficient_material_execution_blocker" or one_question_fit_ref == "insufficient_material"):
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF,
                    reason_ref="insufficient_material_cannot_be_p8_material_candidate",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and qrow.get("p8_material_candidate_reason_ref") != "p8_material_candidate_bodyfree_only":
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_REASON_CHANGED_REF,
                    reason_ref="p8_candidate_reason_ref_must_remain_bodyfree_candidate_only",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
        if p8_candidate and (
            primary_class not in P7_R54_AHR_POST_CR22_EX12_P8_MATERIAL_PRIMARY_CLASS_REFS
            or one_question_fit_ref not in P7_R54_AHR_POST_CR22_EX12_P8_MATERIAL_ONE_QUESTION_FIT_REFS
        ):
            issue_rows.append(
                _postcr22_ex13_make_issue_row(
                    index=issue_index,
                    review_session_id=review_session_id,
                    issue_type_ref=P7_R54_AHR_POST_CR22_EX13_ISSUE_REASON_CHANGED_REF,
                    reason_ref="p8_candidate_primary_class_or_fit_inconsistent",
                    rating_row=rating_row,
                    question_row=qrow,
                )
            )
            issue_index += 1
    expected_manifest = cr.build_p7_r54_ahr_cr04_current_24_case_manifest_refreeze()
    expected_case_refs = {str(row.get("case_ref_id")) for row in expected_manifest.get("case_rows", [])}
    if len(seen_question_case_refs) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT or seen_question_case_refs != expected_case_refs:
        step_blockers.append("ex13_case_ref_mismatch_or_not_24")
    step_blockers = _dedupe_refs(step_blockers)
    if step_blockers:
        return [], step_blockers
    return issue_rows, []


def _postcr22_case_refs_for_issue_type(rows: Sequence[Mapping[str, Any]], issue_type_ref: str) -> list[str]:
    refs = sorted({str(row.get("case_ref_id")) for row in rows if row.get("consistency_issue_type_ref") == issue_type_ref})
    return [ref for ref in refs if ref]


def build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard(
    *,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    readfeel_execution_p5_p4_blocker_classification: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX13 body-free guard that blocks question escape from rating/blocker issues."""

    ex10 = rating_row_normalization_threshold_summary or build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary()
    ex11 = readfeel_execution_p5_p4_blocker_classification or build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification()
    ex12 = question_need_observation_normalization or build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization()
    assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(ex10)
    assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(ex11)
    assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(ex12)
    session_id = _safe_review_session_id(review_session_id or ex12.get("review_session_id") or ex10.get("review_session_id"))
    issue_rows, row_blockers = _postcr22_ex13_consistency_issue_rows_from_sources(
        rating_rows=ex10.get("rating_rows") or (),
        question_rows=ex12.get("question_need_observation_rows") or (),
        review_session_id=session_id,
    )
    source_blockers: list[str] = []
    if ex10.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION:
        source_blockers.append("ex10_schema_version_not_current")
    if ex10.get("rating_row_normalization_ready") is not True:
        source_blockers.append("ex10_rating_rows_not_ready")
    if ex10.get("next_required_step") != P7_R54_AHR_POST_CR22_EX11_STEP_REF:
        source_blockers.append("ex10_next_step_not_ex11")
    if ex11.get("schema_version") != P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION:
        source_blockers.append("ex11_schema_version_not_current")
    if ex11.get("readfeel_execution_p5_p4_blocker_classification_ready") is not True:
        source_blockers.append("ex11_blocker_classification_not_ready")
    if ex11.get("next_required_step") != P7_R54_AHR_POST_CR22_EX12_STEP_REF:
        source_blockers.append("ex11_next_step_not_ex12")
    if ex12.get("schema_version") != P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        source_blockers.append("ex12_schema_version_not_current")
    if ex12.get("question_need_observation_normalization_ready") is not True:
        source_blockers.append("ex12_question_observation_not_ready")
    if ex12.get("next_required_step") != P7_R54_AHR_POST_CR22_EX13_STEP_REF:
        source_blockers.append("ex12_next_step_not_ex13")
    if ex10.get("rating_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        source_blockers.append("ex10_rating_row_count_not_24")
    if ex12.get("question_need_observation_row_count") != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        source_blockers.append("ex12_question_observation_row_count_not_24")
    source_blockers.extend(row_blockers)
    source_blockers = _dedupe_refs(source_blockers)
    evaluated = not source_blockers
    rows_for_output = issue_rows if evaluated else []
    guard_passed = evaluated and len(rows_for_output) == 0
    guard_failed = evaluated and len(rows_for_output) > 0
    status_ref = (
        P7_R54_AHR_POST_CR22_EX13_GUARD_PASSED_STATUS_REF
        if guard_passed
        else P7_R54_AHR_POST_CR22_EX13_GUARD_FAILED_STATUS_REF
        if guard_failed
        else P7_R54_AHR_POST_CR22_EX13_GUARD_BLOCKED_STATUS_REF
    )
    issue_type_counts = _postcr22_count_values(rows_for_output, "consistency_issue_type_ref") if evaluated else {}
    for issue_type_ref in P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_TYPE_REFS:
        issue_type_counts.setdefault(issue_type_ref, 0)
    issue_type_counts = dict(sorted(issue_type_counts.items()))
    question_rows = ex12.get("question_need_observation_rows") or []
    case_refs = [str(row.get("case_ref_id")) for row in question_rows] if evaluated else []
    p8_case_refs = [str(row.get("case_ref_id")) for row in question_rows if row.get("p8_design_material_candidate") is True] if evaluated else []
    below_refs = _postcr22_case_refs_for_issue_type(rows_for_output, P7_R54_AHR_POST_CR22_EX13_ISSUE_RATING_BELOW_TARGET_P8_ESCAPE_REF)
    risk_refs = sorted(set(_postcr22_case_refs_for_issue_type(rows_for_output, P7_R54_AHR_POST_CR22_EX13_ISSUE_CREEPY_OVERCLAIM_P8_ESCAPE_REF)) | set(_postcr22_case_refs_for_issue_type(rows_for_output, P7_R54_AHR_POST_CR22_EX13_ISSUE_SELF_BLAME_P8_ESCAPE_REF)))
    repair_refs = _postcr22_case_refs_for_issue_type(rows_for_output, P7_R54_AHR_POST_CR22_EX13_ISSUE_REPAIR_OR_BLOCKER_P8_ESCAPE_REF)
    heavy_refs = _postcr22_case_refs_for_issue_type(rows_for_output, P7_R54_AHR_POST_CR22_EX13_ISSUE_HEAVY_OBSERVATION_P8_ESCAPE_REF)
    insufficient_refs = _postcr22_case_refs_for_issue_type(rows_for_output, P7_R54_AHR_POST_CR22_EX13_ISSUE_INSUFFICIENT_MATERIAL_P8_ESCAPE_REF)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX13_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX13_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex10_schema_version": ex10.get("schema_version"),
        "ex10_material_ref": ex10.get("material_id", "postcr22_ex10_rating_row_normalization_threshold_summary_bodyfree"),
        "ex10_next_required_step": ex10.get("next_required_step"),
        "ex10_rating_row_normalization_status_ref": ex10.get("rating_row_normalization_status_ref"),
        "ex10_rating_row_count": _int_value_or_zero(ex10.get("rating_row_count")),
        "ex10_actual_rating_rows_materialized_here": ex10.get("actual_rating_rows_materialized_here") is True,
        "ex11_schema_version": ex11.get("schema_version"),
        "ex11_material_ref": ex11.get("material_id", "postcr22_ex11_readfeel_execution_p5_p4_blocker_classification_bodyfree"),
        "ex11_next_required_step": ex11.get("next_required_step"),
        "ex11_readfeel_execution_p5_p4_blocker_classification_status_ref": ex11.get("readfeel_execution_p5_p4_blocker_classification_status_ref"),
        "ex11_blocker_row_count": _int_value_or_zero(ex11.get("blocker_row_count")),
        "ex12_schema_version": ex12.get("schema_version"),
        "ex12_material_ref": ex12.get("material_id", "postcr22_ex12_question_need_observation_normalization_bodyfree"),
        "ex12_next_required_step": ex12.get("next_required_step"),
        "ex12_question_need_observation_normalization_status_ref": ex12.get("question_need_observation_normalization_status_ref"),
        "ex12_question_need_observation_row_count": _int_value_or_zero(ex12.get("question_need_observation_row_count")),
        "ex12_actual_question_need_observation_rows_materialized_here": ex12.get("actual_question_need_observation_rows_materialized_here") is True,
        "rating_question_consistency_guard_status_ref": status_ref,
        "rating_question_consistency_guard_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX13_ALLOWED_GUARD_STATUS_REFS),
        "rating_question_consistency_guard_evaluated": evaluated,
        "rating_question_consistency_guard_passed": guard_passed,
        "rating_question_consistency_guard_reason_refs": [P7_R54_AHR_POST_CR22_EX13_READY_REASON_REF] if guard_passed else ([P7_R54_AHR_POST_CR22_EX13_FAILED_REASON_REF] if guard_failed else []),
        "rating_question_consistency_guard_step_blocker_refs": source_blockers,
        "rating_question_consistency_guard_step_blocker_ref_count": len(source_blockers),
        "required_case_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "source_rating_row_count": ex10.get("rating_row_count") if evaluated else 0,
        "source_question_need_observation_row_count": ex12.get("question_need_observation_row_count") if evaluated else 0,
        "source_blocker_row_count": ex11.get("blocker_row_count") if evaluated else 0,
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(case_refs) == len(set(case_refs)) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "consistency_issue_rows": rows_for_output,
        "consistency_issue_row_count": len(rows_for_output),
        "consistency_issue_row_refs": [str(row.get("consistency_issue_row_ref")) for row in rows_for_output],
        "consistency_issue_row_ref_count": len(rows_for_output),
        "consistency_issue_type_refs": list(P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_TYPE_REFS),
        "consistency_issue_type_counts": issue_type_counts,
        "p8_material_candidate_case_refs_bodyfree_only": p8_case_refs,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_case_refs),
        "rating_below_target_p8_escape_case_refs": below_refs,
        "rating_below_target_p8_escape_case_count": len(below_refs),
        "risk_axis_p8_escape_case_refs": risk_refs,
        "risk_axis_p8_escape_case_count": len(risk_refs),
        "repair_or_blocker_p8_escape_case_refs": repair_refs,
        "repair_or_blocker_p8_escape_case_count": len(repair_refs),
        "heavy_observation_p8_escape_case_refs": heavy_refs,
        "heavy_observation_p8_escape_case_count": len(heavy_refs),
        "insufficient_material_p8_escape_case_refs": insufficient_refs,
        "insufficient_material_p8_escape_case_count": len(insufficient_refs),
        "rows_bodyfree_only": evaluated and all(row.get("body_free") is True for row in rows_for_output),
        "rows_have_no_question_text": evaluated and all(row.get("question_text_materialized_here") is False and row.get("draft_question_text_materialized_here") is False for row in rows_for_output),
        "rating_question_consistency_guarded_here": evaluated,
        "rating_below_target_cannot_escape_to_p8_material": guard_passed,
        "creepy_or_overclaim_risk_cannot_escape_to_question_candidate": guard_passed,
        "self_blame_risk_cannot_escape_to_question_candidate": guard_passed,
        "immediate_observation_heavy_cannot_escape_to_p8_material": guard_passed,
        "insufficient_material_cannot_escape_to_p8_material": guard_passed,
        "repair_or_blocker_rows_cannot_escape_to_p8_material": guard_passed,
        "actual_rating_rows_materialized_here": evaluated,
        "actual_question_need_observation_rows_materialized_here": evaluated,
        "actual_human_review_executed_by_person": ex12.get("actual_human_review_executed_by_person") is True and evaluated,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX13_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_POST_CR22_EX12_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX13_NOT_YET_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_POST_CR22_EX12_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX14_STEP_REF if guard_passed else P7_R54_AHR_POST_CR22_EX13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_rating_rows_materialized_here"] = evaluated
    material["actual_question_need_observation_rows_materialized_here"] = evaluated
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["actual_disposal_receipt_materialized_here"] = False
    material["disposal_verified"] = False
    material["question_text_materialized_here"] = False
    material["draft_question_text_materialized_here"] = False
    material["p8_question_implementation_spec_finalized_here"] = False
    material["p8_start_allowed"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX13_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX13")
    return material


def assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX13_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX13")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX13_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX13",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX13_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX13")
    if tuple(data.get("rating_question_consistency_guard_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX13_ALLOWED_GUARD_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX13 allowed status refs changed")
    status_ref = data.get("rating_question_consistency_guard_status_ref")
    evaluated = status_ref in (P7_R54_AHR_POST_CR22_EX13_GUARD_PASSED_STATUS_REF, P7_R54_AHR_POST_CR22_EX13_GUARD_FAILED_STATUS_REF)
    guard_passed = status_ref == P7_R54_AHR_POST_CR22_EX13_GUARD_PASSED_STATUS_REF
    guard_failed = status_ref == P7_R54_AHR_POST_CR22_EX13_GUARD_FAILED_STATUS_REF
    if data.get("rating_question_consistency_guard_evaluated") is not evaluated:
        raise ValueError("P7-R54-AHR-PostCR22-EX13 evaluated flag changed")
    if data.get("rating_question_consistency_guard_passed") is not guard_passed:
        raise ValueError("P7-R54-AHR-PostCR22-EX13 passed flag changed")
    blockers = list(data.get("rating_question_consistency_guard_step_blocker_refs") or [])
    if data.get("rating_question_consistency_guard_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX13 blocker count changed")
    issue_rows = list(data.get("consistency_issue_rows") or [])
    if data.get("consistency_issue_row_count") != len(issue_rows):
        raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row count changed")
    if data.get("consistency_issue_row_ref_count") != len(data.get("consistency_issue_row_refs") or []):
        raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row ref count changed")
    if tuple(data.get("consistency_issue_type_refs") or ()) != P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_TYPE_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX13 issue type refs changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX13",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX13_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "actual_disposal_receipt_materialized_here",
        "disposal_verified",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p8_start_allowed",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX13 required false field changed: {key}")
    for key in ("r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX13 required true boundary changed: {key}")
    if evaluated:
        if blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 evaluated material cannot carry source blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX13_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 not-yet steps changed")
        for field in ("source_rating_row_count", "source_question_need_observation_row_count", "case_ref_id_count"):
            if data.get(field) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX13 {field} changed")
        for key in (
            "case_ref_ids_unique",
            "rating_question_consistency_guarded_here",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_human_review_executed_by_person",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX13 required true field changed: {key}")
        for row in issue_rows:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row must be mapping")
            _required_fields_present(row, required=P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX13-issue-row")
            if row.get("schema_version") != P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row must remain body-free")
            if row.get("consistency_issue_type_ref") not in P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_TYPE_REFS:
                raise ValueError("P7-R54-AHR-PostCR22-EX13 issue type changed")
            if row.get("rating_question_consistency_guard_blocks_evidence_complete") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row must block evidence complete")
            if row.get("p8_material_candidate_blocked") is not True:
                raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row must block P8 candidate")
            for flag_ref in P7_R54_AHR_POST_CR22_EX13_CONSISTENCY_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError("P7-R54-AHR-PostCR22-EX13 issue row body-free flag changed")
    if guard_passed:
        if issue_rows or data.get("consistency_issue_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 passed guard cannot carry issues")
        if data.get("rating_question_consistency_guard_reason_refs") != [P7_R54_AHR_POST_CR22_EX13_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 passed reason changed")
        for key in (
            "rating_below_target_cannot_escape_to_p8_material",
            "creepy_or_overclaim_risk_cannot_escape_to_question_candidate",
            "self_blame_risk_cannot_escape_to_question_candidate",
            "immediate_observation_heavy_cannot_escape_to_p8_material",
            "insufficient_material_cannot_escape_to_p8_material",
            "repair_or_blocker_rows_cannot_escape_to_p8_material",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX13 guard pass boolean changed: {key}")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX14_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 passed next step changed")
    elif guard_failed:
        if not issue_rows:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 failed guard must carry issues")
        if data.get("rating_question_consistency_guard_reason_refs") != [P7_R54_AHR_POST_CR22_EX13_FAILED_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 failed reason changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 failed next step changed")
    else:
        if status_ref != P7_R54_AHR_POST_CR22_EX13_GUARD_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 blocked material must carry source blockers")
        if data.get("rating_question_consistency_guard_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 blocked material cannot carry guard reasons")
        if issue_rows or data.get("consistency_issue_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 blocked material cannot output issue rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 blocked material cannot claim question rows")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX13_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX13 blocked next step changed")
    return True


# Alias names for the detailed-design wording of EX12 through EX13.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_question_need_observation_normalization_bodyfree(
    *,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    readfeel_execution_p5_p4_blocker_classification: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization(
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        readfeel_execution_p5_p4_blocker_classification=readfeel_execution_p5_p4_blocker_classification,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_question_need_observation_normalization_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_question_consistency_guard_bodyfree(
    *,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    readfeel_execution_p5_p4_blocker_classification: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard(
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        readfeel_execution_p5_p4_blocker_classification=readfeel_execution_p5_p4_blocker_classification,
        question_need_observation_normalization=question_need_observation_normalization,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_rating_question_consistency_guard_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(data)

# ---------------------------------------------------------------------------
# EX14-EX15 disposal receipt intake / final no-leak validation
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex14_disposal_purge_receipt_intake.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex15_final_no_body_leak_no_question_text_no_touch_validation.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:15]
P7_R54_AHR_POST_CR22_EX14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[15:]
P7_R54_AHR_POST_CR22_EX15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:16]
P7_R54_AHR_POST_CR22_EX15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[16:]

P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_ACCEPTED_STATUS_REF: Final = (
    "EX14_DISPOSAL_PURGE_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_BLOCKED_STATUS_REF: Final = (
    "EX14_DISPOSAL_PURGE_RECEIPT_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX14_ALLOWED_DISPOSAL_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_ACCEPTED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX14_READY_REASON_REF: Final = (
    "EX14_BODYFREE_DISPOSAL_PURGE_RECEIPT_ACCEPTED_BODY_REMOVED_NO_PATH_HASH_NOTES"
)
P7_R54_AHR_POST_CR22_EX14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex14_disposal_purge_receipt_or_stop"
)
P7_R54_AHR_POST_CR22_EX14_DEFAULT_DISPOSAL_RECEIPT_REF: Final = (
    "postcr22_disposal_receipt_ref_20260629_001"
)
P7_R54_AHR_POST_CR22_EX14_REJECTED_RECEIPT_PATH_SHAPE_REF: Final = (
    "postcr22_disposal_receipt_ref_rejected_path_shape_bodyfree"
)
P7_R54_AHR_POST_CR22_EX14_DEFAULT_DISPOSAL_STATUS_REF: Final = "BODY_PURGED"
P7_R54_AHR_POST_CR22_EX14_ALLOWED_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "BODY_PURGED",
    "BODY_NOT_MATERIALIZED_NO_DISPOSAL_REQUIRED",
    "DISPOSAL_FAILED",
)
P7_R54_AHR_POST_CR22_EX14_DEFAULT_PAUSE_ABORT_STATUS_REF: Final = (
    "review_completed_without_abort_body_purged"
)
P7_R54_AHR_POST_CR22_EX14_DEFAULT_RETENTION_POLICY_REF: Final = (
    "local_body_full_packet_max_72h_or_shorter"
)
P7_R54_AHR_POST_CR22_EX14_DEFAULT_EXPIRATION_POLICY_REF: Final = (
    "post_review_body_full_packet_expired_or_purged"
)
P7_R54_AHR_POST_CR22_EX14_ALLOWED_ACTUAL_SOURCE_REF: Final = "actual_local_disposal_receipt_bodyfree"
P7_R54_AHR_POST_CR22_EX14_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
)

P7_R54_AHR_POST_CR22_EX15_VALIDATION_PASSED_STATUS_REF: Final = (
    "EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_PASSED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX15_VALIDATION_FAILED_STATUS_REF: Final = (
    "EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_FAILED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX15_VALIDATION_BLOCKED_STATUS_REF: Final = (
    "EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX15_ALLOWED_VALIDATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX15_VALIDATION_PASSED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX15_VALIDATION_FAILED_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX15_VALIDATION_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX15_READY_REASON_REF: Final = (
    "EX15_FINAL_BODYFREE_VALIDATION_PASSED_NO_BODY_NO_QUESTION_NO_TOUCH"
)
P7_R54_AHR_POST_CR22_EX15_FAILED_REASON_REF: Final = (
    "EX15_FINAL_BODYFREE_VALIDATION_FOUND_LEAK_OR_NO_TOUCH_MUTATION"
)
P7_R54_AHR_POST_CR22_EX15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex15_final_no_body_no_question_no_touch_validation_or_stop"
)
P7_R54_AHR_POST_CR22_EX15_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
)
P7_R54_AHR_POST_CR22_EX15_BODY_LEAK_FLAG_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_body_included",
    "current_input_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "comment_text_body_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "packet_content_included",
    "body_full_packet_content_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_POST_CR22_EX15_QUESTION_TEXT_FLAG_REFS: Final[tuple[str, ...]] = (
    "question_text_included",
    "draft_question_text_included",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
)
P7_R54_AHR_POST_CR22_EX15_PATH_OR_HASH_FLAG_REFS: Final[tuple[str, ...]] = (
    "local_absolute_path_included",
    "body_hash_included",
    "body_hash_stored",
    "content_hash_of_body_stored",
)
P7_R54_AHR_POST_CR22_EX15_NO_TOUCH_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_CR22_NO_TOUCH_CONTRACT_REFS,
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "user_label_connection_runtime_changed",
    "p8_question_api_created",
    "p8_question_db_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "r52_reintake_execution_started_here",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "release_allowed",
)

P7_R54_AHR_POST_CR22_EX14_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex13_schema_version",
    "ex13_material_ref",
    "ex13_next_required_step",
    "ex13_rating_question_consistency_guard_status_ref",
    "ex13_rating_question_consistency_guard_passed",
    "ex13_consistency_issue_row_count",
    "ex13_actual_rating_rows_materialized_here",
    "ex13_actual_question_need_observation_rows_materialized_here",
    "disposal_purge_receipt_intake_status_ref",
    "disposal_purge_receipt_intake_allowed_status_refs",
    "disposal_purge_receipt_accepted",
    "disposal_purge_receipt_reason_refs",
    "disposal_purge_receipt_blocker_refs",
    "disposal_purge_receipt_blocker_ref_count",
    "disposal_receipt_ref",
    "disposal_receipt_ref_present",
    "disposal_receipt_ref_is_bodyfree_ref",
    "disposal_receipt_ref_has_local_path_shape",
    "disposal_status_ref",
    "disposal_status_allowed_refs",
    "disposal_status_is_body_purged",
    "packet_materialized_for_review",
    "body_removed",
    "content_hash_of_body_stored",
    "body_hash_stored",
    "local_absolute_path_included",
    "reviewer_notes_body_stored",
    "pause_abort_status_ref",
    "retention_policy_ref",
    "expiration_policy_ref",
    "disposal_receipt_actual_source_ref",
    "disposal_receipt_actual_source_allowed_ref",
    "disposal_receipt_actual_source_guard_passed",
    "disposal_receipt_bodyfree_only",
    "disposal_receipt_forbidden_payload_key_refs",
    "disposal_receipt_forbidden_payload_key_ref_count",
    "body_full_packet_lifecycle_closed_bodyfree",
    "body_removed_without_hash_path_or_reviewer_notes",
    "disposal_receipt_does_not_store_body_hash_or_local_path",
    "disposal_receipt_does_not_store_reviewer_notes_body",
    "disposal_receipt_does_not_create_question_text",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_CR22_EX15_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex14_schema_version",
    "ex14_material_ref",
    "ex14_next_required_step",
    "ex14_disposal_purge_receipt_intake_status_ref",
    "ex14_disposal_purge_receipt_accepted",
    "ex14_disposal_verified",
    "ex14_actual_disposal_receipt_materialized_here",
    "final_validation_status_ref",
    "final_validation_allowed_status_refs",
    "final_validation_evaluated",
    "final_validation_passed",
    "final_validation_reason_refs",
    "final_validation_step_blocker_refs",
    "final_validation_step_blocker_ref_count",
    "scanned_artifact_refs",
    "scanned_artifact_ref_count",
    "scanned_artifact_count",
    "body_or_question_leak_refs",
    "body_or_question_leak_ref_count",
    "body_leak_refs",
    "body_leak_ref_count",
    "question_text_leak_refs",
    "question_text_leak_ref_count",
    "path_or_hash_leak_refs",
    "path_or_hash_leak_ref_count",
    "contract_mutation_refs",
    "contract_mutation_ref_count",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "no_local_path_or_hash_validation_passed",
    "all_scanned_artifacts_bodyfree_only",
    "final_validation_does_not_complete_evidence",
    "final_validation_does_not_start_p8",
    "final_validation_does_not_execute_r52",
    "final_validation_does_not_touch_api_db_rn_runtime",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p8_start_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _postcr22_true_flag_paths(value: Any, flag_refs: tuple[str, ...], *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    flag_set = set(flag_refs)
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in flag_set and child is True:
                paths.append(child_path)
            paths.extend(_postcr22_true_flag_paths(child, flag_refs, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_postcr22_true_flag_paths(child, flag_refs, path=f"{path}[{index}]"))
    return paths


def _postcr22_artifact_ref(value: Mapping[str, Any], *, index: int) -> str:
    ref = clean_identifier(
        value.get("material_id") or value.get("operation_step_ref") or value.get("schema_version"),
        default=f"postcr22_bodyfree_artifact_{index:03d}",
        max_length=220,
    )
    if _ref_has_local_path_shape(ref):
        return f"postcr22_bodyfree_artifact_{index:03d}_rejected_path_shape_ref"
    return ref


def _postcr22_ex14_receipt_fields(receipt: Mapping[str, Any] | None) -> tuple[dict[str, Any], list[str]]:
    receipt_map: Mapping[str, Any] = receipt or {}
    forbidden_key_paths = _forbidden_payload_key_paths(receipt_map, path="ex14_disposal_receipt") if isinstance(receipt_map, Mapping) else []
    receipt_ref, receipt_ref_has_path = _bodyfree_ref_or_rejected(
        receipt_map.get("disposal_receipt_ref") if isinstance(receipt_map, Mapping) else None,
        default="",
        rejected_ref=P7_R54_AHR_POST_CR22_EX14_REJECTED_RECEIPT_PATH_SHAPE_REF,
        max_length=260,
    )
    status_ref = clean_identifier(
        receipt_map.get("disposal_status_ref") if isinstance(receipt_map, Mapping) else None,
        default="",
        max_length=120,
    )
    pause_abort_status_ref = clean_identifier(
        receipt_map.get("pause_abort_status_ref") if isinstance(receipt_map, Mapping) else None,
        default="",
        max_length=180,
    )
    retention_policy_ref = clean_identifier(
        receipt_map.get("retention_policy_ref") if isinstance(receipt_map, Mapping) else None,
        default="",
        max_length=180,
    )
    expiration_policy_ref = clean_identifier(
        receipt_map.get("expiration_policy_ref") if isinstance(receipt_map, Mapping) else None,
        default="",
        max_length=180,
    )
    actual_source_ref = clean_identifier(
        receipt_map.get("actual_source_ref") if isinstance(receipt_map, Mapping) else None,
        default="",
        max_length=180,
    )
    packet_materialized = receipt_map.get("packet_materialized_for_review") is True if isinstance(receipt_map, Mapping) else False
    body_removed = receipt_map.get("body_removed") is True if isinstance(receipt_map, Mapping) else False
    content_hash_stored = receipt_map.get("content_hash_of_body_stored") is True if isinstance(receipt_map, Mapping) else False
    body_hash_stored = receipt_map.get("body_hash_stored") is True if isinstance(receipt_map, Mapping) else False
    local_path_included = receipt_map.get("local_absolute_path_included") is True if isinstance(receipt_map, Mapping) else False
    reviewer_notes_body_stored = receipt_map.get("reviewer_notes_body_stored") is True if isinstance(receipt_map, Mapping) else False
    body_free_receipt = receipt_map.get("body_free") is True if isinstance(receipt_map, Mapping) else False
    blockers: list[str] = []
    if not receipt_ref:
        blockers.append("disposal_receipt_ref_missing")
    if receipt_ref_has_path:
        blockers.append("disposal_receipt_ref_has_local_path_shape")
    if status_ref not in P7_R54_AHR_POST_CR22_EX14_ALLOWED_DISPOSAL_STATUS_REFS:
        blockers.append("disposal_status_ref_not_allowed")
    if status_ref != P7_R54_AHR_POST_CR22_EX14_DEFAULT_DISPOSAL_STATUS_REF:
        blockers.append("disposal_status_ref_not_body_purged")
    if not packet_materialized:
        blockers.append("packet_materialized_for_review_not_confirmed")
    if not body_removed:
        blockers.append("body_removed_not_confirmed")
    if content_hash_stored:
        blockers.append("content_hash_of_body_stored_must_be_false")
    if body_hash_stored:
        blockers.append("body_hash_stored_must_be_false")
    if local_path_included:
        blockers.append("local_absolute_path_included_must_be_false")
    if reviewer_notes_body_stored:
        blockers.append("reviewer_notes_body_stored_must_be_false")
    if not pause_abort_status_ref:
        blockers.append("pause_abort_status_ref_missing")
    if not retention_policy_ref:
        blockers.append("retention_policy_ref_missing")
    if not expiration_policy_ref:
        blockers.append("expiration_policy_ref_missing")
    if actual_source_ref != P7_R54_AHR_POST_CR22_EX14_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append("actual_source_ref_not_actual_local_disposal_receipt_bodyfree")
    if not body_free_receipt:
        blockers.append("disposal_receipt_body_free_not_true")
    if forbidden_key_paths:
        blockers.append("disposal_receipt_contains_forbidden_payload_keys")
    blockers = _dedupe_refs(blockers)
    return (
        {
            "disposal_receipt_ref": receipt_ref,
            "disposal_receipt_ref_present": bool(receipt_ref),
            "disposal_receipt_ref_is_bodyfree_ref": bool(receipt_ref) and not receipt_ref_has_path,
            "disposal_receipt_ref_has_local_path_shape": receipt_ref_has_path,
            "disposal_status_ref": status_ref,
            "disposal_status_allowed_refs": list(P7_R54_AHR_POST_CR22_EX14_ALLOWED_DISPOSAL_STATUS_REFS),
            "disposal_status_is_body_purged": status_ref == P7_R54_AHR_POST_CR22_EX14_DEFAULT_DISPOSAL_STATUS_REF,
            "packet_materialized_for_review": packet_materialized,
            "body_removed": body_removed,
            "content_hash_of_body_stored": content_hash_stored,
            "body_hash_stored": body_hash_stored,
            "local_absolute_path_included": False,
            "reviewer_notes_body_stored": reviewer_notes_body_stored,
            "pause_abort_status_ref": pause_abort_status_ref,
            "retention_policy_ref": retention_policy_ref,
            "expiration_policy_ref": expiration_policy_ref,
            "disposal_receipt_actual_source_ref": actual_source_ref,
            "disposal_receipt_actual_source_allowed_ref": P7_R54_AHR_POST_CR22_EX14_ALLOWED_ACTUAL_SOURCE_REF,
            "disposal_receipt_actual_source_guard_passed": actual_source_ref == P7_R54_AHR_POST_CR22_EX14_ALLOWED_ACTUAL_SOURCE_REF,
            "disposal_receipt_bodyfree_only": body_free_receipt and not bool(forbidden_key_paths),
            "disposal_receipt_forbidden_payload_key_refs": [clean_identifier(path, default="forbidden_payload_key", max_length=260) for path in forbidden_key_paths],
            "disposal_receipt_forbidden_payload_key_ref_count": len(forbidden_key_paths),
            "body_removed_without_hash_path_or_reviewer_notes": (
                body_removed and not content_hash_stored and not body_hash_stored and not local_path_included and not reviewer_notes_body_stored
            ),
            "disposal_receipt_does_not_store_body_hash_or_local_path": not content_hash_stored and not body_hash_stored and not local_path_included,
            "disposal_receipt_does_not_store_reviewer_notes_body": not reviewer_notes_body_stored,
            "disposal_receipt_does_not_create_question_text": True,
        },
        blockers,
    )


def build_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX14 body-free disposal / purge receipt intake material."""

    ex13 = rating_question_consistency_guard or build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard()
    assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(ex13)
    session_id = _safe_review_session_id(review_session_id or ex13.get("review_session_id"))
    receipt_fields, receipt_blockers = _postcr22_ex14_receipt_fields(disposal_receipt)
    source_blockers: list[str] = []
    if ex13.get("schema_version") != P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        source_blockers.append("ex13_schema_version_not_current")
    if ex13.get("rating_question_consistency_guard_passed") is not True:
        source_blockers.append("ex13_rating_question_consistency_guard_not_passed")
    if ex13.get("next_required_step") != P7_R54_AHR_POST_CR22_EX14_STEP_REF:
        source_blockers.append("ex13_next_step_not_ex14")
    if ex13.get("consistency_issue_row_count") != 0:
        source_blockers.append("ex13_consistency_issues_present")
    blockers = _dedupe_refs([*source_blockers, *receipt_blockers])
    accepted = not blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX14_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX14_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex13_schema_version": ex13.get("schema_version"),
        "ex13_material_ref": ex13.get("material_id", "postcr22_ex13_rating_question_consistency_guard_bodyfree"),
        "ex13_next_required_step": ex13.get("next_required_step"),
        "ex13_rating_question_consistency_guard_status_ref": ex13.get("rating_question_consistency_guard_status_ref"),
        "ex13_rating_question_consistency_guard_passed": ex13.get("rating_question_consistency_guard_passed") is True,
        "ex13_consistency_issue_row_count": _int_value_or_zero(ex13.get("consistency_issue_row_count")),
        "ex13_actual_rating_rows_materialized_here": ex13.get("actual_rating_rows_materialized_here") is True,
        "ex13_actual_question_need_observation_rows_materialized_here": ex13.get("actual_question_need_observation_rows_materialized_here") is True,
        "disposal_purge_receipt_intake_status_ref": (
            P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_ACCEPTED_STATUS_REF
            if accepted
            else P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_BLOCKED_STATUS_REF
        ),
        "disposal_purge_receipt_intake_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX14_ALLOWED_DISPOSAL_RECEIPT_STATUS_REFS),
        "disposal_purge_receipt_accepted": accepted,
        "disposal_purge_receipt_reason_refs": [P7_R54_AHR_POST_CR22_EX14_READY_REASON_REF] if accepted else [],
        "disposal_purge_receipt_blocker_refs": blockers,
        "disposal_purge_receipt_blocker_ref_count": len(blockers),
        **receipt_fields,
        "body_full_packet_lifecycle_closed_bodyfree": accepted,
        "actual_rating_rows_materialized_here": ex13.get("actual_rating_rows_materialized_here") is True and accepted,
        "actual_question_need_observation_rows_materialized_here": ex13.get("actual_question_need_observation_rows_materialized_here") is True and accepted,
        "actual_disposal_receipt_materialized_here": accepted,
        "disposal_verified": accepted,
        "actual_human_review_executed_by_person": ex13.get("actual_human_review_executed_by_person") is True and accepted,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX14_IMPLEMENTED_STEPS if accepted else P7_R54_AHR_POST_CR22_EX13_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX14_NOT_YET_IMPLEMENTED_STEPS if accepted else P7_R54_AHR_POST_CR22_EX13_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX15_STEP_REF if accepted else P7_R54_AHR_POST_CR22_EX14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_rating_rows_materialized_here"] = ex13.get("actual_rating_rows_materialized_here") is True and accepted
    material["actual_question_need_observation_rows_materialized_here"] = ex13.get("actual_question_need_observation_rows_materialized_here") is True and accepted
    material["actual_disposal_receipt_materialized_here"] = accepted
    material["disposal_verified"] = accepted
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["p8_start_allowed"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX14_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX14")
    return material


def assert_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX14_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX14")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX14_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX14",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX14_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX14")
    if tuple(data.get("disposal_purge_receipt_intake_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX14_ALLOWED_DISPOSAL_RECEIPT_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX14 allowed status refs changed")
    accepted = data.get("disposal_purge_receipt_intake_status_ref") == P7_R54_AHR_POST_CR22_EX14_DISPOSAL_RECEIPT_ACCEPTED_STATUS_REF
    if data.get("disposal_purge_receipt_accepted") is not accepted:
        raise ValueError("P7-R54-AHR-PostCR22-EX14 accepted flag changed")
    blockers = list(data.get("disposal_purge_receipt_blocker_refs") or [])
    if data.get("disposal_purge_receipt_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX14 blocker count changed")
    if data.get("disposal_receipt_forbidden_payload_key_ref_count") != len(data.get("disposal_receipt_forbidden_payload_key_refs") or []):
        raise ValueError("P7-R54-AHR-PostCR22-EX14 forbidden payload key count changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX14",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX14_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p8_start_allowed",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX14 required false field changed: {key}")
    for key in ("r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX14 required true boundary changed: {key}")
    if accepted:
        if blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 accepted material cannot carry blockers")
        if data.get("disposal_purge_receipt_reason_refs") != [P7_R54_AHR_POST_CR22_EX14_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 accepted reason changed")
        if data.get("ex13_rating_question_consistency_guard_passed") is not True:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 requires EX13 passed")
        for key in (
            "disposal_receipt_ref_present",
            "disposal_receipt_ref_is_bodyfree_ref",
            "disposal_status_is_body_purged",
            "packet_materialized_for_review",
            "body_removed",
            "disposal_receipt_actual_source_guard_passed",
            "disposal_receipt_bodyfree_only",
            "body_full_packet_lifecycle_closed_bodyfree",
            "body_removed_without_hash_path_or_reviewer_notes",
            "disposal_receipt_does_not_store_body_hash_or_local_path",
            "disposal_receipt_does_not_store_reviewer_notes_body",
            "disposal_receipt_does_not_create_question_text",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "actual_human_review_executed_by_person",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX14 required true field changed: {key}")
        for key in (
            "disposal_receipt_ref_has_local_path_shape",
            "content_hash_of_body_stored",
            "body_hash_stored",
            "local_absolute_path_included",
            "reviewer_notes_body_stored",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX14 required false receipt field changed: {key}")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX14_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX15_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 accepted next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 blocked material must carry blockers")
        if data.get("disposal_purge_receipt_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 blocked material cannot carry ready reasons")
        if data.get("actual_disposal_receipt_materialized_here") is not False or data.get("disposal_verified") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 blocked material cannot claim disposal verified")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX14_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX14 blocked next step changed")
    return True


def _postcr22_ex15_scan_artifacts(artifacts: Sequence[Any]) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str]]:
    scanned_refs: list[str] = []
    body_leaks: list[str] = []
    question_leaks: list[str] = []
    path_hash_leaks: list[str] = []
    contract_mutations: list[str] = []
    forbidden_key_refs: list[str] = []
    for index, artifact in enumerate(artifacts, start=1):
        if not isinstance(artifact, Mapping):
            scanned_refs.append(f"postcr22_non_mapping_artifact_{index:03d}")
            body_leaks.append(f"postcr22_non_mapping_artifact_{index:03d}")
            continue
        artifact_ref = _postcr22_artifact_ref(artifact, index=index)
        scanned_refs.append(artifact_ref)
        forbidden_paths = _forbidden_payload_key_paths(artifact, path=artifact_ref)
        forbidden_key_refs.extend(clean_identifier(path, default="forbidden_payload_key", max_length=260) for path in forbidden_paths)
        body_leaks.extend(
            clean_identifier(path, default="body_leak_flag", max_length=260)
            for path in _postcr22_true_flag_paths(artifact, P7_R54_AHR_POST_CR22_EX15_BODY_LEAK_FLAG_REFS, path=artifact_ref)
        )
        question_leaks.extend(
            clean_identifier(path, default="question_text_leak_flag", max_length=260)
            for path in _postcr22_true_flag_paths(artifact, P7_R54_AHR_POST_CR22_EX15_QUESTION_TEXT_FLAG_REFS, path=artifact_ref)
        )
        path_hash_leaks.extend(
            clean_identifier(path, default="path_hash_leak_flag", max_length=260)
            for path in _postcr22_true_flag_paths(artifact, P7_R54_AHR_POST_CR22_EX15_PATH_OR_HASH_FLAG_REFS, path=artifact_ref)
        )
        contract_mutations.extend(
            clean_identifier(path, default="contract_mutation_flag", max_length=260)
            for path in _postcr22_true_flag_paths(artifact, P7_R54_AHR_POST_CR22_EX15_NO_TOUCH_FLAG_REFS, path=artifact_ref)
        )
    body_leaks.extend(forbidden_key_refs)
    return (
        _dedupe_refs(scanned_refs),
        _dedupe_refs(body_leaks),
        _dedupe_refs(question_leaks),
        _dedupe_refs(path_hash_leaks),
        _dedupe_refs(contract_mutations),
        _dedupe_refs(forbidden_key_refs),
    )


def build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation(
    *,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    bodyfree_artifacts: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX15 final body-free no-body / no-question / no-touch validation."""

    ex14 = disposal_purge_receipt_intake or build_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake()
    assert_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_contract(ex14)
    session_id = _safe_review_session_id(review_session_id or ex14.get("review_session_id"))
    artifacts = list(bodyfree_artifacts) if bodyfree_artifacts is not None else [ex14]
    scanned_refs, body_leak_refs, question_leak_refs, path_hash_leak_refs, contract_mutation_refs, forbidden_key_refs = _postcr22_ex15_scan_artifacts(artifacts)
    source_blockers: list[str] = []
    if ex14.get("schema_version") != P7_R54_AHR_POST_CR22_EX14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION:
        source_blockers.append("ex14_schema_version_not_current")
    if ex14.get("disposal_purge_receipt_accepted") is not True:
        source_blockers.append("ex14_disposal_purge_receipt_not_accepted")
    if ex14.get("disposal_verified") is not True:
        source_blockers.append("ex14_disposal_not_verified")
    if ex14.get("next_required_step") != P7_R54_AHR_POST_CR22_EX15_STEP_REF:
        source_blockers.append("ex14_next_step_not_ex15")
    if not artifacts:
        source_blockers.append("bodyfree_artifacts_missing")
    evaluated = not source_blockers
    any_leak_or_mutation = bool(body_leak_refs or question_leak_refs or path_hash_leak_refs or contract_mutation_refs)
    passed = evaluated and not any_leak_or_mutation
    failed = evaluated and any_leak_or_mutation
    status_ref = (
        P7_R54_AHR_POST_CR22_EX15_VALIDATION_PASSED_STATUS_REF
        if passed
        else P7_R54_AHR_POST_CR22_EX15_VALIDATION_FAILED_STATUS_REF
        if failed
        else P7_R54_AHR_POST_CR22_EX15_VALIDATION_BLOCKED_STATUS_REF
    )
    blocker_refs = _dedupe_refs(source_blockers)
    body_or_question_leak_refs = _dedupe_refs([*body_leak_refs, *question_leak_refs])
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX15_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX15_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex14_schema_version": ex14.get("schema_version"),
        "ex14_material_ref": ex14.get("material_id", "postcr22_ex14_disposal_purge_receipt_intake_bodyfree"),
        "ex14_next_required_step": ex14.get("next_required_step"),
        "ex14_disposal_purge_receipt_intake_status_ref": ex14.get("disposal_purge_receipt_intake_status_ref"),
        "ex14_disposal_purge_receipt_accepted": ex14.get("disposal_purge_receipt_accepted") is True,
        "ex14_disposal_verified": ex14.get("disposal_verified") is True,
        "ex14_actual_disposal_receipt_materialized_here": ex14.get("actual_disposal_receipt_materialized_here") is True,
        "final_validation_status_ref": status_ref,
        "final_validation_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX15_ALLOWED_VALIDATION_STATUS_REFS),
        "final_validation_evaluated": evaluated,
        "final_validation_passed": passed,
        "final_validation_reason_refs": [P7_R54_AHR_POST_CR22_EX15_READY_REASON_REF] if passed else ([P7_R54_AHR_POST_CR22_EX15_FAILED_REASON_REF] if failed else []),
        "final_validation_step_blocker_refs": blocker_refs,
        "final_validation_step_blocker_ref_count": len(blocker_refs),
        "scanned_artifact_refs": scanned_refs,
        "scanned_artifact_ref_count": len(scanned_refs),
        "scanned_artifact_count": len(artifacts),
        "body_or_question_leak_refs": body_or_question_leak_refs,
        "body_or_question_leak_ref_count": len(body_or_question_leak_refs),
        "body_leak_refs": body_leak_refs,
        "body_leak_ref_count": len(body_leak_refs),
        "question_text_leak_refs": question_leak_refs,
        "question_text_leak_ref_count": len(question_leak_refs),
        "path_or_hash_leak_refs": path_hash_leak_refs,
        "path_or_hash_leak_ref_count": len(path_hash_leak_refs),
        "contract_mutation_refs": contract_mutation_refs,
        "contract_mutation_ref_count": len(contract_mutation_refs),
        "no_body_leak_validation_passed": evaluated and not body_leak_refs,
        "no_question_text_validation_passed": evaluated and not question_leak_refs,
        "no_touch_validation_passed": evaluated and not contract_mutation_refs,
        "no_local_path_or_hash_validation_passed": evaluated and not path_hash_leak_refs,
        "all_scanned_artifacts_bodyfree_only": evaluated and not forbidden_key_refs and not body_leak_refs and not path_hash_leak_refs,
        "final_validation_does_not_complete_evidence": True,
        "final_validation_does_not_start_p8": True,
        "final_validation_does_not_execute_r52": True,
        "final_validation_does_not_touch_api_db_rn_runtime": True,
        "actual_rating_rows_materialized_here": ex14.get("actual_rating_rows_materialized_here") is True and evaluated,
        "actual_question_need_observation_rows_materialized_here": ex14.get("actual_question_need_observation_rows_materialized_here") is True and evaluated,
        "actual_disposal_receipt_materialized_here": ex14.get("actual_disposal_receipt_materialized_here") is True and evaluated,
        "disposal_verified": ex14.get("disposal_verified") is True and evaluated,
        "actual_human_review_executed_by_person": ex14.get("actual_human_review_executed_by_person") is True and evaluated,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX15_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_POST_CR22_EX14_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX15_NOT_YET_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_POST_CR22_EX14_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX16_STEP_REF if passed else P7_R54_AHR_POST_CR22_EX15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_rating_rows_materialized_here"] = ex14.get("actual_rating_rows_materialized_here") is True and evaluated
    material["actual_question_need_observation_rows_materialized_here"] = ex14.get("actual_question_need_observation_rows_materialized_here") is True and evaluated
    material["actual_disposal_receipt_materialized_here"] = ex14.get("actual_disposal_receipt_materialized_here") is True and evaluated
    material["disposal_verified"] = ex14.get("disposal_verified") is True and evaluated
    material["actual_human_review_run_here"] = False
    material["actual_review_evidence_complete"] = False
    material["p8_start_allowed"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX15_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX15")
    return material


def assert_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX15_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX15")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX15_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX15",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX15_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX15")
    if tuple(data.get("final_validation_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX15_ALLOWED_VALIDATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX15 allowed status refs changed")
    status_ref = data.get("final_validation_status_ref")
    evaluated = status_ref in (
        P7_R54_AHR_POST_CR22_EX15_VALIDATION_PASSED_STATUS_REF,
        P7_R54_AHR_POST_CR22_EX15_VALIDATION_FAILED_STATUS_REF,
    )
    passed = status_ref == P7_R54_AHR_POST_CR22_EX15_VALIDATION_PASSED_STATUS_REF
    failed = status_ref == P7_R54_AHR_POST_CR22_EX15_VALIDATION_FAILED_STATUS_REF
    if data.get("final_validation_evaluated") is not evaluated:
        raise ValueError("P7-R54-AHR-PostCR22-EX15 evaluated flag changed")
    if data.get("final_validation_passed") is not passed:
        raise ValueError("P7-R54-AHR-PostCR22-EX15 passed flag changed")
    blockers = list(data.get("final_validation_step_blocker_refs") or [])
    if data.get("final_validation_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX15 blocker count changed")
    for refs_key, count_key in (
        ("scanned_artifact_refs", "scanned_artifact_ref_count"),
        ("body_or_question_leak_refs", "body_or_question_leak_ref_count"),
        ("body_leak_refs", "body_leak_ref_count"),
        ("question_text_leak_refs", "question_text_leak_ref_count"),
        ("path_or_hash_leak_refs", "path_or_hash_leak_ref_count"),
        ("contract_mutation_refs", "contract_mutation_ref_count"),
    ):
        if data.get(count_key) != len(data.get(refs_key) or []):
            raise ValueError(f"P7-R54-AHR-PostCR22-EX15 {count_key} changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX15",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX15_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p8_start_allowed",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX15 required false field changed: {key}")
    for key in (
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "final_validation_does_not_complete_evidence",
        "final_validation_does_not_start_p8",
        "final_validation_does_not_execute_r52",
        "final_validation_does_not_touch_api_db_rn_runtime",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX15 required true boundary changed: {key}")
    if passed:
        if blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 passed validation cannot carry source blockers")
        if data.get("final_validation_reason_refs") != [P7_R54_AHR_POST_CR22_EX15_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 passed reason changed")
        for key in (
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "no_local_path_or_hash_validation_passed",
            "all_scanned_artifacts_bodyfree_only",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "actual_human_review_executed_by_person",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX15 required true field changed: {key}")
        for refs_key in (
            "body_or_question_leak_refs",
            "body_leak_refs",
            "question_text_leak_refs",
            "path_or_hash_leak_refs",
            "contract_mutation_refs",
        ):
            if data.get(refs_key) != []:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX15 passed validation cannot carry {refs_key}")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX16_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 passed next step changed")
    elif failed:
        if data.get("final_validation_reason_refs") != [P7_R54_AHR_POST_CR22_EX15_FAILED_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 failed reason changed")
        if not (data.get("body_or_question_leak_refs") or data.get("path_or_hash_leak_refs") or data.get("contract_mutation_refs")):
            raise ValueError("P7-R54-AHR-PostCR22-EX15 failed validation must carry leak or mutation refs")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 failed next step changed")
    else:
        if status_ref != P7_R54_AHR_POST_CR22_EX15_VALIDATION_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 blocked material must carry source blockers")
        if data.get("final_validation_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 blocked material cannot carry validation reasons")
        if data.get("actual_disposal_receipt_materialized_here") is not False or data.get("disposal_verified") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 blocked material cannot claim disposal verified")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX15_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX15 blocked next step changed")
    return True


# Alias names for the detailed-design wording of EX14 through EX15.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_disposal_purge_receipt_intake_bodyfree(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake(
        rating_question_consistency_guard=rating_question_consistency_guard,
        disposal_receipt=disposal_receipt,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_disposal_purge_receipt_intake_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex14_disposal_purge_receipt_intake_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_final_no_body_leak_no_question_text_no_touch_validation_bodyfree(
    *,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    bodyfree_artifacts: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation(
        disposal_purge_receipt_intake=disposal_purge_receipt_intake,
        bodyfree_artifacts=bodyfree_artifacts,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_contract(data)


# ---------------------------------------------------------------------------
# EX16-EX17 evidence complete predicate / candidate-only separation
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex16_actual_review_evidence_complete_predicate.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX17_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex17_p5_p6_p8_r52_candidate_only_separation.bodyfree.v1"
)

P7_R54_AHR_POST_CR22_EX16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:17]
P7_R54_AHR_POST_CR22_EX16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[17:]
P7_R54_AHR_POST_CR22_EX17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:18]
P7_R54_AHR_POST_CR22_EX17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[18:]

P7_R54_AHR_POST_CR22_EX16_EVIDENCE_COMPLETE_STATUS_REF: Final = (
    "EX16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_PASSED_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX16_EVIDENCE_BLOCKED_STATUS_REF: Final = (
    "EX16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX16_ALLOWED_EVIDENCE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX16_EVIDENCE_COMPLETE_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX16_EVIDENCE_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX16_READY_REASON_REF: Final = (
    "EX16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_PASSED_ALL_BODYFREE_CONDITIONS"
)
P7_R54_AHR_POST_CR22_EX16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex16_actual_review_evidence_complete_predicate_or_stop"
)
P7_R54_AHR_POST_CR22_EX16_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_review_evidence_complete",
)

P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_READY_STATUS_REF: Final = (
    "EX17_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_READY_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_BLOCKED_STATUS_REF: Final = (
    "EX17_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX17_ALLOWED_CANDIDATE_SEPARATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_READY_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX17_READY_REASON_REF: Final = (
    "EX17_CANDIDATE_ONLY_SEPARATION_READY_NO_AUTO_PROMOTION_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX17_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex17_candidate_only_separation_or_stop"
)
P7_R54_AHR_POST_CR22_EX17_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_review_evidence_complete",
)
P7_R54_AHR_POST_CR22_EX17_DECISION_REFS: Final[tuple[str, ...]] = (
    "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY",
    "P5_REPAIR_REQUIRED_BEFORE_R52_REINTAKE",
    "P4_CURRENT_ONLY_REPAIR_REQUIRED_BEFORE_R52_REINTAKE",
    "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT",
    "R54_OPERATION_BLOCKED_DISPOSAL_NOT_VERIFIED",
    "R54_OPERATION_INCONCLUSIVE_INSUFFICIENT_MATERIAL",
    "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY",
    "P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY",
    "R52_REINTAKE_HANDOFF_CANDIDATE_ONLY",
)

P7_R54_AHR_POST_CR22_EX16_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex07_schema_version",
    "ex07_material_ref",
    "ex07_next_required_step",
    "ex07_operation_receipt_status_ref",
    "ex07_actual_source_guard_passed",
    "ex07_actual_human_review_executed_by_person",
    "ex07_reviewed_case_count",
    "ex07_selection_row_count",
    "ex09_schema_version",
    "ex09_material_ref",
    "ex09_next_required_step",
    "ex09_sanitized_review_result_rows_intake_status_ref",
    "ex09_actual_sanitized_review_result_rows_intaken_here",
    "ex09_actual_rows_source_guard_passed",
    "ex09_sanitized_review_result_row_count",
    "ex10_schema_version",
    "ex10_material_ref",
    "ex10_next_required_step",
    "ex10_rating_row_normalization_status_ref",
    "ex10_actual_rating_rows_materialized_here",
    "ex10_rating_row_count",
    "ex12_schema_version",
    "ex12_material_ref",
    "ex12_next_required_step",
    "ex12_question_need_observation_normalization_status_ref",
    "ex12_actual_question_need_observation_rows_materialized_here",
    "ex12_question_need_observation_row_count",
    "ex13_schema_version",
    "ex13_material_ref",
    "ex13_next_required_step",
    "ex13_rating_question_consistency_guard_status_ref",
    "ex13_rating_question_consistency_guard_passed",
    "ex13_consistency_issue_row_count",
    "ex15_schema_version",
    "ex15_material_ref",
    "ex15_next_required_step",
    "ex15_final_validation_status_ref",
    "ex15_final_validation_passed",
    "ex15_no_body_leak_validation_passed",
    "ex15_no_question_text_validation_passed",
    "ex15_no_touch_validation_passed",
    "ex15_no_local_path_or_hash_validation_passed",
    "ex15_disposal_verified",
    "evidence_complete_predicate_status_ref",
    "evidence_complete_predicate_allowed_status_refs",
    "evidence_complete_predicate_evaluated",
    "evidence_complete_predicate_passed",
    "evidence_complete_predicate_reason_refs",
    "evidence_complete_predicate_blocker_refs",
    "evidence_complete_predicate_blocker_ref_count",
    "required_case_count",
    "actual_source_guard_passed",
    "actual_human_review_executed_by_person",
    "reviewed_case_count",
    "reviewed_case_count_is_24",
    "selection_row_count",
    "selection_row_count_is_24",
    "sanitized_review_result_row_count",
    "sanitized_review_result_row_count_is_24",
    "rating_row_count",
    "rating_row_count_is_24",
    "question_need_observation_row_count",
    "question_need_observation_row_count_is_24",
    "disposal_verified",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "no_local_path_or_hash_validation_passed",
    "consistency_guard_passed",
    "consistency_issue_row_count",
    "body_or_question_leak_refs",
    "body_or_question_leak_ref_count",
    "path_or_hash_leak_refs",
    "path_or_hash_leak_ref_count",
    "contract_mutation_refs",
    "contract_mutation_ref_count",
    "evidence_complete_does_not_finalize_p5",
    "evidence_complete_does_not_start_p6",
    "evidence_complete_does_not_start_p8",
    "evidence_complete_does_not_request_or_execute_r52",
    "evidence_complete_does_not_complete_p7_or_release",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "actual_human_review_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_CR22_EX17_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex16_schema_version",
    "ex16_material_ref",
    "ex16_next_required_step",
    "ex16_evidence_complete_predicate_status_ref",
    "ex16_evidence_complete_predicate_passed",
    "ex16_actual_review_evidence_complete",
    "ex16_actual_source_guard_passed",
    "ex16_reviewed_case_count",
    "ex16_sanitized_review_result_row_count",
    "ex16_rating_row_count",
    "ex16_question_need_observation_row_count",
    "ex16_disposal_verified",
    "ex11_schema_version",
    "ex11_material_ref",
    "ex11_next_required_step",
    "ex11_readfeel_execution_p5_p4_blocker_classification_status_ref",
    "ex11_no_blocker_case_count",
    "ex11_p5_repair_required_case_count",
    "ex11_p4_current_only_repair_required_case_count",
    "ex11_operation_blocked_case_count",
    "ex11_inconclusive_case_count",
    "ex12_schema_version",
    "ex12_material_ref",
    "ex12_next_required_step",
    "ex12_question_need_observation_normalization_status_ref",
    "ex12_p8_material_candidate_case_count_bodyfree_only",
    "ex13_schema_version",
    "ex13_material_ref",
    "ex13_next_required_step",
    "ex13_rating_question_consistency_guard_status_ref",
    "ex13_rating_question_consistency_guard_passed",
    "candidate_only_separation_status_ref",
    "candidate_only_separation_allowed_status_refs",
    "candidate_only_separation_ready",
    "candidate_only_separation_reason_refs",
    "candidate_only_separation_blocker_refs",
    "candidate_only_separation_blocker_ref_count",
    "decision_ref_options",
    "decision_ref_option_count",
    "selected_decision_refs",
    "selected_decision_ref_count",
    "p5_confirmed_candidate_bodyfree_only",
    "p5_confirmed_candidate_case_refs",
    "p5_confirmed_candidate_case_count",
    "p5_repair_required_before_r52_reintake",
    "p5_repair_required_case_refs",
    "p5_repair_required_case_count",
    "p4_current_only_repair_required_before_r52_reintake",
    "p4_current_only_repair_required_case_refs",
    "p4_current_only_repair_required_case_count",
    "operation_blocked_case_refs",
    "operation_blocked_case_count",
    "operation_blocked_body_leak_or_question_text",
    "operation_blocked_disposal_not_verified",
    "inconclusive_insufficient_material_case_refs",
    "inconclusive_insufficient_material_case_count",
    "p6_limited_human_readfeel_candidate_only",
    "p8_question_need_observation_material_candidate_only",
    "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only",
    "r52_reintake_handoff_candidate_only",
    "r52_reintake_handoff_candidate_case_refs",
    "r52_reintake_handoff_candidate_case_count",
    "candidate_only_separation_does_not_finalize_p5",
    "candidate_only_separation_does_not_start_p6",
    "candidate_only_separation_does_not_start_p8",
    "candidate_only_separation_does_not_execute_r52",
    "candidate_only_separation_does_not_complete_p7_or_release",
    "actual_source_guard_passed",
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_review_evidence_complete",
    "actual_human_review_run_here",
    "actual_human_review_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)



# ---------------------------------------------------------------------------
# EX18 validation command matrix / result memo / next-decision hold
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_cr22_actual_local_review_execution_evidence_completion."
    "ex18_validation_command_matrix_result_memo_next_decision_hold.bodyfree.v1"
)
P7_R54_AHR_POST_CR22_EX18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[:19]
P7_R54_AHR_POST_CR22_EX18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_CR22_EX_STEP_REFS[19:]

P7_R54_AHR_POST_CR22_EX18_READY_STATUS_REF: Final = (
    "EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_READY_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX18_BLOCKED_STATUS_REF: Final = (
    "EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_BLOCKED"
)
P7_R54_AHR_POST_CR22_EX18_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX18_READY_STATUS_REF,
    P7_R54_AHR_POST_CR22_EX18_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_CR22_EX18_READY_REASON_REF: Final = (
    "EX18_RESULT_MEMO_READY_NEXT_DECISION_HELD_NO_AUTO_PROMOTION_BODYFREE"
)
P7_R54_AHR_POST_CR22_EX18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex18_validation_command_matrix_result_memo_next_decision_hold_or_stop"
)
P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF: Final = (
    "manual_next_decision_hold_required_p5_p6_p8_r52_release_not_auto_executed"
)
P7_R54_AHR_POST_CR22_EX18_DEFAULT_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostCR22_ActualLocalReviewExecutionEvidenceCompletion_EX18_Result_20260630.md"
)
P7_R54_AHR_POST_CR22_EX18_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_review_evidence_complete",
)

P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF: Final = "passed_bodyfree"
P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_FAILED_REF: Final = "failed_bodyfree"
P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF: Final = "not_run_not_claimed_bodyfree"
P7_R54_AHR_POST_CR22_EX18_ALLOWED_COMMAND_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF,
    P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_FAILED_REF,
    P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
)
P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS: Final[tuple[str, ...]] = (
    "ex18_target_postcr22_ex18_tests",
    "ex18_postcr22_ex00_ex18_combined_target_tests",
    "ex18_cr22_regression",
    "ex18_cr00_cr22_combined_regression_split",
    "ex18_cs00_cs18_selected_regression_split",
    "ex18_cs00_cs01_ahr00_ahr01_selected_smoke",
    "ex18_compileall_ai_services_ai_inference_ai_tests",
)
P7_R54_AHR_POST_CR22_EX18_TARGET_TEST_COMMAND_REFS: Final[tuple[str, ...]] = (
    "ex18_target_postcr22_ex18_tests",
    "ex18_postcr22_ex00_ex18_combined_target_tests",
)
P7_R54_AHR_POST_CR22_EX18_SELECTED_REGRESSION_COMMAND_REFS: Final[tuple[str, ...]] = (
    "ex18_cr22_regression",
    "ex18_cr00_cr22_combined_regression_split",
    "ex18_cs00_cs18_selected_regression_split",
    "ex18_cs00_cs01_ahr00_ahr01_selected_smoke",
)
P7_R54_AHR_POST_CR22_EX18_COMPILEALL_COMMAND_REFS: Final[tuple[str, ...]] = (
    "ex18_compileall_ai_services_ai_inference_ai_tests",
)
P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_DEFINITIONS: Final[dict[str, dict[str, str]]] = {
    "ex18_target_postcr22_ex18_tests": {
        "command_kind_ref": "target_test",
        "command_scope_ref": "postcr22_ex18_target_contract",
        "command_display_ref": "pytest_bodyfree_ref_postcr22_ex18_target",
    },
    "ex18_postcr22_ex00_ex18_combined_target_tests": {
        "command_kind_ref": "target_test",
        "command_scope_ref": "postcr22_ex00_ex18_combined_contract",
        "command_display_ref": "pytest_bodyfree_ref_postcr22_ex00_ex18_combined",
    },
    "ex18_cr22_regression": {
        "command_kind_ref": "selected_regression",
        "command_scope_ref": "cr22_current_received_actual_local_review_operation_contract",
        "command_display_ref": "pytest_bodyfree_ref_r54_ahr_cr22_regression",
    },
    "ex18_cr00_cr22_combined_regression_split": {
        "command_kind_ref": "selected_regression",
        "command_scope_ref": "cr00_cr22_current_received_regression_split",
        "command_display_ref": "pytest_bodyfree_ref_r54_ahr_cr00_cr22_split",
    },
    "ex18_cs00_cs18_selected_regression_split": {
        "command_kind_ref": "selected_regression",
        "command_scope_ref": "cs00_cs18_selected_regression_split",
        "command_display_ref": "pytest_bodyfree_ref_r54_ahr_cs00_cs18_split",
    },
    "ex18_cs00_cs01_ahr00_ahr01_selected_smoke": {
        "command_kind_ref": "selected_regression",
        "command_scope_ref": "cs00_cs01_ahr00_ahr01_selected_smoke",
        "command_display_ref": "pytest_bodyfree_ref_cs00_cs01_ahr00_ahr01_smoke",
    },
    "ex18_compileall_ai_services_ai_inference_ai_tests": {
        "command_kind_ref": "compileall",
        "command_scope_ref": "ai_services_ai_inference_ai_tests_bodyfree_compile_check",
        "command_display_ref": "compileall_bodyfree_ref_ai_services_ai_inference_ai_tests",
    },
}
P7_R54_AHR_POST_CR22_EX18_ALLOWED_VALIDATION_COMMAND_ROW_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "command_ref",
        "command_kind_ref",
        "command_scope_ref",
        "command_display_ref",
        "required",
        "command_status_ref",
        "command_status_allowed_refs",
        "passed",
        "ran_here",
        "green_claimed",
        "full_backend_suite_green_claimed",
        "rn_contract_green_claimed",
        "rn_real_device_modal_claimed",
        "actual_human_review_complete_claimed_by_command",
        "p5_final_claimed",
        "p6_start_claimed",
        "p8_start_claimed",
        "r52_actual_execution_claimed",
        "p7_complete_claimed",
        "release_allowed_claimed",
        "raw_terminal_output_included",
        "terminal_output_body_included",
        "stdout_body_included",
        "stderr_body_included",
        "traceback_body_included",
        "local_absolute_path_included",
        "body_hash_included",
        "body_free",
    }
)
P7_R54_AHR_POST_CR22_EX18_RESULT_MEMO_REQUIRED_SECTION_REFS: Final[tuple[str, ...]] = (
    "implementation_scope",
    "changed_files",
    "target_tests",
    "selected_regression",
    "compileall",
    "actual_human_review_execution_status",
    "actual_source_guard_status",
    "row_counts",
    "disposal_status",
    "no_leak_validation_status",
    "candidate_only_decisions",
    "not_claimed_boundary",
    "next_required_step",
)
P7_R54_AHR_POST_CR22_EX18_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
    "p5_final",
    "p6_start",
    "p8_start",
    "r52_actual_execution",
    "p7_complete",
    "release_allowed",
)
P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_OPTION_REFS: Final[tuple[str, ...]] = (
    "hold_for_manual_review_of_ex18_result_memo",
    "decide_p5_repair_before_r52_reintake",
    "decide_p4_current_only_repair_before_r52_reintake",
    "decide_p6_limited_human_readfeel_candidate_only",
    "decide_p8_question_need_design_material_candidate_only",
    "decide_r52_handoff_candidate_without_execution_here",
    "hold_for_missing_actual_review_evidence",
)

P7_R54_AHR_POST_CR22_EX18_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "operation_step_ref",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "ex17_schema_version",
    "ex17_material_ref",
    "ex17_next_required_step",
    "ex17_candidate_only_separation_status_ref",
    "ex17_candidate_only_separation_ready",
    "ex17_actual_review_evidence_complete",
    "ex17_selected_decision_refs",
    "ex17_selected_decision_ref_count",
    "ex17_p5_confirmed_candidate_bodyfree_only",
    "ex17_p6_limited_human_readfeel_candidate_only",
    "ex17_p8_question_need_observation_material_candidate_only",
    "ex17_r52_reintake_handoff_candidate_only",
    "ex17_p5_repair_required_before_r52_reintake",
    "ex17_p4_current_only_repair_required_before_r52_reintake",
    "ex17_operation_blocked_case_count",
    "ex17_inconclusive_insufficient_material_case_count",
    "validation_command_matrix_status_ref",
    "validation_command_matrix_allowed_status_refs",
    "validation_command_matrix_ready",
    "validation_command_matrix_rows",
    "validation_command_matrix_row_count",
    "validation_command_matrix_required_command_refs",
    "validation_command_matrix_required_command_ref_count",
    "validation_command_matrix_command_refs",
    "validation_command_matrix_command_ref_count",
    "validation_missing_required_command_refs",
    "validation_missing_required_command_ref_count",
    "validation_duplicate_command_refs",
    "validation_duplicate_command_ref_count",
    "validation_nonpassed_required_command_refs",
    "validation_nonpassed_required_command_ref_count",
    "validation_forbidden_body_question_path_hash_command_refs",
    "validation_forbidden_body_question_path_hash_command_ref_count",
    "validation_promotion_claim_command_refs",
    "validation_promotion_claim_command_ref_count",
    "result_memo_ref",
    "result_memo_ref_present",
    "result_memo_required_section_refs",
    "result_memo_required_section_ref_count",
    "result_memo_sections_bodyfree",
    "result_memo_ready",
    "implementation_scope",
    "changed_files",
    "changed_file_count",
    "target_tests",
    "target_test_command_refs",
    "target_test_command_ref_count",
    "selected_regression",
    "selected_regression_command_refs",
    "selected_regression_command_ref_count",
    "compileall",
    "compileall_command_refs",
    "compileall_command_ref_count",
    "actual_human_review_execution_status",
    "actual_source_guard_status",
    "row_counts",
    "disposal_status",
    "no_leak_validation_status",
    "candidate_only_decisions",
    "candidate_only_decision_count",
    "not_claimed_boundary",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "next_decision_hold_required",
    "next_decision_hold_status_ref",
    "next_decision_option_refs",
    "next_decision_option_ref_count",
    "next_decision_auto_execution_allowed",
    "ex18_status_ref",
    "ex18_allowed_status_refs",
    "ex18_ready",
    "ex18_reason_refs",
    "ex18_blocker_refs",
    "ex18_blocker_ref_count",
    "actual_source_guard_passed",
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_review_evidence_complete",
    "actual_human_review_run_here",
    "actual_human_review_complete",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_cr_basis",
    "current_cr_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "postcr22_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

def _postcr22_ex16_source_blockers(
    *,
    ex07: Mapping[str, Any],
    ex09: Mapping[str, Any],
    ex10: Mapping[str, Any],
    ex12: Mapping[str, Any],
    ex13: Mapping[str, Any],
    ex15: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if ex07.get("schema_version") != P7_R54_AHR_POST_CR22_EX07_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION:
        blockers.append("ex07_schema_version_not_current")
    if ex07.get("operation_receipt_status_ref") != P7_R54_AHR_POST_CR22_EX07_OPERATION_RECEIPT_ACCEPTED_STATUS_REF:
        blockers.append("ex07_operation_receipt_not_accepted")
    if ex07.get("actual_source_guard_passed") is not True:
        blockers.append("ex07_actual_source_guard_not_passed")
    if ex07.get("actual_human_review_executed_by_person") is not True:
        blockers.append("ex07_actual_human_review_not_executed_by_person")
    if _int_value_or_zero(ex07.get("reviewed_case_count")) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex07_reviewed_case_count_not_24")
    if _int_value_or_zero(ex07.get("selection_row_count")) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex07_selection_row_count_not_24")

    if ex09.get("schema_version") != P7_R54_AHR_POST_CR22_EX09_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_SCHEMA_VERSION:
        blockers.append("ex09_schema_version_not_current")
    if ex09.get("sanitized_review_result_rows_intake_status_ref") != P7_R54_AHR_POST_CR22_EX09_SANITIZED_ROWS_ACCEPTED_STATUS_REF:
        blockers.append("ex09_sanitized_review_result_rows_not_accepted")
    if ex09.get("ex08_actual_rows_source_guard_passed") is not True or ex09.get("rows_have_actual_person_selection_only_provenance") is not True:
        blockers.append("ex09_actual_selection_row_source_guard_not_passed")
    if ex09.get("actual_sanitized_review_result_rows_intaken_here") is not True:
        blockers.append("ex09_actual_sanitized_review_rows_not_intaken")
    if _int_value_or_zero(ex09.get("sanitized_review_result_row_count")) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex09_sanitized_review_result_row_count_not_24")
    if ex09.get("next_required_step") != P7_R54_AHR_POST_CR22_EX10_STEP_REF:
        blockers.append("ex09_next_step_not_ex10")

    if ex10.get("schema_version") != P7_R54_AHR_POST_CR22_EX10_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION:
        blockers.append("ex10_schema_version_not_current")
    if ex10.get("rating_row_normalization_status_ref") != P7_R54_AHR_POST_CR22_EX10_RATING_ROWS_NORMALIZED_STATUS_REF:
        blockers.append("ex10_rating_rows_not_normalized")
    if ex10.get("actual_rating_rows_materialized_here") is not True:
        blockers.append("ex10_actual_rating_rows_not_materialized")
    if _int_value_or_zero(ex10.get("rating_row_count")) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex10_rating_row_count_not_24")
    if ex10.get("next_required_step") != P7_R54_AHR_POST_CR22_EX11_STEP_REF:
        blockers.append("ex10_next_step_not_ex11")

    if ex12.get("schema_version") != P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        blockers.append("ex12_schema_version_not_current")
    if ex12.get("question_need_observation_normalization_status_ref") != P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF:
        blockers.append("ex12_question_need_observations_not_normalized")
    if ex12.get("actual_question_need_observation_rows_materialized_here") is not True:
        blockers.append("ex12_actual_question_need_observation_rows_not_materialized")
    if _int_value_or_zero(ex12.get("question_need_observation_row_count")) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
        blockers.append("ex12_question_need_observation_row_count_not_24")
    if ex12.get("question_text_materialized_here") is not False or ex12.get("draft_question_text_materialized_here") is not False:
        blockers.append("ex12_question_text_materialized")
    if ex12.get("next_required_step") != P7_R54_AHR_POST_CR22_EX13_STEP_REF:
        blockers.append("ex12_next_step_not_ex13")

    if ex13.get("schema_version") != P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        blockers.append("ex13_schema_version_not_current")
    if ex13.get("rating_question_consistency_guard_status_ref") != P7_R54_AHR_POST_CR22_EX13_GUARD_PASSED_STATUS_REF:
        blockers.append("ex13_rating_question_consistency_guard_not_passed")
    if ex13.get("rating_question_consistency_guard_passed") is not True:
        blockers.append("ex13_consistency_guard_passed_flag_false")
    if _int_value_or_zero(ex13.get("consistency_issue_row_count")) != 0:
        blockers.append("ex13_consistency_issue_rows_present")
    if ex13.get("next_required_step") != P7_R54_AHR_POST_CR22_EX14_STEP_REF:
        blockers.append("ex13_next_step_not_ex14")

    if ex15.get("schema_version") != P7_R54_AHR_POST_CR22_EX15_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION:
        blockers.append("ex15_schema_version_not_current")
    if ex15.get("final_validation_status_ref") != P7_R54_AHR_POST_CR22_EX15_VALIDATION_PASSED_STATUS_REF:
        blockers.append("ex15_final_validation_not_passed")
    if ex15.get("final_validation_passed") is not True:
        blockers.append("ex15_final_validation_passed_flag_false")
    if ex15.get("no_body_leak_validation_passed") is not True:
        blockers.append("ex15_no_body_leak_validation_not_passed")
    if ex15.get("no_question_text_validation_passed") is not True:
        blockers.append("ex15_no_question_text_validation_not_passed")
    if ex15.get("no_touch_validation_passed") is not True:
        blockers.append("ex15_no_touch_validation_not_passed")
    if ex15.get("disposal_verified") is not True:
        blockers.append("ex15_disposal_not_verified")
    if ex15.get("actual_disposal_receipt_materialized_here") is not True:
        blockers.append("ex15_actual_disposal_receipt_not_materialized")
    if ex15.get("actual_review_evidence_complete") is not False:
        blockers.append("ex15_must_not_precomplete_evidence")
    if ex15.get("next_required_step") != P7_R54_AHR_POST_CR22_EX16_STEP_REF:
        blockers.append("ex15_next_step_not_ex16")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    final_no_body_leak_no_question_text_no_touch_validation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX16 body-free actual review evidence complete predicate material."""

    ex07 = actual_operation_receipt_intake or build_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake()
    assert_p7_r54_ahr_post_cr22_ex07_actual_operation_receipt_intake_contract(ex07)
    ex09 = sanitized_review_result_rows_intake or build_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake()
    assert_p7_r54_ahr_post_cr22_ex09_sanitized_review_result_rows_intake_contract(ex09)
    ex10 = rating_row_normalization_threshold_summary or build_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary()
    assert_p7_r54_ahr_post_cr22_ex10_rating_row_normalization_threshold_summary_contract(ex10)
    ex12 = question_need_observation_normalization or build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization()
    assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(ex12)
    ex13 = rating_question_consistency_guard or build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard()
    assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(ex13)
    ex15 = final_no_body_leak_no_question_text_no_touch_validation or build_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation()
    assert_p7_r54_ahr_post_cr22_ex15_final_no_body_leak_no_question_text_no_touch_validation_contract(ex15)
    session_id = _safe_review_session_id(review_session_id or ex15.get("review_session_id") or ex13.get("review_session_id"))

    blocker_refs = _postcr22_ex16_source_blockers(ex07=ex07, ex09=ex09, ex10=ex10, ex12=ex12, ex13=ex13, ex15=ex15)
    passed = not blocker_refs
    status_ref = (
        P7_R54_AHR_POST_CR22_EX16_EVIDENCE_COMPLETE_STATUS_REF
        if passed
        else P7_R54_AHR_POST_CR22_EX16_EVIDENCE_BLOCKED_STATUS_REF
    )
    body_or_question_leak_refs = list(ex15.get("body_or_question_leak_refs") or [])
    path_or_hash_leak_refs = list(ex15.get("path_or_hash_leak_refs") or [])
    contract_mutation_refs = list(ex15.get("contract_mutation_refs") or [])
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX16_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX16_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex07_schema_version": ex07.get("schema_version"),
        "ex07_material_ref": ex07.get("material_id", "postcr22_ex07_actual_operation_receipt_intake_bodyfree"),
        "ex07_next_required_step": ex07.get("next_required_step"),
        "ex07_operation_receipt_status_ref": ex07.get("operation_receipt_status_ref"),
        "ex07_actual_source_guard_passed": ex07.get("actual_source_guard_passed") is True,
        "ex07_actual_human_review_executed_by_person": ex07.get("actual_human_review_executed_by_person") is True,
        "ex07_reviewed_case_count": _int_value_or_zero(ex07.get("reviewed_case_count")),
        "ex07_selection_row_count": _int_value_or_zero(ex07.get("selection_row_count")),
        "ex09_schema_version": ex09.get("schema_version"),
        "ex09_material_ref": ex09.get("material_id", "postcr22_ex09_sanitized_review_result_rows_intake_bodyfree"),
        "ex09_next_required_step": ex09.get("next_required_step"),
        "ex09_sanitized_review_result_rows_intake_status_ref": ex09.get("sanitized_review_result_rows_intake_status_ref"),
        "ex09_actual_sanitized_review_result_rows_intaken_here": ex09.get("actual_sanitized_review_result_rows_intaken_here") is True,
        "ex09_actual_rows_source_guard_passed": ex09.get("ex08_actual_rows_source_guard_passed") is True,
        "ex09_sanitized_review_result_row_count": _int_value_or_zero(ex09.get("sanitized_review_result_row_count")),
        "ex10_schema_version": ex10.get("schema_version"),
        "ex10_material_ref": ex10.get("material_id", "postcr22_ex10_rating_row_normalization_threshold_summary_bodyfree"),
        "ex10_next_required_step": ex10.get("next_required_step"),
        "ex10_rating_row_normalization_status_ref": ex10.get("rating_row_normalization_status_ref"),
        "ex10_actual_rating_rows_materialized_here": ex10.get("actual_rating_rows_materialized_here") is True,
        "ex10_rating_row_count": _int_value_or_zero(ex10.get("rating_row_count")),
        "ex12_schema_version": ex12.get("schema_version"),
        "ex12_material_ref": ex12.get("material_id", "postcr22_ex12_question_need_observation_normalization_bodyfree"),
        "ex12_next_required_step": ex12.get("next_required_step"),
        "ex12_question_need_observation_normalization_status_ref": ex12.get("question_need_observation_normalization_status_ref"),
        "ex12_actual_question_need_observation_rows_materialized_here": ex12.get("actual_question_need_observation_rows_materialized_here") is True,
        "ex12_question_need_observation_row_count": _int_value_or_zero(ex12.get("question_need_observation_row_count")),
        "ex13_schema_version": ex13.get("schema_version"),
        "ex13_material_ref": ex13.get("material_id", "postcr22_ex13_rating_question_consistency_guard_bodyfree"),
        "ex13_next_required_step": ex13.get("next_required_step"),
        "ex13_rating_question_consistency_guard_status_ref": ex13.get("rating_question_consistency_guard_status_ref"),
        "ex13_rating_question_consistency_guard_passed": ex13.get("rating_question_consistency_guard_passed") is True,
        "ex13_consistency_issue_row_count": _int_value_or_zero(ex13.get("consistency_issue_row_count")),
        "ex15_schema_version": ex15.get("schema_version"),
        "ex15_material_ref": ex15.get("material_id", "postcr22_ex15_final_no_body_no_question_no_touch_validation_bodyfree"),
        "ex15_next_required_step": ex15.get("next_required_step"),
        "ex15_final_validation_status_ref": ex15.get("final_validation_status_ref"),
        "ex15_final_validation_passed": ex15.get("final_validation_passed") is True,
        "ex15_no_body_leak_validation_passed": ex15.get("no_body_leak_validation_passed") is True,
        "ex15_no_question_text_validation_passed": ex15.get("no_question_text_validation_passed") is True,
        "ex15_no_touch_validation_passed": ex15.get("no_touch_validation_passed") is True,
        "ex15_no_local_path_or_hash_validation_passed": ex15.get("no_local_path_or_hash_validation_passed") is True,
        "ex15_disposal_verified": ex15.get("disposal_verified") is True,
        "evidence_complete_predicate_status_ref": status_ref,
        "evidence_complete_predicate_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX16_ALLOWED_EVIDENCE_STATUS_REFS),
        "evidence_complete_predicate_evaluated": True,
        "evidence_complete_predicate_passed": passed,
        "evidence_complete_predicate_reason_refs": [P7_R54_AHR_POST_CR22_EX16_READY_REASON_REF] if passed else [],
        "evidence_complete_predicate_blocker_refs": blocker_refs,
        "evidence_complete_predicate_blocker_ref_count": len(blocker_refs),
        "required_case_count": P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "actual_source_guard_passed": passed and ex07.get("actual_source_guard_passed") is True and ex09.get("ex08_actual_rows_source_guard_passed") is True,
        "actual_human_review_executed_by_person": passed and ex07.get("actual_human_review_executed_by_person") is True,
        "reviewed_case_count": _int_value_or_zero(ex07.get("reviewed_case_count")) if passed else 0,
        "reviewed_case_count_is_24": passed and _int_value_or_zero(ex07.get("reviewed_case_count")) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "selection_row_count": _int_value_or_zero(ex07.get("selection_row_count")) if passed else 0,
        "selection_row_count_is_24": passed and _int_value_or_zero(ex07.get("selection_row_count")) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count": _int_value_or_zero(ex09.get("sanitized_review_result_row_count")) if passed else 0,
        "sanitized_review_result_row_count_is_24": passed and _int_value_or_zero(ex09.get("sanitized_review_result_row_count")) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "rating_row_count": _int_value_or_zero(ex10.get("rating_row_count")) if passed else 0,
        "rating_row_count_is_24": passed and _int_value_or_zero(ex10.get("rating_row_count")) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "question_need_observation_row_count": _int_value_or_zero(ex12.get("question_need_observation_row_count")) if passed else 0,
        "question_need_observation_row_count_is_24": passed and _int_value_or_zero(ex12.get("question_need_observation_row_count")) == P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT,
        "disposal_verified": passed and ex15.get("disposal_verified") is True,
        "no_body_leak_validation_passed": passed and ex15.get("no_body_leak_validation_passed") is True,
        "no_question_text_validation_passed": passed and ex15.get("no_question_text_validation_passed") is True,
        "no_touch_validation_passed": passed and ex15.get("no_touch_validation_passed") is True,
        "no_local_path_or_hash_validation_passed": passed and ex15.get("no_local_path_or_hash_validation_passed") is True,
        "consistency_guard_passed": passed and ex13.get("rating_question_consistency_guard_passed") is True,
        "consistency_issue_row_count": _int_value_or_zero(ex13.get("consistency_issue_row_count")) if passed else 0,
        "body_or_question_leak_refs": body_or_question_leak_refs,
        "body_or_question_leak_ref_count": len(body_or_question_leak_refs),
        "path_or_hash_leak_refs": path_or_hash_leak_refs,
        "path_or_hash_leak_ref_count": len(path_or_hash_leak_refs),
        "contract_mutation_refs": contract_mutation_refs,
        "contract_mutation_ref_count": len(contract_mutation_refs),
        "evidence_complete_does_not_finalize_p5": True,
        "evidence_complete_does_not_start_p6": True,
        "evidence_complete_does_not_start_p8": True,
        "evidence_complete_does_not_request_or_execute_r52": True,
        "evidence_complete_does_not_complete_p7_or_release": True,
        "actual_rating_rows_materialized_here": passed,
        "actual_question_need_observation_rows_materialized_here": passed,
        "actual_disposal_receipt_materialized_here": passed,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": passed,
        "actual_human_review_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX16_IMPLEMENTED_STEPS if passed else P7_R54_AHR_POST_CR22_EX15_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX16_NOT_YET_IMPLEMENTED_STEPS if passed else P7_R54_AHR_POST_CR22_EX15_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX17_STEP_REF if passed else P7_R54_AHR_POST_CR22_EX16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_rating_rows_materialized_here"] = passed
    material["actual_question_need_observation_rows_materialized_here"] = passed
    material["actual_disposal_receipt_materialized_here"] = passed
    material["disposal_verified"] = passed and ex15.get("disposal_verified") is True
    material["actual_review_evidence_complete"] = passed
    material["actual_human_review_run_here"] = False
    material["actual_human_review_complete"] = False
    material["p8_start_allowed"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX16_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX16")
    return material


def assert_p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX16_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX16")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX16_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX16",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX16_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX16")
    if tuple(data.get("evidence_complete_predicate_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX16_ALLOWED_EVIDENCE_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX16 allowed status refs changed")
    status_ref = data.get("evidence_complete_predicate_status_ref")
    passed = status_ref == P7_R54_AHR_POST_CR22_EX16_EVIDENCE_COMPLETE_STATUS_REF
    if data.get("evidence_complete_predicate_evaluated") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX16 predicate must be evaluated")
    if data.get("evidence_complete_predicate_passed") is not passed:
        raise ValueError("P7-R54-AHR-PostCR22-EX16 predicate passed flag changed")
    blockers = list(data.get("evidence_complete_predicate_blocker_refs") or [])
    if data.get("evidence_complete_predicate_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX16 blocker count changed")
    for refs_key, count_key in (
        ("body_or_question_leak_refs", "body_or_question_leak_ref_count"),
        ("path_or_hash_leak_refs", "path_or_hash_leak_ref_count"),
        ("contract_mutation_refs", "contract_mutation_ref_count"),
    ):
        if data.get(count_key) != len(data.get(refs_key) or []):
            raise ValueError(f"P7-R54-AHR-PostCR22-EX16 {count_key} changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX16",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX16_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX16 required false field changed: {key}")
    for key in (
        "evidence_complete_does_not_finalize_p5",
        "evidence_complete_does_not_start_p6",
        "evidence_complete_does_not_start_p8",
        "evidence_complete_does_not_request_or_execute_r52",
        "evidence_complete_does_not_complete_p7_or_release",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX16 required true boundary changed: {key}")
    if passed:
        if blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 passed predicate cannot carry blockers")
        if data.get("evidence_complete_predicate_reason_refs") != [P7_R54_AHR_POST_CR22_EX16_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 passed reason changed")
        for key in (
            "actual_source_guard_passed",
            "actual_human_review_executed_by_person",
            "reviewed_case_count_is_24",
            "selection_row_count_is_24",
            "sanitized_review_result_row_count_is_24",
            "rating_row_count_is_24",
            "question_need_observation_row_count_is_24",
            "disposal_verified",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "no_local_path_or_hash_validation_passed",
            "consistency_guard_passed",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "actual_review_evidence_complete",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX16 required true field changed: {key}")
        for count_key in (
            "reviewed_case_count",
            "selection_row_count",
            "sanitized_review_result_row_count",
            "rating_row_count",
            "question_need_observation_row_count",
        ):
            if data.get(count_key) != P7_R54_AHR_POST_CR22_EX04_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX16 {count_key} must be 24")
        if data.get("consistency_issue_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 passed predicate cannot carry consistency issues")
        if data.get("body_or_question_leak_refs") != [] or data.get("path_or_hash_leak_refs") != [] or data.get("contract_mutation_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 passed predicate cannot carry leak refs")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX17_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 passed next step changed")
    else:
        if status_ref != P7_R54_AHR_POST_CR22_EX16_EVIDENCE_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 blocked predicate must carry blockers")
        if data.get("evidence_complete_predicate_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 blocked predicate cannot carry ready reasons")
        if data.get("actual_review_evidence_complete") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 blocked predicate cannot complete evidence")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX16_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX16 blocked next step changed")
    return True


def _postcr22_case_ref_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return _dedupe_refs([clean_identifier(item, default="", max_length=180) for item in value])


def build_p7_r54_ahr_post_cr22_ex17_p5_p6_p8_r52_candidate_only_separation(
    *,
    actual_review_evidence_complete_predicate: Mapping[str, Any] | None = None,
    readfeel_execution_p5_p4_blocker_classification: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX17 body-free candidate-only separation material."""

    ex16 = actual_review_evidence_complete_predicate or build_p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate()
    assert_p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate_contract(ex16)
    ex11 = readfeel_execution_p5_p4_blocker_classification or build_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification()
    assert_p7_r54_ahr_post_cr22_ex11_readfeel_execution_p5_p4_blocker_classification_contract(ex11)
    ex12 = question_need_observation_normalization or build_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization()
    assert_p7_r54_ahr_post_cr22_ex12_question_need_observation_normalization_contract(ex12)
    ex13 = rating_question_consistency_guard or build_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard()
    assert_p7_r54_ahr_post_cr22_ex13_rating_question_consistency_guard_contract(ex13)
    session_id = _safe_review_session_id(review_session_id or ex16.get("review_session_id"))

    source_blockers: list[str] = []
    if ex16.get("schema_version") != P7_R54_AHR_POST_CR22_EX16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION:
        source_blockers.append("ex16_schema_version_not_current")
    if ex16.get("evidence_complete_predicate_passed") is not True or ex16.get("actual_review_evidence_complete") is not True:
        source_blockers.append("ex16_actual_review_evidence_not_complete")
    if ex16.get("next_required_step") != P7_R54_AHR_POST_CR22_EX17_STEP_REF:
        source_blockers.append("ex16_next_step_not_ex17")
    if ex11.get("schema_version") != P7_R54_AHR_POST_CR22_EX11_READFEEL_EXECUTION_P5_P4_BLOCKER_CLASSIFICATION_SCHEMA_VERSION:
        source_blockers.append("ex11_schema_version_not_current")
    if ex11.get("readfeel_execution_p5_p4_blocker_classification_status_ref") != P7_R54_AHR_POST_CR22_EX11_BLOCKERS_CLASSIFIED_STATUS_REF:
        source_blockers.append("ex11_blocker_classification_not_ready")
    if ex12.get("schema_version") != P7_R54_AHR_POST_CR22_EX12_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        source_blockers.append("ex12_schema_version_not_current")
    if ex12.get("question_need_observation_normalization_status_ref") != P7_R54_AHR_POST_CR22_EX12_QUESTION_OBSERVATIONS_NORMALIZED_STATUS_REF:
        source_blockers.append("ex12_question_need_observation_not_ready")
    if ex13.get("schema_version") != P7_R54_AHR_POST_CR22_EX13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        source_blockers.append("ex13_schema_version_not_current")
    if ex13.get("rating_question_consistency_guard_passed") is not True:
        source_blockers.append("ex13_rating_question_consistency_guard_not_passed")
    blockers = _dedupe_refs(source_blockers)
    ready = not blockers
    status_ref = (
        P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_BLOCKED_STATUS_REF
    )

    p5_repair_refs = _postcr22_case_ref_list(ex11.get("p5_repair_required_case_refs")) if ready else []
    p4_repair_refs = _postcr22_case_ref_list(ex11.get("p4_current_only_repair_required_case_refs")) if ready else []
    operation_blocked_refs = _postcr22_case_ref_list(ex11.get("operation_blocked_case_refs")) if ready else []
    inconclusive_refs = _postcr22_case_ref_list(ex11.get("inconclusive_case_refs")) if ready else []
    p8_candidate_refs = _postcr22_case_ref_list(ex13.get("p8_material_candidate_case_refs_bodyfree_only")) if ready else []
    p5_confirmed_refs = _postcr22_case_ref_list(ex11.get("no_blocker_case_refs")) if ready and not (p5_repair_refs or p4_repair_refs or operation_blocked_refs or inconclusive_refs) else []
    r52_candidate_refs = list(p5_confirmed_refs)

    selected_decision_refs: list[str] = []
    if ready:
        if p5_confirmed_refs:
            selected_decision_refs.append("P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY")
            selected_decision_refs.append("P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY")
            selected_decision_refs.append("R52_REINTAKE_HANDOFF_CANDIDATE_ONLY")
        if p5_repair_refs:
            selected_decision_refs.append("P5_REPAIR_REQUIRED_BEFORE_R52_REINTAKE")
        if p4_repair_refs:
            selected_decision_refs.append("P4_CURRENT_ONLY_REPAIR_REQUIRED_BEFORE_R52_REINTAKE")
        if operation_blocked_refs:
            selected_decision_refs.append("R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT")
        if not ex16.get("disposal_verified"):
            selected_decision_refs.append("R54_OPERATION_BLOCKED_DISPOSAL_NOT_VERIFIED")
        if inconclusive_refs:
            selected_decision_refs.append("R54_OPERATION_INCONCLUSIVE_INSUFFICIENT_MATERIAL")
        if p8_candidate_refs:
            selected_decision_refs.append("P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY")
    selected_decision_refs = _dedupe_refs(selected_decision_refs)

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX17_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX17_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX17_STEP_REF,
        "current_phase": "P7 Product Quality Runner / Long-run Product Gate",
        "material_id": "p7_r54_ahr_post_cr22_ex17_p5_p6_p8_r52_candidate_only_separation_20260629",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex16_schema_version": ex16.get("schema_version"),
        "ex16_material_ref": ex16.get("material_id", "postcr22_ex16_actual_review_evidence_complete_predicate_bodyfree"),
        "ex16_next_required_step": ex16.get("next_required_step"),
        "ex16_evidence_complete_predicate_status_ref": ex16.get("evidence_complete_predicate_status_ref"),
        "ex16_evidence_complete_predicate_passed": ex16.get("evidence_complete_predicate_passed") is True,
        "ex16_actual_review_evidence_complete": ex16.get("actual_review_evidence_complete") is True,
        "ex16_actual_source_guard_passed": ex16.get("actual_source_guard_passed") is True,
        "ex16_reviewed_case_count": _int_value_or_zero(ex16.get("reviewed_case_count")),
        "ex16_sanitized_review_result_row_count": _int_value_or_zero(ex16.get("sanitized_review_result_row_count")),
        "ex16_rating_row_count": _int_value_or_zero(ex16.get("rating_row_count")),
        "ex16_question_need_observation_row_count": _int_value_or_zero(ex16.get("question_need_observation_row_count")),
        "ex16_disposal_verified": ex16.get("disposal_verified") is True,
        "ex11_schema_version": ex11.get("schema_version"),
        "ex11_material_ref": ex11.get("material_id", "postcr22_ex11_blocker_classification_bodyfree"),
        "ex11_next_required_step": ex11.get("next_required_step"),
        "ex11_readfeel_execution_p5_p4_blocker_classification_status_ref": ex11.get("readfeel_execution_p5_p4_blocker_classification_status_ref"),
        "ex11_no_blocker_case_count": _int_value_or_zero(ex11.get("no_blocker_case_count")),
        "ex11_p5_repair_required_case_count": _int_value_or_zero(ex11.get("p5_repair_required_case_count")),
        "ex11_p4_current_only_repair_required_case_count": _int_value_or_zero(ex11.get("p4_current_only_repair_required_case_count")),
        "ex11_operation_blocked_case_count": _int_value_or_zero(ex11.get("operation_blocked_case_count")),
        "ex11_inconclusive_case_count": _int_value_or_zero(ex11.get("inconclusive_case_count")),
        "ex12_schema_version": ex12.get("schema_version"),
        "ex12_material_ref": ex12.get("material_id", "postcr22_ex12_question_need_observation_normalization_bodyfree"),
        "ex12_next_required_step": ex12.get("next_required_step"),
        "ex12_question_need_observation_normalization_status_ref": ex12.get("question_need_observation_normalization_status_ref"),
        "ex12_p8_material_candidate_case_count_bodyfree_only": _int_value_or_zero(ex12.get("p8_material_candidate_case_count_bodyfree_only")),
        "ex13_schema_version": ex13.get("schema_version"),
        "ex13_material_ref": ex13.get("material_id", "postcr22_ex13_rating_question_consistency_guard_bodyfree"),
        "ex13_next_required_step": ex13.get("next_required_step"),
        "ex13_rating_question_consistency_guard_status_ref": ex13.get("rating_question_consistency_guard_status_ref"),
        "ex13_rating_question_consistency_guard_passed": ex13.get("rating_question_consistency_guard_passed") is True,
        "candidate_only_separation_status_ref": status_ref,
        "candidate_only_separation_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX17_ALLOWED_CANDIDATE_SEPARATION_STATUS_REFS),
        "candidate_only_separation_ready": ready,
        "candidate_only_separation_reason_refs": [P7_R54_AHR_POST_CR22_EX17_READY_REASON_REF] if ready else [],
        "candidate_only_separation_blocker_refs": blockers,
        "candidate_only_separation_blocker_ref_count": len(blockers),
        "decision_ref_options": list(P7_R54_AHR_POST_CR22_EX17_DECISION_REFS),
        "decision_ref_option_count": len(P7_R54_AHR_POST_CR22_EX17_DECISION_REFS),
        "selected_decision_refs": selected_decision_refs,
        "selected_decision_ref_count": len(selected_decision_refs),
        "p5_confirmed_candidate_bodyfree_only": bool(p5_confirmed_refs),
        "p5_confirmed_candidate_case_refs": p5_confirmed_refs,
        "p5_confirmed_candidate_case_count": len(p5_confirmed_refs),
        "p5_repair_required_before_r52_reintake": bool(p5_repair_refs),
        "p5_repair_required_case_refs": p5_repair_refs,
        "p5_repair_required_case_count": len(p5_repair_refs),
        "p4_current_only_repair_required_before_r52_reintake": bool(p4_repair_refs),
        "p4_current_only_repair_required_case_refs": p4_repair_refs,
        "p4_current_only_repair_required_case_count": len(p4_repair_refs),
        "operation_blocked_case_refs": operation_blocked_refs,
        "operation_blocked_case_count": len(operation_blocked_refs),
        "operation_blocked_body_leak_or_question_text": bool(operation_blocked_refs),
        "operation_blocked_disposal_not_verified": ready and not (ex16.get("disposal_verified") is True),
        "inconclusive_insufficient_material_case_refs": inconclusive_refs,
        "inconclusive_insufficient_material_case_count": len(inconclusive_refs),
        "p6_limited_human_readfeel_candidate_only": bool(p5_confirmed_refs),
        "p8_question_need_observation_material_candidate_only": bool(p8_candidate_refs),
        "p8_material_candidate_case_refs_bodyfree_only": p8_candidate_refs,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_candidate_refs),
        "r52_reintake_handoff_candidate_only": bool(r52_candidate_refs),
        "r52_reintake_handoff_candidate_case_refs": r52_candidate_refs,
        "r52_reintake_handoff_candidate_case_count": len(r52_candidate_refs),
        "candidate_only_separation_does_not_finalize_p5": True,
        "candidate_only_separation_does_not_start_p6": True,
        "candidate_only_separation_does_not_start_p8": True,
        "candidate_only_separation_does_not_execute_r52": True,
        "candidate_only_separation_does_not_complete_p7_or_release": True,
        "actual_source_guard_passed": ready and ex16.get("actual_source_guard_passed") is True,
        "actual_human_review_executed_by_person": ready and ex16.get("actual_human_review_executed_by_person") is True,
        "actual_rating_rows_materialized_here": ready and ex16.get("actual_rating_rows_materialized_here") is True,
        "actual_question_need_observation_rows_materialized_here": ready and ex16.get("actual_question_need_observation_rows_materialized_here") is True,
        "actual_disposal_receipt_materialized_here": ready and ex16.get("actual_disposal_receipt_materialized_here") is True,
        "disposal_verified": ready and ex16.get("disposal_verified") is True,
        "actual_review_evidence_complete": ready and ex16.get("actual_review_evidence_complete") is True,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX17_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX16_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX17_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX16_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX18_STEP_REF if ready else P7_R54_AHR_POST_CR22_EX17_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["actual_rating_rows_materialized_here"] = ready and ex16.get("actual_rating_rows_materialized_here") is True
    material["actual_question_need_observation_rows_materialized_here"] = ready and ex16.get("actual_question_need_observation_rows_materialized_here") is True
    material["actual_disposal_receipt_materialized_here"] = ready and ex16.get("actual_disposal_receipt_materialized_here") is True
    material["disposal_verified"] = ready and ex16.get("disposal_verified") is True
    material["actual_review_evidence_complete"] = ready and ex16.get("actual_review_evidence_complete") is True
    material["actual_human_review_run_here"] = False
    material["actual_human_review_complete"] = False
    material["p8_start_allowed"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_CR22_EX17_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX17")
    return material


def assert_p7_r54_ahr_post_cr22_ex17_p5_p6_p8_r52_candidate_only_separation_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX17_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX17")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX17_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX17_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX17",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX17_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX17")
    if tuple(data.get("candidate_only_separation_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX17_ALLOWED_CANDIDATE_SEPARATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX17 allowed status refs changed")
    if tuple(data.get("decision_ref_options") or ()) != P7_R54_AHR_POST_CR22_EX17_DECISION_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX17 decision refs changed")
    if data.get("decision_ref_option_count") != len(P7_R54_AHR_POST_CR22_EX17_DECISION_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX17 decision ref option count changed")
    ready = data.get("candidate_only_separation_status_ref") == P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_READY_STATUS_REF
    if data.get("candidate_only_separation_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX17 ready flag changed")
    blockers = list(data.get("candidate_only_separation_blocker_refs") or [])
    if data.get("candidate_only_separation_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostCR22-EX17 blocker count changed")
    selected = list(data.get("selected_decision_refs") or [])
    if data.get("selected_decision_ref_count") != len(selected):
        raise ValueError("P7-R54-AHR-PostCR22-EX17 selected decision count changed")
    for decision_ref in selected:
        if decision_ref not in P7_R54_AHR_POST_CR22_EX17_DECISION_REFS:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX17 unknown decision ref: {decision_ref}")
    for refs_key, count_key in (
        ("p5_confirmed_candidate_case_refs", "p5_confirmed_candidate_case_count"),
        ("p5_repair_required_case_refs", "p5_repair_required_case_count"),
        ("p4_current_only_repair_required_case_refs", "p4_current_only_repair_required_case_count"),
        ("operation_blocked_case_refs", "operation_blocked_case_count"),
        ("inconclusive_insufficient_material_case_refs", "inconclusive_insufficient_material_case_count"),
        ("p8_material_candidate_case_refs_bodyfree_only", "p8_material_candidate_case_count_bodyfree_only"),
        ("r52_reintake_handoff_candidate_case_refs", "r52_reintake_handoff_candidate_case_count"),
    ):
        if data.get(count_key) != len(data.get(refs_key) or []):
            raise ValueError(f"P7-R54-AHR-PostCR22-EX17 {count_key} changed")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX17",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX17_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX17 required false field changed: {key}")
    for key in (
        "candidate_only_separation_does_not_finalize_p5",
        "candidate_only_separation_does_not_start_p6",
        "candidate_only_separation_does_not_start_p8",
        "candidate_only_separation_does_not_execute_r52",
        "candidate_only_separation_does_not_complete_p7_or_release",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX17 required true boundary changed: {key}")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 ready material cannot carry blockers")
        if data.get("candidate_only_separation_reason_refs") != [P7_R54_AHR_POST_CR22_EX17_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 ready reason changed")
        for key in (
            "actual_source_guard_passed",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "actual_review_evidence_complete",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX17 required true field changed: {key}")
        if data.get("p5_confirmed_candidate_bodyfree_only") is True:
            for decision_ref in (
                "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY",
                "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY",
                "R52_REINTAKE_HANDOFF_CANDIDATE_ONLY",
            ):
                if decision_ref not in selected:
                    raise ValueError(f"P7-R54-AHR-PostCR22-EX17 missing selected decision: {decision_ref}")
        if data.get("p8_question_need_observation_material_candidate_only") is True and "P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY" not in selected:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 missing P8 material candidate decision")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX18_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 ready next step changed")
    else:
        if data.get("candidate_only_separation_status_ref") != P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 blocked material must carry blockers")
        if data.get("candidate_only_separation_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 blocked material cannot carry ready reasons")
        if data.get("actual_review_evidence_complete") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 blocked material cannot claim evidence complete")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX17_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX17 blocked next step changed")
    return True




def build_p7_r54_ahr_post_cr22_ex18_validation_command_row(
    *,
    command_ref: Any,
    command_status_ref: Any = None,
    ran_here: bool = False,
    green_claimed: bool = False,
) -> dict[str, Any]:
    """Build one EX18 body-free validation command matrix row."""

    ref = clean_identifier(command_ref, default="ex18_unknown_validation_command_ref", max_length=160)
    definition = P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_DEFINITIONS.get(ref, {})
    status_ref = clean_identifier(
        command_status_ref,
        default=P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
        max_length=120,
    )
    if status_ref not in P7_R54_AHR_POST_CR22_EX18_ALLOWED_COMMAND_STATUS_REFS:
        status_ref = P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF
    row = {
        "command_ref": ref,
        "command_kind_ref": clean_identifier(definition.get("command_kind_ref"), default="unknown", max_length=120),
        "command_scope_ref": clean_identifier(definition.get("command_scope_ref"), default="unknown", max_length=180),
        "command_display_ref": clean_identifier(definition.get("command_display_ref"), default="bodyfree_command_ref", max_length=520),
        "required": ref in P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS,
        "command_status_ref": status_ref,
        "command_status_allowed_refs": list(P7_R54_AHR_POST_CR22_EX18_ALLOWED_COMMAND_STATUS_REFS),
        "passed": status_ref == P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF,
        "ran_here": bool(ran_here),
        "green_claimed": bool(green_claimed),
        "full_backend_suite_green_claimed": False,
        "rn_contract_green_claimed": False,
        "rn_real_device_modal_claimed": False,
        "actual_human_review_complete_claimed_by_command": False,
        "p5_final_claimed": False,
        "p6_start_claimed": False,
        "p8_start_claimed": False,
        "r52_actual_execution_claimed": False,
        "p7_complete_claimed": False,
        "release_allowed_claimed": False,
        "raw_terminal_output_included": False,
        "terminal_output_body_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "body_free": True,
    }
    assert_p7_r54_ahr_post_cr22_ex18_validation_command_row_contract(row)
    return row


def assert_p7_r54_ahr_post_cr22_ex18_validation_command_row_contract(row: Mapping[str, Any]) -> bool:
    _required_fields_present(
        row,
        required=tuple(P7_R54_AHR_POST_CR22_EX18_ALLOWED_VALIDATION_COMMAND_ROW_KEY_REFS),
        source="P7-R54-AHR-PostCR22-EX18.validation_command_row",
    )
    _assert_no_payload_keys(row, source="P7-R54-AHR-PostCR22-EX18.validation_command_row")
    if row.get("command_ref") not in P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation command row unknown command_ref")
    if row.get("command_status_ref") not in P7_R54_AHR_POST_CR22_EX18_ALLOWED_COMMAND_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation command row status changed")
    if tuple(row.get("command_status_allowed_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_ALLOWED_COMMAND_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation command row allowed statuses changed")
    if row.get("passed") is not (row.get("command_status_ref") == P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF):
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation command row passed flag changed")
    if row.get("required") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation command row must remain required")
    for key in (
        "full_backend_suite_green_claimed",
        "rn_contract_green_claimed",
        "rn_real_device_modal_claimed",
        "actual_human_review_complete_claimed_by_command",
        "p5_final_claimed",
        "p6_start_claimed",
        "p8_start_claimed",
        "r52_actual_execution_claimed",
        "p7_complete_claimed",
        "release_allowed_claimed",
        "raw_terminal_output_included",
        "terminal_output_body_included",
        "stdout_body_included",
        "stderr_body_included",
        "traceback_body_included",
        "local_absolute_path_included",
        "body_hash_included",
    ):
        if row.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX18 validation command row must keep {key}=False")
    if row.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation command row must remain body-free")
    return True


def build_p7_r54_ahr_post_cr22_ex18_validation_command_rows_input(
    *, command_status_ref: Any = None, ran_here: bool = False, green_claimed: bool = False
) -> list[dict[str, Any]]:
    return [
        build_p7_r54_ahr_post_cr22_ex18_validation_command_row(
            command_ref=command_ref,
            command_status_ref=command_status_ref,
            ran_here=ran_here,
            green_claimed=green_claimed,
        )
        for command_ref in P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS
    ]


def _clean_ex18_validation_command_rows(
    rows: Sequence[Mapping[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    raw_rows: Sequence[Mapping[str, Any]] = (
        list(rows)
        if rows is not None
        else build_p7_r54_ahr_post_cr22_ex18_validation_command_rows_input()
    )
    cleaned: list[dict[str, Any]] = []
    forbidden_row_refs: list[str] = []
    promotion_claim_refs: list[str] = []
    for index, row in enumerate(raw_rows):
        row_ref = f"ex18_validation_command_row_{index + 1:02d}"
        if not isinstance(row, Mapping):
            forbidden_row_refs.append(row_ref)
            continue
        command_ref = clean_identifier(row.get("command_ref"), default=row_ref, max_length=160)
        definition = P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_DEFINITIONS.get(command_ref, {})
        extra_keys = sorted(
            str(key)
            for key in row.keys()
            if str(key) not in P7_R54_AHR_POST_CR22_EX18_ALLOWED_VALIDATION_COMMAND_ROW_KEY_REFS
        )
        if extra_keys:
            forbidden_row_refs.append(command_ref)
        for flag_ref in (
            "raw_terminal_output_included",
            "terminal_output_body_included",
            "stdout_body_included",
            "stderr_body_included",
            "traceback_body_included",
            "local_absolute_path_included",
            "body_hash_included",
        ):
            if row.get(flag_ref) is True:
                forbidden_row_refs.append(command_ref)
        for claim_ref in (
            "full_backend_suite_green_claimed",
            "rn_contract_green_claimed",
            "rn_real_device_modal_claimed",
            "actual_human_review_complete_claimed_by_command",
            "p5_final_claimed",
            "p6_start_claimed",
            "p8_start_claimed",
            "r52_actual_execution_claimed",
            "p7_complete_claimed",
            "release_allowed_claimed",
        ):
            if row.get(claim_ref) is True:
                promotion_claim_refs.append(command_ref)
        status_ref = clean_identifier(
            row.get("command_status_ref"),
            default=P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF,
            max_length=120,
        )
        if status_ref not in P7_R54_AHR_POST_CR22_EX18_ALLOWED_COMMAND_STATUS_REFS:
            forbidden_row_refs.append(command_ref)
            status_ref = P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_NOT_RUN_NOT_CLAIMED_REF
        cleaned.append(
            {
                "command_ref": command_ref,
                "command_kind_ref": clean_identifier(definition.get("command_kind_ref"), default="unknown", max_length=120),
                "command_scope_ref": clean_identifier(definition.get("command_scope_ref"), default="unknown", max_length=180),
                "command_display_ref": clean_identifier(definition.get("command_display_ref"), default="bodyfree_command_ref", max_length=520),
                "required": command_ref in P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS,
                "command_status_ref": status_ref,
                "command_status_allowed_refs": list(P7_R54_AHR_POST_CR22_EX18_ALLOWED_COMMAND_STATUS_REFS),
                "passed": status_ref == P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF,
                "ran_here": bool(row.get("ran_here")),
                "green_claimed": bool(row.get("green_claimed")),
                "full_backend_suite_green_claimed": False,
                "rn_contract_green_claimed": False,
                "rn_real_device_modal_claimed": False,
                "actual_human_review_complete_claimed_by_command": False,
                "p5_final_claimed": False,
                "p6_start_claimed": False,
                "p8_start_claimed": False,
                "r52_actual_execution_claimed": False,
                "p7_complete_claimed": False,
                "release_allowed_claimed": False,
                "raw_terminal_output_included": False,
                "terminal_output_body_included": False,
                "stdout_body_included": False,
                "stderr_body_included": False,
                "traceback_body_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "body_free": True,
            }
        )
    return cleaned, _dedupe_refs(forbidden_row_refs), _dedupe_refs(promotion_claim_refs)


def _ex18_validation_command_blockers(
    rows: Sequence[Mapping[str, Any]] | None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, list[str]]]:
    cleaned, forbidden_row_refs, promotion_claim_refs = _clean_ex18_validation_command_rows(rows)
    command_refs = [str(row["command_ref"]) for row in cleaned]
    duplicate_refs = _duplicate_refs(command_refs)
    missing_refs = [ref for ref in P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS if ref not in command_refs]
    by_ref = {str(row["command_ref"]): row for row in cleaned}
    nonpassed_required_refs = [
        ref
        for ref in P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS
        if by_ref.get(ref, {}).get("command_status_ref") != P7_R54_AHR_POST_CR22_EX18_COMMAND_STATUS_PASSED_REF
    ]
    blockers: list[str] = []
    if missing_refs:
        blockers.append("ex18_required_validation_command_missing")
    if duplicate_refs:
        blockers.append("ex18_validation_command_duplicate")
    if nonpassed_required_refs:
        blockers.append("ex18_required_validation_command_not_passed")
    if forbidden_row_refs:
        blockers.append("ex18_validation_command_forbidden_body_question_path_hash_key")
    if promotion_claim_refs:
        blockers.append("ex18_validation_command_promotion_claim_detected")
    detail = {
        "missing_refs": missing_refs,
        "duplicate_refs": duplicate_refs,
        "nonpassed_required_refs": nonpassed_required_refs,
        "forbidden_row_refs": forbidden_row_refs,
        "promotion_claim_refs": promotion_claim_refs,
    }
    return cleaned, _dedupe_refs(blockers), detail


def build_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold(
    *,
    candidate_only_separation: Mapping[str, Any] | None = None,
    validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    result_memo_ref: Any = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build EX18 body-free validation command matrix / result memo / next-decision hold."""

    ex17 = dict(candidate_only_separation or build_p7_r54_ahr_post_cr22_ex17_p5_p6_p8_r52_candidate_only_separation())
    rows, validation_blockers, validation_detail = _ex18_validation_command_blockers(validation_command_rows)
    result_memo_ref_text = clean_identifier(
        result_memo_ref,
        default=P7_R54_AHR_POST_CR22_EX18_DEFAULT_RESULT_MEMO_REF,
        max_length=220,
    )
    result_memo_ref_present = bool(result_memo_ref_text)
    ex17_ready = (
        ex17.get("schema_version") == P7_R54_AHR_POST_CR22_EX17_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION
        and ex17.get("candidate_only_separation_status_ref") == P7_R54_AHR_POST_CR22_EX17_CANDIDATE_SEPARATION_READY_STATUS_REF
        and ex17.get("candidate_only_separation_ready") is True
        and ex17.get("actual_review_evidence_complete") is True
        and ex17.get("next_required_step") == P7_R54_AHR_POST_CR22_EX18_STEP_REF
    )
    ex17_blockers: list[str] = []
    if not ex17_ready:
        ex17_blockers.append("ex17_candidate_only_separation_not_ready_for_ex18")
    if not result_memo_ref_present:
        ex17_blockers.append("ex18_result_memo_ref_missing")
    validation_ready = not validation_blockers
    result_memo_ready = ex17_ready and validation_ready and result_memo_ref_present
    ready = result_memo_ready
    blocker_refs = _dedupe_refs([*ex17_blockers, *validation_blockers])
    status_ref = P7_R54_AHR_POST_CR22_EX18_READY_STATUS_REF if ready else P7_R54_AHR_POST_CR22_EX18_BLOCKED_STATUS_REF
    actual_review_evidence_complete = bool(ex17.get("actual_review_evidence_complete")) if ready else False
    actual_source_guard_passed = bool(ex17.get("actual_source_guard_passed")) if ready else False
    actual_human_review_executed_by_person = bool(ex17.get("actual_human_review_executed_by_person")) if ready else False
    actual_rating_rows_materialized = bool(ex17.get("actual_rating_rows_materialized_here")) if ready else False
    actual_question_need_rows_materialized = bool(ex17.get("actual_question_need_observation_rows_materialized_here")) if ready else False
    actual_disposal_receipt_materialized = bool(ex17.get("actual_disposal_receipt_materialized_here")) if ready else False
    disposal_verified = bool(ex17.get("disposal_verified")) if ready else False
    row_counts = {
        "reviewed_case_count": _int_value_or_zero(ex17.get("ex16_reviewed_case_count")),
        "selection_row_count": _int_value_or_zero(ex17.get("ex16_reviewed_case_count")),
        "sanitized_review_result_row_count": _int_value_or_zero(ex17.get("ex16_sanitized_review_result_row_count")),
        "rating_row_count": _int_value_or_zero(ex17.get("ex16_rating_row_count")),
        "question_need_observation_row_count": _int_value_or_zero(ex17.get("ex16_question_need_observation_row_count")),
    }
    not_claimed_boundary = {key: False for key in P7_R54_AHR_POST_CR22_EX18_NOT_CLAIMED_BOUNDARY_REFS}
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_CR22_STEP,
        "scope": P7_R54_AHR_POST_CR22_SCOPE,
        "policy_kind": P7_R54_AHR_POST_CR22_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_CR22_EX18_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_CR22_EX18_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_postcr22_ex18_validation_command_matrix_result_memo_next_decision_hold_bodyfree",
        "review_session_id": clean_identifier(review_session_id or ex17.get("review_session_id"), default=P7_R54_AHR_POST_CR22_DEFAULT_REVIEW_SESSION_ID, max_length=180),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ex17_schema_version": ex17.get("schema_version"),
        "ex17_material_ref": ex17.get("material_id"),
        "ex17_next_required_step": ex17.get("next_required_step"),
        "ex17_candidate_only_separation_status_ref": ex17.get("candidate_only_separation_status_ref"),
        "ex17_candidate_only_separation_ready": bool(ex17.get("candidate_only_separation_ready")),
        "ex17_actual_review_evidence_complete": bool(ex17.get("actual_review_evidence_complete")),
        "ex17_selected_decision_refs": list(ex17.get("selected_decision_refs") or []),
        "ex17_selected_decision_ref_count": len(ex17.get("selected_decision_refs") or []),
        "ex17_p5_confirmed_candidate_bodyfree_only": bool(ex17.get("p5_confirmed_candidate_bodyfree_only")),
        "ex17_p6_limited_human_readfeel_candidate_only": bool(ex17.get("p6_limited_human_readfeel_candidate_only")),
        "ex17_p8_question_need_observation_material_candidate_only": bool(ex17.get("p8_question_need_observation_material_candidate_only")),
        "ex17_r52_reintake_handoff_candidate_only": bool(ex17.get("r52_reintake_handoff_candidate_only")),
        "ex17_p5_repair_required_before_r52_reintake": bool(ex17.get("p5_repair_required_before_r52_reintake")),
        "ex17_p4_current_only_repair_required_before_r52_reintake": bool(ex17.get("p4_current_only_repair_required_before_r52_reintake")),
        "ex17_operation_blocked_case_count": _int_value_or_zero(ex17.get("operation_blocked_case_count")),
        "ex17_inconclusive_insufficient_material_case_count": _int_value_or_zero(ex17.get("inconclusive_insufficient_material_case_count")),
        "validation_command_matrix_status_ref": "validation_command_matrix_ready_bodyfree" if validation_ready else "validation_command_matrix_blocked",
        "validation_command_matrix_allowed_status_refs": ["validation_command_matrix_ready_bodyfree", "validation_command_matrix_blocked"],
        "validation_command_matrix_ready": validation_ready,
        "validation_command_matrix_rows": rows,
        "validation_command_matrix_row_count": len(rows),
        "validation_command_matrix_required_command_refs": list(P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS),
        "validation_command_matrix_required_command_ref_count": len(P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS),
        "validation_command_matrix_command_refs": [str(row["command_ref"]) for row in rows],
        "validation_command_matrix_command_ref_count": len(rows),
        "validation_missing_required_command_refs": validation_detail["missing_refs"],
        "validation_missing_required_command_ref_count": len(validation_detail["missing_refs"]),
        "validation_duplicate_command_refs": validation_detail["duplicate_refs"],
        "validation_duplicate_command_ref_count": len(validation_detail["duplicate_refs"]),
        "validation_nonpassed_required_command_refs": validation_detail["nonpassed_required_refs"],
        "validation_nonpassed_required_command_ref_count": len(validation_detail["nonpassed_required_refs"]),
        "validation_forbidden_body_question_path_hash_command_refs": validation_detail["forbidden_row_refs"],
        "validation_forbidden_body_question_path_hash_command_ref_count": len(validation_detail["forbidden_row_refs"]),
        "validation_promotion_claim_command_refs": validation_detail["promotion_claim_refs"],
        "validation_promotion_claim_command_ref_count": len(validation_detail["promotion_claim_refs"]),
        "result_memo_ref": result_memo_ref_text,
        "result_memo_ref_present": result_memo_ref_present,
        "result_memo_required_section_refs": list(P7_R54_AHR_POST_CR22_EX18_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_required_section_ref_count": len(P7_R54_AHR_POST_CR22_EX18_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_sections_bodyfree": True,
        "result_memo_ready": result_memo_ready,
        "implementation_scope": "EX18_validation_command_matrix_result_memo_next_decision_hold_bodyfree_only",
        "changed_files": [
            "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629.py",
            "ai/tests/test_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_ex18_20260630.py",
            P7_R54_AHR_POST_CR22_EX18_DEFAULT_RESULT_MEMO_REF,
        ],
        "changed_file_count": 3,
        "target_tests": {row["command_ref"]: row["command_status_ref"] for row in rows if row["command_ref"] in P7_R54_AHR_POST_CR22_EX18_TARGET_TEST_COMMAND_REFS},
        "target_test_command_refs": list(P7_R54_AHR_POST_CR22_EX18_TARGET_TEST_COMMAND_REFS),
        "target_test_command_ref_count": len(P7_R54_AHR_POST_CR22_EX18_TARGET_TEST_COMMAND_REFS),
        "selected_regression": {row["command_ref"]: row["command_status_ref"] for row in rows if row["command_ref"] in P7_R54_AHR_POST_CR22_EX18_SELECTED_REGRESSION_COMMAND_REFS},
        "selected_regression_command_refs": list(P7_R54_AHR_POST_CR22_EX18_SELECTED_REGRESSION_COMMAND_REFS),
        "selected_regression_command_ref_count": len(P7_R54_AHR_POST_CR22_EX18_SELECTED_REGRESSION_COMMAND_REFS),
        "compileall": {row["command_ref"]: row["command_status_ref"] for row in rows if row["command_ref"] in P7_R54_AHR_POST_CR22_EX18_COMPILEALL_COMMAND_REFS},
        "compileall_command_refs": list(P7_R54_AHR_POST_CR22_EX18_COMPILEALL_COMMAND_REFS),
        "compileall_command_ref_count": len(P7_R54_AHR_POST_CR22_EX18_COMPILEALL_COMMAND_REFS),
        "actual_human_review_execution_status": "referenced_from_prior_actual_operation_receipt_bodyfree_only" if ready else "not_confirmed_by_ex18",
        "actual_source_guard_status": "passed_from_prior_actual_source_guard_bodyfree" if actual_source_guard_passed else "not_passed_or_not_confirmed",
        "row_counts": row_counts,
        "disposal_status": {
            "disposal_verified": disposal_verified,
            "actual_disposal_receipt_materialized_here": actual_disposal_receipt_materialized,
        },
        "no_leak_validation_status": {
            "no_body_leak_validation_passed": bool(ready),
            "no_question_text_validation_passed": bool(ready),
            "no_touch_validation_passed": bool(ready),
            "no_local_path_or_hash_validation_passed": bool(ready),
        },
        "candidate_only_decisions": list(ex17.get("selected_decision_refs") or []) if ready else [],
        "candidate_only_decision_count": len(ex17.get("selected_decision_refs") or []) if ready else 0,
        "not_claimed_boundary": not_claimed_boundary,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_CR22_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_CR22_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "next_decision_hold_required": True,
        "next_decision_hold_status_ref": P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF,
        "next_decision_option_refs": list(P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_OPTION_REFS),
        "next_decision_option_ref_count": len(P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_OPTION_REFS),
        "next_decision_auto_execution_allowed": False,
        "ex18_status_ref": status_ref,
        "ex18_allowed_status_refs": list(P7_R54_AHR_POST_CR22_EX18_ALLOWED_STATUS_REFS),
        "ex18_ready": ready,
        "ex18_reason_refs": [P7_R54_AHR_POST_CR22_EX18_READY_REASON_REF] if ready else [],
        "ex18_blocker_refs": blocker_refs,
        "ex18_blocker_ref_count": len(blocker_refs),
        "actual_source_guard_passed": actual_source_guard_passed,
        "actual_human_review_executed_by_person": actual_human_review_executed_by_person,
        "actual_rating_rows_materialized_here": actual_rating_rows_materialized,
        "actual_question_need_observation_rows_materialized_here": actual_question_need_rows_materialized,
        "actual_disposal_receipt_materialized_here": actual_disposal_receipt_materialized,
        "disposal_verified": disposal_verified,
        "actual_review_evidence_complete": actual_review_evidence_complete,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "full_backend_suite_green": False,
        "rn_contract_green": False,
        "rn_real_device_modal_verified": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS,
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_CR22_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_cr_basis": False,
        "current_cr_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_CR22_CLAIM_BOUNDARY_REFS),
        "implemented_steps": P7_R54_AHR_POST_CR22_EX18_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX17_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_CR22_EX18_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_CR22_EX17_NOT_YET_IMPLEMENTED_STEPS,
        "next_required_step": P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF if ready else P7_R54_AHR_POST_CR22_EX18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "postcr22_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    ex18_allowed_true_values = {
        "actual_rating_rows_materialized_here": actual_rating_rows_materialized,
        "actual_question_need_observation_rows_materialized_here": actual_question_need_rows_materialized,
        "actual_disposal_receipt_materialized_here": actual_disposal_receipt_materialized,
        "disposal_verified": disposal_verified,
        "actual_review_evidence_complete": actual_review_evidence_complete,
    }
    for key in P7_R54_AHR_POST_CR22_EX18_ALLOWED_TRUE_FALSE_FLAG_REFS:
        material[key] = bool(ex18_allowed_true_values.get(key)) if ready else False
    assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(material)
    return material


def assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_CR22_EX18_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostCR22-EX18")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_CR22_EX18_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_NEXT_DECISION_HOLD_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_CR22_EX18_STEP_REF,
        source="P7-R54-AHR-PostCR22-EX18",
        allowed_true_flag_refs=P7_R54_AHR_POST_CR22_EX18_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    _assert_current_basis_and_claim_boundary(data, source="P7-R54-AHR-PostCR22-EX18")
    if tuple(data.get("ex18_allowed_status_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 allowed status refs changed")
    if tuple(data.get("validation_command_matrix_required_command_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 required validation command refs changed")
    if data.get("validation_command_matrix_required_command_ref_count") != len(P7_R54_AHR_POST_CR22_EX18_REQUIRED_VALIDATION_COMMAND_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX18 required validation command count changed")
    rows = list(data.get("validation_command_matrix_rows") or [])
    if data.get("validation_command_matrix_row_count") != len(rows):
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation row count changed")
    for row in rows:
        assert_p7_r54_ahr_post_cr22_ex18_validation_command_row_contract(row)
    command_refs = list(data.get("validation_command_matrix_command_refs") or [])
    if data.get("validation_command_matrix_command_ref_count") != len(command_refs):
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation command ref count changed")
    for refs_key, count_key in (
        ("validation_missing_required_command_refs", "validation_missing_required_command_ref_count"),
        ("validation_duplicate_command_refs", "validation_duplicate_command_ref_count"),
        ("validation_nonpassed_required_command_refs", "validation_nonpassed_required_command_ref_count"),
        ("validation_forbidden_body_question_path_hash_command_refs", "validation_forbidden_body_question_path_hash_command_ref_count"),
        ("validation_promotion_claim_command_refs", "validation_promotion_claim_command_ref_count"),
        ("ex18_blocker_refs", "ex18_blocker_ref_count"),
        ("target_test_command_refs", "target_test_command_ref_count"),
        ("selected_regression_command_refs", "selected_regression_command_ref_count"),
        ("compileall_command_refs", "compileall_command_ref_count"),
        ("candidate_only_decisions", "candidate_only_decision_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("next_decision_option_refs", "next_decision_option_ref_count"),
    ):
        if data.get(count_key) != len(data.get(refs_key) or []):
            raise ValueError(f"P7-R54-AHR-PostCR22-EX18 {count_key} changed")
    if tuple(data.get("result_memo_required_section_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_RESULT_MEMO_REQUIRED_SECTION_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 result memo required sections changed")
    if data.get("result_memo_required_section_ref_count") != len(P7_R54_AHR_POST_CR22_EX18_RESULT_MEMO_REQUIRED_SECTION_REFS):
        raise ValueError("P7-R54-AHR-PostCR22-EX18 result memo required section count changed")
    if data.get("result_memo_sections_bodyfree") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 result memo sections must be body-free")
    if tuple(data.get("target_test_command_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_TARGET_TEST_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 target command refs changed")
    if tuple(data.get("selected_regression_command_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_SELECTED_REGRESSION_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 selected regression command refs changed")
    if tuple(data.get("compileall_command_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_COMPILEALL_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 compileall command refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostCR22-EX18 not-claimed boundary must stay false")
    if tuple(data.get("next_decision_option_refs") or ()) != P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_OPTION_REFS:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 next decision options changed")
    if data.get("next_decision_hold_required") is not True:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 next decision hold must be required")
    if data.get("next_decision_hold_status_ref") != P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 next decision hold ref changed")
    if data.get("next_decision_auto_execution_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 must not allow auto next-decision execution")
    _postcr22_assert_required_false_flags_except(
        data,
        source="P7-R54-AHR-PostCR22-EX18",
        allowed_true_refs=P7_R54_AHR_POST_CR22_EX18_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green",
        "rn_contract_green",
        "rn_real_device_modal_verified",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX18 required false field changed: {key}")
    for key in (
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostCR22-EX18 required true boundary changed: {key}")
    ready = data.get("ex18_status_ref") == P7_R54_AHR_POST_CR22_EX18_READY_STATUS_REF
    if data.get("ex18_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostCR22-EX18 ready flag changed")
    if data.get("validation_command_matrix_ready") is not (not data.get("validation_nonpassed_required_command_refs") and not data.get("validation_missing_required_command_refs") and not data.get("validation_duplicate_command_refs") and not data.get("validation_forbidden_body_question_path_hash_command_refs") and not data.get("validation_promotion_claim_command_refs")):
        raise ValueError("P7-R54-AHR-PostCR22-EX18 validation matrix ready flag changed")
    if ready:
        if data.get("ex18_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 ready material cannot carry blockers")
        if data.get("ex18_reason_refs") != [P7_R54_AHR_POST_CR22_EX18_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 ready reason changed")
        if data.get("result_memo_ready") is not True:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 ready material requires result memo ready")
        for key in (
            "actual_source_guard_passed",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "actual_review_evidence_complete",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostCR22-EX18 ready material missing true field: {key}")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX18_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 ready next required step must hold")
    else:
        if data.get("ex18_status_ref") != P7_R54_AHR_POST_CR22_EX18_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 blocked status changed")
        if not data.get("ex18_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostCR22-EX18 blocked material must carry blockers")
        if data.get("ex18_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 blocked material cannot carry ready reasons")
        if data.get("actual_review_evidence_complete") is not False:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 blocked material cannot claim evidence complete")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_CR22_EX17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_CR22_EX18_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostCR22-EX18 blocked next required step changed")
    return True


# Alias names for the detailed-design wording of EX16 through EX18.
def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_review_evidence_complete_predicate_bodyfree(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    final_no_body_leak_no_question_text_no_touch_validation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate(
        actual_operation_receipt_intake=actual_operation_receipt_intake,
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        question_need_observation_normalization=question_need_observation_normalization,
        rating_question_consistency_guard=rating_question_consistency_guard,
        final_no_body_leak_no_question_text_no_touch_validation=final_no_body_leak_no_question_text_no_touch_validation,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_actual_review_evidence_complete_predicate_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex16_actual_review_evidence_complete_predicate_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_p5_p6_p8_r52_candidate_only_separation_bodyfree(
    *,
    actual_review_evidence_complete_predicate: Mapping[str, Any] | None = None,
    readfeel_execution_p5_p4_blocker_classification: Mapping[str, Any] | None = None,
    question_need_observation_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex17_p5_p6_p8_r52_candidate_only_separation(
        actual_review_evidence_complete_predicate=actual_review_evidence_complete_predicate,
        readfeel_execution_p5_p4_blocker_classification=readfeel_execution_p5_p4_blocker_classification,
        question_need_observation_normalization=question_need_observation_normalization,
        rating_question_consistency_guard=rating_question_consistency_guard,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_p5_p6_p8_r52_candidate_only_separation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex17_p5_p6_p8_r52_candidate_only_separation_contract(data)


def build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_validation_command_matrix_result_memo_next_decision_hold_bodyfree(
    *,
    candidate_only_separation: Mapping[str, Any] | None = None,
    validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    result_memo_ref: Any = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold(
        candidate_only_separation=candidate_only_separation,
        validation_command_rows=validation_command_rows,
        result_memo_ref=result_memo_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_validation_command_matrix_result_memo_next_decision_hold_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_cr22_ex18_validation_command_matrix_result_memo_next_decision_hold_contract(data)

