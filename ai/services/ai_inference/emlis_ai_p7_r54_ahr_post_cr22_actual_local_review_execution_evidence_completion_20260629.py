# -*- coding: utf-8 -*-
"""Post-CR22 R54-AHR actual local-only review evidence completion helper.

EX00-EX03 intentionally create only a body-free Post-CR22 envelope:

* EX00 freezes the scope, no-touch, and non-promotion boundary for the
  Post-CR22 Actual Local-only Human Review Execution Evidence Completion line.
* EX01 intakes CR22 as support material and confirms that the current CR
  actual-review basis remains ``current_received_snapshot_264_85_258_171``.
* EX02 freezes the review session envelope and actual-source guard, so helper
  defaults / unit tests / synthetic rows cannot become actual review evidence.
* EX03 freezes local-only preflight, explicit allow, and packet request boundary
  as body-free refs only; it does not generate any body-full packet.

This module does not execute actual local human review, does not generate or
export body-full packets, does not create actual selection/rating/question rows,
does not create disposal receipts, does not start P8/R52/P6, does not finalize
P5, does not complete P7, and does not allow release.
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
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str
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
    for key in P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
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
