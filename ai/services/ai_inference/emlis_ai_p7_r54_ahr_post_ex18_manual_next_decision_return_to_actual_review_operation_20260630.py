# -*- coding: utf-8 -*-
"""Post-EX18 R54-AHR manual next-decision helpers for MN00-MN11.

MN00-MN11 intentionally add only a thin, body-free Post-EX18 decision layer:

* MN00 freezes the scope, no-touch boundary, and no-promotion boundary for the
  Post-EX18 manual next-decision line.
* MN01 intakes an EX18 result memo / body-free envelope and confirms that EX18's
  manual next-decision hold is the only admissible starting point.
* MN02 normalizes whether actual review evidence is missing, incomplete,
  invalid, or complete-by-actual-person-review without running review here.
* MN03 classifies the manual next decision without auto-executing P5/P6/P8/R52,
  without completing P7, and without allowing release.
* MN04 builds the body-free return-to-actual-review operation plan only when
  MN03 has classified the current state as return-operation required.
* MN05 defines the expected body-free evidence intake bundle boundary for a
  future actual local-only human review without creating that bundle here.
* MN06 scans body-free decision / plan / bundle materials by key path and
  fail-closes on body, question, path, hash, or terminal-output keys.
* MN07 materializes the downstream no-promotion boundary without starting
  P5/P6/P8/R52, completing P7, or allowing release.
* MN08 maps a future body-free actual review evidence bundle back to existing
  Post-CR22 EX07-EX18 without reimplementing those steps or claiming execution.
* MN09 defines a body-free validation command matrix / result memo envelope
  without treating validation green as actual review completion.
* MN10 materializes the alias / contract function boundary without renaming
  existing Post-CR22 helpers or executing downstream decisions.
* MN11 finalizes acceptance / fail-closed state for the Post-EX18 manual
  decision, keeping the next step at actual local-only human review operation.

This module does not generate body-full packets, does not run actual local human
review, does not create actual review rows, does not create question text, does
not start P8/P6/R52, does not finalize P5, does not complete P7, and does not
allow release.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import P7_PHASE, P7_SOURCE_MODE, clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


P7_R54_AHR_POST_EX18_MN00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn00_scope_no_touch_no_promotion_boundary_freeze.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN01_EX18_RESULT_MEMO_BODYFREE_ENVELOPE_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn01_ex18_result_memo_bodyfree_envelope_intake.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN02_ACTUAL_REVIEW_EVIDENCE_STATE_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn02_actual_review_evidence_state_normalization.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_CLASSIFIER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn03_manual_decision_classifier.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN04_RETURN_TO_ACTUAL_REVIEW_OPERATION_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn04_return_to_actual_review_operation_plan.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN05_EXPECTED_BODYFREE_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn05_expected_bodyfree_evidence_intake_bundle_boundary.bodyfree.v1"
)

P7_R54_AHR_POST_EX18_STEP: Final = (
    "R54-AHR-PostEX18_ManualNextDecision_ReturnToActualReviewOperation_20260630"
)
P7_R54_AHR_POST_EX18_SCOPE: Final = (
    "p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation"
)
P7_R54_AHR_POST_EX18_POLICY_KIND: Final = (
    "r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_boundary"
)
P7_R54_AHR_POST_EX18_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postex18_manual_next_decision_session_20260630_"
    "current_received_264_85_258_171_v1"
)

P7_R54_AHR_POST_EX18_MN00_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN00_scope_no_touch_no_promotion_boundary_freeze"
)
P7_R54_AHR_POST_EX18_MN01_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN01_ex18_result_memo_bodyfree_envelope_intake"
)
P7_R54_AHR_POST_EX18_MN02_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN02_actual_review_evidence_state_normalization"
)
P7_R54_AHR_POST_EX18_MN03_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN03_manual_decision_classifier"
)
P7_R54_AHR_POST_EX18_MN04_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN04_return_to_actual_review_operation_plan_builder"
)
P7_R54_AHR_POST_EX18_MN05_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN05_expected_bodyfree_evidence_intake_bundle_boundary"
)
P7_R54_AHR_POST_EX18_MN06_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN06_no_body_no_question_no_path_no_hash_scan"
)
P7_R54_AHR_POST_EX18_MN07_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN07_downstream_no_promotion_boundary_materialization"
)
P7_R54_AHR_POST_EX18_MN08_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN08_reentry_mapping_to_existing_postcr22_ex07_ex18"
)
P7_R54_AHR_POST_EX18_MN09_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN09_validation_command_matrix_result_memo_envelope"
)
P7_R54_AHR_POST_EX18_MN10_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN10_alias_contract_function_boundary"
)
P7_R54_AHR_POST_EX18_MN11_STEP_REF: Final = (
    "R54-AHR-PostEX18-MN11_acceptance_fail_closed_finalizer"
)
P7_R54_AHR_POST_EX18_MN01_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn01_ex18_result_memo_bodyfree_envelope_or_stop"
)
P7_R54_AHR_POST_EX18_MN02_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn02_actual_review_evidence_state_normalization_or_stop"
)
P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF: Final = (
    "actual_local_only_human_review_operation_required_before_p5_p6_p8_r52_decision"
)
P7_R54_AHR_POST_EX18_MN03_HOLD_EX18_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_ex18_result_memo_or_stop"
)
P7_R54_AHR_POST_EX18_MN03_STOP_BODY_LEAK_NEXT_REQUIRED_STEP_REF: Final = (
    "stop_body_leak_or_question_text_detected"
)
P7_R54_AHR_POST_EX18_MN03_STOP_PROMOTION_NEXT_REQUIRED_STEP_REF: Final = (
    "stop_promotion_claim_detected"
)
P7_R54_AHR_POST_EX18_MN03_DOWNSTREAM_MANUAL_NEXT_REQUIRED_STEP_REF: Final = (
    "downstream_manual_decision_required_without_auto_execution"
)
P7_R54_AHR_POST_EX18_MN04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn04_return_to_actual_review_operation_plan_or_stop"
)
P7_R54_AHR_POST_EX18_MN05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn05_expected_bodyfree_evidence_intake_bundle_boundary_or_stop"
)

P7_R54_AHR_POST_EX18_MN_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN00_STEP_REF,
    P7_R54_AHR_POST_EX18_MN01_STEP_REF,
    P7_R54_AHR_POST_EX18_MN02_STEP_REF,
    P7_R54_AHR_POST_EX18_MN03_STEP_REF,
    P7_R54_AHR_POST_EX18_MN04_STEP_REF,
    P7_R54_AHR_POST_EX18_MN05_STEP_REF,
    P7_R54_AHR_POST_EX18_MN06_STEP_REF,
    P7_R54_AHR_POST_EX18_MN07_STEP_REF,
    P7_R54_AHR_POST_EX18_MN08_STEP_REF,
    P7_R54_AHR_POST_EX18_MN09_STEP_REF,
    P7_R54_AHR_POST_EX18_MN10_STEP_REF,
    P7_R54_AHR_POST_EX18_MN11_STEP_REF,
)
P7_R54_AHR_POST_EX18_MN00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN00_STEP_REF,
)
P7_R54_AHR_POST_EX18_MN00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[1:]
P7_R54_AHR_POST_EX18_MN01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:2]
P7_R54_AHR_POST_EX18_MN01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[2:]
P7_R54_AHR_POST_EX18_MN02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:3]
P7_R54_AHR_POST_EX18_MN02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[3:]
P7_R54_AHR_POST_EX18_MN03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:4]
P7_R54_AHR_POST_EX18_MN03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[4:]
P7_R54_AHR_POST_EX18_MN04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:5]
P7_R54_AHR_POST_EX18_MN04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[5:]
P7_R54_AHR_POST_EX18_MN05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:6]
P7_R54_AHR_POST_EX18_MN05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[6:]

P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF: Final = ex.P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_REF
P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = (
    ex.P7_R54_AHR_POST_CR22_ACTUAL_REVIEW_BASIS_ALLOWED_REF
)
P7_R54_AHR_POST_EX18_PRE_DESIGN_MEMO_REF: Final = (
    "Cocolon_EmlisAI_P7_R54AHR_PostEX18_ManualNextDecision_PreDesignMemo_20260630.md"
)
P7_R54_AHR_POST_EX18_DETAILED_DESIGN_REF: Final = (
    "Cocolon_EmlisAI_P7_R54AHR_PostEX18_ReturnToActualReviewOperation_"
    "DetailedDesign_ImplementationOrder_20260630.md"
)
P7_R54_AHR_POST_EX18_EX18_RESULT_MEMO_REF: Final = ex.P7_R54_AHR_POST_CR22_EX18_DEFAULT_RESULT_MEMO_REF
P7_R54_AHR_POST_EX18_EX_HELPER_REF: Final = (
    "ai/services/ai_inference/"
    "emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629.py"
)

P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(269).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(87).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(6).zip",
    "rn_zip_ref": "Cocolon(260).zip",
    "backend_zip_ref": "mashos-api(173).zip",
}
P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS: Final[dict[str, str]] = {
    "pre_design_memo_ref": P7_R54_AHR_POST_EX18_PRE_DESIGN_MEMO_REF,
    "detailed_design_ref": P7_R54_AHR_POST_EX18_DETAILED_DESIGN_REF,
    "ex18_result_memo_ref": P7_R54_AHR_POST_EX18_EX18_RESULT_MEMO_REF,
    "postcr22_ex_helper_ref": P7_R54_AHR_POST_EX18_EX_HELPER_REF,
}
P7_R54_AHR_POST_EX18_EX18_RECORDED_VALIDATION_RESULTS: Final[dict[str, str]] = {
    "ex18_target_result_ref": "17_passed",
    "ex00_ex18_combined_result_ref": "361_passed",
    "cr22_regression_result_ref": "22_passed",
    "cr00_cr22_combined_result_ref": "837_passed",
    "cs00_cs18_selected_regression_result_ref": "450_passed",
    "cs00_cs01_ahr00_ahr01_selected_smoke_result_ref": "102_passed",
    "compileall_result_ref": "passed",
}

P7_R54_AHR_POST_EX18_MN01_READY_STATUS_REF: Final = (
    "MN01_EX18_RESULT_MEMO_BODYFREE_ENVELOPE_ACCEPTED_MANUAL_HOLD_CONFIRMED"
)
P7_R54_AHR_POST_EX18_MN01_BLOCKED_STATUS_REF: Final = (
    "MN01_EX18_RESULT_MEMO_BODYFREE_ENVELOPE_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN01_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN01_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN01_RETURN_OPERATION_CANDIDATE_REF: Final = (
    "RETURN_TO_ACTUAL_REVIEW_OPERATION_REQUIRED_CANDIDATE_ONLY_BEFORE_MN03_CLASSIFIER"
)

P7_R54_AHR_POST_EX18_MN02_READY_STATUS_REF: Final = (
    "MN02_ACTUAL_REVIEW_EVIDENCE_STATE_NORMALIZED_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN02_BLOCKED_STATUS_REF: Final = (
    "MN02_ACTUAL_REVIEW_EVIDENCE_STATE_NORMALIZATION_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN02_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN02_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_ACTUAL_PERSON_LOCAL_ONLY_REVIEW_SOURCE_REF: Final = (
    "actual_person_local_only_review"
)
P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_MISSING_REAL_REVIEW_REQUIRED_REF: Final = (
    "actual_review_evidence_missing_real_review_required"
)
P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INCOMPLETE_BODYFREE_REF: Final = (
    "actual_review_evidence_incomplete_bodyfree"
)
P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BY_ACTUAL_PERSON_REVIEW_BODYFREE_REF: Final = (
    "actual_review_evidence_complete_by_actual_person_review_bodyfree"
)
P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INVALID_SOURCE_DETECTED_REF: Final = (
    "actual_review_evidence_invalid_source_detected"
)
P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_MISSING_REAL_REVIEW_REQUIRED_REF,
    P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INCOMPLETE_BODYFREE_REF,
    P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BY_ACTUAL_PERSON_REVIEW_BODYFREE_REF,
    P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INVALID_SOURCE_DETECTED_REF,
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF: Final = (
    "RETURN_TO_ACTUAL_REVIEW_OPERATION_REQUIRED"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_HOLD_EX18_INVALID_REF: Final = (
    "HOLD_EX18_NOT_READY_OR_INVALID"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_BODY_LEAK_REF: Final = (
    "STOP_FOR_BODY_LEAK_OR_QUESTION_TEXT"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_PROMOTION_CLAIM_REF: Final = (
    "STOP_FOR_PROMOTION_CLAIM"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF: Final = (
    "EVIDENCE_COMPLETE_BUT_DOWNSTREAM_MANUAL_DECISION_REQUIRED"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF,
    P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_HOLD_EX18_INVALID_REF,
    P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_BODY_LEAK_REF,
    P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_PROMOTION_CLAIM_REF,
    P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF,
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_READY_STATUS_REF: Final = (
    "manual_decision_ready_bodyfree"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_BLOCKED_STATUS_REF: Final = (
    "manual_decision_blocked_bodyfree"
)
P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN04_READY_STATUS_REF: Final = (
    "MN04_RETURN_TO_ACTUAL_REVIEW_OPERATION_PLAN_READY_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN04_BLOCKED_STATUS_REF: Final = (
    "MN04_RETURN_TO_ACTUAL_REVIEW_OPERATION_PLAN_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN04_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN04_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN05_READY_STATUS_REF: Final = (
    "MN05_EXPECTED_BODYFREE_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_READY"
)
P7_R54_AHR_POST_EX18_MN05_BLOCKED_STATUS_REF: Final = (
    "MN05_EXPECTED_BODYFREE_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN05_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN05_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_OPERATION_PLAN_REF: Final = (
    "post_ex18_return_to_actual_review_operation_plan_bodyfree_current_received_264_85_258_171"
)
P7_R54_AHR_POST_EX18_EXPECTED_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_REF: Final = (
    "post_ex18_expected_actual_review_evidence_intake_bundle_boundary_bodyfree_v1"
)
P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT: Final = 24
P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS: Final[tuple[str, ...]] = (
    "actual_operation_receipt_ref",
    "sanitized_review_result_rows_ref",
    "rating_rows_ref",
    "question_need_observation_rows_ref",
    "disposal_receipt_ref",
    "no_leak_validation_ref",
    "actual_review_evidence_complete_predicate_ref",
)
P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "returned_body",
    "comment_text_body",
    "history_body",
    "reviewer_notes_body",
    "question_text",
    "draft_question_text",
    "local_absolute_path",
    "body_hash",
    "terminal_output_body",
)
P7_R54_AHR_POST_EX18_MN04_OPERATION_PLAN_ACTION_REFS: Final[tuple[str, ...]] = (
    "confirm_local_only_boundary_before_body_full_packet",
    "confirm_explicit_allow_before_real_review",
    "prepare_purge_plan_before_real_review",
    "human_reviewer_reads_24_cases_selection_only",
    "keep_body_full_packet_out_of_artifacts",
    "return_bodyfree_receipts_rows_disposal_to_existing_postcr22_ex07_ex18_after_real_review",
)
P7_R54_AHR_POST_EX18_MN05_EXPECTED_BUNDLE_COMPONENT_REFS: Final[tuple[str, ...]] = (
    "actual_operation_receipt",
    "sanitized_review_result_rows",
    "rating_rows",
    "question_need_observation_rows",
    "disposal_receipt",
    "no_leak_validation",
)

P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "actual_review_evidence_complete_from_real_review",
    "actual_selection_rows_created_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "manual_decision_classifier_run_here",
    "manual_decision_auto_executes_downstream",
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
    "full_backend_suite_green",
    "full_backend_suite_green_confirmed",
    "rn_contract_green",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_EX18_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "input_body",
        "raw_body",
        "current_input_body",
        "returned_emlis_body",
        "emlis_body",
        "history_body",
        "history_surface",
        "comment_text",
        "comment_text_body",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "question_body",
        "answer_body",
        "packet_content",
        "body_full_packet_content",
        "local_path",
        "absolute_path",
        "file_path",
        "local_absolute_path",
        "body_hash",
        "content_hash_of_body",
        "terminal_output",
        "terminal_output_body",
        "stdout",
        "stderr",
        "traceback",
    }
)
P7_R54_AHR_POST_EX18_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "input_body_included",
    "returned_emlis_body_included",
    "history_body_included",
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
P7_R54_AHR_POST_EX18_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "ex18_green_is_not_actual_human_review_complete",
    "ex18_result_memo_is_not_actual_review_receipt",
    "ex18_next_decision_hold_is_not_p7_complete",
    "unit_test_rows_are_not_actual_review_rows",
    "helper_default_rows_are_not_actual_review_rows",
    "synthetic_contract_rows_are_not_actual_review_rows",
    "outer_received_269_87_260_173_zip_labels_are_not_current_actual_review_basis_rewrite",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "r52_handoff_candidate_is_not_r52_actual_execution",
    "p5_confirmed_candidate_is_not_p5_final",
    "selected_regression_green_is_not_full_backend_suite_green",
    "rn_contract_green_is_not_rn_real_device_modal_verified",
)
P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_complete",
    "p5_final",
    "p6_start",
    "p8_start",
    "r52_actual_execution",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
)

P7_R54_AHR_POST_EX18_MN00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "post_ex18_manual_next_decision_scope_confirmed",
    "return_to_actual_review_operation_design_scope",
    "no_touch_boundary_confirmed",
    "no_promotion_boundary_confirmed",
    "mn00_does_not_intake_ex18_result_memo",
    "mn00_does_not_normalize_actual_review_evidence_state",
    "mn00_does_not_run_manual_decision_classifier",
    "mn00_does_not_generate_body_full_packet",
    "mn00_does_not_run_actual_human_review",
    "mn00_does_not_create_review_rows_rating_rows_question_rows_or_disposal",
    "p8_question_design_out_of_scope",
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
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "support_material_refs",
    "support_material_ref_count",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_ex18_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_EX18_MN01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "mn00_schema_version",
    "mn00_material_ref",
    "mn00_next_required_step",
    "mn00_scope_confirmed",
    "mn00_no_touch_boundary_confirmed",
    "mn00_no_promotion_boundary_confirmed",
    "mn01_status_ref",
    "mn01_allowed_status_refs",
    "mn01_ready",
    "mn01_blocker_refs",
    "mn01_blocker_ref_count",
    "mn01_reason_refs",
    "mn01_reason_ref_count",
    "support_material_refs",
    "support_material_ref_count",
    "ex18_result_memo_ref",
    "ex18_result_memo_ref_present",
    "ex18_bodyfree_envelope_present",
    "ex18_envelope_schema_version",
    "ex18_envelope_operation_step_ref",
    "ex18_envelope_body_free",
    "ex18_next_required_step",
    "ex18_next_decision_hold_required",
    "ex18_next_decision_auto_execution_allowed",
    "ex18_result_memo_ready_reported",
    "ex18_validation_command_matrix_ready_reported",
    "ex18_actual_review_evidence_complete_reported_by_contract",
    "ex18_actual_human_review_run_here_reported",
    "ex18_actual_human_review_newly_run_here_reported",
    "ex18_actual_human_review_complete_reported",
    "ex18_actual_selection_rows_created_here_reported",
    "ex18_actual_rating_rows_materialized_here_reported",
    "ex18_actual_question_need_observation_rows_materialized_here_reported",
    "ex18_actual_disposal_receipt_materialized_here_reported",
    "ex18_disposal_verified_reported",
    "ex18_row_counts_bodyfree",
    "ex18_candidate_only_decisions_bodyfree",
    "ex18_candidate_only_decision_count_bodyfree",
    "ex18_not_claimed_boundary_refs",
    "ex18_not_claimed_boundary_ref_count",
    "ex18_not_claimed_boundary",
    "ex18_forbidden_payload_key_paths",
    "ex18_forbidden_payload_key_path_count",
    "ex18_promotion_claim_refs",
    "ex18_promotion_claim_ref_count",
    "ex18_recorded_validation_results",
    "ex18_green_is_not_actual_review_complete",
    "ex18_result_memo_is_not_actual_review_receipt",
    "mn01_does_not_treat_ex18_contract_green_as_real_review_complete",
    "mn01_does_not_normalize_actual_review_evidence_state",
    "mn01_does_not_run_manual_decision_classifier",
    "mn01_return_to_actual_review_operation_candidate_ref",
    "mn01_return_to_actual_review_operation_candidate_only",
    "mn01_passes_to_actual_review_evidence_state_normalization",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "basis_rewrite_required_here",
    "basis_rewritten_here",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    "outer_received_zip_label_difference_recorded_bodyfree",
    "current_actual_review_basis_remains_264_85_258_171",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_ex18_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


P7_R54_AHR_POST_EX18_MN02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "mn01_schema_version",
    "mn01_material_ref",
    "mn01_status_ref",
    "mn01_ready",
    "mn01_next_required_step",
    "mn01_return_to_actual_review_operation_candidate_ref",
    "mn01_return_to_actual_review_operation_candidate_only",
    "mn02_status_ref",
    "mn02_allowed_status_refs",
    "mn02_ready",
    "mn02_blocker_refs",
    "mn02_blocker_ref_count",
    "mn02_reason_refs",
    "mn02_reason_ref_count",
    "actual_review_evidence_status_ref",
    "actual_review_evidence_status_allowed_refs",
    "actual_review_evidence_status_reason_refs",
    "actual_review_evidence_status_reason_ref_count",
    "actual_review_evidence_intake_bundle_present",
    "actual_review_evidence_intake_bundle_body_free",
    "actual_review_evidence_intake_bundle_source_ref",
    "actual_review_evidence_intake_bundle_forbidden_payload_key_paths",
    "actual_review_evidence_intake_bundle_forbidden_payload_key_path_count",
    "actual_review_evidence_intake_bundle_promotion_claim_refs",
    "actual_review_evidence_intake_bundle_promotion_claim_ref_count",
    "actual_review_evidence_intake_bundle_invalid_source_refs",
    "actual_review_evidence_intake_bundle_invalid_source_ref_count",
    "actual_review_evidence_intake_bundle_row_counts_bodyfree",
    "actual_source_ref",
    "actual_source_guard_passed",
    "actual_source_is_actual_person_local_only_review",
    "actual_human_review_executed_by_person",
    "reviewer_local_only_read_receipt_present",
    "reviewed_case_count",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "question_need_observation_row_count",
    "required_case_count",
    "all_required_counts_are_24",
    "disposal_receipt_present",
    "disposal_verified_bodyfree",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_path_hash_validation_passed",
    "row_created_by_helper",
    "row_created_for_unit_test",
    "row_is_synthetic_contract_fixture",
    "historical_row_reused",
    "unit_test_rows_used_as_actual_evidence",
    "helper_default_rows_used_as_actual_evidence",
    "synthetic_rows_used_as_actual_evidence",
    "historical_rows_used_as_actual_evidence",
    "ex18_contract_green_promoted_to_actual_complete",
    "actual_review_evidence_complete_by_actual_person_review_bodyfree",
    "actual_review_evidence_complete_from_real_review_normalized",
    "actual_review_evidence_complete_from_ex18_contract_report",
    "mn02_does_not_run_actual_human_review",
    "mn02_does_not_create_actual_rows",
    "mn02_does_not_generate_body_full_packet",
    "mn02_does_not_run_manual_decision_classifier",
    "mn02_passes_to_manual_decision_classifier",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_ex18_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_EX18_MN03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "mn02_schema_version",
    "mn02_material_ref",
    "mn02_status_ref",
    "mn02_ready",
    "mn02_next_required_step",
    "manual_decision_ref",
    "manual_decision_allowed_refs",
    "manual_decision_status_ref",
    "manual_decision_status_allowed_refs",
    "manual_decision_ready",
    "manual_decision_reason_refs",
    "manual_decision_reason_ref_count",
    "manual_decision_blocker_refs",
    "manual_decision_blocker_ref_count",
    "manual_decision_classifier_run_here",
    "manual_decision_auto_executes_downstream",
    "next_decision_auto_execution_allowed",
    "mn03_classifier_priority_ref",
    "actual_review_evidence_status_ref",
    "actual_review_evidence_status_allowed_refs",
    "actual_review_evidence_complete_by_actual_person_review_bodyfree",
    "actual_review_evidence_complete_from_real_review_normalized",
    "return_to_actual_review_operation_required",
    "downstream_manual_decision_required",
    "no_promotion_boundary_confirmed",
    "blocked_downstream_refs",
    "blocked_downstream_ref_count",
    "p5_p6_p8_r52_release_auto_execution_blocked",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "r52_handoff_candidate_is_not_r52_actual_execution",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_ex18_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)



P7_R54_AHR_POST_EX18_MN04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn03_schema_version", "mn03_material_ref", "mn03_manual_decision_ref",
    "mn03_manual_decision_status_ref", "mn03_manual_decision_ready",
    "mn03_next_required_step", "mn03_return_to_actual_review_operation_required",
    "mn03_actual_review_evidence_status_ref", "mn03_manual_decision_auto_executes_downstream",
    "mn04_status_ref", "mn04_allowed_status_refs", "mn04_ready", "mn04_blocker_refs",
    "mn04_blocker_ref_count", "mn04_reason_refs", "mn04_reason_ref_count",
    "actual_operation_plan_ref", "operation_basis_ref", "required_case_count",
    "reviewed_case_count_required", "sanitized_review_result_row_count_required",
    "rating_row_count_required", "question_need_observation_row_count_required",
    "local_only_required", "explicit_allow_required", "purge_plan_required",
    "human_reviewer_required", "reviewer_selection_only_required",
    "body_full_packet_local_only_required", "body_full_packet_not_persisted_required",
    "body_free_result_artifacts_required", "required_bodyfree_artifact_refs",
    "required_bodyfree_artifact_ref_count", "forbidden_artifact_refs", "forbidden_artifact_ref_count",
    "operation_plan_bodyfree_action_refs", "operation_plan_bodyfree_action_ref_count",
    "actual_review_operation_not_executed_here", "actual_rows_not_created_by_plan_builder",
    "p8_question_text_not_created_by_plan_builder", "returns_to_existing_postcr22_ex07_ex18_after_actual_review",
    "expected_evidence_intake_bundle_boundary_required",
    "mn04_passes_to_expected_bodyfree_evidence_intake_bundle_boundary",
    "actual_review_basis_refreeze_required_here", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "local_received_zip_refs", "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs", "claim_boundary_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract",
    "post_ex18_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_EX18_MN05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn04_schema_version", "mn04_material_ref", "mn04_status_ref", "mn04_ready",
    "mn04_next_required_step", "mn04_actual_operation_plan_ref", "mn04_required_bodyfree_artifact_refs",
    "mn04_forbidden_artifact_refs", "mn05_status_ref", "mn05_allowed_status_refs", "mn05_ready",
    "mn05_blocker_refs", "mn05_blocker_ref_count", "mn05_reason_refs", "mn05_reason_ref_count",
    "expected_actual_review_evidence_intake_bundle_ref", "expected_bundle_boundary_ref",
    "expected_bundle_template_only", "actual_review_evidence_intake_bundle_materialized_here",
    "expected_actual_source_ref", "required_case_count", "expected_reviewed_case_count",
    "expected_sanitized_review_result_row_count", "expected_rating_row_count",
    "expected_question_need_observation_row_count", "expected_bundle_required_bodyfree_artifact_refs",
    "expected_bundle_required_bodyfree_artifact_ref_count", "expected_bundle_forbidden_artifact_refs",
    "expected_bundle_forbidden_artifact_ref_count", "expected_bundle_component_refs",
    "expected_bundle_component_ref_count", "actual_operation_receipt_expectation",
    "sanitized_review_result_rows_expectation", "rating_rows_expectation",
    "question_need_observation_rows_expectation", "disposal_receipt_expectation",
    "no_body_leak_validation_required", "no_question_text_validation_required", "no_path_hash_validation_required",
    "actual_review_evidence_not_completed_by_boundary", "actual_review_operation_not_run_by_boundary",
    "actual_rows_not_created_by_boundary", "question_text_not_created_by_boundary",
    "bodyfull_packet_not_generated_by_boundary", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "local_received_zip_refs", "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs", "claim_boundary_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract",
    "post_ex18_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_EX18_DEFAULT_REVIEW_SESSION_ID,
        max_length=180,
    )


def _clean_ref(value: Any, *, default: str = "", max_length: int = 220) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_EX18_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_EX18_NO_TOUCH_CONTRACT_REFS}


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS}


def _required_fields_present(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:8]}")
    unexpected = [key for key in data if key not in required]
    if unexpected:
        raise ValueError(f"{source} has unexpected fields: {unexpected[:8]}")


def _dedupe_refs(values: Sequence[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean_ref(value, max_length=220)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _forbidden_payload_key_paths(value: Any, *, path: str = "payload") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_EX18_FORBIDDEN_PAYLOAD_KEY_REFS:
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
        raise ValueError(f"{source} must keep flags false: {true_keys[:8]}")


def _postex18_assert_required_false_flags_except(
    data: Mapping[str, Any], *, source: str, allowed_true_refs: Sequence[str] = ()
) -> None:
    allowed = set(allowed_true_refs)
    for key in P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS:
        if key in allowed:
            continue
        if data.get(key) is not False:
            raise ValueError(f"{source} required false field changed: {key}")


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str,
    allowed_true_false_flag_refs: Sequence[str] = (),
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_EX18_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_EX18_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_EX18_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or claim Git check")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual review basis allowed ref changed")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError(f"{source} zip refs cannot become actual review basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_actual_review_basis") is not False:
        raise ValueError(f"{source} must not rewrite actual review basis from received zip labels")
    for key in ("public_contract", "post_ex18_no_touch_contract", "body_free_markers"):
        if not isinstance(data.get(key), Mapping):
            raise ValueError(f"{source} {key} must be a mapping")
        _assert_all_false(data[key], source=f"{source}.{key}")
    _assert_no_payload_keys(data, source=source)
    _postex18_assert_required_false_flags_except(
        data,
        source=source,
        allowed_true_refs=allowed_true_false_flag_refs,
    )


def _bodyfree_bool(value: Mapping[str, Any], key: str) -> bool:
    return value.get(key) is True


def _safe_string_list(value: Any, *, limit: int = 80, max_length: int = 180) -> list[str]:
    if value is None:
        return []
    source: Sequence[Any]
    if isinstance(value, (str, bytes, bytearray)):
        source = [value]
    elif isinstance(value, Mapping):
        source = list(value.values())
    elif isinstance(value, Sequence):
        source = list(value)
    else:
        source = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in source:
        text = _clean_ref(item, max_length=max_length)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _safe_row_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {
            "reviewed_case_count": 0,
            "sanitized_review_result_row_count": 0,
            "rating_row_count": 0,
            "question_need_observation_row_count": 0,
        }
    out: dict[str, int] = {}
    for key in (
        "reviewed_case_count",
        "sanitized_review_result_row_count",
        "rating_row_count",
        "question_need_observation_row_count",
    ):
        raw = value.get(key, 0)
        out[key] = raw if isinstance(raw, int) and raw >= 0 else 0
    return out


def _ex18_promotion_claim_refs(ex18_envelope: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(ex18_envelope, Mapping):
        return []
    promotion_keys = (
        "next_decision_auto_execution_allowed",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "r52_actual_execution_confirmed",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "rn_contract_green",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
    )
    return [key for key in promotion_keys if ex18_envelope.get(key) is True]


def _ex18_not_claimed_boundary_from_envelope(ex18_envelope: Mapping[str, Any] | None) -> dict[str, bool]:
    if not isinstance(ex18_envelope, Mapping):
        return _not_claimed_boundary()
    boundary = ex18_envelope.get("not_claimed_boundary")
    if not isinstance(boundary, Mapping):
        return _not_claimed_boundary()
    return {key: boundary.get(key) is True for key in P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS}


def _mn01_blockers(
    *,
    mn00: Mapping[str, Any] | None,
    ex18_envelope: Mapping[str, Any] | None,
    result_memo_ref: str,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(mn00, Mapping):
        blockers.append("mn01_mn00_scope_boundary_missing")
    else:
        try:
            assert_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_contract(mn00)
        except ValueError:
            blockers.append("mn01_mn00_scope_boundary_invalid")
    if not result_memo_ref:
        blockers.append("mn01_ex18_result_memo_ref_missing")
    if not isinstance(ex18_envelope, Mapping):
        blockers.append("mn01_ex18_bodyfree_envelope_missing")
        return blockers
    if _forbidden_payload_key_paths(ex18_envelope, path="ex18_result_memo_envelope"):
        blockers.append("mn01_ex18_envelope_forbidden_body_question_path_hash_key_detected")
    if ex18_envelope.get("body_free") is not True:
        blockers.append("mn01_ex18_envelope_not_bodyfree")
    if ex18_envelope.get("operation_step_ref") != ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF:
        blockers.append("mn01_ex18_operation_step_not_ex18")
    if ex18_envelope.get("next_required_step") != ex.P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF:
        blockers.append("mn01_ex18_next_required_step_is_not_manual_hold")
    if ex18_envelope.get("next_decision_hold_required") is not True:
        blockers.append("mn01_ex18_next_decision_hold_not_required")
    if ex18_envelope.get("next_decision_auto_execution_allowed") is not False:
        blockers.append("mn01_ex18_next_decision_auto_execution_claimed")
    if ex18_envelope.get("actual_human_review_run_here") is True or ex18_envelope.get("actual_human_review_operation_run") is True:
        blockers.append("mn01_ex18_actual_human_review_run_claim_detected")
    if ex18_envelope.get("actual_human_review_newly_run_here") is True:
        blockers.append("mn01_ex18_actual_human_review_newly_run_claim_detected")
    if ex18_envelope.get("actual_human_review_complete") is True:
        blockers.append("mn01_ex18_actual_human_review_complete_claim_detected")
    if ex18_envelope.get("actual_selection_rows_created_here") is True:
        blockers.append("mn01_ex18_actual_selection_rows_created_here_claim_detected")
    if any(_ex18_not_claimed_boundary_from_envelope(ex18_envelope).values()):
        blockers.append("mn01_ex18_not_claimed_boundary_contains_true_claim")
    if _ex18_promotion_claim_refs(ex18_envelope):
        blockers.append("mn01_ex18_promotion_or_downstream_claim_detected")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build MN00 body-free scope / no-touch / no-promotion boundary material."""

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN00_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_20260630",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "post_ex18_manual_next_decision_scope_confirmed": True,
        "return_to_actual_review_operation_design_scope": True,
        "no_touch_boundary_confirmed": True,
        "no_promotion_boundary_confirmed": True,
        "mn00_does_not_intake_ex18_result_memo": True,
        "mn00_does_not_normalize_actual_review_evidence_state": True,
        "mn00_does_not_run_manual_decision_classifier": True,
        "mn00_does_not_generate_body_full_packet": True,
        "mn00_does_not_run_actual_human_review": True,
        "mn00_does_not_create_review_rows_rating_rows_question_rows_or_disposal": True,
        "p8_question_design_out_of_scope": True,
        "p8_question_implementation_out_of_scope": True,
        "r52_actual_execution_out_of_scope": True,
        "p5_finalization_out_of_scope": True,
        "p6_start_out_of_scope": True,
        "p7_completion_out_of_scope": True,
        "release_decision_out_of_scope": True,
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen": True,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "support_material_refs": dict(P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN00 scope / no-touch / no-promotion boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN00_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN00 scope / no-touch / no-promotion boundary",
    )
    for key in (
        "post_ex18_manual_next_decision_scope_confirmed",
        "return_to_actual_review_operation_design_scope",
        "no_touch_boundary_confirmed",
        "no_promotion_boundary_confirmed",
        "mn00_does_not_intake_ex18_result_memo",
        "mn00_does_not_normalize_actual_review_evidence_state",
        "mn00_does_not_run_manual_decision_classifier",
        "mn00_does_not_generate_body_full_packet",
        "mn00_does_not_run_actual_human_review",
        "mn00_does_not_create_review_rows_rating_rows_question_rows_or_disposal",
        "p8_question_design_out_of_scope",
        "p8_question_implementation_out_of_scope",
        "r52_actual_execution_out_of_scope",
        "p5_finalization_out_of_scope",
        "p6_start_out_of_scope",
        "p7_completion_out_of_scope",
        "release_decision_out_of_scope",
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN00 required true boundary changed: {key}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostEX18-MN00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostEX18-MN00 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostEX18-MN00 next required step changed")
    if data.get("support_material_refs") != P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN00 support material refs changed")
    if data.get("support_material_ref_count") != len(P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS):
        raise ValueError("P7-R54-AHR-PostEX18-MN00 support material ref count changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN00 claim boundary refs changed")
    if data.get("claim_boundary_ref_count") != len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS):
        raise ValueError("P7-R54-AHR-PostEX18-MN00 claim boundary ref count changed")
    return True


def build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
    *,
    scope_no_touch_no_promotion_boundary_freeze: Mapping[str, Any] | None = None,
    ex18_result_memo_bodyfree_envelope: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_EX18_EX18_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN01 body-free EX18 result memo / envelope intake material."""

    mn00 = dict(
        scope_no_touch_no_promotion_boundary_freeze
        or build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze(
            review_session_id=review_session_id
        )
    )
    result_ref = _clean_ref(result_memo_ref, default="", max_length=220)
    ex18_env = dict(ex18_result_memo_bodyfree_envelope or {}) if isinstance(ex18_result_memo_bodyfree_envelope, Mapping) else None
    blockers = _mn01_blockers(mn00=mn00, ex18_envelope=ex18_env, result_memo_ref=result_ref)
    ready = not blockers
    forbidden_paths = _forbidden_payload_key_paths(ex18_env or {}, path="ex18_result_memo_envelope")
    promotion_claim_refs = _ex18_promotion_claim_refs(ex18_env)
    not_claimed_boundary = _ex18_not_claimed_boundary_from_envelope(ex18_env)
    ex18_row_counts = _safe_row_counts((ex18_env or {}).get("row_counts") if ex18_env else None)
    candidate_only_decisions = _safe_string_list((ex18_env or {}).get("candidate_only_decisions") if ex18_env else None)
    actual_run_reported = _bodyfree_bool(ex18_env or {}, "actual_human_review_run_here") or _bodyfree_bool(
        ex18_env or {}, "actual_human_review_operation_run"
    )
    actual_newly_run_reported = _bodyfree_bool(ex18_env or {}, "actual_human_review_newly_run_here")
    return_candidate = ready and not actual_run_reported and not actual_newly_run_reported

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN01_EX18_RESULT_MEMO_BODYFREE_ENVELOPE_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN01_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_20260630",
        "review_session_id": _safe_review_session_id(review_session_id or mn00.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn00_schema_version": mn00.get("schema_version", ""),
        "mn00_material_ref": mn00.get("material_id", ""),
        "mn00_next_required_step": mn00.get("next_required_step", ""),
        "mn00_scope_confirmed": mn00.get("post_ex18_manual_next_decision_scope_confirmed") is True,
        "mn00_no_touch_boundary_confirmed": mn00.get("no_touch_boundary_confirmed") is True,
        "mn00_no_promotion_boundary_confirmed": mn00.get("no_promotion_boundary_confirmed") is True,
        "mn01_status_ref": (
            P7_R54_AHR_POST_EX18_MN01_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_EX18_MN01_BLOCKED_STATUS_REF
        ),
        "mn01_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN01_ALLOWED_STATUS_REFS),
        "mn01_ready": ready,
        "mn01_blocker_refs": blockers,
        "mn01_blocker_ref_count": len(blockers),
        "mn01_reason_refs": ["mn01_ex18_manual_hold_confirmed_bodyfree"] if ready else [],
        "mn01_reason_ref_count": 1 if ready else 0,
        "support_material_refs": dict(P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS),
        "ex18_result_memo_ref": result_ref,
        "ex18_result_memo_ref_present": bool(result_ref),
        "ex18_bodyfree_envelope_present": ex18_env is not None,
        "ex18_envelope_schema_version": _clean_ref((ex18_env or {}).get("schema_version"), max_length=220),
        "ex18_envelope_operation_step_ref": _clean_ref((ex18_env or {}).get("operation_step_ref"), max_length=220),
        "ex18_envelope_body_free": (ex18_env or {}).get("body_free") is True,
        "ex18_next_required_step": _clean_ref((ex18_env or {}).get("next_required_step"), max_length=220),
        "ex18_next_decision_hold_required": (ex18_env or {}).get("next_decision_hold_required") is True,
        "ex18_next_decision_auto_execution_allowed": False,
        "ex18_result_memo_ready_reported": (ex18_env or {}).get("result_memo_ready") is True,
        "ex18_validation_command_matrix_ready_reported": (ex18_env or {}).get("validation_command_matrix_ready") is True,
        "ex18_actual_review_evidence_complete_reported_by_contract": (ex18_env or {}).get("actual_review_evidence_complete") is True,
        "ex18_actual_human_review_run_here_reported": False,
        "ex18_actual_human_review_newly_run_here_reported": False,
        "ex18_actual_human_review_complete_reported": False,
        "ex18_actual_selection_rows_created_here_reported": False,
        "ex18_actual_rating_rows_materialized_here_reported": (ex18_env or {}).get("actual_rating_rows_materialized_here") is True,
        "ex18_actual_question_need_observation_rows_materialized_here_reported": (
            (ex18_env or {}).get("actual_question_need_observation_rows_materialized_here") is True
        ),
        "ex18_actual_disposal_receipt_materialized_here_reported": (
            (ex18_env or {}).get("actual_disposal_receipt_materialized_here") is True
        ),
        "ex18_disposal_verified_reported": (ex18_env or {}).get("disposal_verified") is True,
        "ex18_row_counts_bodyfree": ex18_row_counts,
        "ex18_candidate_only_decisions_bodyfree": candidate_only_decisions,
        "ex18_candidate_only_decision_count_bodyfree": len(candidate_only_decisions),
        "ex18_not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "ex18_not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "ex18_not_claimed_boundary": not_claimed_boundary,
        "ex18_forbidden_payload_key_paths": _safe_string_list(forbidden_paths, limit=40, max_length=220),
        "ex18_forbidden_payload_key_path_count": len(forbidden_paths),
        "ex18_promotion_claim_refs": promotion_claim_refs,
        "ex18_promotion_claim_ref_count": len(promotion_claim_refs),
        "ex18_recorded_validation_results": dict(P7_R54_AHR_POST_EX18_EX18_RECORDED_VALIDATION_RESULTS),
        "ex18_green_is_not_actual_review_complete": True,
        "ex18_result_memo_is_not_actual_review_receipt": True,
        "mn01_does_not_treat_ex18_contract_green_as_real_review_complete": True,
        "mn01_does_not_normalize_actual_review_evidence_state": True,
        "mn01_does_not_run_manual_decision_classifier": True,
        "mn01_return_to_actual_review_operation_candidate_ref": (
            P7_R54_AHR_POST_EX18_MN01_RETURN_OPERATION_CANDIDATE_REF if return_candidate else ""
        ),
        "mn01_return_to_actual_review_operation_candidate_only": return_candidate,
        "mn01_passes_to_actual_review_evidence_state_normalization": ready,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "basis_rewrite_required_here": False,
        "basis_rewritten_here": False,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "outer_received_zip_label_difference_recorded_bodyfree": True,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(
            P7_R54_AHR_POST_EX18_MN01_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_EX18_MN00_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_EX18_MN01_NOT_YET_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_EX18_MN00_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_EX18_MN02_STEP_REF
            if ready
            else P7_R54_AHR_POST_EX18_MN01_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN01 EX18 result memo / body-free envelope intake",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN01_EX18_RESULT_MEMO_BODYFREE_ENVELOPE_INTAKE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN01_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN01 EX18 result memo / body-free envelope intake",
    )
    if data.get("mn00_schema_version") != P7_R54_AHR_POST_EX18_MN00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostEX18-MN01 MN00 schema version changed")
    if data.get("mn00_next_required_step") != P7_R54_AHR_POST_EX18_MN01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostEX18-MN01 MN00 next required step changed")
    for key in (
        "mn00_scope_confirmed",
        "mn00_no_touch_boundary_confirmed",
        "mn00_no_promotion_boundary_confirmed",
        "ex18_green_is_not_actual_review_complete",
        "ex18_result_memo_is_not_actual_review_receipt",
        "mn01_does_not_treat_ex18_contract_green_as_real_review_complete",
        "mn01_does_not_normalize_actual_review_evidence_state",
        "mn01_does_not_run_manual_decision_classifier",
        "outer_received_zip_label_difference_recorded_bodyfree",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN01 required true boundary changed: {key}")
    if tuple(data.get("mn01_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN01 allowed status refs changed")
    if data.get("support_material_refs") != P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN01 support material refs changed")
    if data.get("support_material_ref_count") != len(P7_R54_AHR_POST_EX18_SUPPORT_MATERIAL_REFS):
        raise ValueError("P7-R54-AHR-PostEX18-MN01 support material ref count changed")
    for field, count_field in (
        ("support_material_refs", "support_material_ref_count"),
        ("mn01_blocker_refs", "mn01_blocker_ref_count"),
        ("mn01_reason_refs", "mn01_reason_ref_count"),
        ("ex18_candidate_only_decisions_bodyfree", "ex18_candidate_only_decision_count_bodyfree"),
        ("ex18_not_claimed_boundary_refs", "ex18_not_claimed_boundary_ref_count"),
        ("ex18_forbidden_payload_key_paths", "ex18_forbidden_payload_key_path_count"),
        ("ex18_promotion_claim_refs", "ex18_promotion_claim_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN01 {count_field} changed")
    if tuple(data.get("ex18_not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN01 EX18 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostEX18-MN01 not-claimed boundary must stay false")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN01 claim boundary refs changed")
    for key in (
        "ex18_next_decision_auto_execution_allowed",
        "ex18_actual_human_review_run_here_reported",
        "ex18_actual_human_review_newly_run_here_reported",
        "ex18_actual_human_review_complete_reported",
        "ex18_actual_selection_rows_created_here_reported",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN01 required false EX18 report field changed: {key}")
    ready = data.get("mn01_status_ref") == P7_R54_AHR_POST_EX18_MN01_READY_STATUS_REF
    if data.get("mn01_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN01 ready flag changed")
    if ready:
        if data.get("mn01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready material cannot carry blockers")
        if data.get("mn01_reason_refs") != ["mn01_ex18_manual_hold_confirmed_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready reason changed")
        if data.get("ex18_bodyfree_envelope_present") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready material requires EX18 envelope")
        if data.get("ex18_envelope_body_free") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready EX18 envelope must be body-free")
        if data.get("ex18_envelope_operation_step_ref") != ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready EX18 operation step changed")
        if data.get("ex18_next_required_step") != ex.P7_R54_AHR_POST_CR22_EX18_NEXT_DECISION_HOLD_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready EX18 next required step must hold")
        if data.get("ex18_next_decision_hold_required") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready EX18 hold required flag changed")
        if data.get("mn01_return_to_actual_review_operation_candidate_only") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready material requires return-operation candidate-only")
        if data.get("mn01_return_to_actual_review_operation_candidate_ref") != P7_R54_AHR_POST_EX18_MN01_RETURN_OPERATION_CANDIDATE_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 return-operation candidate ref changed")
        if data.get("mn01_passes_to_actual_review_evidence_state_normalization") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 ready material must pass to MN02")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN01_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN01_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 next step changed")
    else:
        if data.get("mn01_status_ref") != P7_R54_AHR_POST_EX18_MN01_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 blocked status changed")
        if not data.get("mn01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN01 blocked material must carry blockers")
        if data.get("mn01_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 blocked material cannot carry ready reasons")
        if data.get("mn01_passes_to_actual_review_evidence_state_normalization") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 blocked material cannot pass to MN02")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN00_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN00_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN01_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN01 blocked next required step changed")
    return True



def _evidence_bundle_promotion_claim_refs(bundle: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(bundle, Mapping):
        return []
    promotion_keys = (
        "next_decision_auto_execution_allowed",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "r52_actual_execution_confirmed",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green",
        "full_backend_suite_green_confirmed",
        "rn_contract_green",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
    )
    return [key for key in promotion_keys if bundle.get(key) is True]


def _mn02_invalid_source_refs(bundle: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(bundle, Mapping):
        return []
    invalid: list[str] = []
    source = _clean_ref(bundle.get("actual_source_ref"), max_length=180)
    if source and source != P7_R54_AHR_POST_EX18_ACTUAL_PERSON_LOCAL_ONLY_REVIEW_SOURCE_REF:
        invalid.append("mn02_evidence_bundle_source_is_not_actual_person_local_only_review")
    if bundle.get("row_created_by_helper") is True:
        invalid.append("mn02_helper_created_rows_cannot_be_actual_evidence")
    if bundle.get("row_created_for_unit_test") is True:
        invalid.append("mn02_unit_test_rows_cannot_be_actual_evidence")
    if bundle.get("row_is_synthetic_contract_fixture") is True:
        invalid.append("mn02_synthetic_contract_fixture_rows_cannot_be_actual_evidence")
    if bundle.get("historical_row_reused") is True:
        invalid.append("mn02_historical_rows_cannot_be_reused_as_current_actual_evidence")
    return _dedupe_refs(invalid)


def _bundle_counts_are_complete(row_counts: Mapping[str, int]) -> bool:
    return all(row_counts.get(key) == 24 for key in (
        "reviewed_case_count",
        "sanitized_review_result_row_count",
        "rating_row_count",
        "question_need_observation_row_count",
    ))


def _mn02_status_reason_refs(
    *,
    bundle_present: bool,
    status_ref: str,
    forbidden_payload_key_paths: Sequence[str],
    promotion_claim_refs: Sequence[str],
    invalid_source_refs: Sequence[str],
    all_required_counts_are_24: bool,
    source_is_actual_person: bool,
    reviewer_receipt: bool,
    actual_human_review_executed_by_person: bool,
    disposal_verified_bodyfree: bool,
    no_body_leak_validation_passed: bool,
    no_question_text_validation_passed: bool,
    no_path_hash_validation_passed: bool,
) -> list[str]:
    reasons: list[str] = []
    if forbidden_payload_key_paths:
        reasons.append("mn02_forbidden_body_question_path_hash_key_detected")
    if promotion_claim_refs:
        reasons.append("mn02_promotion_claim_detected_in_evidence_bundle")
    if invalid_source_refs:
        reasons.extend(invalid_source_refs)
    if status_ref == P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_MISSING_REAL_REVIEW_REQUIRED_REF:
        reasons.extend(
            [
                "ex18_next_decision_hold_is_not_actual_review_complete",
                "actual_human_review_execution_not_run_here",
                "actual_selection_rows_not_created_here",
                "actual_rating_rows_not_materialized_from_real_review",
                "actual_question_need_observation_rows_not_materialized_from_real_review",
                "actual_disposal_receipt_not_materialized_here",
            ]
        )
    elif status_ref == P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INCOMPLETE_BODYFREE_REF:
        if not bundle_present:
            reasons.append("mn02_evidence_bundle_missing")
        if not source_is_actual_person:
            reasons.append("mn02_actual_person_source_missing")
        if not actual_human_review_executed_by_person:
            reasons.append("mn02_actual_human_review_executed_by_person_missing")
        if not reviewer_receipt:
            reasons.append("mn02_reviewer_local_only_read_receipt_missing")
        if not all_required_counts_are_24:
            reasons.append("mn02_required_row_counts_not_24")
        if not disposal_verified_bodyfree:
            reasons.append("mn02_disposal_receipt_or_verification_missing")
        if not no_body_leak_validation_passed:
            reasons.append("mn02_no_body_leak_validation_missing")
        if not no_question_text_validation_passed:
            reasons.append("mn02_no_question_text_validation_missing")
        if not no_path_hash_validation_passed:
            reasons.append("mn02_no_path_hash_validation_missing")
    elif status_ref == P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BY_ACTUAL_PERSON_REVIEW_BODYFREE_REF:
        reasons.append("mn02_actual_person_local_only_review_evidence_complete_bodyfree")
    elif status_ref == P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INVALID_SOURCE_DETECTED_REF:
        if not reasons:
            reasons.append("mn02_invalid_actual_review_evidence_source_detected")
    return _dedupe_refs(reasons)


def _manual_decision_next_required_step(decision_ref: str) -> str:
    if decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_BODY_LEAK_REF:
        return P7_R54_AHR_POST_EX18_MN03_STOP_BODY_LEAK_NEXT_REQUIRED_STEP_REF
    if decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_PROMOTION_CLAIM_REF:
        return P7_R54_AHR_POST_EX18_MN03_STOP_PROMOTION_NEXT_REQUIRED_STEP_REF
    if decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_HOLD_EX18_INVALID_REF:
        return P7_R54_AHR_POST_EX18_MN03_HOLD_EX18_NEXT_REQUIRED_STEP_REF
    if decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF:
        return P7_R54_AHR_POST_EX18_MN03_DOWNSTREAM_MANUAL_NEXT_REQUIRED_STEP_REF
    return P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF


def build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
    *,
    ex18_result_memo_bodyfree_envelope_intake: Mapping[str, Any] | None = None,
    actual_review_evidence_intake_bundle: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN02 body-free actual review evidence state normalization material."""

    if ex18_result_memo_bodyfree_envelope_intake is None:
        ex18_result_memo_bodyfree_envelope_intake = build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake()

    mn01_valid = False
    if isinstance(ex18_result_memo_bodyfree_envelope_intake, Mapping):
        try:
            assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(
                ex18_result_memo_bodyfree_envelope_intake
            )
            mn01_valid = ex18_result_memo_bodyfree_envelope_intake.get("mn01_ready") is True
        except ValueError:
            mn01_valid = False

    bundle = actual_review_evidence_intake_bundle if isinstance(actual_review_evidence_intake_bundle, Mapping) else None
    bundle_present = bundle is not None
    forbidden_payload_key_paths = _forbidden_payload_key_paths(bundle, path="actual_review_evidence_intake_bundle") if bundle else []
    promotion_claim_refs = _evidence_bundle_promotion_claim_refs(bundle)
    invalid_source_refs = _mn02_invalid_source_refs(bundle)
    row_counts = _safe_row_counts(bundle.get("row_counts") if bundle else None)

    bundle_body_free = bundle.get("body_free") is True if bundle else False
    actual_source_ref = _clean_ref(bundle.get("actual_source_ref") if bundle else "", max_length=180)
    source_is_actual_person = actual_source_ref == P7_R54_AHR_POST_EX18_ACTUAL_PERSON_LOCAL_ONLY_REVIEW_SOURCE_REF
    actual_source_guard_passed = bundle.get("actual_source_guard_passed") is True if bundle else False
    actual_human_review_executed_by_person = bundle.get("actual_human_review_executed_by_person") is True if bundle else False
    reviewer_receipt = bundle.get("reviewer_local_only_read_receipt_present") is True if bundle else False
    disposal_receipt_present = bool(_clean_ref(bundle.get("disposal_receipt_ref") if bundle else "", max_length=180))
    disposal_verified_bodyfree = bundle.get("disposal_verified") is True if bundle else False
    no_body_leak_validation_passed = bundle.get("no_body_leak_validation_passed") is True if bundle else False
    no_question_text_validation_passed = bundle.get("no_question_text_validation_passed") is True if bundle else False
    no_path_hash_validation_passed = bundle.get("no_path_hash_validation_passed") is True if bundle else False
    all_required_counts_are_24 = _bundle_counts_are_complete(row_counts)
    complete_by_actual_person_review_bodyfree = all(
        (
            bundle_present,
            bundle_body_free,
            mn01_valid,
            not forbidden_payload_key_paths,
            not promotion_claim_refs,
            not invalid_source_refs,
            source_is_actual_person,
            actual_source_guard_passed,
            actual_human_review_executed_by_person,
            reviewer_receipt,
            all_required_counts_are_24,
            disposal_receipt_present,
            disposal_verified_bodyfree,
            no_body_leak_validation_passed,
            no_question_text_validation_passed,
            no_path_hash_validation_passed,
        )
    )

    if forbidden_payload_key_paths or promotion_claim_refs or invalid_source_refs:
        evidence_status_ref = P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INVALID_SOURCE_DETECTED_REF
    elif complete_by_actual_person_review_bodyfree:
        evidence_status_ref = P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BY_ACTUAL_PERSON_REVIEW_BODYFREE_REF
    elif bundle_present:
        evidence_status_ref = P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_INCOMPLETE_BODYFREE_REF
    else:
        evidence_status_ref = P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_MISSING_REAL_REVIEW_REQUIRED_REF

    blocker_refs: list[str] = []
    if not mn01_valid:
        blocker_refs.append("mn02_mn01_ex18_manual_hold_intake_not_ready")
    if forbidden_payload_key_paths:
        blocker_refs.append("mn02_evidence_bundle_forbidden_body_question_path_hash_key_detected")
    if promotion_claim_refs:
        blocker_refs.append("mn02_evidence_bundle_promotion_or_downstream_claim_detected")
    if invalid_source_refs:
        blocker_refs.append("mn02_evidence_bundle_invalid_source_detected")
    blocker_refs = _dedupe_refs(blocker_refs)
    ready = not blocker_refs
    status_ref = P7_R54_AHR_POST_EX18_MN02_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN02_BLOCKED_STATUS_REF
    status_reason_refs = _mn02_status_reason_refs(
        bundle_present=bundle_present,
        status_ref=evidence_status_ref,
        forbidden_payload_key_paths=forbidden_payload_key_paths,
        promotion_claim_refs=promotion_claim_refs,
        invalid_source_refs=invalid_source_refs,
        all_required_counts_are_24=all_required_counts_are_24,
        source_is_actual_person=source_is_actual_person,
        reviewer_receipt=reviewer_receipt,
        actual_human_review_executed_by_person=actual_human_review_executed_by_person,
        disposal_verified_bodyfree=disposal_verified_bodyfree,
        no_body_leak_validation_passed=no_body_leak_validation_passed,
        no_question_text_validation_passed=no_question_text_validation_passed,
        no_path_hash_validation_passed=no_path_hash_validation_passed,
    )
    false_flags = _false_flags()
    if complete_by_actual_person_review_bodyfree:
        false_flags["actual_review_evidence_complete"] = True
        false_flags["actual_review_evidence_complete_from_real_review"] = True

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN02_ACTUAL_REVIEW_EVIDENCE_STATE_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN02_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_20260630",
        "review_session_id": _safe_review_session_id(review_session_id or (ex18_result_memo_bodyfree_envelope_intake or {}).get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn01_schema_version": (ex18_result_memo_bodyfree_envelope_intake or {}).get("schema_version", ""),
        "mn01_material_ref": (ex18_result_memo_bodyfree_envelope_intake or {}).get("material_id", ""),
        "mn01_status_ref": (ex18_result_memo_bodyfree_envelope_intake or {}).get("mn01_status_ref", ""),
        "mn01_ready": mn01_valid,
        "mn01_next_required_step": (ex18_result_memo_bodyfree_envelope_intake or {}).get("next_required_step", ""),
        "mn01_return_to_actual_review_operation_candidate_ref": (ex18_result_memo_bodyfree_envelope_intake or {}).get("mn01_return_to_actual_review_operation_candidate_ref", ""),
        "mn01_return_to_actual_review_operation_candidate_only": (ex18_result_memo_bodyfree_envelope_intake or {}).get("mn01_return_to_actual_review_operation_candidate_only") is True,
        "mn02_status_ref": status_ref,
        "mn02_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN02_ALLOWED_STATUS_REFS),
        "mn02_ready": ready,
        "mn02_blocker_refs": blocker_refs,
        "mn02_blocker_ref_count": len(blocker_refs),
        "mn02_reason_refs": status_reason_refs,
        "mn02_reason_ref_count": len(status_reason_refs),
        "actual_review_evidence_status_ref": evidence_status_ref,
        "actual_review_evidence_status_allowed_refs": list(P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_STATUS_REFS),
        "actual_review_evidence_status_reason_refs": status_reason_refs,
        "actual_review_evidence_status_reason_ref_count": len(status_reason_refs),
        "actual_review_evidence_intake_bundle_present": bundle_present,
        "actual_review_evidence_intake_bundle_body_free": bundle_body_free,
        "actual_review_evidence_intake_bundle_source_ref": actual_source_ref,
        "actual_review_evidence_intake_bundle_forbidden_payload_key_paths": _dedupe_refs(forbidden_payload_key_paths),
        "actual_review_evidence_intake_bundle_forbidden_payload_key_path_count": len(_dedupe_refs(forbidden_payload_key_paths)),
        "actual_review_evidence_intake_bundle_promotion_claim_refs": _dedupe_refs(promotion_claim_refs),
        "actual_review_evidence_intake_bundle_promotion_claim_ref_count": len(_dedupe_refs(promotion_claim_refs)),
        "actual_review_evidence_intake_bundle_invalid_source_refs": invalid_source_refs,
        "actual_review_evidence_intake_bundle_invalid_source_ref_count": len(invalid_source_refs),
        "actual_review_evidence_intake_bundle_row_counts_bodyfree": row_counts,
        "actual_source_ref": actual_source_ref,
        "actual_source_guard_passed": actual_source_guard_passed,
        "actual_source_is_actual_person_local_only_review": source_is_actual_person,
        "actual_human_review_executed_by_person": actual_human_review_executed_by_person,
        "reviewer_local_only_read_receipt_present": reviewer_receipt,
        "reviewed_case_count": row_counts["reviewed_case_count"],
        "sanitized_review_result_row_count": row_counts["sanitized_review_result_row_count"],
        "rating_row_count": row_counts["rating_row_count"],
        "question_need_observation_row_count": row_counts["question_need_observation_row_count"],
        "required_case_count": 24,
        "all_required_counts_are_24": all_required_counts_are_24,
        "disposal_receipt_present": disposal_receipt_present,
        "disposal_verified_bodyfree": disposal_verified_bodyfree,
        "no_body_leak_validation_passed": no_body_leak_validation_passed,
        "no_question_text_validation_passed": no_question_text_validation_passed,
        "no_path_hash_validation_passed": no_path_hash_validation_passed,
        "row_created_by_helper": bundle.get("row_created_by_helper") is True if bundle else False,
        "row_created_for_unit_test": bundle.get("row_created_for_unit_test") is True if bundle else False,
        "row_is_synthetic_contract_fixture": bundle.get("row_is_synthetic_contract_fixture") is True if bundle else False,
        "historical_row_reused": bundle.get("historical_row_reused") is True if bundle else False,
        "unit_test_rows_used_as_actual_evidence": bundle.get("row_created_for_unit_test") is True if bundle else False,
        "helper_default_rows_used_as_actual_evidence": bundle.get("row_created_by_helper") is True if bundle else False,
        "synthetic_rows_used_as_actual_evidence": bundle.get("row_is_synthetic_contract_fixture") is True if bundle else False,
        "historical_rows_used_as_actual_evidence": bundle.get("historical_row_reused") is True if bundle else False,
        "ex18_contract_green_promoted_to_actual_complete": False,
        "actual_review_evidence_complete_by_actual_person_review_bodyfree": complete_by_actual_person_review_bodyfree,
        "actual_review_evidence_complete_from_real_review_normalized": complete_by_actual_person_review_bodyfree,
        "actual_review_evidence_complete_from_ex18_contract_report": False,
        "mn02_does_not_run_actual_human_review": True,
        "mn02_does_not_create_actual_rows": True,
        "mn02_does_not_generate_body_full_packet": True,
        "mn02_does_not_run_manual_decision_classifier": True,
        "mn02_passes_to_manual_decision_classifier": ready,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN02_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN02_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN03_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN02_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN02_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN02 actual review evidence state normalization",
    )
    allowed_true = []
    if data.get("actual_review_evidence_complete_by_actual_person_review_bodyfree") is True:
        allowed_true.extend(["actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review"])
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN02_ACTUAL_REVIEW_EVIDENCE_STATE_NORMALIZATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN02_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN02 actual review evidence state normalization",
        allowed_true_false_flag_refs=allowed_true,
    )
    if tuple(data.get("mn02_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN02 allowed status refs changed")
    if tuple(data.get("actual_review_evidence_status_allowed_refs") or ()) != P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN02 evidence status refs changed")
    for field, count_field in (
        ("mn02_blocker_refs", "mn02_blocker_ref_count"),
        ("mn02_reason_refs", "mn02_reason_ref_count"),
        ("actual_review_evidence_status_reason_refs", "actual_review_evidence_status_reason_ref_count"),
        ("actual_review_evidence_intake_bundle_forbidden_payload_key_paths", "actual_review_evidence_intake_bundle_forbidden_payload_key_path_count"),
        ("actual_review_evidence_intake_bundle_promotion_claim_refs", "actual_review_evidence_intake_bundle_promotion_claim_ref_count"),
        ("actual_review_evidence_intake_bundle_invalid_source_refs", "actual_review_evidence_intake_bundle_invalid_source_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN02 {count_field} changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN02 not-claimed refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostEX18-MN02 not-claimed boundary must stay false")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN02 claim boundary refs changed")
    for key in (
        "mn02_does_not_run_actual_human_review",
        "mn02_does_not_create_actual_rows",
        "mn02_does_not_generate_body_full_packet",
        "mn02_does_not_run_manual_decision_classifier",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN02 required true boundary changed: {key}")
    status_ref = data.get("actual_review_evidence_status_ref")
    if status_ref not in P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN02 invalid evidence status ref")
    complete = status_ref == P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BY_ACTUAL_PERSON_REVIEW_BODYFREE_REF
    if complete:
        if data.get("actual_review_evidence_complete_by_actual_person_review_bodyfree") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 complete status requires complete flag")
        if data.get("actual_review_evidence_complete_from_real_review_normalized") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 complete status requires normalized complete flag")
        if data.get("actual_review_evidence_complete") is not True or data.get("actual_review_evidence_complete_from_real_review") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 complete status requires real-review evidence flags")
        if data.get("mn02_ready") is not True or data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 complete status must pass to MN03")
    else:
        if data.get("actual_review_evidence_complete_by_actual_person_review_bodyfree") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 non-complete status cannot claim complete")
        if data.get("actual_review_evidence_complete_from_real_review_normalized") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 non-complete status cannot normalize complete")
    ready = data.get("mn02_status_ref") == P7_R54_AHR_POST_EX18_MN02_READY_STATUS_REF
    if data.get("mn02_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN02 ready flag changed")
    if ready:
        if data.get("mn02_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 ready material cannot carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN02_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN02_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 next step changed")
    else:
        if data.get("mn02_status_ref") != P7_R54_AHR_POST_EX18_MN02_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 blocked status changed")
        if not data.get("mn02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN02 blocked material must carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN01_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN01_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN02_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN02 blocked next required step changed")
    if data.get("ex18_contract_green_promoted_to_actual_complete") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN02 must not promote EX18 contract green to actual complete")
    return True


def build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(
    *,
    actual_review_evidence_state_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN03 body-free manual decision classifier material."""

    if actual_review_evidence_state_normalization is None:
        actual_review_evidence_state_normalization = build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization()

    mn02_valid = False
    if isinstance(actual_review_evidence_state_normalization, Mapping):
        try:
            assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract(
                actual_review_evidence_state_normalization
            )
            mn02_valid = actual_review_evidence_state_normalization.get("mn02_ready") is True
        except ValueError:
            mn02_valid = False

    blocker_refs = list(actual_review_evidence_state_normalization.get("mn02_blocker_refs") or []) if isinstance(actual_review_evidence_state_normalization, Mapping) else ["mn03_mn02_actual_review_evidence_state_missing"]
    evidence_status_ref = _clean_ref((actual_review_evidence_state_normalization or {}).get("actual_review_evidence_status_ref", ""), max_length=180)
    forbidden_payload_key_paths = list((actual_review_evidence_state_normalization or {}).get("actual_review_evidence_intake_bundle_forbidden_payload_key_paths") or [])
    promotion_claim_refs = list((actual_review_evidence_state_normalization or {}).get("actual_review_evidence_intake_bundle_promotion_claim_refs") or [])
    complete_by_actual_person = (actual_review_evidence_state_normalization or {}).get("actual_review_evidence_complete_by_actual_person_review_bodyfree") is True
    complete_normalized = (actual_review_evidence_state_normalization or {}).get("actual_review_evidence_complete_from_real_review_normalized") is True

    if forbidden_payload_key_paths:
        decision_ref = P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_BODY_LEAK_REF
        priority_ref = "body_leak_or_question_text_detected_first"
    elif promotion_claim_refs:
        decision_ref = P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_PROMOTION_CLAIM_REF
        priority_ref = "promotion_claim_detected_before_return_operation"
    elif not mn02_valid or evidence_status_ref not in P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_STATUS_REFS:
        decision_ref = P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_HOLD_EX18_INVALID_REF
        priority_ref = "ex18_or_mn02_not_ready_or_invalid"
    elif evidence_status_ref == P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_COMPLETE_BY_ACTUAL_PERSON_REVIEW_BODYFREE_REF and complete_by_actual_person and complete_normalized:
        decision_ref = P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF
        priority_ref = "actual_review_evidence_complete_downstream_manual_decision_required"
    else:
        decision_ref = P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF
        priority_ref = "actual_review_evidence_missing_or_incomplete_return_operation_required"

    ready = decision_ref in (
        P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF,
        P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF,
    )
    if decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF:
        reason_refs = [
            "ex18_next_decision_hold_is_not_actual_review_complete",
            "actual_human_review_execution_not_run_here",
            "actual_selection_rows_not_created_here",
            "actual_rating_rows_not_materialized_from_real_review",
            "actual_question_need_observation_rows_not_materialized_from_real_review",
            "actual_disposal_receipt_not_materialized_here",
            "p8_start_allowed_false",
            "r52_actual_execution_confirmed_false",
        ]
    elif decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF:
        reason_refs = [
            "actual_review_evidence_complete_by_actual_person_review_bodyfree",
            "p5_p6_p8_r52_release_still_require_downstream_manual_decision",
            "next_decision_auto_execution_allowed_false",
        ]
    elif decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_BODY_LEAK_REF:
        reason_refs = ["body_or_question_or_path_or_hash_key_detected", *forbidden_payload_key_paths[:8]]
    elif decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STOP_PROMOTION_CLAIM_REF:
        reason_refs = ["promotion_or_downstream_claim_detected", *promotion_claim_refs[:8]]
    else:
        reason_refs = ["ex18_or_mn02_not_ready_or_invalid", *blocker_refs[:8]]
    reason_refs = _dedupe_refs(reason_refs)
    blocker_refs = [] if ready else _dedupe_refs(blocker_refs or reason_refs)

    blocked_downstream_refs = [
        "p5_final",
        "p6_start",
        "p8_start",
        "r52_actual_execution",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green",
        "rn_contract_green",
        "rn_real_device_modal_verified",
    ]
    false_flags = _false_flags()
    false_flags["manual_decision_classifier_run_here"] = True
    if complete_by_actual_person and complete_normalized:
        false_flags["actual_review_evidence_complete"] = True
        false_flags["actual_review_evidence_complete_from_real_review"] = True

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_CLASSIFIER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN03_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_20260630",
        "review_session_id": _safe_review_session_id(review_session_id or (actual_review_evidence_state_normalization or {}).get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn02_schema_version": (actual_review_evidence_state_normalization or {}).get("schema_version", ""),
        "mn02_material_ref": (actual_review_evidence_state_normalization or {}).get("material_id", ""),
        "mn02_status_ref": (actual_review_evidence_state_normalization or {}).get("mn02_status_ref", ""),
        "mn02_ready": mn02_valid,
        "mn02_next_required_step": (actual_review_evidence_state_normalization or {}).get("next_required_step", ""),
        "manual_decision_ref": decision_ref,
        "manual_decision_allowed_refs": list(P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_REFS),
        "manual_decision_status_ref": P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_BLOCKED_STATUS_REF,
        "manual_decision_status_allowed_refs": list(P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STATUS_REFS),
        "manual_decision_ready": ready,
        "manual_decision_reason_refs": reason_refs,
        "manual_decision_reason_ref_count": len(reason_refs),
        "manual_decision_blocker_refs": blocker_refs,
        "manual_decision_blocker_ref_count": len(blocker_refs),
        "manual_decision_classifier_run_here": True,
        "manual_decision_auto_executes_downstream": False,
        "next_decision_auto_execution_allowed": False,
        "mn03_classifier_priority_ref": priority_ref,
        "actual_review_evidence_status_ref": evidence_status_ref,
        "actual_review_evidence_status_allowed_refs": list(P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_STATUS_REFS),
        "actual_review_evidence_complete_by_actual_person_review_bodyfree": complete_by_actual_person,
        "actual_review_evidence_complete_from_real_review_normalized": complete_normalized,
        "return_to_actual_review_operation_required": decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF,
        "downstream_manual_decision_required": decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF,
        "no_promotion_boundary_confirmed": True,
        "blocked_downstream_refs": blocked_downstream_refs,
        "blocked_downstream_ref_count": len(blocked_downstream_refs),
        "p5_p6_p8_r52_release_auto_execution_blocked": True,
        "p8_material_candidate_only_is_not_p8_start_allowed": True,
        "r52_handoff_candidate_is_not_r52_actual_execution": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": _manual_decision_next_required_step(decision_ref),
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN03_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN03 manual decision classifier",
    )
    allowed_true = ["manual_decision_classifier_run_here"]
    if data.get("actual_review_evidence_complete_by_actual_person_review_bodyfree") is True:
        allowed_true.extend(["actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review"])
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_CLASSIFIER_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN03_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN03 manual decision classifier",
        allowed_true_false_flag_refs=allowed_true,
    )
    if tuple(data.get("manual_decision_allowed_refs") or ()) != P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 manual decision refs changed")
    if tuple(data.get("manual_decision_status_allowed_refs") or ()) != P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 manual decision status refs changed")
    if tuple(data.get("actual_review_evidence_status_allowed_refs") or ()) != P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 evidence status refs changed")
    for field, count_field in (
        ("manual_decision_reason_refs", "manual_decision_reason_ref_count"),
        ("manual_decision_blocker_refs", "manual_decision_blocker_ref_count"),
        ("blocked_downstream_refs", "blocked_downstream_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN03 {count_field} changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 not-claimed refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostEX18-MN03 not-claimed boundary must stay false")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 claim boundary refs changed")
    for key in (
        "manual_decision_classifier_run_here",
        "no_promotion_boundary_confirmed",
        "p5_p6_p8_r52_release_auto_execution_blocked",
        "p8_material_candidate_only_is_not_p8_start_allowed",
        "r52_handoff_candidate_is_not_r52_actual_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN03 required true classifier boundary changed: {key}")
    for key in (
        "manual_decision_auto_executes_downstream",
        "next_decision_auto_execution_allowed",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "actual_r52_reintake_execution_confirmed",
        "r52_actual_execution_confirmed",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN03 downstream promotion flag changed: {key}")
    decision_ref = data.get("manual_decision_ref")
    if decision_ref not in P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 invalid manual decision ref")
    if data.get("next_required_step") != _manual_decision_next_required_step(str(decision_ref)):
        raise ValueError("P7-R54-AHR-PostEX18-MN03 next required step changed")
    ready = data.get("manual_decision_status_ref") == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_READY_STATUS_REF
    if data.get("manual_decision_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 ready flag changed")
    if ready and data.get("manual_decision_blocker_refs") != []:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 ready material cannot carry blockers")
    if not ready and not data.get("manual_decision_blocker_refs"):
        raise ValueError("P7-R54-AHR-PostEX18-MN03 blocked material must carry blockers")
    if decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF:
        if data.get("return_to_actual_review_operation_required") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN03 return decision must require actual review operation")
        if data.get("downstream_manual_decision_required") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN03 return decision cannot claim downstream decision ready")
    elif decision_ref == P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_EVIDENCE_COMPLETE_DOWNSTREAM_MANUAL_REF:
        if data.get("return_to_actual_review_operation_required") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN03 complete decision cannot require return operation")
        if data.get("downstream_manual_decision_required") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN03 complete decision must require downstream manual decision")
    else:
        if data.get("return_to_actual_review_operation_required") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN03 stop/hold decision cannot require return operation")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN03_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostEX18-MN03 not-yet steps changed")
    return True



def _mn04_blockers(manual_decision: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(manual_decision, Mapping):
        return ["mn04_manual_decision_classifier_material_missing"]
    try:
        assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(manual_decision)
    except ValueError:
        blockers.append("mn04_manual_decision_classifier_contract_invalid")
    if manual_decision.get("manual_decision_ready") is not True:
        blockers.append("mn04_manual_decision_not_ready")
    if manual_decision.get("manual_decision_ref") != P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF:
        blockers.append("mn04_manual_decision_is_not_return_to_actual_review_operation_required")
    if manual_decision.get("return_to_actual_review_operation_required") is not True:
        blockers.append("mn04_return_to_actual_review_operation_required_flag_missing")
    if manual_decision.get("manual_decision_auto_executes_downstream") is not False:
        blockers.append("mn04_next_decision_auto_execution_claim_detected")
    if manual_decision.get("actual_review_evidence_complete_from_real_review_normalized") is True:
        blockers.append("mn04_actual_review_evidence_complete_should_use_downstream_manual_decision_not_return_plan")
    for key in ("p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed"):
        if manual_decision.get(key) is True:
            blockers.append(f"mn04_downstream_promotion_claim_detected:{key}")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
    *,
    manual_decision_classifier: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN04 body-free return-to-actual-review operation plan material."""

    mn03 = dict(manual_decision_classifier or {}) if isinstance(manual_decision_classifier, Mapping) else None
    if mn03 is None and manual_decision_classifier is None:
        mn03 = build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(review_session_id=review_session_id)
    blockers = _mn04_blockers(mn03)
    ready = not blockers
    reason_refs = ["mn04_return_to_actual_review_operation_plan_ready_bodyfree"] if ready else []
    false_flags = _false_flags()

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN04_RETURN_TO_ACTUAL_REVIEW_OPERATION_PLAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN04_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_20260630",
        "review_session_id": _safe_review_session_id(review_session_id or (mn03 or {}).get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn03_schema_version": (mn03 or {}).get("schema_version", ""),
        "mn03_material_ref": (mn03 or {}).get("material_id", ""),
        "mn03_manual_decision_ref": (mn03 or {}).get("manual_decision_ref", ""),
        "mn03_manual_decision_status_ref": (mn03 or {}).get("manual_decision_status_ref", ""),
        "mn03_manual_decision_ready": (mn03 or {}).get("manual_decision_ready") is True,
        "mn03_next_required_step": (mn03 or {}).get("next_required_step", ""),
        "mn03_return_to_actual_review_operation_required": (mn03 or {}).get("return_to_actual_review_operation_required") is True,
        "mn03_actual_review_evidence_status_ref": (mn03 or {}).get("actual_review_evidence_status_ref", ""),
        "mn03_manual_decision_auto_executes_downstream": (mn03 or {}).get("manual_decision_auto_executes_downstream") is True,
        "mn04_status_ref": P7_R54_AHR_POST_EX18_MN04_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN04_BLOCKED_STATUS_REF,
        "mn04_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN04_ALLOWED_STATUS_REFS),
        "mn04_ready": ready,
        "mn04_blocker_refs": [] if ready else blockers,
        "mn04_blocker_ref_count": 0 if ready else len(blockers),
        "mn04_reason_refs": reason_refs,
        "mn04_reason_ref_count": len(reason_refs),
        "actual_operation_plan_ref": P7_R54_AHR_POST_EX18_OPERATION_PLAN_REF if ready else "",
        "operation_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "required_case_count": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "reviewed_case_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "rating_row_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "question_need_observation_row_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "local_only_required": True,
        "explicit_allow_required": True,
        "purge_plan_required": True,
        "human_reviewer_required": True,
        "reviewer_selection_only_required": True,
        "body_full_packet_local_only_required": True,
        "body_full_packet_not_persisted_required": True,
        "body_free_result_artifacts_required": True,
        "required_bodyfree_artifact_refs": list(P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS),
        "required_bodyfree_artifact_ref_count": len(P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS),
        "forbidden_artifact_refs": list(P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS),
        "forbidden_artifact_ref_count": len(P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS),
        "operation_plan_bodyfree_action_refs": list(P7_R54_AHR_POST_EX18_MN04_OPERATION_PLAN_ACTION_REFS),
        "operation_plan_bodyfree_action_ref_count": len(P7_R54_AHR_POST_EX18_MN04_OPERATION_PLAN_ACTION_REFS),
        "actual_review_operation_not_executed_here": True,
        "actual_rows_not_created_by_plan_builder": True,
        "p8_question_text_not_created_by_plan_builder": True,
        "returns_to_existing_postcr22_ex07_ex18_after_actual_review": True,
        "expected_evidence_intake_bundle_boundary_required": True,
        "mn04_passes_to_expected_bodyfree_evidence_intake_bundle_boundary": ready,
        "actual_review_basis_refreeze_required_here": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN04_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN04_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN05_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN04_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN04_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN04 return-to-actual-review operation plan",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN04_RETURN_TO_ACTUAL_REVIEW_OPERATION_PLAN_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN04_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN04 return-to-actual-review operation plan",
    )
    if tuple(data.get("mn04_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN04 allowed status refs changed")
    for field, count_field in (
        ("mn04_blocker_refs", "mn04_blocker_ref_count"),
        ("mn04_reason_refs", "mn04_reason_ref_count"),
        ("required_bodyfree_artifact_refs", "required_bodyfree_artifact_ref_count"),
        ("forbidden_artifact_refs", "forbidden_artifact_ref_count"),
        ("operation_plan_bodyfree_action_refs", "operation_plan_bodyfree_action_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN04 {count_field} changed")
    if tuple(data.get("required_bodyfree_artifact_refs") or ()) != P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN04 required body-free artifacts changed")
    if tuple(data.get("forbidden_artifact_refs") or ()) != P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN04 forbidden artifacts changed")
    if tuple(data.get("operation_plan_bodyfree_action_refs") or ()) != P7_R54_AHR_POST_EX18_MN04_OPERATION_PLAN_ACTION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN04 operation plan actions changed")
    if data.get("operation_basis_ref") != P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostEX18-MN04 operation basis changed")
    for key in (
        "required_case_count",
        "reviewed_case_count_required",
        "sanitized_review_result_row_count_required",
        "rating_row_count_required",
        "question_need_observation_row_count_required",
    ):
        if data.get(key) != P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN04 required count changed: {key}")
    for key in (
        "local_only_required", "explicit_allow_required", "purge_plan_required",
        "human_reviewer_required", "reviewer_selection_only_required",
        "body_full_packet_local_only_required", "body_full_packet_not_persisted_required",
        "body_free_result_artifacts_required", "actual_review_operation_not_executed_here",
        "actual_rows_not_created_by_plan_builder", "p8_question_text_not_created_by_plan_builder",
        "returns_to_existing_postcr22_ex07_ex18_after_actual_review",
        "expected_evidence_intake_bundle_boundary_required",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN04 required true boundary changed: {key}")
    if data.get("actual_review_basis_refreeze_required_here") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN04 cannot refreeze actual review basis here")
    ready = data.get("mn04_status_ref") == P7_R54_AHR_POST_EX18_MN04_READY_STATUS_REF
    if data.get("mn04_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN04 ready flag changed")
    if ready:
        if data.get("mn04_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 ready material cannot carry blockers")
        if data.get("mn04_reason_refs") != ["mn04_return_to_actual_review_operation_plan_ready_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 ready reason changed")
        if data.get("mn03_manual_decision_ref") != P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 ready plan requires return-operation decision")
        if data.get("mn03_return_to_actual_review_operation_required") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 ready plan requires return-operation flag")
        if data.get("actual_operation_plan_ref") != P7_R54_AHR_POST_EX18_OPERATION_PLAN_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 operation plan ref changed")
        if data.get("mn04_passes_to_expected_bodyfree_evidence_intake_bundle_boundary") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 must pass ready plan to MN05")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 next step changed")
    else:
        if data.get("mn04_status_ref") != P7_R54_AHR_POST_EX18_MN04_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 blocked status changed")
        if not data.get("mn04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN04 blocked material must carry blockers")
        if data.get("mn04_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 blocked material cannot carry ready reasons")
        if data.get("mn04_passes_to_expected_bodyfree_evidence_intake_bundle_boundary") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 blocked plan cannot pass to MN05")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN04_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN04 blocked next step changed")
    return True


def _mn05_blockers(operation_plan: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(operation_plan, Mapping):
        return ["mn05_return_to_actual_review_operation_plan_missing"]
    try:
        assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract(operation_plan)
    except ValueError:
        blockers.append("mn05_return_to_actual_review_operation_plan_contract_invalid")
    if operation_plan.get("mn04_ready") is not True:
        blockers.append("mn05_return_to_actual_review_operation_plan_not_ready")
    if operation_plan.get("actual_operation_plan_ref") != P7_R54_AHR_POST_EX18_OPERATION_PLAN_REF:
        blockers.append("mn05_operation_plan_ref_missing_or_changed")
    if operation_plan.get("mn04_passes_to_expected_bodyfree_evidence_intake_bundle_boundary") is not True:
        blockers.append("mn05_operation_plan_did_not_pass_to_expected_bundle_boundary")
    return _dedupe_refs(blockers)


def _mn05_expectation_maps() -> dict[str, dict[str, Any]]:
    return {
        "actual_operation_receipt_expectation": {
            "reviewer_person_ref_required": True,
            "reviewer_local_only_read_receipt_present_required": True,
            "reviewed_case_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
            "selection_row_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
            "body_free_required": True,
        },
        "sanitized_review_result_rows_expectation": {
            "row_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
            "row_source_ref_required": P7_R54_AHR_POST_EX18_ACTUAL_PERSON_LOCAL_ONLY_REVIEW_SOURCE_REF,
            "row_created_by_helper_allowed": False,
            "row_created_for_unit_test_allowed": False,
            "row_is_synthetic_contract_fixture_allowed": False,
            "historical_row_reused_allowed": False,
            "body_free_required": True,
        },
        "rating_rows_expectation": {
            "row_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
            "body_free_required": True,
        },
        "question_need_observation_rows_expectation": {
            "row_count_required": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
            "question_text_included": False,
            "draft_question_text_included": False,
            "body_free_required": True,
        },
        "disposal_receipt_expectation": {
            "body_removed_required": True,
            "body_hash_stored_allowed": False,
            "local_absolute_path_included_allowed": False,
            "reviewer_notes_body_stored_allowed": False,
            "body_free_required": True,
        },
    }


def build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
    *,
    return_to_actual_review_operation_plan: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN05 expected body-free actual review evidence intake bundle boundary."""

    mn04 = dict(return_to_actual_review_operation_plan or {}) if isinstance(return_to_actual_review_operation_plan, Mapping) else None
    if mn04 is None and return_to_actual_review_operation_plan is None:
        mn04 = build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(review_session_id=review_session_id)
    blockers = _mn05_blockers(mn04)
    ready = not blockers
    reason_refs = ["mn05_expected_bodyfree_evidence_intake_bundle_boundary_ready"] if ready else []
    false_flags = _false_flags()
    expectations = _mn05_expectation_maps()

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN05_EXPECTED_BODYFREE_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN05_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_20260630",
        "review_session_id": _safe_review_session_id(review_session_id or (mn04 or {}).get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn04_schema_version": (mn04 or {}).get("schema_version", ""),
        "mn04_material_ref": (mn04 or {}).get("material_id", ""),
        "mn04_status_ref": (mn04 or {}).get("mn04_status_ref", ""),
        "mn04_ready": (mn04 or {}).get("mn04_ready") is True,
        "mn04_next_required_step": (mn04 or {}).get("next_required_step", ""),
        "mn04_actual_operation_plan_ref": (mn04 or {}).get("actual_operation_plan_ref", ""),
        "mn04_required_bodyfree_artifact_refs": list((mn04 or {}).get("required_bodyfree_artifact_refs") or []),
        "mn04_forbidden_artifact_refs": list((mn04 or {}).get("forbidden_artifact_refs") or []),
        "mn05_status_ref": P7_R54_AHR_POST_EX18_MN05_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN05_BLOCKED_STATUS_REF,
        "mn05_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN05_ALLOWED_STATUS_REFS),
        "mn05_ready": ready,
        "mn05_blocker_refs": [] if ready else blockers,
        "mn05_blocker_ref_count": 0 if ready else len(blockers),
        "mn05_reason_refs": reason_refs,
        "mn05_reason_ref_count": len(reason_refs),
        "expected_actual_review_evidence_intake_bundle_ref": P7_R54_AHR_POST_EX18_EXPECTED_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_REF if ready else "",
        "expected_bundle_boundary_ref": P7_R54_AHR_POST_EX18_EXPECTED_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_REF if ready else "",
        "expected_bundle_template_only": True,
        "actual_review_evidence_intake_bundle_materialized_here": False,
        "expected_actual_source_ref": P7_R54_AHR_POST_EX18_ACTUAL_PERSON_LOCAL_ONLY_REVIEW_SOURCE_REF,
        "required_case_count": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "expected_reviewed_case_count": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "expected_sanitized_review_result_row_count": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "expected_rating_row_count": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "expected_question_need_observation_row_count": P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT,
        "expected_bundle_required_bodyfree_artifact_refs": list(P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS),
        "expected_bundle_required_bodyfree_artifact_ref_count": len(P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS),
        "expected_bundle_forbidden_artifact_refs": list(P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS),
        "expected_bundle_forbidden_artifact_ref_count": len(P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS),
        "expected_bundle_component_refs": list(P7_R54_AHR_POST_EX18_MN05_EXPECTED_BUNDLE_COMPONENT_REFS),
        "expected_bundle_component_ref_count": len(P7_R54_AHR_POST_EX18_MN05_EXPECTED_BUNDLE_COMPONENT_REFS),
        **expectations,
        "no_body_leak_validation_required": True,
        "no_question_text_validation_required": True,
        "no_path_hash_validation_required": True,
        "actual_review_evidence_not_completed_by_boundary": True,
        "actual_review_operation_not_run_by_boundary": True,
        "actual_rows_not_created_by_boundary": True,
        "question_text_not_created_by_boundary": True,
        "bodyfull_packet_not_generated_by_boundary": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN05_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN05_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN06_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN05_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN05_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN05 expected body-free evidence intake bundle boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN05_EXPECTED_BODYFREE_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN05_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN05 expected body-free evidence intake bundle boundary",
    )
    if tuple(data.get("mn05_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN05 allowed status refs changed")
    for field, count_field in (
        ("mn05_blocker_refs", "mn05_blocker_ref_count"),
        ("mn05_reason_refs", "mn05_reason_ref_count"),
        ("expected_bundle_required_bodyfree_artifact_refs", "expected_bundle_required_bodyfree_artifact_ref_count"),
        ("expected_bundle_forbidden_artifact_refs", "expected_bundle_forbidden_artifact_ref_count"),
        ("expected_bundle_component_refs", "expected_bundle_component_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN05 {count_field} changed")
    if tuple(data.get("expected_bundle_required_bodyfree_artifact_refs") or ()) != P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN05 expected required artifacts changed")
    if tuple(data.get("expected_bundle_forbidden_artifact_refs") or ()) != P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN05 expected forbidden artifacts changed")
    if tuple(data.get("expected_bundle_component_refs") or ()) != P7_R54_AHR_POST_EX18_MN05_EXPECTED_BUNDLE_COMPONENT_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN05 expected bundle components changed")
    for key in (
        "required_case_count",
        "expected_reviewed_case_count",
        "expected_sanitized_review_result_row_count",
        "expected_rating_row_count",
        "expected_question_need_observation_row_count",
    ):
        if data.get(key) != P7_R54_AHR_POST_EX18_REQUIRED_CASE_COUNT:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN05 expected count changed: {key}")
    for key in (
        "expected_bundle_template_only", "no_body_leak_validation_required",
        "no_question_text_validation_required", "no_path_hash_validation_required",
        "actual_review_evidence_not_completed_by_boundary", "actual_review_operation_not_run_by_boundary",
        "actual_rows_not_created_by_boundary", "question_text_not_created_by_boundary",
        "bodyfull_packet_not_generated_by_boundary",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN05 required true boundary changed: {key}")
    if data.get("actual_review_evidence_intake_bundle_materialized_here") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN05 cannot materialize actual evidence bundle here")
    expectations = _mn05_expectation_maps()
    for key, expected in expectations.items():
        if data.get(key) != expected:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN05 expectation map changed: {key}")
    ready = data.get("mn05_status_ref") == P7_R54_AHR_POST_EX18_MN05_READY_STATUS_REF
    if data.get("mn05_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN05 ready flag changed")
    if ready:
        if data.get("mn05_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 ready material cannot carry blockers")
        if data.get("mn05_reason_refs") != ["mn05_expected_bodyfree_evidence_intake_bundle_boundary_ready"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 ready reason changed")
        if data.get("mn04_ready") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 ready boundary requires ready MN04 plan")
        if tuple(data.get("mn04_required_bodyfree_artifact_refs") or ()) != P7_R54_AHR_POST_EX18_REQUIRED_BODYFREE_ARTIFACT_REFS:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 MN04 required artifacts changed")
        if tuple(data.get("mn04_forbidden_artifact_refs") or ()) != P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 MN04 forbidden artifacts changed")
        if data.get("expected_actual_review_evidence_intake_bundle_ref") != P7_R54_AHR_POST_EX18_EXPECTED_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 expected bundle ref changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 next step changed")
    else:
        if data.get("mn05_status_ref") != P7_R54_AHR_POST_EX18_MN05_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 blocked status changed")
        if not data.get("mn05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN05 blocked material must carry blockers")
        if data.get("mn05_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN05 blocked next step changed")
    return True

# Alias names for the detailed-design wording of MN00-MN05.
def build_p7_r54_ahr_post_ex18_manual_next_decision_scope_no_touch_no_promotion_boundary_freeze_bodyfree(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze(
        review_session_id=review_session_id
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_scope_no_touch_no_promotion_boundary_freeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_ex18_result_memo_bodyfree_envelope_intake_bodyfree(
    *,
    scope_no_touch_no_promotion_boundary_freeze: Mapping[str, Any] | None = None,
    ex18_result_memo_bodyfree_envelope: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_EX18_EX18_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake(
        scope_no_touch_no_promotion_boundary_freeze=scope_no_touch_no_promotion_boundary_freeze,
        ex18_result_memo_bodyfree_envelope=ex18_result_memo_bodyfree_envelope,
        result_memo_ref=result_memo_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_ex18_result_memo_bodyfree_envelope_intake_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract(data)



def build_p7_r54_ahr_post_ex18_manual_next_decision_actual_review_evidence_state_normalization_bodyfree(
    *,
    ex18_result_memo_bodyfree_envelope_intake: Mapping[str, Any] | None = None,
    actual_review_evidence_intake_bundle: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization(
        ex18_result_memo_bodyfree_envelope_intake=ex18_result_memo_bodyfree_envelope_intake,
        actual_review_evidence_intake_bundle=actual_review_evidence_intake_bundle,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_actual_review_evidence_state_normalization_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_classifier_bodyfree(
    *,
    actual_review_evidence_state_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier(
        actual_review_evidence_state_normalization=actual_review_evidence_state_normalization,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_classifier_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_plan_bodyfree(
    *,
    manual_decision_classifier: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan(
        manual_decision_classifier=manual_decision_classifier,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_plan_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_expected_bodyfree_evidence_intake_bundle_boundary_bodyfree(
    *,
    return_to_actual_review_operation_plan: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
        return_to_actual_review_operation_plan=return_to_actual_review_operation_plan,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_expected_bodyfree_evidence_intake_bundle_boundary_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract(data)

# MN06-MN07 continue the Post-EX18 manual next-decision line without changing
# API/DB/RN/runtime contracts and without creating body-full or question text.
P7_R54_AHR_POST_EX18_MN06_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn06_no_body_no_question_no_path_no_hash_scan.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_MATERIALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn07_downstream_no_promotion_boundary_materialization.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn06_no_body_no_question_no_path_no_hash_scan_or_stop"
)
P7_R54_AHR_POST_EX18_MN07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn07_downstream_no_promotion_boundary_materialization_or_stop"
)
P7_R54_AHR_POST_EX18_MN06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:7]
P7_R54_AHR_POST_EX18_MN06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[7:]
P7_R54_AHR_POST_EX18_MN07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:8]
P7_R54_AHR_POST_EX18_MN07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[8:]
P7_R54_AHR_POST_EX18_MN06_READY_STATUS_REF: Final = (
    "MN06_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_SCAN_PASSED_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN06_BLOCKED_STATUS_REF: Final = (
    "MN06_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_SCAN_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN06_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN06_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN07_READY_STATUS_REF: Final = (
    "MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_MATERIALIZED_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN07_BLOCKED_STATUS_REF: Final = (
    "MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_MATERIALIZATION_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN07_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN07_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN06_SCAN_TARGET_REFS: Final[tuple[str, ...]] = (
    "manual_decision_material_bodyfree_key_paths",
    "return_to_actual_review_operation_plan_bodyfree_key_paths",
    "expected_bodyfree_evidence_intake_bundle_boundary_key_paths",
    "additional_bodyfree_material_key_paths",
)
P7_R54_AHR_POST_EX18_MN06_SCAN_SCOPE_REFS: Final[tuple[str, ...]] = (
    "scan_key_paths_only",
    "do_not_copy_payload_values",
    "reject_body_or_review_body_keys",
    "reject_question_text_keys",
    "reject_local_path_keys",
    "reject_body_hash_keys",
    "reject_terminal_output_keys",
    "fail_closed_on_detected_forbidden_key_path",
)
P7_R54_AHR_POST_EX18_MN06_FORBIDDEN_PAYLOAD_KEY_CATALOG_REFS: Final[tuple[str, ...]] = tuple(
    sorted(set(P7_R54_AHR_POST_EX18_FORBIDDEN_PAYLOAD_KEY_REFS) | {"returned_body"})
)
P7_R54_AHR_POST_EX18_MN06_BODY_FORBIDDEN_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_input", "input_body", "raw_body", "current_input_body", "returned_body",
        "returned_emlis_body", "emlis_body", "history_body", "history_surface",
        "comment_text", "comment_text_body", "reviewer_free_text", "reviewer_note",
        "reviewer_notes_body", "packet_content", "body_full_packet_content",
    }
)
P7_R54_AHR_POST_EX18_MN06_QUESTION_FORBIDDEN_KEY_REFS: Final[frozenset[str]] = frozenset(
    {"question_text", "draft_question_text", "question_body", "answer_body"}
)
P7_R54_AHR_POST_EX18_MN06_PATH_FORBIDDEN_KEY_REFS: Final[frozenset[str]] = frozenset(
    {"local_path", "absolute_path", "file_path", "local_absolute_path"}
)
P7_R54_AHR_POST_EX18_MN06_HASH_FORBIDDEN_KEY_REFS: Final[frozenset[str]] = frozenset(
    {"body_hash", "content_hash_of_body"}
)
P7_R54_AHR_POST_EX18_MN06_TERMINAL_FORBIDDEN_KEY_REFS: Final[frozenset[str]] = frozenset(
    {"terminal_output", "terminal_output_body", "stdout", "stderr", "traceback"}
)
P7_R54_AHR_POST_EX18_MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_REF: Final = (
    "post_ex18_downstream_no_promotion_boundary_materialized_bodyfree_v1"
)
P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS: Final[tuple[str, ...]] = (
    "next_decision_auto_execution_allowed",
    "manual_decision_auto_executes_downstream",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "p8_question_api_created",
    "p8_question_db_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "p8_start_allowed",
    "r52_reintake_execution_allowed_here",
    "r52_reintake_execution_started_here",
    "r52_reintake_execution_completed_here",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "r52_actual_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green",
    "full_backend_suite_green_confirmed",
    "rn_contract_green",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_EX18_MN07_BLOCKED_DOWNSTREAM_REFS: Final[tuple[str, ...]] = (
    "p5_final",
    "p6_start",
    "p8_start",
    "r52_actual_execution",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green",
    "rn_contract_green",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_POST_EX18_MN06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn05_schema_version", "mn05_material_ref", "mn05_status_ref", "mn05_ready",
    "mn05_next_required_step", "expected_evidence_intake_bundle_boundary_ref",
    "mn06_status_ref", "mn06_allowed_status_refs", "mn06_ready", "mn06_blocker_refs",
    "mn06_blocker_ref_count", "mn06_reason_refs", "mn06_reason_ref_count",
    "scan_target_refs", "scan_target_ref_count", "scan_scope_refs", "scan_scope_ref_count",
    "scanned_material_refs", "scanned_material_ref_count", "forbidden_payload_key_catalog_refs",
    "forbidden_payload_key_catalog_ref_count", "detected_forbidden_payload_key_refs",
    "detected_forbidden_payload_key_ref_count", "detected_forbidden_payload_key_path_refs",
    "detected_forbidden_payload_key_path_ref_count", "body_forbidden_key_path_refs",
    "body_forbidden_key_path_ref_count", "question_forbidden_key_path_refs",
    "question_forbidden_key_path_ref_count", "path_forbidden_key_path_refs",
    "path_forbidden_key_path_ref_count", "hash_forbidden_key_path_refs",
    "hash_forbidden_key_path_ref_count", "terminal_forbidden_key_path_refs",
    "terminal_forbidden_key_path_ref_count", "no_body_payload_key_detected",
    "no_question_payload_key_detected", "no_local_path_payload_key_detected",
    "no_hash_payload_key_detected", "no_terminal_output_payload_key_detected",
    "no_body_no_question_no_path_no_hash_scan_passed", "no_payload_value_copied_to_scan_result",
    "scan_reports_key_paths_only", "body_hash_not_stored_as_safe_substitute",
    "local_path_not_stored_as_safe_substitute", "question_text_not_materialized_by_scan",
    "actual_review_evidence_not_completed_by_scan", "actual_review_operation_not_run_by_scan",
    "actual_rows_not_created_by_scan", "next_decision_auto_execution_allowed",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "local_received_zip_refs",
    "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs",
    "claim_boundary_ref_count", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_ex18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_EX18_MN07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn06_schema_version", "mn06_material_ref", "mn06_status_ref", "mn06_ready",
    "mn06_next_required_step", "mn06_scan_passed", "mn06_forbidden_payload_key_path_ref_count",
    "mn07_status_ref", "mn07_allowed_status_refs", "mn07_ready", "mn07_blocker_refs",
    "mn07_blocker_ref_count", "mn07_reason_refs", "mn07_reason_ref_count",
    "downstream_no_promotion_boundary_ref", "downstream_no_promotion_boundary",
    "downstream_no_promotion_boundary_materialized", "downstream_no_promotion_flag_refs",
    "downstream_no_promotion_flag_ref_count", "blocked_downstream_refs",
    "blocked_downstream_ref_count", "promotion_claim_refs", "promotion_claim_ref_count",
    "next_decision_auto_execution_allowed", "no_promotion_boundary_confirmed",
    "p5_p6_p8_r52_release_auto_execution_blocked",
    "mn07_does_not_start_p8_p6_r52_p5_or_release",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "r52_handoff_candidate_is_not_r52_actual_execution",
    "p5_confirmed_candidate_is_not_p5_final",
    "selected_regression_green_is_not_full_backend_suite_green",
    "rn_contract_green_is_not_rn_real_device_modal_verified",
    "actual_review_evidence_missing_keeps_downstream_hold",
    "actual_review_operation_plan_does_not_execute_downstream",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "local_received_zip_refs",
    "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs",
    "claim_boundary_ref_count", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_ex18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _mn06_material_ref(material: Mapping[str, Any], *, fallback: str) -> str:
    return _clean_ref(
        material.get("material_id") or material.get("operation_step_ref") or fallback,
        default=fallback,
        max_length=220,
    )


def _mn06_forbidden_payload_key_path_items(value: Any, *, path: str = "payload") -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            text_key = str(key)
            child_path = f"{path}.{text_key}"
            if text_key in P7_R54_AHR_POST_EX18_MN06_FORBIDDEN_PAYLOAD_KEY_CATALOG_REFS:
                items.append((text_key, child_path))
            items.extend(_mn06_forbidden_payload_key_path_items(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            items.extend(_mn06_forbidden_payload_key_path_items(child, path=f"{path}[{index}]"))
    return items


def _mn06_append_scan_target(
    targets: list[tuple[str, Mapping[str, Any]]],
    material: Mapping[str, Any] | None,
    *,
    fallback: str,
) -> None:
    if isinstance(material, Mapping):
        targets.append((_mn06_material_ref(material, fallback=fallback), material))


def _mn06_extend_additional_scan_targets(
    targets: list[tuple[str, Mapping[str, Any]]],
    value: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
) -> None:
    if isinstance(value, Mapping):
        targets.append((_mn06_material_ref(value, fallback="additional_bodyfree_scan_target_1"), value))
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value, start=1):
            if isinstance(item, Mapping):
                targets.append((_mn06_material_ref(item, fallback=f"additional_bodyfree_scan_target_{index}"), item))


def _mn06_paths_for_keys(items: Sequence[tuple[str, str]], keys: frozenset[str]) -> list[str]:
    return _dedupe_refs([path for key, path in items if key in keys])


def _mn06_blockers(expected_bundle_boundary: Mapping[str, Any] | None, detected_items: Sequence[tuple[str, str]]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(expected_bundle_boundary, Mapping):
        blockers.append("mn05_expected_bodyfree_evidence_intake_bundle_boundary_missing")
    else:
        try:
            assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract(
                expected_bundle_boundary
            )
        except Exception:
            blockers.append("mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract_invalid")
        if expected_bundle_boundary.get("mn05_ready") is not True:
            blockers.append("mn05_expected_bodyfree_evidence_intake_bundle_boundary_not_ready")
        if expected_bundle_boundary.get("next_required_step") != P7_R54_AHR_POST_EX18_MN06_STEP_REF:
            blockers.append("mn05_next_required_step_not_mn06")
    if detected_items:
        blockers.append("mn06_forbidden_body_question_path_hash_or_terminal_key_detected")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
    *,
    expected_bodyfree_evidence_intake_bundle_boundary: Mapping[str, Any] | None = None,
    manual_decision_material: Mapping[str, Any] | None = None,
    return_to_actual_review_operation_plan: Mapping[str, Any] | None = None,
    additional_bodyfree_scan_targets: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN06 body-free key-path scan material without copying payload values."""
    session_id = _safe_review_session_id(review_session_id)
    mn05 = expected_bodyfree_evidence_intake_bundle_boundary
    if mn05 is None:
        mn05 = build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary(
            review_session_id=session_id
        )

    scan_targets: list[tuple[str, Mapping[str, Any]]] = []
    _mn06_append_scan_target(scan_targets, manual_decision_material, fallback="manual_decision_material_ref")
    _mn06_append_scan_target(scan_targets, return_to_actual_review_operation_plan, fallback="return_operation_plan_ref")
    _mn06_append_scan_target(scan_targets, mn05 if isinstance(mn05, Mapping) else None, fallback="mn05_expected_bodyfree_evidence_intake_bundle_boundary")
    _mn06_extend_additional_scan_targets(scan_targets, additional_bodyfree_scan_targets)

    detected_items: list[tuple[str, str]] = []
    for material_ref, material in scan_targets:
        detected_items.extend(
            _mn06_forbidden_payload_key_path_items(material, path=f"mn06_scan_target[{material_ref}]")
        )
    detected_keys = _dedupe_refs([key for key, _ in detected_items])
    detected_paths = _dedupe_refs([path for _, path in detected_items])
    body_paths = _mn06_paths_for_keys(detected_items, P7_R54_AHR_POST_EX18_MN06_BODY_FORBIDDEN_KEY_REFS)
    question_paths = _mn06_paths_for_keys(detected_items, P7_R54_AHR_POST_EX18_MN06_QUESTION_FORBIDDEN_KEY_REFS)
    path_paths = _mn06_paths_for_keys(detected_items, P7_R54_AHR_POST_EX18_MN06_PATH_FORBIDDEN_KEY_REFS)
    hash_paths = _mn06_paths_for_keys(detected_items, P7_R54_AHR_POST_EX18_MN06_HASH_FORBIDDEN_KEY_REFS)
    terminal_paths = _mn06_paths_for_keys(detected_items, P7_R54_AHR_POST_EX18_MN06_TERMINAL_FORBIDDEN_KEY_REFS)
    blockers = _mn06_blockers(mn05, detected_items)
    ready = not blockers
    false_flags = _false_flags()

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN06_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN06_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn05_schema_version": _clean_ref(mn05.get("schema_version") if isinstance(mn05, Mapping) else "", default="mn05_schema_unknown", max_length=220),
        "mn05_material_ref": _clean_ref(mn05.get("material_id") if isinstance(mn05, Mapping) else "", default="mn05_material_missing", max_length=220),
        "mn05_status_ref": _clean_ref(mn05.get("mn05_status_ref") if isinstance(mn05, Mapping) else "", default="mn05_status_missing", max_length=180),
        "mn05_ready": bool(isinstance(mn05, Mapping) and mn05.get("mn05_ready") is True),
        "mn05_next_required_step": _clean_ref(mn05.get("next_required_step") if isinstance(mn05, Mapping) else "", default="mn05_next_required_step_missing", max_length=220),
        "expected_evidence_intake_bundle_boundary_ref": _clean_ref(
            mn05.get("expected_actual_review_evidence_intake_bundle_ref") if isinstance(mn05, Mapping) else "",
            default=P7_R54_AHR_POST_EX18_EXPECTED_EVIDENCE_INTAKE_BUNDLE_BOUNDARY_REF,
            max_length=220,
        ),
        "mn06_status_ref": P7_R54_AHR_POST_EX18_MN06_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN06_BLOCKED_STATUS_REF,
        "mn06_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN06_ALLOWED_STATUS_REFS),
        "mn06_ready": ready,
        "mn06_blocker_refs": blockers,
        "mn06_blocker_ref_count": len(blockers),
        "mn06_reason_refs": ["mn06_no_body_no_question_no_path_no_hash_scan_passed"] if ready else [],
        "mn06_reason_ref_count": 1 if ready else 0,
        "scan_target_refs": list(P7_R54_AHR_POST_EX18_MN06_SCAN_TARGET_REFS),
        "scan_target_ref_count": len(P7_R54_AHR_POST_EX18_MN06_SCAN_TARGET_REFS),
        "scan_scope_refs": list(P7_R54_AHR_POST_EX18_MN06_SCAN_SCOPE_REFS),
        "scan_scope_ref_count": len(P7_R54_AHR_POST_EX18_MN06_SCAN_SCOPE_REFS),
        "scanned_material_refs": [material_ref for material_ref, _ in scan_targets],
        "scanned_material_ref_count": len(scan_targets),
        "forbidden_payload_key_catalog_refs": list(P7_R54_AHR_POST_EX18_MN06_FORBIDDEN_PAYLOAD_KEY_CATALOG_REFS),
        "forbidden_payload_key_catalog_ref_count": len(P7_R54_AHR_POST_EX18_MN06_FORBIDDEN_PAYLOAD_KEY_CATALOG_REFS),
        "detected_forbidden_payload_key_refs": detected_keys,
        "detected_forbidden_payload_key_ref_count": len(detected_keys),
        "detected_forbidden_payload_key_path_refs": detected_paths,
        "detected_forbidden_payload_key_path_ref_count": len(detected_paths),
        "body_forbidden_key_path_refs": body_paths,
        "body_forbidden_key_path_ref_count": len(body_paths),
        "question_forbidden_key_path_refs": question_paths,
        "question_forbidden_key_path_ref_count": len(question_paths),
        "path_forbidden_key_path_refs": path_paths,
        "path_forbidden_key_path_ref_count": len(path_paths),
        "hash_forbidden_key_path_refs": hash_paths,
        "hash_forbidden_key_path_ref_count": len(hash_paths),
        "terminal_forbidden_key_path_refs": terminal_paths,
        "terminal_forbidden_key_path_ref_count": len(terminal_paths),
        "no_body_payload_key_detected": not body_paths,
        "no_question_payload_key_detected": not question_paths,
        "no_local_path_payload_key_detected": not path_paths,
        "no_hash_payload_key_detected": not hash_paths,
        "no_terminal_output_payload_key_detected": not terminal_paths,
        "no_body_no_question_no_path_no_hash_scan_passed": ready,
        "no_payload_value_copied_to_scan_result": True,
        "scan_reports_key_paths_only": True,
        "body_hash_not_stored_as_safe_substitute": True,
        "local_path_not_stored_as_safe_substitute": True,
        "question_text_not_materialized_by_scan": True,
        "actual_review_evidence_not_completed_by_scan": True,
        "actual_review_operation_not_run_by_scan": True,
        "actual_rows_not_created_by_scan": True,
        "next_decision_auto_execution_allowed": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN06_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN06_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN07_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN06_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN06 no-body/no-question/no-path/no-hash scan",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN06_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_SCAN_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN06_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN06 no-body/no-question/no-path/no-hash scan",
    )
    if tuple(data.get("mn06_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN06 allowed status refs changed")
    for field, count_field in (
        ("mn06_blocker_refs", "mn06_blocker_ref_count"),
        ("mn06_reason_refs", "mn06_reason_ref_count"),
        ("scan_target_refs", "scan_target_ref_count"),
        ("scan_scope_refs", "scan_scope_ref_count"),
        ("scanned_material_refs", "scanned_material_ref_count"),
        ("forbidden_payload_key_catalog_refs", "forbidden_payload_key_catalog_ref_count"),
        ("detected_forbidden_payload_key_refs", "detected_forbidden_payload_key_ref_count"),
        ("detected_forbidden_payload_key_path_refs", "detected_forbidden_payload_key_path_ref_count"),
        ("body_forbidden_key_path_refs", "body_forbidden_key_path_ref_count"),
        ("question_forbidden_key_path_refs", "question_forbidden_key_path_ref_count"),
        ("path_forbidden_key_path_refs", "path_forbidden_key_path_ref_count"),
        ("hash_forbidden_key_path_refs", "hash_forbidden_key_path_ref_count"),
        ("terminal_forbidden_key_path_refs", "terminal_forbidden_key_path_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN06 {count_field} changed")
    if tuple(data.get("scan_target_refs") or ()) != P7_R54_AHR_POST_EX18_MN06_SCAN_TARGET_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN06 scan target refs changed")
    if tuple(data.get("scan_scope_refs") or ()) != P7_R54_AHR_POST_EX18_MN06_SCAN_SCOPE_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN06 scan scope refs changed")
    if tuple(data.get("forbidden_payload_key_catalog_refs") or ()) != P7_R54_AHR_POST_EX18_MN06_FORBIDDEN_PAYLOAD_KEY_CATALOG_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN06 forbidden payload key catalog changed")
    for key in (
        "no_payload_value_copied_to_scan_result", "scan_reports_key_paths_only",
        "body_hash_not_stored_as_safe_substitute", "local_path_not_stored_as_safe_substitute",
        "question_text_not_materialized_by_scan", "actual_review_evidence_not_completed_by_scan",
        "actual_review_operation_not_run_by_scan", "actual_rows_not_created_by_scan",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN06 required true boundary changed: {key}")
    if data.get("next_decision_auto_execution_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN06 cannot allow auto execution")
    if data.get("no_body_payload_key_detected") is not (data.get("body_forbidden_key_path_ref_count") == 0):
        raise ValueError("P7-R54-AHR-PostEX18-MN06 body detection flag changed")
    if data.get("no_question_payload_key_detected") is not (data.get("question_forbidden_key_path_ref_count") == 0):
        raise ValueError("P7-R54-AHR-PostEX18-MN06 question detection flag changed")
    if data.get("no_local_path_payload_key_detected") is not (data.get("path_forbidden_key_path_ref_count") == 0):
        raise ValueError("P7-R54-AHR-PostEX18-MN06 path detection flag changed")
    if data.get("no_hash_payload_key_detected") is not (data.get("hash_forbidden_key_path_ref_count") == 0):
        raise ValueError("P7-R54-AHR-PostEX18-MN06 hash detection flag changed")
    if data.get("no_terminal_output_payload_key_detected") is not (data.get("terminal_forbidden_key_path_ref_count") == 0):
        raise ValueError("P7-R54-AHR-PostEX18-MN06 terminal detection flag changed")
    ready = data.get("mn06_status_ref") == P7_R54_AHR_POST_EX18_MN06_READY_STATUS_REF
    if data.get("mn06_ready") is not ready or data.get("no_body_no_question_no_path_no_hash_scan_passed") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN06 ready flag changed")
    if ready:
        if data.get("mn06_blocker_refs") != [] or data.get("detected_forbidden_payload_key_path_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 ready material cannot carry blockers or forbidden paths")
        if data.get("mn06_reason_refs") != ["mn06_no_body_no_question_no_path_no_hash_scan_passed"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 ready reason changed")
        if data.get("mn05_ready") is not True or data.get("mn05_next_required_step") != P7_R54_AHR_POST_EX18_MN06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 ready material requires a ready MN05 boundary")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN06_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 next step changed")
    else:
        if data.get("mn06_status_ref") != P7_R54_AHR_POST_EX18_MN06_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 blocked status changed")
        if not data.get("mn06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN06 blocked material must carry blockers")
        if data.get("mn06_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN06 blocked next step changed")
    return True


def _mn07_downstream_no_promotion_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS}


def _mn07_promotion_claim_refs(value: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    claims: list[str] = []
    for key in P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS:
        if value.get(key) is True:
            claims.append(key)
    return _dedupe_refs(claims)


def _mn07_blockers(scan: Mapping[str, Any] | None, promotion_claim_refs: Sequence[str]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(scan, Mapping):
        blockers.append("mn06_no_body_no_question_no_path_no_hash_scan_missing")
    else:
        try:
            assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract(scan)
        except Exception:
            blockers.append("mn06_no_body_no_question_no_path_no_hash_scan_contract_invalid")
        if scan.get("mn06_ready") is not True:
            blockers.append("mn06_no_body_no_question_no_path_no_hash_scan_not_ready")
        if scan.get("no_body_no_question_no_path_no_hash_scan_passed") is not True:
            blockers.append("mn06_no_body_no_question_no_path_no_hash_scan_not_passed")
        if scan.get("next_required_step") != P7_R54_AHR_POST_EX18_MN07_STEP_REF:
            blockers.append("mn06_next_required_step_not_mn07")
    if promotion_claim_refs:
        blockers.append("mn07_downstream_promotion_claim_detected")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
    *,
    no_body_no_question_no_path_no_hash_scan: Mapping[str, Any] | None = None,
    downstream_promotion_claims: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN07 body-free downstream no-promotion boundary material."""
    session_id = _safe_review_session_id(review_session_id)
    scan = no_body_no_question_no_path_no_hash_scan
    if scan is None:
        scan = build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(review_session_id=session_id)
    promotion_claim_refs = _mn07_promotion_claim_refs(scan) + _mn07_promotion_claim_refs(downstream_promotion_claims)
    promotion_claim_refs = _dedupe_refs(promotion_claim_refs)
    blockers = _mn07_blockers(scan, promotion_claim_refs)
    ready = not blockers
    false_flags = _false_flags()
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_MATERIALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN07_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn06_schema_version": _clean_ref(scan.get("schema_version") if isinstance(scan, Mapping) else "", default="mn06_schema_missing", max_length=220),
        "mn06_material_ref": _clean_ref(scan.get("material_id") if isinstance(scan, Mapping) else "", default="mn06_material_missing", max_length=220),
        "mn06_status_ref": _clean_ref(scan.get("mn06_status_ref") if isinstance(scan, Mapping) else "", default="mn06_status_missing", max_length=180),
        "mn06_ready": bool(isinstance(scan, Mapping) and scan.get("mn06_ready") is True),
        "mn06_next_required_step": _clean_ref(scan.get("next_required_step") if isinstance(scan, Mapping) else "", default="mn06_next_required_step_missing", max_length=220),
        "mn06_scan_passed": bool(isinstance(scan, Mapping) and scan.get("no_body_no_question_no_path_no_hash_scan_passed") is True),
        "mn06_forbidden_payload_key_path_ref_count": int(scan.get("detected_forbidden_payload_key_path_ref_count", 0)) if isinstance(scan, Mapping) else 0,
        "mn07_status_ref": P7_R54_AHR_POST_EX18_MN07_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN07_BLOCKED_STATUS_REF,
        "mn07_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN07_ALLOWED_STATUS_REFS),
        "mn07_ready": ready,
        "mn07_blocker_refs": blockers,
        "mn07_blocker_ref_count": len(blockers),
        "mn07_reason_refs": ["mn07_downstream_no_promotion_boundary_materialized_bodyfree"] if ready else [],
        "mn07_reason_ref_count": 1 if ready else 0,
        "downstream_no_promotion_boundary_ref": P7_R54_AHR_POST_EX18_MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_REF,
        "downstream_no_promotion_boundary": _mn07_downstream_no_promotion_boundary(),
        "downstream_no_promotion_boundary_materialized": ready,
        "downstream_no_promotion_flag_refs": list(P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS),
        "downstream_no_promotion_flag_ref_count": len(P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS),
        "blocked_downstream_refs": list(P7_R54_AHR_POST_EX18_MN07_BLOCKED_DOWNSTREAM_REFS),
        "blocked_downstream_ref_count": len(P7_R54_AHR_POST_EX18_MN07_BLOCKED_DOWNSTREAM_REFS),
        "promotion_claim_refs": promotion_claim_refs,
        "promotion_claim_ref_count": len(promotion_claim_refs),
        "next_decision_auto_execution_allowed": False,
        "no_promotion_boundary_confirmed": ready,
        "p5_p6_p8_r52_release_auto_execution_blocked": True,
        "mn07_does_not_start_p8_p6_r52_p5_or_release": True,
        "p8_material_candidate_only_is_not_p8_start_allowed": True,
        "r52_handoff_candidate_is_not_r52_actual_execution": True,
        "p5_confirmed_candidate_is_not_p5_final": True,
        "selected_regression_green_is_not_full_backend_suite_green": True,
        "rn_contract_green_is_not_rn_real_device_modal_verified": True,
        "actual_review_evidence_missing_keeps_downstream_hold": True,
        "actual_review_operation_plan_does_not_execute_downstream": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN07_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN07_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN08_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN07_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN07 downstream no-promotion boundary materialization",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_MATERIALIZATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN07_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN07 downstream no-promotion boundary materialization",
    )
    if tuple(data.get("mn07_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN07 allowed status refs changed")
    for field, count_field in (
        ("mn07_blocker_refs", "mn07_blocker_ref_count"),
        ("mn07_reason_refs", "mn07_reason_ref_count"),
        ("downstream_no_promotion_flag_refs", "downstream_no_promotion_flag_ref_count"),
        ("blocked_downstream_refs", "blocked_downstream_ref_count"),
        ("promotion_claim_refs", "promotion_claim_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN07 {count_field} changed")
    if tuple(data.get("downstream_no_promotion_flag_refs") or ()) != P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN07 no-promotion flag refs changed")
    if tuple(data.get("blocked_downstream_refs") or ()) != P7_R54_AHR_POST_EX18_MN07_BLOCKED_DOWNSTREAM_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN07 blocked downstream refs changed")
    if data.get("downstream_no_promotion_boundary_ref") != P7_R54_AHR_POST_EX18_MN07_DOWNSTREAM_NO_PROMOTION_BOUNDARY_REF:
        raise ValueError("P7-R54-AHR-PostEX18-MN07 boundary ref changed")
    boundary = data.get("downstream_no_promotion_boundary")
    if not isinstance(boundary, Mapping) or dict(boundary) != _mn07_downstream_no_promotion_boundary():
        raise ValueError("P7-R54-AHR-PostEX18-MN07 downstream no-promotion boundary changed")
    for key in P7_R54_AHR_POST_EX18_MN07_NO_PROMOTION_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN07 promoted downstream flag changed: {key}")
    for key in (
        "p5_p6_p8_r52_release_auto_execution_blocked",
        "mn07_does_not_start_p8_p6_r52_p5_or_release",
        "p8_material_candidate_only_is_not_p8_start_allowed",
        "r52_handoff_candidate_is_not_r52_actual_execution",
        "p5_confirmed_candidate_is_not_p5_final",
        "selected_regression_green_is_not_full_backend_suite_green",
        "rn_contract_green_is_not_rn_real_device_modal_verified",
        "actual_review_evidence_missing_keeps_downstream_hold",
        "actual_review_operation_plan_does_not_execute_downstream",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN07 required true boundary changed: {key}")
    ready = data.get("mn07_status_ref") == P7_R54_AHR_POST_EX18_MN07_READY_STATUS_REF
    if data.get("mn07_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN07 ready flag changed")
    if ready:
        if data.get("mn07_blocker_refs") != [] or data.get("promotion_claim_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 ready material cannot carry blockers or promotion claims")
        if data.get("mn07_reason_refs") != ["mn07_downstream_no_promotion_boundary_materialized_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 ready reason changed")
        if data.get("mn06_ready") is not True or data.get("mn06_scan_passed") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 ready material requires a clean MN06 scan")
        if data.get("downstream_no_promotion_boundary_materialized") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 ready material must materialize no-promotion boundary")
        if data.get("no_promotion_boundary_confirmed") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 ready material must confirm no-promotion boundary")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN07_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 next step changed")
    else:
        if data.get("mn07_status_ref") != P7_R54_AHR_POST_EX18_MN07_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 blocked status changed")
        if not data.get("mn07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN07 blocked material must carry blockers")
        if data.get("mn07_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 blocked material cannot carry ready reasons")
        if data.get("downstream_no_promotion_boundary_materialized") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 blocked material cannot materialize no-promotion boundary")
        if data.get("no_promotion_boundary_confirmed") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 blocked material cannot confirm no-promotion boundary")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN07 blocked next step changed")
    return True


def build_p7_r54_ahr_post_ex18_manual_next_decision_no_body_no_question_no_path_no_hash_scan_bodyfree(
    *,
    expected_bodyfree_evidence_intake_bundle_boundary: Mapping[str, Any] | None = None,
    manual_decision_material: Mapping[str, Any] | None = None,
    return_to_actual_review_operation_plan: Mapping[str, Any] | None = None,
    additional_bodyfree_scan_targets: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan(
        expected_bodyfree_evidence_intake_bundle_boundary=expected_bodyfree_evidence_intake_bundle_boundary,
        manual_decision_material=manual_decision_material,
        return_to_actual_review_operation_plan=return_to_actual_review_operation_plan,
        additional_bodyfree_scan_targets=additional_bodyfree_scan_targets,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_no_body_no_question_no_path_no_hash_scan_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_downstream_no_promotion_boundary_materialization_bodyfree(
    *,
    no_body_no_question_no_path_no_hash_scan: Mapping[str, Any] | None = None,
    downstream_promotion_claims: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(
        no_body_no_question_no_path_no_hash_scan=no_body_no_question_no_path_no_hash_scan,
        downstream_promotion_claims=downstream_promotion_claims,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_downstream_no_promotion_boundary_materialization_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(data)



# ---------------------------------------------------------------------------
# MN08-MN09 re-entry mapping / validation matrix / result memo envelope
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_EX18_MN08_REENTRY_MAPPING_TO_EXISTING_POSTCR22_EX07_EX18_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn08_reentry_mapping_to_existing_postcr22_ex07_ex18.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn09_validation_command_matrix_result_memo_envelope.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_or_stop"
)
P7_R54_AHR_POST_EX18_MN09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn09_validation_command_matrix_result_memo_envelope_or_stop"
)
P7_R54_AHR_POST_EX18_MN08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:9]
P7_R54_AHR_POST_EX18_MN08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[9:]
P7_R54_AHR_POST_EX18_MN09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:10]
P7_R54_AHR_POST_EX18_MN09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[10:]
P7_R54_AHR_POST_EX18_MN08_READY_STATUS_REF: Final = (
    "MN08_REENTRY_MAPPING_TO_EXISTING_POSTCR22_EX07_EX18_READY_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN08_BLOCKED_STATUS_REF: Final = (
    "MN08_REENTRY_MAPPING_TO_EXISTING_POSTCR22_EX07_EX18_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN08_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN08_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN09_READY_STATUS_REF: Final = (
    "MN09_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_READY_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN09_BLOCKED_STATUS_REF: Final = (
    "MN09_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN09_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN09_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN09_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN08_REENTRY_MAPPING_REF: Final = (
    "post_ex18_reentry_mapping_to_existing_postcr22_ex07_ex18_bodyfree_v1"
)
P7_R54_AHR_POST_EX18_MN08_REENTRY_SOURCE_REF: Final = (
    "future_actual_review_evidence_intake_bundle_after_real_review_only"
)
P7_R54_AHR_POST_EX18_MN08_EXISTING_POSTCR22_REENTRY_STEP_REFS: Final[tuple[str, ...]] = (
    ex.P7_R54_AHR_POST_CR22_EX07_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX08_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX09_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX10_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX11_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX12_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX13_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX14_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX15_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX16_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX17_STEP_REF,
    ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF,
)
P7_R54_AHR_POST_EX18_MN08_REENTRY_ARTIFACT_REFS: Final[tuple[str, ...]] = (
    "actual_operation_receipt_ref",
    "actual_selection_rows_provenance_ref",
    "sanitized_review_result_rows_ref",
    "rating_rows_ref",
    "blocker_classification_ref",
    "question_need_observation_rows_ref",
    "rating_question_consistency_ref",
    "disposal_purge_receipt_ref",
    "final_no_leak_validation_ref",
    "actual_review_evidence_complete_predicate_ref",
    "candidate_only_separation_ref",
    "validation_result_memo_next_hold_ref",
)
P7_R54_AHR_POST_EX18_MN08_REENTRY_ROLE_REFS: Final[tuple[str, ...]] = (
    "intake_actual_operation_receipt_after_real_review",
    "guard_actual_selection_rows_provenance_after_real_review",
    "intake_sanitized_review_result_rows_after_real_review",
    "normalize_rating_rows_after_real_review",
    "classify_readfeel_p5_p4_blockers_after_real_review",
    "normalize_question_need_observation_rows_after_real_review",
    "guard_rating_question_consistency_after_real_review",
    "intake_disposal_purge_receipt_after_real_review",
    "run_final_no_leak_validation_after_real_review",
    "evaluate_actual_review_evidence_complete_predicate_after_real_review",
    "separate_p5_p6_p8_r52_candidate_only_after_real_review",
    "prepare_validation_result_memo_next_hold_after_real_review",
)
P7_R54_AHR_POST_EX18_MN08_FORBIDDEN_REENTRY_CLAIM_REFS: Final[tuple[str, ...]] = (
    "reentry_mapping_claims_actual_review_execution",
    "reentry_mapping_claims_actual_rows_created",
    "reentry_mapping_claims_r52_actual_execution",
    "reentry_mapping_claims_p8_start",
    "reentry_mapping_claims_p5_final",
    "reentry_mapping_claims_p7_complete",
    "reentry_mapping_claims_release_allowed",
    "post_ex18_helper_reimplements_postcr22_ex08_ex18",
)
P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostEX18_ManualNextDecision_ReturnToActualReviewOperation_MN08_MN09_Result_20260630.md"
)
P7_R54_AHR_POST_EX18_MN09_COMMAND_STATUS_DECLARED_NOT_RUN_REF: Final = (
    "declared_not_run_by_helper_result_memo_will_record_actual_run_separately"
)
P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_REFS: Final[tuple[str, ...]] = (
    "mn08_mn09_target_postex18_manual_next_decision_tests",
    "mn00_mn09_postex18_manual_next_decision_combined_target_tests",
    "mn09_postcr22_ex18_regression",
    "mn09_postcr22_ex00_ex18_combined_regression",
    "mn09_compileall_ai_services_ai_inference_ai_tests",
)
P7_R54_AHR_POST_EX18_MN09_TARGET_TEST_COMMAND_REFS: Final[tuple[str, ...]] = (
    "mn08_mn09_target_postex18_manual_next_decision_tests",
    "mn00_mn09_postex18_manual_next_decision_combined_target_tests",
)
P7_R54_AHR_POST_EX18_MN09_SELECTED_REGRESSION_COMMAND_REFS: Final[tuple[str, ...]] = (
    "mn09_postcr22_ex18_regression",
    "mn09_postcr22_ex00_ex18_combined_regression",
)
P7_R54_AHR_POST_EX18_MN09_COMPILEALL_COMMAND_REFS: Final[tuple[str, ...]] = (
    "mn09_compileall_ai_services_ai_inference_ai_tests",
)
P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REQUIRED_SECTION_REFS: Final[tuple[str, ...]] = (
    "implementation_scope",
    "changed_files",
    "target_tests",
    "selected_regression",
    "compileall",
    "ex18_intake_status",
    "manual_decision",
    "actual_review_evidence_status",
    "return_operation_plan",
    "reentry_mapping",
    "not_claimed_boundary",
    "next_required_step",
)
P7_R54_AHR_POST_EX18_MN09_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_complete_not_claimed",
    "p5_final_not_claimed",
    "p6_start_not_claimed",
    "p8_start_not_claimed",
    "r52_actual_execution_not_claimed",
    "p7_complete_not_claimed",
    "release_allowed_not_claimed",
    "full_backend_suite_green_not_claimed",
    "rn_contract_green_not_claimed",
    "rn_real_device_modal_verified_not_claimed",
)
P7_R54_AHR_POST_EX18_MN09_NO_GREEN_TO_PRODUCT_CLAIM_REFS: Final[tuple[str, ...]] = (
    "target_tests_green_does_not_claim_actual_human_review_complete",
    "manual_decision_ready_does_not_claim_actual_review_operation_executed",
    "return_operation_plan_ready_does_not_claim_actual_rows_created",
    "reentry_mapping_ready_does_not_claim_reentry_executed",
    "compileall_green_does_not_claim_product_quality_pass",
    "selected_regression_green_does_not_claim_full_backend_suite_green",
)

P7_R54_AHR_POST_EX18_MN08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn07_schema_version", "mn07_material_ref", "mn07_status_ref", "mn07_ready",
    "mn07_next_required_step", "mn07_no_promotion_boundary_confirmed",
    "mn08_status_ref", "mn08_allowed_status_refs", "mn08_ready", "mn08_blocker_refs",
    "mn08_blocker_ref_count", "mn08_reason_refs", "mn08_reason_ref_count",
    "reentry_mapping_ref", "reentry_source_ref", "existing_postcr22_helper_ref",
    "existing_postcr22_reentry_step_refs", "existing_postcr22_reentry_step_ref_count",
    "reentry_artifact_refs", "reentry_artifact_ref_count", "reentry_role_refs", "reentry_role_ref_count",
    "reentry_mapping_rows", "reentry_mapping_row_count", "reentry_mapping_bodyfree_ready",
    "reentry_mapping_requires_future_actual_review_evidence_bundle", "actual_review_evidence_bundle_not_created_by_mapping",
    "actual_review_operation_not_run_by_mapping", "actual_rows_not_created_by_mapping",
    "post_ex18_helper_does_not_reimplement_postcr22_ex08_ex18", "reentry_mapping_is_not_actual_execution_claim",
    "reentry_mapping_is_not_r52_actual_execution_claim", "reentry_mapping_is_not_p8_start_claim",
    "reentry_mapping_is_not_p5_final_claim", "reentry_mapping_is_not_release_claim",
    "forbidden_reentry_claim_refs", "forbidden_reentry_claim_ref_count", "next_decision_auto_execution_allowed",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "local_received_zip_refs",
    "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs",
    "claim_boundary_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_ex18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_EX18_MN09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn08_schema_version", "mn08_material_ref", "mn08_status_ref", "mn08_ready",
    "mn08_next_required_step", "mn08_reentry_mapping_ref", "mn08_reentry_mapping_bodyfree_ready",
    "mn09_status_ref", "mn09_allowed_status_refs", "mn09_ready", "mn09_blocker_refs",
    "mn09_blocker_ref_count", "mn09_reason_refs", "mn09_reason_ref_count",
    "validation_command_matrix_ref", "validation_command_matrix_ready", "validation_command_refs",
    "validation_command_ref_count", "validation_command_rows", "validation_command_row_count",
    "target_test_command_refs", "target_test_command_ref_count", "selected_regression_command_refs",
    "selected_regression_command_ref_count", "compileall_command_refs", "compileall_command_ref_count",
    "result_memo_envelope_ref", "result_memo_ref", "result_memo_envelope_ready",
    "result_memo_required_section_refs", "result_memo_required_section_ref_count",
    "result_memo_bodyfree_required", "result_memo_forbidden_artifact_refs", "result_memo_forbidden_artifact_ref_count",
    "not_claimed_boundary_refs_for_result_memo", "not_claimed_boundary_ref_count_for_result_memo",
    "no_green_to_product_claim_refs", "no_green_to_product_claim_ref_count",
    "validation_matrix_does_not_claim_actual_human_review_complete", "validation_matrix_does_not_claim_actual_review_operation_executed",
    "validation_matrix_does_not_claim_actual_rows_created", "validation_matrix_does_not_claim_full_backend_suite_green",
    "validation_matrix_does_not_claim_rn_contract_green", "validation_matrix_does_not_claim_rn_real_device_modal_verified",
    "validation_matrix_does_not_claim_p5_p6_p8_r52_p7_release", "result_memo_envelope_does_not_copy_terminal_output",
    "result_memo_envelope_does_not_copy_local_path_or_hash", "result_memo_envelope_does_not_copy_body_or_question_text",
    "next_decision_auto_execution_allowed", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "local_received_zip_refs", "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs", "claim_boundary_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract",
    "post_ex18_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _mn08_reentry_mapping_rows() -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []
    for index, (artifact_ref, role_ref, step_ref) in enumerate(
        zip(
            P7_R54_AHR_POST_EX18_MN08_REENTRY_ARTIFACT_REFS,
            P7_R54_AHR_POST_EX18_MN08_REENTRY_ROLE_REFS,
            P7_R54_AHR_POST_EX18_MN08_EXISTING_POSTCR22_REENTRY_STEP_REFS,
        ),
        start=1,
    ):
        rows.append(
            {
                "row_ref": f"mn08_reentry_mapping_row_{index:02d}",
                "artifact_ref": artifact_ref,
                "reentry_role_ref": role_ref,
                "existing_postcr22_step_ref": step_ref,
                "bodyfree_artifact_required_after_real_review": True,
                "postex18_helper_reimplements_existing_step": False,
                "actual_execution_claimed_by_mapping": False,
            }
        )
    return rows


def _mn08_blockers(no_promotion_boundary: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(no_promotion_boundary, Mapping):
        blockers.append("mn07_downstream_no_promotion_boundary_materialization_missing")
    else:
        try:
            assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract(no_promotion_boundary)
        except ValueError:
            blockers.append("mn07_downstream_no_promotion_boundary_materialization_contract_invalid")
        if no_promotion_boundary.get("mn07_ready") is not True:
            blockers.append("mn07_downstream_no_promotion_boundary_materialization_not_ready")
        if no_promotion_boundary.get("next_required_step") != P7_R54_AHR_POST_EX18_MN08_STEP_REF:
            blockers.append("mn07_next_required_step_not_mn08")
        if no_promotion_boundary.get("no_promotion_boundary_confirmed") is not True:
            blockers.append("mn07_no_promotion_boundary_not_confirmed")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(
    *,
    downstream_no_promotion_boundary_materialization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN08 body-free re-entry mapping to existing Post-CR22 EX07-EX18."""

    session_id = _safe_review_session_id(review_session_id)
    mn07 = downstream_no_promotion_boundary_materialization
    if mn07 is None:
        mn07 = build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization(review_session_id=session_id)
    blockers = _mn08_blockers(mn07)
    ready = not blockers
    false_flags = _false_flags()
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN08_REENTRY_MAPPING_TO_EXISTING_POSTCR22_EX07_EX18_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN08_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn07_schema_version": _clean_ref(mn07.get("schema_version") if isinstance(mn07, Mapping) else "", default="mn07_schema_missing", max_length=220),
        "mn07_material_ref": _clean_ref(mn07.get("material_id") if isinstance(mn07, Mapping) else "", default="mn07_material_missing", max_length=220),
        "mn07_status_ref": _clean_ref(mn07.get("mn07_status_ref") if isinstance(mn07, Mapping) else "", default="mn07_status_missing", max_length=180),
        "mn07_ready": bool(isinstance(mn07, Mapping) and mn07.get("mn07_ready") is True),
        "mn07_next_required_step": _clean_ref(mn07.get("next_required_step") if isinstance(mn07, Mapping) else "", default="mn07_next_required_step_missing", max_length=220),
        "mn07_no_promotion_boundary_confirmed": bool(isinstance(mn07, Mapping) and mn07.get("no_promotion_boundary_confirmed") is True),
        "mn08_status_ref": P7_R54_AHR_POST_EX18_MN08_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN08_BLOCKED_STATUS_REF,
        "mn08_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN08_ALLOWED_STATUS_REFS),
        "mn08_ready": ready,
        "mn08_blocker_refs": blockers,
        "mn08_blocker_ref_count": len(blockers),
        "mn08_reason_refs": ["mn08_existing_postcr22_ex07_ex18_reentry_mapping_ready_bodyfree"] if ready else [],
        "mn08_reason_ref_count": 1 if ready else 0,
        "reentry_mapping_ref": P7_R54_AHR_POST_EX18_MN08_REENTRY_MAPPING_REF,
        "reentry_source_ref": P7_R54_AHR_POST_EX18_MN08_REENTRY_SOURCE_REF,
        "existing_postcr22_helper_ref": P7_R54_AHR_POST_EX18_EX_HELPER_REF,
        "existing_postcr22_reentry_step_refs": list(P7_R54_AHR_POST_EX18_MN08_EXISTING_POSTCR22_REENTRY_STEP_REFS),
        "existing_postcr22_reentry_step_ref_count": len(P7_R54_AHR_POST_EX18_MN08_EXISTING_POSTCR22_REENTRY_STEP_REFS),
        "reentry_artifact_refs": list(P7_R54_AHR_POST_EX18_MN08_REENTRY_ARTIFACT_REFS),
        "reentry_artifact_ref_count": len(P7_R54_AHR_POST_EX18_MN08_REENTRY_ARTIFACT_REFS),
        "reentry_role_refs": list(P7_R54_AHR_POST_EX18_MN08_REENTRY_ROLE_REFS),
        "reentry_role_ref_count": len(P7_R54_AHR_POST_EX18_MN08_REENTRY_ROLE_REFS),
        "reentry_mapping_rows": _mn08_reentry_mapping_rows(),
        "reentry_mapping_row_count": len(P7_R54_AHR_POST_EX18_MN08_EXISTING_POSTCR22_REENTRY_STEP_REFS),
        "reentry_mapping_bodyfree_ready": ready,
        "reentry_mapping_requires_future_actual_review_evidence_bundle": True,
        "actual_review_evidence_bundle_not_created_by_mapping": True,
        "actual_review_operation_not_run_by_mapping": True,
        "actual_rows_not_created_by_mapping": True,
        "post_ex18_helper_does_not_reimplement_postcr22_ex08_ex18": True,
        "reentry_mapping_is_not_actual_execution_claim": True,
        "reentry_mapping_is_not_r52_actual_execution_claim": True,
        "reentry_mapping_is_not_p8_start_claim": True,
        "reentry_mapping_is_not_p5_final_claim": True,
        "reentry_mapping_is_not_release_claim": True,
        "forbidden_reentry_claim_refs": list(P7_R54_AHR_POST_EX18_MN08_FORBIDDEN_REENTRY_CLAIM_REFS),
        "forbidden_reentry_claim_ref_count": len(P7_R54_AHR_POST_EX18_MN08_FORBIDDEN_REENTRY_CLAIM_REFS),
        "next_decision_auto_execution_allowed": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN08_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN08_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN09_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN08_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN08_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN08 re-entry mapping to existing Post-CR22 EX07-EX18",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN08_REENTRY_MAPPING_TO_EXISTING_POSTCR22_EX07_EX18_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN08_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN08 re-entry mapping to existing Post-CR22 EX07-EX18",
    )
    if tuple(data.get("mn08_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN08 allowed status refs changed")
    for field, count_field in (
        ("mn08_blocker_refs", "mn08_blocker_ref_count"),
        ("mn08_reason_refs", "mn08_reason_ref_count"),
        ("existing_postcr22_reentry_step_refs", "existing_postcr22_reentry_step_ref_count"),
        ("reentry_artifact_refs", "reentry_artifact_ref_count"),
        ("reentry_role_refs", "reentry_role_ref_count"),
        ("reentry_mapping_rows", "reentry_mapping_row_count"),
        ("forbidden_reentry_claim_refs", "forbidden_reentry_claim_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN08 {count_field} changed")
    if tuple(data.get("existing_postcr22_reentry_step_refs") or ()) != P7_R54_AHR_POST_EX18_MN08_EXISTING_POSTCR22_REENTRY_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN08 existing Post-CR22 re-entry step refs changed")
    if tuple(data.get("reentry_artifact_refs") or ()) != P7_R54_AHR_POST_EX18_MN08_REENTRY_ARTIFACT_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN08 re-entry artifact refs changed")
    if tuple(data.get("reentry_role_refs") or ()) != P7_R54_AHR_POST_EX18_MN08_REENTRY_ROLE_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN08 re-entry role refs changed")
    if data.get("reentry_mapping_rows") != _mn08_reentry_mapping_rows():
        raise ValueError("P7-R54-AHR-PostEX18-MN08 re-entry mapping rows changed")
    for key in (
        "reentry_mapping_requires_future_actual_review_evidence_bundle",
        "actual_review_evidence_bundle_not_created_by_mapping",
        "actual_review_operation_not_run_by_mapping",
        "actual_rows_not_created_by_mapping",
        "post_ex18_helper_does_not_reimplement_postcr22_ex08_ex18",
        "reentry_mapping_is_not_actual_execution_claim",
        "reentry_mapping_is_not_r52_actual_execution_claim",
        "reentry_mapping_is_not_p8_start_claim",
        "reentry_mapping_is_not_p5_final_claim",
        "reentry_mapping_is_not_release_claim",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN08 required true boundary changed: {key}")
    if data.get("next_decision_auto_execution_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN08 cannot allow auto execution")
    ready = data.get("mn08_status_ref") == P7_R54_AHR_POST_EX18_MN08_READY_STATUS_REF
    if data.get("mn08_ready") is not ready or data.get("reentry_mapping_bodyfree_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN08 ready flag changed")
    if ready:
        if data.get("mn08_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 ready material cannot carry blockers")
        if data.get("mn08_reason_refs") != ["mn08_existing_postcr22_ex07_ex18_reentry_mapping_ready_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 ready reason changed")
        if data.get("mn07_ready") is not True or data.get("mn07_no_promotion_boundary_confirmed") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 ready material requires ready MN07 no-promotion boundary")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN08_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 next step changed")
    else:
        if data.get("mn08_status_ref") != P7_R54_AHR_POST_EX18_MN08_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 blocked status changed")
        if not data.get("mn08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN08 blocked material must carry blockers")
        if data.get("mn08_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN08 blocked next step changed")
    return True


def _mn09_validation_command_rows() -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []
    for command_ref in P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_REFS:
        if command_ref in P7_R54_AHR_POST_EX18_MN09_TARGET_TEST_COMMAND_REFS:
            command_kind_ref = "target_test"
        elif command_ref in P7_R54_AHR_POST_EX18_MN09_SELECTED_REGRESSION_COMMAND_REFS:
            command_kind_ref = "selected_regression"
        elif command_ref in P7_R54_AHR_POST_EX18_MN09_COMPILEALL_COMMAND_REFS:
            command_kind_ref = "compileall"
        else:
            command_kind_ref = "unknown"
        rows.append(
            {
                "command_ref": command_ref,
                "command_kind_ref": command_kind_ref,
                "command_status_ref": P7_R54_AHR_POST_EX18_MN09_COMMAND_STATUS_DECLARED_NOT_RUN_REF,
                "ran_here": False,
                "green_claimed_by_helper": False,
                "actual_human_review_complete_claimed": False,
                "p5_final_claimed": False,
                "p6_start_claimed": False,
                "p8_start_claimed": False,
                "r52_actual_execution_claimed": False,
                "p7_complete_claimed": False,
                "release_allowed_claimed": False,
                "full_backend_suite_green_claimed": False,
                "rn_contract_green_claimed": False,
                "rn_real_device_modal_claimed": False,
                "body_free": True,
            }
        )
    return rows


def _mn09_blockers(reentry_mapping: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(reentry_mapping, Mapping):
        blockers.append("mn08_reentry_mapping_missing")
    else:
        try:
            assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(reentry_mapping)
        except ValueError:
            blockers.append("mn08_reentry_mapping_contract_invalid")
        if reentry_mapping.get("mn08_ready") is not True:
            blockers.append("mn08_reentry_mapping_not_ready")
        if reentry_mapping.get("next_required_step") != P7_R54_AHR_POST_EX18_MN09_STEP_REF:
            blockers.append("mn08_next_required_step_not_mn09")
        if reentry_mapping.get("reentry_mapping_bodyfree_ready") is not True:
            blockers.append("mn08_reentry_mapping_bodyfree_not_ready")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
    *,
    reentry_mapping_to_existing_postcr22_ex07_ex18: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN09 body-free validation command matrix / result memo envelope."""

    session_id = _safe_review_session_id(review_session_id)
    mn08 = reentry_mapping_to_existing_postcr22_ex07_ex18
    if mn08 is None:
        mn08 = build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(review_session_id=session_id)
    blockers = _mn09_blockers(mn08)
    ready = not blockers
    false_flags = _false_flags()
    command_rows = _mn09_validation_command_rows()
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN09_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn08_schema_version": _clean_ref(mn08.get("schema_version") if isinstance(mn08, Mapping) else "", default="mn08_schema_missing", max_length=220),
        "mn08_material_ref": _clean_ref(mn08.get("material_id") if isinstance(mn08, Mapping) else "", default="mn08_material_missing", max_length=220),
        "mn08_status_ref": _clean_ref(mn08.get("mn08_status_ref") if isinstance(mn08, Mapping) else "", default="mn08_status_missing", max_length=180),
        "mn08_ready": bool(isinstance(mn08, Mapping) and mn08.get("mn08_ready") is True),
        "mn08_next_required_step": _clean_ref(mn08.get("next_required_step") if isinstance(mn08, Mapping) else "", default="mn08_next_required_step_missing", max_length=220),
        "mn08_reentry_mapping_ref": _clean_ref(mn08.get("reentry_mapping_ref") if isinstance(mn08, Mapping) else "", default="mn08_reentry_mapping_missing", max_length=220),
        "mn08_reentry_mapping_bodyfree_ready": bool(isinstance(mn08, Mapping) and mn08.get("reentry_mapping_bodyfree_ready") is True),
        "mn09_status_ref": P7_R54_AHR_POST_EX18_MN09_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN09_BLOCKED_STATUS_REF,
        "mn09_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN09_ALLOWED_STATUS_REFS),
        "mn09_ready": ready,
        "mn09_blocker_refs": blockers,
        "mn09_blocker_ref_count": len(blockers),
        "mn09_reason_refs": ["mn09_validation_command_matrix_result_memo_envelope_ready_bodyfree"] if ready else [],
        "mn09_reason_ref_count": 1 if ready else 0,
        "validation_command_matrix_ref": "post_ex18_mn09_validation_command_matrix_bodyfree_v1",
        "validation_command_matrix_ready": ready,
        "validation_command_refs": list(P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_REFS),
        "validation_command_ref_count": len(P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_REFS),
        "validation_command_rows": command_rows,
        "validation_command_row_count": len(command_rows),
        "target_test_command_refs": list(P7_R54_AHR_POST_EX18_MN09_TARGET_TEST_COMMAND_REFS),
        "target_test_command_ref_count": len(P7_R54_AHR_POST_EX18_MN09_TARGET_TEST_COMMAND_REFS),
        "selected_regression_command_refs": list(P7_R54_AHR_POST_EX18_MN09_SELECTED_REGRESSION_COMMAND_REFS),
        "selected_regression_command_ref_count": len(P7_R54_AHR_POST_EX18_MN09_SELECTED_REGRESSION_COMMAND_REFS),
        "compileall_command_refs": list(P7_R54_AHR_POST_EX18_MN09_COMPILEALL_COMMAND_REFS),
        "compileall_command_ref_count": len(P7_R54_AHR_POST_EX18_MN09_COMPILEALL_COMMAND_REFS),
        "result_memo_envelope_ref": "post_ex18_mn09_result_memo_envelope_bodyfree_v1",
        "result_memo_ref": _clean_ref(result_memo_ref, default=P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REF, max_length=220),
        "result_memo_envelope_ready": ready,
        "result_memo_required_section_refs": list(P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_required_section_ref_count": len(P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_bodyfree_required": True,
        "result_memo_forbidden_artifact_refs": list(P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS),
        "result_memo_forbidden_artifact_ref_count": len(P7_R54_AHR_POST_EX18_FORBIDDEN_ARTIFACT_REFS),
        "not_claimed_boundary_refs_for_result_memo": list(P7_R54_AHR_POST_EX18_MN09_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count_for_result_memo": len(P7_R54_AHR_POST_EX18_MN09_NOT_CLAIMED_BOUNDARY_REFS),
        "no_green_to_product_claim_refs": list(P7_R54_AHR_POST_EX18_MN09_NO_GREEN_TO_PRODUCT_CLAIM_REFS),
        "no_green_to_product_claim_ref_count": len(P7_R54_AHR_POST_EX18_MN09_NO_GREEN_TO_PRODUCT_CLAIM_REFS),
        "validation_matrix_does_not_claim_actual_human_review_complete": True,
        "validation_matrix_does_not_claim_actual_review_operation_executed": True,
        "validation_matrix_does_not_claim_actual_rows_created": True,
        "validation_matrix_does_not_claim_full_backend_suite_green": True,
        "validation_matrix_does_not_claim_rn_contract_green": True,
        "validation_matrix_does_not_claim_rn_real_device_modal_verified": True,
        "validation_matrix_does_not_claim_p5_p6_p8_r52_p7_release": True,
        "result_memo_envelope_does_not_copy_terminal_output": True,
        "result_memo_envelope_does_not_copy_local_path_or_hash": True,
        "result_memo_envelope_does_not_copy_body_or_question_text": True,
        "next_decision_auto_execution_allowed": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN09_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN09_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN10_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN09_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN09 validation command matrix / result memo envelope",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN09_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN09 validation command matrix / result memo envelope",
    )
    if tuple(data.get("mn09_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN09_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 allowed status refs changed")
    for field, count_field in (
        ("mn09_blocker_refs", "mn09_blocker_ref_count"),
        ("mn09_reason_refs", "mn09_reason_ref_count"),
        ("validation_command_refs", "validation_command_ref_count"),
        ("validation_command_rows", "validation_command_row_count"),
        ("target_test_command_refs", "target_test_command_ref_count"),
        ("selected_regression_command_refs", "selected_regression_command_ref_count"),
        ("compileall_command_refs", "compileall_command_ref_count"),
        ("result_memo_required_section_refs", "result_memo_required_section_ref_count"),
        ("result_memo_forbidden_artifact_refs", "result_memo_forbidden_artifact_ref_count"),
        ("not_claimed_boundary_refs_for_result_memo", "not_claimed_boundary_ref_count_for_result_memo"),
        ("no_green_to_product_claim_refs", "no_green_to_product_claim_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN09 {count_field} changed")
    if tuple(data.get("validation_command_refs") or ()) != P7_R54_AHR_POST_EX18_MN09_VALIDATION_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 validation command refs changed")
    if data.get("validation_command_rows") != _mn09_validation_command_rows():
        raise ValueError("P7-R54-AHR-PostEX18-MN09 validation command rows changed")
    if tuple(data.get("target_test_command_refs") or ()) != P7_R54_AHR_POST_EX18_MN09_TARGET_TEST_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 target command refs changed")
    if tuple(data.get("selected_regression_command_refs") or ()) != P7_R54_AHR_POST_EX18_MN09_SELECTED_REGRESSION_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 selected regression command refs changed")
    if tuple(data.get("compileall_command_refs") or ()) != P7_R54_AHR_POST_EX18_MN09_COMPILEALL_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 compileall command refs changed")
    if tuple(data.get("result_memo_required_section_refs") or ()) != P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REQUIRED_SECTION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 result memo sections changed")
    if tuple(data.get("not_claimed_boundary_refs_for_result_memo") or ()) != P7_R54_AHR_POST_EX18_MN09_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 result memo not-claimed refs changed")
    if tuple(data.get("no_green_to_product_claim_refs") or ()) != P7_R54_AHR_POST_EX18_MN09_NO_GREEN_TO_PRODUCT_CLAIM_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 no-green claim refs changed")
    for row in data.get("validation_command_rows") or []:
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-PostEX18-MN09 command row must be a mapping")
        for key in (
            "ran_here", "green_claimed_by_helper", "actual_human_review_complete_claimed",
            "p5_final_claimed", "p6_start_claimed", "p8_start_claimed", "r52_actual_execution_claimed",
            "p7_complete_claimed", "release_allowed_claimed", "full_backend_suite_green_claimed",
            "rn_contract_green_claimed", "rn_real_device_modal_claimed",
        ):
            if row.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostEX18-MN09 command row promoted claim: {key}")
        if row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 command row must be body-free")
    for key in (
        "result_memo_bodyfree_required",
        "validation_matrix_does_not_claim_actual_human_review_complete",
        "validation_matrix_does_not_claim_actual_review_operation_executed",
        "validation_matrix_does_not_claim_actual_rows_created",
        "validation_matrix_does_not_claim_full_backend_suite_green",
        "validation_matrix_does_not_claim_rn_contract_green",
        "validation_matrix_does_not_claim_rn_real_device_modal_verified",
        "validation_matrix_does_not_claim_p5_p6_p8_r52_p7_release",
        "result_memo_envelope_does_not_copy_terminal_output",
        "result_memo_envelope_does_not_copy_local_path_or_hash",
        "result_memo_envelope_does_not_copy_body_or_question_text",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN09 required true boundary changed: {key}")
    if data.get("next_decision_auto_execution_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 cannot allow auto execution")
    ready = data.get("mn09_status_ref") == P7_R54_AHR_POST_EX18_MN09_READY_STATUS_REF
    if data.get("mn09_ready") is not ready or data.get("validation_command_matrix_ready") is not ready or data.get("result_memo_envelope_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN09 ready flag changed")
    if ready:
        if data.get("mn09_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 ready material cannot carry blockers")
        if data.get("mn09_reason_refs") != ["mn09_validation_command_matrix_result_memo_envelope_ready_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 ready reason changed")
        if data.get("mn08_ready") is not True or data.get("mn08_reentry_mapping_bodyfree_ready") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 ready material requires ready MN08 re-entry mapping")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN09_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN10_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 next step changed")
    else:
        if data.get("mn09_status_ref") != P7_R54_AHR_POST_EX18_MN09_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 blocked status changed")
        if not data.get("mn09_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN09 blocked material must carry blockers")
        if data.get("mn09_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN09 blocked next step changed")
    return True


def build_p7_r54_ahr_post_ex18_manual_next_decision_reentry_mapping_to_existing_postcr22_ex07_ex18_bodyfree(
    *,
    downstream_no_promotion_boundary_materialization: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18(
        downstream_no_promotion_boundary_materialization=downstream_no_promotion_boundary_materialization,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_reentry_mapping_to_existing_postcr22_ex07_ex18_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_validation_command_matrix_result_memo_envelope_bodyfree(
    *,
    reentry_mapping_to_existing_postcr22_ex07_ex18: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_EX18_MN09_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
        reentry_mapping_to_existing_postcr22_ex07_ex18=reentry_mapping_to_existing_postcr22_ex07_ex18,
        result_memo_ref=result_memo_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_validation_command_matrix_result_memo_envelope_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(data)
# MN10-MN11 alias / contract boundary / acceptance fail-closed finalizer
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_EX18_MN10_ALIAS_CONTRACT_FUNCTION_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn10_alias_contract_function_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_FAIL_CLOSED_FINALIZER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_ex18.manual_next_decision."
    "mn11_acceptance_fail_closed_finalizer.bodyfree.v1"
)
P7_R54_AHR_POST_EX18_MN10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn10_alias_contract_function_boundary_or_stop"
)
P7_R54_AHR_POST_EX18_MN11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_mn11_acceptance_fail_closed_finalizer_or_stop"
)
P7_R54_AHR_POST_EX18_MN10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:11]
P7_R54_AHR_POST_EX18_MN10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[11:]
P7_R54_AHR_POST_EX18_MN11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_EX18_MN_STEP_REFS[:12]
P7_R54_AHR_POST_EX18_MN11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R54_AHR_POST_EX18_MN10_READY_STATUS_REF: Final = (
    "MN10_ALIAS_CONTRACT_FUNCTION_BOUNDARY_READY_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN10_BLOCKED_STATUS_REF: Final = (
    "MN10_ALIAS_CONTRACT_FUNCTION_BOUNDARY_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN10_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN10_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN10_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN11_READY_STATUS_REF: Final = (
    "MN11_ACCEPTANCE_FAIL_CLOSED_FINALIZER_READY_BODYFREE"
)
P7_R54_AHR_POST_EX18_MN11_BLOCKED_STATUS_REF: Final = (
    "MN11_ACCEPTANCE_FAIL_CLOSED_FINALIZER_BLOCKED"
)
P7_R54_AHR_POST_EX18_MN11_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_EX18_MN11_READY_STATUS_REF,
    P7_R54_AHR_POST_EX18_MN11_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_EX18_MN10_ALIAS_CONTRACT_BOUNDARY_REF: Final = (
    "post_ex18_mn10_alias_contract_function_boundary_bodyfree_v1"
)
P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_FINALIZER_REF: Final = (
    "post_ex18_mn11_acceptance_fail_closed_finalizer_bodyfree_v1"
)
P7_R54_AHR_POST_EX18_MN11_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostEX18_ManualNextDecision_ReturnToActualReviewOperation_MN10_MN11_Result_20260630.md"
)

P7_R54_AHR_POST_EX18_MN10_PRIMARY_BUILDER_FUNCTION_REFS: Final[tuple[str, ...]] = (
    "build_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze",
    "build_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake",
    "build_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization",
    "build_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier",
    "build_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan",
    "build_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary",
    "build_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan",
    "build_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization",
    "build_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18",
    "build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope",
    "build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary",
    "build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer",
)
P7_R54_AHR_POST_EX18_MN10_PRIMARY_ASSERT_FUNCTION_REFS: Final[tuple[str, ...]] = (
    "assert_p7_r54_ahr_post_ex18_mn00_scope_no_touch_no_promotion_boundary_freeze_contract",
    "assert_p7_r54_ahr_post_ex18_mn01_ex18_result_memo_bodyfree_envelope_intake_contract",
    "assert_p7_r54_ahr_post_ex18_mn02_actual_review_evidence_state_normalization_contract",
    "assert_p7_r54_ahr_post_ex18_mn03_manual_decision_classifier_contract",
    "assert_p7_r54_ahr_post_ex18_mn04_return_to_actual_review_operation_plan_contract",
    "assert_p7_r54_ahr_post_ex18_mn05_expected_bodyfree_evidence_intake_bundle_boundary_contract",
    "assert_p7_r54_ahr_post_ex18_mn06_no_body_no_question_no_path_no_hash_scan_contract",
    "assert_p7_r54_ahr_post_ex18_mn07_downstream_no_promotion_boundary_materialization_contract",
    "assert_p7_r54_ahr_post_ex18_mn08_reentry_mapping_to_existing_postcr22_ex07_ex18_contract",
    "assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract",
    "assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract",
    "assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract",
)
P7_R54_AHR_POST_EX18_MN10_ALIAS_BUILDER_FUNCTION_REFS: Final[tuple[str, ...]] = (
    "build_p7_r54_ahr_post_ex18_manual_next_decision_scope_no_touch_no_promotion_boundary_freeze_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_ex18_result_memo_bodyfree_envelope_intake_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_actual_review_evidence_state_normalization_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_classifier_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_plan_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_expected_bodyfree_evidence_intake_bundle_boundary_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_no_body_no_question_no_path_no_hash_scan_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_downstream_no_promotion_boundary_materialization_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_reentry_mapping_to_existing_postcr22_ex07_ex18_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_validation_command_matrix_result_memo_envelope_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_alias_contract_function_boundary_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_acceptance_fail_closed_finalizer_bodyfree",
    "build_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_bodyfree",
)
P7_R54_AHR_POST_EX18_MN10_ALIAS_ASSERT_FUNCTION_REFS: Final[tuple[str, ...]] = (
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_scope_no_touch_no_promotion_boundary_freeze_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_ex18_result_memo_bodyfree_envelope_intake_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_actual_review_evidence_state_normalization_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_classifier_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_plan_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_expected_bodyfree_evidence_intake_bundle_boundary_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_no_body_no_question_no_path_no_hash_scan_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_downstream_no_promotion_boundary_materialization_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_reentry_mapping_to_existing_postcr22_ex07_ex18_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_validation_command_matrix_result_memo_envelope_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_alias_contract_function_boundary_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_acceptance_fail_closed_finalizer_bodyfree_contract",
    "assert_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_bodyfree_contract",
)
P7_R54_AHR_POST_EX18_MN10_FUNCTION_BOUNDARY_GROUP_REFS: Final[tuple[str, ...]] = (
    "primary_builders",
    "primary_contract_assertions",
    "bodyfree_alias_builders",
    "bodyfree_alias_contract_assertions",
)
P7_R54_AHR_POST_EX18_MN10_FORBIDDEN_FUNCTION_BOUNDARY_CLAIM_REFS: Final[tuple[str, ...]] = (
    "mn10_renames_existing_postcr22_helper_functions",
    "mn10_changes_existing_cr_cs_ex_prefixes",
    "mn10_uses_mn_prefix_outside_postex18_manual_next_decision_line",
    "mn10_reimplements_existing_postcr22_ex07_ex18_line",
    "mn10_changes_api_db_rn_runtime_response_keys",
    "mn10_executes_actual_review_or_generates_bodyfull_packet",
    "mn10_allows_p5_p6_p8_r52_p7_release_promotion",
)
P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_CONDITION_REFS: Final[tuple[str, ...]] = (
    "manual_decision_ref_is_return_to_actual_review_operation_required",
    "return_to_actual_review_operation_required_true",
    "actual_review_evidence_complete_from_real_review_false",
    "actual_review_evidence_complete_from_real_review_accepted_false",
    "next_required_step_is_actual_local_only_human_review_operation_required_before_p5_p6_p8_r52_decision",
    "no_body_leak_validation_passed_true",
    "no_question_text_validation_passed_true",
    "no_path_hash_validation_passed_true",
    "no_touch_boundary_confirmed_true",
    "no_promotion_boundary_confirmed_true",
)
P7_R54_AHR_POST_EX18_MN11_FAIL_CLOSED_CONDITION_REFS: Final[tuple[str, ...]] = (
    "body_leak_detected",
    "question_text_detected",
    "local_path_or_hash_detected",
    "promotion_claim_detected",
    "ex18_result_memo_missing",
    "ex18_next_required_step_not_manual_hold",
    "unit_test_rows_used_as_actual_evidence",
    "actual_basis_ref_overwritten_by_current_zip_label",
    "mn10_alias_contract_function_boundary_missing_or_invalid",
)
P7_R54_AHR_POST_EX18_MN11_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_complete_not_claimed_by_finalizer",
    "actual_review_operation_not_executed_by_finalizer",
    "actual_review_rows_not_created_by_finalizer",
    "p5_final_not_claimed_by_finalizer",
    "p6_start_not_claimed_by_finalizer",
    "p8_start_not_claimed_by_finalizer",
    "r52_actual_execution_not_claimed_by_finalizer",
    "p7_complete_not_claimed_by_finalizer",
    "release_allowed_not_claimed_by_finalizer",
    "full_backend_suite_green_not_claimed_by_finalizer",
    "rn_contract_green_not_claimed_by_finalizer",
    "rn_real_device_modal_verified_not_claimed_by_finalizer",
)

P7_R54_AHR_POST_EX18_MN10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn09_schema_version", "mn09_material_ref", "mn09_status_ref", "mn09_ready",
    "mn09_next_required_step", "mn09_validation_command_matrix_ready", "mn09_result_memo_envelope_ready",
    "mn10_status_ref", "mn10_allowed_status_refs", "mn10_ready", "mn10_blocker_refs",
    "mn10_blocker_ref_count", "mn10_reason_refs", "mn10_reason_ref_count",
    "alias_contract_function_boundary_ref", "function_boundary_group_refs", "function_boundary_group_ref_count",
    "primary_builder_function_refs", "primary_builder_function_ref_count",
    "primary_assert_function_refs", "primary_assert_function_ref_count",
    "alias_builder_function_refs", "alias_builder_function_ref_count",
    "alias_assert_function_refs", "alias_assert_function_ref_count",
    "function_boundary_rows", "function_boundary_row_count",
    "function_refs_resolved_in_module", "contract_assertion_refs_resolved_in_module",
    "existing_postcr22_helper_rename_forbidden", "existing_postcr22_helper_function_boundary_preserved", "existing_cr_cs_ex_prefix_boundary_preserved",
    "mn_prefix_internal_to_postex18_manual_next_decision_only",
    "postex18_helper_does_not_reimplement_postcr22_ex07_ex18",
    "function_boundary_does_not_execute_actual_review", "function_boundary_does_not_generate_bodyfull_packet",
    "function_boundary_does_not_create_actual_rows", "function_boundary_does_not_create_question_text",
    "function_boundary_does_not_materialize_json_or_schema_files",
    "function_boundary_does_not_change_api_db_rn_runtime_response_keys",
    "function_boundary_does_not_allow_downstream_promotion",
    "forbidden_function_boundary_claim_refs", "forbidden_function_boundary_claim_ref_count",
    "next_decision_auto_execution_allowed",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "local_received_zip_refs",
    "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs",
    "claim_boundary_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_ex18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_EX18_MN11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section",
    "operation_step_ref", "current_phase", "material_id", "review_session_id",
    "source_mode", "git_connection_required", "git_checked",
    "mn10_schema_version", "mn10_material_ref", "mn10_status_ref", "mn10_ready",
    "mn10_next_required_step", "mn10_alias_contract_function_boundary_ready",
    "mn11_status_ref", "mn11_allowed_status_refs", "mn11_ready", "mn11_blocker_refs",
    "mn11_blocker_ref_count", "mn11_reason_refs", "mn11_reason_ref_count",
    "acceptance_fail_closed_finalizer_ref", "result_memo_ref",
    "final_manual_decision_ref", "manual_decision_ref", "manual_decision_status_ref",
    "actual_review_evidence_status_ref", "return_to_actual_review_operation_required",
    "actual_local_only_human_review_operation_required_before_downstream_decision",
    "final_next_required_step_ref", "acceptance_condition_refs", "acceptance_condition_ref_count",
    "acceptance_condition_rows", "acceptance_condition_row_count",
    "fail_closed_condition_refs", "fail_closed_condition_ref_count",
    "fail_closed_blocker_refs", "fail_closed_blocker_ref_count",
    "not_claimed_boundary_refs_for_finalizer", "not_claimed_boundary_ref_count_for_finalizer",
    "manual_decision_ref_is_return_to_actual_review_operation_required",
    "return_to_actual_review_operation_required_true",
    "actual_review_evidence_complete_from_real_review_false",
    "actual_review_evidence_complete_from_real_review_accepted_false",
    "next_required_step_is_actual_local_only_human_review_operation_required_before_p5_p6_p8_r52_decision",
    "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed",
    "no_touch_boundary_confirmed", "no_promotion_boundary_confirmed",
    "acceptance_ready", "finalizer_ready_for_result_memo", "final_result_is_bodyfree_hold",
    "finalizer_does_not_execute_actual_review", "finalizer_does_not_generate_bodyfull_packet",
    "finalizer_does_not_create_actual_rows", "finalizer_does_not_create_question_text",
    "finalizer_does_not_change_api_db_rn_runtime_response_keys", "finalizer_does_not_allow_downstream_promotion",
    "p5_p6_p8_r52_p7_release_remain_false", "next_decision_auto_execution_allowed",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "local_received_zip_refs",
    "local_received_zip_ref_count", "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "claim_boundary_refs",
    "claim_boundary_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_ex18_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_EX18_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _mn10_function_boundary_rows() -> list[dict[str, str | bool]]:
    rows: list[dict[str, str | bool]] = []
    for kind, refs in (
        ("primary_builder", P7_R54_AHR_POST_EX18_MN10_PRIMARY_BUILDER_FUNCTION_REFS),
        ("primary_contract_assertion", P7_R54_AHR_POST_EX18_MN10_PRIMARY_ASSERT_FUNCTION_REFS),
        ("bodyfree_alias_builder", P7_R54_AHR_POST_EX18_MN10_ALIAS_BUILDER_FUNCTION_REFS),
        ("bodyfree_alias_contract_assertion", P7_R54_AHR_POST_EX18_MN10_ALIAS_ASSERT_FUNCTION_REFS),
    ):
        for ref in refs:
            rows.append(
                {
                    "function_ref": ref,
                    "function_kind_ref": kind,
                    "boundary_scope_ref": P7_R54_AHR_POST_EX18_SCOPE,
                    "postcr22_existing_function_renamed": False,
                    "cr_cs_ex_prefix_changed": False,
                    "executes_actual_review": False,
                    "generates_bodyfull_packet": False,
                    "creates_actual_rows": False,
                    "creates_question_text": False,
                    "changes_api_db_rn_runtime": False,
                    "allows_downstream_promotion": False,
                    "body_free": True,
                }
            )
    return rows


def _mn10_function_refs_resolved(refs: Sequence[str]) -> bool:
    module_globals = globals()
    return all(callable(module_globals.get(ref)) for ref in refs)


def _mn10_blockers(validation_command_matrix_result_memo_envelope: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(validation_command_matrix_result_memo_envelope, Mapping):
        blockers.append("mn09_validation_command_matrix_result_memo_envelope_missing")
    else:
        try:
            assert_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope_contract(
                validation_command_matrix_result_memo_envelope
            )
        except ValueError:
            blockers.append("mn09_validation_command_matrix_result_memo_envelope_contract_invalid")
        if validation_command_matrix_result_memo_envelope.get("mn09_ready") is not True:
            blockers.append("mn09_validation_command_matrix_result_memo_envelope_not_ready")
        if validation_command_matrix_result_memo_envelope.get("validation_command_matrix_ready") is not True:
            blockers.append("mn09_validation_command_matrix_not_ready")
        if validation_command_matrix_result_memo_envelope.get("result_memo_envelope_ready") is not True:
            blockers.append("mn09_result_memo_envelope_not_ready")
        if validation_command_matrix_result_memo_envelope.get("next_required_step") != P7_R54_AHR_POST_EX18_MN10_STEP_REF:
            blockers.append("mn09_next_required_step_not_mn10")
    if not _mn10_function_refs_resolved(P7_R54_AHR_POST_EX18_MN10_PRIMARY_BUILDER_FUNCTION_REFS):
        blockers.append("mn10_primary_builder_function_refs_not_resolved")
    if not _mn10_function_refs_resolved(P7_R54_AHR_POST_EX18_MN10_PRIMARY_ASSERT_FUNCTION_REFS):
        blockers.append("mn10_primary_assert_function_refs_not_resolved")
    if not _mn10_function_refs_resolved(P7_R54_AHR_POST_EX18_MN10_ALIAS_BUILDER_FUNCTION_REFS):
        blockers.append("mn10_alias_builder_function_refs_not_resolved")
    if not _mn10_function_refs_resolved(P7_R54_AHR_POST_EX18_MN10_ALIAS_ASSERT_FUNCTION_REFS):
        blockers.append("mn10_alias_assert_function_refs_not_resolved")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
    *,
    validation_command_matrix_result_memo_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN10 body-free alias / contract function boundary material."""

    session_id = _safe_review_session_id(review_session_id)
    mn09 = validation_command_matrix_result_memo_envelope
    if mn09 is None:
        mn09 = build_p7_r54_ahr_post_ex18_mn09_validation_command_matrix_result_memo_envelope(
            review_session_id=session_id
        )
    blockers = _mn10_blockers(mn09)
    ready = not blockers
    false_flags = _false_flags()
    boundary_rows = _mn10_function_boundary_rows()
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN10_ALIAS_CONTRACT_FUNCTION_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN10_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn09_schema_version": _clean_ref(mn09.get("schema_version") if isinstance(mn09, Mapping) else "", default="mn09_schema_missing", max_length=220),
        "mn09_material_ref": _clean_ref(mn09.get("material_id") if isinstance(mn09, Mapping) else "", default="mn09_material_missing", max_length=220),
        "mn09_status_ref": _clean_ref(mn09.get("mn09_status_ref") if isinstance(mn09, Mapping) else "", default="mn09_status_missing", max_length=180),
        "mn09_ready": bool(isinstance(mn09, Mapping) and mn09.get("mn09_ready") is True),
        "mn09_next_required_step": _clean_ref(mn09.get("next_required_step") if isinstance(mn09, Mapping) else "", default="mn09_next_required_step_missing", max_length=220),
        "mn09_validation_command_matrix_ready": bool(isinstance(mn09, Mapping) and mn09.get("validation_command_matrix_ready") is True),
        "mn09_result_memo_envelope_ready": bool(isinstance(mn09, Mapping) and mn09.get("result_memo_envelope_ready") is True),
        "mn10_status_ref": P7_R54_AHR_POST_EX18_MN10_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN10_BLOCKED_STATUS_REF,
        "mn10_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN10_ALLOWED_STATUS_REFS),
        "mn10_ready": ready,
        "mn10_blocker_refs": blockers,
        "mn10_blocker_ref_count": len(blockers),
        "mn10_reason_refs": ["mn10_alias_contract_function_boundary_ready_bodyfree"] if ready else [],
        "mn10_reason_ref_count": 1 if ready else 0,
        "alias_contract_function_boundary_ref": P7_R54_AHR_POST_EX18_MN10_ALIAS_CONTRACT_BOUNDARY_REF,
        "function_boundary_group_refs": list(P7_R54_AHR_POST_EX18_MN10_FUNCTION_BOUNDARY_GROUP_REFS),
        "function_boundary_group_ref_count": len(P7_R54_AHR_POST_EX18_MN10_FUNCTION_BOUNDARY_GROUP_REFS),
        "primary_builder_function_refs": list(P7_R54_AHR_POST_EX18_MN10_PRIMARY_BUILDER_FUNCTION_REFS),
        "primary_builder_function_ref_count": len(P7_R54_AHR_POST_EX18_MN10_PRIMARY_BUILDER_FUNCTION_REFS),
        "primary_assert_function_refs": list(P7_R54_AHR_POST_EX18_MN10_PRIMARY_ASSERT_FUNCTION_REFS),
        "primary_assert_function_ref_count": len(P7_R54_AHR_POST_EX18_MN10_PRIMARY_ASSERT_FUNCTION_REFS),
        "alias_builder_function_refs": list(P7_R54_AHR_POST_EX18_MN10_ALIAS_BUILDER_FUNCTION_REFS),
        "alias_builder_function_ref_count": len(P7_R54_AHR_POST_EX18_MN10_ALIAS_BUILDER_FUNCTION_REFS),
        "alias_assert_function_refs": list(P7_R54_AHR_POST_EX18_MN10_ALIAS_ASSERT_FUNCTION_REFS),
        "alias_assert_function_ref_count": len(P7_R54_AHR_POST_EX18_MN10_ALIAS_ASSERT_FUNCTION_REFS),
        "function_boundary_rows": boundary_rows,
        "function_boundary_row_count": len(boundary_rows),
        "function_refs_resolved_in_module": ready,
        "contract_assertion_refs_resolved_in_module": ready,
        "existing_postcr22_helper_rename_forbidden": True,
        "existing_postcr22_helper_function_boundary_preserved": True,
        "existing_cr_cs_ex_prefix_boundary_preserved": True,
        "mn_prefix_internal_to_postex18_manual_next_decision_only": True,
        "postex18_helper_does_not_reimplement_postcr22_ex07_ex18": True,
        "function_boundary_does_not_execute_actual_review": True,
        "function_boundary_does_not_generate_bodyfull_packet": True,
        "function_boundary_does_not_create_actual_rows": True,
        "function_boundary_does_not_create_question_text": True,
        "function_boundary_does_not_materialize_json_or_schema_files": True,
        "function_boundary_does_not_change_api_db_rn_runtime_response_keys": True,
        "function_boundary_does_not_allow_downstream_promotion": True,
        "forbidden_function_boundary_claim_refs": list(P7_R54_AHR_POST_EX18_MN10_FORBIDDEN_FUNCTION_BOUNDARY_CLAIM_REFS),
        "forbidden_function_boundary_claim_ref_count": len(P7_R54_AHR_POST_EX18_MN10_FORBIDDEN_FUNCTION_BOUNDARY_CLAIM_REFS),
        "next_decision_auto_execution_allowed": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN10_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN09_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_EX18_MN11_STEP_REF if ready else P7_R54_AHR_POST_EX18_MN10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN10_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN10 alias / contract function boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN10_ALIAS_CONTRACT_FUNCTION_BOUNDARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN10_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN10 alias / contract function boundary",
    )
    if tuple(data.get("mn10_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN10_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 allowed status refs changed")
    for field, count_field in (
        ("mn10_blocker_refs", "mn10_blocker_ref_count"),
        ("mn10_reason_refs", "mn10_reason_ref_count"),
        ("function_boundary_group_refs", "function_boundary_group_ref_count"),
        ("primary_builder_function_refs", "primary_builder_function_ref_count"),
        ("primary_assert_function_refs", "primary_assert_function_ref_count"),
        ("alias_builder_function_refs", "alias_builder_function_ref_count"),
        ("alias_assert_function_refs", "alias_assert_function_ref_count"),
        ("function_boundary_rows", "function_boundary_row_count"),
        ("forbidden_function_boundary_claim_refs", "forbidden_function_boundary_claim_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN10 {count_field} changed")
    if tuple(data.get("function_boundary_group_refs") or ()) != P7_R54_AHR_POST_EX18_MN10_FUNCTION_BOUNDARY_GROUP_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 function boundary groups changed")
    if tuple(data.get("primary_builder_function_refs") or ()) != P7_R54_AHR_POST_EX18_MN10_PRIMARY_BUILDER_FUNCTION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 primary builder refs changed")
    if tuple(data.get("primary_assert_function_refs") or ()) != P7_R54_AHR_POST_EX18_MN10_PRIMARY_ASSERT_FUNCTION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 primary assert refs changed")
    if tuple(data.get("alias_builder_function_refs") or ()) != P7_R54_AHR_POST_EX18_MN10_ALIAS_BUILDER_FUNCTION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 alias builder refs changed")
    if tuple(data.get("alias_assert_function_refs") or ()) != P7_R54_AHR_POST_EX18_MN10_ALIAS_ASSERT_FUNCTION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 alias assert refs changed")
    if tuple(data.get("forbidden_function_boundary_claim_refs") or ()) != P7_R54_AHR_POST_EX18_MN10_FORBIDDEN_FUNCTION_BOUNDARY_CLAIM_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 forbidden claim refs changed")
    if data.get("function_boundary_rows") != _mn10_function_boundary_rows():
        raise ValueError("P7-R54-AHR-PostEX18-MN10 function boundary rows changed")
    for row in data.get("function_boundary_rows") or []:
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-PostEX18-MN10 function row must be a mapping")
        for key in (
            "postcr22_existing_function_renamed", "cr_cs_ex_prefix_changed", "executes_actual_review",
            "generates_bodyfull_packet", "creates_actual_rows", "creates_question_text",
            "changes_api_db_rn_runtime", "allows_downstream_promotion",
        ):
            if row.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostEX18-MN10 function row violates boundary: {key}")
        if row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 function row must be body-free")
    for key in (
        "existing_postcr22_helper_rename_forbidden",
        "existing_cr_cs_ex_prefix_boundary_preserved",
        "mn_prefix_internal_to_postex18_manual_next_decision_only",
        "postex18_helper_does_not_reimplement_postcr22_ex07_ex18",
        "function_boundary_does_not_execute_actual_review",
        "function_boundary_does_not_generate_bodyfull_packet",
        "function_boundary_does_not_create_actual_rows",
        "function_boundary_does_not_create_question_text",
        "function_boundary_does_not_materialize_json_or_schema_files",
        "function_boundary_does_not_change_api_db_rn_runtime_response_keys",
        "function_boundary_does_not_allow_downstream_promotion",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN10 required true boundary changed: {key}")
    if data.get("next_decision_auto_execution_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 cannot allow auto execution")
    ready = data.get("mn10_status_ref") == P7_R54_AHR_POST_EX18_MN10_READY_STATUS_REF
    if data.get("mn10_ready") is not ready or data.get("function_refs_resolved_in_module") is not ready or data.get("contract_assertion_refs_resolved_in_module") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN10 ready flag changed")
    if ready:
        if data.get("mn10_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 ready material cannot carry blockers")
        if data.get("mn10_reason_refs") != ["mn10_alias_contract_function_boundary_ready_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 ready reason changed")
        if data.get("mn09_ready") is not True or data.get("mn09_validation_command_matrix_ready") is not True or data.get("mn09_result_memo_envelope_ready") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 ready material requires ready MN09")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN10_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN11_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 next step changed")
    else:
        if data.get("mn10_status_ref") != P7_R54_AHR_POST_EX18_MN10_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 blocked status changed")
        if not data.get("mn10_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN10 blocked material must carry blockers")
        if data.get("mn10_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 blocked material cannot carry ready reasons")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN10 blocked next step changed")
    return True


def _mn11_acceptance_condition_rows(*, ready: bool) -> list[dict[str, str | bool]]:
    return [
        {
            "condition_ref": condition_ref,
            "satisfied": ready,
            "required_for_ready": True,
            "auto_executes_downstream": False,
            "body_free": True,
        }
        for condition_ref in P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_CONDITION_REFS
    ]


def _mn11_blockers(alias_contract_function_boundary: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(alias_contract_function_boundary, Mapping):
        blockers.append("mn10_alias_contract_function_boundary_missing")
    else:
        try:
            assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(alias_contract_function_boundary)
        except ValueError:
            blockers.append("mn10_alias_contract_function_boundary_contract_invalid")
        if alias_contract_function_boundary.get("mn10_ready") is not True:
            blockers.append("mn10_alias_contract_function_boundary_not_ready")
        if alias_contract_function_boundary.get("next_required_step") != P7_R54_AHR_POST_EX18_MN11_STEP_REF:
            blockers.append("mn10_next_required_step_not_mn11")
        if alias_contract_function_boundary.get("function_boundary_does_not_allow_downstream_promotion") is not True:
            blockers.append("mn10_function_boundary_downstream_promotion_guard_missing")
        if alias_contract_function_boundary.get("existing_postcr22_helper_rename_forbidden") is not True:
            blockers.append("mn10_existing_postcr22_rename_boundary_missing")
    return _dedupe_refs(blockers)


def build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
    *,
    alias_contract_function_boundary: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_EX18_MN11_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build MN11 final body-free acceptance / fail-closed material."""

    session_id = _safe_review_session_id(review_session_id)
    mn10 = alias_contract_function_boundary
    if mn10 is None:
        mn10 = build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(review_session_id=session_id)
    blockers = _mn11_blockers(mn10)
    ready = not blockers
    false_flags = _false_flags()
    final_manual_decision_ref = (
        P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF
        if ready else P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_HOLD_EX18_INVALID_REF
    )
    manual_status_ref = (
        P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_READY_STATUS_REF
        if ready else P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_BLOCKED_STATUS_REF
    )
    final_next_ref = (
        P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF
        if ready else P7_R54_AHR_POST_EX18_MN11_BLOCKED_NEXT_REQUIRED_STEP_REF
    )
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_FAIL_CLOSED_FINALIZER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_EX18_STEP,
        "scope": P7_R54_AHR_POST_EX18_SCOPE,
        "policy_kind": P7_R54_AHR_POST_EX18_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_EX18_MN11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_EX18_MN11_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "mn10_schema_version": _clean_ref(mn10.get("schema_version") if isinstance(mn10, Mapping) else "", default="mn10_schema_missing", max_length=220),
        "mn10_material_ref": _clean_ref(mn10.get("material_id") if isinstance(mn10, Mapping) else "", default="mn10_material_missing", max_length=220),
        "mn10_status_ref": _clean_ref(mn10.get("mn10_status_ref") if isinstance(mn10, Mapping) else "", default="mn10_status_missing", max_length=180),
        "mn10_ready": bool(isinstance(mn10, Mapping) and mn10.get("mn10_ready") is True),
        "mn10_next_required_step": _clean_ref(mn10.get("next_required_step") if isinstance(mn10, Mapping) else "", default="mn10_next_required_step_missing", max_length=220),
        "mn10_alias_contract_function_boundary_ready": bool(isinstance(mn10, Mapping) and mn10.get("function_boundary_does_not_allow_downstream_promotion") is True),
        "mn11_status_ref": P7_R54_AHR_POST_EX18_MN11_READY_STATUS_REF if ready else P7_R54_AHR_POST_EX18_MN11_BLOCKED_STATUS_REF,
        "mn11_allowed_status_refs": list(P7_R54_AHR_POST_EX18_MN11_ALLOWED_STATUS_REFS),
        "mn11_ready": ready,
        "mn11_blocker_refs": blockers,
        "mn11_blocker_ref_count": len(blockers),
        "mn11_reason_refs": ["mn11_acceptance_fail_closed_finalizer_ready_return_to_actual_review_operation_required"] if ready else [],
        "mn11_reason_ref_count": 1 if ready else 0,
        "acceptance_fail_closed_finalizer_ref": P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_FINALIZER_REF,
        "result_memo_ref": _clean_ref(result_memo_ref, default=P7_R54_AHR_POST_EX18_MN11_RESULT_MEMO_REF, max_length=220),
        "final_manual_decision_ref": final_manual_decision_ref,
        "manual_decision_ref": final_manual_decision_ref,
        "manual_decision_status_ref": manual_status_ref,
        "actual_review_evidence_status_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_MISSING_REAL_REVIEW_REQUIRED_REF,
        "return_to_actual_review_operation_required": ready,
        "actual_local_only_human_review_operation_required_before_downstream_decision": ready,
        "final_next_required_step_ref": final_next_ref,
        "acceptance_condition_refs": list(P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_CONDITION_REFS),
        "acceptance_condition_ref_count": len(P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_CONDITION_REFS),
        "acceptance_condition_rows": _mn11_acceptance_condition_rows(ready=ready),
        "acceptance_condition_row_count": len(P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_CONDITION_REFS),
        "fail_closed_condition_refs": list(P7_R54_AHR_POST_EX18_MN11_FAIL_CLOSED_CONDITION_REFS),
        "fail_closed_condition_ref_count": len(P7_R54_AHR_POST_EX18_MN11_FAIL_CLOSED_CONDITION_REFS),
        "fail_closed_blocker_refs": blockers,
        "fail_closed_blocker_ref_count": len(blockers),
        "not_claimed_boundary_refs_for_finalizer": list(P7_R54_AHR_POST_EX18_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count_for_finalizer": len(P7_R54_AHR_POST_EX18_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "manual_decision_ref_is_return_to_actual_review_operation_required": ready,
        "return_to_actual_review_operation_required_true": ready,
        "actual_review_evidence_complete_from_real_review_false": True,
        "actual_review_evidence_complete_from_real_review_accepted_false": True,
        "next_required_step_is_actual_local_only_human_review_operation_required_before_p5_p6_p8_r52_decision": ready,
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_path_hash_validation_passed": ready,
        "no_touch_boundary_confirmed": ready,
        "no_promotion_boundary_confirmed": ready,
        "acceptance_ready": ready,
        "finalizer_ready_for_result_memo": ready,
        "final_result_is_bodyfree_hold": ready,
        "finalizer_does_not_execute_actual_review": True,
        "finalizer_does_not_generate_bodyfull_packet": True,
        "finalizer_does_not_create_actual_rows": True,
        "finalizer_does_not_create_question_text": True,
        "finalizer_does_not_change_api_db_rn_runtime_response_keys": True,
        "finalizer_does_not_allow_downstream_promotion": True,
        "p5_p6_p8_r52_p7_release_remain_false": True,
        "next_decision_auto_execution_allowed": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_EX18_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_EX18_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "claim_boundary_refs": list(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_EX18_CLAIM_BOUNDARY_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_EX18_MN11_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_EX18_MN11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_EX18_MN10_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": final_next_ref,
        "public_contract": public_contract_flags(),
        "post_ex18_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **false_flags,
        "body_free": True,
    }
    return material


def assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_EX18_MN11_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostEX18-MN11 acceptance / fail-closed finalizer",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_FAIL_CLOSED_FINALIZER_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_EX18_MN11_STEP_REF,
        source="P7-R54-AHR-PostEX18-MN11 acceptance / fail-closed finalizer",
        allowed_true_false_flag_refs=(),
    )
    if tuple(data.get("mn11_allowed_status_refs") or ()) != P7_R54_AHR_POST_EX18_MN11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN11 allowed status refs changed")
    for field, count_field in (
        ("mn11_blocker_refs", "mn11_blocker_ref_count"),
        ("mn11_reason_refs", "mn11_reason_ref_count"),
        ("acceptance_condition_refs", "acceptance_condition_ref_count"),
        ("acceptance_condition_rows", "acceptance_condition_row_count"),
        ("fail_closed_condition_refs", "fail_closed_condition_ref_count"),
        ("fail_closed_blocker_refs", "fail_closed_blocker_ref_count"),
        ("not_claimed_boundary_refs_for_finalizer", "not_claimed_boundary_ref_count_for_finalizer"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostEX18-MN11 {count_field} changed")
    if tuple(data.get("acceptance_condition_refs") or ()) != P7_R54_AHR_POST_EX18_MN11_ACCEPTANCE_CONDITION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN11 acceptance conditions changed")
    if tuple(data.get("fail_closed_condition_refs") or ()) != P7_R54_AHR_POST_EX18_MN11_FAIL_CLOSED_CONDITION_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN11 fail-closed conditions changed")
    if tuple(data.get("not_claimed_boundary_refs_for_finalizer") or ()) != P7_R54_AHR_POST_EX18_MN11_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostEX18-MN11 finalizer not-claimed refs changed")
    for row in data.get("acceptance_condition_rows") or []:
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-PostEX18-MN11 acceptance row must be a mapping")
        if row.get("required_for_ready") is not True or row.get("auto_executes_downstream") is not False:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 acceptance row boundary changed")
        if row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 acceptance row must be body-free")
    for key in (
        "actual_review_evidence_complete_from_real_review_false",
        "finalizer_does_not_execute_actual_review",
        "finalizer_does_not_generate_bodyfull_packet",
        "finalizer_does_not_create_actual_rows",
        "finalizer_does_not_create_question_text",
        "finalizer_does_not_change_api_db_rn_runtime_response_keys",
        "finalizer_does_not_allow_downstream_promotion",
        "p5_p6_p8_r52_p7_release_remain_false",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostEX18-MN11 required true boundary changed: {key}")
    if data.get("next_decision_auto_execution_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostEX18-MN11 cannot allow auto execution")
    ready = data.get("mn11_status_ref") == P7_R54_AHR_POST_EX18_MN11_READY_STATUS_REF
    if data.get("mn11_ready") is not ready or data.get("acceptance_ready") is not ready or data.get("finalizer_ready_for_result_memo") is not ready:
        raise ValueError("P7-R54-AHR-PostEX18-MN11 ready flag changed")
    if ready:
        if data.get("mn11_blocker_refs") != [] or data.get("fail_closed_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 ready material cannot carry blockers")
        if data.get("mn11_reason_refs") != ["mn11_acceptance_fail_closed_finalizer_ready_return_to_actual_review_operation_required"]:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 ready reason changed")
        for key in (
            "manual_decision_ref_is_return_to_actual_review_operation_required",
            "return_to_actual_review_operation_required_true",
            "next_required_step_is_actual_local_only_human_review_operation_required_before_p5_p6_p8_r52_decision",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_path_hash_validation_passed",
            "no_touch_boundary_confirmed",
            "no_promotion_boundary_confirmed",
            "final_result_is_bodyfree_hold",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostEX18-MN11 ready condition changed: {key}")
        if any(row.get("satisfied") is not True for row in data.get("acceptance_condition_rows") or []):
            raise ValueError("P7-R54-AHR-PostEX18-MN11 ready acceptance rows must be satisfied")
        if data.get("final_manual_decision_ref") != P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 final decision changed")
        if data.get("manual_decision_ref") != P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 manual decision changed")
        if data.get("manual_decision_status_ref") != P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 manual status changed")
        if data.get("return_to_actual_review_operation_required") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 return operation requirement changed")
        if data.get("actual_local_only_human_review_operation_required_before_downstream_decision") is not True:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 actual review operation requirement changed")
        if data.get("final_next_required_step_ref") != P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 final next required step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN11_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_EX18_MN11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 next required step changed")
    else:
        if data.get("mn11_status_ref") != P7_R54_AHR_POST_EX18_MN11_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 blocked status changed")
        if not data.get("mn11_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostEX18-MN11 blocked material must carry blockers")
        if data.get("mn11_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 blocked material cannot carry ready reasons")
        if any(row.get("satisfied") is not False for row in data.get("acceptance_condition_rows") or []):
            raise ValueError("P7-R54-AHR-PostEX18-MN11 blocked acceptance rows cannot be satisfied")
        if data.get("next_required_step") != P7_R54_AHR_POST_EX18_MN11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostEX18-MN11 blocked next step changed")
    return True


def build_p7_r54_ahr_post_ex18_manual_next_decision_alias_contract_function_boundary_bodyfree(
    *,
    validation_command_matrix_result_memo_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
        validation_command_matrix_result_memo_envelope=validation_command_matrix_result_memo_envelope,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_alias_contract_function_boundary_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_acceptance_fail_closed_finalizer_bodyfree(
    *,
    alias_contract_function_boundary: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_EX18_MN11_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=alias_contract_function_boundary,
        result_memo_ref=result_memo_ref,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_acceptance_fail_closed_finalizer_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(data)


def build_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_bodyfree(
    *,
    validation_command_matrix_result_memo_envelope: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_EX18_MN11_RESULT_MEMO_REF,
    review_session_id: Any = None,
) -> dict[str, Any]:
    session_id = _safe_review_session_id(review_session_id)
    mn10 = build_p7_r54_ahr_post_ex18_mn10_alias_contract_function_boundary(
        validation_command_matrix_result_memo_envelope=validation_command_matrix_result_memo_envelope,
        review_session_id=session_id,
    )
    return build_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer(
        alias_contract_function_boundary=mn10,
        result_memo_ref=result_memo_ref,
        review_session_id=session_id,
    )


def assert_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(data)
