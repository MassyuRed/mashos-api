# -*- coding: utf-8 -*-
"""Post-PMN23 downstream manual decision hold evidence-intake helpers.

DMH-OP00 through DMH-OP03 intentionally form the first body-free bridge after
PMN-OP23:

* DMH-OP00 re-freezes the Post-PMN23 scope, no-touch boundary, and
  no-promotion boundary.  It does not intake the PMN-OP23 material, generate a
  body-full packet, run actual human review, create receipts/rows, start P8, run
  R52, complete P7, or allow release.
* DMH-OP01 intakes the PMN-OP23 downstream manual decision hold and the
  body-free result-memo current-status envelope.  It confirms that the next step
  remains ``downstream_manual_decision_hold_after_post_mn11_pmn_op23_acceptance_bodyfree``
  and that real-operation actual review evidence is still missing.
* DMH-OP02 decides, body-free, that the existing Post-MN11 PMN helper and the
  existing PostCR22 EX07-EX18 line are reusable as support material.  It does not
  execute re-entry and does not create another giant wrapper.
* DMH-OP03 accepts a body-free explicit-allow receipt and local-only review
  session envelope.  It allows only the next boundary decision; it still does not
  generate a body-full packet, run actual review, create rows, execute purge,
  start P8, run R52, complete P7, or allow release.
* DMH-OP04/OP05 fix the 24-case manifest, packet request boundary, and
  body-free packet-generation receipt intake boundary without exporting packet
  content or claiming actual review evidence.
* DMH-OP06 accepts a body-free packet completeness / export-denylist scan
  receipt shape.  It confirms counts and no-export markers, while still not
  claiming a real folder scan, actual human review, rows, purge, P8, R52, P7
  complete, or release.
* DMH-OP07 finalizes reviewer-person confirmation and a selection-only form
  boundary.  It freezes the human-review form contract without starting the
  actual 24-case local-only review.
* DMH-OP08/OP09 accept only body-free lifecycle and operation-receipt shapes.
  They do not create review rows, rating rows, question observation rows, purge
  receipts, evidence-complete predicates, or downstream promotion.
* DMH-OP10 intakes sanitized selection-only review-result rows only when their
  body-free provenance remains actual-person local review and not helper, unit
  test, synthetic, or historical reuse.
* DMH-OP11 normalizes body-free rating rows and threshold summaries from OP10
  rows as decision material only.  It does not make P5 final, start P6/P8/R52,
  complete P7, or allow release.
* DMH-OP12 normalizes body-free question-need observation rows as P7/P8
  Bridge material.  It does not materialize question text, draft question text,
  question trigger/storage, P8 implementation spec, or P8 start.
* DMH-OP13 checks rating/question consistency and separates blocker routes so
  weak rating, safe-display risk, readfeel repair, execution blockers, and
  inconclusive material cannot escape into P8 candidates.  It does not create
  disposal receipts, complete actual evidence, start P5/P6/P8/R52, complete
  P7, or allow release.
* DMH-OP14/OP15 accept only body-free disposal/purge receipt material and final
  no-body/no-question/no-path/no-hash/no-touch validation material.  They close
  the packet lifecycle boundary for later evidence predicates but do not run
  disposal, complete evidence, execute PostCR22 re-entry, or promote downstream.
* DMH-OP16 evaluates the actual-review evidence-complete predicate from the
  already accepted body-free evidence bundle.  It can mark the predicate result
  true only when every prior intake boundary is ready, but still does not run
  review, create rows, start P5/P6/P8/R52, complete P7, or allow release.
* DMH-OP17 wraps that completed predicate in a PostCR22 EX07-EX18 re-entry
  envelope.  It makes the envelope ready only; it does not execute PostCR22
  re-entry, R52, P5/P6/P8/P7, or release.
* DMH-OP18 closes the body-free result memo / downstream manual decision
  hold finalizer.  It selects the next manual step, but still does not execute
  PostCR22 re-entry, R52, P5/P6/P8/P7, or release.

The PMN-OP23 helper contract can carry a contract-fixture completion predicate;
DMH-OP01 and later DMH steps must not promote that fixture predicate into
real-operation actual human review evidence.  The current real-operation status
remains body-full packet not-run, local human review not-run, receipts/rows
not-received, disposal not-run, and P5/P6/P8/R52/P7/release closed until later
DMH steps receive actual local-only evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import P7_PHASE, P7_SOURCE_MODE, clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630 as pmn


P7_R54_AHR_POST_PMN23_DMH_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op00_scope_no_touch_no_promotion_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP01_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op01_pmn_op23_downstream_manual_decision_hold_intake.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP02_EXISTING_PMN_POSTCR22_EX_REUSE_DECISION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op02_existing_pmn_postcr22_ex_reuse_decision.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_LOCAL_ONLY_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op03_explicit_allow_receipt_local_only_review_session_envelope.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op03_explicit_allow_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_PMN_OP23_RESULT_MEMO_CURRENT_STATUS_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "pmn_op23_result_memo_current_status.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_STEP: Final = (
    "R54-AHR-PostPMN23_DownstreamManualDecisionHold_EvidenceIntake_20260701"
)
P7_R54_AHR_POST_PMN23_DMH_SCOPE: Final = (
    "p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_entry"
)
P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND: Final = (
    "r54_ahr_post_pmn23_downstream_manual_decision_hold_bodyfree_evidence_intake_boundary"
)
P7_R54_AHR_POST_PMN23_DMH_DEFAULT_REVIEW_SESSION_ID: Final = (
    "r54_ahr_postpmn23_dmh_evidence_intake_session_20260701_"
    "current_received_264_85_258_171_v1"
)
P7_R54_AHR_POST_PMN23_DMH_CHOSEN_STAGE_REF: Final = (
    "P7-R54-AHR Post-PMN-OP23 Downstream Manual Decision Hold -> "
    "Actual Local-only Human Review Operation Evidence Intake Entry"
)

P7_R54_AHR_POST_PMN23_DMH_OP00_STEP_REF: Final = (
    "R54-AHR-PostPMN23-DMH-OP00_scope_no_touch_no_promotion_re_freeze"
)
P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF: Final = (
    "R54-AHR-PostPMN23-DMH-OP01_pmn_op23_downstream_manual_decision_hold_intake"
)
P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF: Final = (
    "R54-AHR-PostPMN23-DMH-OP02_existing_pmn_postcr22_ex_reuse_decision"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF: Final = (
    "R54-AHR-PostPMN23-DMH-OP03_explicit_allow_receipt_local_only_review_session_envelope"
)
P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_or_stop"
)

P7_R54_AHR_POST_PMN23_DMH_OP01_READY_STATUS_REF: Final = (
    "DMH_OP01_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_INTAKE_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_STATUS_REF: Final = (
    "DMH_OP01_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP01_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_STATUS_REF,
)

P7_R54_AHR_POST_PMN23_DMH_OP02_READY_STATUS_REF: Final = (
    "DMH_OP02_EXISTING_PMN_POSTCR22_EX_REUSE_DECISION_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_STATUS_REF: Final = (
    "DMH_OP02_EXISTING_PMN_POSTCR22_EX_REUSE_DECISION_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP02_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP03_READY_STATUS_REF: Final = (
    "DMH_OP03_EXPLICIT_ALLOW_RECEIPT_LOCAL_ONLY_REVIEW_SESSION_ENVELOPE_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_STATUS_REF: Final = (
    "DMH_OP03_EXPLICIT_ALLOW_RECEIPT_LOCAL_ONLY_REVIEW_SESSION_ENVELOPE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP03_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_STATUS_REF,
)

P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT: Final = pmn.P7_R54_AHR_POST_MN11_REQUIRED_CASE_COUNT
P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF: Final = pmn.P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_REF
P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = (
    pmn.P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_BASIS_ALLOWED_REF
)
P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_EVIDENCE_STATUS_REF: Final = (
    pmn.P7_R54_AHR_POST_MN11_ACTUAL_REVIEW_EVIDENCE_STATUS_REF
)
P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF: Final = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_REF
)
P7_R54_AHR_POST_PMN23_DMH_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostMN11_ActualLocalOnlyHumanReviewOperation_PMN_OP00_OP23_Result_20260630.md"
)

P7_R54_AHR_POST_PMN23_DMH_EXISTING_PMN_HELPER_REF: Final = (
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630.py"
)
P7_R54_AHR_POST_PMN23_DMH_EXISTING_POSTCR22_EX_HELPER_REF: Final = (
    "ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629.py"
)
P7_R54_AHR_POST_PMN23_DMH_EXISTING_PMN_REUSE_ROLE_REFS: Final[tuple[str, ...]] = (
    "post_mn11_pmn_op00_op23_bodyfree_contract_boundary_reference",
    "scope_no_touch_no_promotion_boundary_reference",
    "local_only_explicit_allow_and_packet_boundary_reference",
    "actual_source_guard_and_selection_only_boundary_reference",
    "result_memo_acceptance_fail_closed_boundary_reference",
)
P7_R54_AHR_POST_PMN23_DMH_EXISTING_POSTCR22_EX_REENTRY_ROLE_REFS: Final[tuple[str, ...]] = (
    *pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS,
)
P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_REF: Final = (
    "post_pmn23_dmh_op03_explicit_allow_receipt_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_REF: Final = (
    "post_pmn23_actual_review_local_only_body_full_packet_generation_explicit_allow_bodyfree_20260702"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOW_SCOPE_REF: Final = (
    "post_pmn23_actual_review_local_only_body_full_packet_generation_for_24case_review_only"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_LOCAL_REVIEW_ROOT_REF: Final = (
    "post_pmn23_local_only_review_workspace_ref_bodyfree"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_RETENTION_POLICY_REF: Final = (
    "local_body_full_packet_same_day_or_shorter_purge_required"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_DISPOSAL_POLICY_REF: Final = (
    "post_review_body_full_packet_temporary_form_and_notes_purge_required"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_EXPORT_DENYLIST_POLICY_REF: Final = (
    "deny_raw_body_question_text_path_hash_terminal_output"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    *pmn.P7_R54_AHR_POST_MN11_PMN_OP04_REQUIRED_DELETE_TARGET_REFS,
)
P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_REQUIRED_REF: Final = (
    "DMH_EXPLICIT_ALLOW_REQUIRED"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_ACCEPTED_REF: Final = (
    "DMH_EXPLICIT_ALLOW_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_REVIEW_SESSION_STATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_REQUIRED_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_ACCEPTED_REF,
    "DMH_LOCAL_ONLY_WORKSPACE_READY_BODYFREE",
)
P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_READY_SESSION_TRANSITION_REFS: Final[tuple[str, ...]] = (
    "DMH_HOLD_INTAKE_READY_TO_DMH_EXPLICIT_ALLOW_REQUIRED",
    "DMH_EXPLICIT_ALLOW_REQUIRED_TO_DMH_EXPLICIT_ALLOW_ACCEPTED_BODYFREE",
)
P7_R54_AHR_POST_PMN23_DMH_OP03_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS: Final[tuple[str, ...]] = (
    "DMH_EXPLICIT_ALLOW_ACCEPTED_BODYFREE_TO_BODY_FULL_PACKET_GENERATED_LOCAL_ONLY",
    "DMH_EXPLICIT_ALLOW_ACCEPTED_BODYFREE_TO_P8_START",
    "DMH_EXPLICIT_ALLOW_ACCEPTED_BODYFREE_TO_R52_ACTUAL_EXECUTION",
    "DMH_EXPLICIT_ALLOW_ACCEPTED_BODYFREE_TO_P7_COMPLETE",
    "DMH_EXPLICIT_ALLOW_ACCEPTED_BODYFREE_TO_RELEASE_ALLOWED",
)

P7_R54_AHR_POST_PMN23_DMH_LOCAL_RECEIVED_ZIP_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(274).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(90).zip",
    "roadmap_zip_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(9).zip",
    "rn_zip_ref": "Cocolon(263).zip",
    "backend_zip_ref": "mashos-api(176).zip",
}

P7_R54_AHR_POST_PMN23_DMH_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_EmlisAI_P7_R54AHR_PostPMN_OP23_DownstreamManualDecisionHold_PreDesignMemo_20260701.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostPMN_OP23_DownstreamManualDecisionHold_ActualLocalOnlyHumanReviewOperation_EvidenceIntake_DetailedDesign_ImplementationOrder_20260701.md",
    P7_R54_AHR_POST_PMN23_DMH_RESULT_MEMO_REF,
    "emlis_ai_p7_r54_ahr_post_mn11_actual_local_only_human_review_operation_20260630.py",
)
P7_R54_AHR_POST_PMN23_DMH_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "P8 question design",
    "P8 question implementation",
    "P6 start",
    "R52 actual execution",
    "P5 final",
    "P7 complete",
    "release decision",
)
P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "pmn_op23_contract_fixture_complete_predicate_is_not_real_operation_actual_evidence",
    "pmn_op23_acceptance_is_not_actual_operation_receipt",
    "pmn_op23_next_required_step_is_not_body_full_packet_generated",
    "target_tests_green_is_not_actual_human_review_complete",
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
P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "actual_body_full_packet_generation",
    "actual_local_human_review_execution",
    "actual_operation_receipt_from_real_operation",
    "actual_sanitized_review_result_rows_from_real_operation",
    "actual_rating_rows_from_real_operation",
    "actual_question_need_observation_rows_from_real_operation",
    "actual_disposal_purge_execution",
    "actual_review_evidence_complete_from_real_review",
    "postcr22_ex07_ex18_reentry_executed_here",
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

P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
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
    "actual_body_full_packet_generation_run_here",
    "actual_body_full_packet_generated_here",
    "body_full_packet_generation_run_here",
    "body_full_packet_exported",
    "actual_24_case_local_only_human_review_run_here",
    "actual_human_review_run_here",
    "actual_human_review_complete",
    "actual_operation_receipt_from_real_operation_received",
    "actual_operation_receipt_created_here",
    "actual_selection_rows_created_here",
    "actual_sanitized_review_result_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_purge_executed_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete_from_real_review",
    "actual_review_evidence_complete_from_real_operation_claimed_here",
    "postcr22_ex07_ex18_reentry_executed_here",
    "manual_decision_auto_executes_downstream",
    "r52_reintake_execution_requested_here",
    "r52_reintake_execution_started_here",
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
    "full_backend_suite_green_claimed_here",
    "rn_contract_green",
    "rn_contract_green_confirmed",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_PMN23_DMH_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_PMN23_DMH_NO_TOUCH_CONTRACT_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS: Final[frozenset[str]] = (
    pmn.P7_R54_AHR_POST_MN11_FORBIDDEN_PAYLOAD_KEY_REFS
)

P7_R54_AHR_POST_PMN23_DMH_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP00_STEP_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF,
    "R54-AHR-PostPMN23-DMH-OP04_24_case_manifest_packet_request_boundary",
    "R54-AHR-PostPMN23-DMH-OP05_body_full_packet_generation_receipt_intake_boundary",
    "R54-AHR-PostPMN23-DMH-OP06_packet_completeness_export_denylist_scan_receipt",
    "R54-AHR-PostPMN23-DMH-OP07_reviewer_person_selection_only_form_finalization",
    "R54-AHR-PostPMN23-DMH-OP08_actual_review_operation_state_machine_pause_abort_lifecycle",
    "R54-AHR-PostPMN23-DMH-OP09_actual_operation_receipt_intake",
    "R54-AHR-PostPMN23-DMH-OP10_sanitized_review_result_rows_intake_provenance_guard",
    "R54-AHR-PostPMN23-DMH-OP11_rating_rows_normalization_threshold_summary",
    "R54-AHR-PostPMN23-DMH-OP12_question_need_observation_rows_normalization",
    "R54-AHR-PostPMN23-DMH-OP13_rating_question_consistency_blocker_separation",
    "R54-AHR-PostPMN23-DMH-OP14_disposal_purge_receipt_intake",
    "R54-AHR-PostPMN23-DMH-OP15_final_no_body_no_question_no_path_no_hash_no_touch_validation",
    "R54-AHR-PostPMN23-DMH-OP16_actual_review_evidence_complete_predicate",
    "R54-AHR-PostPMN23-DMH-OP17_postcr22_ex07_ex18_actual_evidence_reentry_envelope",
    "R54-AHR-PostPMN23-DMH-OP18_result_memo_downstream_manual_decision_hold_finalizer",
)
P7_R54_AHR_POST_PMN23_DMH_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:1]
P7_R54_AHR_POST_PMN23_DMH_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[1:]
P7_R54_AHR_POST_PMN23_DMH_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:2]
P7_R54_AHR_POST_PMN23_DMH_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[2:]
P7_R54_AHR_POST_PMN23_DMH_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:3]
P7_R54_AHR_POST_PMN23_DMH_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[3:]
P7_R54_AHR_POST_PMN23_DMH_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:4]
P7_R54_AHR_POST_PMN23_DMH_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[4:]

P7_R54_AHR_POST_PMN23_DMH_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "post_pmn23_dmh_scope_confirmed",
    "actual_local_only_human_review_evidence_intake_entry",
    "no_touch_boundary_confirmed",
    "no_promotion_boundary_confirmed",
    "dmh_op00_does_not_intake_pmn_op23_hold",
    "dmh_op00_does_not_generate_body_full_packet",
    "dmh_op00_does_not_run_actual_human_review",
    "dmh_op00_does_not_create_operation_receipt_or_rows_or_disposal",
    "pmn_op23_acceptance_not_promoted_to_actual_review_evidence_complete",
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
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_PMN23_DMH_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "dmh_op01_status_ref",
    "dmh_op01_allowed_status_refs",
    "dmh_op01_ready",
    "dmh_op01_blocker_refs",
    "dmh_op01_blocker_ref_count",
    "dmh_op01_reason_refs",
    "dmh_op01_reason_ref_count",
    "support_material_refs",
    "support_material_ref_count",
    "pmn_op23_result_memo_ref",
    "pmn_op23_result_memo_current_status_schema_version",
    "pmn_op23_result_memo_current_status_present",
    "pmn_op23_acceptance_finalizer_present",
    "pmn_op23_contract_valid",
    "pmn_op23_schema_version",
    "pmn_op23_operation_step_ref",
    "pmn_op23_acceptance_finalizer_status_ref",
    "pmn_op23_acceptance_finalizer_ready",
    "pmn_op23_next_required_step",
    "pmn_op23_next_required_step_confirmed",
    "pmn_op23_downstream_manual_decision_hold_confirmed",
    "pmn_op23_actual_review_basis_ref",
    "pmn_op23_actual_review_basis_ref_confirmed",
    "pmn_op23_current_actual_review_basis_remains_264_85_258_171",
    "pmn_op23_contract_fixture_complete_flag_observed",
    "pmn_op23_contract_fixture_complete_flag_not_promoted_to_actual_evidence",
    "actual_review_evidence_status_ref",
    "actual_review_evidence_status_missing_real_review_required_confirmed",
    "actual_review_evidence_complete_from_contract_fixture_path",
    "actual_review_evidence_complete_from_real_review_current_status",
    "actual_review_evidence_complete_from_real_review_false_confirmed",
    "actual_review_evidence_complete_from_real_operation_claimed",
    "actual_body_full_packet_generation_status_ref",
    "actual_local_human_review_execution_status_ref",
    "actual_operation_receipt_status_ref",
    "actual_sanitized_review_result_rows_status_ref",
    "actual_rating_rows_status_ref",
    "actual_question_need_observation_rows_status_ref",
    "actual_disposal_purge_status_ref",
    "pmn_op23_green_is_not_actual_human_review_complete",
    "pmn_op23_acceptance_is_not_actual_operation_receipt",
    "dmh_op01_does_not_treat_pmn_op23_green_as_real_review_complete",
    "dmh_op01_does_not_generate_body_full_packet",
    "dmh_op01_does_not_run_actual_human_review",
    "dmh_op01_does_not_create_operation_receipt_or_rows_or_disposal",
    "dmh_op01_does_not_start_p8_p6_r52_or_release",
    "dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision",
    "actual_local_only_human_review_evidence_intake_required_before_downstream_decision",
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
    "pmn_op23_forbidden_payload_key_paths",
    "pmn_op23_forbidden_payload_key_path_count",
    "pmn_op23_promotion_claim_refs",
    "pmn_op23_promotion_claim_ref_count",
    "result_memo_forbidden_payload_key_paths",
    "result_memo_forbidden_payload_key_path_count",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


P7_R54_AHR_POST_PMN23_DMH_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op01_dmh_ready",
    "op01_downstream_manual_decision_hold_confirmed",
    "op01_actual_review_evidence_missing_real_review_required_confirmed",
    "op01_passes_to_existing_pmn_postcr22_ex_reuse_decision",
    "dmh_op02_status_ref",
    "dmh_op02_allowed_status_refs",
    "dmh_op02_ready",
    "dmh_op02_blocker_refs",
    "dmh_op02_blocker_ref_count",
    "dmh_op02_reason_refs",
    "dmh_op02_reason_ref_count",
    "existing_pmn_helper_ref",
    "existing_pmn_helper_step_refs",
    "existing_pmn_helper_step_ref_count",
    "existing_pmn_helper_first_step_ref",
    "existing_pmn_helper_last_step_ref",
    "existing_pmn_helper_reuse_role_refs",
    "existing_pmn_helper_reuse_role_ref_count",
    "existing_pmn_helper_reuse_candidate",
    "existing_pmn_helper_responsibility_rechecked",
    "existing_postcr22_ex_helper_ref",
    "existing_postcr22_ex_reentry_step_refs",
    "existing_postcr22_ex_reentry_step_ref_count",
    "existing_postcr22_ex_reentry_first_step_ref",
    "existing_postcr22_ex_reentry_last_step_ref",
    "existing_postcr22_ex_reentry_role_refs",
    "existing_postcr22_ex_reentry_role_ref_count",
    "existing_postcr22_ex_reentry_candidate",
    "existing_postcr22_ex_reentry_candidate_only",
    "existing_postcr22_ex_reentry_executed_here",
    "existing_postcr22_ex_reentry_responsibility_rechecked",
    "new_giant_wrapper_required",
    "minimal_evidence_intake_bridge_allowed_if_needed",
    "existing_helpers_reused_without_modification",
    "dmh_op02_does_not_generate_body_full_packet",
    "dmh_op02_does_not_run_actual_human_review",
    "dmh_op02_does_not_create_operation_receipt_or_rows_or_disposal",
    "dmh_op02_does_not_start_p8_p6_r52_or_release",
    "dmh_op02_does_not_execute_postcr22_ex_reentry",
    "dmh_op02_does_not_treat_helper_fixture_as_actual_evidence",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op02_dmh_ready",
    "op02_existing_pmn_helper_reuse_candidate",
    "op02_existing_postcr22_ex_reentry_candidate",
    "op02_new_giant_wrapper_required",
    "dmh_op03_status_ref",
    "dmh_op03_allowed_status_refs",
    "dmh_op03_ready",
    "dmh_op03_blocker_refs",
    "dmh_op03_blocker_ref_count",
    "dmh_op03_reason_refs",
    "dmh_op03_reason_ref_count",
    "explicit_allow_receipt_schema_version",
    "explicit_allow_receipt_present",
    "explicit_allow_receipt_ref",
    "explicit_allow_receipt_forbidden_payload_key_paths",
    "explicit_allow_receipt_forbidden_payload_key_path_count",
    "explicit_allow_ref",
    "explicit_allow_ref_present",
    "allow_scope_ref",
    "allow_scope_ref_present",
    "review_session_id_present",
    "review_session_id_bodyfree_identifier",
    "review_session_id_has_local_path_shape",
    "review_session_id_has_question_or_body_text_shape",
    "local_only_review_session_envelope_status_ref",
    "local_only_review_session_envelope_ready",
    "review_session_state_ref",
    "allowed_review_session_state_refs",
    "allowed_review_session_state_ref_count",
    "allowed_ready_session_transition_refs",
    "allowed_ready_session_transition_ref_count",
    "forbidden_session_promotion_transition_refs",
    "forbidden_session_promotion_transition_ref_count",
    "local_review_root_ref",
    "local_review_root_ref_present",
    "local_review_root_ref_has_path_shape",
    "local_review_root_path_included",
    "actual_review_basis_ref",
    "actual_review_basis_ref_present",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "required_case_count",
    "local_only_required",
    "body_full_packet_generation_allowed_for_local_review_only",
    "body_full_packet_generation_allowed_by_explicit_allow_receipt",
    "body_full_packet_generation_request_allowed_next",
    "body_full_generation_blocked_until_24_case_manifest_boundary",
    "body_full_export_allowed",
    "body_free_summary_export_allowed",
    "retention_policy_ref",
    "retention_policy_ref_present",
    "disposal_policy_ref",
    "disposal_policy_ref_present",
    "export_denylist_policy_ref",
    "export_denylist_policy_ref_present",
    "no_path_hash_in_artifact_required",
    "purge_required_before_or_after_review",
    "purge_required_delete_target_refs",
    "purge_required_delete_target_ref_count",
    "explicit_allow_body_stored_here",
    "body_full_packet_generated_here",
    "body_full_packet_materialized_here",
    "dmh_op03_does_not_generate_body_full_packet",
    "dmh_op03_does_not_run_actual_human_review",
    "dmh_op03_does_not_create_operation_receipt_or_rows_or_disposal",
    "dmh_op03_does_not_start_p8_p6_r52_or_release",
    "dmh_op03_does_not_materialize_question_text",
    "dmh_op03_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _clean_ref(value: Any, *, default: str = "", max_length: int = 180) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any) -> str:
    return _clean_ref(
        value,
        default=P7_R54_AHR_POST_PMN23_DMH_DEFAULT_REVIEW_SESSION_ID,
        max_length=220,
    )


def _ref_has_local_path_shape(value: Any) -> bool:
    text = str(value or "")
    return any(token in text for token in ("/", "\\", "~", "file://"))


def _ref_has_question_or_body_text_shape(value: Any) -> bool:
    text = str(value or "").lower()
    return any(token in text for token in ("question_text", "draft_question", "raw_input", "returned_body"))


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PMN23_DMH_BODY_FREE_MARKER_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PMN23_DMH_NO_TOUCH_CONTRACT_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS}


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
            if key_text in P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _pmn_op23_promotion_claim_refs(pmn_op23_material: Mapping[str, Any]) -> list[str]:
    claim_fields = (
        "actual_review_evidence_complete_from_real_operation_claimed_here",
        "actual_body_full_packet_generation_run_here",
        "actual_24_case_local_only_human_review_run_here",
        "actual_operation_receipt_created_here_by_helper",
        "actual_rows_created_here_by_helper",
        "actual_disposal_purge_executed_here",
        "manual_decision_auto_executes_downstream",
        "p5_final_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    )
    return [field for field in claim_fields if pmn_op23_material.get(field) is True]


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_PMN23_DMH_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_PMN23_DMH_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != operation_step_ref or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step ref changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or claim GitHub connection check")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    for field in P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        if data.get(field) is not False:
            raise ValueError(f"{source} required false flag changed: {field}")
    if any(value is not False for value in (data.get("public_contract") or {}).values()):
        raise ValueError(f"{source} public contract mutated")
    if any(value is not False for value in (data.get("post_pmn23_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract mutated")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free marker changed")
    if any(key in P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains forbidden top-level payload key")


def build_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build DMH-OP00 body-free scope / no-touch / no-promotion re-freeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP00_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze_20260701",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "chosen_stage_ref": P7_R54_AHR_POST_PMN23_DMH_CHOSEN_STAGE_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_STAGE_REFS),
        "post_pmn23_dmh_scope_confirmed": True,
        "actual_local_only_human_review_evidence_intake_entry": True,
        "no_touch_boundary_confirmed": True,
        "no_promotion_boundary_confirmed": True,
        "dmh_op00_does_not_intake_pmn_op23_hold": True,
        "dmh_op00_does_not_generate_body_full_packet": True,
        "dmh_op00_does_not_run_actual_human_review": True,
        "dmh_op00_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "pmn_op23_acceptance_not_promoted_to_actual_review_evidence_complete": True,
        "p8_question_design_out_of_scope": True,
        "p8_question_implementation_out_of_scope": True,
        "p6_start_out_of_scope": True,
        "r52_actual_execution_out_of_scope": True,
        "p5_finalization_out_of_scope": True,
        "p7_complete_out_of_scope": True,
        "release_decision_out_of_scope": True,
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen": True,
        "required_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_PMN23_DMH_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "support_material_refs": list(P7_R54_AHR_POST_PMN23_DMH_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_SUPPORT_MATERIAL_REFS),
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP00 body-free scope / no-touch / no-promotion re-freeze contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP00_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP00 scope / no-touch / no-promotion re-freeze",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_REFREEZE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP00_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP00 scope / no-touch / no-promotion re-freeze",
    )
    for key in (
        "post_pmn23_dmh_scope_confirmed",
        "actual_local_only_human_review_evidence_intake_entry",
        "no_touch_boundary_confirmed",
        "no_promotion_boundary_confirmed",
        "dmh_op00_does_not_intake_pmn_op23_hold",
        "dmh_op00_does_not_generate_body_full_packet",
        "dmh_op00_does_not_run_actual_human_review",
        "dmh_op00_does_not_create_operation_receipt_or_rows_or_disposal",
        "pmn_op23_acceptance_not_promoted_to_actual_review_evidence_complete",
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
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP00 required true boundary changed: {key}")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("local_received_zip_refs", "local_received_zip_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP00 {count_field} changed")
    if tuple(data.get("not_stage_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_STAGE_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 not-stage refs changed")
    if data.get("required_case_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 required case count changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 actual review basis allowed ref changed")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_PMN23_DMH_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 local zip refs changed")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 cannot treat local zip refs as actual review basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 cannot rewrite current actual review basis")
    if tuple(data.get("support_material_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 support material refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 not-claimed boundary must stay false")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP00 next required step changed")
    return True


def build_p7_r54_ahr_post_pmn23_dmh_pmn_op23_result_memo_current_status_envelope_bodyfree(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build the body-free PMN-OP23 result-memo current-status envelope used by DMH-OP01."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_PMN_OP23_RESULT_MEMO_CURRENT_STATUS_SCHEMA_VERSION,
        "result_memo_ref": P7_R54_AHR_POST_PMN23_DMH_RESULT_MEMO_REF,
        "review_session_id": session_id,
        "pmn_op23_result_memo_envelope_present": True,
        "actual_review_evidence_status_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_EVIDENCE_STATUS_REF,
        "actual_review_evidence_complete_from_contract_fixture_path": True,
        "actual_review_evidence_complete_from_real_review_current_status": False,
        "actual_review_evidence_complete_from_real_operation_claimed": False,
        "actual_body_full_packet_generation_status_ref": "not_run",
        "actual_local_human_review_execution_status_ref": "not_run",
        "actual_operation_receipt_status_ref": "not_received",
        "actual_sanitized_review_result_rows_status_ref": "not_received",
        "actual_rating_rows_status_ref": "not_received",
        "actual_question_need_observation_rows_status_ref": "not_received",
        "actual_disposal_purge_status_ref": "not_run",
        "body_free": True,
    }


def _result_memo_current_status_blockers(status: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(status, Mapping):
        return ["dmh_op01_pmn_op23_result_memo_current_status_missing"]
    blockers: list[str] = []
    if _scan_forbidden_payload_key_paths(status, path="pmn_op23_result_memo_current_status"):
        blockers.append("dmh_op01_pmn_op23_result_memo_forbidden_body_question_path_hash_key_detected")
    if status.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_PMN_OP23_RESULT_MEMO_CURRENT_STATUS_SCHEMA_VERSION:
        blockers.append("dmh_op01_pmn_op23_result_memo_current_status_schema_version_mismatch")
    if status.get("pmn_op23_result_memo_envelope_present") is not True:
        blockers.append("dmh_op01_pmn_op23_result_memo_envelope_missing")
    if status.get("actual_review_evidence_status_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_EVIDENCE_STATUS_REF:
        blockers.append("dmh_op01_actual_review_evidence_status_not_missing_real_review_required")
    if status.get("actual_review_evidence_complete_from_real_review_current_status") is not False:
        blockers.append("dmh_op01_actual_review_evidence_complete_from_real_review_current_status_not_false")
    if status.get("actual_review_evidence_complete_from_real_operation_claimed") is not False:
        blockers.append("dmh_op01_actual_review_evidence_complete_from_real_operation_claimed")
    expected_statuses = {
        "actual_body_full_packet_generation_status_ref": "not_run",
        "actual_local_human_review_execution_status_ref": "not_run",
        "actual_operation_receipt_status_ref": "not_received",
        "actual_sanitized_review_result_rows_status_ref": "not_received",
        "actual_rating_rows_status_ref": "not_received",
        "actual_question_need_observation_rows_status_ref": "not_received",
        "actual_disposal_purge_status_ref": "not_run",
    }
    for key, expected in expected_statuses.items():
        if status.get(key) != expected:
            blockers.append(f"dmh_op01_{key}_mismatch")
    return list(dict.fromkeys(blockers))


def _dmh_op01_blockers(
    op00: Mapping[str, Any] | None,
    pmn_op23_acceptance_fail_closed_finalizer: Mapping[str, Any] | None,
    pmn_op23_result_memo_current_status: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze_contract(op00 or {})
    except ValueError:
        blockers.append("dmh_op01_op00_scope_no_touch_no_promotion_refreeze_invalid")

    if not isinstance(pmn_op23_acceptance_fail_closed_finalizer, Mapping):
        blockers.append("dmh_op01_pmn_op23_acceptance_finalizer_missing")
    else:
        if _scan_forbidden_payload_key_paths(
            pmn_op23_acceptance_fail_closed_finalizer,
            path="pmn_op23_acceptance_fail_closed_finalizer",
        ):
            blockers.append("dmh_op01_pmn_op23_forbidden_body_question_path_hash_key_detected")
        try:
            pmn.assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(
                pmn_op23_acceptance_fail_closed_finalizer
            )
        except ValueError:
            blockers.append("dmh_op01_pmn_op23_acceptance_finalizer_contract_invalid")
        if pmn_op23_acceptance_fail_closed_finalizer.get("acceptance_finalizer_ready") is not True:
            blockers.append("dmh_op01_pmn_op23_acceptance_finalizer_not_ready")
        if pmn_op23_acceptance_fail_closed_finalizer.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF:
            blockers.append("dmh_op01_pmn_op23_next_required_step_mismatch")
        if pmn_op23_acceptance_fail_closed_finalizer.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
            blockers.append("dmh_op01_pmn_op23_actual_review_basis_ref_mismatch")
        if pmn_op23_acceptance_fail_closed_finalizer.get("current_actual_review_basis_remains_264_85_258_171") is not True:
            blockers.append("dmh_op01_pmn_op23_current_actual_review_basis_not_preserved")
        promotion_claim_refs = _pmn_op23_promotion_claim_refs(pmn_op23_acceptance_fail_closed_finalizer)
        if promotion_claim_refs:
            blockers.append("dmh_op01_pmn_op23_promotion_or_real_operation_claim_detected")

    blockers.extend(_result_memo_current_status_blockers(pmn_op23_result_memo_current_status))
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake(
    *,
    scope_no_touch_no_promotion_refreeze: Mapping[str, Any] | None = None,
    pmn_op23_acceptance_fail_closed_finalizer: Mapping[str, Any] | None = None,
    pmn_op23_result_memo_current_status: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP01 body-free PMN-OP23 downstream manual decision hold intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op00 = scope_no_touch_no_promotion_refreeze
    if op00 is None:
        op00 = build_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze(
            review_session_id=session_id
        )
    blockers = _dmh_op01_blockers(op00, pmn_op23_acceptance_fail_closed_finalizer, pmn_op23_result_memo_current_status)
    ready = not blockers
    op23 = pmn_op23_acceptance_fail_closed_finalizer if isinstance(pmn_op23_acceptance_fail_closed_finalizer, Mapping) else {}
    status = pmn_op23_result_memo_current_status if isinstance(pmn_op23_result_memo_current_status, Mapping) else {}
    op23_forbidden_paths = _scan_forbidden_payload_key_paths(op23, path="pmn_op23_acceptance_fail_closed_finalizer")
    result_memo_forbidden_paths = _scan_forbidden_payload_key_paths(status, path="pmn_op23_result_memo_current_status")
    promotion_claim_refs = _pmn_op23_promotion_claim_refs(op23)
    op23_contract_valid = False
    if isinstance(pmn_op23_acceptance_fail_closed_finalizer, Mapping):
        try:
            op23_contract_valid = (
                pmn.assert_p7_r54_ahr_post_mn11_pmn_op23_acceptance_fail_closed_finalizer_contract(
                    pmn_op23_acceptance_fail_closed_finalizer
                )
                is True
            )
        except ValueError:
            op23_contract_valid = False

    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP01_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_20260701",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version") if isinstance(op00, Mapping) else "", default="op00_schema_missing", max_length=220),
        "op00_material_ref": _clean_ref(op00.get("material_id") if isinstance(op00, Mapping) else "", default="op00_material_missing", max_length=220),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step") if isinstance(op00, Mapping) else "", default="op00_next_required_step_missing", max_length=220),
        "op00_scope_confirmed": bool(isinstance(op00, Mapping) and op00.get("post_pmn23_dmh_scope_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(isinstance(op00, Mapping) and op00.get("no_promotion_boundary_confirmed") is True),
        "dmh_op01_status_ref": (
            P7_R54_AHR_POST_PMN23_DMH_OP01_READY_STATUS_REF
            if ready
            else P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_STATUS_REF
        ),
        "dmh_op01_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP01_ALLOWED_STATUS_REFS),
        "dmh_op01_ready": ready,
        "dmh_op01_blocker_refs": blockers,
        "dmh_op01_blocker_ref_count": len(blockers),
        "dmh_op01_reason_refs": ["dmh_op01_pmn_op23_hold_and_real_evidence_missing_status_confirmed_bodyfree"] if ready else [],
        "dmh_op01_reason_ref_count": 1 if ready else 0,
        "support_material_refs": list(P7_R54_AHR_POST_PMN23_DMH_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_SUPPORT_MATERIAL_REFS),
        "pmn_op23_result_memo_ref": P7_R54_AHR_POST_PMN23_DMH_RESULT_MEMO_REF,
        "pmn_op23_result_memo_current_status_schema_version": _clean_ref(status.get("schema_version"), max_length=220),
        "pmn_op23_result_memo_current_status_present": bool(isinstance(pmn_op23_result_memo_current_status, Mapping)),
        "pmn_op23_acceptance_finalizer_present": bool(isinstance(pmn_op23_acceptance_fail_closed_finalizer, Mapping)),
        "pmn_op23_contract_valid": op23_contract_valid,
        "pmn_op23_schema_version": _clean_ref(op23.get("schema_version"), max_length=220),
        "pmn_op23_operation_step_ref": _clean_ref(op23.get("operation_step_ref"), max_length=220),
        "pmn_op23_acceptance_finalizer_status_ref": _clean_ref(op23.get("acceptance_finalizer_status_ref"), max_length=220),
        "pmn_op23_acceptance_finalizer_ready": op23.get("acceptance_finalizer_ready") is True,
        "pmn_op23_next_required_step": _clean_ref(op23.get("next_required_step"), max_length=220),
        "pmn_op23_next_required_step_confirmed": op23.get("next_required_step") == P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF,
        "pmn_op23_downstream_manual_decision_hold_confirmed": op23.get("next_required_step") == P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF,
        "pmn_op23_actual_review_basis_ref": _clean_ref(op23.get("actual_review_basis_ref"), max_length=180),
        "pmn_op23_actual_review_basis_ref_confirmed": op23.get("actual_review_basis_ref") == P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "pmn_op23_current_actual_review_basis_remains_264_85_258_171": op23.get("current_actual_review_basis_remains_264_85_258_171") is True,
        "pmn_op23_contract_fixture_complete_flag_observed": op23.get("actual_review_evidence_complete_from_real_review") is True,
        "pmn_op23_contract_fixture_complete_flag_not_promoted_to_actual_evidence": True,
        "actual_review_evidence_status_ref": _clean_ref(status.get("actual_review_evidence_status_ref"), max_length=180),
        "actual_review_evidence_status_missing_real_review_required_confirmed": status.get("actual_review_evidence_status_ref") == P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_EVIDENCE_STATUS_REF,
        "actual_review_evidence_complete_from_contract_fixture_path": status.get("actual_review_evidence_complete_from_contract_fixture_path") is True,
        "actual_review_evidence_complete_from_real_review_current_status": status.get("actual_review_evidence_complete_from_real_review_current_status") is True,
        "actual_review_evidence_complete_from_real_review_false_confirmed": status.get("actual_review_evidence_complete_from_real_review_current_status") is False,
        "actual_review_evidence_complete_from_real_operation_claimed": status.get("actual_review_evidence_complete_from_real_operation_claimed") is True,
        "actual_body_full_packet_generation_status_ref": _clean_ref(status.get("actual_body_full_packet_generation_status_ref"), max_length=120),
        "actual_local_human_review_execution_status_ref": _clean_ref(status.get("actual_local_human_review_execution_status_ref"), max_length=120),
        "actual_operation_receipt_status_ref": _clean_ref(status.get("actual_operation_receipt_status_ref"), max_length=120),
        "actual_sanitized_review_result_rows_status_ref": _clean_ref(status.get("actual_sanitized_review_result_rows_status_ref"), max_length=120),
        "actual_rating_rows_status_ref": _clean_ref(status.get("actual_rating_rows_status_ref"), max_length=120),
        "actual_question_need_observation_rows_status_ref": _clean_ref(status.get("actual_question_need_observation_rows_status_ref"), max_length=120),
        "actual_disposal_purge_status_ref": _clean_ref(status.get("actual_disposal_purge_status_ref"), max_length=120),
        "pmn_op23_green_is_not_actual_human_review_complete": True,
        "pmn_op23_acceptance_is_not_actual_operation_receipt": True,
        "dmh_op01_does_not_treat_pmn_op23_green_as_real_review_complete": True,
        "dmh_op01_does_not_generate_body_full_packet": True,
        "dmh_op01_does_not_run_actual_human_review": True,
        "dmh_op01_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "dmh_op01_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision": ready,
        "actual_local_only_human_review_evidence_intake_required_before_downstream_decision": ready,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "basis_rewrite_required_here": False,
        "basis_rewritten_here": False,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_PMN23_DMH_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_refs_are_actual_review_basis": False,
        "local_received_zip_refs_used_to_rewrite_current_actual_review_basis": False,
        "outer_received_zip_label_difference_recorded_bodyfree": True,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "pmn_op23_forbidden_payload_key_paths": [_clean_ref(path, max_length=220) for path in op23_forbidden_paths],
        "pmn_op23_forbidden_payload_key_path_count": len(op23_forbidden_paths),
        "pmn_op23_promotion_claim_refs": [_clean_ref(ref, max_length=180) for ref in promotion_claim_refs],
        "pmn_op23_promotion_claim_ref_count": len(promotion_claim_refs),
        "result_memo_forbidden_payload_key_paths": [_clean_ref(path, max_length=220) for path in result_memo_forbidden_paths],
        "result_memo_forbidden_payload_key_path_count": len(result_memo_forbidden_paths),
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP01_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP01_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP01 body-free PMN-OP23 downstream manual decision hold intake contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP01_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP01 PMN-OP23 downstream manual decision hold intake",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP01_PMN_OP23_DOWNSTREAM_MANUAL_DECISION_HOLD_INTAKE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP01 PMN-OP23 downstream manual decision hold intake",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP00_SCOPE_NO_TOUCH_NO_PROMOTION_REFREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 OP00 schema version changed")
    if data.get("op00_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 OP00 next required step changed")
    for key in (
        "op00_scope_confirmed",
        "op00_no_touch_boundary_confirmed",
        "op00_no_promotion_boundary_confirmed",
        "pmn_op23_contract_fixture_complete_flag_not_promoted_to_actual_evidence",
        "pmn_op23_green_is_not_actual_human_review_complete",
        "pmn_op23_acceptance_is_not_actual_operation_receipt",
        "dmh_op01_does_not_treat_pmn_op23_green_as_real_review_complete",
        "dmh_op01_does_not_generate_body_full_packet",
        "dmh_op01_does_not_run_actual_human_review",
        "dmh_op01_does_not_create_operation_receipt_or_rows_or_disposal",
        "dmh_op01_does_not_start_p8_p6_r52_or_release",
        "outer_received_zip_label_difference_recorded_bodyfree",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP01 required true boundary changed: {key}")
    if tuple(data.get("dmh_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 allowed status refs changed")
    for field, count_field in (
        ("support_material_refs", "support_material_ref_count"),
        ("dmh_op01_blocker_refs", "dmh_op01_blocker_ref_count"),
        ("dmh_op01_reason_refs", "dmh_op01_reason_ref_count"),
        ("pmn_op23_forbidden_payload_key_paths", "pmn_op23_forbidden_payload_key_path_count"),
        ("pmn_op23_promotion_claim_refs", "pmn_op23_promotion_claim_ref_count"),
        ("result_memo_forbidden_payload_key_paths", "result_memo_forbidden_payload_key_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP01 {count_field} changed")
    if tuple(data.get("support_material_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_SUPPORT_MATERIAL_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 support material refs changed")
    if data.get("pmn_op23_result_memo_ref") != P7_R54_AHR_POST_PMN23_DMH_RESULT_MEMO_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 result memo ref changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 actual review basis allowed changed")
    if data.get("basis_rewrite_required_here") is not False or data.get("basis_rewritten_here") is not False:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 cannot rewrite basis")
    if data.get("local_received_zip_refs") != P7_R54_AHR_POST_PMN23_DMH_LOCAL_RECEIVED_ZIP_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 local zip refs changed")
    if data.get("local_received_zip_refs_are_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 cannot treat local zip refs as actual review basis")
    if data.get("local_received_zip_refs_used_to_rewrite_current_actual_review_basis") is not False:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 cannot rewrite current actual review basis")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 not-claimed boundary must stay false")

    ready = data.get("dmh_op01_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP01_READY_STATUS_REF
    if data.get("dmh_op01_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 ready flag changed")
    if ready:
        if data.get("dmh_op01_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 ready material cannot carry blockers")
        if data.get("dmh_op01_reason_refs") != ["dmh_op01_pmn_op23_hold_and_real_evidence_missing_status_confirmed_bodyfree"]:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 ready reason changed")
        for key in (
            "pmn_op23_result_memo_current_status_present",
            "pmn_op23_acceptance_finalizer_present",
            "pmn_op23_contract_valid",
            "pmn_op23_acceptance_finalizer_ready",
            "pmn_op23_next_required_step_confirmed",
            "pmn_op23_downstream_manual_decision_hold_confirmed",
            "pmn_op23_actual_review_basis_ref_confirmed",
            "pmn_op23_current_actual_review_basis_remains_264_85_258_171",
            "pmn_op23_contract_fixture_complete_flag_observed",
            "actual_review_evidence_status_missing_real_review_required_confirmed",
            "actual_review_evidence_complete_from_contract_fixture_path",
            "actual_review_evidence_complete_from_real_review_false_confirmed",
            "dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision",
            "actual_local_only_human_review_evidence_intake_required_before_downstream_decision",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP01 ready condition changed: {key}")
        if data.get("pmn_op23_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 PMN-OP23 next required step changed")
        if data.get("actual_review_evidence_status_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_EVIDENCE_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 actual evidence status changed")
        if data.get("actual_review_evidence_complete_from_real_review_current_status") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 cannot accept real-review completion")
        if data.get("actual_review_evidence_complete_from_real_operation_claimed") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 cannot accept real-operation completion claim")
        expected_statuses = {
            "actual_body_full_packet_generation_status_ref": "not_run",
            "actual_local_human_review_execution_status_ref": "not_run",
            "actual_operation_receipt_status_ref": "not_received",
            "actual_sanitized_review_result_rows_status_ref": "not_received",
            "actual_rating_rows_status_ref": "not_received",
            "actual_question_need_observation_rows_status_ref": "not_received",
            "actual_disposal_purge_status_ref": "not_run",
        }
        for key, expected in expected_statuses.items():
            if data.get(key) != expected:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP01 current real-operation status changed: {key}")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP01_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP01_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 next required step changed")
    else:
        if data.get("dmh_op01_status_ref") != P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 blocked status changed")
        if not data.get("dmh_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 blocked material must carry blockers")
        if data.get("dmh_op01_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 blocked material cannot carry ready reasons")
        if data.get("dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 blocked material cannot pass to OP02")
        if data.get("actual_local_only_human_review_evidence_intake_required_before_downstream_decision") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 blocked material cannot claim evidence intake readiness")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP00_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP01_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP01 blocked next step changed")
    return True


def _dmh_op02_blockers(op01: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op01, Mapping):
        blockers.append("dmh_op02_pmn_op23_downstream_manual_decision_hold_intake_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract(op01)
        except ValueError:
            blockers.append("dmh_op02_pmn_op23_downstream_manual_decision_hold_intake_contract_invalid")
        if op01.get("dmh_op01_ready") is not True:
            blockers.append("dmh_op02_pmn_op23_downstream_manual_decision_hold_intake_not_ready")
        if op01.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF:
            blockers.append("dmh_op02_op01_next_step_not_existing_pmn_postcr22_ex_reuse_decision")
        if op01.get("pmn_op23_downstream_manual_decision_hold_confirmed") is not True:
            blockers.append("dmh_op02_pmn_op23_downstream_manual_decision_hold_not_confirmed")
        if op01.get("actual_review_evidence_status_missing_real_review_required_confirmed") is not True:
            blockers.append("dmh_op02_actual_review_evidence_missing_real_review_required_not_confirmed")
        if op01.get("dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision") is not True:
            blockers.append("dmh_op02_op01_does_not_pass_to_reuse_decision")
    if len(pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS) != 24:
        blockers.append("dmh_op02_existing_pmn_helper_op00_op23_step_count_mismatch")
    if len(pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS) != 12:
        blockers.append("dmh_op02_existing_postcr22_ex07_ex18_step_count_mismatch")
    if not pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_ROLE_REFS:
        blockers.append("dmh_op02_existing_postcr22_ex_reentry_roles_missing")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision(
    *,
    pmn_op23_downstream_manual_decision_hold_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP02 body-free existing PMN / PostCR22 EX re-use decision material."""

    session_id = _safe_review_session_id(review_session_id)
    op01 = pmn_op23_downstream_manual_decision_hold_intake
    blockers = _dmh_op02_blockers(op01)
    ready = not blockers
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP02_EXISTING_PMN_POSTCR22_EX_REUSE_DECISION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_20260702",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01.get("schema_version") if isinstance(op01, Mapping) else "", default="op01_schema_missing", max_length=220),
        "op01_material_ref": _clean_ref(op01.get("material_id") if isinstance(op01, Mapping) else "", default="op01_material_missing", max_length=220),
        "op01_next_required_step": _clean_ref(op01.get("next_required_step") if isinstance(op01, Mapping) else "", default="op01_next_required_step_missing", max_length=220),
        "op01_dmh_ready": bool(isinstance(op01, Mapping) and op01.get("dmh_op01_ready") is True),
        "op01_downstream_manual_decision_hold_confirmed": bool(isinstance(op01, Mapping) and op01.get("pmn_op23_downstream_manual_decision_hold_confirmed") is True),
        "op01_actual_review_evidence_missing_real_review_required_confirmed": bool(isinstance(op01, Mapping) and op01.get("actual_review_evidence_status_missing_real_review_required_confirmed") is True),
        "op01_passes_to_existing_pmn_postcr22_ex_reuse_decision": bool(isinstance(op01, Mapping) and op01.get("dmh_op01_passes_to_existing_pmn_postcr22_ex_reuse_decision") is True),
        "dmh_op02_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP02_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_STATUS_REF,
        "dmh_op02_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP02_ALLOWED_STATUS_REFS),
        "dmh_op02_ready": ready,
        "dmh_op02_blocker_refs": blockers,
        "dmh_op02_blocker_ref_count": len(blockers),
        "dmh_op02_reason_refs": [
            "existing_post_mn11_pmn_helper_reuse_candidate_confirmed_bodyfree",
            "existing_postcr22_ex07_ex18_reentry_candidate_confirmed_bodyfree",
            "new_giant_wrapper_not_required_minimal_bridge_only",
            "postcr22_ex07_ex18_reentry_not_executed_here",
            "helper_fixture_not_promoted_to_actual_evidence",
        ] if ready else [],
        "dmh_op02_reason_ref_count": 5 if ready else 0,
        "existing_pmn_helper_ref": P7_R54_AHR_POST_PMN23_DMH_EXISTING_PMN_HELPER_REF,
        "existing_pmn_helper_step_refs": list(pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS),
        "existing_pmn_helper_step_ref_count": len(pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS),
        "existing_pmn_helper_first_step_ref": pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS[0],
        "existing_pmn_helper_last_step_ref": pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS[-1],
        "existing_pmn_helper_reuse_role_refs": list(P7_R54_AHR_POST_PMN23_DMH_EXISTING_PMN_REUSE_ROLE_REFS),
        "existing_pmn_helper_reuse_role_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_EXISTING_PMN_REUSE_ROLE_REFS),
        "existing_pmn_helper_reuse_candidate": ready,
        "existing_pmn_helper_responsibility_rechecked": ready,
        "existing_postcr22_ex_helper_ref": P7_R54_AHR_POST_PMN23_DMH_EXISTING_POSTCR22_EX_HELPER_REF,
        "existing_postcr22_ex_reentry_step_refs": list(pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS),
        "existing_postcr22_ex_reentry_step_ref_count": len(pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS),
        "existing_postcr22_ex_reentry_first_step_ref": pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[0],
        "existing_postcr22_ex_reentry_last_step_ref": pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS[-1],
        "existing_postcr22_ex_reentry_role_refs": list(P7_R54_AHR_POST_PMN23_DMH_EXISTING_POSTCR22_EX_REENTRY_ROLE_REFS),
        "existing_postcr22_ex_reentry_role_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_EXISTING_POSTCR22_EX_REENTRY_ROLE_REFS),
        "existing_postcr22_ex_reentry_candidate": ready,
        "existing_postcr22_ex_reentry_candidate_only": ready,
        "existing_postcr22_ex_reentry_executed_here": False,
        "existing_postcr22_ex_reentry_responsibility_rechecked": ready,
        "new_giant_wrapper_required": False,
        "minimal_evidence_intake_bridge_allowed_if_needed": ready,
        "existing_helpers_reused_without_modification": True,
        "dmh_op02_does_not_generate_body_full_packet": True,
        "dmh_op02_does_not_run_actual_human_review": True,
        "dmh_op02_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "dmh_op02_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op02_does_not_execute_postcr22_ex_reentry": True,
        "dmh_op02_does_not_treat_helper_fixture_as_actual_evidence": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP02_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP02_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP02 body-free existing PMN / PostCR22 EX re-use decision contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP02_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP02 existing PMN / PostCR22 EX re-use decision",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP02_EXISTING_PMN_POSTCR22_EX_REUSE_DECISION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP02 existing PMN / PostCR22 EX re-use decision",
    )
    if tuple(data.get("dmh_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 allowed status refs changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 actual review basis allowed changed")
    for key in (
        "existing_helpers_reused_without_modification",
        "dmh_op02_does_not_generate_body_full_packet",
        "dmh_op02_does_not_run_actual_human_review",
        "dmh_op02_does_not_create_operation_receipt_or_rows_or_disposal",
        "dmh_op02_does_not_start_p8_p6_r52_or_release",
        "dmh_op02_does_not_execute_postcr22_ex_reentry",
        "dmh_op02_does_not_treat_helper_fixture_as_actual_evidence",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP02 required true boundary changed: {key}")
    if data.get("new_giant_wrapper_required") is not False:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 must not require a new giant wrapper")
    if data.get("existing_postcr22_ex_reentry_executed_here") is not False:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 must not execute PostCR22 EX re-entry")
    for field, count_field in (
        ("dmh_op02_blocker_refs", "dmh_op02_blocker_ref_count"),
        ("dmh_op02_reason_refs", "dmh_op02_reason_ref_count"),
        ("existing_pmn_helper_step_refs", "existing_pmn_helper_step_ref_count"),
        ("existing_pmn_helper_reuse_role_refs", "existing_pmn_helper_reuse_role_ref_count"),
        ("existing_postcr22_ex_reentry_step_refs", "existing_postcr22_ex_reentry_step_ref_count"),
        ("existing_postcr22_ex_reentry_role_refs", "existing_postcr22_ex_reentry_role_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP02 {count_field} changed")
    if tuple(data.get("existing_pmn_helper_step_refs") or ()) != pmn.P7_R54_AHR_POST_MN11_PMN_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 existing PMN helper step refs changed")
    if tuple(data.get("existing_postcr22_ex_reentry_step_refs") or ()) != pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 existing PostCR22 EX re-entry refs changed")
    if tuple(data.get("existing_pmn_helper_reuse_role_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_EXISTING_PMN_REUSE_ROLE_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 existing PMN helper reuse roles changed")
    if tuple(data.get("existing_postcr22_ex_reentry_role_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_EXISTING_POSTCR22_EX_REENTRY_ROLE_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 existing PostCR22 EX re-entry roles changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 not-claimed boundary must stay false")

    ready = data.get("dmh_op02_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP02_READY_STATUS_REF
    if data.get("dmh_op02_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 ready flag changed")
    if ready:
        if data.get("dmh_op02_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 ready material cannot carry blockers")
        for key in (
            "op01_dmh_ready",
            "op01_downstream_manual_decision_hold_confirmed",
            "op01_actual_review_evidence_missing_real_review_required_confirmed",
            "op01_passes_to_existing_pmn_postcr22_ex_reuse_decision",
            "existing_pmn_helper_reuse_candidate",
            "existing_pmn_helper_responsibility_rechecked",
            "existing_postcr22_ex_reentry_candidate",
            "existing_postcr22_ex_reentry_candidate_only",
            "existing_postcr22_ex_reentry_responsibility_rechecked",
            "minimal_evidence_intake_bridge_allowed_if_needed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP02 ready condition changed: {key}")
        if data.get("op01_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 OP01 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP02_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP02_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 next required step changed")
    else:
        if data.get("dmh_op02_status_ref") != P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 blocked status changed")
        if not data.get("dmh_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 blocked material must carry blockers")
        for key in (
            "existing_pmn_helper_reuse_candidate",
            "existing_pmn_helper_responsibility_rechecked",
            "existing_postcr22_ex_reentry_candidate",
            "existing_postcr22_ex_reentry_candidate_only",
            "existing_postcr22_ex_reentry_responsibility_rechecked",
            "minimal_evidence_intake_bridge_allowed_if_needed",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP02 blocked candidate flag changed: {key}")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP01_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP02_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP02 blocked next step changed")
    return True


def build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_bodyfree(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build a body-free explicit-allow receipt fixture for DMH-OP03 validation."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_SCHEMA_VERSION,
        "explicit_allow_receipt_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_REF,
        "explicit_allow_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_REF,
        "allow_scope_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOW_SCOPE_REF,
        "review_session_id": session_id,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "required_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "local_only_required": True,
        "body_full_packet_generation_allowed_for_local_review_only": True,
        "body_full_export_allowed": False,
        "body_free_summary_export_allowed": True,
        "retention_policy_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_RETENTION_POLICY_REF,
        "disposal_policy_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_DISPOSAL_POLICY_REF,
        "export_denylist_policy_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_EXPORT_DENYLIST_POLICY_REF,
        "no_path_hash_in_artifact_required": True,
        "body_full_packet_generated_here": False,
        "body_free": True,
    }


def _dmh_op03_explicit_allow_receipt_blockers(
    receipt: Mapping[str, Any] | None, *, review_session_id: str
) -> list[str]:
    if not isinstance(receipt, Mapping):
        return ["dmh_op03_explicit_allow_receipt_missing"]
    blockers: list[str] = []
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="explicit_allow_receipt")
    if forbidden_paths:
        blockers.append("dmh_op03_explicit_allow_receipt_forbidden_body_question_path_hash_key_detected")
    if receipt.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_SCHEMA_VERSION:
        blockers.append("dmh_op03_explicit_allow_receipt_schema_version_mismatch")
    if not receipt.get("explicit_allow_ref"):
        blockers.append("dmh_op03_explicit_allow_ref_missing")
    if _ref_has_local_path_shape(receipt.get("explicit_allow_ref")):
        blockers.append("dmh_op03_explicit_allow_ref_has_local_path_shape")
    if _ref_has_question_or_body_text_shape(receipt.get("explicit_allow_ref")):
        blockers.append("dmh_op03_explicit_allow_ref_has_question_or_body_text_shape")
    if receipt.get("allow_scope_ref") != P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOW_SCOPE_REF:
        blockers.append("dmh_op03_allow_scope_ref_mismatch")
    if _safe_review_session_id(receipt.get("review_session_id")) != review_session_id:
        blockers.append("dmh_op03_review_session_id_mismatch")
    if receipt.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("dmh_op03_actual_review_basis_ref_mismatch")
    if receipt.get("required_case_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op03_required_case_count_mismatch")
    expected_bool_fields = {
        "local_only_required": True,
        "body_full_packet_generation_allowed_for_local_review_only": True,
        "body_full_export_allowed": False,
        "body_free_summary_export_allowed": True,
        "no_path_hash_in_artifact_required": True,
        "body_full_packet_generated_here": False,
        "body_free": True,
    }
    for key, expected in expected_bool_fields.items():
        if receipt.get(key) is not expected:
            blockers.append(f"dmh_op03_{key}_mismatch")
    if receipt.get("retention_policy_ref") != P7_R54_AHR_POST_PMN23_DMH_OP03_RETENTION_POLICY_REF:
        blockers.append("dmh_op03_retention_policy_ref_mismatch")
    if receipt.get("disposal_policy_ref") != P7_R54_AHR_POST_PMN23_DMH_OP03_DISPOSAL_POLICY_REF:
        blockers.append("dmh_op03_disposal_policy_ref_mismatch")
    if receipt.get("export_denylist_policy_ref") != P7_R54_AHR_POST_PMN23_DMH_OP03_EXPORT_DENYLIST_POLICY_REF:
        blockers.append("dmh_op03_export_denylist_policy_ref_mismatch")
    return list(dict.fromkeys(blockers))


def _dmh_op03_blockers(
    op02: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
    *,
    review_session_id: str,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op02, Mapping):
        blockers.append("dmh_op03_existing_pmn_postcr22_ex_reuse_decision_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_contract(op02)
        except ValueError:
            blockers.append("dmh_op03_existing_pmn_postcr22_ex_reuse_decision_contract_invalid")
        if op02.get("dmh_op02_ready") is not True:
            blockers.append("dmh_op03_existing_pmn_postcr22_ex_reuse_decision_not_ready")
        if op02.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF:
            blockers.append("dmh_op03_op02_next_step_not_explicit_allow_receipt")
        for field in (
            "existing_pmn_helper_reuse_candidate",
            "existing_postcr22_ex_reentry_candidate",
            "minimal_evidence_intake_bridge_allowed_if_needed",
        ):
            if op02.get(field) is not True:
                blockers.append(f"dmh_op03_op02_{field}_not_ready")
        if op02.get("new_giant_wrapper_required") is not False:
            blockers.append("dmh_op03_op02_new_giant_wrapper_required")
    if not review_session_id:
        blockers.append("dmh_op03_review_session_id_missing")
    if _ref_has_local_path_shape(review_session_id):
        blockers.append("dmh_op03_review_session_id_has_local_path_shape")
    if _ref_has_question_or_body_text_shape(review_session_id):
        blockers.append("dmh_op03_review_session_id_has_question_or_body_text_shape")
    blockers.extend(_dmh_op03_explicit_allow_receipt_blockers(receipt, review_session_id=review_session_id))
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope(
    *,
    existing_pmn_postcr22_ex_reuse_decision: Mapping[str, Any] | None = None,
    explicit_allow_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP03 body-free explicit allow receipt / local-only review session envelope."""

    session_id = _safe_review_session_id(
        review_session_id
        if review_session_id is not None
        else (
            existing_pmn_postcr22_ex_reuse_decision.get("review_session_id")
            if isinstance(existing_pmn_postcr22_ex_reuse_decision, Mapping)
            else None
        )
    )
    op02 = existing_pmn_postcr22_ex_reuse_decision
    receipt = explicit_allow_receipt
    blockers = _dmh_op03_blockers(op02, receipt, review_session_id=session_id)
    ready = not blockers
    receipt_map = receipt if isinstance(receipt, Mapping) else {}
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt_map, path="explicit_allow_receipt")
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_LOCAL_ONLY_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_20260702",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02.get("schema_version") if isinstance(op02, Mapping) else "", default="op02_schema_missing", max_length=220),
        "op02_material_ref": _clean_ref(op02.get("material_id") if isinstance(op02, Mapping) else "", default="op02_material_missing", max_length=220),
        "op02_next_required_step": _clean_ref(op02.get("next_required_step") if isinstance(op02, Mapping) else "", default="op02_next_required_step_missing", max_length=220),
        "op02_dmh_ready": bool(isinstance(op02, Mapping) and op02.get("dmh_op02_ready") is True),
        "op02_existing_pmn_helper_reuse_candidate": bool(isinstance(op02, Mapping) and op02.get("existing_pmn_helper_reuse_candidate") is True),
        "op02_existing_postcr22_ex_reentry_candidate": bool(isinstance(op02, Mapping) and op02.get("existing_postcr22_ex_reentry_candidate") is True),
        "op02_new_giant_wrapper_required": bool(isinstance(op02, Mapping) and op02.get("new_giant_wrapper_required") is True),
        "dmh_op03_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_STATUS_REF,
        "dmh_op03_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_STATUS_REFS),
        "dmh_op03_ready": ready,
        "dmh_op03_blocker_refs": blockers,
        "dmh_op03_blocker_ref_count": len(blockers),
        "dmh_op03_reason_refs": [
            "op02_existing_pmn_and_postcr22_ex_reuse_decision_ready_bodyfree",
            "explicit_allow_receipt_present_bodyfree",
            "local_only_review_session_envelope_accepted_bodyfree",
            "body_full_packet_generation_limited_to_later_local_review_boundary",
            "body_full_packet_not_generated_here",
            "p8_r52_p5_p6_p7_release_not_promoted_here",
        ] if ready else [],
        "dmh_op03_reason_ref_count": 6 if ready else 0,
        "explicit_allow_receipt_schema_version": _clean_ref(receipt_map.get("schema_version"), max_length=220),
        "explicit_allow_receipt_present": bool(isinstance(receipt, Mapping)),
        "explicit_allow_receipt_ref": _clean_ref(receipt_map.get("explicit_allow_receipt_ref"), default="explicit_allow_receipt_missing", max_length=220),
        "explicit_allow_receipt_forbidden_payload_key_paths": [_clean_ref(path, max_length=220) for path in forbidden_paths],
        "explicit_allow_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "explicit_allow_ref": _clean_ref(receipt_map.get("explicit_allow_ref"), default="explicit_allow_ref_missing", max_length=220),
        "explicit_allow_ref_present": bool(receipt_map.get("explicit_allow_ref")) and not _ref_has_local_path_shape(receipt_map.get("explicit_allow_ref")) and not _ref_has_question_or_body_text_shape(receipt_map.get("explicit_allow_ref")),
        "allow_scope_ref": _clean_ref(receipt_map.get("allow_scope_ref"), default="allow_scope_ref_missing", max_length=220),
        "allow_scope_ref_present": receipt_map.get("allow_scope_ref") == P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOW_SCOPE_REF,
        "review_session_id_present": bool(session_id),
        "review_session_id_bodyfree_identifier": bool(session_id) and not _ref_has_local_path_shape(session_id) and not _ref_has_question_or_body_text_shape(session_id),
        "review_session_id_has_local_path_shape": _ref_has_local_path_shape(session_id),
        "review_session_id_has_question_or_body_text_shape": _ref_has_question_or_body_text_shape(session_id),
        "local_only_review_session_envelope_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_STATUS_REF,
        "local_only_review_session_envelope_ready": ready,
        "review_session_state_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_ACCEPTED_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_REQUIRED_REF,
        "allowed_review_session_state_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "allowed_review_session_state_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_REVIEW_SESSION_STATE_REFS),
        "allowed_ready_session_transition_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_READY_SESSION_TRANSITION_REFS),
        "allowed_ready_session_transition_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_READY_SESSION_TRANSITION_REFS),
        "forbidden_session_promotion_transition_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP03_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS),
        "forbidden_session_promotion_transition_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP03_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS),
        "local_review_root_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_LOCAL_REVIEW_ROOT_REF,
        "local_review_root_ref_present": True,
        "local_review_root_ref_has_path_shape": _ref_has_local_path_shape(P7_R54_AHR_POST_PMN23_DMH_OP03_LOCAL_REVIEW_ROOT_REF),
        "local_review_root_path_included": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_ref_present": receipt_map.get("actual_review_basis_ref") == P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "required_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "local_only_required": receipt_map.get("local_only_required") is True,
        "body_full_packet_generation_allowed_for_local_review_only": ready,
        "body_full_packet_generation_allowed_by_explicit_allow_receipt": ready,
        "body_full_packet_generation_request_allowed_next": False,
        "body_full_generation_blocked_until_24_case_manifest_boundary": True,
        "body_full_export_allowed": False,
        "body_free_summary_export_allowed": receipt_map.get("body_free_summary_export_allowed") is True,
        "retention_policy_ref": _clean_ref(receipt_map.get("retention_policy_ref"), default="retention_policy_missing", max_length=220),
        "retention_policy_ref_present": receipt_map.get("retention_policy_ref") == P7_R54_AHR_POST_PMN23_DMH_OP03_RETENTION_POLICY_REF,
        "disposal_policy_ref": _clean_ref(receipt_map.get("disposal_policy_ref"), default="disposal_policy_missing", max_length=220),
        "disposal_policy_ref_present": receipt_map.get("disposal_policy_ref") == P7_R54_AHR_POST_PMN23_DMH_OP03_DISPOSAL_POLICY_REF,
        "export_denylist_policy_ref": _clean_ref(receipt_map.get("export_denylist_policy_ref"), default="export_denylist_policy_missing", max_length=220),
        "export_denylist_policy_ref_present": receipt_map.get("export_denylist_policy_ref") == P7_R54_AHR_POST_PMN23_DMH_OP03_EXPORT_DENYLIST_POLICY_REF,
        "no_path_hash_in_artifact_required": receipt_map.get("no_path_hash_in_artifact_required") is True,
        "purge_required_before_or_after_review": True,
        "purge_required_delete_target_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_DELETE_TARGET_REFS),
        "purge_required_delete_target_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_DELETE_TARGET_REFS),
        "explicit_allow_body_stored_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "dmh_op03_does_not_generate_body_full_packet": True,
        "dmh_op03_does_not_run_actual_human_review": True,
        "dmh_op03_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "dmh_op03_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op03_does_not_materialize_question_text": True,
        "dmh_op03_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP03_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP03_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[4] if ready else P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP03 body-free explicit allow receipt / local-only session envelope contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP03 explicit allow receipt / local-only review session envelope",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_LOCAL_ONLY_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP03 explicit allow receipt / local-only review session envelope",
    )
    if tuple(data.get("dmh_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 allowed status refs changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 actual review basis allowed changed")
    for key in (
        "review_session_id_present",
        "review_session_id_bodyfree_identifier",
        "local_review_root_ref_present",
        "current_actual_review_basis_remains_264_85_258_171",
        "body_full_generation_blocked_until_24_case_manifest_boundary",
        "purge_required_before_or_after_review",
        "dmh_op03_does_not_generate_body_full_packet",
        "dmh_op03_does_not_run_actual_human_review",
        "dmh_op03_does_not_create_operation_receipt_or_rows_or_disposal",
        "dmh_op03_does_not_start_p8_p6_r52_or_release",
        "dmh_op03_does_not_materialize_question_text",
        "dmh_op03_does_not_execute_postcr22_ex_reentry",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP03 required true boundary changed: {key}")
    for key in (
        "op02_new_giant_wrapper_required",
        "review_session_id_has_local_path_shape",
        "review_session_id_has_question_or_body_text_shape",
        "local_review_root_ref_has_path_shape",
        "local_review_root_path_included",
        "body_full_packet_generation_request_allowed_next",
        "body_full_export_allowed",
        "explicit_allow_body_stored_here",
        "body_full_packet_generated_here",
        "body_full_packet_materialized_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP03 required false boundary promoted: {key}")
    for field, count_field in (
        ("dmh_op03_blocker_refs", "dmh_op03_blocker_ref_count"),
        ("dmh_op03_reason_refs", "dmh_op03_reason_ref_count"),
        ("explicit_allow_receipt_forbidden_payload_key_paths", "explicit_allow_receipt_forbidden_payload_key_path_count"),
        ("allowed_review_session_state_refs", "allowed_review_session_state_ref_count"),
        ("allowed_ready_session_transition_refs", "allowed_ready_session_transition_ref_count"),
        ("forbidden_session_promotion_transition_refs", "forbidden_session_promotion_transition_ref_count"),
        ("purge_required_delete_target_refs", "purge_required_delete_target_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP03 {count_field} changed")
    if tuple(data.get("allowed_review_session_state_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_REVIEW_SESSION_STATE_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 allowed review session states changed")
    if tuple(data.get("allowed_ready_session_transition_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOWED_READY_SESSION_TRANSITION_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 allowed ready session transitions changed")
    if tuple(data.get("forbidden_session_promotion_transition_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_FORBIDDEN_SESSION_PROMOTION_TRANSITION_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 forbidden session transitions changed")
    if tuple(data.get("purge_required_delete_target_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 purge target refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 not-claimed boundary must stay false")

    ready = data.get("dmh_op03_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP03_READY_STATUS_REF
    if data.get("dmh_op03_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 ready flag changed")
    if data.get("local_only_review_session_envelope_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 envelope ready flag changed")
    if ready:
        if data.get("dmh_op03_blocker_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 ready material cannot carry blockers")
        for key in (
            "op02_dmh_ready",
            "op02_existing_pmn_helper_reuse_candidate",
            "op02_existing_postcr22_ex_reentry_candidate",
            "explicit_allow_receipt_present",
            "explicit_allow_ref_present",
            "allow_scope_ref_present",
            "actual_review_basis_ref_present",
            "local_only_required",
            "body_full_packet_generation_allowed_for_local_review_only",
            "body_full_packet_generation_allowed_by_explicit_allow_receipt",
            "body_free_summary_export_allowed",
            "retention_policy_ref_present",
            "disposal_policy_ref_present",
            "export_denylist_policy_ref_present",
            "no_path_hash_in_artifact_required",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP03 ready condition changed: {key}")
        if data.get("explicit_allow_receipt_schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_RECEIPT_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 explicit allow receipt schema changed")
        if data.get("allow_scope_ref") != P7_R54_AHR_POST_PMN23_DMH_OP03_ALLOW_SCOPE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 allow scope changed")
        if data.get("review_session_state_ref") != P7_R54_AHR_POST_PMN23_DMH_OP03_REVIEW_SESSION_STATE_ACCEPTED_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 review session state changed")
        if data.get("op02_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 OP02 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[4]:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 next required step changed")
    else:
        if data.get("dmh_op03_status_ref") != P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 blocked status changed")
        if not data.get("dmh_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 blocked material must carry blockers")
        if data.get("body_full_packet_generation_allowed_for_local_review_only") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 blocked material cannot allow packet generation")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP02_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP03_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP03 blocked next step changed")
    return True


build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_scope_no_touch_no_promotion_refreeze_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_scope_no_touch_no_promotion_refreeze_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op00_scope_no_touch_no_promotion_refreeze_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_intake_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_intake_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op01_pmn_op23_downstream_manual_decision_hold_intake_contract
)

build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_existing_pmn_postcr22_ex_reuse_decision_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_existing_pmn_postcr22_ex_reuse_decision_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op02_existing_pmn_postcr22_ex_reuse_decision_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_explicit_allow_receipt_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_explicit_allow_receipt_local_only_review_session_envelope_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_explicit_allow_receipt_local_only_review_session_envelope_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract
)


# DMH-OP04 / DMH-OP05: body-free manifest, packet request, and packet-generation receipt intake boundary.
# These helpers remain internal contract material.  They do not generate a body-full packet,
# run actual human review, create actual review rows, execute purge, start P8, run R52,
# complete P7, or allow release.
P7_R54_AHR_POST_PMN23_DMH_OP04_24_CASE_MANIFEST_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op04_24_case_manifest_packet_request_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_BODY_FULL_PACKET_GENERATION_RECEIPT_INTAKE_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op05_body_full_packet_generation_receipt_intake_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op05_packet_generation_receipt.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_OP04_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[4]
P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[5]
P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[6]
P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op04_24_case_manifest_packet_request_boundary_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op05_body_full_packet_generation_receipt_intake_boundary_or_stop"
)

P7_R54_AHR_POST_PMN23_DMH_OP04_READY_STATUS_REF: Final = (
    "DMH_OP04_24_CASE_MANIFEST_PACKET_REQUEST_BOUNDARY_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_STATUS_REF: Final = (
    "DMH_OP04_24_CASE_MANIFEST_PACKET_REQUEST_BOUNDARY_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP04_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP05_READY_STATUS_REF: Final = (
    "DMH_OP05_BODY_FULL_PACKET_GENERATION_RECEIPT_INTAKE_BOUNDARY_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_STATUS_REF: Final = (
    "DMH_OP05_BODY_FULL_PACKET_GENERATION_RECEIPT_INTAKE_BOUNDARY_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP05_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_STATUS_REF,
)

P7_R54_AHR_POST_PMN23_DMH_OP04_CASE_MANIFEST_REF: Final = (
    "post_pmn23_dmh_op04_24_case_manifest_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF: Final = (
    "post_pmn23_dmh_op04_body_full_packet_generation_request_ref_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP04_LOCAL_OPERATION_REF: Final = (
    "post_pmn23_dmh_local_only_body_full_packet_generation_operation_boundary_bodyfree"
)
P7_R54_AHR_POST_PMN23_DMH_OP04_REVIEWER_IDENTIFIER_POLICY_REF: Final = (
    "reviewer_receives_blind_case_id_only_controller_keeps_case_and_packet_refs_bodyfree"
)
P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION: Final[dict[str, int]] = dict(
    pmn.P7_R54_AHR_POST_MN11_24_CASE_MANIFEST_DISTRIBUTION
)
P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_PMN23_DMH_OP04_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op03_explicit_allow_local_only_review_session_ready_bodyfree",
    "r54_p5_human_blind_qa_24_case_manifest_fixed_bodyfree",
    "case_blind_packet_refs_unique_and_separated_bodyfree",
    "packet_generation_request_payload_is_bodyfree_counts_booleans_and_refs_only",
    "body_full_packet_generation_still_not_run_in_op04",
)
P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_REF: Final = (
    "post_pmn23_dmh_op05_packet_generation_receipt_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_EXPECTED_ACTUAL_SOURCE_REF: Final = (
    "actual_local_body_full_packet_generation_receipt_bodyfree"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_CONTRACT_FIXTURE_SOURCE_KIND_REF: Final = (
    "contract_fixture_receipt_not_real_operation_evidence"
)
P7_R54_AHR_POST_PMN23_DMH_OP05_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op04_24_case_manifest_and_packet_request_boundary_ready_bodyfree",
    "packet_generation_receipt_present_bodyfree",
    "packet_count_and_packet_ref_count_are_24_bodyfree",
    "packet_materialized_local_only_confirmed_by_receipt_bodyfree",
    "receipt_contains_no_packet_content_path_hash_terminal_output_or_question_text",
    "op05_intakes_receipt_boundary_without_running_actual_review_or_promotion",
)
P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_PACKET_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
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
    "body_full_packet_exported_to_artifact",
    "local_absolute_path_included",
    "body_hash_stored",
    "terminal_output_body_included",
    "packet_content_included",
    "question_text_included",
    "draft_question_text_included",
    "receipt_source_kind_ref",
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:5]
P7_R54_AHR_POST_PMN23_DMH_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[5:]
P7_R54_AHR_POST_PMN23_DMH_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:6]
P7_R54_AHR_POST_PMN23_DMH_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[6:]

P7_R54_AHR_POST_PMN23_DMH_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op03_dmh_ready",
    "op03_explicit_allow_receipt_present",
    "op03_body_full_packet_generation_allowed_by_explicit_allow_receipt",
    "op03_local_only_review_session_envelope_ready",
    "dmh_op04_status_ref",
    "dmh_op04_allowed_status_refs",
    "dmh_op04_ready",
    "dmh_op04_blocker_refs",
    "dmh_op04_blocker_ref_count",
    "dmh_op04_reason_refs",
    "dmh_op04_reason_ref_count",
    "case_manifest_ref",
    "case_manifest_boundary_ready",
    "case_manifest_source_ref",
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
    "case_ref_ids",
    "blind_case_ids",
    "packet_ref_ids",
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
    "packet_generation_request_ref",
    "packet_generation_request_payload",
    "packet_generation_request_required_field_refs",
    "packet_generation_request_required_field_ref_count",
    "packet_generation_request_forbidden_payload_key_paths",
    "packet_generation_request_forbidden_payload_key_path_count",
    "local_operation_ref",
    "local_only_required",
    "must_not_export",
    "packet_completeness_scan_required",
    "export_denylist_scan_required",
    "purge_required",
    "packet_generation_request_ready",
    "packet_generation_request_bodyfree_only",
    "packet_generation_request_allowed_after_op04",
    "body_full_packet_generation_may_be_run_after_this_boundary_by_external_local_only_operation",
    "body_full_packet_generation_executed_here",
    "body_full_packet_generated_here",
    "body_full_packet_materialized_here",
    "body_full_packet_exported_to_artifact",
    "body_full_export_allowed",
    "local_absolute_path_included",
    "body_hash_stored",
    "terminal_output_body_included",
    "packet_content_included",
    "question_text_included",
    "draft_question_text_included",
    "actual_human_review_still_not_run",
    "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "dmh_op04_does_not_generate_body_full_packet",
    "dmh_op04_does_not_run_actual_human_review",
    "dmh_op04_does_not_create_operation_receipt_or_rows_or_disposal",
    "dmh_op04_does_not_start_p8_p6_r52_or_release",
    "dmh_op04_does_not_materialize_question_text",
    "dmh_op04_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op04_dmh_ready",
    "op04_packet_generation_request_ready",
    "op04_case_manifest_boundary_ready",
    "op04_packet_generation_request_ref",
    "dmh_op05_status_ref",
    "dmh_op05_allowed_status_refs",
    "dmh_op05_ready",
    "dmh_op05_blocker_refs",
    "dmh_op05_blocker_ref_count",
    "dmh_op05_reason_refs",
    "dmh_op05_reason_ref_count",
    "packet_generation_receipt_present",
    "packet_generation_receipt_schema_version",
    "packet_generation_receipt_ref",
    "packet_generation_receipt_forbidden_payload_key_paths",
    "packet_generation_receipt_forbidden_payload_key_path_count",
    "packet_generation_receipt_required_field_refs",
    "packet_generation_receipt_required_field_ref_count",
    "packet_generation_receipt_intake_boundary_ready",
    "packet_generation_receipt_actual_source_ref",
    "packet_generation_receipt_actual_source_ref_allowed",
    "packet_generation_receipt_source_kind_ref",
    "packet_generation_receipt_source_kind_is_contract_fixture_not_real_evidence",
    "packet_generation_request_ref",
    "packet_generation_request_ref_confirmed",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "actual_review_basis_ref_confirmed",
    "current_actual_review_basis_remains_264_85_258_171",
    "packet_materialized_local_only",
    "packet_count",
    "packet_ref_id_count",
    "packet_ref_ids",
    "packet_ref_ids_unique",
    "expected_packet_count",
    "body_full_exported",
    "body_full_packet_exported_to_artifact",
    "local_absolute_path_included",
    "body_hash_stored",
    "terminal_output_body_included",
    "packet_content_included",
    "question_text_included",
    "draft_question_text_included",
    "packet_generation_receipt_bodyfree_only",
    "packet_generation_receipt_content_export_absent",
    "packet_generation_receipt_path_hash_terminal_output_absent",
    "packet_generation_receipt_intaked_here",
    "packet_generation_receipt_from_real_operation_claimed_here",
    "packet_completeness_export_denylist_scan_required_next",
    "actual_human_review_still_not_run",
    "actual_operation_receipt_still_not_received",
    "actual_review_rows_still_not_created",
    "actual_disposal_purge_still_not_run",
    "actual_review_evidence_complete_from_real_review_still_false",
    "body_full_packet_generation_executed_here",
    "body_full_packet_generated_here",
    "body_full_packet_materialized_here",
    "dmh_op05_does_not_generate_body_full_packet_here",
    "dmh_op05_does_not_run_actual_human_review",
    "dmh_op05_does_not_create_operation_receipt_or_rows_or_disposal",
    "dmh_op05_does_not_start_p8_p6_r52_or_release",
    "dmh_op05_does_not_materialize_question_text",
    "dmh_op05_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _unique_non_empty_refs(values: Sequence[str]) -> bool:
    return bool(values) and len(values) == len(set(values)) and all(bool(value) for value in values)


def _dmh_op04_case_refs() -> tuple[list[str], list[str], list[str]]:
    case_refs = [f"cral_case_ref_{index:03d}" for index in range(1, P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT + 1)]
    blind_refs = [f"cral_blind_case_{index:03d}" for index in range(1, P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT + 1)]
    packet_refs = [f"cral_packet_ref_{index:03d}" for index in range(1, P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT + 1)]
    return case_refs, blind_refs, packet_refs


def _dmh_op04_manifest_rows() -> list[dict[str, Any]]:
    case_refs, blind_refs, packet_refs = _dmh_op04_case_refs()
    rows: list[dict[str, Any]] = []
    cursor = 0
    for family_ref, count in P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION.items():
        for _ in range(count):
            rows.append(
                {
                    "case_ref_id": case_refs[cursor],
                    "blind_case_id": blind_refs[cursor],
                    "packet_ref_id": packet_refs[cursor],
                    "case_role_family_ref": family_ref,
                    "review_unit_ref": "r54_p5_human_blind_qa_24_case_review_unit_bodyfree",
                    "body_free": True,
                }
            )
            cursor += 1
    return rows


def _dmh_op04_reviewer_index_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "reviewer_case_index_ref": f"reviewer_blind_index_{index:03d}",
            "blind_case_id": _clean_ref(row.get("blind_case_id"), default="blind_case_missing"),
            "body_free": True,
        }
        for index, row in enumerate(rows, start=1)
    ]


def _dmh_op04_family_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        family_ref = _clean_ref(row.get("case_role_family_ref"), default="unknown_family", max_length=160)
        counts[family_ref] = counts.get(family_ref, 0) + 1
    return counts


def _dmh_op05_packet_ref_ids(packet_generation_receipt_bodyfree: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(packet_generation_receipt_bodyfree, Mapping):
        return []
    refs = packet_generation_receipt_bodyfree.get("packet_ref_ids")
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes, bytearray)):
        return []
    return [_clean_ref(ref, default="missing_packet_ref", max_length=180) for ref in refs]


def _dmh_op04_blockers(op03: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op03, Mapping):
        return ["dmh_op04_explicit_allow_local_only_review_session_envelope_missing"]
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op03_explicit_allow_receipt_local_only_review_session_envelope_contract(op03)
    except ValueError:
        blockers.append("dmh_op04_op03_explicit_allow_local_only_review_session_envelope_invalid")
    if op03.get("dmh_op03_ready") is not True:
        blockers.append("dmh_op04_op03_explicit_allow_local_only_review_session_not_ready")
    if op03.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP04_STEP_REF:
        blockers.append("dmh_op04_op03_next_step_not_24_case_manifest_boundary")
    if op03.get("body_full_packet_generation_allowed_by_explicit_allow_receipt") is not True:
        blockers.append("dmh_op04_explicit_allow_does_not_allow_local_only_packet_request")
    if _scan_forbidden_payload_key_paths(op03, path="op03_material"):
        blockers.append("dmh_op04_op03_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def _dmh_op05_blockers(
    op04: Mapping[str, Any] | None,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op04, Mapping):
        return ["dmh_op05_24_case_manifest_packet_request_boundary_missing"]
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary_contract(op04)
    except ValueError:
        blockers.append("dmh_op05_op04_24_case_manifest_packet_request_boundary_invalid")
    if op04.get("dmh_op04_ready") is not True:
        blockers.append("dmh_op05_op04_24_case_manifest_packet_request_boundary_not_ready")
    if op04.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF:
        blockers.append("dmh_op05_op04_next_step_not_packet_generation_receipt_intake")
    if op04.get("packet_generation_request_ready") is not True:
        blockers.append("dmh_op05_op04_packet_generation_request_not_ready")
    if _scan_forbidden_payload_key_paths(op04, path="op04_material"):
        blockers.append("dmh_op05_op04_forbidden_body_question_path_hash_key_detected")

    if not isinstance(packet_generation_receipt_bodyfree, Mapping):
        blockers.append("dmh_op05_packet_generation_receipt_missing")
        return list(dict.fromkeys(blockers))

    forbidden_paths = _scan_forbidden_payload_key_paths(packet_generation_receipt_bodyfree, path="packet_generation_receipt")
    if forbidden_paths:
        blockers.append("dmh_op05_packet_generation_receipt_forbidden_body_question_path_hash_key_detected")
    if packet_generation_receipt_bodyfree.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION:
        blockers.append("dmh_op05_packet_generation_receipt_schema_version_mismatch")
    if packet_generation_receipt_bodyfree.get("body_free") is not True:
        blockers.append("dmh_op05_packet_generation_receipt_not_bodyfree")
    if packet_generation_receipt_bodyfree.get("actual_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP05_EXPECTED_ACTUAL_SOURCE_REF:
        blockers.append("dmh_op05_packet_generation_receipt_actual_source_ref_not_allowed")
    if packet_generation_receipt_bodyfree.get("review_session_id") != op04.get("review_session_id"):
        blockers.append("dmh_op05_packet_generation_receipt_review_session_id_mismatch")
    if packet_generation_receipt_bodyfree.get("packet_generation_request_ref") != P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF:
        blockers.append("dmh_op05_packet_generation_receipt_request_ref_mismatch")
    if packet_generation_receipt_bodyfree.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("dmh_op05_packet_generation_receipt_actual_review_basis_ref_mismatch")
    if packet_generation_receipt_bodyfree.get("packet_materialized_local_only") is not True:
        blockers.append("dmh_op05_packet_generation_receipt_does_not_confirm_local_only_materialization")
    if packet_generation_receipt_bodyfree.get("packet_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op05_packet_generation_receipt_packet_count_not_24")
    if packet_generation_receipt_bodyfree.get("packet_ref_id_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op05_packet_generation_receipt_packet_ref_id_count_not_24")
    packet_refs = _dmh_op05_packet_ref_ids(packet_generation_receipt_bodyfree)
    if not _unique_non_empty_refs(packet_refs) or len(packet_refs) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op05_packet_generation_receipt_packet_ref_ids_not_24_unique")
    if tuple(packet_refs) != tuple(op04.get("packet_ref_ids") or ()):  # body-free link only
        blockers.append("dmh_op05_packet_generation_receipt_packet_ref_ids_do_not_match_op04_manifest")
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
            blockers.append(f"dmh_op05_packet_generation_receipt_{false_key}_not_false")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary(
    *,
    explicit_allow_receipt_local_only_review_session_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP04 body-free 24-case manifest / packet request boundary."""

    op03 = explicit_allow_receipt_local_only_review_session_envelope
    session_id = _safe_review_session_id(review_session_id or (op03 or {}).get("review_session_id"))
    blockers = _dmh_op04_blockers(op03)
    ready = not blockers
    manifest_rows = _dmh_op04_manifest_rows() if ready else []
    reviewer_rows = _dmh_op04_reviewer_index_rows(manifest_rows) if ready else []
    family_counts = _dmh_op04_family_counts(manifest_rows)
    case_refs, blind_refs, packet_refs = _dmh_op04_case_refs()
    case_refs = case_refs if ready else []
    blind_refs = blind_refs if ready else []
    packet_refs = packet_refs if ready else []
    request_payload = {
        "packet_generation_request_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF,
        "review_session_id": session_id,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "required_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "case_manifest_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_CASE_MANIFEST_REF,
        "explicit_allow_ref": P7_R54_AHR_POST_PMN23_DMH_OP03_EXPLICIT_ALLOW_REF,
        "local_only_required": True,
        "must_not_export": True,
        "packet_completeness_scan_required": True,
        "export_denylist_scan_required": True,
        "purge_required": True,
        "body_free": True,
    } if ready else {}
    request_forbidden_paths = _scan_forbidden_payload_key_paths(request_payload, path="packet_generation_request_payload")
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP04_24_CASE_MANIFEST_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP04_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": (op03 or {}).get("schema_version", ""),
        "op03_material_ref": (op03 or {}).get("material_id", ""),
        "op03_next_required_step": (op03 or {}).get("next_required_step", ""),
        "op03_dmh_ready": (op03 or {}).get("dmh_op03_ready") is True,
        "op03_explicit_allow_receipt_present": (op03 or {}).get("explicit_allow_receipt_present") is True,
        "op03_body_full_packet_generation_allowed_by_explicit_allow_receipt": (op03 or {}).get("body_full_packet_generation_allowed_by_explicit_allow_receipt") is True,
        "op03_local_only_review_session_envelope_ready": (op03 or {}).get("local_only_review_session_envelope_ready") is True,
        "dmh_op04_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_STATUS_REF,
        "dmh_op04_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP04_ALLOWED_STATUS_REFS),
        "dmh_op04_ready": ready,
        "dmh_op04_blocker_refs": blockers,
        "dmh_op04_blocker_ref_count": len(blockers),
        "dmh_op04_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP04_READY_REASON_REFS) if ready else blockers,
        "dmh_op04_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP04_READY_REASON_REFS) if ready else len(blockers),
        "case_manifest_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_CASE_MANIFEST_REF if ready else "",
        "case_manifest_boundary_ready": ready,
        "case_manifest_source_ref": "r54_p5_human_blind_qa_24_case_manifest_bodyfree_contract_boundary" if ready else "",
        "required_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "total_case_count": len(manifest_rows),
        "case_ref_id_count": len(case_refs),
        "blind_case_id_count": len(blind_refs),
        "packet_ref_id_count": len(packet_refs),
        "selection_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "sanitized_review_result_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "rating_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "question_need_observation_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "case_distribution": dict(P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION.values()),
        "case_distribution_matches_design": family_counts == P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION if ready else False,
        "family_case_counts": family_counts,
        "boundary_case_count": family_counts.get("low_information_history_not_eligible", 0) + family_counts.get("free_tier_history_present_not_allowed", 0),
        "low_information_boundary_case_count": family_counts.get("low_information_history_not_eligible", 0),
        "free_tier_boundary_case_count": family_counts.get("free_tier_history_present_not_allowed", 0),
        "case_ref_ids": case_refs,
        "blind_case_ids": blind_refs,
        "packet_ref_ids": packet_refs,
        "case_ref_ids_unique": _unique_non_empty_refs(case_refs),
        "blind_case_ids_unique": _unique_non_empty_refs(blind_refs),
        "packet_ref_ids_unique": _unique_non_empty_refs(packet_refs),
        "blind_case_id_case_ref_separated": set(blind_refs).isdisjoint(case_refs),
        "blind_case_id_packet_ref_separated": set(blind_refs).isdisjoint(packet_refs),
        "case_ref_id_packet_ref_separated": set(case_refs).isdisjoint(packet_refs),
        "case_manifest_rows": manifest_rows,
        "case_manifest_row_count": len(manifest_rows),
        "controller_manifest_rows": manifest_rows,
        "controller_manifest_row_count": len(manifest_rows),
        "reviewer_facing_case_index_rows": reviewer_rows,
        "reviewer_facing_row_count": len(reviewer_rows),
        "reviewer_identifier_policy_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_REVIEWER_IDENTIFIER_POLICY_REF if ready else "",
        "controller_keeps_family_tier_expected_refs": ready,
        "reviewer_receives_blind_case_id_only": ready,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_case_ref_exposed": False,
        "reviewer_facing_packet_ref_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "reviewer_facing_hidden_metadata_exposed": False,
        "p4_r11_rows_confused_as_r54_review_rows": False,
        "p4_r11_rows_mixed_in": False,
        "p4_r11_rows_mixed_in_count": 0,
        "packet_generation_request_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF if ready else "",
        "packet_generation_request_payload": request_payload,
        "packet_generation_request_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS) if ready else [],
        "packet_generation_request_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS) if ready else 0,
        "packet_generation_request_forbidden_payload_key_paths": request_forbidden_paths,
        "packet_generation_request_forbidden_payload_key_path_count": len(request_forbidden_paths),
        "local_operation_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_LOCAL_OPERATION_REF if ready else "",
        "local_only_required": ready,
        "must_not_export": ready,
        "packet_completeness_scan_required": ready,
        "export_denylist_scan_required": ready,
        "purge_required": ready,
        "packet_generation_request_ready": ready,
        "packet_generation_request_bodyfree_only": True,
        "packet_generation_request_allowed_after_op04": ready,
        "body_full_packet_generation_may_be_run_after_this_boundary_by_external_local_only_operation": ready,
        "body_full_packet_generation_executed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "body_full_packet_exported_to_artifact": False,
        "body_full_export_allowed": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "packet_content_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "actual_human_review_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "dmh_op04_does_not_generate_body_full_packet": True,
        "dmh_op04_does_not_run_actual_human_review": True,
        "dmh_op04_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "dmh_op04_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op04_does_not_materialize_question_text": True,
        "dmh_op04_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP04_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP04_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP04 body-free 24-case manifest / packet request boundary contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP04_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP04 24-case manifest / packet request boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP04_24_CASE_MANIFEST_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP04_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP04 24-case manifest / packet request boundary",
    )
    if tuple(data.get("dmh_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 allowed status refs changed")
    for field, count_field in (
        ("dmh_op04_blocker_refs", "dmh_op04_blocker_ref_count"),
        ("dmh_op04_reason_refs", "dmh_op04_reason_ref_count"),
        ("case_manifest_rows", "case_manifest_row_count"),
        ("controller_manifest_rows", "controller_manifest_row_count"),
        ("reviewer_facing_case_index_rows", "reviewer_facing_row_count"),
        ("packet_generation_request_required_field_refs", "packet_generation_request_required_field_ref_count"),
        ("packet_generation_request_forbidden_payload_key_paths", "packet_generation_request_forbidden_payload_key_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP04 {count_field} changed")
    for key in (
        "packet_generation_request_bodyfree_only",
        "actual_human_review_still_not_run",
        "actual_review_evidence_complete_from_real_review_still_false",
        "current_actual_review_basis_remains_264_85_258_171",
        "dmh_op04_does_not_generate_body_full_packet",
        "dmh_op04_does_not_run_actual_human_review",
        "dmh_op04_does_not_create_operation_receipt_or_rows_or_disposal",
        "dmh_op04_does_not_start_p8_p6_r52_or_release",
        "dmh_op04_does_not_materialize_question_text",
        "dmh_op04_does_not_execute_postcr22_ex_reentry",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP04 required true boundary changed: {key}")
    for key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "reviewer_facing_hidden_metadata_exposed",
        "p4_r11_rows_confused_as_r54_review_rows",
        "p4_r11_rows_mixed_in",
        "body_full_packet_generation_executed_here",
        "body_full_packet_generated_here",
        "body_full_packet_materialized_here",
        "body_full_packet_exported_to_artifact",
        "body_full_export_allowed",
        "local_absolute_path_included",
        "body_hash_stored",
        "terminal_output_body_included",
        "packet_content_included",
        "question_text_included",
        "draft_question_text_included",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP04 required false boundary promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 actual review basis allowed changed")
    if data.get("case_distribution") != P7_R54_AHR_POST_PMN23_DMH_OP04_MANIFEST_DISTRIBUTION:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 case distribution changed")
    if data.get("case_distribution_total_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 distribution total changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 not-claimed boundary must stay false")

    ready = data.get("dmh_op04_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP04_READY_STATUS_REF
    if data.get("dmh_op04_ready") is not ready or data.get("case_manifest_boundary_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 ready flags changed")
    if ready:
        for key in (
            "op03_dmh_ready",
            "op03_explicit_allow_receipt_present",
            "op03_body_full_packet_generation_allowed_by_explicit_allow_receipt",
            "op03_local_only_review_session_envelope_ready",
            "case_distribution_matches_design",
            "case_ref_ids_unique",
            "blind_case_ids_unique",
            "packet_ref_ids_unique",
            "blind_case_id_case_ref_separated",
            "blind_case_id_packet_ref_separated",
            "case_ref_id_packet_ref_separated",
            "controller_keeps_family_tier_expected_refs",
            "reviewer_receives_blind_case_id_only",
            "local_only_required",
            "must_not_export",
            "packet_completeness_scan_required",
            "export_denylist_scan_required",
            "purge_required",
            "packet_generation_request_ready",
            "packet_generation_request_allowed_after_op04",
            "body_full_packet_generation_may_be_run_after_this_boundary_by_external_local_only_operation",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP04 ready condition changed: {key}")
        expected_counts = {
            "total_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "case_ref_id_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "blind_case_id_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "packet_ref_id_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "selection_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "sanitized_review_result_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "rating_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "question_need_observation_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "case_manifest_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "controller_manifest_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
            "reviewer_facing_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        }
        for key, expected in expected_counts.items():
            if data.get(key) != expected:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP04 count changed: {key}")
        if data.get("case_manifest_ref") != P7_R54_AHR_POST_PMN23_DMH_OP04_CASE_MANIFEST_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 case manifest ref changed")
        if data.get("packet_generation_request_ref") != P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 request ref changed")
        payload = data.get("packet_generation_request_payload")
        if not isinstance(payload, Mapping):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 request payload missing")
        if tuple(data.get("packet_generation_request_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 request required field refs changed")
        if tuple(payload.keys()) != P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 request payload keys changed")
        if payload.get("body_free") is not True or payload.get("must_not_export") is not True or payload.get("purge_required") is not True:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 request body-free/export/purge flags changed")
        if data.get("packet_generation_request_forbidden_payload_key_paths") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 request contains forbidden body/path/hash keys")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 next required step changed")
    else:
        if data.get("dmh_op04_status_ref") != P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 blocked status changed")
        if not data.get("dmh_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 blocked material must carry blockers")
        if data.get("packet_generation_request_ready") is not False or data.get("packet_generation_request_allowed_after_op04") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 blocked material cannot allow packet request")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP03_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP04_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP04 blocked next step changed")
    return True


def build_p7_r54_ahr_post_pmn23_dmh_op05_packet_generation_receipt_bodyfree(
    *, review_session_id: Any = None, packet_ref_ids: Sequence[Any] | None = None
) -> dict[str, Any]:
    """Build a body-free OP05 packet-generation receipt fixture shape.

    This helper does not generate body-full packets.  It only materializes the
    body-free receipt shape used by OP05 contract tests and by later real local
    operation intake.
    """

    session_id = _safe_review_session_id(review_session_id)
    default_packet_refs = _dmh_op04_case_refs()[2]
    receipt_packet_refs = [
        _clean_ref(ref, default="missing_packet_ref", max_length=180)
        for ref in (packet_ref_ids if packet_ref_ids is not None else default_packet_refs)
    ]
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION,
        "packet_generation_receipt_ref": P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_REF,
        "review_session_id": session_id,
        "packet_generation_request_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_source_ref": P7_R54_AHR_POST_PMN23_DMH_OP05_EXPECTED_ACTUAL_SOURCE_REF,
        "packet_materialized_local_only": True,
        "packet_count": len(receipt_packet_refs),
        "packet_ref_id_count": len(receipt_packet_refs),
        "packet_ref_ids": receipt_packet_refs,
        "body_full_exported": False,
        "body_full_packet_exported_to_artifact": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "packet_content_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "receipt_source_kind_ref": P7_R54_AHR_POST_PMN23_DMH_OP05_CONTRACT_FIXTURE_SOURCE_KIND_REF,
        "body_free": True,
    }


def build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary(
    *,
    packet_generation_receipt_bodyfree: Mapping[str, Any] | None = None,
    twenty_four_case_manifest_packet_request_boundary: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP05 body-free packet-generation receipt intake boundary."""

    op04 = twenty_four_case_manifest_packet_request_boundary
    session_id = _safe_review_session_id(review_session_id or (op04 or {}).get("review_session_id"))
    receipt_map = packet_generation_receipt_bodyfree if isinstance(packet_generation_receipt_bodyfree, Mapping) else {}
    blockers = _dmh_op05_blockers(op04, packet_generation_receipt_bodyfree)
    ready = not blockers
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt_map, path="packet_generation_receipt") if receipt_map else []
    packet_refs = _dmh_op05_packet_ref_ids(receipt_map)
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP05_BODY_FULL_PACKET_GENERATION_RECEIPT_INTAKE_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": (op04 or {}).get("schema_version", ""),
        "op04_material_ref": (op04 or {}).get("material_id", ""),
        "op04_next_required_step": (op04 or {}).get("next_required_step", ""),
        "op04_dmh_ready": (op04 or {}).get("dmh_op04_ready") is True,
        "op04_packet_generation_request_ready": (op04 or {}).get("packet_generation_request_ready") is True,
        "op04_case_manifest_boundary_ready": (op04 or {}).get("case_manifest_boundary_ready") is True,
        "op04_packet_generation_request_ref": (op04 or {}).get("packet_generation_request_ref", ""),
        "dmh_op05_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP05_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_STATUS_REF,
        "dmh_op05_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP05_ALLOWED_STATUS_REFS),
        "dmh_op05_ready": ready,
        "dmh_op05_blocker_refs": blockers,
        "dmh_op05_blocker_ref_count": len(blockers),
        "dmh_op05_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP05_READY_REASON_REFS) if ready else blockers,
        "dmh_op05_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP05_READY_REASON_REFS) if ready else len(blockers),
        "packet_generation_receipt_present": isinstance(packet_generation_receipt_bodyfree, Mapping),
        "packet_generation_receipt_schema_version": receipt_map.get("schema_version", ""),
        "packet_generation_receipt_ref": _clean_ref(receipt_map.get("packet_generation_receipt_ref"), default=""),
        "packet_generation_receipt_forbidden_payload_key_paths": forbidden_paths,
        "packet_generation_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "packet_generation_receipt_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_PACKET_RECEIPT_FIELD_REFS),
        "packet_generation_receipt_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_PACKET_RECEIPT_FIELD_REFS),
        "packet_generation_receipt_intake_boundary_ready": ready,
        "packet_generation_receipt_actual_source_ref": _clean_ref(receipt_map.get("actual_source_ref"), default=""),
        "packet_generation_receipt_actual_source_ref_allowed": receipt_map.get("actual_source_ref") == P7_R54_AHR_POST_PMN23_DMH_OP05_EXPECTED_ACTUAL_SOURCE_REF,
        "packet_generation_receipt_source_kind_ref": _clean_ref(receipt_map.get("receipt_source_kind_ref"), default=""),
        "packet_generation_receipt_source_kind_is_contract_fixture_not_real_evidence": receipt_map.get("receipt_source_kind_ref") == P7_R54_AHR_POST_PMN23_DMH_OP05_CONTRACT_FIXTURE_SOURCE_KIND_REF,
        "packet_generation_request_ref": _clean_ref(receipt_map.get("packet_generation_request_ref"), default=""),
        "packet_generation_request_ref_confirmed": receipt_map.get("packet_generation_request_ref") == P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "actual_review_basis_ref_confirmed": receipt_map.get("actual_review_basis_ref") == P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "packet_materialized_local_only": receipt_map.get("packet_materialized_local_only") is True,
        "packet_count": int(receipt_map.get("packet_count") or 0),
        "packet_ref_id_count": int(receipt_map.get("packet_ref_id_count") or 0),
        "packet_ref_ids": packet_refs,
        "packet_ref_ids_unique": _unique_non_empty_refs(packet_refs),
        "expected_packet_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "body_full_exported": False,
        "body_full_packet_exported_to_artifact": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "terminal_output_body_included": False,
        "packet_content_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "packet_generation_receipt_bodyfree_only": receipt_map.get("body_free") is True,
        "packet_generation_receipt_content_export_absent": all(
            receipt_map.get(key) is False
            for key in (
                "body_full_exported",
                "body_full_packet_exported_to_artifact",
                "packet_content_included",
                "question_text_included",
                "draft_question_text_included",
            )
        ) if receipt_map else False,
        "packet_generation_receipt_path_hash_terminal_output_absent": all(
            receipt_map.get(key) is False
            for key in ("local_absolute_path_included", "body_hash_stored", "terminal_output_body_included")
        ) if receipt_map else False,
        "packet_generation_receipt_intaked_here": ready,
        "packet_generation_receipt_from_real_operation_claimed_here": False,
        "packet_completeness_export_denylist_scan_required_next": ready,
        "actual_human_review_still_not_run": True,
        "actual_operation_receipt_still_not_received": True,
        "actual_review_rows_still_not_created": True,
        "actual_disposal_purge_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "body_full_packet_generation_executed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "dmh_op05_does_not_generate_body_full_packet_here": True,
        "dmh_op05_does_not_run_actual_human_review": True,
        "dmh_op05_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "dmh_op05_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op05_does_not_materialize_question_text": True,
        "dmh_op05_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP05_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP05_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP05 body-free packet-generation receipt intake boundary contract."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP05 body-full packet generation receipt intake boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP05_BODY_FULL_PACKET_GENERATION_RECEIPT_INTAKE_BOUNDARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP05_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP05 body-full packet generation receipt intake boundary",
    )
    if tuple(data.get("dmh_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 allowed status refs changed")
    for field, count_field in (
        ("dmh_op05_blocker_refs", "dmh_op05_blocker_ref_count"),
        ("dmh_op05_reason_refs", "dmh_op05_reason_ref_count"),
        ("packet_generation_receipt_forbidden_payload_key_paths", "packet_generation_receipt_forbidden_payload_key_path_count"),
        ("packet_generation_receipt_required_field_refs", "packet_generation_receipt_required_field_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP05 {count_field} changed")
    for key in (
        "current_actual_review_basis_remains_264_85_258_171",
        "actual_human_review_still_not_run",
        "actual_operation_receipt_still_not_received",
        "actual_review_rows_still_not_created",
        "actual_disposal_purge_still_not_run",
        "actual_review_evidence_complete_from_real_review_still_false",
        "dmh_op05_does_not_generate_body_full_packet_here",
        "dmh_op05_does_not_run_actual_human_review",
        "dmh_op05_does_not_create_operation_receipt_or_rows_or_disposal",
        "dmh_op05_does_not_start_p8_p6_r52_or_release",
        "dmh_op05_does_not_materialize_question_text",
        "dmh_op05_does_not_execute_postcr22_ex_reentry",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP05 required true boundary changed: {key}")
    for key in (
        "body_full_exported",
        "body_full_packet_exported_to_artifact",
        "local_absolute_path_included",
        "body_hash_stored",
        "terminal_output_body_included",
        "packet_content_included",
        "question_text_included",
        "draft_question_text_included",
        "packet_generation_receipt_from_real_operation_claimed_here",
        "body_full_packet_generation_executed_here",
        "body_full_packet_generated_here",
        "body_full_packet_materialized_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP05 required false boundary promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 actual review basis allowed changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 not-claimed boundary must stay false")
    if tuple(data.get("packet_generation_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP05_REQUIRED_PACKET_RECEIPT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 required receipt fields changed")

    ready = data.get("dmh_op05_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP05_READY_STATUS_REF
    if data.get("dmh_op05_ready") is not ready or data.get("packet_generation_receipt_intake_boundary_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 ready flags changed")
    if ready:
        for key in (
            "op04_dmh_ready",
            "op04_packet_generation_request_ready",
            "op04_case_manifest_boundary_ready",
            "packet_generation_receipt_present",
            "packet_generation_receipt_actual_source_ref_allowed",
            "packet_generation_receipt_source_kind_is_contract_fixture_not_real_evidence",
            "packet_generation_request_ref_confirmed",
            "actual_review_basis_ref_confirmed",
            "packet_materialized_local_only",
            "packet_ref_ids_unique",
            "packet_generation_receipt_bodyfree_only",
            "packet_generation_receipt_content_export_absent",
            "packet_generation_receipt_path_hash_terminal_output_absent",
            "packet_generation_receipt_intaked_here",
            "packet_completeness_export_denylist_scan_required_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP05 ready condition changed: {key}")
        if data.get("packet_generation_receipt_schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 receipt schema changed")
        if data.get("packet_generation_receipt_ref") != P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 receipt ref changed")
        if data.get("packet_generation_receipt_actual_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP05_EXPECTED_ACTUAL_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 actual source ref changed")
        if data.get("packet_generation_request_ref") != P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 request ref changed")
        if data.get("packet_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 packet count changed")
        if data.get("packet_ref_id_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 packet ref count changed")
        if tuple(data.get("packet_ref_ids") or ()) != tuple(_dmh_op04_case_refs()[2]):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 packet refs changed")
        if data.get("expected_packet_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 expected packet count changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 next required step changed")
    else:
        if data.get("dmh_op05_status_ref") != P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 blocked status changed")
        if not data.get("dmh_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 blocked material must carry blockers")
        if data.get("packet_generation_receipt_intaked_here") is not False or data.get("packet_completeness_export_denylist_scan_required_next") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 blocked material cannot claim intake ready")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP05 blocked next step changed")
    return True


build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_24_case_manifest_packet_request_boundary_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_24_case_manifest_packet_request_boundary_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op04_24_case_manifest_packet_request_boundary_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_generation_receipt_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op05_packet_generation_receipt_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_body_full_packet_generation_receipt_intake_boundary_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_body_full_packet_generation_receipt_intake_boundary_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract
)


# DMH-OP06 / DMH-OP07: packet scan receipt boundary and reviewer-person / selection-only form finalization.
# These helpers remain body-free internal contract material.  They do not scan a real local folder,
# export packet content, start the actual 24-case review, create actual rows, execute purge,
# start P8, run R52, complete P7, or allow release.
P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op06_packet_completeness_export_denylist_scan_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op06_packet_completeness_export_denylist_scan_receipt_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op07_reviewer_person_confirmation_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SELECTION_ONLY_FORM_FINALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op07_reviewer_person_confirmation_selection_only_form_finalization.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[6]
P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[7]
P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[8]

P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op06_packet_completeness_export_denylist_scan_receipt_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op07_reviewer_person_confirmation_selection_only_form_or_stop"
)

P7_R54_AHR_POST_PMN23_DMH_OP06_READY_STATUS_REF: Final = (
    "DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_STATUS_REF: Final = (
    "DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_BLOCKED_BY_EXPORT_DENYLIST_OR_BODY_LEAK"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP06_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP07_READY_STATUS_REF: Final = (
    "DMH_OP07_REVIEWER_PERSON_SELECTION_ONLY_FORM_FINALIZED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_STATUS_REF: Final = (
    "DMH_OP07_REVIEWER_PERSON_SELECTION_ONLY_FORM_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP07_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_STATUS_REF,
)

P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_SCAN_RECEIPT_REF: Final = (
    "post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_SCAN_REF: Final = (
    "post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_boundary_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_EXPECTED_SOURCE_REF: Final = (
    "local_packet_completeness_export_denylist_scan_receipt_bodyfree"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_CONTRACT_FIXTURE_SOURCE_KIND_REF: Final = (
    "contract_fixture_scan_not_real_local_folder_scan_evidence"
)
P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DENYLIST_POLICY_REF: Final = (
    P7_R54_AHR_POST_PMN23_DMH_OP03_EXPORT_DENYLIST_POLICY_REF
)
P7_R54_AHR_POST_PMN23_DMH_OP06_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op05_packet_generation_receipt_intake_boundary_ready_bodyfree",
    "packet_completeness_scan_receipt_present_bodyfree",
    "packet_count_and_packet_ref_count_are_24_bodyfree",
    "packet_completeness_scan_passed_bodyfree",
    "export_denylist_scan_passed_without_body_question_path_hash_terminal_output",
    "op06_scan_receipt_boundary_does_not_claim_real_folder_scan_or_actual_review",
)
P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_SCAN_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "packet_scan_receipt_ref",
    "review_session_id",
    "packet_generation_receipt_ref",
    "packet_generation_request_ref",
    "actual_review_basis_ref",
    "actual_source_ref",
    "packet_count",
    "packet_ref_id_count",
    "packet_ref_ids",
    "packet_completeness_scan_required",
    "packet_completeness_scan_passed",
    "export_denylist_policy_ref",
    "export_denylist_scan_required",
    "export_denylist_scan_passed",
    "export_denylist_violation_refs",
    "export_denylist_violation_ref_count",
    "body_full_exported",
    "body_full_packet_exported_to_artifact",
    "raw_input_detected_in_export",
    "comment_text_detected_in_export",
    "returned_emlis_body_detected_in_export",
    "history_body_detected_in_export",
    "packet_content_detected_in_export",
    "question_text_detected_in_export",
    "draft_question_text_detected_in_export",
    "local_path_detected_in_export",
    "body_hash_detected_in_export",
    "terminal_output_body_detected_in_export",
    "stdout_body_detected_in_export",
    "stderr_body_detected_in_export",
    "traceback_body_detected_in_export",
    "scan_source_kind_ref",
    "scan_executed_against_real_local_folder_claimed_here",
    "body_free",
)
P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DETECTION_FALSE_FIELD_REFS: Final[tuple[str, ...]] = (
    "body_full_exported",
    "body_full_packet_exported_to_artifact",
    "raw_input_detected_in_export",
    "comment_text_detected_in_export",
    "returned_emlis_body_detected_in_export",
    "history_body_detected_in_export",
    "packet_content_detected_in_export",
    "question_text_detected_in_export",
    "draft_question_text_detected_in_export",
    "local_path_detected_in_export",
    "body_hash_detected_in_export",
    "terminal_output_body_detected_in_export",
    "stdout_body_detected_in_export",
    "stderr_body_detected_in_export",
    "traceback_body_detected_in_export",
)

P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_REF: Final = (
    "post_pmn23_dmh_op07_reviewer_person_confirmation_receipt_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF: Final = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REVIEWER_PERSON_REF
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_REF: Final = (
    "local_reviewer_person_confirmation_bodyfree"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_KIND_REF: Final = (
    "bodyfree_person_confirmation_boundary_not_actual_review_execution"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_SELECTION_ONLY_FORM_REF: Final = (
    "post_pmn23_dmh_op07_reviewer_selection_only_form_finalized_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_INSTRUCTION_REF: Final = (
    "post_pmn23_dmh_op07_reviewer_instruction_selection_only_no_free_text_no_question_text_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_INSTRUCTION_POLICY_REF: Final = (
    "reviewer_reads_local_only_packet_and_selects_refs_without_body_quote_or_question_text"
)
P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_RATING_AXIS_TARGET_THRESHOLDS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_SCORE_OPTION_REFS: Final[tuple[float, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_SCORE_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_VERDICT_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_SANITIZED_REASON_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_SANITIZED_REASON_ID_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_READFEEL_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_READFEEL_BLOCKER_ID_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_EXECUTION_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_EXECUTION_BLOCKER_ID_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_AMBIGUITY_KIND_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_ONE_QUESTION_FIT_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_REPAIR_REQUIRED_OPTION_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP09_PLAN_CANDIDATE_FLAG_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP07_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op06_packet_completeness_export_denylist_scan_receipt_ready_bodyfree",
    "reviewer_person_confirmed_bodyfree",
    "selection_only_form_finalized_without_free_text_question_text_body_path_hash",
    "six_rating_axes_and_24_case_count_finalized_bodyfree",
    "actual_human_review_not_started_by_op07_form_finalization",
)
P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_REVIEWER_CONFIRMATION_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "reviewer_person_confirmation_receipt_ref",
    "review_session_id",
    "actual_review_basis_ref",
    "reviewer_person_ref",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_person_confirmation_source_ref",
    "reviewer_confirmation_source_kind_ref",
    "reviewer_identity_public_export_allowed",
    "reviewer_free_text_export_allowed",
    "reviewer_notes_body_export_allowed",
    "reviewer_local_only_read_receipt_present",
    "actual_human_review_executed_by_person",
    "ai_or_helper_substitution_allowed",
    "local_absolute_path_included",
    "body_hash_stored",
    "packet_content_included",
    "question_text_included",
    "draft_question_text_included",
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:7]
P7_R54_AHR_POST_PMN23_DMH_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[7:]
P7_R54_AHR_POST_PMN23_DMH_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:8]
P7_R54_AHR_POST_PMN23_DMH_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[8:]

P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op05_schema_version",
    "op05_material_ref",
    "op05_next_required_step",
    "op05_dmh_ready",
    "op05_packet_generation_receipt_intaked_here",
    "op05_packet_completeness_export_denylist_scan_required_next",
    "op05_packet_generation_receipt_ref",
    "op05_packet_generation_request_ref",
    "dmh_op06_status_ref",
    "dmh_op06_allowed_status_refs",
    "dmh_op06_ready",
    "dmh_op06_blocker_refs",
    "dmh_op06_blocker_ref_count",
    "dmh_op06_reason_refs",
    "dmh_op06_reason_ref_count",
    "packet_scan_receipt_present",
    "packet_scan_receipt_schema_version",
    "packet_scan_receipt_ref",
    "packet_scan_receipt_forbidden_payload_key_paths",
    "packet_scan_receipt_forbidden_payload_key_path_count",
    "packet_scan_receipt_required_field_refs",
    "packet_scan_receipt_required_field_ref_count",
    "packet_scan_receipt_intake_boundary_ready",
    "packet_scan_receipt_source_ref",
    "packet_scan_receipt_source_ref_allowed",
    "packet_scan_receipt_source_kind_ref",
    "packet_scan_receipt_source_kind_is_contract_fixture_not_real_scan_evidence",
    "packet_generation_receipt_ref",
    "packet_generation_receipt_ref_confirmed",
    "packet_generation_request_ref",
    "packet_generation_request_ref_confirmed",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "actual_review_basis_ref_confirmed",
    "current_actual_review_basis_remains_264_85_258_171",
    "expected_packet_count",
    "packet_count",
    "packet_ref_id_count",
    "packet_ref_ids",
    "packet_ref_ids_unique",
    "packet_count_matches_expected",
    "packet_ref_id_count_matches_expected",
    "packet_completeness_scan_required",
    "packet_completeness_scan_passed",
    "export_denylist_policy_ref",
    "export_denylist_policy_ref_confirmed",
    "export_denylist_scan_required",
    "export_denylist_scan_passed",
    "export_denylist_violation_refs",
    "export_denylist_violation_ref_count",
    "body_full_packet_export_candidate_refs",
    "body_full_packet_export_candidate_count",
    *P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DETECTION_FALSE_FIELD_REFS,
    "local_absolute_path_included",
    "body_hash_stored",
    "terminal_output_body_included",
    "packet_content_included",
    "question_text_included",
    "draft_question_text_included",
    "packet_scan_receipt_bodyfree_only",
    "packet_scan_receipt_content_export_absent",
    "packet_scan_receipt_path_hash_terminal_output_absent",
    "packet_scan_receipt_intaked_here",
    "packet_scan_receipt_from_real_operation_claimed_here",
    "packet_scan_executed_against_real_local_folder_claimed_here",
    "reviewer_person_selection_only_form_allowed_next",
    "actual_human_review_still_not_run",
    "actual_operation_receipt_still_not_received",
    "actual_review_rows_still_not_created",
    "actual_disposal_purge_still_not_run",
    "actual_review_evidence_complete_from_real_review_still_false",
    "body_full_packet_generation_executed_here",
    "body_full_packet_generated_here",
    "body_full_packet_materialized_here",
    "dmh_op06_does_not_scan_real_local_folder_here",
    "dmh_op06_does_not_generate_body_full_packet_here",
    "dmh_op06_does_not_run_actual_human_review",
    "dmh_op06_does_not_create_operation_receipt_or_rows_or_disposal",
    "dmh_op06_does_not_start_p8_p6_r52_or_release",
    "dmh_op06_does_not_materialize_question_text",
    "dmh_op06_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op06_schema_version",
    "op06_material_ref",
    "op06_next_required_step",
    "op06_dmh_ready",
    "op06_packet_count",
    "op06_packet_ref_id_count",
    "op06_packet_completeness_scan_passed",
    "op06_export_denylist_scan_passed",
    "dmh_op07_status_ref",
    "dmh_op07_allowed_status_refs",
    "dmh_op07_ready",
    "dmh_op07_blocker_refs",
    "dmh_op07_blocker_ref_count",
    "dmh_op07_reason_refs",
    "dmh_op07_reason_ref_count",
    "reviewer_person_confirmation_receipt_present",
    "reviewer_person_confirmation_receipt_schema_version",
    "reviewer_person_confirmation_receipt_ref",
    "reviewer_person_confirmation_receipt_forbidden_payload_key_paths",
    "reviewer_person_confirmation_receipt_forbidden_payload_key_path_count",
    "reviewer_person_confirmation_receipt_required_field_refs",
    "reviewer_person_confirmation_receipt_required_field_ref_count",
    "reviewer_person_confirmation_source_ref",
    "reviewer_person_confirmation_source_ref_allowed",
    "reviewer_confirmation_source_kind_ref",
    "reviewer_confirmation_source_kind_is_boundary_not_actual_review_execution",
    "reviewer_person_ref",
    "reviewer_person_ref_present",
    "reviewer_person_ref_is_bodyfree_ref",
    "reviewer_person_ref_has_local_path_shape",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "actual_human_review_executed_by_person",
    "ai_or_helper_substitution_allowed",
    "selection_only_form_ready",
    "selection_only_form_ref",
    "reviewer_instruction_ref",
    "reviewer_instruction_policy_ref",
    "selection_only",
    "selection_only_form_bodyfree_only",
    "free_text_field_present",
    "free_text_field_export_allowed",
    "reviewer_note_field_present",
    "reviewer_notes_body_field_present",
    "raw_body_copy_field_present",
    "question_text_field_present",
    "draft_question_text_field_present",
    "local_path_field_present",
    "body_hash_field_present",
    "packet_content_field_present",
    "required_axis_count",
    "rating_axis_refs",
    "rating_axis_target_thresholds",
    "score_option_refs",
    "verdict_option_refs",
    "sanitized_reason_id_option_refs",
    "readfeel_blocker_id_option_refs",
    "execution_blocker_id_option_refs",
    "question_need_primary_class_options",
    "ambiguity_kind_option_refs",
    "one_question_fit_option_refs",
    "repair_required_option_refs",
    "plan_candidate_flag_refs",
    "required_case_count",
    "selection_row_count_required",
    "sanitized_review_result_row_count_required",
    "rating_row_count_required",
    "question_need_observation_row_count_required",
    "reviewer_receives_blind_case_id_only",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "reviewer_facing_case_ref_exposed",
    "reviewer_facing_packet_ref_exposed",
    "reviewer_facing_expected_result_exposed",
    "reviewer_facing_hidden_metadata_exposed",
    "actual_review_operation_state_machine_allowed_next",
    "actual_human_review_started_here",
    "actual_human_review_run_here",
    "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
    "dmh_op07_does_not_run_actual_human_review",
    "dmh_op07_does_not_create_actual_operation_receipt_or_rows_or_disposal",
    "dmh_op07_does_not_start_p8_p6_r52_or_release",
    "dmh_op07_does_not_materialize_question_text",
    "dmh_op07_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _dmh_op06_packet_ref_ids(packet_scan_receipt_bodyfree: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(packet_scan_receipt_bodyfree, Mapping):
        return []
    refs = packet_scan_receipt_bodyfree.get("packet_ref_ids")
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes, bytearray)):
        return []
    return [_clean_ref(ref, default="missing_packet_ref", max_length=180) for ref in refs]


def _dmh_op06_blockers(
    op05: Mapping[str, Any] | None,
    packet_scan_receipt_bodyfree: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op05, Mapping):
        return ["dmh_op06_packet_generation_receipt_intake_boundary_missing"]
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary_contract(op05)
    except ValueError:
        blockers.append("dmh_op06_op05_packet_generation_receipt_intake_boundary_invalid")
    if op05.get("dmh_op05_ready") is not True:
        blockers.append("dmh_op06_op05_packet_generation_receipt_intake_boundary_not_ready")
    if op05.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF:
        blockers.append("dmh_op06_op05_next_step_not_packet_scan_receipt")
    if op05.get("packet_completeness_export_denylist_scan_required_next") is not True:
        blockers.append("dmh_op06_op05_packet_scan_not_required_next")
    if _scan_forbidden_payload_key_paths(op05, path="op05_material"):
        blockers.append("dmh_op06_op05_forbidden_body_question_path_hash_key_detected")

    if not isinstance(packet_scan_receipt_bodyfree, Mapping):
        blockers.append("dmh_op06_packet_scan_receipt_missing")
        return list(dict.fromkeys(blockers))

    forbidden_paths = _scan_forbidden_payload_key_paths(packet_scan_receipt_bodyfree, path="packet_scan_receipt")
    if forbidden_paths:
        blockers.append("dmh_op06_packet_scan_receipt_forbidden_body_question_path_hash_key_detected")
    if packet_scan_receipt_bodyfree.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_SCHEMA_VERSION:
        blockers.append("dmh_op06_packet_scan_receipt_schema_version_mismatch")
    if packet_scan_receipt_bodyfree.get("body_free") is not True:
        blockers.append("dmh_op06_packet_scan_receipt_not_bodyfree")
    if packet_scan_receipt_bodyfree.get("actual_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP06_EXPECTED_SOURCE_REF:
        blockers.append("dmh_op06_packet_scan_receipt_source_ref_not_allowed")
    if packet_scan_receipt_bodyfree.get("scan_source_kind_ref") != P7_R54_AHR_POST_PMN23_DMH_OP06_CONTRACT_FIXTURE_SOURCE_KIND_REF:
        blockers.append("dmh_op06_packet_scan_receipt_source_kind_not_contract_boundary")
    if packet_scan_receipt_bodyfree.get("scan_executed_against_real_local_folder_claimed_here") is not False:
        blockers.append("dmh_op06_packet_scan_receipt_claims_real_folder_scan_here")
    if packet_scan_receipt_bodyfree.get("review_session_id") != op05.get("review_session_id"):
        blockers.append("dmh_op06_packet_scan_receipt_review_session_id_mismatch")
    if packet_scan_receipt_bodyfree.get("packet_generation_receipt_ref") != op05.get("packet_generation_receipt_ref"):
        blockers.append("dmh_op06_packet_scan_receipt_packet_generation_receipt_ref_mismatch")
    if packet_scan_receipt_bodyfree.get("packet_generation_request_ref") != P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF:
        blockers.append("dmh_op06_packet_scan_receipt_request_ref_mismatch")
    if packet_scan_receipt_bodyfree.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("dmh_op06_packet_scan_receipt_actual_review_basis_ref_mismatch")
    if packet_scan_receipt_bodyfree.get("packet_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op06_packet_scan_receipt_packet_count_not_24")
    if packet_scan_receipt_bodyfree.get("packet_ref_id_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op06_packet_scan_receipt_packet_ref_id_count_not_24")
    packet_refs = _dmh_op06_packet_ref_ids(packet_scan_receipt_bodyfree)
    if not _unique_non_empty_refs(packet_refs) or len(packet_refs) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op06_packet_scan_receipt_packet_ref_ids_not_24_unique")
    if tuple(packet_refs) != tuple(op05.get("packet_ref_ids") or ()):
        blockers.append("dmh_op06_packet_scan_receipt_packet_ref_ids_do_not_match_op05")
    if packet_scan_receipt_bodyfree.get("packet_completeness_scan_required") is not True:
        blockers.append("dmh_op06_packet_completeness_scan_required_not_true")
    if packet_scan_receipt_bodyfree.get("packet_completeness_scan_passed") is not True:
        blockers.append("dmh_op06_packet_completeness_scan_not_passed")
    if packet_scan_receipt_bodyfree.get("export_denylist_policy_ref") != P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DENYLIST_POLICY_REF:
        blockers.append("dmh_op06_export_denylist_policy_ref_mismatch")
    if packet_scan_receipt_bodyfree.get("export_denylist_scan_required") is not True:
        blockers.append("dmh_op06_export_denylist_scan_required_not_true")
    if packet_scan_receipt_bodyfree.get("export_denylist_scan_passed") is not True:
        blockers.append("dmh_op06_export_denylist_scan_not_passed")
    if packet_scan_receipt_bodyfree.get("export_denylist_violation_refs") not in ([], ()):  # type: ignore[comparison-overlap]
        blockers.append("dmh_op06_export_denylist_violation_refs_not_empty")
    if packet_scan_receipt_bodyfree.get("export_denylist_violation_ref_count") != 0:
        blockers.append("dmh_op06_export_denylist_violation_ref_count_not_zero")
    for false_key in P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DETECTION_FALSE_FIELD_REFS:
        if packet_scan_receipt_bodyfree.get(false_key) is not False:
            blockers.append(f"dmh_op06_packet_scan_receipt_{false_key}_not_false")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_bodyfree(
    *,
    review_session_id: Any = None,
    packet_generation_receipt_ref: Any = None,
    packet_ref_ids: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Build a body-free OP06 packet completeness / export denylist scan receipt fixture shape.

    This shape is a contract fixture and not a claim that a real local folder scan was run.
    """

    session_id = _safe_review_session_id(review_session_id)
    refs = [
        _clean_ref(ref, default="missing_packet_ref", max_length=180)
        for ref in (packet_ref_ids if packet_ref_ids is not None else _dmh_op04_case_refs()[2])
    ]
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_SCHEMA_VERSION,
        "packet_scan_receipt_ref": P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_SCAN_RECEIPT_REF,
        "review_session_id": session_id,
        "packet_generation_receipt_ref": _clean_ref(packet_generation_receipt_ref, default=P7_R54_AHR_POST_PMN23_DMH_OP05_PACKET_GENERATION_RECEIPT_REF, max_length=180),
        "packet_generation_request_ref": P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_source_ref": P7_R54_AHR_POST_PMN23_DMH_OP06_EXPECTED_SOURCE_REF,
        "packet_count": len(refs),
        "packet_ref_id_count": len(refs),
        "packet_ref_ids": refs,
        "packet_completeness_scan_required": True,
        "packet_completeness_scan_passed": True,
        "export_denylist_policy_ref": P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DENYLIST_POLICY_REF,
        "export_denylist_scan_required": True,
        "export_denylist_scan_passed": True,
        "export_denylist_violation_refs": [],
        "export_denylist_violation_ref_count": 0,
        "body_full_exported": False,
        "body_full_packet_exported_to_artifact": False,
        "raw_input_detected_in_export": False,
        "comment_text_detected_in_export": False,
        "returned_emlis_body_detected_in_export": False,
        "history_body_detected_in_export": False,
        "packet_content_detected_in_export": False,
        "question_text_detected_in_export": False,
        "draft_question_text_detected_in_export": False,
        "local_path_detected_in_export": False,
        "body_hash_detected_in_export": False,
        "terminal_output_body_detected_in_export": False,
        "stdout_body_detected_in_export": False,
        "stderr_body_detected_in_export": False,
        "traceback_body_detected_in_export": False,
        "scan_source_kind_ref": P7_R54_AHR_POST_PMN23_DMH_OP06_CONTRACT_FIXTURE_SOURCE_KIND_REF,
        "scan_executed_against_real_local_folder_claimed_here": False,
        "body_free": True,
    }


def build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary(
    *,
    body_full_packet_generation_receipt_intake_boundary: Mapping[str, Any] | None = None,
    packet_scan_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP06 body-free packet completeness / export denylist scan receipt boundary."""

    op05 = body_full_packet_generation_receipt_intake_boundary
    if op05 is None:
        op05 = build_p7_r54_ahr_post_pmn23_dmh_op05_body_full_packet_generation_receipt_intake_boundary()
    session_id = _safe_review_session_id(review_session_id or (op05 or {}).get("review_session_id"))
    blockers = _dmh_op06_blockers(op05, packet_scan_receipt_bodyfree)
    ready = not blockers
    receipt = packet_scan_receipt_bodyfree if isinstance(packet_scan_receipt_bodyfree, Mapping) else {}
    packet_refs = _dmh_op06_packet_ref_ids(receipt)
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="packet_scan_receipt") if isinstance(receipt, Mapping) else []
    denylist_refs = list(receipt.get("export_denylist_violation_refs") or []) if isinstance(receipt, Mapping) else []
    status_ref = (
        P7_R54_AHR_POST_PMN23_DMH_OP06_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_BY_LEAK_STATUS_REF
        if any("not_false" in blocker or "violation" in blocker or "forbidden" in blocker for blocker in blockers)
        else P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_STATUS_REF
    )
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_BOUNDARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": (op05 or {}).get("schema_version", ""),
        "op05_material_ref": (op05 or {}).get("material_id", ""),
        "op05_next_required_step": (op05 or {}).get("next_required_step", ""),
        "op05_dmh_ready": (op05 or {}).get("dmh_op05_ready") is True,
        "op05_packet_generation_receipt_intaked_here": (op05 or {}).get("packet_generation_receipt_intaked_here") is True,
        "op05_packet_completeness_export_denylist_scan_required_next": (op05 or {}).get("packet_completeness_export_denylist_scan_required_next") is True,
        "op05_packet_generation_receipt_ref": (op05 or {}).get("packet_generation_receipt_ref", ""),
        "op05_packet_generation_request_ref": (op05 or {}).get("packet_generation_request_ref", ""),
        "dmh_op06_status_ref": status_ref,
        "dmh_op06_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP06_ALLOWED_STATUS_REFS),
        "dmh_op06_ready": ready,
        "dmh_op06_blocker_refs": blockers,
        "dmh_op06_blocker_ref_count": len(blockers),
        "dmh_op06_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP06_READY_REASON_REFS) if ready else blockers,
        "dmh_op06_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP06_READY_REASON_REFS) if ready else len(blockers),
        "packet_scan_receipt_present": isinstance(packet_scan_receipt_bodyfree, Mapping),
        "packet_scan_receipt_schema_version": receipt.get("schema_version", ""),
        "packet_scan_receipt_ref": receipt.get("packet_scan_receipt_ref", ""),
        "packet_scan_receipt_forbidden_payload_key_paths": forbidden_paths,
        "packet_scan_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "packet_scan_receipt_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_SCAN_RECEIPT_FIELD_REFS),
        "packet_scan_receipt_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_SCAN_RECEIPT_FIELD_REFS),
        "packet_scan_receipt_intake_boundary_ready": ready,
        "packet_scan_receipt_source_ref": receipt.get("actual_source_ref", ""),
        "packet_scan_receipt_source_ref_allowed": receipt.get("actual_source_ref") == P7_R54_AHR_POST_PMN23_DMH_OP06_EXPECTED_SOURCE_REF,
        "packet_scan_receipt_source_kind_ref": receipt.get("scan_source_kind_ref", ""),
        "packet_scan_receipt_source_kind_is_contract_fixture_not_real_scan_evidence": receipt.get("scan_source_kind_ref") == P7_R54_AHR_POST_PMN23_DMH_OP06_CONTRACT_FIXTURE_SOURCE_KIND_REF,
        "packet_generation_receipt_ref": receipt.get("packet_generation_receipt_ref", ""),
        "packet_generation_receipt_ref_confirmed": receipt.get("packet_generation_receipt_ref") == (op05 or {}).get("packet_generation_receipt_ref"),
        "packet_generation_request_ref": receipt.get("packet_generation_request_ref", ""),
        "packet_generation_request_ref_confirmed": receipt.get("packet_generation_request_ref") == P7_R54_AHR_POST_PMN23_DMH_OP04_PACKET_GENERATION_REQUEST_REF,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "actual_review_basis_ref_confirmed": receipt.get("actual_review_basis_ref") == P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "expected_packet_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "packet_count": receipt.get("packet_count", 0),
        "packet_ref_id_count": receipt.get("packet_ref_id_count", 0),
        "packet_ref_ids": packet_refs,
        "packet_ref_ids_unique": _unique_non_empty_refs(packet_refs),
        "packet_count_matches_expected": receipt.get("packet_count") == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "packet_ref_id_count_matches_expected": receipt.get("packet_ref_id_count") == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "packet_completeness_scan_required": receipt.get("packet_completeness_scan_required") is True,
        "packet_completeness_scan_passed": ready and receipt.get("packet_completeness_scan_passed") is True,
        "export_denylist_policy_ref": receipt.get("export_denylist_policy_ref", ""),
        "export_denylist_policy_ref_confirmed": receipt.get("export_denylist_policy_ref") == P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DENYLIST_POLICY_REF,
        "export_denylist_scan_required": receipt.get("export_denylist_scan_required") is True,
        "export_denylist_scan_passed": ready and receipt.get("export_denylist_scan_passed") is True,
        "export_denylist_violation_refs": denylist_refs,
        "export_denylist_violation_ref_count": len(denylist_refs),
        "body_full_packet_export_candidate_refs": [],
        "body_full_packet_export_candidate_count": 0,
        **{key: bool(receipt.get(key)) for key in P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DETECTION_FALSE_FIELD_REFS},
        "local_absolute_path_included": bool(receipt.get("local_path_detected_in_export")),
        "body_hash_stored": bool(receipt.get("body_hash_detected_in_export")),
        "terminal_output_body_included": bool(receipt.get("terminal_output_body_detected_in_export")),
        "packet_content_included": bool(receipt.get("packet_content_detected_in_export")),
        "question_text_included": bool(receipt.get("question_text_detected_in_export")),
        "draft_question_text_included": bool(receipt.get("draft_question_text_detected_in_export")),
        "packet_scan_receipt_bodyfree_only": receipt.get("body_free") is True,
        "packet_scan_receipt_content_export_absent": not bool(receipt.get("packet_content_detected_in_export")),
        "packet_scan_receipt_path_hash_terminal_output_absent": not any(bool(receipt.get(key)) for key in ("local_path_detected_in_export", "body_hash_detected_in_export", "terminal_output_body_detected_in_export")),
        "packet_scan_receipt_intaked_here": ready,
        "packet_scan_receipt_from_real_operation_claimed_here": False,
        "packet_scan_executed_against_real_local_folder_claimed_here": receipt.get("scan_executed_against_real_local_folder_claimed_here") is True,
        "reviewer_person_selection_only_form_allowed_next": ready,
        "actual_human_review_still_not_run": True,
        "actual_operation_receipt_still_not_received": True,
        "actual_review_rows_still_not_created": True,
        "actual_disposal_purge_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "body_full_packet_generation_executed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_materialized_here": False,
        "dmh_op06_does_not_scan_real_local_folder_here": True,
        "dmh_op06_does_not_generate_body_full_packet_here": True,
        "dmh_op06_does_not_run_actual_human_review": True,
        "dmh_op06_does_not_create_operation_receipt_or_rows_or_disposal": True,
        "dmh_op06_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op06_does_not_materialize_question_text": True,
        "dmh_op06_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP06_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP06 body-free packet completeness / export denylist scan receipt boundary."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP06 packet scan receipt boundary",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_BOUNDARY_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP06_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP06 packet scan receipt boundary",
    )
    if tuple(data.get("dmh_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 allowed status refs changed")
    for field, count_field in (
        ("dmh_op06_blocker_refs", "dmh_op06_blocker_ref_count"),
        ("dmh_op06_reason_refs", "dmh_op06_reason_ref_count"),
        ("packet_scan_receipt_forbidden_payload_key_paths", "packet_scan_receipt_forbidden_payload_key_path_count"),
        ("packet_scan_receipt_required_field_refs", "packet_scan_receipt_required_field_ref_count"),
        ("export_denylist_violation_refs", "export_denylist_violation_ref_count"),
        ("body_full_packet_export_candidate_refs", "body_full_packet_export_candidate_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP06 {count_field} changed")
    for key in (
        "current_actual_review_basis_remains_264_85_258_171",
        "actual_human_review_still_not_run",
        "actual_operation_receipt_still_not_received",
        "actual_review_rows_still_not_created",
        "actual_disposal_purge_still_not_run",
        "actual_review_evidence_complete_from_real_review_still_false",
        "dmh_op06_does_not_scan_real_local_folder_here",
        "dmh_op06_does_not_generate_body_full_packet_here",
        "dmh_op06_does_not_run_actual_human_review",
        "dmh_op06_does_not_create_operation_receipt_or_rows_or_disposal",
        "dmh_op06_does_not_start_p8_p6_r52_or_release",
        "dmh_op06_does_not_materialize_question_text",
        "dmh_op06_does_not_execute_postcr22_ex_reentry",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP06 required true boundary changed: {key}")
    for key in (
        "packet_scan_receipt_from_real_operation_claimed_here",
        "body_full_packet_generation_executed_here",
        "body_full_packet_generated_here",
        "body_full_packet_materialized_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP06 required false boundary promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 actual review basis allowed changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 not-claimed boundary must stay false")
    if tuple(data.get("packet_scan_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP06_REQUIRED_SCAN_RECEIPT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 required scan receipt fields changed")

    ready = data.get("dmh_op06_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP06_READY_STATUS_REF
    if data.get("dmh_op06_ready") is not ready or data.get("packet_scan_receipt_intake_boundary_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 ready flags changed")
    if ready:
        for key in (
            *P7_R54_AHR_POST_PMN23_DMH_OP06_EXPORT_DETECTION_FALSE_FIELD_REFS,
            "local_absolute_path_included",
            "body_hash_stored",
            "terminal_output_body_included",
            "packet_content_included",
            "question_text_included",
            "draft_question_text_included",
            "packet_scan_executed_against_real_local_folder_claimed_here",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP06 ready receipt leaked or promoted: {key}")
        for key in (
            "op05_dmh_ready",
            "op05_packet_generation_receipt_intaked_here",
            "op05_packet_completeness_export_denylist_scan_required_next",
            "packet_scan_receipt_present",
            "packet_scan_receipt_source_ref_allowed",
            "packet_scan_receipt_source_kind_is_contract_fixture_not_real_scan_evidence",
            "packet_generation_receipt_ref_confirmed",
            "packet_generation_request_ref_confirmed",
            "actual_review_basis_ref_confirmed",
            "packet_ref_ids_unique",
            "packet_count_matches_expected",
            "packet_ref_id_count_matches_expected",
            "packet_completeness_scan_required",
            "packet_completeness_scan_passed",
            "export_denylist_policy_ref_confirmed",
            "export_denylist_scan_required",
            "export_denylist_scan_passed",
            "packet_scan_receipt_bodyfree_only",
            "packet_scan_receipt_content_export_absent",
            "packet_scan_receipt_path_hash_terminal_output_absent",
            "packet_scan_receipt_intaked_here",
            "reviewer_person_selection_only_form_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP06 ready condition changed: {key}")
        if data.get("packet_scan_receipt_schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_RECEIPT_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 scan receipt schema changed")
        if data.get("packet_scan_receipt_ref") != P7_R54_AHR_POST_PMN23_DMH_OP06_PACKET_SCAN_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 scan receipt ref changed")
        if data.get("packet_scan_receipt_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP06_EXPECTED_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 source ref changed")
        if data.get("packet_scan_receipt_source_kind_ref") != P7_R54_AHR_POST_PMN23_DMH_OP06_CONTRACT_FIXTURE_SOURCE_KIND_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 source kind changed")
        if data.get("packet_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 packet count changed")
        if data.get("packet_ref_id_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 packet ref count changed")
        if tuple(data.get("packet_ref_ids") or ()) != tuple(_dmh_op04_case_refs()[2]):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 packet refs changed")
        if data.get("export_denylist_violation_refs") != [] or data.get("body_full_packet_export_candidate_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 export violations changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 next required step changed")
    else:
        if data.get("dmh_op06_status_ref") not in (
            P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_STATUS_REF,
            P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_BY_LEAK_STATUS_REF,
        ):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 blocked status changed")
        if not data.get("dmh_op06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 blocked material must carry blockers")
        if data.get("packet_scan_receipt_intaked_here") is not False or data.get("reviewer_person_selection_only_form_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 blocked material cannot allow reviewer form")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP06 blocked next step changed")
    return True


def _dmh_op07_blockers(
    op06: Mapping[str, Any] | None,
    reviewer_person_confirmation_receipt_bodyfree: Mapping[str, Any] | None,
) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op06, Mapping):
        return ["dmh_op07_packet_scan_receipt_boundary_missing"]
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract(op06)
    except ValueError:
        blockers.append("dmh_op07_op06_packet_scan_receipt_boundary_invalid")
    if op06.get("dmh_op06_ready") is not True:
        blockers.append("dmh_op07_op06_packet_scan_receipt_boundary_not_ready")
    if op06.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF:
        blockers.append("dmh_op07_op06_next_step_not_reviewer_form")
    if op06.get("packet_completeness_scan_passed") is not True:
        blockers.append("dmh_op07_op06_packet_completeness_scan_not_passed")
    if op06.get("export_denylist_scan_passed") is not True:
        blockers.append("dmh_op07_op06_export_denylist_scan_not_passed")
    if _scan_forbidden_payload_key_paths(op06, path="op06_material"):
        blockers.append("dmh_op07_op06_forbidden_body_question_path_hash_key_detected")

    if not isinstance(reviewer_person_confirmation_receipt_bodyfree, Mapping):
        blockers.append("dmh_op07_reviewer_person_confirmation_receipt_missing")
        return list(dict.fromkeys(blockers))

    forbidden_paths = _scan_forbidden_payload_key_paths(
        reviewer_person_confirmation_receipt_bodyfree,
        path="reviewer_person_confirmation_receipt",
    )
    if forbidden_paths:
        blockers.append("dmh_op07_reviewer_person_confirmation_receipt_forbidden_body_question_path_hash_key_detected")
    if reviewer_person_confirmation_receipt_bodyfree.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_SCHEMA_VERSION:
        blockers.append("dmh_op07_reviewer_person_confirmation_receipt_schema_version_mismatch")
    if reviewer_person_confirmation_receipt_bodyfree.get("body_free") is not True:
        blockers.append("dmh_op07_reviewer_person_confirmation_receipt_not_bodyfree")
    if reviewer_person_confirmation_receipt_bodyfree.get("review_session_id") != op06.get("review_session_id"):
        blockers.append("dmh_op07_reviewer_person_confirmation_receipt_review_session_id_mismatch")
    if reviewer_person_confirmation_receipt_bodyfree.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("dmh_op07_reviewer_person_confirmation_receipt_actual_review_basis_ref_mismatch")
    reviewer_ref = _clean_ref(reviewer_person_confirmation_receipt_bodyfree.get("reviewer_person_ref"), default="", max_length=180)
    if not reviewer_ref:
        blockers.append("dmh_op07_reviewer_person_ref_missing")
    if _ref_has_local_path_shape(reviewer_ref):
        blockers.append("dmh_op07_reviewer_person_ref_has_local_path_shape")
    if _ref_has_question_or_body_text_shape(reviewer_ref):
        blockers.append("dmh_op07_reviewer_person_ref_has_body_or_question_shape")
    if reviewer_person_confirmation_receipt_bodyfree.get("reviewer_is_person") is not True:
        blockers.append("dmh_op07_reviewer_is_person_not_true")
    if reviewer_person_confirmation_receipt_bodyfree.get("reviewer_person_confirmed") is not True:
        blockers.append("dmh_op07_reviewer_person_confirmed_not_true")
    if reviewer_person_confirmation_receipt_bodyfree.get("reviewer_person_confirmation_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_REF:
        blockers.append("dmh_op07_reviewer_person_confirmation_source_ref_not_allowed")
    if reviewer_person_confirmation_receipt_bodyfree.get("reviewer_confirmation_source_kind_ref") != P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_KIND_REF:
        blockers.append("dmh_op07_reviewer_confirmation_source_kind_not_boundary")
    for false_key in (
        "reviewer_identity_public_export_allowed",
        "reviewer_free_text_export_allowed",
        "reviewer_notes_body_export_allowed",
        "reviewer_local_only_read_receipt_present",
        "actual_human_review_executed_by_person",
        "ai_or_helper_substitution_allowed",
        "local_absolute_path_included",
        "body_hash_stored",
        "packet_content_included",
        "question_text_included",
        "draft_question_text_included",
    ):
        if reviewer_person_confirmation_receipt_bodyfree.get(false_key) is not False:
            blockers.append(f"dmh_op07_reviewer_person_confirmation_receipt_{false_key}_not_false")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_receipt_bodyfree(
    *,
    review_session_id: Any = None,
    reviewer_person_ref: Any = None,
) -> dict[str, Any]:
    """Build a body-free reviewer-person confirmation receipt shape for OP07.

    This confirms the reviewer-person boundary and does not claim the actual 24-case review ran.
    """

    session_id = _safe_review_session_id(review_session_id)
    reviewer_ref = _clean_ref(
        reviewer_person_ref,
        default=P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF,
        max_length=180,
    )
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_SCHEMA_VERSION,
        "reviewer_person_confirmation_receipt_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_REF,
        "review_session_id": session_id,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "reviewer_person_ref": reviewer_ref,
        "reviewer_is_person": True,
        "reviewer_person_confirmed": True,
        "reviewer_person_confirmation_source_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_REF,
        "reviewer_confirmation_source_kind_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_KIND_REF,
        "reviewer_identity_public_export_allowed": False,
        "reviewer_free_text_export_allowed": False,
        "reviewer_notes_body_export_allowed": False,
        "reviewer_local_only_read_receipt_present": False,
        "actual_human_review_executed_by_person": False,
        "ai_or_helper_substitution_allowed": False,
        "local_absolute_path_included": False,
        "body_hash_stored": False,
        "packet_content_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "body_free": True,
    }


def build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization(
    *,
    packet_completeness_export_denylist_scan_receipt_boundary: Mapping[str, Any] | None = None,
    reviewer_person_confirmation_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP07 body-free reviewer-person / selection-only form finalization."""

    op06 = packet_completeness_export_denylist_scan_receipt_boundary
    if op06 is None:
        op06 = build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary()
    session_id = _safe_review_session_id(review_session_id or (op06 or {}).get("review_session_id"))
    blockers = _dmh_op07_blockers(op06, reviewer_person_confirmation_receipt_bodyfree)
    ready = not blockers
    receipt = reviewer_person_confirmation_receipt_bodyfree if isinstance(reviewer_person_confirmation_receipt_bodyfree, Mapping) else {}
    forbidden_paths = _scan_forbidden_payload_key_paths(receipt, path="reviewer_person_confirmation_receipt") if isinstance(receipt, Mapping) else []
    reviewer_ref = _clean_ref(receipt.get("reviewer_person_ref", "") if isinstance(receipt, Mapping) else "", default="", max_length=180)
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SELECTION_ONLY_FORM_FINALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": (op06 or {}).get("schema_version", ""),
        "op06_material_ref": (op06 or {}).get("material_id", ""),
        "op06_next_required_step": (op06 or {}).get("next_required_step", ""),
        "op06_dmh_ready": (op06 or {}).get("dmh_op06_ready") is True,
        "op06_packet_count": (op06 or {}).get("packet_count", 0),
        "op06_packet_ref_id_count": (op06 or {}).get("packet_ref_id_count", 0),
        "op06_packet_completeness_scan_passed": (op06 or {}).get("packet_completeness_scan_passed") is True,
        "op06_export_denylist_scan_passed": (op06 or {}).get("export_denylist_scan_passed") is True,
        "dmh_op07_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_STATUS_REF,
        "dmh_op07_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_ALLOWED_STATUS_REFS),
        "dmh_op07_ready": ready,
        "dmh_op07_blocker_refs": blockers,
        "dmh_op07_blocker_ref_count": len(blockers),
        "dmh_op07_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_READY_REASON_REFS) if ready else blockers,
        "dmh_op07_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_READY_REASON_REFS) if ready else len(blockers),
        "reviewer_person_confirmation_receipt_present": isinstance(reviewer_person_confirmation_receipt_bodyfree, Mapping),
        "reviewer_person_confirmation_receipt_schema_version": receipt.get("schema_version", ""),
        "reviewer_person_confirmation_receipt_ref": receipt.get("reviewer_person_confirmation_receipt_ref", ""),
        "reviewer_person_confirmation_receipt_forbidden_payload_key_paths": forbidden_paths,
        "reviewer_person_confirmation_receipt_forbidden_payload_key_path_count": len(forbidden_paths),
        "reviewer_person_confirmation_receipt_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_REVIEWER_CONFIRMATION_RECEIPT_FIELD_REFS),
        "reviewer_person_confirmation_receipt_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_REVIEWER_CONFIRMATION_RECEIPT_FIELD_REFS),
        "reviewer_person_confirmation_source_ref": receipt.get("reviewer_person_confirmation_source_ref", ""),
        "reviewer_person_confirmation_source_ref_allowed": receipt.get("reviewer_person_confirmation_source_ref") == P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_REF,
        "reviewer_confirmation_source_kind_ref": receipt.get("reviewer_confirmation_source_kind_ref", ""),
        "reviewer_confirmation_source_kind_is_boundary_not_actual_review_execution": receipt.get("reviewer_confirmation_source_kind_ref") == P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SOURCE_KIND_REF,
        "reviewer_person_ref": reviewer_ref,
        "reviewer_person_ref_present": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_is_bodyfree_ref": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_has_local_path_shape": _ref_has_local_path_shape(reviewer_ref),
        "reviewer_is_person": ready and receipt.get("reviewer_is_person") is True,
        "reviewer_person_confirmed": ready and receipt.get("reviewer_person_confirmed") is True,
        "reviewer_local_only_read_receipt_present": False,
        "actual_human_review_executed_by_person": False,
        "ai_or_helper_substitution_allowed": False,
        "selection_only_form_ready": ready,
        "selection_only_form_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_SELECTION_ONLY_FORM_REF if ready else "",
        "reviewer_instruction_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_INSTRUCTION_REF if ready else "",
        "reviewer_instruction_policy_ref": P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_INSTRUCTION_POLICY_REF if ready else "",
        "selection_only": ready,
        "selection_only_form_bodyfree_only": True,
        "free_text_field_present": False,
        "free_text_field_export_allowed": False,
        "reviewer_note_field_present": False,
        "reviewer_notes_body_field_present": False,
        "raw_body_copy_field_present": False,
        "question_text_field_present": False,
        "draft_question_text_field_present": False,
        "local_path_field_present": False,
        "body_hash_field_present": False,
        "packet_content_field_present": False,
        "required_axis_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS) if ready else [],
        "rating_axis_target_thresholds": dict(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS) if ready else {},
        "score_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_SCORE_OPTION_REFS) if ready else [],
        "verdict_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_VERDICT_OPTION_REFS) if ready else [],
        "sanitized_reason_id_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_SANITIZED_REASON_ID_OPTION_REFS) if ready else [],
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_READFEEL_BLOCKER_ID_OPTION_REFS) if ready else [],
        "execution_blocker_id_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_EXECUTION_BLOCKER_ID_OPTION_REFS) if ready else [],
        "question_need_primary_class_options": list(P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS) if ready else [],
        "ambiguity_kind_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS) if ready else [],
        "one_question_fit_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS) if ready else [],
        "repair_required_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS) if ready else [],
        "plan_candidate_flag_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_PLAN_CANDIDATE_FLAG_REFS) if ready else [],
        "required_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "selection_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "sanitized_review_result_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "rating_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "question_need_observation_row_count_required": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else 0,
        "reviewer_receives_blind_case_id_only": ready,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_case_ref_exposed": False,
        "reviewer_facing_packet_ref_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "reviewer_facing_hidden_metadata_exposed": False,
        "actual_review_operation_state_machine_allowed_next": ready,
        "actual_human_review_started_here": False,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "dmh_op07_does_not_run_actual_human_review": True,
        "dmh_op07_does_not_create_actual_operation_receipt_or_rows_or_disposal": True,
        "dmh_op07_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op07_does_not_materialize_question_text": True,
        "dmh_op07_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP07_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP07_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DMH-OP07 reviewer-person confirmation / selection-only form finalization."""

    _required_fields_present(
        data,
        required=P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-PostPMN23-DMH-OP07 reviewer-person selection-only form",
    )
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_SELECTION_ONLY_FORM_FINALIZATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP07 reviewer-person selection-only form",
    )
    if tuple(data.get("dmh_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 allowed status refs changed")
    for field, count_field in (
        ("dmh_op07_blocker_refs", "dmh_op07_blocker_ref_count"),
        ("dmh_op07_reason_refs", "dmh_op07_reason_ref_count"),
        ("reviewer_person_confirmation_receipt_forbidden_payload_key_paths", "reviewer_person_confirmation_receipt_forbidden_payload_key_path_count"),
        ("reviewer_person_confirmation_receipt_required_field_refs", "reviewer_person_confirmation_receipt_required_field_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP07 {count_field} changed")
    for key in (
        "selection_only_form_bodyfree_only",
        "actual_review_evidence_complete_from_real_review_still_false",
        "current_actual_review_basis_remains_264_85_258_171",
        "dmh_op07_does_not_run_actual_human_review",
        "dmh_op07_does_not_create_actual_operation_receipt_or_rows_or_disposal",
        "dmh_op07_does_not_start_p8_p6_r52_or_release",
        "dmh_op07_does_not_materialize_question_text",
        "dmh_op07_does_not_execute_postcr22_ex_reentry",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP07 required true boundary changed: {key}")
    for key in (
        "reviewer_local_only_read_receipt_present",
        "actual_human_review_executed_by_person",
        "ai_or_helper_substitution_allowed",
        "free_text_field_present",
        "free_text_field_export_allowed",
        "reviewer_note_field_present",
        "reviewer_notes_body_field_present",
        "raw_body_copy_field_present",
        "question_text_field_present",
        "draft_question_text_field_present",
        "local_path_field_present",
        "body_hash_field_present",
        "packet_content_field_present",
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "reviewer_facing_hidden_metadata_exposed",
        "actual_human_review_started_here",
        "actual_human_review_run_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP07 required false boundary promoted: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 actual review basis changed")
    if data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 actual review basis allowed changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 not-claimed boundary must stay false")
    if tuple(data.get("reviewer_person_confirmation_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP07_REQUIRED_REVIEWER_CONFIRMATION_RECEIPT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 required reviewer confirmation fields changed")

    ready = data.get("dmh_op07_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP07_READY_STATUS_REF
    if data.get("dmh_op07_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 ready flag changed")
    if ready:
        if data.get("reviewer_person_ref_has_local_path_shape") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 ready reviewer ref must not look like a local path")
        if data.get("op06_dmh_ready") is not True or data.get("op06_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 ready requires OP06 ready next step")
        if data.get("op06_packet_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT or data.get("op06_packet_ref_id_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 ready requires 24 packet refs")
        if data.get("op06_packet_completeness_scan_passed") is not True or data.get("op06_export_denylist_scan_passed") is not True:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 ready requires OP06 passed scans")
        for key in (
            "reviewer_person_confirmation_receipt_present",
            "reviewer_person_confirmation_source_ref_allowed",
            "reviewer_confirmation_source_kind_is_boundary_not_actual_review_execution",
            "reviewer_person_ref_present",
            "reviewer_person_ref_is_bodyfree_ref",
            "reviewer_is_person",
            "reviewer_person_confirmed",
            "selection_only_form_ready",
            "selection_only",
            "reviewer_receives_blind_case_id_only",
            "actual_review_operation_state_machine_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP07 ready condition changed: {key}")
        if data.get("reviewer_person_confirmation_receipt_schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 reviewer confirmation schema changed")
        if data.get("reviewer_person_confirmation_receipt_ref") != P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_CONFIRMATION_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 reviewer confirmation receipt ref changed")
        if data.get("reviewer_person_ref") != P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 reviewer ref changed")
        if data.get("selection_only_form_ref") != P7_R54_AHR_POST_PMN23_DMH_OP07_SELECTION_ONLY_FORM_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 selection form ref changed")
        if data.get("reviewer_instruction_ref") != P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_INSTRUCTION_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 reviewer instruction ref changed")
        if data.get("required_axis_count") != len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 axis count changed")
        if tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 axis refs changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 axis thresholds changed")
        for field, expected in (
            ("score_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_SCORE_OPTION_REFS),
            ("verdict_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_VERDICT_OPTION_REFS),
            ("sanitized_reason_id_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_SANITIZED_REASON_ID_OPTION_REFS),
            ("readfeel_blocker_id_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_READFEEL_BLOCKER_ID_OPTION_REFS),
            ("execution_blocker_id_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_EXECUTION_BLOCKER_ID_OPTION_REFS),
            ("question_need_primary_class_options", P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS),
            ("ambiguity_kind_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS),
            ("one_question_fit_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS),
            ("repair_required_option_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS),
            ("plan_candidate_flag_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_PLAN_CANDIDATE_FLAG_REFS),
        ):
            if tuple(data.get(field) or ()) != expected:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP07 option refs changed: {field}")
        if data.get("required_case_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 required case count changed")
        for count_field in (
            "selection_row_count_required",
            "sanitized_review_result_row_count_required",
            "rating_row_count_required",
            "question_need_observation_row_count_required",
        ):
            if data.get(count_field) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP07 {count_field} changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP07_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 next required step changed")
    else:
        if data.get("dmh_op07_status_ref") != P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 blocked status changed")
        if not data.get("dmh_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 blocked material must carry blockers")
        if data.get("selection_only_form_ready") is not False or data.get("actual_review_operation_state_machine_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 blocked material cannot allow review state machine")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 blocked implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP07 blocked next step changed")
    return True


build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_completeness_export_denylist_scan_receipt_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_completeness_export_denylist_scan_receipt_boundary_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_packet_completeness_export_denylist_scan_receipt_boundary_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op06_packet_completeness_export_denylist_scan_receipt_boundary_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_reviewer_person_confirmation_receipt_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_receipt_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_reviewer_person_confirmation_selection_only_form_finalization_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_reviewer_person_confirmation_selection_only_form_finalization_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract
)


# DMH-OP08 / DMH-OP09: actual review operation state-machine intake and operation receipt intake.
# These helpers accept only body-free lifecycle / receipt material supplied from a local-only
# person review boundary.  They do not generate packet content, do not create sanitized rows,
# rating rows, question observation rows, disposal receipts, P8 questions, R52 execution, P7
# completion, or release decisions.
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_LIFECYCLE_STATE_CAPTURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op08_actual_review_operation_lifecycle_state_capture.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_ACTUAL_REVIEW_OPERATION_STATE_MACHINE_PAUSE_ABORT_LIFECYCLE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op08_actual_review_operation_state_machine_pause_abort_lifecycle.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op09_actual_operation_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op09_actual_operation_receipt_intake.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[9]
P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[10]

P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op08_actual_review_operation_state_machine_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_or_abort_actual_local_only_review_before_operation_receipt_intake"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_NEXT_REQUIRED_STEP_REF: Final = (
    "restart_actual_local_only_human_review_after_abort_body_purge_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op09_actual_operation_receipt_intake_or_stop"
)

P7_R54_AHR_POST_PMN23_DMH_OP08_READY_STATUS_REF: Final = (
    "DMH_OP08_REVIEW_COMPLETED_SELECTION_ROWS_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_STATUS_REF: Final = (
    "DMH_OP08_REVIEW_PAUSED_LOCAL_ONLY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_STATUS_REF: Final = (
    "DMH_OP08_ABORTED_BODY_PURGED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_STATUS_REF: Final = (
    "DMH_OP08_ACTUAL_REVIEW_OPERATION_STATE_MACHINE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "DMH_OP08_ACTUAL_REVIEW_OPERATION_STATE_MACHINE_BLOCKED_BY_BODY_LEAK"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP08_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP09_READY_STATUS_REF: Final = (
    "DMH_OP09_ACTUAL_OPERATION_RECEIPT_ACCEPTED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_STATUS_REF: Final = (
    "DMH_OP09_ACTUAL_OPERATION_RECEIPT_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "DMH_OP09_ACTUAL_OPERATION_RECEIPT_INTAKE_BLOCKED_BY_BODY_LEAK"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP09_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_BY_LEAK_STATUS_REF,
)

P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_CAPTURE_REF: Final = (
    "post_pmn23_dmh_op08_actual_review_operation_state_capture_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_ACTUAL_SOURCE_REF: Final = (
    "actual_person_local_only_review_operation_state_capture_bodyfree"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_NOT_STARTED_REF: Final = "DMH_NOT_STARTED"
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_IN_PROGRESS_REF: Final = "DMH_REVIEW_IN_PROGRESS_LOCAL_ONLY"
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF: Final = "DMH_PAUSED_LOCAL_ONLY"
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF: Final = "DMH_ABORTED_BODY_PURGED"
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF: Final = "DMH_REVIEW_COMPLETED_SELECTION_ROWS_READY"
P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_REVIEW_STATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_NOT_STARTED_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_IN_PROGRESS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_NONE_REF: Final = "NO_PAUSE_OR_ABORT_RECORDED_BODYFREE"
P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_PAUSED_REF: Final = "PAUSED_LOCAL_ONLY_REVIEW_RESUMABLE_BODYFREE"
P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_ABORTED_PURGED_REF: Final = "ABORTED_BODY_PURGED_BODYFREE"
P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_PAUSE_ABORT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_NONE_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_PAUSED_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_ABORTED_PURGED_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STARTED_BUCKET_REF: Final = (
    "post_pmn23_dmh_op08_review_started_bucket_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_COMPLETED_BUCKET_REF: Final = (
    "post_pmn23_dmh_op08_review_completed_bucket_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP08_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op07_reviewer_person_selection_only_form_finalized_bodyfree",
    "actual_review_lifecycle_state_capture_received_bodyfree",
    "reviewer_local_only_read_receipt_present_bodyfree",
    "review_state_completed_selection_rows_ready_bodyfree",
    "reviewed_case_count_and_selection_row_count_are_24_bodyfree",
    "operation_receipt_intake_required_next_without_rows_disposal_or_promotion",
)
P7_R54_AHR_POST_PMN23_DMH_OP08_PROTOCOL_STEP_REFS: Final[tuple[str, ...]] = (
    "reviewer_reads_local_only_packet",
    "reviewer_selects_axis_scores_verdict_and_refs_without_body_quote",
    "pause_keeps_body_full_local_only_and_blocks_receipt_intake",
    "abort_requires_body_purged_before_restart_or_stop",
    "complete_requires_24_selection_rows_ready_bodyfree",
    "operation_receipt_is_created_bodyfree_next",
)
P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_STATE_CAPTURE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_state_capture_ref",
    "review_session_id",
    "actual_review_basis_ref",
    "actual_source_ref",
    "reviewer_person_ref",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "review_state_ref",
    "review_started_bucket_ref",
    "review_completed_bucket_ref",
    "reviewed_case_count",
    "selection_row_count",
    "local_only",
    "must_not_export",
    "selection_only",
    "actual_human_review_executed_by_person",
    "pause_abort_status_ref",
    "body_purge_required_on_abort",
    "body_purged_on_abort",
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
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP09_OPERATION_RECEIPT_REF: Final = (
    "post_pmn23_dmh_op09_actual_operation_receipt_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_OPERATION_RECEIPT_INTAKE_REF: Final = (
    "post_pmn23_dmh_op09_actual_operation_receipt_intake_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF: Final = (
    "actual_person_local_only_review_operation_receipt"
)
P7_R54_AHR_POST_PMN23_DMH_OP09_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op08_actual_review_operation_state_machine_ready_bodyfree",
    "actual_operation_receipt_received_bodyfree",
    "actual_source_ref_matches_actual_person_local_only_review_operation_receipt",
    "reviewer_and_24_case_counts_match_op08_state_capture",
    "operation_receipt_contains_no_body_question_path_hash_terminal_output",
    "sanitized_review_result_rows_intake_required_next_without_downstream_promotion",
)
P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_OPERATION_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "operation_receipt_ref",
    "review_session_id",
    "actual_review_basis_ref",
    "review_state_capture_ref",
    "reviewer_person_ref",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "review_started_bucket_ref",
    "review_completed_bucket_ref",
    "reviewed_case_count",
    "selection_row_count",
    "local_only",
    "must_not_export",
    "selection_only",
    "actual_source_ref",
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
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:9]
P7_R54_AHR_POST_PMN23_DMH_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[9:]
P7_R54_AHR_POST_PMN23_DMH_OP09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:10]
P7_R54_AHR_POST_PMN23_DMH_OP09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[10:]

P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op07_schema_version",
    "op07_material_ref",
    "op07_next_required_step",
    "op07_dmh_ready",
    "op07_reviewer_person_ref",
    "op07_reviewer_is_person",
    "op07_reviewer_person_confirmed",
    "op07_selection_only_form_ready",
    "op07_actual_review_operation_state_machine_allowed_next",
    "dmh_op08_status_ref",
    "dmh_op08_allowed_status_refs",
    "dmh_op08_ready",
    "dmh_op08_blocker_refs",
    "dmh_op08_blocker_ref_count",
    "dmh_op08_reason_refs",
    "dmh_op08_reason_ref_count",
    "review_operation_protocol_ref",
    "review_operation_protocol_bodyfree_only",
    "review_operation_protocol_step_refs",
    "review_operation_protocol_step_ref_count",
    "review_state_capture_received_here",
    "review_state_capture_intaked_here",
    "review_state_capture_schema_version",
    "review_state_capture_ref",
    "review_state_capture_required_field_refs",
    "review_state_capture_required_field_ref_count",
    "review_state_capture_forbidden_payload_key_paths",
    "review_state_capture_forbidden_payload_key_path_count",
    "review_state_capture_source_ref",
    "review_state_capture_source_ref_allowed",
    "review_state_capture_bodyfree_only",
    "review_state_ref",
    "review_state_allowed_refs",
    "review_state_is_completed_selection_rows_ready",
    "review_state_is_paused_local_only",
    "review_state_is_aborted_body_purged",
    "pause_abort_status_ref",
    "pause_abort_status_allowed_refs",
    "pause_abort_status_ref_allowed",
    "body_purge_required_on_abort",
    "body_purged_on_abort",
    "review_started_bucket_ref",
    "review_started_bucket_ref_present",
    "review_started_bucket_ref_is_bodyfree_ref",
    "review_started_bucket_ref_has_local_path_shape",
    "review_completed_bucket_ref",
    "review_completed_bucket_ref_present",
    "review_completed_bucket_ref_is_bodyfree_ref",
    "review_completed_bucket_ref_has_local_path_shape",
    "reviewer_person_ref",
    "reviewer_person_ref_present",
    "reviewer_person_ref_is_bodyfree_ref",
    "reviewer_person_ref_has_local_path_shape",
    "reviewer_person_ref_matches_op07",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "actual_human_review_executed_by_person",
    "reviewed_case_count",
    "required_reviewed_case_count",
    "reviewed_case_count_is_24",
    "selection_row_count",
    "required_selection_row_count",
    "selection_row_count_is_24",
    "local_only",
    "must_not_export",
    "selection_only",
    "operation_receipt_intake_allowed_next",
    "actual_operation_receipt_still_not_received",
    "actual_review_rows_still_not_created",
    "actual_disposal_purge_still_not_run",
    "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
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
    "dmh_op08_does_not_generate_body_full_packet_here",
    "dmh_op08_does_not_create_actual_operation_receipt_or_rows_or_disposal",
    "dmh_op08_does_not_start_p8_p6_r52_or_release",
    "dmh_op08_does_not_materialize_question_text",
    "dmh_op08_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op08_schema_version",
    "op08_material_ref",
    "op08_next_required_step",
    "op08_dmh_ready",
    "op08_review_state_ref",
    "op08_review_state_capture_ref",
    "op08_reviewer_person_ref",
    "op08_review_started_bucket_ref",
    "op08_review_completed_bucket_ref",
    "op08_reviewed_case_count",
    "op08_selection_row_count",
    "dmh_op09_status_ref",
    "dmh_op09_allowed_status_refs",
    "dmh_op09_ready",
    "dmh_op09_blocker_refs",
    "dmh_op09_blocker_ref_count",
    "dmh_op09_reason_refs",
    "dmh_op09_reason_ref_count",
    "operation_receipt_received_here",
    "operation_receipt_intaked_here",
    "operation_receipt_schema_version",
    "operation_receipt_intake_ref",
    "operation_receipt_required_field_refs",
    "operation_receipt_required_field_ref_count",
    "operation_receipt_forbidden_payload_key_paths",
    "operation_receipt_forbidden_payload_key_path_count",
    "operation_receipt_ref",
    "operation_receipt_ref_present",
    "operation_receipt_ref_is_bodyfree_ref",
    "operation_receipt_ref_has_local_path_shape",
    "review_state_capture_ref",
    "review_state_capture_ref_matches_op08",
    "reviewer_person_ref",
    "reviewer_person_ref_present",
    "reviewer_person_ref_is_bodyfree_ref",
    "reviewer_person_ref_has_local_path_shape",
    "reviewer_person_ref_matches_op08",
    "review_started_bucket_ref",
    "review_started_bucket_ref_present",
    "review_started_bucket_ref_is_bodyfree_ref",
    "review_started_bucket_ref_has_local_path_shape",
    "review_started_bucket_ref_matches_op08",
    "review_completed_bucket_ref",
    "review_completed_bucket_ref_present",
    "review_completed_bucket_ref_is_bodyfree_ref",
    "review_completed_bucket_ref_has_local_path_shape",
    "review_completed_bucket_ref_matches_op08",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "reviewed_case_count",
    "required_reviewed_case_count",
    "reviewed_case_count_is_24",
    "reviewed_case_count_matches_op08",
    "selection_row_count",
    "required_selection_row_count",
    "selection_row_count_is_24",
    "selection_row_count_matches_op08",
    "local_only",
    "must_not_export",
    "selection_only",
    "actual_source_ref",
    "actual_source_allowed_ref",
    "actual_source_guard_passed",
    "operation_receipt_bodyfree_only",
    "operation_receipt_confirms_actual_person_local_only_review",
    "actual_human_review_executed_by_person",
    "sanitized_review_result_rows_intake_required_next",
    "sanitized_review_result_rows_created_here",
    "rating_rows_created_here",
    "question_need_observation_rows_created_here",
    "disposal_receipt_created_here",
    "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_basis_ref",
    "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171",
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
    "dmh_op09_does_not_create_sanitized_rows_or_rating_rows_or_question_rows",
    "dmh_op09_does_not_create_disposal_receipt",
    "dmh_op09_does_not_start_p8_p6_r52_or_release",
    "dmh_op09_does_not_materialize_question_text",
    "dmh_op09_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "post_pmn23_no_touch_contract",
    "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dmh_op08_state_capture_blockers(op07: Mapping[str, Any] | None, state_capture: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op07, Mapping):
        return ["dmh_op08_reviewer_person_selection_only_form_missing"]
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization_contract(op07)
    except ValueError:
        blockers.append("dmh_op08_op07_reviewer_person_selection_only_form_invalid")
    if op07.get("dmh_op07_ready") is not True:
        blockers.append("dmh_op08_op07_reviewer_person_selection_only_form_not_ready")
    if op07.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF:
        blockers.append("dmh_op08_op07_next_step_not_actual_review_state_machine")
    if op07.get("actual_review_operation_state_machine_allowed_next") is not True:
        blockers.append("dmh_op08_op07_state_machine_not_allowed_next")
    if _scan_forbidden_payload_key_paths(op07):
        blockers.append("dmh_op08_op07_forbidden_body_question_path_hash_key_detected")

    if not isinstance(state_capture, Mapping):
        blockers.append("dmh_op08_review_lifecycle_state_capture_not_received")
        return list(dict.fromkeys(blockers))

    missing_fields = [field for field in P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_STATE_CAPTURE_FIELD_REFS if field not in state_capture]
    if missing_fields:
        blockers.append("dmh_op08_state_capture_required_fields_missing")
    if _scan_forbidden_payload_key_paths(state_capture):
        blockers.append("dmh_op08_state_capture_forbidden_body_question_path_hash_key_detected")
    if state_capture.get("body_free") is not True:
        blockers.append("dmh_op08_state_capture_not_bodyfree")
    if state_capture.get("actual_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append("dmh_op08_state_capture_actual_source_ref_not_allowed")
    if state_capture.get("review_session_id") != op07.get("review_session_id"):
        blockers.append("dmh_op08_state_capture_review_session_id_mismatch")
    if state_capture.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("dmh_op08_state_capture_actual_review_basis_ref_mismatch")
    reviewer_ref = _clean_ref(state_capture.get("reviewer_person_ref"), default="", max_length=180)
    if not reviewer_ref:
        blockers.append("dmh_op08_state_capture_reviewer_person_ref_missing")
    if reviewer_ref and _ref_has_local_path_shape(reviewer_ref):
        blockers.append("dmh_op08_state_capture_reviewer_person_ref_path_shape")
    if reviewer_ref and reviewer_ref != op07.get("reviewer_person_ref"):
        blockers.append("dmh_op08_state_capture_reviewer_person_ref_mismatch")
    if state_capture.get("reviewer_is_person") is not True:
        blockers.append("dmh_op08_state_capture_reviewer_is_person_not_true")
    if state_capture.get("reviewer_person_confirmed") is not True:
        blockers.append("dmh_op08_state_capture_reviewer_person_confirmed_not_true")
    if state_capture.get("reviewer_local_only_read_receipt_present") is not True:
        blockers.append("dmh_op08_state_capture_reviewer_local_only_read_receipt_missing")
    if state_capture.get("actual_human_review_executed_by_person") is not True:
        blockers.append("dmh_op08_state_capture_actual_human_review_executed_by_person_not_true")

    review_state_ref = _clean_ref(state_capture.get("review_state_ref"), default="", max_length=180)
    if review_state_ref not in P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_REVIEW_STATE_REFS:
        blockers.append("dmh_op08_state_capture_review_state_ref_not_allowed")
    pause_abort_status_ref = _clean_ref(state_capture.get("pause_abort_status_ref"), default="", max_length=180)
    if pause_abort_status_ref not in P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_PAUSE_ABORT_STATUS_REFS:
        blockers.append("dmh_op08_state_capture_pause_abort_status_ref_not_allowed")

    started_ref = _clean_ref(state_capture.get("review_started_bucket_ref"), default="", max_length=220)
    completed_ref = _clean_ref(state_capture.get("review_completed_bucket_ref"), default="", max_length=220)
    if not started_ref:
        blockers.append("dmh_op08_state_capture_review_started_bucket_ref_missing")
    if started_ref and _ref_has_local_path_shape(started_ref):
        blockers.append("dmh_op08_state_capture_review_started_bucket_ref_path_shape")
    if review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF:
        if not completed_ref:
            blockers.append("dmh_op08_state_capture_review_completed_bucket_ref_missing")
        if completed_ref and _ref_has_local_path_shape(completed_ref):
            blockers.append("dmh_op08_state_capture_review_completed_bucket_ref_path_shape")
        if pause_abort_status_ref != P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_NONE_REF:
            blockers.append("dmh_op08_state_capture_completed_state_pause_abort_status_not_none")
    elif review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF:
        blockers.append("dmh_op08_state_capture_review_state_paused_operation_receipt_not_allowed_yet")
        if pause_abort_status_ref != P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_PAUSED_REF:
            blockers.append("dmh_op08_state_capture_paused_state_pause_abort_status_mismatch")
    elif review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF:
        blockers.append("dmh_op08_state_capture_review_state_aborted_operation_receipt_not_allowed_yet")
        if pause_abort_status_ref != P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_ABORTED_PURGED_REF:
            blockers.append("dmh_op08_state_capture_aborted_state_pause_abort_status_mismatch")
        if state_capture.get("body_purge_required_on_abort") is not True:
            blockers.append("dmh_op08_state_capture_abort_body_purge_required_not_true")
        if state_capture.get("body_purged_on_abort") is not True:
            blockers.append("dmh_op08_state_capture_abort_body_purged_not_true")
    else:
        blockers.append("dmh_op08_state_capture_review_state_not_completed_selection_rows_ready")

    if _safe_int(state_capture.get("reviewed_case_count")) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op08_state_capture_reviewed_case_count_not_24")
    if _safe_int(state_capture.get("selection_row_count")) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op08_state_capture_selection_row_count_not_24")
    for true_key in ("local_only", "must_not_export", "selection_only"):
        if state_capture.get(true_key) is not True:
            blockers.append(f"dmh_op08_state_capture_{true_key}_not_true")
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
    ):
        if state_capture.get(false_key) is not False:
            blockers.append(f"dmh_op08_state_capture_{false_key}_not_false")
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
            blockers.append(f"dmh_op08_state_capture_{source_flag}_cannot_be_actual")
    return list(dict.fromkeys(blockers))


def _dmh_op08_status_for_blockers(blockers: Sequence[str], review_state_ref: str) -> str:
    if not blockers:
        return P7_R54_AHR_POST_PMN23_DMH_OP08_READY_STATUS_REF
    leak_fragments = ("body", "question", "path", "hash", "terminal", "stdout", "stderr", "traceback")
    if any(any(fragment in blocker for fragment in leak_fragments) for blocker in blockers):
        return P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_BY_LEAK_STATUS_REF
    if review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF:
        return P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_STATUS_REF
    if review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF:
        return P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_STATUS_REF
    return P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_STATUS_REF


def _dmh_op08_next_step_for_status(status_ref: str) -> str:
    if status_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_READY_STATUS_REF:
        return P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF
    if status_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_STATUS_REF:
        return P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_NEXT_REQUIRED_STEP_REF
    if status_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_STATUS_REF:
        return P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_NEXT_REQUIRED_STEP_REF
    return P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF


def build_p7_r54_ahr_post_pmn23_dmh_op08_review_lifecycle_state_capture_bodyfree(
    *,
    review_session_id: Any = None,
    reviewer_person_ref: Any = None,
    review_state_ref: Any = None,
    reviewed_case_count: Any = None,
    selection_row_count: Any = None,
    pause_abort_status_ref: Any = None,
) -> dict[str, Any]:
    """Build body-free supplied review lifecycle state capture material for DMH-OP08."""

    state_ref = _clean_ref(
        review_state_ref,
        default=P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF,
        max_length=180,
    )
    pause_ref_default = (
        P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_PAUSED_REF
        if state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF
        else P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_ABORTED_PURGED_REF
        if state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF
        else P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_NONE_REF
    )
    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_LIFECYCLE_STATE_CAPTURE_SCHEMA_VERSION,
        "review_state_capture_ref": P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_CAPTURE_REF,
        "review_session_id": session_id,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_source_ref": P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_ACTUAL_SOURCE_REF,
        "reviewer_person_ref": _clean_ref(
            reviewer_person_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF,
            max_length=180,
        ),
        "reviewer_is_person": True,
        "reviewer_person_confirmed": True,
        "reviewer_local_only_read_receipt_present": True,
        "review_state_ref": state_ref,
        "review_started_bucket_ref": P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STARTED_BUCKET_REF,
        "review_completed_bucket_ref": P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_COMPLETED_BUCKET_REF,
        "reviewed_case_count": _safe_int(reviewed_case_count, default=P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT),
        "selection_row_count": _safe_int(selection_row_count, default=P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT),
        "local_only": True,
        "must_not_export": True,
        "selection_only": True,
        "actual_human_review_executed_by_person": True,
        "pause_abort_status_ref": _clean_ref(pause_abort_status_ref, default=pause_ref_default, max_length=180),
        "body_purge_required_on_abort": state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF,
        "body_purged_on_abort": state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF,
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
        "body_free": True,
    }


def build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
    *,
    reviewer_person_confirmation_selection_only_form_finalization: Mapping[str, Any] | None = None,
    review_lifecycle_state_capture_bodyfree: Mapping[str, Any] | None = None,
    packet_completeness_export_denylist_scan_receipt_boundary: Mapping[str, Any] | None = None,
    reviewer_person_confirmation_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP08 body-free actual review operation state-machine material."""

    session_id = _safe_review_session_id(review_session_id)
    op07 = reviewer_person_confirmation_selection_only_form_finalization
    if op07 is None:
        op07 = build_p7_r54_ahr_post_pmn23_dmh_op07_reviewer_person_confirmation_selection_only_form_finalization(
            packet_completeness_export_denylist_scan_receipt_boundary=packet_completeness_export_denylist_scan_receipt_boundary,
            reviewer_person_confirmation_receipt_bodyfree=reviewer_person_confirmation_receipt_bodyfree,
            review_session_id=session_id,
        )
    blockers = _dmh_op08_state_capture_blockers(op07, review_lifecycle_state_capture_bodyfree)
    state_received = isinstance(review_lifecycle_state_capture_bodyfree, Mapping)
    state = review_lifecycle_state_capture_bodyfree or {}
    review_state_ref = _clean_ref(state.get("review_state_ref") if state_received else "", default="", max_length=180)
    status_ref = _dmh_op08_status_for_blockers(blockers, review_state_ref)
    ready = status_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_READY_STATUS_REF
    reason_refs = list(P7_R54_AHR_POST_PMN23_DMH_OP08_READY_REASON_REFS) if ready else blockers
    reviewer_ref = _clean_ref(
        state.get("reviewer_person_ref") if state_received else op07.get("reviewer_person_ref") if isinstance(op07, Mapping) else "",
        default="",
        max_length=180,
    )
    started_ref = _clean_ref(state.get("review_started_bucket_ref") if state_received else "", default="", max_length=220)
    completed_ref = _clean_ref(state.get("review_completed_bucket_ref") if state_received else "", default="", max_length=220)
    reviewed_count = _safe_int(state.get("reviewed_case_count") if state_received else 0)
    selection_count = _safe_int(state.get("selection_row_count") if state_received else 0)
    implemented_steps = P7_R54_AHR_POST_PMN23_DMH_OP08_IMPLEMENTED_STEPS if ready else tuple(op07.get("implemented_steps") or P7_R54_AHR_POST_PMN23_DMH_OP07_IMPLEMENTED_STEPS) if isinstance(op07, Mapping) else P7_R54_AHR_POST_PMN23_DMH_OP06_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_PMN23_DMH_OP08_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op07.get("not_yet_implemented_steps") or P7_R54_AHR_POST_PMN23_DMH_OP07_NOT_YET_IMPLEMENTED_STEPS) if isinstance(op07, Mapping) else P7_R54_AHR_POST_PMN23_DMH_OP06_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP08_ACTUAL_REVIEW_OPERATION_STATE_MACHINE_PAUSE_ABORT_LIFECYCLE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_20260702",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_schema_version": _clean_ref(op07.get("schema_version") if isinstance(op07, Mapping) else "", default="op07_schema_missing", max_length=220),
        "op07_material_ref": _clean_ref(op07.get("material_id") if isinstance(op07, Mapping) else "", default="op07_material_missing", max_length=220),
        "op07_next_required_step": _clean_ref(op07.get("next_required_step") if isinstance(op07, Mapping) else "", default="op07_next_required_step_missing", max_length=220),
        "op07_dmh_ready": bool(isinstance(op07, Mapping) and op07.get("dmh_op07_ready") is True),
        "op07_reviewer_person_ref": _clean_ref(op07.get("reviewer_person_ref") if isinstance(op07, Mapping) else "", default="", max_length=180),
        "op07_reviewer_is_person": bool(isinstance(op07, Mapping) and op07.get("reviewer_is_person") is True),
        "op07_reviewer_person_confirmed": bool(isinstance(op07, Mapping) and op07.get("reviewer_person_confirmed") is True),
        "op07_selection_only_form_ready": bool(isinstance(op07, Mapping) and op07.get("selection_only_form_ready") is True),
        "op07_actual_review_operation_state_machine_allowed_next": bool(isinstance(op07, Mapping) and op07.get("actual_review_operation_state_machine_allowed_next") is True),
        "dmh_op08_status_ref": status_ref,
        "dmh_op08_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_STATUS_REFS),
        "dmh_op08_ready": ready,
        "dmh_op08_blocker_refs": blockers,
        "dmh_op08_blocker_ref_count": len(blockers),
        "dmh_op08_reason_refs": reason_refs,
        "dmh_op08_reason_ref_count": len(reason_refs),
        "review_operation_protocol_ref": P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_CAPTURE_REF if ready else "",
        "review_operation_protocol_bodyfree_only": True,
        "review_operation_protocol_step_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP08_PROTOCOL_STEP_REFS),
        "review_operation_protocol_step_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP08_PROTOCOL_STEP_REFS),
        "review_state_capture_received_here": state_received,
        "review_state_capture_intaked_here": ready,
        "review_state_capture_schema_version": _clean_ref(state.get("schema_version") if state_received else "", default="", max_length=220),
        "review_state_capture_ref": _clean_ref(state.get("review_state_capture_ref") if state_received else "", default="", max_length=220),
        "review_state_capture_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_STATE_CAPTURE_FIELD_REFS),
        "review_state_capture_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_STATE_CAPTURE_FIELD_REFS),
        "review_state_capture_forbidden_payload_key_paths": _scan_forbidden_payload_key_paths(state, path="review_lifecycle_state_capture") if state_received else [],
        "review_state_capture_forbidden_payload_key_path_count": len(_scan_forbidden_payload_key_paths(state, path="review_lifecycle_state_capture")) if state_received else 0,
        "review_state_capture_source_ref": _clean_ref(state.get("actual_source_ref") if state_received else "", default="", max_length=220),
        "review_state_capture_source_ref_allowed": bool(state_received and state.get("actual_source_ref") == P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_ACTUAL_SOURCE_REF),
        "review_state_capture_bodyfree_only": bool(state_received and state.get("body_free") is True),
        "review_state_ref": review_state_ref,
        "review_state_allowed_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_REVIEW_STATE_REFS),
        "review_state_is_completed_selection_rows_ready": review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF,
        "review_state_is_paused_local_only": review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_PAUSED_REF,
        "review_state_is_aborted_body_purged": review_state_ref == P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_ABORTED_REF,
        "pause_abort_status_ref": _clean_ref(state.get("pause_abort_status_ref") if state_received else "", default="", max_length=180),
        "pause_abort_status_allowed_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_PAUSE_ABORT_STATUS_REFS),
        "pause_abort_status_ref_allowed": bool(state_received and state.get("pause_abort_status_ref") in P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_PAUSE_ABORT_STATUS_REFS),
        "body_purge_required_on_abort": bool(state_received and state.get("body_purge_required_on_abort") is True),
        "body_purged_on_abort": bool(state_received and state.get("body_purged_on_abort") is True),
        "review_started_bucket_ref": started_ref,
        "review_started_bucket_ref_present": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_bucket_ref_is_bodyfree_ref": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(started_ref),
        "review_completed_bucket_ref": completed_ref,
        "review_completed_bucket_ref_present": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_bucket_ref_is_bodyfree_ref": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(completed_ref),
        "reviewer_person_ref": reviewer_ref,
        "reviewer_person_ref_present": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_is_bodyfree_ref": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_has_local_path_shape": _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_matches_op07": bool(isinstance(op07, Mapping) and reviewer_ref == op07.get("reviewer_person_ref")),
        "reviewer_is_person": bool(ready and state.get("reviewer_is_person") is True),
        "reviewer_person_confirmed": bool(ready and state.get("reviewer_person_confirmed") is True),
        "reviewer_local_only_read_receipt_present": bool(ready and state.get("reviewer_local_only_read_receipt_present") is True),
        "actual_human_review_executed_by_person": ready,
        "reviewed_case_count": reviewed_count,
        "required_reviewed_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "reviewed_case_count_is_24": reviewed_count == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "selection_row_count": selection_count,
        "required_selection_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "selection_row_count_is_24": selection_count == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "local_only": bool(ready and state.get("local_only") is True),
        "must_not_export": bool(ready and state.get("must_not_export") is True),
        "selection_only": bool(ready and state.get("selection_only") is True),
        "operation_receipt_intake_allowed_next": ready,
        "actual_operation_receipt_still_not_received": True,
        "actual_review_rows_still_not_created": True,
        "actual_disposal_purge_still_not_run": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
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
        "dmh_op08_does_not_generate_body_full_packet_here": True,
        "dmh_op08_does_not_create_actual_operation_receipt_or_rows_or_disposal": True,
        "dmh_op08_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op08_does_not_materialize_question_text": True,
        "dmh_op08_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": _dmh_op08_next_step_for_status(status_ref),
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(
    data: Mapping[str, Any]
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP08 actual review operation state machine")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP08_ACTUAL_REVIEW_OPERATION_STATE_MACHINE_PAUSE_ABORT_LIFECYCLE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP08 actual review operation state machine",
    )
    blockers = list(data.get("dmh_op08_blocker_refs") or [])
    expected_status = _dmh_op08_status_for_blockers(blockers, str(data.get("review_state_ref") or ""))
    if data.get("dmh_op08_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 status changed")
    ready = data.get("dmh_op08_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP08_READY_STATUS_REF
    if data.get("dmh_op08_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 ready flag changed")
    if tuple(data.get("dmh_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 allowed statuses changed")
    for count_field, list_field in (
        ("dmh_op08_blocker_ref_count", "dmh_op08_blocker_refs"),
        ("dmh_op08_reason_ref_count", "dmh_op08_reason_refs"),
        ("review_operation_protocol_step_ref_count", "review_operation_protocol_step_refs"),
        ("review_state_capture_required_field_ref_count", "review_state_capture_required_field_refs"),
        ("review_state_capture_forbidden_payload_key_path_count", "review_state_capture_forbidden_payload_key_paths"),
    ):
        if data.get(count_field) != len(data.get(list_field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP08 {count_field} changed")
    for key in (
        "review_operation_protocol_bodyfree_only",
        "actual_operation_receipt_still_not_received",
        "actual_review_rows_still_not_created",
        "actual_disposal_purge_still_not_run",
        "actual_review_evidence_complete_from_real_review_still_false",
        "current_actual_review_basis_remains_264_85_258_171",
        "dmh_op08_does_not_generate_body_full_packet_here",
        "dmh_op08_does_not_create_actual_operation_receipt_or_rows_or_disposal",
        "dmh_op08_does_not_start_p8_p6_r52_or_release",
        "dmh_op08_does_not_materialize_question_text",
        "dmh_op08_does_not_execute_postcr22_ex_reentry",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP08 required true field changed: {key}")
    for key in (
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
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP08 leak marker promoted: {key}")
    if tuple(data.get("review_state_capture_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP08_REQUIRED_STATE_CAPTURE_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 state capture required fields changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 actual review basis changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 not claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 not claimed boundary must stay false")
    if ready:
        for key in (
            "op07_dmh_ready",
            "op07_reviewer_is_person",
            "op07_reviewer_person_confirmed",
            "op07_selection_only_form_ready",
            "op07_actual_review_operation_state_machine_allowed_next",
            "review_state_capture_received_here",
            "review_state_capture_intaked_here",
            "review_state_capture_source_ref_allowed",
            "review_state_capture_bodyfree_only",
            "review_state_is_completed_selection_rows_ready",
            "pause_abort_status_ref_allowed",
            "review_started_bucket_ref_present",
            "review_started_bucket_ref_is_bodyfree_ref",
            "review_completed_bucket_ref_present",
            "review_completed_bucket_ref_is_bodyfree_ref",
            "reviewer_person_ref_present",
            "reviewer_person_ref_is_bodyfree_ref",
            "reviewer_person_ref_matches_op07",
            "reviewer_is_person",
            "reviewer_person_confirmed",
            "reviewer_local_only_read_receipt_present",
            "actual_human_review_executed_by_person",
            "reviewed_case_count_is_24",
            "selection_row_count_is_24",
            "local_only",
            "must_not_export",
            "selection_only",
            "operation_receipt_intake_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP08 ready field changed: {key}")
        if data.get("op07_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 ready requires OP07 next step")
        if data.get("review_state_capture_schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_LIFECYCLE_STATE_CAPTURE_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 state capture schema changed")
        if data.get("review_state_capture_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP08_ALLOWED_ACTUAL_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 actual source changed")
        if data.get("review_state_ref") != P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 ready review state changed")
        if data.get("pause_abort_status_ref") != P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSE_ABORT_NONE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 ready pause/abort status changed")
        if data.get("reviewed_case_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT or data.get("selection_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 ready counts changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP08_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 next step changed")
    else:
        if data.get("review_state_capture_intaked_here") is not False or data.get("operation_receipt_intake_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 blocked lifecycle promoted operation receipt intake")
        if data.get("actual_human_review_executed_by_person") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 blocked lifecycle promoted human review execution")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 blocked lifecycle must carry blockers")
        if data.get("dmh_op08_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_STATUS_REF and data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 paused next step changed")
        if data.get("dmh_op08_status_ref") == P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_STATUS_REF and data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 aborted next step changed")
        if data.get("dmh_op08_status_ref") not in (P7_R54_AHR_POST_PMN23_DMH_OP08_PAUSED_STATUS_REF, P7_R54_AHR_POST_PMN23_DMH_OP08_ABORTED_STATUS_REF) and data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP08 blocked next step changed")
    return True


def _dmh_op09_operation_receipt_blockers(op08: Mapping[str, Any] | None, receipt: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op08, Mapping):
        return ["dmh_op09_actual_review_operation_state_machine_missing"]
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract(op08)
    except ValueError:
        blockers.append("dmh_op09_op08_actual_review_operation_state_machine_invalid")
    if op08.get("dmh_op08_ready") is not True:
        blockers.append("dmh_op09_op08_actual_review_operation_state_machine_not_ready")
    if op08.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF:
        blockers.append("dmh_op09_op08_next_step_not_actual_operation_receipt_intake")
    if op08.get("operation_receipt_intake_allowed_next") is not True:
        blockers.append("dmh_op09_op08_operation_receipt_intake_not_allowed_next")
    if _scan_forbidden_payload_key_paths(op08):
        blockers.append("dmh_op09_op08_forbidden_body_question_path_hash_key_detected")

    if not isinstance(receipt, Mapping):
        blockers.append("dmh_op09_actual_operation_receipt_not_received")
        return list(dict.fromkeys(blockers))

    missing_fields = [field for field in P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_OPERATION_RECEIPT_FIELD_REFS if field not in receipt]
    if missing_fields:
        blockers.append("dmh_op09_operation_receipt_required_fields_missing")
    if _scan_forbidden_payload_key_paths(receipt):
        blockers.append("dmh_op09_operation_receipt_forbidden_body_question_path_hash_key_detected")
    if receipt.get("body_free") is not True:
        blockers.append("dmh_op09_operation_receipt_not_bodyfree")
    if receipt.get("actual_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append("dmh_op09_operation_receipt_actual_source_ref_not_allowed")
    if receipt.get("review_session_id") != op08.get("review_session_id"):
        blockers.append("dmh_op09_operation_receipt_review_session_id_mismatch")
    if receipt.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF:
        blockers.append("dmh_op09_operation_receipt_actual_review_basis_ref_mismatch")
    receipt_ref = _clean_ref(receipt.get("operation_receipt_ref"), default="", max_length=220)
    if not receipt_ref:
        blockers.append("dmh_op09_operation_receipt_ref_missing")
    if receipt_ref and _ref_has_local_path_shape(receipt_ref):
        blockers.append("dmh_op09_operation_receipt_ref_path_shape")
    if receipt.get("review_state_capture_ref") != op08.get("review_state_capture_ref"):
        blockers.append("dmh_op09_operation_receipt_review_state_capture_ref_mismatch")
    reviewer_ref = _clean_ref(receipt.get("reviewer_person_ref"), default="", max_length=180)
    if not reviewer_ref:
        blockers.append("dmh_op09_operation_receipt_reviewer_person_ref_missing")
    if reviewer_ref and _ref_has_local_path_shape(reviewer_ref):
        blockers.append("dmh_op09_operation_receipt_reviewer_person_ref_path_shape")
    if reviewer_ref and reviewer_ref != op08.get("reviewer_person_ref"):
        blockers.append("dmh_op09_operation_receipt_reviewer_person_ref_mismatch")
    for flag in ("reviewer_is_person", "reviewer_person_confirmed", "reviewer_local_only_read_receipt_present"):
        if receipt.get(flag) is not True:
            blockers.append(f"dmh_op09_operation_receipt_{flag}_not_true")
    started_ref = _clean_ref(receipt.get("review_started_bucket_ref"), default="", max_length=220)
    completed_ref = _clean_ref(receipt.get("review_completed_bucket_ref"), default="", max_length=220)
    if not started_ref:
        blockers.append("dmh_op09_operation_receipt_review_started_bucket_ref_missing")
    if started_ref and _ref_has_local_path_shape(started_ref):
        blockers.append("dmh_op09_operation_receipt_review_started_bucket_ref_path_shape")
    if started_ref and started_ref != op08.get("review_started_bucket_ref"):
        blockers.append("dmh_op09_operation_receipt_review_started_bucket_ref_mismatch")
    if not completed_ref:
        blockers.append("dmh_op09_operation_receipt_review_completed_bucket_ref_missing")
    if completed_ref and _ref_has_local_path_shape(completed_ref):
        blockers.append("dmh_op09_operation_receipt_review_completed_bucket_ref_path_shape")
    if completed_ref and completed_ref != op08.get("review_completed_bucket_ref"):
        blockers.append("dmh_op09_operation_receipt_review_completed_bucket_ref_mismatch")
    if _safe_int(receipt.get("reviewed_case_count")) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op09_operation_receipt_reviewed_case_count_not_24")
    if _safe_int(receipt.get("reviewed_case_count")) != op08.get("reviewed_case_count"):
        blockers.append("dmh_op09_operation_receipt_reviewed_case_count_mismatch")
    if _safe_int(receipt.get("selection_row_count")) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op09_operation_receipt_selection_row_count_not_24")
    if _safe_int(receipt.get("selection_row_count")) != op08.get("selection_row_count"):
        blockers.append("dmh_op09_operation_receipt_selection_row_count_mismatch")
    for true_key in ("local_only", "must_not_export", "selection_only"):
        if receipt.get(true_key) is not True:
            blockers.append(f"dmh_op09_operation_receipt_{true_key}_not_true")
    for false_key in (
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
    ):
        if receipt.get(false_key) is not False:
            blockers.append(f"dmh_op09_operation_receipt_{false_key}_not_false")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_bodyfree(
    *,
    review_session_id: Any = None,
    review_state_capture_ref: Any = None,
    reviewer_person_ref: Any = None,
    review_started_bucket_ref: Any = None,
    review_completed_bucket_ref: Any = None,
    reviewed_case_count: Any = None,
    selection_row_count: Any = None,
) -> dict[str, Any]:
    """Build body-free supplied actual operation receipt material for DMH-OP09."""

    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION,
        "operation_receipt_ref": P7_R54_AHR_POST_PMN23_DMH_OP09_OPERATION_RECEIPT_REF,
        "review_session_id": _safe_review_session_id(review_session_id),
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "review_state_capture_ref": _clean_ref(
            review_state_capture_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_CAPTURE_REF,
            max_length=220,
        ),
        "reviewer_person_ref": _clean_ref(
            reviewer_person_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF,
            max_length=180,
        ),
        "reviewer_is_person": True,
        "reviewer_person_confirmed": True,
        "reviewer_local_only_read_receipt_present": True,
        "review_started_bucket_ref": _clean_ref(
            review_started_bucket_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STARTED_BUCKET_REF,
            max_length=220,
        ),
        "review_completed_bucket_ref": _clean_ref(
            review_completed_bucket_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_COMPLETED_BUCKET_REF,
            max_length=220,
        ),
        "reviewed_case_count": _safe_int(reviewed_case_count, default=P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT),
        "selection_row_count": _safe_int(selection_row_count, default=P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT),
        "local_only": True,
        "must_not_export": True,
        "selection_only": True,
        "actual_source_ref": P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF,
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
        "body_free": True,
    }


def build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake(
    *,
    actual_review_operation_state_machine_pause_abort_lifecycle: Mapping[str, Any] | None = None,
    actual_operation_receipt_bodyfree: Mapping[str, Any] | None = None,
    reviewer_person_confirmation_selection_only_form_finalization: Mapping[str, Any] | None = None,
    review_lifecycle_state_capture_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP09 body-free actual operation receipt intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op08 = actual_review_operation_state_machine_pause_abort_lifecycle
    if op08 is None:
        op08 = build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle(
            reviewer_person_confirmation_selection_only_form_finalization=reviewer_person_confirmation_selection_only_form_finalization,
            review_lifecycle_state_capture_bodyfree=review_lifecycle_state_capture_bodyfree,
            review_session_id=session_id,
        )
    blockers = _dmh_op09_operation_receipt_blockers(op08, actual_operation_receipt_bodyfree)
    receipt_received = isinstance(actual_operation_receipt_bodyfree, Mapping)
    leak_fragments = ("body", "question", "path", "hash", "terminal", "stdout", "stderr", "traceback")
    leak_detected = bool(
        receipt_received
        and (
            _scan_forbidden_payload_key_paths(actual_operation_receipt_bodyfree)
            or any(any(fragment in blocker for fragment in leak_fragments) for blocker in blockers)
        )
    )
    ready = not blockers
    status_ref = (
        P7_R54_AHR_POST_PMN23_DMH_OP09_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_BY_LEAK_STATUS_REF
        if leak_detected
        else P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_STATUS_REF
    )
    reason_refs = list(P7_R54_AHR_POST_PMN23_DMH_OP09_READY_REASON_REFS) if ready else blockers
    receipt = actual_operation_receipt_bodyfree or {}
    receipt_ref = _clean_ref(receipt.get("operation_receipt_ref") if receipt_received else "", default="", max_length=220)
    reviewer_ref = _clean_ref(receipt.get("reviewer_person_ref") if receipt_received else op08.get("reviewer_person_ref") if isinstance(op08, Mapping) else "", default="", max_length=180)
    state_capture_ref = _clean_ref(receipt.get("review_state_capture_ref") if receipt_received else "", default="", max_length=220)
    started_ref = _clean_ref(receipt.get("review_started_bucket_ref") if receipt_received else "", default="", max_length=220)
    completed_ref = _clean_ref(receipt.get("review_completed_bucket_ref") if receipt_received else "", default="", max_length=220)
    reviewed_count = _safe_int(receipt.get("reviewed_case_count") if receipt_received else 0)
    selection_count = _safe_int(receipt.get("selection_row_count") if receipt_received else 0)
    implemented_steps = P7_R54_AHR_POST_PMN23_DMH_OP09_IMPLEMENTED_STEPS if ready else tuple(op08.get("implemented_steps") or P7_R54_AHR_POST_PMN23_DMH_OP08_IMPLEMENTED_STEPS) if isinstance(op08, Mapping) else P7_R54_AHR_POST_PMN23_DMH_OP07_IMPLEMENTED_STEPS
    not_yet_steps = P7_R54_AHR_POST_PMN23_DMH_OP09_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(op08.get("not_yet_implemented_steps") or P7_R54_AHR_POST_PMN23_DMH_OP08_NOT_YET_IMPLEMENTED_STEPS) if isinstance(op08, Mapping) else P7_R54_AHR_POST_PMN23_DMH_OP07_NOT_YET_IMPLEMENTED_STEPS
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_20260702",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op08_schema_version": _clean_ref(op08.get("schema_version") if isinstance(op08, Mapping) else "", default="op08_schema_missing", max_length=220),
        "op08_material_ref": _clean_ref(op08.get("material_id") if isinstance(op08, Mapping) else "", default="op08_material_missing", max_length=220),
        "op08_next_required_step": _clean_ref(op08.get("next_required_step") if isinstance(op08, Mapping) else "", default="op08_next_required_step_missing", max_length=220),
        "op08_dmh_ready": bool(isinstance(op08, Mapping) and op08.get("dmh_op08_ready") is True),
        "op08_review_state_ref": _clean_ref(op08.get("review_state_ref") if isinstance(op08, Mapping) else "", default="", max_length=180),
        "op08_review_state_capture_ref": _clean_ref(op08.get("review_state_capture_ref") if isinstance(op08, Mapping) else "", default="", max_length=220),
        "op08_reviewer_person_ref": _clean_ref(op08.get("reviewer_person_ref") if isinstance(op08, Mapping) else "", default="", max_length=180),
        "op08_review_started_bucket_ref": _clean_ref(op08.get("review_started_bucket_ref") if isinstance(op08, Mapping) else "", default="", max_length=220),
        "op08_review_completed_bucket_ref": _clean_ref(op08.get("review_completed_bucket_ref") if isinstance(op08, Mapping) else "", default="", max_length=220),
        "op08_reviewed_case_count": _safe_int(op08.get("reviewed_case_count") if isinstance(op08, Mapping) else 0),
        "op08_selection_row_count": _safe_int(op08.get("selection_row_count") if isinstance(op08, Mapping) else 0),
        "dmh_op09_status_ref": status_ref,
        "dmh_op09_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_STATUS_REFS),
        "dmh_op09_ready": ready,
        "dmh_op09_blocker_refs": blockers,
        "dmh_op09_blocker_ref_count": len(blockers),
        "dmh_op09_reason_refs": reason_refs,
        "dmh_op09_reason_ref_count": len(reason_refs),
        "operation_receipt_received_here": receipt_received,
        "operation_receipt_intaked_here": ready,
        "operation_receipt_schema_version": _clean_ref(receipt.get("schema_version") if receipt_received else "", default="", max_length=220),
        "operation_receipt_intake_ref": P7_R54_AHR_POST_PMN23_DMH_OP09_OPERATION_RECEIPT_INTAKE_REF if ready else "",
        "operation_receipt_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_OPERATION_RECEIPT_FIELD_REFS),
        "operation_receipt_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_OPERATION_RECEIPT_FIELD_REFS),
        "operation_receipt_forbidden_payload_key_paths": _scan_forbidden_payload_key_paths(receipt, path="actual_operation_receipt") if receipt_received else [],
        "operation_receipt_forbidden_payload_key_path_count": len(_scan_forbidden_payload_key_paths(receipt, path="actual_operation_receipt")) if receipt_received else 0,
        "operation_receipt_ref": receipt_ref,
        "operation_receipt_ref_present": bool(receipt_ref) and not _ref_has_local_path_shape(receipt_ref),
        "operation_receipt_ref_is_bodyfree_ref": bool(receipt_ref) and not _ref_has_local_path_shape(receipt_ref),
        "operation_receipt_ref_has_local_path_shape": _ref_has_local_path_shape(receipt_ref),
        "review_state_capture_ref": state_capture_ref,
        "review_state_capture_ref_matches_op08": bool(isinstance(op08, Mapping) and state_capture_ref == op08.get("review_state_capture_ref")),
        "reviewer_person_ref": reviewer_ref,
        "reviewer_person_ref_present": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_is_bodyfree_ref": bool(reviewer_ref) and not _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_has_local_path_shape": _ref_has_local_path_shape(reviewer_ref),
        "reviewer_person_ref_matches_op08": bool(isinstance(op08, Mapping) and reviewer_ref == op08.get("reviewer_person_ref")),
        "review_started_bucket_ref": started_ref,
        "review_started_bucket_ref_present": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_bucket_ref_is_bodyfree_ref": bool(started_ref) and not _ref_has_local_path_shape(started_ref),
        "review_started_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(started_ref),
        "review_started_bucket_ref_matches_op08": bool(isinstance(op08, Mapping) and started_ref == op08.get("review_started_bucket_ref")),
        "review_completed_bucket_ref": completed_ref,
        "review_completed_bucket_ref_present": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_bucket_ref_is_bodyfree_ref": bool(completed_ref) and not _ref_has_local_path_shape(completed_ref),
        "review_completed_bucket_ref_has_local_path_shape": _ref_has_local_path_shape(completed_ref),
        "review_completed_bucket_ref_matches_op08": bool(isinstance(op08, Mapping) and completed_ref == op08.get("review_completed_bucket_ref")),
        "reviewer_is_person": bool(ready and receipt.get("reviewer_is_person") is True),
        "reviewer_person_confirmed": bool(ready and receipt.get("reviewer_person_confirmed") is True),
        "reviewer_local_only_read_receipt_present": bool(ready and receipt.get("reviewer_local_only_read_receipt_present") is True),
        "reviewed_case_count": reviewed_count,
        "required_reviewed_case_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "reviewed_case_count_is_24": reviewed_count == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "reviewed_case_count_matches_op08": bool(isinstance(op08, Mapping) and reviewed_count == op08.get("reviewed_case_count")),
        "selection_row_count": selection_count,
        "required_selection_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "selection_row_count_is_24": selection_count == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "selection_row_count_matches_op08": bool(isinstance(op08, Mapping) and selection_count == op08.get("selection_row_count")),
        "local_only": bool(ready and receipt.get("local_only") is True),
        "must_not_export": bool(ready and receipt.get("must_not_export") is True),
        "selection_only": bool(ready and receipt.get("selection_only") is True),
        "actual_source_ref": _clean_ref(receipt.get("actual_source_ref") if receipt_received else "", default="", max_length=220),
        "actual_source_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF,
        "actual_source_guard_passed": bool(receipt_received and receipt.get("actual_source_ref") == P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF),
        "operation_receipt_bodyfree_only": True,
        "operation_receipt_confirms_actual_person_local_only_review": ready,
        "actual_human_review_executed_by_person": ready,
        "sanitized_review_result_rows_intake_required_next": ready,
        "sanitized_review_result_rows_created_here": False,
        "rating_rows_created_here": False,
        "question_need_observation_rows_created_here": False,
        "disposal_receipt_created_here": False,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
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
        "dmh_op09_does_not_create_sanitized_rows_or_rating_rows_or_question_rows": True,
        "dmh_op09_does_not_create_disposal_receipt": True,
        "dmh_op09_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op09_does_not_materialize_question_text": True,
        "dmh_op09_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP09 actual operation receipt intake")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP09 actual operation receipt intake",
    )
    blockers = list(data.get("dmh_op09_blocker_refs") or [])
    leak_fragments = ("body", "question", "path", "hash", "terminal", "stdout", "stderr", "traceback")
    leak_detected = any(any(fragment in blocker for fragment in leak_fragments) for blocker in blockers)
    expected_status = P7_R54_AHR_POST_PMN23_DMH_OP09_READY_STATUS_REF if not blockers else P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_BY_LEAK_STATUS_REF if leak_detected else P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_STATUS_REF
    if data.get("dmh_op09_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 status changed")
    ready = not blockers
    if data.get("dmh_op09_ready") is not ready:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 ready flag changed")
    if tuple(data.get("dmh_op09_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 allowed statuses changed")
    for count_field, list_field in (
        ("dmh_op09_blocker_ref_count", "dmh_op09_blocker_refs"),
        ("dmh_op09_reason_ref_count", "dmh_op09_reason_refs"),
        ("operation_receipt_required_field_ref_count", "operation_receipt_required_field_refs"),
        ("operation_receipt_forbidden_payload_key_path_count", "operation_receipt_forbidden_payload_key_paths"),
    ):
        if data.get(count_field) != len(data.get(list_field) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP09 {count_field} changed")
    for key in (
        "operation_receipt_bodyfree_only",
        "actual_review_evidence_complete_from_real_review_still_false",
        "current_actual_review_basis_remains_264_85_258_171",
        "dmh_op09_does_not_create_sanitized_rows_or_rating_rows_or_question_rows",
        "dmh_op09_does_not_create_disposal_receipt",
        "dmh_op09_does_not_start_p8_p6_r52_or_release",
        "dmh_op09_does_not_materialize_question_text",
        "dmh_op09_does_not_execute_postcr22_ex_reentry",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP09 required true field changed: {key}")
    for key in (
        "sanitized_review_result_rows_created_here",
        "rating_rows_created_here",
        "question_need_observation_rows_created_here",
        "disposal_receipt_created_here",
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
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP09 leak/promotion marker changed: {key}")
    if tuple(data.get("operation_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP09_REQUIRED_OPERATION_RECEIPT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 required receipt fields changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 actual review basis changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 not claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 not claimed boundary must stay false")
    if ready:
        for key in (
            "op08_dmh_ready",
            "operation_receipt_received_here",
            "operation_receipt_intaked_here",
            "operation_receipt_ref_present",
            "operation_receipt_ref_is_bodyfree_ref",
            "review_state_capture_ref_matches_op08",
            "reviewer_person_ref_present",
            "reviewer_person_ref_is_bodyfree_ref",
            "reviewer_person_ref_matches_op08",
            "review_started_bucket_ref_present",
            "review_started_bucket_ref_is_bodyfree_ref",
            "review_started_bucket_ref_matches_op08",
            "review_completed_bucket_ref_present",
            "review_completed_bucket_ref_is_bodyfree_ref",
            "review_completed_bucket_ref_matches_op08",
            "reviewer_is_person",
            "reviewer_person_confirmed",
            "reviewer_local_only_read_receipt_present",
            "reviewed_case_count_is_24",
            "reviewed_case_count_matches_op08",
            "selection_row_count_is_24",
            "selection_row_count_matches_op08",
            "local_only",
            "must_not_export",
            "selection_only",
            "actual_source_guard_passed",
            "operation_receipt_confirms_actual_person_local_only_review",
            "actual_human_review_executed_by_person",
            "sanitized_review_result_rows_intake_required_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP09 ready field changed: {key}")
        if data.get("op08_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP09_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 ready requires OP08 next step")
        if data.get("op08_review_state_ref") != P7_R54_AHR_POST_PMN23_DMH_OP08_REVIEW_STATE_COMPLETED_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 ready requires completed OP08 state")
        if data.get("operation_receipt_schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_SCHEMA_VERSION:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 receipt schema changed")
        if data.get("actual_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF or data.get("actual_source_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_OP09_ALLOWED_ACTUAL_SOURCE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 actual source changed")
        if data.get("operation_receipt_ref_has_local_path_shape") is not False or data.get("reviewer_person_ref_has_local_path_shape") is not False or data.get("review_started_bucket_ref_has_local_path_shape") is not False or data.get("review_completed_bucket_ref_has_local_path_shape") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 refs must not be paths")
        if data.get("reviewed_case_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT or data.get("selection_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 counts changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP09_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 ready step refs changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 next step changed")
    else:
        if data.get("operation_receipt_intaked_here") is not False or data.get("sanitized_review_result_rows_intake_required_next") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 blocked receipt promoted sanitized rows intake")
        if data.get("actual_human_review_executed_by_person") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 blocked receipt promoted human review execution")
        if not blockers or data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP09 blocked next step changed")
    return True


build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_review_lifecycle_state_capture_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op08_review_lifecycle_state_capture_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_operation_state_machine_pause_abort_lifecycle_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_operation_state_machine_pause_abort_lifecycle_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op08_actual_review_operation_state_machine_pause_abort_lifecycle_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_operation_receipt_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_operation_receipt_intake_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_operation_receipt_intake_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract
)


P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op10_sanitized_review_result_rows_intake_provenance_guard.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op10_sanitized_review_result_row.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROWS_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op11_rating_rows_normalization_threshold_summary.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op11_rating_row.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[11]
P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[12]

P7_R54_AHR_POST_PMN23_DMH_OP10_READY_STATUS_REF: Final = (
    "DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_ACCEPTED_PROVENANCE_GUARDED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF: Final = (
    "DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_BLOCKED_BY_BODY_LEAK"
)
P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP10_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP10_INTAKE_REF: Final = (
    "post_pmn23_dmh_op10_sanitized_review_result_rows_intake_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF: Final = (
    "actual_person_selection_only_rows_local_review"
)

P7_R54_AHR_POST_PMN23_DMH_OP11_READY_STATUS_REF: Final = (
    "DMH_OP11_RATING_ROWS_NORMALIZED_THRESHOLD_SUMMARY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_STATUS_REF: Final = (
    "DMH_OP11_RATING_ROWS_NORMALIZATION_THRESHOLD_SUMMARY_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP11_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP11_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op11_rating_rows_normalization_threshold_summary_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_NORMALIZATION_REF: Final = (
    "post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_bodyfree_20260702_001"
)

P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP12_REQUIRED_SANITIZED_ROW_FIELD_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP10_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP12_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_RATING_ROW_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP13_REQUIRED_RATING_ROW_FIELD_REFS
)

P7_R54_AHR_POST_PMN23_DMH_OP10_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op09_actual_operation_receipt_accepted_bodyfree",
    "twenty_four_actual_person_selection_only_rows_received_bodyfree",
    "row_provenance_guard_blocks_helper_unit_test_synthetic_and_historical_rows",
    "rows_match_24_case_manifest_and_six_axis_contract_bodyfree",
    "rows_contain_no_body_question_path_hash_or_terminal_output",
    "rating_rows_normalization_required_next_without_downstream_promotion",
)
P7_R54_AHR_POST_PMN23_DMH_OP11_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op10_sanitized_review_result_rows_accepted_bodyfree",
    "twenty_four_rating_rows_normalized_from_sanitized_rows_bodyfree",
    "six_axis_threshold_summary_calculated_bodyfree",
    "rating_rows_are_decision_material_only_not_p5_final",
    "question_need_observation_rows_required_next_without_p8_start",
)

P7_R54_AHR_POST_PMN23_DMH_OP10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:11]
P7_R54_AHR_POST_PMN23_DMH_OP10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[11:]
P7_R54_AHR_POST_PMN23_DMH_OP11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:12]
P7_R54_AHR_POST_PMN23_DMH_OP11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[12:]

P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op09_schema_version", "op09_material_ref", "op09_next_required_step", "op09_dmh_ready",
    "op09_operation_receipt_ref", "op09_reviewer_person_ref", "op09_actual_human_review_executed_by_person",
    "op09_reviewed_case_count", "op09_selection_row_count",
    "dmh_op10_status_ref", "dmh_op10_allowed_status_refs", "dmh_op10_ready", "dmh_op10_reason_refs",
    "dmh_op10_reason_ref_count", "dmh_op10_blocker_refs", "dmh_op10_blocker_ref_count",
    "sanitized_review_result_rows_intake_ref", "sanitized_review_result_rows_required_field_refs",
    "sanitized_review_result_rows_required_field_ref_count", "sanitized_review_result_rows_input_present",
    "received_sanitized_review_result_row_count", "sanitized_review_result_row_count",
    "required_sanitized_review_result_row_count", "sanitized_review_result_row_count_is_24",
    "review_result_rows", "review_result_row_refs", "review_result_row_ref_count", "case_ref_ids", "case_ref_id_count",
    "case_ref_ids_unique", "blind_case_ids", "blind_case_id_count", "blind_case_ids_unique", "packet_ref_ids",
    "packet_ref_id_count", "packet_ref_ids_unique", "reviewed_at_bucket_refs", "reviewed_at_bucket_ref_count",
    "reviewed_at_bucket_refs_present", "axis_refs", "axis_ref_count", "axis_score_count_per_row",
    "axis_target_thresholds", "verdict_option_refs", "label_connection_quality_option_refs", "safe_display_check_option_refs",
    "sanitized_reason_id_option_refs", "readfeel_blocker_id_option_refs", "execution_blocker_id_option_refs",
    "question_need_primary_class_option_refs", "ambiguity_kind_option_refs", "one_question_fit_option_refs",
    "repair_required_option_refs", "plan_candidate_flag_refs", "rows_match_24_case_manifest", "rows_bodyfree_only",
    "rows_selection_only", "rows_have_actual_person_selection_only_provenance", "rows_have_required_axis_scores",
    "rows_have_allowed_verdict_refs", "rows_have_allowed_label_connection_refs", "rows_have_allowed_safe_display_refs",
    "rows_have_allowed_question_observation_refs", "rows_have_no_body_or_question_or_path_or_hash",
    "row_provenance_guard_passed", "forbidden_payload_key_paths", "forbidden_payload_key_path_count",
    "sanitized_selection_only_result_rows_intaken_here", "actual_sanitized_review_result_rows_intaken_here",
    "actual_human_review_executed_by_person", "actual_selection_rows_created_here",
    "actual_sanitized_review_result_rows_created_here", "rating_row_normalization_allowed_next",
    "question_text_materialized_here", "draft_question_text_materialized_here", "p8_question_implementation_spec_finalized_here",
    "actual_review_evidence_complete_from_real_review_still_false", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "dmh_op10_does_not_run_actual_human_review_here",
    "dmh_op10_does_not_create_rating_rows_question_rows_or_disposal", "dmh_op10_does_not_start_p8_p6_r52_or_release",
    "dmh_op10_does_not_execute_postcr22_ex_reentry", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_pmn23_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op10_schema_version", "op10_material_ref", "op10_next_required_step", "op10_dmh_ready",
    "op10_sanitized_review_result_row_count", "operation_receipt_ref", "reviewer_person_ref",
    "dmh_op11_status_ref", "dmh_op11_allowed_status_refs", "dmh_op11_ready", "dmh_op11_reason_refs",
    "dmh_op11_reason_ref_count", "dmh_op11_blocker_refs", "dmh_op11_blocker_ref_count",
    "rating_row_normalization_ref", "rating_row_required_field_refs", "rating_row_required_field_ref_count",
    "rating_row_count", "required_rating_row_count", "rating_row_count_is_24", "rating_rows", "rating_row_refs",
    "rating_row_ref_count", "axis_refs", "axis_ref_count", "axis_score_count_per_row", "axis_target_thresholds",
    "axis_target_thresholds_present", "average_axis_scores", "below_target_axis_refs", "below_target_axis_ref_count",
    "axis_pass_summary", "all_axis_target_passed", "label_connection_distribution_ref", "safe_display_distribution_ref",
    "verdict_distribution_ref", "readfeel_blocker_count_ref", "execution_blocker_count_ref",
    "actual_rating_rows_materialized_from_actual_rows", "rating_rows_normalized_here", "rating_decision_material_only",
    "p5_final_allowed", "p5_finalization_still_manual_decision_required", "question_need_observation_row_normalization_allowed_next",
    "actual_review_evidence_complete_from_real_review_still_false", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "dmh_op11_does_not_create_question_rows_or_disposal",
    "dmh_op11_does_not_start_p5_p6_p8_r52_or_release", "dmh_op11_does_not_execute_postcr22_ex_reentry",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract",
    "post_pmn23_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _dmh_op10_clean_ref_list(value: Any, *, allowed: Sequence[str], max_length: int = 180) -> tuple[list[str], bool]:
    if value is None:
        return [], True
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        return [], False
    refs: list[str] = []
    valid = True
    for raw in value:
        ref = _clean_ref(raw, default="", max_length=max_length)
        if not ref or ref not in allowed:
            valid = False
        refs.append(ref)
    return refs, valid


def _dmh_op10_clean_axis_scores(value: Any) -> tuple[dict[str, float], dict[str, bool], bool]:
    raw_scores = value if isinstance(value, Mapping) else {}
    valid = isinstance(value, Mapping)
    scores: dict[str, float] = {}
    flags: dict[str, bool] = {}
    for axis_ref in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS:
        try:
            score = float(raw_scores.get(axis_ref))
        except (TypeError, ValueError):
            score = 0.0
            valid = False
        if score < 0.0 or score > 1.0:
            valid = False
            score = min(max(score, 0.0), 1.0)
        scores[axis_ref] = round(score, 4)
        flags[axis_ref] = score >= P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS[axis_ref]
    return scores, flags, valid


def build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_bodyfree(
    *,
    review_session_id: Any = None,
    operation_receipt_ref: Any = None,
    reviewer_person_ref: Any = None,
    score_overrides_by_index: Mapping[int, Mapping[str, float]] | None = None,
) -> list[dict[str, Any]]:
    session_id = _safe_review_session_id(review_session_id)
    receipt_ref = _clean_ref(operation_receipt_ref, default=P7_R54_AHR_POST_PMN23_DMH_OP09_OPERATION_RECEIPT_REF, max_length=220)
    reviewer_ref = _clean_ref(reviewer_person_ref, default=P7_R54_AHR_POST_PMN23_DMH_OP07_REVIEWER_PERSON_REF, max_length=160)
    overrides = score_overrides_by_index if isinstance(score_overrides_by_index, Mapping) else {}
    rows: list[dict[str, Any]] = []
    for index, manifest_row in enumerate(_dmh_op04_manifest_rows(), start=1):
        scores = {axis: 1.0 for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS}
        override = overrides.get(index) if isinstance(overrides.get(index), Mapping) else {}
        for axis_ref in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS:
            if axis_ref in override:
                scores[axis_ref] = float(override[axis_ref])
        axis_scores, pass_flags, _ = _dmh_op10_clean_axis_scores(scores)
        rows.append(
            {
                "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_session_id": session_id,
                "operation_receipt_ref": receipt_ref,
                "review_result_row_ref": f"post_pmn23_dmh_op10_actual_review_result_row_{index:03d}_bodyfree",
                "case_ref_id": manifest_row["case_ref_id"],
                "blind_case_id": manifest_row["blind_case_id"],
                "packet_ref_id": manifest_row["packet_ref_id"],
                "reviewer_person_ref": reviewer_ref,
                "reviewed_at_bucket_ref": f"post_pmn23_dmh_op10_reviewed_at_bucket_{index:03d}_bodyfree",
                "axis_scores": axis_scores,
                "axis_score_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS),
                "axis_pass_flags": pass_flags,
                "verdict_ref": "PASS" if all(pass_flags.values()) else "YELLOW",
                "label_connection_quality_ref": "label_connection_present_natural",
                "safe_display_check_refs": ["no_overclaim_or_unearned_certainty", "no_body_leak"],
                "sanitized_reason_ids": ["record_returned_as_natural_line"],
                "readfeel_blocker_ids": [],
                "execution_blocker_ids": [],
                "question_need_primary_class_ref": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": [],
                "plan_candidate_flags": {key: False for key in P7_R54_AHR_POST_PMN23_DMH_OP07_PLAN_CANDIDATE_FLAG_REFS},
                "row_source_ref": P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF,
                "row_created_by_helper": False,
                "row_created_for_unit_test": False,
                "row_is_synthetic_contract_fixture": False,
                "historical_row_reused": False,
                "selection_only": True,
                "selection_only_row": True,
                "body_free": True,
            }
        )
    return rows


def _dmh_op10_validate_rows(
    rows_input: Sequence[Any], *, review_session_id: str, operation_receipt_ref: str, reviewer_person_ref: str
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    blockers: list[str] = []
    rows: list[dict[str, Any]] = []
    manifest = {str(row["case_ref_id"]): row for row in _dmh_op04_manifest_rows()}
    if len(rows_input) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op10_sanitized_review_result_row_count_not_24")
    forbidden_paths = _scan_forbidden_payload_key_paths(rows_input, path="sanitized_review_result_rows_bodyfree")
    if forbidden_paths:
        blockers.append("dmh_op10_sanitized_rows_forbidden_body_question_path_hash_key_detected")
    seen_case: set[str] = set()
    seen_blind: set[str] = set()
    seen_packet: set[str] = set()
    row_refs: list[str] = []
    reviewed_bucket_refs: list[str] = []
    flags = {
        "rows_match_24_case_manifest": True,
        "rows_bodyfree_only": True,
        "rows_selection_only": True,
        "rows_have_actual_person_selection_only_provenance": True,
        "rows_have_required_axis_scores": True,
        "rows_have_allowed_verdict_refs": True,
        "rows_have_allowed_label_connection_refs": True,
        "rows_have_allowed_safe_display_refs": True,
        "rows_have_allowed_question_observation_refs": True,
        "rows_have_no_body_or_question_or_path_or_hash": not bool(forbidden_paths),
    }
    for raw in rows_input:
        if not isinstance(raw, Mapping):
            blockers.append("dmh_op10_sanitized_row_not_mapping")
            flags["rows_match_24_case_manifest"] = False
            continue
        if set(raw) != set(P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS):
            blockers.append("dmh_op10_sanitized_row_required_fields_mismatch")
            flags["rows_have_no_body_or_question_or_path_or_hash"] = False
        case_ref = _clean_ref(raw.get("case_ref_id"), default="", max_length=80)
        blind_id = _clean_ref(raw.get("blind_case_id"), default="", max_length=80)
        packet_ref = _clean_ref(raw.get("packet_ref_id"), default="", max_length=80)
        row_ref = _clean_ref(raw.get("review_result_row_ref"), default="", max_length=220)
        reviewed_bucket_ref = _clean_ref(raw.get("reviewed_at_bucket_ref"), default="", max_length=220)
        row_refs.append(row_ref)
        reviewed_bucket_refs.append(reviewed_bucket_ref)
        if _ref_has_local_path_shape(row_ref) or _ref_has_local_path_shape(reviewed_bucket_ref):
            blockers.append("dmh_op10_sanitized_row_ref_or_reviewed_bucket_must_not_be_path")
            flags["rows_have_no_body_or_question_or_path_or_hash"] = False
        manifest_row = manifest.get(case_ref)
        if not manifest_row or manifest_row.get("blind_case_id") != blind_id or manifest_row.get("packet_ref_id") != packet_ref:
            blockers.append("dmh_op10_sanitized_row_manifest_id_mismatch")
            flags["rows_match_24_case_manifest"] = False
        seen_case.add(case_ref)
        seen_blind.add(blind_id)
        seen_packet.add(packet_ref)
        if raw.get("review_session_id") != review_session_id:
            blockers.append("dmh_op10_sanitized_row_review_session_id_mismatch")
            flags["rows_match_24_case_manifest"] = False
        if raw.get("operation_receipt_ref") != operation_receipt_ref:
            blockers.append("dmh_op10_sanitized_row_operation_receipt_ref_mismatch")
            flags["rows_match_24_case_manifest"] = False
        if raw.get("reviewer_person_ref") != reviewer_person_ref:
            blockers.append("dmh_op10_sanitized_row_reviewer_person_ref_mismatch")
            flags["rows_match_24_case_manifest"] = False
        axis_scores, expected_pass_flags, axis_valid = _dmh_op10_clean_axis_scores(raw.get("axis_scores"))
        input_pass_flags = raw.get("axis_pass_flags") if isinstance(raw.get("axis_pass_flags"), Mapping) else {}
        if not axis_valid or _safe_int(raw.get("axis_score_count")) != len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS):
            blockers.append("dmh_op10_sanitized_row_axis_scores_missing_or_out_of_range")
            flags["rows_have_required_axis_scores"] = False
        if any(bool(input_pass_flags.get(axis)) != expected_pass_flags[axis] for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS):
            blockers.append("dmh_op10_sanitized_row_axis_pass_flags_mismatch")
            flags["rows_have_required_axis_scores"] = False
        if raw.get("row_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF:
            blockers.append("dmh_op10_sanitized_row_source_ref_not_actual_person_selection_only_rows_local_review")
            flags["rows_have_actual_person_selection_only_provenance"] = False
        for field_name, blocker_name in (
            ("row_created_by_helper", "dmh_op10_sanitized_row_created_by_helper_cannot_be_actual"),
            ("row_created_for_unit_test", "dmh_op10_sanitized_row_created_for_unit_test_cannot_be_actual"),
            ("row_is_synthetic_contract_fixture", "dmh_op10_sanitized_row_is_synthetic_contract_fixture_cannot_be_actual"),
            ("historical_row_reused", "dmh_op10_sanitized_row_historical_row_reused_cannot_be_actual"),
        ):
            if raw.get(field_name) is not False:
                blockers.append(blocker_name)
                flags["rows_have_actual_person_selection_only_provenance"] = False
        if raw.get("selection_only") is not True or raw.get("selection_only_row") is not True:
            blockers.append("dmh_op10_sanitized_row_selection_only_not_true")
            flags["rows_selection_only"] = False
        if raw.get("body_free") is not True:
            blockers.append("dmh_op10_sanitized_row_body_free_not_true")
            flags["rows_bodyfree_only"] = False
        if raw.get("verdict_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP07_VERDICT_OPTION_REFS:
            blockers.append("dmh_op10_sanitized_row_verdict_ref_not_allowed")
            flags["rows_have_allowed_verdict_refs"] = False
        if raw.get("label_connection_quality_ref") not in pmn.P7_R54_AHR_POST_MN11_PMN_OP12_LABEL_CONNECTION_QUALITY_REFS:
            blockers.append("dmh_op10_sanitized_row_label_connection_ref_not_allowed")
            flags["rows_have_allowed_label_connection_refs"] = False
        for list_field, allowed, blocker_name, flag_name in (
            ("safe_display_check_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_SAFE_DISPLAY_CHECK_REFS, "dmh_op10_sanitized_row_option_ref_not_allowed", "rows_have_allowed_safe_display_refs"),
            ("sanitized_reason_ids", P7_R54_AHR_POST_PMN23_DMH_OP07_SANITIZED_REASON_ID_OPTION_REFS, "dmh_op10_sanitized_row_option_ref_not_allowed", "rows_have_allowed_safe_display_refs"),
            ("readfeel_blocker_ids", P7_R54_AHR_POST_PMN23_DMH_OP07_READFEEL_BLOCKER_ID_OPTION_REFS, "dmh_op10_sanitized_row_option_ref_not_allowed", "rows_have_allowed_safe_display_refs"),
            ("execution_blocker_ids", P7_R54_AHR_POST_PMN23_DMH_OP07_EXECUTION_BLOCKER_ID_OPTION_REFS, "dmh_op10_sanitized_row_option_ref_not_allowed", "rows_have_allowed_safe_display_refs"),
            ("ambiguity_kind_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS, "dmh_op10_sanitized_row_option_ref_not_allowed", "rows_have_allowed_question_observation_refs"),
            ("repair_required_refs", P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS, "dmh_op10_sanitized_row_option_ref_not_allowed", "rows_have_allowed_question_observation_refs"),
        ):
            _, valid_list = _dmh_op10_clean_ref_list(raw.get(list_field), allowed=allowed)
            if not valid_list:
                blockers.append(blocker_name)
                flags[flag_name] = False
        if raw.get("question_need_primary_class_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS:
            blockers.append("dmh_op10_sanitized_row_question_need_primary_class_ref_not_allowed")
            flags["rows_have_allowed_question_observation_refs"] = False
        if raw.get("one_question_fit_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append("dmh_op10_sanitized_row_one_question_fit_ref_not_allowed")
            flags["rows_have_allowed_question_observation_refs"] = False
        clean_row = {key: raw.get(key) for key in P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS}
        clean_row["axis_scores"] = axis_scores
        clean_row["axis_pass_flags"] = expected_pass_flags
        rows.append(clean_row)
    if len(seen_case) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op10_case_ref_ids_not_unique_or_not_24")
        flags["rows_match_24_case_manifest"] = False
    if len(seen_blind) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op10_blind_case_ids_not_unique_or_not_24")
        flags["rows_match_24_case_manifest"] = False
    if len(seen_packet) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op10_packet_ref_ids_not_unique_or_not_24")
        flags["rows_match_24_case_manifest"] = False
    blockers = list(dict.fromkeys(blockers))
    return rows, blockers, {
        **flags,
        "forbidden_payload_key_paths": forbidden_paths,
        "review_result_row_refs": row_refs,
        "case_ref_ids": list(seen_case),
        "blind_case_ids": list(seen_blind),
        "packet_ref_ids": list(seen_packet),
        "reviewed_at_bucket_refs": reviewed_bucket_refs,
    }


def build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard(
    *,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    op09 = actual_operation_receipt_intake if isinstance(actual_operation_receipt_intake, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id or op09.get("review_session_id"))
    operation_receipt_ref = _clean_ref(op09.get("operation_receipt_ref"), default="", max_length=220)
    reviewer_person_ref = _clean_ref(op09.get("reviewer_person_ref"), default="", max_length=160)
    blockers: list[str] = []
    if not op09:
        blockers.append("dmh_op10_actual_operation_receipt_intake_missing")
    elif op09.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP09_ACTUAL_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION or op09.get("dmh_op09_ready") is not True:
        blockers.append("dmh_op10_actual_operation_receipt_intake_not_ready")
    elif op09.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF:
        blockers.append("dmh_op10_actual_operation_receipt_next_step_mismatch")
    rows_input = list(sanitized_review_result_rows_bodyfree or [])
    rows_input_present = bool(sanitized_review_result_rows_bodyfree)
    if not rows_input_present:
        blockers.append("dmh_op10_sanitized_review_result_rows_not_received")
    rows, row_blockers, meta = _dmh_op10_validate_rows(rows_input, review_session_id=session_id, operation_receipt_ref=operation_receipt_ref, reviewer_person_ref=reviewer_person_ref)
    blockers.extend(row_blockers if rows_input_present else [])
    blockers = list(dict.fromkeys(blockers))
    leak = any("forbidden_body_question_path_hash_key_detected" in b or "path" in b or "body_leak" in b for b in blockers)
    ready = not blockers
    status = P7_R54_AHR_POST_PMN23_DMH_OP10_READY_STATUS_REF if ready else (P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_BY_LEAK_STATUS_REF if leak else P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF)
    case_ids = [row.get("case_ref_id") for row in rows]
    blind_ids = [row.get("blind_case_id") for row in rows]
    packet_ids = [row.get("packet_ref_id") for row in rows]
    reviewed_bucket_refs = [row.get("reviewed_at_bucket_ref") for row in rows]
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op09_schema_version": op09.get("schema_version", ""),
        "op09_material_ref": op09.get("material_id", ""),
        "op09_next_required_step": op09.get("next_required_step", ""),
        "op09_dmh_ready": op09.get("dmh_op09_ready") is True,
        "op09_operation_receipt_ref": operation_receipt_ref,
        "op09_reviewer_person_ref": reviewer_person_ref,
        "op09_actual_human_review_executed_by_person": op09.get("actual_human_review_executed_by_person") is True,
        "op09_reviewed_case_count": _safe_int(op09.get("reviewed_case_count")),
        "op09_selection_row_count": _safe_int(op09.get("selection_row_count")),
        "dmh_op10_status_ref": status,
        "dmh_op10_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_STATUS_REFS),
        "dmh_op10_ready": ready,
        "dmh_op10_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP10_READY_REASON_REFS) if ready else [],
        "dmh_op10_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP10_READY_REASON_REFS) if ready else 0,
        "dmh_op10_blocker_refs": blockers,
        "dmh_op10_blocker_ref_count": len(blockers),
        "sanitized_review_result_rows_intake_ref": P7_R54_AHR_POST_PMN23_DMH_OP10_INTAKE_REF,
        "sanitized_review_result_rows_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS),
        "sanitized_review_result_rows_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS),
        "sanitized_review_result_rows_input_present": rows_input_present,
        "received_sanitized_review_result_row_count": len(rows_input),
        "sanitized_review_result_row_count": len(rows),
        "required_sanitized_review_result_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count_is_24": len(rows) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "review_result_rows": rows,
        "review_result_row_refs": [row.get("review_result_row_ref") for row in rows],
        "review_result_row_ref_count": len({row.get("review_result_row_ref") for row in rows}),
        "case_ref_ids": case_ids,
        "case_ref_id_count": len(set(case_ids)),
        "case_ref_ids_unique": len(set(case_ids)) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(set(blind_ids)),
        "blind_case_ids_unique": len(set(blind_ids)) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "packet_ref_ids": packet_ids,
        "packet_ref_id_count": len(set(packet_ids)),
        "packet_ref_ids_unique": len(set(packet_ids)) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "reviewed_at_bucket_refs": reviewed_bucket_refs,
        "reviewed_at_bucket_ref_count": len(set(reviewed_bucket_refs)),
        "reviewed_at_bucket_refs_present": len(set(reviewed_bucket_refs)) == len(rows) and all(bool(ref) for ref in reviewed_bucket_refs),
        "axis_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS),
        "axis_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS),
        "axis_target_thresholds": dict(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS),
        "verdict_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_VERDICT_OPTION_REFS),
        "label_connection_quality_option_refs": list(pmn.P7_R54_AHR_POST_MN11_PMN_OP12_LABEL_CONNECTION_QUALITY_REFS),
        "safe_display_check_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_SAFE_DISPLAY_CHECK_REFS),
        "sanitized_reason_id_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_SANITIZED_REASON_ID_OPTION_REFS),
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_READFEEL_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "question_need_primary_class_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_PLAN_CANDIDATE_FLAG_REFS),
        "rows_match_24_case_manifest": ready and meta["rows_match_24_case_manifest"],
        "rows_bodyfree_only": ready and meta["rows_bodyfree_only"],
        "rows_selection_only": ready and meta["rows_selection_only"],
        "rows_have_actual_person_selection_only_provenance": ready and meta["rows_have_actual_person_selection_only_provenance"],
        "rows_have_required_axis_scores": ready and meta["rows_have_required_axis_scores"],
        "rows_have_allowed_verdict_refs": ready and meta["rows_have_allowed_verdict_refs"],
        "rows_have_allowed_label_connection_refs": ready and meta["rows_have_allowed_label_connection_refs"],
        "rows_have_allowed_safe_display_refs": ready and meta["rows_have_allowed_safe_display_refs"],
        "rows_have_allowed_question_observation_refs": ready and meta["rows_have_allowed_question_observation_refs"],
        "rows_have_no_body_or_question_or_path_or_hash": ready and meta["rows_have_no_body_or_question_or_path_or_hash"],
        "row_provenance_guard_passed": ready,
        "forbidden_payload_key_paths": meta["forbidden_payload_key_paths"],
        "forbidden_payload_key_path_count": len(meta["forbidden_payload_key_paths"]),
        "sanitized_selection_only_result_rows_intaken_here": ready,
        "actual_sanitized_review_result_rows_intaken_here": ready,
        "actual_human_review_executed_by_person": op09.get("actual_human_review_executed_by_person") is True and ready,
        "actual_selection_rows_created_here": False,
        "actual_sanitized_review_result_rows_created_here": False,
        "rating_row_normalization_allowed_next": ready,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "dmh_op10_does_not_run_actual_human_review_here": True,
        "dmh_op10_does_not_create_rating_rows_question_rows_or_disposal": True,
        "dmh_op10_does_not_start_p8_p6_r52_or_release": True,
        "dmh_op10_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP10_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP09_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP09_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP10")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP10_STEP_REF, source="P7-R54-AHR-PostPMN23-DMH-OP10")
    blockers = list(data.get("dmh_op10_blocker_refs") or [])
    expected_ready = len(blockers) == 0
    expected_status = P7_R54_AHR_POST_PMN23_DMH_OP10_READY_STATUS_REF if expected_ready else (P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_BY_LEAK_STATUS_REF if any("forbidden_body_question_path_hash_key_detected" in b for b in blockers) else P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_STATUS_REF)
    if data.get("dmh_op10_ready") is not expected_ready or data.get("dmh_op10_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 status/ready changed")
    if data.get("dmh_op10_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 blocker count changed")
    if expected_ready:
        required_true = (
            "op09_dmh_ready", "op09_actual_human_review_executed_by_person", "sanitized_review_result_rows_input_present",
            "sanitized_review_result_row_count_is_24", "case_ref_ids_unique", "blind_case_ids_unique", "packet_ref_ids_unique",
            "rows_match_24_case_manifest", "rows_bodyfree_only", "rows_selection_only",
            "rows_have_actual_person_selection_only_provenance", "rows_have_required_axis_scores",
            "rows_have_allowed_verdict_refs", "rows_have_allowed_label_connection_refs", "rows_have_allowed_safe_display_refs",
            "rows_have_allowed_question_observation_refs", "rows_have_no_body_or_question_or_path_or_hash", "row_provenance_guard_passed",
            "sanitized_selection_only_result_rows_intaken_here", "actual_sanitized_review_result_rows_intaken_here",
            "actual_human_review_executed_by_person", "rating_row_normalization_allowed_next",
            "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171",
            "dmh_op10_does_not_run_actual_human_review_here", "dmh_op10_does_not_create_rating_rows_question_rows_or_disposal",
            "dmh_op10_does_not_start_p8_p6_r52_or_release", "dmh_op10_does_not_execute_postcr22_ex_reentry",
        )
        for key in required_true:
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP10 required ready field changed: {key}")
        for key in ("actual_selection_rows_created_here", "actual_sanitized_review_result_rows_created_here"):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP10 required ready false field changed: {key}")
        if data.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 row count changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP10_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 implemented steps changed")
        rows = data.get("review_result_rows")
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)) or len(rows) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 review result rows shape changed")
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 row must be mapping")
            if set(row) != set(P7_R54_AHR_POST_PMN23_DMH_OP10_REQUIRED_SANITIZED_ROW_FIELD_REFS):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 row fields changed")
            if row.get("row_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 row source changed")
            for flag in ("row_created_by_helper", "row_created_for_unit_test", "row_is_synthetic_contract_fixture", "historical_row_reused"):
                if row.get(flag) is not False:
                    raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP10 row provenance flag changed: {flag}")
            for flag in P7_R54_AHR_POST_PMN23_DMH_OP10_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(flag) is not False:
                    raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP10 row body-free false flag changed: {flag}")
            if row.get("selection_only") is not True or row.get("selection_only_row") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 row selection/body-free guard changed")
            if _scan_forbidden_payload_key_paths(row, path="dmh_op10_review_result_row"):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 row leaked forbidden payload key")
    else:
        if data.get("sanitized_selection_only_result_rows_intaken_here") is not False or data.get("rating_row_normalization_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 blocked material promoted next step")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP10 blocked next step changed")
    return True


def _dmh_op11_distribution(values: Sequence[Any]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for value in values:
        ref = str(value or "")
        dist[ref] = dist.get(ref, 0) + 1
    return dist


def _dmh_op11_rating_rows(rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rating_rows: list[dict[str, Any]] = []
    axis_totals = {axis: 0.0 for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS}
    axis_summary = {axis: {"passed": 0, "below_target": 0} for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS}
    below_targets: set[str] = set()
    for index, row in enumerate(rows, start=1):
        scores = row.get("axis_scores") if isinstance(row.get("axis_scores"), Mapping) else {}
        axis_scores = {axis: round(float(scores.get(axis, 0.0)), 4) for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS}
        pass_flags = {axis: axis_scores[axis] >= P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS[axis] for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS}
        below_axis = [axis for axis, passed in pass_flags.items() if not passed]
        for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS:
            axis_totals[axis] += axis_scores[axis]
            axis_summary[axis]["passed" if pass_flags[axis] else "below_target"] += 1
            if not pass_flags[axis]:
                below_targets.add(axis)
        rating_rows.append(
            {
                "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROW_SCHEMA_VERSION,
                "review_session_id": row.get("review_session_id"),
                "operation_receipt_ref": row.get("operation_receipt_ref"),
                "rating_row_ref": f"post_pmn23_dmh_op11_rating_row_{index:03d}_bodyfree",
                "rating_source_review_result_row_ref": row.get("review_result_row_ref"),
                "case_ref_id": row.get("case_ref_id"),
                "blind_case_id": row.get("blind_case_id"),
                "packet_ref_id": row.get("packet_ref_id"),
                "axis_scores": axis_scores,
                "axis_score_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS),
                "axis_pass_flags": pass_flags,
                "below_target_axis_refs": below_axis,
                "all_axis_target_passed": not below_axis,
                "verdict_ref": row.get("verdict_ref"),
                "label_connection_quality_ref": row.get("label_connection_quality_ref"),
                "safe_display_check_refs": list(row.get("safe_display_check_refs") or []),
                "readfeel_blocker_ids": list(row.get("readfeel_blocker_ids") or []),
                "execution_blocker_ids": list(row.get("execution_blocker_ids") or []),
                "row_source_ref": row.get("row_source_ref"),
                "rating_decision_material_only": True,
                "body_free": True,
            }
        )
    count = len(rows)
    average_scores = {axis: round(axis_totals[axis] / count, 4) for axis in P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS} if count else {}
    return rating_rows, {
        "axis_pass_summary": axis_summary,
        "below_target_axis_refs": sorted(below_targets),
        "average_axis_scores": average_scores,
        "all_axis_target_passed": not bool(below_targets) and count == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
    }


def build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary(
    *, sanitized_review_result_rows_intake: Mapping[str, Any] | None = None, review_session_id: Any = None
) -> dict[str, Any]:
    op10 = sanitized_review_result_rows_intake if isinstance(sanitized_review_result_rows_intake, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id or op10.get("review_session_id"))
    blockers: list[str] = []
    if not op10:
        blockers.append("dmh_op11_sanitized_review_result_rows_intake_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(op10)
        except ValueError:
            blockers.append("dmh_op11_op10_sanitized_review_result_rows_contract_invalid")
        if op10.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP10_SANITIZED_REVIEW_RESULT_ROWS_INTAKE_PROVENANCE_GUARD_SCHEMA_VERSION or op10.get("dmh_op10_ready") is not True:
            blockers.append("dmh_op11_op10_sanitized_review_result_rows_not_ready")
        if op10.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF:
            blockers.append("dmh_op11_op10_next_step_mismatch")
    rows = list(op10.get("review_result_rows") or []) if isinstance(op10.get("review_result_rows"), Sequence) and not isinstance(op10.get("review_result_rows"), (str, bytes, bytearray)) else []
    rating_rows, summary = _dmh_op11_rating_rows(rows) if not blockers else ([], {"axis_pass_summary": {}, "below_target_axis_refs": [], "average_axis_scores": {}, "all_axis_target_passed": False})
    if not blockers and len(rating_rows) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op11_rating_row_count_not_24")
    ready = not blockers
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROWS_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op10_schema_version": op10.get("schema_version", ""),
        "op10_material_ref": op10.get("material_id", ""),
        "op10_next_required_step": op10.get("next_required_step", ""),
        "op10_dmh_ready": op10.get("dmh_op10_ready") is True,
        "op10_sanitized_review_result_row_count": _safe_int(op10.get("sanitized_review_result_row_count")),
        "operation_receipt_ref": op10.get("op09_operation_receipt_ref", ""),
        "reviewer_person_ref": op10.get("op09_reviewer_person_ref", ""),
        "dmh_op11_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP11_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_STATUS_REF,
        "dmh_op11_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP11_ALLOWED_STATUS_REFS),
        "dmh_op11_ready": ready,
        "dmh_op11_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP11_READY_REASON_REFS) if ready else [],
        "dmh_op11_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP11_READY_REASON_REFS) if ready else 0,
        "dmh_op11_blocker_refs": blockers,
        "dmh_op11_blocker_ref_count": len(blockers),
        "rating_row_normalization_ref": P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_NORMALIZATION_REF,
        "rating_row_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_RATING_ROW_FIELD_REFS),
        "rating_row_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_RATING_ROW_FIELD_REFS),
        "rating_row_count": len(rating_rows),
        "required_rating_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "rating_row_count_is_24": len(rating_rows) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "rating_rows": rating_rows,
        "rating_row_refs": [row["rating_row_ref"] for row in rating_rows],
        "rating_row_ref_count": len({row["rating_row_ref"] for row in rating_rows}),
        "axis_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS) if ready else [],
        "axis_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS) if ready else 0,
        "axis_score_count_per_row": len(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_REFS) if ready else 0,
        "axis_target_thresholds": dict(P7_R54_AHR_POST_PMN23_DMH_OP07_RATING_AXIS_TARGET_THRESHOLDS) if ready else {},
        "axis_target_thresholds_present": ready,
        "average_axis_scores": summary["average_axis_scores"],
        "below_target_axis_refs": summary["below_target_axis_refs"],
        "below_target_axis_ref_count": len(summary["below_target_axis_refs"]),
        "axis_pass_summary": summary["axis_pass_summary"],
        "all_axis_target_passed": bool(summary["all_axis_target_passed"]),
        "label_connection_distribution_ref": _dmh_op11_distribution([row.get("label_connection_quality_ref") for row in rows]) if ready else {},
        "safe_display_distribution_ref": _dmh_op11_distribution([ref for row in rows for ref in (row.get("safe_display_check_refs") or [])]) if ready else {},
        "verdict_distribution_ref": _dmh_op11_distribution([row.get("verdict_ref") for row in rows]) if ready else {},
        "readfeel_blocker_count_ref": sum(len(row.get("readfeel_blocker_ids") or []) for row in rows) if ready else 0,
        "execution_blocker_count_ref": sum(len(row.get("execution_blocker_ids") or []) for row in rows) if ready else 0,
        "actual_rating_rows_materialized_from_actual_rows": ready,
        "rating_rows_normalized_here": ready,
        "rating_decision_material_only": ready,
        "p5_final_allowed": False,
        "p5_finalization_still_manual_decision_required": True,
        "question_need_observation_row_normalization_allowed_next": ready,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "dmh_op11_does_not_create_question_rows_or_disposal": True,
        "dmh_op11_does_not_start_p5_p6_p8_r52_or_release": True,
        "dmh_op11_does_not_execute_postcr22_ex_reentry": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP11_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP10_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP11")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROWS_NORMALIZATION_THRESHOLD_SUMMARY_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP11_STEP_REF, source="P7-R54-AHR-PostPMN23-DMH-OP11")
    blockers = list(data.get("dmh_op11_blocker_refs") or [])
    expected_ready = len(blockers) == 0
    expected_status = P7_R54_AHR_POST_PMN23_DMH_OP11_READY_STATUS_REF if expected_ready else P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_STATUS_REF
    if data.get("dmh_op11_ready") is not expected_ready or data.get("dmh_op11_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 status/ready changed")
    if data.get("dmh_op11_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 blocker count changed")
    if expected_ready:
        for key in (
            "op10_dmh_ready", "rating_row_count_is_24", "axis_target_thresholds_present",
            "actual_rating_rows_materialized_from_actual_rows", "rating_rows_normalized_here", "rating_decision_material_only",
            "p5_finalization_still_manual_decision_required", "question_need_observation_row_normalization_allowed_next",
            "actual_review_evidence_complete_from_real_review_still_false", "current_actual_review_basis_remains_264_85_258_171",
            "dmh_op11_does_not_create_question_rows_or_disposal", "dmh_op11_does_not_start_p5_p6_p8_r52_or_release",
            "dmh_op11_does_not_execute_postcr22_ex_reentry",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP11 ready field changed: {key}")
        if data.get("rating_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 rating row count changed")
        if data.get("p5_final_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 p5 final promoted")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP11_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 implemented steps changed")
        for row in data.get("rating_rows") or []:
            if set(row) != set(P7_R54_AHR_POST_PMN23_DMH_OP11_REQUIRED_RATING_ROW_FIELD_REFS):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 rating row fields changed")
            if row.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP11_RATING_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 rating row schema changed")
            if row.get("row_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP10_ALLOWED_ROW_SOURCE_REF:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 rating row source changed")
            if row.get("rating_decision_material_only") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 rating row promoted or leaked body")
    else:
        if data.get("rating_rows_normalized_here") is not False or data.get("actual_rating_rows_materialized_from_actual_rows") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 blocked material promoted rows")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP11 blocked next step changed")
    return True


build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_sanitized_review_result_rows_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_sanitized_review_result_rows_intake_provenance_guard_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_sanitized_review_result_rows_intake_provenance_guard_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_rows_normalization_threshold_summary_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_rows_normalization_threshold_summary_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract
)

# Alias retained for OP10 row validation wording; OP07 finalized the form, but the
# safe-display option refs originate from the inherited PMN row contract.
P7_R54_AHR_POST_PMN23_DMH_OP07_SAFE_DISPLAY_CHECK_REFS: Final[tuple[str, ...]] = (
    pmn.P7_R54_AHR_POST_MN11_PMN_OP12_SAFE_DISPLAY_CHECK_REFS
)

# OP10 row body-free leak markers are already enforced by the top-level material
# marker maps and forbidden-key scan in this helper; keep this tuple empty for
# sanitized-row shapes that deliberately contain only selection refs and no
# explicit body leak booleans.
P7_R54_AHR_POST_PMN23_DMH_OP10_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = ()

_p7_r54_ahr_post_pmn23_dmh_op10_contract_before_created_flag_guard = (
    assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract
)

def assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(data: Mapping[str, Any]) -> bool:
    _p7_r54_ahr_post_pmn23_dmh_op10_contract_before_created_flag_guard(data)
    if data.get("dmh_op10_ready") is True:
        for field in ("actual_selection_rows_created_here", "actual_sanitized_review_result_rows_created_here"):
            if data.get(field) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP10 must not create actual rows here: {field}")
    return True

assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_sanitized_review_result_rows_intake_provenance_guard_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract
)


# ---------------------------------------------------------------------------
# DMH-OP12 / DMH-OP13 question observation normalization and consistency guard
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op12_question_need_observation_rows_normalization.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op12_question_need_observation_row.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP13_RATING_QUESTION_CONSISTENCY_BLOCKER_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op13_rating_question_consistency_blocker_separation.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op13_consistency_blocker_row.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[13]
P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[14]

P7_R54_AHR_POST_PMN23_DMH_OP12_READY_STATUS_REF: Final = (
    "DMH_OP12_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_STATUS_REF: Final = (
    "DMH_OP12_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZATION_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP12_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP12_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op12_question_need_observation_rows_normalization_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP12_NORMALIZATION_REF: Final = (
    "post_pmn23_dmh_op12_question_need_observation_rows_normalization_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP12_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op11_rating_rows_normalized_bodyfree",
    "op10_actual_sanitized_review_result_rows_available_bodyfree",
    "twenty_four_question_need_observation_rows_normalized_from_selection_only_rows",
    "question_text_trigger_storage_and_p8_spec_not_materialized",
    "rating_question_consistency_blocker_separation_required_next_without_p8_start",
)

P7_R54_AHR_POST_PMN23_DMH_OP13_READY_STATUS_REF: Final = (
    "DMH_OP13_RATING_QUESTION_CONSISTENCY_BLOCKER_SEPARATION_PASSED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_STATUS_REF: Final = (
    "DMH_OP13_RATING_QUESTION_CONSISTENCY_BLOCKER_SEPARATION_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP13_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP13_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op13_rating_question_consistency_blocker_separation_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP13_GUARD_REF: Final = (
    "post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP13_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op12_question_need_observation_rows_normalized_bodyfree",
    "op11_rating_rows_available_bodyfree",
    "p5_p4_operation_safe_display_and_inconclusive_blockers_separated_bodyfree",
    "p8_material_candidate_escape_blocked_without_question_text_or_p8_start",
    "disposal_purge_receipt_intake_required_next_without_evidence_complete",
)

P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP10_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "operation_receipt_ref",
    "question_need_row_ref",
    "source_review_result_row_ref",
    "source_rating_row_ref",
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
    *P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS,
)

P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_KIND_REFS: Final[tuple[str, ...]] = (
    "readfeel_blocker",
    "execution_blocker",
    "repair_required",
    "below_target_axis",
    "safe_display_risk",
    "inconclusive_material",
    "verdict_blocker",
    "heavy_observation",
)
P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_CATEGORY_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_STATUS_REF: Final = "open_bodyfree_product_or_operation_blocker"
P7_R54_AHR_POST_PMN23_DMH_OP13_P8_MATERIAL_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_AHR_POST_PMN23_DMH_OP13_P8_MATERIAL_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "fits_one_question",
)
P7_R54_AHR_POST_PMN23_DMH_OP13_SAFE_DISPLAY_RISK_CHECK_REFS: Final[tuple[str, ...]] = (
    "safe_display_risk_detected",
)
P7_R54_AHR_POST_PMN23_DMH_OP13_READFEEL_ROUTE_REF: Final = "P5_READFEEL_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_POST_PMN23_DMH_OP13_P4_ROUTE_REF: Final = "P4_CURRENT_ONLY_SURFACE_REPAIR_BEFORE_P8_OR_R52"
P7_R54_AHR_POST_PMN23_DMH_OP13_OPERATION_ROUTE_REF: Final = "R54_OPERATION_BLOCKER_REPAIR_BEFORE_EVIDENCE_COMPLETE"
P7_R54_AHR_POST_PMN23_DMH_OP13_INCONCLUSIVE_ROUTE_REF: Final = "R54_INCONCLUSIVE_MATERIAL_REVIEW_REQUIRED"
P7_R54_AHR_POST_PMN23_DMH_OP13_CLEAN_ROUTE_REF: Final = "NO_BLOCKER_CONTINUE_TO_DISPOSAL_PURGE_RECEIPT_INTAKE"
P7_R54_AHR_POST_PMN23_DMH_OP13_READFEEL_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = dict(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP14_READFEEL_BLOCKER_CATEGORY_BY_ID
)
P7_R54_AHR_POST_PMN23_DMH_OP13_EXECUTION_BLOCKER_CATEGORY_BY_ID: Final[dict[str, str]] = dict(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP14_EXECUTION_BLOCKER_CATEGORY_BY_ID
)
P7_R54_AHR_POST_PMN23_DMH_OP13_REPAIR_CATEGORY_BY_REF: Final[dict[str, str]] = dict(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP14_REPAIR_CATEGORY_BY_REF
)
P7_R54_AHR_POST_PMN23_DMH_OP13_BELOW_TARGET_AXIS_CATEGORY_BY_REF: Final[dict[str, str]] = dict(
    pmn.P7_R54_AHR_POST_MN11_PMN_OP14_BELOW_TARGET_AXIS_CATEGORY_BY_REF
)
P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_PMN23_DMH_OP10_ROW_BODYFREE_FALSE_FLAG_REFS,
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_trigger_logic_materialized_here",
    "question_answer_storage_materialized_here",
    "p8_implementation_spec_finalized_here",
    "p8_start_allowed",
)
P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "consistency_blocker_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "source_rating_row_ref",
    "source_question_need_row_ref",
    "blocker_kind_ref",
    "blocker_category_ref",
    "issue_reason_ref",
    "blocked_escape_to_ref",
    "routes_to_ref",
    "p8_candidate_escape_detected",
    "p8_candidate_escape_blocked",
    "p8_material_candidate_after_blocker_separation",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_trigger_logic_materialized_here",
    "question_answer_storage_materialized_here",
    "p8_implementation_spec_finalized_here",
    "p8_start_allowed",
    "body_free",
    *P7_R54_AHR_POST_PMN23_DMH_OP10_ROW_BODYFREE_FALSE_FLAG_REFS,
)

P7_R54_AHR_POST_PMN23_DMH_OP12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:13]
P7_R54_AHR_POST_PMN23_DMH_OP12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[13:]
P7_R54_AHR_POST_PMN23_DMH_OP13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:14]
P7_R54_AHR_POST_PMN23_DMH_OP13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[14:]

P7_R54_AHR_POST_PMN23_DMH_OP12_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op11_schema_version", "op11_material_ref", "op11_next_required_step", "op11_dmh_ready", "op11_rating_row_count",
    "op11_question_need_observation_row_normalization_allowed_next", "op10_schema_version", "op10_material_ref", "op10_dmh_ready",
    "op10_sanitized_review_result_row_count", "operation_receipt_ref", "reviewer_person_ref", "dmh_op12_status_ref",
    "dmh_op12_allowed_status_refs", "dmh_op12_ready", "dmh_op12_reason_refs", "dmh_op12_reason_ref_count",
    "dmh_op12_blocker_refs", "dmh_op12_blocker_ref_count", "question_need_observation_rows_normalization_ref",
    "question_need_observation_row_required_field_refs", "question_need_observation_row_required_field_ref_count",
    "source_sanitized_review_result_row_count", "source_rating_row_count", "required_question_need_observation_row_count",
    "question_need_observation_row_count", "question_need_observation_row_count_is_24", "question_need_observation_rows",
    "question_need_observation_row_refs", "question_need_observation_row_ref_count", "case_ref_ids", "case_ref_id_count",
    "case_ref_ids_unique", "blind_case_ids", "blind_case_id_count", "blind_case_ids_unique", "packet_ref_ids",
    "packet_ref_id_count", "packet_ref_ids_unique", "question_need_primary_class_option_refs", "question_need_primary_class_option_ref_count",
    "ambiguity_kind_option_refs", "ambiguity_kind_option_ref_count", "one_question_fit_option_refs", "one_question_fit_option_ref_count",
    "repair_required_option_refs", "repair_required_option_ref_count", "question_need_primary_class_counts", "ambiguity_kind_counts",
    "one_question_fit_counts", "repair_required_ref_counts", "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only", "plus_single_question_candidate_case_refs_bodyfree_only",
    "plus_single_question_candidate_case_count_bodyfree_only", "premium_deep_dive_candidate_case_refs_bodyfree_only",
    "premium_deep_dive_candidate_case_count_bodyfree_only", "p8_material_candidate_blocked_by_blocker_case_refs",
    "p8_material_candidate_blocked_by_blocker_case_count", "question_text_materialized_here", "draft_question_text_materialized_here",
    "question_trigger_logic_materialized_here", "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here",
    "p8_start_allowed", "question_need_observation_rows_normalized_here", "actual_question_need_observation_rows_materialized_from_actual_rows",
    "actual_question_need_observation_rows_materialized_here", "rating_question_consistency_blocker_separation_allowed_next",
    "actual_review_evidence_complete_from_real_review_still_false", "p8_material_candidate_only_is_not_p8_start",
    "dmh_op12_does_not_create_question_text_or_p8_storage", "dmh_op12_does_not_create_disposal_or_evidence_complete",
    "dmh_op12_does_not_start_p5_p6_p8_r52_or_release", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_pmn23_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP13_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op12_schema_version", "op12_material_ref", "op12_next_required_step", "op12_dmh_ready",
    "op12_question_need_observation_row_count", "op12_p8_material_candidate_case_count_bodyfree_only", "op12_p8_start_allowed",
    "op11_schema_version", "op11_material_ref", "op11_dmh_ready", "op11_rating_row_count", "operation_receipt_ref",
    "dmh_op13_status_ref", "dmh_op13_allowed_status_refs", "dmh_op13_ready", "rating_question_consistency_guard_passed",
    "dmh_op13_reason_refs", "dmh_op13_reason_ref_count", "dmh_op13_blocker_refs", "dmh_op13_blocker_ref_count",
    "rating_question_consistency_blocker_separation_ref", "consistency_blocker_row_required_field_refs",
    "consistency_blocker_row_required_field_ref_count", "consistency_blocker_rows", "consistency_blocker_row_count",
    "consistency_blocker_row_refs", "consistency_blocker_row_ref_count", "blocker_kind_refs", "blocker_kind_counts",
    "blocker_category_refs", "blocker_category_counts", "p8_material_candidate_case_refs_bodyfree_only",
    "p8_material_candidate_case_count_bodyfree_only", "p8_material_candidate_blocked_by_blocker_case_refs",
    "p8_material_candidate_blocked_by_blocker_case_count", "p8_material_candidate_allowed_after_blocker_separation_case_refs",
    "p8_material_candidate_allowed_after_blocker_separation_case_count", "no_blocker_case_refs", "no_blocker_case_count",
    "p5_repair_required_case_refs", "p5_repair_required_case_count", "p4_current_only_repair_required_case_refs",
    "p4_current_only_repair_required_case_count", "operation_blocked_case_refs", "operation_blocked_case_count",
    "safe_display_blocked_case_refs", "safe_display_blocked_case_count", "inconclusive_case_refs", "inconclusive_case_count",
    "below_target_axis_p8_escape_blocked_count", "safe_display_question_escape_blocked_count",
    "readfeel_blocker_question_escape_blocked_count", "execution_blocker_question_escape_blocked_count",
    "insufficient_material_question_escape_blocked_count", "heavy_observation_p8_escape_blocked_count",
    "repair_required_question_escape_blocked_count", "verdict_blocker_p8_escape_blocked_count",
    "rating_question_consistency_checked_here", "rating_question_consistency_guard_blocks_p8_escape",
    "p5_repair_required_cases_routed_to_p5_repair", "p4_repair_required_cases_routed_to_p4_repair",
    "safe_display_risk_cases_not_routed_to_p8", "operation_blocker_cases_not_routed_to_p8",
    "weak_rating_or_blocker_not_treated_as_question_candidate", "question_would_make_immediate_observation_heavy_not_p8_candidate",
    "question_trigger_logic_materialized_here", "question_observation_guard_does_not_create_question_text",
    "question_observation_guard_does_not_start_p8", "consistency_guard_does_not_create_disposal_or_evidence_complete",
    "actual_review_evidence_complete_from_real_review_still_false",
    "disposal_purge_receipt_intake_allowed_next", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "post_pmn23_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)


def _dmh_op12_count_nested_values(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
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


def _dmh_op12_clean_ref_list(value: Any, *, allowed: Sequence[str] | None = None, max_length: int = 180) -> list[str]:
    if value is None or isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        return []
    cleaned: list[str] = []
    for item in value:
        ref = _clean_ref(item, default="", max_length=max_length)
        if ref and (allowed is None or ref in allowed):
            cleaned.append(ref)
    return cleaned


def _dmh_op12_normalize_question_need_rows(
    sanitized_rows: Sequence[Mapping[str, Any]],
    rating_rows: Sequence[Mapping[str, Any]],
    *,
    review_session_id: str,
    operation_receipt_ref: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    blockers: list[str] = []
    rating_by_case: dict[str, Mapping[str, Any]] = {}
    for row in rating_rows:
        if isinstance(row, Mapping):
            rating_by_case[_clean_ref(row.get("case_ref_id"), default="", max_length=180)] = row
    rows: list[dict[str, Any]] = []
    plus_cases: list[str] = []
    premium_cases: list[str] = []
    p8_cases: list[str] = []
    seen_case: set[str] = set()
    seen_blind: set[str] = set()
    seen_packet: set[str] = set()
    for index, source_row in enumerate(sanitized_rows, start=1):
        case_ref = _clean_ref(source_row.get("case_ref_id"), default="", max_length=180)
        blind_id = _clean_ref(source_row.get("blind_case_id"), default="", max_length=180)
        packet_ref = _clean_ref(source_row.get("packet_ref_id"), default="", max_length=180)
        seen_case.add(case_ref)
        seen_blind.add(blind_id)
        seen_packet.add(packet_ref)
        rating_row = rating_by_case.get(case_ref, {})
        if not rating_row:
            blockers.append("dmh_op12_rating_row_missing_for_question_case_ref")
        primary_class = _clean_ref(source_row.get("question_need_primary_class_ref"), default="insufficient_material_execution_blocker", max_length=180)
        one_question_fit_ref = _clean_ref(source_row.get("one_question_fit_ref"), default="insufficient_material", max_length=180)
        ambiguity_refs = _dmh_op12_clean_ref_list(source_row.get("ambiguity_kind_refs"), allowed=P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS)
        repair_refs = _dmh_op12_clean_ref_list(source_row.get("repair_required_refs"), allowed=P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS)
        plan_flags = source_row.get("plan_candidate_flags") if isinstance(source_row.get("plan_candidate_flags"), Mapping) else {}
        p8_candidate = bool(
            primary_class in P7_R54_AHR_POST_PMN23_DMH_OP13_P8_MATERIAL_PRIMARY_CLASS_REFS
            and one_question_fit_ref in P7_R54_AHR_POST_PMN23_DMH_OP13_P8_MATERIAL_ONE_QUESTION_FIT_REFS
        )
        plus_candidate = bool(p8_candidate and (primary_class == "plus_single_question_candidate_later" or plan_flags.get("plus_single_question_candidate_later") is True))
        premium_candidate = bool(p8_candidate and (primary_class == "premium_deep_dive_candidate_later" or plan_flags.get("premium_deep_dive_candidate_later") is True))
        if p8_candidate:
            p8_cases.append(case_ref)
        if plus_candidate:
            plus_cases.append(case_ref)
        if premium_candidate:
            premium_cases.append(case_ref)
        row: dict[str, Any] = {
            "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
            "review_session_id": review_session_id,
            "operation_receipt_ref": operation_receipt_ref,
            "question_need_row_ref": f"post_pmn23_dmh_op12_question_need_observation_row_{index:03d}_bodyfree",
            "source_review_result_row_ref": _clean_ref(source_row.get("review_result_row_ref"), default=f"post_pmn23_dmh_op10_actual_review_result_row_{index:03d}_bodyfree", max_length=220),
            "source_rating_row_ref": _clean_ref(rating_row.get("rating_row_ref"), default=f"post_pmn23_dmh_op11_rating_row_{index:03d}_bodyfree", max_length=220),
            "case_ref_id": case_ref,
            "blind_case_id": blind_id,
            "packet_ref_id": packet_ref,
            "question_need_primary_class_ref": primary_class,
            "ambiguity_kind_refs": ambiguity_refs,
            "one_question_fit_ref": one_question_fit_ref,
            "repair_required_refs": repair_refs,
            "p8_material_candidate_only": p8_candidate,
            "plus_single_question_candidate_later": plus_candidate,
            "premium_deep_dive_candidate_later": premium_candidate,
            "p8_material_candidate_blocked_by_blocker": False,
            "question_text_materialized_here": False,
            "draft_question_text_materialized_here": False,
            "question_trigger_logic_materialized_here": False,
            "question_answer_storage_materialized_here": False,
            "p8_implementation_spec_finalized_here": False,
            "p8_start_allowed": False,
            "body_free": True,
        }
        row.update({flag_ref: False for flag_ref in P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_OBSERVATION_ROW_BODYFREE_FALSE_FLAG_REFS})
        rows.append(row)
    if len(sanitized_rows) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op12_source_sanitized_review_result_row_count_not_24")
    if len(rating_rows) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op12_source_rating_row_count_not_24")
    if len(seen_case) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op12_case_ref_ids_not_unique_or_not_24")
    if len(seen_blind) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op12_blind_case_ids_not_unique_or_not_24")
    if len(seen_packet) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op12_packet_ref_ids_not_unique_or_not_24")
    summary = {
        "question_need_primary_class_counts": _dmh_op12_count_nested_values(rows, "question_need_primary_class_ref"),
        "ambiguity_kind_counts": _dmh_op12_count_nested_values(rows, "ambiguity_kind_refs"),
        "one_question_fit_counts": _dmh_op12_count_nested_values(rows, "one_question_fit_ref"),
        "repair_required_ref_counts": _dmh_op12_count_nested_values(rows, "repair_required_refs"),
        "p8_cases": sorted(set(p8_cases)),
        "plus_cases": sorted(set(plus_cases)),
        "premium_cases": sorted(set(premium_cases)),
        "case_ref_ids": sorted(seen_case),
        "blind_case_ids": sorted(seen_blind),
        "packet_ref_ids": sorted(seen_packet),
    }
    return rows, summary, list(dict.fromkeys(blockers))


def _dmh_op12_blockers(op11: Mapping[str, Any] | None, op10: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op11, Mapping):
        blockers.append("dmh_op12_rating_rows_normalization_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(op11)
        except ValueError:
            blockers.append("dmh_op12_op11_rating_rows_normalization_invalid")
        if op11.get("dmh_op11_ready") is not True:
            blockers.append("dmh_op12_op11_rating_rows_normalization_not_ready")
        if op11.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF:
            blockers.append("dmh_op12_op11_next_step_not_question_need_observation")
        if op11.get("question_need_observation_row_normalization_allowed_next") is not True:
            blockers.append("dmh_op12_op11_question_observation_not_allowed_next")
    if not isinstance(op10, Mapping):
        blockers.append("dmh_op12_sanitized_review_result_rows_intake_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract(op10)
        except ValueError:
            blockers.append("dmh_op12_op10_sanitized_review_result_rows_intake_invalid")
        if op10.get("dmh_op10_ready") is not True:
            blockers.append("dmh_op12_op10_sanitized_review_result_rows_not_ready")
        if op10.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            blockers.append("dmh_op12_op10_sanitized_review_result_row_count_not_24")
    if isinstance(op11, Mapping) and _scan_forbidden_payload_key_paths(op11):
        blockers.append("dmh_op12_op11_forbidden_body_question_path_hash_key_detected")
    if isinstance(op10, Mapping) and _scan_forbidden_payload_key_paths(op10):
        blockers.append("dmh_op12_op10_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization(
    *,
    rating_rows_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    op11 = rating_rows_normalization_threshold_summary if isinstance(rating_rows_normalization_threshold_summary, Mapping) else {}
    op10 = sanitized_review_result_rows_intake if isinstance(sanitized_review_result_rows_intake, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id or op11.get("review_session_id") or op10.get("review_session_id"))
    operation_receipt_ref = _clean_ref(op11.get("operation_receipt_ref") or op10.get("op09_operation_receipt_ref"), default="", max_length=220)
    reviewer_person_ref = _clean_ref(op11.get("reviewer_person_ref") or op10.get("op09_reviewer_person_ref"), default="", max_length=160)
    blockers = _dmh_op12_blockers(op11 if op11 else None, op10 if op10 else None)
    rows_input = list(op10.get("review_result_rows") or []) if isinstance(op10, Mapping) else []
    rating_rows = list(op11.get("rating_rows") or []) if isinstance(op11, Mapping) else []
    question_rows, summary, row_blockers = _dmh_op12_normalize_question_need_rows(rows_input, rating_rows, review_session_id=session_id, operation_receipt_ref=operation_receipt_ref)
    blockers.extend(row_blockers if rows_input or rating_rows else [])
    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op11_schema_version": op11.get("schema_version", ""),
        "op11_material_ref": op11.get("material_id", ""),
        "op11_next_required_step": op11.get("next_required_step", ""),
        "op11_dmh_ready": op11.get("dmh_op11_ready") is True,
        "op11_rating_row_count": _safe_int(op11.get("rating_row_count")),
        "op11_question_need_observation_row_normalization_allowed_next": op11.get("question_need_observation_row_normalization_allowed_next") is True,
        "op10_schema_version": op10.get("schema_version", ""),
        "op10_material_ref": op10.get("material_id", ""),
        "op10_dmh_ready": op10.get("dmh_op10_ready") is True,
        "op10_sanitized_review_result_row_count": _safe_int(op10.get("sanitized_review_result_row_count")),
        "operation_receipt_ref": operation_receipt_ref,
        "reviewer_person_ref": reviewer_person_ref,
        "dmh_op12_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP12_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_STATUS_REF,
        "dmh_op12_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP12_ALLOWED_STATUS_REFS),
        "dmh_op12_ready": ready,
        "dmh_op12_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP12_READY_REASON_REFS) if ready else [],
        "dmh_op12_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP12_READY_REASON_REFS) if ready else 0,
        "dmh_op12_blocker_refs": blockers,
        "dmh_op12_blocker_ref_count": len(blockers),
        "question_need_observation_rows_normalization_ref": P7_R54_AHR_POST_PMN23_DMH_OP12_NORMALIZATION_REF,
        "question_need_observation_row_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_observation_row_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "source_sanitized_review_result_row_count": len(rows_input) if ready else 0,
        "source_rating_row_count": len(rating_rows) if ready else 0,
        "required_question_need_observation_row_count": P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "question_need_observation_row_count": len(question_rows) if ready else 0,
        "question_need_observation_row_count_is_24": len(question_rows) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else False,
        "question_need_observation_rows": question_rows if ready else [],
        "question_need_observation_row_refs": [_clean_ref(row.get("question_need_row_ref"), default="", max_length=220) for row in question_rows] if ready else [],
        "question_need_observation_row_ref_count": len(question_rows) if ready else 0,
        "case_ref_ids": summary["case_ref_ids"] if ready else [],
        "case_ref_id_count": len(summary["case_ref_ids"]) if ready else 0,
        "case_ref_ids_unique": len(summary["case_ref_ids"]) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else False,
        "blind_case_ids": summary["blind_case_ids"] if ready else [],
        "blind_case_id_count": len(summary["blind_case_ids"]) if ready else 0,
        "blind_case_ids_unique": len(summary["blind_case_ids"]) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else False,
        "packet_ref_ids": summary["packet_ref_ids"] if ready else [],
        "packet_ref_id_count": len(summary["packet_ref_ids"]) if ready else 0,
        "packet_ref_ids_unique": len(summary["packet_ref_ids"]) == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT if ready else False,
        "question_need_primary_class_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "question_need_primary_class_option_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS),
        "ambiguity_kind_option_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS),
        "one_question_fit_option_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_option_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS),
        "repair_required_option_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP07_REPAIR_REQUIRED_OPTION_REFS),
        "question_need_primary_class_counts": summary["question_need_primary_class_counts"] if ready else {},
        "ambiguity_kind_counts": summary["ambiguity_kind_counts"] if ready else {},
        "one_question_fit_counts": summary["one_question_fit_counts"] if ready else {},
        "repair_required_ref_counts": summary["repair_required_ref_counts"] if ready else {},
        "p8_material_candidate_case_refs_bodyfree_only": summary["p8_cases"] if ready else [],
        "p8_material_candidate_case_count_bodyfree_only": len(summary["p8_cases"]) if ready else 0,
        "plus_single_question_candidate_case_refs_bodyfree_only": summary["plus_cases"] if ready else [],
        "plus_single_question_candidate_case_count_bodyfree_only": len(summary["plus_cases"]) if ready else 0,
        "premium_deep_dive_candidate_case_refs_bodyfree_only": summary["premium_cases"] if ready else [],
        "premium_deep_dive_candidate_case_count_bodyfree_only": len(summary["premium_cases"]) if ready else 0,
        "p8_material_candidate_blocked_by_blocker_case_refs": [],
        "p8_material_candidate_blocked_by_blocker_case_count": 0,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "question_trigger_logic_materialized_here": False,
        "question_answer_storage_materialized_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "question_need_observation_rows_normalized_here": ready,
        "actual_question_need_observation_rows_materialized_from_actual_rows": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "rating_question_consistency_blocker_separation_allowed_next": ready,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "p8_material_candidate_only_is_not_p8_start": True,
        "dmh_op12_does_not_create_question_text_or_p8_storage": True,
        "dmh_op12_does_not_create_disposal_or_evidence_complete": True,
        "dmh_op12_does_not_start_p5_p6_p8_r52_or_release": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP12_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP12_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP12_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP12")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZATION_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF, source="P7-R54-AHR-PostPMN23-DMH-OP12")
    blockers = list(data.get("dmh_op12_blocker_refs") or [])
    expected_ready = len(blockers) == 0
    expected_status = P7_R54_AHR_POST_PMN23_DMH_OP12_READY_STATUS_REF if expected_ready else P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_STATUS_REF
    if data.get("dmh_op12_ready") is not expected_ready or data.get("dmh_op12_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 status/ready changed")
    if data.get("dmh_op12_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 blocker count changed")
    for key in (
        "actual_review_evidence_complete_from_real_review_still_false", "p8_material_candidate_only_is_not_p8_start",
        "dmh_op12_does_not_create_question_text_or_p8_storage", "dmh_op12_does_not_create_disposal_or_evidence_complete",
        "dmh_op12_does_not_start_p5_p6_p8_r52_or_release", "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP12 required true field changed: {key}")
    for key in (
        "question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_materialized_here",
        "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here", "p8_start_allowed",
        "actual_question_need_observation_rows_materialized_here", "p5_final_allowed", "p6_start_allowed",
        "r52_actual_execution_confirmed", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP12 required false field promoted: {key}")
    if expected_ready:
        for key in (
            "op11_dmh_ready", "op11_question_need_observation_row_normalization_allowed_next", "op10_dmh_ready",
            "question_need_observation_row_count_is_24", "case_ref_ids_unique", "blind_case_ids_unique", "packet_ref_ids_unique",
            "question_need_observation_rows_normalized_here", "actual_question_need_observation_rows_materialized_from_actual_rows",
            "rating_question_consistency_blocker_separation_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP12 ready field changed: {key}")
        if data.get("op11_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP12_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 OP11 next step changed")
        if data.get("question_need_observation_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT or len(data.get("question_need_observation_rows") or []) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 row count must be 24")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP12_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 implemented steps changed")
        for row in data.get("question_need_observation_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 row must be mapping")
            if set(row) != set(P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 row fields changed")
            if row.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 row schema/body-free changed")
            if row.get("question_need_primary_class_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP07_QUESTION_NEED_PRIMARY_CLASS_REFS:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 primary class changed")
            if row.get("one_question_fit_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP07_ONE_QUESTION_FIT_OPTION_REFS:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 one question fit changed")
            for flag_key in ("question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_materialized_here", "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here", "p8_start_allowed"):
                if row.get(flag_key) is not False:
                    raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 row question/p8 flag changed")
            if _scan_forbidden_payload_key_paths(row, path="dmh_op12_question_row"):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 row leaked forbidden payload key")
    else:
        if data.get("question_need_observation_rows") != [] or data.get("question_need_observation_rows_normalized_here") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 blocked material promoted rows")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP12 blocked next step changed")
    return True


def _dmh_op13_routes_to(category_ref: str) -> str:
    if category_ref == "no_blocker":
        return P7_R54_AHR_POST_PMN23_DMH_OP13_CLEAN_ROUTE_REF
    if category_ref == "p4_current_only_surface_repair_required":
        return P7_R54_AHR_POST_PMN23_DMH_OP13_P4_ROUTE_REF
    if category_ref.startswith("operation_blocked_"):
        return P7_R54_AHR_POST_PMN23_DMH_OP13_OPERATION_ROUTE_REF
    if category_ref == "inconclusive_insufficient_material":
        return P7_R54_AHR_POST_PMN23_DMH_OP13_INCONCLUSIVE_ROUTE_REF
    return P7_R54_AHR_POST_PMN23_DMH_OP13_READFEEL_ROUTE_REF


def _dmh_op13_make_blocker_row(
    *,
    seq: int,
    rating_row: Mapping[str, Any],
    question_row: Mapping[str, Any],
    review_session_id: str,
    blocker_kind_ref: str,
    blocker_category_ref: str,
    issue_reason_ref: str,
    p8_candidate: bool,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_SCHEMA_VERSION,
        "review_session_id": review_session_id,
        "consistency_blocker_row_ref": f"post_pmn23_dmh_op13_consistency_blocker_row_{seq:03d}_bodyfree",
        "case_ref_id": _clean_ref(rating_row.get("case_ref_id") or question_row.get("case_ref_id"), default="", max_length=180),
        "blind_case_id": _clean_ref(rating_row.get("blind_case_id") or question_row.get("blind_case_id"), default="", max_length=180),
        "packet_ref_id": _clean_ref(rating_row.get("packet_ref_id") or question_row.get("packet_ref_id"), default="", max_length=180),
        "source_rating_row_ref": _clean_ref(rating_row.get("rating_row_ref"), default=f"post_pmn23_dmh_op11_rating_row_{seq:03d}_bodyfree", max_length=220),
        "source_question_need_row_ref": _clean_ref(question_row.get("question_need_row_ref"), default=f"post_pmn23_dmh_op12_question_need_observation_row_{seq:03d}_bodyfree", max_length=220),
        "blocker_kind_ref": blocker_kind_ref,
        "blocker_category_ref": blocker_category_ref,
        "issue_reason_ref": _clean_ref(issue_reason_ref, default="unknown_bodyfree_blocker", max_length=220),
        "blocked_escape_to_ref": "P8_MATERIAL_CANDIDATE_ONLY" if p8_candidate else "NO_P8_ESCAPE_DETECTED_BODYFREE",
        "routes_to_ref": _dmh_op13_routes_to(blocker_category_ref),
        "p8_candidate_escape_detected": p8_candidate,
        "p8_candidate_escape_blocked": p8_candidate,
        "p8_material_candidate_after_blocker_separation": False if p8_candidate else False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "question_trigger_logic_materialized_here": False,
        "question_answer_storage_materialized_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_start_allowed": False,
        "body_free": True,
    }
    row.update({flag_ref: False for flag_ref in P7_R54_AHR_POST_PMN23_DMH_OP10_ROW_BODYFREE_FALSE_FLAG_REFS})
    return row


def _dmh_op13_case_refs_for_categories(rows: Sequence[Mapping[str, Any]], categories: set[str]) -> list[str]:
    return sorted({
        _clean_ref(row.get("case_ref_id"), default="", max_length=180)
        for row in rows
        if _clean_ref(row.get("blocker_category_ref"), default="", max_length=180) in categories
    } - {""})


def _dmh_op13_count_rows(rows: Sequence[Mapping[str, Any]], key: str, allowed: Sequence[str]) -> dict[str, int]:
    counts = {ref: 0 for ref in allowed}
    for row in rows:
        ref = _clean_ref(row.get(key), default="", max_length=180)
        if ref in counts:
            counts[ref] += 1
    return counts


def _dmh_op13_build_blocker_rows(
    rating_rows: Sequence[Mapping[str, Any]],
    question_rows: Sequence[Mapping[str, Any]],
    *,
    review_session_id: str,
) -> tuple[list[dict[str, Any]], list[str], dict[str, list[str]], dict[str, int]]:
    blockers: list[str] = []
    question_by_case = {_clean_ref(row.get("case_ref_id"), default="", max_length=180): row for row in question_rows if isinstance(row, Mapping)}
    rows: list[dict[str, Any]] = []
    p8_candidate_cases: set[str] = set()
    blocked_p8_cases: set[str] = set()
    seq = 1
    reason_counts = {
        "below_target_axis": 0,
        "safe_display": 0,
        "readfeel": 0,
        "execution": 0,
        "insufficient": 0,
        "heavy_observation": 0,
        "repair_required": 0,
        "verdict_blocker": 0,
    }
    if len(rating_rows) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op13_source_rating_row_count_not_24")
    if len(question_rows) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
        blockers.append("dmh_op13_source_question_need_observation_row_count_not_24")
    for rating_row in rating_rows:
        if not isinstance(rating_row, Mapping):
            blockers.append("dmh_op13_source_rating_row_not_mapping")
            continue
        if _scan_forbidden_payload_key_paths(rating_row, path="dmh_op13_rating_row"):
            blockers.append("dmh_op13_source_rating_row_forbidden_body_question_path_hash_key")
            continue
        case_ref = _clean_ref(rating_row.get("case_ref_id"), default="", max_length=180)
        question_row = question_by_case.get(case_ref, {})
        if not question_row:
            blockers.append("dmh_op13_question_need_row_missing_for_rating_case_ref")
            continue
        if _scan_forbidden_payload_key_paths(question_row, path="dmh_op13_question_row"):
            blockers.append("dmh_op13_source_question_row_forbidden_body_question_path_hash_key")
            continue
        p8_candidate = question_row.get("p8_material_candidate_only") is True
        if p8_candidate:
            p8_candidate_cases.add(case_ref)
        case_rows_before = len(rows)
        for blocker_id in _dmh_op12_clean_ref_list(rating_row.get("readfeel_blocker_ids")):
            category = P7_R54_AHR_POST_PMN23_DMH_OP13_READFEEL_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                blockers.append("dmh_op13_readfeel_blocker_id_not_allowed")
                continue
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="readfeel_blocker", blocker_category_ref=category, issue_reason_ref=blocker_id, p8_candidate=p8_candidate))
            seq += 1
            reason_counts["readfeel"] += 1 if p8_candidate else 0
        for blocker_id in _dmh_op12_clean_ref_list(rating_row.get("execution_blocker_ids")):
            category = P7_R54_AHR_POST_PMN23_DMH_OP13_EXECUTION_BLOCKER_CATEGORY_BY_ID.get(blocker_id)
            if not category:
                blockers.append("dmh_op13_execution_blocker_id_not_allowed")
                continue
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="execution_blocker", blocker_category_ref=category, issue_reason_ref=blocker_id, p8_candidate=p8_candidate))
            seq += 1
            reason_counts["execution"] += 1 if p8_candidate else 0
        for repair_ref in _dmh_op12_clean_ref_list(question_row.get("repair_required_refs")):
            if repair_ref == "no_repair_required":
                continue
            category = P7_R54_AHR_POST_PMN23_DMH_OP13_REPAIR_CATEGORY_BY_REF.get(repair_ref)
            if not category:
                blockers.append("dmh_op13_repair_required_ref_not_allowed")
                continue
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="repair_required", blocker_category_ref=category, issue_reason_ref=repair_ref, p8_candidate=p8_candidate))
            seq += 1
            reason_counts["repair_required"] += 1 if p8_candidate else 0
        for axis_ref in _dmh_op12_clean_ref_list(rating_row.get("below_target_axis_refs")):
            category = P7_R54_AHR_POST_PMN23_DMH_OP13_BELOW_TARGET_AXIS_CATEGORY_BY_REF.get(axis_ref)
            if not category:
                continue
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="below_target_axis", blocker_category_ref=category, issue_reason_ref=f"below_target_axis_{axis_ref}", p8_candidate=p8_candidate))
            seq += 1
            reason_counts["below_target_axis"] += 1 if p8_candidate else 0
        for safe_ref in _dmh_op12_clean_ref_list(rating_row.get("safe_display_check_refs")):
            if safe_ref in P7_R54_AHR_POST_PMN23_DMH_OP13_SAFE_DISPLAY_RISK_CHECK_REFS:
                rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="safe_display_risk", blocker_category_ref="p5_safe_display_risk", issue_reason_ref=safe_ref, p8_candidate=p8_candidate))
                seq += 1
                reason_counts["safe_display"] += 1 if p8_candidate else 0
        verdict_ref = _clean_ref(rating_row.get("verdict_ref"), default="", max_length=80)
        if verdict_ref == "RED":
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="verdict_blocker", blocker_category_ref="p5_readfeel_repair_required", issue_reason_ref="verdict_red", p8_candidate=p8_candidate))
            seq += 1
            reason_counts["verdict_blocker"] += 1 if p8_candidate else 0
        if verdict_ref in {"BLOCKED", "NOT_REVIEWABLE"}:
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="inconclusive_material", blocker_category_ref="inconclusive_insufficient_material", issue_reason_ref=f"verdict_{verdict_ref.lower()}", p8_candidate=p8_candidate))
            seq += 1
            reason_counts["insufficient"] += 1 if p8_candidate else 0
        primary_class = _clean_ref(question_row.get("question_need_primary_class_ref"), default="", max_length=180)
        if primary_class == "insufficient_material_execution_blocker":
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="inconclusive_material", blocker_category_ref="inconclusive_insufficient_material", issue_reason_ref=primary_class, p8_candidate=p8_candidate))
            seq += 1
            reason_counts["insufficient"] += 1 if p8_candidate else 0
        if primary_class == "question_would_make_immediate_observation_heavy" and p8_candidate:
            rows.append(_dmh_op13_make_blocker_row(seq=seq, rating_row=rating_row, question_row=question_row, review_session_id=review_session_id, blocker_kind_ref="heavy_observation", blocker_category_ref="p5_readfeel_repair_required", issue_reason_ref=primary_class, p8_candidate=p8_candidate))
            seq += 1
            reason_counts["heavy_observation"] += 1
        if len(rows) > case_rows_before and p8_candidate:
            blocked_p8_cases.add(case_ref)
    all_blocker_cases = sorted({_clean_ref(row.get("case_ref_id"), default="", max_length=180) for row in rows} - {""})
    allowed_p8_cases = sorted(p8_candidate_cases - blocked_p8_cases)
    return rows, list(dict.fromkeys(blockers)), {
        "p8_candidate_cases": sorted(p8_candidate_cases),
        "blocked_p8_cases": sorted(blocked_p8_cases),
        "allowed_p8_cases": allowed_p8_cases,
        "all_blocker_cases": all_blocker_cases,
    }, reason_counts


def _dmh_op13_blockers(op12: Mapping[str, Any] | None, op11: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op12, Mapping):
        blockers.append("dmh_op13_question_need_observation_rows_normalization_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract(op12)
        except ValueError:
            blockers.append("dmh_op13_op12_question_need_observation_rows_normalization_invalid")
        if op12.get("dmh_op12_ready") is not True:
            blockers.append("dmh_op13_op12_question_need_observation_rows_not_ready")
        if op12.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF:
            blockers.append("dmh_op13_op12_next_step_not_rating_question_consistency")
        if op12.get("rating_question_consistency_blocker_separation_allowed_next") is not True:
            blockers.append("dmh_op13_op12_consistency_not_allowed_next")
    if not isinstance(op11, Mapping):
        blockers.append("dmh_op13_rating_rows_normalization_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract(op11)
        except ValueError:
            blockers.append("dmh_op13_op11_rating_rows_normalization_invalid")
        if op11.get("dmh_op11_ready") is not True:
            blockers.append("dmh_op13_op11_rating_rows_not_ready")
        if op11.get("rating_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            blockers.append("dmh_op13_op11_rating_row_count_not_24")
    if isinstance(op12, Mapping) and _scan_forbidden_payload_key_paths(op12):
        blockers.append("dmh_op13_op12_forbidden_body_question_path_hash_key_detected")
    if isinstance(op11, Mapping) and _scan_forbidden_payload_key_paths(op11):
        blockers.append("dmh_op13_op11_forbidden_body_question_path_hash_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation(
    *,
    question_need_observation_rows_normalization: Mapping[str, Any] | None = None,
    rating_rows_normalization_threshold_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    op12 = question_need_observation_rows_normalization if isinstance(question_need_observation_rows_normalization, Mapping) else {}
    op11 = rating_rows_normalization_threshold_summary if isinstance(rating_rows_normalization_threshold_summary, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id or op12.get("review_session_id") or op11.get("review_session_id"))
    operation_receipt_ref = _clean_ref(op12.get("operation_receipt_ref") or op11.get("operation_receipt_ref"), default="", max_length=220)
    blockers = _dmh_op13_blockers(op12 if op12 else None, op11 if op11 else None)
    rating_rows = list(op11.get("rating_rows") or []) if isinstance(op11, Mapping) else []
    question_rows = list(op12.get("question_need_observation_rows") or []) if isinstance(op12, Mapping) else []
    consistency_rows, row_blockers, case_summary, reason_counts = _dmh_op13_build_blocker_rows(rating_rows, question_rows, review_session_id=session_id)
    blockers.extend(row_blockers if rating_rows or question_rows else [])
    blockers = list(dict.fromkeys(blockers))
    ready = not blockers
    kind_counts = _dmh_op13_count_rows(consistency_rows, "blocker_kind_ref", P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_KIND_REFS) if ready else {kind: 0 for kind in P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_KIND_REFS}
    category_counts = _dmh_op13_count_rows(consistency_rows, "blocker_category_ref", P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_CATEGORY_REFS) if ready else {cat: 0 for cat in P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_CATEGORY_REFS}
    p5_cases = _dmh_op13_case_refs_for_categories(consistency_rows, {"p5_readfeel_repair_required", "p5_history_connection_weak", "p5_creepy_or_overclaim_risk", "p5_self_blame_amplification_risk", "p5_safe_display_risk"}) if ready else []
    p4_cases = _dmh_op13_case_refs_for_categories(consistency_rows, {"p4_current_only_surface_repair_required"}) if ready else []
    operation_cases = _dmh_op13_case_refs_for_categories(consistency_rows, {"operation_blocked_missing_receipt", "operation_blocked_body_leak", "operation_blocked_question_text", "operation_blocked_disposal_missing", "operation_blocked_no_touch_violation"}) if ready else []
    safe_cases = _dmh_op13_case_refs_for_categories(consistency_rows, {"p5_safe_display_risk"}) if ready else []
    inconclusive_cases = _dmh_op13_case_refs_for_categories(consistency_rows, {"inconclusive_insufficient_material"}) if ready else []
    all_case_refs = sorted({_clean_ref(row.get("case_ref_id"), default="", max_length=180) for row in question_rows if isinstance(row, Mapping)} - {""})
    no_blocker_cases = sorted(set(all_case_refs) - set(case_summary["all_blocker_cases"])) if ready else []
    category_counts["no_blocker"] = len(no_blocker_cases) if ready else 0
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP13_RATING_QUESTION_CONSISTENCY_BLOCKER_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op12_schema_version": op12.get("schema_version", ""),
        "op12_material_ref": op12.get("material_id", ""),
        "op12_next_required_step": op12.get("next_required_step", ""),
        "op12_dmh_ready": op12.get("dmh_op12_ready") is True,
        "op12_question_need_observation_row_count": _safe_int(op12.get("question_need_observation_row_count")),
        "op12_p8_material_candidate_case_count_bodyfree_only": _safe_int(op12.get("p8_material_candidate_case_count_bodyfree_only")),
        "op12_p8_start_allowed": op12.get("p8_start_allowed") is True,
        "op11_schema_version": op11.get("schema_version", ""),
        "op11_material_ref": op11.get("material_id", ""),
        "op11_dmh_ready": op11.get("dmh_op11_ready") is True,
        "op11_rating_row_count": _safe_int(op11.get("rating_row_count")),
        "operation_receipt_ref": operation_receipt_ref,
        "dmh_op13_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP13_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_STATUS_REF,
        "dmh_op13_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP13_ALLOWED_STATUS_REFS),
        "dmh_op13_ready": ready,
        "rating_question_consistency_guard_passed": ready,
        "dmh_op13_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP13_READY_REASON_REFS) if ready else [],
        "dmh_op13_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP13_READY_REASON_REFS) if ready else 0,
        "dmh_op13_blocker_refs": blockers,
        "dmh_op13_blocker_ref_count": len(blockers),
        "rating_question_consistency_blocker_separation_ref": P7_R54_AHR_POST_PMN23_DMH_OP13_GUARD_REF,
        "consistency_blocker_row_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "consistency_blocker_row_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "consistency_blocker_rows": consistency_rows if ready else [],
        "consistency_blocker_row_count": len(consistency_rows) if ready else 0,
        "consistency_blocker_row_refs": [_clean_ref(row.get("consistency_blocker_row_ref"), default="", max_length=220) for row in consistency_rows] if ready else [],
        "consistency_blocker_row_ref_count": len(consistency_rows) if ready else 0,
        "blocker_kind_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_KIND_REFS),
        "blocker_kind_counts": kind_counts,
        "blocker_category_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_CATEGORY_REFS),
        "blocker_category_counts": category_counts,
        "p8_material_candidate_case_refs_bodyfree_only": case_summary["p8_candidate_cases"] if ready else [],
        "p8_material_candidate_case_count_bodyfree_only": len(case_summary["p8_candidate_cases"]) if ready else 0,
        "p8_material_candidate_blocked_by_blocker_case_refs": case_summary["blocked_p8_cases"] if ready else [],
        "p8_material_candidate_blocked_by_blocker_case_count": len(case_summary["blocked_p8_cases"]) if ready else 0,
        "p8_material_candidate_allowed_after_blocker_separation_case_refs": case_summary["allowed_p8_cases"] if ready else [],
        "p8_material_candidate_allowed_after_blocker_separation_case_count": len(case_summary["allowed_p8_cases"]) if ready else 0,
        "no_blocker_case_refs": no_blocker_cases,
        "no_blocker_case_count": len(no_blocker_cases),
        "p5_repair_required_case_refs": p5_cases,
        "p5_repair_required_case_count": len(p5_cases),
        "p4_current_only_repair_required_case_refs": p4_cases,
        "p4_current_only_repair_required_case_count": len(p4_cases),
        "operation_blocked_case_refs": operation_cases,
        "operation_blocked_case_count": len(operation_cases),
        "safe_display_blocked_case_refs": safe_cases,
        "safe_display_blocked_case_count": len(safe_cases),
        "inconclusive_case_refs": inconclusive_cases,
        "inconclusive_case_count": len(inconclusive_cases),
        "below_target_axis_p8_escape_blocked_count": reason_counts["below_target_axis"] if ready else 0,
        "safe_display_question_escape_blocked_count": reason_counts["safe_display"] if ready else 0,
        "readfeel_blocker_question_escape_blocked_count": reason_counts["readfeel"] if ready else 0,
        "execution_blocker_question_escape_blocked_count": reason_counts["execution"] if ready else 0,
        "insufficient_material_question_escape_blocked_count": reason_counts["insufficient"] if ready else 0,
        "heavy_observation_p8_escape_blocked_count": reason_counts["heavy_observation"] if ready else 0,
        "repair_required_question_escape_blocked_count": reason_counts["repair_required"] if ready else 0,
        "verdict_blocker_p8_escape_blocked_count": reason_counts["verdict_blocker"] if ready else 0,
        "rating_question_consistency_checked_here": ready,
        "rating_question_consistency_guard_blocks_p8_escape": ready,
        "p5_repair_required_cases_routed_to_p5_repair": ready,
        "p4_repair_required_cases_routed_to_p4_repair": ready,
        "safe_display_risk_cases_not_routed_to_p8": ready,
        "operation_blocker_cases_not_routed_to_p8": ready,
        "weak_rating_or_blocker_not_treated_as_question_candidate": ready,
        "question_would_make_immediate_observation_heavy_not_p8_candidate": ready,
        "question_trigger_logic_materialized_here": False,
        "question_observation_guard_does_not_create_question_text": True,
        "question_observation_guard_does_not_start_p8": True,
        "consistency_guard_does_not_create_disposal_or_evidence_complete": True,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "disposal_purge_receipt_intake_allowed_next": ready,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP13_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP13_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP12_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP13_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP13_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP13")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_PMN23_DMH_OP13_RATING_QUESTION_CONSISTENCY_BLOCKER_SEPARATION_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF, source="P7-R54-AHR-PostPMN23-DMH-OP13")
    blockers = list(data.get("dmh_op13_blocker_refs") or [])
    expected_ready = len(blockers) == 0
    expected_status = P7_R54_AHR_POST_PMN23_DMH_OP13_READY_STATUS_REF if expected_ready else P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_STATUS_REF
    if data.get("dmh_op13_ready") is not expected_ready or data.get("dmh_op13_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 status/ready changed")
    if data.get("dmh_op13_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker count changed")
    for key in (
        "question_observation_guard_does_not_create_question_text", "question_observation_guard_does_not_start_p8",
        "consistency_guard_does_not_create_disposal_or_evidence_complete", "actual_review_evidence_complete_from_real_review_still_false",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP13 required true field changed: {key}")
    for key in (
        "question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_materialized_here",
        "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here", "p8_start_allowed",
        "actual_review_evidence_complete_from_real_review", "p5_final_allowed", "p6_start_allowed",
        "r52_actual_execution_confirmed", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP13 required false field promoted: {key}")
    if expected_ready:
        for key in (
            "op12_dmh_ready", "op11_dmh_ready", "rating_question_consistency_guard_passed",
            "rating_question_consistency_checked_here", "rating_question_consistency_guard_blocks_p8_escape",
            "p5_repair_required_cases_routed_to_p5_repair", "p4_repair_required_cases_routed_to_p4_repair",
            "safe_display_risk_cases_not_routed_to_p8", "operation_blocker_cases_not_routed_to_p8",
            "weak_rating_or_blocker_not_treated_as_question_candidate", "question_would_make_immediate_observation_heavy_not_p8_candidate",
            "disposal_purge_receipt_intake_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP13 ready field changed: {key}")
        if data.get("op12_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP13_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 OP12 next step changed")
        if data.get("op12_p8_start_allowed") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 OP12 p8 start promoted")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP13_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 implemented steps changed")
        if tuple(data.get("consistency_blocker_row_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_REQUIRED_FIELD_REFS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row field refs changed")
        if data.get("consistency_blocker_row_count") != len(data.get("consistency_blocker_rows") or []):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row count changed")
        for row in data.get("consistency_blocker_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row must be mapping")
            if set(row) != set(P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_REQUIRED_FIELD_REFS):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row fields changed")
            if row.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_SCHEMA_VERSION or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row schema/body-free changed")
            if row.get("blocker_kind_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_KIND_REFS or row.get("blocker_category_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKER_CATEGORY_REFS:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row kind/category changed")
            for flag_ref in P7_R54_AHR_POST_PMN23_DMH_OP13_CONSISTENCY_BLOCKER_ROW_FALSE_FLAG_REFS:
                if row.get(flag_ref) is not False:
                    raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row question/p8 flag changed")
            if _scan_forbidden_payload_key_paths(row, path="dmh_op13_blocker_row"):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocker row leaked forbidden payload key")
    else:
        if data.get("rating_question_consistency_guard_passed") is not False or data.get("disposal_purge_receipt_intake_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocked material promoted guard")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP13 blocked next step changed")
    return True


build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_question_need_observation_rows_normalization_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_question_need_observation_rows_normalization_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_question_consistency_blocker_separation_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_rating_question_consistency_blocker_separation_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract
)


# ---------------------------------------------------------------------------
# DMH-OP14 / DMH-OP15 disposal receipt intake and final no-leak/no-touch guard
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op14_disposal_purge_receipt_intake.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op14_disposal_receipt.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP15_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op15_final_no_body_no_question_no_path_no_hash_no_touch_validation.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[15]
P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[16]

P7_R54_AHR_POST_PMN23_DMH_OP14_READY_STATUS_REF: Final = (
    "DMH_OP14_DISPOSAL_PURGE_RECEIPT_INTAKED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_STATUS_REF: Final = (
    "DMH_OP14_DISPOSAL_PURGE_RECEIPT_INTAKE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "DMH_OP14_DISPOSAL_PURGE_RECEIPT_INTAKE_BLOCKED_BY_BODY_QUESTION_PATH_HASH_OR_NOTES_LEAK"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP14_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op14_disposal_purge_receipt_intake_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_INTAKE_REF: Final = (
    "post_pmn23_dmh_op14_disposal_purge_receipt_intake_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_DEFAULT_DISPOSAL_RECEIPT_REF: Final = (
    "post_pmn23_dmh_op14_disposal_receipt_ref_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    "BODY_PURGED",
    "ABORTED_BODY_PURGED",
)
P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_ACTUAL_SOURCE_REF: Final = "actual_local_disposal_receipt_bodyfree"
P7_R54_AHR_POST_PMN23_DMH_OP14_DEFAULT_RETENTION_POLICY_REF: Final = (
    "local_body_full_packet_same_day_or_shorter_purge_required"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_DEFAULT_EXPIRATION_POLICY_REF: Final = (
    "post_review_body_full_packet_temporary_form_and_notes_purged"
)
P7_R54_AHR_POST_PMN23_DMH_OP14_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op13_rating_question_consistency_guard_passed_bodyfree",
    "actual_local_disposal_receipt_received_bodyfree",
    "disposal_status_is_body_purged_or_aborted_body_purged",
    "body_notes_and_temporary_form_removed_without_question_path_or_hash",
    "final_no_body_no_question_no_path_no_hash_no_touch_validation_required_next_without_evidence_complete",
)

P7_R54_AHR_POST_PMN23_DMH_OP15_READY_STATUS_REF: Final = (
    "DMH_OP15_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_STATUS_REF: Final = (
    "DMH_OP15_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_BY_LEAK_STATUS_REF: Final = (
    "DMH_OP15_FINAL_VALIDATION_BLOCKED_BY_BODY_QUESTION_PATH_HASH_OR_NO_TOUCH_LEAK"
)
P7_R54_AHR_POST_PMN23_DMH_OP15_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP15_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_BY_LEAK_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op15_final_bodyfree_no_leak_no_touch_validation_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP15_VALIDATION_REF: Final = (
    "post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP15_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op14_disposal_purge_receipt_intaked_bodyfree",
    "no_body_or_packet_or_reviewer_notes_body_detected",
    "no_question_text_or_draft_question_text_detected",
    "no_local_path_or_body_hash_detected",
    "no_terminal_output_body_detected",
    "api_db_rn_runtime_response_key_p8_r52_release_no_touch_preserved",
    "actual_review_evidence_complete_predicate_required_next_without_auto_promotion",
)

P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "question_text_included",
    "draft_question_text_included",
    "terminal_output_body_included",
    "pause_abort_status_ref",
    "retention_policy_ref",
    "expiration_policy_ref",
    "actual_source_ref",
    "body_free",
)
P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op13_schema_version", "op13_material_ref", "op13_next_required_step", "op13_dmh_ready",
    "op13_rating_question_consistency_guard_passed", "op13_consistency_blocker_row_count", "op13_operation_receipt_ref",
    "op13_disposal_purge_receipt_intake_allowed_next", "dmh_op14_status_ref", "dmh_op14_allowed_status_refs",
    "dmh_op14_ready", "disposal_purge_receipt_accepted", "dmh_op14_reason_refs", "dmh_op14_reason_ref_count",
    "dmh_op14_blocker_refs", "dmh_op14_blocker_ref_count", "disposal_purge_receipt_intake_ref",
    "disposal_receipt_required_field_refs", "disposal_receipt_required_field_ref_count", "disposal_receipt_ref",
    "disposal_receipt_ref_present", "disposal_receipt_ref_is_bodyfree_ref", "disposal_receipt_ref_has_local_path_shape",
    "disposal_receipt_received_here", "disposal_receipt_intaked_here", "operation_receipt_ref",
    "operation_receipt_ref_matches_op13", "disposal_status_ref", "disposal_status_allowed_refs",
    "disposal_status_is_body_purged_or_aborted_body_purged", "packet_materialized_for_review", "body_removed",
    "reviewer_notes_removed", "temporary_form_removed", "content_hash_of_body_stored", "body_hash_stored",
    "local_absolute_path_included", "reviewer_notes_body_stored", "question_text_included", "draft_question_text_included",
    "terminal_output_body_included", "pause_abort_status_ref", "retention_policy_ref", "expiration_policy_ref",
    "actual_source_ref", "actual_source_allowed_ref", "actual_source_guard_passed", "disposal_receipt_bodyfree_only",
    "forbidden_disposal_receipt_payload_key_paths", "forbidden_disposal_receipt_payload_key_path_count",
    "body_full_packet_lifecycle_closed_bodyfree", "body_removed_without_hash_path_question_or_reviewer_notes",
    "temporary_form_removed_without_export", "disposal_receipt_does_not_store_body_hash_or_local_path",
    "disposal_receipt_does_not_store_reviewer_notes_body", "disposal_receipt_does_not_create_question_text",
    "disposal_receipt_does_not_store_terminal_output_body", "actual_disposal_receipt_materialized_here",
    "disposal_verified", "disposal_receipt_ready_for_final_no_leak_validation_only",
    "actual_review_evidence_complete_from_real_review_still_false", "dmh_op14_does_not_run_disposal_here",
    "dmh_op14_does_not_complete_evidence", "dmh_op14_does_not_start_p5_p6_p8_r52_or_release",
    "dmh_op14_does_not_execute_postcr22_ex_reentry", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_pmn23_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_PMN23_DMH_OP15_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op14_schema_version", "op14_material_ref", "op14_next_required_step", "op14_dmh_ready",
    "op14_disposal_purge_receipt_accepted", "op14_disposal_receipt_ref", "op14_disposal_status_ref",
    "op14_disposal_receipt_ready_for_final_no_leak_validation_only", "op14_actual_review_evidence_complete_still_false",
    "dmh_op15_status_ref", "dmh_op15_allowed_status_refs", "dmh_op15_ready", "dmh_op15_reason_refs",
    "dmh_op15_reason_ref_count", "dmh_op15_blocker_refs", "dmh_op15_blocker_ref_count", "final_no_leak_validation_ref",
    "validated_artifact_refs", "validated_artifact_ref_count", "validation_scope_refs", "validation_scope_ref_count",
    "forbidden_payload_key_paths", "forbidden_payload_key_path_count", "body_leak_flag_paths", "body_leak_flag_path_count",
    "question_text_flag_paths", "question_text_flag_path_count", "path_hash_flag_paths", "path_hash_flag_path_count",
    "terminal_output_body_flag_paths", "terminal_output_body_flag_path_count", "no_touch_violation_paths",
    "no_touch_violation_path_count", "no_body_leak_validation_passed", "no_question_text_validation_passed",
    "no_path_hash_validation_passed", "no_terminal_output_body_validation_passed", "no_touch_validation_passed",
    "final_no_leak_validation_passed", "body_free_artifacts_only", "disposal_verified", "disposal_verified_by_op15_validation_only",
    "actual_review_evidence_complete_predicate_allowed_next", "actual_review_evidence_complete_from_real_review_still_false",
    "actual_review_evidence_complete_from_real_review", "question_text_materialized_here", "draft_question_text_materialized_here",
    "p8_start_allowed", "dmh_op15_does_not_execute_disposal_here", "dmh_op15_does_not_create_or_export_body_full_packet",
    "dmh_op15_does_not_create_question_text", "dmh_op15_does_not_change_api_db_rn_runtime_response_key",
    "dmh_op15_does_not_complete_evidence", "dmh_op15_does_not_start_p5_p6_p8_r52_or_release",
    "dmh_op15_does_not_execute_postcr22_ex_reentry", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_pmn23_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:15]
P7_R54_AHR_POST_PMN23_DMH_OP14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[15:]
P7_R54_AHR_POST_PMN23_DMH_OP15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:16]
P7_R54_AHR_POST_PMN23_DMH_OP15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[16:]

P7_R54_AHR_POST_PMN23_DMH_OP15_VALIDATION_SCOPE_REFS: Final[tuple[str, ...]] = (
    "scope_material_bodyfree_boundary",
    "pmn_op23_hold_intake_material_bodyfree_boundary",
    "explicit_allow_receipt_bodyfree_boundary",
    "packet_generation_receipt_bodyfree_boundary",
    "packet_scan_receipt_bodyfree_boundary",
    "actual_operation_receipt_bodyfree_boundary",
    "sanitized_review_result_rows_bodyfree_boundary",
    "rating_rows_bodyfree_boundary",
    "question_need_rows_bodyfree_boundary",
    "disposal_receipt_bodyfree_boundary",
    "evidence_completion_summary_not_yet_materialized_boundary",
    "result_memo_envelope_bodyfree_boundary",
)
P7_R54_AHR_POST_PMN23_DMH_OP15_BODY_LEAK_FLAG_REFS: Final[tuple[str, ...]] = (
    "raw_input_included", "input_body_included", "returned_emlis_body_included", "history_body_included",
    "comment_text_body_included", "reviewer_free_text_included", "reviewer_notes_body_included",
    "packet_content_included", "body_full_packet_content_included", "packet_material_included",
)
P7_R54_AHR_POST_PMN23_DMH_OP15_QUESTION_FLAG_REFS: Final[tuple[str, ...]] = (
    "question_text_included", "draft_question_text_included", "question_text_materialized_here",
    "draft_question_text_materialized_here", "question_trigger_logic_materialized_here",
    "question_answer_storage_materialized_here", "p8_implementation_spec_finalized_here",
)
P7_R54_AHR_POST_PMN23_DMH_OP15_PATH_HASH_FLAG_REFS: Final[tuple[str, ...]] = (
    "local_absolute_path_included", "local_path_included", "body_hash_included", "body_hash_stored",
    "content_hash_of_body_stored", "local_review_root_path_included", "disposal_receipt_ref_has_local_path_shape",
)
P7_R54_AHR_POST_PMN23_DMH_OP15_TERMINAL_FLAG_REFS: Final[tuple[str, ...]] = (
    "terminal_output_body_included", "stdout_body_included", "stderr_body_included", "traceback_body_included",
)
P7_R54_AHR_POST_PMN23_DMH_OP15_NO_TOUCH_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed",
    "public_response_top_level_key_added", "user_label_connection_runtime_changed", "p8_question_design_started",
    "p8_question_implementation_started", "p8_question_api_created", "p8_question_db_created", "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created", "r52_reintake_execution_started_here", "release_allowed",
)


def build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_bodyfree(
    *,
    review_session_id: Any = None,
    operation_receipt_ref: Any = None,
    disposal_receipt_ref: Any = None,
    disposal_status_ref: Any = "BODY_PURGED",
    packet_materialized_for_review: bool = True,
    body_removed: bool = True,
    reviewer_notes_removed: bool = True,
    temporary_form_removed: bool = True,
    content_hash_of_body_stored: bool = False,
    body_hash_stored: bool = False,
    local_absolute_path_included: bool = False,
    reviewer_notes_body_stored: bool = False,
    question_text_included: bool = False,
    draft_question_text_included: bool = False,
    terminal_output_body_included: bool = False,
    pause_abort_status_ref: Any = "DMH_REVIEW_COMPLETED_SELECTION_ROWS_READY_TO_BODY_PURGED",
    retention_policy_ref: Any = None,
    expiration_policy_ref: Any = None,
    actual_source_ref: Any = None,
) -> dict[str, Any]:
    """Build a body-free OP14 disposal/purge receipt shape.

    The receipt is an intake shape only.  It records that a local operation says
    body material was removed, but this helper still does not execute disposal,
    store a body hash/path, or complete actual evidence.
    """

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "disposal_receipt_ref": _clean_ref(
            disposal_receipt_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP14_DEFAULT_DISPOSAL_RECEIPT_REF,
            max_length=220,
        ),
        "review_session_id": session_id,
        "operation_receipt_ref": _clean_ref(
            operation_receipt_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP09_OPERATION_RECEIPT_REF,
            max_length=220,
        ),
        "disposal_status_ref": _clean_ref(disposal_status_ref, default="", max_length=120),
        "packet_materialized_for_review": packet_materialized_for_review,
        "body_removed": body_removed,
        "reviewer_notes_removed": reviewer_notes_removed,
        "temporary_form_removed": temporary_form_removed,
        "content_hash_of_body_stored": content_hash_of_body_stored,
        "body_hash_stored": body_hash_stored,
        "local_absolute_path_included": local_absolute_path_included,
        "reviewer_notes_body_stored": reviewer_notes_body_stored,
        "question_text_included": question_text_included,
        "draft_question_text_included": draft_question_text_included,
        "terminal_output_body_included": terminal_output_body_included,
        "pause_abort_status_ref": _clean_ref(pause_abort_status_ref, default="DMH_PURGE_STATUS_BODYFREE", max_length=180),
        "retention_policy_ref": _clean_ref(
            retention_policy_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP14_DEFAULT_RETENTION_POLICY_REF,
            max_length=220,
        ),
        "expiration_policy_ref": _clean_ref(
            expiration_policy_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP14_DEFAULT_EXPIRATION_POLICY_REF,
            max_length=220,
        ),
        "actual_source_ref": _clean_ref(
            actual_source_ref,
            default=P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_ACTUAL_SOURCE_REF,
            max_length=180,
        ),
        "body_free": True,
    }


def _dmh_op14_receipt_blockers(
    op13: Mapping[str, Any] | None,
    receipt: Mapping[str, Any] | None,
) -> tuple[list[str], list[str]]:
    blockers: list[str] = []
    leak_paths: list[str] = []
    if not isinstance(op13, Mapping):
        blockers.append("dmh_op14_rating_question_consistency_blocker_separation_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract(op13)
        except ValueError:
            blockers.append("dmh_op14_op13_rating_question_consistency_blocker_separation_invalid")
        if op13.get("dmh_op13_ready") is not True or op13.get("rating_question_consistency_guard_passed") is not True:
            blockers.append("dmh_op14_op13_consistency_guard_not_passed")
        if op13.get("disposal_purge_receipt_intake_allowed_next") is not True:
            blockers.append("dmh_op14_op13_disposal_intake_not_allowed_next")
        if op13.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF:
            blockers.append("dmh_op14_op13_next_step_not_disposal_intake")
    if not isinstance(receipt, Mapping):
        blockers.append("dmh_op14_disposal_receipt_missing")
        return list(dict.fromkeys(blockers)), leak_paths
    missing = [field for field in P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS if field not in receipt]
    if missing:
        blockers.append("dmh_op14_disposal_receipt_missing_required_fields")
    leak_paths = _scan_forbidden_payload_key_paths(receipt, path="dmh_op14_disposal_receipt")
    if leak_paths:
        blockers.append("dmh_op14_disposal_receipt_forbidden_payload_key")
    if receipt.get("schema_version") != P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_RECEIPT_SCHEMA_VERSION:
        blockers.append("dmh_op14_disposal_receipt_schema_version_mismatch")
    if _ref_has_local_path_shape(receipt.get("disposal_receipt_ref")):
        blockers.append("dmh_op14_disposal_receipt_ref_has_path_shape")
    if receipt.get("review_session_id") != (op13 or {}).get("review_session_id"):
        blockers.append("dmh_op14_review_session_id_mismatch")
    if receipt.get("operation_receipt_ref") != (op13 or {}).get("operation_receipt_ref"):
        blockers.append("dmh_op14_operation_receipt_ref_mismatch")
    if receipt.get("disposal_status_ref") not in P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_DISPOSAL_STATUS_REFS:
        blockers.append("dmh_op14_disposal_status_not_allowed_body_purged_or_aborted_body_purged")
    for key in ("body_removed", "reviewer_notes_removed", "temporary_form_removed", "body_free"):
        if receipt.get(key) is not True:
            blockers.append(f"dmh_op14_{key}_not_true")
    for key in (
        "content_hash_of_body_stored", "body_hash_stored", "local_absolute_path_included",
        "reviewer_notes_body_stored", "question_text_included", "draft_question_text_included",
        "terminal_output_body_included",
    ):
        if receipt.get(key) is not False:
            blockers.append(f"dmh_op14_{key}_not_false")
    if receipt.get("actual_source_ref") != P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_ACTUAL_SOURCE_REF:
        blockers.append("dmh_op14_actual_source_ref_not_allowed")
    if not _clean_ref(receipt.get("disposal_receipt_ref"), default="", max_length=220):
        blockers.append("dmh_op14_disposal_receipt_ref_missing")
    return list(dict.fromkeys(blockers)), leak_paths


def build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
    *,
    rating_question_consistency_blocker_separation: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_rows_normalization: Mapping[str, Any] | None = None,
    rating_rows_normalization_threshold_summary: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_bodyfree: Sequence[Any] | None = None,
    review_session_id: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build DMH-OP14 disposal / purge receipt intake material."""

    session_id = _safe_review_session_id(review_session_id)
    op13 = rating_question_consistency_blocker_separation
    if op13 is None:
        op13 = build_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation(
            question_need_observation_rows_normalization=question_need_observation_rows_normalization,
            rating_rows_normalization_threshold_summary=rating_rows_normalization_threshold_summary,
            review_session_id=session_id,
        )
    blockers, leak_paths = _dmh_op14_receipt_blockers(op13, disposal_receipt_bodyfree)
    ready = not blockers
    leak_detected = bool(leak_paths) or any(
        ref.endswith("not_false") for ref in blockers
    ) or "dmh_op14_disposal_receipt_ref_has_path_shape" in blockers
    receipt = disposal_receipt_bodyfree if isinstance(disposal_receipt_bodyfree, Mapping) else {}
    session_id = _clean_ref((op13 or {}).get("review_session_id"), default=session_id, max_length=220) if isinstance(op13, Mapping) else session_id
    operation_receipt_ref = _clean_ref((op13 or {}).get("operation_receipt_ref"), default="", max_length=220) if isinstance(op13, Mapping) else ""
    disposal_receipt_ref = _clean_ref(receipt.get("disposal_receipt_ref"), default="", max_length=220)
    status = (
        P7_R54_AHR_POST_PMN23_DMH_OP14_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_BY_LEAK_STATUS_REF
        if leak_detected
        else P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_STATUS_REF
    )
    body_removed = receipt.get("body_removed") is True
    reviewer_notes_removed = receipt.get("reviewer_notes_removed") is True
    temporary_form_removed = receipt.get("temporary_form_removed") is True
    content_hash_of_body_stored = receipt.get("content_hash_of_body_stored") is True
    body_hash_stored = receipt.get("body_hash_stored") is True
    local_absolute_path_included = receipt.get("local_absolute_path_included") is True
    reviewer_notes_body_stored = receipt.get("reviewer_notes_body_stored") is True
    question_text_included = receipt.get("question_text_included") is True
    draft_question_text_included = receipt.get("draft_question_text_included") is True
    terminal_output_body_included = receipt.get("terminal_output_body_included") is True
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_20260702",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op13_schema_version": _clean_ref((op13 or {}).get("schema_version"), default="op13_schema_missing", max_length=220) if isinstance(op13, Mapping) else "op13_schema_missing",
        "op13_material_ref": _clean_ref((op13 or {}).get("material_id"), default="op13_material_missing", max_length=220) if isinstance(op13, Mapping) else "op13_material_missing",
        "op13_next_required_step": _clean_ref((op13 or {}).get("next_required_step"), default="op13_next_required_step_missing", max_length=220) if isinstance(op13, Mapping) else "op13_next_required_step_missing",
        "op13_dmh_ready": bool(isinstance(op13, Mapping) and op13.get("dmh_op13_ready") is True),
        "op13_rating_question_consistency_guard_passed": bool(isinstance(op13, Mapping) and op13.get("rating_question_consistency_guard_passed") is True),
        "op13_consistency_blocker_row_count": int((op13 or {}).get("consistency_blocker_row_count") or 0) if isinstance(op13, Mapping) else 0,
        "op13_operation_receipt_ref": operation_receipt_ref,
        "op13_disposal_purge_receipt_intake_allowed_next": bool(isinstance(op13, Mapping) and op13.get("disposal_purge_receipt_intake_allowed_next") is True),
        "dmh_op14_status_ref": status,
        "dmh_op14_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_STATUS_REFS),
        "dmh_op14_ready": ready,
        "disposal_purge_receipt_accepted": ready,
        "dmh_op14_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP14_READY_REASON_REFS) if ready else [],
        "dmh_op14_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP14_READY_REASON_REFS) if ready else 0,
        "dmh_op14_blocker_refs": blockers,
        "dmh_op14_blocker_ref_count": len(blockers),
        "disposal_purge_receipt_intake_ref": P7_R54_AHR_POST_PMN23_DMH_OP14_INTAKE_REF,
        "disposal_receipt_required_field_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS),
        "disposal_receipt_required_field_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS),
        "disposal_receipt_ref": disposal_receipt_ref,
        "disposal_receipt_ref_present": bool(disposal_receipt_ref),
        "disposal_receipt_ref_is_bodyfree_ref": bool(disposal_receipt_ref) and not _ref_has_local_path_shape(disposal_receipt_ref),
        "disposal_receipt_ref_has_local_path_shape": _ref_has_local_path_shape(disposal_receipt_ref),
        "disposal_receipt_received_here": isinstance(disposal_receipt_bodyfree, Mapping),
        "disposal_receipt_intaked_here": ready,
        "operation_receipt_ref": operation_receipt_ref,
        "operation_receipt_ref_matches_op13": receipt.get("operation_receipt_ref") == operation_receipt_ref if isinstance(disposal_receipt_bodyfree, Mapping) else False,
        "disposal_status_ref": _clean_ref(receipt.get("disposal_status_ref"), default="", max_length=120),
        "disposal_status_allowed_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_DISPOSAL_STATUS_REFS),
        "disposal_status_is_body_purged_or_aborted_body_purged": receipt.get("disposal_status_ref") in P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_DISPOSAL_STATUS_REFS,
        "packet_materialized_for_review": receipt.get("packet_materialized_for_review") is True,
        "body_removed": body_removed,
        "reviewer_notes_removed": reviewer_notes_removed,
        "temporary_form_removed": temporary_form_removed,
        "content_hash_of_body_stored": content_hash_of_body_stored,
        "body_hash_stored": body_hash_stored,
        "local_absolute_path_included": local_absolute_path_included,
        "reviewer_notes_body_stored": reviewer_notes_body_stored,
        "question_text_included": question_text_included,
        "draft_question_text_included": draft_question_text_included,
        "terminal_output_body_included": terminal_output_body_included,
        "pause_abort_status_ref": _clean_ref(receipt.get("pause_abort_status_ref"), default="", max_length=180),
        "retention_policy_ref": _clean_ref(receipt.get("retention_policy_ref"), default="", max_length=220),
        "expiration_policy_ref": _clean_ref(receipt.get("expiration_policy_ref"), default="", max_length=220),
        "actual_source_ref": _clean_ref(receipt.get("actual_source_ref"), default="", max_length=180),
        "actual_source_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_ACTUAL_SOURCE_REF,
        "actual_source_guard_passed": receipt.get("actual_source_ref") == P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_ACTUAL_SOURCE_REF,
        "disposal_receipt_bodyfree_only": receipt.get("body_free") is True,
        "forbidden_disposal_receipt_payload_key_paths": leak_paths,
        "forbidden_disposal_receipt_payload_key_path_count": len(leak_paths),
        "body_full_packet_lifecycle_closed_bodyfree": ready,
        "body_removed_without_hash_path_question_or_reviewer_notes": ready and body_removed and reviewer_notes_removed and not body_hash_stored and not content_hash_of_body_stored and not local_absolute_path_included and not reviewer_notes_body_stored and not question_text_included and not draft_question_text_included,
        "temporary_form_removed_without_export": ready and temporary_form_removed,
        "disposal_receipt_does_not_store_body_hash_or_local_path": not body_hash_stored and not content_hash_of_body_stored and not local_absolute_path_included,
        "disposal_receipt_does_not_store_reviewer_notes_body": not reviewer_notes_body_stored,
        "disposal_receipt_does_not_create_question_text": not question_text_included and not draft_question_text_included,
        "disposal_receipt_does_not_store_terminal_output_body": not terminal_output_body_included,
        "actual_disposal_receipt_materialized_here": False,
        "disposal_verified": False,
        "disposal_receipt_ready_for_final_no_leak_validation_only": ready,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "dmh_op14_does_not_run_disposal_here": True,
        "dmh_op14_does_not_complete_evidence": True,
        "dmh_op14_does_not_start_p5_p6_p8_r52_or_release": True,
        "dmh_op14_does_not_execute_postcr22_ex_reentry": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP14_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP14_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP13_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP14")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP14_DISPOSAL_PURGE_RECEIPT_INTAKE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP14",
    )
    ready = bool(data.get("dmh_op14_ready"))
    blockers = list(data.get("dmh_op14_blocker_refs") or [])
    leak_paths = list(data.get("forbidden_disposal_receipt_payload_key_paths") or [])
    leak_detected = bool(leak_paths) or any(data.get(key) is True for key in (
        "content_hash_of_body_stored", "body_hash_stored", "local_absolute_path_included",
        "reviewer_notes_body_stored", "question_text_included", "draft_question_text_included",
        "terminal_output_body_included", "disposal_receipt_ref_has_local_path_shape",
    ))
    expected_status = (
        P7_R54_AHR_POST_PMN23_DMH_OP14_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_BY_LEAK_STATUS_REF
        if leak_detected
        else P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_STATUS_REF
    )
    if data.get("dmh_op14_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 status changed")
    if tuple(data.get("dmh_op14_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP14_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 allowed status refs changed")
    if tuple(data.get("disposal_receipt_required_field_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP14_REQUIRED_DISPOSAL_RECEIPT_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 receipt field refs changed")
    if data.get("dmh_op14_blocker_ref_count") != len(blockers) or data.get("forbidden_disposal_receipt_payload_key_path_count") != len(leak_paths):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 blocker/leak count changed")
    for key in (
        "actual_disposal_receipt_materialized_here", "disposal_verified", "actual_review_evidence_complete_from_real_review",
        "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "r52_actual_execution_confirmed", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP14 required false field promoted: {key}")
    for key in (
        "actual_review_evidence_complete_from_real_review_still_false", "dmh_op14_does_not_run_disposal_here",
        "dmh_op14_does_not_complete_evidence", "dmh_op14_does_not_start_p5_p6_p8_r52_or_release",
        "dmh_op14_does_not_execute_postcr22_ex_reentry", "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP14 required true field changed: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 basis changed")
    if ready:
        for key in (
            "op13_dmh_ready", "op13_rating_question_consistency_guard_passed", "op13_disposal_purge_receipt_intake_allowed_next",
            "disposal_purge_receipt_accepted", "disposal_receipt_ref_present", "disposal_receipt_ref_is_bodyfree_ref",
            "disposal_receipt_received_here", "disposal_receipt_intaked_here", "operation_receipt_ref_matches_op13",
            "disposal_status_is_body_purged_or_aborted_body_purged", "body_removed", "reviewer_notes_removed",
            "temporary_form_removed", "actual_source_guard_passed", "disposal_receipt_bodyfree_only",
            "body_full_packet_lifecycle_closed_bodyfree", "body_removed_without_hash_path_question_or_reviewer_notes",
            "temporary_form_removed_without_export", "disposal_receipt_does_not_store_body_hash_or_local_path",
            "disposal_receipt_does_not_store_reviewer_notes_body", "disposal_receipt_does_not_create_question_text",
            "disposal_receipt_does_not_store_terminal_output_body", "disposal_receipt_ready_for_final_no_leak_validation_only",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP14 ready field changed: {key}")
        for key in (
            "disposal_receipt_ref_has_local_path_shape", "content_hash_of_body_stored", "body_hash_stored",
            "local_absolute_path_included", "reviewer_notes_body_stored", "question_text_included",
            "draft_question_text_included", "terminal_output_body_included",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP14 ready leak field changed: {key}")
        if data.get("dmh_op14_reason_refs") != list(P7_R54_AHR_POST_PMN23_DMH_OP14_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 ready reasons changed")
        if blockers or leak_paths:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 ready material cannot have blockers/leaks")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP14_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 ready implemented steps changed")
        if data.get("op13_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP14_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 OP13 next step changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 next step changed")
    else:
        if data.get("dmh_op14_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 blocked material cannot carry ready reasons")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 blocked material must carry blockers")
        if data.get("disposal_receipt_ready_for_final_no_leak_validation_only") is not False:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 blocked material allowed OP15")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP14 blocked next step changed")
    return True


def _dmh_op15_artifact_ref(artifact: Mapping[str, Any], *, index: int) -> str:
    for key in ("material_id", "disposal_receipt_ref", "operation_receipt_ref", "rating_row_normalization_ref", "question_need_observation_rows_normalization_ref"):
        value = artifact.get(key)
        if value:
            return _clean_ref(value, default=f"bodyfree_artifact_{index:03d}", max_length=220)
    return f"bodyfree_artifact_{index:03d}"


def _dmh_op15_collect_paths(value: Any, *, path: str, flag_refs: Sequence[str]) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in flag_refs and child is True:
                paths.append(child_path)
            paths.extend(_dmh_op15_collect_paths(child, path=child_path, flag_refs=flag_refs))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_dmh_op15_collect_paths(child, path=f"{path}[{index}]", flag_refs=flag_refs))
    return paths


def _dmh_op15_no_touch_paths(value: Any, *, path: str) -> list[str]:
    paths = _dmh_op15_collect_paths(value, path=path, flag_refs=P7_R54_AHR_POST_PMN23_DMH_OP15_NO_TOUCH_FLAG_REFS)
    if isinstance(value, Mapping):
        no_touch = value.get("post_pmn23_no_touch_contract")
        if isinstance(no_touch, Mapping):
            for key, child in no_touch.items():
                if child is True:
                    paths.append(f"{path}.post_pmn23_no_touch_contract.{key}")
        public_contract = value.get("public_contract")
        if isinstance(public_contract, Mapping):
            for key, child in public_contract.items():
                if child is True:
                    paths.append(f"{path}.public_contract.{key}")
    return paths


def _dmh_op15_validation_inputs(
    *,
    op14: Mapping[str, Any] | None,
    artifacts: Sequence[Any] | None,
) -> list[Mapping[str, Any]]:
    values: list[Mapping[str, Any]] = []
    if isinstance(op14, Mapping):
        values.append(op14)
    if isinstance(artifacts, Sequence) and not isinstance(artifacts, (str, bytes, bytearray)):
        for item in artifacts:
            if isinstance(item, Mapping):
                values.append(item)
    return values


def build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation(
    *,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    bodyfree_artifacts: Sequence[Any] | None = None,
    rating_question_consistency_blocker_separation: Mapping[str, Any] | None = None,
    disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build DMH-OP15 final no-body/no-question/no-path/no-hash/no-touch validation material."""

    session_id = _safe_review_session_id(review_session_id)
    op14 = disposal_purge_receipt_intake
    if op14 is None:
        op14 = build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake(
            rating_question_consistency_blocker_separation=rating_question_consistency_blocker_separation,
            disposal_receipt_bodyfree=disposal_receipt_bodyfree,
            review_session_id=session_id,
            **kwargs,
        )
    blockers: list[str] = []
    try:
        assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract(op14 or {})
    except ValueError:
        blockers.append("dmh_op15_op14_disposal_purge_receipt_intake_invalid")
    if not isinstance(op14, Mapping):
        blockers.append("dmh_op15_disposal_purge_receipt_intake_missing")
    else:
        if op14.get("dmh_op14_ready") is not True or op14.get("disposal_receipt_ready_for_final_no_leak_validation_only") is not True:
            blockers.append("dmh_op15_op14_not_ready_for_final_validation")
        if op14.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF:
            blockers.append("dmh_op15_op14_next_step_not_final_validation")
    validation_inputs = _dmh_op15_validation_inputs(op14=op14, artifacts=bodyfree_artifacts)
    forbidden_paths: list[str] = []
    body_paths: list[str] = []
    question_paths: list[str] = []
    path_hash_paths: list[str] = []
    terminal_paths: list[str] = []
    no_touch_paths: list[str] = []
    artifact_refs: list[str] = []
    for index, artifact in enumerate(validation_inputs, start=1):
        artifact_ref = _dmh_op15_artifact_ref(artifact, index=index)
        artifact_refs.append(artifact_ref)
        artifact_path = f"dmh_op15_artifacts[{index}:{artifact_ref}]"
        forbidden_paths.extend(_scan_forbidden_payload_key_paths(artifact, path=artifact_path))
        body_paths.extend(_dmh_op15_collect_paths(artifact, path=artifact_path, flag_refs=P7_R54_AHR_POST_PMN23_DMH_OP15_BODY_LEAK_FLAG_REFS))
        question_paths.extend(_dmh_op15_collect_paths(artifact, path=artifact_path, flag_refs=P7_R54_AHR_POST_PMN23_DMH_OP15_QUESTION_FLAG_REFS))
        path_hash_paths.extend(_dmh_op15_collect_paths(artifact, path=artifact_path, flag_refs=P7_R54_AHR_POST_PMN23_DMH_OP15_PATH_HASH_FLAG_REFS))
        terminal_paths.extend(_dmh_op15_collect_paths(artifact, path=artifact_path, flag_refs=P7_R54_AHR_POST_PMN23_DMH_OP15_TERMINAL_FLAG_REFS))
        no_touch_paths.extend(_dmh_op15_no_touch_paths(artifact, path=artifact_path))
    if forbidden_paths or body_paths:
        blockers.append("dmh_op15_body_or_forbidden_payload_leak_detected")
    if question_paths:
        blockers.append("dmh_op15_question_text_or_question_trigger_detected")
    if path_hash_paths:
        blockers.append("dmh_op15_path_or_body_hash_detected")
    if terminal_paths:
        blockers.append("dmh_op15_terminal_output_body_detected")
    if no_touch_paths:
        blockers.append("dmh_op15_no_touch_violation_detected")
    blockers = list(dict.fromkeys(blockers))
    leak_blocked = bool(forbidden_paths or body_paths or question_paths or path_hash_paths or terminal_paths or no_touch_paths)
    ready = not blockers
    status = (
        P7_R54_AHR_POST_PMN23_DMH_OP15_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_BY_LEAK_STATUS_REF
        if leak_blocked
        else P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_STATUS_REF
    )
    op14_mapping = op14 if isinstance(op14, Mapping) else {}
    session_id = _clean_ref(op14_mapping.get("review_session_id"), default=session_id, max_length=220)
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP15_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_20260702",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op14_schema_version": _clean_ref(op14_mapping.get("schema_version"), default="op14_schema_missing", max_length=220),
        "op14_material_ref": _clean_ref(op14_mapping.get("material_id"), default="op14_material_missing", max_length=220),
        "op14_next_required_step": _clean_ref(op14_mapping.get("next_required_step"), default="op14_next_required_step_missing", max_length=220),
        "op14_dmh_ready": op14_mapping.get("dmh_op14_ready") is True,
        "op14_disposal_purge_receipt_accepted": op14_mapping.get("disposal_purge_receipt_accepted") is True,
        "op14_disposal_receipt_ref": _clean_ref(op14_mapping.get("disposal_receipt_ref"), default="", max_length=220),
        "op14_disposal_status_ref": _clean_ref(op14_mapping.get("disposal_status_ref"), default="", max_length=120),
        "op14_disposal_receipt_ready_for_final_no_leak_validation_only": op14_mapping.get("disposal_receipt_ready_for_final_no_leak_validation_only") is True,
        "op14_actual_review_evidence_complete_still_false": op14_mapping.get("actual_review_evidence_complete_from_real_review_still_false") is True,
        "dmh_op15_status_ref": status,
        "dmh_op15_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP15_ALLOWED_STATUS_REFS),
        "dmh_op15_ready": ready,
        "dmh_op15_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP15_READY_REASON_REFS) if ready else [],
        "dmh_op15_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP15_READY_REASON_REFS) if ready else 0,
        "dmh_op15_blocker_refs": blockers,
        "dmh_op15_blocker_ref_count": len(blockers),
        "final_no_leak_validation_ref": P7_R54_AHR_POST_PMN23_DMH_OP15_VALIDATION_REF,
        "validated_artifact_refs": artifact_refs,
        "validated_artifact_ref_count": len(artifact_refs),
        "validation_scope_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP15_VALIDATION_SCOPE_REFS),
        "validation_scope_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP15_VALIDATION_SCOPE_REFS),
        "forbidden_payload_key_paths": forbidden_paths,
        "forbidden_payload_key_path_count": len(forbidden_paths),
        "body_leak_flag_paths": body_paths,
        "body_leak_flag_path_count": len(body_paths),
        "question_text_flag_paths": question_paths,
        "question_text_flag_path_count": len(question_paths),
        "path_hash_flag_paths": path_hash_paths,
        "path_hash_flag_path_count": len(path_hash_paths),
        "terminal_output_body_flag_paths": terminal_paths,
        "terminal_output_body_flag_path_count": len(terminal_paths),
        "no_touch_violation_paths": no_touch_paths,
        "no_touch_violation_path_count": len(no_touch_paths),
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_path_hash_validation_passed": ready,
        "no_terminal_output_body_validation_passed": ready,
        "no_touch_validation_passed": ready,
        "final_no_leak_validation_passed": ready,
        "body_free_artifacts_only": ready,
        "disposal_verified": ready,
        "disposal_verified_by_op15_validation_only": ready,
        "actual_review_evidence_complete_predicate_allowed_next": ready,
        "actual_review_evidence_complete_from_real_review_still_false": True,
        "actual_review_evidence_complete_from_real_review": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_start_allowed": False,
        "dmh_op15_does_not_execute_disposal_here": True,
        "dmh_op15_does_not_create_or_export_body_full_packet": True,
        "dmh_op15_does_not_create_question_text": True,
        "dmh_op15_does_not_change_api_db_rn_runtime_response_key": True,
        "dmh_op15_does_not_complete_evidence": True,
        "dmh_op15_does_not_start_p5_p6_p8_r52_or_release": True,
        "dmh_op15_does_not_execute_postcr22_ex_reentry": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP15_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP15_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP14_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP15_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP15_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP15")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP15_FINAL_NO_BODY_NO_QUESTION_NO_PATH_NO_HASH_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP15",
    )
    ready = bool(data.get("dmh_op15_ready"))
    blockers = list(data.get("dmh_op15_blocker_refs") or [])
    leak_count = sum(int(data.get(key) or 0) for key in (
        "forbidden_payload_key_path_count", "body_leak_flag_path_count", "question_text_flag_path_count",
        "path_hash_flag_path_count", "terminal_output_body_flag_path_count", "no_touch_violation_path_count",
    ))
    expected_status = (
        P7_R54_AHR_POST_PMN23_DMH_OP15_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_BY_LEAK_STATUS_REF
        if leak_count
        else P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_STATUS_REF
    )
    if data.get("dmh_op15_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 status changed")
    if tuple(data.get("dmh_op15_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP15_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 allowed status refs changed")
    for count_key, list_key in (
        ("forbidden_payload_key_path_count", "forbidden_payload_key_paths"),
        ("body_leak_flag_path_count", "body_leak_flag_paths"),
        ("question_text_flag_path_count", "question_text_flag_paths"),
        ("path_hash_flag_path_count", "path_hash_flag_paths"),
        ("terminal_output_body_flag_path_count", "terminal_output_body_flag_paths"),
        ("no_touch_violation_path_count", "no_touch_violation_paths"),
        ("validated_artifact_ref_count", "validated_artifact_refs"),
    ):
        if data.get(count_key) != len(data.get(list_key) or []):
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP15 count changed: {count_key}")
    for key in (
        "actual_review_evidence_complete_from_real_review", "question_text_materialized_here", "draft_question_text_materialized_here",
        "p8_start_allowed", "p5_final_allowed", "p6_start_allowed", "r52_actual_execution_confirmed", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP15 required false field promoted: {key}")
    for key in (
        "actual_review_evidence_complete_from_real_review_still_false", "dmh_op15_does_not_execute_disposal_here",
        "dmh_op15_does_not_create_or_export_body_full_packet", "dmh_op15_does_not_create_question_text",
        "dmh_op15_does_not_change_api_db_rn_runtime_response_key", "dmh_op15_does_not_complete_evidence",
        "dmh_op15_does_not_start_p5_p6_p8_r52_or_release", "dmh_op15_does_not_execute_postcr22_ex_reentry",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP15 required true field changed: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 basis changed")
    if ready:
        for key in (
            "op14_dmh_ready", "op14_disposal_purge_receipt_accepted", "op14_disposal_receipt_ready_for_final_no_leak_validation_only",
            "op14_actual_review_evidence_complete_still_false", "no_body_leak_validation_passed",
            "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_terminal_output_body_validation_passed",
            "no_touch_validation_passed", "final_no_leak_validation_passed", "body_free_artifacts_only",
            "disposal_verified", "disposal_verified_by_op15_validation_only", "actual_review_evidence_complete_predicate_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP15 ready field changed: {key}")
        if blockers or leak_count:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 ready material cannot have blockers or leak paths")
        if data.get("dmh_op15_reason_refs") != list(P7_R54_AHR_POST_PMN23_DMH_OP15_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 ready implemented steps changed")
        if data.get("op14_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP15_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 OP14 next step changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 next step changed")
    else:
        if data.get("dmh_op15_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 blocked material cannot carry ready reasons")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 blocked material must carry blockers")
        for key in (
            "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed",
            "no_terminal_output_body_validation_passed", "no_touch_validation_passed", "final_no_leak_validation_passed",
            "body_free_artifacts_only", "disposal_verified", "disposal_verified_by_op15_validation_only",
            "actual_review_evidence_complete_predicate_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP15 blocked field promoted: {key}")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP15 blocked next step changed")
    return True


build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_disposal_purge_receipt_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_bodyfree
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_disposal_purge_receipt_intake_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_disposal_purge_receipt_intake_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_final_no_body_no_question_no_path_no_hash_no_touch_validation_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract
)


# ---------------------------------------------------------------------------
# DMH-OP16 / DMH-OP17: actual evidence predicate and PostCR22 re-entry envelope
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[17]
P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF: Final = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[18]

P7_R54_AHR_POST_PMN23_DMH_OP16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op16_actual_review_evidence_complete_predicate.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP17_POSTCR22_EX07_EX18_ACTUAL_EVIDENCE_REENTRY_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope.bodyfree.v1"
)

P7_R54_AHR_POST_PMN23_DMH_OP16_READY_STATUS_REF: Final = (
    "DMH_OP16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_STATUS_REF: Final = (
    "DMH_OP16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP16_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP16_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP17_READY_STATUS_REF: Final = (
    "DMH_OP17_POSTCR22_EX07_EX18_ACTUAL_EVIDENCE_REENTRY_ENVELOPE_READY_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_STATUS_REF: Final = (
    "DMH_OP17_POSTCR22_EX07_EX18_ACTUAL_EVIDENCE_REENTRY_ENVELOPE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP17_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP17_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_STATUS_REF,
)

P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op16_actual_review_evidence_complete_predicate_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "fix_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_or_stop"
)
P7_R54_AHR_POST_PMN23_DMH_OP16_PREDICATE_REF: Final = (
    "post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_ENVELOPE_REF: Final = (
    "post_pmn23_dmh_op17_postcr22_ex07_ex18_reentry_envelope_bodyfree_20260702_001"
)

P7_R54_AHR_POST_PMN23_DMH_OP16_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op15_final_no_leak_validation_ready",
    "actual_source_guard_passed",
    "actual_human_review_executed_by_person_bodyfree_receipt_accepted",
    "reviewed_case_count_is_24",
    "sanitized_review_result_row_count_is_24",
    "rating_row_count_is_24",
    "question_need_observation_row_count_is_24",
    "disposal_verified_by_final_validation",
    "rating_question_consistency_guard_passed",
    "no_body_no_question_no_path_no_hash_no_touch_validation_passed",
)
P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS: Final[tuple[str, ...]] = (
    "actual_source_guard_passed",
    "actual_human_review_executed_by_person",
    "reviewed_case_count_24",
    "selection_row_count_24",
    "sanitized_review_result_row_count_24",
    "rating_row_count_24",
    "question_need_observation_row_count_24",
    "disposal_verified",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_path_hash_validation_passed",
    "no_touch_validation_passed",
    "consistency_guard_passed",
)
P7_R54_AHR_POST_PMN23_DMH_OP17_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op16_actual_review_evidence_complete_predicate_ready",
    "postcr22_ex07_ex18_mapping_bodyfree_only",
    "candidate_only_separation_preserved",
    "r52_actual_execution_not_started_here",
    "p5_p6_p8_p7_release_not_promoted",
)
P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_MAPPING_REFS: Final[tuple[tuple[str, str], ...]] = (
    ("actual_operation_receipt", "existing PostCR22 EX07"),
    ("actual_selection_rows_provenance", "existing PostCR22 EX08"),
    ("sanitized_review_result_rows", "existing PostCR22 EX09"),
    ("rating_rows", "existing PostCR22 EX10"),
    ("blocker_classification", "existing PostCR22 EX11"),
    ("question_need_observation_rows", "existing PostCR22 EX12"),
    ("rating_question_consistency", "existing PostCR22 EX13"),
    ("disposal_purge_receipt", "existing PostCR22 EX14"),
    ("final_no_leak_validation", "existing PostCR22 EX15"),
    ("actual_review_evidence_complete_predicate", "existing PostCR22 EX16"),
    ("candidate_only_separation", "existing PostCR22 EX17"),
    ("validation_result_memo_next_hold", "existing PostCR22 EX18"),
)

P7_R54_AHR_POST_PMN23_DMH_OP16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:17]
P7_R54_AHR_POST_PMN23_DMH_OP16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[17:]
P7_R54_AHR_POST_PMN23_DMH_OP17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:18]
P7_R54_AHR_POST_PMN23_DMH_OP17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[18:]

P7_R54_AHR_POST_PMN23_DMH_OP16_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op15_schema_version", "op15_material_ref", "op15_next_required_step", "op15_dmh_ready",
    "op15_final_no_leak_validation_passed", "op15_disposal_verified", "op15_actual_review_evidence_complete_predicate_allowed_next",
    "op09_material_ref", "op09_next_required_step", "op09_dmh_ready", "op09_actual_source_guard_passed",
    "op09_actual_human_review_executed_by_person", "op09_reviewed_case_count", "op09_selection_row_count",
    "op10_material_ref", "op10_dmh_ready", "op10_row_provenance_guard_passed", "op10_sanitized_review_result_row_count",
    "op11_material_ref", "op11_dmh_ready", "op11_rating_row_count",
    "op12_material_ref", "op12_dmh_ready", "op12_question_need_observation_row_count",
    "op13_material_ref", "op13_dmh_ready", "op13_rating_question_consistency_guard_passed",
    "op14_material_ref", "op14_dmh_ready", "op14_disposal_purge_receipt_accepted",
    "dmh_op16_status_ref", "dmh_op16_allowed_status_refs", "dmh_op16_ready", "dmh_op16_reason_refs",
    "dmh_op16_reason_ref_count", "dmh_op16_blocker_refs", "dmh_op16_blocker_ref_count",
    "actual_review_evidence_complete_predicate_ref", "complete_condition_refs", "complete_condition_ref_count",
    "complete_condition_passed_refs", "complete_condition_passed_ref_count", "complete_condition_missing_refs",
    "complete_condition_missing_ref_count", "operation_receipt_ref", "reviewer_person_ref", "actual_source_guard_passed",
    "actual_human_review_executed_by_person", "reviewed_case_count", "reviewed_case_count_is_24",
    "selection_row_count", "selection_row_count_is_24", "sanitized_review_result_row_count",
    "sanitized_review_result_row_count_is_24", "rating_row_count", "rating_row_count_is_24",
    "question_need_observation_row_count", "question_need_observation_row_count_is_24", "disposal_verified",
    "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed",
    "no_touch_validation_passed", "consistency_guard_passed", "actual_review_evidence_complete_predicate_evaluated_here",
    "actual_review_evidence_complete_predicate_passed", "actual_review_evidence_complete_candidate_from_real_review",
    "actual_review_evidence_complete_from_real_review_before_op16", "actual_review_evidence_complete_from_real_review",
    "op16_does_not_run_actual_human_review_here", "op16_does_not_create_rows_here", "op16_does_not_run_disposal_here",
    "op16_does_not_execute_postcr22_ex_reentry", "op16_does_not_start_p5_p6_p8_r52_or_release",
    "p5_human_blind_qa_confirmed_final", "p5_confirmed_final", "p5_final_allowed", "p6_start_allowed",
    "p8_start_allowed", "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed",
    "p7_complete", "release_allowed", "actual_review_basis_ref", "actual_review_basis_allowed_ref",
    "current_actual_review_basis_remains_264_85_258_171", "claim_boundary_refs", "claim_boundary_ref_count",
    "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "implemented_steps",
    "not_yet_implemented_steps", "next_required_step", "public_contract", "post_pmn23_no_touch_contract",
    "body_free_markers", *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS, "body_free",
)
P7_R54_AHR_POST_PMN23_DMH_OP17_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op16_schema_version", "op16_material_ref", "op16_next_required_step", "op16_dmh_ready",
    "op16_actual_review_evidence_complete_predicate_passed", "op16_actual_review_evidence_complete_from_real_review",
    "dmh_op17_status_ref", "dmh_op17_allowed_status_refs", "dmh_op17_ready", "dmh_op17_reason_refs",
    "dmh_op17_reason_ref_count", "dmh_op17_blocker_refs", "dmh_op17_blocker_ref_count",
    "postcr22_ex07_ex18_reentry_envelope_ref", "existing_postcr22_ex_reentry_helper_ref",
    "existing_postcr22_ex_reentry_step_refs", "existing_postcr22_ex_reentry_step_ref_count",
    "postcr22_ex07_ex18_mapping_rows", "postcr22_ex07_ex18_mapping_row_count",
    "postcr22_ex07_ex18_reentry_envelope_ready", "postcr22_ex07_ex18_reentry_executed_here",
    "postcr22_ex07_ex18_reentry_execution_requested_here", "r52_actual_execution_started_here",
    "r52_actual_execution_confirmed", "candidate_only_separation_preserved", "actual_review_evidence_complete_from_real_review",
    "actual_review_evidence_complete_predicate_carried_into_reentry_envelope", "p5_final_allowed", "p6_start_allowed",
    "p8_start_allowed", "p7_complete", "release_allowed", "op17_does_not_execute_postcr22_ex_reentry",
    "op17_does_not_start_r52_actual_execution", "op17_does_not_start_p5_p6_p8_p7_or_release",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract",
    "post_pmn23_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_DOWNSTREAM_MANUAL_DECISION_HOLD_FINALIZER_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pmn23.dmh."
    "op18_result_memo_downstream_manual_decision_hold_finalizer.bodyfree.v1"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_READY_STATUS_REF: Final = (
    "DMH_OP18_RESULT_MEMO_DOWNSTREAM_MANUAL_DECISION_HOLD_FINALIZED_BODYFREE"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF: Final = (
    "DMH_OP18_RESULT_MEMO_DOWNSTREAM_MANUAL_DECISION_HOLD_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATUS_REF: Final = (
    "DMH_OP18_RESULT_MEMO_BODYFREE_EVIDENCE_BOUNDARY_REPAIR_REQUIRED"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PMN23_DMH_OP18_READY_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF,
    P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATUS_REF,
)
P7_R54_AHR_POST_PMN23_DMH_OP18_FINALIZER_REF: Final = (
    "post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_bodyfree_20260702_001"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REF: Final = (
    "R54_AHR_PostPMN23_DownstreamManualDecisionHold_EvidenceIntake_DMH_OP18_Result_20260702.md"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_INCOMPLETE_REF: Final = (
    "continue_or_retry_actual_local_only_human_review_operation_before_downstream_decision"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_COMPLETE_REF: Final = (
    "downstream_manual_decision_required_without_auto_execution"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_REPAIR_REF: Final = (
    "stop_and_repair_bodyfree_evidence_boundary"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_DOWNSTREAM_MANUAL_DECISION_HOLD_STATE_REF: Final = (
    "DMH_DOWNSTREAM_MANUAL_DECISION_HOLD"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_BLOCKED_STATE_REF: Final = (
    "DMH_EVIDENCE_BLOCKED"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_COMPLETE_STATE_REF: Final = (
    "actual_review_evidence_complete_from_real_review_bodyfree_candidate_ready"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_INCOMPLETE_STATE_REF: Final = (
    "actual_review_evidence_incomplete_continue_or_retry_actual_review"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATE_REF: Final = (
    "bodyfree_evidence_boundary_repair_required"
)
P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS: Final[tuple[str, ...]] = (
    "op17_postcr22_ex07_ex18_reentry_envelope_ready_bodyfree",
    "result_memo_bodyfree_boundary_closed",
    "downstream_manual_decision_hold_finalized_without_auto_execution",
    "actual_review_evidence_complete_candidate_kept_candidate_only",
    "p5_p6_p8_r52_p7_release_not_promoted",
)
P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REQUIRED_SECTION_REFS: Final[tuple[str, ...]] = (
    "implementation_scope",
    "changed_files",
    "target_tests",
    "selected_regression",
    "compileall",
    "pmn_op23_hold_intake_status",
    "explicit_allow_status",
    "actual_body_full_packet_generation_status",
    "packet_scan_status",
    "actual_human_review_execution_status",
    "actual_operation_receipt_status",
    "sanitized_review_result_row_status",
    "rating_row_status",
    "question_need_observation_row_status",
    "disposal_purge_status",
    "no_leak_validation_status",
    "actual_review_evidence_status",
    "postcr22_ex_reentry_status",
    "not_claimed_boundary",
    "next_required_step",
)
P7_R54_AHR_POST_PMN23_DMH_OP18_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "P5 confirmed candidate != P5 final",
    "P6 candidate-only != P6 start",
    "P8 material candidate-only != P8 start",
    "R52 handoff candidate != R52 actual execution",
)
P7_R54_AHR_POST_PMN23_DMH_OP18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[:19]
P7_R54_AHR_POST_PMN23_DMH_OP18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_POST_PMN23_DMH_STEP_REFS[19:]
P7_R54_AHR_POST_PMN23_DMH_OP18_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op17_schema_version", "op17_material_ref", "op17_next_required_step", "op17_dmh_ready",
    "op17_postcr22_ex07_ex18_reentry_envelope_ready", "op17_actual_review_evidence_complete_from_real_review",
    "op17_actual_review_evidence_complete_predicate_carried_into_reentry_envelope",
    "op17_reentry_execution_claim_detected", "op17_r52_actual_execution_claim_detected",
    "op17_downstream_promotion_claim_detected", "op17_forbidden_payload_key_detected",
    "dmh_op18_status_ref", "dmh_op18_allowed_status_refs", "dmh_op18_ready", "dmh_op18_reason_refs",
    "dmh_op18_reason_ref_count", "dmh_op18_blocker_refs", "dmh_op18_blocker_ref_count",
    "result_memo_finalizer_ref", "result_memo_ref", "result_memo_bodyfree_closed",
    "result_memo_required_section_refs", "result_memo_required_section_ref_count",
    "result_memo_includes_body_text", "result_memo_includes_question_text", "result_memo_includes_local_path",
    "result_memo_includes_body_hash", "result_memo_includes_terminal_output_body",
    "result_memo_contains_no_body_question_path_hash_or_terminal_output",
    "downstream_manual_decision_hold_ref", "downstream_manual_decision_hold_state_ref",
    "downstream_manual_decision_hold_finalized", "manual_downstream_decision_required",
    "manual_decision_auto_executes_downstream", "actual_review_evidence_status_ref",
    "actual_review_evidence_complete_candidate_from_real_review", "actual_review_evidence_complete_from_real_review",
    "actual_review_evidence_complete_predicate_carried_into_reentry_envelope",
    "evidence_completion_state_ref", "evidence_incomplete_continue_or_retry_required", "bodyfree_evidence_boundary_repair_required",
    "postcr22_ex07_ex18_reentry_ready_candidate", "postcr22_ex07_ex18_reentry_executed_here",
    "r52_actual_execution_started_here", "r52_actual_execution_confirmed",
    "p5_confirmed_candidate_not_p5_final", "p6_candidate_only_not_p6_start",
    "p8_material_candidate_only_not_p8_start", "r52_handoff_candidate_not_r52_actual_execution",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "op18_does_not_execute_postcr22_ex_reentry", "op18_does_not_start_r52_actual_execution",
    "op18_does_not_start_p5_p6_p8_p7_or_release", "op18_does_not_create_question_text",
    "op18_does_not_change_api_db_rn_runtime_response_key", "op18_does_not_claim_full_backend_or_rn_green",
    "actual_review_basis_ref", "actual_review_basis_allowed_ref", "current_actual_review_basis_remains_264_85_258_171",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count",
    "not_claimed_boundary", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "post_pmn23_no_touch_contract", "body_free_markers",
    *P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _false_flags_with_actual_review_evidence_complete(*, complete: bool) -> dict[str, bool]:
    flags = _false_flags()
    flags["actual_review_evidence_complete_from_real_review"] = bool(complete)
    return flags


def _assert_base_bodyfree_boundary_allow_actual_evidence_complete(
    data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_PMN23_DMH_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_PMN23_DMH_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != operation_step_ref or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step ref changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or claim GitHub connection check")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    for field in P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        expected = (data.get("actual_review_evidence_complete_predicate_passed") is True or data.get("actual_review_evidence_complete_predicate_carried_into_reentry_envelope") is True) if field == "actual_review_evidence_complete_from_real_review" else False
        if data.get(field) is not expected:
            raise ValueError(f"{source} required false flag changed: {field}")
    if any(value is not False for value in (data.get("public_contract") or {}).values()):
        raise ValueError(f"{source} public contract mutated")
    if any(value is not False for value in (data.get("post_pmn23_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract mutated")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free marker changed")
    if any(key in P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains forbidden top-level payload key")


def _dmh_op16_assert_optional_contract(
    assertion_fn: Any,
    material: Mapping[str, Any],
    blocker_ref: str,
    blockers: list[str],
) -> None:
    try:
        assertion_fn(material)
    except Exception:
        blockers.append(blocker_ref)


def _dmh_op16_missing_condition_refs(*, conditions: Mapping[str, bool]) -> list[str]:
    return [ref for ref in P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS if not conditions.get(ref, False)]


def _dmh_op16_blockers(
    *,
    op15: Mapping[str, Any],
    op09: Mapping[str, Any],
    op10: Mapping[str, Any],
    op11: Mapping[str, Any],
    op12: Mapping[str, Any],
    op13: Mapping[str, Any],
    op14: Mapping[str, Any],
) -> list[str]:
    blockers: list[str] = []
    if not op15:
        blockers.append("dmh_op16_op15_final_no_leak_validation_missing")
    else:
        _dmh_op16_assert_optional_contract(
            assert_p7_r54_ahr_post_pmn23_dmh_op15_final_no_body_no_question_no_path_no_hash_no_touch_validation_contract,
            op15,
            "dmh_op16_op15_final_no_leak_validation_invalid",
            blockers,
        )
        if op15.get("dmh_op15_ready") is not True:
            blockers.append("dmh_op16_op15_not_ready")
        if op15.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF:
            blockers.append("dmh_op16_op15_next_step_not_actual_review_evidence_complete_predicate")
        if op15.get("final_no_leak_validation_passed") is not True:
            blockers.append("dmh_op16_final_no_leak_validation_not_passed")
        if op15.get("disposal_verified") is not True:
            blockers.append("dmh_op16_disposal_not_verified_by_op15")
        if op15.get("actual_review_evidence_complete_predicate_allowed_next") is not True:
            blockers.append("dmh_op16_predicate_not_allowed_by_op15")
    if not op09:
        blockers.append("dmh_op16_op09_actual_operation_receipt_missing")
    else:
        _dmh_op16_assert_optional_contract(
            assert_p7_r54_ahr_post_pmn23_dmh_op09_actual_operation_receipt_intake_contract,
            op09,
            "dmh_op16_op09_actual_operation_receipt_invalid",
            blockers,
        )
        if op09.get("dmh_op09_ready") is not True:
            blockers.append("dmh_op16_op09_not_ready")
        if op09.get("actual_source_guard_passed") is not True:
            blockers.append("dmh_op16_actual_source_guard_not_passed")
        if op09.get("actual_human_review_executed_by_person") is not True:
            blockers.append("dmh_op16_actual_human_review_executed_by_person_missing")
        if op09.get("reviewed_case_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            blockers.append("dmh_op16_reviewed_case_count_not_24")
        if op09.get("selection_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            blockers.append("dmh_op16_selection_row_count_not_24")
    if not op10:
        blockers.append("dmh_op16_op10_sanitized_rows_missing")
    else:
        _dmh_op16_assert_optional_contract(
            assert_p7_r54_ahr_post_pmn23_dmh_op10_sanitized_review_result_rows_intake_provenance_guard_contract,
            op10,
            "dmh_op16_op10_sanitized_rows_invalid",
            blockers,
        )
        if op10.get("dmh_op10_ready") is not True:
            blockers.append("dmh_op16_op10_not_ready")
        if op10.get("row_provenance_guard_passed") is not True:
            blockers.append("dmh_op16_row_provenance_guard_not_passed")
        if op10.get("sanitized_review_result_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            blockers.append("dmh_op16_sanitized_review_result_row_count_not_24")
    if not op11:
        blockers.append("dmh_op16_op11_rating_rows_missing")
    else:
        _dmh_op16_assert_optional_contract(
            assert_p7_r54_ahr_post_pmn23_dmh_op11_rating_rows_normalization_threshold_summary_contract,
            op11,
            "dmh_op16_op11_rating_rows_invalid",
            blockers,
        )
        if op11.get("dmh_op11_ready") is not True:
            blockers.append("dmh_op16_op11_not_ready")
        if op11.get("rating_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            blockers.append("dmh_op16_rating_row_count_not_24")
    if not op12:
        blockers.append("dmh_op16_op12_question_need_observation_rows_missing")
    else:
        _dmh_op16_assert_optional_contract(
            assert_p7_r54_ahr_post_pmn23_dmh_op12_question_need_observation_rows_normalization_contract,
            op12,
            "dmh_op16_op12_question_need_observation_rows_invalid",
            blockers,
        )
        if op12.get("dmh_op12_ready") is not True:
            blockers.append("dmh_op16_op12_not_ready")
        if op12.get("question_need_observation_row_count") != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
            blockers.append("dmh_op16_question_need_observation_row_count_not_24")
    if not op13:
        blockers.append("dmh_op16_op13_rating_question_consistency_missing")
    else:
        _dmh_op16_assert_optional_contract(
            assert_p7_r54_ahr_post_pmn23_dmh_op13_rating_question_consistency_blocker_separation_contract,
            op13,
            "dmh_op16_op13_rating_question_consistency_invalid",
            blockers,
        )
        if op13.get("dmh_op13_ready") is not True:
            blockers.append("dmh_op16_op13_not_ready")
        if op13.get("rating_question_consistency_guard_passed") is not True:
            blockers.append("dmh_op16_rating_question_consistency_guard_not_passed")
    if not op14:
        blockers.append("dmh_op16_op14_disposal_purge_receipt_intake_missing")
    else:
        _dmh_op16_assert_optional_contract(
            assert_p7_r54_ahr_post_pmn23_dmh_op14_disposal_purge_receipt_intake_contract,
            op14,
            "dmh_op16_op14_disposal_purge_receipt_intake_invalid",
            blockers,
        )
        if op14.get("dmh_op14_ready") is not True:
            blockers.append("dmh_op16_op14_not_ready")
        if op14.get("disposal_purge_receipt_accepted") is not True:
            blockers.append("dmh_op16_disposal_purge_receipt_not_accepted")
    session_refs = {
        _clean_ref(item.get("review_session_id"), default="", max_length=220)
        for item in (op15, op09, op10, op11, op12, op13, op14)
        if item
    } - {""}
    if len(session_refs) > 1:
        blockers.append("dmh_op16_review_session_id_mismatch_across_evidence_bundle")
    operation_refs = {
        _clean_ref(item.get("operation_receipt_ref"), default="", max_length=220)
        for item in (op09, op10, op11, op12, op13, op14)
        if item and item.get("operation_receipt_ref")
    } - {""}
    if len(operation_refs) > 1:
        blockers.append("dmh_op16_operation_receipt_ref_mismatch_across_evidence_bundle")
    for name, material in (
        ("op15", op15), ("op09", op09), ("op10", op10), ("op11", op11),
        ("op12", op12), ("op13", op13), ("op14", op14),
    ):
        if material and _scan_forbidden_payload_key_paths(material, path=f"dmh_op16_{name}"):
            blockers.append(f"dmh_op16_{name}_forbidden_payload_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate(
    *,
    final_no_body_no_question_no_path_no_hash_no_touch_validation: Mapping[str, Any] | None = None,
    actual_operation_receipt_intake: Mapping[str, Any] | None = None,
    sanitized_review_result_rows_intake: Mapping[str, Any] | None = None,
    rating_rows_normalization_threshold_summary: Mapping[str, Any] | None = None,
    question_need_observation_rows_normalization: Mapping[str, Any] | None = None,
    rating_question_consistency_blocker_separation: Mapping[str, Any] | None = None,
    disposal_purge_receipt_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP16 actual_review_evidence_complete predicate material.

    This evaluates an already received body-free evidence bundle.  It does not
    run actual review, create rows, execute disposal, execute PostCR22 re-entry,
    or promote P5/P6/P8/R52/P7/release.
    """

    op15 = final_no_body_no_question_no_path_no_hash_no_touch_validation if isinstance(final_no_body_no_question_no_path_no_hash_no_touch_validation, Mapping) else {}
    op09 = actual_operation_receipt_intake if isinstance(actual_operation_receipt_intake, Mapping) else {}
    op10 = sanitized_review_result_rows_intake if isinstance(sanitized_review_result_rows_intake, Mapping) else {}
    op11 = rating_rows_normalization_threshold_summary if isinstance(rating_rows_normalization_threshold_summary, Mapping) else {}
    op12 = question_need_observation_rows_normalization if isinstance(question_need_observation_rows_normalization, Mapping) else {}
    op13 = rating_question_consistency_blocker_separation if isinstance(rating_question_consistency_blocker_separation, Mapping) else {}
    op14 = disposal_purge_receipt_intake if isinstance(disposal_purge_receipt_intake, Mapping) else {}
    session_id = _safe_review_session_id(
        review_session_id
        or op15.get("review_session_id")
        or op09.get("review_session_id")
        or op10.get("review_session_id")
        or op11.get("review_session_id")
        or op12.get("review_session_id")
        or op13.get("review_session_id")
        or op14.get("review_session_id")
    )
    blockers = _dmh_op16_blockers(op15=op15, op09=op09, op10=op10, op11=op11, op12=op12, op13=op13, op14=op14)
    conditions = {
        "actual_source_guard_passed": op09.get("actual_source_guard_passed") is True,
        "actual_human_review_executed_by_person": op09.get("actual_human_review_executed_by_person") is True,
        "reviewed_case_count_24": op09.get("reviewed_case_count") == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "selection_row_count_24": op09.get("selection_row_count") == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "sanitized_review_result_row_count_24": op10.get("sanitized_review_result_row_count") == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "rating_row_count_24": op11.get("rating_row_count") == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "question_need_observation_row_count_24": op12.get("question_need_observation_row_count") == P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT,
        "disposal_verified": op15.get("disposal_verified") is True,
        "no_body_leak_validation_passed": op15.get("no_body_leak_validation_passed") is True,
        "no_question_text_validation_passed": op15.get("no_question_text_validation_passed") is True,
        "no_path_hash_validation_passed": op15.get("no_path_hash_validation_passed") is True,
        "no_touch_validation_passed": op15.get("no_touch_validation_passed") is True,
        "consistency_guard_passed": op13.get("rating_question_consistency_guard_passed") is True,
    }
    missing_conditions = _dmh_op16_missing_condition_refs(conditions=conditions)
    ready = not blockers and not missing_conditions
    status = P7_R54_AHR_POST_PMN23_DMH_OP16_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_STATUS_REF
    operation_receipt_ref = _clean_ref(
        op09.get("operation_receipt_ref") or op10.get("operation_receipt_ref") or op13.get("operation_receipt_ref") or op14.get("operation_receipt_ref"),
        default="",
        max_length=220,
    )
    reviewer_person_ref = _clean_ref(op09.get("reviewer_person_ref") or op10.get("reviewer_person_ref") or op11.get("reviewer_person_ref") or op12.get("reviewer_person_ref"), default="", max_length=220)
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op15_schema_version": _clean_ref(op15.get("schema_version"), default="op15_schema_missing", max_length=240),
        "op15_material_ref": _clean_ref(op15.get("material_id"), default="op15_material_missing", max_length=240),
        "op15_next_required_step": _clean_ref(op15.get("next_required_step"), default="op15_next_required_step_missing", max_length=240),
        "op15_dmh_ready": op15.get("dmh_op15_ready") is True,
        "op15_final_no_leak_validation_passed": op15.get("final_no_leak_validation_passed") is True,
        "op15_disposal_verified": op15.get("disposal_verified") is True,
        "op15_actual_review_evidence_complete_predicate_allowed_next": op15.get("actual_review_evidence_complete_predicate_allowed_next") is True,
        "op09_material_ref": _clean_ref(op09.get("material_id"), default="op09_material_missing", max_length=240),
        "op09_next_required_step": _clean_ref(op09.get("next_required_step"), default="op09_next_required_step_missing", max_length=240),
        "op09_dmh_ready": op09.get("dmh_op09_ready") is True,
        "op09_actual_source_guard_passed": op09.get("actual_source_guard_passed") is True,
        "op09_actual_human_review_executed_by_person": op09.get("actual_human_review_executed_by_person") is True,
        "op09_reviewed_case_count": _safe_int(op09.get("reviewed_case_count")),
        "op09_selection_row_count": _safe_int(op09.get("selection_row_count")),
        "op10_material_ref": _clean_ref(op10.get("material_id"), default="op10_material_missing", max_length=240),
        "op10_dmh_ready": op10.get("dmh_op10_ready") is True,
        "op10_row_provenance_guard_passed": op10.get("row_provenance_guard_passed") is True,
        "op10_sanitized_review_result_row_count": _safe_int(op10.get("sanitized_review_result_row_count")),
        "op11_material_ref": _clean_ref(op11.get("material_id"), default="op11_material_missing", max_length=240),
        "op11_dmh_ready": op11.get("dmh_op11_ready") is True,
        "op11_rating_row_count": _safe_int(op11.get("rating_row_count")),
        "op12_material_ref": _clean_ref(op12.get("material_id"), default="op12_material_missing", max_length=240),
        "op12_dmh_ready": op12.get("dmh_op12_ready") is True,
        "op12_question_need_observation_row_count": _safe_int(op12.get("question_need_observation_row_count")),
        "op13_material_ref": _clean_ref(op13.get("material_id"), default="op13_material_missing", max_length=240),
        "op13_dmh_ready": op13.get("dmh_op13_ready") is True,
        "op13_rating_question_consistency_guard_passed": op13.get("rating_question_consistency_guard_passed") is True,
        "op14_material_ref": _clean_ref(op14.get("material_id"), default="op14_material_missing", max_length=240),
        "op14_dmh_ready": op14.get("dmh_op14_ready") is True,
        "op14_disposal_purge_receipt_accepted": op14.get("disposal_purge_receipt_accepted") is True,
        "dmh_op16_status_ref": status,
        "dmh_op16_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP16_ALLOWED_STATUS_REFS),
        "dmh_op16_ready": ready,
        "dmh_op16_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP16_READY_REASON_REFS) if ready else [],
        "dmh_op16_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP16_READY_REASON_REFS) if ready else 0,
        "dmh_op16_blocker_refs": blockers + [f"dmh_op16_missing_condition_{ref}" for ref in missing_conditions],
        "dmh_op16_blocker_ref_count": len(blockers) + len(missing_conditions),
        "actual_review_evidence_complete_predicate_ref": P7_R54_AHR_POST_PMN23_DMH_OP16_PREDICATE_REF,
        "complete_condition_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS),
        "complete_condition_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS),
        "complete_condition_passed_refs": [ref for ref in P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS if conditions.get(ref, False)],
        "complete_condition_passed_ref_count": len([ref for ref in P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS if conditions.get(ref, False)]),
        "complete_condition_missing_refs": missing_conditions,
        "complete_condition_missing_ref_count": len(missing_conditions),
        "operation_receipt_ref": operation_receipt_ref,
        "reviewer_person_ref": reviewer_person_ref,
        "actual_source_guard_passed": conditions["actual_source_guard_passed"] and ready,
        "actual_human_review_executed_by_person": conditions["actual_human_review_executed_by_person"] and ready,
        "reviewed_case_count": _safe_int(op09.get("reviewed_case_count")) if ready else 0,
        "reviewed_case_count_is_24": conditions["reviewed_case_count_24"] and ready,
        "selection_row_count": _safe_int(op09.get("selection_row_count")) if ready else 0,
        "selection_row_count_is_24": conditions["selection_row_count_24"] and ready,
        "sanitized_review_result_row_count": _safe_int(op10.get("sanitized_review_result_row_count")) if ready else 0,
        "sanitized_review_result_row_count_is_24": conditions["sanitized_review_result_row_count_24"] and ready,
        "rating_row_count": _safe_int(op11.get("rating_row_count")) if ready else 0,
        "rating_row_count_is_24": conditions["rating_row_count_24"] and ready,
        "question_need_observation_row_count": _safe_int(op12.get("question_need_observation_row_count")) if ready else 0,
        "question_need_observation_row_count_is_24": conditions["question_need_observation_row_count_24"] and ready,
        "disposal_verified": conditions["disposal_verified"] and ready,
        "no_body_leak_validation_passed": conditions["no_body_leak_validation_passed"] and ready,
        "no_question_text_validation_passed": conditions["no_question_text_validation_passed"] and ready,
        "no_path_hash_validation_passed": conditions["no_path_hash_validation_passed"] and ready,
        "no_touch_validation_passed": conditions["no_touch_validation_passed"] and ready,
        "consistency_guard_passed": conditions["consistency_guard_passed"] and ready,
        "actual_review_evidence_complete_predicate_evaluated_here": ready,
        "actual_review_evidence_complete_predicate_passed": ready,
        "actual_review_evidence_complete_candidate_from_real_review": ready,
        "actual_review_evidence_complete_from_real_review_before_op16": False,
        "actual_review_evidence_complete_from_real_review": ready,
        "op16_does_not_run_actual_human_review_here": True,
        "op16_does_not_create_rows_here": True,
        "op16_does_not_run_disposal_here": True,
        "op16_does_not_execute_postcr22_ex_reentry": True,
        "op16_does_not_start_p5_p6_p8_r52_or_release": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP16_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP16_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP15_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags_with_actual_review_evidence_complete(complete=ready),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP16_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP16_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP16")
    _assert_base_bodyfree_boundary_allow_actual_evidence_complete(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP16_ACTUAL_REVIEW_EVIDENCE_COMPLETE_PREDICATE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP16",
    )
    ready = bool(data.get("dmh_op16_ready"))
    blockers = list(data.get("dmh_op16_blocker_refs") or [])
    if data.get("dmh_op16_status_ref") != (P7_R54_AHR_POST_PMN23_DMH_OP16_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 status changed")
    if tuple(data.get("dmh_op16_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP16_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 allowed status refs changed")
    if data.get("dmh_op16_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 blocker count changed")
    if data.get("complete_condition_ref_count") != len(data.get("complete_condition_refs") or []) or tuple(data.get("complete_condition_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP16_COMPLETE_CONDITION_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 complete condition refs changed")
    if data.get("complete_condition_passed_ref_count") != len(data.get("complete_condition_passed_refs") or []) or data.get("complete_condition_missing_ref_count") != len(data.get("complete_condition_missing_refs") or []):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 condition counts changed")
    for key in (
        "p5_human_blind_qa_confirmed_final", "p5_confirmed_final", "p5_final_allowed", "p6_start_allowed", "p8_start_allowed",
        "r52_reintake_execution_requested_here", "actual_r52_reintake_execution_confirmed", "p7_complete", "release_allowed",
        "postcr22_ex07_ex18_reentry_executed_here", "actual_review_evidence_complete_from_real_operation_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP16 downstream flag promoted: {key}")
    for key in (
        "op16_does_not_run_actual_human_review_here", "op16_does_not_create_rows_here", "op16_does_not_run_disposal_here",
        "op16_does_not_execute_postcr22_ex_reentry", "op16_does_not_start_p5_p6_p8_r52_or_release",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP16 required true field changed: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 basis changed")
    if ready:
        for key in (
            "op15_dmh_ready", "op15_final_no_leak_validation_passed", "op15_disposal_verified", "op15_actual_review_evidence_complete_predicate_allowed_next",
            "op09_dmh_ready", "op09_actual_source_guard_passed", "op09_actual_human_review_executed_by_person", "op10_dmh_ready",
            "op10_row_provenance_guard_passed", "op11_dmh_ready", "op12_dmh_ready", "op13_dmh_ready", "op13_rating_question_consistency_guard_passed",
            "op14_dmh_ready", "op14_disposal_purge_receipt_accepted", "actual_source_guard_passed", "actual_human_review_executed_by_person",
            "reviewed_case_count_is_24", "selection_row_count_is_24", "sanitized_review_result_row_count_is_24", "rating_row_count_is_24",
            "question_need_observation_row_count_is_24", "disposal_verified", "no_body_leak_validation_passed", "no_question_text_validation_passed",
            "no_path_hash_validation_passed", "no_touch_validation_passed", "consistency_guard_passed", "actual_review_evidence_complete_predicate_evaluated_here",
            "actual_review_evidence_complete_predicate_passed", "actual_review_evidence_complete_candidate_from_real_review", "actual_review_evidence_complete_from_real_review",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP16 ready field changed: {key}")
        for count_key in ("op09_reviewed_case_count", "op09_selection_row_count", "op10_sanitized_review_result_row_count", "op11_rating_row_count", "op12_question_need_observation_row_count", "reviewed_case_count", "selection_row_count", "sanitized_review_result_row_count", "rating_row_count", "question_need_observation_row_count"):
            if data.get(count_key) != P7_R54_AHR_POST_PMN23_DMH_REQUIRED_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP16 ready count changed: {count_key}")
        if blockers or data.get("complete_condition_missing_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 ready material cannot have blockers or missing conditions")
        if data.get("dmh_op16_reason_refs") != list(P7_R54_AHR_POST_PMN23_DMH_OP16_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 ready reasons changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 implemented steps changed")
        if data.get("op15_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP16_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 OP15 next step changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 next step changed")
    else:
        if data.get("dmh_op16_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 blocked material cannot carry ready reasons")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 blocked material must carry blockers")
        for key in (
            "actual_source_guard_passed", "actual_human_review_executed_by_person", "reviewed_case_count_is_24", "selection_row_count_is_24",
            "sanitized_review_result_row_count_is_24", "rating_row_count_is_24", "question_need_observation_row_count_is_24", "disposal_verified",
            "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_path_hash_validation_passed", "no_touch_validation_passed",
            "consistency_guard_passed", "actual_review_evidence_complete_predicate_evaluated_here", "actual_review_evidence_complete_predicate_passed",
            "actual_review_evidence_complete_candidate_from_real_review", "actual_review_evidence_complete_from_real_review",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP16 blocked field promoted: {key}")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP16 blocked next step changed")
    return True


def _dmh_op17_blockers(op16: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if not op16:
        blockers.append("dmh_op17_op16_actual_review_evidence_complete_predicate_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract(op16)
        except Exception:
            blockers.append("dmh_op17_op16_actual_review_evidence_complete_predicate_invalid")
        if op16.get("dmh_op16_ready") is not True:
            blockers.append("dmh_op17_op16_not_ready")
        if op16.get("actual_review_evidence_complete_predicate_passed") is not True:
            blockers.append("dmh_op17_actual_review_evidence_complete_predicate_not_passed")
        if op16.get("actual_review_evidence_complete_from_real_review") is not True:
            blockers.append("dmh_op17_actual_review_evidence_complete_from_real_review_not_true")
        if op16.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF:
            blockers.append("dmh_op17_op16_next_step_not_postcr22_reentry_envelope")
        if _scan_forbidden_payload_key_paths(op16, path="dmh_op17_op16"):
            blockers.append("dmh_op17_op16_forbidden_payload_key_detected")
    return list(dict.fromkeys(blockers))


def build_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope(
    *,
    actual_review_evidence_complete_predicate: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP17 PostCR22 EX07-EX18 actual-evidence re-entry envelope.

    This only prepares a body-free handoff envelope.  It does not execute
    PostCR22 re-entry, R52, P5/P6/P8/P7, or release.
    """

    op16 = actual_review_evidence_complete_predicate if isinstance(actual_review_evidence_complete_predicate, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id or op16.get("review_session_id"))
    blockers = _dmh_op17_blockers(op16)
    ready = not blockers
    mapping_rows = [
        {
            "source_ref": source_ref,
            "target_ref": target_ref,
            "body_free": True,
            "reentry_executed_here": False,
            "r52_actual_execution_started_here": False,
        }
        for source_ref, target_ref in P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_MAPPING_REFS
    ] if ready else []
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP17_POSTCR22_EX07_EX18_ACTUAL_EVIDENCE_REENTRY_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op16_schema_version": _clean_ref(op16.get("schema_version"), default="op16_schema_missing", max_length=240),
        "op16_material_ref": _clean_ref(op16.get("material_id"), default="op16_material_missing", max_length=240),
        "op16_next_required_step": _clean_ref(op16.get("next_required_step"), default="op16_next_required_step_missing", max_length=240),
        "op16_dmh_ready": op16.get("dmh_op16_ready") is True,
        "op16_actual_review_evidence_complete_predicate_passed": op16.get("actual_review_evidence_complete_predicate_passed") is True,
        "op16_actual_review_evidence_complete_from_real_review": op16.get("actual_review_evidence_complete_from_real_review") is True,
        "dmh_op17_status_ref": P7_R54_AHR_POST_PMN23_DMH_OP17_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_STATUS_REF,
        "dmh_op17_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP17_ALLOWED_STATUS_REFS),
        "dmh_op17_ready": ready,
        "dmh_op17_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP17_READY_REASON_REFS) if ready else [],
        "dmh_op17_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP17_READY_REASON_REFS) if ready else 0,
        "dmh_op17_blocker_refs": blockers,
        "dmh_op17_blocker_ref_count": len(blockers),
        "postcr22_ex07_ex18_reentry_envelope_ref": P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_ENVELOPE_REF,
        "existing_postcr22_ex_reentry_helper_ref": P7_R54_AHR_POST_PMN23_DMH_EXISTING_POSTCR22_EX_HELPER_REF,
        "existing_postcr22_ex_reentry_step_refs": list(pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS),
        "existing_postcr22_ex_reentry_step_ref_count": len(pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS),
        "postcr22_ex07_ex18_mapping_rows": mapping_rows,
        "postcr22_ex07_ex18_mapping_row_count": len(mapping_rows),
        "postcr22_ex07_ex18_reentry_envelope_ready": ready,
        "postcr22_ex07_ex18_reentry_executed_here": False,
        "postcr22_ex07_ex18_reentry_execution_requested_here": False,
        "r52_actual_execution_started_here": False,
        "r52_actual_execution_confirmed": False,
        "candidate_only_separation_preserved": ready,
        "actual_review_evidence_complete_from_real_review": ready,
        "actual_review_evidence_complete_predicate_carried_into_reentry_envelope": ready,
        "p5_final_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "op17_does_not_execute_postcr22_ex_reentry": True,
        "op17_does_not_start_r52_actual_execution": True,
        "op17_does_not_start_p5_p6_p8_p7_or_release": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP17_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP17_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP16_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags_with_actual_review_evidence_complete(complete=ready),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP17_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP17_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP17")
    _assert_base_bodyfree_boundary_allow_actual_evidence_complete(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP17_POSTCR22_EX07_EX18_ACTUAL_EVIDENCE_REENTRY_ENVELOPE_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP17",
    )
    ready = bool(data.get("dmh_op17_ready"))
    blockers = list(data.get("dmh_op17_blocker_refs") or [])
    if data.get("dmh_op17_status_ref") != (P7_R54_AHR_POST_PMN23_DMH_OP17_READY_STATUS_REF if ready else P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_STATUS_REF):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 status changed")
    if tuple(data.get("dmh_op17_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP17_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 allowed status refs changed")
    if data.get("dmh_op17_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 blocker count changed")
    for key in (
        "postcr22_ex07_ex18_reentry_executed_here", "postcr22_ex07_ex18_reentry_execution_requested_here",
        "r52_actual_execution_started_here", "r52_actual_execution_confirmed", "p5_final_allowed", "p6_start_allowed",
        "p8_start_allowed", "p7_complete", "release_allowed", "actual_review_evidence_complete_from_real_operation_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP17 downstream flag promoted: {key}")
    for key in (
        "op17_does_not_execute_postcr22_ex_reentry", "op17_does_not_start_r52_actual_execution",
        "op17_does_not_start_p5_p6_p8_p7_or_release", "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP17 required true field changed: {key}")
    if data.get("existing_postcr22_ex_reentry_step_ref_count") != len(data.get("existing_postcr22_ex_reentry_step_refs") or []) or tuple(data.get("existing_postcr22_ex_reentry_step_refs") or ()) != pmn.P7_R54_AHR_POST_MN11_EXISTING_EX_LINE_REENTRY_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 existing EX line refs changed")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 basis changed")
    if ready:
        for key in (
            "op16_dmh_ready", "op16_actual_review_evidence_complete_predicate_passed", "op16_actual_review_evidence_complete_from_real_review",
            "postcr22_ex07_ex18_reentry_envelope_ready", "candidate_only_separation_preserved",
            "actual_review_evidence_complete_from_real_review", "actual_review_evidence_complete_predicate_carried_into_reentry_envelope",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP17 ready field changed: {key}")
        if blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 ready material cannot have blockers")
        if data.get("dmh_op17_reason_refs") != list(P7_R54_AHR_POST_PMN23_DMH_OP17_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 ready reasons changed")
        if data.get("postcr22_ex07_ex18_mapping_row_count") != len(P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_MAPPING_REFS) or len(data.get("postcr22_ex07_ex18_mapping_rows") or []) != len(P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_MAPPING_REFS):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 mapping row count changed")
        for row, expected in zip(data.get("postcr22_ex07_ex18_mapping_rows") or [], P7_R54_AHR_POST_PMN23_DMH_OP17_REENTRY_MAPPING_REFS):
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 mapping row must be mapping")
            if row.get("source_ref") != expected[0] or row.get("target_ref") != expected[1] or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 mapping row changed")
            if row.get("reentry_executed_here") is not False or row.get("r52_actual_execution_started_here") is not False:
                raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 mapping row executed downstream")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 implemented steps changed")
        if data.get("op16_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP17_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 OP16 next step changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 next step changed")
    else:
        if data.get("dmh_op17_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 blocked material cannot carry ready reasons")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 blocked material must carry blockers")
        for key in (
            "postcr22_ex07_ex18_reentry_envelope_ready", "candidate_only_separation_preserved",
            "actual_review_evidence_complete_from_real_review", "actual_review_evidence_complete_predicate_carried_into_reentry_envelope",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP17 blocked field promoted: {key}")
        if data.get("postcr22_ex07_ex18_mapping_rows") != [] or data.get("postcr22_ex07_ex18_mapping_row_count") != 0:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 blocked material cannot carry mapping rows")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP17 blocked next step changed")
    return True


def _dmh_op18_blockers(op17: Mapping[str, Any]) -> tuple[list[str], bool]:
    blockers: list[str] = []
    repair_required = False
    if not op17:
        blockers.append("dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_missing")
    else:
        try:
            assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(op17)
        except Exception:
            blockers.append("dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid")
            repair_required = True
        if op17.get("dmh_op17_ready") is not True:
            blockers.append("dmh_op18_op17_not_ready")
        if op17.get("postcr22_ex07_ex18_reentry_envelope_ready") is not True:
            blockers.append("dmh_op18_postcr22_ex07_ex18_reentry_envelope_not_ready")
        if op17.get("actual_review_evidence_complete_from_real_review") is not True:
            blockers.append("dmh_op18_actual_review_evidence_complete_from_real_review_missing")
        if op17.get("actual_review_evidence_complete_predicate_carried_into_reentry_envelope") is not True:
            blockers.append("dmh_op18_actual_review_evidence_predicate_not_carried_into_reentry_envelope")
        if op17.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF:
            blockers.append("dmh_op18_op17_next_step_not_result_memo_finalizer")
        if op17.get("postcr22_ex07_ex18_reentry_executed_here") is not False or op17.get("postcr22_ex07_ex18_reentry_execution_requested_here") is not False:
            blockers.append("dmh_op18_op17_reentry_execution_claim_detected")
            repair_required = True
        if op17.get("r52_actual_execution_started_here") is not False or op17.get("r52_actual_execution_confirmed") is not False:
            blockers.append("dmh_op18_op17_r52_actual_execution_claim_detected")
            repair_required = True
        if any(op17.get(key) is True for key in ("p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed")):
            blockers.append("dmh_op18_op17_downstream_promotion_claim_detected")
            repair_required = True
        if _scan_forbidden_payload_key_paths(op17, path="dmh_op18_op17"):
            blockers.append("dmh_op18_op17_forbidden_payload_key_detected")
            repair_required = True
    return list(dict.fromkeys(blockers)), repair_required


def build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer(
    *,
    postcr22_ex07_ex18_actual_evidence_reentry_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build DMH-OP18 result memo / downstream manual decision hold finalizer.

    The finalizer closes only a body-free result-memo boundary and selects the
    next manual step.  It never executes PostCR22 re-entry, R52, P5/P6/P8/P7,
    or release.
    """

    op17 = postcr22_ex07_ex18_actual_evidence_reentry_envelope if isinstance(postcr22_ex07_ex18_actual_evidence_reentry_envelope, Mapping) else {}
    session_id = _safe_review_session_id(review_session_id or op17.get("review_session_id"))
    blockers, repair_required = _dmh_op18_blockers(op17)
    ready = not blockers
    status = (
        P7_R54_AHR_POST_PMN23_DMH_OP18_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATUS_REF
        if repair_required
        else P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF
    )
    next_required_step = (
        P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_COMPLETE_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_REPAIR_REF
        if repair_required
        else P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_INCOMPLETE_REF
    )
    evidence_state_ref = (
        P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_COMPLETE_STATE_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATE_REF
        if repair_required
        else P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_INCOMPLETE_STATE_REF
    )
    downstream_state_ref = (
        P7_R54_AHR_POST_PMN23_DMH_OP18_DOWNSTREAM_MANUAL_DECISION_HOLD_STATE_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_BLOCKED_STATE_REF
    )
    material = {
        "schema_version": P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_DOWNSTREAM_MANUAL_DECISION_HOLD_FINALIZER_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_POST_PMN23_DMH_STEP,
        "scope": P7_R54_AHR_POST_PMN23_DMH_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PMN23_DMH_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": f"{P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF}:{session_id}",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op17_schema_version": _clean_ref(op17.get("schema_version"), default="op17_schema_missing", max_length=260),
        "op17_material_ref": _clean_ref(op17.get("material_id"), default="op17_material_missing", max_length=260),
        "op17_next_required_step": _clean_ref(op17.get("next_required_step"), default="op17_next_required_step_missing", max_length=260),
        "op17_dmh_ready": op17.get("dmh_op17_ready") is True,
        "op17_postcr22_ex07_ex18_reentry_envelope_ready": op17.get("postcr22_ex07_ex18_reentry_envelope_ready") is True,
        "op17_actual_review_evidence_complete_from_real_review": op17.get("actual_review_evidence_complete_from_real_review") is True,
        "op17_actual_review_evidence_complete_predicate_carried_into_reentry_envelope": op17.get("actual_review_evidence_complete_predicate_carried_into_reentry_envelope") is True,
        "op17_reentry_execution_claim_detected": op17.get("postcr22_ex07_ex18_reentry_executed_here") is True or op17.get("postcr22_ex07_ex18_reentry_execution_requested_here") is True,
        "op17_r52_actual_execution_claim_detected": op17.get("r52_actual_execution_started_here") is True or op17.get("r52_actual_execution_confirmed") is True,
        "op17_downstream_promotion_claim_detected": any(op17.get(key) is True for key in ("p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed")),
        "op17_forbidden_payload_key_detected": bool(_scan_forbidden_payload_key_paths(op17, path="dmh_op18_op17")),
        "dmh_op18_status_ref": status,
        "dmh_op18_allowed_status_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP18_ALLOWED_STATUS_REFS),
        "dmh_op18_ready": ready,
        "dmh_op18_reason_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS) if ready else [],
        "dmh_op18_reason_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS) if ready else 0,
        "dmh_op18_blocker_refs": blockers,
        "dmh_op18_blocker_ref_count": len(blockers),
        "result_memo_finalizer_ref": P7_R54_AHR_POST_PMN23_DMH_OP18_FINALIZER_REF,
        "result_memo_ref": P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REF,
        "result_memo_bodyfree_closed": ready,
        "result_memo_required_section_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_required_section_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REQUIRED_SECTION_REFS),
        "result_memo_includes_body_text": False,
        "result_memo_includes_question_text": False,
        "result_memo_includes_local_path": False,
        "result_memo_includes_body_hash": False,
        "result_memo_includes_terminal_output_body": False,
        "result_memo_contains_no_body_question_path_hash_or_terminal_output": True,
        "downstream_manual_decision_hold_ref": P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF,
        "downstream_manual_decision_hold_state_ref": downstream_state_ref,
        "downstream_manual_decision_hold_finalized": ready,
        "manual_downstream_decision_required": ready,
        "manual_decision_auto_executes_downstream": False,
        "actual_review_evidence_status_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_EVIDENCE_STATUS_REF,
        "actual_review_evidence_complete_candidate_from_real_review": ready,
        "actual_review_evidence_complete_from_real_review": ready,
        "actual_review_evidence_complete_predicate_carried_into_reentry_envelope": ready,
        "evidence_completion_state_ref": evidence_state_ref,
        "evidence_incomplete_continue_or_retry_required": not ready and not repair_required,
        "bodyfree_evidence_boundary_repair_required": repair_required,
        "postcr22_ex07_ex18_reentry_ready_candidate": ready,
        "postcr22_ex07_ex18_reentry_executed_here": False,
        "r52_actual_execution_started_here": False,
        "r52_actual_execution_confirmed": False,
        "p5_confirmed_candidate_not_p5_final": True,
        "p6_candidate_only_not_p6_start": True,
        "p8_material_candidate_only_not_p8_start": True,
        "r52_handoff_candidate_not_r52_actual_execution": True,
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PMN23_DMH_OP18_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_OP18_FIXED_NON_PROMOTION_REFS),
        "op18_does_not_execute_postcr22_ex_reentry": True,
        "op18_does_not_start_r52_actual_execution": True,
        "op18_does_not_start_p5_p6_p8_p7_or_release": True,
        "op18_does_not_create_question_text": True,
        "op18_does_not_change_api_db_rn_runtime_response_key": True,
        "op18_does_not_claim_full_backend_or_rn_green": True,
        "actual_review_basis_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed_ref": P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "current_actual_review_basis_remains_264_85_258_171": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PMN23_DMH_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP18_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PMN23_DMH_OP18_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_POST_PMN23_DMH_OP17_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "post_pmn23_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags_with_actual_review_evidence_complete(complete=ready),
        "body_free": True,
    }
    return {key: material[key] for key in P7_R54_AHR_POST_PMN23_DMH_OP18_REQUIRED_FIELD_REFS}


def assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_PMN23_DMH_OP18_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPMN23-DMH-OP18")
    _assert_base_bodyfree_boundary_allow_actual_evidence_complete(
        data,
        schema_version=P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_DOWNSTREAM_MANUAL_DECISION_HOLD_FINALIZER_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF,
        source="P7-R54-AHR-PostPMN23-DMH-OP18",
    )
    ready = bool(data.get("dmh_op18_ready"))
    blockers = list(data.get("dmh_op18_blocker_refs") or [])
    repair_required = data.get("bodyfree_evidence_boundary_repair_required") is True
    expected_status = (
        P7_R54_AHR_POST_PMN23_DMH_OP18_READY_STATUS_REF
        if ready
        else P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATUS_REF
        if repair_required
        else P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF
    )
    if data.get("dmh_op18_status_ref") != expected_status:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 status changed")
    if tuple(data.get("dmh_op18_allowed_status_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP18_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 allowed status refs changed")
    if data.get("dmh_op18_blocker_ref_count") != len(blockers):
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 blocker count changed")
    if data.get("result_memo_required_section_ref_count") != len(data.get("result_memo_required_section_refs") or []) or tuple(data.get("result_memo_required_section_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REQUIRED_SECTION_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 result memo sections changed")
    if data.get("fixed_non_promotion_ref_count") != len(data.get("fixed_non_promotion_refs") or []) or tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP18_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 fixed non-promotion refs changed")
    for key in (
        "result_memo_includes_body_text", "result_memo_includes_question_text", "result_memo_includes_local_path",
        "result_memo_includes_body_hash", "result_memo_includes_terminal_output_body", "manual_decision_auto_executes_downstream",
        "postcr22_ex07_ex18_reentry_executed_here", "r52_actual_execution_started_here", "r52_actual_execution_confirmed",
        "p5_final_allowed", "p6_start_allowed", "p8_start_allowed", "p7_complete", "release_allowed",
        "actual_review_evidence_complete_from_real_operation_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP18 downstream/bodyfree flag promoted: {key}")
    for key in (
        "result_memo_contains_no_body_question_path_hash_or_terminal_output", "p5_confirmed_candidate_not_p5_final",
        "p6_candidate_only_not_p6_start", "p8_material_candidate_only_not_p8_start", "r52_handoff_candidate_not_r52_actual_execution",
        "op18_does_not_execute_postcr22_ex_reentry", "op18_does_not_start_r52_actual_execution",
        "op18_does_not_start_p5_p6_p8_p7_or_release", "op18_does_not_create_question_text",
        "op18_does_not_change_api_db_rn_runtime_response_key", "op18_does_not_claim_full_backend_or_rn_green",
        "current_actual_review_basis_remains_264_85_258_171",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP18 required true field changed: {key}")
    if data.get("actual_review_basis_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_REF or data.get("actual_review_basis_allowed_ref") != P7_R54_AHR_POST_PMN23_DMH_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 basis changed")
    if ready:
        for key in (
            "op17_dmh_ready", "op17_postcr22_ex07_ex18_reentry_envelope_ready",
            "op17_actual_review_evidence_complete_from_real_review",
            "op17_actual_review_evidence_complete_predicate_carried_into_reentry_envelope",
            "result_memo_bodyfree_closed", "downstream_manual_decision_hold_finalized",
            "manual_downstream_decision_required", "actual_review_evidence_complete_candidate_from_real_review",
            "actual_review_evidence_complete_from_real_review", "actual_review_evidence_complete_predicate_carried_into_reentry_envelope",
            "postcr22_ex07_ex18_reentry_ready_candidate",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP18 ready field changed: {key}")
        if blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 ready material cannot have blockers")
        if data.get("dmh_op18_reason_refs") != list(P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS):
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 ready reasons changed")
        if data.get("op17_next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 OP17 next step changed")
        if data.get("evidence_completion_state_ref") != P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_COMPLETE_STATE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 ready evidence state changed")
        if data.get("downstream_manual_decision_hold_state_ref") != P7_R54_AHR_POST_PMN23_DMH_OP18_DOWNSTREAM_MANUAL_DECISION_HOLD_STATE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 ready hold state changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP18_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 implemented steps changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_COMPLETE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 ready next step changed")
    else:
        if data.get("dmh_op18_reason_refs") != []:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 blocked material cannot carry ready reasons")
        if not blockers:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 blocked material must carry blockers")
        for key in (
            "result_memo_bodyfree_closed", "downstream_manual_decision_hold_finalized", "manual_downstream_decision_required",
            "actual_review_evidence_complete_candidate_from_real_review", "actual_review_evidence_complete_from_real_review",
            "actual_review_evidence_complete_predicate_carried_into_reentry_envelope", "postcr22_ex07_ex18_reentry_ready_candidate",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-PostPMN23-DMH-OP18 blocked field promoted: {key}")
        if data.get("downstream_manual_decision_hold_state_ref") != P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_BLOCKED_STATE_REF:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 blocked hold state changed")
        expected_next = P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_REPAIR_REF if repair_required else P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_INCOMPLETE_REF
        expected_state = P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATE_REF if repair_required else P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_INCOMPLETE_STATE_REF
        if data.get("next_required_step") != expected_next or data.get("evidence_completion_state_ref") != expected_state:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 blocked next step/state changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_PMN23_DMH_OP17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-PostPMN23-DMH-OP18 blocked implemented steps changed")
    return True



build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_evidence_complete_predicate_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_actual_review_evidence_complete_predicate_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op16_actual_review_evidence_complete_predicate_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_postcr22_ex07_ex18_actual_evidence_reentry_envelope_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_postcr22_ex07_ex18_actual_evidence_reentry_envelope_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract
)
build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_result_memo_downstream_manual_decision_hold_finalizer_bodyfree = (
    build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer
)
assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_result_memo_downstream_manual_decision_hold_finalizer_bodyfree_contract = (
    assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract
)
