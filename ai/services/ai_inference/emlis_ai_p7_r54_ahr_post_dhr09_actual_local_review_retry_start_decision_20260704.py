# -*- coding: utf-8 -*-
"""Post-DHR09 actual local-only review retry/start decision helpers for RSR-OP00〜OP15.

RSR is intentionally a thin Post-DHR09 boundary.  It does not generate
body-full packets, run actual local-only human review, create actual receipts
or rows, execute disposal/purge, run DMD/R52, start P5/P6/P8, complete P7, or
allow release.

* RSR-OP00 refreezes the scope, no-touch boundary, and no-promotion boundary
  after DHR-OP09.
* RSR-OP01 intakes the DHR-OP09 result memo / selected branch / next step as
  body-free material.  It accepts the current retry/start-required default only
  as an instruction to continue with RSR-OP02; it does not convert DHR-OP09 into
  actual review execution, actual evidence, DMD handoff, P8 start, P7
  completion, or release readiness.
* RSR-OP02 verifies DMD-OP08 / ALR-OP12 / ELR-OP19 / DHR-OP09 as body-free
  upstream relationship material. DHR-OP09 closed retry/start is sufficient for
  the default path; any supplied upstream memo must not conflict or promote
  helper green into actual evidence.
* RSR-OP03 accepts only an externally supplied explicit local-only allow
  receipt. Missing/invalid/scope-mismatched allow stops before body-full packet
  generation or actual review execution.
* RSR-OP04 classifies readiness blockers before any local-only session envelope
  or body-full packet request can be prepared.
* RSR-OP05 materializes only a body-free review session envelope and reviewer
  person boundary. It does not run review or create actual source evidence.
* RSR-OP06 materializes only a 24-case body-free packet request boundary. It
  does not generate the body-full packet.
* RSR-OP07 intakes only a body-free packet generation receipt and export/
  persistence denylist scan result. It does not run actual human review.
* RSR-OP08 freezes the selection-only reviewer form, rating axes, score
  options, and question-need observation classes without materializing P8
  questions.
* RSR-OP09 captures only body-free actual local-only review lifecycle state.
  Completed lifecycle state requires an OP10 receipt; this helper does not run
  the review or accept the receipt here.
* RSR-OP10 intakes only an externally supplied body-free actual operation
  receipt. It may accept that receipt as evidence input, but never creates it
  and never treats receipt acceptance as rows/evidence completion.
* RSR-OP11 intakes externally supplied body-free sanitized review result rows
  and rating rows together. It validates provenance and row alignment without
  creating rows, materializing P8 questions, disposal/purge receipts, DMD/R52,
  P5/P6/P8/P7 completion, or release.
* RSR-OP12 intakes externally supplied body-free question-need observation rows
  only as P7/P8 Bridge material. It never materializes question text or starts
  P8 design.
* RSR-OP13 intakes an externally supplied body-free disposal/purge receipt. It
  never executes purge itself and never completes final evidence.
* RSR-OP14 performs the final body-free no-leak / no-promotion / source-kind
  validation across supplied RSR materials without creating actual evidence.
* RSR-OP15 resolves the next branch and can mark an evidence-complete candidate
  for DHR re-intake, but it never executes DHR/DMD/R52/P5/P6/P8/P7/release.
* RSR-OP16 closes the result memo / target tests / selected regression record as
  body-free material. It records verification results and the OP15 selected branch
  without converting tests, helper green, or complete candidate material into
  actual review execution or downstream promotion.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr
import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr


P7_R54_AHR_POST_DHR09_RSR_PHASE: Final = "P7"
P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_DHR09_RSR_STEP: Final = (
    "R54-AHR-PostDHR09_ActualLocalReview_RetryStartDecision_20260704"
)
P7_R54_AHR_POST_DHR09_RSR_SCOPE: Final = (
    "p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision"
)
P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND: Final = (
    "r54_ahr_post_dhr09_actual_local_review_retry_start_decision_bodyfree_boundary"
)
P7_R54_AHR_POST_DHR09_RSR_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postdhr09_rsr_session_20260704_current_received_284_95_268_181_v1"
)

P7_R54_AHR_POST_DHR09_RSR_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr."
    "op00_scope_no_touch_no_promotion_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr."
    "op01_dhr_op09_result_memo_selected_branch_next_step_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op02_upstream_relationship_verification.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op03_explicit_local_only_allow_receipt_acceptance_gate.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op04_readiness_blocker_classifier.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op05_local_only_review_session_envelope_reviewer_person_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op06_24_case_body_full_packet_transient_request_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op07_body_full_packet_generation_receipt_export_denylist_scan_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op08_selection_only_reviewer_form_rating_axis_contract_freeze.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP09_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op09_actual_local_only_review_lifecycle_state_capture.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP10_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op10_actual_operation_receipt_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP11_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op11_sanitized_review_result_rows_rating_rows_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.actual_operation_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.sanitized_review_result_row.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.rating_row.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.packet_generation_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT: Final = 24
P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.explicit_local_only_allow_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_REF: Final = (
    "explicit_local_only_allow_for_24_case_actual_review_start_retry_with_purge"
)

P7_R54_AHR_POST_DHR09_RSR_OP00_STEP_REF: Final = (
    "RSR-OP00_scope_no_touch_no_promotion_refreeze_after_DHR_OP09"
)
P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF: Final = (
    "RSR-OP01_DHR_OP09_result_memo_selected_branch_next_step_intake"
)
P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF: Final = (
    "RSR-OP02_upstream_relationship_verification_ALR_OP12_ELR_OP19_DHR_OP09_DMD_OP08"
)
P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF: Final = (
    "RSR-OP03_explicit_local_only_allow_receipt_acceptance_gate"
)
P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF: Final = "RSR-OP04_readiness_blocker_classifier"
P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF: Final = (
    "RSR-OP05_local_only_review_session_envelope_reviewer_person_boundary"
)
P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF: Final = (
    "RSR-OP06_24_case_body_full_packet_transient_request_boundary"
)
P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF: Final = (
    "RSR-OP07_body_full_packet_generation_receipt_export_denylist_scan_intake"
)
P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF: Final = (
    "RSR-OP08_selection_only_reviewer_form_rating_axis_contract_freeze"
)
P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF: Final = (
    "RSR-OP09_actual_local_only_review_lifecycle_state_capture"
)
P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF: Final = "RSR-OP10_actual_operation_receipt_intake"
P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF: Final = (
    "RSR-OP11_sanitized_review_result_rows_rating_rows_intake"
)
P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF: Final = (
    "RSR-OP12_question_need_observation_rows_intake_p7_p8_bridge_material_only"
)
P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF: Final = "RSR-OP13_disposal_purge_receipt_intake"
P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF: Final = (
    "RSR-OP14_final_no_leak_no_promotion_source_kind_validation"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF: Final = (
    "RSR-OP15_actual_evidence_complete_candidate_next_branch_resolver"
)
P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF: Final = "RSR-OP16_result_memo_tests_selected_regression_closure"
P7_R54_AHR_POST_DHR09_RSR_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP00_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF,
)
P7_R54_AHR_POST_DHR09_RSR_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:1]
)
P7_R54_AHR_POST_DHR09_RSR_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[1:]
)
P7_R54_AHR_POST_DHR09_RSR_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:2]
)
P7_R54_AHR_POST_DHR09_RSR_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[2:]
)
P7_R54_AHR_POST_DHR09_RSR_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:3]
)
P7_R54_AHR_POST_DHR09_RSR_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[3:]
)
P7_R54_AHR_POST_DHR09_RSR_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:4]
)
P7_R54_AHR_POST_DHR09_RSR_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[4:]
)
P7_R54_AHR_POST_DHR09_RSR_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:5]
)
P7_R54_AHR_POST_DHR09_RSR_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[5:]
)
P7_R54_AHR_POST_DHR09_RSR_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:6]
)
P7_R54_AHR_POST_DHR09_RSR_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[6:]
)
P7_R54_AHR_POST_DHR09_RSR_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:7]
)
P7_R54_AHR_POST_DHR09_RSR_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[7:]
)
P7_R54_AHR_POST_DHR09_RSR_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:8]
)
P7_R54_AHR_POST_DHR09_RSR_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[8:]
)
P7_R54_AHR_POST_DHR09_RSR_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:9]
)
P7_R54_AHR_POST_DHR09_RSR_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[9:]
)
P7_R54_AHR_POST_DHR09_RSR_OP09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:10]
)
P7_R54_AHR_POST_DHR09_RSR_OP09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[10:]
)
P7_R54_AHR_POST_DHR09_RSR_OP10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:11]
)
P7_R54_AHR_POST_DHR09_RSR_OP10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[11:]
)
P7_R54_AHR_POST_DHR09_RSR_OP11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:12]
)
P7_R54_AHR_POST_DHR09_RSR_OP11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[12:]
)

P7_R54_AHR_POST_DHR09_RSR_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-DHR09 Actual Local-Only Human Review Retry/Start Decision"
)
P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RETRY_OR_START_REQUIRED_BEFORE_DOWNSTREAM_HANDOFF_REF
)
P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_RETRY_OR_START_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_OPERATION_REF
)
P7_R54_AHR_POST_DHR09_RSR_DHR_HANDOFF_BRANCH_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_DMD_HANDOFF_READY_MANUAL_DECISION_REQUIRED_NO_AUTO_EXECUTION_REF
)
P7_R54_AHR_POST_DHR09_RSR_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "P8 question design",
    "P8 question implementation",
    "DMD execution",
    "R52 actual execution",
    "P5 finalization",
    "P6 start",
    "P7 complete",
    "release decision",
)
P7_R54_AHR_POST_DHR09_RSR_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(284).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(95).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(14).zip",
    "rn_zip_ref": "Cocolon(268).zip",
    "backend_zip_ref": "mashos-api(181).zip",
}
P7_R54_AHR_POST_DHR09_RSR_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R54AHR_PostDHR09_RetryStart_PreDesignMemo_20260704.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostDHR09_ActualLocalOnlyReview_RetryStartDecision_DetailedDesign_ImplementationOrder_20260704.md",
    "R54_AHR_PostELR19_DownstreamManualDecision_HandoffOrRetry_DHR_OP00_OP09_Result_20260704.md",
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "dhr_op09_result_memo_closure_is_not_actual_review_execution",
    "dhr_op09_retry_or_start_branch_is_not_explicit_local_only_allow_granted",
    "dhr_op09_retry_or_start_branch_is_not_body_full_packet_generation",
    "dhr_op09_retry_or_start_branch_is_not_operation_receipt_creation",
    "helper_green_is_not_actual_human_review_complete",
    "target_green_is_not_actual_human_review_complete",
    "result_memo_green_is_not_actual_human_review_complete",
    "question_need_observation_is_not_p8_question_design",
    "actual_source_claim_requires_person_review_receipts_rows_and_purge",
    "release_decision_is_not_allowed_here",
)
P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "explicit_local_only_allow_receipt_accepted",
    "actual_body_full_packet_generation",
    "actual_local_only_human_review_execution",
    "actual_operation_receipt_real_creation",
    "sanitized_review_result_rows_real_creation",
    "rating_rows_real_creation",
    "question_need_observation_rows_real_creation",
    "disposal_purge_real_execution",
    "actual_source_claim_for_dhr_reintake",
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
P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "DHR-OP09 closure != actual review complete",
    "DHR-OP09 retry/start branch != explicit local-only allow receipt",
    "RSR-OP00/OP01 helper green != actual local-only human review start",
    "RSR-OP00/OP01 helper green != actual evidence complete",
    "RSR-OP06 packet request != body-full packet generation",
    "RSR-OP07 packet generation receipt intake != actual local-only human review execution",
    "RSR-OP08 selection-only form contract != actual review rows",
    "RSR-OP09 lifecycle completed state != actual operation receipt accepted",
    "RSR-OP10 receipt accepted != review rows accepted",
    "RSR-OP11 review rows accepted != question need rows or purge accepted",
    "DMD handoff plan must not materialize from retry/start branch",
    "DMD/R52/P5/P6/P8/P7/release promotion is outside RSR-OP00/OP01",
)

P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "explicit_local_only_allow_receipt_accepted_here",
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
    "actual_source_claim_for_dhr_reintake_materialized_here",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
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
P7_R54_AHR_POST_DHR09_RSR_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_DHR09_RSR_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
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
    "body_full_packet_generated_here",
    "actual_local_human_review_executed_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "release_allowed",
)
P7_R54_AHR_POST_DHR09_RSR_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = frozenset(
    {
        *dhr.P7_R54_AHR_POST_ELR19_DHR_FORBIDDEN_PAYLOAD_KEY_REFS,
        "raw_answer",
        "answer_text",
        "returned_surface_body",
        "body_full_packet",
        "body_full_packet_body",
        "reviewer_free_text",
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
P7_R54_AHR_POST_DHR09_RSR_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "explicit_local_only_allow_receipt_accepted_here",
    "actual_review_evidence_complete",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "actual_local_human_review_complete",
    "actual_local_human_review_executed",
    "actual_local_human_review_executed_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_disposal_purge_executed_here",
    "actual_source_claim_for_dhr_reintake_materialized_here",
    "helper_green_promoted_to_actual_review_complete",
    "target_green_promoted_to_actual_review_complete",
    "result_memo_green_promoted_to_actual_review_complete",
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

P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_RETRY_OR_START_REQUIRED_REF: Final = (
    "RSR_DHR09_INTAKE_RETRY_OR_START_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF: Final = (
    "RSR_DHR09_INTAKE_WAITING_OR_INCOMPLETE"
)
P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF: Final = (
    "RSR_DHR09_INTAKE_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF: Final = (
    "RSR_DHR09_INTAKE_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD"
)
P7_R54_AHR_POST_DHR09_RSR_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_RETRY_OR_START_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF,
)
P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_RETRY_OR_START_REQUIRED_REF: Final = (
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_RETRY_OR_START_REQUIRED_REF
)
P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_WAITING_OR_INCOMPLETE_REF: Final = (
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF
)
P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_REPAIR_REQUIRED_REF: Final = (
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF
)
P7_R54_AHR_POST_DHR09_RSR_DHR09_INTAKE_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF: Final = (
    P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_DHR_OP09_CLOSED_RETRY_BRANCH_REF: Final = (
    "wait_for_dhr_op09_closed_retry_start_branch"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DHR_OP09_RESULT_MEMO_BOUNDARY_REF: Final = (
    "repair_dhr_op09_result_memo_boundary_before_rsr"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_UNEXPECTED_DHR_HANDOFF_BRANCH_REF: Final = (
    "manual_hold_unexpected_dhr_handoff_branch_without_auto_execution"
)

P7_R54_AHR_POST_DHR09_RSR_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "expected_default_branch_ref", "expected_default_next_required_step_ref", "not_stage_refs",
    "not_stage_ref_count", "support_material_refs", "support_material_ref_count", "local_received_zip_refs",
    "local_received_zip_ref_count", "body_free", "rsr_op00_scope_confirmed", "rsr_op00_no_touch_boundary_confirmed",
    "rsr_op00_no_promotion_boundary_confirmed", "rsr_op00_does_not_intake_dhr_op09_result_memo",
    "rsr_op00_does_not_generate_body_full_packet", "rsr_op00_does_not_run_actual_local_human_review",
    "rsr_op00_does_not_create_receipts_rows_or_disposal", "rsr_op00_does_not_accept_explicit_local_only_allow",
    "rsr_op00_does_not_execute_dmd_or_r52", "rsr_op00_does_not_start_p5_p6_p8_p7_or_release",
    "rsr_op00_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dhr09_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_DHR09_RSR_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed",
    "op00_no_touch_boundary_confirmed", "op00_no_promotion_boundary_confirmed", "op00_contract_valid",
    "dhr_op09_result_memo_present", "dhr_op09_contract_valid", "dhr_op09_schema_version", "dhr_op09_operation_step_ref",
    "dhr_op09_material_ref", "dhr_op09_result_memo_status_ref", "dhr_op09_result_memo_bodyfree_closed",
    "dhr_op09_selected_branch_ref", "dhr_op09_next_required_step", "dhr_op09_dmd_handoff_plan_materialized",
    "dhr_op09_dmd_handoff_ready_manual_decision_required", "dhr_op09_actual_local_human_review_execution_verified_here",
    "dhr_op09_actual_rows_created_verified_here", "dhr_op09_actual_disposal_purge_execution_verified_here",
    "dhr_op09_actual_body_full_packet_generation_verified_here", "target_tests_summary_bodyfree", "target_tests_summary_status_ref",
    "target_tests_passed_count", "target_tests_failed_count", "target_tests_timed_out", "selected_regression_summary_bodyfree",
    "selected_regression_summary_status_ref", "selected_regression_passed_count", "selected_regression_failed_count",
    "selected_regression_timed_out", "compileall_summary_bodyfree", "compileall_summary_status_ref", "compileall_passed",
    "compileall_failed", "compileall_timed_out", "dhr_op09_forbidden_payload_key_path_refs",
    "dhr_op09_forbidden_payload_key_path_count", "dhr_op09_body_like_value_path_refs", "dhr_op09_body_like_value_path_count",
    "dhr_op09_promotion_claim_refs", "dhr_op09_promotion_claim_ref_count", "rsr_op01_status_ref",
    "dhr_op09_intake_status_ref", "rsr_op01_allowed_status_refs", "rsr_op01_allowed_status_ref_count", "rsr_op01_ready",
    "rsr_op01_retry_or_start_required", "rsr_op01_waiting_or_incomplete", "rsr_op01_repair_required",
    "rsr_op01_unexpected_handoff_branch_manual_hold", "rsr_op01_reason_refs", "rsr_op01_reason_ref_count",
    "rsr_op01_blocker_refs", "rsr_op01_blocker_ref_count", "rsr_op01_ready_for_upstream_relationship_verification",
    "actual_review_execution_claimed_by_rsr_op01", "explicit_local_only_allow_accepted_by_rsr_op01",
    "rsr_op01_does_not_generate_body_full_packet", "rsr_op01_does_not_run_actual_local_human_review",
    "rsr_op01_does_not_create_receipts_rows_or_disposal", "rsr_op01_does_not_execute_dmd_or_r52",
    "rsr_op01_does_not_start_p5_p6_p8_p7_or_release", "rsr_op01_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_VERIFIED_BODYFREE_REF: Final = "RSR_UPSTREAM_RELATION_VERIFIED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_PARTIAL_DHR09_CLOSED_BODYFREE_REF: Final = "RSR_UPSTREAM_RELATION_PARTIAL_DHR09_CLOSED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_WAITING_OR_INCOMPLETE_REF: Final = "RSR_UPSTREAM_RELATION_WAITING_OR_INCOMPLETE"
P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_REPAIR_REQUIRED_REF: Final = "RSR_UPSTREAM_RELATION_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_VERIFIED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_PARTIAL_DHR09_CLOSED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_WAITING_OR_INCOMPLETE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_OP02_UPSTREAM_CHAIN_REFS: Final[tuple[str, ...]] = (
    "DMD-OP08_bodyfree_result_memo_retry_continue_decision_material_only",
    "ALR-OP12_bodyfree_result_memo_selected_action_schema_guard_closure_only",
    "ELR-OP19_bodyfree_result_memo_validation_closure_only",
    "DHR-OP09_bodyfree_handoff_or_retry_branch_closure_only",
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_RSR_OP01_RETRY_START_INTAKE_REF: Final = (
    "wait_for_rsr_op01_retry_start_intake_before_upstream_relationship_verification"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_UPSTREAM_RELATION_BEFORE_ALLOW_GATE_REF: Final = (
    "repair_upstream_relationship_before_explicit_local_only_allow_gate"
)

P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_ACCEPTED_BODYFREE_REF: Final = "RSR_EXPLICIT_ALLOW_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF: Final = "RSR_EXPLICIT_ALLOW_MISSING_WAITING"
P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = "RSR_EXPLICIT_ALLOW_INVALID_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_SCOPE_MISMATCH_BLOCKED_REF: Final = "RSR_EXPLICIT_ALLOW_SCOPE_MISMATCH_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_SCOPE_MISMATCH_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF: Final = (
    "wait_for_explicit_local_only_allow_receipt_before_actual_review_start"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF: Final = (
    "repair_explicit_local_only_allow_receipt_before_actual_review_start"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_MISMATCH_REF: Final = (
    "blocked_explicit_local_only_allow_scope_mismatch_no_actual_review_start"
)

P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_READY_TO_START_REF: Final = "RSR_READINESS_READY_TO_START_LOCAL_ONLY_REVIEW"
P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF: Final = "RSR_READINESS_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW"
P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF: Final = "RSR_READINESS_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_BODY_LEAK_RISK_BLOCKED_REF: Final = "RSR_READINESS_BODY_LEAK_RISK_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_SOURCE_CLAIM_INSUFFICIENT_REF: Final = "RSR_READINESS_SOURCE_CLAIM_INSUFFICIENT"
P7_R54_AHR_POST_DHR09_RSR_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_READY_TO_START_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_BODY_LEAK_RISK_BLOCKED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_SOURCE_CLAIM_INSUFFICIENT_REF,
)

P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_ENVIRONMENT_MISSING_REF: Final = "RSR_STOP_ENVIRONMENT_MISSING"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_MATERIAL_MISSING_REF: Final = "RSR_STOP_MATERIAL_MISSING"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_EXPLICIT_ALLOW_MISSING_REF: Final = "RSR_STOP_EXPLICIT_ALLOW_MISSING"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_BODY_LEAK_RISK_REF: Final = "RSR_STOP_BODY_LEAK_RISK"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_SOURCE_CLAIM_INSUFFICIENT_REF: Final = "RSR_STOP_SOURCE_CLAIM_INSUFFICIENT"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_REVIEWER_PERSON_NOT_CONFIRMED_REF: Final = "RSR_STOP_REVIEWER_PERSON_NOT_CONFIRMED"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_LOCAL_ONLY_BOUNDARY_NOT_CONFIRMED_REF: Final = "RSR_STOP_LOCAL_ONLY_BOUNDARY_NOT_CONFIRMED"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_PURGE_PLAN_MISSING_REF: Final = "RSR_STOP_PURGE_PLAN_MISSING"
P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_UPSTREAM_REPAIR_REQUIRED_REF: Final = "RSR_STOP_UPSTREAM_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_READINESS_STOP_REASON_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_ENVIRONMENT_MISSING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_MATERIAL_MISSING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_EXPLICIT_ALLOW_MISSING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_BODY_LEAK_RISK_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_SOURCE_CLAIM_INSUFFICIENT_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_REVIEWER_PERSON_NOT_CONFIRMED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_LOCAL_ONLY_BOUNDARY_NOT_CONFIRMED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_PURGE_PLAN_MISSING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP04_STOP_UPSTREAM_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_READINESS_BLOCKERS_BEFORE_SESSION_ENVELOPE_REF: Final = (
    "repair_readiness_blockers_before_local_only_review_session_envelope"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODY_LEAK_RISK_BEFORE_SESSION_ENVELOPE_REF: Final = (
    "blocked_body_leak_risk_before_local_only_review_session_envelope"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SOURCE_CLAIM_PREFLIGHT_BEFORE_SESSION_ENVELOPE_REF: Final = (
    "repair_source_claim_preflight_before_local_only_review_session_envelope"
)

P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF: Final = "selection_only_review_operator"
P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_ACCEPTED_BODYFREE_REF: Final = "RSR_REVIEW_SESSION_ENVELOPE_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_WAITING_FOR_READINESS_REF: Final = "RSR_REVIEW_SESSION_WAITING_FOR_READINESS"
P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_REVIEWER_PERSON_NOT_CONFIRMED_REF: Final = "RSR_REVIEW_SESSION_REVIEWER_PERSON_NOT_CONFIRMED"
P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = "RSR_REVIEW_SESSION_INVALID_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_BODY_LEAK_BLOCKED_REF: Final = "RSR_REVIEW_SESSION_BODY_LEAK_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_WAITING_FOR_READINESS_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_REVIEWER_PERSON_NOT_CONFIRMED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_BODY_LEAK_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_READINESS_BEFORE_REVIEW_SESSION_ENVELOPE_REF: Final = (
    "wait_for_readiness_blocker_classifier_ready_before_review_session_envelope"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEWER_PERSON_BOUNDARY_REF: Final = (
    "repair_reviewer_person_boundary_before_body_full_packet_request"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEWER_BODY_LEAK_BEFORE_PACKET_REQUEST_REF: Final = (
    "blocked_reviewer_person_boundary_body_leak_before_body_full_packet_request"
)

P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_ACCEPTED_BODYFREE_REF: Final = "RSR_PACKET_REQUEST_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_WAITING_FOR_SESSION_ENVELOPE_REF: Final = "RSR_PACKET_REQUEST_WAITING_FOR_SESSION_ENVELOPE"
P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_CASE_MANIFEST_REPAIR_REQUIRED_REF: Final = "RSR_PACKET_REQUEST_CASE_MANIFEST_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_BODY_LEAK_BLOCKED_REF: Final = "RSR_PACKET_REQUEST_BODY_LEAK_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_WAITING_FOR_SESSION_ENVELOPE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_CASE_MANIFEST_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_BODY_LEAK_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_REVIEW_SESSION_ENVELOPE_BEFORE_PACKET_REQUEST_REF: Final = (
    "wait_for_review_session_envelope_before_body_full_packet_request"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_24_CASE_BODYFREE_CASE_REF_MANIFEST_BEFORE_PACKET_REQUEST_REF: Final = (
    "repair_24_case_bodyfree_case_ref_manifest_before_packet_request"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODY_FULL_PACKET_REQUEST_BODY_LEAK_BEFORE_RECEIPT_REF: Final = (
    "blocked_body_full_packet_request_body_leak_before_packet_generation_receipt"
)

P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_ACCEPTED_BODYFREE_REF: Final = "RSR_PACKET_GENERATION_RECEIPT_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF: Final = "RSR_PACKET_GENERATION_RECEIPT_MISSING_WAITING"
P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = "RSR_PACKET_GENERATION_RECEIPT_INVALID_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_EXPORT_OR_PERSISTENCE_BLOCKED_REF: Final = "RSR_PACKET_EXPORT_OR_PERSISTENCE_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_EXPORT_OR_PERSISTENCE_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_REQUEST_BOUNDARY_BEFORE_RECEIPT_REF: Final = (
    "wait_for_body_full_packet_request_boundary_before_packet_generation_receipt_intake"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_GENERATION_RECEIPT_REF: Final = (
    "wait_for_body_full_packet_generation_receipt_before_selection_form_contract"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_BODY_FULL_PACKET_GENERATION_RECEIPT_REF: Final = (
    "repair_body_full_packet_generation_receipt_before_selection_form_contract"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_PACKET_EXPORT_OR_REPO_PERSISTENCE_REF: Final = (
    "blocked_packet_export_or_repo_persistence_no_actual_review_continue"
)

P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_ACCEPTED_BODYFREE_REF: Final = "RSR_SELECTION_ONLY_FORM_CONTRACT_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_WAITING_FOR_PACKET_GENERATION_RECEIPT_REF: Final = "RSR_SELECTION_ONLY_FORM_WAITING_FOR_PACKET_GENERATION_RECEIPT"
P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = "RSR_SELECTION_ONLY_FORM_CONTRACT_INVALID_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF: Final = "RSR_SELECTION_ONLY_FORM_BODY_LEAK_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_WAITING_FOR_PACKET_GENERATION_RECEIPT_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS: Final[dict[str, float]] = {
    "history_connection_naturalness": 0.90,
    "creepy_absence": 0.95,
    "overclaim_absence": 0.95,
    "self_blame_non_amplification": 0.95,
    "wants_more_input_or_accumulation": 0.85,
    "non_shallow_repeat": 0.90,
}
P7_R54_AHR_POST_DHR09_RSR_OP08_SCORE_OPTION_REFS: Final[tuple[float, ...]] = (0.0, 0.25, 0.5, 0.75, 1.0)
P7_R54_AHR_POST_DHR09_RSR_OP08_QUESTION_NEED_CLASS_REFS: Final[tuple[str, ...]] = (
    "no_question_needed_emlis_can_observe",
    "question_may_reduce_overread_risk",
    "question_would_make_immediate_observation_heavy",
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "insufficient_material_execution_blocker",
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_PACKET_GENERATION_RECEIPT_BEFORE_SELECTION_FORM_CONTRACT_REF: Final = (
    "wait_for_packet_generation_receipt_before_selection_only_form_contract"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SELECTION_ONLY_REVIEWER_FORM_CONTRACT_REF: Final = (
    "repair_selection_only_reviewer_form_rating_axis_contract_before_lifecycle_capture"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_SELECTION_ONLY_FORM_BODY_LEAK_BEFORE_LIFECYCLE_REF: Final = (
    "blocked_selection_only_form_body_leak_before_lifecycle_capture"
)

P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF: Final = "RSR_REVIEW_OPERATION_NOT_STARTED"
P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_READY_TO_START_REF: Final = "RSR_REVIEW_OPERATION_READY_TO_START"
P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_IN_PROGRESS_LOCAL_ONLY_REF: Final = "RSR_REVIEW_OPERATION_IN_PROGRESS_LOCAL_ONLY"
P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_PAUSED_LOCAL_ONLY_REF: Final = "RSR_REVIEW_OPERATION_PAUSED_LOCAL_ONLY"
P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF: Final = "RSR_REVIEW_OPERATION_COMPLETED_RECEIPT_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_ABORTED_REPAIR_REQUIRED_REF: Final = "RSR_REVIEW_OPERATION_ABORTED_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF,
    P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_READY_TO_START_REF,
    P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_IN_PROGRESS_LOCAL_ONLY_REF,
    P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_PAUSED_LOCAL_ONLY_REF,
    P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_ABORTED_REPAIR_REQUIRED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_WAITING_FOR_SELECTION_FORM_CONTRACT_REF: Final = "RSR_REVIEW_LIFECYCLE_WAITING_FOR_SELECTION_FORM_CONTRACT"
P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = "RSR_REVIEW_LIFECYCLE_INVALID_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_BODY_LEAK_BLOCKED_REF: Final = "RSR_REVIEW_LIFECYCLE_BODY_LEAK_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP09_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_REFS,
    P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_WAITING_FOR_SELECTION_FORM_CONTRACT_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_BODY_LEAK_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_SELECTION_FORM_CONTRACT_BEFORE_LIFECYCLE_CAPTURE_REF: Final = (
    "wait_for_selection_only_form_contract_before_review_lifecycle_capture"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_START_OR_CONTINUE_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_LOCAL_ONLY_REF: Final = (
    "start_or_continue_actual_local_only_review_operation_local_only_without_helper_execution"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_ACTUAL_OPERATION_RECEIPT_AFTER_COMPLETED_LIFECYCLE_REF: Final = (
    P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_ABORTED_ACTUAL_LOCAL_ONLY_REVIEW_LIFECYCLE_REF: Final = (
    "repair_or_retry_aborted_actual_local_only_review_lifecycle_before_receipt"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEW_LIFECYCLE_STATE_CAPTURE_REF: Final = (
    "repair_review_lifecycle_state_capture_before_actual_operation_receipt"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEW_LIFECYCLE_BODY_LEAK_BEFORE_RECEIPT_REF: Final = (
    "blocked_review_lifecycle_body_leak_before_actual_operation_receipt"
)

P7_R54_AHR_POST_DHR09_RSR_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_contract_valid", "op05_status_ref", "op05_ready_for_body_full_packet_transient_request_boundary", "op05_next_required_step",
    "review_session_envelope_ref", "reviewer_person_ref", "reviewer_is_person_confirmed", "expected_case_count",
    "case_ref_values", "case_ref_count", "case_ref_unique_count", "case_ref_duplicate_refs", "case_ref_duplicate_ref_count",
    "case_ref_invalid_refs", "case_ref_invalid_ref_count", "case_ref_manifest_bodyfree", "case_ref_manifest_exactly_24_unique",
    "packet_request_ref", "packet_request_ref_bodyfree", "packet_request_created_here", "packet_generated_here", "body_full_packet_content_included",
    "transient_body_full_packet_required", "local_only_transient_boundary_confirmed", "external_export_allowed", "persisted_to_repo_allowed",
    "packet_request_local_path_included", "packet_request_body_hash_included", "packet_request_terminal_output_body_included",
    "packet_request_forbidden_payload_key_path_refs", "packet_request_forbidden_payload_key_path_count",
    "packet_request_body_like_value_path_refs", "packet_request_body_like_value_path_count",
    "packet_request_promotion_claim_refs", "packet_request_promotion_claim_ref_count",
    "packet_request_reason_refs", "packet_request_reason_ref_count", "packet_request_blocker_refs", "packet_request_blocker_ref_count",
    "rsr_op06_status_ref", "rsr_op06_allowed_status_refs", "rsr_op06_allowed_status_ref_count", "rsr_op06_ready",
    "rsr_op06_packet_request_accepted", "rsr_op06_waiting_for_session_envelope", "rsr_op06_case_manifest_repair_required", "rsr_op06_body_leak_blocked",
    "rsr_op06_ready_for_body_full_packet_generation_receipt_intake",
    "rsr_op06_does_not_generate_body_full_packet", "rsr_op06_does_not_run_actual_local_human_review", "rsr_op06_does_not_create_receipts_rows_or_disposal",
    "rsr_op06_does_not_execute_dmd_or_r52", "rsr_op06_does_not_start_p5_p6_p8_p7_or_release", "rsr_op06_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_DHR09_RSR_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_contract_valid", "op07_status_ref", "op07_ready_for_selection_only_reviewer_form_rating_axis_contract_freeze", "op07_next_required_step",
    "op07_packet_generation_receipt_accepted", "op07_packet_generation_receipt_accepted_but_actual_review_not_executed",
    "selection_form_contract_ref", "selection_form_contract_ref_bodyfree", "selection_form_contract_material_present", "selection_form_contract_material_body_free",
    "rating_axis_target_refs", "rating_axis_target_ref_count", "rating_axis_target_threshold_refs", "rating_axis_target_threshold_ref_count", "rating_axis_targets_match_elr_contract",
    "score_option_refs", "score_option_ref_count", "score_options_allowed_scalar_only", "question_need_class_refs", "question_need_class_ref_count",
    "selection_only_form_required", "selection_only_form_used_for_contract", "selection_only_row_conversion_contract_ready",
    "question_need_observation_material_only", "p8_design_material_candidate_only", "question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here",
    "reviewer_free_text_allowed", "reviewer_body_note_allowed", "reviewer_name_material_included", "reviewer_email_material_included", "reviewer_raw_note_material_included", "reviewer_local_path_material_included",
    "body_full_packet_body_allowed_in_form", "raw_input_allowed_in_form", "returned_surface_body_allowed_in_form", "question_text_allowed_in_form", "draft_question_text_allowed_in_form",
    "selection_form_forbidden_payload_key_path_refs", "selection_form_forbidden_payload_key_path_count", "selection_form_body_like_value_path_refs", "selection_form_body_like_value_path_count",
    "selection_form_promotion_claim_refs", "selection_form_promotion_claim_ref_count", "selection_form_reason_refs", "selection_form_reason_ref_count", "selection_form_blocker_refs", "selection_form_blocker_ref_count",
    "rsr_op08_status_ref", "rsr_op08_allowed_status_refs", "rsr_op08_allowed_status_ref_count", "rsr_op08_ready", "rsr_op08_selection_only_form_contract_accepted", "rsr_op08_waiting_for_packet_generation_receipt", "rsr_op08_invalid_repair_required", "rsr_op08_body_leak_blocked",
    "rsr_op08_ready_for_actual_local_only_review_lifecycle_state_capture", "selection_only_form_contract_accepted_but_no_review_rows_created", "rsr_op08_does_not_run_actual_local_human_review", "rsr_op08_does_not_create_actual_operation_receipt_rows_or_disposal",
    "rsr_op08_does_not_materialize_question_text_or_p8_spec", "rsr_op08_does_not_execute_dmd_or_r52", "rsr_op08_does_not_start_p5_p6_p8_p7_or_release", "rsr_op08_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DHR09_RSR_OP09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op08_contract_valid", "op08_status_ref", "op08_ready_for_actual_local_only_review_lifecycle_state_capture", "op08_next_required_step", "op08_selection_only_form_contract_accepted",
    "lifecycle_state_material_present", "lifecycle_state_material_body_free", "lifecycle_status_requested_ref", "lifecycle_status_ref", "lifecycle_status_allowed_refs", "lifecycle_status_allowed_ref_count",
    "lifecycle_state_forbidden_payload_key_path_refs", "lifecycle_state_forbidden_payload_key_path_count", "lifecycle_state_body_like_value_path_refs", "lifecycle_state_body_like_value_path_count", "lifecycle_state_promotion_claim_refs", "lifecycle_state_promotion_claim_ref_count",
    "lifecycle_state_reason_refs", "lifecycle_state_reason_ref_count", "lifecycle_state_blocker_refs", "lifecycle_state_blocker_ref_count",
    "rsr_op09_status_ref", "rsr_op09_allowed_status_refs", "rsr_op09_allowed_status_ref_count", "rsr_op09_ready", "rsr_op09_waiting_for_selection_form_contract", "rsr_op09_invalid_repair_required", "rsr_op09_body_leak_blocked",
    "rsr_op09_review_operation_not_started", "rsr_op09_review_operation_ready_to_start", "rsr_op09_review_operation_in_progress_local_only", "rsr_op09_review_operation_paused_local_only", "rsr_op09_review_operation_completed_receipt_required", "rsr_op09_review_operation_aborted_repair_required",
    "review_lifecycle_state_captured_bodyfree", "helper_executes_actual_review", "actual_local_human_review_executed_here_by_helper", "actual_review_lifecycle_completed_but_receipt_not_accepted", "actual_operation_receipt_required", "actual_operation_receipt_accepted_by_op09", "rsr_op09_ready_for_actual_operation_receipt_intake",
    "rsr_op09_does_not_generate_body_full_packet", "rsr_op09_does_not_run_actual_local_human_review", "rsr_op09_does_not_create_actual_operation_receipt_rows_or_disposal", "rsr_op09_does_not_execute_dmd_or_r52", "rsr_op09_does_not_start_p5_p6_p8_p7_or_release", "rsr_op09_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF: Final = "actual_local_only_human_review_by_person"
P7_R54_AHR_POST_DHR09_RSR_REVIEW_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = (
    elr.P7_R54_AHR_POST_ALR12_ELR_REVIEW_VERDICT_OPTION_REFS
)
P7_R54_AHR_POST_DHR09_RSR_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = (
    elr.P7_R54_AHR_POST_ALR12_ELR_ONE_QUESTION_FIT_OPTION_REFS
)
P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_ACCEPTED_BODYFREE_REF: Final = "RSR_ACTUAL_OPERATION_RECEIPT_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_MISSING_WAITING_REF: Final = "RSR_ACTUAL_OPERATION_RECEIPT_MISSING_WAITING"
P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = "RSR_ACTUAL_OPERATION_RECEIPT_INVALID_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF: Final = "RSR_ACTUAL_OPERATION_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP10_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_MISSING_WAITING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_COMPLETED_LIFECYCLE_BEFORE_OPERATION_RECEIPT_REF: Final = (
    "wait_for_completed_review_lifecycle_before_actual_operation_receipt_intake"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_ACTUAL_OPERATION_RECEIPT_BODYFREE_REF: Final = (
    "provide_actual_operation_receipt_bodyfree_after_completed_lifecycle"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_BEFORE_ROWS_REF: Final = (
    "repair_actual_operation_receipt_before_sanitized_review_result_rows_rating_rows_intake"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF: Final = (
    "blocked_actual_operation_receipt_body_leak_or_source_claim_before_rows_intake"
)

P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_ACCEPTED_BODYFREE_REF: Final = "RSR_SANITIZED_REVIEW_RESULT_ROWS_RATING_ROWS_ACCEPTED_BODYFREE"
P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_MISSING_WAITING_REF: Final = "RSR_SANITIZED_REVIEW_RESULT_ROWS_RATING_ROWS_MISSING_WAITING"
P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = "RSR_SANITIZED_REVIEW_RESULT_ROWS_RATING_ROWS_INVALID_REPAIR_REQUIRED"
P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF: Final = "RSR_SANITIZED_REVIEW_RESULT_ROWS_RATING_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED"
P7_R54_AHR_POST_DHR09_RSR_OP11_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_MISSING_WAITING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_SANITIZED_REVIEW_RESULT_ROWS_AND_RATING_ROWS_BODYFREE_REF: Final = (
    "provide_sanitized_review_result_rows_and_rating_rows_bodyfree_after_operation_receipt"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SANITIZED_REVIEW_RESULT_ROWS_AND_RATING_ROWS_REF: Final = (
    "repair_sanitized_review_result_rows_rating_rows_before_question_need_observation_rows_intake"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEW_ROWS_RATING_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF: Final = (
    "blocked_review_rows_rating_rows_body_leak_or_source_claim_before_question_need_observation_rows_intake"
)

P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "review_session_id", "operation_receipt_ref", "review_result_row_ref", "case_ref", "reviewer_person_ref",
    "source_kind_ref", "verdict_ref", "axis_score_refs", "axis_score_count", "axis_pass_flags", "sanitized_reason_id_refs",
    "readfeel_blocker_id_refs", "execution_blocker_id_refs", "question_need_primary_class_ref", "ambiguity_kind_refs",
    "one_question_fit_ref", "repair_required_refs", "selection_only", "row_created_by_helper", "row_created_for_unit_test",
    "row_is_synthetic_contract_fixture", "historical_row_reused", "body_free",
)
P7_R54_AHR_POST_DHR09_RSR_SANITIZED_ROW_PROVENANCE_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "row_created_by_helper", "row_created_for_unit_test", "row_is_synthetic_contract_fixture", "historical_row_reused",
)
P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "rating_row_ref", "source_sanitized_review_result_row_ref", "review_session_id", "operation_receipt_ref",
    "case_ref", "verdict_ref", "axis_score_refs", "axis_pass_flags", "below_target_axis_refs", "readfeel_blocker_id_refs",
    "execution_blocker_id_refs", "repair_required_refs", "actual_rating_row_from_real_operation", "rating_decision_material_only", "body_free",
)
P7_R54_AHR_POST_DHR09_RSR_OPERATION_RECEIPT_BODYFREE_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "external_export_performed", "raw_input_included", "comment_text_body_included", "returned_surface_body_included",
    "reviewer_free_text_included", "reviewer_note_body_included", "question_text_included", "draft_question_text_included",
    "answer_text_included", "local_path_included", "body_hash_included", "terminal_output_body_included",
)

P7_R54_AHR_POST_DHR09_RSR_OP10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op09_contract_valid", "op09_status_ref", "op09_ready_for_actual_operation_receipt_intake", "op09_next_required_step",
    "op09_review_lifecycle_completed_receipt_required", "op09_actual_operation_receipt_required",
    "actual_operation_receipt_present", "actual_operation_receipt_schema_version", "operation_receipt_ref", "operation_receipt_ref_present",
    "operation_receipt_review_session_id", "operation_receipt_review_session_id_matches", "operation_receipt_packet_request_ref", "operation_receipt_packet_request_ref_present",
    "source_kind_ref", "source_kind_is_actual_local_only_human_review_by_person", "created_from_real_operation", "actual_human_review_executed_by_person",
    "reviewer_person_ref", "reviewer_person_ref_present", "reviewed_case_count", "selection_row_count", "local_only_operation_confirmed", "selection_only_form_used",
    "actual_operation_receipt_external_export_performed", "actual_operation_receipt_body_free", "actual_operation_receipt_raw_input_included", "actual_operation_receipt_comment_text_body_included",
    "actual_operation_receipt_returned_surface_body_included", "actual_operation_receipt_reviewer_free_text_included", "actual_operation_receipt_reviewer_note_body_included",
    "actual_operation_receipt_question_text_included", "actual_operation_receipt_draft_question_text_included", "actual_operation_receipt_answer_text_included",
    "actual_operation_receipt_local_path_included", "actual_operation_receipt_body_hash_included", "actual_operation_receipt_terminal_output_body_included",
    "actual_operation_receipt_forbidden_payload_key_path_refs", "actual_operation_receipt_forbidden_payload_key_path_count", "actual_operation_receipt_body_like_value_path_refs", "actual_operation_receipt_body_like_value_path_count",
    "actual_operation_receipt_promotion_claim_refs", "actual_operation_receipt_promotion_claim_ref_count", "actual_operation_receipt_body_free_marker_violation_refs", "actual_operation_receipt_body_free_marker_violation_ref_count",
    "actual_operation_receipt_source_claim_blocker_refs", "actual_operation_receipt_source_claim_blocker_ref_count",
    "rsr_op10_status_ref", "rsr_op10_allowed_status_refs", "rsr_op10_allowed_status_ref_count", "rsr_op10_ready", "rsr_op10_actual_operation_receipt_accepted",
    "rsr_op10_actual_operation_receipt_missing_waiting", "rsr_op10_actual_operation_receipt_invalid_repair_required", "rsr_op10_actual_operation_receipt_body_leak_or_source_claim_blocked",
    "actual_operation_receipt_accepted_by_rsr_op10", "ready_for_sanitized_review_result_rows_rating_rows_intake", "actual_operation_receipt_intake_bodyfree_accepted_without_rows", "sanitized_review_result_rows_and_rating_rows_required_next",
    "op10_reason_refs", "op10_reason_ref_count", "op10_blocker_refs", "op10_blocker_ref_count",
    "helper_executes_actual_review", "actual_operation_receipt_created_here_by_helper", "actual_rows_created_here_by_helper", "actual_review_evidence_complete_here",
    "rsr_op10_does_not_run_actual_local_human_review", "rsr_op10_does_not_create_actual_operation_receipt", "rsr_op10_does_not_create_rows_question_rows_or_disposal",
    "rsr_op10_does_not_execute_dmd_or_r52", "rsr_op10_does_not_start_p5_p6_p8_p7_or_release", "rsr_op10_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DHR09_RSR_OP11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op10_contract_valid", "op10_status_ref", "op10_actual_operation_receipt_accepted", "op10_ready_for_sanitized_review_result_rows_rating_rows_intake", "op10_next_required_step",
    "operation_receipt_ref", "operation_receipt_packet_request_ref", "reviewer_person_ref",
    "sanitized_review_result_rows_present", "rating_rows_present", "sanitized_rows_status_ref", "rating_rows_status_ref",
    "rsr_op11_status_ref", "rsr_op11_allowed_status_refs", "rsr_op11_allowed_status_ref_count", "rsr_op11_ready",
    "rsr_op11_sanitized_review_result_rows_accepted", "rsr_op11_rating_rows_accepted", "rsr_op11_rows_missing_waiting", "rsr_op11_rows_invalid_repair_required", "rsr_op11_rows_body_leak_or_source_claim_blocked",
    "sanitized_review_result_row_schema_version", "rating_row_schema_version", "required_sanitized_review_result_row_field_refs", "required_sanitized_review_result_row_field_ref_count", "required_rating_row_field_refs", "required_rating_row_field_ref_count",
    "sanitized_review_result_row_count", "rating_row_count", "expected_review_row_count", "sanitized_review_result_row_count_is_24", "rating_row_count_is_24",
    "sanitized_review_result_row_refs", "sanitized_review_result_row_ref_count", "rating_row_refs", "rating_row_ref_count", "case_ref_values", "case_ref_count", "case_ref_unique_count", "case_refs_match_between_sanitized_and_rating_rows",
    "sanitized_review_result_rows", "rating_rows", "sanitized_rows_bodyfree_only", "sanitized_rows_selection_only", "sanitized_rows_have_actual_person_selection_only_provenance", "sanitized_rows_have_required_axis_scores",
    "sanitized_rows_have_allowed_verdict_refs", "sanitized_rows_have_allowed_question_observation_refs", "sanitized_rows_have_no_body_or_question_or_path_or_hash",
    "rating_rows_bodyfree_only", "rating_rows_from_sanitized_rows", "rating_rows_have_required_axis_scores", "rating_rows_have_no_body_or_question_or_path_or_hash",
    "rows_operation_receipt_ref_matches", "rows_reviewer_person_ref_matches", "rows_source_kind_is_actual_local_only_human_review_by_person",
    "review_rows_forbidden_payload_key_path_refs", "review_rows_forbidden_payload_key_path_count", "review_rows_body_like_value_path_refs", "review_rows_body_like_value_path_count", "review_rows_promotion_claim_refs", "review_rows_promotion_claim_ref_count",
    "rating_rows_forbidden_payload_key_path_refs", "rating_rows_forbidden_payload_key_path_count", "rating_rows_body_like_value_path_refs", "rating_rows_body_like_value_path_count", "rating_rows_promotion_claim_refs", "rating_rows_promotion_claim_ref_count",
    "question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here",
    "sanitized_review_result_rows_accepted_by_rsr_op11", "rating_rows_accepted_by_rsr_op11", "actual_sanitized_review_result_rows_accepted_without_creation", "actual_rating_rows_accepted_without_creation", "actual_review_rows_and_rating_rows_intaken_bodyfree",
    "question_need_observation_rows_required_next", "actual_review_evidence_complete_here", "op11_reason_refs", "op11_reason_ref_count", "op11_blocker_refs", "op11_blocker_ref_count",
    "rsr_op11_does_not_create_sanitized_rows_or_rating_rows", "rsr_op11_does_not_create_question_rows_or_disposal", "rsr_op11_does_not_materialize_question_text_or_p8_spec", "rsr_op11_does_not_execute_dmd_or_r52",
    "rsr_op11_does_not_start_p5_p6_p8_p7_or_release", "rsr_op11_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DHR09_RSR_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_contract_valid", "op06_status_ref", "op06_ready_for_body_full_packet_generation_receipt_intake", "op06_next_required_step",
    "op06_packet_request_ref", "op06_case_ref_count", "packet_generation_receipt_present", "packet_generation_receipt_contract_valid",
    "packet_generation_receipt_schema_version", "packet_generation_receipt_ref", "packet_generation_receipt_packet_request_ref", "packet_generation_receipt_review_session_id",
    "packet_generation_receipt_generated_case_count", "packet_generation_receipt_generated_local_only", "packet_generation_receipt_persisted_to_repo",
    "packet_generation_receipt_external_export_performed", "packet_generation_receipt_raw_input_included", "packet_generation_receipt_comment_text_body_included",
    "packet_generation_receipt_returned_surface_body_included", "packet_generation_receipt_local_path_included", "packet_generation_receipt_body_hash_included",
    "packet_generation_receipt_terminal_output_body_included", "packet_generation_receipt_body_free",
    "packet_generation_receipt_forbidden_payload_key_path_refs", "packet_generation_receipt_forbidden_payload_key_path_count",
    "packet_generation_receipt_body_like_value_path_refs", "packet_generation_receipt_body_like_value_path_count",
    "packet_generation_receipt_promotion_claim_refs", "packet_generation_receipt_promotion_claim_ref_count",
    "packet_generation_receipt_export_or_persistence_blocker_refs", "packet_generation_receipt_export_or_persistence_blocker_ref_count",
    "packet_generation_receipt_reason_refs", "packet_generation_receipt_reason_ref_count", "packet_generation_receipt_blocker_refs", "packet_generation_receipt_blocker_ref_count",
    "rsr_op07_status_ref", "rsr_op07_allowed_status_refs", "rsr_op07_allowed_status_ref_count", "rsr_op07_ready",
    "rsr_op07_packet_generation_receipt_accepted", "rsr_op07_missing_waiting", "rsr_op07_invalid_repair_required", "rsr_op07_export_or_persistence_blocked",
    "rsr_op07_ready_for_selection_only_reviewer_form_rating_axis_contract_freeze", "packet_generation_receipt_accepted_by_rsr_op07",
    "packet_generation_receipt_accepted_but_actual_review_not_executed", "rsr_op07_does_not_generate_body_full_packet_here",
    "rsr_op07_does_not_run_actual_local_human_review", "rsr_op07_does_not_create_actual_operation_receipt_rows_or_disposal",
    "rsr_op07_does_not_execute_dmd_or_r52", "rsr_op07_does_not_start_p5_p6_p8_p7_or_release", "rsr_op07_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DHR09_RSR_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_contract_valid", "op01_status_ref", "op01_ready_for_upstream_relationship_verification", "op01_next_required_step",
    "dhr_op09_contract_valid", "dhr_op09_result_memo_bodyfree_closed", "dhr_op09_selected_branch_ref", "dhr_op09_next_required_step", "dhr_op09_dmd_handoff_plan_materialized",
    "upstream_chain_refs", "upstream_chain_ref_count", "dmd_op08_material_present", "dmd_op08_contract_valid", "dmd_op08_branch_ref", "dmd_op08_next_required_step",
    "alr_op12_material_present", "alr_op12_contract_valid", "alr_op12_selected_action_ref", "alr_op12_next_required_step",
    "elr_op19_material_present", "elr_op19_contract_valid", "elr_op19_result_memo_bodyfree_closed", "elr_op19_next_required_step",
    "op02_optional_upstream_material_count", "op02_valid_upstream_material_count", "op02_missing_optional_upstream_relation_refs", "op02_missing_optional_upstream_relation_ref_count",
    "op02_relation_conflict_refs", "op02_relation_conflict_ref_count", "op02_forbidden_payload_key_path_refs", "op02_forbidden_payload_key_path_count",
    "op02_body_like_value_path_refs", "op02_body_like_value_path_count", "op02_promotion_claim_refs", "op02_promotion_claim_ref_count",
    "rsr_op02_status_ref", "rsr_op02_allowed_status_refs", "rsr_op02_allowed_status_ref_count", "rsr_op02_ready", "rsr_op02_upstream_relationship_verified",
    "rsr_op02_partial_upstream_material_accepted_from_dhr09", "rsr_op02_waiting_or_incomplete", "rsr_op02_repair_required", "rsr_op02_ready_for_explicit_local_only_allow_gate",
    "rsr_op02_reason_refs", "rsr_op02_reason_ref_count", "rsr_op02_blocker_refs", "rsr_op02_blocker_ref_count", "rsr_op02_does_not_accept_explicit_local_only_allow",
    "rsr_op02_does_not_generate_body_full_packet", "rsr_op02_does_not_run_actual_local_human_review", "rsr_op02_does_not_create_receipts_rows_or_disposal",
    "rsr_op02_does_not_execute_dmd_or_r52", "rsr_op02_does_not_start_p5_p6_p8_p7_or_release", "rsr_op02_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DHR09_RSR_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_contract_valid", "op02_ready_for_explicit_local_only_allow_gate", "op02_next_required_step",
    "explicit_allow_receipt_present", "explicit_allow_receipt_contract_valid", "explicit_allow_receipt_schema_version", "explicit_allow_receipt_ref", "explicit_allow_receipt_review_session_id",
    "explicit_allow_allowed_operation_scope_ref", "explicit_allow_allowed_case_count", "explicit_allow_local_only_operation_allowed", "explicit_allow_body_full_transient_review_allowed",
    "explicit_allow_external_export_allowed", "explicit_allow_disposal_purge_required", "explicit_allow_raw_input_included", "explicit_allow_comment_text_body_included", "explicit_allow_returned_surface_body_included",
    "explicit_allow_reviewer_free_text_included", "explicit_allow_question_text_included", "explicit_allow_draft_question_text_included", "explicit_allow_local_path_included", "explicit_allow_body_hash_included", "explicit_allow_terminal_output_body_included", "explicit_allow_body_free",
    "explicit_allow_forbidden_payload_key_path_refs", "explicit_allow_forbidden_payload_key_path_count", "explicit_allow_body_like_value_path_refs", "explicit_allow_body_like_value_path_count",
    "explicit_allow_promotion_claim_refs", "explicit_allow_promotion_claim_ref_count", "rsr_op03_status_ref", "rsr_op03_allowed_status_refs", "rsr_op03_allowed_status_ref_count",
    "rsr_op03_ready", "rsr_op03_explicit_allow_accepted", "rsr_op03_explicit_allow_missing_waiting", "rsr_op03_explicit_allow_invalid_repair_required", "rsr_op03_explicit_allow_scope_mismatch_blocked",
    "rsr_op03_ready_for_readiness_blocker_classifier", "explicit_local_only_allow_receipt_accepted_by_rsr_op03", "explicit_local_only_allow_granted_by_helper", "allow_required_was_not_rewritten_to_allow_granted",
    "rsr_op03_reason_refs", "rsr_op03_reason_ref_count", "rsr_op03_blocker_refs", "rsr_op03_blocker_ref_count",
    "rsr_op03_does_not_generate_body_full_packet", "rsr_op03_does_not_run_actual_local_human_review", "rsr_op03_does_not_create_receipts_rows_or_disposal",
    "rsr_op03_does_not_execute_dmd_or_r52", "rsr_op03_does_not_start_p5_p6_p8_p7_or_release", "rsr_op03_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_DHR09_RSR_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_contract_valid", "op03_status_ref", "op03_ready_for_readiness_blocker_classifier", "op03_explicit_allow_accepted", "op03_next_required_step",
    "environment_ready", "environment_ready_ref", "material_manifest_ready", "material_manifest_ready_ref", "explicit_allow_accepted",
    "reviewer_person_boundary_ready", "local_only_boundary_ready", "purge_plan_ready", "source_claim_preflight_ready", "body_leak_preflight_passed",
    "body_leak_preflight_forbidden_payload_key_path_refs", "body_leak_preflight_forbidden_payload_key_path_count",
    "body_leak_preflight_body_like_value_path_refs", "body_leak_preflight_body_like_value_path_count",
    "body_leak_preflight_promotion_claim_refs", "body_leak_preflight_promotion_claim_ref_count",
    "readiness_stop_reason_refs", "readiness_stop_reason_ref_count", "readiness_reason_refs", "readiness_reason_ref_count",
    "readiness_blocker_refs", "readiness_blocker_ref_count", "rsr_op04_status_ref", "rsr_op04_allowed_status_refs", "rsr_op04_allowed_status_ref_count",
    "rsr_op04_ready", "rsr_op04_ready_to_start_local_only_review", "rsr_op04_wait_for_explicit_local_only_allow", "rsr_op04_environment_or_material_repair_required",
    "rsr_op04_body_leak_risk_blocked", "rsr_op04_source_claim_insufficient", "rsr_op04_ready_for_local_only_review_session_envelope",
    "rsr_op04_does_not_generate_body_full_packet", "rsr_op04_does_not_run_actual_local_human_review", "rsr_op04_does_not_create_receipts_rows_or_disposal",
    "rsr_op04_does_not_execute_dmd_or_r52", "rsr_op04_does_not_start_p5_p6_p8_p7_or_release", "rsr_op04_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_DHR09_RSR_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_contract_valid", "op04_status_ref", "op04_ready_for_local_only_review_session_envelope", "op04_next_required_step",
    "review_session_envelope_ref", "review_session_id_normalized", "review_session_id_bodyfree", "reviewer_person_ref_present", "reviewer_person_ref",
    "reviewer_person_ref_bodyfree", "reviewer_person_ref_shape_valid", "reviewer_is_person_confirmed", "reviewer_role_ref", "expected_reviewer_role_ref",
    "reviewer_role_is_selection_only_review_operator", "reviewer_is_helper_or_unit_test", "reviewer_free_text_allowed", "reviewer_body_note_allowed",
    "reviewer_name_material_included", "reviewer_email_material_included", "reviewer_raw_note_material_included", "reviewer_local_path_material_included",
    "reviewer_boundary_forbidden_payload_key_path_refs", "reviewer_boundary_forbidden_payload_key_path_count",
    "reviewer_boundary_body_like_value_path_refs", "reviewer_boundary_body_like_value_path_count",
    "reviewer_boundary_promotion_claim_refs", "reviewer_boundary_promotion_claim_ref_count",
    "reviewer_boundary_reason_refs", "reviewer_boundary_reason_ref_count", "reviewer_boundary_blocker_refs", "reviewer_boundary_blocker_ref_count",
    "selection_only_review_operator_boundary_confirmed", "actual_source_claim_allowed_by_op05", "rsr_op05_status_ref", "rsr_op05_allowed_status_refs", "rsr_op05_allowed_status_ref_count",
    "rsr_op05_ready", "rsr_op05_review_session_envelope_accepted", "rsr_op05_waiting_for_readiness", "rsr_op05_reviewer_person_not_confirmed",
    "rsr_op05_invalid_repair_required", "rsr_op05_body_leak_blocked", "rsr_op05_ready_for_body_full_packet_transient_request_boundary",
    "rsr_op05_does_not_generate_body_full_packet", "rsr_op05_does_not_run_actual_local_human_review", "rsr_op05_does_not_create_receipts_rows_or_disposal",
    "rsr_op05_does_not_execute_dmd_or_r52", "rsr_op05_does_not_start_p5_p6_p8_p7_or_release", "rsr_op05_does_not_change_api_db_rn_runtime_response_key",
    "manual_decision_required_without_auto_execution", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any) -> str:
    return _clean_ref(
        value,
        default=P7_R54_AHR_POST_DHR09_RSR_DEFAULT_REVIEW_SESSION_ID,
        max_length=220,
    )


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHR09_RSR_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHR09_RSR_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS}


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
            if key_text in P7_R54_AHR_POST_DHR09_RSR_FORBIDDEN_PAYLOAD_KEY_REFS:
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
        "file_path", "absolute_path", "relative_path", "hash", "terminal", "stdout", "stderr", "traceback",
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
        for field in P7_R54_AHR_POST_DHR09_RSR_PROMOTION_CLAIM_FIELD_REFS
        if material.get(field) is True
    ]


def _summary_bodyfree(material: Mapping[str, Any], *, field: str, default_status_ref: str) -> dict[str, Any]:
    summary = material.get(field)
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


def _dhr_op09_contract_valid(dhr_op09: Mapping[str, Any] | None) -> bool:
    if not isinstance(dhr_op09, Mapping):
        return False
    try:
        return dhr.assert_p7_r54_ahr_post_elr19_dhr_op09_bodyfree_result_memo_target_tests_regression_closure_contract(dhr_op09) is True
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
    if data.get("phase") != P7_R54_AHR_POST_DHR09_RSR_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_DHR09_RSR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_DHR09_RSR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("operation_step_ref") != operation_step_ref or data.get("policy_section") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git connection flags changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must stay body-free")
    _assert_public_contract_false(data, source=source)
    _assert_false_mapping(data, field="post_dhr09_no_touch_contract", source=source)
    _assert_false_mapping(data, field="body_free_markers", source=source)
    for key in P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")
    if any(key in P7_R54_AHR_POST_DHR09_RSR_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")


def _op01_status_reason_blocker_next(
    *,
    dhr_op09: Mapping[str, Any] | None,
    dhr_op09_contract_valid: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    op00_valid: bool,
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if not op00_valid:
        blockers.append("rsr_op00_contract_invalid")
    if not isinstance(dhr_op09, Mapping):
        blockers.append("dhr_op09_result_memo_missing")
    elif not dhr_op09_contract_valid:
        blockers.append("dhr_op09_result_memo_contract_invalid")
    if forbidden_paths:
        blockers.append("dhr_op09_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("dhr_op09_body_like_value_detected")
    if promotion_claims:
        blockers.append("dhr_op09_promotion_claim_detected")
    if blockers and "dhr_op09_result_memo_missing" not in blockers:
        return (
            P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF,
            _dedupe_clean_refs(reasons or ["dhr_op09_result_memo_boundary_repair_required"]),
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DHR_OP09_RESULT_MEMO_BOUNDARY_REF,
        )
    if not isinstance(dhr_op09, Mapping):
        return (
            P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF,
            ["dhr_op09_result_memo_missing_or_not_provided"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_DHR_OP09_CLOSED_RETRY_BRANCH_REF,
        )

    branch_ref = _clean_ref(dhr_op09.get("selected_branch_ref"), default="dhr_op09_branch_missing", max_length=260)
    next_step = _clean_ref(dhr_op09.get("next_required_step"), default="dhr_op09_next_required_step_missing", max_length=260)
    result_status = _clean_ref(dhr_op09.get("result_memo_status_ref"), default="dhr_op09_result_status_missing", max_length=260)
    dmd_plan_materialized = dhr_op09.get("dmd_handoff_plan_materialized") is True
    closed = result_status == dhr.P7_R54_AHR_POST_ELR19_DHR_OP09_STATUS_CLOSED_BODYFREE_REF

    if branch_ref == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF:
        if dmd_plan_materialized:
            blockers.append("dhr_op09_retry_branch_materialized_dmd_handoff_plan")
        if next_step != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF:
            blockers.append("dhr_op09_retry_branch_next_step_mismatch")
        if blockers:
            return (
                P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF,
                ["dhr_op09_retry_branch_boundary_repair_required"],
                _dedupe_clean_refs(blockers),
                P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DHR_OP09_RESULT_MEMO_BOUNDARY_REF,
            )
        if closed:
            return (
                P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_RETRY_OR_START_REQUIRED_REF,
                ["dhr_op09_closed_retry_or_start_required_before_downstream_handoff"],
                [],
                P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF,
            )
        return (
            P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF,
            ["dhr_op09_retry_branch_not_closed_bodyfree_yet"],
            [],
            P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_DHR_OP09_CLOSED_RETRY_BRANCH_REF,
        )

    if branch_ref == P7_R54_AHR_POST_DHR09_RSR_DHR_HANDOFF_BRANCH_REF:
        return (
            P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF,
            ["dhr_op09_selected_handoff_branch_instead_of_current_retry_start_default"],
            [],
            P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_UNEXPECTED_DHR_HANDOFF_BRANCH_REF,
        )

    if branch_ref in (
        dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_WAIT_FOR_ELR_COMPLETE_EVIDENCE_OR_MANUAL_HOLD_REF,
        dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_MANUAL_DECISION_HOLD_CONTINUES_UNRESOLVED_REF,
    ):
        return (
            P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF,
            ["dhr_op09_selected_wait_or_unresolved_manual_hold_branch"],
            [],
            P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_DHR_OP09_CLOSED_RETRY_BRANCH_REF,
        )

    return (
        P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF,
        ["dhr_op09_selected_branch_is_not_rsr_retry_start_intake_target"],
        ["dhr_op09_selected_branch_requires_repair_before_rsr"],
        P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DHR_OP09_RESULT_MEMO_BOUNDARY_REF,
    )


def build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build RSR-OP00 body-free scope / no-touch / no-promotion re-freeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_DHR09_RSR_SELECTED_STAGE_REF,
        "expected_default_branch_ref": P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF,
        "expected_default_next_required_step_ref": P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_DHR09_RSR_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_DHR09_RSR_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "rsr_op00_scope_confirmed": True,
        "rsr_op00_no_touch_boundary_confirmed": True,
        "rsr_op00_no_promotion_boundary_confirmed": True,
        "rsr_op00_does_not_intake_dhr_op09_result_memo": True,
        "rsr_op00_does_not_generate_body_full_packet": True,
        "rsr_op00_does_not_run_actual_local_human_review": True,
        "rsr_op00_does_not_create_receipts_rows_or_disposal": True,
        "rsr_op00_does_not_accept_explicit_local_only_allow": True,
        "rsr_op00_does_not_execute_dmd_or_r52": True,
        "rsr_op00_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RSR-OP00 scope / no-touch / no-promotion re-freeze contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DHR09_RSR_OP00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDHR09-RSR-OP00",
    )
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DHR09_RSR_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP00_STEP_REF,
        source="P7-R54-AHR-PostDHR09-RSR-OP00",
    )
    for key in (
        "rsr_op00_scope_confirmed",
        "rsr_op00_no_touch_boundary_confirmed",
        "rsr_op00_no_promotion_boundary_confirmed",
        "rsr_op00_does_not_intake_dhr_op09_result_memo",
        "rsr_op00_does_not_generate_body_full_packet",
        "rsr_op00_does_not_run_actual_local_human_review",
        "rsr_op00_does_not_create_receipts_rows_or_disposal",
        "rsr_op00_does_not_accept_explicit_local_only_allow",
        "rsr_op00_does_not_execute_dmd_or_r52",
        "rsr_op00_does_not_start_p5_p6_p8_p7_or_release",
        "rsr_op00_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP00 required true boundary changed: {key}")
    if data.get("expected_default_branch_ref") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 expected branch changed")
    if data.get("expected_default_next_required_step_ref") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 expected next step changed")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP00 {count_field} changed")
    if data.get("local_received_zip_ref_count") != len(data.get("local_received_zip_refs") or {}):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 local received zip count changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DHR09_RSR_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DHR09_RSR_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 not-yet-implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP00 next step changed")
    return True


def build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(
    *,
    scope_no_touch_no_promotion_refreeze: Mapping[str, Any] | None = None,
    dhr_op09_result_memo: Mapping[str, Any] | None = None,
    op09_result_memo: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP01 body-free DHR-OP09 selected branch / next-step intake material."""

    op09 = dhr_op09_result_memo if dhr_op09_result_memo is not None else op09_result_memo
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op09.get("review_session_id") if isinstance(op09, Mapping) else None))
    op00 = scope_no_touch_no_promotion_refreeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09(
            review_session_id=session_id
        )
    try:
        op00_valid = assert_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract(op00) is True
    except ValueError:
        op00_valid = False

    op09_map = op09 if isinstance(op09, Mapping) else {}
    op09_contract_valid = _dhr_op09_contract_valid(op09)
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(op09_map, path="dhr_op09_result_memo"),
        max_length=280,
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(op09_map, path="dhr_op09_result_memo"),
        max_length=280,
    )
    promotion_claims = _dedupe_clean_refs(
        [f"dhr_op09_result_memo.{ref}" for ref in (_promotion_claim_refs(op09_map) if isinstance(op09_map, Mapping) else [])],
        max_length=280,
    )
    status_ref, reasons, blockers, next_required_step = _op01_status_reason_blocker_next(
        dhr_op09=op09,
        dhr_op09_contract_valid=op09_contract_valid,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        op00_valid=op00_valid,
    )
    retry_required = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_RETRY_OR_START_REQUIRED_REF
    waiting = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF
    repair = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF
    unexpected_handoff = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF

    target_summary = _summary_bodyfree(op09_map, field="target_tests_summary_bodyfree", default_status_ref="target_tests_not_confirmed_by_rsr_op01")
    regression_summary = _summary_bodyfree(op09_map, field="selected_regression_summary_bodyfree", default_status_ref="selected_regression_not_confirmed_by_rsr_op01")
    compile_summary = _summary_bodyfree(op09_map, field="compileall_summary_bodyfree", default_status_ref="compileall_not_confirmed_by_rsr_op01")

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else "", default="op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else "", default="op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else "", default="op00_next_required_step_missing", max_length=260),
        "op00_scope_confirmed": bool(isinstance(op00, Mapping) and op00.get("rsr_op00_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("rsr_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("rsr_op00_no_promotion_boundary_confirmed") is True),
        "op00_contract_valid": op00_valid,
        "dhr_op09_result_memo_present": isinstance(op09, Mapping),
        "dhr_op09_contract_valid": op09_contract_valid,
        "dhr_op09_schema_version": _clean_ref(op09_map.get("schema_version"), default="dhr_op09_schema_missing", max_length=260),
        "dhr_op09_operation_step_ref": _clean_ref(op09_map.get("operation_step_ref"), default="dhr_op09_operation_step_missing", max_length=260),
        "dhr_op09_material_ref": _clean_ref(op09_map.get("material_id"), default="dhr_op09_material_missing", max_length=260),
        "dhr_op09_result_memo_status_ref": _clean_ref(op09_map.get("result_memo_status_ref"), default="dhr_op09_result_status_missing", max_length=260),
        "dhr_op09_result_memo_bodyfree_closed": bool(op09_map.get("result_memo_bodyfree_closed") is True),
        "dhr_op09_selected_branch_ref": _clean_ref(op09_map.get("selected_branch_ref"), default="dhr_op09_branch_missing", max_length=260),
        "dhr_op09_next_required_step": _clean_ref(op09_map.get("next_required_step"), default="dhr_op09_next_required_step_missing", max_length=260),
        "dhr_op09_dmd_handoff_plan_materialized": bool(op09_map.get("dmd_handoff_plan_materialized") is True),
        "dhr_op09_dmd_handoff_ready_manual_decision_required": bool(op09_map.get("dmd_handoff_ready_manual_decision_required") is True),
        "dhr_op09_actual_local_human_review_execution_verified_here": bool(op09_map.get("actual_local_human_review_execution_verified_here") is True),
        "dhr_op09_actual_rows_created_verified_here": bool(op09_map.get("actual_rows_created_verified_here") is True),
        "dhr_op09_actual_disposal_purge_execution_verified_here": bool(op09_map.get("actual_disposal_purge_execution_verified_here") is True),
        "dhr_op09_actual_body_full_packet_generation_verified_here": bool(op09_map.get("actual_body_full_packet_generation_verified_here") is True),
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
        "compileall_passed": compile_summary["status_ref"] in {"passed", "passed_bodyfree_count_only", "ok"} and compile_summary["failed_count"] == 0 and compile_summary["timed_out"] is False,
        "compileall_failed": compile_summary["failed_count"] > 0,
        "compileall_timed_out": compile_summary["timed_out"],
        "dhr_op09_forbidden_payload_key_path_refs": forbidden_paths,
        "dhr_op09_forbidden_payload_key_path_count": len(forbidden_paths),
        "dhr_op09_body_like_value_path_refs": body_like_paths,
        "dhr_op09_body_like_value_path_count": len(body_like_paths),
        "dhr_op09_promotion_claim_refs": promotion_claims,
        "dhr_op09_promotion_claim_ref_count": len(promotion_claims),
        "rsr_op01_status_ref": status_ref,
        "dhr_op09_intake_status_ref": status_ref,
        "rsr_op01_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP01_ALLOWED_STATUS_REFS),
        "rsr_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP01_ALLOWED_STATUS_REFS),
        "rsr_op01_ready": retry_required,
        "rsr_op01_retry_or_start_required": retry_required,
        "rsr_op01_waiting_or_incomplete": waiting,
        "rsr_op01_repair_required": repair,
        "rsr_op01_unexpected_handoff_branch_manual_hold": unexpected_handoff,
        "rsr_op01_reason_refs": reasons,
        "rsr_op01_reason_ref_count": len(reasons),
        "rsr_op01_blocker_refs": blockers,
        "rsr_op01_blocker_ref_count": len(blockers),
        "rsr_op01_ready_for_upstream_relationship_verification": retry_required,
        "actual_review_execution_claimed_by_rsr_op01": False,
        "explicit_local_only_allow_accepted_by_rsr_op01": False,
        "rsr_op01_does_not_generate_body_full_packet": True,
        "rsr_op01_does_not_run_actual_local_human_review": True,
        "rsr_op01_does_not_create_receipts_rows_or_disposal": True,
        "rsr_op01_does_not_execute_dmd_or_r52": True,
        "rsr_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert RSR-OP01 body-free DHR-OP09 result memo / branch / next-step intake contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_DHR09_RSR_OP01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostDHR09-RSR-OP01",
    )
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_DHR09_RSR_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF,
        source="P7-R54-AHR-PostDHR09-RSR-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_DHR09_RSR_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 OP00 next step changed")
    if data.get("op00_contract_valid") is not True:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 OP00 contract must be valid")
    if data.get("dhr_op09_intake_status_ref") != data.get("rsr_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 DHR-OP09 intake status alias changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "rsr_op01_does_not_generate_body_full_packet",
        "rsr_op01_does_not_run_actual_local_human_review",
        "rsr_op01_does_not_create_receipts_rows_or_disposal",
        "rsr_op01_does_not_execute_dmd_or_r52",
        "rsr_op01_does_not_start_p5_p6_p8_p7_or_release",
        "rsr_op01_does_not_change_api_db_rn_runtime_response_key",
        "manual_decision_required_without_auto_execution",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP01 required true boundary changed: {key}")
    for key in (
        "actual_review_execution_claimed_by_rsr_op01",
        "explicit_local_only_allow_accepted_by_rsr_op01",
        "dhr_op09_actual_local_human_review_execution_verified_here",
        "dhr_op09_actual_rows_created_verified_here",
        "dhr_op09_actual_disposal_purge_execution_verified_here",
        "dhr_op09_actual_body_full_packet_generation_verified_here",
        "explicit_local_only_allow_receipt_accepted_here",
        "body_full_packet_generated_here",
        "actual_local_human_review_executed_here",
        "actual_rows_created_here",
        "actual_operation_receipt_created_here",
        "actual_disposal_purge_executed_here",
        "actual_source_claim_for_dhr_reintake_materialized_here",
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
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP01 downstream/execution flag promoted: {key}")
    for field, count_field in (
        ("dhr_op09_forbidden_payload_key_path_refs", "dhr_op09_forbidden_payload_key_path_count"),
        ("dhr_op09_body_like_value_path_refs", "dhr_op09_body_like_value_path_count"),
        ("dhr_op09_promotion_claim_refs", "dhr_op09_promotion_claim_ref_count"),
        ("rsr_op01_allowed_status_refs", "rsr_op01_allowed_status_ref_count"),
        ("rsr_op01_reason_refs", "rsr_op01_reason_ref_count"),
        ("rsr_op01_blocker_refs", "rsr_op01_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP01 {count_field} changed")
    if tuple(data.get("rsr_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 allowed status refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DHR09_RSR_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_DHR09_RSR_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 not-yet-implemented steps changed")

    status_ref = data.get("rsr_op01_status_ref")
    status_flags = [
        data.get("rsr_op01_retry_or_start_required") is True,
        data.get("rsr_op01_waiting_or_incomplete") is True,
        data.get("rsr_op01_repair_required") is True,
        data.get("rsr_op01_unexpected_handoff_branch_manual_hold") is True,
    ]
    if sum(status_flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 exactly one status flag must be true")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_RETRY_OR_START_REQUIRED_REF:
        if data.get("dhr_op09_contract_valid") is not True or data.get("dhr_op09_result_memo_bodyfree_closed") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 retry/start requires valid closed DHR-OP09")
        if data.get("dhr_op09_selected_branch_ref") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 retry/start branch changed")
        if data.get("dhr_op09_next_required_step") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 retry/start DHR next step changed")
        if data.get("dhr_op09_dmd_handoff_plan_materialized") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 retry/start cannot carry DMD plan")
        if data.get("rsr_op01_ready") is not True or data.get("rsr_op01_ready_for_upstream_relationship_verification") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 retry/start readiness changed")
        if data.get("rsr_op01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 retry/start cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 retry/start next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_WAITING_OR_INCOMPLETE_REF:
        if data.get("rsr_op01_ready") is not False or data.get("rsr_op01_ready_for_upstream_relationship_verification") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 waiting cannot proceed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_DHR_OP09_CLOSED_RETRY_BRANCH_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_REPAIR_REQUIRED_REF:
        if data.get("rsr_op01_ready") is not False or data.get("rsr_op01_repair_required") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 repair flags changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DHR_OP09_RESULT_MEMO_BOUNDARY_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 repair next step changed")
        if not data.get("rsr_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 repair must carry blockers")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_UNEXPECTED_HANDOFF_BRANCH_MANUAL_HOLD_REF:
        if data.get("rsr_op01_ready") is not False or data.get("rsr_op01_unexpected_handoff_branch_manual_hold") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 unexpected handoff flags changed")
        if data.get("dhr_op09_selected_branch_ref") != P7_R54_AHR_POST_DHR09_RSR_DHR_HANDOFF_BRANCH_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 unexpected handoff branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_UNEXPECTED_DHR_HANDOFF_BRANCH_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 unexpected handoff next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP01 status ref is not allowed")
    return True

def _contract_valid_for(material: Mapping[str, Any] | None, assertion: Any) -> bool:
    if not isinstance(material, Mapping):
        return False
    try:
        return assertion(material) is True
    except ValueError:
        return False


def _scan_optional_materials(materials: Mapping[str, Mapping[str, Any] | None]) -> tuple[list[str], list[str], list[str]]:
    forbidden: list[str] = []
    body_like: list[str] = []
    promotion: list[str] = []
    for name, material in materials.items():
        if not isinstance(material, Mapping):
            continue
        forbidden.extend(_scan_forbidden_payload_key_paths(material, path=name))
        body_like.extend(_scan_body_like_value_paths(material, path=name))
        promotion.extend(f"{name}.{ref}" for ref in _promotion_claim_refs(material))
    return (
        _dedupe_clean_refs(forbidden, max_length=300),
        _dedupe_clean_refs(body_like, max_length=300),
        _dedupe_clean_refs(promotion, max_length=300),
    )


def _safe_int_value(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(
    *,
    dhr_op09_intake: Mapping[str, Any] | None = None,
    dhr_op09_result_memo_selected_branch_next_step_intake: Mapping[str, Any] | None = None,
    rsr_op01_dhr_op09_intake: Mapping[str, Any] | None = None,
    dmd_op08_result_memo: Mapping[str, Any] | None = None,
    alr_op12_result_memo: Mapping[str, Any] | None = None,
    elr_op19_result_memo: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP02 body-free upstream relationship verification material."""

    op01 = dhr_op09_intake or dhr_op09_result_memo_selected_branch_next_step_intake or rsr_op01_dhr_op09_intake
    if op01 is None:
        op01 = build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op01.get("review_session_id") if isinstance(op01, Mapping) else None))
    try:
        op01_valid = assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract(op01) is True
    except ValueError:
        op01_valid = False
    op01_map = op01 if isinstance(op01, Mapping) else {}

    dmd_map = dmd_op08_result_memo if isinstance(dmd_op08_result_memo, Mapping) else {}
    alr_map = alr_op12_result_memo if isinstance(alr_op12_result_memo, Mapping) else {}
    elr_map = elr_op19_result_memo if isinstance(elr_op19_result_memo, Mapping) else {}
    dmd_present = bool(dmd_map)
    alr_present = bool(alr_map)
    elr_present = bool(elr_map)
    dmd_valid = _contract_valid_for(dmd_op08_result_memo, dmd.assert_p7_r54_ahr_post_dmh18_dmd_op08_bodyfree_result_memo_target_tests_regression_closure_contract)
    alr_valid = _contract_valid_for(alr_op12_result_memo, alr.assert_p7_r54_ahr_post_dmd08_alr_op12_result_memo_target_tests_selected_regression_closure_contract)
    elr_valid = _contract_valid_for(elr_op19_result_memo, elr.assert_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure_contract)

    dhr_closed_retry = (
        op01_valid
        and op01_map.get("rsr_op01_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP01_STATUS_RETRY_OR_START_REQUIRED_REF
        and op01_map.get("dhr_op09_contract_valid") is True
        and op01_map.get("dhr_op09_result_memo_bodyfree_closed") is True
        and op01_map.get("dhr_op09_selected_branch_ref") == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_BRANCH_REF
        and op01_map.get("dhr_op09_next_required_step") == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_DEFAULT_NEXT_REQUIRED_STEP_REF
        and op01_map.get("dhr_op09_dmd_handoff_plan_materialized") is False
    )
    missing_optional = []
    if not dmd_present:
        missing_optional.append("dmd_op08_optional_material_missing_but_dhr09_closed_bodyfree")
    if not alr_present:
        missing_optional.append("alr_op12_optional_material_missing_but_dhr09_closed_bodyfree")
    if not elr_present:
        missing_optional.append("elr_op19_optional_material_missing_but_dhr09_closed_bodyfree")
    relation_conflicts: list[str] = []
    if dmd_present and not dmd_valid:
        relation_conflicts.append("dmd_op08_contract_invalid")
    if alr_present and not alr_valid:
        relation_conflicts.append("alr_op12_contract_invalid")
    if elr_present and not elr_valid:
        relation_conflicts.append("elr_op19_contract_invalid")
    if dmd_valid and dmd_map.get("branch_ref") != dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF:
        relation_conflicts.append("dmd_op08_branch_conflicts_with_dhr09_retry_start_required")
    if alr_valid and alr_map.get("selected_action_ref") != alr.P7_R54_AHR_POST_DMD08_ALR_ACTION_RETRY_OR_START_LOCAL_ONLY_REVIEW_REQUIRED_REF:
        relation_conflicts.append("alr_op12_selected_action_conflicts_with_dhr09_retry_start_required")
    if elr_valid and elr_map.get("result_memo_bodyfree_closed") is not True:
        relation_conflicts.append("elr_op19_not_closed_bodyfree")
    forbidden_paths, body_like_paths, promotion_claims = _scan_optional_materials({
        "rsr_op01_dhr09_intake": op01_map,
        "dmd_op08_result_memo": dmd_op08_result_memo,
        "alr_op12_result_memo": alr_op12_result_memo,
        "elr_op19_result_memo": elr_op19_result_memo,
    })

    blockers: list[str] = []
    if not dhr_closed_retry:
        blockers.append("dhr09_missing_or_invalid_retry_start_closed_intake")
    if relation_conflicts:
        blockers.append("upstream_relation_conflict_or_contract_invalid")
    if forbidden_paths:
        blockers.append("upstream_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("upstream_body_like_value_detected")
    if promotion_claims:
        blockers.append("upstream_helper_green_promotion_claim_detected")
    if blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_REPAIR_REQUIRED_REF if op01_valid else P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_WAITING_OR_INCOMPLETE_REF
        reasons = ["upstream_relationship_not_ready_for_allow_gate"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_UPSTREAM_RELATION_BEFORE_ALLOW_GATE_REF if op01_valid else P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_RSR_OP01_RETRY_START_INTAKE_REF
    elif not (dmd_present and alr_present and elr_present):
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_PARTIAL_DHR09_CLOSED_BODYFREE_REF
        reasons = ["dhr09_closed_retry_start_branch_sufficient_with_optional_upstream_missing"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_VERIFIED_BODYFREE_REF
        reasons = ["upstream_relationship_verified_bodyfree"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF
    ready = status_ref in (P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_VERIFIED_BODYFREE_REF, P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_PARTIAL_DHR09_CLOSED_BODYFREE_REF)
    optional_count = sum(1 for flag in (dmd_present, alr_present, elr_present) if flag)
    valid_count = sum(1 for flag in (dmd_valid, alr_valid, elr_valid) if flag)

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_contract_valid": op01_valid,
        "op01_status_ref": _clean_ref(op01_map.get("rsr_op01_status_ref"), default="op01_status_missing", max_length=260),
        "op01_ready_for_upstream_relationship_verification": bool(op01_map.get("rsr_op01_ready_for_upstream_relationship_verification") is True),
        "op01_next_required_step": _clean_ref(op01_map.get("next_required_step"), default="op01_next_required_step_missing", max_length=260),
        "dhr_op09_contract_valid": bool(op01_map.get("dhr_op09_contract_valid") is True),
        "dhr_op09_result_memo_bodyfree_closed": bool(op01_map.get("dhr_op09_result_memo_bodyfree_closed") is True),
        "dhr_op09_selected_branch_ref": _clean_ref(op01_map.get("dhr_op09_selected_branch_ref"), default="dhr_op09_branch_missing", max_length=260),
        "dhr_op09_next_required_step": _clean_ref(op01_map.get("dhr_op09_next_required_step"), default="dhr_op09_next_missing", max_length=260),
        "dhr_op09_dmd_handoff_plan_materialized": bool(op01_map.get("dhr_op09_dmd_handoff_plan_materialized") is True),
        "upstream_chain_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP02_UPSTREAM_CHAIN_REFS),
        "upstream_chain_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP02_UPSTREAM_CHAIN_REFS),
        "dmd_op08_material_present": dmd_present,
        "dmd_op08_contract_valid": dmd_valid,
        "dmd_op08_branch_ref": _clean_ref(dmd_map.get("branch_ref"), default="dmd_op08_branch_missing", max_length=260),
        "dmd_op08_next_required_step": _clean_ref(dmd_map.get("next_required_step"), default="dmd_op08_next_missing", max_length=260),
        "alr_op12_material_present": alr_present,
        "alr_op12_contract_valid": alr_valid,
        "alr_op12_selected_action_ref": _clean_ref(alr_map.get("selected_action_ref"), default="alr_op12_selected_action_missing", max_length=260),
        "alr_op12_next_required_step": _clean_ref(alr_map.get("next_required_step"), default="alr_op12_next_missing", max_length=260),
        "elr_op19_material_present": elr_present,
        "elr_op19_contract_valid": elr_valid,
        "elr_op19_result_memo_bodyfree_closed": bool(elr_map.get("result_memo_bodyfree_closed") is True),
        "elr_op19_next_required_step": _clean_ref(elr_map.get("next_required_step"), default="elr_op19_next_missing", max_length=260),
        "op02_optional_upstream_material_count": optional_count,
        "op02_valid_upstream_material_count": valid_count,
        "op02_missing_optional_upstream_relation_refs": _dedupe_clean_refs(missing_optional),
        "op02_missing_optional_upstream_relation_ref_count": len(_dedupe_clean_refs(missing_optional)),
        "op02_relation_conflict_refs": _dedupe_clean_refs(relation_conflicts),
        "op02_relation_conflict_ref_count": len(_dedupe_clean_refs(relation_conflicts)),
        "op02_forbidden_payload_key_path_refs": forbidden_paths,
        "op02_forbidden_payload_key_path_count": len(forbidden_paths),
        "op02_body_like_value_path_refs": body_like_paths,
        "op02_body_like_value_path_count": len(body_like_paths),
        "op02_promotion_claim_refs": promotion_claims,
        "op02_promotion_claim_ref_count": len(promotion_claims),
        "rsr_op02_status_ref": status_ref,
        "rsr_op02_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP02_ALLOWED_STATUS_REFS),
        "rsr_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP02_ALLOWED_STATUS_REFS),
        "rsr_op02_ready": ready,
        "rsr_op02_upstream_relationship_verified": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_VERIFIED_BODYFREE_REF,
        "rsr_op02_partial_upstream_material_accepted_from_dhr09": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_PARTIAL_DHR09_CLOSED_BODYFREE_REF,
        "rsr_op02_waiting_or_incomplete": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_WAITING_OR_INCOMPLETE_REF,
        "rsr_op02_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_REPAIR_REQUIRED_REF,
        "rsr_op02_ready_for_explicit_local_only_allow_gate": ready,
        "rsr_op02_reason_refs": _dedupe_clean_refs(reasons),
        "rsr_op02_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "rsr_op02_blocker_refs": _dedupe_clean_refs(blockers),
        "rsr_op02_blocker_ref_count": len(_dedupe_clean_refs(blockers)),
        "rsr_op02_does_not_accept_explicit_local_only_allow": True,
        "rsr_op02_does_not_generate_body_full_packet": True,
        "rsr_op02_does_not_run_actual_local_human_review": True,
        "rsr_op02_does_not_create_receipts_rows_or_disposal": True,
        "rsr_op02_does_not_execute_dmd_or_r52": True,
        "rsr_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP02 upstream relationship verification contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP02")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP02_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP02_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP02")
    if tuple(data.get("rsr_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 allowed status refs changed")
    for field, count_field in (("upstream_chain_refs", "upstream_chain_ref_count"), ("op02_missing_optional_upstream_relation_refs", "op02_missing_optional_upstream_relation_ref_count"), ("op02_relation_conflict_refs", "op02_relation_conflict_ref_count"), ("op02_forbidden_payload_key_path_refs", "op02_forbidden_payload_key_path_count"), ("op02_body_like_value_path_refs", "op02_body_like_value_path_count"), ("op02_promotion_claim_refs", "op02_promotion_claim_ref_count"), ("rsr_op02_allowed_status_refs", "rsr_op02_allowed_status_ref_count"), ("rsr_op02_reason_refs", "rsr_op02_reason_ref_count"), ("rsr_op02_blocker_refs", "rsr_op02_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP02 {count_field} changed")
    if tuple(data.get("upstream_chain_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP02_UPSTREAM_CHAIN_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 upstream chain refs changed")
    for key in ("rsr_op02_does_not_accept_explicit_local_only_allow", "rsr_op02_does_not_generate_body_full_packet", "rsr_op02_does_not_run_actual_local_human_review", "rsr_op02_does_not_create_receipts_rows_or_disposal", "rsr_op02_does_not_execute_dmd_or_r52", "rsr_op02_does_not_start_p5_p6_p8_p7_or_release", "rsr_op02_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP02 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP02_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 implemented/not-yet steps changed")
    flags = [data.get("rsr_op02_upstream_relationship_verified") is True, data.get("rsr_op02_partial_upstream_material_accepted_from_dhr09") is True, data.get("rsr_op02_waiting_or_incomplete") is True, data.get("rsr_op02_repair_required") is True]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 exactly one status flag must be true")
    if data.get("rsr_op02_status_ref") in (P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_VERIFIED_BODYFREE_REF, P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_PARTIAL_DHR09_CLOSED_BODYFREE_REF):
        if data.get("rsr_op02_ready") is not True or data.get("rsr_op02_ready_for_explicit_local_only_allow_gate") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 ready status changed")
        if data.get("rsr_op02_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 ready status cannot carry blockers")
    elif data.get("rsr_op02_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_REPAIR_REQUIRED_REF:
        if data.get("rsr_op02_ready") is not False or not data.get("rsr_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 repair status changed")
    elif data.get("rsr_op02_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP02_STATUS_WAITING_OR_INCOMPLETE_REF:
        if data.get("rsr_op02_ready") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_RSR_OP01_RETRY_START_INTAKE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 waiting status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP02 status ref is not allowed")
    return True


def _evaluate_allow_receipt(receipt: Mapping[str, Any] | None, *, expected_review_session_id: str) -> tuple[bool, bool, bool, list[str], list[str], list[str], list[str], list[str]]:
    if not isinstance(receipt, Mapping):
        return False, False, False, ["explicit_local_only_allow_receipt_missing"], [], [], [], []
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(receipt, path="explicit_local_only_allow_receipt"), max_length=300)
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(receipt, path="explicit_local_only_allow_receipt"), max_length=300)
    promo = _dedupe_clean_refs([f"explicit_local_only_allow_receipt.{ref}" for ref in _promotion_claim_refs(receipt)], max_length=300)
    blockers: list[str] = []
    scope_blockers: list[str] = []
    if receipt.get("schema_version") != P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_SCHEMA_VERSION:
        blockers.append("explicit_local_only_allow_receipt_schema_invalid")
    if not _clean_ref(receipt.get("allow_receipt_ref"), default=""):
        blockers.append("explicit_local_only_allow_receipt_ref_missing")
    if _safe_review_session_id(receipt.get("review_session_id")) != expected_review_session_id:
        scope_blockers.append("explicit_local_only_allow_review_session_mismatch")
    if receipt.get("allowed_operation_scope_ref") != P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_REF:
        scope_blockers.append("explicit_local_only_allow_scope_mismatch")
    if _safe_int_value(receipt.get("allowed_case_count")) != 24:
        scope_blockers.append("explicit_local_only_allow_case_count_mismatch")
    if receipt.get("local_only_operation_allowed") is not True:
        scope_blockers.append("explicit_local_only_allow_local_only_not_true")
    if receipt.get("body_full_transient_review_allowed") is not True:
        scope_blockers.append("explicit_local_only_allow_body_full_transient_not_true")
    if receipt.get("external_export_allowed") is not False:
        scope_blockers.append("explicit_local_only_allow_external_export_not_false")
    if receipt.get("disposal_purge_required") is not True:
        scope_blockers.append("explicit_local_only_allow_purge_required_not_true")
    for key in ("raw_input_included", "comment_text_body_included", "returned_surface_body_included", "reviewer_free_text_included", "question_text_included", "draft_question_text_included", "local_path_included", "body_hash_included", "terminal_output_body_included"):
        if receipt.get(key) is not False:
            blockers.append(f"explicit_local_only_allow_{key}_must_be_false")
    if receipt.get("body_free") is not True:
        blockers.append("explicit_local_only_allow_body_free_not_true")
    if forbidden:
        blockers.append("explicit_local_only_allow_forbidden_payload_key_detected")
    if body_like:
        blockers.append("explicit_local_only_allow_body_like_value_detected")
    if promo:
        blockers.append("explicit_local_only_allow_promotion_claim_detected")
    return not blockers and not scope_blockers, bool(scope_blockers), True, _dedupe_clean_refs(blockers), _dedupe_clean_refs(scope_blockers), forbidden, body_like, promo


def build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate(
    *,
    upstream_relationship_verification: Mapping[str, Any] | None = None,
    rsr_op02_upstream_relationship_verification: Mapping[str, Any] | None = None,
    explicit_local_only_allow_receipt: Mapping[str, Any] | None = None,
    allow_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP03 explicit local-only allow receipt acceptance gate material."""
    op02 = upstream_relationship_verification or rsr_op02_upstream_relationship_verification
    if op02 is None:
        op02 = build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op02.get("review_session_id") if isinstance(op02, Mapping) else None))
    try:
        op02_valid = assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract(op02) is True
    except ValueError:
        op02_valid = False
    op02_map = op02 if isinstance(op02, Mapping) else {}
    op02_ready = op02_valid and op02_map.get("rsr_op02_ready_for_explicit_local_only_allow_gate") is True
    receipt = explicit_local_only_allow_receipt if explicit_local_only_allow_receipt is not None else allow_receipt
    receipt_map = receipt if isinstance(receipt, Mapping) else {}
    receipt_valid, scope_mismatch, receipt_present, blockers, scope_blockers, forbidden, body_like, promo = _evaluate_allow_receipt(receipt, expected_review_session_id=session_id)
    all_blockers = _dedupe_clean_refs([*blockers, *scope_blockers, *( [] if op02_ready else ["rsr_op02_not_ready_for_allow_gate"] )])
    if not receipt_present:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF
        reasons = ["explicit_local_only_allow_receipt_missing_waiting"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF
    elif not op02_ready:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF
        reasons = ["explicit_local_only_allow_cannot_be_accepted_before_op02_ready"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_UPSTREAM_RELATION_BEFORE_ALLOW_GATE_REF
    elif scope_mismatch:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_SCOPE_MISMATCH_BLOCKED_REF
        reasons = ["explicit_local_only_allow_scope_mismatch_blocks_actual_review_start"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_MISMATCH_REF
    elif not receipt_valid:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF
        reasons = ["explicit_local_only_allow_receipt_invalid_or_not_bodyfree"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_ACCEPTED_BODYFREE_REF
        reasons = ["explicit_local_only_allow_receipt_accepted_bodyfree"]
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF
    accepted = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_ACCEPTED_BODYFREE_REF

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_contract_valid": op02_valid,
        "op02_ready_for_explicit_local_only_allow_gate": op02_ready,
        "op02_next_required_step": _clean_ref(op02_map.get("next_required_step"), default="op02_next_missing", max_length=260),
        "explicit_allow_receipt_present": receipt_present,
        "explicit_allow_receipt_contract_valid": receipt_valid,
        "explicit_allow_receipt_schema_version": _clean_ref(receipt_map.get("schema_version"), default="explicit_allow_schema_missing", max_length=260),
        "explicit_allow_receipt_ref": _clean_ref(receipt_map.get("allow_receipt_ref"), default="explicit_allow_ref_missing", max_length=260),
        "explicit_allow_receipt_review_session_id": _safe_review_session_id(receipt_map.get("review_session_id")) if receipt_present else "explicit_allow_review_session_missing",
        "explicit_allow_allowed_operation_scope_ref": _clean_ref(receipt_map.get("allowed_operation_scope_ref"), default="explicit_allow_scope_missing", max_length=260),
        "explicit_allow_allowed_case_count": _safe_int_value(receipt_map.get("allowed_case_count")) if receipt_present else 0,
        "explicit_allow_local_only_operation_allowed": bool(receipt_map.get("local_only_operation_allowed") is True),
        "explicit_allow_body_full_transient_review_allowed": bool(receipt_map.get("body_full_transient_review_allowed") is True),
        "explicit_allow_external_export_allowed": bool(receipt_map.get("external_export_allowed") is True),
        "explicit_allow_disposal_purge_required": bool(receipt_map.get("disposal_purge_required") is True),
        "explicit_allow_raw_input_included": bool(receipt_map.get("raw_input_included") is True),
        "explicit_allow_comment_text_body_included": bool(receipt_map.get("comment_text_body_included") is True),
        "explicit_allow_returned_surface_body_included": bool(receipt_map.get("returned_surface_body_included") is True),
        "explicit_allow_reviewer_free_text_included": bool(receipt_map.get("reviewer_free_text_included") is True),
        "explicit_allow_question_text_included": bool(receipt_map.get("question_text_included") is True),
        "explicit_allow_draft_question_text_included": bool(receipt_map.get("draft_question_text_included") is True),
        "explicit_allow_local_path_included": bool(receipt_map.get("local_path_included") is True),
        "explicit_allow_body_hash_included": bool(receipt_map.get("body_hash_included") is True),
        "explicit_allow_terminal_output_body_included": bool(receipt_map.get("terminal_output_body_included") is True),
        "explicit_allow_body_free": bool(receipt_map.get("body_free") is True),
        "explicit_allow_forbidden_payload_key_path_refs": forbidden,
        "explicit_allow_forbidden_payload_key_path_count": len(forbidden),
        "explicit_allow_body_like_value_path_refs": body_like,
        "explicit_allow_body_like_value_path_count": len(body_like),
        "explicit_allow_promotion_claim_refs": promo,
        "explicit_allow_promotion_claim_ref_count": len(promo),
        "rsr_op03_status_ref": status_ref,
        "rsr_op03_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP03_ALLOWED_STATUS_REFS),
        "rsr_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP03_ALLOWED_STATUS_REFS),
        "rsr_op03_ready": accepted,
        "rsr_op03_explicit_allow_accepted": accepted,
        "rsr_op03_explicit_allow_missing_waiting": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF,
        "rsr_op03_explicit_allow_invalid_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF,
        "rsr_op03_explicit_allow_scope_mismatch_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_SCOPE_MISMATCH_BLOCKED_REF,
        "rsr_op03_ready_for_readiness_blocker_classifier": accepted,
        "explicit_local_only_allow_receipt_accepted_by_rsr_op03": accepted,
        "explicit_local_only_allow_granted_by_helper": False,
        "allow_required_was_not_rewritten_to_allow_granted": True,
        "rsr_op03_reason_refs": _dedupe_clean_refs(reasons),
        "rsr_op03_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "rsr_op03_blocker_refs": [] if accepted or status_ref == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF else all_blockers,
        "rsr_op03_blocker_ref_count": 0 if accepted or status_ref == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF else len(all_blockers),
        "rsr_op03_does_not_generate_body_full_packet": True,
        "rsr_op03_does_not_run_actual_local_human_review": True,
        "rsr_op03_does_not_create_receipts_rows_or_disposal": True,
        "rsr_op03_does_not_execute_dmd_or_r52": True,
        "rsr_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP03 explicit local-only allow receipt acceptance gate contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP03")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP03_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP03_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP03")
    for field, count_field in (("explicit_allow_forbidden_payload_key_path_refs", "explicit_allow_forbidden_payload_key_path_count"), ("explicit_allow_body_like_value_path_refs", "explicit_allow_body_like_value_path_count"), ("explicit_allow_promotion_claim_refs", "explicit_allow_promotion_claim_ref_count"), ("rsr_op03_allowed_status_refs", "rsr_op03_allowed_status_ref_count"), ("rsr_op03_reason_refs", "rsr_op03_reason_ref_count"), ("rsr_op03_blocker_refs", "rsr_op03_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP03 {count_field} changed")
    for key in ("rsr_op03_does_not_generate_body_full_packet", "rsr_op03_does_not_run_actual_local_human_review", "rsr_op03_does_not_create_receipts_rows_or_disposal", "rsr_op03_does_not_execute_dmd_or_r52", "rsr_op03_does_not_start_p5_p6_p8_p7_or_release", "rsr_op03_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution", "allow_required_was_not_rewritten_to_allow_granted"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP03 required true boundary changed: {key}")
    for key in ("explicit_local_only_allow_granted_by_helper", "explicit_local_only_allow_receipt_accepted_here", "body_full_packet_generated_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP03 execution/grant flag promoted: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP03_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 implemented/not-yet steps changed")
    flags = [data.get("rsr_op03_explicit_allow_accepted") is True, data.get("rsr_op03_explicit_allow_missing_waiting") is True, data.get("rsr_op03_explicit_allow_invalid_repair_required") is True, data.get("rsr_op03_explicit_allow_scope_mismatch_blocked") is True]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 exactly one status flag must be true")
    if data.get("rsr_op03_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_ACCEPTED_BODYFREE_REF:
        if data.get("op02_ready_for_explicit_local_only_allow_gate") is not True or data.get("explicit_allow_receipt_contract_valid") is not True or data.get("rsr_op03_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 accepted status changed")
        if data.get("explicit_allow_allowed_case_count") != 24 or data.get("explicit_allow_allowed_operation_scope_ref") != P7_R54_AHR_POST_DHR09_RSR_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_REF or data.get("explicit_allow_external_export_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 accepted receipt boundary changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 accepted next step changed")
    elif data.get("rsr_op03_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_MISSING_WAITING_REF:
        if data.get("rsr_op03_ready") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 missing status changed")
    elif data.get("rsr_op03_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op03_ready") is not False or not data.get("rsr_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 invalid status changed")
    elif data.get("rsr_op03_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP03_STATUS_SCOPE_MISMATCH_BLOCKED_REF:
        if data.get("rsr_op03_ready") is not False or not data.get("rsr_op03_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_EXPLICIT_LOCAL_ONLY_ALLOW_SCOPE_MISMATCH_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 scope mismatch status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP03 status ref is not allowed")
    return True


def _safe_bool(value: Any) -> bool:
    return bool(value is True)


def _bodyfree_status_ref(value: Any, *, default: str) -> str:
    return _clean_ref(value, default=default, max_length=220)


def _reviewer_person_ref_shape_valid(value: Any) -> bool:
    raw = str(value or "")
    cleaned = _clean_ref(value, max_length=180)
    if not cleaned:
        return False
    if "@" in raw or _ref_has_local_path_shape(raw):
        return False
    lowered = raw.lower()
    if "mailto:" in lowered or "file://" in lowered:
        return False
    return True


def build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier(
    *,
    explicit_local_only_allow_gate: Mapping[str, Any] | None = None,
    op03_explicit_local_only_allow_gate: Mapping[str, Any] | None = None,
    environment_ready: Any = False,
    environment_ready_ref: Any = "environment_ready_ref_missing",
    material_manifest_ready: Any = False,
    material_manifest_ready_ref: Any = "material_manifest_ready_ref_missing",
    reviewer_person_boundary_ready: Any = False,
    local_only_boundary_ready: Any = False,
    purge_plan_ready: Any = False,
    source_claim_preflight_ready: Any = False,
    body_leak_preflight_passed: Any = True,
    body_leak_preflight_material: Mapping[str, Any] | Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP04 readiness blocker classifier material."""

    op03 = explicit_local_only_allow_gate if explicit_local_only_allow_gate is not None else op03_explicit_local_only_allow_gate
    if op03 is None:
        op03 = build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate()
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op03.get("review_session_id") if isinstance(op03, Mapping) else None))
    try:
        op03_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract(op03) is True
    except ValueError:
        op03_contract_valid = False
    op03_status_ref = _bodyfree_status_ref(op03.get("rsr_op03_status_ref") if isinstance(op03, Mapping) else None, default="rsr_op03_status_missing")
    op03_ready = bool(op03_contract_valid and op03.get("rsr_op03_ready_for_readiness_blocker_classifier") is True)
    op03_explicit_allow_accepted = bool(op03_contract_valid and op03.get("rsr_op03_explicit_allow_accepted") is True)
    op03_next_step = _bodyfree_status_ref(op03.get("next_required_step") if isinstance(op03, Mapping) else None, default="rsr_op03_next_required_step_missing")

    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(body_leak_preflight_material or {}, path="op04_body_leak_preflight"))
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(body_leak_preflight_material or {}, path="op04_body_leak_preflight"))
    promo = _dedupe_clean_refs(_promotion_claim_refs(body_leak_preflight_material if isinstance(body_leak_preflight_material, Mapping) else {}))

    env_ready = _safe_bool(environment_ready)
    material_ready = _safe_bool(material_manifest_ready)
    reviewer_ready = _safe_bool(reviewer_person_boundary_ready)
    local_ready = _safe_bool(local_only_boundary_ready)
    purge_ready = _safe_bool(purge_plan_ready)
    source_ready = _safe_bool(source_claim_preflight_ready)
    leak_passed = bool(body_leak_preflight_passed is True and not forbidden and not body_like and not promo)

    stop_reasons: list[str] = []
    blockers: list[str] = []
    reasons: list[str] = []
    if not op03_contract_valid:
        stop_reasons.append("RSR_STOP_UPSTREAM_REPAIR_REQUIRED")
        blockers.append("rsr_op03_contract_invalid_before_readiness_classifier")
    if not op03_explicit_allow_accepted:
        stop_reasons.append("RSR_STOP_EXPLICIT_ALLOW_MISSING")
        blockers.append("explicit_local_only_allow_not_accepted_before_readiness_classifier")
    if not env_ready:
        stop_reasons.append("RSR_STOP_ENVIRONMENT_MISSING")
        blockers.append("environment_ready_ref_missing_or_false")
    if not material_ready:
        stop_reasons.append("RSR_STOP_MATERIAL_MISSING")
        blockers.append("material_manifest_ready_ref_missing_or_false")
    if not reviewer_ready:
        stop_reasons.append("RSR_STOP_REVIEWER_PERSON_NOT_CONFIRMED")
        blockers.append("reviewer_person_boundary_not_ready")
    if not local_ready:
        stop_reasons.append("RSR_STOP_LOCAL_ONLY_BOUNDARY_NOT_CONFIRMED")
        blockers.append("local_only_boundary_not_confirmed")
    if not purge_ready:
        stop_reasons.append("RSR_STOP_PURGE_PLAN_MISSING")
        blockers.append("purge_plan_not_ready")
    if not source_ready:
        stop_reasons.append("RSR_STOP_SOURCE_CLAIM_INSUFFICIENT")
        blockers.append("source_claim_preflight_insufficient")
    if not leak_passed:
        stop_reasons.append("RSR_STOP_BODY_LEAK_RISK")
        if forbidden:
            blockers.append("readiness_body_leak_forbidden_payload_key_detected")
        if body_like:
            blockers.append("readiness_body_like_value_detected")
        if promo:
            blockers.append("readiness_promotion_claim_detected")
        if body_leak_preflight_passed is not True:
            blockers.append("body_leak_preflight_not_passed")

    blockers = _dedupe_clean_refs(blockers)
    stop_reasons = _dedupe_clean_refs(stop_reasons)

    if "RSR_STOP_BODY_LEAK_RISK" in stop_reasons:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_BODY_LEAK_RISK_BLOCKED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODY_LEAK_RISK_BEFORE_SESSION_ENVELOPE_REF
        reasons.append("readiness_body_leak_risk_blocks_before_session_envelope")
    elif not op03_explicit_allow_accepted:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF
        reasons.append("explicit_local_only_allow_receipt_still_required_before_readiness")
    elif blockers == ["source_claim_preflight_insufficient"]:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_SOURCE_CLAIM_INSUFFICIENT_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SOURCE_CLAIM_PREFLIGHT_BEFORE_SESSION_ENVELOPE_REF
        reasons.append("source_claim_preflight_insufficient_before_session_envelope")
    elif blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_READINESS_BLOCKERS_BEFORE_SESSION_ENVELOPE_REF
        reasons.append("readiness_environment_material_reviewer_local_only_or_purge_repair_required")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_READY_TO_START_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF
        reasons.append("readiness_bodyfree_ready_for_local_only_session_envelope")
    ready = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_READY_TO_START_REF

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_contract_valid": op03_contract_valid,
        "op03_status_ref": op03_status_ref,
        "op03_ready_for_readiness_blocker_classifier": op03_ready,
        "op03_explicit_allow_accepted": op03_explicit_allow_accepted,
        "op03_next_required_step": op03_next_step,
        "environment_ready": env_ready,
        "environment_ready_ref": _clean_ref(environment_ready_ref, default="environment_ready_ref_missing", max_length=180),
        "material_manifest_ready": material_ready,
        "material_manifest_ready_ref": _clean_ref(material_manifest_ready_ref, default="material_manifest_ready_ref_missing", max_length=180),
        "explicit_allow_accepted": op03_explicit_allow_accepted,
        "reviewer_person_boundary_ready": reviewer_ready,
        "local_only_boundary_ready": local_ready,
        "purge_plan_ready": purge_ready,
        "source_claim_preflight_ready": source_ready,
        "body_leak_preflight_passed": leak_passed,
        "body_leak_preflight_forbidden_payload_key_path_refs": forbidden,
        "body_leak_preflight_forbidden_payload_key_path_count": len(forbidden),
        "body_leak_preflight_body_like_value_path_refs": body_like,
        "body_leak_preflight_body_like_value_path_count": len(body_like),
        "body_leak_preflight_promotion_claim_refs": promo,
        "body_leak_preflight_promotion_claim_ref_count": len(promo),
        "readiness_stop_reason_refs": stop_reasons,
        "readiness_stop_reason_ref_count": len(stop_reasons),
        "readiness_reason_refs": _dedupe_clean_refs(reasons),
        "readiness_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "readiness_blocker_refs": blockers,
        "readiness_blocker_ref_count": len(blockers),
        "rsr_op04_status_ref": status_ref,
        "rsr_op04_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP04_ALLOWED_STATUS_REFS),
        "rsr_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP04_ALLOWED_STATUS_REFS),
        "rsr_op04_ready": ready,
        "rsr_op04_ready_to_start_local_only_review": ready,
        "rsr_op04_wait_for_explicit_local_only_allow": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
        "rsr_op04_environment_or_material_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF,
        "rsr_op04_body_leak_risk_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_BODY_LEAK_RISK_BLOCKED_REF,
        "rsr_op04_source_claim_insufficient": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_SOURCE_CLAIM_INSUFFICIENT_REF,
        "rsr_op04_ready_for_local_only_review_session_envelope": ready,
        "rsr_op04_does_not_generate_body_full_packet": True,
        "rsr_op04_does_not_run_actual_local_human_review": True,
        "rsr_op04_does_not_create_receipts_rows_or_disposal": True,
        "rsr_op04_does_not_execute_dmd_or_r52": True,
        "rsr_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP04 readiness blocker classifier contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP04")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP04_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP04_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP04")
    for field, count_field in (("body_leak_preflight_forbidden_payload_key_path_refs", "body_leak_preflight_forbidden_payload_key_path_count"), ("body_leak_preflight_body_like_value_path_refs", "body_leak_preflight_body_like_value_path_count"), ("body_leak_preflight_promotion_claim_refs", "body_leak_preflight_promotion_claim_ref_count"), ("readiness_stop_reason_refs", "readiness_stop_reason_ref_count"), ("readiness_reason_refs", "readiness_reason_ref_count"), ("readiness_blocker_refs", "readiness_blocker_ref_count"), ("rsr_op04_allowed_status_refs", "rsr_op04_allowed_status_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP04 {count_field} changed")
    for key in ("rsr_op04_does_not_generate_body_full_packet", "rsr_op04_does_not_run_actual_local_human_review", "rsr_op04_does_not_create_receipts_rows_or_disposal", "rsr_op04_does_not_execute_dmd_or_r52", "rsr_op04_does_not_start_p5_p6_p8_p7_or_release", "rsr_op04_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP04 required true boundary changed: {key}")
    for key in ("body_full_packet_generated_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP04 execution/promoted flag changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP04_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 implemented/not-yet steps changed")
    flags = [data.get("rsr_op04_ready_to_start_local_only_review") is True, data.get("rsr_op04_wait_for_explicit_local_only_allow") is True, data.get("rsr_op04_environment_or_material_repair_required") is True, data.get("rsr_op04_body_leak_risk_blocked") is True, data.get("rsr_op04_source_claim_insufficient") is True]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 exactly one status flag must be true")
    if data.get("rsr_op04_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_READY_TO_START_REF:
        if data.get("rsr_op04_ready") is not True or data.get("readiness_blocker_refs") != [] or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 ready status changed")
        for key in ("op03_explicit_allow_accepted", "environment_ready", "material_manifest_ready", "reviewer_person_boundary_ready", "local_only_boundary_ready", "purge_plan_ready", "source_claim_preflight_ready", "body_leak_preflight_passed"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP04 ready prerequisite changed: {key}")
    elif data.get("rsr_op04_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF:
        if data.get("rsr_op04_ready") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 wait-for-allow status changed")
    elif data.get("rsr_op04_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_BODY_LEAK_RISK_BLOCKED_REF:
        if data.get("rsr_op04_ready") is not False or "RSR_STOP_BODY_LEAK_RISK" not in (data.get("readiness_stop_reason_refs") or []):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 body-leak blocked status changed")
    elif data.get("rsr_op04_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_SOURCE_CLAIM_INSUFFICIENT_REF:
        if data.get("rsr_op04_ready") is not False or "RSR_STOP_SOURCE_CLAIM_INSUFFICIENT" not in (data.get("readiness_stop_reason_refs") or []):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 source-claim status changed")
    elif data.get("rsr_op04_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP04_STATUS_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF:
        if data.get("rsr_op04_ready") is not False or not data.get("readiness_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 repair status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP04 status ref is not allowed")
    return True


def build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(
    *,
    readiness_blocker_classifier: Mapping[str, Any] | None = None,
    op04_readiness_blocker_classifier: Mapping[str, Any] | None = None,
    reviewer_person_ref: Any = None,
    reviewer_is_person_confirmed: Any = False,
    reviewer_role_ref: Any = P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF,
    reviewer_boundary_material: Mapping[str, Any] | Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP05 body-free local-only review session envelope and reviewer boundary."""

    op04 = readiness_blocker_classifier if readiness_blocker_classifier is not None else op04_readiness_blocker_classifier
    if op04 is None:
        op04 = build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier()
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op04.get("review_session_id") if isinstance(op04, Mapping) else None))
    try:
        op04_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract(op04) is True
    except ValueError:
        op04_contract_valid = False
    op04_status_ref = _bodyfree_status_ref(op04.get("rsr_op04_status_ref") if isinstance(op04, Mapping) else None, default="rsr_op04_status_missing")
    op04_ready = bool(op04_contract_valid and op04.get("rsr_op04_ready_for_local_only_review_session_envelope") is True)
    op04_next_step = _bodyfree_status_ref(op04.get("next_required_step") if isinstance(op04, Mapping) else None, default="rsr_op04_next_required_step_missing")
    raw_reviewer_ref = str(reviewer_person_ref or "")
    cleaned_reviewer_ref = _clean_ref(reviewer_person_ref, default="", max_length=180)
    reviewer_ref_present = bool(cleaned_reviewer_ref)
    reviewer_ref_shape_valid = _reviewer_person_ref_shape_valid(reviewer_person_ref)
    reviewer_person_ref_for_output = (
        cleaned_reviewer_ref
        if reviewer_ref_shape_valid
        else ("reviewer_person_ref_invalid_bodyfree_boundary" if reviewer_ref_present else "")
    )
    person_confirmed = _safe_bool(reviewer_is_person_confirmed)
    role = _clean_ref(reviewer_role_ref, default="reviewer_role_missing", max_length=180)
    role_valid = role == P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF

    scan_material: Any = reviewer_boundary_material or {}
    if isinstance(scan_material, Mapping):
        scan_material = {**scan_material, "reviewer_person_ref_candidate": raw_reviewer_ref, "reviewer_role_ref_candidate": role}
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(scan_material, path="op05_reviewer_boundary"))
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(scan_material, path="op05_reviewer_boundary"))
    promo = _dedupe_clean_refs(_promotion_claim_refs(scan_material if isinstance(scan_material, Mapping) else {}))

    blockers: list[str] = []
    reasons: list[str] = []
    if not op04_ready:
        blockers.append("rsr_op04_not_ready_for_review_session_envelope")
    if not reviewer_ref_present:
        blockers.append("reviewer_person_ref_missing")
    if reviewer_ref_present and not reviewer_ref_shape_valid:
        blockers.append("reviewer_person_ref_not_bodyfree_identifier")
    if not person_confirmed:
        blockers.append("reviewer_person_not_confirmed")
    if not role_valid:
        blockers.append("reviewer_role_not_selection_only_review_operator")
    if forbidden:
        blockers.append("reviewer_boundary_forbidden_payload_key_detected")
    if body_like:
        blockers.append("reviewer_boundary_body_like_value_detected")
    if promo:
        blockers.append("reviewer_boundary_promotion_claim_detected")
    blockers = _dedupe_clean_refs(blockers)

    if forbidden or body_like or promo:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_BODY_LEAK_BLOCKED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEWER_BODY_LEAK_BEFORE_PACKET_REQUEST_REF
        reasons.append("reviewer_boundary_body_leak_blocks_before_packet_request")
    elif not op04_ready:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_WAITING_FOR_READINESS_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_READINESS_BEFORE_REVIEW_SESSION_ENVELOPE_REF
        reasons.append("readiness_classifier_not_ready_for_review_session_envelope")
    elif not person_confirmed:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_REVIEWER_PERSON_NOT_CONFIRMED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEWER_PERSON_BOUNDARY_REF
        reasons.append("reviewer_person_confirmation_required_before_packet_request")
    elif blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEWER_PERSON_BOUNDARY_REF
        reasons.append("reviewer_person_boundary_repair_required_before_packet_request")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_ACCEPTED_BODYFREE_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF
        reasons.append("bodyfree_review_session_envelope_and_reviewer_person_boundary_accepted")
    ready = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_ACCEPTED_BODYFREE_REF
    envelope_ref = _clean_ref(f"rsr_op05_review_session_envelope_{session_id}", max_length=220)

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op05_review_session_envelope_reviewer_boundary_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_contract_valid": op04_contract_valid,
        "op04_status_ref": op04_status_ref,
        "op04_ready_for_local_only_review_session_envelope": op04_ready,
        "op04_next_required_step": op04_next_step,
        "review_session_envelope_ref": envelope_ref,
        "review_session_id_normalized": session_id,
        "review_session_id_bodyfree": True,
        "reviewer_person_ref_present": reviewer_ref_present,
        "reviewer_person_ref": reviewer_person_ref_for_output,
        "reviewer_person_ref_bodyfree": reviewer_ref_shape_valid,
        "reviewer_person_ref_shape_valid": reviewer_ref_shape_valid,
        "reviewer_is_person_confirmed": person_confirmed,
        "reviewer_role_ref": role,
        "expected_reviewer_role_ref": P7_R54_AHR_POST_DHR09_RSR_OP05_REVIEWER_ROLE_SELECTION_ONLY_OPERATOR_REF,
        "reviewer_role_is_selection_only_review_operator": role_valid,
        "reviewer_is_helper_or_unit_test": False,
        "reviewer_free_text_allowed": False,
        "reviewer_body_note_allowed": False,
        "reviewer_name_material_included": False,
        "reviewer_email_material_included": False,
        "reviewer_raw_note_material_included": False,
        "reviewer_local_path_material_included": False,
        "reviewer_boundary_forbidden_payload_key_path_refs": forbidden,
        "reviewer_boundary_forbidden_payload_key_path_count": len(forbidden),
        "reviewer_boundary_body_like_value_path_refs": body_like,
        "reviewer_boundary_body_like_value_path_count": len(body_like),
        "reviewer_boundary_promotion_claim_refs": promo,
        "reviewer_boundary_promotion_claim_ref_count": len(promo),
        "reviewer_boundary_reason_refs": _dedupe_clean_refs(reasons),
        "reviewer_boundary_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "reviewer_boundary_blocker_refs": blockers,
        "reviewer_boundary_blocker_ref_count": len(blockers),
        "selection_only_review_operator_boundary_confirmed": ready,
        "actual_source_claim_allowed_by_op05": False,
        "rsr_op05_status_ref": status_ref,
        "rsr_op05_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP05_ALLOWED_STATUS_REFS),
        "rsr_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP05_ALLOWED_STATUS_REFS),
        "rsr_op05_ready": ready,
        "rsr_op05_review_session_envelope_accepted": ready,
        "rsr_op05_waiting_for_readiness": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_WAITING_FOR_READINESS_REF,
        "rsr_op05_reviewer_person_not_confirmed": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_REVIEWER_PERSON_NOT_CONFIRMED_REF,
        "rsr_op05_invalid_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF,
        "rsr_op05_body_leak_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_BODY_LEAK_BLOCKED_REF,
        "rsr_op05_ready_for_body_full_packet_transient_request_boundary": ready,
        "rsr_op05_does_not_generate_body_full_packet": True,
        "rsr_op05_does_not_run_actual_local_human_review": True,
        "rsr_op05_does_not_create_receipts_rows_or_disposal": True,
        "rsr_op05_does_not_execute_dmd_or_r52": True,
        "rsr_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP05 local-only review session envelope / reviewer person boundary."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP05")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP05_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP05_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP05")
    for field, count_field in (("reviewer_boundary_forbidden_payload_key_path_refs", "reviewer_boundary_forbidden_payload_key_path_count"), ("reviewer_boundary_body_like_value_path_refs", "reviewer_boundary_body_like_value_path_count"), ("reviewer_boundary_promotion_claim_refs", "reviewer_boundary_promotion_claim_ref_count"), ("reviewer_boundary_reason_refs", "reviewer_boundary_reason_ref_count"), ("reviewer_boundary_blocker_refs", "reviewer_boundary_blocker_ref_count"), ("rsr_op05_allowed_status_refs", "rsr_op05_allowed_status_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP05 {count_field} changed")
    for key in ("review_session_id_bodyfree", "rsr_op05_does_not_generate_body_full_packet", "rsr_op05_does_not_run_actual_local_human_review", "rsr_op05_does_not_create_receipts_rows_or_disposal", "rsr_op05_does_not_execute_dmd_or_r52", "rsr_op05_does_not_start_p5_p6_p8_p7_or_release", "rsr_op05_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP05 required true boundary changed: {key}")
    for key in ("reviewer_is_helper_or_unit_test", "reviewer_free_text_allowed", "reviewer_body_note_allowed", "reviewer_name_material_included", "reviewer_email_material_included", "reviewer_raw_note_material_included", "reviewer_local_path_material_included", "actual_source_claim_allowed_by_op05", "body_full_packet_generated_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP05 execution/reviewer/promotion flag changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP05_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP05_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 implemented/not-yet steps changed")
    flags = [data.get("rsr_op05_review_session_envelope_accepted") is True, data.get("rsr_op05_waiting_for_readiness") is True, data.get("rsr_op05_reviewer_person_not_confirmed") is True, data.get("rsr_op05_invalid_repair_required") is True, data.get("rsr_op05_body_leak_blocked") is True]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 exactly one status flag must be true")
    if data.get("rsr_op05_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_ACCEPTED_BODYFREE_REF:
        if data.get("rsr_op05_ready") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF or data.get("reviewer_boundary_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 accepted status changed")
        for key in ("op04_ready_for_local_only_review_session_envelope", "reviewer_person_ref_present", "reviewer_person_ref_bodyfree", "reviewer_person_ref_shape_valid", "reviewer_is_person_confirmed", "reviewer_role_is_selection_only_review_operator", "selection_only_review_operator_boundary_confirmed"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP05 accepted prerequisite changed: {key}")
    elif data.get("rsr_op05_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_WAITING_FOR_READINESS_REF:
        if data.get("rsr_op05_ready") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_READINESS_BEFORE_REVIEW_SESSION_ENVELOPE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 waiting status changed")
    elif data.get("rsr_op05_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_REVIEWER_PERSON_NOT_CONFIRMED_REF:
        if data.get("rsr_op05_ready") is not False or "reviewer_person_not_confirmed" not in (data.get("reviewer_boundary_blocker_refs") or []):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 reviewer not confirmed status changed")
    elif data.get("rsr_op05_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_BODY_LEAK_BLOCKED_REF:
        if data.get("rsr_op05_ready") is not False or not data.get("reviewer_boundary_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 body leak status changed")
    elif data.get("rsr_op05_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP05_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op05_ready") is not False or not data.get("reviewer_boundary_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 invalid status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP05 status ref is not allowed")
    return True


def _case_ref_shape_valid(value: Any) -> bool:
    raw = str(value or "")
    cleaned = _clean_ref(value, max_length=180)
    if not cleaned:
        return False
    lowered = raw.lower()
    if _ref_has_local_path_shape(raw) or "@" in raw or "file://" in lowered or any(ch.isspace() for ch in raw):
        return False
    forbidden_tokens = (
        "raw_input", "comment_text", "returned_surface", "answer_text", "question_text",
        "draft_question", "body_full_packet", "local_path", "file_path", "absolute_path",
        "relative_path", "sha256", "input_hash", "body_hash", "terminal_output", "stdout", "stderr", "traceback",
    )
    return not any(token in lowered for token in forbidden_tokens)


def _normalize_case_refs(case_ref_values: Sequence[Any] | None) -> tuple[list[str], list[str], list[str]]:
    values = list(case_ref_values or [])
    cleaned_values: list[str] = []
    invalid_refs: list[str] = []
    seen: set[str] = set()
    duplicate_refs: list[str] = []
    for index, value in enumerate(values):
        cleaned = _clean_ref(value, default="", max_length=180)
        if not _case_ref_shape_valid(value):
            invalid_refs.append(f"case_ref_invalid_shape_at_index_{index}")
            continue
        cleaned_values.append(cleaned)
        if cleaned in seen and cleaned not in duplicate_refs:
            duplicate_refs.append(cleaned)
        seen.add(cleaned)
    return cleaned_values, _dedupe_clean_refs(duplicate_refs), _dedupe_clean_refs(invalid_refs)


def build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary(
    *,
    local_only_review_session_envelope: Mapping[str, Any] | None = None,
    rsr_op05_local_only_review_session_envelope: Mapping[str, Any] | None = None,
    case_ref_values: Sequence[Any] | None = None,
    packet_request_ref: Any = None,
    packet_request_material: Mapping[str, Any] | Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP06 24-case body-full packet transient request boundary.

    This material creates only a body-free request boundary. It never generates
    the body-full packet and never runs actual local-only human review.
    """
    op05 = local_only_review_session_envelope if local_only_review_session_envelope is not None else rsr_op05_local_only_review_session_envelope
    if op05 is None:
        op05 = build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op05.get("review_session_id") if isinstance(op05, Mapping) else None))
    try:
        op05_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract(op05) is True
    except ValueError:
        op05_contract_valid = False
    op05_status_ref = _bodyfree_status_ref(op05.get("rsr_op05_status_ref") if isinstance(op05, Mapping) else None, default="rsr_op05_status_missing")
    op05_ready = bool(op05_contract_valid and op05.get("rsr_op05_ready_for_body_full_packet_transient_request_boundary") is True)
    op05_next_step = _bodyfree_status_ref(op05.get("next_required_step") if isinstance(op05, Mapping) else None, default="rsr_op05_next_required_step_missing")
    review_session_envelope_ref = _clean_ref(op05.get("review_session_envelope_ref") if isinstance(op05, Mapping) else None, default="review_session_envelope_ref_missing", max_length=220)
    reviewer_person_ref = _clean_ref(op05.get("reviewer_person_ref") if isinstance(op05, Mapping) else None, default="reviewer_person_ref_missing", max_length=180)
    reviewer_confirmed = bool(op05_contract_valid and op05.get("reviewer_is_person_confirmed") is True)

    cleaned_case_refs, duplicate_refs, invalid_refs = _normalize_case_refs(case_ref_values)
    unique_case_count = len(set(cleaned_case_refs))
    exact_24_unique = (
        len(cleaned_case_refs) == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
        and unique_case_count == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
        and not duplicate_refs
        and not invalid_refs
    )

    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(packet_request_material or {}, path="op06_packet_request_material"), max_length=300)
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(packet_request_material or {}, path="op06_packet_request_material"), max_length=300)
    promo = _dedupe_clean_refs(_promotion_claim_refs(packet_request_material if isinstance(packet_request_material, Mapping) else {}), max_length=300)

    blockers: list[str] = []
    reasons: list[str] = []
    if not op05_contract_valid:
        blockers.append("op05_contract_invalid_before_packet_request")
    if not op05_ready:
        blockers.append("op05_review_session_envelope_not_ready_before_packet_request")
    if not exact_24_unique:
        if len(cleaned_case_refs) != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            blockers.append("case_ref_count_not_24")
        if unique_case_count != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            blockers.append("case_ref_unique_count_not_24")
        if duplicate_refs:
            blockers.append("case_ref_duplicates_detected")
        if invalid_refs:
            blockers.append("case_ref_invalid_shape_detected")
    if forbidden:
        blockers.append("packet_request_forbidden_payload_key_detected")
    if body_like:
        blockers.append("packet_request_body_like_value_detected")
    if promo:
        blockers.append("packet_request_promotion_claim_detected")
    blockers = _dedupe_clean_refs(blockers)

    if forbidden or body_like or promo:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_BODY_LEAK_BLOCKED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODY_FULL_PACKET_REQUEST_BODY_LEAK_BEFORE_RECEIPT_REF
        reasons.append("packet_request_body_leak_or_promotion_blocks_before_packet_generation_receipt")
    elif not op05_ready:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_WAITING_FOR_SESSION_ENVELOPE_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_REVIEW_SESSION_ENVELOPE_BEFORE_PACKET_REQUEST_REF
        reasons.append("review_session_envelope_required_before_packet_request")
    elif not exact_24_unique:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_CASE_MANIFEST_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_24_CASE_BODYFREE_CASE_REF_MANIFEST_BEFORE_PACKET_REQUEST_REF
        reasons.append("twenty_four_unique_bodyfree_case_refs_required_before_packet_request")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_ACCEPTED_BODYFREE_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF
        reasons.append("packet_request_bodyfree_boundary_ready_for_generation_receipt_intake")
    ready = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_ACCEPTED_BODYFREE_REF
    packet_request_ref_out = _clean_ref(
        packet_request_ref,
        default=f"rsr_op06_packet_request_{session_id}_24_cases_bodyfree" if ready else "packet_request_ref_not_materialized_waiting_or_repair",
        max_length=220,
    )

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_contract_valid": op05_contract_valid,
        "op05_status_ref": op05_status_ref,
        "op05_ready_for_body_full_packet_transient_request_boundary": op05_ready,
        "op05_next_required_step": op05_next_step,
        "review_session_envelope_ref": review_session_envelope_ref,
        "reviewer_person_ref": reviewer_person_ref,
        "reviewer_is_person_confirmed": reviewer_confirmed,
        "expected_case_count": P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "case_ref_values": cleaned_case_refs,
        "case_ref_count": len(cleaned_case_refs),
        "case_ref_unique_count": unique_case_count,
        "case_ref_duplicate_refs": duplicate_refs,
        "case_ref_duplicate_ref_count": len(duplicate_refs),
        "case_ref_invalid_refs": invalid_refs,
        "case_ref_invalid_ref_count": len(invalid_refs),
        "case_ref_manifest_bodyfree": True,
        "case_ref_manifest_exactly_24_unique": exact_24_unique,
        "packet_request_ref": packet_request_ref_out,
        "packet_request_ref_bodyfree": True,
        "packet_request_created_here": ready,
        "packet_generated_here": False,
        "body_full_packet_content_included": False,
        "transient_body_full_packet_required": True,
        "local_only_transient_boundary_confirmed": ready,
        "external_export_allowed": False,
        "persisted_to_repo_allowed": False,
        "packet_request_local_path_included": False,
        "packet_request_body_hash_included": False,
        "packet_request_terminal_output_body_included": False,
        "packet_request_forbidden_payload_key_path_refs": forbidden,
        "packet_request_forbidden_payload_key_path_count": len(forbidden),
        "packet_request_body_like_value_path_refs": body_like,
        "packet_request_body_like_value_path_count": len(body_like),
        "packet_request_promotion_claim_refs": promo,
        "packet_request_promotion_claim_ref_count": len(promo),
        "packet_request_reason_refs": _dedupe_clean_refs(reasons),
        "packet_request_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "packet_request_blocker_refs": blockers,
        "packet_request_blocker_ref_count": len(blockers),
        "rsr_op06_status_ref": status_ref,
        "rsr_op06_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP06_ALLOWED_STATUS_REFS),
        "rsr_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP06_ALLOWED_STATUS_REFS),
        "rsr_op06_ready": ready,
        "rsr_op06_packet_request_accepted": ready,
        "rsr_op06_waiting_for_session_envelope": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_WAITING_FOR_SESSION_ENVELOPE_REF,
        "rsr_op06_case_manifest_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_CASE_MANIFEST_REPAIR_REQUIRED_REF,
        "rsr_op06_body_leak_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_BODY_LEAK_BLOCKED_REF,
        "rsr_op06_ready_for_body_full_packet_generation_receipt_intake": ready,
        "rsr_op06_does_not_generate_body_full_packet": True,
        "rsr_op06_does_not_run_actual_local_human_review": True,
        "rsr_op06_does_not_create_receipts_rows_or_disposal": True,
        "rsr_op06_does_not_execute_dmd_or_r52": True,
        "rsr_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP06 24-case packet request boundary contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP06")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP06_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP06_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP06")
    for field, count_field in (("case_ref_duplicate_refs", "case_ref_duplicate_ref_count"), ("case_ref_invalid_refs", "case_ref_invalid_ref_count"), ("packet_request_forbidden_payload_key_path_refs", "packet_request_forbidden_payload_key_path_count"), ("packet_request_body_like_value_path_refs", "packet_request_body_like_value_path_count"), ("packet_request_promotion_claim_refs", "packet_request_promotion_claim_ref_count"), ("packet_request_reason_refs", "packet_request_reason_ref_count"), ("packet_request_blocker_refs", "packet_request_blocker_ref_count"), ("rsr_op06_allowed_status_refs", "rsr_op06_allowed_status_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP06 {count_field} changed")
    for key in ("case_ref_manifest_bodyfree", "packet_request_ref_bodyfree", "transient_body_full_packet_required", "rsr_op06_does_not_generate_body_full_packet", "rsr_op06_does_not_run_actual_local_human_review", "rsr_op06_does_not_create_receipts_rows_or_disposal", "rsr_op06_does_not_execute_dmd_or_r52", "rsr_op06_does_not_start_p5_p6_p8_p7_or_release", "rsr_op06_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP06 required true boundary changed: {key}")
    for key in ("packet_generated_here", "body_full_packet_content_included", "external_export_allowed", "persisted_to_repo_allowed", "packet_request_local_path_included", "packet_request_body_hash_included", "packet_request_terminal_output_body_included", "body_full_packet_generated_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP06 execution/promotion flag changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP06_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP06_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 implemented/not-yet steps changed")
    flags = [data.get("rsr_op06_packet_request_accepted") is True, data.get("rsr_op06_waiting_for_session_envelope") is True, data.get("rsr_op06_case_manifest_repair_required") is True, data.get("rsr_op06_body_leak_blocked") is True]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 exactly one status flag must be true")
    if data.get("rsr_op06_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_ACCEPTED_BODYFREE_REF:
        if data.get("rsr_op06_ready") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF or data.get("packet_request_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 accepted status changed")
        if data.get("case_ref_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or data.get("case_ref_unique_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or data.get("case_ref_manifest_exactly_24_unique") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 accepted case manifest changed")
        if data.get("packet_request_created_here") is not True or data.get("local_only_transient_boundary_confirmed") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 request boundary changed")
    elif data.get("rsr_op06_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_WAITING_FOR_SESSION_ENVELOPE_REF:
        if data.get("rsr_op06_ready") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_REVIEW_SESSION_ENVELOPE_BEFORE_PACKET_REQUEST_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 waiting status changed")
    elif data.get("rsr_op06_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_CASE_MANIFEST_REPAIR_REQUIRED_REF:
        if data.get("rsr_op06_ready") is not False or not data.get("packet_request_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 case repair status changed")
    elif data.get("rsr_op06_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP06_STATUS_BODY_LEAK_BLOCKED_REF:
        if data.get("rsr_op06_ready") is not False or not data.get("packet_request_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 body leak status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP06 status ref is not allowed")
    return True


def _evaluate_packet_generation_receipt(
    receipt: Mapping[str, Any] | None,
    *,
    expected_review_session_id: str,
    expected_packet_request_ref: str,
) -> tuple[bool, bool, bool, list[str], list[str], list[str], list[str], list[str], list[str]]:
    if not isinstance(receipt, Mapping):
        return False, False, False, ["packet_generation_receipt_missing"], [], [], [], [], []
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(receipt, path="packet_generation_receipt"), max_length=300)
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(receipt, path="packet_generation_receipt"), max_length=300)
    promo = _dedupe_clean_refs([f"packet_generation_receipt.{ref}" for ref in _promotion_claim_refs(receipt)], max_length=300)
    blockers: list[str] = []
    export_blockers: list[str] = []
    if receipt.get("schema_version") != P7_R54_AHR_POST_DHR09_RSR_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION:
        blockers.append("packet_generation_receipt_schema_invalid")
    if not _clean_ref(receipt.get("packet_generation_receipt_ref"), default=""):
        blockers.append("packet_generation_receipt_ref_missing")
    if _clean_ref(receipt.get("packet_request_ref"), default="", max_length=220) != expected_packet_request_ref:
        blockers.append("packet_generation_receipt_packet_request_ref_mismatch")
    if _safe_review_session_id(receipt.get("review_session_id")) != expected_review_session_id:
        blockers.append("packet_generation_receipt_review_session_mismatch")
    if _safe_int_value(receipt.get("generated_case_count")) != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
        blockers.append("packet_generation_receipt_generated_case_count_not_24")
    if receipt.get("generated_local_only") is not True:
        blockers.append("packet_generation_receipt_generated_local_only_not_true")
    if receipt.get("persisted_to_repo") is not False:
        export_blockers.append("packet_generation_receipt_persisted_to_repo_not_false")
    if receipt.get("external_export_performed") is not False:
        export_blockers.append("packet_generation_receipt_external_export_performed_not_false")
    for key in ("raw_input_included", "comment_text_body_included", "returned_surface_body_included", "local_path_included", "body_hash_included", "terminal_output_body_included"):
        if receipt.get(key) is not False:
            blockers.append(f"packet_generation_receipt_{key}_must_be_false")
    if receipt.get("body_free") is not True:
        blockers.append("packet_generation_receipt_body_free_not_true")
    if forbidden:
        blockers.append("packet_generation_receipt_forbidden_payload_key_detected")
    if body_like:
        blockers.append("packet_generation_receipt_body_like_value_detected")
    if promo:
        blockers.append("packet_generation_receipt_promotion_claim_detected")
    return not blockers and not export_blockers, bool(export_blockers), True, _dedupe_clean_refs(blockers), _dedupe_clean_refs(export_blockers), forbidden, body_like, promo, []


def build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
    *,
    body_full_packet_transient_request_boundary: Mapping[str, Any] | None = None,
    rsr_op06_body_full_packet_transient_request_boundary: Mapping[str, Any] | None = None,
    body_full_packet_generation_receipt: Mapping[str, Any] | None = None,
    packet_generation_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP07 packet generation receipt / export denylist scan intake."""
    op06 = body_full_packet_transient_request_boundary if body_full_packet_transient_request_boundary is not None else rsr_op06_body_full_packet_transient_request_boundary
    if op06 is None:
        op06 = build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary(review_session_id=review_session_id)
    receipt = body_full_packet_generation_receipt if body_full_packet_generation_receipt is not None else packet_generation_receipt
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op06.get("review_session_id") if isinstance(op06, Mapping) else None))
    try:
        op06_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract(op06) is True
    except ValueError:
        op06_contract_valid = False
    op06_status_ref = _bodyfree_status_ref(op06.get("rsr_op06_status_ref") if isinstance(op06, Mapping) else None, default="rsr_op06_status_missing")
    op06_ready = bool(op06_contract_valid and op06.get("rsr_op06_ready_for_body_full_packet_generation_receipt_intake") is True)
    op06_next_step = _bodyfree_status_ref(op06.get("next_required_step") if isinstance(op06, Mapping) else None, default="rsr_op06_next_required_step_missing")
    op06_packet_request_ref = _clean_ref(op06.get("packet_request_ref") if isinstance(op06, Mapping) else None, default="packet_request_ref_missing", max_length=220)
    op06_case_count = _safe_int_value(op06.get("case_ref_count") if isinstance(op06, Mapping) else 0)

    accepted, export_blocked, present, blockers, export_blockers, forbidden, body_like, promo, _ = _evaluate_packet_generation_receipt(
        receipt,
        expected_review_session_id=session_id,
        expected_packet_request_ref=op06_packet_request_ref,
    )
    receipt_contract_valid = bool(op06_ready and accepted)
    if not op06_ready:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_REQUEST_BOUNDARY_BEFORE_RECEIPT_REF
        reasons = ["packet_request_boundary_required_before_packet_generation_receipt_intake"]
        blockers = _dedupe_clean_refs([*blockers, "op06_packet_request_boundary_not_ready_before_receipt_intake"])
    elif not present:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_GENERATION_RECEIPT_REF
        reasons = ["packet_generation_receipt_required_after_packet_request_boundary"]
    elif export_blocked:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_EXPORT_OR_PERSISTENCE_BLOCKED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_PACKET_EXPORT_OR_REPO_PERSISTENCE_REF
        reasons = ["packet_export_or_repo_persistence_blocks_actual_review_continue"]
    elif not accepted:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_INVALID_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_BODY_FULL_PACKET_GENERATION_RECEIPT_REF
        reasons = ["packet_generation_receipt_repair_required_before_selection_form_contract"]
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_ACCEPTED_BODYFREE_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF
        reasons = ["packet_generation_receipt_bodyfree_accepted_for_selection_form_contract"]
    ready = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_ACCEPTED_BODYFREE_REF
    receipt_mapping = receipt if isinstance(receipt, Mapping) else {}

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op07_packet_generation_receipt_export_denylist_scan_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_contract_valid": op06_contract_valid,
        "op06_status_ref": op06_status_ref,
        "op06_ready_for_body_full_packet_generation_receipt_intake": op06_ready,
        "op06_next_required_step": op06_next_step,
        "op06_packet_request_ref": op06_packet_request_ref,
        "op06_case_ref_count": op06_case_count,
        "packet_generation_receipt_present": present,
        "packet_generation_receipt_contract_valid": receipt_contract_valid,
        "packet_generation_receipt_schema_version": _clean_ref(receipt_mapping.get("schema_version"), default="packet_generation_receipt_schema_missing", max_length=220),
        "packet_generation_receipt_ref": _clean_ref(receipt_mapping.get("packet_generation_receipt_ref"), default="packet_generation_receipt_ref_missing", max_length=220),
        "packet_generation_receipt_packet_request_ref": _clean_ref(receipt_mapping.get("packet_request_ref"), default="packet_request_ref_missing", max_length=220),
        "packet_generation_receipt_review_session_id": _safe_review_session_id(receipt_mapping.get("review_session_id")) if present else "review_session_id_missing",
        "packet_generation_receipt_generated_case_count": _safe_int_value(receipt_mapping.get("generated_case_count")),
        "packet_generation_receipt_generated_local_only": receipt_mapping.get("generated_local_only") is True,
        "packet_generation_receipt_persisted_to_repo": receipt_mapping.get("persisted_to_repo") is True,
        "packet_generation_receipt_external_export_performed": receipt_mapping.get("external_export_performed") is True,
        "packet_generation_receipt_raw_input_included": receipt_mapping.get("raw_input_included") is True,
        "packet_generation_receipt_comment_text_body_included": receipt_mapping.get("comment_text_body_included") is True,
        "packet_generation_receipt_returned_surface_body_included": receipt_mapping.get("returned_surface_body_included") is True,
        "packet_generation_receipt_local_path_included": receipt_mapping.get("local_path_included") is True,
        "packet_generation_receipt_body_hash_included": receipt_mapping.get("body_hash_included") is True,
        "packet_generation_receipt_terminal_output_body_included": receipt_mapping.get("terminal_output_body_included") is True,
        "packet_generation_receipt_body_free": receipt_mapping.get("body_free") is True,
        "packet_generation_receipt_forbidden_payload_key_path_refs": forbidden,
        "packet_generation_receipt_forbidden_payload_key_path_count": len(forbidden),
        "packet_generation_receipt_body_like_value_path_refs": body_like,
        "packet_generation_receipt_body_like_value_path_count": len(body_like),
        "packet_generation_receipt_promotion_claim_refs": promo,
        "packet_generation_receipt_promotion_claim_ref_count": len(promo),
        "packet_generation_receipt_export_or_persistence_blocker_refs": export_blockers,
        "packet_generation_receipt_export_or_persistence_blocker_ref_count": len(export_blockers),
        "packet_generation_receipt_reason_refs": _dedupe_clean_refs(reasons),
        "packet_generation_receipt_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "packet_generation_receipt_blocker_refs": _dedupe_clean_refs(blockers),
        "packet_generation_receipt_blocker_ref_count": len(_dedupe_clean_refs(blockers)),
        "rsr_op07_status_ref": status_ref,
        "rsr_op07_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP07_ALLOWED_STATUS_REFS),
        "rsr_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP07_ALLOWED_STATUS_REFS),
        "rsr_op07_ready": ready,
        "rsr_op07_packet_generation_receipt_accepted": ready,
        "rsr_op07_missing_waiting": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF,
        "rsr_op07_invalid_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_INVALID_REPAIR_REQUIRED_REF,
        "rsr_op07_export_or_persistence_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_EXPORT_OR_PERSISTENCE_BLOCKED_REF,
        "rsr_op07_ready_for_selection_only_reviewer_form_rating_axis_contract_freeze": ready,
        "packet_generation_receipt_accepted_by_rsr_op07": ready,
        "packet_generation_receipt_accepted_but_actual_review_not_executed": ready,
        "rsr_op07_does_not_generate_body_full_packet_here": True,
        "rsr_op07_does_not_run_actual_local_human_review": True,
        "rsr_op07_does_not_create_actual_operation_receipt_rows_or_disposal": True,
        "rsr_op07_does_not_execute_dmd_or_r52": True,
        "rsr_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP07 packet generation receipt/export denylist intake contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP07")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP07_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP07_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP07")
    for field, count_field in (("packet_generation_receipt_forbidden_payload_key_path_refs", "packet_generation_receipt_forbidden_payload_key_path_count"), ("packet_generation_receipt_body_like_value_path_refs", "packet_generation_receipt_body_like_value_path_count"), ("packet_generation_receipt_promotion_claim_refs", "packet_generation_receipt_promotion_claim_ref_count"), ("packet_generation_receipt_export_or_persistence_blocker_refs", "packet_generation_receipt_export_or_persistence_blocker_ref_count"), ("packet_generation_receipt_reason_refs", "packet_generation_receipt_reason_ref_count"), ("packet_generation_receipt_blocker_refs", "packet_generation_receipt_blocker_ref_count"), ("rsr_op07_allowed_status_refs", "rsr_op07_allowed_status_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP07 {count_field} changed")
    for key in ("rsr_op07_does_not_generate_body_full_packet_here", "rsr_op07_does_not_run_actual_local_human_review", "rsr_op07_does_not_create_actual_operation_receipt_rows_or_disposal", "rsr_op07_does_not_execute_dmd_or_r52", "rsr_op07_does_not_start_p5_p6_p8_p7_or_release", "rsr_op07_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP07 required true boundary changed: {key}")
    for key in ("body_full_packet_generated_here", "body_full_packet_generation_run_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP07 execution/promotion flag changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP07_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP07_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 implemented/not-yet steps changed")
    flags = [data.get("rsr_op07_packet_generation_receipt_accepted") is True, data.get("rsr_op07_missing_waiting") is True, data.get("rsr_op07_invalid_repair_required") is True, data.get("rsr_op07_export_or_persistence_blocked") is True]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 exactly one status flag must be true")
    if data.get("rsr_op07_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_ACCEPTED_BODYFREE_REF:
        if data.get("rsr_op07_ready") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF or data.get("packet_generation_receipt_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 accepted status changed")
        for key in ("op06_ready_for_body_full_packet_generation_receipt_intake", "packet_generation_receipt_present", "packet_generation_receipt_contract_valid", "packet_generation_receipt_generated_local_only", "packet_generation_receipt_body_free", "packet_generation_receipt_accepted_by_rsr_op07", "packet_generation_receipt_accepted_but_actual_review_not_executed"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP07 accepted prerequisite changed: {key}")
        for key in ("packet_generation_receipt_persisted_to_repo", "packet_generation_receipt_external_export_performed", "packet_generation_receipt_raw_input_included", "packet_generation_receipt_comment_text_body_included", "packet_generation_receipt_returned_surface_body_included", "packet_generation_receipt_local_path_included", "packet_generation_receipt_body_hash_included", "packet_generation_receipt_terminal_output_body_included"):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP07 accepted false marker changed: {key}")
        if data.get("packet_generation_receipt_generated_case_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 accepted case count changed")
    elif data.get("rsr_op07_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_MISSING_WAITING_REF:
        if data.get("rsr_op07_ready") is not False or data.get("next_required_step") not in (P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_REQUEST_BOUNDARY_BEFORE_RECEIPT_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_BODY_FULL_PACKET_GENERATION_RECEIPT_REF):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 waiting status changed")
    elif data.get("rsr_op07_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op07_ready") is not False or not data.get("packet_generation_receipt_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 invalid status changed")
    elif data.get("rsr_op07_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP07_STATUS_EXPORT_OR_PERSISTENCE_BLOCKED_REF:
        if data.get("rsr_op07_ready") is not False or not data.get("packet_generation_receipt_export_or_persistence_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 export blocked status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP07 status ref is not allowed")
    return True


def build_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze(
    *,
    packet_generation_receipt_intake: Mapping[str, Any] | None = None,
    body_full_packet_generation_receipt_intake: Mapping[str, Any] | None = None,
    selection_form_contract_material: Mapping[str, Any] | Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP08 selection-only reviewer form and rating axis contract freeze."""

    op07 = packet_generation_receipt_intake if packet_generation_receipt_intake is not None else body_full_packet_generation_receipt_intake
    if op07 is None:
        op07 = build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake(
            review_session_id=review_session_id
        )
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op07.get("review_session_id") if isinstance(op07, Mapping) else None))
    try:
        op07_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract(op07) is True
    except ValueError:
        op07_contract_valid = False
    op07_status_ref = _bodyfree_status_ref(op07.get("rsr_op07_status_ref") if isinstance(op07, Mapping) else None, default="rsr_op07_status_missing")
    op07_ready = bool(op07_contract_valid and op07.get("rsr_op07_ready_for_selection_only_reviewer_form_rating_axis_contract_freeze") is True)
    op07_next_step = _bodyfree_status_ref(op07.get("next_required_step") if isinstance(op07, Mapping) else None, default="rsr_op07_next_required_step_missing")
    op07_receipt_accepted = bool(op07_contract_valid and op07.get("rsr_op07_packet_generation_receipt_accepted") is True)
    op07_receipt_no_review = bool(op07_contract_valid and op07.get("packet_generation_receipt_accepted_but_actual_review_not_executed") is True)

    material_present = selection_form_contract_material is not None
    scan_material: Any = selection_form_contract_material if material_present else {}
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(scan_material, path="op08_selection_form_contract"))
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(scan_material, path="op08_selection_form_contract"))
    promo = _dedupe_clean_refs(_promotion_claim_refs(scan_material if isinstance(scan_material, Mapping) else {}))
    material_body_free = not material_present or (isinstance(scan_material, Mapping) and scan_material.get("body_free") is True)

    blockers: list[str] = []
    reasons: list[str] = []
    if not op07_ready:
        blockers.append("op07_packet_generation_receipt_not_ready_for_selection_form_contract")
    if material_present and material_body_free is not True:
        blockers.append("selection_form_contract_material_body_free_not_true")
    if forbidden:
        blockers.append("selection_form_forbidden_payload_key_detected")
    if body_like:
        blockers.append("selection_form_body_like_value_detected")
    if promo:
        blockers.append("selection_form_promotion_claim_detected")
    blockers = _dedupe_clean_refs(blockers)

    if forbidden or body_like or promo:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_SELECTION_ONLY_FORM_BODY_LEAK_BEFORE_LIFECYCLE_REF
        reasons.append("selection_only_form_contract_body_leak_blocks_before_lifecycle_capture")
    elif not op07_ready:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_WAITING_FOR_PACKET_GENERATION_RECEIPT_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_PACKET_GENERATION_RECEIPT_BEFORE_SELECTION_FORM_CONTRACT_REF
        reasons.append("packet_generation_receipt_required_before_selection_only_form_contract")
    elif blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_INVALID_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SELECTION_ONLY_REVIEWER_FORM_CONTRACT_REF
        reasons.append("selection_only_form_contract_repair_required_before_lifecycle_capture")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_ACCEPTED_BODYFREE_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF
        reasons.append("selection_only_form_rating_axis_contract_bodyfree_accepted")
    ready = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_ACCEPTED_BODYFREE_REF
    axis_targets = dict(P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS)
    axis_threshold_refs = [f"{axis}:{threshold:.2f}" for axis, threshold in axis_targets.items()]
    form_ref = _clean_ref(f"rsr_op08_selection_only_form_contract_{session_id}", max_length=240)

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op08_selection_only_form_rating_axis_contract_freeze_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_contract_valid": op07_contract_valid,
        "op07_status_ref": op07_status_ref,
        "op07_ready_for_selection_only_reviewer_form_rating_axis_contract_freeze": op07_ready,
        "op07_next_required_step": op07_next_step,
        "op07_packet_generation_receipt_accepted": op07_receipt_accepted,
        "op07_packet_generation_receipt_accepted_but_actual_review_not_executed": op07_receipt_no_review,
        "selection_form_contract_ref": form_ref,
        "selection_form_contract_ref_bodyfree": True,
        "selection_form_contract_material_present": material_present,
        "selection_form_contract_material_body_free": material_body_free,
        "rating_axis_target_refs": list(axis_targets.keys()),
        "rating_axis_target_ref_count": len(axis_targets),
        "rating_axis_target_threshold_refs": axis_threshold_refs,
        "rating_axis_target_threshold_ref_count": len(axis_threshold_refs),
        "rating_axis_targets_match_elr_contract": True,
        "score_option_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP08_SCORE_OPTION_REFS),
        "score_option_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP08_SCORE_OPTION_REFS),
        "score_options_allowed_scalar_only": True,
        "question_need_class_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP08_QUESTION_NEED_CLASS_REFS),
        "question_need_class_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP08_QUESTION_NEED_CLASS_REFS),
        "selection_only_form_required": True,
        "selection_only_form_used_for_contract": True,
        "selection_only_row_conversion_contract_ready": ready,
        "question_need_observation_material_only": True,
        "p8_design_material_candidate_only": True,
        "question_text_materialized": False,
        "draft_question_text_materialized": False,
        "p8_question_spec_created": False,
        "p8_question_design_started_here": False,
        "reviewer_free_text_allowed": False,
        "reviewer_body_note_allowed": False,
        "reviewer_name_material_included": False,
        "reviewer_email_material_included": False,
        "reviewer_raw_note_material_included": False,
        "reviewer_local_path_material_included": False,
        "body_full_packet_body_allowed_in_form": False,
        "raw_input_allowed_in_form": False,
        "returned_surface_body_allowed_in_form": False,
        "question_text_allowed_in_form": False,
        "draft_question_text_allowed_in_form": False,
        "selection_form_forbidden_payload_key_path_refs": forbidden,
        "selection_form_forbidden_payload_key_path_count": len(forbidden),
        "selection_form_body_like_value_path_refs": body_like,
        "selection_form_body_like_value_path_count": len(body_like),
        "selection_form_promotion_claim_refs": promo,
        "selection_form_promotion_claim_ref_count": len(promo),
        "selection_form_reason_refs": _dedupe_clean_refs(reasons),
        "selection_form_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "selection_form_blocker_refs": blockers,
        "selection_form_blocker_ref_count": len(blockers),
        "rsr_op08_status_ref": status_ref,
        "rsr_op08_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP08_ALLOWED_STATUS_REFS),
        "rsr_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP08_ALLOWED_STATUS_REFS),
        "rsr_op08_ready": ready,
        "rsr_op08_selection_only_form_contract_accepted": ready,
        "rsr_op08_waiting_for_packet_generation_receipt": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_WAITING_FOR_PACKET_GENERATION_RECEIPT_REF,
        "rsr_op08_invalid_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_INVALID_REPAIR_REQUIRED_REF,
        "rsr_op08_body_leak_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF,
        "rsr_op08_ready_for_actual_local_only_review_lifecycle_state_capture": ready,
        "selection_only_form_contract_accepted_but_no_review_rows_created": ready,
        "rsr_op08_does_not_run_actual_local_human_review": True,
        "rsr_op08_does_not_create_actual_operation_receipt_rows_or_disposal": True,
        "rsr_op08_does_not_materialize_question_text_or_p8_spec": True,
        "rsr_op08_does_not_execute_dmd_or_r52": True,
        "rsr_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP08 selection-only reviewer form/rating axis contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP08")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP08_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP08_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP08")
    for field, count_field in (("rating_axis_target_refs", "rating_axis_target_ref_count"), ("rating_axis_target_threshold_refs", "rating_axis_target_threshold_ref_count"), ("score_option_refs", "score_option_ref_count"), ("question_need_class_refs", "question_need_class_ref_count"), ("selection_form_forbidden_payload_key_path_refs", "selection_form_forbidden_payload_key_path_count"), ("selection_form_body_like_value_path_refs", "selection_form_body_like_value_path_count"), ("selection_form_promotion_claim_refs", "selection_form_promotion_claim_ref_count"), ("selection_form_reason_refs", "selection_form_reason_ref_count"), ("selection_form_blocker_refs", "selection_form_blocker_ref_count"), ("rsr_op08_allowed_status_refs", "rsr_op08_allowed_status_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP08 {count_field} changed")
    for key in ("selection_only_form_required", "selection_only_form_used_for_contract", "question_need_observation_material_only", "p8_design_material_candidate_only", "rating_axis_targets_match_elr_contract", "score_options_allowed_scalar_only", "rsr_op08_does_not_run_actual_local_human_review", "rsr_op08_does_not_create_actual_operation_receipt_rows_or_disposal", "rsr_op08_does_not_materialize_question_text_or_p8_spec", "rsr_op08_does_not_execute_dmd_or_r52", "rsr_op08_does_not_start_p5_p6_p8_p7_or_release", "rsr_op08_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP08 required true boundary changed: {key}")
    for key in ("question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here", "reviewer_free_text_allowed", "reviewer_body_note_allowed", "reviewer_name_material_included", "reviewer_email_material_included", "reviewer_raw_note_material_included", "reviewer_local_path_material_included", "body_full_packet_body_allowed_in_form", "raw_input_allowed_in_form", "returned_surface_body_allowed_in_form", "question_text_allowed_in_form", "draft_question_text_allowed_in_form", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_question_need_observation_rows_materialized_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP08 false boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP08_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP08_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 implemented/not-yet steps changed")
    if tuple(data.get("rating_axis_target_refs") or ()) != tuple(P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS.keys()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 rating axes changed")
    if tuple(data.get("score_option_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP08_SCORE_OPTION_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 score options changed")
    if tuple(data.get("question_need_class_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP08_QUESTION_NEED_CLASS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 question need classes changed")
    flags = [data.get("rsr_op08_selection_only_form_contract_accepted") is True, data.get("rsr_op08_waiting_for_packet_generation_receipt") is True, data.get("rsr_op08_invalid_repair_required") is True, data.get("rsr_op08_body_leak_blocked") is True]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 exactly one status flag must be true")
    if data.get("rsr_op08_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_ACCEPTED_BODYFREE_REF:
        if data.get("rsr_op08_ready") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF or data.get("selection_form_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 accepted status changed")
        if data.get("selection_only_row_conversion_contract_ready") is not True or data.get("op07_packet_generation_receipt_accepted_but_actual_review_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 accepted prerequisite changed")
    elif data.get("rsr_op08_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_WAITING_FOR_PACKET_GENERATION_RECEIPT_REF:
        if data.get("rsr_op08_ready") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_PACKET_GENERATION_RECEIPT_BEFORE_SELECTION_FORM_CONTRACT_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 waiting status changed")
    elif data.get("rsr_op08_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op08_ready") is not False or not data.get("selection_form_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 invalid status changed")
    elif data.get("rsr_op08_status_ref") == P7_R54_AHR_POST_DHR09_RSR_OP08_STATUS_BODY_LEAK_BLOCKED_REF:
        if data.get("rsr_op08_ready") is not False or not data.get("selection_form_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 body leak status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP08 status ref is not allowed")
    return True


def _normalize_review_lifecycle_status(value: Any) -> str:
    return _clean_ref(value, default=P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_READY_TO_START_REF, max_length=220)


def build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture(
    *,
    selection_only_reviewer_form_contract: Mapping[str, Any] | None = None,
    selection_form_contract_freeze: Mapping[str, Any] | None = None,
    lifecycle_status_ref: Any = None,
    review_lifecycle_status_ref: Any = None,
    lifecycle_state_material: Mapping[str, Any] | Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP09 body-free actual local-only review lifecycle state capture."""

    op08 = selection_only_reviewer_form_contract if selection_only_reviewer_form_contract is not None else selection_form_contract_freeze
    if op08 is None:
        op08 = build_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze(
            review_session_id=review_session_id
        )
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op08.get("review_session_id") if isinstance(op08, Mapping) else None))
    try:
        op08_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract(op08) is True
    except ValueError:
        op08_contract_valid = False
    op08_status_ref = _bodyfree_status_ref(op08.get("rsr_op08_status_ref") if isinstance(op08, Mapping) else None, default="rsr_op08_status_missing")
    op08_ready = bool(op08_contract_valid and op08.get("rsr_op08_ready_for_actual_local_only_review_lifecycle_state_capture") is True)
    op08_next_step = _bodyfree_status_ref(op08.get("next_required_step") if isinstance(op08, Mapping) else None, default="rsr_op08_next_required_step_missing")
    op08_accepted = bool(op08_contract_valid and op08.get("rsr_op08_selection_only_form_contract_accepted") is True)

    material_present = lifecycle_state_material is not None
    scan_material: Any = lifecycle_state_material if material_present else {}
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(scan_material, path="op09_lifecycle_state"))
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(scan_material, path="op09_lifecycle_state"))
    promo = _dedupe_clean_refs(_promotion_claim_refs(scan_material if isinstance(scan_material, Mapping) else {}))
    material_body_free = not material_present or (isinstance(scan_material, Mapping) and scan_material.get("body_free") is True)
    requested_value = lifecycle_status_ref if lifecycle_status_ref is not None else review_lifecycle_status_ref
    if requested_value is None and isinstance(scan_material, Mapping):
        requested_value = scan_material.get("lifecycle_status_ref") or scan_material.get("review_lifecycle_status_ref")
    requested_status = _normalize_review_lifecycle_status(requested_value)

    blockers: list[str] = []
    reasons: list[str] = []
    if not op08_ready:
        blockers.append("op08_selection_form_contract_not_ready_for_lifecycle_capture")
    if material_present and material_body_free is not True:
        blockers.append("lifecycle_state_material_body_free_not_true")
    if requested_status not in P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_REFS:
        blockers.append("review_lifecycle_status_ref_not_allowed")
    if forbidden:
        blockers.append("lifecycle_state_forbidden_payload_key_detected")
    if body_like:
        blockers.append("lifecycle_state_body_like_value_detected")
    if promo:
        blockers.append("lifecycle_state_promotion_claim_detected")
    blockers = _dedupe_clean_refs(blockers)

    if forbidden or body_like or promo:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_BODY_LEAK_BLOCKED_REF
        lifecycle_status = P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEW_LIFECYCLE_BODY_LEAK_BEFORE_RECEIPT_REF
        reasons.append("review_lifecycle_state_body_leak_blocks_before_receipt")
    elif not op08_ready:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_WAITING_FOR_SELECTION_FORM_CONTRACT_REF
        lifecycle_status = P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_SELECTION_FORM_CONTRACT_BEFORE_LIFECYCLE_CAPTURE_REF
        reasons.append("selection_only_form_contract_required_before_lifecycle_capture")
    elif blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_INVALID_REPAIR_REQUIRED_REF
        lifecycle_status = P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF
        next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_REVIEW_LIFECYCLE_STATE_CAPTURE_REF
        reasons.append("review_lifecycle_state_repair_required_before_receipt")
    else:
        lifecycle_status = requested_status
        status_ref = lifecycle_status
        if lifecycle_status == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF:
            next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_ACTUAL_OPERATION_RECEIPT_AFTER_COMPLETED_LIFECYCLE_REF
            reasons.append("actual_review_lifecycle_completed_but_actual_operation_receipt_required")
        elif lifecycle_status == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_ABORTED_REPAIR_REQUIRED_REF:
            next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_ABORTED_ACTUAL_LOCAL_ONLY_REVIEW_LIFECYCLE_REF
            reasons.append("actual_review_lifecycle_aborted_requires_repair_or_retry")
        else:
            next_required_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_START_OR_CONTINUE_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_LOCAL_ONLY_REF
            reasons.append("actual_review_lifecycle_state_captured_bodyfree_without_helper_execution")
    completed = status_ref == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF
    captured = status_ref in P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_REFS
    ready = captured

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP09_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op08_contract_valid": op08_contract_valid,
        "op08_status_ref": op08_status_ref,
        "op08_ready_for_actual_local_only_review_lifecycle_state_capture": op08_ready,
        "op08_next_required_step": op08_next_step,
        "op08_selection_only_form_contract_accepted": op08_accepted,
        "lifecycle_state_material_present": material_present,
        "lifecycle_state_material_body_free": material_body_free,
        "lifecycle_status_requested_ref": requested_status,
        "lifecycle_status_ref": lifecycle_status,
        "lifecycle_status_allowed_refs": list(P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_REFS),
        "lifecycle_status_allowed_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_REFS),
        "lifecycle_state_forbidden_payload_key_path_refs": forbidden,
        "lifecycle_state_forbidden_payload_key_path_count": len(forbidden),
        "lifecycle_state_body_like_value_path_refs": body_like,
        "lifecycle_state_body_like_value_path_count": len(body_like),
        "lifecycle_state_promotion_claim_refs": promo,
        "lifecycle_state_promotion_claim_ref_count": len(promo),
        "lifecycle_state_reason_refs": _dedupe_clean_refs(reasons),
        "lifecycle_state_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "lifecycle_state_blocker_refs": blockers,
        "lifecycle_state_blocker_ref_count": len(blockers),
        "rsr_op09_status_ref": status_ref,
        "rsr_op09_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP09_ALLOWED_STATUS_REFS),
        "rsr_op09_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP09_ALLOWED_STATUS_REFS),
        "rsr_op09_ready": ready,
        "rsr_op09_waiting_for_selection_form_contract": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_WAITING_FOR_SELECTION_FORM_CONTRACT_REF,
        "rsr_op09_invalid_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_INVALID_REPAIR_REQUIRED_REF,
        "rsr_op09_body_leak_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_BODY_LEAK_BLOCKED_REF,
        "rsr_op09_review_operation_not_started": lifecycle_status == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF and captured,
        "rsr_op09_review_operation_ready_to_start": lifecycle_status == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_READY_TO_START_REF and captured,
        "rsr_op09_review_operation_in_progress_local_only": lifecycle_status == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_IN_PROGRESS_LOCAL_ONLY_REF and captured,
        "rsr_op09_review_operation_paused_local_only": lifecycle_status == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_PAUSED_LOCAL_ONLY_REF and captured,
        "rsr_op09_review_operation_completed_receipt_required": completed,
        "rsr_op09_review_operation_aborted_repair_required": lifecycle_status == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_ABORTED_REPAIR_REQUIRED_REF and captured,
        "review_lifecycle_state_captured_bodyfree": captured,
        "helper_executes_actual_review": False,
        "actual_local_human_review_executed_here_by_helper": False,
        "actual_review_lifecycle_completed_but_receipt_not_accepted": completed,
        "actual_operation_receipt_required": completed,
        "actual_operation_receipt_accepted_by_op09": False,
        "rsr_op09_ready_for_actual_operation_receipt_intake": completed,
        "rsr_op09_does_not_generate_body_full_packet": True,
        "rsr_op09_does_not_run_actual_local_human_review": True,
        "rsr_op09_does_not_create_actual_operation_receipt_rows_or_disposal": True,
        "rsr_op09_does_not_execute_dmd_or_r52": True,
        "rsr_op09_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op09_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP09_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP09 body-free lifecycle state capture contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP09")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP09_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP09_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP09_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP09")
    for field, count_field in (("lifecycle_status_allowed_refs", "lifecycle_status_allowed_ref_count"), ("lifecycle_state_forbidden_payload_key_path_refs", "lifecycle_state_forbidden_payload_key_path_count"), ("lifecycle_state_body_like_value_path_refs", "lifecycle_state_body_like_value_path_count"), ("lifecycle_state_promotion_claim_refs", "lifecycle_state_promotion_claim_ref_count"), ("lifecycle_state_reason_refs", "lifecycle_state_reason_ref_count"), ("lifecycle_state_blocker_refs", "lifecycle_state_blocker_ref_count"), ("rsr_op09_allowed_status_refs", "rsr_op09_allowed_status_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP09 {count_field} changed")
    for key in ("rsr_op09_does_not_generate_body_full_packet", "rsr_op09_does_not_run_actual_local_human_review", "rsr_op09_does_not_create_actual_operation_receipt_rows_or_disposal", "rsr_op09_does_not_execute_dmd_or_r52", "rsr_op09_does_not_start_p5_p6_p8_p7_or_release", "rsr_op09_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP09 required true boundary changed: {key}")
    for key in ("helper_executes_actual_review", "actual_local_human_review_executed_here_by_helper", "actual_operation_receipt_accepted_by_op09", "body_full_packet_generated_here", "body_full_packet_generation_run_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP09 false boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP09_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP09_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 implemented/not-yet steps changed")
    if tuple(data.get("lifecycle_status_allowed_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 lifecycle status set changed")
    flags = [
        data.get("rsr_op09_review_operation_not_started") is True,
        data.get("rsr_op09_review_operation_ready_to_start") is True,
        data.get("rsr_op09_review_operation_in_progress_local_only") is True,
        data.get("rsr_op09_review_operation_paused_local_only") is True,
        data.get("rsr_op09_review_operation_completed_receipt_required") is True,
        data.get("rsr_op09_review_operation_aborted_repair_required") is True,
        data.get("rsr_op09_waiting_for_selection_form_contract") is True,
        data.get("rsr_op09_invalid_repair_required") is True,
        data.get("rsr_op09_body_leak_blocked") is True,
    ]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 exactly one status flag must be true")
    status_ref = data.get("rsr_op09_status_ref")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF:
        if data.get("rsr_op09_ready_for_actual_operation_receipt_intake") is not True or data.get("actual_operation_receipt_required") is not True or data.get("actual_review_lifecycle_completed_but_receipt_not_accepted") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 completed status changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_ABORTED_REPAIR_REQUIRED_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_ABORTED_ACTUAL_LOCAL_ONLY_REVIEW_LIFECYCLE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 aborted status changed")
    elif status_ref in (
        P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF,
        P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_READY_TO_START_REF,
        P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_IN_PROGRESS_LOCAL_ONLY_REF,
        P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_PAUSED_LOCAL_ONLY_REF,
    ):
        if data.get("rsr_op09_ready") is not True or data.get("actual_operation_receipt_required") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_START_OR_CONTINUE_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_LOCAL_ONLY_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 local-only lifecycle status changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_WAITING_FOR_SELECTION_FORM_CONTRACT_REF:
        if data.get("rsr_op09_ready") is not False or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_SELECTION_FORM_CONTRACT_BEFORE_LIFECYCLE_CAPTURE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 waiting status changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op09_ready") is not False or not data.get("lifecycle_state_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 invalid status changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP09_STATUS_BODY_LEAK_BLOCKED_REF:
        if data.get("rsr_op09_ready") is not False or not data.get("lifecycle_state_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 body leak status changed")
    else:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP09 status ref is not allowed")
    return True




def _safe_bodyfree_ref(value: Any, *, default: str, max_length: int = 180) -> str:
    ref = _clean_ref(value, default=default, max_length=max_length)
    if _ref_has_local_path_shape(ref):
        return default
    return ref


def _safe_int_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _sequence_rows(value: Any) -> tuple[bool, list[Any]]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return True, list(value)
    return False, []


def _rsr_ref_list(values: Any, *, field: str) -> tuple[list[str], list[str]]:
    present, raw_values = _sequence_rows(values)
    if not present:
        return [], [f"{field}_not_list"]
    cleaned: list[str] = []
    blockers: list[str] = []
    for index, value in enumerate(raw_values, start=1):
        ref = _safe_bodyfree_ref(value, default=f"invalid_{field}_{index:03d}", max_length=220)
        if ref.startswith("invalid_"):
            blockers.append(f"{field}_contains_invalid_ref")
        cleaned.append(ref)
    return cleaned, blockers


def _rsr_axis_scores_and_pass_flags(raw_scores: Any, raw_pass_flags: Any = None) -> tuple[dict[str, float], dict[str, bool], list[str]]:
    blockers: list[str] = []
    axis_refs = tuple(P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS.keys())
    thresholds = P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS
    if not isinstance(raw_scores, Mapping):
        return ({axis: 0.0 for axis in axis_refs}, {axis: False for axis in axis_refs}, ["axis_score_refs_not_mapping"])
    if set(str(key) for key in raw_scores) != set(axis_refs):
        blockers.append("axis_score_refs_axis_set_mismatch")
    scores: dict[str, float] = {}
    pass_flags: dict[str, bool] = {}
    for axis in axis_refs:
        try:
            score = round(float(raw_scores.get(axis)), 4)
        except (TypeError, ValueError):
            score = 0.0
            blockers.append("axis_score_ref_not_numeric")
        if score < 0.0 or score > 1.0:
            blockers.append("axis_score_ref_out_of_range")
            score = max(0.0, min(1.0, score))
        scores[axis] = score
        pass_flags[axis] = score >= thresholds[axis]
    if not isinstance(raw_pass_flags, Mapping):
        blockers.append("axis_pass_flags_not_mapping")
    else:
        if set(str(key) for key in raw_pass_flags) != set(axis_refs):
            blockers.append("axis_pass_flags_axis_set_mismatch")
        for axis in axis_refs:
            if bool(raw_pass_flags.get(axis)) != pass_flags[axis]:
                blockers.append("axis_pass_flags_mismatch")
                break
    return scores, pass_flags, _dedupe_clean_refs(blockers)


def _actual_operation_receipt_blocker_refs(receipt: Mapping[str, Any] | None, *, review_session_id: str) -> tuple[list[str], list[str]]:
    if not isinstance(receipt, Mapping):
        return ["actual_operation_receipt_missing"], []
    blockers: list[str] = []
    source_blockers: list[str] = []
    if receipt.get("schema_version") != P7_R54_AHR_POST_DHR09_RSR_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION:
        blockers.append("actual_operation_receipt_schema_version_mismatch")
    operation_receipt_ref_raw = receipt.get("operation_receipt_ref")
    if not _clean_ref(operation_receipt_ref_raw, max_length=220):
        blockers.append("operation_receipt_ref_missing")
    if _ref_has_local_path_shape(_clean_ref(operation_receipt_ref_raw, max_length=260)):
        blockers.append("operation_receipt_ref_has_local_path_shape")
    if _safe_review_session_id(receipt.get("review_session_id")) != review_session_id:
        blockers.append("actual_operation_receipt_review_session_id_mismatch")
    packet_request_ref_raw = receipt.get("packet_request_ref")
    if not _clean_ref(packet_request_ref_raw, max_length=220):
        blockers.append("packet_request_ref_missing")
    if _ref_has_local_path_shape(_clean_ref(packet_request_ref_raw, max_length=260)):
        blockers.append("packet_request_ref_has_local_path_shape")
    reviewer_person_ref_raw = receipt.get("reviewer_person_ref")
    if not _clean_ref(reviewer_person_ref_raw, max_length=180):
        source_blockers.append("reviewer_person_ref_missing")
    if _ref_has_local_path_shape(_clean_ref(reviewer_person_ref_raw, max_length=220)):
        source_blockers.append("reviewer_person_ref_has_local_path_shape")
    if _clean_ref(receipt.get("source_kind_ref"), max_length=220) != P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
        source_blockers.append("source_kind_not_actual_local_only_human_review_by_person")
    for key in ("created_from_real_operation", "actual_human_review_executed_by_person", "local_only_operation_confirmed", "selection_only_form_used", "body_free"):
        if receipt.get(key) is not True:
            source_blockers.append(f"{key}_not_true")
    for key in P7_R54_AHR_POST_DHR09_RSR_OPERATION_RECEIPT_BODYFREE_FALSE_FIELD_REFS:
        if receipt.get(key, False) is not False:
            blockers.append(f"{key}_not_false")
    if _safe_int_count(receipt.get("reviewed_case_count")) != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
        source_blockers.append("reviewed_case_count_not_24")
    if _safe_int_count(receipt.get("selection_row_count")) != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
        source_blockers.append("selection_row_count_not_24")
    return _dedupe_clean_refs(blockers), _dedupe_clean_refs(source_blockers)


def build_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake(
    *,
    actual_local_only_review_lifecycle_state_capture: Mapping[str, Any] | None = None,
    review_lifecycle_state_capture: Mapping[str, Any] | None = None,
    op09_lifecycle_state_capture: Mapping[str, Any] | None = None,
    actual_operation_receipt_optional: Mapping[str, Any] | None = None,
    actual_operation_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP10 body-free actual operation receipt intake material."""

    op09 = actual_local_only_review_lifecycle_state_capture or review_lifecycle_state_capture or op09_lifecycle_state_capture
    if op09 is None:
        op09 = build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op09.get("review_session_id") if isinstance(op09, Mapping) else None))
    try:
        op09_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract(op09) is True
    except ValueError:
        op09_contract_valid = False
    op09_status_ref = _bodyfree_status_ref(op09.get("rsr_op09_status_ref") if isinstance(op09, Mapping) else None, default="rsr_op09_status_missing")
    op09_ready_for_receipt = bool(op09_contract_valid and op09.get("rsr_op09_ready_for_actual_operation_receipt_intake") is True)
    op09_next_step = _bodyfree_status_ref(op09.get("next_required_step") if isinstance(op09, Mapping) else None, default="rsr_op09_next_required_step_missing")
    op09_completed = bool(op09_contract_valid and op09.get("rsr_op09_review_operation_completed_receipt_required") is True)
    op09_receipt_required = bool(op09_contract_valid and op09.get("actual_operation_receipt_required") is True)

    receipt_input = actual_operation_receipt if actual_operation_receipt is not None else actual_operation_receipt_optional
    receipt_present = isinstance(receipt_input, Mapping)
    receipt = receipt_input if receipt_present else {}
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(receipt_input, path="op10_actual_operation_receipt") if receipt_present else [])
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(receipt_input, path="op10_actual_operation_receipt") if receipt_present else [])
    promo = _dedupe_clean_refs(_promotion_claim_refs(receipt_input) if receipt_present else [])
    receipt_blockers, source_claim_blockers = _actual_operation_receipt_blocker_refs(receipt_input if receipt_present else None, review_session_id=session_id)
    marker_violations = _dedupe_clean_refs([
        f"actual_operation_receipt_{field}_present_or_true"
        for field in P7_R54_AHR_POST_DHR09_RSR_OPERATION_RECEIPT_BODYFREE_FALSE_FIELD_REFS
        if receipt.get(field, False) is not False
    ])

    blockers: list[str] = []
    reasons: list[str] = []
    if not op09_contract_valid:
        blockers.append("op09_lifecycle_state_capture_contract_invalid_or_missing")
    elif not op09_ready_for_receipt:
        blockers.append("op09_lifecycle_not_completed_receipt_required")
    if receipt_present:
        blockers.extend(receipt_blockers)
        blockers.extend(source_claim_blockers)
        if forbidden:
            blockers.append("actual_operation_receipt_forbidden_payload_key_detected")
        if body_like:
            blockers.append("actual_operation_receipt_body_like_value_detected")
        if promo:
            blockers.append("actual_operation_receipt_promotion_claim_detected")
    elif op09_ready_for_receipt:
        blockers.extend(ref for ref in receipt_blockers if ref != "actual_operation_receipt_missing")

    blocker_refs = _dedupe_clean_refs(blockers)
    source_leak_or_claim_block = bool(forbidden or body_like or promo or source_claim_blockers)
    if not receipt_present:
        if op09_ready_for_receipt:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_MISSING_WAITING_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_ACTUAL_OPERATION_RECEIPT_BODYFREE_REF
            reasons.append("actual_operation_receipt_missing_waiting_bodyfree")
        else:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_COMPLETED_LIFECYCLE_BEFORE_OPERATION_RECEIPT_REF
            reasons.append("actual_operation_receipt_prerequisite_lifecycle_repair_required")
    elif source_leak_or_claim_block:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF
        reasons.append("actual_operation_receipt_body_leak_or_source_claim_blocks_rows_intake")
    elif op09_ready_for_receipt and not blocker_refs:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_ACCEPTED_BODYFREE_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF
        reasons.append("actual_operation_receipt_accepted_bodyfree_without_rows_complete")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_ACTUAL_OPERATION_RECEIPT_BEFORE_ROWS_REF
        reasons.append("actual_operation_receipt_invalid_or_prerequisite_repair_required")
    reason_refs = _dedupe_clean_refs(reasons)
    accepted = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_ACCEPTED_BODYFREE_REF
    missing = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_MISSING_WAITING_REF
    invalid = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF
    blocked = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF

    operation_receipt_ref = _safe_bodyfree_ref(receipt.get("operation_receipt_ref"), default="missing_or_invalid_operation_receipt_ref", max_length=220)
    packet_request_ref = _safe_bodyfree_ref(receipt.get("packet_request_ref"), default="missing_or_invalid_packet_request_ref", max_length=220)
    reviewer_person_ref = _safe_bodyfree_ref(receipt.get("reviewer_person_ref"), default="missing_or_invalid_reviewer_person_ref", max_length=180)
    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP10_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op09_contract_valid": op09_contract_valid,
        "op09_status_ref": op09_status_ref,
        "op09_ready_for_actual_operation_receipt_intake": op09_ready_for_receipt,
        "op09_next_required_step": op09_next_step,
        "op09_review_lifecycle_completed_receipt_required": op09_completed,
        "op09_actual_operation_receipt_required": op09_receipt_required,
        "actual_operation_receipt_present": receipt_present,
        "actual_operation_receipt_schema_version": _clean_ref(receipt.get("schema_version"), default="missing_actual_operation_receipt_schema_version", max_length=280),
        "operation_receipt_ref": operation_receipt_ref,
        "operation_receipt_ref_present": bool(_clean_ref(receipt.get("operation_receipt_ref"), max_length=220)),
        "operation_receipt_review_session_id": _safe_review_session_id(receipt.get("review_session_id")),
        "operation_receipt_review_session_id_matches": _safe_review_session_id(receipt.get("review_session_id")) == session_id,
        "operation_receipt_packet_request_ref": packet_request_ref,
        "operation_receipt_packet_request_ref_present": bool(_clean_ref(receipt.get("packet_request_ref"), max_length=220)),
        "source_kind_ref": _clean_ref(receipt.get("source_kind_ref"), default="missing_source_kind_ref", max_length=220),
        "source_kind_is_actual_local_only_human_review_by_person": _clean_ref(receipt.get("source_kind_ref"), max_length=220) == P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "created_from_real_operation": receipt.get("created_from_real_operation") is True,
        "actual_human_review_executed_by_person": receipt.get("actual_human_review_executed_by_person") is True,
        "reviewer_person_ref": reviewer_person_ref,
        "reviewer_person_ref_present": bool(_clean_ref(receipt.get("reviewer_person_ref"), max_length=180)),
        "reviewed_case_count": _safe_int_count(receipt.get("reviewed_case_count")),
        "selection_row_count": _safe_int_count(receipt.get("selection_row_count")),
        "local_only_operation_confirmed": receipt.get("local_only_operation_confirmed") is True,
        "selection_only_form_used": receipt.get("selection_only_form_used") is True,
        "actual_operation_receipt_external_export_performed": receipt.get("external_export_performed", False) is True,
        "actual_operation_receipt_body_free": receipt.get("body_free") is True,
        "actual_operation_receipt_raw_input_included": receipt.get("raw_input_included", False) is True,
        "actual_operation_receipt_comment_text_body_included": receipt.get("comment_text_body_included", False) is True,
        "actual_operation_receipt_returned_surface_body_included": receipt.get("returned_surface_body_included", False) is True,
        "actual_operation_receipt_reviewer_free_text_included": receipt.get("reviewer_free_text_included", False) is True,
        "actual_operation_receipt_reviewer_note_body_included": receipt.get("reviewer_note_body_included", False) is True,
        "actual_operation_receipt_question_text_included": receipt.get("question_text_included", False) is True,
        "actual_operation_receipt_draft_question_text_included": receipt.get("draft_question_text_included", False) is True,
        "actual_operation_receipt_answer_text_included": receipt.get("answer_text_included", False) is True,
        "actual_operation_receipt_local_path_included": receipt.get("local_path_included", False) is True,
        "actual_operation_receipt_body_hash_included": receipt.get("body_hash_included", False) is True,
        "actual_operation_receipt_terminal_output_body_included": receipt.get("terminal_output_body_included", False) is True,
        "actual_operation_receipt_forbidden_payload_key_path_refs": forbidden,
        "actual_operation_receipt_forbidden_payload_key_path_count": len(forbidden),
        "actual_operation_receipt_body_like_value_path_refs": body_like,
        "actual_operation_receipt_body_like_value_path_count": len(body_like),
        "actual_operation_receipt_promotion_claim_refs": promo,
        "actual_operation_receipt_promotion_claim_ref_count": len(promo),
        "actual_operation_receipt_body_free_marker_violation_refs": marker_violations,
        "actual_operation_receipt_body_free_marker_violation_ref_count": len(marker_violations),
        "actual_operation_receipt_source_claim_blocker_refs": source_claim_blockers,
        "actual_operation_receipt_source_claim_blocker_ref_count": len(source_claim_blockers),
        "rsr_op10_status_ref": status_ref,
        "rsr_op10_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP10_ALLOWED_STATUS_REFS),
        "rsr_op10_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP10_ALLOWED_STATUS_REFS),
        "rsr_op10_ready": accepted,
        "rsr_op10_actual_operation_receipt_accepted": accepted,
        "rsr_op10_actual_operation_receipt_missing_waiting": missing,
        "rsr_op10_actual_operation_receipt_invalid_repair_required": invalid,
        "rsr_op10_actual_operation_receipt_body_leak_or_source_claim_blocked": blocked,
        "actual_operation_receipt_accepted_by_rsr_op10": accepted,
        "ready_for_sanitized_review_result_rows_rating_rows_intake": accepted,
        "actual_operation_receipt_intake_bodyfree_accepted_without_rows": accepted,
        "sanitized_review_result_rows_and_rating_rows_required_next": accepted,
        "op10_reason_refs": reason_refs,
        "op10_reason_ref_count": len(reason_refs),
        "op10_blocker_refs": blocker_refs,
        "op10_blocker_ref_count": len(blocker_refs),
        "helper_executes_actual_review": False,
        "actual_operation_receipt_created_here_by_helper": False,
        "actual_rows_created_here_by_helper": False,
        "actual_review_evidence_complete_here": False,
        "rsr_op10_does_not_run_actual_local_human_review": True,
        "rsr_op10_does_not_create_actual_operation_receipt": True,
        "rsr_op10_does_not_create_rows_question_rows_or_disposal": True,
        "rsr_op10_does_not_execute_dmd_or_r52": True,
        "rsr_op10_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op10_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP10_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP10 body-free actual operation receipt intake contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP10_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP10")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP10_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP10_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP10_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP10")
    for field, count_field in (("rsr_op10_allowed_status_refs", "rsr_op10_allowed_status_ref_count"), ("actual_operation_receipt_forbidden_payload_key_path_refs", "actual_operation_receipt_forbidden_payload_key_path_count"), ("actual_operation_receipt_body_like_value_path_refs", "actual_operation_receipt_body_like_value_path_count"), ("actual_operation_receipt_promotion_claim_refs", "actual_operation_receipt_promotion_claim_ref_count"), ("actual_operation_receipt_body_free_marker_violation_refs", "actual_operation_receipt_body_free_marker_violation_ref_count"), ("actual_operation_receipt_source_claim_blocker_refs", "actual_operation_receipt_source_claim_blocker_ref_count"), ("op10_reason_refs", "op10_reason_ref_count"), ("op10_blocker_refs", "op10_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP10 {count_field} changed")
    if tuple(data.get("rsr_op10_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP10_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 allowed status refs changed")
    for key in ("rsr_op10_does_not_run_actual_local_human_review", "rsr_op10_does_not_create_actual_operation_receipt", "rsr_op10_does_not_create_rows_question_rows_or_disposal", "rsr_op10_does_not_execute_dmd_or_r52", "rsr_op10_does_not_start_p5_p6_p8_p7_or_release", "rsr_op10_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP10 required true boundary changed: {key}")
    for key in ("helper_executes_actual_review", "actual_operation_receipt_created_here_by_helper", "actual_rows_created_here_by_helper", "actual_review_evidence_complete_here", "body_full_packet_generated_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP10 false boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP10_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP10_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 implemented/not-yet steps changed")
    status_ref = data.get("rsr_op10_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHR09_RSR_OP10_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 status ref is not allowed")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_ACCEPTED_BODYFREE_REF:
        for key in ("op09_ready_for_actual_operation_receipt_intake", "op09_review_lifecycle_completed_receipt_required", "op09_actual_operation_receipt_required", "actual_operation_receipt_present", "operation_receipt_ref_present", "operation_receipt_review_session_id_matches", "operation_receipt_packet_request_ref_present", "source_kind_is_actual_local_only_human_review_by_person", "created_from_real_operation", "actual_human_review_executed_by_person", "reviewer_person_ref_present", "local_only_operation_confirmed", "selection_only_form_used", "actual_operation_receipt_body_free", "actual_operation_receipt_accepted_by_rsr_op10", "ready_for_sanitized_review_result_rows_rating_rows_intake", "actual_operation_receipt_intake_bodyfree_accepted_without_rows", "sanitized_review_result_rows_and_rating_rows_required_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP10 accepted branch required true changed: {key}")
        if data.get("reviewed_case_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or data.get("selection_row_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 accepted count changed")
        if data.get("op10_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 accepted branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 accepted next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_MISSING_WAITING_REF:
        if data.get("rsr_op10_actual_operation_receipt_missing_waiting") is not True or data.get("actual_operation_receipt_accepted_by_rsr_op10") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 missing branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_ACTUAL_OPERATION_RECEIPT_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 missing next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op10_actual_operation_receipt_invalid_repair_required") is not True or not data.get("op10_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 invalid branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP10_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF:
        if data.get("rsr_op10_actual_operation_receipt_body_leak_or_source_claim_blocked") is not True or not data.get("op10_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_ACTUAL_OPERATION_RECEIPT_BODY_LEAK_OR_SOURCE_CLAIM_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP10 blocked next step changed")
    return True


def _validate_rsr_op11_sanitized_rows(rows_input: Any, *, review_session_id: str, operation_receipt_ref: str, reviewer_person_ref: str, expected_case_refs: Sequence[Any] | None = None) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    present, raw_rows = _sequence_rows(rows_input)
    blockers: list[str] = []
    clean_rows: list[dict[str, Any]] = []
    if not present:
        blockers.append("sanitized_review_result_rows_missing")
    elif len(raw_rows) != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
        blockers.append("sanitized_review_result_row_count_not_24")
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(rows_input, path="op11_sanitized_review_result_rows") if present else [])
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(rows_input, path="op11_sanitized_review_result_rows") if present else [])
    promo: list[str] = []
    row_refs: list[str] = []
    case_refs: list[str] = []
    flags = {
        "sanitized_rows_bodyfree_only": True,
        "sanitized_rows_selection_only": True,
        "sanitized_rows_have_actual_person_selection_only_provenance": True,
        "sanitized_rows_have_required_axis_scores": True,
        "sanitized_rows_have_allowed_verdict_refs": True,
        "sanitized_rows_have_allowed_question_observation_refs": True,
        "sanitized_rows_have_no_body_or_question_or_path_or_hash": not bool(forbidden or body_like),
        "rows_operation_receipt_ref_matches": True,
        "rows_reviewer_person_ref_matches": True,
        "rows_source_kind_is_actual_local_only_human_review_by_person": True,
    }
    for index, raw in enumerate(raw_rows, start=1):
        if not isinstance(raw, Mapping):
            blockers.append("sanitized_review_result_row_not_mapping")
            flags["sanitized_rows_bodyfree_only"] = False
            continue
        promo.extend(_promotion_claim_refs(raw))
        if set(raw) != set(P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS):
            blockers.append("sanitized_review_result_row_required_fields_mismatch")
            flags["sanitized_rows_have_no_body_or_question_or_path_or_hash"] = False
        if raw.get("schema_version") != P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
            blockers.append("sanitized_review_result_row_schema_version_mismatch")
        row_ref = _safe_bodyfree_ref(raw.get("review_result_row_ref"), default=f"invalid_review_result_row_ref_{index:03d}", max_length=220)
        case_ref = _safe_bodyfree_ref(raw.get("case_ref"), default=f"invalid_case_ref_{index:03d}", max_length=180)
        row_refs.append(row_ref)
        case_refs.append(case_ref)
        if raw.get("review_session_id") != review_session_id:
            blockers.append("sanitized_review_result_row_review_session_id_mismatch")
        if raw.get("operation_receipt_ref") != operation_receipt_ref:
            blockers.append("sanitized_review_result_row_operation_receipt_ref_mismatch")
            flags["rows_operation_receipt_ref_matches"] = False
        if raw.get("reviewer_person_ref") != reviewer_person_ref:
            blockers.append("sanitized_review_result_row_reviewer_person_ref_mismatch")
            flags["rows_reviewer_person_ref_matches"] = False
        if _clean_ref(raw.get("source_kind_ref"), max_length=220) != P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
            blockers.append("sanitized_review_result_row_source_kind_not_actual_local_only_human_review_by_person")
            flags["rows_source_kind_is_actual_local_only_human_review_by_person"] = False
            flags["sanitized_rows_have_actual_person_selection_only_provenance"] = False
        if raw.get("verdict_ref") not in P7_R54_AHR_POST_DHR09_RSR_REVIEW_VERDICT_OPTION_REFS:
            blockers.append("sanitized_review_result_row_verdict_ref_not_allowed")
            flags["sanitized_rows_have_allowed_verdict_refs"] = False
        scores, pass_flags, axis_blockers = _rsr_axis_scores_and_pass_flags(raw.get("axis_score_refs"), raw.get("axis_pass_flags"))
        if axis_blockers or raw.get("axis_score_count") != len(P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS):
            blockers.extend(f"sanitized_row_{ref}" for ref in axis_blockers)
            if raw.get("axis_score_count") != len(P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS):
                blockers.append("sanitized_review_result_row_axis_score_count_mismatch")
            flags["sanitized_rows_have_required_axis_scores"] = False
        list_outputs: dict[str, list[str]] = {}
        for list_field in ("sanitized_reason_id_refs", "readfeel_blocker_id_refs", "execution_blocker_id_refs", "ambiguity_kind_refs", "repair_required_refs"):
            cleaned, list_blockers = _rsr_ref_list(raw.get(list_field), field=list_field)
            list_outputs[list_field] = cleaned
            blockers.extend(f"sanitized_row_{ref}" for ref in list_blockers)
            if list_blockers:
                flags["sanitized_rows_have_no_body_or_question_or_path_or_hash"] = False
        if raw.get("question_need_primary_class_ref") not in P7_R54_AHR_POST_DHR09_RSR_OP08_QUESTION_NEED_CLASS_REFS:
            blockers.append("sanitized_review_result_row_question_need_primary_class_ref_not_allowed")
            flags["sanitized_rows_have_allowed_question_observation_refs"] = False
        if raw.get("one_question_fit_ref") not in P7_R54_AHR_POST_DHR09_RSR_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append("sanitized_review_result_row_one_question_fit_ref_not_allowed")
            flags["sanitized_rows_have_allowed_question_observation_refs"] = False
        if raw.get("selection_only") is not True:
            blockers.append("sanitized_review_result_row_selection_only_not_true")
            flags["sanitized_rows_selection_only"] = False
        for field in P7_R54_AHR_POST_DHR09_RSR_SANITIZED_ROW_PROVENANCE_FALSE_FIELD_REFS:
            if raw.get(field, False) is not False:
                blockers.append(f"sanitized_review_result_row_{field}_not_false")
                flags["sanitized_rows_have_actual_person_selection_only_provenance"] = False
        if raw.get("body_free") is not True:
            blockers.append("sanitized_review_result_row_body_free_not_true")
            flags["sanitized_rows_bodyfree_only"] = False
        clean_rows.append({
            "schema_version": P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "review_result_row_ref": row_ref,
            "case_ref": case_ref,
            "reviewer_person_ref": reviewer_person_ref,
            "source_kind_ref": _clean_ref(raw.get("source_kind_ref"), default="missing_source_kind_ref", max_length=220),
            "verdict_ref": _clean_ref(raw.get("verdict_ref"), default="missing_verdict_ref", max_length=120),
            "axis_score_refs": scores,
            "axis_score_count": len(P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS),
            "axis_pass_flags": pass_flags,
            "sanitized_reason_id_refs": list_outputs.get("sanitized_reason_id_refs", []),
            "readfeel_blocker_id_refs": list_outputs.get("readfeel_blocker_id_refs", []),
            "execution_blocker_id_refs": list_outputs.get("execution_blocker_id_refs", []),
            "question_need_primary_class_ref": _clean_ref(raw.get("question_need_primary_class_ref"), default="missing_question_need_primary_class_ref", max_length=180),
            "ambiguity_kind_refs": list_outputs.get("ambiguity_kind_refs", []),
            "one_question_fit_ref": _clean_ref(raw.get("one_question_fit_ref"), default="missing_one_question_fit_ref", max_length=180),
            "repair_required_refs": list_outputs.get("repair_required_refs", []),
            "selection_only": raw.get("selection_only") is True,
            "row_created_by_helper": raw.get("row_created_by_helper", False) is True,
            "row_created_for_unit_test": raw.get("row_created_for_unit_test", False) is True,
            "row_is_synthetic_contract_fixture": raw.get("row_is_synthetic_contract_fixture", False) is True,
            "historical_row_reused": raw.get("historical_row_reused", False) is True,
            "body_free": raw.get("body_free") is True,
        })
    if promo:
        blockers.append("sanitized_review_result_rows_promotion_claim_detected")
    case_refs_unique = len(set(case_refs)) == len(case_refs)
    if present and not case_refs_unique:
        blockers.append("sanitized_review_result_row_case_ref_duplicate_detected")
    expected_present, expected_values = _sequence_rows(expected_case_refs)
    expected_clean = [_safe_bodyfree_ref(ref, default="invalid_expected_case_ref", max_length=180) for ref in expected_values] if expected_present else []
    case_refs_match_expected = set(case_refs) == set(expected_clean) if expected_present else (len(case_refs) == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT and case_refs_unique)
    if present and not case_refs_match_expected:
        blockers.append("sanitized_review_result_row_case_refs_do_not_match_expected_manifest")
    return clean_rows, _dedupe_clean_refs(blockers), {
        **flags,
        "forbidden_paths": forbidden,
        "body_like_paths": body_like,
        "promotion_claims": _dedupe_clean_refs(promo),
        "row_refs": row_refs,
        "case_refs": case_refs,
        "case_refs_unique": case_refs_unique,
        "unique_case_ref_count": len(set(case_refs)),
        "case_refs_match_expected_manifest": case_refs_match_expected,
    }


def _validate_rsr_op11_rating_rows(rows_input: Any, *, sanitized_rows: Sequence[Mapping[str, Any]], review_session_id: str, operation_receipt_ref: str) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    present, raw_rows = _sequence_rows(rows_input)
    blockers: list[str] = []
    clean_rows: list[dict[str, Any]] = []
    if not present:
        blockers.append("rating_rows_missing")
    elif len(raw_rows) != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
        blockers.append("rating_row_count_not_24")
    forbidden = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(rows_input, path="op11_rating_rows") if present else [])
    body_like = _dedupe_clean_refs(_scan_body_like_value_paths(rows_input, path="op11_rating_rows") if present else [])
    promo: list[str] = []
    rating_row_refs: list[str] = []
    rating_case_refs: list[str] = []
    sanitized_by_case = {str(row.get("case_ref")): row for row in sanitized_rows if isinstance(row, Mapping)}
    flags = {
        "rating_rows_bodyfree_only": True,
        "rating_rows_from_sanitized_rows": True,
        "rating_rows_have_required_axis_scores": True,
        "rating_rows_have_no_body_or_question_or_path_or_hash": not bool(forbidden or body_like),
    }
    for index, raw in enumerate(raw_rows, start=1):
        if not isinstance(raw, Mapping):
            blockers.append("rating_row_not_mapping")
            flags["rating_rows_bodyfree_only"] = False
            continue
        promo.extend(_promotion_claim_refs(raw))
        if set(raw) != set(P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_REQUIRED_FIELD_REFS):
            blockers.append("rating_row_required_fields_mismatch")
            flags["rating_rows_have_no_body_or_question_or_path_or_hash"] = False
        if raw.get("schema_version") != P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_SCHEMA_VERSION:
            blockers.append("rating_row_schema_version_mismatch")
        rating_ref = _safe_bodyfree_ref(raw.get("rating_row_ref"), default=f"invalid_rating_row_ref_{index:03d}", max_length=220)
        case_ref = _safe_bodyfree_ref(raw.get("case_ref"), default=f"invalid_rating_case_ref_{index:03d}", max_length=180)
        source_sanitized_ref = _safe_bodyfree_ref(raw.get("source_sanitized_review_result_row_ref"), default=f"invalid_source_sanitized_review_result_row_ref_{index:03d}", max_length=220)
        rating_row_refs.append(rating_ref)
        rating_case_refs.append(case_ref)
        sanitized = sanitized_by_case.get(case_ref)
        if raw.get("review_session_id") != review_session_id:
            blockers.append("rating_row_review_session_id_mismatch")
        if raw.get("operation_receipt_ref") != operation_receipt_ref:
            blockers.append("rating_row_operation_receipt_ref_mismatch")
        if sanitized is None:
            blockers.append("rating_row_case_ref_not_found_in_sanitized_rows")
            flags["rating_rows_from_sanitized_rows"] = False
            expected_scores: dict[str, float] = {axis: 0.0 for axis in P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS}
            expected_pass: dict[str, bool] = {axis: False for axis in P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS}
        else:
            if source_sanitized_ref != sanitized.get("review_result_row_ref"):
                blockers.append("rating_row_source_sanitized_review_result_row_ref_mismatch")
                flags["rating_rows_from_sanitized_rows"] = False
            if raw.get("verdict_ref") != sanitized.get("verdict_ref"):
                blockers.append("rating_row_verdict_ref_mismatch")
                flags["rating_rows_from_sanitized_rows"] = False
            expected_scores = dict(sanitized.get("axis_score_refs") or {})
            expected_pass = dict(sanitized.get("axis_pass_flags") or {})
        scores, pass_flags, axis_blockers = _rsr_axis_scores_and_pass_flags(raw.get("axis_score_refs"), raw.get("axis_pass_flags"))
        if axis_blockers:
            blockers.extend(f"rating_row_{ref}" for ref in axis_blockers)
            flags["rating_rows_have_required_axis_scores"] = False
        if {axis: round(float(expected_scores.get(axis, 0.0)), 4) for axis in P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS} != scores:
            blockers.append("rating_row_axis_score_refs_do_not_match_sanitized_row")
            flags["rating_rows_from_sanitized_rows"] = False
        if {axis: bool(expected_pass.get(axis)) for axis in P7_R54_AHR_POST_DHR09_RSR_OP08_RATING_AXIS_TARGET_REFS} != pass_flags:
            blockers.append("rating_row_axis_pass_flags_do_not_match_sanitized_row")
            flags["rating_rows_from_sanitized_rows"] = False
        below_target = [axis for axis, passed in pass_flags.items() if not passed]
        below_refs, below_blockers = _rsr_ref_list(raw.get("below_target_axis_refs"), field="below_target_axis_refs")
        blockers.extend(f"rating_row_{ref}" for ref in below_blockers)
        if set(below_refs) != set(below_target):
            blockers.append("rating_row_below_target_axis_refs_mismatch")
            flags["rating_rows_have_required_axis_scores"] = False
        ref_lists: dict[str, list[str]] = {}
        for field in ("readfeel_blocker_id_refs", "execution_blocker_id_refs", "repair_required_refs"):
            cleaned, list_blockers = _rsr_ref_list(raw.get(field), field=field)
            ref_lists[field] = cleaned
            blockers.extend(f"rating_row_{ref}" for ref in list_blockers)
            if list_blockers:
                flags["rating_rows_have_no_body_or_question_or_path_or_hash"] = False
            if sanitized is not None and cleaned != list(sanitized.get(field) or []):
                blockers.append(f"rating_row_{field}_do_not_match_sanitized_row")
                flags["rating_rows_from_sanitized_rows"] = False
        if raw.get("actual_rating_row_from_real_operation") is not True:
            blockers.append("rating_row_actual_rating_row_from_real_operation_not_true")
            flags["rating_rows_from_sanitized_rows"] = False
        if raw.get("rating_decision_material_only") is not True:
            blockers.append("rating_row_rating_decision_material_only_not_true")
        if raw.get("body_free") is not True:
            blockers.append("rating_row_body_free_not_true")
            flags["rating_rows_bodyfree_only"] = False
        clean_rows.append({
            "schema_version": P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_SCHEMA_VERSION,
            "rating_row_ref": rating_ref,
            "source_sanitized_review_result_row_ref": source_sanitized_ref,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "case_ref": case_ref,
            "verdict_ref": _clean_ref(raw.get("verdict_ref"), default="missing_verdict_ref", max_length=120),
            "axis_score_refs": scores,
            "axis_pass_flags": pass_flags,
            "below_target_axis_refs": below_refs,
            "readfeel_blocker_id_refs": ref_lists.get("readfeel_blocker_id_refs", []),
            "execution_blocker_id_refs": ref_lists.get("execution_blocker_id_refs", []),
            "repair_required_refs": ref_lists.get("repair_required_refs", []),
            "actual_rating_row_from_real_operation": raw.get("actual_rating_row_from_real_operation") is True,
            "rating_decision_material_only": raw.get("rating_decision_material_only") is True,
            "body_free": raw.get("body_free") is True,
        })
    if promo:
        blockers.append("rating_rows_promotion_claim_detected")
    case_refs_match = set(rating_case_refs) == set(row.get("case_ref") for row in sanitized_rows) and len(rating_case_refs) == len(sanitized_rows) == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    if present and not case_refs_match:
        blockers.append("rating_rows_case_refs_do_not_match_sanitized_rows")
    if len(set(rating_row_refs)) != len(rating_row_refs):
        blockers.append("rating_row_ref_duplicate_detected")
    return clean_rows, _dedupe_clean_refs(blockers), {
        **flags,
        "forbidden_paths": forbidden,
        "body_like_paths": body_like,
        "promotion_claims": _dedupe_clean_refs(promo),
        "rating_row_refs": rating_row_refs,
        "rating_case_refs": rating_case_refs,
        "case_refs_match_between_sanitized_and_rating_rows": case_refs_match,
    }


def build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    op10_actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_optional: Sequence[Mapping[str, Any]] | None = None,
    sanitized_review_result_rows: Sequence[Mapping[str, Any]] | None = None,
    rating_rows_optional: Sequence[Mapping[str, Any]] | None = None,
    rating_rows: Sequence[Mapping[str, Any]] | None = None,
    expected_case_refs: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP11 body-free sanitized review result rows / rating rows intake material."""

    op10 = actual_operation_receipt_intake if actual_operation_receipt_intake is not None else op10_actual_operation_receipt_intake
    if op10 is None:
        op10 = build_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op10.get("review_session_id") if isinstance(op10, Mapping) else None))
    try:
        op10_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract(op10) is True
    except ValueError:
        op10_contract_valid = False
    op10_status_ref = _bodyfree_status_ref(op10.get("rsr_op10_status_ref") if isinstance(op10, Mapping) else None, default="rsr_op10_status_missing")
    op10_accepted = bool(op10_contract_valid and op10.get("rsr_op10_actual_operation_receipt_accepted") is True and op10.get("next_required_step") == P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF)
    op10_ready = bool(op10_contract_valid and op10.get("ready_for_sanitized_review_result_rows_rating_rows_intake") is True)
    op10_next = _bodyfree_status_ref(op10.get("next_required_step") if isinstance(op10, Mapping) else None, default="rsr_op10_next_required_step_missing")
    operation_receipt_ref = _safe_bodyfree_ref(op10.get("operation_receipt_ref") if isinstance(op10, Mapping) else None, default="missing_or_invalid_operation_receipt_ref", max_length=220)
    packet_request_ref = _safe_bodyfree_ref(op10.get("operation_receipt_packet_request_ref") if isinstance(op10, Mapping) else None, default="missing_or_invalid_packet_request_ref", max_length=220)
    reviewer_person_ref = _safe_bodyfree_ref(op10.get("reviewer_person_ref") if isinstance(op10, Mapping) else None, default="missing_or_invalid_reviewer_person_ref", max_length=180)
    sanitized_input = sanitized_review_result_rows if sanitized_review_result_rows is not None else sanitized_review_result_rows_optional
    rating_input = rating_rows if rating_rows is not None else rating_rows_optional
    sanitized_present, _ = _sequence_rows(sanitized_input)
    rating_present, _ = _sequence_rows(rating_input)
    sanitized_clean_rows, sanitized_blockers, sanitized_meta = _validate_rsr_op11_sanitized_rows(
        sanitized_input,
        review_session_id=session_id,
        operation_receipt_ref=operation_receipt_ref,
        reviewer_person_ref=reviewer_person_ref,
        expected_case_refs=expected_case_refs,
    )
    rating_clean_rows, rating_blockers, rating_meta = _validate_rsr_op11_rating_rows(
        rating_input,
        sanitized_rows=sanitized_clean_rows,
        review_session_id=session_id,
        operation_receipt_ref=operation_receipt_ref,
    )
    blockers: list[str] = []
    reasons: list[str] = []
    if not op10_contract_valid:
        blockers.append("op10_actual_operation_receipt_intake_contract_invalid_or_missing")
    elif not op10_accepted:
        blockers.append("op10_actual_operation_receipt_not_accepted")
    if sanitized_present:
        blockers.extend(ref for ref in sanitized_blockers if ref != "sanitized_review_result_rows_missing")
    if rating_present:
        blockers.extend(ref for ref in rating_blockers if ref != "rating_rows_missing")
    if not sanitized_present or not rating_present:
        if op10_accepted:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_MISSING_WAITING_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_SANITIZED_REVIEW_RESULT_ROWS_AND_RATING_ROWS_BODYFREE_REF
            reasons.append("sanitized_review_result_rows_or_rating_rows_missing_waiting_bodyfree")
        else:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SANITIZED_REVIEW_RESULT_ROWS_AND_RATING_ROWS_REF
            reasons.append("review_rows_rating_rows_prerequisite_repair_required")
    elif any(ref in blockers for ref in ("sanitized_review_result_rows_promotion_claim_detected", "rating_rows_promotion_claim_detected")) or sanitized_meta["forbidden_paths"] or sanitized_meta["body_like_paths"] or sanitized_meta["promotion_claims"] or rating_meta["forbidden_paths"] or rating_meta["body_like_paths"] or rating_meta["promotion_claims"] or not sanitized_meta["rows_source_kind_is_actual_local_only_human_review_by_person"]:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEW_ROWS_RATING_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF
        reasons.append("review_rows_rating_rows_body_leak_or_source_claim_blocked")
    elif op10_accepted and not blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_ACCEPTED_BODYFREE_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF
        reasons.append("sanitized_review_result_rows_and_rating_rows_accepted_bodyfree")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_SANITIZED_REVIEW_RESULT_ROWS_AND_RATING_ROWS_REF
        reasons.append("review_rows_rating_rows_invalid_or_repair_required")
    blockers = _dedupe_clean_refs(blockers)
    reasons = _dedupe_clean_refs(reasons)
    accepted = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_ACCEPTED_BODYFREE_REF
    missing = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_MISSING_WAITING_REF
    invalid = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF
    blocked = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF
    case_refs = sanitized_meta["case_refs"] if accepted else []
    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP11_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op10_contract_valid": op10_contract_valid,
        "op10_status_ref": op10_status_ref,
        "op10_actual_operation_receipt_accepted": op10_accepted,
        "op10_ready_for_sanitized_review_result_rows_rating_rows_intake": op10_ready,
        "op10_next_required_step": op10_next,
        "operation_receipt_ref": operation_receipt_ref,
        "operation_receipt_packet_request_ref": packet_request_ref,
        "reviewer_person_ref": reviewer_person_ref,
        "sanitized_review_result_rows_present": sanitized_present,
        "rating_rows_present": rating_present,
        "sanitized_rows_status_ref": status_ref,
        "rating_rows_status_ref": status_ref,
        "rsr_op11_status_ref": status_ref,
        "rsr_op11_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP11_ALLOWED_STATUS_REFS),
        "rsr_op11_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP11_ALLOWED_STATUS_REFS),
        "rsr_op11_ready": accepted,
        "rsr_op11_sanitized_review_result_rows_accepted": accepted,
        "rsr_op11_rating_rows_accepted": accepted,
        "rsr_op11_rows_missing_waiting": missing,
        "rsr_op11_rows_invalid_repair_required": invalid,
        "rsr_op11_rows_body_leak_or_source_claim_blocked": blocked,
        "sanitized_review_result_row_schema_version": P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
        "rating_row_schema_version": P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_SCHEMA_VERSION,
        "required_sanitized_review_result_row_field_refs": list(P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS),
        "required_sanitized_review_result_row_field_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS),
        "required_rating_row_field_refs": list(P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_REQUIRED_FIELD_REFS),
        "required_rating_row_field_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_REQUIRED_FIELD_REFS),
        "sanitized_review_result_row_count": len(sanitized_clean_rows) if accepted else 0,
        "rating_row_count": len(rating_clean_rows) if accepted else 0,
        "expected_review_row_count": P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "sanitized_review_result_row_count_is_24": accepted and len(sanitized_clean_rows) == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "rating_row_count_is_24": accepted and len(rating_clean_rows) == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "sanitized_review_result_row_refs": sanitized_meta["row_refs"] if accepted else [],
        "sanitized_review_result_row_ref_count": len(set(sanitized_meta["row_refs"])) if accepted else 0,
        "rating_row_refs": rating_meta["rating_row_refs"] if accepted else [],
        "rating_row_ref_count": len(set(rating_meta["rating_row_refs"])) if accepted else 0,
        "case_ref_values": case_refs,
        "case_ref_count": len(case_refs),
        "case_ref_unique_count": len(set(case_refs)),
        "case_refs_match_between_sanitized_and_rating_rows": bool(accepted and rating_meta["case_refs_match_between_sanitized_and_rating_rows"]),
        "sanitized_review_result_rows": sanitized_clean_rows if accepted else [],
        "rating_rows": rating_clean_rows if accepted else [],
        "sanitized_rows_bodyfree_only": bool(accepted and sanitized_meta["sanitized_rows_bodyfree_only"]),
        "sanitized_rows_selection_only": bool(accepted and sanitized_meta["sanitized_rows_selection_only"]),
        "sanitized_rows_have_actual_person_selection_only_provenance": bool(accepted and sanitized_meta["sanitized_rows_have_actual_person_selection_only_provenance"]),
        "sanitized_rows_have_required_axis_scores": bool(accepted and sanitized_meta["sanitized_rows_have_required_axis_scores"]),
        "sanitized_rows_have_allowed_verdict_refs": bool(accepted and sanitized_meta["sanitized_rows_have_allowed_verdict_refs"]),
        "sanitized_rows_have_allowed_question_observation_refs": bool(accepted and sanitized_meta["sanitized_rows_have_allowed_question_observation_refs"]),
        "sanitized_rows_have_no_body_or_question_or_path_or_hash": bool(accepted and sanitized_meta["sanitized_rows_have_no_body_or_question_or_path_or_hash"]),
        "rating_rows_bodyfree_only": bool(accepted and rating_meta["rating_rows_bodyfree_only"]),
        "rating_rows_from_sanitized_rows": bool(accepted and rating_meta["rating_rows_from_sanitized_rows"]),
        "rating_rows_have_required_axis_scores": bool(accepted and rating_meta["rating_rows_have_required_axis_scores"]),
        "rating_rows_have_no_body_or_question_or_path_or_hash": bool(accepted and rating_meta["rating_rows_have_no_body_or_question_or_path_or_hash"]),
        "rows_operation_receipt_ref_matches": bool(accepted and sanitized_meta["rows_operation_receipt_ref_matches"]),
        "rows_reviewer_person_ref_matches": bool(accepted and sanitized_meta["rows_reviewer_person_ref_matches"]),
        "rows_source_kind_is_actual_local_only_human_review_by_person": bool(accepted and sanitized_meta["rows_source_kind_is_actual_local_only_human_review_by_person"]),
        "review_rows_forbidden_payload_key_path_refs": sanitized_meta["forbidden_paths"],
        "review_rows_forbidden_payload_key_path_count": len(sanitized_meta["forbidden_paths"]),
        "review_rows_body_like_value_path_refs": sanitized_meta["body_like_paths"],
        "review_rows_body_like_value_path_count": len(sanitized_meta["body_like_paths"]),
        "review_rows_promotion_claim_refs": sanitized_meta["promotion_claims"],
        "review_rows_promotion_claim_ref_count": len(sanitized_meta["promotion_claims"]),
        "rating_rows_forbidden_payload_key_path_refs": rating_meta["forbidden_paths"],
        "rating_rows_forbidden_payload_key_path_count": len(rating_meta["forbidden_paths"]),
        "rating_rows_body_like_value_path_refs": rating_meta["body_like_paths"],
        "rating_rows_body_like_value_path_count": len(rating_meta["body_like_paths"]),
        "rating_rows_promotion_claim_refs": rating_meta["promotion_claims"],
        "rating_rows_promotion_claim_ref_count": len(rating_meta["promotion_claims"]),
        "question_text_materialized": False,
        "draft_question_text_materialized": False,
        "p8_question_spec_created": False,
        "p8_question_design_started_here": False,
        "sanitized_review_result_rows_accepted_by_rsr_op11": accepted,
        "rating_rows_accepted_by_rsr_op11": accepted,
        "actual_sanitized_review_result_rows_accepted_without_creation": accepted,
        "actual_rating_rows_accepted_without_creation": accepted,
        "actual_review_rows_and_rating_rows_intaken_bodyfree": accepted,
        "question_need_observation_rows_required_next": accepted,
        "actual_review_evidence_complete_here": False,
        "op11_reason_refs": reasons,
        "op11_reason_ref_count": len(reasons),
        "op11_blocker_refs": blockers,
        "op11_blocker_ref_count": len(blockers),
        "rsr_op11_does_not_create_sanitized_rows_or_rating_rows": True,
        "rsr_op11_does_not_create_question_rows_or_disposal": True,
        "rsr_op11_does_not_materialize_question_text_or_p8_spec": True,
        "rsr_op11_does_not_execute_dmd_or_r52": True,
        "rsr_op11_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op11_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP11 body-free sanitized review result rows / rating rows intake contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP11_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP11")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP11_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP11_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP11_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP11")
    for field, count_field in (("rsr_op11_allowed_status_refs", "rsr_op11_allowed_status_ref_count"), ("required_sanitized_review_result_row_field_refs", "required_sanitized_review_result_row_field_ref_count"), ("required_rating_row_field_refs", "required_rating_row_field_ref_count"), ("sanitized_review_result_row_refs", "sanitized_review_result_row_ref_count"), ("rating_row_refs", "rating_row_ref_count"), ("review_rows_forbidden_payload_key_path_refs", "review_rows_forbidden_payload_key_path_count"), ("review_rows_body_like_value_path_refs", "review_rows_body_like_value_path_count"), ("review_rows_promotion_claim_refs", "review_rows_promotion_claim_ref_count"), ("rating_rows_forbidden_payload_key_path_refs", "rating_rows_forbidden_payload_key_path_count"), ("rating_rows_body_like_value_path_refs", "rating_rows_body_like_value_path_count"), ("rating_rows_promotion_claim_refs", "rating_rows_promotion_claim_ref_count"), ("op11_reason_refs", "op11_reason_ref_count"), ("op11_blocker_refs", "op11_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP11 {count_field} changed")
    if tuple(data.get("rsr_op11_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 allowed status refs changed")
    if tuple(data.get("required_sanitized_review_result_row_field_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 sanitized row required refs changed")
    if tuple(data.get("required_rating_row_field_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 rating row required refs changed")
    for key in ("rsr_op11_does_not_create_sanitized_rows_or_rating_rows", "rsr_op11_does_not_create_question_rows_or_disposal", "rsr_op11_does_not_materialize_question_text_or_p8_spec", "rsr_op11_does_not_execute_dmd_or_r52", "rsr_op11_does_not_start_p5_p6_p8_p7_or_release", "rsr_op11_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP11 required true boundary changed: {key}")
    for key in ("question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here", "actual_review_evidence_complete_here", "actual_sanitized_review_result_rows_materialized_here", "actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "body_full_packet_generated_here", "actual_local_human_review_executed_here", "actual_operation_receipt_created_here", "actual_rows_created_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP11 false boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP11_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP11_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 implemented/not-yet steps changed")
    status_ref = data.get("rsr_op11_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHR09_RSR_OP11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 status ref is not allowed")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_ACCEPTED_BODYFREE_REF:
        for key in ("op10_actual_operation_receipt_accepted", "op10_ready_for_sanitized_review_result_rows_rating_rows_intake", "sanitized_review_result_rows_present", "rating_rows_present", "rsr_op11_sanitized_review_result_rows_accepted", "rsr_op11_rating_rows_accepted", "sanitized_review_result_row_count_is_24", "rating_row_count_is_24", "case_refs_match_between_sanitized_and_rating_rows", "sanitized_rows_bodyfree_only", "sanitized_rows_selection_only", "sanitized_rows_have_actual_person_selection_only_provenance", "sanitized_rows_have_required_axis_scores", "sanitized_rows_have_allowed_verdict_refs", "sanitized_rows_have_allowed_question_observation_refs", "sanitized_rows_have_no_body_or_question_or_path_or_hash", "rating_rows_bodyfree_only", "rating_rows_from_sanitized_rows", "rating_rows_have_required_axis_scores", "rating_rows_have_no_body_or_question_or_path_or_hash", "rows_operation_receipt_ref_matches", "rows_reviewer_person_ref_matches", "rows_source_kind_is_actual_local_only_human_review_by_person", "sanitized_review_result_rows_accepted_by_rsr_op11", "rating_rows_accepted_by_rsr_op11", "actual_sanitized_review_result_rows_accepted_without_creation", "actual_rating_rows_accepted_without_creation", "actual_review_rows_and_rating_rows_intaken_bodyfree", "question_need_observation_rows_required_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP11 accepted branch required true changed: {key}")
        if data.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or data.get("rating_row_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 accepted row count changed")
        if data.get("op11_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 accepted branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 accepted next step changed")
        for row in data.get("sanitized_review_result_rows") or []:
            if set(row) != set(P7_R54_AHR_POST_DHR09_RSR_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS):
                raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 sanitized row field set changed")
            for field in P7_R54_AHR_POST_DHR09_RSR_SANITIZED_ROW_PROVENANCE_FALSE_FIELD_REFS:
                if row.get(field) is not False:
                    raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP11 sanitized row provenance false changed: {field}")
        for row in data.get("rating_rows") or []:
            if set(row) != set(P7_R54_AHR_POST_DHR09_RSR_RATING_ROW_REQUIRED_FIELD_REFS):
                raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 rating row field set changed")
            if row.get("actual_rating_row_from_real_operation") is not True or row.get("rating_decision_material_only") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 rating row boundary changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_MISSING_WAITING_REF:
        if data.get("rsr_op11_rows_missing_waiting") is not True or data.get("rsr_op11_sanitized_review_result_rows_accepted") is not False or data.get("rsr_op11_rating_rows_accepted") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 missing branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op11_rows_invalid_repair_required") is not True or not data.get("op11_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 invalid branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP11_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF:
        if data.get("rsr_op11_rows_body_leak_or_source_claim_blocked") is not True or not data.get("op11_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_REVIEW_ROWS_RATING_ROWS_BODY_LEAK_OR_SOURCE_CLAIM_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP11 blocked next step changed")
    return True




# RSR-OP12/OP13 additions: body-free P7/P8 Bridge observation rows and purge receipt intake.
P7_R54_AHR_POST_DHR09_RSR_OP12_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr."
    "op12_question_need_observation_rows_intake_p7_p8_bridge_material_only.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP13_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.op13_disposal_purge_receipt_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.question_need_observation_row.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr.disposal_purge_receipt.bodyfree.v1"
)

P7_R54_AHR_POST_DHR09_RSR_OP12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:13]
)
P7_R54_AHR_POST_DHR09_RSR_OP12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[13:]
)
P7_R54_AHR_POST_DHR09_RSR_OP13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:14]
)
P7_R54_AHR_POST_DHR09_RSR_OP13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[14:]
)

P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_ACCEPTED_BODYFREE_REF: Final = (
    "RSR_QUESTION_NEED_OBSERVATION_ROWS_ACCEPTED_P7_P8_BRIDGE_MATERIAL_ONLY_BODYFREE"
)
P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_MISSING_WAITING_REF: Final = (
    "RSR_QUESTION_NEED_OBSERVATION_ROWS_MISSING_WAITING"
)
P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = (
    "RSR_QUESTION_NEED_OBSERVATION_ROWS_INVALID_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED_REF: Final = (
    "RSR_QUESTION_NEED_OBSERVATION_ROWS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED"
)
P7_R54_AHR_POST_DHR09_RSR_OP12_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_MISSING_WAITING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_QUESTION_NEED_OBSERVATION_ROWS_BODYFREE_REF: Final = (
    "provide_question_need_observation_rows_bodyfree_as_p7_p8_bridge_material_only"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_QUESTION_NEED_OBSERVATION_ROWS_REF: Final = (
    "repair_question_need_observation_rows_before_disposal_purge_receipt_intake"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_QUESTION_NEED_OBSERVATION_ROWS_BODY_LEAK_OR_MATERIALIZATION_REF: Final = (
    "blocked_question_need_observation_rows_body_leak_or_question_materialization_before_purge"
)

P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF: Final = (
    "RSR_DISPOSAL_PURGE_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_MISSING_WAITING_REF: Final = (
    "RSR_DISPOSAL_PURGE_RECEIPT_MISSING_WAITING"
)
P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF: Final = (
    "RSR_DISPOSAL_PURGE_RECEIPT_INVALID_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF: Final = (
    "RSR_DISPOSAL_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_BLOCKED"
)
P7_R54_AHR_POST_DHR09_RSR_OP13_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_MISSING_WAITING_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_DISPOSAL_PURGE_RECEIPT_BODYFREE_REF: Final = (
    "provide_disposal_purge_receipt_bodyfree_before_final_validation"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DISPOSAL_PURGE_RECEIPT_REF: Final = (
    "repair_disposal_purge_receipt_before_final_no_leak_validation"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_DISPOSAL_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF: Final = (
    "blocked_disposal_purge_receipt_body_leak_or_retention_before_final_validation"
)

P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "question_need_observation_row_ref", "review_session_id", "operation_receipt_ref",
    "source_sanitized_review_result_row_ref", "source_rating_row_ref", "case_ref", "reviewer_person_ref",
    "source_kind_ref", "question_need_primary_class_ref", "ambiguity_kind_refs", "one_question_fit_ref",
    "p7_p8_bridge_material_only", "p8_design_material_candidate_only", "question_observation_material_only",
    "question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created",
    "p8_question_design_started", "row_created_by_helper", "row_created_for_unit_test",
    "row_is_synthetic_contract_fixture", "historical_row_reused", "body_free",
)
P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_TRUE_REFS: Final[tuple[str, ...]] = (
    "p7_p8_bridge_material_only", "p8_design_material_candidate_only", "question_observation_material_only", "body_free",
)
P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_FALSE_REFS: Final[tuple[str, ...]] = (
    "question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created",
    "p8_question_design_started", "row_created_by_helper", "row_created_for_unit_test",
    "row_is_synthetic_contract_fixture", "historical_row_reused",
)
P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "disposal_purge_receipt_ref", "review_session_id", "operation_receipt_ref",
    "packet_request_ref", "source_kind_ref", "body_full_packet_retained", "local_temp_material_retained",
    "reviewer_working_form_body_retained", "external_export_performed", "purge_completed",
    "raw_input_included", "comment_text_body_included", "returned_surface_body_included",
    "reviewer_free_text_included", "reviewer_note_body_included", "question_text_included",
    "draft_question_text_included", "answer_text_included", "local_path_included", "body_hash_included",
    "terminal_output_body_included", "body_free",
)
P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_retained", "local_temp_material_retained", "reviewer_working_form_body_retained",
    "external_export_performed", "raw_input_included", "comment_text_body_included",
    "returned_surface_body_included", "reviewer_free_text_included", "reviewer_note_body_included",
    "question_text_included", "draft_question_text_included", "answer_text_included", "local_path_included",
    "body_hash_included", "terminal_output_body_included",
)

P7_R54_AHR_POST_DHR09_RSR_OP12_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op11_contract_valid", "op11_status_ref", "op11_sanitized_review_result_rows_accepted", "op11_rating_rows_accepted",
    "op11_question_need_observation_rows_required_next", "op11_next_required_step", "operation_receipt_ref", "operation_receipt_packet_request_ref", "reviewer_person_ref",
    "question_need_observation_rows_present", "question_need_observation_rows_contract_valid", "question_need_observation_row_schema_version",
    "required_question_need_observation_row_field_refs", "required_question_need_observation_row_field_ref_count", "question_need_observation_row_count", "expected_question_need_observation_row_count",
    "question_need_observation_row_count_is_24", "question_need_observation_row_refs", "question_need_observation_row_ref_count", "source_sanitized_review_result_row_refs", "source_sanitized_review_result_row_ref_count",
    "source_rating_row_refs", "source_rating_row_ref_count", "case_ref_values", "case_ref_count", "case_ref_unique_count", "question_need_rows_match_op11_case_refs",
    "question_need_observation_rows", "question_need_observation_rows_bodyfree_only", "question_need_observation_rows_from_review_rows_and_rating_rows", "question_need_observation_rows_have_actual_person_source",
    "question_need_observation_rows_have_allowed_classes", "question_need_observation_rows_material_only", "question_need_observation_rows_have_no_question_text_or_p8_spec",
    "p7_p8_bridge_material_only", "p8_design_material_candidate_only", "question_observation_material_only", "question_text_materialized", "draft_question_text_materialized",
    "p8_question_spec_created", "p8_question_design_started_here", "p8_question_design_started_by_rows",
    "question_need_observation_rows_forbidden_payload_key_path_refs", "question_need_observation_rows_forbidden_payload_key_path_count",
    "question_need_observation_rows_body_like_value_path_refs", "question_need_observation_rows_body_like_value_path_count", "question_need_observation_rows_promotion_claim_refs", "question_need_observation_rows_promotion_claim_ref_count",
    "rsr_op12_status_ref", "rsr_op12_allowed_status_refs", "rsr_op12_allowed_status_ref_count", "rsr_op12_ready", "rsr_op12_question_need_observation_rows_accepted",
    "rsr_op12_question_need_observation_rows_missing_waiting", "rsr_op12_question_need_observation_rows_invalid_repair_required", "rsr_op12_question_need_observation_rows_body_leak_or_question_materialization_blocked",
    "question_need_observation_rows_accepted_by_rsr_op12", "actual_question_need_observation_rows_accepted_without_creation", "actual_question_need_observation_rows_intaken_bodyfree",
    "disposal_purge_receipt_required_next", "actual_review_evidence_complete_here", "op12_reason_refs", "op12_reason_ref_count", "op12_blocker_refs", "op12_blocker_ref_count",
    "rsr_op12_does_not_create_question_need_rows", "rsr_op12_does_not_materialize_question_text_or_p8_spec", "rsr_op12_does_not_execute_disposal_purge", "rsr_op12_does_not_execute_dmd_or_r52",
    "rsr_op12_does_not_start_p5_p6_p8_p7_or_release", "rsr_op12_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DHR09_RSR_OP13_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op12_contract_valid", "op12_status_ref", "op12_question_need_observation_rows_accepted", "op12_disposal_purge_receipt_required_next", "op12_next_required_step",
    "operation_receipt_ref", "packet_request_ref", "reviewer_person_ref", "disposal_purge_receipt_present", "disposal_purge_receipt_contract_valid", "disposal_purge_receipt_schema_version",
    "disposal_purge_receipt_ref", "disposal_purge_receipt_review_session_id", "disposal_purge_receipt_operation_receipt_ref", "disposal_purge_receipt_packet_request_ref", "disposal_purge_receipt_source_kind_ref",
    "disposal_purge_receipt_review_session_id_matches", "disposal_purge_receipt_operation_receipt_ref_matches", "disposal_purge_receipt_packet_request_ref_matches", "disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person",
    "disposal_purge_receipt_body_full_packet_retained", "disposal_purge_receipt_local_temp_material_retained", "disposal_purge_receipt_reviewer_working_form_body_retained", "disposal_purge_receipt_external_export_performed",
    "disposal_purge_receipt_purge_completed", "disposal_purge_receipt_body_free", "disposal_purge_receipt_raw_input_included", "disposal_purge_receipt_comment_text_body_included", "disposal_purge_receipt_returned_surface_body_included",
    "disposal_purge_receipt_reviewer_free_text_included", "disposal_purge_receipt_reviewer_note_body_included", "disposal_purge_receipt_question_text_included", "disposal_purge_receipt_draft_question_text_included",
    "disposal_purge_receipt_answer_text_included", "disposal_purge_receipt_local_path_included", "disposal_purge_receipt_body_hash_included", "disposal_purge_receipt_terminal_output_body_included",
    "disposal_purge_receipt_forbidden_payload_key_path_refs", "disposal_purge_receipt_forbidden_payload_key_path_count", "disposal_purge_receipt_body_like_value_path_refs", "disposal_purge_receipt_body_like_value_path_count",
    "disposal_purge_receipt_promotion_claim_refs", "disposal_purge_receipt_promotion_claim_ref_count", "disposal_purge_receipt_retention_or_export_blocker_refs", "disposal_purge_receipt_retention_or_export_blocker_ref_count",
    "rsr_op13_status_ref", "rsr_op13_allowed_status_refs", "rsr_op13_allowed_status_ref_count", "rsr_op13_ready", "rsr_op13_disposal_purge_receipt_accepted", "rsr_op13_disposal_purge_receipt_missing_waiting",
    "rsr_op13_disposal_purge_receipt_invalid_repair_required", "rsr_op13_disposal_purge_receipt_body_leak_or_retention_blocked", "disposal_purge_receipt_accepted_by_rsr_op13",
    "disposal_purge_receipt_accepted_without_purge_execution_by_helper", "body_full_transient_material_reported_purged", "local_temp_material_reported_purged", "reviewer_working_form_body_reported_purged",
    "final_no_leak_source_kind_validation_required_next", "actual_review_evidence_complete_here", "op13_reason_refs", "op13_reason_ref_count", "op13_blocker_refs", "op13_blocker_ref_count",
    "helper_executes_disposal_purge", "actual_disposal_purge_executed_here_by_helper", "rsr_op13_does_not_execute_disposal_purge", "rsr_op13_does_not_perform_final_no_leak_validation", "rsr_op13_does_not_complete_actual_evidence",
    "rsr_op13_does_not_execute_dmd_or_r52", "rsr_op13_does_not_start_p5_p6_p8_p7_or_release", "rsr_op13_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _validate_rsr_op12_question_need_rows(op11: Mapping[str, Any], rows_value: Any) -> tuple[bool, list[dict[str, Any]], list[str], dict[str, Any]]:
    present, raw_rows = _sequence_rows(rows_value)
    if not present:
        return False, [], ["question_need_observation_rows_missing"], {
            "row_refs": [], "case_refs": [], "source_review_refs": [], "source_rating_refs": [],
            "forbidden_paths": [], "body_like_paths": [], "promotion_claims": [],
            "question_need_observation_rows_bodyfree_only": False,
            "question_need_observation_rows_from_review_rows_and_rating_rows": False,
            "question_need_observation_rows_have_actual_person_source": False,
            "question_need_observation_rows_have_allowed_classes": False,
            "question_need_observation_rows_material_only": False,
            "question_need_observation_rows_have_no_question_text_or_p8_spec": False,
            "case_refs_match": False,
        }
    review_session_id = _safe_review_session_id(op11.get("review_session_id"))
    operation_receipt_ref = _safe_bodyfree_ref(op11.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220)
    reviewer_person_ref = _safe_bodyfree_ref(op11.get("reviewer_person_ref"), default="reviewer_person_ref_missing", max_length=180)
    sanitized_by_case = {str(row.get("case_ref")): str(row.get("review_result_row_ref")) for row in (op11.get("sanitized_review_result_rows") or []) if isinstance(row, Mapping)}
    rating_by_case = {str(row.get("case_ref")): str(row.get("rating_row_ref")) for row in (op11.get("rating_rows") or []) if isinstance(row, Mapping)}
    forbidden = _scan_forbidden_payload_key_paths({"question_need_observation_rows": raw_rows}, path="question_need_observation_rows")
    body_like = _scan_body_like_value_paths({"question_need_observation_rows": raw_rows}, path="question_need_observation_rows")
    promotion_claims: list[str] = []
    blockers: list[str] = []
    clean_rows: list[dict[str, Any]] = []
    row_refs: list[str] = []
    case_refs: list[str] = []
    source_review_refs: list[str] = []
    source_rating_refs: list[str] = []
    if len(raw_rows) != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
        blockers.append("question_need_observation_row_count_not_24")
    flags = {
        "question_need_observation_rows_bodyfree_only": True,
        "question_need_observation_rows_from_review_rows_and_rating_rows": True,
        "question_need_observation_rows_have_actual_person_source": True,
        "question_need_observation_rows_have_allowed_classes": True,
        "question_need_observation_rows_material_only": True,
        "question_need_observation_rows_have_no_question_text_or_p8_spec": True,
    }
    for index, raw in enumerate(raw_rows, start=1):
        if not isinstance(raw, Mapping):
            blockers.append("question_need_observation_row_not_mapping")
            flags["question_need_observation_rows_bodyfree_only"] = False
            continue
        promotion_claims.extend(_promotion_claim_refs(raw))
        if set(raw) != set(P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS):
            blockers.append("question_need_observation_row_required_fields_mismatch")
            flags["question_need_observation_rows_bodyfree_only"] = False
        if raw.get("schema_version") != P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
            blockers.append("question_need_observation_row_schema_version_mismatch")
        row_ref = _safe_bodyfree_ref(raw.get("question_need_observation_row_ref"), default=f"invalid_question_need_observation_row_ref_{index:03d}", max_length=220)
        case_ref = _safe_bodyfree_ref(raw.get("case_ref"), default=f"invalid_question_need_case_ref_{index:03d}", max_length=180)
        source_review_ref = _safe_bodyfree_ref(raw.get("source_sanitized_review_result_row_ref"), default="missing_source_sanitized_review_result_row_ref", max_length=220)
        source_rating_ref = _safe_bodyfree_ref(raw.get("source_rating_row_ref"), default="missing_source_rating_row_ref", max_length=220)
        ambiguity_refs, ambiguity_blockers = _rsr_ref_list(raw.get("ambiguity_kind_refs"), field="question_need_observation_row_ambiguity_kind_refs")
        blockers.extend(ambiguity_blockers)
        if raw.get("review_session_id") != review_session_id:
            blockers.append("question_need_observation_row_review_session_id_mismatch")
        if raw.get("operation_receipt_ref") != operation_receipt_ref:
            blockers.append("question_need_observation_row_operation_receipt_ref_mismatch")
        if raw.get("reviewer_person_ref") != reviewer_person_ref:
            blockers.append("question_need_observation_row_reviewer_person_ref_mismatch")
        if source_review_ref != sanitized_by_case.get(case_ref):
            blockers.append("question_need_observation_row_source_sanitized_review_result_row_ref_mismatch")
            flags["question_need_observation_rows_from_review_rows_and_rating_rows"] = False
        if source_rating_ref != rating_by_case.get(case_ref):
            blockers.append("question_need_observation_row_source_rating_row_ref_mismatch")
            flags["question_need_observation_rows_from_review_rows_and_rating_rows"] = False
        if _safe_bodyfree_ref(raw.get("source_kind_ref"), default="source_kind_ref_missing", max_length=220) != P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
            blockers.append("question_need_observation_row_source_kind_not_actual_local_only_human_review_by_person")
            flags["question_need_observation_rows_have_actual_person_source"] = False
        if raw.get("question_need_primary_class_ref") not in P7_R54_AHR_POST_DHR09_RSR_OP08_QUESTION_NEED_CLASS_REFS:
            blockers.append("question_need_observation_row_question_need_class_not_allowed")
            flags["question_need_observation_rows_have_allowed_classes"] = False
        for field in P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_TRUE_REFS:
            if raw.get(field) is not True:
                blockers.append(f"question_need_observation_row_{field}_not_true")
                if field in ("p7_p8_bridge_material_only", "p8_design_material_candidate_only", "question_observation_material_only"):
                    flags["question_need_observation_rows_material_only"] = False
                if field == "body_free":
                    flags["question_need_observation_rows_bodyfree_only"] = False
        for field in P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_FALSE_REFS:
            if raw.get(field) is not False:
                blockers.append(f"question_need_observation_row_{field}_not_false")
                if field in ("question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started"):
                    flags["question_need_observation_rows_have_no_question_text_or_p8_spec"] = False
                else:
                    flags["question_need_observation_rows_have_actual_person_source"] = False
        row_refs.append(row_ref)
        case_refs.append(case_ref)
        source_review_refs.append(source_review_ref)
        source_rating_refs.append(source_rating_ref)
        clean_rows.append({
            "schema_version": P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
            "question_need_observation_row_ref": row_ref,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "source_sanitized_review_result_row_ref": source_review_ref,
            "source_rating_row_ref": source_rating_ref,
            "case_ref": case_ref,
            "reviewer_person_ref": reviewer_person_ref,
            "source_kind_ref": P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
            "question_need_primary_class_ref": _safe_bodyfree_ref(raw.get("question_need_primary_class_ref"), default="insufficient_material_execution_blocker", max_length=180),
            "ambiguity_kind_refs": ambiguity_refs,
            "one_question_fit_ref": _safe_bodyfree_ref(raw.get("one_question_fit_ref"), default="one_question_fit_ref_missing", max_length=180),
            "p7_p8_bridge_material_only": raw.get("p7_p8_bridge_material_only") is True,
            "p8_design_material_candidate_only": raw.get("p8_design_material_candidate_only") is True,
            "question_observation_material_only": raw.get("question_observation_material_only") is True,
            "question_text_materialized": raw.get("question_text_materialized") is True,
            "draft_question_text_materialized": raw.get("draft_question_text_materialized") is True,
            "p8_question_spec_created": raw.get("p8_question_spec_created") is True,
            "p8_question_design_started": raw.get("p8_question_design_started") is True,
            "row_created_by_helper": raw.get("row_created_by_helper") is True,
            "row_created_for_unit_test": raw.get("row_created_for_unit_test") is True,
            "row_is_synthetic_contract_fixture": raw.get("row_is_synthetic_contract_fixture") is True,
            "historical_row_reused": raw.get("historical_row_reused") is True,
            "body_free": raw.get("body_free") is True,
        })
    if forbidden:
        blockers.append("question_need_observation_rows_forbidden_payload_key_detected")
    if body_like:
        blockers.append("question_need_observation_rows_body_like_value_detected")
    if promotion_claims:
        blockers.append("question_need_observation_rows_promotion_claim_detected")
    if len(set(row_refs)) != len(row_refs):
        blockers.append("question_need_observation_row_ref_duplicate_detected")
    case_refs_match = set(case_refs) == set(str(ref) for ref in (op11.get("case_ref_values") or [])) and len(case_refs) == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    if not case_refs_match:
        blockers.append("question_need_observation_row_case_refs_do_not_match_op11")
    return True, clean_rows, _dedupe_clean_refs(blockers), {
        **flags,
        "row_refs": row_refs,
        "case_refs": case_refs,
        "source_review_refs": source_review_refs,
        "source_rating_refs": source_rating_refs,
        "forbidden_paths": forbidden,
        "body_like_paths": body_like,
        "promotion_claims": _dedupe_clean_refs(promotion_claims),
        "case_refs_match": case_refs_match,
    }


def build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(
    *,
    review_rows_rating_rows_intake: Mapping[str, Any] | None = None,
    op11_sanitized_review_result_rows_rating_rows_intake: Mapping[str, Any] | None = None,
    question_need_observation_rows_optional: Sequence[Mapping[str, Any]] | None = None,
    question_need_observation_rows: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP12 body-free question-need observation rows intake material.

    OP12 accepts question-need observations only as P7/P8 Bridge material. It never
    materializes question text, starts P8 design, creates rows, runs purge, or
    completes actual evidence.
    """
    op11 = review_rows_rating_rows_intake if review_rows_rating_rows_intake is not None else op11_sanitized_review_result_rows_rating_rows_intake
    if op11 is None:
        op11 = build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op11.get("review_session_id") if isinstance(op11, Mapping) else None))
    try:
        op11_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract(op11) is True
    except ValueError:
        op11_contract_valid = False
    op11_status_ref = _bodyfree_status_ref(op11.get("rsr_op11_status_ref") if isinstance(op11, Mapping) else None, default="rsr_op11_status_missing")
    op11_sanitized_accepted = bool(op11_contract_valid and op11.get("rsr_op11_sanitized_review_result_rows_accepted") is True)
    op11_rating_accepted = bool(op11_contract_valid and op11.get("rsr_op11_rating_rows_accepted") is True)
    op11_question_required = bool(op11_contract_valid and op11.get("question_need_observation_rows_required_next") is True and op11.get("next_required_step") == P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF)
    op11_next = _bodyfree_status_ref(op11.get("next_required_step") if isinstance(op11, Mapping) else None, default="rsr_op11_next_required_step_missing")
    operation_receipt_ref = _safe_bodyfree_ref(op11.get("operation_receipt_ref") if isinstance(op11, Mapping) else None, default="missing_or_invalid_operation_receipt_ref", max_length=220)
    packet_request_ref = _safe_bodyfree_ref(op11.get("operation_receipt_packet_request_ref") if isinstance(op11, Mapping) else None, default="missing_or_invalid_packet_request_ref", max_length=220)
    reviewer_person_ref = _safe_bodyfree_ref(op11.get("reviewer_person_ref") if isinstance(op11, Mapping) else None, default="missing_or_invalid_reviewer_person_ref", max_length=180)
    rows_input = question_need_observation_rows if question_need_observation_rows is not None else question_need_observation_rows_optional
    rows_present, clean_rows, row_blockers, row_meta = _validate_rsr_op12_question_need_rows(op11, rows_input)
    blockers: list[str] = []
    reasons: list[str] = []
    if not op11_contract_valid:
        blockers.append("op11_review_rows_rating_rows_intake_contract_invalid_or_missing")
    elif not (op11_sanitized_accepted and op11_rating_accepted and op11_question_required):
        blockers.append("op11_review_rows_rating_rows_not_accepted_or_question_need_rows_not_required")
    if rows_present:
        blockers.extend(ref for ref in row_blockers if ref != "question_need_observation_rows_missing")
    if not rows_present:
        if op11_sanitized_accepted and op11_rating_accepted and op11_question_required:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_MISSING_WAITING_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_QUESTION_NEED_OBSERVATION_ROWS_BODYFREE_REF
            reasons.append("question_need_observation_rows_missing_waiting_bodyfree")
        else:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_INVALID_REPAIR_REQUIRED_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_QUESTION_NEED_OBSERVATION_ROWS_REF
            reasons.append("op11_prerequisite_repair_required_before_question_need_rows")
    elif row_meta["forbidden_paths"] or row_meta["body_like_paths"] or row_meta["promotion_claims"] or not row_meta["question_need_observation_rows_have_no_question_text_or_p8_spec"]:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_QUESTION_NEED_OBSERVATION_ROWS_BODY_LEAK_OR_MATERIALIZATION_REF
        reasons.append("question_need_observation_rows_body_leak_or_question_materialization_blocked")
    elif op11_sanitized_accepted and op11_rating_accepted and op11_question_required and not blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_ACCEPTED_BODYFREE_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF
        reasons.append("question_need_observation_rows_accepted_as_p7_p8_bridge_material_only")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_INVALID_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_QUESTION_NEED_OBSERVATION_ROWS_REF
        reasons.append("question_need_observation_rows_invalid_or_repair_required")
    blockers = _dedupe_clean_refs(blockers)
    reasons = _dedupe_clean_refs(reasons)
    accepted = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_ACCEPTED_BODYFREE_REF
    missing = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_MISSING_WAITING_REF
    invalid = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_INVALID_REPAIR_REQUIRED_REF
    blocked = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED_REF
    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP12_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op11_contract_valid": op11_contract_valid,
        "op11_status_ref": op11_status_ref,
        "op11_sanitized_review_result_rows_accepted": op11_sanitized_accepted,
        "op11_rating_rows_accepted": op11_rating_accepted,
        "op11_question_need_observation_rows_required_next": op11_question_required,
        "op11_next_required_step": op11_next,
        "operation_receipt_ref": operation_receipt_ref,
        "operation_receipt_packet_request_ref": packet_request_ref,
        "reviewer_person_ref": reviewer_person_ref,
        "question_need_observation_rows_present": rows_present,
        "question_need_observation_rows_contract_valid": accepted,
        "question_need_observation_row_schema_version": P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "required_question_need_observation_row_field_refs": list(P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "required_question_need_observation_row_field_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_observation_row_count": len(clean_rows) if accepted else 0,
        "expected_question_need_observation_row_count": P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "question_need_observation_row_count_is_24": accepted and len(clean_rows) == P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT,
        "question_need_observation_row_refs": row_meta["row_refs"] if accepted else [],
        "question_need_observation_row_ref_count": len(set(row_meta["row_refs"])) if accepted else 0,
        "source_sanitized_review_result_row_refs": row_meta["source_review_refs"] if accepted else [],
        "source_sanitized_review_result_row_ref_count": len(set(row_meta["source_review_refs"])) if accepted else 0,
        "source_rating_row_refs": row_meta["source_rating_refs"] if accepted else [],
        "source_rating_row_ref_count": len(set(row_meta["source_rating_refs"])) if accepted else 0,
        "case_ref_values": row_meta["case_refs"] if accepted else [],
        "case_ref_count": len(row_meta["case_refs"]) if accepted else 0,
        "case_ref_unique_count": len(set(row_meta["case_refs"])) if accepted else 0,
        "question_need_rows_match_op11_case_refs": bool(accepted and row_meta["case_refs_match"]),
        "question_need_observation_rows": clean_rows if accepted else [],
        "question_need_observation_rows_bodyfree_only": bool(accepted and row_meta["question_need_observation_rows_bodyfree_only"]),
        "question_need_observation_rows_from_review_rows_and_rating_rows": bool(accepted and row_meta["question_need_observation_rows_from_review_rows_and_rating_rows"]),
        "question_need_observation_rows_have_actual_person_source": bool(accepted and row_meta["question_need_observation_rows_have_actual_person_source"]),
        "question_need_observation_rows_have_allowed_classes": bool(accepted and row_meta["question_need_observation_rows_have_allowed_classes"]),
        "question_need_observation_rows_material_only": bool(accepted and row_meta["question_need_observation_rows_material_only"]),
        "question_need_observation_rows_have_no_question_text_or_p8_spec": bool(accepted and row_meta["question_need_observation_rows_have_no_question_text_or_p8_spec"]),
        "p7_p8_bridge_material_only": accepted,
        "p8_design_material_candidate_only": accepted,
        "question_observation_material_only": accepted,
        "question_text_materialized": False,
        "draft_question_text_materialized": False,
        "p8_question_spec_created": False,
        "p8_question_design_started_here": False,
        "p8_question_design_started_by_rows": False,
        "question_need_observation_rows_forbidden_payload_key_path_refs": row_meta["forbidden_paths"],
        "question_need_observation_rows_forbidden_payload_key_path_count": len(row_meta["forbidden_paths"]),
        "question_need_observation_rows_body_like_value_path_refs": row_meta["body_like_paths"],
        "question_need_observation_rows_body_like_value_path_count": len(row_meta["body_like_paths"]),
        "question_need_observation_rows_promotion_claim_refs": row_meta["promotion_claims"],
        "question_need_observation_rows_promotion_claim_ref_count": len(row_meta["promotion_claims"]),
        "rsr_op12_status_ref": status_ref,
        "rsr_op12_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP12_ALLOWED_STATUS_REFS),
        "rsr_op12_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP12_ALLOWED_STATUS_REFS),
        "rsr_op12_ready": accepted,
        "rsr_op12_question_need_observation_rows_accepted": accepted,
        "rsr_op12_question_need_observation_rows_missing_waiting": missing,
        "rsr_op12_question_need_observation_rows_invalid_repair_required": invalid,
        "rsr_op12_question_need_observation_rows_body_leak_or_question_materialization_blocked": blocked,
        "question_need_observation_rows_accepted_by_rsr_op12": accepted,
        "actual_question_need_observation_rows_accepted_without_creation": accepted,
        "actual_question_need_observation_rows_intaken_bodyfree": accepted,
        "disposal_purge_receipt_required_next": accepted,
        "actual_review_evidence_complete_here": False,
        "op12_reason_refs": reasons,
        "op12_reason_ref_count": len(reasons),
        "op12_blocker_refs": blockers,
        "op12_blocker_ref_count": len(blockers),
        "rsr_op12_does_not_create_question_need_rows": True,
        "rsr_op12_does_not_materialize_question_text_or_p8_spec": True,
        "rsr_op12_does_not_execute_disposal_purge": True,
        "rsr_op12_does_not_execute_dmd_or_r52": True,
        "rsr_op12_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op12_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP12_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP12 P7/P8 Bridge question-need row intake contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP12_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP12")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP12_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP12_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP12_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP12")
    for field, count_field in (("rsr_op12_allowed_status_refs", "rsr_op12_allowed_status_ref_count"), ("required_question_need_observation_row_field_refs", "required_question_need_observation_row_field_ref_count"), ("question_need_observation_row_refs", "question_need_observation_row_ref_count"), ("source_sanitized_review_result_row_refs", "source_sanitized_review_result_row_ref_count"), ("source_rating_row_refs", "source_rating_row_ref_count"), ("question_need_observation_rows_forbidden_payload_key_path_refs", "question_need_observation_rows_forbidden_payload_key_path_count"), ("question_need_observation_rows_body_like_value_path_refs", "question_need_observation_rows_body_like_value_path_count"), ("question_need_observation_rows_promotion_claim_refs", "question_need_observation_rows_promotion_claim_ref_count"), ("op12_reason_refs", "op12_reason_ref_count"), ("op12_blocker_refs", "op12_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP12 {count_field} changed")
    if tuple(data.get("rsr_op12_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 allowed status refs changed")
    if tuple(data.get("required_question_need_observation_row_field_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 required row refs changed")
    for key in ("rsr_op12_does_not_create_question_need_rows", "rsr_op12_does_not_materialize_question_text_or_p8_spec", "rsr_op12_does_not_execute_disposal_purge", "rsr_op12_does_not_execute_dmd_or_r52", "rsr_op12_does_not_start_p5_p6_p8_p7_or_release", "rsr_op12_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP12 required true boundary changed: {key}")
    for key in ("question_text_materialized", "draft_question_text_materialized", "p8_question_spec_created", "p8_question_design_started_here", "p8_question_design_started_by_rows", "actual_review_evidence_complete_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP12 false boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP12_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP12_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 implemented/not-yet steps changed")
    status_ref = data.get("rsr_op12_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHR09_RSR_OP12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 status ref is not allowed")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_ACCEPTED_BODYFREE_REF:
        for key in ("op11_sanitized_review_result_rows_accepted", "op11_rating_rows_accepted", "op11_question_need_observation_rows_required_next", "question_need_observation_rows_present", "question_need_observation_rows_contract_valid", "question_need_observation_row_count_is_24", "question_need_rows_match_op11_case_refs", "question_need_observation_rows_bodyfree_only", "question_need_observation_rows_from_review_rows_and_rating_rows", "question_need_observation_rows_have_actual_person_source", "question_need_observation_rows_have_allowed_classes", "question_need_observation_rows_material_only", "question_need_observation_rows_have_no_question_text_or_p8_spec", "p7_p8_bridge_material_only", "p8_design_material_candidate_only", "question_observation_material_only", "rsr_op12_question_need_observation_rows_accepted", "question_need_observation_rows_accepted_by_rsr_op12", "actual_question_need_observation_rows_accepted_without_creation", "actual_question_need_observation_rows_intaken_bodyfree", "disposal_purge_receipt_required_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP12 accepted branch required true changed: {key}")
        if data.get("question_need_observation_row_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 accepted row count changed")
        if data.get("op12_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 accepted branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 accepted next step changed")
        for row in data.get("question_need_observation_rows") or []:
            if set(row) != set(P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS):
                raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 row field set changed")
            for key in P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_TRUE_REFS:
                if row.get(key) is not True:
                    raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP12 row true boundary changed: {key}")
            for key in P7_R54_AHR_POST_DHR09_RSR_QUESTION_NEED_OBSERVATION_ROW_FALSE_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP12 row false boundary changed: {key}")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_MISSING_WAITING_REF:
        if data.get("rsr_op12_question_need_observation_rows_missing_waiting") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_QUESTION_NEED_OBSERVATION_ROWS_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 missing branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op12_question_need_observation_rows_invalid_repair_required") is not True or not data.get("op12_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 invalid branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP12_STATUS_BODY_LEAK_OR_QUESTION_MATERIALIZATION_BLOCKED_REF:
        if data.get("rsr_op12_question_need_observation_rows_body_leak_or_question_materialization_blocked") is not True or not data.get("op12_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_QUESTION_NEED_OBSERVATION_ROWS_BODY_LEAK_OR_MATERIALIZATION_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP12 blocked next step changed")
    return True


def _validate_rsr_op13_disposal_purge_receipt(op12: Mapping[str, Any], receipt: Any) -> tuple[bool, dict[str, Any], list[str], list[str], dict[str, Any]]:
    if not isinstance(receipt, Mapping):
        return False, {}, ["disposal_purge_receipt_missing"], [], {
            "forbidden_paths": [], "body_like_paths": [], "promotion_claims": [], "retention_or_export_blockers": []
        }
    operation_receipt_ref = _safe_bodyfree_ref(op12.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220)
    packet_request_ref = _safe_bodyfree_ref(op12.get("operation_receipt_packet_request_ref"), default="packet_request_ref_missing", max_length=220)
    review_session_id = _safe_review_session_id(op12.get("review_session_id"))
    blockers: list[str] = []
    retention_or_export_blockers: list[str] = []
    if set(receipt) != set(P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_REQUIRED_FIELD_REFS):
        blockers.append("disposal_purge_receipt_required_fields_mismatch")
    if receipt.get("schema_version") != P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION:
        blockers.append("disposal_purge_receipt_schema_version_mismatch")
    if receipt.get("review_session_id") != review_session_id:
        blockers.append("disposal_purge_receipt_review_session_id_mismatch")
    if _safe_bodyfree_ref(receipt.get("operation_receipt_ref"), default="operation_receipt_ref_missing", max_length=220) != operation_receipt_ref:
        blockers.append("disposal_purge_receipt_operation_receipt_ref_mismatch")
    if _safe_bodyfree_ref(receipt.get("packet_request_ref"), default="packet_request_ref_missing", max_length=220) != packet_request_ref:
        blockers.append("disposal_purge_receipt_packet_request_ref_mismatch")
    if _safe_bodyfree_ref(receipt.get("source_kind_ref"), default="source_kind_ref_missing", max_length=220) != P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
        blockers.append("disposal_purge_receipt_source_kind_not_actual_local_only_human_review_by_person")
    for field in P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_FALSE_FIELD_REFS:
        if receipt.get(field) is not False:
            retention_or_export_blockers.append(f"disposal_purge_receipt_{field}_not_false")
    if receipt.get("purge_completed") is not True:
        blockers.append("disposal_purge_receipt_purge_completed_not_true")
    if receipt.get("body_free") is not True:
        blockers.append("disposal_purge_receipt_body_free_not_true")
    forbidden = _scan_forbidden_payload_key_paths({"disposal_purge_receipt": receipt}, path="disposal_purge_receipt")
    body_like = _scan_body_like_value_paths({"disposal_purge_receipt": receipt}, path="disposal_purge_receipt")
    promotion_claims = _promotion_claim_refs(receipt)
    clean_receipt = {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_DISPOSAL_PURGE_RECEIPT_SCHEMA_VERSION,
        "disposal_purge_receipt_ref": _safe_bodyfree_ref(receipt.get("disposal_purge_receipt_ref"), default="disposal_purge_receipt_ref_missing", max_length=220),
        "review_session_id": review_session_id,
        "operation_receipt_ref": operation_receipt_ref,
        "packet_request_ref": packet_request_ref,
        "source_kind_ref": P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF,
        "body_full_packet_retained": receipt.get("body_full_packet_retained") is True,
        "local_temp_material_retained": receipt.get("local_temp_material_retained") is True,
        "reviewer_working_form_body_retained": receipt.get("reviewer_working_form_body_retained") is True,
        "external_export_performed": receipt.get("external_export_performed") is True,
        "purge_completed": receipt.get("purge_completed") is True,
        "raw_input_included": receipt.get("raw_input_included") is True,
        "comment_text_body_included": receipt.get("comment_text_body_included") is True,
        "returned_surface_body_included": receipt.get("returned_surface_body_included") is True,
        "reviewer_free_text_included": receipt.get("reviewer_free_text_included") is True,
        "reviewer_note_body_included": receipt.get("reviewer_note_body_included") is True,
        "question_text_included": receipt.get("question_text_included") is True,
        "draft_question_text_included": receipt.get("draft_question_text_included") is True,
        "answer_text_included": receipt.get("answer_text_included") is True,
        "local_path_included": receipt.get("local_path_included") is True,
        "body_hash_included": receipt.get("body_hash_included") is True,
        "terminal_output_body_included": receipt.get("terminal_output_body_included") is True,
        "body_free": receipt.get("body_free") is True,
    }
    return True, clean_receipt, _dedupe_clean_refs(blockers), _dedupe_clean_refs(retention_or_export_blockers), {
        "forbidden_paths": forbidden,
        "body_like_paths": body_like,
        "promotion_claims": _dedupe_clean_refs(promotion_claims),
        "retention_or_export_blockers": _dedupe_clean_refs(retention_or_export_blockers),
    }


def build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
    *,
    question_need_observation_rows_intake: Mapping[str, Any] | None = None,
    op12_question_need_observation_rows_intake: Mapping[str, Any] | None = None,
    disposal_purge_receipt_optional: Mapping[str, Any] | None = None,
    disposal_purge_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP13 body-free disposal / purge receipt intake material."""
    op12 = question_need_observation_rows_intake if question_need_observation_rows_intake is not None else op12_question_need_observation_rows_intake
    if op12 is None:
        op12 = build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op12.get("review_session_id") if isinstance(op12, Mapping) else None))
    try:
        op12_contract_valid = assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract(op12) is True
    except ValueError:
        op12_contract_valid = False
    op12_status_ref = _bodyfree_status_ref(op12.get("rsr_op12_status_ref") if isinstance(op12, Mapping) else None, default="rsr_op12_status_missing")
    op12_accepted = bool(op12_contract_valid and op12.get("rsr_op12_question_need_observation_rows_accepted") is True and op12.get("next_required_step") == P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF)
    op12_purge_required = bool(op12_contract_valid and op12.get("disposal_purge_receipt_required_next") is True)
    op12_next = _bodyfree_status_ref(op12.get("next_required_step") if isinstance(op12, Mapping) else None, default="rsr_op12_next_required_step_missing")
    operation_receipt_ref = _safe_bodyfree_ref(op12.get("operation_receipt_ref") if isinstance(op12, Mapping) else None, default="missing_or_invalid_operation_receipt_ref", max_length=220)
    packet_request_ref = _safe_bodyfree_ref(op12.get("operation_receipt_packet_request_ref") if isinstance(op12, Mapping) else None, default="missing_or_invalid_packet_request_ref", max_length=220)
    reviewer_person_ref = _safe_bodyfree_ref(op12.get("reviewer_person_ref") if isinstance(op12, Mapping) else None, default="missing_or_invalid_reviewer_person_ref", max_length=180)
    receipt_input = disposal_purge_receipt if disposal_purge_receipt is not None else disposal_purge_receipt_optional
    receipt_present, clean_receipt, receipt_blockers, retention_blockers, receipt_meta = _validate_rsr_op13_disposal_purge_receipt(op12, receipt_input)
    blockers: list[str] = []
    reasons: list[str] = []
    if not op12_contract_valid:
        blockers.append("op12_question_need_observation_rows_intake_contract_invalid_or_missing")
    elif not (op12_accepted and op12_purge_required):
        blockers.append("op12_question_need_observation_rows_not_accepted_or_purge_receipt_not_required")
    if receipt_present:
        blockers.extend(ref for ref in receipt_blockers if ref != "disposal_purge_receipt_missing")
        blockers.extend(retention_blockers)
        if receipt_meta["forbidden_paths"]:
            blockers.append("disposal_purge_receipt_forbidden_payload_key_detected")
        if receipt_meta["body_like_paths"]:
            blockers.append("disposal_purge_receipt_body_like_value_detected")
        if receipt_meta["promotion_claims"]:
            blockers.append("disposal_purge_receipt_promotion_claim_detected")
    if not receipt_present:
        if op12_accepted and op12_purge_required:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_MISSING_WAITING_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_DISPOSAL_PURGE_RECEIPT_BODYFREE_REF
            reasons.append("disposal_purge_receipt_missing_waiting_bodyfree")
        else:
            status_ref = P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF
            next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DISPOSAL_PURGE_RECEIPT_REF
            reasons.append("op12_prerequisite_repair_required_before_disposal_purge_receipt")
    elif retention_blockers or receipt_meta["forbidden_paths"] or receipt_meta["body_like_paths"] or receipt_meta["promotion_claims"]:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_DISPOSAL_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF
        reasons.append("disposal_purge_receipt_body_leak_retention_export_or_promotion_blocked")
    elif op12_accepted and op12_purge_required and not blockers:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF
        reasons.append("disposal_purge_receipt_accepted_bodyfree_without_helper_purge_execution")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_DISPOSAL_PURGE_RECEIPT_REF
        reasons.append("disposal_purge_receipt_invalid_or_repair_required")
    blockers = _dedupe_clean_refs(blockers)
    reasons = _dedupe_clean_refs(reasons)
    accepted = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF
    missing = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_MISSING_WAITING_REF
    invalid = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF
    blocked = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF
    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP13_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op12_contract_valid": op12_contract_valid,
        "op12_status_ref": op12_status_ref,
        "op12_question_need_observation_rows_accepted": op12_accepted,
        "op12_disposal_purge_receipt_required_next": op12_purge_required,
        "op12_next_required_step": op12_next,
        "operation_receipt_ref": operation_receipt_ref,
        "packet_request_ref": packet_request_ref,
        "reviewer_person_ref": reviewer_person_ref,
        "disposal_purge_receipt_present": receipt_present,
        "disposal_purge_receipt_contract_valid": accepted,
        "disposal_purge_receipt_schema_version": clean_receipt.get("schema_version", ""),
        "disposal_purge_receipt_ref": clean_receipt.get("disposal_purge_receipt_ref", ""),
        "disposal_purge_receipt_review_session_id": clean_receipt.get("review_session_id", ""),
        "disposal_purge_receipt_operation_receipt_ref": clean_receipt.get("operation_receipt_ref", ""),
        "disposal_purge_receipt_packet_request_ref": clean_receipt.get("packet_request_ref", ""),
        "disposal_purge_receipt_source_kind_ref": clean_receipt.get("source_kind_ref", ""),
        "disposal_purge_receipt_review_session_id_matches": accepted,
        "disposal_purge_receipt_operation_receipt_ref_matches": accepted,
        "disposal_purge_receipt_packet_request_ref_matches": accepted,
        "disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person": accepted,
        "disposal_purge_receipt_body_full_packet_retained": bool(clean_receipt.get("body_full_packet_retained") is True),
        "disposal_purge_receipt_local_temp_material_retained": bool(clean_receipt.get("local_temp_material_retained") is True),
        "disposal_purge_receipt_reviewer_working_form_body_retained": bool(clean_receipt.get("reviewer_working_form_body_retained") is True),
        "disposal_purge_receipt_external_export_performed": bool(clean_receipt.get("external_export_performed") is True),
        "disposal_purge_receipt_purge_completed": bool(accepted and clean_receipt.get("purge_completed") is True),
        "disposal_purge_receipt_body_free": bool(accepted and clean_receipt.get("body_free") is True),
        "disposal_purge_receipt_raw_input_included": bool(clean_receipt.get("raw_input_included") is True),
        "disposal_purge_receipt_comment_text_body_included": bool(clean_receipt.get("comment_text_body_included") is True),
        "disposal_purge_receipt_returned_surface_body_included": bool(clean_receipt.get("returned_surface_body_included") is True),
        "disposal_purge_receipt_reviewer_free_text_included": bool(clean_receipt.get("reviewer_free_text_included") is True),
        "disposal_purge_receipt_reviewer_note_body_included": bool(clean_receipt.get("reviewer_note_body_included") is True),
        "disposal_purge_receipt_question_text_included": bool(clean_receipt.get("question_text_included") is True),
        "disposal_purge_receipt_draft_question_text_included": bool(clean_receipt.get("draft_question_text_included") is True),
        "disposal_purge_receipt_answer_text_included": bool(clean_receipt.get("answer_text_included") is True),
        "disposal_purge_receipt_local_path_included": bool(clean_receipt.get("local_path_included") is True),
        "disposal_purge_receipt_body_hash_included": bool(clean_receipt.get("body_hash_included") is True),
        "disposal_purge_receipt_terminal_output_body_included": bool(clean_receipt.get("terminal_output_body_included") is True),
        "disposal_purge_receipt_forbidden_payload_key_path_refs": receipt_meta["forbidden_paths"],
        "disposal_purge_receipt_forbidden_payload_key_path_count": len(receipt_meta["forbidden_paths"]),
        "disposal_purge_receipt_body_like_value_path_refs": receipt_meta["body_like_paths"],
        "disposal_purge_receipt_body_like_value_path_count": len(receipt_meta["body_like_paths"]),
        "disposal_purge_receipt_promotion_claim_refs": receipt_meta["promotion_claims"],
        "disposal_purge_receipt_promotion_claim_ref_count": len(receipt_meta["promotion_claims"]),
        "disposal_purge_receipt_retention_or_export_blocker_refs": receipt_meta["retention_or_export_blockers"],
        "disposal_purge_receipt_retention_or_export_blocker_ref_count": len(receipt_meta["retention_or_export_blockers"]),
        "rsr_op13_status_ref": status_ref,
        "rsr_op13_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP13_ALLOWED_STATUS_REFS),
        "rsr_op13_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP13_ALLOWED_STATUS_REFS),
        "rsr_op13_ready": accepted,
        "rsr_op13_disposal_purge_receipt_accepted": accepted,
        "rsr_op13_disposal_purge_receipt_missing_waiting": missing,
        "rsr_op13_disposal_purge_receipt_invalid_repair_required": invalid,
        "rsr_op13_disposal_purge_receipt_body_leak_or_retention_blocked": blocked,
        "disposal_purge_receipt_accepted_by_rsr_op13": accepted,
        "disposal_purge_receipt_accepted_without_purge_execution_by_helper": accepted,
        "body_full_transient_material_reported_purged": accepted,
        "local_temp_material_reported_purged": accepted,
        "reviewer_working_form_body_reported_purged": accepted,
        "final_no_leak_source_kind_validation_required_next": accepted,
        "actual_review_evidence_complete_here": False,
        "op13_reason_refs": reasons,
        "op13_reason_ref_count": len(reasons),
        "op13_blocker_refs": blockers,
        "op13_blocker_ref_count": len(blockers),
        "helper_executes_disposal_purge": False,
        "actual_disposal_purge_executed_here_by_helper": False,
        "rsr_op13_does_not_execute_disposal_purge": True,
        "rsr_op13_does_not_perform_final_no_leak_validation": True,
        "rsr_op13_does_not_complete_actual_evidence": True,
        "rsr_op13_does_not_execute_dmd_or_r52": True,
        "rsr_op13_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op13_does_not_change_api_db_rn_runtime_response_key": True,
        "manual_decision_required_without_auto_execution": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP13_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP13 disposal / purge receipt intake contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP13_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP13")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP13_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP13_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP13_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP13")
    for field, count_field in (("rsr_op13_allowed_status_refs", "rsr_op13_allowed_status_ref_count"), ("disposal_purge_receipt_forbidden_payload_key_path_refs", "disposal_purge_receipt_forbidden_payload_key_path_count"), ("disposal_purge_receipt_body_like_value_path_refs", "disposal_purge_receipt_body_like_value_path_count"), ("disposal_purge_receipt_promotion_claim_refs", "disposal_purge_receipt_promotion_claim_ref_count"), ("disposal_purge_receipt_retention_or_export_blocker_refs", "disposal_purge_receipt_retention_or_export_blocker_ref_count"), ("op13_reason_refs", "op13_reason_ref_count"), ("op13_blocker_refs", "op13_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP13 {count_field} changed")
    if tuple(data.get("rsr_op13_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP13_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 allowed status refs changed")
    for key in ("helper_executes_disposal_purge", "actual_disposal_purge_executed_here_by_helper", "actual_review_evidence_complete_here", "actual_disposal_purge_executed_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p8_start_allowed", "p8_question_design_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP13 false boundary changed: {key}")
    for key in ("rsr_op13_does_not_execute_disposal_purge", "rsr_op13_does_not_perform_final_no_leak_validation", "rsr_op13_does_not_complete_actual_evidence", "rsr_op13_does_not_execute_dmd_or_r52", "rsr_op13_does_not_start_p5_p6_p8_p7_or_release", "rsr_op13_does_not_change_api_db_rn_runtime_response_key", "manual_decision_required_without_auto_execution"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP13 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP13_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP13_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 implemented/not-yet steps changed")
    status_ref = data.get("rsr_op13_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHR09_RSR_OP13_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 status ref is not allowed")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_ACCEPTED_BODYFREE_REF:
        for key in ("op12_question_need_observation_rows_accepted", "op12_disposal_purge_receipt_required_next", "disposal_purge_receipt_present", "disposal_purge_receipt_contract_valid", "disposal_purge_receipt_review_session_id_matches", "disposal_purge_receipt_operation_receipt_ref_matches", "disposal_purge_receipt_packet_request_ref_matches", "disposal_purge_receipt_source_kind_is_actual_local_only_human_review_by_person", "disposal_purge_receipt_purge_completed", "disposal_purge_receipt_body_free", "rsr_op13_disposal_purge_receipt_accepted", "disposal_purge_receipt_accepted_by_rsr_op13", "disposal_purge_receipt_accepted_without_purge_execution_by_helper", "body_full_transient_material_reported_purged", "local_temp_material_reported_purged", "reviewer_working_form_body_reported_purged", "final_no_leak_source_kind_validation_required_next"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP13 accepted branch required true changed: {key}")
        for key in ("disposal_purge_receipt_body_full_packet_retained", "disposal_purge_receipt_local_temp_material_retained", "disposal_purge_receipt_reviewer_working_form_body_retained", "disposal_purge_receipt_external_export_performed", "disposal_purge_receipt_raw_input_included", "disposal_purge_receipt_comment_text_body_included", "disposal_purge_receipt_returned_surface_body_included", "disposal_purge_receipt_reviewer_free_text_included", "disposal_purge_receipt_reviewer_note_body_included", "disposal_purge_receipt_question_text_included", "disposal_purge_receipt_draft_question_text_included", "disposal_purge_receipt_answer_text_included", "disposal_purge_receipt_local_path_included", "disposal_purge_receipt_body_hash_included", "disposal_purge_receipt_terminal_output_body_included"):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP13 accepted purge false field changed: {key}")
        if data.get("op13_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 accepted branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 accepted next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_MISSING_WAITING_REF:
        if data.get("rsr_op13_disposal_purge_receipt_missing_waiting") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_PROVIDE_DISPOSAL_PURGE_RECEIPT_BODYFREE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 missing branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_INVALID_REPAIR_REQUIRED_REF:
        if data.get("rsr_op13_disposal_purge_receipt_invalid_repair_required") is not True or not data.get("op13_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 invalid branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP13_STATUS_BODY_LEAK_OR_RETENTION_BLOCKED_REF:
        if data.get("rsr_op13_disposal_purge_receipt_body_leak_or_retention_blocked") is not True or not data.get("op13_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_DISPOSAL_PURGE_RECEIPT_BODY_LEAK_OR_RETENTION_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP13 blocked next step changed")
    return True

# RSR-OP14/OP15 additions: final validation and branch resolution.
P7_R54_AHR_POST_DHR09_RSR_OP14_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr."
    "op14_final_no_leak_no_promotion_source_kind_validation.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr."
    "op15_actual_evidence_complete_candidate_next_branch_resolver.bodyfree.v1"
)

P7_R54_AHR_POST_DHR09_RSR_OP14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:15]
)
P7_R54_AHR_POST_DHR09_RSR_OP14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[15:]
)
P7_R54_AHR_POST_DHR09_RSR_OP15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:16]
)
P7_R54_AHR_POST_DHR09_RSR_OP15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[16:]
)

P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_PASSED_BODYFREE_REF: Final = (
    "RSR_FINAL_NO_LEAK_NO_PROMOTION_SOURCE_KIND_VALIDATION_PASSED_BODYFREE"
)
P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_WAITING_FOR_ACCEPTED_OP13_REF: Final = (
    "RSR_FINAL_VALIDATION_WAITING_FOR_ACCEPTED_DISPOSAL_PURGE_RECEIPT"
)
P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_REPAIR_REQUIRED_REF: Final = (
    "RSR_FINAL_VALIDATION_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF: Final = (
    "RSR_FINAL_VALIDATION_BODY_LEAK_PROMOTION_OR_SOURCE_CLAIM_BLOCKED"
)
P7_R54_AHR_POST_DHR09_RSR_OP14_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_PASSED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_WAITING_FOR_ACCEPTED_OP13_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_ACCEPTED_DISPOSAL_PURGE_RECEIPT_BEFORE_FINAL_VALIDATION_REF: Final = (
    "wait_for_accepted_disposal_purge_receipt_before_final_no_leak_validation"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_FINAL_VALIDATION_MATERIAL_REF: Final = (
    "repair_final_no_leak_source_kind_validation_material_before_branch_resolution"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_FINAL_VALIDATION_BODY_LEAK_PROMOTION_OR_SOURCE_KIND_REF: Final = (
    "blocked_final_no_leak_promotion_or_source_kind_validation_before_branch_resolution"
)

P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF: Final = (
    "RSR_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_STOP_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF: Final = (
    "RSR_BRANCH_STOP_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_READY_TO_START_ACTUAL_LOCAL_ONLY_REVIEW_REF: Final = (
    "RSR_BRANCH_READY_TO_START_ACTUAL_LOCAL_ONLY_REVIEW"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_IN_PROGRESS_OR_PAUSED_LOCAL_ONLY_REF: Final = (
    "RSR_BRANCH_REVIEW_IN_PROGRESS_OR_PAUSED_LOCAL_ONLY"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED_REF: Final = (
    "RSR_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF: Final = (
    "RSR_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF: Final = (
    "RSR_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF: Final = (
    "RSR_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION"
)
P7_R54_AHR_POST_DHR09_RSR_OP15_ALLOWED_BRANCH_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_STOP_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_READY_TO_START_ACTUAL_LOCAL_ONLY_REVIEW_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_IN_PROGRESS_OR_PAUSED_LOCAL_ONLY_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_NO_AUTO_EXECUTION_REF: Final = (
    "return_to_dhr_actual_source_claim_reintake_without_auto_execution"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_AFTER_OP15_NO_PROMOTION_REF: Final = (
    "manual_hold_after_rsr_op15_without_downstream_promotion"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETRY_OR_REPAIR_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_REF: Final = (
    "retry_or_repair_actual_local_only_review_operation_without_auto_downstream_execution"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_RSR_OP03_EXPLICIT_ALLOW_GATE_REF: Final = (
    "return_to_rsr_op03_explicit_local_only_allow_gate"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_READINESS_BEFORE_ACTUAL_REVIEW_START_REF: Final = (
    "repair_readiness_before_actual_local_only_review_start"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODYFREE_LEAK_OR_SOURCE_CLAIM_BEFORE_DHR_REINTAKE_REF: Final = (
    "blocked_bodyfree_leak_or_source_claim_before_dhr_reintake"
)

P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS: Final[tuple[str, ...]] = (
    "explicit_allow_accepted",
    "readiness_blocker_count_zero",
    "reviewer_person_confirmed",
    "packet_generation_receipt_accepted",
    "actual_operation_receipt_accepted",
    "sanitized_review_result_rows_accepted",
    "rating_rows_accepted",
    "question_need_observation_rows_accepted",
    "disposal_purge_receipt_accepted",
    "final_no_leak_validation_passed",
)
P7_R54_AHR_POST_DHR09_RSR_OP14_SCAN_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "dhr_op09_intake_material",
    "allow_receipt_acceptance_gate",
    "readiness_material",
    "session_envelope",
    "packet_request",
    "packet_generation_receipt_intake",
    "lifecycle_material",
    "operation_receipt_intake",
    "sanitized_rating_rows_intake",
    "question_need_observation_rows_intake",
    "disposal_purge_receipt_intake",
)
P7_R54_AHR_POST_DHR09_RSR_OP14_QUESTION_MATERIALIZATION_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        "question_text",
        "draft_question_text",
        "question_text_materialized",
        "draft_question_text_materialized",
        "question_text_included",
        "draft_question_text_included",
        "p8_question_spec_created",
        "p8_question_design_started",
        "p8_question_design_started_here",
        "p8_question_design_started_by_rows",
    }
)
P7_R54_AHR_POST_DHR09_RSR_OP14_HELPER_GENERATED_ACTUAL_CLAIM_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        "row_created_by_helper",
        "row_created_for_unit_test",
        "row_is_synthetic_contract_fixture",
        "historical_row_reused",
        "helper_green_promoted_to_actual_review_complete",
        "target_green_promoted_to_actual_review_complete",
        "result_memo_green_promoted_to_actual_review_complete",
        "actual_operation_receipt_created_here",
        "actual_rows_created_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_purge_executed_here",
    }
)

P7_R54_AHR_POST_DHR09_RSR_OP14_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op13_contract_valid", "op13_status_ref", "op13_disposal_purge_receipt_accepted", "op13_final_no_leak_source_kind_validation_required_next", "op13_next_required_step",
    "complete_candidate_prerequisite_refs", "complete_candidate_prerequisite_ref_count", "complete_candidate_prerequisite_satisfied_refs", "complete_candidate_prerequisite_satisfied_ref_count", "complete_candidate_prerequisite_missing_refs", "complete_candidate_prerequisite_missing_ref_count",
    "op03_contract_valid", "explicit_allow_accepted", "op04_contract_valid", "readiness_blocker_count_zero", "op05_contract_valid", "reviewer_person_confirmed", "op07_contract_valid", "packet_generation_receipt_accepted",
    "op09_contract_valid", "review_lifecycle_completed_receipt_required", "review_lifecycle_in_progress_or_paused", "review_lifecycle_aborted_or_incomplete", "op10_contract_valid", "actual_operation_receipt_accepted", "op11_contract_valid", "sanitized_review_result_rows_accepted", "rating_rows_accepted", "op12_contract_valid", "question_need_observation_rows_accepted", "op13_disposal_purge_receipt_bodyfree_purge_confirmed",
    "scanned_material_refs", "scanned_material_ref_count", "scanned_material_contract_valid_refs", "scanned_material_contract_valid_ref_count", "scanned_material_contract_invalid_refs", "scanned_material_contract_invalid_ref_count",
    "final_validation_forbidden_payload_key_path_refs", "final_validation_forbidden_payload_key_path_count", "final_validation_body_like_value_path_refs", "final_validation_body_like_value_path_count", "final_validation_local_path_shape_refs", "final_validation_local_path_shape_ref_count", "final_validation_hash_shape_refs", "final_validation_hash_shape_ref_count", "final_validation_terminal_output_body_refs", "final_validation_terminal_output_body_ref_count", "final_validation_promotion_claim_refs", "final_validation_promotion_claim_ref_count", "final_validation_invalid_source_kind_refs", "final_validation_invalid_source_kind_ref_count", "final_validation_question_text_materialization_refs", "final_validation_question_text_materialization_ref_count", "final_validation_helper_generated_actual_claim_refs", "final_validation_helper_generated_actual_claim_ref_count",
    "final_validation_issue_refs", "final_validation_issue_ref_count", "rsr_op14_status_ref", "rsr_op14_allowed_status_refs", "rsr_op14_allowed_status_ref_count", "rsr_op14_ready", "rsr_op14_final_validation_passed", "rsr_op14_waiting_for_accepted_disposal_purge_receipt", "rsr_op14_repair_required", "rsr_op14_body_leak_promotion_or_source_kind_blocked",
    "actual_evidence_complete_candidate_ready_for_op15", "actual_review_evidence_complete_here", "op14_reason_refs", "op14_reason_ref_count", "op14_blocker_refs", "op14_blocker_ref_count",
    "rsr_op14_does_not_create_or_modify_actual_evidence", "rsr_op14_does_not_execute_actual_review", "rsr_op14_does_not_execute_dhr_dmd_r52_or_release", "rsr_op14_does_not_start_p5_p6_p8_p7", "rsr_op14_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_DHR09_RSR_OP15_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op14_contract_valid", "op14_status_ref", "op14_final_validation_passed", "op14_body_leak_promotion_or_source_kind_blocked", "op14_complete_candidate_prerequisite_missing_refs", "op14_complete_candidate_prerequisite_missing_ref_count",
    "complete_candidate_prerequisite_refs", "complete_candidate_prerequisite_ref_count", "complete_candidate_prerequisite_satisfied_refs", "complete_candidate_prerequisite_satisfied_ref_count", "complete_candidate_prerequisite_missing_refs", "complete_candidate_prerequisite_missing_ref_count",
    "actual_evidence_complete_candidate", "actual_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution", "dhr_actual_source_claim_reintake_required_next", "dhr_actual_source_claim_reintake_executed_here", "actual_source_claim_for_dhr_reintake_materialized_here_by_helper", "downstream_manual_decision_materialization_candidate_only", "downstream_auto_execution_allowed", "manual_decision_required_without_auto_execution",
    "source_claim_bundle_candidate_bodyfree", "source_claim_bundle_candidate_ref", "source_claim_bundle_candidate_source_kind_ref", "source_claim_bundle_candidate_review_session_id", "source_claim_bundle_candidate_operation_receipt_ref", "source_claim_bundle_candidate_packet_request_ref", "source_claim_bundle_candidate_disposal_purge_receipt_ref", "source_claim_bundle_candidate_reviewed_case_count", "source_claim_bundle_candidate_selection_row_count", "source_claim_bundle_candidate_body_free",
    "rsr_op15_branch_ref", "rsr_op15_allowed_branch_refs", "rsr_op15_allowed_branch_ref_count", "rsr_op15_wait_for_explicit_allow", "rsr_op15_stop_environment_or_material_repair_required", "rsr_op15_ready_to_start_actual_local_only_review", "rsr_op15_review_in_progress_or_paused_local_only", "rsr_op15_review_aborted_or_incomplete_retry_required", "rsr_op15_bodyfree_leak_or_source_claim_blocked", "rsr_op15_actual_review_evidence_ready_for_dhr_reintake_no_auto_execution", "rsr_op15_manual_hold_unresolved_no_promotion",
    "actual_review_evidence_complete_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed",
    "op15_reason_refs", "op15_reason_ref_count", "op15_blocker_refs", "op15_blocker_ref_count",
    "rsr_op15_does_not_execute_dhr_reintake", "rsr_op15_does_not_execute_dmd_or_r52", "rsr_op15_does_not_start_p5_p6_p8_p7_or_release", "rsr_op15_does_not_change_api_db_rn_runtime_response_key", "rsr_op15_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _scan_rsr_op14_key_shape_refs(value: Any, *, path: str, key_tokens: Sequence[str]) -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if any(token in key_lower for token in key_tokens):
                if isinstance(child, str) and child.strip():
                    refs.append(child_path)
                elif child is True and (
                    key_lower.endswith("_included")
                    or key_lower.endswith("_retained")
                    or key_lower.endswith("_body")
                    or key_lower in {"local_path", "file_path", "absolute_path", "relative_path", "body_hash", "input_hash", "terminal_output", "stdout", "stderr", "traceback"}
                ):
                    refs.append(child_path)
            refs.extend(_scan_rsr_op14_key_shape_refs(child, path=child_path, key_tokens=key_tokens))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_rsr_op14_key_shape_refs(child, path=f"{path}[{index}]", key_tokens=key_tokens))
    return refs


def _scan_rsr_op14_invalid_source_kind_refs(value: Any, *, path: str = "material") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            key_lower = key_text.lower()
            if key_lower.endswith("source_kind_ref") or key_lower == "source_kind_ref":
                child_ref = _clean_ref(child, default="", max_length=260)
                if child_ref and child_ref != P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
                    refs.append(child_path)
            refs.extend(_scan_rsr_op14_invalid_source_kind_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_rsr_op14_invalid_source_kind_refs(child, path=f"{path}[{index}]"))
    return refs


def _scan_rsr_op14_question_materialization_refs(value: Any, *, path: str = "material") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_DHR09_RSR_OP14_QUESTION_MATERIALIZATION_FIELD_REFS:
                if child is True or (isinstance(child, str) and child.strip()):
                    refs.append(child_path)
            refs.extend(_scan_rsr_op14_question_materialization_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_rsr_op14_question_materialization_refs(child, path=f"{path}[{index}]"))
    return refs


def _scan_rsr_op14_helper_generated_actual_claim_refs(value: Any, *, path: str = "material") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_DHR09_RSR_OP14_HELPER_GENERATED_ACTUAL_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_rsr_op14_helper_generated_actual_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_rsr_op14_helper_generated_actual_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _contract_valid_bool(material: Mapping[str, Any] | None, assertion: Any) -> bool:
    return _contract_valid_for(material, assertion)


def _normalize_optional_materials_for_op14(
    *,
    dhr_op09_intake_material: Mapping[str, Any] | None = None,
    allow_receipt_acceptance_gate: Mapping[str, Any] | None = None,
    explicit_local_only_allow_gate: Mapping[str, Any] | None = None,
    readiness_material: Mapping[str, Any] | None = None,
    readiness_blocker_classifier: Mapping[str, Any] | None = None,
    session_envelope: Mapping[str, Any] | None = None,
    local_only_review_session_envelope: Mapping[str, Any] | None = None,
    packet_request: Mapping[str, Any] | None = None,
    body_full_packet_transient_request_boundary: Mapping[str, Any] | None = None,
    packet_generation_receipt_intake: Mapping[str, Any] | None = None,
    body_full_packet_generation_receipt_intake: Mapping[str, Any] | None = None,
    lifecycle_material: Mapping[str, Any] | None = None,
    actual_local_only_review_lifecycle_state_capture: Mapping[str, Any] | None = None,
    operation_receipt_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_rating_rows_intake: Mapping[str, Any] | None = None,
    review_rows_rating_rows_intake: Mapping[str, Any] | None = None,
    question_need_observation_rows_intake: Mapping[str, Any] | None = None,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    op13_disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    additional_bodyfree_materials: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Mapping[str, Any] | None]:
    materials: dict[str, Mapping[str, Any] | None] = {
        "dhr_op09_intake_material": dhr_op09_intake_material,
        "allow_receipt_acceptance_gate": allow_receipt_acceptance_gate if allow_receipt_acceptance_gate is not None else explicit_local_only_allow_gate,
        "readiness_material": readiness_material if readiness_material is not None else readiness_blocker_classifier,
        "session_envelope": session_envelope if session_envelope is not None else local_only_review_session_envelope,
        "packet_request": packet_request if packet_request is not None else body_full_packet_transient_request_boundary,
        "packet_generation_receipt_intake": packet_generation_receipt_intake if packet_generation_receipt_intake is not None else body_full_packet_generation_receipt_intake,
        "lifecycle_material": lifecycle_material if lifecycle_material is not None else actual_local_only_review_lifecycle_state_capture,
        "operation_receipt_intake": operation_receipt_intake if operation_receipt_intake is not None else actual_operation_receipt_intake,
        "sanitized_rating_rows_intake": sanitized_rating_rows_intake if sanitized_rating_rows_intake is not None else review_rows_rating_rows_intake,
        "question_need_observation_rows_intake": question_need_observation_rows_intake,
        "disposal_purge_receipt_intake": disposal_purge_receipt_intake if disposal_purge_receipt_intake is not None else op13_disposal_purge_receipt_intake,
    }
    if isinstance(additional_bodyfree_materials, Mapping):
        for key, value in additional_bodyfree_materials.items():
            if isinstance(value, Mapping):
                materials[_clean_ref(key, default="additional_bodyfree_material", max_length=120)] = value
    return materials


def _scan_rsr_op14_materials(materials: Mapping[str, Mapping[str, Any] | None]) -> dict[str, list[str]]:
    forbidden: list[str] = []
    body_like: list[str] = []
    local_path: list[str] = []
    hash_shape: list[str] = []
    terminal_output: list[str] = []
    promotion: list[str] = []
    invalid_source_kind: list[str] = []
    question_materialization: list[str] = []
    helper_generated_actual: list[str] = []
    for name, material in materials.items():
        if not isinstance(material, Mapping):
            continue
        forbidden.extend(_scan_forbidden_payload_key_paths(material, path=name))
        body_like.extend(_scan_body_like_value_paths(material, path=name))
        local_path.extend(_scan_rsr_op14_key_shape_refs(material, path=name, key_tokens=("local_path", "file_path", "absolute_path", "relative_path")))
        hash_shape.extend(_scan_rsr_op14_key_shape_refs(material, path=name, key_tokens=("hash", "sha256")))
        terminal_output.extend(_scan_rsr_op14_key_shape_refs(material, path=name, key_tokens=("terminal", "stdout", "stderr", "traceback")))
        promotion.extend(f"{name}.{ref}" for ref in _promotion_claim_refs(material))
        invalid_source_kind.extend(_scan_rsr_op14_invalid_source_kind_refs(material, path=name))
        question_materialization.extend(_scan_rsr_op14_question_materialization_refs(material, path=name))
        helper_generated_actual.extend(_scan_rsr_op14_helper_generated_actual_claim_refs(material, path=name))
    return {
        "forbidden": _dedupe_clean_refs(forbidden, max_length=320),
        "body_like": _dedupe_clean_refs(body_like, max_length=320),
        "local_path": _dedupe_clean_refs(local_path, max_length=320),
        "hash_shape": _dedupe_clean_refs(hash_shape, max_length=320),
        "terminal_output": _dedupe_clean_refs(terminal_output, max_length=320),
        "promotion": _dedupe_clean_refs(promotion, max_length=320),
        "invalid_source_kind": _dedupe_clean_refs(invalid_source_kind, max_length=320),
        "question_materialization": _dedupe_clean_refs(question_materialization, max_length=320),
        "helper_generated_actual": _dedupe_clean_refs(helper_generated_actual, max_length=320),
    }


def _op14_satisfied_and_missing_prereqs(*, flags: Mapping[str, bool]) -> tuple[list[str], list[str]]:
    satisfied = [ref for ref in P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS if flags.get(ref) is True]
    missing = [ref for ref in P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS if flags.get(ref) is not True]
    return satisfied, missing


def build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation(
    *,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    op13_disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    dhr_op09_intake_material: Mapping[str, Any] | None = None,
    allow_receipt_acceptance_gate: Mapping[str, Any] | None = None,
    explicit_local_only_allow_gate: Mapping[str, Any] | None = None,
    readiness_material: Mapping[str, Any] | None = None,
    readiness_blocker_classifier: Mapping[str, Any] | None = None,
    session_envelope: Mapping[str, Any] | None = None,
    local_only_review_session_envelope: Mapping[str, Any] | None = None,
    packet_request: Mapping[str, Any] | None = None,
    body_full_packet_transient_request_boundary: Mapping[str, Any] | None = None,
    packet_generation_receipt_intake: Mapping[str, Any] | None = None,
    body_full_packet_generation_receipt_intake: Mapping[str, Any] | None = None,
    lifecycle_material: Mapping[str, Any] | None = None,
    actual_local_only_review_lifecycle_state_capture: Mapping[str, Any] | None = None,
    operation_receipt_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_rating_rows_intake: Mapping[str, Any] | None = None,
    review_rows_rating_rows_intake: Mapping[str, Any] | None = None,
    question_need_observation_rows_intake: Mapping[str, Any] | None = None,
    additional_bodyfree_materials: Mapping[str, Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP14 final body-free no-leak / no-promotion / source-kind validation."""
    op13 = disposal_purge_receipt_intake if disposal_purge_receipt_intake is not None else op13_disposal_purge_receipt_intake
    if op13 is None:
        op13 = build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op13.get("review_session_id") if isinstance(op13, Mapping) else None))
    op13_contract_valid = _contract_valid_bool(op13, assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract)
    op13_status_ref = _bodyfree_status_ref(op13.get("rsr_op13_status_ref") if isinstance(op13, Mapping) else None, default="rsr_op13_status_missing")
    op13_accepted = bool(op13_contract_valid and op13.get("rsr_op13_disposal_purge_receipt_accepted") is True and op13.get("next_required_step") == P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF)
    op13_final_required = bool(op13_contract_valid and op13.get("final_no_leak_source_kind_validation_required_next") is True)
    op13_next = _bodyfree_status_ref(op13.get("next_required_step") if isinstance(op13, Mapping) else None, default="rsr_op13_next_required_step_missing")

    op03 = allow_receipt_acceptance_gate if allow_receipt_acceptance_gate is not None else explicit_local_only_allow_gate
    op04 = readiness_material if readiness_material is not None else readiness_blocker_classifier
    op05 = session_envelope if session_envelope is not None else local_only_review_session_envelope
    op07 = packet_generation_receipt_intake if packet_generation_receipt_intake is not None else body_full_packet_generation_receipt_intake
    op09 = lifecycle_material if lifecycle_material is not None else actual_local_only_review_lifecycle_state_capture
    op10 = operation_receipt_intake if operation_receipt_intake is not None else actual_operation_receipt_intake
    op11 = sanitized_rating_rows_intake if sanitized_rating_rows_intake is not None else review_rows_rating_rows_intake
    op12 = question_need_observation_rows_intake
    materials = _normalize_optional_materials_for_op14(
        dhr_op09_intake_material=dhr_op09_intake_material,
        allow_receipt_acceptance_gate=op03,
        readiness_material=op04,
        session_envelope=op05,
        packet_request=packet_request if packet_request is not None else body_full_packet_transient_request_boundary,
        packet_generation_receipt_intake=op07,
        lifecycle_material=op09,
        operation_receipt_intake=op10,
        sanitized_rating_rows_intake=op11,
        question_need_observation_rows_intake=op12,
        disposal_purge_receipt_intake=op13,
        additional_bodyfree_materials=additional_bodyfree_materials,
    )
    scan = _scan_rsr_op14_materials(materials)
    issue_refs = _dedupe_clean_refs(
        [
            *(f"forbidden_payload:{ref}" for ref in scan["forbidden"]),
            *(f"body_like:{ref}" for ref in scan["body_like"]),
            *(f"local_path:{ref}" for ref in scan["local_path"]),
            *(f"hash_shape:{ref}" for ref in scan["hash_shape"]),
            *(f"terminal_output:{ref}" for ref in scan["terminal_output"]),
            *(f"promotion:{ref}" for ref in scan["promotion"]),
            *(f"invalid_source_kind:{ref}" for ref in scan["invalid_source_kind"]),
            *(f"question_materialization:{ref}" for ref in scan["question_materialization"]),
            *(f"helper_generated_actual:{ref}" for ref in scan["helper_generated_actual"]),
        ],
        max_length=360,
    )

    op03_valid = _contract_valid_bool(op03, assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract)
    op04_valid = _contract_valid_bool(op04, assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract)
    op05_valid = _contract_valid_bool(op05, assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract)
    op07_valid = _contract_valid_bool(op07, assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract)
    op09_valid = _contract_valid_bool(op09, assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract)
    op10_valid = _contract_valid_bool(op10, assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract)
    op11_valid = _contract_valid_bool(op11, assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract)
    op12_valid = _contract_valid_bool(op12, assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract)
    contract_valid_refs = _dedupe_clean_refs([
        "op13_disposal_purge_receipt_intake" if op13_contract_valid else "",
        "op03_explicit_allow_gate" if op03_valid else "",
        "op04_readiness" if op04_valid else "",
        "op05_session_envelope" if op05_valid else "",
        "op07_packet_generation_receipt" if op07_valid else "",
        "op09_lifecycle" if op09_valid else "",
        "op10_actual_operation_receipt" if op10_valid else "",
        "op11_sanitized_rating_rows" if op11_valid else "",
        "op12_question_need_observation_rows" if op12_valid else "",
    ])
    supplied_contract_pairs = (
        ("op03_explicit_allow_gate", op03, op03_valid),
        ("op04_readiness", op04, op04_valid),
        ("op05_session_envelope", op05, op05_valid),
        ("op07_packet_generation_receipt", op07, op07_valid),
        ("op09_lifecycle", op09, op09_valid),
        ("op10_actual_operation_receipt", op10, op10_valid),
        ("op11_sanitized_rating_rows", op11, op11_valid),
        ("op12_question_need_observation_rows", op12, op12_valid),
        ("op13_disposal_purge_receipt_intake", op13, op13_contract_valid),
    )
    contract_invalid_refs = _dedupe_clean_refs([name for name, material, valid in supplied_contract_pairs if material is not None and not valid])

    explicit_allow_accepted = bool(op03_valid and op03.get("rsr_op03_explicit_allow_accepted") is True)
    readiness_blocker_count_zero = bool(op04_valid and _safe_int_value(op04.get("readiness_blocker_ref_count")) == 0 and op04.get("rsr_op04_ready") is True)
    reviewer_person_confirmed = bool(op05_valid and op05.get("reviewer_is_person_confirmed") is True)
    packet_generation_receipt_accepted = bool(op07_valid and op07.get("rsr_op07_packet_generation_receipt_accepted") is True)
    op09_lifecycle_ref = _bodyfree_status_ref(op09.get("rsr_op09_status_ref") if isinstance(op09, Mapping) else None, default="rsr_op09_status_missing")
    review_lifecycle_completed = bool(op09_valid and op09.get("rsr_op09_ready_for_actual_operation_receipt_intake") is True and op09_lifecycle_ref == P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_COMPLETED_RECEIPT_REQUIRED_REF)
    review_lifecycle_in_progress_or_paused = bool(op09_valid and op09_lifecycle_ref in (P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_IN_PROGRESS_LOCAL_ONLY_REF, P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_PAUSED_LOCAL_ONLY_REF))
    review_lifecycle_aborted_or_incomplete = bool(op09_valid and op09_lifecycle_ref in (P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_ABORTED_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_NOT_STARTED_REF, P7_R54_AHR_POST_DHR09_RSR_REVIEW_LIFECYCLE_STATUS_READY_TO_START_REF))
    actual_operation_receipt_accepted = bool(op10_valid and op10.get("rsr_op10_actual_operation_receipt_accepted") is True)
    sanitized_rows_accepted = bool(op11_valid and op11.get("rsr_op11_sanitized_review_result_rows_accepted") is True)
    rating_rows_accepted = bool(op11_valid and op11.get("rsr_op11_rating_rows_accepted") is True)
    question_rows_accepted = bool(op12_valid and op12.get("rsr_op12_question_need_observation_rows_accepted") is True)
    purge_accepted = bool(op13_accepted and op13.get("disposal_purge_receipt_purge_completed") is True and op13.get("disposal_purge_receipt_body_free") is True)

    blockers: list[str] = []
    reasons: list[str] = []
    if not op13_contract_valid:
        blockers.append("op13_disposal_purge_receipt_intake_contract_invalid_or_missing")
    elif not (op13_accepted and op13_final_required):
        blockers.append("op13_disposal_purge_receipt_not_accepted_or_final_validation_not_required")
    if contract_invalid_refs:
        blockers.append("supplied_bodyfree_material_contract_invalid")
    if issue_refs:
        blockers.append("final_validation_body_leak_promotion_source_kind_or_helper_claim_detected")
    if not op13_accepted:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_WAITING_FOR_ACCEPTED_OP13_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_ACCEPTED_DISPOSAL_PURGE_RECEIPT_BEFORE_FINAL_VALIDATION_REF
        reasons.append("accepted_disposal_purge_receipt_required_before_final_validation")
    elif issue_refs:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_FINAL_VALIDATION_BODY_LEAK_PROMOTION_OR_SOURCE_KIND_REF
        reasons.append("body_leak_promotion_source_kind_or_helper_generated_actual_claim_blocked")
    elif contract_invalid_refs:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_FINAL_VALIDATION_MATERIAL_REF
        reasons.append("supplied_optional_material_contract_repair_required")
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_PASSED_BODYFREE_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF
        reasons.append("final_no_leak_no_promotion_source_kind_validation_passed_bodyfree")
    final_passed = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_PASSED_BODYFREE_REF
    flags = {
        "explicit_allow_accepted": explicit_allow_accepted,
        "readiness_blocker_count_zero": readiness_blocker_count_zero,
        "reviewer_person_confirmed": reviewer_person_confirmed,
        "packet_generation_receipt_accepted": packet_generation_receipt_accepted,
        "actual_operation_receipt_accepted": actual_operation_receipt_accepted,
        "sanitized_review_result_rows_accepted": sanitized_rows_accepted,
        "rating_rows_accepted": rating_rows_accepted,
        "question_need_observation_rows_accepted": question_rows_accepted,
        "disposal_purge_receipt_accepted": purge_accepted,
        "final_no_leak_validation_passed": final_passed,
    }
    satisfied, missing = _op14_satisfied_and_missing_prereqs(flags=flags)
    scanned_refs = _dedupe_clean_refs([name for name, material in materials.items() if isinstance(material, Mapping)])
    blockers = _dedupe_clean_refs(blockers)
    reasons = _dedupe_clean_refs(reasons)
    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP14_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op13_contract_valid": op13_contract_valid,
        "op13_status_ref": op13_status_ref,
        "op13_disposal_purge_receipt_accepted": op13_accepted,
        "op13_final_no_leak_source_kind_validation_required_next": op13_final_required,
        "op13_next_required_step": op13_next,
        "complete_candidate_prerequisite_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS),
        "complete_candidate_prerequisite_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS),
        "complete_candidate_prerequisite_satisfied_refs": satisfied,
        "complete_candidate_prerequisite_satisfied_ref_count": len(satisfied),
        "complete_candidate_prerequisite_missing_refs": missing,
        "complete_candidate_prerequisite_missing_ref_count": len(missing),
        "op03_contract_valid": op03_valid,
        "explicit_allow_accepted": explicit_allow_accepted,
        "op04_contract_valid": op04_valid,
        "readiness_blocker_count_zero": readiness_blocker_count_zero,
        "op05_contract_valid": op05_valid,
        "reviewer_person_confirmed": reviewer_person_confirmed,
        "op07_contract_valid": op07_valid,
        "packet_generation_receipt_accepted": packet_generation_receipt_accepted,
        "op09_contract_valid": op09_valid,
        "review_lifecycle_completed_receipt_required": review_lifecycle_completed,
        "review_lifecycle_in_progress_or_paused": review_lifecycle_in_progress_or_paused,
        "review_lifecycle_aborted_or_incomplete": review_lifecycle_aborted_or_incomplete,
        "op10_contract_valid": op10_valid,
        "actual_operation_receipt_accepted": actual_operation_receipt_accepted,
        "op11_contract_valid": op11_valid,
        "sanitized_review_result_rows_accepted": sanitized_rows_accepted,
        "rating_rows_accepted": rating_rows_accepted,
        "op12_contract_valid": op12_valid,
        "question_need_observation_rows_accepted": question_rows_accepted,
        "op13_disposal_purge_receipt_bodyfree_purge_confirmed": purge_accepted,
        "scanned_material_refs": scanned_refs,
        "scanned_material_ref_count": len(scanned_refs),
        "scanned_material_contract_valid_refs": contract_valid_refs,
        "scanned_material_contract_valid_ref_count": len(contract_valid_refs),
        "scanned_material_contract_invalid_refs": contract_invalid_refs,
        "scanned_material_contract_invalid_ref_count": len(contract_invalid_refs),
        "final_validation_forbidden_payload_key_path_refs": scan["forbidden"],
        "final_validation_forbidden_payload_key_path_count": len(scan["forbidden"]),
        "final_validation_body_like_value_path_refs": scan["body_like"],
        "final_validation_body_like_value_path_count": len(scan["body_like"]),
        "final_validation_local_path_shape_refs": scan["local_path"],
        "final_validation_local_path_shape_ref_count": len(scan["local_path"]),
        "final_validation_hash_shape_refs": scan["hash_shape"],
        "final_validation_hash_shape_ref_count": len(scan["hash_shape"]),
        "final_validation_terminal_output_body_refs": scan["terminal_output"],
        "final_validation_terminal_output_body_ref_count": len(scan["terminal_output"]),
        "final_validation_promotion_claim_refs": scan["promotion"],
        "final_validation_promotion_claim_ref_count": len(scan["promotion"]),
        "final_validation_invalid_source_kind_refs": scan["invalid_source_kind"],
        "final_validation_invalid_source_kind_ref_count": len(scan["invalid_source_kind"]),
        "final_validation_question_text_materialization_refs": scan["question_materialization"],
        "final_validation_question_text_materialization_ref_count": len(scan["question_materialization"]),
        "final_validation_helper_generated_actual_claim_refs": scan["helper_generated_actual"],
        "final_validation_helper_generated_actual_claim_ref_count": len(scan["helper_generated_actual"]),
        "final_validation_issue_refs": issue_refs,
        "final_validation_issue_ref_count": len(issue_refs),
        "rsr_op14_status_ref": status_ref,
        "rsr_op14_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP14_ALLOWED_STATUS_REFS),
        "rsr_op14_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP14_ALLOWED_STATUS_REFS),
        "rsr_op14_ready": final_passed,
        "rsr_op14_final_validation_passed": final_passed,
        "rsr_op14_waiting_for_accepted_disposal_purge_receipt": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_WAITING_FOR_ACCEPTED_OP13_REF,
        "rsr_op14_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_REPAIR_REQUIRED_REF,
        "rsr_op14_body_leak_promotion_or_source_kind_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF,
        "actual_evidence_complete_candidate_ready_for_op15": final_passed and not missing,
        "actual_review_evidence_complete_here": False,
        "op14_reason_refs": reasons,
        "op14_reason_ref_count": len(reasons),
        "op14_blocker_refs": blockers,
        "op14_blocker_ref_count": len(blockers),
        "rsr_op14_does_not_create_or_modify_actual_evidence": True,
        "rsr_op14_does_not_execute_actual_review": True,
        "rsr_op14_does_not_execute_dhr_dmd_r52_or_release": True,
        "rsr_op14_does_not_start_p5_p6_p8_p7": True,
        "rsr_op14_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP14_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP14 final validation contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP14_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP14")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP14_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP14_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP14")
    for field, count_field in (("complete_candidate_prerequisite_refs", "complete_candidate_prerequisite_ref_count"), ("complete_candidate_prerequisite_satisfied_refs", "complete_candidate_prerequisite_satisfied_ref_count"), ("complete_candidate_prerequisite_missing_refs", "complete_candidate_prerequisite_missing_ref_count"), ("scanned_material_refs", "scanned_material_ref_count"), ("scanned_material_contract_valid_refs", "scanned_material_contract_valid_ref_count"), ("scanned_material_contract_invalid_refs", "scanned_material_contract_invalid_ref_count"), ("final_validation_forbidden_payload_key_path_refs", "final_validation_forbidden_payload_key_path_count"), ("final_validation_body_like_value_path_refs", "final_validation_body_like_value_path_count"), ("final_validation_local_path_shape_refs", "final_validation_local_path_shape_ref_count"), ("final_validation_hash_shape_refs", "final_validation_hash_shape_ref_count"), ("final_validation_terminal_output_body_refs", "final_validation_terminal_output_body_ref_count"), ("final_validation_promotion_claim_refs", "final_validation_promotion_claim_ref_count"), ("final_validation_invalid_source_kind_refs", "final_validation_invalid_source_kind_ref_count"), ("final_validation_question_text_materialization_refs", "final_validation_question_text_materialization_ref_count"), ("final_validation_helper_generated_actual_claim_refs", "final_validation_helper_generated_actual_claim_ref_count"), ("final_validation_issue_refs", "final_validation_issue_ref_count"), ("op14_reason_refs", "op14_reason_ref_count"), ("op14_blocker_refs", "op14_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP14 {count_field} changed")
    if tuple(data.get("complete_candidate_prerequisite_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 prerequisite refs changed")
    if tuple(data.get("rsr_op14_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP14_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 allowed status refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP14_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP14_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 implemented/not-yet steps changed")
    for key in ("actual_review_evidence_complete_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP14 false promotion boundary changed: {key}")
    for key in ("rsr_op14_does_not_create_or_modify_actual_evidence", "rsr_op14_does_not_execute_actual_review", "rsr_op14_does_not_execute_dhr_dmd_r52_or_release", "rsr_op14_does_not_start_p5_p6_p8_p7", "rsr_op14_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP14 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 not-claimed boundary must stay false")
    status_ref = data.get("rsr_op14_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHR09_RSR_OP14_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 status ref is not allowed")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_PASSED_BODYFREE_REF:
        if data.get("rsr_op14_final_validation_passed") is not True or data.get("rsr_op14_ready") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 passed flags changed")
        zero_fields = (
            "final_validation_forbidden_payload_key_path_count", "final_validation_body_like_value_path_count", "final_validation_local_path_shape_ref_count", "final_validation_hash_shape_ref_count", "final_validation_terminal_output_body_ref_count", "final_validation_promotion_claim_ref_count", "final_validation_invalid_source_kind_ref_count", "final_validation_question_text_materialization_ref_count", "final_validation_helper_generated_actual_claim_ref_count", "final_validation_issue_ref_count",
        )
        for field in zero_fields:
            if data.get(field) != 0:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP14 passed branch issue count changed: {field}")
        if data.get("op14_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 passed branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 passed next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_WAITING_FOR_ACCEPTED_OP13_REF:
        if data.get("rsr_op14_waiting_for_accepted_disposal_purge_receipt") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_ACCEPTED_DISPOSAL_PURGE_RECEIPT_BEFORE_FINAL_VALIDATION_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 waiting branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_REPAIR_REQUIRED_REF:
        if data.get("rsr_op14_repair_required") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_FINAL_VALIDATION_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 repair branch changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF:
        if data.get("rsr_op14_body_leak_promotion_or_source_kind_blocked") is not True or not data.get("op14_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 blocked branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_FINAL_VALIDATION_BODY_LEAK_PROMOTION_OR_SOURCE_KIND_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP14 blocked next step changed")
    return True


def _resolve_rsr_op15_branch(final_validation: Mapping[str, Any], *, op14_contract_valid: bool) -> tuple[str, str, list[str], list[str], bool]:
    blockers: list[str] = []
    reasons: list[str] = []
    missing = list(final_validation.get("complete_candidate_prerequisite_missing_refs") or []) if isinstance(final_validation, Mapping) else []
    if not op14_contract_valid:
        blockers.append("op14_final_validation_contract_invalid_or_missing")
        reasons.append("op14_final_validation_must_be_repaired_before_branch_resolution")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_AFTER_OP15_NO_PROMOTION_REF, reasons, blockers, False
    if final_validation.get("rsr_op14_body_leak_promotion_or_source_kind_blocked") is True or _safe_int_value(final_validation.get("final_validation_issue_ref_count")) > 0:
        blockers.append("op14_bodyfree_leak_promotion_source_claim_or_helper_generated_actual_claim_detected")
        reasons.append("bodyfree_leak_or_source_claim_blocked_before_dhr_reintake")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODYFREE_LEAK_OR_SOURCE_CLAIM_BEFORE_DHR_REINTAKE_REF, reasons, blockers, False
    if final_validation.get("explicit_allow_accepted") is not True:
        blockers.append("explicit_local_only_allow_not_accepted")
        reasons.append("wait_for_explicit_local_only_allow_before_actual_review_evidence_candidate")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_RSR_OP03_EXPLICIT_ALLOW_GATE_REF, reasons, blockers, False
    if final_validation.get("readiness_blocker_count_zero") is not True or final_validation.get("reviewer_person_confirmed") is not True:
        blockers.append("readiness_or_reviewer_person_boundary_not_confirmed")
        reasons.append("readiness_repair_required_before_actual_review_start")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_STOP_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_READINESS_BEFORE_ACTUAL_REVIEW_START_REF, reasons, blockers, False
    if final_validation.get("packet_generation_receipt_accepted") is not True:
        blockers.append("packet_generation_receipt_not_accepted")
        reasons.append("ready_to_start_or_continue_actual_local_only_review_without_complete_evidence")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_READY_TO_START_ACTUAL_LOCAL_ONLY_REVIEW_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETRY_OR_REPAIR_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_REF, reasons, blockers, False
    if final_validation.get("review_lifecycle_in_progress_or_paused") is True:
        reasons.append("actual_local_only_review_in_progress_or_paused_local_only")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_IN_PROGRESS_OR_PAUSED_LOCAL_ONLY_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETRY_OR_REPAIR_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_REF, reasons, blockers, False
    if final_validation.get("review_lifecycle_aborted_or_incomplete") is True:
        blockers.append("actual_local_only_review_aborted_or_incomplete")
        reasons.append("actual_local_only_review_retry_required_without_downstream_promotion")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETRY_OR_REPAIR_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_REF, reasons, blockers, False
    receipt_or_rows_missing = [ref for ref in missing if ref in {"actual_operation_receipt_accepted", "sanitized_review_result_rows_accepted", "rating_rows_accepted", "question_need_observation_rows_accepted", "disposal_purge_receipt_accepted", "final_no_leak_validation_passed"}]
    if receipt_or_rows_missing:
        blockers.extend(f"missing_{ref}" for ref in receipt_or_rows_missing)
        reasons.append("actual_review_receipt_rows_question_or_purge_evidence_incomplete")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETRY_OR_REPAIR_ACTUAL_LOCAL_ONLY_REVIEW_OPERATION_REF, reasons, blockers, False
    if final_validation.get("actual_evidence_complete_candidate_ready_for_op15") is True and not missing:
        reasons.append("actual_review_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution")
        return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_NO_AUTO_EXECUTION_REF, reasons, blockers, True
    blockers.append("manual_hold_unresolved_no_promotion")
    reasons.append("manual_hold_unresolved_without_actual_evidence_promotion")
    return P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF, P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_AFTER_OP15_NO_PROMOTION_REF, reasons, blockers, False


def build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(
    *,
    final_validation: Mapping[str, Any] | None = None,
    op14_final_no_leak_no_promotion_source_kind_validation: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build RSR-OP15 actual evidence complete candidate and next branch resolver."""
    op14 = final_validation if final_validation is not None else op14_final_no_leak_no_promotion_source_kind_validation
    if op14 is None:
        op14 = build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation(review_session_id=review_session_id)
    session_id = _safe_review_session_id(review_session_id if review_session_id is not None else (op14.get("review_session_id") if isinstance(op14, Mapping) else None))
    op14_valid = _contract_valid_bool(op14, assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract)
    branch_ref, next_step, reasons, blockers, complete_candidate = _resolve_rsr_op15_branch(op14, op14_contract_valid=op14_valid)
    candidate_ref = "rsr_op15_actual_evidence_candidate_not_ready"
    source_kind_ref = ""
    operation_receipt_ref = ""
    packet_request_ref = ""
    disposal_purge_receipt_ref = ""
    reviewed_case_count = 0
    selection_row_count = 0
    if complete_candidate:
        candidate_ref = _clean_ref(f"rsr_op15_bodyfree_actual_evidence_candidate_{session_id}", max_length=220)
        source_kind_ref = P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF
        # OP14 does not retain body-full data.  These refs are intentionally body-free identifiers only.
        operation_receipt_ref = "operation_receipt_bodyfree_ref_accepted_upstream"
        packet_request_ref = "packet_request_bodyfree_ref_accepted_upstream"
        disposal_purge_receipt_ref = "disposal_purge_receipt_bodyfree_ref_accepted_upstream"
        reviewed_case_count = P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
        selection_row_count = P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    missing = list(op14.get("complete_candidate_prerequisite_missing_refs") or []) if isinstance(op14, Mapping) else list(P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS)
    satisfied = list(op14.get("complete_candidate_prerequisite_satisfied_refs") or []) if isinstance(op14, Mapping) else []
    branch_flags = {
        "rsr_op15_wait_for_explicit_allow": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
        "rsr_op15_stop_environment_or_material_repair_required": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_STOP_ENVIRONMENT_OR_MATERIAL_REPAIR_REQUIRED_REF,
        "rsr_op15_ready_to_start_actual_local_only_review": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_READY_TO_START_ACTUAL_LOCAL_ONLY_REVIEW_REF,
        "rsr_op15_review_in_progress_or_paused_local_only": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_IN_PROGRESS_OR_PAUSED_LOCAL_ONLY_REF,
        "rsr_op15_review_aborted_or_incomplete_retry_required": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_REVIEW_ABORTED_OR_INCOMPLETE_RETRY_REQUIRED_REF,
        "rsr_op15_bodyfree_leak_or_source_claim_blocked": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF,
        "rsr_op15_actual_review_evidence_ready_for_dhr_reintake_no_auto_execution": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF,
        "rsr_op15_manual_hold_unresolved_no_promotion": branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_MANUAL_HOLD_UNRESOLVED_NO_PROMOTION_REF,
    }
    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP15_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op14_contract_valid": op14_valid,
        "op14_status_ref": _bodyfree_status_ref(op14.get("rsr_op14_status_ref") if isinstance(op14, Mapping) else None, default="rsr_op14_status_missing"),
        "op14_final_validation_passed": bool(op14_valid and op14.get("rsr_op14_final_validation_passed") is True),
        "op14_body_leak_promotion_or_source_kind_blocked": bool(op14_valid and op14.get("rsr_op14_body_leak_promotion_or_source_kind_blocked") is True),
        "op14_complete_candidate_prerequisite_missing_refs": missing,
        "op14_complete_candidate_prerequisite_missing_ref_count": len(missing),
        "complete_candidate_prerequisite_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS),
        "complete_candidate_prerequisite_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS),
        "complete_candidate_prerequisite_satisfied_refs": satisfied,
        "complete_candidate_prerequisite_satisfied_ref_count": len(satisfied),
        "complete_candidate_prerequisite_missing_refs": missing,
        "complete_candidate_prerequisite_missing_ref_count": len(missing),
        "actual_evidence_complete_candidate": complete_candidate,
        "actual_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution": complete_candidate,
        "dhr_actual_source_claim_reintake_required_next": complete_candidate,
        "dhr_actual_source_claim_reintake_executed_here": False,
        "actual_source_claim_for_dhr_reintake_materialized_here_by_helper": False,
        "downstream_manual_decision_materialization_candidate_only": complete_candidate,
        "downstream_auto_execution_allowed": False,
        "manual_decision_required_without_auto_execution": True,
        "source_claim_bundle_candidate_bodyfree": True,
        "source_claim_bundle_candidate_ref": candidate_ref,
        "source_claim_bundle_candidate_source_kind_ref": source_kind_ref,
        "source_claim_bundle_candidate_review_session_id": session_id if complete_candidate else "",
        "source_claim_bundle_candidate_operation_receipt_ref": operation_receipt_ref,
        "source_claim_bundle_candidate_packet_request_ref": packet_request_ref,
        "source_claim_bundle_candidate_disposal_purge_receipt_ref": disposal_purge_receipt_ref,
        "source_claim_bundle_candidate_reviewed_case_count": reviewed_case_count,
        "source_claim_bundle_candidate_selection_row_count": selection_row_count,
        "source_claim_bundle_candidate_body_free": True,
        "rsr_op15_branch_ref": branch_ref,
        "rsr_op15_allowed_branch_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP15_ALLOWED_BRANCH_REFS),
        "rsr_op15_allowed_branch_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP15_ALLOWED_BRANCH_REFS),
        **branch_flags,
        "actual_review_evidence_complete_here": False,
        "dmd_execution_started_here": False,
        "r52_actual_execution_started_here": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "p7_complete": False,
        "release_allowed": False,
        "op15_reason_refs": _dedupe_clean_refs(reasons),
        "op15_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "op15_blocker_refs": _dedupe_clean_refs(blockers),
        "op15_blocker_ref_count": len(_dedupe_clean_refs(blockers)),
        "rsr_op15_does_not_execute_dhr_reintake": True,
        "rsr_op15_does_not_execute_dmd_or_r52": True,
        "rsr_op15_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op15_does_not_change_api_db_rn_runtime_response_key": True,
        "rsr_op15_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP15_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP15 branch resolver contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP15_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP15")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP15_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP15_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP15")
    for field, count_field in (("op14_complete_candidate_prerequisite_missing_refs", "op14_complete_candidate_prerequisite_missing_ref_count"), ("complete_candidate_prerequisite_refs", "complete_candidate_prerequisite_ref_count"), ("complete_candidate_prerequisite_satisfied_refs", "complete_candidate_prerequisite_satisfied_ref_count"), ("complete_candidate_prerequisite_missing_refs", "complete_candidate_prerequisite_missing_ref_count"), ("rsr_op15_allowed_branch_refs", "rsr_op15_allowed_branch_ref_count"), ("op15_reason_refs", "op15_reason_ref_count"), ("op15_blocker_refs", "op15_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP15 {count_field} changed")
    if tuple(data.get("complete_candidate_prerequisite_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP14_COMPLETE_CANDIDATE_PREREQUISITE_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 prerequisite refs changed")
    if tuple(data.get("rsr_op15_allowed_branch_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP15_ALLOWED_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 allowed branch refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP15_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP15_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 implemented/not-yet steps changed")
    for key in ("dhr_actual_source_claim_reintake_executed_here", "actual_source_claim_for_dhr_reintake_materialized_here_by_helper", "downstream_auto_execution_allowed", "actual_review_evidence_complete_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP15 false promotion boundary changed: {key}")
    for key in ("manual_decision_required_without_auto_execution", "source_claim_bundle_candidate_bodyfree", "source_claim_bundle_candidate_body_free", "rsr_op15_does_not_execute_dhr_reintake", "rsr_op15_does_not_execute_dmd_or_r52", "rsr_op15_does_not_start_p5_p6_p8_p7_or_release", "rsr_op15_does_not_change_api_db_rn_runtime_response_key", "rsr_op15_does_not_materialize_p8_question_spec"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP15 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 not-claimed boundary must stay false")
    branch_ref = data.get("rsr_op15_branch_ref")
    if branch_ref not in P7_R54_AHR_POST_DHR09_RSR_OP15_ALLOWED_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 branch ref is not allowed")
    branch_true_count = sum(1 for key in ("rsr_op15_wait_for_explicit_allow", "rsr_op15_stop_environment_or_material_repair_required", "rsr_op15_ready_to_start_actual_local_only_review", "rsr_op15_review_in_progress_or_paused_local_only", "rsr_op15_review_aborted_or_incomplete_retry_required", "rsr_op15_bodyfree_leak_or_source_claim_blocked", "rsr_op15_actual_review_evidence_ready_for_dhr_reintake_no_auto_execution", "rsr_op15_manual_hold_unresolved_no_promotion") if data.get(key) is True)
    if branch_true_count != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 must select exactly one branch flag")
    if branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF:
        for key in ("op14_contract_valid", "op14_final_validation_passed", "actual_evidence_complete_candidate", "actual_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution", "dhr_actual_source_claim_reintake_required_next", "downstream_manual_decision_materialization_candidate_only"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP15 complete candidate true field changed: {key}")
        if data.get("complete_candidate_prerequisite_missing_refs") != [] or data.get("op15_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 complete candidate cannot carry missing prerequisites or blockers")
        if data.get("source_claim_bundle_candidate_source_kind_ref") != P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 complete candidate source kind changed")
        if data.get("source_claim_bundle_candidate_reviewed_case_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT or data.get("source_claim_bundle_candidate_selection_row_count") != P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 complete candidate case counts changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_NO_AUTO_EXECUTION_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 complete candidate next step changed")
    else:
        if data.get("actual_evidence_complete_candidate") is not False or data.get("dhr_actual_source_claim_reintake_required_next") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 non-complete branch cannot claim evidence complete candidate")
        if branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF and data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODYFREE_LEAK_OR_SOURCE_CLAIM_BEFORE_DHR_REINTAKE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 blocked next step changed")
        if branch_ref == P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF and data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_RSR_OP03_EXPLICIT_ALLOW_GATE_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP15 explicit allow wait next step changed")
    return True


# RSR-OP16 additions: result memo / tests / selected regression closure.
P7_R54_AHR_POST_DHR09_RSR_OP16_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhr09.rsr."
    "op16_result_memo_tests_selected_regression_closure.bodyfree.v1"
)
P7_R54_AHR_POST_DHR09_RSR_OP16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_STEP_REFS[:17]
)
P7_R54_AHR_POST_DHR09_RSR_OP16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF: Final = (
    "RSR_RESULT_MEMO_TESTS_SELECTED_REGRESSION_CLOSED_BODYFREE"
)
P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF: Final = (
    "RSR_RESULT_MEMO_WAITING_FOR_OP15_BRANCH_RESOLUTION"
)
P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF: Final = (
    "RSR_RESULT_MEMO_TESTS_OR_REGRESSION_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF: Final = (
    "RSR_RESULT_MEMO_BODY_LEAK_OR_PROMOTION_BLOCKED"
)
P7_R54_AHR_POST_DHR09_RSR_OP16_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF,
)
P7_R54_AHR_POST_DHR09_RSR_OP16_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostDHR09_ActualLocalReview_RetryStartDecision_RSR_OP00_OP16_Result_20260704"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_RSR_OP16_TESTS_OR_REGRESSION_SUMMARY_REF: Final = (
    "repair_rsr_op16_tests_or_selected_regression_summary_before_result_memo_closure"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF: Final = (
    "blocked_rsr_op16_result_memo_body_leak_or_promotion_before_any_downstream_handoff"
)
P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_RSR_OP15_BRANCH_RESOLUTION_REF: Final = (
    "wait_for_rsr_op15_branch_resolution_before_result_memo_closure"
)
P7_R54_AHR_POST_DHR09_RSR_OP16_VERIFICATION_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "rsr_op16_target_tests",
    "rsr_op00_op16_accumulated_target",
    "dhr_op00_op09_selected_regression",
    "elr_dmd_alr_selected_regression",
    "services_ai_inference_compileall",
)
P7_R54_AHR_POST_DHR09_RSR_OP16_UNVERIFIED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "explicit_local_only_allow_receipt_actual_creation_unverified",
    "actual_body_full_packet_generation_unverified",
    "actual_local_only_human_review_execution_unverified",
    "actual_operation_receipt_real_creation_unverified",
    "sanitized_review_result_rows_real_creation_unverified",
    "rating_rows_real_creation_unverified",
    "question_need_observation_rows_real_creation_unverified",
    "disposal_purge_real_execution_unverified",
    "dhr_actual_source_claim_reintake_execution_unverified",
    "dmd_execution_unverified",
    "r52_actual_execution_unverified",
    "p5_finalization_unverified",
    "p6_start_unverified",
    "p8_start_unverified",
    "p8_question_design_unverified",
    "p8_question_implementation_unverified",
    "p7_complete_unverified",
    "release_decision_unverified",
    "full_backend_suite_green_unverified",
    "rn_real_device_modal_verification_unverified",
)
P7_R54_AHR_POST_DHR09_RSR_OP16_NO_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "rsr_op16_result_memo_closed_is_not_actual_review_execution",
    "rsr_op16_target_tests_green_is_not_actual_review_execution",
    "rsr_op16_selected_regression_green_is_not_actual_evidence_complete",
    "rsr_op16_compileall_ok_is_not_full_backend_suite_green",
    "rsr_op15_complete_candidate_is_not_dhr_reintake_execution",
    "rsr_op15_complete_candidate_is_not_dmd_execution",
    "rsr_op15_complete_candidate_is_not_r52_execution",
    "rsr_op15_complete_candidate_is_not_p5_p6_p8_p7_or_release",
    "question_need_observation_rows_remain_p7_p8_bridge_material_only",
    "result_memo_bodyfree_closure_does_not_materialize_p8_question_spec",
)

P7_R54_AHR_POST_DHR09_RSR_OP16_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op15_contract_valid", "op15_branch_ref", "op15_next_required_step", "op15_actual_evidence_complete_candidate", "op15_dhr_actual_source_claim_reintake_required_next", "op15_downstream_auto_execution_allowed", "op15_selected_branch_bodyfree",
    "result_memo_ref", "result_memo_bodyfree_closed", "result_memo_created_here", "result_memo_contains_body_full_packet", "result_memo_contains_raw_input", "result_memo_contains_returned_surface_body", "result_memo_contains_reviewer_free_text", "result_memo_contains_question_text", "result_memo_contains_local_path_hash_or_terminal_body",
    "target_test_summary", "rsr_accumulated_target_summary", "dhr_selected_regression_summary", "elr_dmd_alr_selected_regression_summary", "compileall_summary",
    "verification_summary_refs", "verification_summary_ref_count", "verification_summary_present_refs", "verification_summary_present_ref_count", "verification_summary_missing_refs", "verification_summary_missing_ref_count", "verification_summary_green_refs", "verification_summary_green_ref_count", "verification_summary_non_green_refs", "verification_summary_non_green_ref_count", "verification_total_passed_count", "verification_total_failed_count", "verification_any_timed_out", "verification_all_required_summaries_green", "compileall_ok",
    "op16_forbidden_payload_key_path_refs", "op16_forbidden_payload_key_path_count", "op16_body_like_value_path_refs", "op16_body_like_value_path_count", "op16_promotion_claim_refs", "op16_promotion_claim_ref_count",
    "modified_file_refs", "modified_file_ref_count", "new_file_refs", "new_file_ref_count", "changed_file_refs", "changed_file_ref_count",
    "selected_branch_ref", "selected_next_required_step_after_result_memo", "manual_decision_required_without_auto_execution", "downstream_auto_execution_allowed", "actual_review_evidence_complete_here",
    "rsr_op16_status_ref", "rsr_op16_allowed_status_refs", "rsr_op16_allowed_status_ref_count", "rsr_op16_closed", "rsr_op16_waiting_for_op15", "rsr_op16_repair_required", "rsr_op16_body_leak_or_promotion_blocked",
    "op16_reason_refs", "op16_reason_ref_count", "op16_blocker_refs", "op16_blocker_ref_count",
    "rsr_op16_does_not_execute_actual_review", "rsr_op16_does_not_create_actual_receipts_or_rows", "rsr_op16_does_not_execute_disposal_purge", "rsr_op16_does_not_execute_dhr_reintake_dmd_or_r52", "rsr_op16_does_not_start_p5_p6_p8_p7_or_release", "rsr_op16_does_not_change_api_db_rn_runtime_response_key", "rsr_op16_does_not_materialize_p8_question_spec", "rsr_op16_does_not_claim_full_backend_or_rn_real_device_green",
    "unverified_boundary_refs", "unverified_boundary_ref_count", "op16_no_promotion_refs", "op16_no_promotion_ref_count", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "post_dhr09_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_DHR09_RSR_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _rsr_op16_safe_count(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _normalize_rsr_op16_verification_summary(summary: Mapping[str, Any] | None, *, default_status_ref: str) -> tuple[dict[str, Any], bool, bool, list[str], list[str], list[str]]:
    present = isinstance(summary, Mapping)
    raw_summary: Mapping[str, Any] = summary if isinstance(summary, Mapping) else {}
    status_ref = _clean_ref(raw_summary.get("status_ref"), default=default_status_ref, max_length=180)
    passed_count = _rsr_op16_safe_count(raw_summary.get("passed_count"))
    failed_count = _rsr_op16_safe_count(raw_summary.get("failed_count"))
    timed_out = raw_summary.get("timed_out") is True
    ok = raw_summary.get("ok") is True
    body_free = raw_summary.get("body_free") is not False
    forbidden_paths = _scan_forbidden_payload_key_paths(raw_summary, path=default_status_ref)
    body_like_paths = _scan_body_like_value_paths(raw_summary, path=default_status_ref)
    promotion_claims = _promotion_claim_refs(raw_summary)
    status_lower = status_ref.lower()
    status_green = any(token in status_lower for token in ("passed", "green", "ok", "compileall_ok", "closed"))
    green = bool(
        present
        and body_free
        and not forbidden_paths
        and not body_like_paths
        and not promotion_claims
        and failed_count == 0
        and not timed_out
        and (ok or passed_count > 0 or status_green)
    )
    normalized = {
        "status_ref": status_ref,
        "summary_present": present,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "timed_out": timed_out,
        "ok": ok or green,
        "green": green,
        "body_free": True,
    }
    return normalized, present, green, forbidden_paths, body_like_paths, promotion_claims


def _rsr_op16_branch_flags(status_ref: str) -> dict[str, bool]:
    return {
        "rsr_op16_closed": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF,
        "rsr_op16_waiting_for_op15": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF,
        "rsr_op16_repair_required": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF,
        "rsr_op16_body_leak_or_promotion_blocked": status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF,
    }


def build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure(
    *,
    branch_resolution: Mapping[str, Any] | None = None,
    target_test_summary: Mapping[str, Any] | None = None,
    rsr_accumulated_target_summary: Mapping[str, Any] | None = None,
    dhr_selected_regression_summary: Mapping[str, Any] | None = None,
    elr_dmd_alr_selected_regression_summary: Mapping[str, Any] | None = None,
    compileall_summary: Mapping[str, Any] | None = None,
    result_memo_ref: Any = P7_R54_AHR_POST_DHR09_RSR_OP16_RESULT_MEMO_REF,
    modified_file_refs: Sequence[Any] | None = None,
    new_file_refs: Sequence[Any] | None = None,
    additional_bodyfree_materials: Mapping[str, Mapping[str, Any] | None] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build the RSR-OP16 body-free result memo/test/regression closure."""
    session_id = _safe_review_session_id(review_session_id or (branch_resolution or {}).get("review_session_id"))
    try:
        op15_contract_valid = bool(
            isinstance(branch_resolution, Mapping)
            and assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(branch_resolution) is True
        )
    except ValueError:
        op15_contract_valid = False

    summaries_raw = {
        "rsr_op16_target_tests": target_test_summary,
        "rsr_op00_op16_accumulated_target": rsr_accumulated_target_summary,
        "dhr_op00_op09_selected_regression": dhr_selected_regression_summary,
        "elr_dmd_alr_selected_regression": elr_dmd_alr_selected_regression_summary,
        "services_ai_inference_compileall": compileall_summary,
    }
    normalized_summaries: dict[str, dict[str, Any]] = {}
    present_refs: list[str] = []
    missing_refs: list[str] = []
    green_refs: list[str] = []
    non_green_refs: list[str] = []
    forbidden_paths: list[str] = []
    body_like_paths: list[str] = []
    promotion_claims: list[str] = []
    total_passed = 0
    total_failed = 0
    any_timed_out = False
    for summary_ref, summary in summaries_raw.items():
        normalized, present, green, forbidden, body_like, promotions = _normalize_rsr_op16_verification_summary(
            summary,
            default_status_ref=f"{summary_ref}_missing",
        )
        normalized_summaries[summary_ref] = normalized
        if present:
            present_refs.append(summary_ref)
        else:
            missing_refs.append(summary_ref)
        if green:
            green_refs.append(summary_ref)
        else:
            non_green_refs.append(summary_ref)
        total_passed += int(normalized["passed_count"])
        total_failed += int(normalized["failed_count"])
        any_timed_out = any_timed_out or bool(normalized["timed_out"])
        forbidden_paths.extend(forbidden)
        body_like_paths.extend(body_like)
        promotion_claims.extend(promotions)

    extra_materials = additional_bodyfree_materials or {}
    for name, material in extra_materials.items():
        if not isinstance(material, Mapping):
            continue
        safe_name = _clean_ref(name, default="additional_material", max_length=120)
        forbidden_paths.extend(_scan_forbidden_payload_key_paths(material, path=f"additional_bodyfree_materials.{safe_name}"))
        body_like_paths.extend(_scan_body_like_value_paths(material, path=f"additional_bodyfree_materials.{safe_name}"))
        promotion_claims.extend(_promotion_claim_refs(material))

    all_green = len(green_refs) == len(P7_R54_AHR_POST_DHR09_RSR_OP16_VERIFICATION_SUMMARY_REFS)
    compileall_ok = normalized_summaries["services_ai_inference_compileall"]["green"] is True
    reasons: list[str] = []
    blockers: list[str] = []
    if not op15_contract_valid:
        blockers.append("op15_branch_resolution_missing_or_invalid")
    if missing_refs:
        reasons.append("verification_summary_missing")
        blockers.append("verification_summary_missing")
    if non_green_refs:
        reasons.append("verification_summary_not_green")
        blockers.append("verification_summary_not_green")
    if total_failed > 0:
        blockers.append("verification_failed_count_nonzero")
    if any_timed_out:
        blockers.append("verification_timed_out")
    if not compileall_ok:
        blockers.append("compileall_summary_not_green")
    if forbidden_paths or body_like_paths or promotion_claims:
        blockers.append("result_memo_body_leak_or_promotion_detected")

    if forbidden_paths or body_like_paths or promotion_claims:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF
    elif not op15_contract_valid:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_RSR_OP15_BRANCH_RESOLUTION_REF
    elif not all_green or total_failed > 0 or any_timed_out or not compileall_ok:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF
        next_step = P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_RSR_OP16_TESTS_OR_REGRESSION_SUMMARY_REF
    else:
        status_ref = P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF
        next_step = _clean_ref(
            branch_resolution.get("next_required_step") if isinstance(branch_resolution, Mapping) else None,
            default=P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_MANUAL_HOLD_AFTER_OP15_NO_PROMOTION_REF,
            max_length=220,
        )
        reasons.append("result_memo_tests_selected_regression_closed_bodyfree")

    selected_branch_ref = _clean_ref(
        branch_resolution.get("rsr_op15_branch_ref") if isinstance(branch_resolution, Mapping) else None,
        default="rsr_op15_branch_missing",
        max_length=220,
    )
    modified_refs = _dedupe_clean_refs(modified_file_refs or ())
    new_refs = _dedupe_clean_refs(new_file_refs or ())
    changed_refs = _dedupe_clean_refs([*modified_refs, *new_refs])
    result_memo_closed = status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF
    branch_flags = _rsr_op16_branch_flags(status_ref)

    return {
        "schema_version": P7_R54_AHR_POST_DHR09_RSR_OP16_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "step": P7_R54_AHR_POST_DHR09_RSR_STEP,
        "scope": P7_R54_AHR_POST_DHR09_RSR_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHR09_RSR_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF,
        "current_phase": P7_R54_AHR_POST_DHR09_RSR_PHASE,
        "material_id": "p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_20260704",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHR09_RSR_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op15_contract_valid": op15_contract_valid,
        "op15_branch_ref": selected_branch_ref,
        "op15_next_required_step": _clean_ref(branch_resolution.get("next_required_step") if isinstance(branch_resolution, Mapping) else None, default="op15_next_required_step_missing", max_length=220),
        "op15_actual_evidence_complete_candidate": bool(op15_contract_valid and branch_resolution.get("actual_evidence_complete_candidate") is True),
        "op15_dhr_actual_source_claim_reintake_required_next": bool(op15_contract_valid and branch_resolution.get("dhr_actual_source_claim_reintake_required_next") is True),
        "op15_downstream_auto_execution_allowed": False,
        "op15_selected_branch_bodyfree": op15_contract_valid,
        "result_memo_ref": _clean_ref(result_memo_ref, default=P7_R54_AHR_POST_DHR09_RSR_OP16_RESULT_MEMO_REF, max_length=220),
        "result_memo_bodyfree_closed": result_memo_closed,
        "result_memo_created_here": False,
        "result_memo_contains_body_full_packet": False,
        "result_memo_contains_raw_input": False,
        "result_memo_contains_returned_surface_body": False,
        "result_memo_contains_reviewer_free_text": False,
        "result_memo_contains_question_text": False,
        "result_memo_contains_local_path_hash_or_terminal_body": False,
        "target_test_summary": normalized_summaries["rsr_op16_target_tests"],
        "rsr_accumulated_target_summary": normalized_summaries["rsr_op00_op16_accumulated_target"],
        "dhr_selected_regression_summary": normalized_summaries["dhr_op00_op09_selected_regression"],
        "elr_dmd_alr_selected_regression_summary": normalized_summaries["elr_dmd_alr_selected_regression"],
        "compileall_summary": normalized_summaries["services_ai_inference_compileall"],
        "verification_summary_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP16_VERIFICATION_SUMMARY_REFS),
        "verification_summary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP16_VERIFICATION_SUMMARY_REFS),
        "verification_summary_present_refs": present_refs,
        "verification_summary_present_ref_count": len(present_refs),
        "verification_summary_missing_refs": missing_refs,
        "verification_summary_missing_ref_count": len(missing_refs),
        "verification_summary_green_refs": green_refs,
        "verification_summary_green_ref_count": len(green_refs),
        "verification_summary_non_green_refs": non_green_refs,
        "verification_summary_non_green_ref_count": len(non_green_refs),
        "verification_total_passed_count": total_passed,
        "verification_total_failed_count": total_failed,
        "verification_any_timed_out": any_timed_out,
        "verification_all_required_summaries_green": all_green,
        "compileall_ok": compileall_ok,
        "op16_forbidden_payload_key_path_refs": _dedupe_clean_refs(forbidden_paths, max_length=320),
        "op16_forbidden_payload_key_path_count": len(_dedupe_clean_refs(forbidden_paths, max_length=320)),
        "op16_body_like_value_path_refs": _dedupe_clean_refs(body_like_paths, max_length=320),
        "op16_body_like_value_path_count": len(_dedupe_clean_refs(body_like_paths, max_length=320)),
        "op16_promotion_claim_refs": _dedupe_clean_refs(promotion_claims, max_length=220),
        "op16_promotion_claim_ref_count": len(_dedupe_clean_refs(promotion_claims, max_length=220)),
        "modified_file_refs": modified_refs,
        "modified_file_ref_count": len(modified_refs),
        "new_file_refs": new_refs,
        "new_file_ref_count": len(new_refs),
        "changed_file_refs": changed_refs,
        "changed_file_ref_count": len(changed_refs),
        "selected_branch_ref": selected_branch_ref,
        "selected_next_required_step_after_result_memo": next_step,
        "manual_decision_required_without_auto_execution": True,
        "downstream_auto_execution_allowed": False,
        "actual_review_evidence_complete_here": False,
        "rsr_op16_status_ref": status_ref,
        "rsr_op16_allowed_status_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP16_ALLOWED_STATUS_REFS),
        "rsr_op16_allowed_status_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP16_ALLOWED_STATUS_REFS),
        **branch_flags,
        "op16_reason_refs": _dedupe_clean_refs(reasons),
        "op16_reason_ref_count": len(_dedupe_clean_refs(reasons)),
        "op16_blocker_refs": _dedupe_clean_refs(blockers),
        "op16_blocker_ref_count": len(_dedupe_clean_refs(blockers)),
        "rsr_op16_does_not_execute_actual_review": True,
        "rsr_op16_does_not_create_actual_receipts_or_rows": True,
        "rsr_op16_does_not_execute_disposal_purge": True,
        "rsr_op16_does_not_execute_dhr_reintake_dmd_or_r52": True,
        "rsr_op16_does_not_start_p5_p6_p8_p7_or_release": True,
        "rsr_op16_does_not_change_api_db_rn_runtime_response_key": True,
        "rsr_op16_does_not_materialize_p8_question_spec": True,
        "rsr_op16_does_not_claim_full_backend_or_rn_real_device_green": True,
        "unverified_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP16_UNVERIFIED_BOUNDARY_REFS),
        "unverified_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP16_UNVERIFIED_BOUNDARY_REFS),
        "op16_no_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_OP16_NO_PROMOTION_REFS),
        "op16_no_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_OP16_NO_PROMOTION_REFS),
        "claim_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHR09_RSR_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHR09_RSR_OP16_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "post_dhr09_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract(data: Mapping[str, Any]) -> bool:
    """Assert RSR-OP16 result memo/tests/selected regression closure contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_DHR09_RSR_OP16_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHR09-RSR-OP16")
    if set(data) != set(P7_R54_AHR_POST_DHR09_RSR_OP16_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_DHR09_RSR_OP16_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF, source="P7-R54-AHR-PostDHR09-RSR-OP16")
    list_count_fields = (
        ("verification_summary_refs", "verification_summary_ref_count"),
        ("verification_summary_present_refs", "verification_summary_present_ref_count"),
        ("verification_summary_missing_refs", "verification_summary_missing_ref_count"),
        ("verification_summary_green_refs", "verification_summary_green_ref_count"),
        ("verification_summary_non_green_refs", "verification_summary_non_green_ref_count"),
        ("op16_forbidden_payload_key_path_refs", "op16_forbidden_payload_key_path_count"),
        ("op16_body_like_value_path_refs", "op16_body_like_value_path_count"),
        ("op16_promotion_claim_refs", "op16_promotion_claim_ref_count"),
        ("modified_file_refs", "modified_file_ref_count"),
        ("new_file_refs", "new_file_ref_count"),
        ("changed_file_refs", "changed_file_ref_count"),
        ("rsr_op16_allowed_status_refs", "rsr_op16_allowed_status_ref_count"),
        ("op16_reason_refs", "op16_reason_ref_count"),
        ("op16_blocker_refs", "op16_blocker_ref_count"),
        ("unverified_boundary_refs", "unverified_boundary_ref_count"),
        ("op16_no_promotion_refs", "op16_no_promotion_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    )
    for field, count_field in list_count_fields:
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP16 {count_field} changed")
    if tuple(data.get("verification_summary_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP16_VERIFICATION_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 verification summary refs changed")
    if tuple(data.get("rsr_op16_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP16_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 allowed status refs changed")
    if tuple(data.get("unverified_boundary_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP16_UNVERIFIED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 unverified boundary refs changed")
    if tuple(data.get("op16_no_promotion_refs") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP16_NO_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 no-promotion refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP16_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHR09_RSR_OP16_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 implemented/not-yet steps changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_DHR09_RSR_STEP_REFS) or data.get("not_yet_implemented_steps") != []:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 must close RSR-OP00 through RSR-OP16 only")
    status_ref = data.get("rsr_op16_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHR09_RSR_OP16_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 status ref is not allowed")
    branch_true_count = sum(1 for key in ("rsr_op16_closed", "rsr_op16_waiting_for_op15", "rsr_op16_repair_required", "rsr_op16_body_leak_or_promotion_blocked") if data.get(key) is True)
    if branch_true_count != 1:
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 must select exactly one status flag")
    for key in ("result_memo_created_here", "result_memo_contains_body_full_packet", "result_memo_contains_raw_input", "result_memo_contains_returned_surface_body", "result_memo_contains_reviewer_free_text", "result_memo_contains_question_text", "result_memo_contains_local_path_hash_or_terminal_body", "downstream_auto_execution_allowed", "actual_review_evidence_complete_here", "op15_downstream_auto_execution_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP16 false boundary changed: {key}")
    for key in ("manual_decision_required_without_auto_execution", "rsr_op16_does_not_execute_actual_review", "rsr_op16_does_not_create_actual_receipts_or_rows", "rsr_op16_does_not_execute_disposal_purge", "rsr_op16_does_not_execute_dhr_reintake_dmd_or_r52", "rsr_op16_does_not_start_p5_p6_p8_p7_or_release", "rsr_op16_does_not_change_api_db_rn_runtime_response_key", "rsr_op16_does_not_materialize_p8_question_spec", "rsr_op16_does_not_claim_full_backend_or_rn_real_device_green"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHR09-RSR-OP16 required true boundary changed: {key}")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 not-claimed boundary must stay false")
    if set(data.get("changed_file_refs") or []) != set([*(data.get("modified_file_refs") or []), *(data.get("new_file_refs") or [])]):
        raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 changed file refs must match modified + new refs")
    if status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_CLOSED_BODYFREE_REF:
        if data.get("op15_contract_valid") is not True or data.get("result_memo_bodyfree_closed") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 closed branch requires valid OP15 and body-free memo closure")
        if data.get("verification_all_required_summaries_green") is not True or data.get("compileall_ok") is not True:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 closed branch requires green summaries and compileall")
        if data.get("verification_summary_missing_refs") != [] or data.get("verification_summary_non_green_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 closed branch cannot carry missing/non-green summaries")
        if data.get("verification_total_failed_count") != 0 or data.get("verification_any_timed_out") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 closed branch cannot carry failures/timeouts")
        if data.get("op16_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 closed branch cannot carry blockers")
        if data.get("next_required_step") != data.get("selected_next_required_step_after_result_memo"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 closed next step mismatch")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_WAITING_FOR_OP15_REF:
        if data.get("op15_contract_valid") is not False or data.get("result_memo_bodyfree_closed") is not False:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 waiting branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_RSR_OP15_BRANCH_RESOLUTION_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_REPAIR_REQUIRED_REF:
        if data.get("result_memo_bodyfree_closed") is not False or not data.get("op16_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 repair branch changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_REPAIR_RSR_OP16_TESTS_OR_REGRESSION_SUMMARY_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DHR09_RSR_OP16_STATUS_BODY_LEAK_OR_PROMOTION_BLOCKED_REF:
        if data.get("result_memo_bodyfree_closed") is not False or not data.get("op16_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 blocked branch changed")
        if not (data.get("op16_forbidden_payload_key_path_refs") or data.get("op16_body_like_value_path_refs") or data.get("op16_promotion_claim_refs")):
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 blocked branch requires leak/promotion refs")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_RSR_OP16_BODY_LEAK_OR_PROMOTION_REF:
            raise ValueError("P7-R54-AHR-PostDHR09-RSR-OP16 blocked next step changed")
    return True


# Full-title aliases used by adjacent R54-AHR helpers/tests.
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09 = (
    build_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op00_scope_no_touch_no_promotion_refreeze_after_dhr_op09_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake = (
    build_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op01_dhr_op09_result_memo_selected_branch_next_step_intake_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_upstream_relationship_verification = (
    build_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_upstream_relationship_verification_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op02_upstream_relationship_verification_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate = (
    build_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op03_explicit_local_only_allow_receipt_acceptance_gate_contract
)

build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op04_readiness_blocker_classifier = (
    build_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op04_readiness_blocker_classifier_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op04_readiness_blocker_classifier_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary = (
    build_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op05_local_only_review_session_envelope_reviewer_person_boundary_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op06_24_case_body_full_packet_transient_request_boundary = (
    build_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op06_24_case_body_full_packet_transient_request_boundary_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake = (
    build_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op07_body_full_packet_generation_receipt_export_denylist_scan_intake_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze = (
    build_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op08_selection_only_reviewer_form_rating_axis_contract_freeze_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op09_actual_local_only_review_lifecycle_state_capture = (
    build_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op09_actual_local_only_review_lifecycle_state_capture_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op10_actual_operation_receipt_intake = (
    build_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op10_actual_operation_receipt_intake_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op10_actual_operation_receipt_intake_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op11_sanitized_review_result_rows_rating_rows_intake = (
    build_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op11_sanitized_review_result_rows_rating_rows_intake_contract
)

build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only = (
    build_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op12_question_need_observation_rows_intake_p7_p8_bridge_material_only_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op13_disposal_purge_receipt_intake = (
    build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op13_disposal_purge_receipt_intake_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract
)

build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op14_final_no_leak_no_promotion_source_kind_validation = (
    build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver = (
    build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract
)
build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op16_result_memo_tests_selected_regression_closure = (
    build_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure
)
assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op16_result_memo_tests_selected_regression_closure_contract = (
    assert_p7_r54_ahr_post_dhr09_rsr_op16_result_memo_tests_selected_regression_closure_contract
)
