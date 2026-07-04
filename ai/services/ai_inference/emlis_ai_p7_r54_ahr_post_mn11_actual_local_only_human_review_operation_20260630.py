# -*- coding: utf-8 -*-
"""Post-MN11 R54-AHR actual local-only human review operation helpers.

PMN-OP00 through PMN-OP23 intentionally form the first, small
body-free bridge after the Post-EX18 MN11 manual decision:

* PMN-OP00 freezes the Post-MN11 actual local-only human review operation
  scope, no-touch boundary, and no-promotion boundary.
* PMN-OP01 intakes the MN11 body-free manual decision material and confirms
  that the next step remains actual local-only human review operation with the
  current received snapshot basis.
* PMN-OP02 inventories the existing OP / EX / MN support material and keeps the
  implementation on a minimal bridge rather than a new giant wrapper.
* PMN-OP03 freezes the review session envelope and actual-source guard so
  helper / unit-test / synthetic / historical rows cannot be promoted to actual
  human review evidence.
* PMN-OP04 freezes the local-only preflight and explicit-allow boundary without
  generating body-full packets.
* PMN-OP05 refreezes the 24-case manifest as body-free controller/reviewer
  refs without materializing reviewer packet content.
* PMN-OP06 builds the body-free packet generation request without executing
  body-full packet generation.
* PMN-OP07 freezes the local operation receipt boundary without accepting
  packet content, local paths, hashes, or terminal output.
* PMN-OP08 freezes the packet completeness / export denylist scan, and only
  passes it when a body-free local packet generation receipt is supplied.
* PMN-OP09 freezes the reviewer-person / selection-only form boundary after
  OP08 passes, without starting actual human review.
* PMN-OP10 intakes only body-free actual review state capture and keeps the
  execution protocol separate from helper/unit-test rows.
* PMN-OP11 intakes only a body-free actual operation receipt and does not
  create sanitized rows, rating rows, question observation rows, disposal
  receipts, or downstream promotion.
* PMN-OP12 intakes only body-free sanitized review result rows supplied from
  actual-person selection-only review evidence, and blocks helper / unit-test /
  synthetic / historical rows from being promoted.
* PMN-OP13 normalizes rating rows and threshold summaries from accepted
  sanitized rows as decision material only, without P5 finalization.
* PMN-OP14 classifies readfeel / label connection / safe display / blocker
  refs from body-free rating material without escaping repair/blocker cases to
  P8 candidate material.
* PMN-OP15 normalizes question-need observation rows as P7/P8 Bridge material
  without materializing question text, triggers, storage, P8 spec, or P8 start.
* PMN-OP16 guards rating/question consistency so blocker, weak-rating,
  insufficient, or heavy-observation cases cannot escape into P8 candidate
  material.
* PMN-OP17 intakes a supplied body-free disposal / purge receipt boundary and
  keeps disposal verification, no-leak validation, and evidence completion for
  later steps.
* PMN-OP18 performs final no-body / no-question / no-path / no-hash / no-touch
  validation across supplied body-free artifacts after OP17.
* PMN-OP19 evaluates the actual_review_evidence_complete predicate from body-free
  evidence without promoting P5/P6/P8/R52/P7/release decisions.
* PMN-OP20 separates P5/P6/P8/R52 downstream material as candidate-only
  decisions without finalization, start, execution, completion, or release.
* PMN-OP21 maps the Post-MN11 body-free evidence bundle back to the
  existing PostCR22 EX07-EX18 line without executing that re-entry here.
* PMN-OP22 builds the validation command matrix and result memo envelope as
  body-free material without claiming actual command execution or full-suite
  green.
* PMN-OP23 finalizes acceptance / fail-closed status for the Post-MN11 bridge
  without promoting downstream P5/P6/P8/R52/P7/release decisions.

This module does not generate body-full packets, does not run actual local human
review, does not create actual review rows outside supplied body-free evidence,
does not create question text, schemas, JSON files, API routes, DB
migrations, RN UI, runtime changes, R52 execution, P5 finalization, P6/P8 start,
P7 completion, or release decisions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import P7_PHASE, P7_SOURCE_MODE, clean_identifier, public_contract_flags
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex
import emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630 as mn


P7_R54_AHR_POST_MN11_PMN_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op00_scope_no_touch_no_promotion_boundary_freeze.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP01_MN11_MANUAL_DECISION_INTAKE_BASIS_CONFIRMATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op01_mn11_manual_decision_intake_basis_confirmation.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP02_EXISTING_OP_EX_MN_SUPPORT_MATERIAL_INVENTORY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op02_existing_op_ex_mn_support_material_inventory.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP03_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op03_review_session_envelope_actual_source_guard_freeze.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op04_local_only_preflight_explicit_allow_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP05_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op05_24_case_manifest_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_BUILDER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op06_body_full_packet_generation_request_bodyfree_builder.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_LOCAL_OPERATION_RECEIPT_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op07_packet_generation_local_operation_receipt_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op08_packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op09_reviewer_person_boundary_selection_only_form_freeze.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP10_ACTUAL_24_CASE_HUMAN_REVIEW_EXECUTION_PROTOCOL_STATE_CAPTURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op10_actual_24_case_human_review_execution_protocol_state_capture.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP11_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op11_actual_operation_receipt_intake.bodyfree.v1"
)

P7_R54_AHR_POST_MN11_STEP: Final = "R54-AHR-PostMN11_ActualLocalOnlyHumanReviewOperation_20260630"
P7_R54_AHR_POST_MN11_SCOPE: Final = (
    "p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_evidence_intake_reentry"
)
P7_R54_AHR_POST_MN11_POLICY_KIND: Final = (
    "r54_ahr_post_mn11_actual_local_only_human_review_operation_bodyfree_boundary"
)
P7_R54_AHR_POST_MN11_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postmn11_actual_local_review_session_20260630_"
    "current_received_264_85_258_171_v1"
)
P7_R54_AHR_POST_MN11_CHOSEN_STAGE_REF: Final = (
    "P7-R54-AHR Post-MN11 Actual Local-only Human Review Operation / Evidence Intake Re-entry"
)

P7_R54_AHR_POST_MN11_PMN_OP00_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP00_scope_no_touch_no_promotion_boundary_freeze"
)
P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP01_mn11_manual_decision_intake_basis_confirmation"
)
P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP02_existing_op_ex_mn_support_material_inventory"
)
P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP03_review_session_envelope_actual_source_guard_freeze"
)
P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP04_local_only_preflight_explicit_allow_boundary"
)
P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP05_24_case_manifest_refreeze"
)
P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP06_body_full_packet_generation_request_bodyfree_builder"
)
P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP07_packet_generation_local_operation_receipt_boundary"
)
P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP08_packet_completeness_export_denylist_scan"
)
P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP09_reviewer_person_boundary_selection_only_form_freeze"
)
P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP10_actual_24_case_human_review_execution_protocol_state_capture"
)
P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP11_actual_operation_receipt_intake"
)
P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP12_sanitized_review_result_rows_intake_provenance_guard"
)
P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP13_rating_row_normalization_threshold_summary"
)
P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP14_readfeel_label_connection_safe_display_blocker_classification"
)
P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP15_question_need_observation_row_normalization"
)
P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP16_rating_question_consistency_guard"
)
P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP17_disposal_purge_receipt_intake"
)
P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP18_final_no_body_no_question_no_path_no_hash_no_touch_validation"
)
P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP19_actual_review_evidence_complete_predicate"
)
P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP20_p5_p6_p8_r52_candidate_only_separation"
)
P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP21_existing_postcr22_ex07_ex18_reentry_mapping"
)
P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP22_validation_command_matrix_result_memo_envelope"
)
P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF: Final = (
    "R54-AHR-PostMN11-PMN-OP23_acceptance_fail_closed_finalizer"
)
P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op01_mn11_manual_decision_intake_basis_confirmation_or_stop"
)

P7_R54_AHR_POST_MN11_PMN_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP00_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF,
    P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP00_STEP_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[1:]
)
P7_R54_AHR_POST_MN11_PMN_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:2]
)
P7_R54_AHR_POST_MN11_PMN_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[2:]
)
P7_R54_AHR_POST_MN11_PMN_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:3]
)
P7_R54_AHR_POST_MN11_PMN_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[3:]
)
P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:4]
)
P7_R54_AHR_POST_MN11_PMN_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[4:]
)
P7_R54_AHR_POST_MN11_PMN_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:5]
)
P7_R54_AHR_POST_MN11_PMN_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[5:]
)
P7_R54_AHR_POST_MN11_PMN_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:6]
)
P7_R54_AHR_POST_MN11_PMN_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[6:]
)
P7_R54_AHR_POST_MN11_PMN_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:7]
)
P7_R54_AHR_POST_MN11_PMN_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[7:]
)
P7_R54_AHR_POST_MN11_PMN_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:8]
)
P7_R54_AHR_POST_MN11_PMN_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[8:]
)
P7_R54_AHR_POST_MN11_PMN_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:9]
)
P7_R54_AHR_POST_MN11_PMN_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[9:]
)
P7_R54_AHR_POST_MN11_PMN_OP09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:10]
)
P7_R54_AHR_POST_MN11_PMN_OP09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[10:]
)
P7_R54_AHR_POST_MN11_PMN_OP10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:11]
)
P7_R54_AHR_POST_MN11_PMN_OP10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[11:]
)
P7_R54_AHR_POST_MN11_PMN_OP11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:12]
)
P7_R54_AHR_POST_MN11_PMN_OP11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[12:]
)

P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT: Final = 24
P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF: Final = mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_REF
P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = (
    mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_BASIS_ALLOWED_REF
)
P7_R54_AHR_POST_MN11_MANUAL_DECISION_REF: Final = (
    mn.P7_R54_AHR_POST_EX18_MN03_MANUAL_DECISION_RETURN_OPERATION_REQUIRED_REF
)
P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_EVIDENCE_STATUS_REF: Final = (
    mn.P7_R54_AHR_POST_EX18_ACTUAL_REVIEW_EVIDENCE_MISSING_REAL_REVIEW_REQUIRED_REF
)
P7_R54_AHR_POST_MN11_NEXT_REQUIRED_STEP_REF: Final = mn.P7_R54_AHR_POST_EX18_MN03_RETURN_NEXT_REQUIRED_STEP_REF
P7_R54_AHR_POST_MN11_MN11_RESULT_MEMO_REF: Final = mn.P7_R54_AHR_POST_EX18_MN11_RESULT_MEMO_REF

P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(271).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(88).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(7).zip",
    "rn_zip_ref": "Cocolon(261).zip",
    "backend_zip_ref": "mashos-api(174).zip",
}
P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R54AHR_PostMN11_ActualLocalOnlyHumanReviewOperation_PreDesignMemo_20260630.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostMN11_ActualLocalOnlyHumanReviewOperation_DetailedDesign_ImplementationOrder_20260630.md",
    "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "ai/services/ai_inference/emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.py",
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629.py",
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630.py",
)

P7_R54_AHR_POST_MN11_PMN_OP01_READY_STATUS_REF: Final = "PMN_OP01_MN11_MANUAL_DECISION_INTAKE_READY"
P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_STATUS_REF: Final = "PMN_OP01_MN11_MANUAL_DECISION_INTAKE_BLOCKED"
P7_R54_AHR_POST_MN11_PMN_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP01_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP02_READY_STATUS_REF: Final = (
    "PMN_OP02_EXISTING_OP_EX_MN_SUPPORT_MATERIAL_INVENTORY_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_STATUS_REF: Final = (
    "PMN_OP02_EXISTING_OP_EX_MN_SUPPORT_MATERIAL_INVENTORY_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP02_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op02_existing_support_material_inventory_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP03_READY_STATUS_REF: Final = (
    "PMN_OP03_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_STATUS_REF: Final = (
    "PMN_OP03_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP03_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op03_review_session_envelope_actual_source_guard_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP04_READY_STATUS_REF: Final = (
    "PMN_OP04_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_STATUS_REF: Final = (
    "PMN_OP04_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP04_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op04_local_only_preflight_explicit_allow_boundary_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_REVIEW_ROOT_REF: Final = (
    "post_mn11_local_review_root_declared_outside_repo_export_scope_bodyfree"
)
P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF: Final = (
    "POST_MN11_ACTUAL_LOCAL_REVIEW_BODY_FULL_PACKET_GENERATION_ALLOWED_FOR_24CASE_REVIEW_ONLY_20260630"
)
P7_R54_AHR_POST_MN11_PMN_OP04_ALLOW_SCOPE_REF: Final = (
    "post_mn11_actual_review_local_only_body_full_packet_generation_for_24case_review_only"
)
P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF: Final = (
    "local_body_full_packet_max_72h_or_shorter"
)
P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF: Final = (
    "post_review_body_full_packet_and_notes_purge_required"
)
P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF: Final = (
    "deny_raw_body_question_text_path_hash_terminal_output"
)
P7_R54_AHR_POST_MN11_PMN_OP04_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op03_review_session_envelope_and_actual_source_guard_ready_bodyfree",
    "local_only_root_ref_explicitly_declared_bodyfree",
    "explicit_allow_ref_present_for_local_review_only_bodyfull_packet_generation",
    "retention_disposal_export_denylist_policies_present_bodyfree",
    "body_full_packet_generation_still_not_run_until_later_packet_request_step",
)
P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    "body_full_packet",
    "reviewer_notes",
    "temporary_form",
)
P7_R54_AHR_POST_MN11_PMN_OP05_READY_STATUS_REF: Final = (
    "PMN_OP05_24_CASE_MANIFEST_REFROZEN_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_STATUS_REF: Final = (
    "PMN_OP05_24_CASE_MANIFEST_REFREEZE_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP05_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op05_24_case_manifest_refreeze_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP05_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op04_local_only_preflight_explicit_allow_boundary_ready_bodyfree",
    "r54_p5_human_blind_qa_24_case_manifest_refrozen_bodyfree",
    "case_blind_packet_refs_unique_and_separated_bodyfree",
    "p4_r11_rows_not_confused_as_r54_review_rows",
    "body_full_packet_generation_still_not_run_until_pmn_op06_request_step",
)
P7_R54_AHR_POST_MN11_PMN_OP05_REVIEWER_IDENTIFIER_POLICY_REF: Final = (
    "reviewer_receives_blind_case_id_only_controller_keeps_case_refs"
)
P7_R54_AHR_POST_MN11_PMN_OP06_READY_STATUS_REF: Final = (
    "PMN_OP06_BODY_FULL_PACKET_GENERATION_REQUEST_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_STATUS_REF: Final = (
    "PMN_OP06_BODY_FULL_PACKET_GENERATION_REQUEST_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP06_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op06_body_full_packet_generation_request_bodyfree_builder_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF: Final = (
    "postmn11_body_full_packet_generation_request_ref_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP06_CASE_MANIFEST_REF: Final = (
    "postmn11_pmn_op05_24_case_manifest_refrozen_bodyfree"
)
P7_R54_AHR_POST_MN11_PMN_OP06_LOCAL_OPERATION_REF: Final = (
    "postmn11_local_only_body_full_packet_generation_operation_boundary_bodyfree"
)
P7_R54_AHR_POST_MN11_PMN_OP06_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op05_24_case_manifest_refrozen_ready_bodyfree",
    "explicit_allow_ref_carried_forward_from_op04_bodyfree",
    "required_case_count_and_manifest_counts_are_24_bodyfree",
    "request_requires_local_only_generation_and_must_not_export",
    "request_requires_packet_completeness_export_denylist_and_purge",
    "request_builder_does_not_generate_body_full_packet_here",
)
P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_REQUEST_FIELD_REFS: Final[tuple[str, ...]] = (
    "packet_generation_request_ref",
    "review_session_id",
    "actual_review_basis_ref",
    "required_case_count",
    "case_manifest_ref",
    "explicit_allow_ref",
    "local_only_required",
    "must_not_export",
    "packet_completeness_scan_required",
    "export_denylist_scan_required",
    "purge_required",
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP07_READY_STATUS_REF: Final = (
    "PMN_OP07_PACKET_GENERATION_LOCAL_OPERATION_RECEIPT_BOUNDARY_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_STATUS_REF: Final = (
    "PMN_OP07_PACKET_GENERATION_LOCAL_OPERATION_RECEIPT_BOUNDARY_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP07_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op07_packet_generation_local_operation_receipt_boundary_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_RECEIPT_BOUNDARY_REF: Final = (
    "postmn11_packet_generation_local_operation_receipt_boundary_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP07_EXPECTED_PACKET_GENERATION_RECEIPT_REF: Final = (
    "postmn11_actual_local_body_full_packet_generation_receipt_bodyfree_required_after_external_local_generation"
)
P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF: Final = (
    "actual_local_body_full_packet_generation_receipt_bodyfree"
)
P7_R54_AHR_POST_MN11_PMN_OP07_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op06_packet_generation_request_ready_bodyfree",
    "local_operation_receipt_boundary_defined_without_packet_content_path_hash_or_terminal_output",
    "future_receipt_must_prove_24_packets_local_only_and_no_export",
    "future_receipt_requires_body_free_counts_booleans_and_refs_only",
    "actual_packet_generation_receipt_not_received_or_promoted_here",
)
P7_R54_AHR_POST_MN11_PMN_OP08_READY_STATUS_REF: Final = (
    "PMN_OP08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_STATUS_REF: Final = (
    "PMN_OP08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "PMN_OP08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_BLOCKED_BY_EXPORT_DENYLIST_OR_BODY_LEAK"
)
P7_R54_AHR_POST_MN11_PMN_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP08_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_or_supply_actual_local_packet_generation_receipt_before_packet_scan_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP08_PACKET_SCAN_REF: Final = (
    "postmn11_packet_completeness_export_denylist_scan_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP08_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op07_packet_generation_local_operation_receipt_boundary_ready_bodyfree",
    "actual_local_packet_generation_receipt_received_bodyfree",
    "packet_count_and_packet_ref_count_are_24_bodyfree",
    "packet_completeness_scan_passed_bodyfree",
    "export_denylist_scan_passed_without_body_question_path_hash_terminal_output",
    "packet_scan_does_not_export_or_materialize_packet_content_here",
)
P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_PACKET_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "packet_generation_receipt_ref",
    "review_session_id",
    "packet_generation_request_ref",
    "actual_review_basis_ref",
    "actual_source_ref",
    "packet_materialized_local_only",
    "packet_count",
    "packet_ref_id_count",
    "packet_ref_ids",
    "body_full_exported",
    "local_absolute_path_included",
    "body_hash_stored",
    "terminal_output_body_included",
    "packet_content_included",
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_REVIEWER_PACKET_FIELD_REFS: Final[tuple[str, ...]] = (
    "current_input_review_surface_local_only",
    "returned_emlis_surface_local_only",
    "p5_history_line_or_boundary_surface_local_only",
    "plan_tier_context_local_only",
    "case_role_family_ref",
    "rating_axis_instruction_ref",
    "selection_form_ref",
)
P7_R54_AHR_POST_MN11_PMN_OP09_READY_STATUS_REF: Final = (
    "PMN_OP09_REVIEWER_PERSON_SELECTION_ONLY_FORM_FROZEN_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_STATUS_REF: Final = (
    "PMN_OP09_REVIEWER_PERSON_SELECTION_ONLY_FORM_BLOCKED_BY_PACKET_SCAN"
)
P7_R54_AHR_POST_MN11_PMN_OP09_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP09_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op08_packet_scan_before_reviewer_person_selection_only_form_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_REF: Final = "local_person_reviewer_ref_001_bodyfree"
P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_INSTRUCTION_REF: Final = (
    "postmn11_reviewer_instruction_selection_only_no_free_text_no_question_text_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP09_SELECTION_ONLY_FORM_REF: Final = (
    "postmn11_reviewer_selection_only_form_freeze_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP09_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op08_packet_completeness_export_denylist_scan_ready_bodyfree",
    "reviewer_person_boundary_frozen_bodyfree",
    "selection_only_form_frozen_without_free_text_question_text_body_path_hash",
    "six_rating_axes_and_24_case_count_frozen",
    "actual_human_review_not_started_by_form_freeze",
)
P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS: Final[tuple[str, ...]] = (
    "history_connection_naturalness",
    "creepy_absence",
    "overclaim_absence",
    "self_blame_non_amplification",
    "wants_more_input_or_accumulation",
    "non_shallow_repeat",
)
P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = {
    "history_connection_naturalness": 0.90,
    "creepy_absence": 0.95,
    "overclaim_absence": 0.95,
    "self_blame_non_amplification": 0.95,
    "wants_more_input_or_accumulation": 0.85,
    "non_shallow_repeat": 0.90,
}
P7_R54_AHR_POST_MN11_PMN_OP09_SCORE_OPTION_REFS: Final[tuple[float, ...]] = (0.0, 0.25, 0.5, 0.75, 1.0)
P7_R54_AHR_POST_MN11_PMN_OP09_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = (
    "PASS", "YELLOW", "REPAIR_REQUIRED", "RED", "BLOCKED", "NOT_REVIEWABLE"
)
P7_R54_AHR_POST_MN11_PMN_OP09_SANITIZED_REASON_ID_OPTION_REFS: Final[tuple[str, ...]] = (
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
    "safe_display_risk_detected",
    "execution_blocker_present",
)
P7_R54_AHR_POST_MN11_PMN_OP09_READFEEL_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "history_connection_weak",
    "history_line_creepy_or_overread",
    "current_input_overridden_by_history",
    "overclaim_or_unearned_certainty",
    "self_blame_amplified",
    "shallow_repeat_or_generic",
    "wants_less_input_or_no_accumulation",
    "boundary_history_line_leak",
    "safe_display_risk",
)
P7_R54_AHR_POST_MN11_PMN_OP09_EXECUTION_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "packet_missing",
    "packet_not_local_only",
    "case_manifest_incomplete",
    "reviewer_not_assigned",
    "reviewer_selection_incomplete",
    "forbidden_body_leak",
    "question_text_leak",
    "disposal_missing",
    "no_touch_violation",
    "source_guard_missing",
)
P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "no_question_needed_emlis_can_observe",
    "question_may_reduce_overread_risk",
    "question_would_make_immediate_observation_heavy",
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_p4_current_surface_repair_required",
    "not_question_gate_boundary_required",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "insufficient_material_execution_blocker",
)
P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = (
    "not_needed",
    "fits_one_question",
    "needs_more_than_one_question_not_p7",
    "would_delay_immediate_observation",
    "unsafe_or_boundary_not_question",
    "repair_required_not_question",
    "insufficient_material",
)
P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = (
    "no_repair_required",
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "p4_current_surface_repair_required",
    "gate_boundary_repair_required",
    "safe_display_repair_required",
)
P7_R54_AHR_POST_MN11_PMN_OP09_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_design_material_candidate_only",
)

P7_R54_AHR_POST_MN11_PMN_OP10_READY_STATUS_REF: Final = (
    "PMN_OP10_ACTUAL_24_CASE_HUMAN_REVIEW_EXECUTION_STATE_CAPTURE_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_STATUS_REF: Final = (
    "PMN_OP10_ACTUAL_24_CASE_HUMAN_REVIEW_EXECUTION_STATE_CAPTURE_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "PMN_OP10_ACTUAL_24_CASE_HUMAN_REVIEW_EXECUTION_STATE_CAPTURE_BLOCKED_BY_BODY_LEAK"
)
P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP10_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op10_actual_human_review_execution_state_capture_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP10_STATE_CAPTURE_REF: Final = (
    "postmn11_actual_24_case_human_review_execution_state_capture_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_ACTUAL_SOURCE_REF: Final = (
    "actual_person_local_only_review_execution_state_capture_bodyfree"
)
P7_R54_AHR_POST_MN11_PMN_OP10_REVIEW_STATE_COMPLETED_SELECTION_ROWS_READY_REF: Final = (
    "REVIEW_COMPLETED_SELECTION_ROWS_READY"
)
P7_R54_AHR_POST_MN11_PMN_OP10_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op09_reviewer_person_selection_only_form_ready_bodyfree",
    "actual_human_review_execution_state_capture_received_bodyfree",
    "reviewer_local_only_read_receipt_present_bodyfree",
    "reviewed_case_count_and_selection_row_count_are_24_bodyfree",
    "review_state_captured_without_body_question_path_hash_terminal_output",
    "operation_receipt_intake_required_next_without_rows_or_disposal_creation",
)
P7_R54_AHR_POST_MN11_PMN_OP10_PROTOCOL_STEP_REFS: Final[tuple[str, ...]] = (
    "reviewer_reads_local_only_packet",
    "reviewer_selects_axis_scores_verdict_and_refs_without_body_quote",
    "reviewer_notes_are_not_exported",
    "question_text_is_not_written",
    "all_24_cases_are_completed",
    "operation_receipt_is_created_bodyfree_next",
)
P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_STATE_CAPTURE_FIELD_REFS: Final[tuple[str, ...]] = (
    "review_state_capture_ref",
    "review_session_id",
    "actual_review_basis_ref",
    "actual_source_ref",
    "reviewer_person_ref",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "review_state_ref",
    "review_started_at_bucket_ref",
    "review_completed_at_bucket_ref",
    "reviewed_case_count",
    "selection_row_count",
    "local_only",
    "must_not_export",
    "selection_only",
    "actual_human_review_executed_by_person",
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP11_READY_STATUS_REF: Final = (
    "PMN_OP11_ACTUAL_OPERATION_RECEIPT_INTAKED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_STATUS_REF: Final = (
    "PMN_OP11_ACTUAL_OPERATION_RECEIPT_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "PMN_OP11_ACTUAL_OPERATION_RECEIPT_INTAKE_BLOCKED_BY_BODY_LEAK"
)
P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP11_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op11_actual_operation_receipt_intake_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF: Final = (
    ex.P7_R54_AHR_POST_CR22_EX07_ALLOWED_ACTUAL_SOURCE_REF
)
P7_R54_AHR_POST_MN11_PMN_OP11_OPERATION_RECEIPT_INTAKE_REF: Final = (
    "postmn11_actual_operation_receipt_intake_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP11_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op10_actual_human_review_execution_state_capture_ready_bodyfree",
    "actual_operation_receipt_received_bodyfree",
    "actual_source_ref_matches_actual_person_local_only_review_operation_receipt",
    "reviewer_and_24_case_counts_match_op10_state_capture",
    "operation_receipt_contains_no_body_question_path_hash_terminal_output",
    "sanitized_review_result_rows_intake_required_next_without_downstream_promotion",
)
P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_OPERATION_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "operation_receipt_ref",
    "review_session_id",
    "actual_review_basis_ref",
    "reviewer_person_ref",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "review_started_at_bucket_ref",
    "review_completed_at_bucket_ref",
    "reviewed_case_count",
    "selection_row_count",
    "local_only",
    "must_not_export",
    "selection_only",
    "actual_source_ref",
    "body_free",
)

P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS: Final[tuple[str, ...]] = tuple(
    getattr(op, f"P7_R54_OP{index:02d}_STEP_REF") for index in range(25)
)
P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_STEP_REFS: Final[tuple[str, ...]] = (
    mn.P7_R54_AHR_POST_EX18_MN_STEP_REFS
)
P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_REUSE_ROLE_REFS: Final[tuple[str, ...]] = (
    "local_only_operation_scope_and_no_touch_boundary",
    "local_only_preflight_and_explicit_allow_boundary",
    "24_case_manifest_boundary",
    "body_full_packet_generation_request_boundary",
    "reviewer_instruction_and_selection_only_boundary",
    "operation_state_capture_and_validation_matrix_boundary",
)
P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS: Final[tuple[str, ...]] = (
    "actual_operation_receipt_intake",
    "actual_selection_row_provenance_guard",
    "sanitized_review_result_rows_intake",
    "rating_row_normalization_threshold_summary",
    "readfeel_label_connection_safe_display_blocker_classification",
    "question_need_observation_row_normalization",
    "disposal_purge_receipt_intake",
    "final_no_body_no_question_no_path_no_hash_no_touch_validation",
    "actual_review_evidence_complete_predicate",
    "candidate_only_separation_and_manual_next_decision_hold",
)
P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_INTAKE_ROLE_REFS: Final[tuple[str, ...]] = (
    "return_to_actual_review_operation_required_decision",
    "actual_review_evidence_missing_real_review_required_confirmation",
    "current_received_snapshot_264_85_258_171_basis_confirmation",
    "downstream_no_promotion_boundary",
    "postcr22_ex07_ex18_reentry_mapping_reference",
)
P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION: Final[dict[str, int]] = dict(op.P7_R54_OP05_CASE_DISTRIBUTION)
P7_R54_AHR_POST_MN11_ALLOWED_ACTUAL_SOURCE_REFS: Final[tuple[str, ...]] = (
    ex.P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS
)
P7_R54_AHR_POST_MN11_FORBIDDEN_ACTUAL_SOURCE_REFS: Final[tuple[str, ...]] = (
    ex.P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS
)
P7_R54_AHR_POST_MN11_ALLOWED_REVIEW_SESSION_STATE_REFS: Final[tuple[str, ...]] = (
    ex.P7_R54_AHR_POST_CR22_ALLOWED_REVIEW_SESSION_STATE_REFS
)
P7_R54_AHR_POST_MN11_ALLOWED_READY_SESSION_TRANSITION_REFS: Final[tuple[str, ...]] = (
    ex.P7_R54_AHR_POST_CR22_ALLOWED_READY_SESSION_TRANSITION_REFS
)
P7_R54_AHR_POST_MN11_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS: Final[tuple[str, ...]] = (
    ex.P7_R54_AHR_POST_CR22_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS
)
P7_R54_AHR_POST_MN11_REVIEW_SESSION_STATE_NOT_STARTED_REF: Final = (
    ex.P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_NOT_STARTED_REF
)
P7_R54_AHR_POST_MN11_SOURCE_GUARD_REQUIRED_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "helper_default_rows_allowed_as_actual",
    "unit_test_rows_allowed_as_actual",
    "synthetic_contract_fixture_rows_allowed_as_actual",
    "synthetic_rows_allowed_as_actual",
    "historical_rows_allowed_as_actual",
    "ai_inferred_rows_allowed_as_actual",
    "rows_without_person_read_receipt_allowed_as_actual",
    "helper_default_rows_materialized_as_actual_here",
    "unit_test_rows_materialized_as_actual_here",
    "synthetic_contract_rows_materialized_as_actual_here",
    "historical_rows_materialized_as_actual_here",
    "actual_source_guard_materializes_actual_rows_here",
    "actual_source_guard_runs_actual_human_review_here",
)

P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "question_answer_storage_materialized_here",
    "p8_implementation_spec_finalized_here",
    "actual_body_full_packet_generated_here",
    "body_full_packet_generation_run_here",
    "body_full_packet_exported",
    "actual_human_review_newly_run_here",
    "actual_human_review_run_here",
    "actual_human_review_operation_run",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_review",
    "actual_operation_receipt_created_here",
    "actual_selection_rows_created_here",
    "actual_sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
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
P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "input_body",
        "raw_body",
        "current_input_body",
        "returned_body",
        "returned_emlis_body",
        "emlis_body",
        "history_body",
        "history_surface",
        "comment_text",
        "comment_text_body",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
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
P7_R54_AHR_POST_MN11_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_MN11_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "mn11_green_is_not_actual_human_review_complete",
    "mn11_manual_decision_is_not_actual_operation_receipt",
    "mn11_next_required_step_is_not_body_full_packet_generated",
    "unit_test_rows_are_not_actual_review_rows",
    "helper_default_rows_are_not_actual_review_rows",
    "synthetic_contract_rows_are_not_actual_review_rows",
    "current_received_snapshot_264_85_258_171_must_not_be_rewritten_by_latest_zip_label",
    "p8_material_candidate_only_is_not_p8_start_allowed",
    "r52_handoff_candidate_is_not_r52_actual_execution",
    "p5_confirmed_candidate_is_not_p5_final",
    "selected_regression_green_is_not_full_backend_suite_green",
    "rn_contract_green_is_not_rn_real_device_modal_verified",
)
P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation",
    "actual_human_review_execution",
    "actual_operation_receipt",
    "actual_sanitized_review_result_rows",
    "actual_rating_rows",
    "actual_question_need_observation_rows",
    "actual_disposal_purge_receipt",
    "actual_review_evidence_complete_from_real_review",
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
P7_R54_AHR_POST_MN11_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "P8 question design",
    "P8 question implementation",
    "P6 start",
    "R52 actual execution",
    "P5 final",
    "P7 complete",
    "release decision",
)

P7_R54_AHR_POST_MN11_PMN_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "chosen_stage_ref",
    "not_stage_refs",
    "not_stage_ref_count",
    "post_mn11_actual_operation_scope_confirmed",
    "post_mn11_actual_operation_evidence_intake_reentry_scope",
    "no_touch_boundary_confirmed",
    "no_promotion_boundary_confirmed",
    "pmn_op00_does_not_intake_mn11_manual_decision",
    "pmn_op00_does_not_generate_body_full_packet",
    "pmn_op00_does_not_run_actual_human_review",
    "pmn_op00_does_not_create_operation_receipt_or_rows_or_disposal",
    "p8_question_design_out_of_scope",
    "p8_question_implementation_out_of_scope",
    "p6_start_out_of_scope",
    "r52_actual_execution_out_of_scope",
    "p5_finalization_out_of_scope",
    "p7_complete_out_of_scope",
    "release_decision_out_of_scope",
    "api_db_rn_runtime_public_contract_no_touch_boundary_frozen",
    "required_case_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    "support_material_refs",
    "support_material_ref_count",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_mn11_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op00_schema_version",
    "op00_material_ref",
    "op00_next_required_step",
    "op00_scope_confirmed",
    "op00_no_touch_boundary_confirmed",
    "op00_no_promotion_boundary_confirmed",
    "pmn_op01_status_ref",
    "pmn_op01_allowed_status_refs",
    "pmn_op01_ready",
    "pmn_op01_blocker_refs",
    "pmn_op01_blocker_ref_count",
    "pmn_op01_reason_refs",
    "pmn_op01_reason_ref_count",
    "support_material_refs",
    "support_material_ref_count",
    "mn11_result_memo_ref",
    "mn11_result_memo_ref_present",
    "mn11_bodyfree_envelope_present",
    "mn11_schema_version",
    "mn11_operation_step_ref",
    "mn11_status_ref",
    "mn11_ready",
    "mn11_manual_decision_ref",
    "mn11_final_manual_decision_ref",
    "mn11_manual_decision_status_ref",
    "mn11_actual_review_evidence_status_ref",
    "mn11_next_required_step",
    "mn11_actual_review_evidence_complete_from_real_review",
    "mn11_actual_review_basis_ref",
    "mn11_manual_decision_ref_confirmed",
    "mn11_actual_review_evidence_missing_real_review_required_confirmed",
    "mn11_next_required_step_confirmed",
    "mn11_actual_review_evidence_complete_from_real_review_false_confirmed",
    "mn11_actual_review_basis_ref_confirmed",
    "mn11_no_body_leak_validation_passed_reported",
    "mn11_no_question_text_validation_passed_reported",
    "mn11_no_path_hash_validation_passed_reported",
    "mn11_no_touch_boundary_confirmed_reported",
    "mn11_no_promotion_boundary_confirmed_reported",
    "mn11_green_is_not_actual_human_review_complete",
    "mn11_manual_decision_is_not_actual_operation_receipt",
    "pmn_op01_does_not_treat_mn11_green_as_real_review_complete",
    "pmn_op01_does_not_generate_body_full_packet",
    "pmn_op01_does_not_run_actual_human_review",
    "pmn_op01_does_not_create_operation_receipt_or_rows_or_disposal",
    "pmn_op01_does_not_start_p8_p6_r52_or_release",
    "pmn_op01_passes_to_existing_support_material_inventory",
    "actual_local_only_human_review_operation_required_before_downstream_decision",
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
    "mn11_forbidden_payload_key_paths",
    "mn11_forbidden_payload_key_path_count",
    "mn11_promotion_claim_refs",
    "mn11_promotion_claim_ref_count",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_mn11_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


P7_R54_AHR_POST_MN11_PMN_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op01_schema_version",
    "op01_material_ref",
    "op01_next_required_step",
    "op01_ready",
    "op01_manual_decision_ref_confirmed",
    "op01_actual_review_basis_ref_confirmed",
    "op01_passes_to_existing_support_material_inventory",
    "support_inventory_status_ref",
    "support_inventory_allowed_status_refs",
    "support_inventory_ready",
    "support_inventory_blocker_refs",
    "support_inventory_blocker_ref_count",
    "support_inventory_reason_refs",
    "support_inventory_reason_ref_count",
    "existing_op_line_helper_ref",
    "existing_op_line_step_refs",
    "existing_op_line_step_ref_count",
    "existing_op_line_first_step_ref",
    "existing_op_line_last_step_ref",
    "existing_op_line_reuse_role_refs",
    "existing_op_line_reuse_role_ref_count",
    "existing_op_line_reuse_candidate",
    "existing_ex_line_helper_ref",
    "existing_ex_line_reentry_step_refs",
    "existing_ex_line_reentry_step_ref_count",
    "existing_ex_line_reentry_first_step_ref",
    "existing_ex_line_reentry_last_step_ref",
    "existing_ex_line_reentry_role_refs",
    "existing_ex_line_reentry_role_ref_count",
    "existing_ex_line_reentry_candidate",
    "existing_mn_line_helper_ref",
    "existing_mn_line_step_refs",
    "existing_mn_line_step_ref_count",
    "existing_mn_line_first_step_ref",
    "existing_mn_line_last_step_ref",
    "existing_mn_line_intake_role_refs",
    "existing_mn_line_intake_role_ref_count",
    "existing_mn_line_manual_decision_intake_candidate",
    "new_giant_wrapper_required",
    "minimal_bridge_allowed_if_needed",
    "post_mn11_helper_role_limited_to_bridge",
    "existing_support_material_inventory_does_not_modify_existing_helpers",
    "pmn_op02_does_not_generate_body_full_packet",
    "pmn_op02_does_not_run_actual_human_review",
    "pmn_op02_does_not_create_operation_receipt_or_rows_or_disposal",
    "pmn_op02_does_not_start_p8_p6_r52_or_release",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "support_material_refs",
    "support_material_ref_count",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_mn11_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op02_schema_version",
    "op02_material_ref",
    "op02_next_required_step",
    "op02_support_inventory_ready",
    "op02_existing_op_line_reuse_candidate",
    "op02_existing_ex_line_reentry_candidate",
    "op02_existing_mn_line_manual_decision_intake_candidate",
    "review_session_envelope_status_ref",
    "review_session_envelope_allowed_status_refs",
    "review_session_envelope_ready",
    "review_session_envelope_blocker_refs",
    "review_session_envelope_blocker_ref_count",
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
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "allowed_actual_source_refs_are_from_existing_postcr22_ex_line",
    "forbidden_actual_source_refs_are_from_existing_postcr22_ex_line",
    "helper_default_rows_allowed_as_actual",
    "unit_test_rows_allowed_as_actual",
    "synthetic_contract_fixture_rows_allowed_as_actual",
    "synthetic_rows_allowed_as_actual",
    "historical_rows_allowed_as_actual",
    "ai_inferred_rows_allowed_as_actual",
    "rows_without_person_read_receipt_allowed_as_actual",
    "helper_default_rows_materialized_as_actual_here",
    "unit_test_rows_materialized_as_actual_here",
    "synthetic_contract_rows_materialized_as_actual_here",
    "historical_rows_materialized_as_actual_here",
    "actual_source_guard_materializes_actual_rows_here",
    "actual_source_guard_runs_actual_human_review_here",
    "local_received_zip_refs",
    "local_received_zip_ref_count",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_mn11_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op03_schema_version",
    "op03_material_ref",
    "op03_next_required_step",
    "op03_review_session_envelope_ready",
    "op03_actual_source_guard_ready",
    "op03_review_session_state_ref",
    "local_only_preflight_status_ref",
    "local_only_preflight_allowed_status_refs",
    "local_only_preflight_ready",
    "local_only_preflight_blocker_refs",
    "local_only_preflight_blocker_ref_count",
    "local_only_preflight_reason_refs",
    "local_only_preflight_reason_ref_count",
    "local_review_root_ref",
    "local_review_root_ref_present",
    "local_review_root_ref_has_path_shape",
    "local_review_root_path_included",
    "explicit_allow_ref",
    "explicit_allow_ref_present",
    "explicit_allow_scope_ref",
    "explicit_allow_body_stored_here",
    "retention_policy_ref",
    "retention_policy_ref_present",
    "disposal_policy_ref",
    "disposal_policy_ref_present",
    "export_denylist_policy_ref",
    "export_denylist_policy_ref_present",
    "export_denylist_violation_refs",
    "export_denylist_violation_ref_count",
    "purge_required_before_or_after_review",
    "purge_required_delete_target_refs",
    "purge_required_delete_target_ref_count",
    "local_only",
    "must_not_export",
    "body_full_packet_generation_allowed_for_local_review_only",
    "body_full_packet_generation_allowed_by_preflight",
    "body_full_packet_generation_request_allowed_next",
    "body_full_generation_blocked_until_manifest_refreeze",
    "body_full_packet_export_allowed",
    "body_free_summary_export_allowed",
    "body_full_packet_generated_here",
    "body_full_packet_materialized_here",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "local_received_zip_refs_are_actual_review_basis",
    "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    "pmn_op04_does_not_generate_body_full_packet",
    "pmn_op04_does_not_run_actual_human_review",
    "pmn_op04_does_not_create_operation_receipt_or_rows_or_disposal",
    "pmn_op04_does_not_start_p8_p6_r52_or_release",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_mn11_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op04_schema_version",
    "op04_material_ref",
    "op04_next_required_step",
    "op04_local_only_preflight_status_ref",
    "op04_local_only_preflight_ready",
    "op04_body_full_generation_blocked_until_manifest_refreeze",
    "op04_body_full_packet_generation_allowed_by_preflight",
    "manifest_status_ref",
    "manifest_allowed_status_refs",
    "manifest_ready",
    "manifest_blocker_refs",
    "manifest_blocker_ref_count",
    "manifest_reason_refs",
    "manifest_reason_ref_count",
    "required_case_count",
    "total_case_count",
    "case_ref_id_count",
    "blind_case_id_count",
    "packet_ref_id_count",
    "selection_row_count_required",
    "sanitized_review_result_row_count_required",
    "rating_row_count_required",
    "question_need_observation_row_count_required",
    "case_distribution",
    "case_distribution_total_count",
    "case_distribution_matches_design",
    "family_case_counts",
    "boundary_case_count",
    "low_information_boundary_case_count",
    "free_tier_boundary_case_count",
    "case_ref_ids_unique",
    "blind_case_ids_unique",
    "packet_ref_ids_unique",
    "blind_case_id_case_ref_separated",
    "blind_case_id_packet_ref_separated",
    "case_ref_id_packet_ref_separated",
    "case_manifest_rows",
    "case_manifest_row_count",
    "controller_manifest_rows",
    "controller_manifest_row_count",
    "reviewer_facing_case_index_rows",
    "reviewer_facing_row_count",
    "reviewer_identifier_policy_ref",
    "controller_keeps_family_tier_expected_refs",
    "reviewer_receives_blind_case_id_only",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "reviewer_facing_case_ref_exposed",
    "reviewer_facing_packet_ref_exposed",
    "reviewer_facing_expected_result_exposed",
    "reviewer_facing_hidden_metadata_exposed",
    "p4_r11_rows_confused_as_r54_review_rows",
    "p4_r11_rows_mixed_in",
    "p4_r11_rows_mixed_in_count",
    "body_full_packet_generation_request_allowed_next",
    "body_full_packet_generated_here",
    "body_full_packet_materialized_here",
    "body_full_generation_blocked_until_pmn_op06_request_step",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "actual_human_review_still_not_run",
    "actual_review_evidence_complete_from_real_review_still_false",
    "pmn_op05_does_not_generate_body_full_packet",
    "pmn_op05_does_not_run_actual_human_review",
    "pmn_op05_does_not_create_operation_receipt_or_rows_or_disposal",
    "pmn_op05_does_not_start_p8_p6_r52_or_release",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_mn11_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_schema_version", "op05_material_ref", "op05_next_required_step", "op05_manifest_ready",
    "op05_body_full_packet_generation_request_allowed_next", "packet_generation_request_status_ref",
    "packet_generation_request_allowed_status_refs", "packet_generation_request_ready", "packet_generation_request_blocker_refs",
    "packet_generation_request_blocker_ref_count", "packet_generation_request_reason_refs", "packet_generation_request_reason_ref_count",
    "packet_generation_request_ref", "packet_generation_request_required_field_refs", "packet_generation_request_required_field_ref_count",
    "packet_generation_request_bodyfree_payload", "packet_generation_request_bodyfree_payload_field_count",
    "packet_generation_request_contains_forbidden_payload_key", "packet_generation_request_forbidden_payload_key_paths",
    "packet_generation_request_forbidden_payload_key_path_count", "case_manifest_ref", "case_manifest_ready", "case_manifest_row_count",
    "case_ref_id_count", "blind_case_id_count", "packet_ref_id_count", "explicit_allow_ref", "explicit_allow_ref_matches_op04",
    "local_operation_ref", "local_only_required", "must_not_export", "packet_completeness_scan_required", "export_denylist_scan_required",
    "purge_required", "retention_policy_ref", "disposal_policy_ref", "export_denylist_policy_ref",
    "body_full_packet_generation_allowed_for_local_review_only", "body_full_packet_generation_request_built_here",
    "body_full_packet_generation_request_bodyfree_only", "body_full_packet_generation_request_allowed_next",
    "packet_generation_local_operation_receipt_required_next", "body_full_packet_generation_executed_here",
    "body_full_packet_generated_here", "body_full_packet_materialized_here", "body_full_packet_export_allowed",
    "body_full_packet_exported_to_artifact", "local_absolute_path_included", "body_hash_stored", "terminal_output_body_included",
    "actual_human_review_still_not_run", "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "pmn_op06_does_not_generate_body_full_packet", "pmn_op06_does_not_run_actual_human_review",
    "pmn_op06_does_not_create_operation_receipt_or_rows_or_disposal", "pmn_op06_does_not_start_p8_p6_r52_or_release",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_schema_version", "op06_material_ref", "op06_next_required_step", "op06_packet_generation_request_ready",
    "op06_packet_generation_request_ref", "packet_generation_receipt_boundary_status_ref",
    "packet_generation_receipt_boundary_allowed_status_refs", "packet_generation_receipt_boundary_ready",
    "packet_generation_receipt_boundary_blocker_refs", "packet_generation_receipt_boundary_blocker_ref_count",
    "packet_generation_receipt_boundary_reason_refs", "packet_generation_receipt_boundary_reason_ref_count",
    "packet_generation_receipt_boundary_ref", "expected_packet_generation_receipt_ref",
    "packet_generation_receipt_required_after_external_local_generation", "packet_generation_receipt_received_here",
    "packet_generation_receipt_intaked_here", "packet_generation_receipt_actual_source_ref_required",
    "packet_generation_receipt_expected_actual_source_ref", "packet_generation_local_operation_receipt_boundary_defined_here",
    "packet_generation_local_operation_receipt_bodyfree_only", "future_packet_generation_receipt_required_field_refs",
    "future_packet_generation_receipt_required_field_ref_count", "expected_packet_count", "packet_count", "packet_ref_id_count",
    "packet_materialized_local_only", "packet_materialized_local_only_claimed_here", "packet_completeness_scan_required_next",
    "export_denylist_scan_required_next", "body_full_packet_generation_executed_here", "body_full_packet_generated_here",
    "body_full_packet_materialized_here", "body_full_packet_exported_to_artifact", "body_full_packet_export_allowed",
    "local_absolute_path_included", "body_hash_stored", "terminal_output_body_included", "packet_content_included",
    "actual_human_review_still_not_run", "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "pmn_op07_does_not_generate_body_full_packet", "pmn_op07_does_not_run_actual_human_review",
    "pmn_op07_does_not_create_actual_operation_receipt_or_rows_or_disposal", "pmn_op07_does_not_start_p8_p6_r52_or_release",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_schema_version", "op07_material_ref", "op07_next_required_step", "op07_packet_generation_receipt_boundary_ready",
    "op07_packet_generation_receipt_required_after_external_local_generation", "op07_expected_actual_source_ref",
    "packet_scan_status_ref", "packet_scan_allowed_status_refs", "packet_scan_ready", "packet_scan_blocker_refs",
    "packet_scan_blocker_ref_count", "packet_scan_reason_refs", "packet_scan_reason_ref_count", "packet_scan_ref",
    "packet_scan_bodyfree_only", "packet_scan_depends_on_actual_packet_generation_receipt",
    "actual_packet_generation_receipt_received_here", "actual_packet_generation_receipt_intaked_here",
    "actual_packet_generation_receipt_ref", "actual_packet_generation_receipt_source_ref",
    "actual_packet_generation_receipt_source_allowed", "packet_generation_request_ref", "expected_packet_count",
    "packet_count", "packet_ref_id_count", "packet_ref_ids", "packet_ref_ids_unique", "packet_count_matches_expected",
    "packet_ref_id_count_matches_expected", "packet_completeness_scan_required", "packet_completeness_scan_passed",
    "reviewer_packet_required_fields_present", "reviewer_packet_required_field_refs", "reviewer_packet_required_field_ref_count",
    "export_denylist_policy_ref", "export_denylist_scan_required", "export_denylist_scan_passed",
    "export_denylist_violation_refs", "export_denylist_violation_ref_count", "body_full_packet_export_candidate_refs",
    "body_full_packet_export_candidate_count", "body_full_packet_content_detected_in_export",
    "question_text_detected_in_export", "draft_question_text_detected_in_export", "local_path_detected_in_export",
    "body_hash_detected_in_export", "terminal_output_body_detected_in_export", "body_full_packet_exported",
    "body_full_packet_exported_to_artifact", "body_full_packet_export_allowed", "local_absolute_path_included",
    "body_hash_stored", "terminal_output_body_included", "packet_content_included", "question_text_included",
    "draft_question_text_included", "packet_scan_does_not_materialize_packet_content_here",
    "reviewer_person_selection_only_form_freeze_allowed_next", "actual_human_review_still_not_run",
    "actual_review_evidence_complete_from_real_review_still_false", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "pmn_op08_does_not_generate_body_full_packet",
    "pmn_op08_does_not_run_actual_human_review", "pmn_op08_does_not_create_actual_operation_receipt_or_review_rows_or_disposal",
    "pmn_op08_does_not_start_p8_p6_r52_or_release", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_mn11_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op08_schema_version", "op08_material_ref", "op08_next_required_step", "op08_packet_scan_status_ref",
    "op08_packet_scan_ready", "op08_packet_count", "op08_packet_ref_id_count", "op08_packet_completeness_scan_passed",
    "op08_export_denylist_scan_passed", "reviewer_form_status_ref", "reviewer_form_allowed_status_refs",
    "reviewer_form_ready", "reviewer_form_blocker_refs", "reviewer_form_blocker_ref_count", "reviewer_form_reason_refs",
    "reviewer_form_reason_ref_count", "reviewer_person_ref", "reviewer_person_ref_present", "reviewer_is_person",
    "reviewer_person_confirmed", "reviewer_local_only_read_receipt_present", "actual_human_review_executed_by_person",
    "reviewer_identity_public_export_allowed", "reviewer_free_text_export_allowed", "reviewer_notes_body_export_allowed",
    "selection_only_form_ready", "selection_only_form_ref", "reviewer_instruction_ref", "reviewer_instruction_policy_ref",
    "selection_only", "selection_only_form_bodyfree_only", "free_text_field_present", "free_text_field_export_allowed",
    "reviewer_notes_body_field_present", "raw_body_copy_field_present", "question_text_field_present", "draft_question_text_field_present",
    "local_path_field_present", "body_hash_field_present", "packet_content_field_present", "required_axis_count",
    "required_case_count", "rating_axis_refs", "rating_axis_target_thresholds", "score_option_refs", "verdict_option_refs",
    "sanitized_reason_id_option_refs", "readfeel_blocker_id_option_refs", "execution_blocker_id_option_refs",
    "question_need_primary_class_options", "ambiguity_kind_option_refs", "one_question_fit_option_refs",
    "repair_required_option_refs", "plan_candidate_flag_refs", "reviewer_receives_blind_case_id_only",
    "reviewer_facing_family_exposed", "reviewer_facing_tier_exposed", "reviewer_facing_case_ref_exposed",
    "reviewer_facing_packet_ref_exposed", "reviewer_facing_expected_result_exposed", "reviewer_facing_hidden_metadata_exposed",
    "actual_human_review_state_capture_allowed_next", "actual_human_review_started_here", "actual_human_review_run_here",
    "actual_review_evidence_complete_from_real_review_still_false", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "pmn_op09_does_not_run_actual_human_review",
    "pmn_op09_does_not_create_actual_operation_receipt_or_rows_or_disposal", "pmn_op09_does_not_start_p8_p6_r52_or_release",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op09_schema_version", "op09_material_ref", "op09_next_required_step", "op09_reviewer_form_status_ref",
    "op09_reviewer_form_ready", "op09_selection_only_form_ready", "op09_reviewer_person_ref",
    "review_execution_protocol_status_ref", "review_execution_protocol_allowed_status_refs", "review_execution_state_capture_ready",
    "review_execution_state_capture_blocker_refs", "review_execution_state_capture_blocker_ref_count",
    "review_execution_state_capture_reason_refs", "review_execution_state_capture_reason_ref_count",
    "review_state_capture_ref", "review_state_ref", "allowed_review_state_refs", "actual_review_state_capture_received_here",
    "actual_review_state_capture_intaked_here", "actual_review_state_capture_source_ref", "actual_review_state_capture_source_allowed",
    "reviewer_person_ref", "reviewer_person_ref_matches_op09", "reviewer_is_person", "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present", "actual_human_review_executed_by_person", "review_started_at_bucket_ref",
    "review_completed_at_bucket_ref", "reviewed_case_count", "selection_row_count", "reviewed_case_count_matches_expected",
    "selection_row_count_matches_expected", "local_only", "must_not_export", "selection_only",
    "state_capture_bodyfree_only", "state_capture_contains_reviewer_free_text", "state_capture_contains_reviewer_notes_body",
    "state_capture_contains_packet_content", "state_capture_contains_question_text", "state_capture_contains_draft_question_text",
    "state_capture_contains_local_path", "state_capture_contains_body_hash", "operation_receipt_intake_allowed_next",
    "actual_operation_receipt_created_here", "actual_operation_receipt_intaked_here", "actual_selection_rows_created_here",
    "actual_sanitized_review_result_rows_materialized_here", "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete_from_real_review_still_false", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "pmn_op10_does_not_run_actual_human_review_here",
    "pmn_op10_does_not_create_actual_operation_receipt_or_rows_or_disposal", "pmn_op10_does_not_start_p8_p6_r52_or_release",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op10_schema_version", "op10_material_ref", "op10_next_required_step", "op10_review_execution_state_capture_ready",
    "op10_reviewer_person_ref", "op10_reviewed_case_count", "op10_selection_row_count",
    "operation_receipt_status_ref", "operation_receipt_allowed_status_refs", "operation_receipt_accepted",
    "operation_receipt_blocker_refs", "operation_receipt_blocker_ref_count", "operation_receipt_reason_refs",
    "operation_receipt_reason_ref_count", "operation_receipt_intake_ref", "operation_receipt_ref", "operation_receipt_ref_present",
    "operation_receipt_ref_is_bodyfree_ref", "operation_receipt_ref_has_local_path_shape", "operation_receipt_bodyfree_only",
    "operation_receipt_received_here", "operation_receipt_intaked_here", "operation_receipt_required_actual_source_ref",
    "actual_source_ref", "actual_source_ref_allowed", "reviewer_person_ref", "reviewer_person_ref_matches_op10",
    "reviewer_is_person", "reviewer_person_confirmed", "reviewer_local_only_read_receipt_present",
    "actual_human_review_executed_by_person", "review_started_at_bucket_ref", "review_completed_at_bucket_ref",
    "reviewed_case_count", "selection_row_count", "reviewed_case_count_matches_expected", "selection_row_count_matches_expected",
    "local_only", "must_not_export", "selection_only", "operation_receipt_confirms_actual_person_local_only_review",
    "operation_receipt_does_not_create_selection_rows_here", "operation_receipt_does_not_materialize_rating_rows_here",
    "operation_receipt_does_not_materialize_question_observation_rows_here", "operation_receipt_does_not_create_disposal_receipt_here",
    "operation_receipt_does_not_complete_evidence_here", "operation_receipt_does_not_export_body_or_notes",
    "forbidden_receipt_payload_key_paths", "forbidden_receipt_payload_key_path_count", "receipt_forbidden_body_path_hash_or_question_flag_requested",
    "sanitized_review_result_rows_intake_allowed_next", "actual_operation_receipt_created_here", "actual_selection_rows_created_here",
    "actual_sanitized_review_result_rows_materialized_here", "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete_from_real_review_still_false", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "pmn_op11_does_not_run_actual_human_review_here",
    "pmn_op11_does_not_start_p8_p6_r52_or_release", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_mn11_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op09_schema_version", "op09_material_ref", "op09_next_required_step", "op09_reviewer_form_status_ref",
    "op09_reviewer_form_ready", "op09_reviewer_person_ref", "op09_reviewer_is_person",
    "op09_reviewer_person_confirmed", "op09_selection_only_form_ready", "op09_actual_human_review_state_capture_allowed_next",
    "review_execution_state_capture_status_ref", "review_execution_state_capture_allowed_status_refs",
    "review_execution_state_capture_ready", "review_execution_state_capture_blocker_refs",
    "review_execution_state_capture_blocker_ref_count", "review_execution_state_capture_reason_refs",
    "review_execution_state_capture_reason_ref_count", "review_execution_protocol_ref", "review_execution_protocol_bodyfree_only",
    "review_execution_protocol_step_refs", "review_execution_protocol_step_ref_count",
    "actual_review_state_capture_received_here", "actual_review_state_capture_intaked_here",
    "actual_review_state_capture_required_field_refs", "actual_review_state_capture_required_field_ref_count",
    "actual_review_state_capture_ref", "actual_review_state_capture_source_ref", "actual_review_state_capture_source_allowed",
    "review_state_ref", "allowed_review_state_refs", "allowed_review_state_ref_count",
    "reviewer_person_ref", "reviewer_person_ref_present", "reviewer_person_ref_matches_op09", "reviewer_is_person",
    "reviewer_person_confirmed", "reviewer_local_only_read_receipt_present", "actual_human_review_executed_by_person",
    "review_started_at_bucket_ref", "review_started_at_bucket_ref_present", "review_started_at_bucket_ref_is_bodyfree_ref",
    "review_started_at_bucket_ref_has_local_path_shape", "review_completed_at_bucket_ref", "review_completed_at_bucket_ref_present",
    "review_completed_at_bucket_ref_is_bodyfree_ref", "review_completed_at_bucket_ref_has_local_path_shape",
    "reviewed_case_count", "required_reviewed_case_count", "reviewed_case_count_is_24",
    "selection_row_count", "required_selection_row_count", "selection_row_count_is_24",
    "local_only", "must_not_export", "selection_only", "body_full_packet_stayed_local_only",
    "reviewer_free_text_exported", "reviewer_notes_body_exported", "body_quotation_exported", "question_text_materialized_in_review",
    "draft_question_text_materialized_in_review", "packet_content_exported", "body_full_packet_content_exported",
    "local_absolute_path_included", "body_hash_included", "terminal_output_body_included",
    "actual_operation_receipt_required_next", "operation_receipt_required_actual_source_ref", "actual_operation_receipt_intake_allowed_next",
    "actual_operation_receipt_intaked_here", "actual_selection_rows_created_here", "actual_sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here", "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "pmn_op10_does_not_generate_body_full_packet", "pmn_op10_does_not_create_actual_operation_receipt_or_rows_or_disposal",
    "pmn_op10_does_not_start_p8_p6_r52_or_release", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_mn11_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op10_schema_version", "op10_material_ref", "op10_next_required_step", "op10_review_execution_state_capture_ready",
    "op10_review_state_ref", "op10_reviewer_person_ref", "op10_review_started_at_bucket_ref", "op10_review_completed_at_bucket_ref",
    "op10_reviewed_case_count", "op10_selection_row_count", "operation_receipt_status_ref",
    "operation_receipt_allowed_status_refs", "operation_receipt_accepted", "operation_receipt_reason_refs",
    "operation_receipt_blocker_refs", "operation_receipt_blocker_ref_count", "operation_receipt_intake_ref",
    "operation_receipt_required_field_refs", "operation_receipt_required_field_ref_count", "operation_receipt_ref",
    "operation_receipt_ref_present", "operation_receipt_ref_is_bodyfree_ref", "operation_receipt_ref_has_local_path_shape",
    "reviewer_person_ref", "reviewer_person_ref_present", "reviewer_person_ref_is_bodyfree_ref", "reviewer_person_ref_has_local_path_shape",
    "reviewer_person_ref_matches_op10", "reviewer_is_person", "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present", "review_started_at_bucket_ref", "review_started_at_bucket_ref_present",
    "review_started_at_bucket_ref_is_bodyfree_ref", "review_started_at_bucket_ref_has_local_path_shape",
    "review_started_at_bucket_ref_matches_op10", "review_completed_at_bucket_ref", "review_completed_at_bucket_ref_present",
    "review_completed_at_bucket_ref_is_bodyfree_ref", "review_completed_at_bucket_ref_has_local_path_shape",
    "review_completed_at_bucket_ref_matches_op10", "reviewed_case_count", "required_reviewed_case_count",
    "reviewed_case_count_is_24", "reviewed_case_count_matches_op10", "selection_row_count", "required_selection_row_count",
    "selection_row_count_is_24", "selection_row_count_matches_op10", "local_only", "must_not_export", "selection_only",
    "actual_source_ref", "actual_source_allowed_ref", "actual_source_guard_passed", "operation_receipt_bodyfree_only",
    "operation_receipt_received_here", "operation_receipt_intaked_here", "operation_receipt_confirms_actual_person_local_only_review",
    "actual_human_review_executed_by_person", "actual_human_review_run_here", "sanitized_review_result_rows_intake_required_next",
    "sanitized_review_result_rows_created_here", "rating_rows_created_here", "question_need_observation_rows_created_here",
    "disposal_receipt_created_here", "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "raw_input_included", "returned_emlis_body_included", "history_body_included", "comment_text_body_included",
    "reviewer_free_text_included", "reviewer_notes_body_included", "question_text_included", "draft_question_text_included",
    "packet_content_included", "body_full_packet_content_included", "local_absolute_path_included", "body_hash_included",
    "terminal_output_body_included", "stdout_body_included", "stderr_body_included", "traceback_body_included",
    "pmn_op11_does_not_create_sanitized_rows_or_rating_rows_or_question_rows", "pmn_op11_does_not_create_disposal_receipt",
    "pmn_op11_does_not_start_p8_p6_r52_or_release", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_mn11_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any | None) -> str:
    return _clean_ref(value, default=P7_R54_AHR_POST_MN11_DEFAULT_REVIEW_SESSION_ID, max_length=220)


def _ref_has_local_path_shape(value: Any) -> bool:
    text = str(value or "")
    return any(token in text for token in ("/", "\\", "~", "file://"))


def _ref_has_question_or_body_text_shape(value: Any) -> bool:
    text = str(value or "")
    return any(token in text.lower() for token in ("question_text", "draft_question", "raw_input", "returned_body"))


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MN11_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MN11_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS}


def _required_fields_present(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {', '.join(missing[:12])}")


def _scan_forbidden_payload_key_paths(value: Any, *, path: str = "payload", limit: int = 80) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            if len(paths) >= limit:
                return paths[:limit]
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path, limit=limit - len(paths)))
            if len(paths) >= limit:
                return paths[:limit]
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]", limit=limit - len(paths)))
            if len(paths) >= limit:
                return paths[:limit]
    return paths[:limit]


def _count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        ref = _clean_ref(row.get(key), default="missing_ref", max_length=180)
        counts[ref] = counts.get(ref, 0) + 1
    return counts


def _case_ref_values(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    return [_clean_ref(row.get(key), default="missing_ref", max_length=180) for row in rows]


def _unique_non_empty(values: Sequence[str]) -> bool:
    return bool(values) and all(values) and len(set(values)) == len(values)


def _pmn_op05_case_manifest_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    manifest_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        manifest_rows.append({
            "case_manifest_row_ref": f"postmn11-pmn-op05-case-manifest-row-{index:03d}",
            "case_ref_id": _clean_ref(row.get("case_ref_id"), default=f"missing_case_ref_{index:03d}", max_length=180),
            "blind_case_id": _clean_ref(row.get("blind_case_id"), default=f"missing_blind_case_{index:03d}", max_length=180),
            "packet_ref_id": _clean_ref(row.get("packet_ref_id"), default=f"missing_packet_ref_{index:03d}", max_length=180),
            "family": _clean_ref(row.get("family"), default="missing_family", max_length=180),
            "case_role": _clean_ref(row.get("case_role"), default="missing_case_role", max_length=180),
            "subscription_tier_ref": _clean_ref(row.get("subscription_tier_ref"), default="missing_subscription_tier_ref", max_length=120),
            "case_material_status_ref": _clean_ref(row.get("case_material_status_ref"), default="missing_case_material_status_ref", max_length=180),
            "history_evidence_policy_ref": _clean_ref(row.get("history_evidence_policy_ref"), default="missing_history_evidence_policy_ref", max_length=220),
            "controller_only": True,
            "reviewer_facing_family_exposed": False,
            "reviewer_facing_tier_exposed": False,
            "reviewer_facing_case_ref_exposed": False,
            "reviewer_facing_packet_ref_exposed": False,
            "reviewer_facing_expected_result_exposed": False,
            "body_full_packet_materialized_here": False,
            "local_reviewer_payload_materialized_here": False,
            "body_free": True,
        })
    return manifest_rows


def _pmn_op05_controller_manifest_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    controller_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        controller_rows.append({
            "controller_manifest_row_ref": f"postmn11-pmn-op05-controller-row-{index:03d}",
            "case_ref_id": _clean_ref(row.get("case_ref_id"), default=f"missing_case_ref_{index:03d}", max_length=180),
            "blind_case_id": _clean_ref(row.get("blind_case_id"), default=f"missing_blind_case_{index:03d}", max_length=180),
            "packet_ref_id": _clean_ref(row.get("packet_ref_id"), default=f"missing_packet_ref_{index:03d}", max_length=180),
            "family": _clean_ref(row.get("family"), default="missing_family", max_length=180),
            "case_role": _clean_ref(row.get("case_role"), default="missing_case_role", max_length=180),
            "subscription_tier_ref": _clean_ref(row.get("subscription_tier_ref"), default="missing_subscription_tier_ref", max_length=120),
            "case_material_status_ref": _clean_ref(row.get("case_material_status_ref"), default="missing_case_material_status_ref", max_length=180),
            "history_evidence_policy_ref": _clean_ref(row.get("history_evidence_policy_ref"), default="missing_history_evidence_policy_ref", max_length=220),
            "controller_only": True,
            "reviewer_facing_family_exposed": False,
            "reviewer_facing_tier_exposed": False,
            "reviewer_facing_case_ref_exposed": False,
            "reviewer_facing_packet_ref_exposed": False,
            "reviewer_facing_expected_result_exposed": False,
            "body_free": True,
        })
    return controller_rows


def _pmn_op05_reviewer_facing_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    reviewer_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        reviewer_rows.append({
            "reviewer_case_order": index,
            "blind_case_id": _clean_ref(row.get("blind_case_id"), default=f"missing_blind_case_{index:03d}", max_length=180),
            "reviewer_receives_blind_case_id_only": True,
            "family_exposed": False,
            "tier_exposed": False,
            "case_ref_exposed": False,
            "packet_ref_exposed": False,
            "expected_result_exposed": False,
            "hidden_metadata_exposed": False,
            "body_free": True,
        })
    return reviewer_rows


def _assert_pmn_op05_bodyfree_row(row: Mapping[str, Any], *, source: str) -> None:
    if row.get("body_free") is not True:
        raise ValueError(f"{source} row must be body-free")
    if _scan_forbidden_payload_key_paths(row, path=source):
        raise ValueError(f"{source} row contains forbidden body/question/path/hash key")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "family_exposed",
        "tier_exposed",
        "case_ref_exposed",
        "packet_ref_exposed",
        "expected_result_exposed",
        "hidden_metadata_exposed",
    ):
        if false_key in row and row.get(false_key) is not False:
            raise ValueError(f"{source} row must keep {false_key}=False")


def _mn11_promotion_claim_refs(mn11_material: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(mn11_material, Mapping):
        return []
    claim_fields = (
        "actual_review_evidence_complete_from_real_review",
        "actual_review_evidence_complete",
        "actual_human_review_complete",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_selection_rows_created_here",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_actual_execution_confirmed",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
    )
    return [field for field in claim_fields if mn11_material.get(field) is True]


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str, allowed_true_flag_refs: Sequence[str] = ()
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_MN11_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_MN11_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_MN11_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != operation_step_ref or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step ref changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or claim GitHub connection check")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    allowed_true_flags = set(allowed_true_flag_refs)
    for field in P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS:
        if field in allowed_true_flags:
            continue
        if data.get(field) is not False:
            raise ValueError(f"{source} required false flag changed: {field}")
    if any(value is not False for value in (data.get("public_contract") or {}).values()):
        raise ValueError(f"{source} public contract mutated")
    if any(value is not False for value in (data.get("post_mn11_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract mutated")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free marker changed")
    if any(key in P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains forbidden top-level payload key")


def build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build PMN-OP00 body-free scope / no-touch / no-promotion material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP00_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "chosen_stage_ref": P7_R54_AHR_POST_MN11_CHOSEN_STAGE_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_MN11_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_MN11_NOT_STAGE_REFS),
        "post_mn11_actual_operation_scope_confirmed": True,
        "post_mn11_actual_operation_evidence_intake_reentry_scope": True,
        "no_touch_boundary_confirmed": True,
        "no_promotion_boundary_confirmed": True,
        "pmn_op00_does_not_intake_mn11_manual_decision": True,
        "pmn_op00_does_not_generate_body_full_packet": True,
        "pmn_op00_does_not_run_actual_human_review": True,
        "pmn_op00_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "p8_question_design_out_of_scope": True,
        "p8_question_implementation_out_of_scope": True,
        "p6_start_out_of_scope": True,
        "r52_actual_execution_out_of_scope": True,
        "p5_finalization_out_of_scope": True,
        "p7_complete_out_of_scope": True,
        "release_decision_out_of_scope": True,
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen": True,
        "required_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "support_material_refs": list(P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS),
        "claim_boundary_refs": list(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_MN11_PMN_OP00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostMN11-PMN-OP00 scope / no-touch / no-promotion boundary freeze",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP00_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP00 scope / no-touch / no-promotion boundary freeze",
    )
    for key in (
        "post_mn11_actual_operation_scope_confirmed",
        "post_mn11_actual_operation_evidence_intake_reentry_scope",
        "no_touch_boundary_confirmed",
        "no_promotion_boundary_confirmed",
        "pmn_op00_does_not_intake_mn11_manual_decision",
        "pmn_op00_does_not_generate_body_full_packet",
        "pmn_op00_does_not_run_actual_human_review",
        "pmn_op00_does_not_create_operation_receipt_or_rows_or_disposal",
        "p8_question_design_out_of_scope",
        "p8_question_implementation_out_of_scope",
        "p6_start_out_of_scope",
        "r52_actual_execution_out_of_scope",
        "p5_finalization_out_of_scope",
        "p7_complete_out_of_scope",
        "release_decision_out_of_scope",
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP00 required true boundary changed: {key}")
    if tuple(data.get("not_stage_refs") or ()) != P7_R54_AHR_POST_MN11_NOT_STAGE_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 not-stage refs changed")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("local_received_zip_refs", "local_received_zip_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP00 {count_field} changed")
    if data.get("required_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 required case count changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 actual review basis allowed ref changed")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 local zip refs changed")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 cannot treat local zip refs as actual review basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 cannot rewrite current actual review basis")
    if tuple(data.get("support_material_refs") or ()) != P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 support material refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP00 next required step changed")
    return True


def _pmn_op01_blockers(mn11_manual_decision_material: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(mn11_manual_decision_material, Mapping):
        return ["pmn_op01_mn11_manual_decision_envelope_missing"]

    forbidden_paths = _scan_forbidden_payload_key_paths(mn11_manual_decision_material)
    if forbidden_paths:
        blockers.append("pmn_op01_mn11_forbidden_body_question_path_hash_key_detected")

    try:
        mn.assert_p7_r54_ahr_post_ex18_mn11_acceptance_fail_closed_finalizer_contract(mn11_manual_decision_material)
    except ValueError:
        blockers.append("pmn_op01_mn11_manual_decision_envelope_contract_invalid")

    if mn11_manual_decision_material.get("mn11_ready") is not True:
        blockers.append("pmn_op01_mn11_not_ready")
    if mn11_manual_decision_material.get("manual_decision_ref") != P7_R54_AHR_POST_MN11_MANUAL_DECISION_REF:
        blockers.append("pmn_op01_manual_decision_ref_not_return_to_actual_review_operation_required")
    if mn11_manual_decision_material.get("actual_review_evidence_status_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_EVIDENCE_STATUS_REF:
        blockers.append("pmn_op01_actual_review_evidence_status_not_missing_real_review_required")
    if mn11_manual_decision_material.get("next_required_step") != P7_R54_AHR_POST_MN11_NEXT_REQUIRED_STEP_REF:
        blockers.append("pmn_op01_next_required_step_not_actual_local_only_human_review_operation")
    if mn11_manual_decision_material.get("actual_review_evidence_complete_from_real_review") is not False:
        blockers.append("pmn_op01_actual_review_evidence_complete_from_real_review_not_false")
    if mn11_manual_decision_material.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("pmn_op01_actual_review_basis_ref_mismatch")
    if mn11_manual_decision_material.get("local_received_zip_refs_are_actual_review_basis") is not False:
        blockers.append("pmn_op01_local_zip_refs_claimed_as_actual_review_basis")
    if mn11_manual_decision_material.get("local_received_zip_refs_used_to_rewrite_current_actual_review_basis") is not False:
        blockers.append("pmn_op01_current_actual_review_basis_rewrite_claim_detected")
    if _mn11_promotion_claim_refs(mn11_manual_decision_material):
        blockers.append("pmn_op01_mn11_promotion_or_completion_claim_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
    *,
    scope_no_touch_no_promotion_boundary_freeze: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP01 body-free MN11 manual-decision intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op00 = scope_no_touch_no_promotion_boundary_freeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze(
            review_session_id=session_id
        )
    blockers = _pmn_op01_blockers(mn11_manual_decision_material)
    op00_ready = False
    try:
        op00_ready = (
            assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(op00) is True
        )
    except ValueError:
        blockers.append("pmn_op01_op00_scope_no_touch_no_promotion_boundary_invalid")
    if not op00_ready:
        blockers.append("pmn_op01_op00_scope_no_touch_no_promotion_boundary_not_ready")

    ready = not blockers
    mn11_material = mn11_manual_decision_material if isinstance(mn11_manual_decision_material, Mapping) else {}
    forbidden_paths = _scan_forbidden_payload_key_paths(mn11_material)
    promotion_claim_refs = _mn11_promotion_claim_refs(mn11_material)

    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP01_MN11_MANUAL_DECISION_INTAKE_BASIS_CONFIRMATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else "", default="op00_schema_missing", max_length=220),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else "", default="op00_material_missing", max_length=220),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else "", default="op00_next_required_step_missing", max_length=220),
        "op00_scope_confirmed": bool(isinstance(op00, Mapping) and op00.get("post_mn11_actual_operation_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("no_promotion_boundary_confirmed") is True),
        "pmn_op01_status_ref": (
            P7_R54_AHR_POST_MN11_PMN_OP01_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_STATUS_REF
        ),
        "pmn_op01_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP01_ALLOWED_STATUS_REFS),
        "pmn_op01_ready": ready,
        "pmn_op01_blocker_refs": blockers,
        "pmn_op01_blocker_ref_count": len(blockers),
        "pmn_op01_reason_refs": ["pmn_op01_mn11_return_operation_required_basis_confirmed_bodyfree"] if ready else [],
        "pmn_op01_reason_ref_count": 1 if ready else 0,
        "support_material_refs": list(P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS),
        "mn11_result_memo_ref": P7_R54_AHR_POST_MN11_MN11_RESULT_MEMO_REF,
        "mn11_result_memo_ref_present": bool(isinstance(mn11_manual_decision_material, Mapping)),
        "mn11_bodyfree_envelope_present": bool(isinstance(mn11_manual_decision_material, Mapping)),
        "mn11_schema_version": _clean_ref(mn11_material.get("schema_version"), max_length=220),
        "mn11_operation_step_ref": _clean_ref(mn11_material.get("operation_step_ref"), max_length=220),
        "mn11_status_ref": _clean_ref(mn11_material.get("mn11_status_ref"), max_length=180),
        "mn11_ready": mn11_material.get("mn11_ready") is True,
        "mn11_manual_decision_ref": _clean_ref(mn11_material.get("manual_decision_ref"), max_length=180),
        "mn11_final_manual_decision_ref": _clean_ref(mn11_material.get("final_manual_decision_ref"), max_length=180),
        "mn11_manual_decision_status_ref": _clean_ref(mn11_material.get("manual_decision_status_ref"), max_length=180),
        "mn11_actual_review_evidence_status_ref": _clean_ref(mn11_material.get("actual_review_evidence_status_ref"), max_length=180),
        "mn11_next_required_step": _clean_ref(mn11_material.get("next_required_step"), max_length=220),
        "mn11_actual_review_evidence_complete_from_real_review": (
            mn11_material.get("actual_review_evidence_complete_from_real_review") is True
        ),
        "mn11_actual_review_basis_ref": _clean_ref(mn11_material.get("actual_review_basis_ref"), max_length=180),
        "mn11_manual_decision_ref_confirmed": mn11_material.get("manual_decision_ref") == P7_R54_AHR_POST_MN11_MANUAL_DECISION_REF,
        "mn11_actual_review_evidence_missing_real_review_required_confirmed": (
            mn11_material.get("actual_review_evidence_status_ref") == P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_EVIDENCE_STATUS_REF
        ),
        "mn11_next_required_step_confirmed": mn11_material.get("next_required_step") == P7_R54_AHR_POST_MN11_NEXT_REQUIRED_STEP_REF,
        "mn11_actual_review_evidence_complete_from_real_review_false_confirmed": (
            mn11_material.get("actual_review_evidence_complete_from_real_review") is False
        ),
        "mn11_actual_review_basis_ref_confirmed": (
            mn11_material.get("actual_review_basis_ref") == P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF
        ),
        "mn11_no_body_leak_validation_passed_reported": mn11_material.get("no_body_leak_validation_passed") is True,
        "mn11_no_question_text_validation_passed_reported": mn11_material.get("no_question_text_validation_passed") is True,
        "mn11_no_path_hash_validation_passed_reported": mn11_material.get("no_path_hash_validation_passed") is True,
        "mn11_no_touch_boundary_confirmed_reported": mn11_material.get("no_touch_boundary_confirmed") is True,
        "mn11_no_promotion_boundary_confirmed_reported": mn11_material.get("no_promotion_boundary_confirmed") is True,
        "mn11_green_is_not_actual_human_review_complete": True,
        "mn11_manual_decision_is_not_actual_operation_receipt": True,
        "pmn_op01_does_not_treat_mn11_green_as_real_review_complete": True,
        "pmn_op01_does_not_generate_body_full_packet": True,
        "pmn_op01_does_not_run_actual_human_review": True,
        "pmn_op01_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "pmn_op01_does_not_start_p8_p6_r52_or_release": True,
        "pmn_op01_passes_to_existing_support_material_inventory": ready,
        "actual_local_only_human_review_operation_required_before_downstream_decision": ready,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "basis_rewrite_required_here": False,
        "basis_rewritten_here": False,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "outer_received_zip_label_difference_recorded_bodyfree": True,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "mn11_forbidden_payload_key_paths": [_clean_ref(path, max_length=220) for path in forbidden_paths],
        "mn11_forbidden_payload_key_path_count": len(forbidden_paths),
        "mn11_promotion_claim_refs": [_clean_ref(ref, max_length=160) for ref in promotion_claim_refs],
        "mn11_promotion_claim_ref_count": len(promotion_claim_refs),
        "claim_boundary_refs": list(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP01_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP00_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP01_NOT_YET_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP00_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_MN11_PMN_OP01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostMN11-PMN-OP01 MN11 manual decision intake / basis confirmation",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP01_MN11_MANUAL_DECISION_INTAKE_BASIS_CONFIRMATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP01 MN11 manual decision intake / basis confirmation",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_MN11_PMN_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 OP00 next required step changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "mn11_green_is_not_actual_human_review_complete",
        "mn11_manual_decision_is_not_actual_operation_receipt",
        "pmn_op01_does_not_treat_mn11_green_as_real_review_complete",
        "pmn_op01_does_not_generate_body_full_packet",
        "pmn_op01_does_not_run_actual_human_review",
        "pmn_op01_does_not_create_operation_receipt_or_rows_or_disposal",
        "pmn_op01_does_not_start_p8_p6_r52_or_release",
        "outer_received_zip_label_difference_recorded_bodyfree",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP01 required true boundary changed: {key}")
    if tuple(data.get("pmn_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 allowed status refs changed")
    for field, count_field in (
        ("support_material_refs", "support_material_ref_count"),
        ("pmn_op01_blocker_refs", "pmn_op01_blocker_ref_count"),
        ("pmn_op01_reason_refs", "pmn_op01_reason_ref_count"),
        ("mn11_forbidden_payload_key_paths", "mn11_forbidden_payload_key_path_count"),
        ("mn11_promotion_claim_refs", "mn11_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP01 {count_field} changed")
    if tuple(data.get("support_material_refs") or ()) != P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 support material refs changed")
    if data.get("mn11_result_memo_ref") != P7_R54_AHR_POST_MN11_MN11_RESULT_MEMO_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 MN11 result memo ref changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 actual review basis allowed changed")
    if data.get("basis_rewrite_required_here") is not False or data.get("basis_rewritten_here") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 cannot rewrite basis")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 local zip refs changed")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 cannot treat local zip refs as actual review basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 cannot rewrite current actual review basis")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 not-claimed boundary must stay false")

    ready = data.get("pmn_op01_status_ref") == P7_R54_AHR_POST_MN11_PMN_OP01_READY_STATUS_REF
    if data.get("pmn_op01_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 ready flag changed")
    if ready:
        if data.get("pmn_op01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 ready material cannot carry blockers")
        if data.get("pmn_op01_reason_refs") != ["pmn_op01_mn11_return_operation_required_basis_confirmed_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 ready reason changed")
        for key in (
            "mn11_bodyfree_envelope_present",
            "mn11_ready",
            "mn11_manual_decision_ref_confirmed",
            "mn11_actual_review_evidence_missing_real_review_required_confirmed",
            "mn11_next_required_step_confirmed",
            "mn11_actual_review_evidence_complete_from_real_review_false_confirmed",
            "mn11_actual_review_basis_ref_confirmed",
            "mn11_no_body_leak_validation_passed_reported",
            "mn11_no_question_text_validation_passed_reported",
            "mn11_no_path_hash_validation_passed_reported",
            "mn11_no_touch_boundary_confirmed_reported",
            "mn11_no_promotion_boundary_confirmed_reported",
            "pmn_op01_passes_to_existing_support_material_inventory",
            "actual_local_only_human_review_operation_required_before_downstream_decision",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP01 ready condition changed: {key}")
        if data.get("mn11_manual_decision_ref") != P7_R54_AHR_POST_MN11_MANUAL_DECISION_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 MN11 manual decision changed")
        if data.get("mn11_final_manual_decision_ref") != P7_R54_AHR_POST_MN11_MANUAL_DECISION_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 MN11 final manual decision changed")
        if data.get("mn11_actual_review_evidence_status_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_EVIDENCE_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 MN11 evidence status changed")
        if data.get("mn11_next_required_step") != P7_R54_AHR_POST_MN11_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 MN11 next required step changed")
        if data.get("mn11_actual_review_evidence_complete_from_real_review") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 cannot accept completed actual evidence")
        if data.get("mn11_actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 MN11 actual review basis changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP01_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP01_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 next required step changed")
    else:
        if data.get("pmn_op01_status_ref") != P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 blocked status changed")
        if not data.get("pmn_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 blocked material must carry blockers")
        if data.get("pmn_op01_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 blocked material cannot carry ready reasons")
        if data.get("pmn_op01_passes_to_existing_support_material_inventory") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 blocked material cannot pass to OP02")
        if data.get("actual_local_only_human_review_operation_required_before_downstream_decision") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 blocked material cannot claim operation requirement ready")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP00_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP01 blocked next step changed")
    return True


def _pmn_op02_blockers(op01: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op01, Mapping):
        return ["pmn_op02_op01_mn11_intake_material_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(op01)
    except ValueError:
        blockers.append("pmn_op02_op01_mn11_intake_contract_invalid")
    if op01.get("pmn_op01_ready") is not True:
        blockers.append("pmn_op02_op01_mn11_intake_not_ready")
    if op01.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF:
        blockers.append("pmn_op02_op01_next_step_not_existing_support_material_inventory")
    if op01.get("pmn_op01_passes_to_existing_support_material_inventory") is not True:
        blockers.append("pmn_op02_op01_does_not_pass_to_support_inventory")
    if op01.get("mn11_manual_decision_ref_confirmed") is not True:
        blockers.append("pmn_op02_mn11_manual_decision_ref_not_confirmed")
    if op01.get("mn11_actual_review_basis_ref_confirmed") is not True:
        blockers.append("pmn_op02_mn11_actual_review_basis_ref_not_confirmed")
    if len(P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS) != 25:
        blockers.append("pmn_op02_existing_op_line_step_count_mismatch")
    if len(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS) != 12:
        blockers.append("pmn_op02_existing_ex_line_reentry_step_count_mismatch")
    if len(P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_STEP_REFS) != 12:
        blockers.append("pmn_op02_existing_mn_line_step_count_mismatch")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory(
    *,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP02 body-free OP / EX / MN support-material inventory."""

    session_id = _safe_review_session_id(review_session_id)
    op01 = mn11_manual_decision_intake_basis_confirmation
    if op01 is None:
        op01 = build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op02_blockers(op01)
    ready = not blockers
    existing_op_line_reuse_candidate = ready
    existing_ex_line_reentry_candidate = ready
    existing_mn_line_manual_decision_intake_candidate = ready
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP02_EXISTING_OP_EX_MN_SUPPORT_MATERIAL_INVENTORY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01.get("schema_version") if isinstance(op01, Mapping) else "", default="op01_schema_missing", max_length=220),
        "op01_material_ref": _clean_ref(op01.get("material_id") if isinstance(op01, Mapping) else "", default="op01_material_missing", max_length=220),
        "op01_next_required_step": _clean_ref(op01.get("next_required_step") if isinstance(op01, Mapping) else "", default="op01_next_required_step_missing", max_length=220),
        "op01_ready": bool(isinstance(op01, Mapping) and op01.get("pmn_op01_ready") is True),
        "op01_manual_decision_ref_confirmed": bool(isinstance(op01, Mapping) and op01.get("mn11_manual_decision_ref_confirmed") is True),
        "op01_actual_review_basis_ref_confirmed": bool(isinstance(op01, Mapping) and op01.get("mn11_actual_review_basis_ref_confirmed") is True),
        "op01_passes_to_existing_support_material_inventory": bool(isinstance(op01, Mapping) and op01.get("pmn_op01_passes_to_existing_support_material_inventory") is True),
        "support_inventory_status_ref": (
            P7_R54_AHR_POST_MN11_PMN_OP02_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_STATUS_REF
        ),
        "support_inventory_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP02_ALLOWED_STATUS_REFS),
        "support_inventory_ready": ready,
        "support_inventory_blocker_refs": blockers,
        "support_inventory_blocker_ref_count": len(blockers),
        "support_inventory_reason_refs": [
            "existing_op_line_reuse_candidate_confirmed_bodyfree",
            "existing_postcr22_ex07_ex18_reentry_candidate_confirmed_bodyfree",
            "existing_postex18_mn00_mn11_intake_candidate_confirmed_bodyfree",
            "new_giant_wrapper_not_required_minimal_bridge_only",
        ] if ready else [],
        "support_inventory_reason_ref_count": 4 if ready else 0,
        "existing_op_line_helper_ref": "ai/services/ai_inference/emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.py",
        "existing_op_line_step_refs": list(P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS),
        "existing_op_line_step_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS),
        "existing_op_line_first_step_ref": P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS[0],
        "existing_op_line_last_step_ref": P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS[-1],
        "existing_op_line_reuse_role_refs": list(P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_REUSE_ROLE_REFS),
        "existing_op_line_reuse_role_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_REUSE_ROLE_REFS),
        "existing_op_line_reuse_candidate": existing_op_line_reuse_candidate,
        "existing_ex_line_helper_ref": "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629.py",
        "existing_ex_line_reentry_step_refs": list(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS),
        "existing_ex_line_reentry_step_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS),
        "existing_ex_line_reentry_first_step_ref": P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[0],
        "existing_ex_line_reentry_last_step_ref": P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[-1],
        "existing_ex_line_reentry_role_refs": list(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS),
        "existing_ex_line_reentry_role_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS),
        "existing_ex_line_reentry_candidate": existing_ex_line_reentry_candidate,
        "existing_mn_line_helper_ref": "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_ex18_manual_next_decision_return_to_actual_review_operation_20260630.py",
        "existing_mn_line_step_refs": list(P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_STEP_REFS),
        "existing_mn_line_step_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_STEP_REFS),
        "existing_mn_line_first_step_ref": P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_STEP_REFS[0],
        "existing_mn_line_last_step_ref": P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_STEP_REFS[-1],
        "existing_mn_line_intake_role_refs": list(P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_INTAKE_ROLE_REFS),
        "existing_mn_line_intake_role_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_INTAKE_ROLE_REFS),
        "existing_mn_line_manual_decision_intake_candidate": existing_mn_line_manual_decision_intake_candidate,
        "new_giant_wrapper_required": False,
        "minimal_bridge_allowed_if_needed": ready,
        "post_mn11_helper_role_limited_to_bridge": True,
        "existing_support_material_inventory_does_not_modify_existing_helpers": True,
        "pmn_op02_does_not_generate_body_full_packet": True,
        "pmn_op02_does_not_run_actual_human_review": True,
        "pmn_op02_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "pmn_op02_does_not_start_p8_p6_r52_or_release": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "support_material_refs": list(P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS),
        "claim_boundary_refs": list(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP02_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP01_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP02_NOT_YET_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP01_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_MN11_PMN_OP02_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostMN11-PMN-OP02 existing OP / EX / MN support material inventory",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP02_EXISTING_OP_EX_MN_SUPPORT_MATERIAL_INVENTORY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP02 existing OP / EX / MN support material inventory",
    )
    if data.get("op01_schema_version") != P7_R54_AHR_POST_MN11_PMN_OP01_MN11_MANUAL_DECISION_INTAKE_BASIS_CONFIRMATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 OP01 schema version changed")
    for key in (
        "post_mn11_helper_role_limited_to_bridge",
        "existing_support_material_inventory_does_not_modify_existing_helpers",
        "pmn_op02_does_not_generate_body_full_packet",
        "pmn_op02_does_not_run_actual_human_review",
        "pmn_op02_does_not_create_operation_receipt_or_rows_or_disposal",
        "pmn_op02_does_not_start_p8_p6_r52_or_release",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP02 required true boundary changed: {key}")
    for field, count_field in (
        ("support_inventory_blocker_refs", "support_inventory_blocker_ref_count"),
        ("support_inventory_reason_refs", "support_inventory_reason_ref_count"),
        ("existing_op_line_step_refs", "existing_op_line_step_ref_count"),
        ("existing_op_line_reuse_role_refs", "existing_op_line_reuse_role_ref_count"),
        ("existing_ex_line_reentry_step_refs", "existing_ex_line_reentry_step_ref_count"),
        ("existing_ex_line_reentry_role_refs", "existing_ex_line_reentry_role_ref_count"),
        ("existing_mn_line_step_refs", "existing_mn_line_step_ref_count"),
        ("existing_mn_line_intake_role_refs", "existing_mn_line_intake_role_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP02 {count_field} changed")
    if tuple(data.get("support_inventory_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 status refs changed")
    if tuple(data.get("existing_op_line_step_refs") or ()) != P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 OP line step refs changed")
    if data.get("existing_op_line_first_step_ref") != P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS[0]:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 OP line first step changed")
    if data.get("existing_op_line_last_step_ref") != P7_R54_AHR_POST_MN11_EXISTING_OP_LINE_STEP_REFS[-1]:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 OP line last step changed")
    if tuple(data.get("existing_ex_line_reentry_step_refs") or ()) != P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 EX line reentry refs changed")
    if data.get("existing_ex_line_reentry_first_step_ref") != P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[0]:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 EX first reentry step changed")
    if data.get("existing_ex_line_reentry_last_step_ref") != P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[-1]:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 EX last reentry step changed")
    if tuple(data.get("existing_mn_line_step_refs") or ()) != P7_R54_AHR_POST_MN11_EXISTING_MN_LINE_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 MN line refs changed")
    if tuple(data.get("support_material_refs") or ()) != P7_R54_AHR_POST_MN11_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 support material refs changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 actual review basis allowed changed")
    if data.get("new_giant_wrapper_required") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 must not require a new giant wrapper")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 not-claimed boundary must stay false")
    ready = data.get("support_inventory_status_ref") == P7_R54_AHR_POST_MN11_PMN_OP02_READY_STATUS_REF
    if data.get("support_inventory_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 ready flag changed")
    if ready:
        if data.get("support_inventory_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 ready material cannot carry blockers")
        for key in (
            "op01_ready",
            "op01_manual_decision_ref_confirmed",
            "op01_actual_review_basis_ref_confirmed",
            "op01_passes_to_existing_support_material_inventory",
            "existing_op_line_reuse_candidate",
            "existing_ex_line_reentry_candidate",
            "existing_mn_line_manual_decision_intake_candidate",
            "minimal_bridge_allowed_if_needed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP02 ready condition changed: {key}")
        if data.get("op01_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 OP01 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP02_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP02_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 next step changed")
    else:
        if data.get("support_inventory_status_ref") != P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 blocked status changed")
        if not data.get("support_inventory_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 blocked material must carry blockers")
        if any(data.get(key) is not False for key in (
            "existing_op_line_reuse_candidate",
            "existing_ex_line_reentry_candidate",
            "existing_mn_line_manual_decision_intake_candidate",
            "minimal_bridge_allowed_if_needed",
        )):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 blocked candidate flags must be false")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP02 blocked next step changed")
    return True


def _pmn_op03_blockers(op02: Mapping[str, Any] | None, *, review_session_id: str) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op02, Mapping):
        blockers.append("pmn_op03_support_inventory_material_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(op02)
        except ValueError:
            blockers.append("pmn_op03_support_inventory_contract_invalid")
        if op02.get("support_inventory_ready") is not True:
            blockers.append("pmn_op03_support_inventory_not_ready")
        if op02.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF:
            blockers.append("pmn_op03_support_inventory_next_step_not_review_session_guard")
        for field in (
            "existing_op_line_reuse_candidate",
            "existing_ex_line_reentry_candidate",
            "existing_mn_line_manual_decision_intake_candidate",
        ):
            if op02.get(field) is not True:
                blockers.append(f"pmn_op03_{field}_not_ready")
    if not review_session_id:
        blockers.append("pmn_op03_review_session_id_missing")
    if _ref_has_local_path_shape(review_session_id):
        blockers.append("pmn_op03_review_session_id_has_local_path_shape")
    if _ref_has_question_or_body_text_shape(review_session_id):
        blockers.append("pmn_op03_review_session_id_has_question_or_body_text_shape")
    if not P7_R54_AHR_POST_MN11_ALLOWED_ACTUAL_SOURCE_REFS:
        blockers.append("pmn_op03_allowed_actual_source_refs_missing")
    if not P7_R54_AHR_POST_MN11_FORBIDDEN_ACTUAL_SOURCE_REFS:
        blockers.append("pmn_op03_forbidden_actual_source_refs_missing")
    if set(P7_R54_AHR_POST_MN11_ALLOWED_ACTUAL_SOURCE_REFS).intersection(
        P7_R54_AHR_POST_MN11_FORBIDDEN_ACTUAL_SOURCE_REFS
    ):
        blockers.append("pmn_op03_allowed_forbidden_actual_source_refs_overlap")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
    *,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP03 body-free review-session envelope and actual source guard."""

    session_id = _safe_review_session_id(review_session_id)
    op02_material = existing_op_ex_mn_support_material_inventory
    if op02_material is None:
        op02_material = build_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory(
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op03_blockers(op02_material, review_session_id=session_id)
    ready = not blockers
    source_guard_false_fields = {key: False for key in P7_R54_AHR_POST_MN11_SOURCE_GUARD_REQUIRED_FALSE_FIELD_REFS}
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP03_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02_material.get("schema_version") if isinstance(op02_material, Mapping) else "", default="op02_schema_missing", max_length=220),
        "op02_material_ref": _clean_ref(op02_material.get("material_id") if isinstance(op02_material, Mapping) else "", default="op02_material_missing", max_length=220),
        "op02_next_required_step": _clean_ref(op02_material.get("next_required_step") if isinstance(op02_material, Mapping) else "", default="op02_next_required_step_missing", max_length=220),
        "op02_support_inventory_ready": bool(isinstance(op02_material, Mapping) and op02_material.get("support_inventory_ready") is True),
        "op02_existing_op_line_reuse_candidate": bool(isinstance(op02_material, Mapping) and op02_material.get("existing_op_line_reuse_candidate") is True),
        "op02_existing_ex_line_reentry_candidate": bool(isinstance(op02_material, Mapping) and op02_material.get("existing_ex_line_reentry_candidate") is True),
        "op02_existing_mn_line_manual_decision_intake_candidate": bool(isinstance(op02_material, Mapping) and op02_material.get("existing_mn_line_manual_decision_intake_candidate") is True),
        "review_session_envelope_status_ref": (
            P7_R54_AHR_POST_MN11_PMN_OP03_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_STATUS_REF
        ),
        "review_session_envelope_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP03_ALLOWED_STATUS_REFS),
        "review_session_envelope_ready": ready,
        "review_session_envelope_blocker_refs": blockers,
        "review_session_envelope_blocker_ref_count": len(blockers),
        "review_session_state_ref": P7_R54_AHR_POST_MN11_REVIEW_SESSION_STATE_NOT_STARTED_REF,
        "allowed_review_session_state_refs": list(P7_R54_AHR_POST_MN11_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "allowed_review_session_state_ref_count": len(P7_R54_AHR_POST_MN11_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "allowed_ready_session_transition_refs": list(P7_R54_AHR_POST_MN11_ALLOWED_READY_SESSION_TRANSITION_REFS),
        "allowed_ready_session_transition_ref_count": len(P7_R54_AHR_POST_MN11_ALLOWED_READY_SESSION_TRANSITION_REFS),
        "forbidden_session_promotion_transition_refs": list(P7_R54_AHR_POST_MN11_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS),
        "forbidden_session_promotion_transition_ref_count": len(P7_R54_AHR_POST_MN11_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS),
        "review_session_id_bodyfree_identifier": bool(session_id) and not _ref_has_local_path_shape(session_id),
        "review_session_id_has_local_path_shape": _ref_has_local_path_shape(session_id),
        "review_session_id_has_question_or_body_text_shape": _ref_has_question_or_body_text_shape(session_id),
        "review_session_envelope_bodyfree_only": True,
        "review_session_envelope_does_not_start_preflight": True,
        "review_session_envelope_does_not_generate_body_full_packet": True,
        "review_session_envelope_does_not_run_actual_human_review": True,
        "actual_source_guard_required": True,
        "actual_source_guard_status_ref": (
            P7_R54_AHR_POST_MN11_PMN_OP03_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_STATUS_REF
        ),
        "actual_source_guard_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP03_ALLOWED_STATUS_REFS),
        "actual_source_guard_ready": ready,
        "actual_source_guard_step_blocker_refs": blockers,
        "actual_source_guard_step_blocker_ref_count": len(blockers),
        "allowed_actual_source_refs": list(P7_R54_AHR_POST_MN11_ALLOWED_ACTUAL_SOURCE_REFS),
        "allowed_actual_source_ref_count": len(P7_R54_AHR_POST_MN11_ALLOWED_ACTUAL_SOURCE_REFS),
        "forbidden_actual_source_refs": list(P7_R54_AHR_POST_MN11_FORBIDDEN_ACTUAL_SOURCE_REFS),
        "forbidden_actual_source_ref_count": len(P7_R54_AHR_POST_MN11_FORBIDDEN_ACTUAL_SOURCE_REFS),
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
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "allowed_actual_source_refs_are_from_existing_postcr22_ex_line": True,
        "forbidden_actual_source_refs_are_from_existing_postcr22_ex_line": True,
        **source_guard_false_fields,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_MN11_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP02_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP03_NOT_YET_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP02_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_MN11_PMN_OP03_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostMN11-PMN-OP03 review session envelope / actual source guard",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP03_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP03 review session envelope / actual source guard",
    )
    if data.get("op02_schema_version") != P7_R54_AHR_POST_MN11_PMN_OP02_EXISTING_OP_EX_MN_SUPPORT_MATERIAL_INVENTORY_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 OP02 schema version changed")
    for key in (
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
        "current_actual_review_basis_remains_264_85_258_171",
        "allowed_actual_source_refs_are_from_existing_postcr22_ex_line",
        "forbidden_actual_source_refs_are_from_existing_postcr22_ex_line",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP03 required true field changed: {key}")
    for field, count_field in (
        ("review_session_envelope_blocker_refs", "review_session_envelope_blocker_ref_count"),
        ("actual_source_guard_step_blocker_refs", "actual_source_guard_step_blocker_ref_count"),
        ("allowed_review_session_state_refs", "allowed_review_session_state_ref_count"),
        ("allowed_ready_session_transition_refs", "allowed_ready_session_transition_ref_count"),
        ("forbidden_session_promotion_transition_refs", "forbidden_session_promotion_transition_ref_count"),
        ("allowed_actual_source_refs", "allowed_actual_source_ref_count"),
        ("forbidden_actual_source_refs", "forbidden_actual_source_ref_count"),
        ("local_received_zip_refs", "local_received_zip_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP03 {count_field} changed")
    if data.get("review_session_id_bodyfree_identifier") is not True:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 review session id must be body-free")
    if data.get("review_session_id_has_local_path_shape") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 review session id must not contain path shape")
    if data.get("review_session_id_has_question_or_body_text_shape") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 review session id must not carry question/body text")
    if tuple(data.get("review_session_envelope_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 envelope status refs changed")
    if tuple(data.get("actual_source_guard_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 source guard status refs changed")
    if tuple(data.get("allowed_review_session_state_refs") or ()) != P7_R54_AHR_POST_MN11_ALLOWED_REVIEW_SESSION_STATE_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 session state refs changed")
    if tuple(data.get("allowed_ready_session_transition_refs") or ()) != P7_R54_AHR_POST_MN11_ALLOWED_READY_SESSION_TRANSITION_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 ready transition refs changed")
    if tuple(data.get("forbidden_session_promotion_transition_refs") or ()) != P7_R54_AHR_POST_MN11_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 forbidden transition refs changed")
    if tuple(data.get("allowed_actual_source_refs") or ()) != P7_R54_AHR_POST_MN11_ALLOWED_ACTUAL_SOURCE_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 allowed actual source refs changed")
    if tuple(data.get("forbidden_actual_source_refs") or ()) != P7_R54_AHR_POST_MN11_FORBIDDEN_ACTUAL_SOURCE_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 forbidden actual source refs changed")
    if set(data.get("allowed_actual_source_refs") or []).intersection(data.get("forbidden_actual_source_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 allowed/forbidden actual source refs overlap")
    for key in P7_R54_AHR_POST_MN11_SOURCE_GUARD_REQUIRED_FALSE_FIELD_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP03 source guard false field promoted: {key}")
    if data.get("actual_rows_source_guard_passed") is not False or data.get("actual_rows_intaked_here") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 must not intake actual rows")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 actual review basis allowed changed")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_MN11_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 local zip refs changed")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 cannot treat local zip refs as actual review basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 cannot rewrite current actual review basis")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 not-claimed boundary must stay false")
    blockers = list(data.get("actual_source_guard_step_blocker_refs") or [])
    ready = not blockers
    if list(data.get("review_session_envelope_blocker_refs") or []) != blockers:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 envelope/source guard blockers diverged")
    if data.get("review_session_envelope_ready") is not ready or data.get("actual_source_guard_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 ready flags changed")
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP03_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_STATUS_REF
    if data.get("review_session_envelope_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 envelope status changed")
    if data.get("actual_source_guard_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 source guard status changed")
    if data.get("review_session_state_ref") != P7_R54_AHR_POST_MN11_REVIEW_SESSION_STATE_NOT_STARTED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 must leave session not started")
    if ready:
        for key in (
            "op02_support_inventory_ready",
            "op02_existing_op_line_reuse_candidate",
            "op02_existing_ex_line_reentry_candidate",
            "op02_existing_mn_line_manual_decision_intake_candidate",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP03 ready dependency changed: {key}")
        if data.get("op02_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 OP02 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP03_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 blocked material must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP03 blocked next step changed")
    return True


def _pmn_op04_blockers(op03: Mapping[str, Any] | None, *, refs: Mapping[str, str]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op03, Mapping):
        return ["pmn_op04_review_session_envelope_actual_source_guard_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(op03)
    except ValueError:
        blockers.append("pmn_op04_op03_review_session_envelope_actual_source_guard_invalid")
    if op03.get("review_session_envelope_ready") is not True:
        blockers.append("pmn_op04_op03_review_session_envelope_not_ready")
    if op03.get("actual_source_guard_ready") is not True:
        blockers.append("pmn_op04_op03_actual_source_guard_not_ready")
    if op03.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF:
        blockers.append("pmn_op04_op03_next_step_not_local_only_preflight")
    if op03.get("review_session_state_ref") != P7_R54_AHR_POST_MN11_REVIEW_SESSION_STATE_NOT_STARTED_REF:
        blockers.append("pmn_op04_review_session_state_not_started_mismatch")
    if _scan_forbidden_payload_key_paths(op03):
        blockers.append("pmn_op04_op03_forbidden_body_question_path_hash_key_detected")

    local_review_root_ref = refs.get("local_review_root_ref", "")
    explicit_allow_ref = refs.get("explicit_allow_ref", "")
    retention_policy_ref = refs.get("retention_policy_ref", "")
    disposal_policy_ref = refs.get("disposal_policy_ref", "")
    export_denylist_policy_ref = refs.get("export_denylist_policy_ref", "")
    if local_review_root_ref != P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_REVIEW_ROOT_REF:
        blockers.append("pmn_op04_local_review_root_ref_missing_or_mismatched")
    if _ref_has_local_path_shape(local_review_root_ref) or _ref_has_question_or_body_text_shape(local_review_root_ref):
        blockers.append("pmn_op04_local_review_root_ref_not_bodyfree_identifier")
    if explicit_allow_ref != P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF:
        blockers.append("pmn_op04_explicit_allow_ref_missing_or_mismatched")
    if _ref_has_local_path_shape(explicit_allow_ref) or _ref_has_question_or_body_text_shape(explicit_allow_ref):
        blockers.append("pmn_op04_explicit_allow_ref_not_bodyfree_identifier")
    if retention_policy_ref != P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF:
        blockers.append("pmn_op04_retention_policy_ref_missing_or_mismatched")
    if disposal_policy_ref != P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF:
        blockers.append("pmn_op04_disposal_policy_ref_missing_or_mismatched")
    if export_denylist_policy_ref != P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF:
        blockers.append("pmn_op04_export_denylist_policy_ref_missing_or_mismatched")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary(
    *,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    local_review_root_ref: Any = None,
    explicit_allow_ref: Any = None,
    retention_policy_ref: Any = None,
    disposal_policy_ref: Any = None,
    export_denylist_policy_ref: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP04 body-free local-only preflight / explicit allow boundary."""

    session_id = _safe_review_session_id(review_session_id)
    op03 = review_session_envelope_actual_source_guard_freeze
    if op03 is None:
        op03 = build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    local_root_ref = _clean_ref(local_review_root_ref, default="missing_local_review_root_ref", max_length=180)
    allow_ref = _clean_ref(explicit_allow_ref, default="missing_explicit_allow_ref", max_length=180)
    retention_ref = _clean_ref(retention_policy_ref, default="missing_retention_policy_ref", max_length=180)
    disposal_ref = _clean_ref(disposal_policy_ref, default="missing_disposal_policy_ref", max_length=180)
    denylist_ref = _clean_ref(export_denylist_policy_ref, default="missing_export_denylist_policy_ref", max_length=180)
    refs = {
        "local_review_root_ref": local_root_ref,
        "explicit_allow_ref": allow_ref,
        "retention_policy_ref": retention_ref,
        "disposal_policy_ref": disposal_ref,
        "export_denylist_policy_ref": denylist_ref,
    }
    blockers = _pmn_op04_blockers(op03, refs=refs)
    ready = not blockers
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": _clean_ref(op03.get("schema_version") if isinstance(op03, Mapping) else "", default="op03_schema_missing", max_length=220),
        "op03_material_ref": _clean_ref(op03.get("material_id") if isinstance(op03, Mapping) else "", default="op03_material_missing", max_length=220),
        "op03_next_required_step": _clean_ref(op03.get("next_required_step") if isinstance(op03, Mapping) else "", default="op03_next_required_step_missing", max_length=220),
        "op03_review_session_envelope_ready": bool(isinstance(op03, Mapping) and op03.get("review_session_envelope_ready") is True),
        "op03_actual_source_guard_ready": bool(isinstance(op03, Mapping) and op03.get("actual_source_guard_ready") is True),
        "op03_review_session_state_ref": _clean_ref(op03.get("review_session_state_ref") if isinstance(op03, Mapping) else "", default="op03_review_session_state_missing", max_length=180),
        "local_only_preflight_status_ref": (
            P7_R54_AHR_POST_MN11_PMN_OP04_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_STATUS_REF
        ),
        "local_only_preflight_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP04_ALLOWED_STATUS_REFS),
        "local_only_preflight_ready": ready,
        "local_only_preflight_blocker_refs": blockers,
        "local_only_preflight_blocker_ref_count": len(blockers),
        "local_only_preflight_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP04_READY_REASON_REFS) if ready else blockers,
        "local_only_preflight_reason_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP04_READY_REASON_REFS) if ready else len(blockers),
        "local_review_root_ref": local_root_ref,
        "local_review_root_ref_present": local_root_ref == P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_REVIEW_ROOT_REF,
        "local_review_root_ref_has_path_shape": _ref_has_local_path_shape(local_root_ref),
        "local_review_root_path_included": False,
        "explicit_allow_ref": allow_ref,
        "explicit_allow_ref_present": allow_ref == P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF,
        "explicit_allow_scope_ref": P7_R54_AHR_POST_MN11_PMN_OP04_ALLOW_SCOPE_REF,
        "explicit_allow_body_stored_here": False,
        "retention_policy_ref": retention_ref,
        "retention_policy_ref_present": retention_ref == P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF,
        "disposal_policy_ref": disposal_ref,
        "disposal_policy_ref_present": disposal_ref == P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF,
        "export_denylist_policy_ref": denylist_ref,
        "export_denylist_policy_ref_present": denylist_ref == P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF,
        "export_denylist_violation_refs": [],
        "export_denylist_violation_ref_count": 0,
        "purge_required_before_or_after_review": True,
        "purge_required_delete_target_refs": list(P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_DELETE_TARGET_REFS),
        "purge_required_delete_target_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_DELETE_TARGET_REFS),
        "local_only": True,
        "must_not_export": True,
        "body_full_packet_generation_allowed_for_local_review_only": ready,
        "body_full_packet_generation_allowed_by_preflight": ready,
        "body_full_packet_generation_request_allowed_next": False,
        "body_full_generation_blocked_until_manifest_refreeze": True,
        "body_full_packet_export_allowed": False,
        "body_free_summary_export_allowed": True,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "pmn_op04_does_not_generate_body_full_packet": True,
        "pmn_op04_does_not_run_actual_human_review": True,
        "pmn_op04_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "pmn_op04_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP04_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP04_NOT_YET_IMPLEMENTED_STEPS
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP03_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF
            if ready
            else P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostMN11-PMN-OP04 local-only preflight / explicit allow boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_BOUNDARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP04 local-only preflight / explicit allow boundary",
    )
    if data.get("op03_schema_version") != P7_R54_AHR_POST_MN11_PMN_OP03_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 OP03 schema version changed")
    if tuple(data.get("local_only_preflight_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 status refs changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 actual review basis allowed changed")
    for key in (
        "local_only",
        "must_not_export",
        "body_free_summary_export_allowed",
        "body_full_generation_blocked_until_manifest_refreeze",
        "purge_required_before_or_after_review",
        "current_actual_review_basis_remains_264_85_258_171",
        "pmn_op04_does_not_generate_body_full_packet",
        "pmn_op04_does_not_run_actual_human_review",
        "pmn_op04_does_not_create_operation_receipt_or_rows_or_disposal",
        "pmn_op04_does_not_start_p8_p6_r52_or_release",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP04 required true field changed: {key}")
    for key in (
        "local_review_root_ref_has_path_shape",
        "local_review_root_path_included",
        "explicit_allow_body_stored_here",
        "body_full_packet_generation_request_allowed_next",
        "body_full_packet_export_allowed",
        "body_full_packet_generated_here",
        "body_full_packet_materialized_here",
        "local_received_zip_refs_are_actual_review_basis",
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP04 required false field promoted: {key}")
    if tuple(data.get("purge_required_delete_target_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 purge delete target refs changed")
    if data.get("purge_required_delete_target_ref_count") != len(P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_DELETE_TARGET_REFS):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 purge delete target count changed")
    if data.get("export_denylist_violation_refs") != [] or data.get("export_denylist_violation_ref_count") != 0:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 export denylist violations must be empty")
    blockers = list(data.get("local_only_preflight_blocker_refs") or [])
    ready = not blockers
    if data.get("local_only_preflight_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 blocker count changed")
    if data.get("local_only_preflight_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 ready flag changed")
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP04_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_STATUS_REF
    if data.get("local_only_preflight_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 status changed")
    if ready:
        for key in (
            "op03_review_session_envelope_ready",
            "op03_actual_source_guard_ready",
            "local_review_root_ref_present",
            "explicit_allow_ref_present",
            "retention_policy_ref_present",
            "disposal_policy_ref_present",
            "export_denylist_policy_ref_present",
            "body_full_packet_generation_allowed_for_local_review_only",
            "body_full_packet_generation_allowed_by_preflight",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP04 ready dependency changed: {key}")
        if data.get("op03_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 OP03 next step changed")
        if data.get("op03_review_session_state_ref") != P7_R54_AHR_POST_MN11_REVIEW_SESSION_STATE_NOT_STARTED_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 review session state must stay NOT_STARTED")
        if data.get("local_review_root_ref") != P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_REVIEW_ROOT_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 local root ref changed")
        if data.get("explicit_allow_ref") != P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 explicit allow ref changed")
        if data.get("explicit_allow_scope_ref") != P7_R54_AHR_POST_MN11_PMN_OP04_ALLOW_SCOPE_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 allow scope changed")
        if data.get("retention_policy_ref") != P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 retention policy changed")
        if data.get("disposal_policy_ref") != P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 disposal policy changed")
        if data.get("export_denylist_policy_ref") != P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 export denylist policy changed")
        if tuple(data.get("local_only_preflight_reason_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP04_READY_REASON_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 blocked material must carry blockers")
        if data.get("body_full_packet_generation_allowed_for_local_review_only") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 blocked material must not allow body-full generation")
        if data.get("body_full_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 blocked material must not allow generation by preflight")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 blocked material must not advance implemented steps")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP03_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP04 blocked next step changed")
    return True


def _pmn_op05_blockers(op04: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op04, Mapping):
        return ["pmn_op05_local_only_preflight_explicit_allow_boundary_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(op04)
    except ValueError:
        blockers.append("pmn_op05_op04_local_only_preflight_explicit_allow_boundary_invalid")
    if op04.get("local_only_preflight_ready") is not True:
        blockers.append("pmn_op05_op04_local_only_preflight_not_ready")
    if op04.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF:
        blockers.append("pmn_op05_op04_next_step_not_manifest_refreeze")
    if op04.get("body_full_generation_blocked_until_manifest_refreeze") is not True:
        blockers.append("pmn_op05_op04_body_full_generation_not_blocked_until_manifest")
    if op04.get("body_full_packet_generation_allowed_by_preflight") is not True:
        blockers.append("pmn_op05_op04_body_full_generation_not_allowed_by_preflight")
    if _scan_forbidden_payload_key_paths(op04):
        blockers.append("pmn_op05_op04_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
    *,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP05 body-free 24-case manifest refreeze material."""

    session_id = _safe_review_session_id(review_session_id)
    op04 = local_only_preflight_explicit_allow_boundary
    if op04 is None:
        op04 = build_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary(
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op05_blockers(op04)
    preflight_ready = not blockers
    source_rows: list[dict[str, Any]] = []
    if preflight_ready:
        case_matrix = op.build_p7_r48_p5_first_formal_review_case_matrix(
            material_id="p7_r54_ahr_post_mn11_pmn_op05_r48_first_formal_case_matrix_basis"
        )
        op.assert_p7_r48_p5_first_formal_review_case_matrix_contract(case_matrix)
        source_rows = [dict(row) for row in (case_matrix.get("case_rows") or [])]

    family_counts = _count_by(source_rows, "family") if source_rows else {}
    case_ref_ids = _case_ref_values(source_rows, "case_ref_id") if source_rows else []
    blind_case_ids = _case_ref_values(source_rows, "blind_case_id") if source_rows else []
    packet_ref_ids = _case_ref_values(source_rows, "packet_ref_id") if source_rows else []
    distribution_matches = bool(source_rows and family_counts == P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION)
    manifest_ready = bool(
        preflight_ready
        and len(source_rows) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT
        and distribution_matches
        and _unique_non_empty(case_ref_ids)
        and _unique_non_empty(blind_case_ids)
        and _unique_non_empty(packet_ref_ids)
    )
    if preflight_ready and not manifest_ready:
        blockers.append("pmn_op05_24_case_manifest_distribution_or_unique_ref_mismatch")
    case_manifest_rows = _pmn_op05_case_manifest_rows(source_rows) if manifest_ready else []
    controller_rows = _pmn_op05_controller_manifest_rows(source_rows) if manifest_ready else []
    reviewer_rows = _pmn_op05_reviewer_facing_rows(source_rows) if manifest_ready else []
    reason_refs = list(P7_R54_AHR_POST_MN11_PMN_OP05_READY_REASON_REFS) if manifest_ready else blockers
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP05_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": _clean_ref(op04.get("schema_version") if isinstance(op04, Mapping) else "", default="op04_schema_missing", max_length=220),
        "op04_material_ref": _clean_ref(op04.get("material_id") if isinstance(op04, Mapping) else "", default="op04_material_missing", max_length=220),
        "op04_next_required_step": _clean_ref(op04.get("next_required_step") if isinstance(op04, Mapping) else "", default="op04_next_required_step_missing", max_length=220),
        "op04_local_only_preflight_status_ref": _clean_ref(op04.get("local_only_preflight_status_ref") if isinstance(op04, Mapping) else "", default="op04_preflight_status_missing", max_length=220),
        "op04_local_only_preflight_ready": bool(isinstance(op04, Mapping) and op04.get("local_only_preflight_ready") is True),
        "op04_body_full_generation_blocked_until_manifest_refreeze": bool(isinstance(op04, Mapping) and op04.get("body_full_generation_blocked_until_manifest_refreeze") is True),
        "op04_body_full_packet_generation_allowed_by_preflight": bool(isinstance(op04, Mapping) and op04.get("body_full_packet_generation_allowed_by_preflight") is True),
        "manifest_status_ref": (
            P7_R54_AHR_POST_MN11_PMN_OP05_READY_STATUS_REF
            if manifest_ready
            else P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_STATUS_REF
        ),
        "manifest_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP05_ALLOWED_STATUS_REFS),
        "manifest_ready": manifest_ready,
        "manifest_blocker_refs": blockers,
        "manifest_blocker_ref_count": len(blockers),
        "manifest_reason_refs": reason_refs,
        "manifest_reason_ref_count": len(reason_refs),
        "required_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "total_case_count": len(source_rows) if manifest_ready else 0,
        "case_ref_id_count": len(case_ref_ids) if manifest_ready else 0,
        "blind_case_id_count": len(blind_case_ids) if manifest_ready else 0,
        "packet_ref_id_count": len(packet_ref_ids) if manifest_ready else 0,
        "selection_row_count_required": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count_required": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "rating_row_count_required": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "question_need_observation_row_count_required": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "case_distribution": dict(P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION.values()),
        "case_distribution_matches_design": distribution_matches if manifest_ready else False,
        "family_case_counts": family_counts if manifest_ready else {},
        "boundary_case_count": (family_counts.get("low_information_history_not_eligible", 0) + family_counts.get("free_tier_history_present_not_allowed", 0)) if manifest_ready else 0,
        "low_information_boundary_case_count": family_counts.get("low_information_history_not_eligible", 0) if manifest_ready else 0,
        "free_tier_boundary_case_count": family_counts.get("free_tier_history_present_not_allowed", 0) if manifest_ready else 0,
        "case_ref_ids_unique": _unique_non_empty(case_ref_ids) if manifest_ready else False,
        "blind_case_ids_unique": _unique_non_empty(blind_case_ids) if manifest_ready else False,
        "packet_ref_ids_unique": _unique_non_empty(packet_ref_ids) if manifest_ready else False,
        "blind_case_id_case_ref_separated": set(blind_case_ids).isdisjoint(set(case_ref_ids)) if manifest_ready else False,
        "blind_case_id_packet_ref_separated": set(blind_case_ids).isdisjoint(set(packet_ref_ids)) if manifest_ready else False,
        "case_ref_id_packet_ref_separated": set(case_ref_ids).isdisjoint(set(packet_ref_ids)) if manifest_ready else False,
        "case_manifest_rows": case_manifest_rows,
        "case_manifest_row_count": len(case_manifest_rows),
        "controller_manifest_rows": controller_rows,
        "controller_manifest_row_count": len(controller_rows),
        "reviewer_facing_case_index_rows": reviewer_rows,
        "reviewer_facing_row_count": len(reviewer_rows),
        "reviewer_identifier_policy_ref": P7_R54_AHR_POST_MN11_PMN_OP05_REVIEWER_IDENTIFIER_POLICY_REF,
        "controller_keeps_family_tier_expected_refs": manifest_ready,
        "reviewer_receives_blind_case_id_only": manifest_ready,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_case_ref_exposed": False,
        "reviewer_facing_packet_ref_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "reviewer_facing_hidden_metadata_exposed": False,
        "p4_r11_rows_confused_as_r54_review_rows": False,
        "p4_r11_rows_mixed_in": False,
        "p4_r11_rows_mixed_in_count": 0,
        "body_full_packet_generation_request_allowed_next": manifest_ready,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "body_full_generation_blocked_until_pmn_op06_request_step": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "actual_human_review_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "pmn_op05_does_not_generate_body_full_packet": True,
        "pmn_op05_does_not_run_actual_human_review": True,
        "pmn_op05_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "pmn_op05_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP05_IMPLEMENTED_STEPS
            if manifest_ready
            else P7_R54_AHR_POST_MN11_PMN_OP04_IMPLEMENTED_STEPS
            if preflight_ready
            else P7_R54_AHR_POST_MN11_PMN_OP03_IMPLEMENTED_STEPS
        ),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_POST_MN11_PMN_OP05_NOT_YET_IMPLEMENTED_STEPS
            if manifest_ready
            else P7_R54_AHR_POST_MN11_PMN_OP04_NOT_YET_IMPLEMENTED_STEPS
            if preflight_ready
            else P7_R54_AHR_POST_MN11_PMN_OP03_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": (
            P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF
            if manifest_ready
            else P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF
        ),
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_MN11_PMN_OP05_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostMN11-PMN-OP05 24-case manifest refreeze",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP05_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP05 24-case manifest refreeze",
    )
    if data.get("op04_schema_version") != P7_R54_AHR_POST_MN11_PMN_OP04_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_BOUNDARY_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 OP04 schema version changed")
    if tuple(data.get("manifest_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 status refs changed")
    if data.get("required_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 required case count changed")
    if data.get("case_distribution") != P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 case distribution changed")
    if data.get("case_distribution_total_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 distribution total must be 24")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 actual review basis allowed changed")
    for key in (
        "body_full_generation_blocked_until_pmn_op06_request_step",
        "current_actual_review_basis_remains_264_85_258_171",
        "actual_human_review_still_not_run",
        "actual_review_evidence_complete_from_real_review_still_false",
        "pmn_op05_does_not_generate_body_full_packet",
        "pmn_op05_does_not_run_actual_human_review",
        "pmn_op05_does_not_create_operation_receipt_or_rows_or_disposal",
        "pmn_op05_does_not_start_p8_p6_r52_or_release",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP05 required true field changed: {key}")
    for key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "reviewer_facing_hidden_metadata_exposed",
        "p4_r11_rows_confused_as_r54_review_rows",
        "p4_r11_rows_mixed_in",
        "body_full_packet_generated_here",
        "body_full_packet_materialized_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP05 required false field promoted: {key}")
    if data.get("p4_r11_rows_mixed_in_count") != 0:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 P4-R11 mixed count must stay zero")
    blockers = list(data.get("manifest_blocker_refs") or [])
    manifest_ready = not blockers
    if data.get("manifest_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 blocker count changed")
    if data.get("manifest_ready") is not manifest_ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 ready flag changed")
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP05_READY_STATUS_REF if manifest_ready else P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_STATUS_REF
    if data.get("manifest_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 status changed")
    rows = [row for row in (data.get("case_manifest_rows") or []) if isinstance(row, Mapping)]
    controller_rows = [row for row in (data.get("controller_manifest_rows") or []) if isinstance(row, Mapping)]
    reviewer_rows = [row for row in (data.get("reviewer_facing_case_index_rows") or []) if isinstance(row, Mapping)]
    if manifest_ready:
        if data.get("op04_local_only_preflight_ready") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 ready manifest requires OP04 ready")
        if data.get("op04_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 OP04 next step changed")
        if data.get("op04_body_full_generation_blocked_until_manifest_refreeze") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 OP04 must block generation until manifest")
        if data.get("case_distribution_matches_design") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 distribution must match design")
        for count_key in (
            "total_case_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
            "selection_row_count_required",
            "sanitized_review_result_row_count_required",
            "rating_row_count_required",
            "question_need_observation_row_count_required",
            "case_manifest_row_count",
            "controller_manifest_row_count",
            "reviewer_facing_row_count",
        ):
            if data.get(count_key) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP05 {count_key} must be 24")
        if data.get("family_case_counts") != P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 family counts changed")
        if data.get("boundary_case_count") != 4 or data.get("low_information_boundary_case_count") != 2 or data.get("free_tier_boundary_case_count") != 2:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 boundary counts changed")
        for key in (
            "case_ref_ids_unique",
            "blind_case_ids_unique",
            "packet_ref_ids_unique",
            "blind_case_id_case_ref_separated",
            "blind_case_id_packet_ref_separated",
            "case_ref_id_packet_ref_separated",
            "controller_keeps_family_tier_expected_refs",
            "reviewer_receives_blind_case_id_only",
            "body_full_packet_generation_request_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP05 ready field changed: {key}")
        for row in rows:
            _assert_pmn_op05_bodyfree_row(row, source="postmn11_pmn_op05_case_manifest_rows")
        for row in controller_rows:
            _assert_pmn_op05_bodyfree_row(row, source="postmn11_pmn_op05_controller_manifest_rows")
        for row in reviewer_rows:
            _assert_pmn_op05_bodyfree_row(row, source="postmn11_pmn_op05_reviewer_facing_rows")
        if tuple(data.get("manifest_reason_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP05_READY_REASON_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 ready reasons changed")
        if data.get("reviewer_identifier_policy_ref") != P7_R54_AHR_POST_MN11_PMN_OP05_REVIEWER_IDENTIFIER_POLICY_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 reviewer identifier policy changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 next step changed")
    else:
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 blocked manifest must not allow packet request")
        if rows or controller_rows or reviewer_rows:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 blocked manifest must not freeze rows")
        for count_key in (
            "total_case_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
            "case_manifest_row_count",
            "controller_manifest_row_count",
            "reviewer_facing_row_count",
        ):
            if data.get(count_key) != 0:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP05 blocked {count_key} must be zero")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 blocked material must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP05 blocked next step changed")
    return True




def _pmn_op06_blockers(op05: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op05, Mapping):
        return ["pmn_op06_24_case_manifest_refreeze_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(op05)
    except ValueError:
        blockers.append("pmn_op06_op05_24_case_manifest_refreeze_invalid")
    if op05.get("manifest_ready") is not True:
        blockers.append("pmn_op06_op05_manifest_not_ready")
    if op05.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF:
        blockers.append("pmn_op06_op05_next_step_not_packet_generation_request")
    if op05.get("body_full_packet_generation_request_allowed_next") is not True:
        blockers.append("pmn_op06_op05_packet_generation_request_not_allowed_next")
    for count_field in ("total_case_count", "case_ref_id_count", "blind_case_id_count", "packet_ref_id_count"):
        if op05.get(count_field) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append(f"pmn_op06_op05_{count_field}_not_24")
    if op05.get("actual_human_review_still_not_run") is not True:
        blockers.append("pmn_op06_op05_actual_human_review_already_claimed")
    if _scan_forbidden_payload_key_paths(op05):
        blockers.append("pmn_op06_op05_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder(
    *,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP06 body-free packet-generation request material without running generation."""

    session_id = _safe_review_session_id(review_session_id)
    op05 = case_manifest_refreeze
    if op05 is None:
        op05 = build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op06_blockers(op05)
    ready = not blockers
    payload = {
        "packet_generation_request_ref": P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF,
        "review_session_id": session_id,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "required_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "case_manifest_ref": P7_R54_AHR_POST_MN11_PMN_OP06_CASE_MANIFEST_REF,
        "explicit_allow_ref": P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF,
        "local_only_required": True,
        "must_not_export": True,
        "packet_completeness_scan_required": True,
        "export_denylist_scan_required": True,
        "purge_required": True,
        "body_free": True,
    } if ready else {}
    forbidden_paths = _scan_forbidden_payload_key_paths(payload)
    reason_refs = list(P7_R54_AHR_POST_MN11_PMN_OP06_READY_REASON_REFS) if ready else blockers
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_BUILDER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": _clean_ref(op05.get("schema_version") if isinstance(op05, Mapping) else "", default="op05_schema_missing", max_length=220),
        "op05_material_ref": _clean_ref(op05.get("material_id") if isinstance(op05, Mapping) else "", default="op05_material_missing", max_length=220),
        "op05_next_required_step": _clean_ref(op05.get("next_required_step") if isinstance(op05, Mapping) else "", default="op05_next_required_step_missing", max_length=220),
        "op05_manifest_ready": bool(isinstance(op05, Mapping) and op05.get("manifest_ready") is True),
        "op05_body_full_packet_generation_request_allowed_next": bool(isinstance(op05, Mapping) and op05.get("body_full_packet_generation_request_allowed_next") is True),
        "packet_generation_request_status_ref": P7_R54_AHR_POST_MN11_PMN_OP06_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_STATUS_REF,
        "packet_generation_request_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP06_ALLOWED_STATUS_REFS),
        "packet_generation_request_ready": ready,
        "packet_generation_request_blocker_refs": blockers,
        "packet_generation_request_blocker_ref_count": len(blockers),
        "packet_generation_request_reason_refs": reason_refs,
        "packet_generation_request_reason_ref_count": len(reason_refs),
        "packet_generation_request_ref": P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF if ready else "",
        "packet_generation_request_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_REQUEST_FIELD_REFS),
        "packet_generation_request_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_REQUEST_FIELD_REFS),
        "packet_generation_request_bodyfree_payload": payload,
        "packet_generation_request_bodyfree_payload_field_count": len(payload),
        "packet_generation_request_contains_forbidden_payload_key": bool(forbidden_paths),
        "packet_generation_request_forbidden_payload_key_paths": forbidden_paths,
        "packet_generation_request_forbidden_payload_key_path_count": len(forbidden_paths),
        "case_manifest_ref": P7_R54_AHR_POST_MN11_PMN_OP06_CASE_MANIFEST_REF if ready else "",
        "case_manifest_ready": ready,
        "case_manifest_row_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else 0,
        "case_ref_id_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else 0,
        "blind_case_id_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else 0,
        "packet_ref_id_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else 0,
        "explicit_allow_ref": P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF if ready else "",
        "explicit_allow_ref_matches_op04": ready,
        "local_operation_ref": P7_R54_AHR_POST_MN11_PMN_OP06_LOCAL_OPERATION_REF if ready else "",
        "local_only_required": ready,
        "must_not_export": ready,
        "packet_completeness_scan_required": ready,
        "export_denylist_scan_required": ready,
        "purge_required": ready,
        "retention_policy_ref": P7_R54_AHR_POST_MN11_PMN_OP04_RETENTION_POLICY_REF if ready else "",
        "disposal_policy_ref": P7_R54_AHR_POST_MN11_PMN_OP04_DISPOSAL_POLICY_REF if ready else "",
        "export_denylist_policy_ref": P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF if ready else "",
        "body_full_packet_generation_allowed_for_local_review_only": ready,
        "body_full_packet_generation_request_built_here": ready,
        "body_full_packet_generation_request_bodyfree_only": True,
        "body_full_packet_generation_request_allowed_next": False,
        "packet_generation_local_operation_receipt_required_next": ready,
        "body_full_packet_generation_executed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_exported_to_artifact": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "actual_human_review_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op06_does_not_generate_body_full_packet": True,
        "pmn_op06_does_not_run_actual_human_review": True,
        "pmn_op06_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "pmn_op06_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP06_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP06_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP06 packet generation request body-free builder")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_BUILDER_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP06 packet generation request body-free builder")
    blockers = list(data.get("packet_generation_request_blocker_refs") or [])
    ready = not blockers
    if data.get("packet_generation_request_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 ready flag changed")
    if data.get("packet_generation_request_status_ref") != (P7_R54_AHR_POST_MN11_PMN_OP06_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 status changed")
    if tuple(data.get("packet_generation_request_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 status refs changed")
    for key in ("body_full_packet_generation_request_bodyfree_only", "actual_human_review_still_not_run", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171", "pmn_op06_does_not_generate_body_full_packet", "pmn_op06_does_not_run_actual_human_review", "pmn_op06_does_not_create_operation_receipt_or_rows_or_disposal", "pmn_op06_does_not_start_p8_p6_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP06 required true field changed: {key}")
    for key in ("body_full_packet_generation_request_allowed_next", "body_full_packet_generation_executed_here", "body_full_packet_generated_here", "body_full_packet_materialized_here", "body_full_packet_export_allowed", "body_full_packet_exported_to_artifact", "local_absolute_path_included", "body_hash_stored", "terminal_output_body_included", "packet_generation_request_contains_forbidden_payload_key"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP06 required false field promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 actual review basis changed")
    if data.get("packet_generation_request_required_field_ref_count") != len(data.get("packet_generation_request_required_field_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 required request field count changed")
    if tuple(data.get("packet_generation_request_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP06_REQUIRED_REQUEST_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 required request fields changed")
    payload = data.get("packet_generation_request_bodyfree_payload") or {}
    if data.get("packet_generation_request_bodyfree_payload_field_count") != len(payload):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 payload field count changed")
    if data.get("packet_generation_request_forbidden_payload_key_path_count") != len(data.get("packet_generation_request_forbidden_payload_key_paths") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 forbidden path count changed")
    if ready:
        if data.get("op05_manifest_ready") is not True or data.get("op05_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 ready request requires OP05 ready next step")
        for count_key in ("case_manifest_row_count", "case_ref_id_count", "blind_case_id_count", "packet_ref_id_count"):
            if data.get(count_key) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP06 {count_key} must be 24")
        for key in ("case_manifest_ready", "explicit_allow_ref_matches_op04", "local_only_required", "must_not_export", "packet_completeness_scan_required", "export_denylist_scan_required", "purge_required", "body_full_packet_generation_allowed_for_local_review_only", "body_full_packet_generation_request_built_here", "packet_generation_local_operation_receipt_required_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP06 ready field changed: {key}")
        if payload != {"packet_generation_request_ref": P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF, "review_session_id": data.get("review_session_id"), "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF, "required_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT, "case_manifest_ref": P7_R54_AHR_POST_MN11_PMN_OP06_CASE_MANIFEST_REF, "explicit_allow_ref": P7_R54_AHR_POST_MN11_PMN_OP04_EXPLICIT_ALLOW_REF, "local_only_required": True, "must_not_export": True, "packet_completeness_scan_required": True, "export_denylist_scan_required": True, "purge_required": True, "body_free": True}:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 request payload changed")
        if tuple(data.get("packet_generation_request_reason_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP06_READY_REASON_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP06_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 next step changed")
    else:
        if payload or data.get("body_full_packet_generation_request_built_here") is not False or data.get("packet_generation_local_operation_receipt_required_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 blocked material promoted request")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP06 blocked next step changed")
    return True


def _pmn_op07_blockers(op06: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op06, Mapping):
        return ["pmn_op07_packet_generation_request_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(op06)
    except ValueError:
        blockers.append("pmn_op07_op06_packet_generation_request_invalid")
    if op06.get("packet_generation_request_ready") is not True:
        blockers.append("pmn_op07_op06_packet_generation_request_not_ready")
    if op06.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF:
        blockers.append("pmn_op07_op06_next_step_not_packet_generation_receipt_boundary")
    if op06.get("packet_generation_local_operation_receipt_required_next") is not True:
        blockers.append("pmn_op07_op06_receipt_boundary_not_required_next")
    if op06.get("body_full_packet_generation_executed_here") is not False:
        blockers.append("pmn_op07_op06_body_full_generation_already_executed")
    if _scan_forbidden_payload_key_paths(op06):
        blockers.append("pmn_op07_op06_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary(
    *,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP07 body-free packet generation local operation receipt boundary."""

    session_id = _safe_review_session_id(review_session_id)
    op06 = packet_generation_request_bodyfree_builder
    if op06 is None:
        op06 = build_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder(
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op07_blockers(op06)
    ready = not blockers
    future_receipt_required_fields = ("packet_generation_receipt_ref", "review_session_id", "packet_generation_request_ref", "actual_review_basis_ref", "actual_source_ref", "packet_materialized_local_only", "packet_count", "packet_ref_id_count", "body_full_exported", "local_absolute_path_included", "body_hash_stored", "terminal_output_body_included", "body_free")
    reason_refs = list(P7_R54_AHR_POST_MN11_PMN_OP07_READY_REASON_REFS) if ready else blockers
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_LOCAL_OPERATION_RECEIPT_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": _clean_ref(op06.get("schema_version") if isinstance(op06, Mapping) else "", default="op06_schema_missing", max_length=220),
        "op06_material_ref": _clean_ref(op06.get("material_id") if isinstance(op06, Mapping) else "", default="op06_material_missing", max_length=220),
        "op06_next_required_step": _clean_ref(op06.get("next_required_step") if isinstance(op06, Mapping) else "", default="op06_next_required_step_missing", max_length=220),
        "op06_packet_generation_request_ready": bool(isinstance(op06, Mapping) and op06.get("packet_generation_request_ready") is True),
        "op06_packet_generation_request_ref": _clean_ref(op06.get("packet_generation_request_ref") if isinstance(op06, Mapping) else "", default="op06_packet_generation_request_ref_missing", max_length=220),
        "packet_generation_receipt_boundary_status_ref": P7_R54_AHR_POST_MN11_PMN_OP07_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_STATUS_REF,
        "packet_generation_receipt_boundary_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP07_ALLOWED_STATUS_REFS),
        "packet_generation_receipt_boundary_ready": ready,
        "packet_generation_receipt_boundary_blocker_refs": blockers,
        "packet_generation_receipt_boundary_blocker_ref_count": len(blockers),
        "packet_generation_receipt_boundary_reason_refs": reason_refs,
        "packet_generation_receipt_boundary_reason_ref_count": len(reason_refs),
        "packet_generation_receipt_boundary_ref": P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_RECEIPT_BOUNDARY_REF if ready else "",
        "expected_packet_generation_receipt_ref": P7_R54_AHR_POST_MN11_PMN_OP07_EXPECTED_PACKET_GENERATION_RECEIPT_REF if ready else "",
        "packet_generation_receipt_required_after_external_local_generation": ready,
        "packet_generation_receipt_received_here": False,
        "packet_generation_receipt_intaked_here": False,
        "packet_generation_receipt_actual_source_ref_required": ready,
        "packet_generation_receipt_expected_actual_source_ref": P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF if ready else "",
        "packet_generation_local_operation_receipt_boundary_defined_here": ready,
        "packet_generation_local_operation_receipt_bodyfree_only": True,
        "future_packet_generation_receipt_required_field_refs": list(future_receipt_required_fields),
        "future_packet_generation_receipt_required_field_ref_count": len(future_receipt_required_fields),
        "expected_packet_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "packet_count": 0,
        "packet_ref_id_count": 0,
        "packet_materialized_local_only": False,
        "packet_materialized_local_only_claimed_here": False,
        "packet_completeness_scan_required_next": ready,
        "export_denylist_scan_required_next": ready,
        "body_full_packet_generation_executed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "body_full_packet_exported_to_artifact": False,
        "body_full_packet_export_allowed": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "packet_content_included": False,
        "actual_human_review_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op07_does_not_generate_body_full_packet": True,
        "pmn_op07_does_not_run_actual_human_review": True,
        "pmn_op07_does_not_create_actual_operation_receipt_or_rows_or_disposal": True,
        "pmn_op07_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP07_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP07_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP07 packet generation local operation receipt boundary")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_LOCAL_OPERATION_RECEIPT_BOUNDARY_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP07 packet generation local operation receipt boundary")
    blockers = list(data.get("packet_generation_receipt_boundary_blocker_refs") or [])
    ready = not blockers
    if data.get("packet_generation_receipt_boundary_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 ready flag changed")
    if data.get("packet_generation_receipt_boundary_status_ref") != (P7_R54_AHR_POST_MN11_PMN_OP07_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 status changed")
    if tuple(data.get("packet_generation_receipt_boundary_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 status refs changed")
    for key in ("packet_generation_local_operation_receipt_bodyfree_only", "actual_human_review_still_not_run", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171", "pmn_op07_does_not_generate_body_full_packet", "pmn_op07_does_not_run_actual_human_review", "pmn_op07_does_not_create_actual_operation_receipt_or_rows_or_disposal", "pmn_op07_does_not_start_p8_p6_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP07 required true field changed: {key}")
    for key in ("packet_generation_receipt_received_here", "packet_generation_receipt_intaked_here", "packet_materialized_local_only", "packet_materialized_local_only_claimed_here", "body_full_packet_generation_executed_here", "body_full_packet_generated_here", "body_full_packet_materialized_here", "body_full_packet_exported_to_artifact", "body_full_packet_export_allowed", "local_absolute_path_included", "body_hash_stored", "terminal_output_body_included", "packet_content_included"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP07 required false field promoted: {key}")
    if data.get("expected_packet_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 expected packet count changed")
    if data.get("future_packet_generation_receipt_required_field_ref_count") != len(data.get("future_packet_generation_receipt_required_field_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 required receipt field count changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 actual review basis changed")
    if ready:
        if data.get("op06_packet_generation_request_ready") is not True or data.get("op06_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 ready boundary requires OP06 ready next step")
        if data.get("op06_packet_generation_request_ref") != P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 OP06 request ref changed")
        if data.get("packet_generation_receipt_boundary_ref") != P7_R54_AHR_POST_MN11_PMN_OP07_PACKET_GENERATION_RECEIPT_BOUNDARY_REF or data.get("expected_packet_generation_receipt_ref") != P7_R54_AHR_POST_MN11_PMN_OP07_EXPECTED_PACKET_GENERATION_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 receipt refs changed")
        if data.get("packet_generation_receipt_expected_actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 expected actual source ref changed")
        for key in ("packet_generation_receipt_required_after_external_local_generation", "packet_generation_receipt_actual_source_ref_required", "packet_generation_local_operation_receipt_boundary_defined_here", "packet_completeness_scan_required_next", "export_denylist_scan_required_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP07 ready field changed: {key}")
        if data.get("packet_count") != 0 or data.get("packet_ref_id_count") != 0:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 must not claim packet counts before actual generation")
        if tuple(data.get("packet_generation_receipt_boundary_reason_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP07_READY_REASON_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP07_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 next step changed")
    else:
        if data.get("packet_generation_local_operation_receipt_boundary_defined_here") is not False or data.get("packet_completeness_scan_required_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 blocked material promoted boundary")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP07 blocked next step changed")
    return True




def _packet_receipt_ref_ids(packet_generation_receipt_bodyfree: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(packet_generation_receipt_bodyfree, Mapping):
        return []
    refs = packet_generation_receipt_bodyfree.get("packet_ref_ids")
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes, bytearray)):
        return []
    return [_clean_ref(ref, default="missing_packet_ref", max_length=180) for ref in refs]


def _pmn_op08_blockers(
    op07: Mapping[str, Any] | None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None,
    *,
    export_denylist_violation_refs: Sequence[Any] | None = None,
    body_full_packet_export_candidate_refs: Sequence[Any] | None = None,
    body_full_packet_content_detected_in_export: bool = False,
    question_text_detected_in_export: bool = False,
    draft_question_text_detected_in_export: bool = False,
    local_path_detected_in_export: bool = False,
    body_hash_detected_in_export: bool = False,
    terminal_output_body_detected_in_export: bool = False,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op07, Mapping):
        return ["pmn_op08_packet_generation_receipt_boundary_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(op07)
    except ValueError:
        blockers.append("pmn_op08_op07_packet_generation_receipt_boundary_invalid")
    if op07.get("packet_generation_receipt_boundary_ready") is not True:
        blockers.append("pmn_op08_op07_packet_generation_receipt_boundary_not_ready")
    if op07.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF:
        blockers.append("pmn_op08_op07_next_step_not_packet_scan")
    if op07.get("packet_generation_receipt_required_after_external_local_generation") is not True:
        blockers.append("pmn_op08_op07_packet_generation_receipt_not_required_next")
    if op07.get("packet_generation_receipt_expected_actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF:
        blockers.append("pmn_op08_op07_expected_actual_source_ref_mismatch")
    if _scan_forbidden_payload_key_paths(op07):
        blockers.append("pmn_op08_op07_forbidden_body_question_path_hash_key_detected")

    if not isinstance(packet_generation_receipt_bodyfree, Mapping):
        blockers.append("pmn_op08_actual_local_packet_generation_receipt_not_received")
        return list(dict.fromkeys(blockers))

    forbidden_paths = _scan_forbidden_payload_key_paths(packet_generation_receipt_bodyfree)
    if forbidden_paths:
        blockers.append("pmn_op08_packet_generation_receipt_forbidden_body_question_path_hash_key_detected")
    if packet_generation_receipt_bodyfree.get("body_free") is not True:
        blockers.append("pmn_op08_packet_generation_receipt_not_bodyfree")
    if packet_generation_receipt_bodyfree.get("actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF:
        blockers.append("pmn_op08_packet_generation_receipt_actual_source_ref_not_allowed")
    if packet_generation_receipt_bodyfree.get("review_session_id") != op07.get("review_session_id"):
        blockers.append("pmn_op08_packet_generation_receipt_review_session_id_mismatch")
    if packet_generation_receipt_bodyfree.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("pmn_op08_packet_generation_receipt_actual_review_basis_ref_mismatch")
    if packet_generation_receipt_bodyfree.get("packet_generation_request_ref") != P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF:
        blockers.append("pmn_op08_packet_generation_receipt_request_ref_mismatch")
    if packet_generation_receipt_bodyfree.get("packet_materialized_local_only") is not True:
        blockers.append("pmn_op08_packet_generation_receipt_does_not_confirm_local_only_materialization")
    if packet_generation_receipt_bodyfree.get("packet_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op08_packet_generation_receipt_packet_count_not_24")
    if packet_generation_receipt_bodyfree.get("packet_ref_id_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op08_packet_generation_receipt_packet_ref_id_count_not_24")
    packet_refs = _packet_receipt_ref_ids(packet_generation_receipt_bodyfree)
    if not _unique_non_empty(packet_refs) or len(packet_refs) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op08_packet_generation_receipt_packet_ref_ids_not_24_unique")
    for false_key in (
        "body_full_exported",
        "body_full_packet_exported_to_artifact",
        "local_absolute_path_included",
        "body_hash_stored",
        "terminal_output_body_included",
        "packet_content_included",
        "question_text_included",
        "draft_question_text_included",
    ):
        if packet_generation_receipt_bodyfree.get(false_key) is not False:
            blockers.append(f"pmn_op08_packet_generation_receipt_{false_key}_not_false")
    if export_denylist_violation_refs:
        blockers.append("pmn_op08_export_denylist_violation_detected")
    if body_full_packet_export_candidate_refs:
        blockers.append("pmn_op08_body_full_packet_export_candidate_detected")
    if body_full_packet_content_detected_in_export:
        blockers.append("pmn_op08_body_full_packet_content_detected_in_export")
    if question_text_detected_in_export:
        blockers.append("pmn_op08_question_text_detected_in_export")
    if draft_question_text_detected_in_export:
        blockers.append("pmn_op08_draft_question_text_detected_in_export")
    if local_path_detected_in_export:
        blockers.append("pmn_op08_local_path_detected_in_export")
    if body_hash_detected_in_export:
        blockers.append("pmn_op08_body_hash_detected_in_export")
    if terminal_output_body_detected_in_export:
        blockers.append("pmn_op08_terminal_output_body_detected_in_export")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
    *,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    export_denylist_violation_refs: Sequence[Any] | None = None,
    body_full_packet_export_candidate_refs: Sequence[Any] | None = None,
    body_full_packet_content_detected_in_export: bool = False,
    question_text_detected_in_export: bool = False,
    draft_question_text_detected_in_export: bool = False,
    local_path_detected_in_export: bool = False,
    body_hash_detected_in_export: bool = False,
    terminal_output_body_detected_in_export: bool = False,
) -> dict[str, Any]:
    """Build PMN-OP08 body-free packet completeness / export denylist scan material."""

    session_id = _safe_review_session_id(review_session_id)
    op07 = packet_generation_local_operation_receipt_boundary
    if op07 is None:
        op07 = build_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary(
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )

    deny_refs = [_clean_ref(ref, default="export_denylist_violation_ref", max_length=220) for ref in (export_denylist_violation_refs or [])]
    export_candidate_refs = [_clean_ref(ref, default="body_full_packet_export_candidate_ref", max_length=220) for ref in (body_full_packet_export_candidate_refs or [])]
    blockers = _pmn_op08_blockers(
        op07,
        packet_generation_receipt_bodyfree,
        export_denylist_violation_refs=deny_refs,
        body_full_packet_export_candidate_refs=export_candidate_refs,
        body_full_packet_content_detected_in_export=body_full_packet_content_detected_in_export,
        question_text_detected_in_export=question_text_detected_in_export,
        draft_question_text_detected_in_export=draft_question_text_detected_in_export,
        local_path_detected_in_export=local_path_detected_in_export,
        body_hash_detected_in_export=body_hash_detected_in_export,
        terminal_output_body_detected_in_export=terminal_output_body_detected_in_export,
    )
    receipt_received = isinstance(packet_generation_receipt_bodyfree, Mapping)
    receipt_refs = _packet_receipt_ref_ids(packet_generation_receipt_bodyfree)
    packet_count = int(packet_generation_receipt_bodyfree.get("packet_count") or 0) if receipt_received else 0
    packet_ref_id_count = int(packet_generation_receipt_bodyfree.get("packet_ref_id_count") or 0) if receipt_received else 0
    leak_detected = bool(
        deny_refs
        or export_candidate_refs
        or body_full_packet_content_detected_in_export
        or question_text_detected_in_export
        or draft_question_text_detected_in_export
        or local_path_detected_in_export
        or body_hash_detected_in_export
        or terminal_output_body_detected_in_export
        or (receipt_received and packet_generation_receipt_bodyfree.get("body_full_exported") is not False)
        or (receipt_received and packet_generation_receipt_bodyfree.get("body_full_packet_exported_to_artifact") is not False)
        or (receipt_received and packet_generation_receipt_bodyfree.get("local_absolute_path_included") is not False)
        or (receipt_received and packet_generation_receipt_bodyfree.get("body_hash_stored") is not False)
        or (receipt_received and packet_generation_receipt_bodyfree.get("terminal_output_body_included") is not False)
        or (receipt_received and packet_generation_receipt_bodyfree.get("packet_content_included") is not False)
        or (receipt_received and packet_generation_receipt_bodyfree.get("question_text_included") is not False)
        or (receipt_received and packet_generation_receipt_bodyfree.get("draft_question_text_included") is not False)
    )
    ready = not blockers
    status_ref = (
        P7_R54_AHR_POST_MN11_PMN_OP08_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_BY_LEAK_STATUS_REF
        if leak_detected
        else P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_STATUS_REF
    )
    reason_refs = list(P7_R54_AHR_POST_MN11_PMN_OP08_READY_REASON_REFS) if ready else blockers
    implemented_steps = (
        P7_R54_AHR_POST_MN11_PMN_OP08_IMPLEMENTED_STEPS
        if ready
        else P7_R54_AHR_POST_MN11_PMN_OP07_IMPLEMENTED_STEPS
        if isinstance(op07, Mapping) and op07.get("packet_generation_receipt_boundary_ready") is True
        else P7_R54_AHR_POST_MN11_PMN_OP06_IMPLEMENTED_STEPS
    )
    not_yet_steps = (
        P7_R54_AHR_POST_MN11_PMN_OP08_NOT_YET_IMPLEMENTED_STEPS
        if ready
        else P7_R54_AHR_POST_MN11_PMN_OP07_NOT_YET_IMPLEMENTED_STEPS
        if isinstance(op07, Mapping) and op07.get("packet_generation_receipt_boundary_ready") is True
        else P7_R54_AHR_POST_MN11_PMN_OP06_NOT_YET_IMPLEMENTED_STEPS
    )
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_schema_version": _clean_ref(op07.get("schema_version") if isinstance(op07, Mapping) else "", default="op07_schema_missing", max_length=220),
        "op07_material_ref": _clean_ref(op07.get("material_id") if isinstance(op07, Mapping) else "", default="op07_material_missing", max_length=220),
        "op07_next_required_step": _clean_ref(op07.get("next_required_step") if isinstance(op07, Mapping) else "", default="op07_next_required_step_missing", max_length=220),
        "op07_packet_generation_receipt_boundary_ready": bool(isinstance(op07, Mapping) and op07.get("packet_generation_receipt_boundary_ready") is True),
        "op07_packet_generation_receipt_required_after_external_local_generation": bool(isinstance(op07, Mapping) and op07.get("packet_generation_receipt_required_after_external_local_generation") is True),
        "op07_expected_actual_source_ref": _clean_ref(op07.get("packet_generation_receipt_expected_actual_source_ref") if isinstance(op07, Mapping) else "", default="op07_expected_actual_source_missing", max_length=220),
        "packet_scan_status_ref": status_ref,
        "packet_scan_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP08_ALLOWED_STATUS_REFS),
        "packet_scan_ready": ready,
        "packet_scan_blocker_refs": blockers,
        "packet_scan_blocker_ref_count": len(blockers),
        "packet_scan_reason_refs": reason_refs,
        "packet_scan_reason_ref_count": len(reason_refs),
        "packet_scan_ref": P7_R54_AHR_POST_MN11_PMN_OP08_PACKET_SCAN_REF if ready else "",
        "packet_scan_bodyfree_only": True,
        "packet_scan_depends_on_actual_packet_generation_receipt": True,
        "actual_packet_generation_receipt_received_here": receipt_received,
        "actual_packet_generation_receipt_intaked_here": ready,
        "actual_packet_generation_receipt_ref": _clean_ref(packet_generation_receipt_bodyfree.get("packet_generation_receipt_ref") if receipt_received else "", default="", max_length=220),
        "actual_packet_generation_receipt_source_ref": _clean_ref(packet_generation_receipt_bodyfree.get("actual_source_ref") if receipt_received else "", default="", max_length=220),
        "actual_packet_generation_receipt_source_allowed": bool(receipt_received and packet_generation_receipt_bodyfree.get("actual_source_ref") == P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF),
        "packet_generation_request_ref": _clean_ref(packet_generation_receipt_bodyfree.get("packet_generation_request_ref") if receipt_received else "", default="", max_length=220),
        "expected_packet_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "packet_count": packet_count,
        "packet_ref_id_count": packet_ref_id_count,
        "packet_ref_ids": receipt_refs,
        "packet_ref_ids_unique": _unique_non_empty(receipt_refs),
        "packet_count_matches_expected": packet_count == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "packet_ref_id_count_matches_expected": packet_ref_id_count == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "packet_completeness_scan_required": bool(isinstance(op07, Mapping) and op07.get("packet_completeness_scan_required_next") is True),
        "packet_completeness_scan_passed": ready,
        "reviewer_packet_required_fields_present": ready,
        "reviewer_packet_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_REVIEWER_PACKET_FIELD_REFS) if ready else [],
        "reviewer_packet_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_REVIEWER_PACKET_FIELD_REFS) if ready else 0,
        "export_denylist_policy_ref": P7_R54_AHR_POST_MN11_PMN_OP04_EXPORT_DENYLIST_POLICY_REF,
        "export_denylist_scan_required": bool(isinstance(op07, Mapping) and op07.get("export_denylist_scan_required_next") is True),
        "export_denylist_scan_passed": ready,
        "export_denylist_violation_refs": deny_refs,
        "export_denylist_violation_ref_count": len(deny_refs),
        "body_full_packet_export_candidate_refs": export_candidate_refs,
        "body_full_packet_export_candidate_count": len(export_candidate_refs),
        "body_full_packet_content_detected_in_export": bool(body_full_packet_content_detected_in_export),
        "question_text_detected_in_export": bool(question_text_detected_in_export),
        "draft_question_text_detected_in_export": bool(draft_question_text_detected_in_export),
        "local_path_detected_in_export": bool(local_path_detected_in_export),
        "body_hash_detected_in_export": bool(body_hash_detected_in_export),
        "terminal_output_body_detected_in_export": bool(terminal_output_body_detected_in_export),
        "body_full_packet_exported": False,
        "body_full_packet_exported_to_artifact": False,
        "body_full_packet_export_allowed": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "packet_content_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "packet_scan_does_not_materialize_packet_content_here": True,
        "reviewer_person_selection_only_form_freeze_allowed_next": ready,
        "actual_human_review_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op08_does_not_generate_body_full_packet": True,
        "pmn_op08_does_not_run_actual_human_review": True,
        "pmn_op08_does_not_create_actual_operation_receipt_or_review_rows_or_disposal": True,
        "pmn_op08_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP08 packet completeness / export denylist scan")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP08_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP08 packet completeness / export denylist scan")
    blockers = list(data.get("packet_scan_blocker_refs") or [])
    ready = not blockers
    leak_blocker_fragments = ("body_full", "packet_content", "question_text", "draft_question_text", "local_absolute_path", "local_path", "body_hash", "terminal_output")
    leak_detected = (
        any(data.get(key) is True for key in ("body_full_packet_content_detected_in_export", "question_text_detected_in_export", "draft_question_text_detected_in_export", "local_path_detected_in_export", "body_hash_detected_in_export", "terminal_output_body_detected_in_export"))
        or bool(data.get("export_denylist_violation_refs") or data.get("body_full_packet_export_candidate_refs"))
        or any(any(fragment in blocker for fragment in leak_blocker_fragments) for blocker in blockers)
    )
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP08_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_BY_LEAK_STATUS_REF if leak_detected else P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_STATUS_REF
    if data.get("packet_scan_status_ref") != expected_status or data.get("packet_scan_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 status/ready changed")
    if tuple(data.get("packet_scan_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 allowed status refs changed")
    for count_field, list_field in (("packet_scan_blocker_ref_count", "packet_scan_blocker_refs"), ("packet_scan_reason_ref_count", "packet_scan_reason_refs"), ("export_denylist_violation_ref_count", "export_denylist_violation_refs"), ("body_full_packet_export_candidate_count", "body_full_packet_export_candidate_refs")):
        if data.get(count_field) != len(data.get(list_field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP08 {count_field} changed")
    for key in ("packet_scan_bodyfree_only", "packet_scan_depends_on_actual_packet_generation_receipt", "packet_scan_does_not_materialize_packet_content_here", "actual_human_review_still_not_run", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171", "pmn_op08_does_not_generate_body_full_packet", "pmn_op08_does_not_run_actual_human_review", "pmn_op08_does_not_create_actual_operation_receipt_or_review_rows_or_disposal", "pmn_op08_does_not_start_p8_p6_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP08 required true field changed: {key}")
    for key in ("body_full_packet_exported", "body_full_packet_exported_to_artifact", "body_full_packet_export_allowed", "local_absolute_path_included", "body_hash_stored", "terminal_output_body_included", "packet_content_included", "question_text_included", "draft_question_text_included"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP08 required false field promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 actual review basis changed")
    if data.get("expected_packet_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 expected packet count changed")
    if ready:
        if data.get("op07_packet_generation_receipt_boundary_ready") is not True or data.get("op07_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 ready scan requires OP07 ready next step")
        if data.get("actual_packet_generation_receipt_received_here") is not True or data.get("actual_packet_generation_receipt_intaked_here") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 ready scan requires body-free receipt")
        if data.get("actual_packet_generation_receipt_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP07_ACTUAL_SOURCE_REF or data.get("actual_packet_generation_receipt_source_allowed") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 actual source ref changed")
        if data.get("packet_generation_request_ref") != P7_R54_AHR_POST_MN11_PMN_OP06_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 packet generation request ref changed")
        if data.get("packet_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("packet_ref_id_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 packet counts must be 24")
        if data.get("packet_count_matches_expected") is not True or data.get("packet_ref_id_count_matches_expected") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 packet count match flags changed")
        if not _unique_non_empty(list(data.get("packet_ref_ids") or [])) or len(data.get("packet_ref_ids") or []) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 packet refs must be 24 unique body-free refs")
        for key in ("packet_completeness_scan_required", "packet_completeness_scan_passed", "reviewer_packet_required_fields_present", "export_denylist_scan_required", "export_denylist_scan_passed", "reviewer_person_selection_only_form_freeze_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP08 ready field changed: {key}")
        if tuple(data.get("reviewer_packet_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_REVIEWER_PACKET_FIELD_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 reviewer packet field refs changed")
        if data.get("reviewer_packet_required_field_ref_count") != len(P7_R54_AHR_POST_MN11_PMN_OP08_REQUIRED_REVIEWER_PACKET_FIELD_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 reviewer packet field count changed")
        if leak_detected or data.get("packet_scan_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP08_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 ready scan leak/reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP08_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 next step changed")
    else:
        if data.get("packet_completeness_scan_passed") is not False or data.get("export_denylist_scan_passed") is not False or data.get("reviewer_person_selection_only_form_freeze_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 blocked scan promoted scan/form readiness")
        if data.get("actual_packet_generation_receipt_intaked_here") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 blocked scan cannot intake receipt")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP08 blocked next step changed")
    return True


def _pmn_op09_blockers(op08: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op08, Mapping):
        return ["pmn_op09_packet_scan_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_contract(op08)
    except ValueError:
        blockers.append("pmn_op09_packet_scan_contract_invalid")
    if op08.get("packet_scan_ready") is not True:
        blockers.append("pmn_op09_packet_scan_not_ready")
    if op08.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF:
        blockers.append("pmn_op09_op08_next_step_not_reviewer_form")
    if op08.get("reviewer_person_selection_only_form_freeze_allowed_next") is not True:
        blockers.append("pmn_op09_form_freeze_not_allowed_next")
    if op08.get("packet_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or op08.get("packet_ref_id_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op09_packet_counts_not_24")
    if op08.get("packet_completeness_scan_passed") is not True or op08.get("export_denylist_scan_passed") is not True:
        blockers.append("pmn_op09_packet_scan_not_passed")
    if _scan_forbidden_payload_key_paths(op08):
        blockers.append("pmn_op09_op08_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze(
    *,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP09 body-free reviewer person / selection-only form freeze material."""

    session_id = _safe_review_session_id(review_session_id)
    op08 = packet_completeness_export_denylist_scan
    if op08 is None:
        op08 = build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
            packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
            packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op09_blockers(op08)
    ready = not blockers
    reason_refs = list(P7_R54_AHR_POST_MN11_PMN_OP09_READY_REASON_REFS) if ready else blockers
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op08_schema_version": _clean_ref(op08.get("schema_version") if isinstance(op08, Mapping) else "", default="op08_schema_missing", max_length=220),
        "op08_material_ref": _clean_ref(op08.get("material_id") if isinstance(op08, Mapping) else "", default="op08_material_missing", max_length=220),
        "op08_next_required_step": _clean_ref(op08.get("next_required_step") if isinstance(op08, Mapping) else "", default="op08_next_required_step_missing", max_length=220),
        "op08_packet_scan_status_ref": _clean_ref(op08.get("packet_scan_status_ref") if isinstance(op08, Mapping) else "", default="op08_packet_scan_status_missing", max_length=220),
        "op08_packet_scan_ready": bool(isinstance(op08, Mapping) and op08.get("packet_scan_ready") is True),
        "op08_packet_count": int(op08.get("packet_count") or 0) if isinstance(op08, Mapping) else 0,
        "op08_packet_ref_id_count": int(op08.get("packet_ref_id_count") or 0) if isinstance(op08, Mapping) else 0,
        "op08_packet_completeness_scan_passed": bool(isinstance(op08, Mapping) and op08.get("packet_completeness_scan_passed") is True),
        "op08_export_denylist_scan_passed": bool(isinstance(op08, Mapping) and op08.get("export_denylist_scan_passed") is True),
        "reviewer_form_status_ref": P7_R54_AHR_POST_MN11_PMN_OP09_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_STATUS_REF,
        "reviewer_form_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_ALLOWED_STATUS_REFS),
        "reviewer_form_ready": ready,
        "reviewer_form_blocker_refs": blockers,
        "reviewer_form_blocker_ref_count": len(blockers),
        "reviewer_form_reason_refs": reason_refs,
        "reviewer_form_reason_ref_count": len(reason_refs),
        "reviewer_person_ref": P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_REF if ready else "",
        "reviewer_person_ref_present": ready,
        "reviewer_is_person": ready,
        "reviewer_person_confirmed": ready,
        "reviewer_local_only_read_receipt_present": False,
        "actual_human_review_executed_by_person": False,
        "reviewer_identity_public_export_allowed": False,
        "reviewer_free_text_export_allowed": False,
        "reviewer_notes_body_export_allowed": False,
        "selection_only_form_ready": ready,
        "selection_only_form_ref": P7_R54_AHR_POST_MN11_PMN_OP09_SELECTION_ONLY_FORM_REF if ready else "",
        "reviewer_instruction_ref": P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_INSTRUCTION_REF if ready else "",
        "reviewer_instruction_policy_ref": "selection_only_no_free_text_no_question_text_no_raw_body_no_path_no_hash" if ready else "",
        "selection_only": ready,
        "selection_only_form_bodyfree_only": True,
        "free_text_field_present": False,
        "free_text_field_export_allowed": False,
        "reviewer_notes_body_field_present": False,
        "raw_body_copy_field_present": False,
        "question_text_field_present": False,
        "draft_question_text_field_present": False,
        "local_path_field_present": False,
        "body_hash_field_present": False,
        "packet_content_field_present": False,
        "required_axis_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS) if ready else 0,
        "required_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "rating_axis_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS) if ready else [],
        "rating_axis_target_thresholds": dict(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS) if ready else {},
        "score_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_SCORE_OPTION_REFS) if ready else [],
        "verdict_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_VERDICT_OPTION_REFS) if ready else [],
        "sanitized_reason_id_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_SANITIZED_REASON_ID_OPTION_REFS) if ready else [],
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_READFEEL_BLOCKER_ID_OPTION_REFS) if ready else [],
        "execution_blocker_id_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_EXECUTION_BLOCKER_ID_OPTION_REFS) if ready else [],
        "question_need_primary_class_options": list(P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS) if ready else [],
        "ambiguity_kind_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS) if ready else [],
        "one_question_fit_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS) if ready else [],
        "repair_required_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS) if ready else [],
        "plan_candidate_flag_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_PLAN_CANDIDATE_FLAG_REFS) if ready else [],
        "reviewer_receives_blind_case_id_only": ready,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_case_ref_exposed": False,
        "reviewer_facing_packet_ref_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "reviewer_facing_hidden_metadata_exposed": False,
        "actual_human_review_state_capture_allowed_next": ready,
        "actual_human_review_started_here": False,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op09_does_not_run_actual_human_review": True,
        "pmn_op09_does_not_create_actual_operation_receipt_or_rows_or_disposal": True,
        "pmn_op09_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP09_IMPLEMENTED_STEPS if ready else tuple(op08.get("implemented_steps") or P7_R54_AHR_POST_MN11_PMN_OP07_IMPLEMENTED_STEPS) if isinstance(op08, Mapping) else P7_R54_AHR_POST_MN11_PMN_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP09_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op08.get("not_yet_implemented_steps") or P7_R54_AHR_POST_MN11_PMN_OP07_NOT_YET_IMPLEMENTED_STEPS) if isinstance(op08, Mapping) else P7_R54_AHR_POST_MN11_PMN_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP09 reviewer person / selection-only form freeze")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_SELECTION_ONLY_FORM_FREEZE_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP09 reviewer person / selection-only form freeze")
    blockers = list(data.get("reviewer_form_blocker_refs") or [])
    ready = not blockers
    if data.get("reviewer_form_status_ref") != (P7_R54_AHR_POST_MN11_PMN_OP09_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_STATUS_REF) or data.get("reviewer_form_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 status/ready changed")
    if tuple(data.get("reviewer_form_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP09_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 allowed status refs changed")
    for count_field, list_field in (("reviewer_form_blocker_ref_count", "reviewer_form_blocker_refs"), ("reviewer_form_reason_ref_count", "reviewer_form_reason_refs")):
        if data.get(count_field) != len(data.get(list_field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP09 {count_field} changed")
    for key in ("selection_only_form_bodyfree_only", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171", "pmn_op09_does_not_run_actual_human_review", "pmn_op09_does_not_create_actual_operation_receipt_or_rows_or_disposal", "pmn_op09_does_not_start_p8_p6_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP09 required true field changed: {key}")
    for key in ("reviewer_local_only_read_receipt_present", "actual_human_review_executed_by_person", "reviewer_identity_public_export_allowed", "reviewer_free_text_export_allowed", "reviewer_notes_body_export_allowed", "free_text_field_present", "free_text_field_export_allowed", "reviewer_notes_body_field_present", "raw_body_copy_field_present", "question_text_field_present", "draft_question_text_field_present", "local_path_field_present", "body_hash_field_present", "packet_content_field_present", "reviewer_facing_family_exposed", "reviewer_facing_tier_exposed", "reviewer_facing_case_ref_exposed", "reviewer_facing_packet_ref_exposed", "reviewer_facing_expected_result_exposed", "reviewer_facing_hidden_metadata_exposed", "actual_human_review_started_here", "actual_human_review_run_here"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP09 required false field promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 actual review basis changed")
    if data.get("required_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 required case count changed")
    if ready:
        if data.get("op08_packet_scan_ready") is not True or data.get("op08_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 ready form requires OP08 ready next step")
        if data.get("op08_packet_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("op08_packet_ref_id_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 ready form requires 24 packets")
        if data.get("op08_packet_completeness_scan_passed") is not True or data.get("op08_export_denylist_scan_passed") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 ready form requires OP08 passed scans")
        for key in ("reviewer_person_ref_present", "reviewer_is_person", "reviewer_person_confirmed", "selection_only_form_ready", "selection_only", "reviewer_receives_blind_case_id_only", "actual_human_review_state_capture_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP09 ready field changed: {key}")
        if data.get("reviewer_person_ref") != P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 reviewer person ref changed")
        if data.get("selection_only_form_ref") != P7_R54_AHR_POST_MN11_PMN_OP09_SELECTION_ONLY_FORM_REF or data.get("reviewer_instruction_ref") != P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_INSTRUCTION_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 form/instruction refs changed")
        if data.get("required_axis_count") != len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 axis count changed")
        if tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 axis refs changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 axis thresholds changed")
        for field, expected in (
            ("score_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_SCORE_OPTION_REFS),
            ("verdict_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_VERDICT_OPTION_REFS),
            ("sanitized_reason_id_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_SANITIZED_REASON_ID_OPTION_REFS),
            ("readfeel_blocker_id_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_READFEEL_BLOCKER_ID_OPTION_REFS),
            ("execution_blocker_id_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_EXECUTION_BLOCKER_ID_OPTION_REFS),
            ("question_need_primary_class_options", P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS),
            ("ambiguity_kind_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS),
            ("one_question_fit_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS),
            ("repair_required_option_refs", P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS),
            ("plan_candidate_flag_refs", P7_R54_AHR_POST_MN11_PMN_OP09_PLAN_CANDIDATE_FLAG_REFS),
        ):
            if tuple(data.get(field) or ()) != expected:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP09 option refs changed: {field}")
        if data.get("reviewer_form_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP09_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP09_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 next step changed")
    else:
        for key in ("reviewer_person_ref_present", "reviewer_is_person", "reviewer_person_confirmed", "selection_only_form_ready", "selection_only", "reviewer_receives_blind_case_id_only", "actual_human_review_state_capture_allowed_next"):
            if data.get(key) is not False:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 blocked form promoted reviewer boundary")
        for field in ("rating_axis_refs", "score_option_refs", "verdict_option_refs", "question_need_primary_class_options"):
            if data.get(field) != []:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 blocked form exposed reviewer options")
        if data.get("required_axis_count") != 0:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 blocked axis count changed")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP09 blocked next step changed")
    return True




def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bodyfree_ref_details(value: Any, *, default: str = "", max_length: int = 220) -> tuple[str, bool, bool, bool]:
    ref = _clean_ref(value, default=default, max_length=max_length)
    has_path = _ref_has_local_path_shape(ref)
    present = bool(ref) and not has_path
    return ref, present, present, has_path


def _pmn_op10_state_capture_blockers(op09: Mapping[str, Any] | None, state_capture: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op09, Mapping):
        return ["pmn_op10_reviewer_person_selection_only_form_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_contract(op09)
    except ValueError:
        blockers.append("pmn_op10_op09_reviewer_person_selection_only_form_invalid")
    if op09.get("reviewer_form_ready") is not True:
        blockers.append("pmn_op10_op09_reviewer_form_not_ready")
    if op09.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF:
        blockers.append("pmn_op10_op09_next_step_not_actual_review_state_capture")
    if op09.get("actual_human_review_state_capture_allowed_next") is not True:
        blockers.append("pmn_op10_op09_state_capture_not_allowed_next")
    if _scan_forbidden_payload_key_paths(op09):
        blockers.append("pmn_op10_op09_forbidden_body_question_path_hash_key_detected")

    if not isinstance(state_capture, Mapping):
        blockers.append("pmn_op10_actual_human_review_execution_state_capture_not_received")
        return list(dict.fromkeys(blockers))

    missing_fields = [field for field in P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_STATE_CAPTURE_FIELD_REFS if field not in state_capture]
    if missing_fields:
        blockers.append("pmn_op10_state_capture_required_fields_missing")
    if _scan_forbidden_payload_key_paths(state_capture):
        blockers.append("pmn_op10_state_capture_forbidden_body_question_path_hash_key_detected")
    if state_capture.get("body_free") is not True:
        blockers.append("pmn_op10_state_capture_not_bodyfree")
    if state_capture.get("actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append("pmn_op10_state_capture_actual_source_ref_not_allowed")
    if state_capture.get("review_session_id") != op09.get("review_session_id"):
        blockers.append("pmn_op10_state_capture_review_session_id_mismatch")
    if state_capture.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("pmn_op10_state_capture_actual_review_basis_ref_mismatch")
    reviewer_ref = _clean_ref(state_capture.get("reviewer_person_ref"), default="", max_length=180)
    if not reviewer_ref:
        blockers.append("pmn_op10_state_capture_reviewer_person_ref_missing")
    if _ref_has_local_path_shape(reviewer_ref):
        blockers.append("pmn_op10_state_capture_reviewer_person_ref_path_shape")
    if reviewer_ref and reviewer_ref != op09.get("reviewer_person_ref"):
        blockers.append("pmn_op10_state_capture_reviewer_person_ref_mismatch")
    if state_capture.get("reviewer_is_person") is not True:
        blockers.append("pmn_op10_state_capture_reviewer_is_person_not_true")
    if state_capture.get("reviewer_person_confirmed") is not True:
        blockers.append("pmn_op10_state_capture_reviewer_person_confirmed_not_true")
    if state_capture.get("reviewer_local_only_read_receipt_present") is not True:
        blockers.append("pmn_op10_state_capture_reviewer_local_only_read_receipt_missing")
    if state_capture.get("actual_human_review_executed_by_person") is not True:
        blockers.append("pmn_op10_state_capture_actual_human_review_executed_by_person_not_true")
    if state_capture.get("review_state_ref") != P7_R54_AHR_POST_MN11_PMN_OP10_REVIEW_STATE_COMPLETED_SELECTION_ROWS_READY_REF:
        blockers.append("pmn_op10_state_capture_review_state_not_completed_selection_rows_ready")
    started_ref = _clean_ref(state_capture.get("review_started_at_bucket_ref"), default="", max_length=220)
    completed_ref = _clean_ref(state_capture.get("review_completed_at_bucket_ref"), default="", max_length=220)
    if not started_ref:
        blockers.append("pmn_op10_state_capture_review_started_bucket_ref_missing")
    if started_ref and _ref_has_local_path_shape(started_ref):
        blockers.append("pmn_op10_state_capture_review_started_bucket_ref_path_shape")
    if not completed_ref:
        blockers.append("pmn_op10_state_capture_review_completed_bucket_ref_missing")
    if completed_ref and _ref_has_local_path_shape(completed_ref):
        blockers.append("pmn_op10_state_capture_review_completed_bucket_ref_path_shape")
    if _safe_int(state_capture.get("reviewed_case_count")) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op10_state_capture_reviewed_case_count_not_24")
    if _safe_int(state_capture.get("selection_row_count")) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op10_state_capture_selection_row_count_not_24")
    for true_key in ("local_only", "must_not_export", "selection_only"):
        if state_capture.get(true_key) is not True:
            blockers.append(f"pmn_op10_state_capture_{true_key}_not_true")
    for false_key in (
        "reviewer_free_text_exported",
        "reviewer_notes_body_exported",
        "body_quotation_exported",
        "question_text_materialized_in_review",
        "draft_question_text_materialized_in_review",
        "packet_content_exported",
        "body_full_packet_content_exported",
        "local_absolute_path_included",
        "body_hash_included",
        "terminal_output_body_included",
        "raw_input_included",
        "returned_emlis_body_included",
        "history_body_included",
        "comment_text_body_included",
        "reviewer_free_text_included",
        "reviewer_notes_body_included",
        "question_text_included",
        "draft_question_text_included",
        "packet_content_included",
        "body_full_packet_content_included",
        "stdout_body_included",
        "stderr_body_included",
        "traceback_body_included",
    ):
        if false_key in state_capture and state_capture.get(false_key) is not False:
            blockers.append(f"pmn_op10_state_capture_{false_key}_not_false")
    for source_flag in (
        "row_created_by_helper",
        "row_created_for_unit_test",
        "row_is_synthetic_contract_fixture",
        "historical_row_reused",
        "helper_default_rows_materialized_as_actual_here",
        "unit_test_rows_materialized_as_actual_here",
        "synthetic_contract_rows_materialized_as_actual_here",
        "historical_rows_materialized_as_actual_here",
    ):
        if state_capture.get(source_flag) is True:
            blockers.append(f"pmn_op10_state_capture_{source_flag}_cannot_be_actual")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture(
    *,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP10 body-free actual 24-case review execution state capture material."""

    session_id = _safe_review_session_id(review_session_id)
    op09 = reviewer_person_boundary_selection_only_form_freeze
    if op09 is None:
        op09 = build_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze(
            packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
            packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
            packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op10_state_capture_blockers(op09, actual_review_execution_state_capture_bodyfree)
    ready = not blockers
    capture_received = isinstance(actual_review_execution_state_capture_bodyfree, Mapping)
    leak_detected = bool(
        capture_received
        and (
            _scan_forbidden_payload_key_paths(actual_review_execution_state_capture_bodyfree)
            or any("body" in blocker or "question" in blocker or "path" in blocker or "hash" in blocker or "terminal" in blocker for blocker in blockers)
        )
    )
    status_ref = (
        P7_R54_AHR_POST_MN11_PMN_OP10_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_BY_LEAK_STATUS_REF
        if leak_detected
        else P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_STATUS_REF
    )
    reason_refs = list(P7_R54_AHR_POST_MN11_PMN_OP10_READY_REASON_REFS) if ready else blockers
    state = actual_review_execution_state_capture_bodyfree or {}
    reviewer_ref = _clean_ref(state.get("reviewer_person_ref") if capture_received else op09.get("reviewer_person_ref") if isinstance(op09, Mapping) else "", default="", max_length=180)
    started_ref = _clean_ref(state.get("review_started_at_bucket_ref") if capture_received else "", default="", max_length=220)
    completed_ref = _clean_ref(state.get("review_completed_at_bucket_ref") if capture_received else "", default="", max_length=220)
    reviewed_count = _safe_int(state.get("reviewed_case_count") if capture_received else 0)
    selection_count = _safe_int(state.get("selection_row_count") if capture_received else 0)
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP10_IMPLEMENTED_STEPS if ready else tuple(op09.get("implemented_steps") or P7_R54_AHR_POST_MN11_PMN_OP09_IMPLEMENTED_STEPS) if isinstance(op09, Mapping) else P7_R54_AHR_POST_MN11_PMN_OP08_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP10_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op09.get("not_yet_implemented_steps") or P7_R54_AHR_POST_MN11_PMN_OP09_NOT_YET_IMPLEMENTED_STEPS) if isinstance(op09, Mapping) else P7_R54_AHR_POST_MN11_PMN_OP08_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP10_ACTUAL_24_CASE_HUMAN_REVIEW_EXECUTION_PROTOCOL_STATE_CAPTURE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op09_schema_version": _clean_ref(op09.get("schema_version") if isinstance(op09, Mapping) else "", default="op09_schema_missing", max_length=220),
        "op09_material_ref": _clean_ref(op09.get("material_id") if isinstance(op09, Mapping) else "", default="op09_material_missing", max_length=220),
        "op09_next_required_step": _clean_ref(op09.get("next_required_step") if isinstance(op09, Mapping) else "", default="op09_next_required_step_missing", max_length=220),
        "op09_reviewer_form_status_ref": _clean_ref(op09.get("reviewer_form_status_ref") if isinstance(op09, Mapping) else "", default="op09_reviewer_form_status_missing", max_length=220),
        "op09_reviewer_form_ready": bool(isinstance(op09, Mapping) and op09.get("reviewer_form_ready") is True),
        "op09_reviewer_person_ref": _clean_ref(op09.get("reviewer_person_ref") if isinstance(op09, Mapping) else "", default="", max_length=180),
        "op09_reviewer_is_person": bool(isinstance(op09, Mapping) and op09.get("reviewer_is_person") is True),
        "op09_reviewer_person_confirmed": bool(isinstance(op09, Mapping) and op09.get("reviewer_person_confirmed") is True),
        "op09_selection_only_form_ready": bool(isinstance(op09, Mapping) and op09.get("selection_only_form_ready") is True),
        "op09_actual_human_review_state_capture_allowed_next": bool(isinstance(op09, Mapping) and op09.get("actual_human_review_state_capture_allowed_next") is True),
        "review_execution_state_capture_status_ref": status_ref,
        "review_execution_state_capture_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_STATUS_REFS),
        "review_execution_state_capture_ready": ready,
        "review_execution_state_capture_blocker_refs": blockers,
        "review_execution_state_capture_blocker_ref_count": len(blockers),
        "review_execution_state_capture_reason_refs": reason_refs,
        "review_execution_state_capture_reason_ref_count": len(reason_refs),
        "review_execution_protocol_ref": P7_R54_AHR_POST_MN11_PMN_OP10_STATE_CAPTURE_REF if ready else "",
        "review_execution_protocol_bodyfree_only": True,
        "review_execution_protocol_step_refs": list(P7_R54_AHR_POST_MN11_PMN_OP10_PROTOCOL_STEP_REFS),
        "review_execution_protocol_step_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP10_PROTOCOL_STEP_REFS),
        "actual_review_state_capture_received_here": capture_received,
        "actual_review_state_capture_intaked_here": ready,
        "actual_review_state_capture_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_STATE_CAPTURE_FIELD_REFS),
        "actual_review_state_capture_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_STATE_CAPTURE_FIELD_REFS),
        "actual_review_state_capture_ref": _clean_ref(state.get("review_state_capture_ref") if capture_received else "", default="", max_length=220),
        "actual_review_state_capture_source_ref": _clean_ref(state.get("actual_source_ref") if capture_received else "", default="", max_length=220),
        "actual_review_state_capture_source_allowed": bool(capture_received and state.get("actual_source_ref") == P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_ACTUAL_SOURCE_REF),
        "review_state_ref": _clean_ref(state.get("review_state_ref") if capture_received else "", default="", max_length=180),
        "allowed_review_state_refs": list(P7_R54_AHR_POST_MN11_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "allowed_review_state_ref_count": len(P7_R54_AHR_POST_MN11_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "reviewer_person_ref": reviewer_ref,
        "reviewer_person_ref_present": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_matches_op09": bool(isinstance(op09, Mapping) and reviewer_ref == op09.get("reviewer_person_ref")),
        "reviewer_is_person": bool(capture_received and state.get("reviewer_is_person") is True),
        "reviewer_person_confirmed": bool(capture_received and state.get("reviewer_person_confirmed") is True),
        "reviewer_local_only_read_receipt_present": bool(capture_received and state.get("reviewer_local_only_read_receipt_present") is True),
        "actual_human_review_executed_by_person": bool(capture_received and state.get("actual_human_review_executed_by_person") is True and ready),
        "review_started_at_bucket_ref": started_ref,
        "review_started_at_bucket_ref_present": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_at_bucket_ref_is_bodyfree_ref": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_at_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(started_ref),
        "review_completed_at_bucket_ref": completed_ref,
        "review_completed_at_bucket_ref_present": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_at_bucket_ref_is_bodyfree_ref": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_at_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(completed_ref),
        "reviewed_case_count": reviewed_count,
        "required_reviewed_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "reviewed_case_count_is_24": reviewed_count == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "selection_row_count": selection_count,
        "required_selection_row_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "selection_row_count_is_24": selection_count == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "local_only": bool(capture_received and state.get("local_only") is True),
        "must_not_export": bool(capture_received and state.get("must_not_export") is True),
        "selection_only": bool(capture_received and state.get("selection_only") is True),
        "body_full_packet_stayed_local_only": ready,
        "reviewer_free_text_exported": False,
        "reviewer_notes_body_exported": False,
        "body_quotation_exported": False,
        "question_text_materialized_in_review": False,
        "draft_question_text_materialized_in_review": False,
        "packet_content_exported": False,
        "body_full_packet_content_exported": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "actual_operation_receipt_required_next": ready,
        "operation_receipt_required_actual_source_ref": P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF,
        "actual_operation_receipt_intake_allowed_next": ready,
        "actual_operation_receipt_intaked_here": False,
        "actual_selection_rows_created_here": False,
        "actual_sanitized_review_result_rows_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op10_does_not_generate_body_full_packet": True,
        "pmn_op10_does_not_create_actual_operation_receipt_or_rows_or_disposal": True,
        "pmn_op10_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP10 actual human review execution state capture")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP10_ACTUAL_24_CASE_HUMAN_REVIEW_EXECUTION_PROTOCOL_STATE_CAPTURE_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP10 actual human review execution state capture")
    blockers = list(data.get("review_execution_state_capture_blocker_refs") or [])
    ready = not blockers
    leak_blocker_fragments = ("body", "question", "path", "hash", "terminal", "stdout", "stderr", "traceback")
    leak_detected = any(any(fragment in blocker for fragment in leak_blocker_fragments) for blocker in blockers)
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP10_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_BY_LEAK_STATUS_REF if leak_detected else P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_STATUS_REF
    if data.get("review_execution_state_capture_status_ref") != expected_status or data.get("review_execution_state_capture_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 status/ready changed")
    if tuple(data.get("review_execution_state_capture_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 allowed status refs changed")
    for count_field, list_field in (("review_execution_state_capture_blocker_ref_count", "review_execution_state_capture_blocker_refs"), ("review_execution_state_capture_reason_ref_count", "review_execution_state_capture_reason_refs"), ("review_execution_protocol_step_ref_count", "review_execution_protocol_step_refs"), ("actual_review_state_capture_required_field_ref_count", "actual_review_state_capture_required_field_refs"), ("allowed_review_state_ref_count", "allowed_review_state_refs")):
        if data.get(count_field) != len(data.get(list_field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP10 {count_field} changed")
    for key in ("review_execution_protocol_bodyfree_only", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171", "pmn_op10_does_not_generate_body_full_packet", "pmn_op10_does_not_create_actual_operation_receipt_or_rows_or_disposal", "pmn_op10_does_not_start_p8_p6_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP10 required true field changed: {key}")
    for key in ("reviewer_free_text_exported", "reviewer_notes_body_exported", "body_quotation_exported", "question_text_materialized_in_review", "draft_question_text_materialized_in_review", "packet_content_exported", "body_full_packet_content_exported", "local_absolute_path_included", "body_hash_included", "terminal_output_body_included", "actual_operation_receipt_intaked_here", "actual_selection_rows_created_here", "actual_sanitized_review_result_rows_materialized_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP10 required false field promoted: {key}")
    if tuple(data.get("review_execution_protocol_step_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP10_PROTOCOL_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 protocol steps changed")
    if tuple(data.get("actual_review_state_capture_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP10_REQUIRED_STATE_CAPTURE_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 required state capture fields changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 actual review basis changed")
    if data.get("required_reviewed_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("required_selection_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 required counts changed")
    if ready:
        if data.get("op09_reviewer_form_ready") is not True or data.get("op09_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP10_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 ready capture requires OP09 ready next step")
        for key in ("actual_review_state_capture_received_here", "actual_review_state_capture_intaked_here", "actual_review_state_capture_source_allowed", "reviewer_person_ref_present", "reviewer_person_ref_matches_op09", "reviewer_is_person", "reviewer_person_confirmed", "reviewer_local_only_read_receipt_present", "actual_human_review_executed_by_person", "review_started_at_bucket_ref_present", "review_started_at_bucket_ref_is_bodyfree_ref", "review_completed_at_bucket_ref_present", "review_completed_at_bucket_ref_is_bodyfree_ref", "reviewed_case_count_is_24", "selection_row_count_is_24", "local_only", "must_not_export", "selection_only", "body_full_packet_stayed_local_only", "actual_operation_receipt_required_next", "actual_operation_receipt_intake_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP10 ready field changed: {key}")
        if data.get("actual_review_state_capture_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP10_ALLOWED_ACTUAL_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 source ref changed")
        if data.get("review_state_ref") != P7_R54_AHR_POST_MN11_PMN_OP10_REVIEW_STATE_COMPLETED_SELECTION_ROWS_READY_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 review state changed")
        if data.get("review_started_at_bucket_ref_has_local_path_shape") is not False or data.get("review_completed_at_bucket_ref_has_local_path_shape") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 bucket refs must be body-free refs")
        if data.get("reviewed_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("selection_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 counts must be 24")
        if data.get("operation_receipt_required_actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 operation receipt source changed")
        if data.get("review_execution_state_capture_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP10_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP10_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 next step changed")
    else:
        if data.get("actual_review_state_capture_intaked_here") is not False or data.get("actual_operation_receipt_intake_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 blocked capture promoted operation receipt intake")
        if data.get("actual_human_review_executed_by_person") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 blocked capture promoted human review execution")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP10 blocked next step changed")
    return True


def _pmn_op11_operation_receipt_blockers(op10: Mapping[str, Any] | None, operation_receipt: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op10, Mapping):
        return ["pmn_op11_actual_review_execution_state_capture_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_contract(op10)
    except ValueError:
        blockers.append("pmn_op11_op10_actual_review_execution_state_capture_invalid")
    if op10.get("review_execution_state_capture_ready") is not True:
        blockers.append("pmn_op11_op10_actual_review_execution_state_capture_not_ready")
    if op10.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF:
        blockers.append("pmn_op11_op10_next_step_not_operation_receipt_intake")
    if op10.get("actual_operation_receipt_required_next") is not True:
        blockers.append("pmn_op11_op10_operation_receipt_not_required_next")
    if _scan_forbidden_payload_key_paths(op10):
        blockers.append("pmn_op11_op10_forbidden_body_question_path_hash_key_detected")
    if not isinstance(operation_receipt, Mapping):
        blockers.append("pmn_op11_actual_operation_receipt_not_received")
        return list(dict.fromkeys(blockers))
    missing_fields = [field for field in P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_OPERATION_RECEIPT_FIELD_REFS if field not in operation_receipt]
    if missing_fields:
        blockers.append("pmn_op11_operation_receipt_required_fields_missing")
    if _scan_forbidden_payload_key_paths(operation_receipt):
        blockers.append("pmn_op11_operation_receipt_forbidden_body_question_path_hash_key_detected")
    if operation_receipt.get("body_free") is not True:
        blockers.append("pmn_op11_operation_receipt_not_bodyfree")
    if operation_receipt.get("actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append("pmn_op11_operation_receipt_actual_source_ref_not_allowed")
    if operation_receipt.get("review_session_id") != op10.get("review_session_id"):
        blockers.append("pmn_op11_operation_receipt_review_session_id_mismatch")
    if operation_receipt.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("pmn_op11_operation_receipt_actual_review_basis_ref_mismatch")
    receipt_ref = _clean_ref(operation_receipt.get("operation_receipt_ref"), default="", max_length=220)
    if not receipt_ref:
        blockers.append("pmn_op11_operation_receipt_ref_missing")
    if receipt_ref and _ref_has_local_path_shape(receipt_ref):
        blockers.append("pmn_op11_operation_receipt_ref_path_shape")
    reviewer_ref = _clean_ref(operation_receipt.get("reviewer_person_ref"), default="", max_length=180)
    if not reviewer_ref:
        blockers.append("pmn_op11_operation_receipt_reviewer_person_ref_missing")
    if reviewer_ref and _ref_has_local_path_shape(reviewer_ref):
        blockers.append("pmn_op11_operation_receipt_reviewer_person_ref_path_shape")
    if reviewer_ref and reviewer_ref != op10.get("reviewer_person_ref"):
        blockers.append("pmn_op11_operation_receipt_reviewer_person_ref_mismatch")
    if operation_receipt.get("reviewer_is_person") is not True:
        blockers.append("pmn_op11_operation_receipt_reviewer_is_person_not_true")
    if operation_receipt.get("reviewer_person_confirmed") is not True:
        blockers.append("pmn_op11_operation_receipt_reviewer_person_confirmed_not_true")
    if operation_receipt.get("reviewer_local_only_read_receipt_present") is not True:
        blockers.append("pmn_op11_operation_receipt_reviewer_local_only_read_receipt_missing")
    started_ref = _clean_ref(operation_receipt.get("review_started_at_bucket_ref"), default="", max_length=220)
    completed_ref = _clean_ref(operation_receipt.get("review_completed_at_bucket_ref"), default="", max_length=220)
    if not started_ref:
        blockers.append("pmn_op11_operation_receipt_review_started_bucket_ref_missing")
    if started_ref and _ref_has_local_path_shape(started_ref):
        blockers.append("pmn_op11_operation_receipt_review_started_bucket_ref_path_shape")
    if started_ref and started_ref != op10.get("review_started_at_bucket_ref"):
        blockers.append("pmn_op11_operation_receipt_review_started_bucket_ref_mismatch")
    if not completed_ref:
        blockers.append("pmn_op11_operation_receipt_review_completed_bucket_ref_missing")
    if completed_ref and _ref_has_local_path_shape(completed_ref):
        blockers.append("pmn_op11_operation_receipt_review_completed_bucket_ref_path_shape")
    if completed_ref and completed_ref != op10.get("review_completed_at_bucket_ref"):
        blockers.append("pmn_op11_operation_receipt_review_completed_bucket_ref_mismatch")
    reviewed_count = _safe_int(operation_receipt.get("reviewed_case_count"))
    selection_count = _safe_int(operation_receipt.get("selection_row_count"))
    if reviewed_count != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op11_operation_receipt_reviewed_case_count_not_24")
    if reviewed_count != op10.get("reviewed_case_count"):
        blockers.append("pmn_op11_operation_receipt_reviewed_case_count_mismatch_op10")
    if selection_count != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op11_operation_receipt_selection_row_count_not_24")
    if selection_count != op10.get("selection_row_count"):
        blockers.append("pmn_op11_operation_receipt_selection_row_count_mismatch_op10")
    for true_key in ("local_only", "must_not_export", "selection_only"):
        if operation_receipt.get(true_key) is not True:
            blockers.append(f"pmn_op11_operation_receipt_{true_key}_not_true")
    for false_key in (
        "raw_input_included",
        "returned_emlis_body_included",
        "history_body_included",
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
        "body_hash_stored",
        "terminal_output_body_included",
        "stdout_body_included",
        "stderr_body_included",
        "traceback_body_included",
    ):
        if false_key in operation_receipt and operation_receipt.get(false_key) is not False:
            blockers.append(f"pmn_op11_operation_receipt_{false_key}_not_false")
    for source_flag in (
        "row_created_by_helper",
        "row_created_for_unit_test",
        "row_is_synthetic_contract_fixture",
        "historical_row_reused",
        "helper_default_rows_materialized_as_actual_here",
        "unit_test_rows_materialized_as_actual_here",
        "synthetic_contract_rows_materialized_as_actual_here",
        "historical_rows_materialized_as_actual_here",
    ):
        if operation_receipt.get(source_flag) is True:
            blockers.append(f"pmn_op11_operation_receipt_{source_flag}_cannot_be_actual")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake(
    *,
    actual_24_case_human_review_execution_protocol_state_capture: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP11 body-free actual operation receipt intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op10 = actual_24_case_human_review_execution_protocol_state_capture
    if op10 is None:
        op10 = build_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture(
            reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
            actual_review_execution_state_capture_bodyfree=actual_review_execution_state_capture_bodyfree,
            packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
            packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
            packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op11_operation_receipt_blockers(op10, actual_operation_receipt_bodyfree)
    ready = not blockers
    receipt_received = isinstance(actual_operation_receipt_bodyfree, Mapping)
    leak_detected = bool(
        receipt_received
        and (
            _scan_forbidden_payload_key_paths(actual_operation_receipt_bodyfree)
            or any("body" in blocker or "question" in blocker or "path" in blocker or "hash" in blocker or "terminal" in blocker for blocker in blockers)
        )
    )
    status_ref = (
        P7_R54_AHR_POST_MN11_PMN_OP11_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_BY_LEAK_STATUS_REF
        if leak_detected
        else P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_STATUS_REF
    )
    reason_refs = list(P7_R54_AHR_POST_MN11_PMN_OP11_READY_REASON_REFS) if ready else blockers
    receipt = actual_operation_receipt_bodyfree or {}
    receipt_ref = _clean_ref(receipt.get("operation_receipt_ref") if receipt_received else "", default="", max_length=220)
    reviewer_ref = _clean_ref(receipt.get("reviewer_person_ref") if receipt_received else op10.get("reviewer_person_ref") if isinstance(op10, Mapping) else "", default="", max_length=180)
    started_ref = _clean_ref(receipt.get("review_started_at_bucket_ref") if receipt_received else "", default="", max_length=220)
    completed_ref = _clean_ref(receipt.get("review_completed_at_bucket_ref") if receipt_received else "", default="", max_length=220)
    reviewed_count = _safe_int(receipt.get("reviewed_case_count") if receipt_received else 0)
    selection_count = _safe_int(receipt.get("selection_row_count") if receipt_received else 0)
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP11_IMPLEMENTED_STEPS if ready else tuple(op10.get("implemented_steps") or P7_R54_AHR_POST_MN11_PMN_OP10_IMPLEMENTED_STEPS) if isinstance(op10, Mapping) else P7_R54_AHR_POST_MN11_PMN_OP09_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP11_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op10.get("not_yet_implemented_steps") or P7_R54_AHR_POST_MN11_PMN_OP10_NOT_YET_IMPLEMENTED_STEPS) if isinstance(op10, Mapping) else P7_R54_AHR_POST_MN11_PMN_OP09_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP11_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op10_schema_version": _clean_ref(op10.get("schema_version") if isinstance(op10, Mapping) else "", default="op10_schema_missing", max_length=220),
        "op10_material_ref": _clean_ref(op10.get("material_id") if isinstance(op10, Mapping) else "", default="op10_material_missing", max_length=220),
        "op10_next_required_step": _clean_ref(op10.get("next_required_step") if isinstance(op10, Mapping) else "", default="op10_next_required_step_missing", max_length=220),
        "op10_review_execution_state_capture_ready": bool(isinstance(op10, Mapping) and op10.get("review_execution_state_capture_ready") is True),
        "op10_review_state_ref": _clean_ref(op10.get("review_state_ref") if isinstance(op10, Mapping) else "", default="", max_length=180),
        "op10_reviewer_person_ref": _clean_ref(op10.get("reviewer_person_ref") if isinstance(op10, Mapping) else "", default="", max_length=180),
        "op10_review_started_at_bucket_ref": _clean_ref(op10.get("review_started_at_bucket_ref") if isinstance(op10, Mapping) else "", default="", max_length=220),
        "op10_review_completed_at_bucket_ref": _clean_ref(op10.get("review_completed_at_bucket_ref") if isinstance(op10, Mapping) else "", default="", max_length=220),
        "op10_reviewed_case_count": _safe_int(op10.get("reviewed_case_count") if isinstance(op10, Mapping) else 0),
        "op10_selection_row_count": _safe_int(op10.get("selection_row_count") if isinstance(op10, Mapping) else 0),
        "operation_receipt_status_ref": status_ref,
        "operation_receipt_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_STATUS_REFS),
        "operation_receipt_accepted": ready,
        "operation_receipt_reason_refs": reason_refs,
        "operation_receipt_blocker_refs": blockers,
        "operation_receipt_blocker_ref_count": len(blockers),
        "operation_receipt_intake_ref": P7_R54_AHR_POST_MN11_PMN_OP11_OPERATION_RECEIPT_INTAKE_REF if ready else "",
        "operation_receipt_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_OPERATION_RECEIPT_FIELD_REFS),
        "operation_receipt_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_OPERATION_RECEIPT_FIELD_REFS),
        "operation_receipt_ref": receipt_ref,
        "operation_receipt_ref_present": bool(receipt_ref) and not _ref_has_local_path_shape(receipt_ref),
        "operation_receipt_ref_is_bodyfree_ref": bool(receipt_ref) and not _ref_has_local_path_shape(receipt_ref),
        "operation_receipt_ref_has_local_path_shape": _ref_has_local_path_shape(receipt_ref),
        "reviewer_person_ref": reviewer_ref,
        "reviewer_person_ref_present": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_is_bodyfree_ref": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_has_local_path_shape": _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_matches_op10": bool(isinstance(op10, Mapping) and reviewer_ref == op10.get("reviewer_person_ref")),
        "reviewer_is_person": bool(receipt_received and receipt.get("reviewer_is_person") is True),
        "reviewer_person_confirmed": bool(receipt_received and receipt.get("reviewer_person_confirmed") is True),
        "reviewer_local_only_read_receipt_present": bool(receipt_received and receipt.get("reviewer_local_only_read_receipt_present") is True),
        "review_started_at_bucket_ref": started_ref,
        "review_started_at_bucket_ref_present": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_at_bucket_ref_is_bodyfree_ref": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_at_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(started_ref),
        "review_started_at_bucket_ref_matches_op10": bool(isinstance(op10, Mapping) and started_ref == op10.get("review_started_at_bucket_ref")),
        "review_completed_at_bucket_ref": completed_ref,
        "review_completed_at_bucket_ref_present": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_at_bucket_ref_is_bodyfree_ref": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_at_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(completed_ref),
        "review_completed_at_bucket_ref_matches_op10": bool(isinstance(op10, Mapping) and completed_ref == op10.get("review_completed_at_bucket_ref")),
        "reviewed_case_count": reviewed_count,
        "required_reviewed_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "reviewed_case_count_is_24": reviewed_count == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "reviewed_case_count_matches_op10": bool(isinstance(op10, Mapping) and reviewed_count == op10.get("reviewed_case_count")),
        "selection_row_count": selection_count,
        "required_selection_row_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "selection_row_count_is_24": selection_count == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "selection_row_count_matches_op10": bool(isinstance(op10, Mapping) and selection_count == op10.get("selection_row_count")),
        "local_only": bool(receipt_received and receipt.get("local_only") is True),
        "must_not_export": bool(receipt_received and receipt.get("must_not_export") is True),
        "selection_only": bool(receipt_received and receipt.get("selection_only") is True),
        "actual_source_ref": _clean_ref(receipt.get("actual_source_ref") if receipt_received else "", default="", max_length=220),
        "actual_source_allowed_ref": P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF,
        "actual_source_guard_passed": bool(receipt_received and receipt.get("actual_source_ref") == P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF),
        "operation_receipt_bodyfree_only": True,
        "operation_receipt_received_here": receipt_received,
        "operation_receipt_intaked_here": ready,
        "operation_receipt_confirms_actual_person_local_only_review": ready,
        "actual_human_review_executed_by_person": ready,
        "actual_human_review_run_here": False,
        "sanitized_review_result_rows_intake_required_next": ready,
        "sanitized_review_result_rows_created_here": False,
        "rating_rows_created_here": False,
        "question_need_observation_rows_created_here": False,
        "disposal_receipt_created_here": False,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "raw_input_included": False,
        "returned_emlis_body_included": False,
        "history_body_included": False,
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
        "pmn_op11_does_not_create_sanitized_rows_or_rating_rows_or_question_rows": True,
        "pmn_op11_does_not_create_disposal_receipt": True,
        "pmn_op11_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP11 actual operation receipt intake")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP11_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP11 actual operation receipt intake")
    blockers = list(data.get("operation_receipt_blocker_refs") or [])
    ready = not blockers
    leak_blocker_fragments = ("body", "question", "path", "hash", "terminal", "stdout", "stderr", "traceback")
    leak_detected = any(any(fragment in blocker for fragment in leak_blocker_fragments) for blocker in blockers)
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP11_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_BY_LEAK_STATUS_REF if leak_detected else P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_STATUS_REF
    if data.get("operation_receipt_status_ref") != expected_status or data.get("operation_receipt_accepted") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 status/accepted changed")
    if tuple(data.get("operation_receipt_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 allowed status refs changed")
    for count_field, list_field in (("operation_receipt_blocker_ref_count", "operation_receipt_blocker_refs"), ("operation_receipt_required_field_ref_count", "operation_receipt_required_field_refs")):
        if data.get(count_field) != len(data.get(list_field) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP11 {count_field} changed")
    for key in ("operation_receipt_bodyfree_only", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171", "pmn_op11_does_not_create_sanitized_rows_or_rating_rows_or_question_rows", "pmn_op11_does_not_create_disposal_receipt", "pmn_op11_does_not_start_p8_p6_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP11 required true field changed: {key}")
    for key in ("actual_human_review_run_here", "sanitized_review_result_rows_created_here", "rating_rows_created_here", "question_need_observation_rows_created_here", "disposal_receipt_created_here", "raw_input_included", "returned_emlis_body_included", "history_body_included", "comment_text_body_included", "reviewer_free_text_included", "reviewer_notes_body_included", "question_text_included", "draft_question_text_included", "packet_content_included", "body_full_packet_content_included", "local_absolute_path_included", "body_hash_included", "terminal_output_body_included", "stdout_body_included", "stderr_body_included", "traceback_body_included"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP11 required false field promoted: {key}")
    if tuple(data.get("operation_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP11_REQUIRED_OPERATION_RECEIPT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 required receipt fields changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 actual review basis changed")
    if data.get("required_reviewed_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("required_selection_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 required counts changed")
    if ready:
        if data.get("op10_review_execution_state_capture_ready") is not True or data.get("op10_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 ready receipt requires OP10 ready next step")
        for key in ("operation_receipt_received_here", "operation_receipt_intaked_here", "operation_receipt_confirms_actual_person_local_only_review", "actual_human_review_executed_by_person", "sanitized_review_result_rows_intake_required_next", "operation_receipt_ref_present", "operation_receipt_ref_is_bodyfree_ref", "reviewer_person_ref_present", "reviewer_person_ref_is_bodyfree_ref", "reviewer_person_ref_matches_op10", "reviewer_is_person", "reviewer_person_confirmed", "reviewer_local_only_read_receipt_present", "review_started_at_bucket_ref_present", "review_started_at_bucket_ref_is_bodyfree_ref", "review_started_at_bucket_ref_matches_op10", "review_completed_at_bucket_ref_present", "review_completed_at_bucket_ref_is_bodyfree_ref", "review_completed_at_bucket_ref_matches_op10", "reviewed_case_count_is_24", "reviewed_case_count_matches_op10", "selection_row_count_is_24", "selection_row_count_matches_op10", "local_only", "must_not_export", "selection_only", "actual_source_guard_passed"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP11 ready field changed: {key}")
        if data.get("actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF or data.get("actual_source_allowed_ref") != P7_R54_AHR_POST_MN11_PMN_OP11_ALLOWED_ACTUAL_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 actual source ref changed")
        if data.get("operation_receipt_ref_has_local_path_shape") is not False or data.get("reviewer_person_ref_has_local_path_shape") is not False or data.get("review_started_at_bucket_ref_has_local_path_shape") is not False or data.get("review_completed_at_bucket_ref_has_local_path_shape") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 refs must not be paths")
        if data.get("reviewed_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("selection_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 counts must be 24")
        if data.get("operation_receipt_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP11_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP11_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 next step changed")
    else:
        if data.get("operation_receipt_intaked_here") is not False or data.get("sanitized_review_result_rows_intake_required_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 blocked receipt promoted next intake")
        if data.get("actual_human_review_executed_by_person") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 blocked receipt promoted human review execution")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP11 blocked next step changed")
    return True


def build_p7_r54_ahr_post_mn11_actual_operation_scope_no_touch_no_promotion_boundary_freeze_bodyfree(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze(
        review_session_id=review_session_id
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_scope_no_touch_no_promotion_boundary_freeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op00_scope_no_touch_no_promotion_boundary_freeze_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_mn11_manual_decision_intake_basis_confirmation_bodyfree(
    *,
    scope_no_touch_no_promotion_boundary_freeze: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation(
        scope_no_touch_no_promotion_boundary_freeze=scope_no_touch_no_promotion_boundary_freeze,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_mn11_manual_decision_intake_basis_confirmation_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op01_mn11_manual_decision_intake_basis_confirmation_contract(data)



def build_p7_r54_ahr_post_mn11_actual_operation_existing_op_ex_mn_support_material_inventory_bodyfree(
    *,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory(
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_existing_op_ex_mn_support_material_inventory_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op02_existing_op_ex_mn_support_material_inventory_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_review_session_envelope_actual_source_guard_freeze_bodyfree(
    *,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze(
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_review_session_envelope_actual_source_guard_freeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op03_review_session_envelope_actual_source_guard_freeze_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_local_only_preflight_explicit_allow_boundary_bodyfree(
    *,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    local_review_root_ref: Any = None,
    explicit_allow_ref: Any = None,
    retention_policy_ref: Any = None,
    disposal_policy_ref: Any = None,
    export_denylist_policy_ref: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary(
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
        local_review_root_ref=local_review_root_ref,
        explicit_allow_ref=explicit_allow_ref,
        retention_policy_ref=retention_policy_ref,
        disposal_policy_ref=disposal_policy_ref,
        export_denylist_policy_ref=export_denylist_policy_ref,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_local_only_preflight_explicit_allow_boundary_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op04_local_only_preflight_explicit_allow_boundary_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_24_case_manifest_refreeze_bodyfree(
    *,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze(
        local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_24_case_manifest_refreeze_bodyfree_contract(
    data: Mapping[str, Any]
) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op05_24_case_manifest_refreeze_contract(data)



def build_p7_r54_ahr_post_mn11_actual_operation_body_full_packet_generation_request_bodyfree_builder(
    *,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder(
        case_manifest_refreeze=case_manifest_refreeze,
        local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_body_full_packet_generation_request_bodyfree_builder_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op06_body_full_packet_generation_request_bodyfree_builder_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_packet_generation_local_operation_receipt_boundary_bodyfree(
    *,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary(
        packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
        case_manifest_refreeze=case_manifest_refreeze,
        local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_packet_generation_local_operation_receipt_boundary_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op07_packet_generation_local_operation_receipt_boundary_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_packet_completeness_export_denylist_scan_bodyfree(
    *,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
        packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
        packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
        case_manifest_refreeze=case_manifest_refreeze,
        local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_packet_completeness_export_denylist_scan_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op08_packet_completeness_export_denylist_scan_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_reviewer_person_boundary_selection_only_form_freeze_bodyfree(
    *,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze(
        packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
        packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
        packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
        packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
        case_manifest_refreeze=case_manifest_refreeze,
        local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_reviewer_person_boundary_selection_only_form_freeze_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op09_reviewer_person_boundary_selection_only_form_freeze_contract(data)





def build_p7_r54_ahr_post_mn11_actual_operation_actual_24_case_human_review_execution_protocol_state_capture_bodyfree(
    *,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture(
        reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
        actual_review_execution_state_capture_bodyfree=actual_review_execution_state_capture_bodyfree,
        packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
        packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
        packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
        packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
        case_manifest_refreeze=case_manifest_refreeze,
        local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_actual_24_case_human_review_execution_protocol_state_capture_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op10_actual_24_case_human_review_execution_protocol_state_capture_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_actual_operation_receipt_intake_bodyfree(
    *,
    actual_24_case_human_review_execution_protocol_state_capture: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake(
        actual_24_case_human_review_execution_protocol_state_capture=actual_24_case_human_review_execution_protocol_state_capture,
        actual_operation_receipt_bodyfree=actual_operation_receipt_bodyfree,
        reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
        actual_review_execution_state_capture_bodyfree=actual_review_execution_state_capture_bodyfree,
        packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
        packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
        packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
        packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
        case_manifest_refreeze=case_manifest_refreeze,
        local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
        review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
        existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
        mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
        mn11_manual_decision_material=mn11_manual_decision_material,
        review_session_id=review_session_id,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_actual_operation_receipt_intake_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(data)


# ---------------------------------------------------------------------------
# PMN-OP12 / PMN-OP13 sanitized row intake and rating normalization
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op12_sanitized_review_result_rows_intake_provenance_guard.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op12_sanitized_review_result_row.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op13_rating_row_normalization_threshold_summary.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op13_rating_row.bodyfree.v1"
)

P7_R54_AHR_POST_MN11_PMN_OP12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:13]
)
P7_R54_AHR_POST_MN11_PMN_OP12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[13:]
)
P7_R54_AHR_POST_MN11_PMN_OP13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:14]
)
P7_R54_AHR_POST_MN11_PMN_OP13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[14:]
)

P7_R54_AHR_POST_MN11_PMN_OP12_READY_STATUS_REF: Final = (
    "PMN_OP12_SANITIZED_REVIEW_RESULT_ROWS_INTAKED_PROVENANCE_GUARDED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_STATUS_REF: Final = (
    "PMN_OP12_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "PMN_OP12_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_BLOCKED_BY_BODY_LEAK"
)
P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP12_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF: Final = (
    "actual_person_selection_only_rows_local_review"
)
P7_R54_AHR_POST_MN11_PMN_OP12_FORBIDDEN_ROW_SOURCE_REFS: Final[tuple[str, ...]] = (
    "helper_default_fixture_rows",
    "unit_test_contract_rows",
    "synthetic_bodyfree_rows",
    "synthetic_contract_fixture_rows",
    "historical_ahr_260_83_256_169_rows",
    "historical_cs_262_84_257_170_rows",
    "ai_inferred_review_rows",
    "rows_without_person_read_receipt",
)
P7_R54_AHR_POST_MN11_PMN_OP12_INTAKE_REF: Final = (
    "postmn11_actual_sanitized_review_result_rows_intake_provenance_guard_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP12_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op11_actual_operation_receipt_accepted_bodyfree",
    "twenty_four_actual_person_selection_only_rows_received_bodyfree",
    "row_provenance_flags_block_helper_unit_test_synthetic_historical_sources",
    "rows_match_24_case_manifest_and_six_axis_contract",
    "rows_contain_no_body_question_path_hash_or_terminal_output",
    "rating_row_normalization_required_next_without_downstream_promotion",
)
P7_R54_AHR_POST_MN11_PMN_OP12_LABEL_CONNECTION_QUALITY_REFS: Final[tuple[str, ...]] = (
    "label_connection_present_natural",
    "label_connection_weak_or_generic",
    "label_connection_overread_or_creepy",
    "current_input_overridden_by_history",
    "history_correctly_not_used_due_to_boundary",
    "history_present_but_tier_not_allowed_correctly_blocked",
    "insufficient_material_to_rate_label_connection",
)
P7_R54_AHR_POST_MN11_PMN_OP12_SAFE_DISPLAY_CHECK_REFS: Final[tuple[str, ...]] = (
    "no_overclaim_or_unearned_certainty",
    "no_creepy_history_overread",
    "no_self_blame_amplification",
    "no_boundary_history_line_leak",
    "no_tier_policy_leak",
    "no_body_leak",
    "no_question_text_leak",
    "safe_display_risk_detected",
)
P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
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
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_implementation_spec_finalized_here",
)
P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "operation_receipt_ref",
    "review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "reviewer_person_ref",
    "reviewed_at_bucket_ref",
    "axis_scores",
    "axis_score_count",
    "axis_pass_flags",
    "verdict_ref",
    "label_connection_quality_ref",
    "safe_display_check_refs",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class_ref",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "row_source_ref",
    "row_created_by_helper",
    "row_created_for_unit_test",
    "row_is_synthetic_contract_fixture",
    "historical_row_reused",
    "selection_only",
    "selection_only_row",
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op11_schema_version", "op11_material_ref", "op11_next_required_step", "op11_operation_receipt_status_ref",
    "op11_operation_receipt_accepted", "op11_operation_receipt_ref", "op11_reviewer_person_ref",
    "op11_actual_human_review_executed_by_person", "op11_reviewed_case_count", "op11_selection_row_count",
    "sanitized_review_result_rows_intake_status_ref", "sanitized_review_result_rows_intake_allowed_status_refs",
    "sanitized_review_result_rows_intake_ready", "sanitized_review_result_rows_intake_reason_refs",
    "sanitized_review_result_rows_intake_blocker_refs", "sanitized_review_result_rows_intake_blocker_ref_count",
    "sanitized_review_result_rows_intake_ref", "sanitized_review_result_rows_required_field_refs",
    "sanitized_review_result_rows_required_field_ref_count", "sanitized_review_result_rows_input_present",
    "received_sanitized_review_result_row_count", "sanitized_review_result_row_count", "required_sanitized_review_result_row_count",
    "sanitized_review_result_row_count_is_24", "review_result_rows", "review_result_row_refs", "review_result_row_ref_count",
    "case_ref_ids", "case_ref_id_count", "case_ref_ids_unique", "blind_case_ids", "blind_case_id_count", "blind_case_ids_unique",
    "packet_ref_ids", "packet_ref_id_count", "packet_ref_ids_unique", "reviewed_at_bucket_refs", "reviewed_at_bucket_ref_count",
    "reviewed_at_bucket_refs_present", "axis_refs", "axis_ref_count", "axis_score_count_per_row", "axis_target_thresholds",
    "verdict_option_refs", "label_connection_quality_option_refs", "safe_display_check_option_refs", "sanitized_reason_id_option_refs",
    "readfeel_blocker_id_option_refs", "execution_blocker_id_option_refs", "question_need_primary_class_option_refs",
    "ambiguity_kind_option_refs", "one_question_fit_option_refs", "repair_required_option_refs", "plan_candidate_flag_refs",
    "rows_match_24_case_manifest", "rows_bodyfree_only", "rows_selection_only", "rows_have_actual_person_selection_only_provenance",
    "rows_have_required_axis_scores", "rows_have_allowed_verdict_refs", "rows_have_allowed_label_connection_refs",
    "rows_have_allowed_safe_display_refs", "rows_have_allowed_question_observation_refs", "rows_have_no_body_or_question_or_path_or_hash",
    "sanitized_selection_only_result_rows_intaken_here", "actual_sanitized_review_result_rows_intaken_here",
    "actual_human_review_executed_by_person", "actual_selection_rows_created_here", "actual_sanitized_review_result_rows_created_here",
    "rating_row_normalization_allowed_next", "question_text_materialized_here", "draft_question_text_materialized_here",
    "p8_question_implementation_spec_finalized_here", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "pmn_op12_does_not_run_actual_human_review_here",
    "pmn_op12_does_not_create_rating_rows_question_rows_or_disposal", "pmn_op12_does_not_start_p8_p6_r52_or_release",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP13_READY_STATUS_REF: Final = (
    "PMN_OP13_RATING_ROWS_NORMALIZED_THRESHOLD_SUMMARY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_STATUS_REF: Final = (
    "PMN_OP13_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP13_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP13_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op13_rating_row_normalization_threshold_summary_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP13_RATING_NORMALIZATION_REF: Final = (
    "postmn11_actual_rating_row_normalization_threshold_summary_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP13_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op12_sanitized_review_result_rows_intaked_bodyfree",
    "twenty_four_rating_rows_normalized_from_actual_sanitized_rows",
    "six_axis_threshold_summary_calculated_bodyfree",
    "rating_rows_are_decision_material_only_not_p5_final",
    "question_need_observation_row_normalization_required_next_without_p8_start",
)
P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_RATING_ROW_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "operation_receipt_ref",
    "rating_row_ref",
    "rating_source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "axis_scores",
    "axis_score_count",
    "axis_pass_flags",
    "below_target_axis_refs",
    "all_axis_target_passed",
    "verdict_ref",
    "label_connection_quality_ref",
    "safe_display_check_refs",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "row_source_ref",
    "rating_decision_material_only",
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op12_schema_version", "op12_material_ref", "op12_next_required_step", "op12_sanitized_rows_ready",
    "op12_sanitized_review_result_row_count", "operation_receipt_ref", "reviewer_person_ref",
    "rating_row_normalization_status_ref", "rating_row_normalization_allowed_status_refs", "rating_row_normalization_ready",
    "rating_row_normalization_reason_refs", "rating_row_normalization_blocker_refs", "rating_row_normalization_blocker_ref_count",
    "rating_row_normalization_ref", "rating_row_required_field_refs", "rating_row_required_field_ref_count",
    "rating_row_count", "required_rating_row_count", "rating_row_count_is_24", "rating_rows", "rating_row_refs", "rating_row_ref_count",
    "axis_refs", "axis_ref_count", "axis_score_count_per_row", "axis_target_thresholds", "axis_target_thresholds_present",
    "average_axis_scores", "below_target_axis_refs", "below_target_axis_ref_count", "axis_pass_summary", "all_axis_target_passed",
    "label_connection_distribution_ref", "safe_display_distribution_ref", "verdict_distribution_ref", "readfeel_blocker_count_ref",
    "execution_blocker_count_ref", "actual_rating_rows_materialized_from_actual_rows", "rating_rows_normalized_here",
    "rating_decision_material_only", "p5_final_allowed", "p5_finalization_still_manual_decision_required",
    "question_need_observation_row_normalization_allowed_next", "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "pmn_op13_does_not_create_question_rows_or_disposal", "pmn_op13_does_not_start_p5_p6_p8_r52_or_release",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _pmn_op12_expected_manifest_by_case() -> dict[str, dict[str, str]]:
    case_matrix = op.build_p7_r48_p5_first_formal_review_case_matrix(
        material_id="p7_r54_ahr_post_mn11_pmn_op12_r48_first_formal_case_matrix_basis"
    )
    op.assert_p7_r48_p5_first_formal_review_case_matrix_contract(case_matrix)
    expected: dict[str, dict[str, str]] = {}
    for raw_row in case_matrix.get("case_rows") or []:
        row = raw_row if isinstance(raw_row, Mapping) else {}
        case_ref = _clean_ref(row.get("case_ref_id"), default="", max_length=180)
        if case_ref:
            expected[case_ref] = {
                "case_ref_id": case_ref,
                "blind_case_id": _clean_ref(row.get("blind_case_id"), default="", max_length=180),
                "packet_ref_id": _clean_ref(row.get("packet_ref_id"), default="", max_length=180),
            }
    return expected


def _pmn_op12_clean_ref_list(value: Any, *, allowed: Sequence[str], max_length: int = 180) -> tuple[list[str], bool]:
    if value is None:
        return [], True
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        return [], False
    cleaned: list[str] = []
    valid = True
    for raw in value:
        ref = _clean_ref(raw, default="", max_length=max_length)
        if not ref or ref not in allowed:
            valid = False
        else:
            cleaned.append(ref)
    return cleaned, valid


def _pmn_op12_clean_plan_candidate_flags(value: Any) -> tuple[dict[str, bool], bool]:
    raw = value if isinstance(value, Mapping) else {}
    valid = isinstance(value, Mapping)
    flags = {key: bool(raw.get(key, False)) for key in P7_R54_AHR_POST_MN11_PMN_OP09_PLAN_CANDIDATE_FLAG_REFS}
    if raw.get("p8_implementation_spec_finalized_here") is True:
        valid = False
    flags["p8_implementation_spec_finalized_here"] = False
    return flags, valid


def _pmn_op12_clean_axis_scores(value: Any) -> tuple[dict[str, float], dict[str, bool], bool]:
    scores_input = value if isinstance(value, Mapping) else {}
    valid = isinstance(value, Mapping)
    scores: dict[str, float] = {}
    pass_flags: dict[str, bool] = {}
    for axis_ref in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS:
        raw_score = scores_input.get(axis_ref) if isinstance(scores_input, Mapping) else None
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            score = 0.0
            valid = False
        if score < 0.0 or score > 1.0:
            valid = False
            score = min(max(score, 0.0), 1.0)
        scores[axis_ref] = round(score, 4)
        pass_flags[axis_ref] = score >= P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS[axis_ref]
    return scores, pass_flags, valid


def _pmn_op12_validate_sanitized_rows(
    rows: Sequence[Any],
    *,
    review_session_id: str,
    operation_receipt_ref: str,
    reviewer_person_ref: str,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    blockers: list[str] = []
    sanitized_rows: list[dict[str, Any]] = []
    expected_manifest = _pmn_op12_expected_manifest_by_case()
    if len(rows) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op12_sanitized_review_result_row_count_not_24")
    seen_case_refs: set[str] = set()
    seen_blind_ids: set[str] = set()
    seen_packet_refs: set[str] = set()
    row_refs: list[str] = []
    reviewed_bucket_refs: list[str] = []
    counters = {
        "helper_rows": 0,
        "unit_test_rows": 0,
        "synthetic_rows": 0,
        "historical_rows": 0,
        "session_mismatch": 0,
        "operation_receipt_mismatch": 0,
        "reviewer_mismatch": 0,
        "manifest_mismatch": 0,
        "forbidden_payload_key": 0,
        "forbidden_body_flag": 0,
        "path_shape_ref": 0,
        "selection_only_false": 0,
        "body_free_false": 0,
        "axis_invalid": 0,
        "option_invalid": 0,
    }
    for index, raw in enumerate(rows, start=1):
        if not isinstance(raw, Mapping):
            blockers.append("pmn_op12_sanitized_row_not_mapping")
            continue
        missing = [field for field in P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS if field not in raw]
        if missing:
            blockers.append("pmn_op12_sanitized_row_required_fields_missing")
        if raw.get("schema_version") != P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
            blockers.append("pmn_op12_sanitized_row_schema_version_not_allowed")
        if _scan_forbidden_payload_key_paths(raw, path=f"sanitized_row_{index}"):
            counters["forbidden_payload_key"] += 1
            blockers.append("pmn_op12_sanitized_row_contains_forbidden_body_question_path_hash_or_terminal_key")
        if any(raw.get(flag) is not False for flag in P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS if flag in raw):
            counters["forbidden_body_flag"] += 1
            blockers.append("pmn_op12_sanitized_row_bodyfree_false_flag_not_false")
        row_ref = _clean_ref(raw.get("review_result_row_ref"), default=f"postmn11_actual_review_result_row_{index:03d}", max_length=180)
        case_ref = _clean_ref(raw.get("case_ref_id"), default="", max_length=180)
        blind_id = _clean_ref(raw.get("blind_case_id"), default="", max_length=180)
        packet_ref = _clean_ref(raw.get("packet_ref_id"), default="", max_length=180)
        reviewed_ref = _clean_ref(raw.get("reviewed_at_bucket_ref"), default="", max_length=180)
        if _ref_has_local_path_shape(row_ref) or _ref_has_local_path_shape(reviewed_ref):
            counters["path_shape_ref"] += 1
            blockers.append("pmn_op12_sanitized_row_ref_or_reviewed_bucket_must_not_be_path")
        row_refs.append(row_ref)
        reviewed_bucket_refs.append(reviewed_ref)
        seen_case_refs.add(case_ref)
        seen_blind_ids.add(blind_id)
        seen_packet_refs.add(packet_ref)
        expected = expected_manifest.get(case_ref)
        if not expected or blind_id != expected.get("blind_case_id") or packet_ref != expected.get("packet_ref_id"):
            counters["manifest_mismatch"] += 1
            blockers.append("pmn_op12_sanitized_row_manifest_id_mismatch")
        if _clean_ref(raw.get("review_session_id"), default="", max_length=220) != review_session_id:
            counters["session_mismatch"] += 1
            blockers.append("pmn_op12_sanitized_row_review_session_id_mismatch")
        if _clean_ref(raw.get("operation_receipt_ref"), default="", max_length=220) != operation_receipt_ref:
            counters["operation_receipt_mismatch"] += 1
            blockers.append("pmn_op12_sanitized_row_operation_receipt_ref_mismatch")
        if _clean_ref(raw.get("reviewer_person_ref"), default="", max_length=220) != reviewer_person_ref:
            counters["reviewer_mismatch"] += 1
            blockers.append("pmn_op12_sanitized_row_reviewer_person_ref_mismatch")
        source_ref = _clean_ref(raw.get("row_source_ref"), default="", max_length=180)
        if source_ref != P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF:
            blockers.append("pmn_op12_sanitized_row_source_ref_not_actual_person_selection_only_rows_local_review")
        if source_ref in P7_R54_AHR_POST_MN11_PMN_OP12_FORBIDDEN_ROW_SOURCE_REFS:
            blockers.append("pmn_op12_sanitized_row_source_ref_forbidden")
        if raw.get("row_created_by_helper") is not False:
            counters["helper_rows"] += 1
            blockers.append("pmn_op12_sanitized_row_created_by_helper_cannot_be_actual")
        if raw.get("row_created_for_unit_test") is not False:
            counters["unit_test_rows"] += 1
            blockers.append("pmn_op12_sanitized_row_created_for_unit_test_cannot_be_actual")
        if raw.get("row_is_synthetic_contract_fixture") is not False:
            counters["synthetic_rows"] += 1
            blockers.append("pmn_op12_sanitized_row_is_synthetic_contract_fixture_cannot_be_actual")
        if raw.get("historical_row_reused") is not False:
            counters["historical_rows"] += 1
            blockers.append("pmn_op12_sanitized_row_historical_row_reused_cannot_be_actual")
        if raw.get("selection_only") is not True or raw.get("selection_only_row") is not True:
            counters["selection_only_false"] += 1
            blockers.append("pmn_op12_sanitized_row_selection_only_not_true")
        if raw.get("body_free") is not True:
            counters["body_free_false"] += 1
            blockers.append("pmn_op12_sanitized_row_body_free_not_true")
        axis_scores, axis_pass_flags, axis_valid = _pmn_op12_clean_axis_scores(raw.get("axis_scores"))
        if not axis_valid or _safe_int(raw.get("axis_score_count")) != len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS):
            counters["axis_invalid"] += 1
            blockers.append("pmn_op12_sanitized_row_axis_scores_missing_or_out_of_range")
        input_axis_pass_flags = raw.get("axis_pass_flags") if isinstance(raw.get("axis_pass_flags"), Mapping) else {}
        if any(bool(input_axis_pass_flags.get(axis)) != axis_pass_flags[axis] for axis in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS):
            counters["axis_invalid"] += 1
            blockers.append("pmn_op12_sanitized_row_axis_pass_flags_mismatch")
        verdict_ref = _clean_ref(raw.get("verdict_ref"), default="", max_length=80)
        label_ref = _clean_ref(raw.get("label_connection_quality_ref"), default="", max_length=180)
        question_class_ref = _clean_ref(raw.get("question_need_primary_class_ref"), default="", max_length=180)
        one_question_fit_ref = _clean_ref(raw.get("one_question_fit_ref"), default="", max_length=180)
        safe_refs, safe_valid = _pmn_op12_clean_ref_list(raw.get("safe_display_check_refs"), allowed=P7_R54_AHR_POST_MN11_PMN_OP12_SAFE_DISPLAY_CHECK_REFS)
        reason_refs, reason_valid = _pmn_op12_clean_ref_list(raw.get("sanitized_reason_ids"), allowed=P7_R54_AHR_POST_MN11_PMN_OP09_SANITIZED_REASON_ID_OPTION_REFS)
        readfeel_blockers, readfeel_valid = _pmn_op12_clean_ref_list(raw.get("readfeel_blocker_ids"), allowed=P7_R54_AHR_POST_MN11_PMN_OP09_READFEEL_BLOCKER_ID_OPTION_REFS)
        execution_blockers, execution_valid = _pmn_op12_clean_ref_list(raw.get("execution_blocker_ids"), allowed=P7_R54_AHR_POST_MN11_PMN_OP09_EXECUTION_BLOCKER_ID_OPTION_REFS)
        ambiguity_refs, ambiguity_valid = _pmn_op12_clean_ref_list(raw.get("ambiguity_kind_refs"), allowed=P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS)
        repair_refs, repair_valid = _pmn_op12_clean_ref_list(raw.get("repair_required_refs"), allowed=P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS)
        plan_flags, plan_valid = _pmn_op12_clean_plan_candidate_flags(raw.get("plan_candidate_flags"))
        if (
            verdict_ref not in P7_R54_AHR_POST_MN11_PMN_OP09_VERDICT_OPTION_REFS
            or label_ref not in P7_R54_AHR_POST_MN11_PMN_OP12_LABEL_CONNECTION_QUALITY_REFS
            or question_class_ref not in P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS
            or one_question_fit_ref not in P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS
            or not all([safe_valid, reason_valid, readfeel_valid, execution_valid, ambiguity_valid, repair_valid, plan_valid])
        ):
            counters["option_invalid"] += 1
            blockers.append("pmn_op12_sanitized_row_allowed_option_ref_invalid")
        sanitized_row = {
            "schema_version": P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "review_result_row_ref": row_ref,
            "case_ref_id": case_ref,
            "blind_case_id": blind_id,
            "packet_ref_id": packet_ref,
            "reviewer_person_ref": reviewer_person_ref,
            "reviewed_at_bucket_ref": reviewed_ref,
            "axis_scores": axis_scores,
            "axis_score_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS),
            "axis_pass_flags": axis_pass_flags,
            "verdict_ref": verdict_ref,
            "label_connection_quality_ref": label_ref,
            "safe_display_check_refs": safe_refs,
            "sanitized_reason_ids": reason_refs,
            "readfeel_blocker_ids": readfeel_blockers,
            "execution_blocker_ids": execution_blockers,
            "question_need_primary_class_ref": question_class_ref,
            "ambiguity_kind_refs": ambiguity_refs,
            "one_question_fit_ref": one_question_fit_ref,
            "repair_required_refs": repair_refs,
            "plan_candidate_flags": plan_flags,
            "row_source_ref": P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF,
            "row_created_by_helper": False,
            "row_created_for_unit_test": False,
            "row_is_synthetic_contract_fixture": False,
            "historical_row_reused": False,
            "selection_only": True,
            "selection_only_row": True,
            **{flag: False for flag in P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS},
            "body_free": True,
        }
        sanitized_rows.append(sanitized_row)
    blockers = list(dict.fromkeys(blockers))
    stats = {
        "review_result_row_refs": sorted(set(row_refs)),
        "case_ref_ids": sorted(seen_case_refs),
        "blind_case_ids": sorted(seen_blind_ids),
        "packet_ref_ids": sorted(seen_packet_refs),
        "reviewed_at_bucket_refs": sorted(set(ref for ref in reviewed_bucket_refs if ref)),
        "case_ref_ids_unique": len(seen_case_refs) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "blind_case_ids_unique": len(seen_blind_ids) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "packet_ref_ids_unique": len(seen_packet_refs) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "reviewed_at_bucket_refs_present": len([ref for ref in reviewed_bucket_refs if ref]) == len(rows) and bool(rows),
        "rows_match_24_case_manifest": counters["manifest_mismatch"] == 0 and len(seen_case_refs) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "rows_bodyfree_only": counters["forbidden_payload_key"] == 0 and counters["forbidden_body_flag"] == 0 and counters["body_free_false"] == 0 and bool(rows),
        "rows_selection_only": counters["selection_only_false"] == 0 and bool(rows),
        "rows_have_actual_person_selection_only_provenance": counters["helper_rows"] == 0 and counters["unit_test_rows"] == 0 and counters["synthetic_rows"] == 0 and counters["historical_rows"] == 0 and bool(rows),
        "rows_have_required_axis_scores": counters["axis_invalid"] == 0 and bool(rows),
        "rows_have_allowed_options": counters["option_invalid"] == 0 and bool(rows),
        "rows_have_no_body_or_question_or_path_or_hash": counters["forbidden_payload_key"] == 0 and counters["forbidden_body_flag"] == 0 and counters["path_shape_ref"] == 0 and bool(rows),
    }
    return sanitized_rows if not blockers else [], blockers, stats


def _pmn_op12_blockers(op11: Mapping[str, Any] | None, rows: Sequence[Any] | None) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    blockers: list[str] = []
    if not isinstance(op11, Mapping):
        return ["pmn_op12_actual_operation_receipt_intake_missing"], [], {}
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(op11)
    except ValueError:
        blockers.append("pmn_op12_op11_actual_operation_receipt_intake_invalid")
    if op11.get("operation_receipt_accepted") is not True:
        blockers.append("pmn_op12_op11_operation_receipt_not_accepted")
    if op11.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF:
        blockers.append("pmn_op12_op11_next_step_not_sanitized_rows_intake")
    if op11.get("sanitized_review_result_rows_intake_required_next") is not True:
        blockers.append("pmn_op12_op11_sanitized_rows_not_required_next")
    if op11.get("actual_human_review_executed_by_person") is not True:
        blockers.append("pmn_op12_op11_actual_human_review_executed_by_person_missing")
    if _scan_forbidden_payload_key_paths(op11):
        blockers.append("pmn_op12_op11_forbidden_body_question_path_hash_key_detected")
    if rows is None:
        blockers.append("pmn_op12_sanitized_review_result_rows_not_received")
        return list(dict.fromkeys(blockers)), [], {}
    rows_list = list(rows)
    sanitized_rows, row_blockers, stats = _pmn_op12_validate_sanitized_rows(
        rows_list,
        review_session_id=_clean_ref(op11.get("review_session_id"), default=P7_R54_AHR_POST_MN11_DEFAULT_REVIEW_SESSION_ID, max_length=220),
        operation_receipt_ref=_clean_ref(op11.get("operation_receipt_ref"), default="", max_length=220),
        reviewer_person_ref=_clean_ref(op11.get("reviewer_person_ref"), default="", max_length=220),
    )
    blockers.extend(row_blockers)
    return list(dict.fromkeys(blockers)), sanitized_rows, stats


def build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    actual_24_case_human_review_execution_protocol_state_capture: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP12 body-free sanitized review result rows intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op11 = actual_operation_receipt_intake
    if op11 is None:
        op11 = build_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake(
            actual_24_case_human_review_execution_protocol_state_capture=actual_24_case_human_review_execution_protocol_state_capture,
            actual_operation_receipt_bodyfree=actual_operation_receipt_bodyfree,
            reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
            actual_review_execution_state_capture_bodyfree=actual_review_execution_state_capture_bodyfree,
            packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
            packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
            packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers, sanitized_rows, stats = _pmn_op12_blockers(op11, sanitized_review_result_rows_bodyfree)
    ready = not blockers
    rows_present = sanitized_review_result_rows_bodyfree is not None
    rows_input_count = len(list(sanitized_review_result_rows_bodyfree or []))
    leak_detected = bool(any("body" in blocker or "question" in blocker or "path" in blocker or "hash" in blocker or "terminal" in blocker for blocker in blockers))
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP12_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP11_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP11_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_20260630",
        "review_session_id": _clean_ref(op11.get("review_session_id") if isinstance(op11, Mapping) else session_id, default=session_id, max_length=220),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op11_schema_version": _clean_ref(op11.get("schema_version") if isinstance(op11, Mapping) else "", default="op11_schema_missing", max_length=220),
        "op11_material_ref": _clean_ref(op11.get("material_id") if isinstance(op11, Mapping) else "", default="op11_material_missing", max_length=220),
        "op11_next_required_step": _clean_ref(op11.get("next_required_step") if isinstance(op11, Mapping) else "", default="op11_next_missing", max_length=220),
        "op11_operation_receipt_status_ref": _clean_ref(op11.get("operation_receipt_status_ref") if isinstance(op11, Mapping) else "", default="op11_receipt_status_missing", max_length=220),
        "op11_operation_receipt_accepted": bool(isinstance(op11, Mapping) and op11.get("operation_receipt_accepted") is True),
        "op11_operation_receipt_ref": _clean_ref(op11.get("operation_receipt_ref") if isinstance(op11, Mapping) else "", default="", max_length=220),
        "op11_reviewer_person_ref": _clean_ref(op11.get("reviewer_person_ref") if isinstance(op11, Mapping) else "", default="", max_length=220),
        "op11_actual_human_review_executed_by_person": bool(isinstance(op11, Mapping) and op11.get("actual_human_review_executed_by_person") is True),
        "op11_reviewed_case_count": _safe_int(op11.get("reviewed_case_count") if isinstance(op11, Mapping) else 0),
        "op11_selection_row_count": _safe_int(op11.get("selection_row_count") if isinstance(op11, Mapping) else 0),
        "sanitized_review_result_rows_intake_status_ref": P7_R54_AHR_POST_MN11_PMN_OP12_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_BY_LEAK_STATUS_REF if leak_detected else P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_STATUS_REF,
        "sanitized_review_result_rows_intake_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_STATUS_REFS),
        "sanitized_review_result_rows_intake_ready": ready,
        "sanitized_review_result_rows_intake_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP12_READY_REASON_REFS) if ready else [],
        "sanitized_review_result_rows_intake_blocker_refs": blockers,
        "sanitized_review_result_rows_intake_blocker_ref_count": len(blockers),
        "sanitized_review_result_rows_intake_ref": P7_R54_AHR_POST_MN11_PMN_OP12_INTAKE_REF,
        "sanitized_review_result_rows_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS),
        "sanitized_review_result_rows_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS),
        "sanitized_review_result_rows_input_present": rows_present,
        "received_sanitized_review_result_row_count": rows_input_count,
        "sanitized_review_result_row_count": len(sanitized_rows),
        "required_sanitized_review_result_row_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count_is_24": len(sanitized_rows) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "review_result_rows": sanitized_rows,
        "review_result_row_refs": stats.get("review_result_row_refs", []),
        "review_result_row_ref_count": len(stats.get("review_result_row_refs", [])),
        "case_ref_ids": stats.get("case_ref_ids", []),
        "case_ref_id_count": len(stats.get("case_ref_ids", [])),
        "case_ref_ids_unique": bool(stats.get("case_ref_ids_unique", False)),
        "blind_case_ids": stats.get("blind_case_ids", []),
        "blind_case_id_count": len(stats.get("blind_case_ids", [])),
        "blind_case_ids_unique": bool(stats.get("blind_case_ids_unique", False)),
        "packet_ref_ids": stats.get("packet_ref_ids", []),
        "packet_ref_id_count": len(stats.get("packet_ref_ids", [])),
        "packet_ref_ids_unique": bool(stats.get("packet_ref_ids_unique", False)),
        "reviewed_at_bucket_refs": stats.get("reviewed_at_bucket_refs", []),
        "reviewed_at_bucket_ref_count": len(stats.get("reviewed_at_bucket_refs", [])),
        "reviewed_at_bucket_refs_present": bool(stats.get("reviewed_at_bucket_refs_present", False)),
        "axis_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS),
        "axis_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS) if ready else 0,
        "axis_target_thresholds": dict(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS),
        "verdict_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_VERDICT_OPTION_REFS),
        "label_connection_quality_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP12_LABEL_CONNECTION_QUALITY_REFS),
        "safe_display_check_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP12_SAFE_DISPLAY_CHECK_REFS),
        "sanitized_reason_id_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_SANITIZED_REASON_ID_OPTION_REFS),
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_READFEEL_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "question_need_primary_class_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_PLAN_CANDIDATE_FLAG_REFS),
        "rows_match_24_case_manifest": bool(stats.get("rows_match_24_case_manifest", False)) and ready,
        "rows_bodyfree_only": bool(stats.get("rows_bodyfree_only", False)) and ready,
        "rows_selection_only": bool(stats.get("rows_selection_only", False)) and ready,
        "rows_have_actual_person_selection_only_provenance": bool(stats.get("rows_have_actual_person_selection_only_provenance", False)) and ready,
        "rows_have_required_axis_scores": bool(stats.get("rows_have_required_axis_scores", False)) and ready,
        "rows_have_allowed_verdict_refs": bool(stats.get("rows_have_allowed_options", False)) and ready,
        "rows_have_allowed_label_connection_refs": bool(stats.get("rows_have_allowed_options", False)) and ready,
        "rows_have_allowed_safe_display_refs": bool(stats.get("rows_have_allowed_options", False)) and ready,
        "rows_have_allowed_question_observation_refs": bool(stats.get("rows_have_allowed_options", False)) and ready,
        "rows_have_no_body_or_question_or_path_or_hash": bool(stats.get("rows_have_no_body_or_question_or_path_or_hash", False)) and ready,
        "sanitized_selection_only_result_rows_intaken_here": ready,
        "actual_sanitized_review_result_rows_intaken_here": ready,
        "actual_human_review_executed_by_person": ready,
        "actual_selection_rows_created_here": False,
        "actual_sanitized_review_result_rows_created_here": False,
        "rating_row_normalization_allowed_next": ready,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op12_does_not_run_actual_human_review_here": True,
        "pmn_op12_does_not_create_rating_rows_question_rows_or_disposal": True,
        "pmn_op12_does_not_start_p8_p6_r52_or_release": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP12 sanitized rows intake")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP12 sanitized rows intake")
    ready = bool(data.get("sanitized_review_result_rows_intake_ready"))
    blockers = list(data.get("sanitized_review_result_rows_intake_blocker_refs") or [])
    leak_detected = any(any(fragment in blocker for fragment in ("body", "question", "path", "hash", "terminal")) for blocker in blockers)
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP12_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_BY_LEAK_STATUS_REF if leak_detected else P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_STATUS_REF
    if data.get("sanitized_review_result_rows_intake_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 status changed")
    if tuple(data.get("sanitized_review_result_rows_intake_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 allowed status refs changed")
    if data.get("sanitized_review_result_rows_intake_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 blocker count changed")
    for key in ("current_actual_review_basis_remains_264_85_258_171", "pmn_op12_does_not_run_actual_human_review_here", "pmn_op12_does_not_create_rating_rows_question_rows_or_disposal", "pmn_op12_does_not_start_p8_p6_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP12 required true field changed: {key}")
    for key in ("actual_selection_rows_created_here", "actual_sanitized_review_result_rows_created_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "question_text_materialized_here", "draft_question_text_materialized_here", "p8_question_implementation_spec_finalized_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP12 required false field promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 basis changed")
    if tuple(data.get("sanitized_review_result_rows_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 required row fields changed")
    if ready:
        for key in ("op11_operation_receipt_accepted", "op11_actual_human_review_executed_by_person", "sanitized_review_result_row_count_is_24", "rows_match_24_case_manifest", "rows_bodyfree_only", "rows_selection_only", "rows_have_actual_person_selection_only_provenance", "rows_have_required_axis_scores", "rows_have_allowed_verdict_refs", "rows_have_allowed_label_connection_refs", "rows_have_allowed_safe_display_refs", "rows_have_allowed_question_observation_refs", "rows_have_no_body_or_question_or_path_or_hash", "sanitized_selection_only_result_rows_intaken_here", "actual_sanitized_review_result_rows_intaken_here", "actual_human_review_executed_by_person", "rating_row_normalization_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP12 ready field changed: {key}")
        if data.get("op11_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 OP11 next step changed")
        if data.get("sanitized_review_result_rows_intake_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP12_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 ready reasons changed")
        if data.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or len(data.get("review_result_rows") or []) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 row count must be 24")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP12_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 next step changed")
        for row in data.get("review_result_rows") or []:
            _required_fields_present(row, required=P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP12 sanitized row")
            if row.get("schema_version") != P7_R54_AHR_POST_MN11_PMN_OP12_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 row schema changed")
            if row.get("row_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 row source changed")
            if any(row.get(flag) is not False for flag in ("row_created_by_helper", "row_created_for_unit_test", "row_is_synthetic_contract_fixture", "historical_row_reused")):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 provenance flag promoted")
            if any(row.get(flag) is not False for flag in P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 row body-free false flag changed")
            if row.get("selection_only") is not True or row.get("selection_only_row") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 row body-free/selection flags changed")
    else:
        if data.get("sanitized_selection_only_result_rows_intaken_here") is not False or data.get("actual_sanitized_review_result_rows_intaken_here") is not False or data.get("rating_row_normalization_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 blocked material promoted rows")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP12 blocked next step changed")
    return True


def _pmn_op13_distribution(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                ref = _clean_ref(item, default="", max_length=180)
                if ref:
                    counts[ref] = counts.get(ref, 0) + 1
        else:
            ref = _clean_ref(value, default="", max_length=180)
            if ref:
                counts[ref] = counts.get(ref, 0) + 1
    return dict(sorted(counts.items()))


def _pmn_op13_normalize_rating_rows(rows: Sequence[Mapping[str, Any]], *, review_session_id: str, operation_receipt_ref: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rating_rows: list[dict[str, Any]] = []
    axis_totals = {axis: 0.0 for axis in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS}
    below_target_refs: set[str] = set()
    axis_pass_summary = {axis: {"passed": 0, "below_target": 0} for axis in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS}
    for index, row in enumerate(rows, start=1):
        scores = row.get("axis_scores") if isinstance(row.get("axis_scores"), Mapping) else {}
        axis_scores = {axis: round(float(scores.get(axis, 0.0)), 4) for axis in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS}
        axis_pass_flags = {
            axis: axis_scores[axis] >= P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS[axis]
            for axis in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS
        }
        below = [axis for axis, passed in axis_pass_flags.items() if not passed]
        for axis in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS:
            axis_totals[axis] += axis_scores[axis]
            axis_pass_summary[axis]["passed" if axis_pass_flags[axis] else "below_target"] += 1
        below_target_refs.update(below)
        rating_rows.append({
            "schema_version": P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "rating_row_ref": f"postmn11_actual_rating_row_{index:03d}_bodyfree",
            "rating_source_review_result_row_ref": row.get("review_result_row_ref"),
            "case_ref_id": row.get("case_ref_id"),
            "blind_case_id": row.get("blind_case_id"),
            "packet_ref_id": row.get("packet_ref_id"),
            "axis_scores": axis_scores,
            "axis_score_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS),
            "axis_pass_flags": axis_pass_flags,
            "below_target_axis_refs": below,
            "all_axis_target_passed": not below,
            "verdict_ref": row.get("verdict_ref"),
            "label_connection_quality_ref": row.get("label_connection_quality_ref"),
            "safe_display_check_refs": list(row.get("safe_display_check_refs") or []),
            "readfeel_blocker_ids": list(row.get("readfeel_blocker_ids") or []),
            "execution_blocker_ids": list(row.get("execution_blocker_ids") or []),
            "row_source_ref": P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF,
            "rating_decision_material_only": True,
            "body_free": True,
        })
    row_count = len(rows) or 1
    average_scores = {axis: round(axis_totals[axis] / row_count, 4) for axis in P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS} if rows else {}
    summary = {
        "average_axis_scores": average_scores,
        "below_target_axis_refs": sorted(below_target_refs),
        "axis_pass_summary": axis_pass_summary,
        "all_axis_target_passed": not below_target_refs and bool(rows),
        "label_connection_distribution_ref": _pmn_op13_distribution(rows, "label_connection_quality_ref"),
        "safe_display_distribution_ref": _pmn_op13_distribution(rows, "safe_display_check_refs"),
        "verdict_distribution_ref": _pmn_op13_distribution(rows, "verdict_ref"),
        "readfeel_blocker_count_ref": _pmn_op13_distribution(rows, "readfeel_blocker_ids"),
        "execution_blocker_count_ref": _pmn_op13_distribution(rows, "execution_blocker_ids"),
    }
    return rating_rows, summary


def _pmn_op13_blockers(op12: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op12, Mapping):
        return ["pmn_op13_sanitized_review_result_rows_intake_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(op12)
    except ValueError:
        blockers.append("pmn_op13_op12_sanitized_review_result_rows_intake_invalid")
    if op12.get("sanitized_review_result_rows_intake_ready") is not True:
        blockers.append("pmn_op13_op12_sanitized_review_result_rows_not_ready")
    if op12.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF:
        blockers.append("pmn_op13_op12_next_step_not_rating_row_normalization")
    if op12.get("rating_row_normalization_allowed_next") is not True:
        blockers.append("pmn_op13_op12_rating_row_normalization_not_allowed_next")
    if op12.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op13_op12_sanitized_review_result_row_count_not_24")
    if _scan_forbidden_payload_key_paths(op12):
        blockers.append("pmn_op13_op12_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
    *,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    actual_24_case_human_review_execution_protocol_state_capture: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP13 body-free rating row normalization material."""

    session_id = _safe_review_session_id(review_session_id)
    op12 = sanitized_review_result_rows_intake
    if op12 is None:
        op12 = build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=actual_operation_receipt_intake,
            sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
            actual_24_case_human_review_execution_protocol_state_capture=actual_24_case_human_review_execution_protocol_state_capture,
            actual_operation_receipt_bodyfree=actual_operation_receipt_bodyfree,
            reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
            actual_review_execution_state_capture_bodyfree=actual_review_execution_state_capture_bodyfree,
            packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
            packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
            packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    blockers = _pmn_op13_blockers(op12)
    ready = not blockers
    rows = list(op12.get("review_result_rows") or []) if isinstance(op12, Mapping) and ready else []
    session_id = _clean_ref(op12.get("review_session_id") if isinstance(op12, Mapping) else session_id, default=session_id, max_length=220)
    operation_receipt_ref = _clean_ref(op12.get("op11_operation_receipt_ref") if isinstance(op12, Mapping) else "", default="", max_length=220)
    rating_rows, summary = _pmn_op13_normalize_rating_rows(rows, review_session_id=session_id, operation_receipt_ref=operation_receipt_ref) if ready else ([], {})
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP13_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP12_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP13_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP12_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op12_schema_version": _clean_ref(op12.get("schema_version") if isinstance(op12, Mapping) else "", default="op12_schema_missing", max_length=220),
        "op12_material_ref": _clean_ref(op12.get("material_id") if isinstance(op12, Mapping) else "", default="op12_material_missing", max_length=220),
        "op12_next_required_step": _clean_ref(op12.get("next_required_step") if isinstance(op12, Mapping) else "", default="op12_next_missing", max_length=220),
        "op12_sanitized_rows_ready": bool(isinstance(op12, Mapping) and op12.get("sanitized_review_result_rows_intake_ready") is True),
        "op12_sanitized_review_result_row_count": _safe_int(op12.get("sanitized_review_result_row_count") if isinstance(op12, Mapping) else 0),
        "operation_receipt_ref": operation_receipt_ref,
        "reviewer_person_ref": _clean_ref(op12.get("op11_reviewer_person_ref") if isinstance(op12, Mapping) else "", default="", max_length=220),
        "rating_row_normalization_status_ref": P7_R54_AHR_POST_MN11_PMN_OP13_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_STATUS_REF,
        "rating_row_normalization_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP13_ALLOWED_STATUS_REFS),
        "rating_row_normalization_ready": ready,
        "rating_row_normalization_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP13_READY_REASON_REFS) if ready else [],
        "rating_row_normalization_blocker_refs": blockers,
        "rating_row_normalization_blocker_ref_count": len(blockers),
        "rating_row_normalization_ref": P7_R54_AHR_POST_MN11_PMN_OP13_RATING_NORMALIZATION_REF,
        "rating_row_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_RATING_ROW_FIELD_REFS),
        "rating_row_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_RATING_ROW_FIELD_REFS),
        "rating_row_count": len(rating_rows),
        "required_rating_row_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "rating_row_count_is_24": len(rating_rows) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "rating_rows": rating_rows,
        "rating_row_refs": [str(row.get("rating_row_ref")) for row in rating_rows],
        "rating_row_ref_count": len(rating_rows),
        "axis_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS),
        "axis_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS) if ready else 0,
        "axis_target_thresholds": dict(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS),
        "axis_target_thresholds_present": True,
        "average_axis_scores": summary.get("average_axis_scores", {}),
        "below_target_axis_refs": summary.get("below_target_axis_refs", []),
        "below_target_axis_ref_count": len(summary.get("below_target_axis_refs", [])),
        "axis_pass_summary": summary.get("axis_pass_summary", {}),
        "all_axis_target_passed": bool(summary.get("all_axis_target_passed", False)),
        "label_connection_distribution_ref": summary.get("label_connection_distribution_ref", {}),
        "safe_display_distribution_ref": summary.get("safe_display_distribution_ref", {}),
        "verdict_distribution_ref": summary.get("verdict_distribution_ref", {}),
        "readfeel_blocker_count_ref": summary.get("readfeel_blocker_count_ref", {}),
        "execution_blocker_count_ref": summary.get("execution_blocker_count_ref", {}),
        "actual_rating_rows_materialized_from_actual_rows": ready,
        "rating_rows_normalized_here": ready,
        "rating_decision_material_only": True,
        "p5_final_allowed": False,
        "p5_finalization_still_manual_decision_required": True,
        "question_need_observation_row_normalization_allowed_next": ready,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op13_does_not_create_question_rows_or_disposal": True,
        "pmn_op13_does_not_start_p5_p6_p8_r52_or_release": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP13 rating row normalization")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP13 rating row normalization")
    ready = bool(data.get("rating_row_normalization_ready"))
    blockers = list(data.get("rating_row_normalization_blocker_refs") or [])
    if data.get("rating_row_normalization_status_ref") != (P7_R54_AHR_POST_MN11_PMN_OP13_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 status changed")
    if tuple(data.get("rating_row_normalization_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP13_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 allowed status refs changed")
    if data.get("rating_row_normalization_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 blocker count changed")
    for key in ("axis_target_thresholds_present", "rating_decision_material_only", "p5_finalization_still_manual_decision_required", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171", "pmn_op13_does_not_create_question_rows_or_disposal", "pmn_op13_does_not_start_p5_p6_p8_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP13 required true field changed: {key}")
    for key in ("p5_final_allowed", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "p6_start_allowed", "p8_start_allowed", "r52_actual_execution_confirmed", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP13 required false field promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 basis changed")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_RATING_ROW_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 required rating row fields changed")
    if data.get("axis_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS) or data.get("axis_target_thresholds") != P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 axis contract changed")
    if ready:
        for key in ("op12_sanitized_rows_ready", "rating_row_normalization_ready", "rating_row_count_is_24", "actual_rating_rows_materialized_from_actual_rows", "rating_rows_normalized_here", "question_need_observation_row_normalization_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP13 ready field changed: {key}")
        if data.get("op12_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 OP12 next step changed")
        if data.get("rating_row_normalization_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP13_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 ready reasons changed")
        if data.get("rating_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or len(data.get("rating_rows") or []) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 rating row count must be 24")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP13_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 next step changed")
        for row in data.get("rating_rows") or []:
            _required_fields_present(row, required=P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_RATING_ROW_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP13 rating row")
            if row.get("schema_version") != P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 rating row schema changed")
            if row.get("row_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP12_ALLOWED_ROW_SOURCE_REF or row.get("rating_decision_material_only") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 rating row source/body-free changed")
            if _scan_forbidden_payload_key_paths(row, path="pmn_op13_rating_row"):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 rating row leaked forbidden payload key")
    else:
        if data.get("rating_rows_normalized_here") is not False or data.get("actual_rating_rows_materialized_from_actual_rows") is not False or data.get("question_need_observation_row_normalization_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 blocked material promoted rating rows")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP13 blocked next step changed")
    return True



# ---------------------------------------------------------------------------
# PMN-OP14 / PMN-OP15 blocker classification and question observation rows
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_LABEL_CONNECTION_SAFE_DISPLAY_BLOCKER_CLASSIFICATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op14_readfeel_label_connection_safe_display_blocker_classification.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CLASSIFICATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op14_blocker_classification_row.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op15_question_need_observation_row_normalization.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op15_question_need_observation_row.bodyfree.v1"
)

P7_R54_AHR_POST_MN11_PMN_OP14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:15]
)
P7_R54_AHR_POST_MN11_PMN_OP14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[15:]
)
P7_R54_AHR_POST_MN11_PMN_OP15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:16]
)
P7_R54_AHR_POST_MN11_PMN_OP15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[16:]
)

P7_R54_AHR_POST_MN11_PMN_OP14_READY_STATUS_REF: Final = (
    "PMN_OP14_READFEEL_LABEL_CONNECTION_SAFE_DISPLAY_BLOCKERS_CLASSIFIED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_STATUS_REF: Final = (
    "PMN_OP14_READFEEL_LABEL_CONNECTION_SAFE_DISPLAY_BLOCKER_CLASSIFICATION_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP14_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP14_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP14_CLASSIFICATION_REF: Final = (
    "postmn11_readfeel_label_connection_safe_display_blocker_classification_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP14_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op13_rating_rows_normalized_bodyfree",
    "op12_question_observation_source_refs_available_bodyfree",
    "readfeel_label_connection_safe_display_and_blocker_refs_classified_bodyfree",
    "p5_p4_operation_safe_display_blockers_not_escaped_to_p8_candidate",
    "question_need_observation_row_normalization_required_next_without_p8_start",
)
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_STATUS_OPEN_REF: Final = "open_bodyfree_product_or_operation_blocker"
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "readfeel_blocker",
    "execution_blocker",
    "repair_required",
    "below_target_axis",
    "safe_display_risk",
    "inconclusive_material",
    "verdict_blocker",
)
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CATEGORY_REFS: Final[tuple[str, ...]] = (
    "no_blocker",
    "p5_readfeel_repair_required",
    "p5_history_connection_weak",
    "p5_creepy_or_overclaim_risk",
    "p5_self_blame_amplification_risk",
    "p5_safe_display_risk",
    "p4_current_only_surface_repair_required",
    "operation_blocked_missing_receipt",
    "operation_blocked_body_leak",
    "operation_blocked_question_text",
    "operation_blocked_disposal_missing",
    "operation_blocked_no_touch_violation",
    "inconclusive_insufficient_material",
)
P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_ROUTE_REF: Final = "P5_READFEEL_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_POST_MN11_PMN_OP14_P4_ROUTE_REF: Final = "P4_CURRENT_ONLY_SURFACE_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_POST_MN11_PMN_OP14_OPERATION_ROUTE_REF: Final = "R54_OPERATION_BLOCKER_REPAIR_BEFORE_EVIDENCE_COMPLETE"
P7_R54_AHR_POST_MN11_PMN_OP14_INCONCLUSIVE_ROUTE_REF: Final = "R54_INCONCLUSIVE_MATERIAL_REVIEW_REQUIRED"
P7_R54_AHR_POST_MN11_PMN_OP14_CLEAN_ROUTE_REF: Final = "NO_BLOCKER_CONTINUE_TO_QUESTION_NEED_OBSERVATION_NORMALIZATION"
P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = {
    "history_connection_weak": "p5_history_connection_weak",
    "history_line_creepy_or_overread": "p5_creepy_or_overclaim_risk",
    "current_input_overridden_by_history": "p5_creepy_or_overclaim_risk",
    "overclaim_or_unearned_certainty": "p5_creepy_or_overclaim_risk",
    "self_blame_amplified": "p5_self_blame_amplification_risk",
    "shallow_repeat_or_generic": "p5_readfeel_repair_required",
    "wants_less_input_or_no_accumulation": "p5_readfeel_repair_required",
    "boundary_history_line_leak": "p5_creepy_or_overclaim_risk",
    "safe_display_risk": "p5_safe_display_risk",
}
P7_R54_AHR_POST_MN11_PMN_OP14_EXECUTION_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = {
    "packet_missing": "operation_blocked_missing_receipt",
    "packet_not_local_only": "operation_blocked_missing_receipt",
    "case_manifest_incomplete": "operation_blocked_missing_receipt",
    "reviewer_not_assigned": "operation_blocked_missing_receipt",
    "reviewer_selection_incomplete": "operation_blocked_missing_receipt",
    "forbidden_body_leak": "operation_blocked_body_leak",
    "question_text_leak": "operation_blocked_question_text",
    "disposal_missing": "operation_blocked_disposal_missing",
    "no_touch_violation": "operation_blocked_no_touch_violation",
    "source_guard_missing": "operation_blocked_missing_receipt",
}
P7_R54_AHR_POST_MN11_PMN_OP14_REPAIR_CATEGORY_BY_REF: Final[dict[str, str]] = {
    "emlis_readfeel_repair_required": "p5_readfeel_repair_required",
    "p5_surface_repair_required": "p5_readfeel_repair_required",
    "gate_boundary_repair_required": "p5_readfeel_repair_required",
    "p4_current_surface_repair_required": "p4_current_only_surface_repair_required",
    "safe_display_repair_required": "p5_safe_display_risk",
}
P7_R54_AHR_POST_MN11_PMN_OP14_BELOW_TARGET_AXIS_CATEGORY_BY_REF: Final[dict[str, str]] = {
    "history_connection_naturalness": "p5_history_connection_weak",
    "creepy_absence": "p5_creepy_or_overclaim_risk",
    "overclaim_absence": "p5_creepy_or_overclaim_risk",
    "self_blame_non_amplification": "p5_self_blame_amplification_risk",
    "wants_more_input_or_accumulation": "p5_readfeel_repair_required",
    "non_shallow_repeat": "p5_readfeel_repair_required",
}
P7_R54_AHR_POST_MN11_PMN_OP14_SAFE_DISPLAY_RISK_CHECK_REFS: Final[tuple[str, ...]] = (
    "safe_display_risk_detected",
)
P7_R54_AHR_POST_MN11_PMN_OP14_P8_MATERIAL_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_AHR_POST_MN11_PMN_OP14_P8_MATERIAL_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "fits_one_question",
)
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blocker_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "blocker_kind_ref",
    "blocker_category_ref",
    "blocker_id_ref",
    "blocker_status_ref",
    "routes_to_ref",
    "p8_material_candidate_blocked",
    "safe_display_risk_not_question_candidate",
    "body_free",
    *P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_MN11_PMN_OP14_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op13_schema_version", "op13_material_ref", "op13_next_required_step", "op13_rating_row_normalization_ready",
    "op13_rating_row_count", "op13_question_need_observation_row_normalization_allowed_next",
    "op13_actual_rating_rows_materialized_from_actual_rows", "op12_schema_version", "op12_material_ref", "op12_sanitized_rows_ready",
    "op12_sanitized_review_result_row_count", "readfeel_label_connection_safe_display_blocker_classification_status_ref",
    "readfeel_label_connection_safe_display_blocker_classification_allowed_status_refs",
    "readfeel_label_connection_safe_display_blocker_classification_ready",
    "readfeel_label_connection_safe_display_blocker_classification_reason_refs",
    "readfeel_label_connection_safe_display_blocker_classification_blocker_refs",
    "readfeel_label_connection_safe_display_blocker_classification_blocker_ref_count",
    "blocker_classification_ref", "blocker_row_required_field_refs", "blocker_row_required_field_ref_count",
    "required_case_count", "source_rating_row_count", "source_rating_row_refs", "source_rating_row_ref_count",
    "source_review_result_row_count", "case_ref_ids", "case_ref_id_count", "case_ref_ids_unique",
    "blocker_rows", "blocker_row_count", "blocker_row_refs", "blocker_row_ref_count", "blocker_kind_refs", "blocker_kind_counts",
    "blocker_category_refs", "blocker_category_counts", "readfeel_blocker_row_count", "execution_blocker_row_count",
    "repair_required_blocker_row_count", "below_target_axis_blocker_row_count", "safe_display_blocker_row_count",
    "inconclusive_blocker_row_count", "verdict_blocker_row_count", "readfeel_blocker_id_counts", "execution_blocker_id_counts",
    "repair_required_ref_counts", "below_target_axis_ref_counts", "safe_display_risk_case_refs", "safe_display_risk_case_count",
    "label_connection_distribution_ref", "safe_display_distribution_ref", "verdict_distribution_ref", "no_blocker_case_refs",
    "no_blocker_case_count", "p5_repair_required_case_refs", "p5_repair_required_case_count", "p4_current_only_repair_required_case_refs",
    "p4_current_only_repair_required_case_count", "operation_blocked_case_refs", "operation_blocked_case_count", "safe_display_blocked_case_refs",
    "safe_display_blocked_case_count", "inconclusive_case_refs", "inconclusive_case_count", "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only", "p8_material_candidate_blocked_by_blocker_case_refs",
    "p8_material_candidate_blocked_by_blocker_case_count", "rows_bodyfree_only", "rows_have_no_question_text",
    "p5_p4_operation_readfeel_safe_display_blockers_not_escaped_to_p8_candidate", "safe_display_risk_not_question_candidate",
    "readfeel_label_connection_safe_display_blockers_classified_here", "actual_rating_rows_materialized_from_actual_rows",
    "actual_rating_rows_materialized_here", "actual_human_review_executed_by_person", "actual_human_review_run_here",
    "question_need_observation_normalization_allowed_next", "actual_question_need_observation_rows_materialized_here",
    "p5_finalization_blocked_here", "p6_p8_release_promotion_blocked_here", "r52_reintake_claim_blocked_here",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "pmn_op14_does_not_create_question_rows_or_disposal", "pmn_op14_does_not_start_p5_p6_p8_r52_or_release",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP15_READY_STATUS_REF: Final = (
    "PMN_OP15_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_STATUS_REF: Final = (
    "PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP15_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP15_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op15_question_need_observation_row_normalization_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP15_NORMALIZATION_REF: Final = (
    "postmn11_question_need_observation_row_normalization_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP15_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op14_readfeel_label_connection_safe_display_blockers_classified_bodyfree",
    "twenty_four_question_need_observation_rows_normalized_from_actual_sanitized_rows",
    "p8_material_candidates_remain_candidate_only_and_blocker_guarded",
    "question_text_trigger_storage_and_p8_spec_not_materialized",
    "rating_question_consistency_guard_required_next_without_p8_start",
)
P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "operation_receipt_ref",
    "question_need_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "question_need_primary_class_ref",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "p8_material_candidate_only",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_material_candidate_blocked_by_blocker",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_trigger_logic_materialized_here",
    "question_answer_storage_materialized_here",
    "p8_implementation_spec_finalized_here",
    "p8_start_allowed",
    "body_free",
    *P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_MN11_PMN_OP15_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op14_schema_version", "op14_material_ref", "op14_next_required_step", "op14_blocker_classification_ready",
    "op14_question_need_observation_normalization_allowed_next", "op12_schema_version", "op12_material_ref", "op12_sanitized_rows_ready",
    "op12_sanitized_review_result_row_count", "operation_receipt_ref", "question_need_observation_row_normalization_status_ref",
    "question_need_observation_row_normalization_allowed_status_refs", "question_need_observation_row_normalization_ready",
    "question_need_observation_row_normalization_reason_refs", "question_need_observation_row_normalization_step_blocker_refs",
    "question_need_observation_row_normalization_step_blocker_ref_count", "question_need_observation_row_normalization_ref",
    "question_need_observation_row_required_field_refs", "question_need_observation_row_required_field_ref_count",
    "source_sanitized_review_result_row_count", "required_question_need_observation_row_count", "question_need_observation_row_count",
    "question_need_observation_row_count_is_24", "question_need_observation_rows", "question_need_observation_row_refs",
    "question_need_observation_row_ref_count", "case_ref_ids", "case_ref_id_count", "case_ref_ids_unique", "blind_case_ids",
    "blind_case_id_count", "blind_case_ids_unique", "packet_ref_ids", "packet_ref_id_count", "packet_ref_ids_unique",
    "question_need_primary_class_option_refs", "question_need_primary_class_option_ref_count", "ambiguity_kind_option_refs",
    "ambiguity_kind_option_ref_count", "one_question_fit_option_refs", "one_question_fit_option_ref_count", "repair_required_option_refs",
    "repair_required_option_ref_count", "question_need_primary_class_counts", "ambiguity_kind_counts", "one_question_fit_counts",
    "repair_required_ref_counts", "p8_material_candidate_case_refs_bodyfree_only", "p8_material_candidate_case_count_bodyfree_only",
    "plus_single_question_candidate_case_refs_bodyfree_only", "plus_single_question_candidate_case_count_bodyfree_only",
    "premium_deep_dive_candidate_case_refs_bodyfree_only", "premium_deep_dive_candidate_case_count_bodyfree_only",
    "p8_material_candidate_blocked_by_blocker_case_refs", "p8_material_candidate_blocked_by_blocker_case_count",
    "question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_materialized_here",
    "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here", "p8_start_allowed",
    "question_need_observation_rows_normalized_here", "actual_question_need_observation_rows_materialized_from_actual_rows",
    "actual_question_need_observation_rows_materialized_here", "actual_review_evidence_complete_from_real_review_still_false",
    "p8_material_candidate_only_is_not_p8_start", "pmn_op15_does_not_create_disposal_or_evidence_complete",
    "pmn_op15_does_not_start_p5_p6_p8_r52_or_release", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_mn11_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _pmn_op14_clean_ref_list(value: Any, *, max_length: int = 180) -> list[str]:
    if value is None or isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        return []
    cleaned: list[str] = []
    for item in value:
        ref = _clean_ref(item, default="", max_length=max_length)
        if ref:
            cleaned.append(ref)
    return cleaned


def _pmn_op14_count_nested_string_values(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for ref in _pmn_op14_clean_ref_list(row.get(key)):
            counts[ref] = counts.get(ref, 0) + 1
    return dict(sorted(counts.items()))


def _pmn_op14_case_refs_for_categories(rows: Sequence[Mapping[str, Any]], categories: set[str]) -> list[str]:
    refs = {
        _clean_ref(row.get("case_ref_id"), default="", max_length=180)
        for row in rows
        if _clean_ref(row.get("blocker_category_ref"), default="", max_length=180) in categories
    }
    return sorted(ref for ref in refs if ref)


def _pmn_op14_routes_to(category_ref: str) -> str:
    if category_ref == "no_blocker":
        return P7_R54_AHR_POST_MN11_PMN_OP14_CLEAN_ROUTE_REF
    if category_ref == "p4_current_only_surface_repair_required":
        return P7_R54_AHR_POST_MN11_PMN_OP14_P4_ROUTE_REF
    if category_ref.startswith("operation_blocked_"):
        return P7_R54_AHR_POST_MN11_PMN_OP14_OPERATION_ROUTE_REF
    if category_ref == "inconclusive_insufficient_material":
        return P7_R54_AHR_POST_MN11_PMN_OP14_INCONCLUSIVE_ROUTE_REF
    return P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_ROUTE_REF


def _pmn_op14_make_blocker_row(
    *,
    seq: int,
    source_row: Mapping[str, Any],
    source_question_row: Mapping[str, Any] | None,
    review_session_id: str,
    blocker_kind_ref: str,
    blocker_category_ref: str,
    blocker_id_ref: str,
) -> dict[str, Any]:
    question_row = source_question_row if isinstance(source_question_row, Mapping) else {}
    row: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CLASSIFICATION_ROW_SCHEMA_VERSION,
        "review_session_id": review_session_id,
        "blocker_row_ref": f"postmn11_pmn_op14_blocker_row_{seq:03d}_bodyfree",
        "source_rating_row_ref": _clean_ref(source_row.get("rating_row_ref"), default=f"postmn11_rating_row_{seq:03d}", max_length=180),
        "source_review_result_row_ref": _clean_ref(
            question_row.get("review_result_row_ref") or source_row.get("rating_source_review_result_row_ref"),
            default=f"postmn11_actual_review_result_row_{seq:03d}",
            max_length=180,
        ),
        "case_ref_id": _clean_ref(source_row.get("case_ref_id"), default="", max_length=180),
        "blind_case_id": _clean_ref(source_row.get("blind_case_id"), default="", max_length=180),
        "packet_ref_id": _clean_ref(source_row.get("packet_ref_id"), default="", max_length=180),
        "blocker_kind_ref": blocker_kind_ref,
        "blocker_category_ref": blocker_category_ref,
        "blocker_id_ref": _clean_ref(blocker_id_ref, default="unknown_blocker", max_length=180),
        "blocker_status_ref": P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_STATUS_OPEN_REF,
        "routes_to_ref": _pmn_op14_routes_to(blocker_category_ref),
        "p8_material_candidate_blocked": True,
        "safe_display_risk_not_question_candidate": blocker_category_ref == "p5_safe_display_risk",
        "body_free": True,
    }
    row.update({flag_ref: False for flag_ref in P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS})
    return row


def _pmn_op14_blocker_rows_from_rating_and_sanitized_rows(
    rating_rows: Sequence[Any],
    sanitized_rows: Sequence[Any],
    *,
    review_session_id: str,
) -> tuple[list[dict[str, Any]], list[str], set[str], set[str]]:
    blockers: list[str] = []
    blocker_rows: list[dict[str, Any]] = []
    sanitized_by_case: dict[str, Mapping[str, Any]] = {}
    for raw in sanitized_rows:
        if isinstance(raw, Mapping):
            sanitized_by_case[_clean_ref(raw.get("case_ref_id"), default="", max_length=180)] = raw
    seen_case_refs: set[str] = set()
    blocked_case_refs: set[str] = set()
    p8_candidate_case_refs: set[str] = set()
    seq = 1
    if len(rating_rows) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op14_source_rating_row_count_not_24")
    if len(sanitized_rows) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op14_source_sanitized_review_result_row_count_not_24")
    for raw_row in rating_rows:
        if not isinstance(raw_row, Mapping):
            blockers.append("pmn_op14_source_rating_row_not_mapping")
            continue
        if _scan_forbidden_payload_key_paths(raw_row, path="pmn_op14_source_rating_row"):
            blockers.append("pmn_op14_source_rating_row_forbidden_body_question_path_hash_key")
            continue
        if raw_row.get("schema_version") != P7_R54_AHR_POST_MN11_PMN_OP13_RATING_ROW_SCHEMA_VERSION:
            blockers.append("pmn_op14_source_rating_row_schema_not_op13")
        if raw_row.get("body_free") is not True:
            blockers.append("pmn_op14_source_rating_row_not_bodyfree")
        case_ref_id = _clean_ref(raw_row.get("case_ref_id"), default="", max_length=180)
        seen_case_refs.add(case_ref_id)
        question_row = sanitized_by_case.get(case_ref_id, {})
        if not question_row:
            blockers.append("pmn_op14_source_sanitized_row_missing_for_rating_case_ref")
        case_had_blocker = False
        for blocker_id in _pmn_op14_clean_ref_list(raw_row.get("readfeel_blocker_ids")):
            category = P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                blockers.append("pmn_op14_readfeel_blocker_id_not_allowed")
                continue
            blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="readfeel_blocker", blocker_category_ref=category, blocker_id_ref=blocker_id))
            seq += 1
            case_had_blocker = True
        for blocker_id in _pmn_op14_clean_ref_list(raw_row.get("execution_blocker_ids")):
            category = P7_R54_AHR_POST_MN11_PMN_OP14_EXECUTION_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                blockers.append("pmn_op14_execution_blocker_id_not_allowed")
                continue
            blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="execution_blocker", blocker_category_ref=category, blocker_id_ref=blocker_id))
            seq += 1
            case_had_blocker = True
        for repair_ref in _pmn_op14_clean_ref_list(question_row.get("repair_required_refs") if question_row else []):
            if repair_ref == "no_repair_required":
                continue
            category = P7_R54_AHR_POST_MN11_PMN_OP14_REPAIR_CATEGORY_BY_REF.get(repair_ref)
            if not category:
                blockers.append("pmn_op14_repair_required_ref_not_allowed")
                continue
            blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="repair_required", blocker_category_ref=category, blocker_id_ref=repair_ref))
            seq += 1
            case_had_blocker = True
        for axis_ref in _pmn_op14_clean_ref_list(raw_row.get("below_target_axis_refs")):
            category = P7_R54_AHR_POST_MN11_PMN_OP14_BELOW_TARGET_AXIS_CATEGORY_BY_REF.get(axis_ref)
            if not category:
                continue
            blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="below_target_axis", blocker_category_ref=category, blocker_id_ref=f"below_target_axis_{axis_ref}"))
            seq += 1
            case_had_blocker = True
        safe_display_refs = _pmn_op14_clean_ref_list(raw_row.get("safe_display_check_refs"))
        for safe_ref in safe_display_refs:
            if safe_ref in P7_R54_AHR_POST_MN11_PMN_OP14_SAFE_DISPLAY_RISK_CHECK_REFS:
                blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="safe_display_risk", blocker_category_ref="p5_safe_display_risk", blocker_id_ref=safe_ref))
                seq += 1
                case_had_blocker = True
        verdict_ref = _clean_ref(raw_row.get("verdict_ref"), default="", max_length=80)
        if verdict_ref in {"RED"}:
            blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="verdict_blocker", blocker_category_ref="p5_readfeel_repair_required", blocker_id_ref=f"verdict_{verdict_ref.lower()}"))
            seq += 1
            case_had_blocker = True
        if verdict_ref in {"BLOCKED", "NOT_REVIEWABLE"}:
            blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="inconclusive_material", blocker_category_ref="inconclusive_insufficient_material", blocker_id_ref=f"verdict_{verdict_ref.lower()}"))
            seq += 1
            case_had_blocker = True
        primary_class = _clean_ref(question_row.get("question_need_primary_class_ref") if question_row else "", default="", max_length=180)
        one_question_fit_ref = _clean_ref(question_row.get("one_question_fit_ref") if question_row else "", default="", max_length=180)
        repair_refs = set(_pmn_op14_clean_ref_list(question_row.get("repair_required_refs") if question_row else []))
        p8_candidate = (
            primary_class in P7_R54_AHR_POST_MN11_PMN_OP14_P8_MATERIAL_PRIMARY_CLASS_REFS
            and one_question_fit_ref in P7_R54_AHR_POST_MN11_PMN_OP14_P8_MATERIAL_ONE_QUESTION_FIT_REFS
        )
        if primary_class == "insufficient_material_execution_blocker":
            blocker_rows.append(_pmn_op14_make_blocker_row(seq=seq, source_row=raw_row, source_question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="inconclusive_material", blocker_category_ref="inconclusive_insufficient_material", blocker_id_ref=primary_class))
            seq += 1
            case_had_blocker = True
        if case_had_blocker:
            blocked_case_refs.add(case_ref_id)
        if p8_candidate:
            p8_candidate_case_refs.add(case_ref_id)
    if len(seen_case_refs) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
        blockers.append("pmn_op14_source_rating_case_ref_count_not_24_or_not_unique")
    return blocker_rows, list(dict.fromkeys(blockers)), blocked_case_refs, p8_candidate_case_refs


def _pmn_op14_blockers(op13: Mapping[str, Any] | None, op12: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op13, Mapping):
        blockers.append("pmn_op14_rating_row_normalization_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(op13)
        except ValueError:
            blockers.append("pmn_op14_op13_rating_row_normalization_invalid")
        if op13.get("rating_row_normalization_ready") is not True:
            blockers.append("pmn_op14_op13_rating_row_normalization_not_ready")
        if op13.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF:
            blockers.append("pmn_op14_op13_next_step_not_blocker_classification")
        if op13.get("question_need_observation_row_normalization_allowed_next") is not True:
            blockers.append("pmn_op14_op13_question_observation_not_allowed_next")
    if not isinstance(op12, Mapping):
        blockers.append("pmn_op14_sanitized_review_result_rows_intake_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(op12)
        except ValueError:
            blockers.append("pmn_op14_op12_sanitized_review_result_rows_intake_invalid")
        if op12.get("sanitized_review_result_rows_intake_ready") is not True:
            blockers.append("pmn_op14_op12_sanitized_review_result_rows_not_ready")
        if op12.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append("pmn_op14_op12_sanitized_review_result_row_count_not_24")
    if isinstance(op13, Mapping) and _scan_forbidden_payload_key_paths(op13):
        blockers.append("pmn_op14_op13_forbidden_body_question_path_hash_key_detected")
    if isinstance(op12, Mapping) and _scan_forbidden_payload_key_paths(op12):
        blockers.append("pmn_op14_op12_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification(
    *,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    actual_24_case_human_review_execution_protocol_state_capture: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP14 body-free readfeel / label / safe-display blocker classification."""

    session_id = _safe_review_session_id(review_session_id)
    op12 = sanitized_review_result_rows_intake
    if op12 is None:
        op12 = build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=actual_operation_receipt_intake,
            sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
            actual_24_case_human_review_execution_protocol_state_capture=actual_24_case_human_review_execution_protocol_state_capture,
            actual_operation_receipt_bodyfree=actual_operation_receipt_bodyfree,
            reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
            actual_review_execution_state_capture_bodyfree=actual_review_execution_state_capture_bodyfree,
            packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
            packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
            packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    op13 = rating_row_normalization_threshold_summary
    if op13 is None:
        op13 = build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    blockers = _pmn_op14_blockers(op13, op12)
    ready = not blockers
    session_id = _clean_ref(op13.get("review_session_id") if isinstance(op13, Mapping) else session_id, default=session_id, max_length=220)
    rating_rows = list(op13.get("rating_rows") or []) if isinstance(op13, Mapping) and ready else []
    sanitized_rows = list(op12.get("review_result_rows") or []) if isinstance(op12, Mapping) and ready else []
    blocker_rows, row_blockers, blocked_cases_from_rows, p8_candidate_cases = (
        _pmn_op14_blocker_rows_from_rating_and_sanitized_rows(rating_rows, sanitized_rows, review_session_id=session_id)
        if ready
        else ([], [], set(), set())
    )
    blockers = list(dict.fromkeys([*blockers, *row_blockers]))
    ready = not blockers
    if not ready:
        blocker_rows = []
        blocked_cases_from_rows = set()
        p8_candidate_cases = set()
        rating_rows = []
        sanitized_rows = []
    source_refs = [_clean_ref(row.get("rating_row_ref"), default="", max_length=180) for row in rating_rows if isinstance(row, Mapping)]
    case_refs = [_clean_ref(row.get("case_ref_id"), default="", max_length=180) for row in rating_rows if isinstance(row, Mapping)]
    kind_counts = {kind: 0 for kind in P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_KIND_REFS}
    category_counts = {category: 0 for category in P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CATEGORY_REFS}
    for row in blocker_rows:
        kind = _clean_ref(row.get("blocker_kind_ref"), default="", max_length=180)
        category = _clean_ref(row.get("blocker_category_ref"), default="", max_length=180)
        if kind in kind_counts:
            kind_counts[kind] += 1
        if category in category_counts:
            category_counts[category] += 1
    p5_case_refs = _pmn_op14_case_refs_for_categories(blocker_rows, {"p5_readfeel_repair_required", "p5_history_connection_weak", "p5_creepy_or_overclaim_risk", "p5_self_blame_amplification_risk", "p5_safe_display_risk"})
    p4_case_refs = _pmn_op14_case_refs_for_categories(blocker_rows, {"p4_current_only_surface_repair_required"})
    operation_case_refs = _pmn_op14_case_refs_for_categories(blocker_rows, {"operation_blocked_missing_receipt", "operation_blocked_body_leak", "operation_blocked_question_text", "operation_blocked_disposal_missing", "operation_blocked_no_touch_violation"})
    safe_case_refs = _pmn_op14_case_refs_for_categories(blocker_rows, {"p5_safe_display_risk"})
    inconclusive_case_refs = _pmn_op14_case_refs_for_categories(blocker_rows, {"inconclusive_insufficient_material"})
    all_blocker_case_refs = sorted(set(p5_case_refs) | set(p4_case_refs) | set(operation_case_refs) | set(inconclusive_case_refs) | set(blocked_cases_from_rows))
    no_blocker_case_refs = sorted(set(case_refs) - set(all_blocker_case_refs)) if ready else []
    category_counts["no_blocker"] = len(no_blocker_case_refs)
    p8_candidates = sorted(set(p8_candidate_cases) - set(all_blocker_case_refs)) if ready else []
    p8_blocked_by_blocker = sorted(set(p8_candidate_cases) & set(all_blocker_case_refs)) if ready else []
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP14_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP13_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP14_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP13_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_LABEL_CONNECTION_SAFE_DISPLAY_BLOCKER_CLASSIFICATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op13_schema_version": op13.get("schema_version") if isinstance(op13, Mapping) else None,
        "op13_material_ref": op13.get("material_id", "postmn11_pmn_op13_rating_row_normalization_threshold_summary_bodyfree") if isinstance(op13, Mapping) else "missing_op13",
        "op13_next_required_step": op13.get("next_required_step") if isinstance(op13, Mapping) else None,
        "op13_rating_row_normalization_ready": op13.get("rating_row_normalization_ready") is True if isinstance(op13, Mapping) else False,
        "op13_rating_row_count": int(op13.get("rating_row_count") or 0) if isinstance(op13, Mapping) else 0,
        "op13_question_need_observation_row_normalization_allowed_next": op13.get("question_need_observation_row_normalization_allowed_next") is True if isinstance(op13, Mapping) else False,
        "op13_actual_rating_rows_materialized_from_actual_rows": op13.get("actual_rating_rows_materialized_from_actual_rows") is True if isinstance(op13, Mapping) else False,
        "op12_schema_version": op12.get("schema_version") if isinstance(op12, Mapping) else None,
        "op12_material_ref": op12.get("material_id", "postmn11_pmn_op12_sanitized_review_result_rows_intake_bodyfree") if isinstance(op12, Mapping) else "missing_op12",
        "op12_sanitized_rows_ready": op12.get("sanitized_review_result_rows_intake_ready") is True if isinstance(op12, Mapping) else False,
        "op12_sanitized_review_result_row_count": int(op12.get("sanitized_review_result_row_count") or 0) if isinstance(op12, Mapping) else 0,
        "readfeel_label_connection_safe_display_blocker_classification_status_ref": P7_R54_AHR_POST_MN11_PMN_OP14_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_STATUS_REF,
        "readfeel_label_connection_safe_display_blocker_classification_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP14_ALLOWED_STATUS_REFS),
        "readfeel_label_connection_safe_display_blocker_classification_ready": ready,
        "readfeel_label_connection_safe_display_blocker_classification_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP14_READY_REASON_REFS) if ready else [],
        "readfeel_label_connection_safe_display_blocker_classification_blocker_refs": blockers,
        "readfeel_label_connection_safe_display_blocker_classification_blocker_ref_count": len(blockers),
        "blocker_classification_ref": P7_R54_AHR_POST_MN11_PMN_OP14_CLASSIFICATION_REF,
        "blocker_row_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "blocker_row_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "required_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "source_rating_row_count": len(rating_rows) if ready else 0,
        "source_rating_row_refs": source_refs,
        "source_rating_row_ref_count": len(source_refs),
        "source_review_result_row_count": len(sanitized_rows) if ready else 0,
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else False,
        "blocker_rows": blocker_rows,
        "blocker_row_count": len(blocker_rows),
        "blocker_row_refs": [_clean_ref(row.get("blocker_row_ref"), default="", max_length=180) for row in blocker_rows],
        "blocker_row_ref_count": len(blocker_rows),
        "blocker_kind_refs": list(P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_KIND_REFS),
        "blocker_kind_counts": kind_counts,
        "blocker_category_refs": list(P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CATEGORY_REFS),
        "blocker_category_counts": category_counts,
        "readfeel_blocker_row_count": kind_counts.get("readfeel_blocker", 0),
        "execution_blocker_row_count": kind_counts.get("execution_blocker", 0),
        "repair_required_blocker_row_count": kind_counts.get("repair_required", 0),
        "below_target_axis_blocker_row_count": kind_counts.get("below_target_axis", 0),
        "safe_display_blocker_row_count": kind_counts.get("safe_display_risk", 0),
        "inconclusive_blocker_row_count": kind_counts.get("inconclusive_material", 0),
        "verdict_blocker_row_count": kind_counts.get("verdict_blocker", 0),
        "readfeel_blocker_id_counts": _pmn_op14_count_nested_string_values(rating_rows, "readfeel_blocker_ids") if ready else {},
        "execution_blocker_id_counts": _pmn_op14_count_nested_string_values(rating_rows, "execution_blocker_ids") if ready else {},
        "repair_required_ref_counts": _pmn_op14_count_nested_string_values(sanitized_rows, "repair_required_refs") if ready else {},
        "below_target_axis_ref_counts": _pmn_op14_count_nested_string_values(rating_rows, "below_target_axis_refs") if ready else {},
        "safe_display_risk_case_refs": safe_case_refs,
        "safe_display_risk_case_count": len(safe_case_refs),
        "label_connection_distribution_ref": op13.get("label_connection_distribution_ref", {}) if isinstance(op13, Mapping) and ready else {},
        "safe_display_distribution_ref": op13.get("safe_display_distribution_ref", {}) if isinstance(op13, Mapping) and ready else {},
        "verdict_distribution_ref": op13.get("verdict_distribution_ref", {}) if isinstance(op13, Mapping) and ready else {},
        "no_blocker_case_refs": no_blocker_case_refs,
        "no_blocker_case_count": len(no_blocker_case_refs),
        "p5_repair_required_case_refs": p5_case_refs,
        "p5_repair_required_case_count": len(p5_case_refs),
        "p4_current_only_repair_required_case_refs": p4_case_refs,
        "p4_current_only_repair_required_case_count": len(p4_case_refs),
        "operation_blocked_case_refs": operation_case_refs,
        "operation_blocked_case_count": len(operation_case_refs),
        "safe_display_blocked_case_refs": safe_case_refs,
        "safe_display_blocked_case_count": len(safe_case_refs),
        "inconclusive_case_refs": inconclusive_case_refs,
        "inconclusive_case_count": len(inconclusive_case_refs),
        "p8_material_candidate_case_refs_bodyfree_only": p8_candidates,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_candidates),
        "p8_material_candidate_blocked_by_blocker_case_refs": p8_blocked_by_blocker,
        "p8_material_candidate_blocked_by_blocker_case_count": len(p8_blocked_by_blocker),
        "rows_bodyfree_only": all(row.get("body_free") is True for row in blocker_rows) if ready else False,
        "rows_have_no_question_text": all(row.get("question_text_included") is False and row.get("draft_question_text_included") is False for row in blocker_rows) if ready else False,
        "p5_p4_operation_readfeel_safe_display_blockers_not_escaped_to_p8_candidate": not (set(p8_candidates) & set(all_blocker_case_refs)) if ready else False,
        "safe_display_risk_not_question_candidate": not (set(safe_case_refs) & set(p8_candidates)) if ready else False,
        "readfeel_label_connection_safe_display_blockers_classified_here": ready,
        "actual_rating_rows_materialized_from_actual_rows": op13.get("actual_rating_rows_materialized_from_actual_rows") is True and ready if isinstance(op13, Mapping) else False,
        "actual_rating_rows_materialized_here": False,
        "actual_human_review_executed_by_person": op12.get("actual_human_review_executed_by_person") is True and ready if isinstance(op12, Mapping) else False,
        "actual_human_review_run_here": False,
        "question_need_observation_normalization_allowed_next": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "p5_finalization_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op14_does_not_create_question_rows_or_disposal": True,
        "pmn_op14_does_not_start_p5_p6_p8_r52_or_release": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP14_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP14 blocker classification")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_LABEL_CONNECTION_SAFE_DISPLAY_BLOCKER_CLASSIFICATION_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP14 blocker classification")
    ready = bool(data.get("readfeel_label_connection_safe_display_blocker_classification_ready"))
    blockers = list(data.get("readfeel_label_connection_safe_display_blocker_classification_blocker_refs") or [])
    if data.get("readfeel_label_connection_safe_display_blocker_classification_status_ref") != (P7_R54_AHR_POST_MN11_PMN_OP14_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 status changed")
    if tuple(data.get("readfeel_label_connection_safe_display_blocker_classification_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP14_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 allowed status refs changed")
    if data.get("readfeel_label_connection_safe_display_blocker_classification_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker count changed")
    if tuple(data.get("blocker_row_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row fields changed")
    for key in ("p5_finalization_blocked_here", "p6_p8_release_promotion_blocked_here", "r52_reintake_claim_blocked_here", "current_actual_review_basis_remains_264_85_258_171", "pmn_op14_does_not_create_question_rows_or_disposal", "pmn_op14_does_not_start_p5_p6_p8_r52_or_release"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP14 required true field changed: {key}")
    for key in ("actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_human_review_run_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_actual_execution_confirmed", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP14 required false field promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 basis changed")
    if ready:
        for key in ("op13_rating_row_normalization_ready", "op13_question_need_observation_row_normalization_allowed_next", "op13_actual_rating_rows_materialized_from_actual_rows", "op12_sanitized_rows_ready", "case_ref_ids_unique", "p5_p4_operation_readfeel_safe_display_blockers_not_escaped_to_p8_candidate", "safe_display_risk_not_question_candidate", "readfeel_label_connection_safe_display_blockers_classified_here", "actual_rating_rows_materialized_from_actual_rows", "actual_human_review_executed_by_person", "question_need_observation_normalization_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP14 ready field changed: {key}")
        if data.get("op13_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 OP13 next step changed")
        if data.get("readfeel_label_connection_safe_display_blocker_classification_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP14_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 ready reasons changed")
        if data.get("source_rating_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("source_review_result_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 source row counts must be 24")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP14_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 next step changed")
        if tuple(data.get("blocker_kind_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_KIND_REFS or tuple(data.get("blocker_category_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CATEGORY_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker refs changed")
        if data.get("blocker_row_ref_count") != len(data.get("blocker_rows") or []):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row count changed")
        for row in data.get("blocker_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row must be mapping")
            _required_fields_present(row, required=P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP14 blocker row")
            if row.get("schema_version") != P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CLASSIFICATION_ROW_SCHEMA_VERSION or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row schema/body-free changed")
            if row.get("blocker_kind_ref") not in P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_KIND_REFS or row.get("blocker_category_ref") not in P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_CATEGORY_REFS:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row kind/category changed")
            if row.get("blocker_status_ref") != P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_STATUS_OPEN_REF or row.get("p8_material_candidate_blocked") is not True:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row status/p8 block changed")
            for flag_ref in P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKER_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row body-free flag changed")
            if _scan_forbidden_payload_key_paths(row, path="pmn_op14_blocker_row"):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocker row leaked forbidden payload key")
    else:
        if data.get("readfeel_label_connection_safe_display_blocker_classification_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocked material cannot carry ready reasons")
        if data.get("blocker_rows") != [] or data.get("source_rating_row_count") != 0 or data.get("question_need_observation_normalization_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocked material promoted classification")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP14 blocked next step changed")
    return True


def _pmn_op15_count_nested_values(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                ref = _clean_ref(item, default="", max_length=180)
                if ref:
                    counts[ref] = counts.get(ref, 0) + 1
        else:
            ref = _clean_ref(value, default="", max_length=180)
            if ref:
                counts[ref] = counts.get(ref, 0) + 1
    return dict(sorted(counts.items()))


def _pmn_op15_normalize_question_need_rows(
    sanitized_rows: Sequence[Mapping[str, Any]],
    *,
    review_session_id: str,
    operation_receipt_ref: str,
    op14: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    p8_candidate_cases = set(op14.get("p8_material_candidate_case_refs_bodyfree_only") or [])
    p8_blocked_cases = set(op14.get("p8_material_candidate_blocked_by_blocker_case_refs") or [])
    question_rows: list[dict[str, Any]] = []
    plus_cases: list[str] = []
    premium_cases: list[str] = []
    for index, source_row in enumerate(sanitized_rows, start=1):
        case_ref = _clean_ref(source_row.get("case_ref_id"), default="", max_length=180)
        primary_class = _clean_ref(source_row.get("question_need_primary_class_ref"), default="insufficient_material_execution_blocker", max_length=180)
        ambiguity_refs = _pmn_op14_clean_ref_list(source_row.get("ambiguity_kind_refs"))
        one_question_fit_ref = _clean_ref(source_row.get("one_question_fit_ref"), default="insufficient_material", max_length=180)
        repair_refs = _pmn_op14_clean_ref_list(source_row.get("repair_required_refs"))
        plan_flags = source_row.get("plan_candidate_flags") if isinstance(source_row.get("plan_candidate_flags"), Mapping) else {}
        p8_candidate = case_ref in p8_candidate_cases
        plus_candidate = bool(p8_candidate and (primary_class == "plus_single_question_candidate_later" or plan_flags.get("plus_single_question_candidate_later") is True))
        premium_candidate = bool(p8_candidate and (primary_class == "premium_deep_dive_candidate_later" or plan_flags.get("premium_deep_dive_candidate_later") is True))
        if plus_candidate:
            plus_cases.append(case_ref)
        if premium_candidate:
            premium_cases.append(case_ref)
        row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "question_need_row_ref": f"postmn11_pmn_op15_question_need_observation_row_{index:03d}_bodyfree",
            "source_review_result_row_ref": source_row.get("review_result_row_ref"),
            "case_ref_id": case_ref,
            "blind_case_id": source_row.get("blind_case_id"),
            "packet_ref_id": source_row.get("packet_ref_id"),
            "question_need_primary_class_ref": primary_class,
            "ambiguity_kind_refs": ambiguity_refs,
            "one_question_fit_ref": one_question_fit_ref,
            "repair_required_refs": repair_refs,
            "p8_material_candidate_only": p8_candidate,
            "plus_single_question_candidate_later": plus_candidate,
            "premium_deep_dive_candidate_later": premium_candidate,
            "p8_material_candidate_blocked_by_blocker": case_ref in p8_blocked_cases,
            "question_text_materialized_here": False,
            "draft_question_text_materialized_here": False,
            "question_trigger_logic_materialized_here": False,
            "question_answer_storage_materialized_here": False,
            "p8_implementation_spec_finalized_here": False,
            "p8_start_allowed": False,
            "body_free": True,
        }
        row.update({flag_ref: False for flag_ref in P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS})
        question_rows.append(row)
    summary = {
        "question_need_primary_class_counts": _pmn_op15_count_nested_values(question_rows, "question_need_primary_class_ref"),
        "ambiguity_kind_counts": _pmn_op15_count_nested_values(question_rows, "ambiguity_kind_refs"),
        "one_question_fit_counts": _pmn_op15_count_nested_values(question_rows, "one_question_fit_ref"),
        "repair_required_ref_counts": _pmn_op15_count_nested_values(question_rows, "repair_required_refs"),
        "plus_cases": sorted(set(plus_cases)),
        "premium_cases": sorted(set(premium_cases)),
    }
    return question_rows, summary


def _pmn_op15_blockers(op14: Mapping[str, Any] | None, op12: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op14, Mapping):
        blockers.append("pmn_op15_blocker_classification_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(op14)
        except ValueError:
            blockers.append("pmn_op15_op14_blocker_classification_invalid")
        if op14.get("readfeel_label_connection_safe_display_blocker_classification_ready") is not True:
            blockers.append("pmn_op15_op14_blocker_classification_not_ready")
        if op14.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF:
            blockers.append("pmn_op15_op14_next_step_not_question_need_observation")
        if op14.get("question_need_observation_normalization_allowed_next") is not True:
            blockers.append("pmn_op15_op14_question_observation_not_allowed_next")
    if not isinstance(op12, Mapping):
        blockers.append("pmn_op15_sanitized_review_result_rows_intake_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(op12)
        except ValueError:
            blockers.append("pmn_op15_op12_sanitized_review_result_rows_intake_invalid")
        if op12.get("sanitized_review_result_rows_intake_ready") is not True:
            blockers.append("pmn_op15_op12_sanitized_review_result_rows_not_ready")
        if op12.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append("pmn_op15_op12_sanitized_review_result_row_count_not_24")
    if isinstance(op14, Mapping) and _scan_forbidden_payload_key_paths(op14):
        blockers.append("pmn_op15_op14_forbidden_body_question_path_hash_key_detected")
    if isinstance(op12, Mapping) and _scan_forbidden_payload_key_paths(op12):
        blockers.append("pmn_op15_op12_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization(
    *,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    actual_24_case_human_review_execution_protocol_state_capture: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    reviewer_person_boundary_selection_only_form_freeze: Mapping[str, Any] | None = None,
    actual_review_execution_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    packet_generation_local_operation_receipt_boundary: Mapping[str, Any] | None = None,
    packet_generation_request_bodyfree_builder: Mapping[str, Any] | None = None,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    local_only_preflight_explicit_allow_boundary: Mapping[str, Any] | None = None,
    review_session_envelope_actual_source_guard_freeze: Mapping[str, Any] | None = None,
    existing_op_ex_mn_support_material_inventory: Mapping[str, Any] | None = None,
    mn11_manual_decision_intake_basis_confirmation: Mapping[str, Any] | None = None,
    mn11_manual_decision_material: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP15 body-free question-need observation rows without question text."""

    session_id = _safe_review_session_id(review_session_id)
    op12 = sanitized_review_result_rows_intake
    if op12 is None:
        op12 = build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=actual_operation_receipt_intake,
            sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
            actual_24_case_human_review_execution_protocol_state_capture=actual_24_case_human_review_execution_protocol_state_capture,
            actual_operation_receipt_bodyfree=actual_operation_receipt_bodyfree,
            reviewer_person_boundary_selection_only_form_freeze=reviewer_person_boundary_selection_only_form_freeze,
            actual_review_execution_state_capture_bodyfree=actual_review_execution_state_capture_bodyfree,
            packet_completeness_export_denylist_scan=packet_completeness_export_denylist_scan,
            packet_generation_receipt_bodyfree=packet_generation_receipt_bodyfree,
            packet_generation_local_operation_receipt_boundary=packet_generation_local_operation_receipt_boundary,
            packet_generation_request_bodyfree_builder=packet_generation_request_bodyfree_builder,
            case_manifest_refreeze=case_manifest_refreeze,
            local_only_preflight_explicit_allow_boundary=local_only_preflight_explicit_allow_boundary,
            review_session_envelope_actual_source_guard_freeze=review_session_envelope_actual_source_guard_freeze,
            existing_op_ex_mn_support_material_inventory=existing_op_ex_mn_support_material_inventory,
            mn11_manual_decision_intake_basis_confirmation=mn11_manual_decision_intake_basis_confirmation,
            mn11_manual_decision_material=mn11_manual_decision_material,
            review_session_id=session_id,
        )
    op14 = readfeel_label_connection_safe_display_blocker_classification
    if op14 is None:
        op14 = build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification(
            rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    blockers = _pmn_op15_blockers(op14, op12)
    ready = not blockers
    session_id = _clean_ref(op14.get("review_session_id") if isinstance(op14, Mapping) else session_id, default=session_id, max_length=220)
    sanitized_rows = list(op12.get("review_result_rows") or []) if isinstance(op12, Mapping) and ready else []
    operation_receipt_ref = _clean_ref(op12.get("op11_operation_receipt_ref") if isinstance(op12, Mapping) else "", default="", max_length=220)
    question_rows, summary = _pmn_op15_normalize_question_need_rows(sanitized_rows, review_session_id=session_id, operation_receipt_ref=operation_receipt_ref, op14=op14) if ready else ([], {})
    p8_candidate_cases = list(op14.get("p8_material_candidate_case_refs_bodyfree_only") or []) if isinstance(op14, Mapping) and ready else []
    p8_blocked_cases = list(op14.get("p8_material_candidate_blocked_by_blocker_case_refs") or []) if isinstance(op14, Mapping) and ready else []
    case_refs = [_clean_ref(row.get("case_ref_id"), default="", max_length=180) for row in question_rows]
    blind_refs = [_clean_ref(row.get("blind_case_id"), default="", max_length=180) for row in question_rows]
    packet_refs = [_clean_ref(row.get("packet_ref_id"), default="", max_length=180) for row in question_rows]
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP15_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP14_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP15_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP14_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op14_schema_version": op14.get("schema_version") if isinstance(op14, Mapping) else None,
        "op14_material_ref": op14.get("material_id", "postmn11_pmn_op14_blocker_classification_bodyfree") if isinstance(op14, Mapping) else "missing_op14",
        "op14_next_required_step": op14.get("next_required_step") if isinstance(op14, Mapping) else None,
        "op14_blocker_classification_ready": op14.get("readfeel_label_connection_safe_display_blocker_classification_ready") is True if isinstance(op14, Mapping) else False,
        "op14_question_need_observation_normalization_allowed_next": op14.get("question_need_observation_normalization_allowed_next") is True if isinstance(op14, Mapping) else False,
        "op12_schema_version": op12.get("schema_version") if isinstance(op12, Mapping) else None,
        "op12_material_ref": op12.get("material_id", "postmn11_pmn_op12_sanitized_review_result_rows_intake_bodyfree") if isinstance(op12, Mapping) else "missing_op12",
        "op12_sanitized_rows_ready": op12.get("sanitized_review_result_rows_intake_ready") is True if isinstance(op12, Mapping) else False,
        "op12_sanitized_review_result_row_count": int(op12.get("sanitized_review_result_row_count") or 0) if isinstance(op12, Mapping) else 0,
        "operation_receipt_ref": operation_receipt_ref,
        "question_need_observation_row_normalization_status_ref": P7_R54_AHR_POST_MN11_PMN_OP15_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_STATUS_REF,
        "question_need_observation_row_normalization_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP15_ALLOWED_STATUS_REFS),
        "question_need_observation_row_normalization_ready": ready,
        "question_need_observation_row_normalization_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP15_READY_REASON_REFS) if ready else [],
        "question_need_observation_row_normalization_step_blocker_refs": blockers,
        "question_need_observation_row_normalization_step_blocker_ref_count": len(blockers),
        "question_need_observation_row_normalization_ref": P7_R54_AHR_POST_MN11_PMN_OP15_NORMALIZATION_REF,
        "question_need_observation_row_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_observation_row_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "source_sanitized_review_result_row_count": len(sanitized_rows) if ready else 0,
        "required_question_need_observation_row_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "question_need_observation_row_count": len(question_rows),
        "question_need_observation_row_count_is_24": len(question_rows) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else False,
        "question_need_observation_rows": question_rows,
        "question_need_observation_row_refs": [_clean_ref(row.get("question_need_row_ref"), default="", max_length=180) for row in question_rows],
        "question_need_observation_row_ref_count": len(question_rows),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else False,
        "blind_case_ids": blind_refs,
        "blind_case_id_count": len(blind_refs),
        "blind_case_ids_unique": len(set(blind_refs)) == len(blind_refs) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else False,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT if ready else False,
        "question_need_primary_class_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "question_need_primary_class_option_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS),
        "ambiguity_kind_option_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS),
        "one_question_fit_option_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS),
        "repair_required_option_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS),
        "question_need_primary_class_counts": summary.get("question_need_primary_class_counts", {}),
        "ambiguity_kind_counts": summary.get("ambiguity_kind_counts", {}),
        "one_question_fit_counts": summary.get("one_question_fit_counts", {}),
        "repair_required_ref_counts": summary.get("repair_required_ref_counts", {}),
        "p8_material_candidate_case_refs_bodyfree_only": p8_candidate_cases,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_candidate_cases),
        "plus_single_question_candidate_case_refs_bodyfree_only": summary.get("plus_cases", []),
        "plus_single_question_candidate_case_count_bodyfree_only": len(summary.get("plus_cases", [])),
        "premium_deep_dive_candidate_case_refs_bodyfree_only": summary.get("premium_cases", []),
        "premium_deep_dive_candidate_case_count_bodyfree_only": len(summary.get("premium_cases", [])),
        "p8_material_candidate_blocked_by_blocker_case_refs": p8_blocked_cases,
        "p8_material_candidate_blocked_by_blocker_case_count": len(p8_blocked_cases),
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "question_trigger_logic_materialized_here": False,
        "question_answer_storage_materialized_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "question_need_observation_rows_normalized_here": ready,
        "actual_question_need_observation_rows_materialized_from_actual_rows": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "p8_material_candidate_only_is_not_p8_start": True,
        "pmn_op15_does_not_create_disposal_or_evidence_complete": True,
        "pmn_op15_does_not_start_p5_p6_p8_r52_or_release": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP15_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP15 question observation")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP15 question observation")
    ready = bool(data.get("question_need_observation_row_normalization_ready"))
    blockers = list(data.get("question_need_observation_row_normalization_step_blocker_refs") or [])
    if data.get("question_need_observation_row_normalization_status_ref") != (P7_R54_AHR_POST_MN11_PMN_OP15_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 status changed")
    if tuple(data.get("question_need_observation_row_normalization_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP15_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 allowed status refs changed")
    if data.get("question_need_observation_row_normalization_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 blocker count changed")
    if tuple(data.get("question_need_observation_row_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 row fields changed")
    for key in ("actual_review_evidence_complete_from_real_review_still_false", "p8_material_candidate_only_is_not_p8_start", "pmn_op15_does_not_create_disposal_or_evidence_complete", "pmn_op15_does_not_start_p5_p6_p8_r52_or_release", "current_actual_review_basis_remains_264_85_258_171"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP15 required true field changed: {key}")
    for key in ("question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_materialized_here", "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here", "p8_start_allowed", "actual_question_need_observation_rows_materialized_here", "p5_final_allowed", "p6_start_allowed", "r52_actual_execution_confirmed", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP15 required false field promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 basis changed")
    if ready:
        for key in ("op14_blocker_classification_ready", "op14_question_need_observation_normalization_allowed_next", "op12_sanitized_rows_ready", "question_need_observation_row_count_is_24", "case_ref_ids_unique", "blind_case_ids_unique", "packet_ref_ids_unique", "question_need_observation_rows_normalized_here", "actual_question_need_observation_rows_materialized_from_actual_rows"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP15 ready field changed: {key}")
        if data.get("op14_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 OP14 next step changed")
        if data.get("question_need_observation_row_normalization_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP15_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 ready reasons changed")
        if data.get("question_need_observation_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or len(data.get("question_need_observation_rows") or []) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 row count must be 24")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP15_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 next step changed")
        if data.get("p8_material_candidate_case_count_bodyfree_only") != len(data.get("p8_material_candidate_case_refs_bodyfree_only") or []):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 p8 candidate count changed")
        for row in data.get("question_need_observation_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 row must be mapping")
            _required_fields_present(row, required=P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP15 question row")
            if row.get("schema_version") != P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 row schema/body-free changed")
            if row.get("question_need_primary_class_ref") not in P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 primary class changed")
            if row.get("one_question_fit_ref") not in P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 one question fit changed")
            for flag_key in ("question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_materialized_here", "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here", "p8_start_allowed"):
                if row.get(flag_key) is not False:
                    raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 row question/p8 flag changed")
            for flag_ref in P7_R54_AHR_POST_MN11_PMN_OP15_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 row body-free flag changed")
            if _scan_forbidden_payload_key_paths(row, path="pmn_op15_question_row"):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 row leaked forbidden payload key")
    else:
        if data.get("question_need_observation_row_normalization_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 blocked material cannot carry ready reasons")
        if data.get("question_need_observation_rows") != [] or data.get("question_need_observation_rows_normalized_here") is not False or data.get("actual_question_need_observation_rows_materialized_from_actual_rows") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 blocked material promoted rows")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP15 blocked next step changed")
    return True


def build_p7_r54_ahr_post_mn11_actual_operation_readfeel_label_connection_safe_display_blocker_classification_bodyfree(
    *,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification(
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_readfeel_label_connection_safe_display_blocker_classification_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_question_need_observation_row_normalization_bodyfree(
    *,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization(
        readfeel_label_connection_safe_display_blocker_classification=readfeel_label_connection_safe_display_blocker_classification,
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_question_need_observation_row_normalization_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(data)

def build_p7_r54_ahr_post_mn11_actual_operation_sanitized_review_result_rows_intake_provenance_guard_bodyfree(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
        actual_operation_receipt_intake=actual_operation_receipt_intake,
        sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_sanitized_review_result_rows_intake_provenance_guard_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_rating_row_normalization_threshold_summary_bodyfree(
    *,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        actual_operation_receipt_intake=actual_operation_receipt_intake,
        sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_rating_row_normalization_threshold_summary_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(data)


# ---------------------------------------------------------------------------
# PMN-OP16 / PMN-OP17 rating-question consistency and disposal receipt intake
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_MN11_PMN_OP16_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op16_rating_question_consistency_guard.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op16_rating_question_consistency_issue_row.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP17_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op17_disposal_purge_receipt_intake.bodyfree.v1"
)

P7_R54_AHR_POST_MN11_PMN_OP16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:17]
)
P7_R54_AHR_POST_MN11_PMN_OP16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[17:]
)
P7_R54_AHR_POST_MN11_PMN_OP17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:18]
)
P7_R54_AHR_POST_MN11_PMN_OP17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[18:]
)

P7_R54_AHR_POST_MN11_PMN_OP16_READY_STATUS_REF: Final = (
    "PMN_OP16_RATING_QUESTION_CONSISTENCY_GUARD_PASSED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_STATUS_REF: Final = (
    "PMN_OP16_RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_DETECTED_STATUS_REF: Final = (
    "PMN_OP16_RATING_QUESTION_CONSISTENCY_GUARD_ISSUE_DETECTED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP16_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP16_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_DETECTED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op16_rating_question_consistency_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP16_GUARD_REF: Final = (
    "postmn11_rating_question_consistency_guard_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP16_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op15_question_need_observation_rows_normalized_bodyfree",
    "op14_blocker_classification_ready_bodyfree",
    "op13_rating_rows_normalized_bodyfree",
    "rating_question_consistency_checked_without_p8_escape",
    "disposal_purge_receipt_intake_required_next_without_evidence_complete",
)
P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_KIND_REFS: Final[tuple[str, ...]] = (
    "below_target_axis_p8_escape",
    "safe_display_risk_question_escape",
    "readfeel_blocker_question_escape",
    "execution_blocker_question_escape",
    "insufficient_material_question_escape",
    "heavy_observation_p8_escape",
    "verdict_blocker_p8_escape",
    "repair_required_question_escape",
    "op14_blocked_candidate_resurfaced",
)
P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS,
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_trigger_logic_materialized_here",
    "question_answer_storage_materialized_here",
    "p8_implementation_spec_finalized_here",
    "p8_start_allowed",
)
P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "consistency_issue_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "source_rating_row_ref",
    "source_question_need_row_ref",
    "issue_kind_ref",
    "issue_reason_ref",
    "blocked_escape_to_ref",
    "p8_candidate_escape_detected",
    "p8_candidate_escape_blocked",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_trigger_logic_materialized_here",
    "question_answer_storage_materialized_here",
    "p8_implementation_spec_finalized_here",
    "p8_start_allowed",
    "body_free",
    *P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_MN11_PMN_OP16_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op15_schema_version", "op15_material_ref", "op15_next_required_step", "op15_question_need_observation_row_normalization_ready",
    "op15_question_need_observation_row_count", "op15_p8_material_candidate_case_count_bodyfree_only", "op15_p8_start_allowed",
    "op14_schema_version", "op14_material_ref", "op14_blocker_classification_ready", "op14_blocker_row_count",
    "op14_p8_material_candidate_case_count_bodyfree_only", "op14_p8_material_candidate_blocked_by_blocker_case_count",
    "op13_schema_version", "op13_material_ref", "op13_rating_row_normalization_ready", "op13_rating_row_count",
    "operation_receipt_ref", "rating_question_consistency_guard_status_ref", "rating_question_consistency_guard_allowed_status_refs",
    "rating_question_consistency_guard_passed", "rating_question_consistency_guard_reason_refs", "rating_question_consistency_guard_step_blocker_refs",
    "rating_question_consistency_guard_step_blocker_ref_count", "rating_question_consistency_guard_ref",
    "consistency_issue_row_required_field_refs", "consistency_issue_row_required_field_ref_count",
    "consistency_issue_rows", "consistency_issue_row_count", "consistency_issue_row_refs", "consistency_issue_row_ref_count",
    "consistency_issue_kind_refs", "consistency_issue_kind_counts", "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only", "p8_material_candidate_blocked_by_blocker_case_refs",
    "p8_material_candidate_blocked_by_blocker_case_count", "below_target_axis_p8_escape_issue_count",
    "safe_display_question_escape_issue_count", "readfeel_blocker_question_escape_issue_count",
    "execution_blocker_question_escape_issue_count", "insufficient_material_question_escape_issue_count",
    "heavy_observation_p8_escape_issue_count", "verdict_blocker_p8_escape_issue_count", "repair_required_question_escape_issue_count",
    "op14_blocked_candidate_resurfaced_issue_count", "rating_question_consistency_checked_here",
    "rating_question_consistency_guard_blocks_p8_escape", "weak_rating_or_blocker_not_treated_as_question_candidate",
    "safe_display_risk_not_question_candidate", "question_would_make_immediate_observation_heavy_not_p8_candidate",
    "question_observation_guard_does_not_create_question_text", "question_observation_guard_does_not_start_p8",
    "consistency_guard_does_not_create_disposal_or_evidence_complete", "actual_review_evidence_complete_from_real_review_still_false",
    "disposal_purge_receipt_intake_allowed_next", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_mn11_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP17_READY_STATUS_REF: Final = (
    "PMN_OP17_DISPOSAL_PURGE_RECEIPT_INTAKED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_STATUS_REF: Final = (
    "PMN_OP17_DISPOSAL_PURGE_RECEIPT_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "PMN_OP17_DISPOSAL_PURGE_RECEIPT_INTAKE_BLOCKED_BY_BODY_PATH_HASH_OR_NOTES_LEAK"
)
P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP17_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op17_disposal_purge_receipt_intake_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP17_INTAKE_REF: Final = (
    "postmn11_disposal_purge_receipt_intake_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP17_DEFAULT_DISPOSAL_RECEIPT_REF: Final = (
    "postmn11_disposal_receipt_ref_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "BODY_PURGED",
    "BODY_NOT_MATERIALIZED_NO_DISPOSAL_REQUIRED",
    "DISPOSAL_FAILED",
)
P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_ACTUAL_SOURCE_REF: Final = "actual_local_disposal_receipt_bodyfree"
P7_R54_AHR_POST_MN11_PMN_OP17_DEFAULT_RETENTION_POLICY_REF: Final = "local_body_full_packet_max_72h_or_shorter"
P7_R54_AHR_POST_MN11_PMN_OP17_DEFAULT_EXPIRATION_POLICY_REF: Final = "post_review_body_full_packet_expired_or_purged"
P7_R54_AHR_POST_MN11_PMN_OP17_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op16_rating_question_consistency_guard_passed_bodyfree",
    "actual_local_disposal_receipt_received_bodyfree",
    "disposal_status_is_body_purged",
    "body_notes_and_temporary_form_removed_without_path_or_hash",
    "final_no_leak_validation_required_next_without_evidence_complete",
)
P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "disposal_receipt_ref",
    "review_session_id",
    "operation_receipt_ref",
    "disposal_status_ref",
    "packet_materialized_for_review",
    "body_removed",
    "reviewer_notes_removed",
    "temporary_form_removed",
    "content_hash_of_body_stored",
    "body_hash_stored",
    "local_absolute_path_included",
    "reviewer_notes_body_stored",
    "pause_abort_status_ref",
    "retention_policy_ref",
    "expiration_policy_ref",
    "actual_source_ref",
    "body_free",
)
P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op16_schema_version", "op16_material_ref", "op16_next_required_step", "op16_rating_question_consistency_guard_passed",
    "op16_consistency_issue_row_count", "op16_operation_receipt_ref", "disposal_purge_receipt_intake_status_ref",
    "disposal_purge_receipt_intake_allowed_status_refs", "disposal_purge_receipt_intake_ready",
    "disposal_purge_receipt_accepted", "disposal_purge_receipt_reason_refs", "disposal_purge_receipt_blocker_refs",
    "disposal_purge_receipt_blocker_ref_count", "disposal_purge_receipt_intake_ref",
    "disposal_receipt_required_field_refs", "disposal_receipt_required_field_ref_count", "disposal_receipt_ref",
    "disposal_receipt_ref_present", "disposal_receipt_ref_is_bodyfree_ref", "disposal_receipt_ref_has_local_path_shape",
    "disposal_receipt_received_here", "disposal_receipt_intaked_here", "operation_receipt_ref",
    "operation_receipt_ref_matches_op16", "disposal_status_ref", "disposal_status_allowed_refs", "disposal_status_is_body_purged",
    "packet_materialized_for_review", "body_removed", "reviewer_notes_removed", "temporary_form_removed",
    "content_hash_of_body_stored", "body_hash_stored", "local_absolute_path_included", "reviewer_notes_body_stored",
    "pause_abort_status_ref", "retention_policy_ref", "expiration_policy_ref", "actual_source_ref", "actual_source_allowed_ref",
    "actual_source_guard_passed", "disposal_receipt_bodyfree_only", "forbidden_disposal_receipt_payload_key_paths",
    "forbidden_disposal_receipt_payload_key_path_count", "body_full_packet_lifecycle_closed_bodyfree",
    "body_removed_without_hash_path_or_reviewer_notes", "temporary_form_removed_without_export", "disposal_receipt_does_not_store_body_hash_or_local_path",
    "disposal_receipt_does_not_store_reviewer_notes_body", "disposal_receipt_does_not_create_question_text",
    "actual_disposal_receipt_materialized_here", "disposal_verified", "disposal_receipt_ready_for_final_no_leak_validation_only",
    "actual_review_evidence_complete_from_real_review_still_false", "pmn_op17_does_not_run_disposal_here",
    "pmn_op17_does_not_complete_evidence", "pmn_op17_does_not_start_p5_p6_p8_r52_or_release",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _pmn_op16_clean_ref_set(value: Any) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return set()
    return {_clean_ref(item, default="", max_length=180) for item in value if _clean_ref(item, default="", max_length=180)}


def _pmn_op16_make_issue_row(
    *,
    seq: int,
    question_row: Mapping[str, Any],
    rating_row: Mapping[str, Any] | None,
    review_session_id: str,
    issue_kind_ref: str,
    issue_reason_ref: str,
) -> dict[str, Any]:
    row = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "review_session_id": review_session_id,
        "consistency_issue_row_ref": f"postmn11-pmn-op16-consistency-issue-row-{seq:03d}",
        "case_ref_id": _clean_ref(question_row.get("case_ref_id"), default=f"missing_case_ref_{seq:03d}", max_length=180),
        "blind_case_id": _clean_ref(question_row.get("blind_case_id"), default=f"missing_blind_case_{seq:03d}", max_length=180),
        "packet_ref_id": _clean_ref(question_row.get("packet_ref_id"), default=f"missing_packet_ref_{seq:03d}", max_length=180),
        "source_rating_row_ref": _clean_ref((rating_row or {}).get("rating_row_ref"), default="missing_rating_row_ref", max_length=180),
        "source_question_need_row_ref": _clean_ref(question_row.get("question_need_row_ref"), default="missing_question_need_row_ref", max_length=180),
        "issue_kind_ref": issue_kind_ref,
        "issue_reason_ref": issue_reason_ref,
        "blocked_escape_to_ref": "P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY",
        "p8_candidate_escape_detected": True,
        "p8_candidate_escape_blocked": True,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "question_trigger_logic_materialized_here": False,
        "question_answer_storage_materialized_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "body_free": True,
    }
    row.update({flag_ref: False for flag_ref in P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS})
    return row


def _pmn_op16_issue_rows(
    *,
    question_rows: Sequence[Any],
    rating_rows: Sequence[Any],
    op14: Mapping[str, Any],
    review_session_id: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    issues: list[dict[str, Any]] = []
    blockers: list[str] = []
    rating_by_case: dict[str, Mapping[str, Any]] = {}
    for raw in rating_rows:
        if not isinstance(raw, Mapping):
            blockers.append("pmn_op16_source_rating_row_not_mapping")
            continue
        if _scan_forbidden_payload_key_paths(raw, path="pmn_op16_rating_row"):
            blockers.append("pmn_op16_source_rating_row_forbidden_payload_key")
            continue
        rating_by_case[_clean_ref(raw.get("case_ref_id"), default="", max_length=180)] = raw
    blocked_cases = set(_clean_ref(ref, default="", max_length=180) for ref in (op14.get("p8_material_candidate_blocked_by_blocker_case_refs") or []))
    blocker_case_refs = set()
    for raw in op14.get("blocker_rows") or []:
        if isinstance(raw, Mapping):
            blocker_case_refs.add(_clean_ref(raw.get("case_ref_id"), default="", max_length=180))
    seq = 1
    for raw in question_rows:
        if not isinstance(raw, Mapping):
            blockers.append("pmn_op16_question_need_row_not_mapping")
            continue
        if _scan_forbidden_payload_key_paths(raw, path="pmn_op16_question_row"):
            blockers.append("pmn_op16_question_need_row_forbidden_payload_key")
            continue
        case_ref = _clean_ref(raw.get("case_ref_id"), default="", max_length=180)
        rating_row = rating_by_case.get(case_ref, {})
        if not rating_row:
            blockers.append("pmn_op16_rating_row_missing_for_question_case_ref")
            continue
        primary_class = _clean_ref(raw.get("question_need_primary_class_ref"), default="", max_length=180)
        one_question_fit_ref = _clean_ref(raw.get("one_question_fit_ref"), default="", max_length=180)
        p8_candidate = bool(raw.get("p8_material_candidate_only"))
        candidate_like = p8_candidate or primary_class in P7_R54_AHR_POST_MN11_PMN_OP14_P8_MATERIAL_PRIMARY_CLASS_REFS
        if not candidate_like:
            continue
        issue_specs: list[tuple[str, str]] = []
        if case_ref in blocked_cases or case_ref in blocker_case_refs:
            issue_specs.append(("op14_blocked_candidate_resurfaced", "op14_blocked_case_reappeared_as_question_or_p8_candidate"))
        below_target_refs = _pmn_op16_clean_ref_set(rating_row.get("below_target_axis_refs"))
        if below_target_refs and p8_candidate:
            issue_specs.append(("below_target_axis_p8_escape", "axis_target_below_threshold_but_p8_candidate"))
        safe_refs = _pmn_op16_clean_ref_set(rating_row.get("safe_display_check_refs"))
        if "safe_display_risk_detected" in safe_refs and candidate_like:
            issue_specs.append(("safe_display_risk_question_escape", "safe_display_risk_cannot_be_question_candidate"))
        readfeel_refs = _pmn_op16_clean_ref_set(rating_row.get("readfeel_blocker_ids"))
        if readfeel_refs and candidate_like:
            issue_specs.append(("readfeel_blocker_question_escape", "readfeel_blocker_cannot_escape_to_question_candidate"))
        execution_refs = _pmn_op16_clean_ref_set(rating_row.get("execution_blocker_ids"))
        if execution_refs and candidate_like:
            issue_specs.append(("execution_blocker_question_escape", "execution_blocker_cannot_escape_to_question_candidate"))
        repair_refs = _pmn_op16_clean_ref_set(raw.get("repair_required_refs")) - {"no_repair_required"}
        if repair_refs and candidate_like:
            issue_specs.append(("repair_required_question_escape", "repair_required_case_cannot_escape_to_question_candidate"))
        verdict_ref = _clean_ref(rating_row.get("verdict_ref"), default="", max_length=80)
        if verdict_ref in {"RED", "BLOCKED", "NOT_REVIEWABLE"} and candidate_like:
            issue_specs.append(("verdict_blocker_p8_escape", "red_blocked_or_not_reviewable_verdict_cannot_be_p8_candidate"))
        if primary_class == "insufficient_material_execution_blocker" and candidate_like:
            issue_specs.append(("insufficient_material_question_escape", "insufficient_material_or_execution_blocker_cannot_be_question_candidate"))
        if (primary_class == "question_would_make_immediate_observation_heavy" or one_question_fit_ref == "would_delay_immediate_observation") and p8_candidate:
            issue_specs.append(("heavy_observation_p8_escape", "heavy_observation_case_cannot_be_p8_candidate"))
        seen: set[tuple[str, str]] = set()
        for issue_kind, reason in issue_specs:
            key = (issue_kind, reason)
            if key in seen:
                continue
            seen.add(key)
            issues.append(_pmn_op16_make_issue_row(seq=seq, question_row=raw, rating_row=rating_row, review_session_id=review_session_id, issue_kind_ref=issue_kind, issue_reason_ref=reason))
            seq += 1
    return issues, list(dict.fromkeys(blockers))


def _pmn_op16_blockers(
    op15: Mapping[str, Any] | None,
    op14: Mapping[str, Any] | None,
    op13: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op15, Mapping):
        blockers.append("pmn_op16_question_need_observation_row_normalization_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(op15)
        except ValueError:
            blockers.append("pmn_op16_op15_question_need_observation_invalid")
        if op15.get("question_need_observation_row_normalization_ready") is not True:
            blockers.append("pmn_op16_op15_question_need_observation_not_ready")
        if op15.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF:
            blockers.append("pmn_op16_op15_next_step_not_consistency_guard")
        if op15.get("p8_start_allowed") is not False:
            blockers.append("pmn_op16_op15_p8_start_promoted")
    if not isinstance(op14, Mapping):
        blockers.append("pmn_op16_blocker_classification_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(op14)
        except ValueError:
            blockers.append("pmn_op16_op14_blocker_classification_invalid")
        if op14.get("readfeel_label_connection_safe_display_blocker_classification_ready") is not True:
            blockers.append("pmn_op16_op14_blocker_classification_not_ready")
    if not isinstance(op13, Mapping):
        blockers.append("pmn_op16_rating_row_normalization_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(op13)
        except ValueError:
            blockers.append("pmn_op16_op13_rating_row_normalization_invalid")
        if op13.get("rating_row_normalization_ready") is not True:
            blockers.append("pmn_op16_op13_rating_row_normalization_not_ready")
    for material, prefix in ((op15, "op15"), (op14, "op14"), (op13, "op13")):
        if isinstance(material, Mapping) and _scan_forbidden_payload_key_paths(material, path=f"pmn_op16_{prefix}"):
            blockers.append(f"pmn_op16_{prefix}_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard(
    *,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    review_session_id: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build PMN-OP16 body-free rating/question consistency guard material."""

    session_id = _safe_review_session_id(review_session_id)
    op12 = sanitized_review_result_rows_intake
    if op12 is None and (question_need_observation_row_normalization is None or readfeel_label_connection_safe_display_blocker_classification is None or rating_row_normalization_threshold_summary is None):
        op12 = build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=actual_operation_receipt_intake,
            sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
            review_session_id=session_id,
            **kwargs,
        )
    op13 = rating_row_normalization_threshold_summary
    if op13 is None:
        op13 = build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    op14 = readfeel_label_connection_safe_display_blocker_classification
    if op14 is None:
        op14 = build_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification(
            rating_row_normalization_threshold_summary=op13,
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    op15 = question_need_observation_row_normalization
    if op15 is None:
        op15 = build_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization(
            readfeel_label_connection_safe_display_blocker_classification=op14,
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    blockers = _pmn_op16_blockers(op15, op14, op13)
    can_check = not blockers
    session_id = _clean_ref(op15.get("review_session_id") if isinstance(op15, Mapping) else session_id, default=session_id, max_length=220)
    question_rows = list(op15.get("question_need_observation_rows") or []) if isinstance(op15, Mapping) and can_check else []
    rating_rows = list(op13.get("rating_rows") or []) if isinstance(op13, Mapping) and can_check else []
    issue_rows, issue_blockers = _pmn_op16_issue_rows(question_rows=question_rows, rating_rows=rating_rows, op14=op14 or {}, review_session_id=session_id) if can_check else ([], [])
    blockers = list(dict.fromkeys([*blockers, *issue_blockers]))
    issue_kind_counts = {kind: 0 for kind in P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_KIND_REFS}
    for row in issue_rows:
        kind = _clean_ref(row.get("issue_kind_ref"), default="", max_length=180)
        if kind in issue_kind_counts:
            issue_kind_counts[kind] += 1
    passed = not blockers and not issue_rows
    issue_detected = not blockers and bool(issue_rows)
    status = P7_R54_AHR_POST_MN11_PMN_OP16_READY_STATUS_REF if passed else P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_DETECTED_STATUS_REF if issue_detected else P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_STATUS_REF
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP16_IMPLEMENTED_STEPS if passed else P7_R54_AHR_POST_MN11_PMN_OP15_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP16_NOT_YET_IMPLEMENTED_STEPS if passed else P7_R54_AHR_POST_MN11_PMN_OP15_NOT_YET_IMPLEMENTED_STEPS
    p8_candidate_cases = list(op15.get("p8_material_candidate_case_refs_bodyfree_only") or []) if isinstance(op15, Mapping) and can_check else []
    p8_blocked_cases = list(op15.get("p8_material_candidate_blocked_by_blocker_case_refs") or []) if isinstance(op15, Mapping) and can_check else []
    operation_receipt_ref = _clean_ref(op15.get("operation_receipt_ref") if isinstance(op15, Mapping) else "", default="", max_length=220)
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP16_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op15_schema_version": op15.get("schema_version") if isinstance(op15, Mapping) else None,
        "op15_material_ref": op15.get("material_id", "missing_op15") if isinstance(op15, Mapping) else "missing_op15",
        "op15_next_required_step": op15.get("next_required_step") if isinstance(op15, Mapping) else None,
        "op15_question_need_observation_row_normalization_ready": op15.get("question_need_observation_row_normalization_ready") is True if isinstance(op15, Mapping) else False,
        "op15_question_need_observation_row_count": int(op15.get("question_need_observation_row_count") or 0) if isinstance(op15, Mapping) else 0,
        "op15_p8_material_candidate_case_count_bodyfree_only": int(op15.get("p8_material_candidate_case_count_bodyfree_only") or 0) if isinstance(op15, Mapping) else 0,
        "op15_p8_start_allowed": op15.get("p8_start_allowed") is True if isinstance(op15, Mapping) else False,
        "op14_schema_version": op14.get("schema_version") if isinstance(op14, Mapping) else None,
        "op14_material_ref": op14.get("material_id", "missing_op14") if isinstance(op14, Mapping) else "missing_op14",
        "op14_blocker_classification_ready": op14.get("readfeel_label_connection_safe_display_blocker_classification_ready") is True if isinstance(op14, Mapping) else False,
        "op14_blocker_row_count": int(op14.get("blocker_row_count") or 0) if isinstance(op14, Mapping) else 0,
        "op14_p8_material_candidate_case_count_bodyfree_only": int(op14.get("p8_material_candidate_case_count_bodyfree_only") or 0) if isinstance(op14, Mapping) else 0,
        "op14_p8_material_candidate_blocked_by_blocker_case_count": int(op14.get("p8_material_candidate_blocked_by_blocker_case_count") or 0) if isinstance(op14, Mapping) else 0,
        "op13_schema_version": op13.get("schema_version") if isinstance(op13, Mapping) else None,
        "op13_material_ref": op13.get("material_id", "missing_op13") if isinstance(op13, Mapping) else "missing_op13",
        "op13_rating_row_normalization_ready": op13.get("rating_row_normalization_ready") is True if isinstance(op13, Mapping) else False,
        "op13_rating_row_count": int(op13.get("rating_row_count") or 0) if isinstance(op13, Mapping) else 0,
        "operation_receipt_ref": operation_receipt_ref,
        "rating_question_consistency_guard_status_ref": status,
        "rating_question_consistency_guard_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP16_ALLOWED_STATUS_REFS),
        "rating_question_consistency_guard_passed": passed,
        "rating_question_consistency_guard_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP16_READY_REASON_REFS) if passed else [],
        "rating_question_consistency_guard_step_blocker_refs": blockers,
        "rating_question_consistency_guard_step_blocker_ref_count": len(blockers),
        "rating_question_consistency_guard_ref": P7_R54_AHR_POST_MN11_PMN_OP16_GUARD_REF,
        "consistency_issue_row_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS),
        "consistency_issue_row_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS),
        "consistency_issue_rows": issue_rows,
        "consistency_issue_row_count": len(issue_rows),
        "consistency_issue_row_refs": [_clean_ref(row.get("consistency_issue_row_ref"), default="", max_length=180) for row in issue_rows],
        "consistency_issue_row_ref_count": len(issue_rows),
        "consistency_issue_kind_refs": list(P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_KIND_REFS),
        "consistency_issue_kind_counts": issue_kind_counts,
        "p8_material_candidate_case_refs_bodyfree_only": p8_candidate_cases,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_candidate_cases),
        "p8_material_candidate_blocked_by_blocker_case_refs": p8_blocked_cases,
        "p8_material_candidate_blocked_by_blocker_case_count": len(p8_blocked_cases),
        "below_target_axis_p8_escape_issue_count": issue_kind_counts["below_target_axis_p8_escape"],
        "safe_display_question_escape_issue_count": issue_kind_counts["safe_display_risk_question_escape"],
        "readfeel_blocker_question_escape_issue_count": issue_kind_counts["readfeel_blocker_question_escape"],
        "execution_blocker_question_escape_issue_count": issue_kind_counts["execution_blocker_question_escape"],
        "insufficient_material_question_escape_issue_count": issue_kind_counts["insufficient_material_question_escape"],
        "heavy_observation_p8_escape_issue_count": issue_kind_counts["heavy_observation_p8_escape"],
        "verdict_blocker_p8_escape_issue_count": issue_kind_counts["verdict_blocker_p8_escape"],
        "repair_required_question_escape_issue_count": issue_kind_counts["repair_required_question_escape"],
        "op14_blocked_candidate_resurfaced_issue_count": issue_kind_counts["op14_blocked_candidate_resurfaced"],
        "rating_question_consistency_checked_here": can_check,
        "rating_question_consistency_guard_blocks_p8_escape": passed,
        "weak_rating_or_blocker_not_treated_as_question_candidate": passed,
        "safe_display_risk_not_question_candidate": passed,
        "question_would_make_immediate_observation_heavy_not_p8_candidate": passed,
        "question_observation_guard_does_not_create_question_text": True,
        "question_observation_guard_does_not_start_p8": True,
        "consistency_guard_does_not_create_disposal_or_evidence_complete": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "disposal_purge_receipt_intake_allowed_next": passed,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF if passed else P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP16_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP16 rating-question consistency")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP16_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP16 rating-question consistency")
    passed = bool(data.get("rating_question_consistency_guard_passed"))
    blockers = list(data.get("rating_question_consistency_guard_step_blocker_refs") or [])
    issue_rows = list(data.get("consistency_issue_rows") or [])
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP16_READY_STATUS_REF if passed else P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_DETECTED_STATUS_REF if issue_rows and not blockers else P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_STATUS_REF
    if data.get("rating_question_consistency_guard_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 status changed")
    if tuple(data.get("rating_question_consistency_guard_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP16_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 allowed status refs changed")
    if data.get("rating_question_consistency_guard_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 blocker count changed")
    if tuple(data.get("consistency_issue_row_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue row required fields changed")
    if data.get("consistency_issue_row_count") != len(issue_rows) or data.get("consistency_issue_row_ref_count") != len(issue_rows):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue row count changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 basis changed")
    for key in ("question_observation_guard_does_not_create_question_text", "question_observation_guard_does_not_start_p8", "consistency_guard_does_not_create_disposal_or_evidence_complete", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP16 required true field changed: {key}")
    for key in ("op15_p8_start_allowed", "p8_start_allowed", "actual_disposal_receipt_materialized_here", "disposal_verified", "actual_review_evidence_complete_from_real_review", "p5_final_allowed", "p6_start_allowed", "r52_actual_execution_confirmed", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP16 required false field promoted: {key}")
    if passed:
        for key in ("op15_question_need_observation_row_normalization_ready", "op14_blocker_classification_ready", "op13_rating_row_normalization_ready", "rating_question_consistency_checked_here", "rating_question_consistency_guard_blocks_p8_escape", "weak_rating_or_blocker_not_treated_as_question_candidate", "safe_display_risk_not_question_candidate", "question_would_make_immediate_observation_heavy_not_p8_candidate", "disposal_purge_receipt_intake_allowed_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP16 ready field changed: {key}")
        if data.get("op15_next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 OP15 next step changed")
        if data.get("op15_question_need_observation_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT or data.get("op13_rating_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 source count must be 24")
        if data.get("rating_question_consistency_guard_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP16_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 ready reasons changed")
        if issue_rows or blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 passed material cannot have issues or blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP16_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 ready steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 next step changed")
    else:
        if data.get("rating_question_consistency_guard_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 blocked material cannot carry ready reasons")
        if data.get("disposal_purge_receipt_intake_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 blocked material allowed disposal intake")
        if not blockers and not issue_rows:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 blocked material must carry blocker or issue rows")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 blocked next step changed")
    for row in issue_rows:
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue row must be mapping")
        _required_fields_present(row, required=P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP16 issue row")
        if row.get("schema_version") != P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION or row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue row schema/body-free changed")
        if row.get("issue_kind_ref") not in P7_R54_AHR_POST_MN11_PMN_OP16_ISSUE_KIND_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue kind changed")
        for flag_ref in P7_R54_AHR_POST_MN11_PMN_OP16_CONSISTENCY_ISSUE_ROW_FALSE_FLAG_REFS:
            if row.get(flag_ref) is not False:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue row false flag changed")
        if row.get("p8_candidate_escape_detected") is not True or row.get("p8_candidate_escape_blocked") is not True:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue row must block escape")
        if _scan_forbidden_payload_key_paths(row, path="pmn_op16_issue_row"):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP16 issue row leaked forbidden payload key")
    return True


def _pmn_op17_receipt_blockers(op16: Mapping[str, Any] | None, receipt: Mapping[str, Any] | None) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    leak_paths: list[str] = []
    if not isinstance(op16, Mapping):
        blockers.append("pmn_op17_rating_question_consistency_guard_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(op16)
        except ValueError:
            blockers.append("pmn_op17_op16_rating_question_consistency_guard_invalid")
        if op16.get("rating_question_consistency_guard_passed") is not True:
            blockers.append("pmn_op17_op16_consistency_guard_not_passed")
        if op16.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF:
            blockers.append("pmn_op17_op16_next_step_not_disposal_intake")
    if not isinstance(receipt, Mapping):
        blockers.append("pmn_op17_disposal_receipt_missing")
        return list(dict.fromkeys(blockers)), leak_paths
    missing = [field for field in P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS if field not in receipt]
    if missing:
        blockers.append("pmn_op17_disposal_receipt_missing_required_fields")
    leak_paths = _scan_forbidden_payload_key_paths(receipt, path="pmn_op17_disposal_receipt")
    if leak_paths:
        blockers.append("pmn_op17_disposal_receipt_forbidden_payload_key")
    if _ref_has_local_path_shape(receipt.get("disposal_receipt_ref")):
        blockers.append("pmn_op17_disposal_receipt_ref_has_path_shape")
    if receipt.get("review_session_id") != (op16 or {}).get("review_session_id"):
        blockers.append("pmn_op17_review_session_id_mismatch")
    if receipt.get("operation_receipt_ref") != (op16 or {}).get("operation_receipt_ref"):
        blockers.append("pmn_op17_operation_receipt_ref_mismatch")
    if receipt.get("disposal_status_ref") != "BODY_PURGED":
        blockers.append("pmn_op17_disposal_status_not_body_purged")
    for key in ("body_removed", "reviewer_notes_removed", "temporary_form_removed", "body_free"):
        if receipt.get(key) is not True:
            blockers.append(f"pmn_op17_{key}_not_true")
    for key in ("content_hash_of_body_stored", "body_hash_stored", "local_absolute_path_included", "reviewer_notes_body_stored"):
        if receipt.get(key) is not False:
            blockers.append(f"pmn_op17_{key}_not_false")
    if receipt.get("actual_source_ref") != P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append("pmn_op17_actual_source_ref_not_allowed")
    if not _clean_ref(receipt.get("disposal_receipt_ref"), default="", max_length=220):
        blockers.append("pmn_op17_disposal_receipt_ref_missing")
    return list(dict.fromkeys(blockers)), leak_paths


def build_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    review_session_id: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build PMN-OP17 body-free disposal / purge receipt intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op16 = rating_question_consistency_guard
    if op16 is None:
        op16 = build_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard(
            question_need_observation_row_normalization=question_need_observation_row_normalization,
            readfeel_label_connection_safe_display_blocker_classification=readfeel_label_connection_safe_display_blocker_classification,
            rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
            sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
            actual_operation_receipt_intake=actual_operation_receipt_intake,
            sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
            review_session_id=session_id,
            **kwargs,
        )
    blockers, leak_paths = _pmn_op17_receipt_blockers(op16, disposal_receipt_bodyfree)
    accepted = not blockers
    leak_detected = bool(leak_paths) or any(ref.endswith("not_false") for ref in blockers) or "pmn_op17_disposal_receipt_ref_has_path_shape" in blockers
    receipt = disposal_receipt_bodyfree if isinstance(disposal_receipt_bodyfree, Mapping) else {}
    session_id = _clean_ref((op16 or {}).get("review_session_id"), default=session_id, max_length=220) if isinstance(op16, Mapping) else session_id
    operation_receipt_ref = _clean_ref((op16 or {}).get("operation_receipt_ref"), default="", max_length=220) if isinstance(op16, Mapping) else ""
    status = P7_R54_AHR_POST_MN11_PMN_OP17_READY_STATUS_REF if accepted else P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_BY_LEAK_STATUS_REF if leak_detected else P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_STATUS_REF
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP17_IMPLEMENTED_STEPS if accepted else P7_R54_AHR_POST_MN11_PMN_OP16_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP17_NOT_YET_IMPLEMENTED_STEPS if accepted else P7_R54_AHR_POST_MN11_PMN_OP16_NOT_YET_IMPLEMENTED_STEPS
    disposal_receipt_ref = _clean_ref(receipt.get("disposal_receipt_ref"), default="", max_length=220)
    body_removed = receipt.get("body_removed") is True
    reviewer_notes_removed = receipt.get("reviewer_notes_removed") is True
    temporary_form_removed = receipt.get("temporary_form_removed") is True
    body_hash_stored = receipt.get("body_hash_stored") is True
    local_absolute_path_included = receipt.get("local_absolute_path_included") is True
    reviewer_notes_body_stored = receipt.get("reviewer_notes_body_stored") is True
    content_hash_of_body_stored = receipt.get("content_hash_of_body_stored") is True
    return {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP17_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op16_schema_version": op16.get("schema_version") if isinstance(op16, Mapping) else None,
        "op16_material_ref": op16.get("material_id", "missing_op16") if isinstance(op16, Mapping) else "missing_op16",
        "op16_next_required_step": op16.get("next_required_step") if isinstance(op16, Mapping) else None,
        "op16_rating_question_consistency_guard_passed": op16.get("rating_question_consistency_guard_passed") is True if isinstance(op16, Mapping) else False,
        "op16_consistency_issue_row_count": int(op16.get("consistency_issue_row_count") or 0) if isinstance(op16, Mapping) else 0,
        "op16_operation_receipt_ref": operation_receipt_ref,
        "disposal_purge_receipt_intake_status_ref": status,
        "disposal_purge_receipt_intake_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_STATUS_REFS),
        "disposal_purge_receipt_intake_ready": accepted,
        "disposal_purge_receipt_accepted": accepted,
        "disposal_purge_receipt_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP17_READY_REASON_REFS) if accepted else [],
        "disposal_purge_receipt_blocker_refs": blockers,
        "disposal_purge_receipt_blocker_ref_count": len(blockers),
        "disposal_purge_receipt_intake_ref": P7_R54_AHR_POST_MN11_PMN_OP17_INTAKE_REF,
        "disposal_receipt_required_field_refs": list(P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS),
        "disposal_receipt_required_field_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS),
        "disposal_receipt_ref": disposal_receipt_ref,
        "disposal_receipt_ref_present": bool(disposal_receipt_ref),
        "disposal_receipt_ref_is_bodyfree_ref": bool(disposal_receipt_ref) and not _ref_has_local_path_shape(disposal_receipt_ref),
        "disposal_receipt_ref_has_local_path_shape": _ref_has_local_path_shape(disposal_receipt_ref),
        "disposal_receipt_received_here": isinstance(disposal_receipt_bodyfree, Mapping),
        "disposal_receipt_intaked_here": accepted,
        "operation_receipt_ref": _clean_ref(receipt.get("operation_receipt_ref"), default="", max_length=220),
        "operation_receipt_ref_matches_op16": receipt.get("operation_receipt_ref") == operation_receipt_ref if isinstance(disposal_receipt_bodyfree, Mapping) else False,
        "disposal_status_ref": _clean_ref(receipt.get("disposal_status_ref"), default="", max_length=120),
        "disposal_status_allowed_refs": list(P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_DISPOSAL_STATUS_REFS),
        "disposal_status_is_body_purged": receipt.get("disposal_status_ref") == "BODY_PURGED",
        "packet_materialized_for_review": receipt.get("packet_materialized_for_review") is True,
        "body_removed": body_removed,
        "reviewer_notes_removed": reviewer_notes_removed,
        "temporary_form_removed": temporary_form_removed,
        "content_hash_of_body_stored": content_hash_of_body_stored,
        "body_hash_stored": body_hash_stored,
        "local_absolute_path_included": local_absolute_path_included,
        "reviewer_notes_body_stored": reviewer_notes_body_stored,
        "pause_abort_status_ref": _clean_ref(receipt.get("pause_abort_status_ref"), default="", max_length=180),
        "retention_policy_ref": _clean_ref(receipt.get("retention_policy_ref"), default="", max_length=220),
        "expiration_policy_ref": _clean_ref(receipt.get("expiration_policy_ref"), default="", max_length=220),
        "actual_source_ref": _clean_ref(receipt.get("actual_source_ref"), default="", max_length=180),
        "actual_source_allowed_ref": P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_ACTUAL_SOURCE_REF,
        "actual_source_guard_passed": receipt.get("actual_source_ref") == P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_ACTUAL_SOURCE_REF,
        "disposal_receipt_bodyfree_only": receipt.get("body_free") is True,
        "forbidden_disposal_receipt_payload_key_paths": leak_paths,
        "forbidden_disposal_receipt_payload_key_path_count": len(leak_paths),
        "body_full_packet_lifecycle_closed_bodyfree": accepted,
        "body_removed_without_hash_path_or_reviewer_notes": accepted and body_removed and reviewer_notes_removed and not body_hash_stored and not local_absolute_path_included and not reviewer_notes_body_stored,
        "temporary_form_removed_without_export": accepted and temporary_form_removed,
        "disposal_receipt_does_not_store_body_hash_or_local_path": not body_hash_stored and not content_hash_of_body_stored and not local_absolute_path_included,
        "disposal_receipt_does_not_store_reviewer_notes_body": not reviewer_notes_body_stored,
        "disposal_receipt_does_not_create_question_text": True,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "disposal_receipt_ready_for_final_no_leak_validation_only": accepted,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "pmn_op17_does_not_run_disposal_here": True,
        "pmn_op17_does_not_complete_evidence": True,
        "pmn_op17_does_not_start_p5_p6_p8_r52_or_release": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF if accepted else P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP17 disposal receipt")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_MN11_PMN_OP17_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF, source="P7-R54-AHR-PostMN11-PMN-OP17 disposal receipt")
    ready = bool(data.get("disposal_purge_receipt_intake_ready"))
    blockers = list(data.get("disposal_purge_receipt_blocker_refs") or [])
    leak_paths = list(data.get("forbidden_disposal_receipt_payload_key_paths") or [])
    expected_status = P7_R54_AHR_POST_MN11_PMN_OP17_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_BY_LEAK_STATUS_REF if leak_paths or data.get("local_absolute_path_included") or data.get("body_hash_stored") or data.get("reviewer_notes_body_stored") else P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_STATUS_REF
    if data.get("disposal_purge_receipt_intake_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 status changed")
    if tuple(data.get("disposal_purge_receipt_intake_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP17_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 allowed status refs changed")
    if tuple(data.get("disposal_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP17_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 receipt required fields changed")
    if data.get("disposal_purge_receipt_blocker_ref_count") != len(blockers) or data.get("forbidden_disposal_receipt_payload_key_path_count") != len(leak_paths):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 blocker/leak count changed")
    for key in ("actual_disposal_receipt_materialized_here", "disposal_verified", "actual_review_evidence_complete_from_real_review", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_actual_execution_confirmed", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP17 required false field promoted: {key}")
    for key in ("disposal_receipt_does_not_create_question_text", "actual_review_evidence_complete_from_real_review_still_false", "pmn_op17_does_not_run_disposal_here", "pmn_op17_does_not_complete_evidence", "pmn_op17_does_not_start_p5_p6_p8_r52_or_release", "current_actual_review_basis_remains_264_85_258_171"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP17 required true field changed: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 basis changed")
    if ready:
        for key in ("op16_rating_question_consistency_guard_passed", "disposal_purge_receipt_accepted", "disposal_receipt_ref_present", "disposal_receipt_ref_is_bodyfree_ref", "disposal_receipt_received_here", "disposal_receipt_intaked_here", "operation_receipt_ref_matches_op16", "disposal_status_is_body_purged", "body_removed", "reviewer_notes_removed", "temporary_form_removed", "actual_source_guard_passed", "disposal_receipt_bodyfree_only", "body_full_packet_lifecycle_closed_bodyfree", "body_removed_without_hash_path_or_reviewer_notes", "temporary_form_removed_without_export", "disposal_receipt_does_not_store_body_hash_or_local_path", "disposal_receipt_does_not_store_reviewer_notes_body", "disposal_receipt_ready_for_final_no_leak_validation_only"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP17 ready field changed: {key}")
        for key in ("disposal_receipt_ref_has_local_path_shape", "content_hash_of_body_stored", "body_hash_stored", "local_absolute_path_included", "reviewer_notes_body_stored"):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP17 leak false field changed: {key}")
        if data.get("disposal_purge_receipt_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP17_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 ready reasons changed")
        if blockers or leak_paths:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 ready material cannot have blockers/leaks")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP17_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 ready steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 next step changed")
    else:
        if data.get("disposal_purge_receipt_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 blocked material cannot carry ready reasons")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 blocked material must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP17 blocked next step changed")
    return True


def build_p7_r54_ahr_post_mn11_actual_operation_rating_question_consistency_guard_bodyfree(
    *,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard(
        question_need_observation_row_normalization=question_need_observation_row_normalization,
        readfeel_label_connection_safe_display_blocker_classification=readfeel_label_connection_safe_display_blocker_classification,
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_rating_question_consistency_guard_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_disposal_purge_receipt_intake_bodyfree(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake(
        rating_question_consistency_guard=rating_question_consistency_guard,
        disposal_receipt_bodyfree=disposal_receipt_bodyfree,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_disposal_purge_receipt_intake_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(data)


# ---------------------------------------------------------------------------
# PMN-OP18 / PMN-OP19 final no-leak validation and evidence-complete predicate
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_MN11_PMN_OP18_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP19_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op19_actual_review_evidence_complete_predicate.bodyfree.v1"
)

P7_R54_AHR_POST_MN11_PMN_OP18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:19]
)
P7_R54_AHR_POST_MN11_PMN_OP18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[19:]
)
P7_R54_AHR_POST_MN11_PMN_OP19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:20]
)
P7_R54_AHR_POST_MN11_PMN_OP19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[20:]
)

P7_R54_AHR_POST_MN11_PMN_OP18_READY_STATUS_REF: Final = (
    "PMN_OP18_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_PASSED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP18_FAILED_STATUS_REF: Final = (
    "PMN_OP18_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_FAILED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_STATUS_REF: Final = (
    "PMN_OP18_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP18_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP18_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP18_FAILED_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP18_VALIDATION_REF: Final = (
    "postmn11_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP18_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op17_disposal_purge_receipt_intaked_bodyfree",
    "bodyfree_artifacts_scanned_without_body_question_path_hash_or_terminal_output",
    "no_touch_contract_remained_false_for_api_db_rn_runtime_response_key_p8_r52_release",
    "disposal_verified_only_after_final_no_leak_validation",
    "evidence_complete_predicate_required_next_without_downstream_promotion",
)
P7_R54_AHR_POST_MN11_PMN_OP18_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "disposal_verified",
)
P7_R54_AHR_POST_MN11_PMN_OP18_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op17_schema_version", "op17_material_ref", "op17_next_required_step", "op17_disposal_purge_receipt_intake_ready",
    "op17_disposal_purge_receipt_accepted", "op17_disposal_receipt_ref", "op17_disposal_status_ref",
    "op17_actual_source_guard_passed", "op17_body_full_packet_lifecycle_closed_bodyfree",
    "op17_disposal_verified", "final_no_leak_validation_status_ref", "final_no_leak_validation_allowed_status_refs",
    "final_no_leak_validation_evaluated", "final_no_leak_validation_passed", "final_no_leak_validation_reason_refs",
    "final_no_leak_validation_step_blocker_refs", "final_no_leak_validation_step_blocker_ref_count",
    "final_no_leak_validation_ref", "scanned_artifact_refs", "scanned_artifact_ref_count", "scanned_artifact_count",
    "forbidden_payload_key_paths", "forbidden_payload_key_path_count", "body_leak_refs", "body_leak_ref_count",
    "question_text_leak_refs", "question_text_leak_ref_count", "path_or_hash_leak_refs", "path_or_hash_leak_ref_count",
    "terminal_output_leak_refs", "terminal_output_leak_ref_count", "no_touch_contract_mutation_refs",
    "no_touch_contract_mutation_ref_count", "no_body_leak_validation_passed", "no_question_text_validation_passed",
    "no_path_hash_validation_passed", "no_terminal_output_body_validation_passed", "no_touch_validation_passed",
    "all_scanned_artifacts_bodyfree_only", "disposal_verified", "final_validation_does_not_complete_evidence",
    "final_validation_does_not_start_p8", "final_validation_does_not_execute_r52", "final_validation_does_not_touch_api_db_rn_runtime",
    "actual_review_evidence_complete_from_real_review_still_false", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_mn11_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP19_READY_STATUS_REF: Final = (
    "PMN_OP19_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_PASSED_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_STATUS_REF: Final = (
    "PMN_OP19_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP19_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_or_retry_actual_local_only_human_review_operation_before_downstream_decision"
)
P7_R54_AHR_POST_MN11_PMN_OP19_PREDICATE_REF: Final = (
    "postmn11_actual_review_evidence_complete_predicate_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP19_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "actual_source_guard_passed_bodyfree",
    "actual_person_local_only_human_review_receipt_and_24_counts_present",
    "sanitized_rating_and_question_observation_rows_24_each_bodyfree",
    "disposal_verified_and_final_no_leak_validation_passed_bodyfree",
    "consistency_guard_passed_without_p8_escape",
    "downstream_manual_decision_hold_required_no_auto_promotion",
)
P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "disposal_verified",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_review",
)
P7_R54_AHR_POST_MN11_PMN_OP19_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op11_schema_version", "op11_material_ref", "op11_next_required_step", "op11_operation_receipt_accepted",
    "op11_actual_source_guard_passed", "op11_actual_human_review_executed_by_person", "op11_reviewed_case_count",
    "op11_selection_row_count", "op12_schema_version", "op12_material_ref", "op12_next_required_step",
    "op12_sanitized_review_result_rows_intake_ready", "op12_sanitized_review_result_row_count",
    "op13_schema_version", "op13_material_ref", "op13_next_required_step", "op13_rating_row_normalization_ready",
    "op13_rating_row_count", "op15_schema_version", "op15_material_ref", "op15_next_required_step",
    "op15_question_need_observation_row_normalization_ready", "op15_question_need_observation_row_count",
    "op16_schema_version", "op16_material_ref", "op16_next_required_step", "op16_rating_question_consistency_guard_passed",
    "op16_consistency_issue_row_count", "op18_schema_version", "op18_material_ref", "op18_next_required_step",
    "op18_final_no_leak_validation_passed", "op18_disposal_verified", "op18_no_body_leak_validation_passed",
    "op18_no_question_text_validation_passed", "op18_no_path_hash_validation_passed", "op18_no_touch_validation_passed",
    "actual_review_evidence_complete_predicate_status_ref", "actual_review_evidence_complete_predicate_allowed_status_refs",
    "actual_review_evidence_complete_predicate_evaluated", "actual_review_evidence_complete_predicate_passed",
    "actual_review_evidence_complete_predicate_reason_refs", "actual_review_evidence_complete_predicate_blocker_refs",
    "actual_review_evidence_complete_predicate_blocker_ref_count", "actual_review_evidence_complete_predicate_ref",
    "required_case_count", "actual_source_guard_passed", "actual_human_review_executed_by_person", "reviewed_case_count",
    "reviewed_case_count_is_24", "selection_row_count", "selection_row_count_is_24", "sanitized_review_result_row_count",
    "sanitized_review_result_row_count_is_24", "rating_row_count", "rating_row_count_is_24", "question_need_observation_row_count",
    "question_need_observation_row_count_is_24", "disposal_verified", "no_body_leak_validation_passed",
    "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_touch_validation_passed",
    "consistency_guard_passed", "consistency_issue_row_count", "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_review", "evidence_complete_does_not_finalize_p5",
    "evidence_complete_does_not_start_p6", "evidence_complete_does_not_start_p8",
    "evidence_complete_does_not_request_or_execute_r52", "evidence_complete_does_not_complete_p7_or_release",
    "downstream_manual_decision_hold_required", "p5_human_blind_qa_confirmed_final", "p5_confirmed_final",
    "p5_final_allowed", "p6_limited_human_readfeel_start_allowed", "p6_start_allowed", "p8_start_allowed",
    "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _dedupe_bodyfree_refs(values: Sequence[str]) -> list[str]:
    return [item for item in dict.fromkeys(values) if item]


def _pmn_op18_artifact_ref(value: Any, *, index: int) -> str:
    if isinstance(value, Mapping):
        for key in ("material_id", "operation_step_ref", "policy_section", "schema_version"):
            ref = _clean_ref(value.get(key), default="", max_length=220)
            if ref:
                return ref
    return f"postmn11-pmn-op18-scanned-artifact-{index:03d}"


def _pmn_op18_leak_bucket(path_ref: str) -> str:
    lowered = path_ref.lower()
    if any(token in lowered for token in ("question", "draft_question", "answer_body")):
        return "question"
    if any(token in lowered for token in ("path", "hash", "absolute_path", "file_path")):
        return "path_hash"
    if any(token in lowered for token in ("terminal", "stdout", "stderr", "traceback")):
        return "terminal"
    return "body"


def _pmn_op18_scan_artifacts(artifacts: Sequence[Any]) -> tuple[list[str], list[str], list[str], list[str], list[str], list[str], list[str]]:
    scanned_refs: list[str] = []
    forbidden_paths: list[str] = []
    body_leaks: list[str] = []
    question_leaks: list[str] = []
    path_hash_leaks: list[str] = []
    terminal_leaks: list[str] = []
    no_touch_mutations: list[str] = []
    for index, artifact in enumerate(artifacts, start=1):
        artifact_ref = _pmn_op18_artifact_ref(artifact, index=index)
        scanned_refs.append(artifact_ref)
        paths = _scan_forbidden_payload_key_paths(artifact, path=artifact_ref)
        forbidden_paths.extend(paths)
        for path_ref in paths:
            bucket = _pmn_op18_leak_bucket(path_ref)
            if bucket == "question":
                question_leaks.append(path_ref)
            elif bucket == "path_hash":
                path_hash_leaks.append(path_ref)
            elif bucket == "terminal":
                terminal_leaks.append(path_ref)
            else:
                body_leaks.append(path_ref)
        if not isinstance(artifact, Mapping):
            continue
        for marker_key in P7_R54_AHR_POST_MN11_BODY_FREE_MARKER_REFS:
            if artifact.get(marker_key) is True:
                marker_ref = f"{artifact_ref}.{marker_key}"
                bucket = _pmn_op18_leak_bucket(marker_ref)
                if bucket == "question":
                    question_leaks.append(marker_ref)
                elif bucket == "path_hash":
                    path_hash_leaks.append(marker_ref)
                elif bucket == "terminal":
                    terminal_leaks.append(marker_ref)
                else:
                    body_leaks.append(marker_ref)
        for key in ("reviewer_notes_body_stored", "reviewer_free_text_included", "raw_input_included", "returned_emlis_body_included", "history_body_included", "comment_text_body_included"):
            if artifact.get(key) is True:
                body_leaks.append(f"{artifact_ref}.{key}")
        for key in ("question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_materialized_here", "question_answer_storage_materialized_here"):
            if artifact.get(key) is True:
                question_leaks.append(f"{artifact_ref}.{key}")
        for key in ("local_absolute_path_included", "body_hash_included", "body_hash_stored", "content_hash_of_body_stored", "disposal_receipt_ref_has_local_path_shape", "operation_receipt_ref_has_local_path_shape"):
            if artifact.get(key) is True:
                path_hash_leaks.append(f"{artifact_ref}.{key}")
        for key in ("terminal_output_body_included", "stdout_body_included", "stderr_body_included", "traceback_body_included"):
            if artifact.get(key) is True:
                terminal_leaks.append(f"{artifact_ref}.{key}")
        for map_key in ("public_contract", "post_mn11_no_touch_contract"):
            map_value = artifact.get(map_key)
            if isinstance(map_value, Mapping):
                no_touch_mutations.extend(
                    f"{artifact_ref}.{map_key}.{_clean_ref(mutated_key, default='unknown_mutation', max_length=120)}"
                    for mutated_key, mutated_value in map_value.items()
                    if mutated_value is True
                )
        for no_touch_key in P7_R54_AHR_POST_MN11_NO_TOUCH_CONTRACT_REFS:
            if artifact.get(no_touch_key) is True:
                no_touch_mutations.append(f"{artifact_ref}.{no_touch_key}")
        for promotion_key in (
            "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_reintake_execution_started_here",
            "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed",
            "p8_question_api_created", "p8_question_db_created", "p8_question_rn_ui_created", "p8_question_trigger_logic_created",
        ):
            if artifact.get(promotion_key) is True:
                no_touch_mutations.append(f"{artifact_ref}.{promotion_key}")
    return (
        _dedupe_bodyfree_refs(scanned_refs),
        _dedupe_bodyfree_refs(forbidden_paths),
        _dedupe_bodyfree_refs(body_leaks),
        _dedupe_bodyfree_refs(question_leaks),
        _dedupe_bodyfree_refs(path_hash_leaks),
        _dedupe_bodyfree_refs(terminal_leaks),
        _dedupe_bodyfree_refs(no_touch_mutations),
    )


def _pmn_op18_source_blockers(op17: Mapping[str, Any] | None, artifacts: Sequence[Any]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op17, Mapping):
        blockers.append("pmn_op18_disposal_purge_receipt_intake_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake_contract(op17)
        except ValueError:
            blockers.append("pmn_op18_op17_disposal_purge_receipt_intake_invalid")
        if op17.get("disposal_purge_receipt_intake_ready") is not True:
            blockers.append("pmn_op18_op17_disposal_purge_receipt_not_ready")
        if op17.get("disposal_purge_receipt_accepted") is not True:
            blockers.append("pmn_op18_op17_disposal_purge_receipt_not_accepted")
        if op17.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF:
            blockers.append("pmn_op18_op17_next_step_not_final_validation")
        if op17.get("actual_source_guard_passed") is not True:
            blockers.append("pmn_op18_op17_actual_source_guard_not_passed")
    if not artifacts:
        blockers.append("pmn_op18_bodyfree_artifacts_missing")
    return _dedupe_bodyfree_refs(blockers)


def build_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation(
    *,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    bodyfree_artifacts: Sequence[Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    review_session_id: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build PMN-OP18 final body-free no-leak / no-touch validation material."""

    session_id = _safe_review_session_id(review_session_id)
    op17 = disposal_purge_receipt_intake
    if op17 is None:
        op17 = build_p7_r54_ahr_post_mn11_pmn_op17_disposal_purge_receipt_intake(
            rating_question_consistency_guard=rating_question_consistency_guard,
            disposal_receipt_bodyfree=disposal_receipt_bodyfree,
            question_need_observation_row_normalization=question_need_observation_row_normalization,
            readfeel_label_connection_safe_display_blocker_classification=readfeel_label_connection_safe_display_blocker_classification,
            rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
            sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
            actual_operation_receipt_intake=actual_operation_receipt_intake,
            sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
            review_session_id=session_id,
            **kwargs,
        )
    artifact_list = list(bodyfree_artifacts) if bodyfree_artifacts is not None else ([op17] if isinstance(op17, Mapping) else [])
    source_blockers = _pmn_op18_source_blockers(op17 if isinstance(op17, Mapping) else None, artifact_list)
    scanned_refs, forbidden_paths, body_leaks, question_leaks, path_hash_leaks, terminal_leaks, no_touch_mutations = _pmn_op18_scan_artifacts(artifact_list)
    evaluated = not source_blockers
    any_leak_or_mutation = bool(body_leaks or question_leaks or path_hash_leaks or terminal_leaks or no_touch_mutations or forbidden_paths)
    passed = evaluated and not any_leak_or_mutation
    failed = evaluated and any_leak_or_mutation
    status_ref = (
        P7_R54_AHR_POST_MN11_PMN_OP18_READY_STATUS_REF
        if passed
        else P7_R54_AHR_POST_MN11_PMN_OP18_FAILED_STATUS_REF
        if failed
        else P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_STATUS_REF
    )
    op17_map = op17 if isinstance(op17, Mapping) else {}
    session_id = _clean_ref(op17_map.get("review_session_id"), default=session_id, max_length=220)
    blocker_refs = _dedupe_bodyfree_refs(source_blockers)
    implemented_steps = P7_R54_AHR_POST_MN11_PMN_OP18_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_POST_MN11_PMN_OP17_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_MN11_PMN_OP18_NOT_YET_IMPLEMENTED_STEPS if evaluated else P7_R54_AHR_POST_MN11_PMN_OP17_NOT_YET_IMPLEMENTED_STEPS
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP18_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op17_schema_version": op17_map.get("schema_version"),
        "op17_material_ref": op17_map.get("material_id", "postmn11_pmn_op17_disposal_purge_receipt_intake_bodyfree"),
        "op17_next_required_step": op17_map.get("next_required_step"),
        "op17_disposal_purge_receipt_intake_ready": op17_map.get("disposal_purge_receipt_intake_ready") is True,
        "op17_disposal_purge_receipt_accepted": op17_map.get("disposal_purge_receipt_accepted") is True,
        "op17_disposal_receipt_ref": _clean_ref(op17_map.get("disposal_receipt_ref"), default="", max_length=220),
        "op17_disposal_status_ref": _clean_ref(op17_map.get("disposal_status_ref"), default="", max_length=120),
        "op17_actual_source_guard_passed": op17_map.get("actual_source_guard_passed") is True,
        "op17_body_full_packet_lifecycle_closed_bodyfree": op17_map.get("body_full_packet_lifecycle_closed_bodyfree") is True,
        "op17_disposal_verified": op17_map.get("disposal_verified") is True,
        "final_no_leak_validation_status_ref": status_ref,
        "final_no_leak_validation_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP18_ALLOWED_STATUS_REFS),
        "final_no_leak_validation_evaluated": evaluated,
        "final_no_leak_validation_passed": passed,
        "final_no_leak_validation_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP18_READY_REASON_REFS) if passed else [],
        "final_no_leak_validation_step_blocker_refs": blocker_refs,
        "final_no_leak_validation_step_blocker_ref_count": len(blocker_refs),
        "final_no_leak_validation_ref": P7_R54_AHR_POST_MN11_PMN_OP18_VALIDATION_REF,
        "scanned_artifact_refs": scanned_refs,
        "scanned_artifact_ref_count": len(scanned_refs),
        "scanned_artifact_count": len(artifact_list),
        "forbidden_payload_key_paths": forbidden_paths,
        "forbidden_payload_key_path_count": len(forbidden_paths),
        "body_leak_refs": body_leaks,
        "body_leak_ref_count": len(body_leaks),
        "question_text_leak_refs": question_leaks,
        "question_text_leak_ref_count": len(question_leaks),
        "path_or_hash_leak_refs": path_hash_leaks,
        "path_or_hash_leak_ref_count": len(path_hash_leaks),
        "terminal_output_leak_refs": terminal_leaks,
        "terminal_output_leak_ref_count": len(terminal_leaks),
        "no_touch_contract_mutation_refs": no_touch_mutations,
        "no_touch_contract_mutation_ref_count": len(no_touch_mutations),
        "no_body_leak_validation_passed": evaluated and not body_leaks and not forbidden_paths,
        "no_question_text_validation_passed": evaluated and not question_leaks,
        "no_path_hash_validation_passed": evaluated and not path_hash_leaks,
        "no_terminal_output_body_validation_passed": evaluated and not terminal_leaks,
        "no_touch_validation_passed": evaluated and not no_touch_mutations,
        "all_scanned_artifacts_bodyfree_only": evaluated and not (body_leaks or question_leaks or path_hash_leaks or terminal_leaks or forbidden_paths),
        "disposal_verified": passed and op17_map.get("disposal_purge_receipt_accepted") is True,
        "final_validation_does_not_complete_evidence": True,
        "final_validation_does_not_start_p8": True,
        "final_validation_does_not_execute_r52": True,
        "final_validation_does_not_touch_api_db_rn_runtime": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF if passed else P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["disposal_verified"] = passed and op17_map.get("disposal_purge_receipt_accepted") is True
    material["actual_review_evidence_complete_from_real_review"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_MN11_PMN_OP18_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP18")
    return material


def assert_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP18_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP18")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP18_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP18",
        allowed_true_flag_refs=P7_R54_AHR_POST_MN11_PMN_OP18_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if tuple(data.get("final_no_leak_validation_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP18_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 allowed status refs changed")
    status_ref = data.get("final_no_leak_validation_status_ref")
    evaluated = status_ref in (P7_R54_AHR_POST_MN11_PMN_OP18_READY_STATUS_REF, P7_R54_AHR_POST_MN11_PMN_OP18_FAILED_STATUS_REF)
    passed = status_ref == P7_R54_AHR_POST_MN11_PMN_OP18_READY_STATUS_REF
    failed = status_ref == P7_R54_AHR_POST_MN11_PMN_OP18_FAILED_STATUS_REF
    blockers = list(data.get("final_no_leak_validation_step_blocker_refs") or [])
    if data.get("final_no_leak_validation_evaluated") is not evaluated:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 evaluated flag changed")
    if data.get("final_no_leak_validation_passed") is not passed:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 passed flag changed")
    if data.get("final_no_leak_validation_step_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 blocker count changed")
    for refs_key, count_key in (
        ("scanned_artifact_refs", "scanned_artifact_ref_count"),
        ("forbidden_payload_key_paths", "forbidden_payload_key_path_count"),
        ("body_leak_refs", "body_leak_ref_count"),
        ("question_text_leak_refs", "question_text_leak_ref_count"),
        ("path_or_hash_leak_refs", "path_or_hash_leak_ref_count"),
        ("terminal_output_leak_refs", "terminal_output_leak_ref_count"),
        ("no_touch_contract_mutation_refs", "no_touch_contract_mutation_ref_count"),
    ):
        if data.get(count_key) != len(data.get(refs_key) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP18 {count_key} changed")
    for key in ("final_validation_does_not_complete_evidence", "final_validation_does_not_start_p8", "final_validation_does_not_execute_r52", "final_validation_does_not_touch_api_db_rn_runtime", "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP18 required boundary changed: {key}")
    if data.get("actual_review_evidence_complete_from_real_review") is not False or data.get("actual_review_evidence_complete") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 cannot complete evidence")
    if not passed and data.get("disposal_verified") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 cannot verify disposal without passed final validation")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 basis changed")
    if passed:
        if blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 passed material cannot carry blockers")
        if data.get("final_no_leak_validation_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP18_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 passed reasons changed")
        for key in ("op17_disposal_purge_receipt_intake_ready", "op17_disposal_purge_receipt_accepted", "op17_actual_source_guard_passed", "op17_body_full_packet_lifecycle_closed_bodyfree", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_terminal_output_body_validation_passed", "no_touch_validation_passed", "all_scanned_artifacts_bodyfree_only", "disposal_verified"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP18 passed field changed: {key}")
        for refs_key in ("forbidden_payload_key_paths", "body_leak_refs", "question_text_leak_refs", "path_or_hash_leak_refs", "terminal_output_leak_refs", "no_touch_contract_mutation_refs"):
            if data.get(refs_key) != []:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP18 passed material cannot carry {refs_key}")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP18_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 passed steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 passed next step changed")
    elif failed:
        if not (data.get("forbidden_payload_key_paths") or data.get("body_leak_refs") or data.get("question_text_leak_refs") or data.get("path_or_hash_leak_refs") or data.get("terminal_output_leak_refs") or data.get("no_touch_contract_mutation_refs")):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 failed material must carry leak or mutation refs")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 failed next step changed")
    else:
        if status_ref != P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 blocked material must carry blockers")
        if data.get("disposal_verified") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 blocked material cannot verify disposal")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP18 blocked next step changed")
    return True


def _pmn_op19_source_blockers(
    *,
    op11: Mapping[str, Any] | None,
    op12: Mapping[str, Any] | None,
    op13: Mapping[str, Any] | None,
    op15: Mapping[str, Any] | None,
    op16: Mapping[str, Any] | None,
    op18: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op11, Mapping):
        blockers.append("pmn_op19_op11_actual_operation_receipt_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op11_actual_operation_receipt_intake_contract(op11)
        except ValueError:
            blockers.append("pmn_op19_op11_actual_operation_receipt_invalid")
        if op11.get("operation_receipt_accepted") is not True:
            blockers.append("pmn_op19_op11_operation_receipt_not_accepted")
        if op11.get("actual_source_guard_passed") is not True:
            blockers.append("pmn_op19_op11_actual_source_guard_not_passed")
        if op11.get("actual_human_review_executed_by_person") is not True:
            blockers.append("pmn_op19_op11_actual_human_review_not_executed_by_person")
        if op11.get("reviewed_case_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append("pmn_op19_reviewed_case_count_not_24")
        if op11.get("selection_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append("pmn_op19_selection_row_count_not_24")
    if not isinstance(op12, Mapping):
        blockers.append("pmn_op19_op12_sanitized_review_result_rows_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard_contract(op12)
        except ValueError:
            blockers.append("pmn_op19_op12_sanitized_review_result_rows_invalid")
        if op12.get("sanitized_review_result_rows_intake_ready") is not True:
            blockers.append("pmn_op19_op12_sanitized_rows_not_ready")
        if op12.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append("pmn_op19_sanitized_review_result_row_count_not_24")
    if not isinstance(op13, Mapping):
        blockers.append("pmn_op19_op13_rating_rows_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary_contract(op13)
        except ValueError:
            blockers.append("pmn_op19_op13_rating_rows_invalid")
        if op13.get("rating_row_normalization_ready") is not True:
            blockers.append("pmn_op19_op13_rating_rows_not_ready")
        if op13.get("rating_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append("pmn_op19_rating_row_count_not_24")
    if not isinstance(op15, Mapping):
        blockers.append("pmn_op19_op15_question_need_observation_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(op15)
        except ValueError:
            blockers.append("pmn_op19_op15_question_need_observation_invalid")
        if op15.get("question_need_observation_row_normalization_ready") is not True:
            blockers.append("pmn_op19_op15_question_need_observation_not_ready")
        if op15.get("question_need_observation_row_count") != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
            blockers.append("pmn_op19_question_need_observation_row_count_not_24")
        if op15.get("p8_start_allowed") is not False:
            blockers.append("pmn_op19_op15_p8_start_allowed_not_false")
    if not isinstance(op16, Mapping):
        blockers.append("pmn_op19_op16_rating_question_consistency_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(op16)
        except ValueError:
            blockers.append("pmn_op19_op16_rating_question_consistency_invalid")
        if op16.get("rating_question_consistency_guard_passed") is not True:
            blockers.append("pmn_op19_op16_rating_question_consistency_not_passed")
        if op16.get("consistency_issue_row_count") != 0:
            blockers.append("pmn_op19_consistency_issue_row_count_not_zero")
    if not isinstance(op18, Mapping):
        blockers.append("pmn_op19_op18_final_no_leak_validation_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(op18)
        except ValueError:
            blockers.append("pmn_op19_op18_final_no_leak_validation_invalid")
        if op18.get("final_no_leak_validation_passed") is not True:
            blockers.append("pmn_op19_op18_final_no_leak_validation_not_passed")
        if op18.get("disposal_verified") is not True:
            blockers.append("pmn_op19_disposal_not_verified")
        for key, blocker in (
            ("no_body_leak_validation_passed", "pmn_op19_no_body_leak_validation_not_passed"),
            ("no_question_text_validation_passed", "pmn_op19_no_question_text_validation_not_passed"),
            ("no_path_hash_validation_passed", "pmn_op19_no_path_hash_validation_not_passed"),
            ("no_touch_validation_passed", "pmn_op19_no_touch_validation_not_passed"),
        ):
            if op18.get(key) is not True:
                blockers.append(blocker)
    return _dedupe_bodyfree_refs(blockers)


def build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate(
    *,
    final_no_body_no_question_no_path_no_hash_no_touch_validation: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    bodyfree_artifacts: Sequence[Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    review_session_id: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build PMN-OP19 body-free actual_review_evidence_complete predicate material."""

    session_id = _safe_review_session_id(review_session_id)
    op11 = actual_operation_receipt_intake
    op12 = sanitized_review_result_rows_intake
    op13 = rating_row_normalization_threshold_summary
    op15 = question_need_observation_row_normalization
    op16 = rating_question_consistency_guard
    op18 = final_no_body_no_question_no_path_no_hash_no_touch_validation
    if op12 is None and sanitized_review_result_rows_bodyfree is not None:
        op12 = build_p7_r54_ahr_post_mn11_pmn_op12_sanitized_review_result_rows_intake_provenance_guard(
            actual_operation_receipt_intake=op11,
            sanitized_review_result_rows_bodyfree=sanitized_review_result_rows_bodyfree,
            review_session_id=session_id,
            **kwargs,
        )
    if op13 is None and isinstance(op12, Mapping):
        op13 = build_p7_r54_ahr_post_mn11_pmn_op13_rating_row_normalization_threshold_summary(
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    if op15 is None and isinstance(op12, Mapping):
        op15 = build_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization(
            readfeel_label_connection_safe_display_blocker_classification=kwargs.get("readfeel_label_connection_safe_display_blocker_classification"),
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    if op16 is None and isinstance(op15, Mapping) and isinstance(op13, Mapping):
        op16 = build_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard(
            question_need_observation_row_normalization=op15,
            rating_row_normalization_threshold_summary=op13,
            sanitized_review_result_rows_intake=op12,
            review_session_id=session_id,
        )
    if op18 is None:
        op18 = build_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation(
            disposal_purge_receipt_intake=disposal_purge_receipt_intake,
            bodyfree_artifacts=bodyfree_artifacts,
            rating_question_consistency_guard=op16,
            disposal_receipt_bodyfree=disposal_receipt_bodyfree,
            sanitized_review_result_rows_intake=op12,
            rating_row_normalization_threshold_summary=op13,
            question_need_observation_row_normalization=op15,
            actual_operation_receipt_intake=op11,
            review_session_id=session_id,
            **kwargs,
        )
    blockers = _pmn_op19_source_blockers(
        op11=op11 if isinstance(op11, Mapping) else None,
        op12=op12 if isinstance(op12, Mapping) else None,
        op13=op13 if isinstance(op13, Mapping) else None,
        op15=op15 if isinstance(op15, Mapping) else None,
        op16=op16 if isinstance(op16, Mapping) else None,
        op18=op18 if isinstance(op18, Mapping) else None,
    )
    passed = not blockers
    status_ref = P7_R54_AHR_POST_MN11_PMN_OP19_READY_STATUS_REF if passed else P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_STATUS_REF
    op11_map = op11 if isinstance(op11, Mapping) else {}
    op12_map = op12 if isinstance(op12, Mapping) else {}
    op13_map = op13 if isinstance(op13, Mapping) else {}
    op15_map = op15 if isinstance(op15, Mapping) else {}
    op16_map = op16 if isinstance(op16, Mapping) else {}
    op18_map = op18 if isinstance(op18, Mapping) else {}
    session_id = _clean_ref(op18_map.get("review_session_id") or op16_map.get("review_session_id") or op11_map.get("review_session_id"), default=session_id, max_length=220)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP19_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op11_schema_version": op11_map.get("schema_version"),
        "op11_material_ref": op11_map.get("material_id", "postmn11_pmn_op11_actual_operation_receipt_intake_bodyfree"),
        "op11_next_required_step": op11_map.get("next_required_step"),
        "op11_operation_receipt_accepted": op11_map.get("operation_receipt_accepted") is True,
        "op11_actual_source_guard_passed": op11_map.get("actual_source_guard_passed") is True,
        "op11_actual_human_review_executed_by_person": op11_map.get("actual_human_review_executed_by_person") is True,
        "op11_reviewed_case_count": _safe_int(op11_map.get("reviewed_case_count")),
        "op11_selection_row_count": _safe_int(op11_map.get("selection_row_count")),
        "op12_schema_version": op12_map.get("schema_version"),
        "op12_material_ref": op12_map.get("material_id", "postmn11_pmn_op12_sanitized_review_result_rows_intake_bodyfree"),
        "op12_next_required_step": op12_map.get("next_required_step"),
        "op12_sanitized_review_result_rows_intake_ready": op12_map.get("sanitized_review_result_rows_intake_ready") is True,
        "op12_sanitized_review_result_row_count": _safe_int(op12_map.get("sanitized_review_result_row_count")),
        "op13_schema_version": op13_map.get("schema_version"),
        "op13_material_ref": op13_map.get("material_id", "postmn11_pmn_op13_rating_row_normalization_bodyfree"),
        "op13_next_required_step": op13_map.get("next_required_step"),
        "op13_rating_row_normalization_ready": op13_map.get("rating_row_normalization_ready") is True,
        "op13_rating_row_count": _safe_int(op13_map.get("rating_row_count")),
        "op15_schema_version": op15_map.get("schema_version"),
        "op15_material_ref": op15_map.get("material_id", "postmn11_pmn_op15_question_need_observation_row_normalization_bodyfree"),
        "op15_next_required_step": op15_map.get("next_required_step"),
        "op15_question_need_observation_row_normalization_ready": op15_map.get("question_need_observation_row_normalization_ready") is True,
        "op15_question_need_observation_row_count": _safe_int(op15_map.get("question_need_observation_row_count")),
        "op16_schema_version": op16_map.get("schema_version"),
        "op16_material_ref": op16_map.get("material_id", "postmn11_pmn_op16_rating_question_consistency_guard_bodyfree"),
        "op16_next_required_step": op16_map.get("next_required_step"),
        "op16_rating_question_consistency_guard_passed": op16_map.get("rating_question_consistency_guard_passed") is True,
        "op16_consistency_issue_row_count": _safe_int(op16_map.get("consistency_issue_row_count")),
        "op18_schema_version": op18_map.get("schema_version"),
        "op18_material_ref": op18_map.get("material_id", "postmn11_pmn_op18_final_no_leak_validation_bodyfree"),
        "op18_next_required_step": op18_map.get("next_required_step"),
        "op18_final_no_leak_validation_passed": op18_map.get("final_no_leak_validation_passed") is True,
        "op18_disposal_verified": op18_map.get("disposal_verified") is True,
        "op18_no_body_leak_validation_passed": op18_map.get("no_body_leak_validation_passed") is True,
        "op18_no_question_text_validation_passed": op18_map.get("no_question_text_validation_passed") is True,
        "op18_no_path_hash_validation_passed": op18_map.get("no_path_hash_validation_passed") is True,
        "op18_no_touch_validation_passed": op18_map.get("no_touch_validation_passed") is True,
        "actual_review_evidence_complete_predicate_status_ref": status_ref,
        "actual_review_evidence_complete_predicate_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_STATUS_REFS),
        "actual_review_evidence_complete_predicate_evaluated": True,
        "actual_review_evidence_complete_predicate_passed": passed,
        "actual_review_evidence_complete_predicate_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP19_READY_REASON_REFS) if passed else [],
        "actual_review_evidence_complete_predicate_blocker_refs": blockers,
        "actual_review_evidence_complete_predicate_blocker_ref_count": len(blockers),
        "actual_review_evidence_complete_predicate_ref": P7_R54_AHR_POST_MN11_PMN_OP19_PREDICATE_REF,
        "required_case_count": P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "actual_source_guard_passed": passed and op11_map.get("actual_source_guard_passed") is True,
        "actual_human_review_executed_by_person": passed and op11_map.get("actual_human_review_executed_by_person") is True,
        "reviewed_case_count": _safe_int(op11_map.get("reviewed_case_count")) if passed else 0,
        "reviewed_case_count_is_24": passed and _safe_int(op11_map.get("reviewed_case_count")) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "selection_row_count": _safe_int(op11_map.get("selection_row_count")) if passed else 0,
        "selection_row_count_is_24": passed and _safe_int(op11_map.get("selection_row_count")) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count": _safe_int(op12_map.get("sanitized_review_result_row_count")) if passed else 0,
        "sanitized_review_result_row_count_is_24": passed and _safe_int(op12_map.get("sanitized_review_result_row_count")) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_int(op13_map.get("rating_row_count")) if passed else 0,
        "rating_row_count_is_24": passed and _safe_int(op13_map.get("rating_row_count")) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "question_need_observation_row_count": _safe_int(op15_map.get("question_need_observation_row_count")) if passed else 0,
        "question_need_observation_row_count_is_24": passed and _safe_int(op15_map.get("question_need_observation_row_count")) == P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT,
        "disposal_verified": passed and op18_map.get("disposal_verified") is True,
        "no_body_leak_validation_passed": passed and op18_map.get("no_body_leak_validation_passed") is True,
        "no_question_text_validation_passed": passed and op18_map.get("no_question_text_validation_passed") is True,
        "no_path_hash_validation_passed": passed and op18_map.get("no_path_hash_validation_passed") is True,
        "no_touch_validation_passed": passed and op18_map.get("no_touch_validation_passed") is True,
        "consistency_guard_passed": passed and op16_map.get("rating_question_consistency_guard_passed") is True,
        "consistency_issue_row_count": _safe_int(op16_map.get("consistency_issue_row_count")) if passed else 0,
        "actual_review_evidence_complete": passed,
        "actual_review_evidence_complete_from_real_review": passed,
        "evidence_complete_does_not_finalize_p5": True,
        "evidence_complete_does_not_start_p6": True,
        "evidence_complete_does_not_start_p8": True,
        "evidence_complete_does_not_request_or_execute_r52": True,
        "evidence_complete_does_not_complete_p7_or_release": True,
        "downstream_manual_decision_hold_required": True,
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
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP19_IMPLEMENTED_STEPS if passed else P7_R54_AHR_POST_MN11_PMN_OP18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP19_NOT_YET_IMPLEMENTED_STEPS if passed else P7_R54_AHR_POST_MN11_PMN_OP18_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF if passed else P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["disposal_verified"] = passed and op18_map.get("disposal_verified") is True
    material["actual_review_evidence_complete"] = passed
    material["actual_review_evidence_complete_from_real_review"] = passed
    material["actual_human_review_run_here"] = False
    material["actual_human_review_complete"] = False
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
    _required_fields_present(material, required=P7_R54_AHR_POST_MN11_PMN_OP19_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP19")
    return material


def assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP19_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP19")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP19_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP19",
        allowed_true_flag_refs=P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if tuple(data.get("actual_review_evidence_complete_predicate_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP19_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 allowed status refs changed")
    status_ref = data.get("actual_review_evidence_complete_predicate_status_ref")
    passed = status_ref == P7_R54_AHR_POST_MN11_PMN_OP19_READY_STATUS_REF
    blockers = list(data.get("actual_review_evidence_complete_predicate_blocker_refs") or [])
    if data.get("actual_review_evidence_complete_predicate_evaluated") is not True:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 predicate must be evaluated")
    if data.get("actual_review_evidence_complete_predicate_passed") is not passed:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 passed flag changed")
    if data.get("actual_review_evidence_complete_predicate_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 blocker count changed")
    for key in ("evidence_complete_does_not_finalize_p5", "evidence_complete_does_not_start_p6", "evidence_complete_does_not_start_p8", "evidence_complete_does_not_request_or_execute_r52", "evidence_complete_does_not_complete_p7_or_release", "downstream_manual_decision_hold_required", "current_actual_review_basis_remains_264_85_258_171"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP19 required boundary changed: {key}")
    for key in ("actual_human_review_run_here", "actual_human_review_complete", "p5_human_blind_qa_confirmed_final", "p5_confirmed_final", "p5_final_allowed", "p6_limited_human_readfeel_start_allowed", "p6_start_allowed", "p8_start_allowed", "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP19 downstream promotion changed: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 basis changed")
    if passed:
        if blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 passed predicate cannot carry blockers")
        if data.get("actual_review_evidence_complete_predicate_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP19_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 passed reasons changed")
        for key in ("actual_source_guard_passed", "actual_human_review_executed_by_person", "reviewed_case_count_is_24", "selection_row_count_is_24", "sanitized_review_result_row_count_is_24", "rating_row_count_is_24", "question_need_observation_row_count_is_24", "disposal_verified", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_touch_validation_passed", "consistency_guard_passed", "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP19 passed field changed: {key}")
        for count_key in ("reviewed_case_count", "selection_row_count", "sanitized_review_result_row_count", "rating_row_count", "question_need_observation_row_count"):
            if data.get(count_key) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP19 {count_key} must be 24")
        if data.get("consistency_issue_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 passed predicate cannot carry consistency issues")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP19_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 passed steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 passed next step changed")
    else:
        if status_ref != P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 blocked predicate must carry blockers")
        if data.get("actual_review_evidence_complete") is not False or data.get("actual_review_evidence_complete_from_real_review") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 blocked predicate cannot complete evidence")
        if data.get("disposal_verified") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 blocked predicate cannot verify disposal")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP19 blocked next step changed")
    return True


def build_p7_r54_ahr_post_mn11_actual_operation_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree(
    *,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    bodyfree_artifacts: Sequence[Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation(
        disposal_purge_receipt_intake=disposal_purge_receipt_intake,
        bodyfree_artifacts=bodyfree_artifacts,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op18_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_actual_review_evidence_complete_predicate_bodyfree(
    *,
    final_no_body_no_question_no_path_no_hash_no_touch_validation: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    rating_row_normalization_threshold_summary: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate(
        final_no_body_no_question_no_path_no_hash_no_touch_validation=final_no_body_no_question_no_path_no_hash_no_touch_validation,
        actual_operation_receipt_intake=actual_operation_receipt_intake,
        sanitized_review_result_rows_intake=sanitized_review_result_rows_intake,
        rating_row_normalization_threshold_summary=rating_row_normalization_threshold_summary,
        question_need_observation_row_normalization=question_need_observation_row_normalization,
        rating_question_consistency_guard=rating_question_consistency_guard,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_actual_review_evidence_complete_predicate_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(data)


# ---------------------------------------------------------------------------
# PMN-OP20 / PMN-OP21 candidate-only separation and PostCR22 re-entry mapping
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_MN11_PMN_OP20_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op20_p5_p6_p8_r52_candidate_only_separation.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP21_EXISTING_POSTCR22_EX07_EX18_REENTRY_MAPPING_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping.bodyfree.v1"
)

P7_R54_AHR_POST_MN11_PMN_OP20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:21]
)
P7_R54_AHR_POST_MN11_PMN_OP20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[21:]
)
P7_R54_AHR_POST_MN11_PMN_OP21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:22]
)
P7_R54_AHR_POST_MN11_PMN_OP21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[22:]
)

P7_R54_AHR_POST_MN11_PMN_OP20_READY_STATUS_REF: Final = (
    "PMN_OP20_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_STATUS_REF: Final = (
    "PMN_OP20_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP20_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP20_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op20_candidate_only_separation_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP20_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op19_actual_review_evidence_complete_predicate_passed_bodyfree",
    "op14_blocker_classification_and_op16_question_consistency_available_bodyfree",
    "downstream_p5_p6_p8_r52_material_split_into_candidate_only_refs",
    "p5_p6_p8_r52_p7_release_auto_promotion_remains_blocked",
    "existing_postcr22_ex07_ex18_reentry_mapping_required_next_without_execution",
)
P7_R54_AHR_POST_MN11_PMN_OP20_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "disposal_verified",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_review",
)
P7_R54_AHR_POST_MN11_PMN_OP20_DECISION_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_MN11_PMN_OP20_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op19_schema_version", "op19_material_ref", "op19_next_required_step",
    "op19_actual_review_evidence_complete_predicate_status_ref", "op19_actual_review_evidence_complete_predicate_passed",
    "op19_actual_review_evidence_complete", "op19_actual_review_evidence_complete_from_real_review",
    "op19_actual_source_guard_passed", "op19_actual_human_review_executed_by_person", "op19_reviewed_case_count",
    "op19_sanitized_review_result_row_count", "op19_rating_row_count", "op19_question_need_observation_row_count",
    "op19_disposal_verified", "op14_schema_version", "op14_material_ref", "op14_next_required_step",
    "op14_blocker_classification_ready", "op14_no_blocker_case_count", "op14_p5_repair_required_case_count",
    "op14_p4_current_only_repair_required_case_count", "op14_operation_blocked_case_count",
    "op14_safe_display_blocked_case_count", "op14_inconclusive_case_count", "op15_schema_version", "op15_material_ref",
    "op15_next_required_step", "op15_question_need_observation_row_normalization_ready",
    "op15_question_need_observation_row_count", "op15_p8_material_candidate_case_count_bodyfree_only",
    "op16_schema_version", "op16_material_ref", "op16_next_required_step", "op16_rating_question_consistency_guard_passed",
    "op16_consistency_issue_row_count", "candidate_only_separation_status_ref", "candidate_only_separation_allowed_status_refs",
    "candidate_only_separation_ready", "candidate_only_separation_reason_refs", "candidate_only_separation_blocker_refs",
    "candidate_only_separation_blocker_ref_count", "decision_ref_options", "decision_ref_option_count", "selected_decision_refs",
    "selected_decision_ref_count", "p5_confirmed_candidate_bodyfree_only", "p5_confirmed_candidate_case_refs",
    "p5_confirmed_candidate_case_count", "p5_repair_required_before_r52_reintake", "p5_repair_required_case_refs",
    "p5_repair_required_case_count", "p4_current_only_repair_required_before_r52_reintake", "p4_current_only_repair_required_case_refs",
    "p4_current_only_repair_required_case_count", "operation_blocked_case_refs", "operation_blocked_case_count",
    "operation_blocked_body_leak_or_question_text", "operation_blocked_disposal_not_verified",
    "inconclusive_insufficient_material_case_refs", "inconclusive_insufficient_material_case_count",
    "p6_limited_human_readfeel_candidate_only", "p8_question_need_observation_material_candidate_only",
    "p8_material_candidate_case_refs_bodyfree_only", "p8_material_candidate_case_count_bodyfree_only",
    "p8_material_candidate_blocked_by_blocker_case_refs", "p8_material_candidate_blocked_by_blocker_case_count",
    "r52_reintake_handoff_candidate_only", "r52_reintake_handoff_candidate_case_refs",
    "r52_reintake_handoff_candidate_case_count", "candidate_only_separation_does_not_finalize_p5",
    "candidate_only_separation_does_not_start_p6", "candidate_only_separation_does_not_start_p8",
    "candidate_only_separation_does_not_execute_r52", "candidate_only_separation_does_not_complete_p7_or_release",
    "downstream_manual_decision_hold_required", "actual_source_guard_passed", "actual_human_review_executed_by_person",
    "disposal_verified", "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review",
    "actual_human_review_run_here", "actual_human_review_complete", "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final", "p5_final_allowed", "p6_limited_human_readfeel_start_allowed", "p6_start_allowed",
    "p8_start_allowed", "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed",
    "p7_complete", "release_allowed", "r52_reintake_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_mn11_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP21_READY_STATUS_REF: Final = (
    "PMN_OP21_EXISTING_POSTCR22_EX07_EX18_REENTRY_MAPPING_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_STATUS_REF: Final = (
    "PMN_OP21_EXISTING_POSTCR22_EX07_EX18_REENTRY_MAPPING_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP21_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP21_MAPPING_REF: Final = (
    "postmn11_existing_postcr22_ex07_ex18_reentry_mapping_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP21_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op20_candidate_only_separation_ready_bodyfree",
    "postmn11_operation_receipt_rows_rating_question_disposal_validation_mapped_to_existing_ex07_ex18",
    "reentry_mapping_reuses_existing_postcr22_line_without_new_giant_wrapper",
    "reentry_not_executed_here_and_ex18_remains_manual_next_decision_hold",
    "p5_p6_p8_r52_p7_release_auto_promotion_remains_blocked",
)
P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "disposal_verified",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_review",
)
P7_R54_AHR_POST_MN11_PMN_OP21_REENTRY_MAPPING_ROW_REFS: Final[tuple[tuple[str, str, str, str], ...]] = (
    ("actual_operation_receipt", P7_R54_AHR_POST_MN11_PMN_OP11_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX07_STEP_REF, "existing_postcr22_ex07_actual_operation_receipt_intake"),
    ("actual_selection_row_provenance_guard", P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX08_STEP_REF, "existing_postcr22_ex08_actual_selection_row_provenance_guard"),
    ("sanitized_review_result_rows", P7_R54_AHR_POST_MN11_PMN_OP12_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX09_STEP_REF, "existing_postcr22_ex09_sanitized_review_result_rows_intake"),
    ("rating_rows", P7_R54_AHR_POST_MN11_PMN_OP13_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX10_STEP_REF, "existing_postcr22_ex10_rating_row_normalization_threshold_summary"),
    ("blocker_classification", P7_R54_AHR_POST_MN11_PMN_OP14_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX11_STEP_REF, "existing_postcr22_ex11_readfeel_execution_p5_p4_blocker_classification"),
    ("question_need_observation_rows", P7_R54_AHR_POST_MN11_PMN_OP15_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX12_STEP_REF, "existing_postcr22_ex12_question_need_observation_normalization"),
    ("rating_question_consistency", P7_R54_AHR_POST_MN11_PMN_OP16_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX13_STEP_REF, "existing_postcr22_ex13_rating_question_consistency_guard"),
    ("disposal_purge_receipt", P7_R54_AHR_POST_MN11_PMN_OP17_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX14_STEP_REF, "existing_postcr22_ex14_disposal_purge_receipt_intake"),
    ("final_no_leak_validation", P7_R54_AHR_POST_MN11_PMN_OP18_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX15_STEP_REF, "existing_postcr22_ex15_final_no_body_no_question_no_touch_validation"),
    ("actual_review_evidence_complete_predicate", P7_R54_AHR_POST_MN11_PMN_OP19_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX16_STEP_REF, "existing_postcr22_ex16_actual_review_evidence_complete_predicate"),
    ("candidate_only_separation", P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX17_STEP_REF, "existing_postcr22_ex17_p5_p6_p8_r52_candidate_only_separation"),
    ("validation_result_memo_next_decision_hold", P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF, ex.P7_R54_AHR_POST_CR22_EX18_STEP_REF, "existing_postcr22_ex18_validation_command_matrix_result_memo_next_decision_hold"),
)
P7_R54_AHR_POST_MN11_PMN_OP21_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op20_schema_version", "op20_material_ref", "op20_next_required_step", "op20_candidate_only_separation_status_ref",
    "op20_candidate_only_separation_ready", "op20_actual_review_evidence_complete", "op20_actual_review_evidence_complete_from_real_review",
    "op20_selected_decision_refs", "op20_selected_decision_ref_count", "existing_postcr22_ex07_ex18_reentry_mapping_status_ref",
    "existing_postcr22_ex07_ex18_reentry_mapping_allowed_status_refs", "existing_postcr22_ex07_ex18_reentry_mapping_ready",
    "existing_postcr22_ex07_ex18_reentry_mapping_reason_refs", "existing_postcr22_ex07_ex18_reentry_mapping_blocker_refs",
    "existing_postcr22_ex07_ex18_reentry_mapping_blocker_ref_count", "reentry_mapping_ref", "reentry_mapping_rows",
    "reentry_mapping_row_count", "reentry_mapping_role_refs", "reentry_mapping_role_ref_count", "existing_ex_line_reentry_step_refs",
    "existing_ex_line_reentry_step_ref_count", "existing_ex_line_reentry_first_step_ref", "existing_ex_line_reentry_last_step_ref",
    "existing_ex_line_reentry_role_refs", "existing_ex_line_reentry_role_ref_count", "postcr22_ex07_ex18_reentry_executed_here",
    "reentry_executed_here", "reentry_mapping_reuses_existing_postcr22_ex_line", "reentry_mapping_does_not_reimplement_ex_helpers",
    "reentry_mapping_does_not_execute_ex_helpers_here", "postcr22_ex18_ready_is_manual_hold_not_r52_execution",
    "new_giant_wrapper_required", "minimal_bridge_only", "actual_source_guard_passed", "actual_human_review_executed_by_person",
    "disposal_verified", "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review",
    "actual_human_review_run_here", "actual_human_review_complete", "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final", "p5_final_allowed", "p6_limited_human_readfeel_start_allowed", "p6_start_allowed",
    "p8_start_allowed", "r52_reintake_execution_requested_here", "r52_reintake_execution_started_here",
    "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed", "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here", "actual_review_basis_ref",
    "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_mn11_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _pmn_op20_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _pmn_op20_case_ref_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    refs = [_clean_ref(item, default="", max_length=180) for item in value]
    return sorted({ref for ref in refs if ref})


def _pmn_op20_blockers(
    op19: Mapping[str, Any] | None,
    op14: Mapping[str, Any] | None,
    op15: Mapping[str, Any] | None,
    op16: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op19, Mapping):
        blockers.append("pmn_op20_op19_actual_review_evidence_complete_predicate_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op19_actual_review_evidence_complete_predicate_contract(op19)
        except ValueError:
            blockers.append("pmn_op20_op19_actual_review_evidence_complete_predicate_invalid")
        if op19.get("actual_review_evidence_complete_predicate_passed") is not True:
            blockers.append("pmn_op20_op19_predicate_not_passed")
        if op19.get("actual_review_evidence_complete") is not True:
            blockers.append("pmn_op20_op19_actual_review_evidence_not_complete")
        if op19.get("actual_review_evidence_complete_from_real_review") is not True:
            blockers.append("pmn_op20_op19_actual_review_evidence_from_real_review_not_complete")
        if op19.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF:
            blockers.append("pmn_op20_op19_next_step_not_candidate_only_separation")
        for false_field in (
            "p5_final_allowed", "p6_start_allowed", "p8_start_allowed",
            "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed",
            "p7_complete", "release_allowed",
        ):
            if op19.get(false_field) is not False:
                blockers.append(f"pmn_op20_op19_{false_field}_promoted")
    if not isinstance(op14, Mapping):
        blockers.append("pmn_op20_op14_blocker_classification_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op14_readfeel_label_connection_safe_display_blocker_classification_contract(op14)
        except ValueError:
            blockers.append("pmn_op20_op14_blocker_classification_invalid")
        if op14.get("readfeel_label_connection_safe_display_blocker_classification_ready") is not True:
            blockers.append("pmn_op20_op14_blocker_classification_not_ready")
    if not isinstance(op15, Mapping):
        blockers.append("pmn_op20_op15_question_need_observation_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op15_question_need_observation_row_normalization_contract(op15)
        except ValueError:
            blockers.append("pmn_op20_op15_question_need_observation_invalid")
        if op15.get("question_need_observation_row_normalization_ready") is not True:
            blockers.append("pmn_op20_op15_question_need_observation_not_ready")
        if op15.get("p8_start_allowed") is not False:
            blockers.append("pmn_op20_op15_p8_start_promoted")
    if not isinstance(op16, Mapping):
        blockers.append("pmn_op20_op16_rating_question_consistency_guard_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op16_rating_question_consistency_guard_contract(op16)
        except ValueError:
            blockers.append("pmn_op20_op16_rating_question_consistency_guard_invalid")
        if op16.get("rating_question_consistency_guard_passed") is not True:
            blockers.append("pmn_op20_op16_rating_question_consistency_guard_not_passed")
        if op16.get("consistency_issue_row_count") not in (0, None):
            blockers.append("pmn_op20_op16_consistency_issues_present")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation(
    *,
    actual_review_evidence_complete_predicate: Mapping[str, Any] | None = None,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP20 body-free candidate-only separation material."""

    op19 = actual_review_evidence_complete_predicate
    op14 = readfeel_label_connection_safe_display_blocker_classification
    op15 = question_need_observation_row_normalization
    op16 = rating_question_consistency_guard
    session_id = _safe_review_session_id(review_session_id or (op19 or {}).get("review_session_id") if isinstance(op19, Mapping) else review_session_id)
    blockers = _pmn_op20_blockers(op19, op14, op15, op16)
    ready = not blockers
    status_ref = P7_R54_AHR_POST_MN11_PMN_OP20_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_STATUS_REF

    p5_repair_refs = _pmn_op20_case_ref_list((op14 or {}).get("p5_repair_required_case_refs")) if ready and isinstance(op14, Mapping) else []
    safe_display_refs = _pmn_op20_case_ref_list((op14 or {}).get("safe_display_blocked_case_refs")) if ready and isinstance(op14, Mapping) else []
    p5_repair_refs = sorted(set(p5_repair_refs) | set(safe_display_refs))
    p4_repair_refs = _pmn_op20_case_ref_list((op14 or {}).get("p4_current_only_repair_required_case_refs")) if ready and isinstance(op14, Mapping) else []
    operation_blocked_refs = _pmn_op20_case_ref_list((op14 or {}).get("operation_blocked_case_refs")) if ready and isinstance(op14, Mapping) else []
    inconclusive_refs = _pmn_op20_case_ref_list((op14 or {}).get("inconclusive_case_refs")) if ready and isinstance(op14, Mapping) else []
    no_blocker_refs = _pmn_op20_case_ref_list((op14 or {}).get("no_blocker_case_refs")) if ready and isinstance(op14, Mapping) else []
    p8_candidate_refs = _pmn_op20_case_ref_list((op16 or {}).get("p8_material_candidate_case_refs_bodyfree_only")) if ready and isinstance(op16, Mapping) else []
    p8_blocked_refs = _pmn_op20_case_ref_list((op16 or {}).get("p8_material_candidate_blocked_by_blocker_case_refs")) if ready and isinstance(op16, Mapping) else []
    p5_confirmed_refs = no_blocker_refs if ready and not (p5_repair_refs or p4_repair_refs or operation_blocked_refs or inconclusive_refs) else []
    r52_candidate_refs = list(p5_confirmed_refs)

    selected_decision_refs: list[str] = []
    if ready:
        if p5_confirmed_refs:
            selected_decision_refs.extend([
                "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY",
                "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY",
                "R52_REINTAKE_HANDOFF_CANDIDATE_ONLY",
            ])
        if p5_repair_refs:
            selected_decision_refs.append("P5_REPAIR_REQUIRED_BEFORE_R52_REINTAKE")
        if p4_repair_refs:
            selected_decision_refs.append("P4_CURRENT_ONLY_REPAIR_REQUIRED_BEFORE_R52_REINTAKE")
        if operation_blocked_refs:
            selected_decision_refs.append("R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT")
        if not ((op19 or {}).get("disposal_verified") is True):
            selected_decision_refs.append("R54_OPERATION_BLOCKED_DISPOSAL_NOT_VERIFIED")
        if inconclusive_refs:
            selected_decision_refs.append("R54_OPERATION_INCONCLUSIVE_INSUFFICIENT_MATERIAL")
        if p8_candidate_refs:
            selected_decision_refs.append("P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY")
    selected_decision_refs = list(dict.fromkeys(selected_decision_refs))

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP20_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op19_schema_version": (op19 or {}).get("schema_version") if isinstance(op19, Mapping) else None,
        "op19_material_ref": (op19 or {}).get("material_id", "missing_op19") if isinstance(op19, Mapping) else "missing_op19",
        "op19_next_required_step": (op19 or {}).get("next_required_step") if isinstance(op19, Mapping) else None,
        "op19_actual_review_evidence_complete_predicate_status_ref": (op19 or {}).get("actual_review_evidence_complete_predicate_status_ref") if isinstance(op19, Mapping) else None,
        "op19_actual_review_evidence_complete_predicate_passed": (op19 or {}).get("actual_review_evidence_complete_predicate_passed") is True if isinstance(op19, Mapping) else False,
        "op19_actual_review_evidence_complete": (op19 or {}).get("actual_review_evidence_complete") is True if isinstance(op19, Mapping) else False,
        "op19_actual_review_evidence_complete_from_real_review": (op19 or {}).get("actual_review_evidence_complete_from_real_review") is True if isinstance(op19, Mapping) else False,
        "op19_actual_source_guard_passed": (op19 or {}).get("actual_source_guard_passed") is True if isinstance(op19, Mapping) else False,
        "op19_actual_human_review_executed_by_person": (op19 or {}).get("actual_human_review_executed_by_person") is True if isinstance(op19, Mapping) else False,
        "op19_reviewed_case_count": _pmn_op20_int((op19 or {}).get("reviewed_case_count")) if isinstance(op19, Mapping) else 0,
        "op19_sanitized_review_result_row_count": _pmn_op20_int((op19 or {}).get("sanitized_review_result_row_count")) if isinstance(op19, Mapping) else 0,
        "op19_rating_row_count": _pmn_op20_int((op19 or {}).get("rating_row_count")) if isinstance(op19, Mapping) else 0,
        "op19_question_need_observation_row_count": _pmn_op20_int((op19 or {}).get("question_need_observation_row_count")) if isinstance(op19, Mapping) else 0,
        "op19_disposal_verified": (op19 or {}).get("disposal_verified") is True if isinstance(op19, Mapping) else False,
        "op14_schema_version": (op14 or {}).get("schema_version") if isinstance(op14, Mapping) else None,
        "op14_material_ref": (op14 or {}).get("material_id", "missing_op14") if isinstance(op14, Mapping) else "missing_op14",
        "op14_next_required_step": (op14 or {}).get("next_required_step") if isinstance(op14, Mapping) else None,
        "op14_blocker_classification_ready": (op14 or {}).get("readfeel_label_connection_safe_display_blocker_classification_ready") is True if isinstance(op14, Mapping) else False,
        "op14_no_blocker_case_count": _pmn_op20_int((op14 or {}).get("no_blocker_case_count")) if isinstance(op14, Mapping) else 0,
        "op14_p5_repair_required_case_count": _pmn_op20_int((op14 or {}).get("p5_repair_required_case_count")) if isinstance(op14, Mapping) else 0,
        "op14_p4_current_only_repair_required_case_count": _pmn_op20_int((op14 or {}).get("p4_current_only_repair_required_case_count")) if isinstance(op14, Mapping) else 0,
        "op14_operation_blocked_case_count": _pmn_op20_int((op14 or {}).get("operation_blocked_case_count")) if isinstance(op14, Mapping) else 0,
        "op14_safe_display_blocked_case_count": _pmn_op20_int((op14 or {}).get("safe_display_blocked_case_count")) if isinstance(op14, Mapping) else 0,
        "op14_inconclusive_case_count": _pmn_op20_int((op14 or {}).get("inconclusive_case_count")) if isinstance(op14, Mapping) else 0,
        "op15_schema_version": (op15 or {}).get("schema_version") if isinstance(op15, Mapping) else None,
        "op15_material_ref": (op15 or {}).get("material_id", "missing_op15") if isinstance(op15, Mapping) else "missing_op15",
        "op15_next_required_step": (op15 or {}).get("next_required_step") if isinstance(op15, Mapping) else None,
        "op15_question_need_observation_row_normalization_ready": (op15 or {}).get("question_need_observation_row_normalization_ready") is True if isinstance(op15, Mapping) else False,
        "op15_question_need_observation_row_count": _pmn_op20_int((op15 or {}).get("question_need_observation_row_count")) if isinstance(op15, Mapping) else 0,
        "op15_p8_material_candidate_case_count_bodyfree_only": _pmn_op20_int((op15 or {}).get("p8_material_candidate_case_count_bodyfree_only")) if isinstance(op15, Mapping) else 0,
        "op16_schema_version": (op16 or {}).get("schema_version") if isinstance(op16, Mapping) else None,
        "op16_material_ref": (op16 or {}).get("material_id", "missing_op16") if isinstance(op16, Mapping) else "missing_op16",
        "op16_next_required_step": (op16 or {}).get("next_required_step") if isinstance(op16, Mapping) else None,
        "op16_rating_question_consistency_guard_passed": (op16 or {}).get("rating_question_consistency_guard_passed") is True if isinstance(op16, Mapping) else False,
        "op16_consistency_issue_row_count": _pmn_op20_int((op16 or {}).get("consistency_issue_row_count")) if isinstance(op16, Mapping) else 0,
        "candidate_only_separation_status_ref": status_ref,
        "candidate_only_separation_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP20_ALLOWED_STATUS_REFS),
        "candidate_only_separation_ready": ready,
        "candidate_only_separation_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP20_READY_REASON_REFS) if ready else [],
        "candidate_only_separation_blocker_refs": blockers,
        "candidate_only_separation_blocker_ref_count": len(blockers),
        "decision_ref_options": list(P7_R54_AHR_POST_MN11_PMN_OP20_DECISION_REFS),
        "decision_ref_option_count": len(P7_R54_AHR_POST_MN11_PMN_OP20_DECISION_REFS),
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
        "operation_blocked_disposal_not_verified": ready and not ((op19 or {}).get("disposal_verified") is True),
        "inconclusive_insufficient_material_case_refs": inconclusive_refs,
        "inconclusive_insufficient_material_case_count": len(inconclusive_refs),
        "p6_limited_human_readfeel_candidate_only": bool(p5_confirmed_refs),
        "p8_question_need_observation_material_candidate_only": bool(p8_candidate_refs),
        "p8_material_candidate_case_refs_bodyfree_only": p8_candidate_refs,
        "p8_material_candidate_case_count_bodyfree_only": len(p8_candidate_refs),
        "p8_material_candidate_blocked_by_blocker_case_refs": p8_blocked_refs,
        "p8_material_candidate_blocked_by_blocker_case_count": len(p8_blocked_refs),
        "r52_reintake_handoff_candidate_only": bool(r52_candidate_refs),
        "r52_reintake_handoff_candidate_case_refs": r52_candidate_refs,
        "r52_reintake_handoff_candidate_case_count": len(r52_candidate_refs),
        "candidate_only_separation_does_not_finalize_p5": True,
        "candidate_only_separation_does_not_start_p6": True,
        "candidate_only_separation_does_not_start_p8": True,
        "candidate_only_separation_does_not_execute_r52": True,
        "candidate_only_separation_does_not_complete_p7_or_release": True,
        "downstream_manual_decision_hold_required": True,
        "actual_source_guard_passed": ready and (op19 or {}).get("actual_source_guard_passed") is True,
        "actual_human_review_executed_by_person": ready and (op19 or {}).get("actual_human_review_executed_by_person") is True,
        "disposal_verified": ready and (op19 or {}).get("disposal_verified") is True,
        "actual_review_evidence_complete": ready and (op19 or {}).get("actual_review_evidence_complete") is True,
        "actual_review_evidence_complete_from_real_review": ready and (op19 or {}).get("actual_review_evidence_complete_from_real_review") is True,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
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
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP20_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP20_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP19_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["disposal_verified"] = ready and (op19 or {}).get("disposal_verified") is True
    material["actual_review_evidence_complete"] = ready and (op19 or {}).get("actual_review_evidence_complete") is True
    material["actual_review_evidence_complete_from_real_review"] = ready and (op19 or {}).get("actual_review_evidence_complete_from_real_review") is True
    material["actual_human_review_run_here"] = False
    material["actual_human_review_complete"] = False
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
    _required_fields_present(material, required=P7_R54_AHR_POST_MN11_PMN_OP20_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP20")
    return material


def assert_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP20_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP20")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP20_P5_P6_P8_R52_CANDIDATE_ONLY_SEPARATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP20_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP20",
        allowed_true_flag_refs=P7_R54_AHR_POST_MN11_PMN_OP20_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if tuple(data.get("candidate_only_separation_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP20_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 allowed status refs changed")
    if tuple(data.get("decision_ref_options") or ()) != P7_R54_AHR_POST_MN11_PMN_OP20_DECISION_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 decision refs changed")
    if data.get("decision_ref_option_count") != len(P7_R54_AHR_POST_MN11_PMN_OP20_DECISION_REFS):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 decision option count changed")
    ready = data.get("candidate_only_separation_status_ref") == P7_R54_AHR_POST_MN11_PMN_OP20_READY_STATUS_REF
    if data.get("candidate_only_separation_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 ready flag changed")
    blockers = list(data.get("candidate_only_separation_blocker_refs") or [])
    selected = list(data.get("selected_decision_refs") or [])
    if data.get("candidate_only_separation_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 blocker count changed")
    if data.get("selected_decision_ref_count") != len(selected):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 selected decision count changed")
    for decision_ref in selected:
        if decision_ref not in P7_R54_AHR_POST_MN11_PMN_OP20_DECISION_REFS:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP20 unknown decision ref: {decision_ref}")
    for refs_key, count_key in (
        ("p5_confirmed_candidate_case_refs", "p5_confirmed_candidate_case_count"),
        ("p5_repair_required_case_refs", "p5_repair_required_case_count"),
        ("p4_current_only_repair_required_case_refs", "p4_current_only_repair_required_case_count"),
        ("operation_blocked_case_refs", "operation_blocked_case_count"),
        ("inconclusive_insufficient_material_case_refs", "inconclusive_insufficient_material_case_count"),
        ("p8_material_candidate_case_refs_bodyfree_only", "p8_material_candidate_case_count_bodyfree_only"),
        ("p8_material_candidate_blocked_by_blocker_case_refs", "p8_material_candidate_blocked_by_blocker_case_count"),
        ("r52_reintake_handoff_candidate_case_refs", "r52_reintake_handoff_candidate_case_count"),
    ):
        if data.get(count_key) != len(data.get(refs_key) or []):
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP20 {count_key} changed")
    for key in (
        "candidate_only_separation_does_not_finalize_p5",
        "candidate_only_separation_does_not_start_p6",
        "candidate_only_separation_does_not_start_p8",
        "candidate_only_separation_does_not_execute_r52",
        "candidate_only_separation_does_not_complete_p7_or_release",
        "downstream_manual_decision_hold_required",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP20 required boundary changed: {key}")
    for key in (
        "actual_human_review_run_here", "actual_human_review_complete", "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final", "p5_final_allowed", "p6_limited_human_readfeel_start_allowed", "p6_start_allowed",
        "p8_start_allowed", "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed",
        "p7_complete", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP20 downstream promotion changed: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 basis changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 ready material cannot carry blockers")
        if data.get("candidate_only_separation_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP20_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 ready reason refs changed")
        for key in (
            "op19_actual_review_evidence_complete_predicate_passed", "op19_actual_review_evidence_complete",
            "op19_actual_review_evidence_complete_from_real_review", "op19_actual_source_guard_passed",
            "op19_actual_human_review_executed_by_person", "op19_disposal_verified", "op14_blocker_classification_ready",
            "op15_question_need_observation_row_normalization_ready", "op16_rating_question_consistency_guard_passed",
            "actual_source_guard_passed", "actual_human_review_executed_by_person", "disposal_verified",
            "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP20 ready field changed: {key}")
        for count_key in ("op19_reviewed_case_count", "op19_sanitized_review_result_row_count", "op19_rating_row_count", "op19_question_need_observation_row_count", "op15_question_need_observation_row_count"):
            if data.get(count_key) != P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP20 {count_key} must be 24")
        if data.get("p5_confirmed_candidate_bodyfree_only") is True:
            for decision_ref in (
                "P5_CONFIRMED_CANDIDATE_BODYFREE_ONLY",
                "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY",
                "R52_REINTAKE_HANDOFF_CANDIDATE_ONLY",
            ):
                if decision_ref not in selected:
                    raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP20 missing selected decision: {decision_ref}")
        if data.get("p8_question_need_observation_material_candidate_only") is True and "P8_QUESTION_NEED_OBSERVATION_MATERIAL_CANDIDATE_ONLY" not in selected:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 missing P8 candidate-only decision")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP20_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP20_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 ready steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 ready next step changed")
    else:
        if data.get("candidate_only_separation_status_ref") != P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 blocked material must carry blockers")
        if data.get("candidate_only_separation_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 blocked material cannot carry ready reasons")
        if data.get("actual_review_evidence_complete") is not False or data.get("actual_review_evidence_complete_from_real_review") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 blocked material cannot claim evidence complete")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP20 blocked next step changed")
    return True


def _pmn_op21_mapping_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, (role_ref, post_mn11_step_ref, postcr22_step_ref, mapping_ref) in enumerate(P7_R54_AHR_POST_MN11_PMN_OP21_REENTRY_MAPPING_ROW_REFS, start=1):
        rows.append({
            "reentry_mapping_row_ref": f"postmn11-pmn-op21-reentry-mapping-row-{index:03d}",
            "reentry_role_ref": role_ref,
            "post_mn11_source_step_ref": post_mn11_step_ref,
            "postcr22_target_step_ref": postcr22_step_ref,
            "mapping_ref": mapping_ref,
            "reentry_executed_here": False,
            "existing_helper_reused": True,
            "new_giant_wrapper_required": False,
            "body_free": True,
        })
    return rows


def _pmn_op21_blockers(op20: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op20, Mapping):
        return ["pmn_op21_candidate_only_separation_missing"]
    try:
        assert_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation_contract(op20)
    except ValueError:
        blockers.append("pmn_op21_candidate_only_separation_invalid")
    if op20.get("candidate_only_separation_ready") is not True:
        blockers.append("pmn_op21_candidate_only_separation_not_ready")
    if op20.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF:
        blockers.append("pmn_op21_candidate_only_next_step_not_reentry_mapping")
    if op20.get("actual_review_evidence_complete") is not True:
        blockers.append("pmn_op21_actual_review_evidence_not_complete")
    if op20.get("actual_review_evidence_complete_from_real_review") is not True:
        blockers.append("pmn_op21_actual_review_evidence_from_real_review_not_complete")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping(
    *,
    p5_p6_p8_r52_candidate_only_separation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP21 body-free mapping back to existing PostCR22 EX07-EX18."""

    op20 = p5_p6_p8_r52_candidate_only_separation
    session_id = _safe_review_session_id(review_session_id or (op20 or {}).get("review_session_id") if isinstance(op20, Mapping) else review_session_id)
    blockers = _pmn_op21_blockers(op20)
    ready = not blockers
    status_ref = P7_R54_AHR_POST_MN11_PMN_OP21_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_STATUS_REF
    mapping_rows = _pmn_op21_mapping_rows() if ready else []
    role_refs = [row[0] for row in P7_R54_AHR_POST_MN11_PMN_OP21_REENTRY_MAPPING_ROW_REFS]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP21_EXISTING_POSTCR22_EX07_EX18_REENTRY_MAPPING_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op20_schema_version": (op20 or {}).get("schema_version") if isinstance(op20, Mapping) else None,
        "op20_material_ref": (op20 or {}).get("material_id", "missing_op20") if isinstance(op20, Mapping) else "missing_op20",
        "op20_next_required_step": (op20 or {}).get("next_required_step") if isinstance(op20, Mapping) else None,
        "op20_candidate_only_separation_status_ref": (op20 or {}).get("candidate_only_separation_status_ref") if isinstance(op20, Mapping) else None,
        "op20_candidate_only_separation_ready": (op20 or {}).get("candidate_only_separation_ready") is True if isinstance(op20, Mapping) else False,
        "op20_actual_review_evidence_complete": (op20 or {}).get("actual_review_evidence_complete") is True if isinstance(op20, Mapping) else False,
        "op20_actual_review_evidence_complete_from_real_review": (op20 or {}).get("actual_review_evidence_complete_from_real_review") is True if isinstance(op20, Mapping) else False,
        "op20_selected_decision_refs": list((op20 or {}).get("selected_decision_refs") or []) if isinstance(op20, Mapping) and ready else [],
        "op20_selected_decision_ref_count": len((op20 or {}).get("selected_decision_refs") or []) if isinstance(op20, Mapping) and ready else 0,
        "existing_postcr22_ex07_ex18_reentry_mapping_status_ref": status_ref,
        "existing_postcr22_ex07_ex18_reentry_mapping_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_STATUS_REFS),
        "existing_postcr22_ex07_ex18_reentry_mapping_ready": ready,
        "existing_postcr22_ex07_ex18_reentry_mapping_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP21_READY_REASON_REFS) if ready else [],
        "existing_postcr22_ex07_ex18_reentry_mapping_blocker_refs": blockers,
        "existing_postcr22_ex07_ex18_reentry_mapping_blocker_ref_count": len(blockers),
        "reentry_mapping_ref": P7_R54_AHR_POST_MN11_PMN_OP21_MAPPING_REF,
        "reentry_mapping_rows": mapping_rows,
        "reentry_mapping_row_count": len(mapping_rows),
        "reentry_mapping_role_refs": role_refs if ready else [],
        "reentry_mapping_role_ref_count": len(role_refs) if ready else 0,
        "existing_ex_line_reentry_step_refs": list(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS) if ready else [],
        "existing_ex_line_reentry_step_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS) if ready else 0,
        "existing_ex_line_reentry_first_step_ref": P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[0] if ready else "",
        "existing_ex_line_reentry_last_step_ref": P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[-1] if ready else "",
        "existing_ex_line_reentry_role_refs": list(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS) if ready else [],
        "existing_ex_line_reentry_role_ref_count": len(P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS) if ready else 0,
        "postcr22_ex07_ex18_reentry_executed_here": False,
        "reentry_executed_here": False,
        "reentry_mapping_reuses_existing_postcr22_ex_line": ready,
        "reentry_mapping_does_not_reimplement_ex_helpers": True,
        "reentry_mapping_does_not_execute_ex_helpers_here": True,
        "postcr22_ex18_ready_is_manual_hold_not_r52_execution": True,
        "new_giant_wrapper_required": False,
        "minimal_bridge_only": True,
        "actual_source_guard_passed": ready and (op20 or {}).get("actual_source_guard_passed") is True,
        "actual_human_review_executed_by_person": ready and (op20 or {}).get("actual_human_review_executed_by_person") is True,
        "disposal_verified": ready and (op20 or {}).get("disposal_verified") is True,
        "actual_review_evidence_complete": ready and (op20 or {}).get("actual_review_evidence_complete") is True,
        "actual_review_evidence_complete_from_real_review": ready and (op20 or {}).get("actual_review_evidence_complete_from_real_review") is True,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "r52_reintake_execution_started_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP21_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP20_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP21_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP20_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["disposal_verified"] = ready and (op20 or {}).get("disposal_verified") is True
    material["actual_review_evidence_complete"] = ready and (op20 or {}).get("actual_review_evidence_complete") is True
    material["actual_review_evidence_complete_from_real_review"] = ready and (op20 or {}).get("actual_review_evidence_complete_from_real_review") is True
    material["actual_human_review_run_here"] = False
    material["actual_human_review_complete"] = False
    material["p5_human_blind_qa_confirmed_final"] = False
    material["p5_confirmed_final"] = False
    material["p5_final_allowed"] = False
    material["p6_limited_human_readfeel_start_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["r52_reintake_execution_requested_here"] = False
    material["r52_reintake_execution_started_here"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_MN11_PMN_OP21_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP21")
    return material


def assert_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP21_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP21")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP21_EXISTING_POSTCR22_EX07_EX18_REENTRY_MAPPING_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP21_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP21",
        allowed_true_flag_refs=P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if tuple(data.get("existing_postcr22_ex07_ex18_reentry_mapping_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP21_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 allowed status refs changed")
    ready = data.get("existing_postcr22_ex07_ex18_reentry_mapping_status_ref") == P7_R54_AHR_POST_MN11_PMN_OP21_READY_STATUS_REF
    if data.get("existing_postcr22_ex07_ex18_reentry_mapping_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 ready flag changed")
    blockers = list(data.get("existing_postcr22_ex07_ex18_reentry_mapping_blocker_refs") or [])
    if data.get("existing_postcr22_ex07_ex18_reentry_mapping_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 blocker count changed")
    rows = list(data.get("reentry_mapping_rows") or [])
    if data.get("reentry_mapping_row_count") != len(rows):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 mapping row count changed")
    if data.get("reentry_mapping_role_ref_count") != len(data.get("reentry_mapping_role_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 mapping role count changed")
    if data.get("existing_ex_line_reentry_step_ref_count") != len(data.get("existing_ex_line_reentry_step_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 EX step count changed")
    if data.get("existing_ex_line_reentry_role_ref_count") != len(data.get("existing_ex_line_reentry_role_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 EX role count changed")
    for key in (
        "postcr22_ex07_ex18_reentry_executed_here", "reentry_executed_here", "actual_human_review_run_here",
        "actual_human_review_complete", "p5_human_blind_qa_confirmed_final", "p5_confirmed_final", "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed", "p6_start_allowed", "p8_start_allowed", "r52_reintake_execution_requested_here",
        "r52_reintake_execution_started_here", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP21 forbidden execution/promotion changed: {key}")
    for key in (
        "reentry_mapping_does_not_reimplement_ex_helpers", "reentry_mapping_does_not_execute_ex_helpers_here",
        "postcr22_ex18_ready_is_manual_hold_not_r52_execution", "minimal_bridge_only", "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here", "p5_finalization_blocked_here", "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP21 required boundary changed: {key}")
    if data.get("new_giant_wrapper_required") is not False:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 must not require new giant wrapper")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 basis changed")
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 ready material cannot carry blockers")
        if data.get("existing_postcr22_ex07_ex18_reentry_mapping_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP21_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 ready reasons changed")
        for key in (
            "op20_candidate_only_separation_ready", "op20_actual_review_evidence_complete",
            "op20_actual_review_evidence_complete_from_real_review", "actual_source_guard_passed",
            "actual_human_review_executed_by_person", "disposal_verified", "actual_review_evidence_complete",
            "actual_review_evidence_complete_from_real_review", "reentry_mapping_reuses_existing_postcr22_ex_line",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP21 ready field changed: {key}")
        if tuple(data.get("existing_ex_line_reentry_step_refs") or ()) != P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 EX step refs changed")
        if data.get("existing_ex_line_reentry_first_step_ref") != P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[0] or data.get("existing_ex_line_reentry_last_step_ref") != P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[-1]:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 EX first/last refs changed")
        if tuple(data.get("existing_ex_line_reentry_role_refs") or ()) != P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 EX role refs changed")
        if tuple(data.get("reentry_mapping_role_refs") or ()) != tuple(row[0] for row in P7_R54_AHR_POST_MN11_PMN_OP21_REENTRY_MAPPING_ROW_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 mapping role refs changed")
        if len(rows) != len(P7_R54_AHR_POST_MN11_PMN_OP21_REENTRY_MAPPING_ROW_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 mapping row length changed")
        for row, expected in zip(rows, P7_R54_AHR_POST_MN11_PMN_OP21_REENTRY_MAPPING_ROW_REFS):
            role_ref, source_step_ref, target_step_ref, mapping_ref = expected
            if row.get("reentry_role_ref") != role_ref or row.get("post_mn11_source_step_ref") != source_step_ref or row.get("postcr22_target_step_ref") != target_step_ref or row.get("mapping_ref") != mapping_ref:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 mapping row changed")
            if row.get("reentry_executed_here") is not False or row.get("existing_helper_reused") is not True or row.get("new_giant_wrapper_required") is not False or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 mapping row boundary changed")
            if _scan_forbidden_payload_key_paths(row, path="pmn_op21_mapping_row"):
                raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 mapping row leaked forbidden payload key")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP21_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP21_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 ready steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 ready next step changed")
    else:
        if data.get("existing_postcr22_ex07_ex18_reentry_mapping_status_ref") != P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 blocked material must carry blockers")
        if data.get("existing_postcr22_ex07_ex18_reentry_mapping_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 blocked material cannot carry ready reasons")
        if data.get("actual_review_evidence_complete") is not False or data.get("actual_review_evidence_complete_from_real_review") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 blocked material cannot claim evidence complete")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP21_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP21 blocked next step changed")
    return True


def build_p7_r54_ahr_post_mn11_actual_operation_p5_p6_p8_r52_candidate_only_separation_bodyfree(
    *,
    actual_review_evidence_complete_predicate: Mapping[str, Any] | None = None,
    readfeel_label_connection_safe_display_blocker_classification: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation(
        actual_review_evidence_complete_predicate=actual_review_evidence_complete_predicate,
        readfeel_label_connection_safe_display_blocker_classification=readfeel_label_connection_safe_display_blocker_classification,
        question_need_observation_row_normalization=question_need_observation_row_normalization,
        rating_question_consistency_guard=rating_question_consistency_guard,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_p5_p6_p8_r52_candidate_only_separation_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op20_p5_p6_p8_r52_candidate_only_separation_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_existing_postcr22_ex07_ex18_reentry_mapping_bodyfree(
    *,
    p5_p6_p8_r52_candidate_only_separation: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping(
        p5_p6_p8_r52_candidate_only_separation=p5_p6_p8_r52_candidate_only_separation,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_existing_postcr22_ex07_ex18_reentry_mapping_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_contract(data)


# ---------------------------------------------------------------------------
# PMN-OP22 / PMN-OP23 validation memo envelope and fail-closed finalizer
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_MN11_PMN_OP22_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op22_validation_command_matrix_result_memo_envelope.bodyfree.v1"
)
P7_R54_AHR_POST_MN11_PMN_OP23_ACCEPTANCE_FAIL_CLOSED_FINALIZER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_mn11.actual_local_only_human_review_operation."
    "pmn_op23_acceptance_fail_closed_finalizer.bodyfree.v1"
)

P7_R54_AHR_POST_MN11_PMN_OP22_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:23]
)
P7_R54_AHR_POST_MN11_PMN_OP22_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[23:]
)
P7_R54_AHR_POST_MN11_PMN_OP23_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_STEP_REFS[:24]
)
P7_R54_AHR_POST_MN11_PMN_OP23_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_MN11_PMN_OP22_READY_STATUS_REF: Final = (
    "PMN_OP22_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_STATUS_REF: Final = (
    "PMN_OP22_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP22_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP22_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op22_validation_command_matrix_result_memo_envelope_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP22_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op21_existing_postcr22_ex07_ex18_reentry_mapping_ready_bodyfree",
    "validation_command_matrix_defined_without_command_execution_claim",
    "result_memo_required_sections_defined_bodyfree",
    "not_claimed_boundary_and_next_required_step_recorded",
    "full_backend_suite_green_not_claimed_and_downstream_promotion_blocked",
)
P7_R54_AHR_POST_MN11_PMN_OP22_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "disposal_verified",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_review",
)
P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS: Final[tuple[str, ...]] = (
    "pytest_pmn_op00_op01_target",
    "pytest_pmn_op02_op03_target",
    "pytest_pmn_op04_op05_target",
    "pytest_pmn_op06_op07_target",
    "pytest_pmn_op08_op09_target",
    "pytest_pmn_op10_op11_target",
    "pytest_pmn_op12_op13_target",
    "pytest_pmn_op14_op15_target",
    "pytest_pmn_op16_op17_target",
    "pytest_pmn_op18_op19_target",
    "pytest_pmn_op20_op21_target",
    "pytest_pmn_op22_op23_contract_target",
)
P7_R54_AHR_POST_MN11_PMN_OP22_SELECTED_REGRESSION_COMMAND_REFS: Final[tuple[str, ...]] = (
    "pytest_post_ex18_mn00_mn11_selected_regression",
    "pytest_postcr22_ex00_ex18_selected_regression",
)
P7_R54_AHR_POST_MN11_PMN_OP22_COMPILEALL_COMMAND_REF: Final = (
    "compileall_post_mn11_actual_local_only_human_review_operation_helper"
)
P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS: Final[tuple[str, ...]] = (
    "implementation_scope",
    "changed_files",
    "target_tests",
    "selected_regression",
    "compileall",
    "mn11_intake_status",
    "local_only_preflight_status",
    "explicit_allow_status",
    "actual_body_full_packet_generation_status",
    "actual_human_review_execution_status",
    "actual_operation_receipt_status",
    "sanitized_review_result_row_status",
    "rating_row_status",
    "question_need_observation_row_status",
    "disposal_purge_status",
    "no_leak_validation_status",
    "actual_review_evidence_status",
    "reentry_mapping_status",
    "not_claimed_boundary",
    "next_required_step",
)
P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_ENVELOPE_REF: Final = (
    "postmn11_pmn_op22_validation_command_matrix_result_memo_envelope_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP22_VALIDATION_COMMAND_MATRIX_REF: Final = (
    "postmn11_pmn_op22_validation_command_matrix_bodyfree_20260630_001"
)
P7_R54_AHR_POST_MN11_PMN_OP22_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op21_schema_version", "op21_material_ref", "op21_next_required_step", "op21_existing_postcr22_ex07_ex18_reentry_mapping_status_ref",
    "op21_existing_postcr22_ex07_ex18_reentry_mapping_ready", "op21_reentry_mapping_row_count",
    "op21_actual_review_evidence_complete", "op21_actual_review_evidence_complete_from_real_review", "op21_reentry_executed_here",
    "op21_postcr22_ex07_ex18_reentry_executed_here", "op21_actual_source_guard_passed", "op21_disposal_verified",
    "validation_command_matrix_status_ref", "validation_command_matrix_allowed_status_refs", "validation_command_matrix_ready",
    "validation_command_matrix_reason_refs", "validation_command_matrix_blocker_refs", "validation_command_matrix_blocker_ref_count",
    "validation_command_matrix_ref", "target_test_command_refs", "target_test_command_ref_count", "target_test_status_refs",
    "target_test_status_ref_count", "selected_regression_command_refs", "selected_regression_command_ref_count",
    "selected_regression_status_refs", "selected_regression_status_ref_count", "compileall_command_ref", "compileall_status_ref",
    "validation_commands_executed_here", "target_tests_green_claimed_here", "selected_regression_green_claimed_here",
    "full_backend_suite_green_claimed_here", "compileall_result_claimed_here", "zip_overlay_verification_claimed_here",
    "result_memo_envelope_ref", "result_memo_required_section_refs", "result_memo_required_section_ref_count",
    "result_memo_present_section_refs", "result_memo_present_section_ref_count", "result_memo_missing_section_refs",
    "result_memo_missing_section_ref_count", "result_memo_is_bodyfree_envelope", "result_memo_file_materialized_here",
    "result_memo_forbidden_payload_key_paths", "result_memo_forbidden_payload_key_path_count",
    "result_memo_does_not_include_forbidden_payload", "result_memo_records_actual_operation_status", "result_memo_records_actual_evidence_status",
    "result_memo_records_not_claimed_boundary", "result_memo_records_next_required_step", "result_memo_does_not_claim_full_backend_suite_green",
    "result_memo_does_not_claim_rn_contract_green", "result_memo_does_not_claim_rn_real_device_modal_verified",
    "actual_operation_status_ref", "actual_evidence_status_ref", "actual_source_guard_passed", "actual_human_review_executed_by_person",
    "disposal_verified", "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review",
    "actual_review_evidence_complete_from_real_operation_claimed_here", "actual_body_full_packet_generation_run_here",
    "actual_24_case_local_only_human_review_run_here", "actual_operation_receipt_created_here_by_helper", "actual_rows_created_here_by_helper",
    "actual_disposal_purge_executed_here", "downstream_manual_decision_hold_required", "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count", "not_claimed_boundary", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_mn11_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_MN11_PMN_OP23_READY_STATUS_REF: Final = (
    "PMN_OP23_ACCEPTANCE_FAIL_CLOSED_FINALIZER_READY_BODYFREE"
)
P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_STATUS_REF: Final = (
    "PMN_OP23_ACCEPTANCE_FAIL_CLOSED_FINALIZER_BLOCKED"
)
P7_R54_AHR_POST_MN11_PMN_OP23_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_MN11_PMN_OP23_READY_STATUS_REF,
    P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_pmn_op23_acceptance_fail_closed_finalizer_or_stop"
)
P7_R54_AHR_POST_MN11_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_REF: Final = (
    "downstream_manual_decision_hold_after_post_mn11_pmn_op23_acceptance_bodyfree"
)
P7_R54_AHR_POST_MN11_PMN_OP23_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op22_validation_command_matrix_result_memo_envelope_ready_bodyfree",
    "ready_conditions_passed_without_body_question_path_hash_leak",
    "fail_closed_conditions_observed_as_absent",
    "pmn_op00_to_pmn_op23_implementation_sequence_closed",
    "downstream_p5_p6_p8_r52_p7_release_manual_hold_required",
)
P7_R54_AHR_POST_MN11_PMN_OP23_READY_CONDITION_REFS: Final[tuple[str, ...]] = (
    "scope_confirmed",
    "mn11_return_operation_required_intake_passed",
    "local_only_preflight_passed",
    "actual_source_guard_passed",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_path_hash_validation_passed",
    "no_touch_validation_passed",
    "no_promotion_boundary_confirmed",
)
P7_R54_AHR_POST_MN11_PMN_OP23_FAIL_CLOSED_CONDITION_REFS: Final[tuple[str, ...]] = (
    "body_leak_detected",
    "question_text_detected",
    "local_path_or_hash_detected",
    "promotion_claim_detected",
    "mn11_result_memo_missing",
    "mn11_next_required_step_mismatch",
    "unit_test_rows_used_as_actual_evidence",
    "actual_basis_ref_overwritten_by_latest_zip_label",
    "reviewed_case_count_not_24",
    "row_counts_not_24",
    "disposal_receipt_missing",
)
P7_R54_AHR_POST_MN11_PMN_OP23_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "disposal_verified",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_review",
)
P7_R54_AHR_POST_MN11_PMN_OP23_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op22_schema_version", "op22_material_ref", "op22_next_required_step", "op22_validation_command_matrix_status_ref",
    "op22_validation_command_matrix_ready", "op22_result_memo_envelope_ref", "op22_result_memo_required_section_ref_count",
    "acceptance_finalizer_status_ref", "acceptance_finalizer_allowed_status_refs", "acceptance_finalizer_ready",
    "acceptance_finalizer_reason_refs", "acceptance_finalizer_blocker_refs", "acceptance_finalizer_blocker_ref_count",
    "ready_condition_refs", "ready_condition_ref_count", "ready_condition_pass_flags", "ready_condition_pass_count",
    "fail_closed_condition_refs", "fail_closed_condition_ref_count", "observed_fail_closed_condition_refs", "observed_fail_closed_condition_ref_count",
    "scope_confirmed", "mn11_return_operation_required_intake_passed", "local_only_preflight_passed", "actual_source_guard_passed",
    "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_touch_validation_passed",
    "no_promotion_boundary_confirmed", "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review",
    "actual_review_evidence_complete_from_real_operation_claimed_here", "disposal_verified", "post_mn11_actual_operation_acceptance_ready",
    "post_mn11_actual_operation_ready_for_downstream_manual_decision_hold", "acceptance_ready_without_downstream_promotion",
    "fail_closed_finalizer_does_not_generate_body_full_packet", "fail_closed_finalizer_does_not_run_actual_human_review",
    "fail_closed_finalizer_does_not_create_actual_rows", "fail_closed_finalizer_does_not_execute_validation_commands",
    "fail_closed_finalizer_does_not_execute_postcr22_reentry", "downstream_manual_decision_hold_required", "manual_decision_auto_executes_downstream",
    "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed",
    "p7_complete", "release_allowed", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "rn_real_device_modal_verified_claimed_here",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_mn11_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_MN11_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _pmn_op22_clean_ref_list(value: Sequence[Any] | None, *, default: Sequence[str]) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        value = default
    refs = [_clean_ref(item, default="", max_length=220) for item in value]
    return [ref for ref in refs if ref]


def _pmn_op22_blockers(op21: Mapping[str, Any] | None, present_sections: Sequence[str]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op21, Mapping):
        blockers.append("pmn_op22_op21_existing_postcr22_ex07_ex18_reentry_mapping_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_contract(op21)
        except ValueError:
            blockers.append("pmn_op22_op21_existing_postcr22_ex07_ex18_reentry_mapping_invalid")
        if op21.get("existing_postcr22_ex07_ex18_reentry_mapping_ready") is not True:
            blockers.append("pmn_op22_op21_existing_postcr22_ex07_ex18_reentry_mapping_not_ready")
        if op21.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF:
            blockers.append("pmn_op22_op21_next_step_not_validation_result_memo_envelope")
        if op21.get("reentry_executed_here") is not False or op21.get("postcr22_ex07_ex18_reentry_executed_here") is not False:
            blockers.append("pmn_op22_op21_reentry_was_executed_here")
        for false_field in (
            "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_reintake_execution_requested_here",
            "r52_reintake_execution_started_here", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed",
        ):
            if op21.get(false_field) is not False:
                blockers.append(f"pmn_op22_op21_{false_field}_promoted")
    missing_sections = [
        section for section in P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS
        if section not in set(present_sections)
    ]
    if missing_sections:
        blockers.append("pmn_op22_result_memo_required_sections_missing")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope(
    *,
    existing_postcr22_ex07_ex18_reentry_mapping: Mapping[str, Any] | None = None,
    target_test_status_refs: Sequence[Any] | None = None,
    selected_regression_status_refs: Sequence[Any] | None = None,
    compileall_status_ref: Any = "compileall_status_to_be_recorded_by_operator_bodyfree",
    changed_file_refs: Sequence[Any] | None = None,
    result_memo_section_refs: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP22 body-free validation matrix / result memo envelope material."""

    op21 = existing_postcr22_ex07_ex18_reentry_mapping
    session_id = _safe_review_session_id(review_session_id or (op21 or {}).get("review_session_id") if isinstance(op21, Mapping) else review_session_id)
    present_sections = _pmn_op22_clean_ref_list(
        result_memo_section_refs,
        default=P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS,
    )
    blockers = _pmn_op22_blockers(op21, present_sections)
    forbidden_paths = _scan_forbidden_payload_key_paths({"present_sections": present_sections}, path="pmn_op22_result_memo_envelope")
    if forbidden_paths:
        blockers.append("pmn_op22_result_memo_envelope_forbidden_payload_key_detected")
    ready = not blockers
    status_ref = P7_R54_AHR_POST_MN11_PMN_OP22_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_STATUS_REF
    missing_sections = [
        section for section in P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS
        if section not in set(present_sections)
    ]
    target_statuses = _pmn_op22_clean_ref_list(
        target_test_status_refs,
        default=tuple("target_status_to_be_recorded_" + ref for ref in P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS),
    )
    selected_regression_statuses = _pmn_op22_clean_ref_list(
        selected_regression_status_refs,
        default=tuple("selected_regression_status_to_be_recorded_" + ref for ref in P7_R54_AHR_POST_MN11_PMN_OP22_SELECTED_REGRESSION_COMMAND_REFS),
    )
    changed_refs = _pmn_op22_clean_ref_list(
        changed_file_refs,
        default=(
            "ai_services_ai_inference_post_mn11_actual_local_only_human_review_operation_helper_modified",
            "ai_tests_post_mn11_pmn_op22_op23_contract_added",
            "ai_tests_post_mn11_pmn_op00_op23_result_memo_added",
        ),
    )
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP22_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op21_schema_version": (op21 or {}).get("schema_version") if isinstance(op21, Mapping) else None,
        "op21_material_ref": (op21 or {}).get("material_id", "postmn11_pmn_op21_existing_postcr22_ex07_ex18_reentry_mapping_bodyfree") if isinstance(op21, Mapping) else "missing_op21_material",
        "op21_next_required_step": (op21 or {}).get("next_required_step") if isinstance(op21, Mapping) else None,
        "op21_existing_postcr22_ex07_ex18_reentry_mapping_status_ref": (op21 or {}).get("existing_postcr22_ex07_ex18_reentry_mapping_status_ref") if isinstance(op21, Mapping) else None,
        "op21_existing_postcr22_ex07_ex18_reentry_mapping_ready": (op21 or {}).get("existing_postcr22_ex07_ex18_reentry_mapping_ready") is True if isinstance(op21, Mapping) else False,
        "op21_reentry_mapping_row_count": _safe_int((op21 or {}).get("reentry_mapping_row_count")) if isinstance(op21, Mapping) else 0,
        "op21_actual_review_evidence_complete": (op21 or {}).get("actual_review_evidence_complete") is True if isinstance(op21, Mapping) else False,
        "op21_actual_review_evidence_complete_from_real_review": (op21 or {}).get("actual_review_evidence_complete_from_real_review") is True if isinstance(op21, Mapping) else False,
        "op21_reentry_executed_here": (op21 or {}).get("reentry_executed_here") is True if isinstance(op21, Mapping) else False,
        "op21_postcr22_ex07_ex18_reentry_executed_here": (op21 or {}).get("postcr22_ex07_ex18_reentry_executed_here") is True if isinstance(op21, Mapping) else False,
        "op21_actual_source_guard_passed": (op21 or {}).get("actual_source_guard_passed") is True if isinstance(op21, Mapping) else False,
        "op21_disposal_verified": (op21 or {}).get("disposal_verified") is True if isinstance(op21, Mapping) else False,
        "validation_command_matrix_status_ref": status_ref,
        "validation_command_matrix_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP22_ALLOWED_STATUS_REFS),
        "validation_command_matrix_ready": ready,
        "validation_command_matrix_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP22_READY_REASON_REFS) if ready else [],
        "validation_command_matrix_blocker_refs": blockers,
        "validation_command_matrix_blocker_ref_count": len(blockers),
        "validation_command_matrix_ref": P7_R54_AHR_POST_MN11_PMN_OP22_VALIDATION_COMMAND_MATRIX_REF,
        "target_test_command_refs": list(P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS),
        "target_test_command_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS),
        "target_test_status_refs": target_statuses,
        "target_test_status_ref_count": len(target_statuses),
        "selected_regression_command_refs": list(P7_R54_AHR_POST_MN11_PMN_OP22_SELECTED_REGRESSION_COMMAND_REFS),
        "selected_regression_command_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP22_SELECTED_REGRESSION_COMMAND_REFS),
        "selected_regression_status_refs": selected_regression_statuses,
        "selected_regression_status_ref_count": len(selected_regression_statuses),
        "compileall_command_ref": P7_R54_AHR_POST_MN11_PMN_OP22_COMPILEALL_COMMAND_REF,
        "compileall_status_ref": _clean_ref(compileall_status_ref, default="compileall_status_to_be_recorded_by_operator_bodyfree", max_length=220),
        "validation_commands_executed_here": False,
        "target_tests_green_claimed_here": False,
        "selected_regression_green_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "compileall_result_claimed_here": False,
        "zip_overlay_verification_claimed_here": False,
        "result_memo_envelope_ref": P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_ENVELOPE_REF,
        "result_memo_required_section_refs": list(P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_required_section_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_present_section_refs": present_sections,
        "result_memo_present_section_ref_count": len(present_sections),
        "result_memo_missing_section_refs": missing_sections,
        "result_memo_missing_section_ref_count": len(missing_sections),
        "result_memo_is_bodyfree_envelope": True,
        "result_memo_file_materialized_here": False,
        "result_memo_forbidden_payload_key_paths": forbidden_paths,
        "result_memo_forbidden_payload_key_path_count": len(forbidden_paths),
        "result_memo_does_not_include_forbidden_payload": not forbidden_paths,
        "result_memo_records_actual_operation_status": True,
        "result_memo_records_actual_evidence_status": True,
        "result_memo_records_not_claimed_boundary": True,
        "result_memo_records_next_required_step": True,
        "result_memo_does_not_claim_full_backend_suite_green": True,
        "result_memo_does_not_claim_rn_contract_green": True,
        "result_memo_does_not_claim_rn_real_device_modal_verified": True,
        "actual_operation_status_ref": "actual_operation_status_not_run_here_bodyfree_envelope",
        "actual_evidence_status_ref": "actual_evidence_status_from_supplied_op21_bodyfree_material",
        "actual_source_guard_passed": ready and isinstance(op21, Mapping) and op21.get("actual_source_guard_passed") is True,
        "actual_human_review_executed_by_person": ready and isinstance(op21, Mapping) and op21.get("actual_human_review_executed_by_person") is True,
        "disposal_verified": ready and isinstance(op21, Mapping) and op21.get("disposal_verified") is True,
        "actual_review_evidence_complete": ready and isinstance(op21, Mapping) and op21.get("actual_review_evidence_complete") is True,
        "actual_review_evidence_complete_from_real_review": ready and isinstance(op21, Mapping) and op21.get("actual_review_evidence_complete_from_real_review") is True,
        "actual_review_evidence_complete_from_real_operation_claimed_here": False,
        "actual_body_full_packet_generation_run_here": False,
        "actual_24_case_local_only_human_review_run_here": False,
        "actual_operation_receipt_created_here_by_helper": False,
        "actual_rows_created_here_by_helper": False,
        "actual_disposal_purge_executed_here": False,
        "downstream_manual_decision_hold_required": True,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP22_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP21_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP22_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP21_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    material["changed_file_refs"] = changed_refs
    material.pop("changed_file_refs")
    # _false_flags() is intentionally applied as a baseline; restore the OP22
    # body-free evidence status fields that are allowed to mirror supplied OP21
    # contract material without claiming that this helper ran the real operation.
    material["actual_source_guard_passed"] = ready and isinstance(op21, Mapping) and op21.get("actual_source_guard_passed") is True
    material["actual_human_review_executed_by_person"] = ready and isinstance(op21, Mapping) and op21.get("actual_human_review_executed_by_person") is True
    material["disposal_verified"] = ready and isinstance(op21, Mapping) and op21.get("disposal_verified") is True
    material["actual_review_evidence_complete"] = ready and isinstance(op21, Mapping) and op21.get("actual_review_evidence_complete") is True
    material["actual_review_evidence_complete_from_real_review"] = ready and isinstance(op21, Mapping) and op21.get("actual_review_evidence_complete_from_real_review") is True
    material["actual_review_evidence_complete_from_real_operation_claimed_here"] = False
    material["actual_body_full_packet_generation_run_here"] = False
    material["actual_24_case_local_only_human_review_run_here"] = False
    material["actual_operation_receipt_created_here_by_helper"] = False
    material["actual_rows_created_here_by_helper"] = False
    material["actual_disposal_purge_executed_here"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_MN11_PMN_OP22_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP22")
    return material


def assert_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP22_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP22")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP22_VALIDATION_COMMAND_MATRIX_RESULT_MEMO_ENVELOPE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP22_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP22",
        allowed_true_flag_refs=P7_R54_AHR_POST_MN11_PMN_OP22_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if tuple(data.get("validation_command_matrix_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP22_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 allowed status refs changed")
    ready = data.get("validation_command_matrix_status_ref") == P7_R54_AHR_POST_MN11_PMN_OP22_READY_STATUS_REF
    blockers = list(data.get("validation_command_matrix_blocker_refs") or [])
    if data.get("validation_command_matrix_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 ready flag changed")
    if data.get("validation_command_matrix_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 blocker count changed")
    if tuple(data.get("target_test_command_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 target test command refs changed")
    if data.get("target_test_command_ref_count") != len(P7_R54_AHR_POST_MN11_PMN_OP22_TARGET_TEST_COMMAND_REFS):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 target test command count changed")
    if data.get("target_test_status_ref_count") != len(data.get("target_test_status_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 target status count changed")
    if tuple(data.get("selected_regression_command_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP22_SELECTED_REGRESSION_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 selected regression command refs changed")
    if data.get("selected_regression_status_ref_count") != len(data.get("selected_regression_status_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 selected regression status count changed")
    if data.get("compileall_command_ref") != P7_R54_AHR_POST_MN11_PMN_OP22_COMPILEALL_COMMAND_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 compileall command ref changed")
    if tuple(data.get("result_memo_required_section_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP22_RESULT_MEMO_REQUIRED_SECTION_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 result memo required sections changed")
    missing_sections = list(data.get("result_memo_missing_section_refs") or [])
    if data.get("result_memo_missing_section_ref_count") != len(missing_sections):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 missing section count changed")
    if data.get("result_memo_present_section_ref_count") != len(data.get("result_memo_present_section_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 present section count changed")
    if data.get("result_memo_forbidden_payload_key_path_count") != len(data.get("result_memo_forbidden_payload_key_paths") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 forbidden key path count changed")
    for key in (
        "validation_commands_executed_here", "target_tests_green_claimed_here", "selected_regression_green_claimed_here",
        "full_backend_suite_green_claimed_here", "compileall_result_claimed_here", "zip_overlay_verification_claimed_here",
        "actual_review_evidence_complete_from_real_operation_claimed_here", "actual_body_full_packet_generation_run_here",
        "actual_24_case_local_only_human_review_run_here", "actual_operation_receipt_created_here_by_helper",
        "actual_rows_created_here_by_helper", "actual_disposal_purge_executed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP22 forbidden execution/claim changed: {key}")
    for key in (
        "result_memo_is_bodyfree_envelope", "result_memo_does_not_include_forbidden_payload",
        "result_memo_records_actual_operation_status", "result_memo_records_actual_evidence_status",
        "result_memo_records_not_claimed_boundary", "result_memo_records_next_required_step",
        "result_memo_does_not_claim_full_backend_suite_green", "result_memo_does_not_claim_rn_contract_green",
        "result_memo_does_not_claim_rn_real_device_modal_verified", "downstream_manual_decision_hold_required",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP22 required boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 not-claimed boundary changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 not-claimed refs changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 basis changed")
    if ready:
        if blockers or missing_sections:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 ready material cannot carry blockers or missing sections")
        if data.get("validation_command_matrix_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP22_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 ready reasons changed")
        for key in (
            "op21_existing_postcr22_ex07_ex18_reentry_mapping_ready", "op21_actual_review_evidence_complete",
            "op21_actual_review_evidence_complete_from_real_review", "op21_actual_source_guard_passed", "op21_disposal_verified",
            "actual_source_guard_passed", "actual_human_review_executed_by_person", "disposal_verified",
            "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP22 ready field changed: {key}")
        if data.get("op21_reentry_executed_here") is not False or data.get("op21_postcr22_ex07_ex18_reentry_executed_here") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 cannot execute re-entry")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP22_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP22_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 ready steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 ready next step changed")
    else:
        if data.get("validation_command_matrix_status_ref") != P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 blocked material must carry blockers")
        if data.get("actual_review_evidence_complete") is not False or data.get("actual_review_evidence_complete_from_real_review") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 blocked material cannot complete evidence")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP22_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP22 blocked next step changed")
    return True


def _pmn_op23_blockers(op22: Mapping[str, Any] | None, ready_flags: Mapping[str, bool]) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op22, Mapping):
        blockers.append("pmn_op23_op22_validation_command_matrix_result_memo_envelope_missing")
    else:
        try:
            assert_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_contract(op22)
        except ValueError:
            blockers.append("pmn_op23_op22_validation_command_matrix_result_memo_envelope_invalid")
        if op22.get("validation_command_matrix_ready") is not True:
            blockers.append("pmn_op23_op22_validation_command_matrix_result_memo_envelope_not_ready")
        if op22.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF:
            blockers.append("pmn_op23_op22_next_step_not_acceptance_fail_closed_finalizer")
        for false_field in (
            "validation_commands_executed_here", "target_tests_green_claimed_here", "selected_regression_green_claimed_here",
            "full_backend_suite_green_claimed_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed",
            "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed",
        ):
            if op22.get(false_field) is not False:
                blockers.append(f"pmn_op23_op22_{false_field}_promoted_or_claimed")
    for condition_ref, passed in ready_flags.items():
        if passed is not True:
            blockers.append(f"pmn_op23_ready_condition_failed_{condition_ref}")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer(
    *,
    validation_command_matrix_result_memo_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PMN-OP23 body-free acceptance / fail-closed finalizer material."""

    op22 = validation_command_matrix_result_memo_envelope
    session_id = _safe_review_session_id(review_session_id or (op22 or {}).get("review_session_id") if isinstance(op22, Mapping) else review_session_id)
    op22_ready = isinstance(op22, Mapping) and op22.get("validation_command_matrix_ready") is True
    actual_source_guard_passed = op22_ready and op22.get("actual_source_guard_passed") is True
    disposal_verified = op22_ready and op22.get("disposal_verified") is True
    actual_review_evidence_complete = op22_ready and op22.get("actual_review_evidence_complete") is True
    actual_review_evidence_complete_from_real_review = op22_ready and op22.get("actual_review_evidence_complete_from_real_review") is True
    ready_flags: dict[str, bool] = {
        "scope_confirmed": op22_ready,
        "mn11_return_operation_required_intake_passed": op22_ready,
        "local_only_preflight_passed": op22_ready,
        "actual_source_guard_passed": actual_source_guard_passed,
        "no_body_leak_validation_passed": op22_ready,
        "no_question_text_validation_passed": op22_ready,
        "no_path_hash_validation_passed": op22_ready,
        "no_touch_validation_passed": op22_ready,
        "no_promotion_boundary_confirmed": op22_ready,
    }
    blockers = _pmn_op23_blockers(op22, ready_flags)
    ready = not blockers
    status_ref = P7_R54_AHR_POST_MN11_PMN_OP23_READY_STATUS_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_STATUS_REF
    observed_fail_closed_refs = [] if ready else [
        ref for ref, passed in ready_flags.items() if passed is not True
    ]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_MN11_PMN_OP23_ACCEPTANCE_FAIL_CLOSED_FINALIZER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_MN11_STEP,
        "scope": P7_R54_AHR_POST_MN11_SCOPE,
        "policy_kind": P7_R54_AHR_POST_MN11_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_20260630",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op22_schema_version": (op22 or {}).get("schema_version") if isinstance(op22, Mapping) else None,
        "op22_material_ref": (op22 or {}).get("material_id", "postmn11_pmn_op22_validation_command_matrix_result_memo_envelope_bodyfree") if isinstance(op22, Mapping) else "missing_op22_material",
        "op22_next_required_step": (op22 or {}).get("next_required_step") if isinstance(op22, Mapping) else None,
        "op22_validation_command_matrix_status_ref": (op22 or {}).get("validation_command_matrix_status_ref") if isinstance(op22, Mapping) else None,
        "op22_validation_command_matrix_ready": op22_ready,
        "op22_result_memo_envelope_ref": (op22 or {}).get("result_memo_envelope_ref") if isinstance(op22, Mapping) else None,
        "op22_result_memo_required_section_ref_count": _safe_int((op22 or {}).get("result_memo_required_section_ref_count")) if isinstance(op22, Mapping) else 0,
        "acceptance_finalizer_status_ref": status_ref,
        "acceptance_finalizer_allowed_status_refs": list(P7_R54_AHR_POST_MN11_PMN_OP23_ALLOWED_STATUS_REFS),
        "acceptance_finalizer_ready": ready,
        "acceptance_finalizer_reason_refs": list(P7_R54_AHR_POST_MN11_PMN_OP23_READY_REASON_REFS) if ready else [],
        "acceptance_finalizer_blocker_refs": blockers,
        "acceptance_finalizer_blocker_ref_count": len(blockers),
        "ready_condition_refs": list(P7_R54_AHR_POST_MN11_PMN_OP23_READY_CONDITION_REFS),
        "ready_condition_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP23_READY_CONDITION_REFS),
        "ready_condition_pass_flags": ready_flags,
        "ready_condition_pass_count": sum(1 for value in ready_flags.values() if value is True),
        "fail_closed_condition_refs": list(P7_R54_AHR_POST_MN11_PMN_OP23_FAIL_CLOSED_CONDITION_REFS),
        "fail_closed_condition_ref_count": len(P7_R54_AHR_POST_MN11_PMN_OP23_FAIL_CLOSED_CONDITION_REFS),
        "observed_fail_closed_condition_refs": observed_fail_closed_refs,
        "observed_fail_closed_condition_ref_count": len(observed_fail_closed_refs),
        "scope_confirmed": ready_flags["scope_confirmed"],
        "mn11_return_operation_required_intake_passed": ready_flags["mn11_return_operation_required_intake_passed"],
        "local_only_preflight_passed": ready_flags["local_only_preflight_passed"],
        "actual_source_guard_passed": actual_source_guard_passed,
        "no_body_leak_validation_passed": ready_flags["no_body_leak_validation_passed"],
        "no_question_text_validation_passed": ready_flags["no_question_text_validation_passed"],
        "no_path_hash_validation_passed": ready_flags["no_path_hash_validation_passed"],
        "no_touch_validation_passed": ready_flags["no_touch_validation_passed"],
        "no_promotion_boundary_confirmed": ready_flags["no_promotion_boundary_confirmed"],
        "actual_review_evidence_complete": ready and actual_review_evidence_complete,
        "actual_review_evidence_complete_from_real_review": ready and actual_review_evidence_complete_from_real_review,
        "actual_review_evidence_complete_from_real_operation_claimed_here": False,
        "disposal_verified": ready and disposal_verified,
        "post_mn11_actual_operation_acceptance_ready": ready,
        "post_mn11_actual_operation_ready_for_downstream_manual_decision_hold": ready,
        "acceptance_ready_without_downstream_promotion": ready,
        "fail_closed_finalizer_does_not_generate_body_full_packet": True,
        "fail_closed_finalizer_does_not_run_actual_human_review": True,
        "fail_closed_finalizer_does_not_create_actual_rows": True,
        "fail_closed_finalizer_does_not_execute_validation_commands": True,
        "fail_closed_finalizer_does_not_execute_postcr22_reentry": True,
        "downstream_manual_decision_hold_required": True,
        "manual_decision_auto_executes_downstream": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "full_backend_suite_green_claimed_here": False,
        "rn_contract_green_claimed_here": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "actual_review_basis_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP23_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP22_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_MN11_PMN_OP23_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_MN11_PMN_OP22_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_MN11_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_REF if ready else P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_mn11_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    # _false_flags() is intentionally applied as a baseline; restore OP23
    # acceptance fields that are allowed to be true for body-free contract
    # material, while keeping all downstream promotion / execution claims false.
    material["scope_confirmed"] = ready_flags["scope_confirmed"]
    material["mn11_return_operation_required_intake_passed"] = ready_flags["mn11_return_operation_required_intake_passed"]
    material["local_only_preflight_passed"] = ready_flags["local_only_preflight_passed"]
    material["actual_source_guard_passed"] = actual_source_guard_passed
    material["no_body_leak_validation_passed"] = ready_flags["no_body_leak_validation_passed"]
    material["no_question_text_validation_passed"] = ready_flags["no_question_text_validation_passed"]
    material["no_path_hash_validation_passed"] = ready_flags["no_path_hash_validation_passed"]
    material["no_touch_validation_passed"] = ready_flags["no_touch_validation_passed"]
    material["no_promotion_boundary_confirmed"] = ready_flags["no_promotion_boundary_confirmed"]
    material["actual_review_evidence_complete"] = ready and actual_review_evidence_complete
    material["actual_review_evidence_complete_from_real_review"] = ready and actual_review_evidence_complete_from_real_review
    material["actual_review_evidence_complete_from_real_operation_claimed_here"] = False
    material["disposal_verified"] = ready and disposal_verified
    material["post_mn11_actual_operation_acceptance_ready"] = ready
    material["post_mn11_actual_operation_ready_for_downstream_manual_decision_hold"] = ready
    material["acceptance_ready_without_downstream_promotion"] = ready
    material["manual_decision_auto_executes_downstream"] = False
    material["p5_final_allowed"] = False
    material["p6_start_allowed"] = False
    material["p8_start_allowed"] = False
    material["actual_r52_reintake_execution_confirmed"] = False
    material["p7_complete"] = False
    material["release_allowed"] = False
    _required_fields_present(material, required=P7_R54_AHR_POST_MN11_PMN_OP23_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP23")
    return material


def assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_MN11_PMN_OP23_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostMN11-PMN-OP23")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_MN11_PMN_OP23_ACCEPTANCE_FAIL_CLOSED_FINALIZER_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_MN11_PMN_OP23_STEP_REF,
        source="P7-R54-AHR-PostMN11-PMN-OP23",
        allowed_true_flag_refs=P7_R54_AHR_POST_MN11_PMN_OP23_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if tuple(data.get("acceptance_finalizer_allowed_status_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP23_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 allowed status refs changed")
    ready = data.get("acceptance_finalizer_status_ref") == P7_R54_AHR_POST_MN11_PMN_OP23_READY_STATUS_REF
    blockers = list(data.get("acceptance_finalizer_blocker_refs") or [])
    if data.get("acceptance_finalizer_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 ready flag changed")
    if data.get("acceptance_finalizer_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 blocker count changed")
    if tuple(data.get("ready_condition_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP23_READY_CONDITION_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 ready condition refs changed")
    if tuple(data.get("fail_closed_condition_refs") or ()) != P7_R54_AHR_POST_MN11_PMN_OP23_FAIL_CLOSED_CONDITION_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 fail-closed condition refs changed")
    ready_flags = data.get("ready_condition_pass_flags") or {}
    if data.get("ready_condition_pass_count") != sum(1 for value in ready_flags.values() if value is True):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 ready condition pass count changed")
    if data.get("observed_fail_closed_condition_ref_count") != len(data.get("observed_fail_closed_condition_refs") or []):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 observed fail-closed count changed")
    for key in (
        "fail_closed_finalizer_does_not_generate_body_full_packet", "fail_closed_finalizer_does_not_run_actual_human_review",
        "fail_closed_finalizer_does_not_create_actual_rows", "fail_closed_finalizer_does_not_execute_validation_commands",
        "fail_closed_finalizer_does_not_execute_postcr22_reentry", "downstream_manual_decision_hold_required",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP23 required boundary changed: {key}")
    for key in (
        "actual_review_evidence_complete_from_real_operation_claimed_here", "manual_decision_auto_executes_downstream",
        "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed", "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here", "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP23 promotion/claim changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 not-claimed boundary changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_MN11_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 not-claimed refs changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 basis changed")
    if ready:
        if blockers or data.get("observed_fail_closed_condition_refs"):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 ready material cannot carry blockers")
        if data.get("acceptance_finalizer_reason_refs") != list(P7_R54_AHR_POST_MN11_PMN_OP23_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 ready reasons changed")
        for key in (
            "op22_validation_command_matrix_ready", "scope_confirmed", "mn11_return_operation_required_intake_passed",
            "local_only_preflight_passed", "actual_source_guard_passed", "no_body_leak_validation_passed",
            "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_touch_validation_passed",
            "no_promotion_boundary_confirmed", "actual_review_evidence_complete", "actual_review_evidence_complete_from_real_review",
            "disposal_verified", "post_mn11_actual_operation_acceptance_ready", "post_mn11_actual_operation_ready_for_downstream_manual_decision_hold",
            "acceptance_ready_without_downstream_promotion",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostMN11-PMN-OP23 ready field changed: {key}")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP23_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_MN11_PMN_OP23_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 ready steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 ready next step changed")
    else:
        if data.get("acceptance_finalizer_status_ref") != P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 blocked material must carry blockers")
        if data.get("post_mn11_actual_operation_acceptance_ready") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 blocked material cannot be acceptance-ready")
        if data.get("actual_review_evidence_complete") is not False or data.get("actual_review_evidence_complete_from_real_review") is not False:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 blocked material cannot complete evidence")
        if data.get("next_required_step") != P7_R54_AHR_POST_MN11_PMN_OP23_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostMN11-PMN-OP23 blocked next step changed")
    return True


def build_p7_r54_ahr_post_mn11_actual_operation_validation_command_matrix_result_memo_envelope_bodyfree(
    *,
    existing_postcr22_ex07_ex18_reentry_mapping: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope(
        existing_postcr22_ex07_ex18_reentry_mapping=existing_postcr22_ex07_ex18_reentry_mapping,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_validation_command_matrix_result_memo_envelope_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op22_validation_command_matrix_result_memo_envelope_contract(data)


def build_p7_r54_ahr_post_mn11_actual_operation_acceptance_fail_closed_finalizer_bodyfree(
    *,
    validation_command_matrix_result_memo_envelope: Mapping[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    return build_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer(
        validation_command_matrix_result_memo_envelope=validation_command_matrix_result_memo_envelope,
        **kwargs,
    )


def assert_p7_r54_ahr_post_mn11_actual_operation_acceptance_fail_closed_finalizer_bodyfree_contract(data: Mapping[str, Any]) -> bool:
    return assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(data)
