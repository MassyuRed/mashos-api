# -*- coding: utf-8 -*-
"""Post-PNT closed material next boundary confirmation helpers.

R0/R1/R2/R3/R4/R5/R6 scope.

This module is intentionally a thin body-free boundary after the already-closed
PNT-OP08 selected handoff-or-stop triage result memo.  R0 freezes the work
boundary; R1 adds the PCM helper file, constants, allowed refs, forbidden refs,
and a small constants-summary contract.  R2 implements PCM-OP00 and PCM-OP01. R3 implements PCM-OP02 and PCM-OP03. R4 implements PCM-OP04 and PCM-OP05. R5 implements PCM-OP06 and PCM-OP07. R6 implements PCM-OP08.

Important boundary:
* PCM requires one explicit closed PNT-OP08 material in future OP01 work.
* This module never calls a PNT-OP08 default builder, never synthesizes a
  current PNT lane, and never treats a PNT decision table or all-lane target
  green result as one selected closed material.
* This module does not execute the selected post-NCI boundary, DHR-OP05,
  DHR-OP06, DHR-OP07, DMD, R52, actual review, P8, release,
  API/DB/RN/runtime/response-key changes, validation commands, full-backend/RN/
  real-device claims, downstream builders after OP08, or question text
  materialization.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707 as pnt


P7_R54_AHR_POST_PNT_PCM_PHASE: Final = "P7"
P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_PNT_PCM_STEP: Final = (
    "R54-AHR-PostPNT_ClosedMaterialNextBoundaryConfirmation_20260707"
)
P7_R54_AHR_POST_PNT_PCM_SCOPE: Final = (
    "p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_boundary"
)
P7_R54_AHR_POST_PNT_PCM_POLICY_KIND: Final = (
    "r54_ahr_post_pnt_explicit_closed_material_next_boundary_confirmation_bodyfree_boundary"
)
P7_R54_AHR_POST_PNT_PCM_DEFAULT_REVIEW_SESSION_ID: Final = (
    "p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707"
)
P7_R54_AHR_POST_PNT_PCM_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-PNT Closed Material Next Boundary Confirmation / next design candidate only"
)
P7_R54_AHR_POST_PNT_PCM_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-PNT Closed Material Next Boundary Confirmation / next design candidate only"
)
P7_R54_AHR_POST_PNT_PCM_BOUNDARY_PREFIX_REF: Final = "PCM"
P7_R54_AHR_POST_PNT_PCM_BOUNDARY_PREFIX_MEANING_REF: Final = (
    "Post-PNT Closed Material confirmation"
)
P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF: Final = "R0_work_pre_freeze"
P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF: Final = "R1_helper_skeleton_constants"
P7_R54_AHR_POST_PNT_PCM_EXPECTED_FROM_PNT_OP08_REF: Final = (
    "PNT-OP08 body-free stopped closure may record a selected post-NCI next boundary; "
    "it is not downstream execution, DHR-OP05 permission, P8 start, P7 complete, or release readiness"
)
P7_R54_AHR_POST_PNT_PCM_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08"
)

P7_R54_AHR_POST_PNT_PCM_R1_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.r1_helper_skeleton_constants_summary.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op01_explicit_closed_pnt_op08_material_intake.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op02_closed_material_contract_validation.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op03_single_selected_lane_confirmation.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op04_next_work_class_resolver.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op05_next_design_candidate_envelope.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op07_validation_plan_result_memo_draft_material.bodyfree.v1"
)
P7_R54_AHR_POST_PNT_PCM_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pnt.pcm.op08_result_memo_closure.bodyfree.v1"
)

P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF: Final = (
    "PCM-OP00_scope_explicit_closed_material_no_execution_refreeze_after_PNT_OP08"
)
P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF: Final = (
    "PCM-OP01_explicit_closed_PNT_OP08_material_intake"
)
P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF: Final = (
    "PCM-OP02_closed_material_contract_validation"
)
P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF: Final = (
    "PCM-OP03_single_selected_lane_confirmation"
)
P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF: Final = "PCM-OP04_next_work_class_resolver"
P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF: Final = (
    "PCM-OP05_next_design_candidate_envelope_materialization"
)
P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF: Final = (
    "PCM-OP06_bodyfree_no_touch_no_promotion_no_auto_execution_guard"
)
P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF: Final = (
    "PCM-OP07_validation_plan_result_memo_draft_material"
)
P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF: Final = (
    "PCM-OP08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure"
)
P7_R54_AHR_POST_PNT_PCM_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_R0_R1_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_R0_R1_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_STEP_REFS
)

P7_R54_AHR_POST_PNT_PCM_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REQUIRED: Final = True
P7_R54_AHR_POST_PNT_PCM_PNT_OP08_DEFAULT_BUILDER_CALL_ALLOWED: Final = False
P7_R54_AHR_POST_PNT_PCM_PNT_OP08_DEFAULT_MATERIAL_SYNTHESIS_ALLOWED: Final = False
P7_R54_AHR_POST_PNT_PCM_PNT_OP08_DECISION_TABLE_AS_SINGLE_LANE_ALLOWED: Final = False
P7_R54_AHR_POST_PNT_PCM_PNT_OP08_TEST_FIXTURE_GENERATION_ALLOWED_ONLY_INSIDE_TESTS: Final = True
P7_R54_AHR_POST_PNT_PCM_SELECTED_POST_NCI_NEXT_BOUNDARY_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_SELECTED_PCM_NEXT_BOUNDARY_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_DHR_OP05_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_DHR_OP05_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_DHR_OP06_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_DMD_R52_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_ACTUAL_REVIEW_START_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_REPAIR_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_RAW_EVIDENCE_REQUEST_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_P8_QUESTION_DESIGN_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_API_DB_RN_RESPONSE_KEY_CHANGE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PNT_PCM_BODY_FREE: Final = True

P7_R54_AHR_POST_PNT_PCM_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(297).zip",
    "implemented_docs": "EmlisAIの実装済み資料(102).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_system_update_20260706(3).zip",
    "cocolon_app": "Cocolon(275).zip",
    "backend": "mashos-api(188).zip",
}
P7_R54_AHR_POST_PNT_PCM_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/07_latest_snapshot_diff.md",
    "Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/09_work_start_checklist.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/14_cocolon_joint_development_and_karen_thought_boundary.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/15_trust_based_joint_development_boundary_2026_06_05.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt",
    "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
    "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostPNT_NextBoundarySelection_PreDesignMemo_20260707.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostPNT_ClosedMaterialNextBoundaryConfirmation_DetailedDesign_ImplementationOrder_20260707.md",
    "mashos-api/ai/tests/R54_AHR_PostNCI_SelectedHandoffOrStopDecisionTriage_PNT_OP00_OP08_Result_20260707.md",
    "mashos-api/ai/tests/R54_AHR_PostNCI_SelectedHandoffOrStopDecisionTriage_PNT_R10_ResultMemoClosure_20260707.md",
    "mashos-api/ai/tests/R54_AHR_PostNCI_SelectedHandoffOrStopDecisionTriage_PNT_R11_NextWorkDecision_20260707.md",
)
P7_R54_AHR_POST_PNT_PCM_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "PNT-OP08 material default synthesis",
    "PNT-OP08 builder call without explicit closed material",
    "PNT R11 decision table as current selected lane",
    "six-outcome or all-lane summary as current selected lane",
    "selected_post_nci_next_boundary execution",
    "selected_pcm_next_boundary execution",
    "DHR-OP05 call / builder call / preflight scan execution",
    "DHR-OP06 call",
    "DHR-OP07 materialization",
    "DMD execution",
    "R52 actual execution",
    "actual review start",
    "actual body-full packet generation",
    "actual rows / question need observation rows creation",
    "raw evidence request",
    "repair execution",
    "P5 finalization",
    "P6 start",
    "P8 start",
    "P8 question design / implementation",
    "question_text / draft_question_text / answer_text materialization",
    "API / DB / RN / runtime / response key change",
    "json / schema file creation",
    "P7 completion",
    "release decision",
)
P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "PCM R0/R1 only freezes the post-PNT scope and provides helper skeleton constants",
    "PCM helper body must require one explicit closed PNT-OP08 material in future OP01 work",
    "PCM helper body must not call a PNT-OP08 default builder without explicit material",
    "PCM helper body must not synthesize current lane from PNT all-lane target green",
    "PCM constants keep PNT R11 decision table and six-outcome summary out of single-lane material",
    "PCM constants classify allowed lanes only as next_design_candidate, wait_hold, or stop",
    "PCM constants keep selected post-NCI and PCM next boundary refs not executed",
    "PCM constants keep DHR-OP05, P8 question design, and release unavailable",
    "PCM constants keep API / DB / RN / runtime / response key no-touch",
)
P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "pcm_op00_implemented",
    "pcm_op01_implemented",
    "pcm_op02_implemented",
    "pcm_op03_implemented",
    "pcm_op04_implemented",
    "pcm_op05_implemented",
    "pcm_op06_implemented",
    "pcm_op07_implemented",
    "pcm_op08_implemented",
    "pnt_op08_builder_called_here",
    "pnt_op08_material_synthesized_here",
    "pnt_r11_decision_table_used_as_single_lane_here",
    "selected_post_nci_next_boundary_executed_here",
    "selected_pcm_next_boundary_executed_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_body_full_packet_generated_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "raw_evidence_request_created_here",
    "repair_executed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_pnt_op08_default_builder_call_without_explicit_closed_material",
    "no_pnt_op08_material_synthesis",
    "no_pnt_r11_decision_table_as_current_lane",
    "no_all_lane_target_green_as_current_lane",
    "no_selected_post_nci_next_boundary_execution",
    "no_selected_pcm_next_boundary_execution",
    "no_dhr_op05_call_or_builder_call",
    "no_dhr_op06_or_dhr_op07",
    "no_dmd_or_r52_execution",
    "no_actual_review_execution",
    "no_actual_rows_creation",
    "no_raw_evidence_request",
    "no_repair_execution",
    "no_p5_p6_p8_p7_release_promotion",
    "no_api_db_rn_runtime_response_key_change",
    "no_p8_question_text_or_question_spec_materialization",
    "no_json_schema_file_creation_in_r0_r1",
)

P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS: Final[tuple[str, ...]] = (
    pnt.P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS
)
P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF
)
P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF
)
P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF
)
P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF
)
P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF
)
P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
)

P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF: Final = "next_design_candidate"
P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF: Final = "wait_hold"
P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF: Final = "stop"
P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF,
    P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
)
P7_R54_AHR_POST_PNT_PCM_ALLOWED_OUTCOME_GROUP_REFS: Final[tuple[str, ...]] = (
    pnt.P7_R54_AHR_POST_NCI_PNT_ALLOWED_OUTCOME_GROUP_REFS
)
P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF,
}

P7_R54_AHR_POST_PNT_PCM_NEXT_DESIGN_DOCUMENT_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_DHR_OP05_BOUNDARY_REF
)
P7_R54_AHR_POST_PNT_PCM_NEXT_DESIGN_DOCUMENT_RETRY_START_BOUNDARY_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_RETRY_START_REF
)
P7_R54_AHR_POST_PNT_PCM_NEXT_DESIGN_DOCUMENT_REPAIR_BOUNDARY_REF: Final = (
    pnt.P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_REPAIR_BOUNDARY_REF
)
P7_R54_AHR_POST_PNT_PCM_WAIT_HOLD_EXTERNAL_BODYFREE_CLAIM_REF: Final = (
    "hold_for_external_bodyfree_claim_reintake_without_raw_evidence"
)
P7_R54_AHR_POST_PNT_PCM_STOP_MANUAL_HOLD_UNRESOLVED_REF: Final = (
    "stop_manual_hold_unresolved_without_next_design_promotion"
)
P7_R54_AHR_POST_PNT_PCM_STOP_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "stop_blocked_bodyfree_leak_promotion_or_autorun_without_next_design_promotion"
)
P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_DESIGN_OR_HOLD_STOP_REFS: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_DESIGN_DOCUMENT_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_DESIGN_DOCUMENT_RETRY_START_BOUNDARY_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_WAIT_HOLD_EXTERNAL_BODYFREE_CLAIM_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_NEXT_DESIGN_DOCUMENT_REPAIR_BOUNDARY_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_STOP_MANUAL_HOLD_UNRESOLVED_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_STOP_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
}

P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_DHR_OP05_PREFLIGHT_DESIGN_WITHOUT_CALL_REF: Final = (
    "prepare_post_pnt_dhr_op05_manual_handoff_boundary_preflight_design_without_call"
)
P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_ACTUAL_LOCAL_ONLY_REVIEW_RETRY_START_DESIGN_WITHOUT_EXECUTION_REF: Final = (
    "prepare_post_pnt_actual_local_only_review_retry_start_boundary_design_without_execution"
)
P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_RDB_OR_UPSTREAM_REPAIR_DESIGN_WITHOUT_EXECUTION_REF: Final = (
    "prepare_post_pnt_rdb_or_upstream_repair_boundary_design_without_execution"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_BOUNDARY_KIND_NEXT_DESIGN_CANDIDATE_REF: Final = (
    "pcm_next_design_candidate_boundary_without_execution"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_BOUNDARY_KIND_WAIT_HOLD_REF: Final = (
    "pcm_wait_hold_without_raw_evidence"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_BOUNDARY_KIND_STOP_REF: Final = (
    "pcm_stop_without_next_design_promotion"
)
P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_DHR_OP05_PREFLIGHT_DESIGN_WITHOUT_CALL_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_ACTUAL_LOCAL_ONLY_REVIEW_RETRY_START_DESIGN_WITHOUT_EXECUTION_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_WAIT_HOLD_EXTERNAL_BODYFREE_CLAIM_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_RDB_OR_UPSTREAM_REPAIR_DESIGN_WITHOUT_EXECUTION_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_STOP_MANUAL_HOLD_UNRESOLVED_REF,
    P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF: P7_R54_AHR_POST_PNT_PCM_STOP_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
}
P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF_MAP: Final[Mapping[str, str]] = {
    lane_ref: (
        P7_R54_AHR_POST_PNT_PCM_NEXT_BOUNDARY_KIND_NEXT_DESIGN_CANDIDATE_REF
        if P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref] == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF
        else P7_R54_AHR_POST_PNT_PCM_NEXT_BOUNDARY_KIND_WAIT_HOLD_REF
        if P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref] == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF
        else P7_R54_AHR_POST_PNT_PCM_NEXT_BOUNDARY_KIND_STOP_REF
    )
    for lane_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS
}

P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_READY_FOR_OP02_REF: Final = (
    "PCM_STATUS_PNT_OP08_CLOSED_MATERIAL_INTAKE_READY_FOR_CONTRACT_VALIDATION"
)
P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF: Final = (
    "PCM_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL"
)
P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_PNT_OP08_TO_CLOSE_REF: Final = (
    "PCM_STATUS_WAITING_FOR_PNT_OP08_TO_CLOSE"
)
P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF: Final = (
    "PCM_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL"
)
P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "PCM_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_PNT_PCM_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_READY_FOR_OP02_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_PNT_OP08_TO_CLOSE_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "PCM_STATUS_CLOSED_PNT_OP08_MATERIAL_CONTRACT_VALID_STOPPED",
    "PCM_STATUS_REPAIR_REQUIRED_FOR_CLOSED_PNT_OP08_MATERIAL_CONTRACT",
    "PCM_STATUS_BLOCKED_CLOSED_PNT_OP08_MATERIAL_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PNT_PCM_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "PCM_STATUS_SINGLE_SELECTED_PNT_LANE_CONFIRMED_STOPPED",
    "PCM_STATUS_WAITING_FOR_SINGLE_SELECTED_PNT_LANE_MATERIAL",
    "PCM_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_PNT_LANE_MATERIAL",
    "PCM_STATUS_BLOCKED_SINGLE_LANE_CONFIRMATION_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_NEXT_WORK_CLASS_RESOLVED_STOPPED_REF: Final = (
    "PCM_STATUS_NEXT_WORK_CLASS_RESOLVED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF: Final = (
    "PCM_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS"
)
P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF: Final = (
    "PCM_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN"
)
P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF: Final = (
    "PCM_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF: Final = (
    "PCM_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF: Final = (
    "PCM_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF: Final = (
    "PCM_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS"
)
P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF: Final = (
    "PCM_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN"
)
P7_R54_AHR_POST_PNT_PCM_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_NEXT_WORK_CLASS_RESOLVED_STOPPED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_GUARD_PASSED_REF: Final = (
    "PCM_STATUS_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD_PASSED"
)
P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF: Final = (
    "PCM_STATUS_REPAIR_REQUIRED_FOR_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_INPUTS"
)
P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_BLOCKED_GUARD_REF: Final = (
    "PCM_STATUS_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD"
)
P7_R54_AHR_POST_PNT_PCM_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_GUARD_PASSED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_BLOCKED_GUARD_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF: Final = (
    "PCM_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF: Final = (
    "PCM_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF: Final = (
    "PCM_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS"
)
P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_BLOCKED_RESULT_MEMO_DRAFT_REF: Final = (
    "PCM_STATUS_BLOCKED_RESULT_MEMO_DRAFT_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_PNT_PCM_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_BLOCKED_RESULT_MEMO_DRAFT_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_CLOSED_STOPPED_REF: Final = (
    "PCM_OP08_BODYFREE_POST_PNT_CLOSED_MATERIAL_CONFIRMATION_CLOSED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF: Final = (
    "PCM_OP08_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL"
)
P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_REPAIR_REQUIRED_FOR_POST_PNT_CONFIRMATION_INPUTS_REF: Final = (
    "PCM_OP08_REPAIR_REQUIRED_FOR_POST_PNT_CONFIRMATION_INPUTS"
)
P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "PCM_OP08_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_PNT_PCM_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_CLOSED_STOPPED_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_REPAIR_REQUIRED_FOR_POST_PNT_CONFIRMATION_INPUTS_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
)
P7_R54_AHR_POST_PNT_PCM_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_PNT_PCM_OP01_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PNT_PCM_OP02_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PNT_PCM_OP03_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PNT_PCM_OP04_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PNT_PCM_OP05_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PNT_PCM_OP06_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PNT_PCM_OP07_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PNT_PCM_OP08_ALLOWED_STATUS_REFS
    )
)

P7_R54_AHR_POST_PNT_PCM_PNT_OP08_REQUIRED_KEY_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "operation_step_ref",
    "body_free",
    "pnt_op08_status_ref",
    "pnt_op08_closed_bodyfree_stopped",
    "selected_pnt_status_ref",
    "selected_pnt_lane_ref",
    "selected_post_nci_outcome_group_ref",
    "selected_post_nci_next_boundary_ref",
    "selected_post_nci_next_boundary_kind_ref",
    "selected_post_nci_next_boundary_not_executed",
    "selected_handoff_or_stop_ref",
    "selected_handoff_or_stop_kind_ref",
    "selected_handoff_or_stop_not_executed",
    "next_design_document_candidate_ref",
    "next_design_document_allowed",
    "manual_wait_required",
    "manual_stop_required",
    "repair_design_candidate",
    "target_test_result_status_ref",
    "selected_regression_result_status_ref",
    "compileall_result_status_ref",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "dhr_op05_not_called",
    "dhr_op06_not_called",
    "dmd_r52_not_executed",
    "p5_p6_p8_p7_release_not_started",
    "p8_question_design_not_started",
    "p8_question_implementation_not_started",
    "api_db_rn_runtime_response_key_not_changed",
)
P7_R54_AHR_POST_PNT_PCM_DECISION_TABLE_OR_MULTI_LANE_MATERIAL_KEY_REFS: Final[tuple[str, ...]] = (
    "decision_table",
    "all_outcomes",
    "all_lane_summary",
    "six_outcome_summary",
    "supported_outcomes",
    "allowed_lanes_table",
    "target_green_all_lane_fixture_summary",
)
P7_R54_AHR_POST_PNT_PCM_NO_TOUCH_CONTRACT_KEYS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        pnt.P7_R54_AHR_POST_NCI_PNT_NO_TOUCH_CONTRACT_KEYS
        + (
            "api_changed",
            "db_changed",
            "rn_changed",
            "runtime_changed",
            "response_key_changed",
            "p8_question_design_changed",
            "p8_question_implementation_changed",
            "json_schema_file_created_here",
        )
    )
)
P7_R54_AHR_POST_PNT_PCM_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        pnt.P7_R54_AHR_POST_NCI_PNT_BODY_FREE_MARKER_REFS
        + (
            "raw_evidence_included",
            "body_included",
            "body_full_packet_included",
            "comment_text_included",
            "question_text_included",
            "question_answer_body_included",
            "local_path_included",
            "hash_included",
            "stdout_stderr_traceback_included",
        )
    )
)
P7_R54_AHR_POST_PNT_PCM_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        pnt.P7_R54_AHR_POST_NCI_PNT_FORBIDDEN_PAYLOAD_KEY_REFS
        + (
            "raw_input",
            "raw_answer",
            "raw_evidence",
            "body",
            "body_full_packet",
            "comment_text",
            "reviewer_comment",
            "reviewer_free_text",
            "question_text",
            "draft_question_text",
            "answer_text",
            "local_path",
            "absolute_path",
            "hash",
            "sha256",
            "stdout",
            "stderr",
            "traceback",
        )
    )
)
P7_R54_AHR_POST_PNT_PCM_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        pnt.P7_R54_AHR_POST_NCI_PNT_PROMOTION_CLAIM_FIELD_REFS
        + (
            "pnt_op08_builder_called_here",
            "pnt_op08_material_synthesized_here",
            "pnt_r11_decision_table_used_as_single_lane_here",
            "selected_post_nci_next_boundary_executed_here",
            "selected_pcm_next_boundary_executed_here",
            "selected_pcm_next_boundary_execution_allowed_here",
            "dhr_op05_call_allowed_here",
            "dhr_op05_builder_call_allowed_here",
            "dhr_op06_call_allowed_here",
            "dmd_r52_execution_allowed_here",
            "actual_review_start_allowed_here",
            "raw_evidence_request_allowed_here",
            "repair_execution_allowed_here",
            "p8_question_design_allowed_here",
            "api_db_rn_response_key_change_allowed_here",
            "json_schema_file_created_here",
            "pcm_op00_implemented",
            "pcm_op01_implemented",
            "pcm_op02_implemented",
            "pcm_op03_implemented",
            "pcm_op04_implemented",
            "pcm_op05_implemented",
            "pcm_op06_implemented",
            "pcm_op07_implemented",
            "pcm_op08_implemented",
        )
    )
)
P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        pnt.P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS
        + (
            "pnt_op08_builder_called_here",
            "pnt_op08_material_synthesized_here",
            "pnt_r11_decision_table_used_as_single_lane_here",
            "selected_post_nci_next_boundary_executed_here",
            "selected_pcm_next_boundary_executed_here",
            "dhr_op05_called_here",
            "dhr_op05_builder_called_here",
            "dhr_op06_called_here",
            "dhr_op07_materialized_here",
            "dmd_execution_started_here",
            "r52_actual_execution_started_here",
            "actual_review_started_here",
            "actual_body_full_packet_generated_here",
            "actual_rows_created_here",
            "actual_question_need_observation_rows_created_here",
            "actual_disposal_or_purge_executed_here",
            "raw_evidence_request_created_here",
            "repair_executed_here",
            "p8_start_allowed",
            "p8_question_design_started",
            "p8_question_implementation_started",
            "question_text_materialized",
            "api_changed",
            "db_changed",
            "rn_changed",
            "runtime_changed",
            "response_key_changed",
            "json_schema_file_created_here",
            "pcm_op00_implemented",
            "pcm_op01_implemented",
            "pcm_op02_implemented",
            "pcm_op03_implemented",
            "pcm_op04_implemented",
            "pcm_op05_implemented",
            "pcm_op06_implemented",
            "pcm_op07_implemented",
            "pcm_op08_implemented",
        )
    )
)

P7_R54_AHR_POST_PNT_PCM_OP00_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key != "pcm_op00_implemented"
)
P7_R54_AHR_POST_PNT_PCM_OP01_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented"}
)

P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_op01_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_op03_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_op05_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_op07_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_result_20260707.py",
)
P7_R54_AHR_POST_PNT_PCM_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS
    + pnt.P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS
    + pnt.P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS
)
P7_R54_AHR_POST_PNT_PCM_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
        )
        + pnt.P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS
    )
)
P7_R54_AHR_POST_PNT_PCM_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "R7 target validation must be run externally after PCM-OP00..OP08 implementation",
    "R8 selected regression must be run externally after PCM target validation",
    "R9 compileall must be run externally after helper and selected upstream modules are present",
    "R0/R1 skeleton does not run pytest or compileall internally",
)

P7_R54_AHR_POST_PNT_PCM_R1_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "operation_step_ref",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "selected_stage_ref",
    "selected_design_target_ref",
    "boundary_prefix_ref",
    "boundary_prefix_meaning_ref",
    "expected_from_pnt_op08_ref",
    "expected_next_required_step_ref",
    "implemented_step_refs",
    "not_yet_implemented_step_refs",
    "pcm_step_refs",
    "local_received_zip_refs",
    "support_material_refs",
    "not_stage_refs",
    "claim_boundary_refs",
    "not_claimed_boundary_refs",
    "fixed_non_promotion_refs",
    "explicit_pnt_op08_closed_material_required",
    "pnt_op08_default_builder_call_allowed",
    "pnt_op08_default_material_synthesis_allowed",
    "pnt_op08_decision_table_as_single_lane_allowed",
    "pnt_op08_test_fixture_generation_allowed_only_inside_tests",
    "selected_post_nci_next_boundary_execution_allowed_here",
    "selected_pcm_next_boundary_execution_allowed_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "dhr_op06_call_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "repair_execution_allowed_here",
    "raw_evidence_request_allowed_here",
    "p8_question_design_allowed_here",
    "api_db_rn_response_key_change_allowed_here",
    "json_schema_file_creation_allowed_here",
    "allowed_lane_refs",
    "allowed_outcome_group_refs",
    "allowed_next_work_class_refs",
    "lane_to_next_work_class_refs",
    "lane_to_next_design_or_hold_stop_refs",
    "allowed_status_refs",
    "pnt_op08_required_key_refs",
    "decision_table_or_multi_lane_material_key_refs",
    "no_touch_contract_keys",
    "body_free_marker_refs",
    "forbidden_payload_key_refs",
    "promotion_claim_field_refs",
    "required_false_flag_refs",
    "target_test_ref_refs",
    "selected_regression_test_ref_refs",
    "compileall_target_ref_refs",
    "validation_command_summary_refs",
    "public_contract",
    *P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS,
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "next_required_step",
    "body_free",
)


def build_p7_r54_ahr_post_pnt_pcm_r1_helper_skeleton_constants_summary(
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Return a body-free R0/R1 constants summary without calling PNT builders."""

    safe_review_session_id = clean_identifier(
        review_session_id,
        default=P7_R54_AHR_POST_PNT_PCM_DEFAULT_REVIEW_SESSION_ID,
        max_length=160,
    )
    data: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_R1_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
        "material_id": "p7_r54_ahr_post_pnt_pcm_r1_helper_skeleton_constants_summary_20260707",
        "review_session_id": safe_review_session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_PNT_PCM_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_PNT_PCM_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_PNT_PCM_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_PNT_PCM_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_pnt_op08_ref": P7_R54_AHR_POST_PNT_PCM_EXPECTED_FROM_PNT_OP08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_PNT_PCM_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "implemented_step_refs": P7_R54_AHR_POST_PNT_PCM_R0_R1_IMPLEMENTED_STEPS,
        "not_yet_implemented_step_refs": P7_R54_AHR_POST_PNT_PCM_R0_R1_NOT_YET_IMPLEMENTED_STEPS,
        "pcm_step_refs": P7_R54_AHR_POST_PNT_PCM_STEP_REFS,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_PNT_PCM_LOCAL_RECEIVED_ZIP_REFS),
        "support_material_refs": P7_R54_AHR_POST_PNT_PCM_SUPPORT_MATERIAL_REFS,
        "not_stage_refs": P7_R54_AHR_POST_PNT_PCM_NOT_STAGE_REFS,
        "claim_boundary_refs": P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS,
        "not_claimed_boundary_refs": P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS,
        "fixed_non_promotion_refs": P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS,
        "explicit_pnt_op08_closed_material_required": P7_R54_AHR_POST_PNT_PCM_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REQUIRED,
        "pnt_op08_default_builder_call_allowed": P7_R54_AHR_POST_PNT_PCM_PNT_OP08_DEFAULT_BUILDER_CALL_ALLOWED,
        "pnt_op08_default_material_synthesis_allowed": P7_R54_AHR_POST_PNT_PCM_PNT_OP08_DEFAULT_MATERIAL_SYNTHESIS_ALLOWED,
        "pnt_op08_decision_table_as_single_lane_allowed": P7_R54_AHR_POST_PNT_PCM_PNT_OP08_DECISION_TABLE_AS_SINGLE_LANE_ALLOWED,
        "pnt_op08_test_fixture_generation_allowed_only_inside_tests": P7_R54_AHR_POST_PNT_PCM_PNT_OP08_TEST_FIXTURE_GENERATION_ALLOWED_ONLY_INSIDE_TESTS,
        "selected_post_nci_next_boundary_execution_allowed_here": P7_R54_AHR_POST_PNT_PCM_SELECTED_POST_NCI_NEXT_BOUNDARY_EXECUTION_ALLOWED_HERE,
        "selected_pcm_next_boundary_execution_allowed_here": P7_R54_AHR_POST_PNT_PCM_SELECTED_PCM_NEXT_BOUNDARY_EXECUTION_ALLOWED_HERE,
        "dhr_op05_call_allowed_here": P7_R54_AHR_POST_PNT_PCM_DHR_OP05_CALL_ALLOWED_HERE,
        "dhr_op05_builder_call_allowed_here": P7_R54_AHR_POST_PNT_PCM_DHR_OP05_BUILDER_CALL_ALLOWED_HERE,
        "dhr_op06_call_allowed_here": P7_R54_AHR_POST_PNT_PCM_DHR_OP06_CALL_ALLOWED_HERE,
        "dmd_r52_execution_allowed_here": P7_R54_AHR_POST_PNT_PCM_DMD_R52_EXECUTION_ALLOWED_HERE,
        "actual_review_start_allowed_here": P7_R54_AHR_POST_PNT_PCM_ACTUAL_REVIEW_START_ALLOWED_HERE,
        "repair_execution_allowed_here": P7_R54_AHR_POST_PNT_PCM_REPAIR_EXECUTION_ALLOWED_HERE,
        "raw_evidence_request_allowed_here": P7_R54_AHR_POST_PNT_PCM_RAW_EVIDENCE_REQUEST_ALLOWED_HERE,
        "p8_question_design_allowed_here": P7_R54_AHR_POST_PNT_PCM_P8_QUESTION_DESIGN_ALLOWED_HERE,
        "api_db_rn_response_key_change_allowed_here": P7_R54_AHR_POST_PNT_PCM_API_DB_RN_RESPONSE_KEY_CHANGE_ALLOWED_HERE,
        "json_schema_file_creation_allowed_here": P7_R54_AHR_POST_PNT_PCM_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE,
        "allowed_lane_refs": P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS,
        "allowed_outcome_group_refs": P7_R54_AHR_POST_PNT_PCM_ALLOWED_OUTCOME_GROUP_REFS,
        "allowed_next_work_class_refs": P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS,
        "lane_to_next_work_class_refs": dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS),
        "lane_to_next_design_or_hold_stop_refs": dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_DESIGN_OR_HOLD_STOP_REFS),
        "allowed_status_refs": P7_R54_AHR_POST_PNT_PCM_ALLOWED_STATUS_REFS,
        "pnt_op08_required_key_refs": P7_R54_AHR_POST_PNT_PCM_PNT_OP08_REQUIRED_KEY_REFS,
        "decision_table_or_multi_lane_material_key_refs": P7_R54_AHR_POST_PNT_PCM_DECISION_TABLE_OR_MULTI_LANE_MATERIAL_KEY_REFS,
        "no_touch_contract_keys": P7_R54_AHR_POST_PNT_PCM_NO_TOUCH_CONTRACT_KEYS,
        "body_free_marker_refs": P7_R54_AHR_POST_PNT_PCM_BODY_FREE_MARKER_REFS,
        "forbidden_payload_key_refs": P7_R54_AHR_POST_PNT_PCM_FORBIDDEN_PAYLOAD_KEY_REFS,
        "promotion_claim_field_refs": P7_R54_AHR_POST_PNT_PCM_PROMOTION_CLAIM_FIELD_REFS,
        "required_false_flag_refs": P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS,
        "target_test_ref_refs": P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS,
        "selected_regression_test_ref_refs": P7_R54_AHR_POST_PNT_PCM_SELECTED_REGRESSION_TEST_REF_REFS,
        "compileall_target_ref_refs": P7_R54_AHR_POST_PNT_PCM_COMPILEALL_TARGET_REF_REFS,
        "validation_command_summary_refs": P7_R54_AHR_POST_PNT_PCM_VALIDATION_COMMAND_SUMMARY_REFS,
        "public_contract": public_contract_flags(),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "next_required_step": P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
        "body_free": True,
    }
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS:
        data[key] = False
    return data


def assert_p7_r54_ahr_post_pnt_pcm_r1_helper_skeleton_constants_summary_contract(
    data: Mapping[str, Any],
) -> bool:
    """Validate the R0/R1 skeleton summary without validating future OP00+ output."""

    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_R1_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_PNT_PCM_R1_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 schema version mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 operation step mismatch")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 must remain body-free")
    if data.get("source_mode") != P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 must not require/check GitHub")
    if tuple(data.get("implemented_step_refs", ())) != P7_R54_AHR_POST_PNT_PCM_R0_R1_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_step_refs", ())) != P7_R54_AHR_POST_PNT_PCM_R0_R1_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 must leave PCM-OP00..OP08 not yet implemented")
    if tuple(data.get("pcm_step_refs", ())) != P7_R54_AHR_POST_PNT_PCM_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 PCM step refs mismatch")
    if data.get("explicit_pnt_op08_closed_material_required") is not True:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 must require explicit future closed PNT-OP08 material")
    if data.get("pnt_op08_default_builder_call_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 must not allow PNT-OP08 default builder calls")
    if data.get("pnt_op08_default_material_synthesis_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 must not allow PNT-OP08 material synthesis")
    if data.get("pnt_op08_decision_table_as_single_lane_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 must reject PNT decision table as a single lane")
    if tuple(data.get("allowed_lane_refs", ())) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 allowed lane refs mismatch")
    if tuple(data.get("allowed_outcome_group_refs", ())) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_OUTCOME_GROUP_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 allowed outcome refs mismatch")
    if tuple(data.get("allowed_next_work_class_refs", ())) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 allowed next work class refs mismatch")
    if dict(data.get("lane_to_next_work_class_refs", {})) != dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 lane-to-next-work-class refs mismatch")
    if dict(data.get("lane_to_next_design_or_hold_stop_refs", {})) != dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_DESIGN_OR_HOLD_STOP_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 lane-to-next-design refs mismatch")
    if tuple(data.get("allowed_status_refs", ())) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 allowed status refs mismatch")
    if tuple(data.get("decision_table_or_multi_lane_material_key_refs", ())) != P7_R54_AHR_POST_PNT_PCM_DECISION_TABLE_OR_MULTI_LANE_MATERIAL_KEY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 decision table guard refs mismatch")
    if tuple(data.get("pnt_op08_required_key_refs", ())) != P7_R54_AHR_POST_PNT_PCM_PNT_OP08_REQUIRED_KEY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 closed PNT-OP08 required key refs mismatch")
    if tuple(data.get("target_test_ref_refs", ())) != P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 target test refs mismatch")
    if tuple(data.get("compileall_target_ref_refs", ())) != P7_R54_AHR_POST_PNT_PCM_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 compileall target refs mismatch")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 public contract changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-R1 next step must be PCM-OP00")
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-R1 forbidden promotion flag set: {key}")
    for key in (
        "selected_post_nci_next_boundary_execution_allowed_here",
        "selected_pcm_next_boundary_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "repair_execution_allowed_here",
        "raw_evidence_request_allowed_here",
        "p8_question_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-R1 no-execution flag changed: {key}")
    return True



P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF: Final = (
    "wait_for_explicit_pnt_op08_closed_material"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_PNT_OP08_CLOSURE_REF: Final = (
    "wait_for_pnt_op08_closure_before_post_pnt_confirmation"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF: Final = (
    "repair_pnt_op08_material_without_downstream_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_PNT_OP08_CLOSED_MATERIAL_REF: Final = (
    "blocked_post_pnt_confirmation_due_to_pnt_op08_block"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF: Final = (
    "repair_closed_pnt_op08_material_contract_without_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF: Final = (
    "blocked_closed_pnt_op08_material_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_SINGLE_SELECTED_PNT_LANE_MATERIAL_REF: Final = (
    "wait_for_single_selected_pnt_lane_material_without_lane_synthesis"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_MULTI_OR_AMBIGUOUS_PNT_LANE_MATERIAL_REF: Final = (
    "repair_multi_or_ambiguous_pnt_lane_material_without_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_SINGLE_LANE_CONFIRMATION_REF: Final = (
    "blocked_single_selected_lane_confirmation_leak_promotion_or_autorun"
)

P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_CONTRACT_VALID_STOPPED_REF: Final = (
    "PCM_STATUS_CLOSED_PNT_OP08_MATERIAL_CONTRACT_VALID_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_REPAIR_REQUIRED_FOR_CONTRACT_REF: Final = (
    "PCM_STATUS_REPAIR_REQUIRED_FOR_CLOSED_PNT_OP08_MATERIAL_CONTRACT"
)
P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_BLOCKED_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "PCM_STATUS_BLOCKED_CLOSED_PNT_OP08_MATERIAL_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_SINGLE_SELECTED_LANE_CONFIRMED_STOPPED_REF: Final = (
    "PCM_STATUS_SINGLE_SELECTED_PNT_LANE_CONFIRMED_STOPPED"
)
P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_WAITING_FOR_SINGLE_SELECTED_LANE_MATERIAL_REF: Final = (
    "PCM_STATUS_WAITING_FOR_SINGLE_SELECTED_PNT_LANE_MATERIAL"
)
P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_LANE_REF: Final = (
    "PCM_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_PNT_LANE_MATERIAL"
)
P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_BLOCKED_PROMOTION_OR_AUTORUN_REF: Final = (
    "PCM_STATUS_BLOCKED_SINGLE_LANE_CONFIRMATION_PROMOTION_OR_AUTORUN"
)

P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_WORK_CLASS_INPUTS_REF: Final = (
    "repair_next_work_class_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_WORK_CLASS_RESOLVER_REF: Final = (
    "blocked_next_work_class_resolver_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_DESIGN_CANDIDATE_ENVELOPE_INPUTS_REF: Final = (
    "repair_next_design_candidate_envelope_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_DESIGN_CANDIDATE_ENVELOPE_REF: Final = (
    "blocked_next_design_candidate_envelope_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_INPUTS_REF: Final = (
    "repair_bodyfree_no_touch_no_promotion_guard_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_REF: Final = (
    "blocked_bodyfree_no_touch_no_promotion_no_auto_execution_guard"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_RESULT_MEMO_DRAFT_INPUTS_REF: Final = (
    "repair_validation_plan_result_memo_draft_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_RESULT_MEMO_DRAFT_REF: Final = (
    "blocked_validation_plan_result_memo_draft_due_to_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF: Final = (
    "repair_post_pnt_closed_material_confirmation_closure_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF: Final = (
    "blocked_post_pnt_closed_material_confirmation_closure_due_to_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_STOP_AFTER_OP08_NEXT_DESIGN_CANDIDATE_REF: Final = (
    "stop_after_pcm_op08_with_next_design_candidate_recorded_no_execution"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_HOLD_AFTER_OP08_REF: Final = (
    "manual_wait_hold_after_pcm_op08_without_raw_evidence_request"
)
P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_STOP_AFTER_OP08_REF: Final = (
    "stop_after_pcm_op08_without_next_design_promotion"
)


P7_R54_AHR_POST_PNT_PCM_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)

P7_R54_AHR_POST_PNT_PCM_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PNT_PCM_R0_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_R1_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
)
P7_R54_AHR_POST_PNT_PCM_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_PNT_PCM_OP02_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented"}
)
P7_R54_AHR_POST_PNT_PCM_OP03_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented"}
)

P7_R54_AHR_POST_PNT_PCM_OP04_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented"}
)
P7_R54_AHR_POST_PNT_PCM_OP05_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented"}
)
P7_R54_AHR_POST_PNT_PCM_OP06_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented"}
)
P7_R54_AHR_POST_PNT_PCM_OP07_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented", "pcm_op07_implemented"}
)
P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS
    if key not in {"pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented", "pcm_op07_implemented", "pcm_op08_implemented"}
)

P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS: Final[tuple[str, ...]] = (
    "pcm_op03_dhr_op05_manual_handoff_boundary_design_candidate_present",
    "pcm_op03_retry_start_route_boundary_candidate_present",
    "pcm_op03_wait_external_bodyfree_claim_hold_present",
    "pcm_op03_repair_boundary_candidate_present",
    "pcm_op03_manual_hold_unresolved_stop_present",
    "pcm_op03_blocked_bodyfree_promotion_autorun_stop_present",
)

P7_R54_AHR_POST_PNT_PCM_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_design_target_ref", "boundary_prefix_ref", "boundary_prefix_meaning_ref",
    "expected_from_pnt_op08_ref", "expected_next_required_step_ref",
    "pcm_scope_refrozen", "explicit_pnt_op08_closed_material_required", "pnt_op08_default_builder_call_allowed", "pnt_op08_default_material_synthesis_allowed", "pnt_op08_decision_table_as_single_lane_allowed",
    "selected_post_nci_next_boundary_execution_allowed_here", "selected_pcm_next_boundary_execution_allowed_here",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "repair_execution_allowed_here", "raw_evidence_request_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    "pcm_op00_scope_confirmed", "pcm_op00_explicit_closed_material_boundary_confirmed", "pcm_op00_no_execution_boundary_confirmed", "pcm_op00_no_touch_boundary_confirmed", "pcm_op00_no_promotion_boundary_confirmed",
    "source_mode_local_received_zip_only_confirmed", "github_connection_check_not_required_by_mash_instruction", "github_connection_check_performed",
    "pcm_op00_does_not_intake_pnt_op08_material", "pcm_op00_does_not_synthesize_pnt_op08_material", "pcm_op00_does_not_use_pnt_r11_decision_table_as_current_lane", "pcm_op00_does_not_execute_selected_post_nci_next_boundary", "pcm_op00_does_not_call_dhr_op05", "pcm_op00_does_not_start_p8_question_design", "pcm_op00_does_not_change_api_db_rn_runtime_response_key", "pcm_op00_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", *P7_R54_AHR_POST_PNT_PCM_OP00_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PNT_PCM_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_material_present", "op00_contract_valid", "op00_schema_version", "op00_material_ref", "op00_next_required_step",
    "explicit_pnt_op08_closed_material_required", "pnt_op08_default_builder_call_allowed", "pnt_op08_default_material_synthesis_allowed", "pnt_op08_decision_table_as_single_lane_allowed", "pnt_op08_default_builder_called_here", "pnt_op08_default_material_synthesized_here", "pnt_r11_decision_table_used_as_single_lane_here",
    "pnt_op08_material_present", "pnt_op08_contract_valid", "pnt_op08_schema_version", "pnt_op08_material_ref", "pnt_op08_operation_step_ref", "pnt_op08_status_ref", "bodyfree_post_nci_triage_result_memo_closure_status_ref", "pnt_op08_closed_bodyfree_stopped", "pnt_op08_waiting_for_input_refs", "pnt_op08_repair_required", "pnt_op08_blocked_bodyfree_promotion_autorun",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_pnt_lane_ref_present", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_not_executed", "selected_post_nci_next_boundary_not_executed_present", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed", "selected_handoff_or_stop_not_executed_present",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate",
    "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "pnt_op08_input_forbidden_payload_key_path_refs", "pnt_op08_input_forbidden_payload_key_path_count", "pnt_op08_input_body_like_value_path_refs", "pnt_op08_input_body_like_value_path_count", "pnt_op08_input_promotion_claim_refs", "pnt_op08_input_promotion_claim_ref_count", "pnt_op08_input_no_touch_mutation_path_refs", "pnt_op08_input_no_touch_mutation_path_count",
    "pcm_op01_status_ref", "bodyfree_pnt_op08_closed_material_intake_status_ref", "pcm_op01_allowed_status_refs", "pcm_op01_allowed_status_ref_count",
    "pcm_op01_ready_for_contract_validation", "pcm_op01_waiting_for_explicit_pnt_op08_closed_material", "pcm_op01_waiting_for_pnt_op08_to_close", "pcm_op01_repair_required", "pcm_op01_bodyfree_leak_promotion_or_autorun_blocked", "pcm_op01_reason_refs", "pcm_op01_reason_ref_count", "pcm_op01_blocker_refs", "pcm_op01_blocker_ref_count",
    "pcm_op01_does_not_validate_closed_material_contract", "pcm_op01_does_not_confirm_single_selected_lane", "pcm_op01_does_not_resolve_next_work_class", "pcm_op01_does_not_materialize_next_design_candidate", "pcm_op01_does_not_execute_selected_post_nci_next_boundary", "pcm_op01_does_not_call_dhr_op05", "pcm_op01_does_not_call_dhr_op06", "pcm_op01_does_not_execute_dmd_r52_or_release", "pcm_op01_does_not_start_actual_review", "pcm_op01_does_not_request_raw_evidence", "pcm_op01_does_not_execute_repair", "pcm_op01_does_not_start_p5_p6_p8_p7_or_release", "pcm_op01_does_not_change_api_db_rn_runtime_response_key", "pcm_op01_does_not_materialize_p8_question_spec", "pcm_op01_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", *P7_R54_AHR_POST_PNT_PCM_OP01_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PNT_PCM_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_material_present", "op01_contract_valid", "op01_schema_version", "op01_material_ref", "op01_status_ref", "op01_next_required_step", "op01_ready_for_contract_validation",
    "pnt_op08_status_ref", "pnt_op08_closed_bodyfree_stopped", "pnt_op08_contract_valid",
    "selected_pnt_status_ref", "selected_pnt_status_ref_present", "selected_pnt_status_ref_matches_lane",
    "selected_pnt_lane_ref", "selected_pnt_lane_ref_present", "selected_pnt_lane_ref_allowed",
    "selected_post_nci_outcome_group_ref", "selected_post_nci_outcome_group_ref_present", "selected_post_nci_outcome_group_ref_allowed", "selected_post_nci_outcome_group_ref_matches_lane",
    "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_ref_present", "selected_post_nci_next_boundary_ref_matches_lane",
    "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_kind_ref_present", "selected_post_nci_next_boundary_kind_ref_matches_lane",
    "selected_post_nci_next_boundary_not_executed", "selected_post_nci_next_boundary_not_executed_present",
    "selected_handoff_or_stop_ref", "selected_handoff_or_stop_ref_present", "selected_handoff_or_stop_ref_matches_selected_post_nci_next_boundary_ref", "selected_handoff_or_stop_ref_matches_lane",
    "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_kind_ref_present", "selected_handoff_or_stop_kind_ref_matches_lane",
    "selected_handoff_or_stop_not_executed", "selected_handoff_or_stop_not_executed_present",
    "next_design_document_candidate_ref", "next_design_document_candidate_ref_present", "next_design_document_candidate_ref_matches_lane", "next_design_document_allowed", "next_design_document_allowed_matches_lane",
    "manual_wait_required", "manual_wait_required_matches_lane", "manual_stop_required", "manual_stop_required_matches_lane", "repair_design_candidate", "repair_design_candidate_matches_lane",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "closed_pnt_op08_material_contract_valid", "pcm_op02_status_ref", "bodyfree_closed_pnt_op08_material_contract_validation_status_ref", "pcm_op02_allowed_status_refs", "pcm_op02_allowed_status_ref_count",
    "pcm_op02_contract_valid_stopped", "pcm_op02_repair_required", "pcm_op02_bodyfree_leak_promotion_or_autorun_blocked",
    "pcm_op02_reason_refs", "pcm_op02_reason_ref_count", "pcm_op02_blocker_refs", "pcm_op02_blocker_ref_count",
    "op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count", "op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count", "op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count", "op02_input_no_touch_mutation_path_refs", "op02_input_no_touch_mutation_path_count", "op02_input_multi_lane_material_key_path_refs", "op02_input_multi_lane_material_key_path_count",
    "pcm_op02_does_not_confirm_single_selected_lane", "pcm_op02_does_not_resolve_next_work_class", "pcm_op02_does_not_materialize_next_design_candidate", "pcm_op02_does_not_execute_selected_post_nci_next_boundary", "pcm_op02_does_not_execute_selected_pcm_next_boundary", "pcm_op02_does_not_call_dhr_op05", "pcm_op02_does_not_call_dhr_op06", "pcm_op02_does_not_execute_dmd_r52_or_release", "pcm_op02_does_not_start_actual_review", "pcm_op02_does_not_request_raw_evidence", "pcm_op02_does_not_execute_repair", "pcm_op02_does_not_start_p5_p6_p8_p7_or_release", "pcm_op02_does_not_change_api_db_rn_runtime_response_key", "pcm_op02_does_not_materialize_p8_question_spec", "pcm_op02_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", *P7_R54_AHR_POST_PNT_PCM_OP02_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PNT_PCM_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_material_present", "op02_contract_valid", "op02_schema_version", "op02_material_ref", "op02_status_ref", "op02_next_required_step", "op02_contract_valid_stopped",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_pnt_lane_ref_allowed", "single_selected_pnt_lane_confirmed", "single_selected_pnt_lane_material_present",
    "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_not_executed",
    "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate",
    "selected_pcm_next_work_class_not_resolved_here", "selected_pcm_next_boundary_not_materialized_here", "selected_pcm_next_boundary_execution_allowed_here",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count", "allowed_pnt_outcome_group_refs", "allowed_pnt_outcome_group_ref_count", "pcm_op03_lane_flag_refs", "pcm_op03_lane_flag_ref_count",
    *P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS,
    "single_lane_flag_count", "decision_table_material_rejected", "multi_lane_material_rejected", "multi_lane_material_key_path_refs", "multi_lane_material_key_path_count", "ambiguous_lane_flag_refs", "ambiguous_lane_flag_ref_count",
    "pcm_op03_status_ref", "bodyfree_single_selected_lane_confirmation_status_ref", "pcm_op03_allowed_status_refs", "pcm_op03_allowed_status_ref_count",
    "pcm_op03_single_selected_lane_confirmed_stopped", "pcm_op03_waiting_for_single_selected_lane_material", "pcm_op03_repair_required_for_multi_or_ambiguous_lane", "pcm_op03_bodyfree_leak_promotion_or_autorun_blocked",
    "pcm_op03_reason_refs", "pcm_op03_reason_ref_count", "pcm_op03_blocker_refs", "pcm_op03_blocker_ref_count",
    "op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count", "op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count", "op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count", "op03_input_no_touch_mutation_path_refs", "op03_input_no_touch_mutation_path_count",
    "pcm_op03_does_not_resolve_next_work_class", "pcm_op03_does_not_materialize_next_design_candidate", "pcm_op03_does_not_execute_selected_post_nci_next_boundary", "pcm_op03_does_not_execute_selected_pcm_next_boundary", "pcm_op03_does_not_call_dhr_op05", "pcm_op03_does_not_call_dhr_op06", "pcm_op03_does_not_execute_dmd_r52_or_release", "pcm_op03_does_not_start_actual_review", "pcm_op03_does_not_request_raw_evidence", "pcm_op03_does_not_execute_repair", "pcm_op03_does_not_start_p5_p6_p8_p7_or_release", "pcm_op03_does_not_change_api_db_rn_runtime_response_key", "pcm_op03_does_not_materialize_p8_question_spec", "pcm_op03_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", *P7_R54_AHR_POST_PNT_PCM_OP03_REQUIRED_FALSE_FLAG_REFS, "body_free",
)



P7_R54_AHR_POST_PNT_PCM_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_material_present", "op03_contract_valid", "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_next_required_step", "op03_single_selected_lane_confirmed_stopped",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_pnt_lane_ref_allowed", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_not_executed", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_pcm_next_work_class_ref", "selected_pcm_next_work_class_ref_allowed", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_not_executed", "selected_pcm_next_boundary_execution_allowed_here", "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate", "execution_allowed_here",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    "allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count", "allowed_next_work_class_refs", "allowed_next_work_class_ref_count", "lane_to_next_work_class_refs", "lane_to_selected_pcm_next_boundary_refs", "lane_to_selected_pcm_next_boundary_kind_refs", "lane_to_next_design_document_candidate_refs",
    "pcm_op04_status_ref", "bodyfree_next_work_class_resolver_status_ref", "pcm_op04_allowed_status_refs", "pcm_op04_allowed_status_ref_count", "pcm_op04_next_work_class_resolved_stopped", "pcm_op04_repair_required_for_next_work_class_inputs", "pcm_op04_bodyfree_leak_promotion_or_autorun_blocked", "pcm_op04_reason_refs", "pcm_op04_reason_ref_count", "pcm_op04_blocker_refs", "pcm_op04_blocker_ref_count",
    "op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count", "op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count", "op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count", "op04_input_no_touch_mutation_path_refs", "op04_input_no_touch_mutation_path_count",
    "pcm_op04_does_not_materialize_next_design_candidate_envelope", "pcm_op04_does_not_execute_selected_post_nci_next_boundary", "pcm_op04_does_not_execute_selected_pcm_next_boundary", "pcm_op04_does_not_call_dhr_op05", "pcm_op04_does_not_call_dhr_op06", "pcm_op04_does_not_execute_dmd_r52_or_release", "pcm_op04_does_not_start_actual_review", "pcm_op04_does_not_request_raw_evidence", "pcm_op04_does_not_execute_repair", "pcm_op04_does_not_start_p5_p6_p8_p7_or_release", "pcm_op04_does_not_change_api_db_rn_runtime_response_key", "pcm_op04_does_not_materialize_p8_question_spec", "pcm_op04_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", *P7_R54_AHR_POST_PNT_PCM_OP04_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PNT_PCM_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_material_present", "op04_contract_valid", "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_next_required_step", "op04_next_work_class_resolved_stopped",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_not_executed", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_pcm_next_work_class_ref", "selected_pcm_next_work_class_ref_allowed", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_not_executed", "selected_pcm_next_boundary_execution_allowed_here", "selected_pcm_next_boundary_envelope_materialized_here", "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate", "execution_allowed_here",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    "pcm_op05_dhr_op05_design_candidate_envelope_materialized_without_call", "pcm_op05_retry_start_design_candidate_envelope_materialized_without_actual_review", "pcm_op05_repair_design_candidate_envelope_materialized_without_repair_execution", "pcm_op05_wait_hold_envelope_materialized_without_raw_evidence", "pcm_op05_stop_envelope_materialized_without_next_design_promotion",
    "pcm_op05_status_ref", "bodyfree_next_design_candidate_envelope_status_ref", "pcm_op05_allowed_status_refs", "pcm_op05_allowed_status_ref_count", "pcm_op05_next_design_candidate_envelope_materialized_stopped", "pcm_op05_wait_hold_envelope_materialized_stopped", "pcm_op05_stop_envelope_materialized_stopped", "pcm_op05_repair_required_for_next_work_class_inputs", "pcm_op05_bodyfree_leak_promotion_or_autorun_blocked", "pcm_op05_reason_refs", "pcm_op05_reason_ref_count", "pcm_op05_blocker_refs", "pcm_op05_blocker_ref_count",
    "op05_input_forbidden_payload_key_path_refs", "op05_input_forbidden_payload_key_path_count", "op05_input_body_like_value_path_refs", "op05_input_body_like_value_path_count", "op05_input_promotion_claim_refs", "op05_input_promotion_claim_ref_count", "op05_input_no_touch_mutation_path_refs", "op05_input_no_touch_mutation_path_count",
    "pcm_op05_does_not_execute_selected_post_nci_next_boundary", "pcm_op05_does_not_execute_selected_pcm_next_boundary", "pcm_op05_does_not_call_dhr_op05", "pcm_op05_does_not_call_dhr_op06", "pcm_op05_does_not_execute_dmd_r52_or_release", "pcm_op05_does_not_start_actual_review", "pcm_op05_does_not_request_raw_evidence", "pcm_op05_does_not_execute_repair", "pcm_op05_does_not_start_p5_p6_p8_p7_or_release", "pcm_op05_does_not_change_api_db_rn_runtime_response_key", "pcm_op05_does_not_materialize_p8_question_spec", "pcm_op05_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", *P7_R54_AHR_POST_PNT_PCM_OP05_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_PNT_PCM_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_material_present", "op05_contract_valid", "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_next_required_step", "op05_envelope_materialized_stopped",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_not_executed", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_pcm_next_work_class_ref", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_not_executed", "selected_pcm_next_boundary_execution_allowed_here", "selected_pcm_next_boundary_envelope_materialized_here", "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate", "execution_allowed_here",
    "guard_subject_step_refs", "guard_subject_step_ref_count", "guard_scope_ref",
    "validation_commands_executed_here", "pytest_executed_here", "pcm_target_tests_executed_here", "selected_regression_executed_here", "compileall_executed_here", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    "pcm_op06_status_ref", "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref", "pcm_op06_allowed_status_refs", "pcm_op06_allowed_status_ref_count", "pcm_op06_guard_passed", "pcm_op06_repair_required_for_guard_inputs", "pcm_op06_bodyfree_leak_promotion_or_autorun_blocked", "pcm_op06_reason_refs", "pcm_op06_reason_ref_count", "pcm_op06_blocker_refs", "pcm_op06_blocker_ref_count",
    "op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count", "op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count", "op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count", "op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count",
    "pcm_op06_does_not_execute_validation_commands", "pcm_op06_does_not_claim_full_backend_rn_or_real_device_green", "pcm_op06_does_not_execute_selected_post_nci_next_boundary", "pcm_op06_does_not_execute_selected_pcm_next_boundary", "pcm_op06_does_not_call_dhr_op05", "pcm_op06_does_not_call_dhr_op06", "pcm_op06_does_not_execute_dmd_r52_or_release", "pcm_op06_does_not_start_actual_review", "pcm_op06_does_not_request_raw_evidence", "pcm_op06_does_not_execute_repair", "pcm_op06_does_not_start_p5_p6_p8_p7_or_release", "pcm_op06_does_not_change_api_db_rn_runtime_response_key", "pcm_op06_does_not_materialize_p8_question_spec", "pcm_op06_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented", *P7_R54_AHR_POST_PNT_PCM_OP06_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PNT_PCM_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_material_present", "op06_contract_valid", "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_next_required_step", "op06_guard_passed",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_not_executed", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_pcm_next_work_class_ref", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_not_executed", "selected_pcm_next_boundary_execution_allowed_here", "selected_pcm_next_boundary_envelope_materialized_here", "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate", "execution_allowed_here",
    "validation_plan_ref", "validation_plan_recorded", "validation_plan_bodyfree", "validation_plan_execution_allowed_here", "validation_commands_executed_here", "pytest_executed_here", "pcm_target_tests_executed_here", "selected_regression_executed_here", "compileall_executed_here",
    "target_test_ref_refs", "target_test_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_count", "compileall_target_ref_refs", "compileall_target_ref_count", "validation_command_summary_refs", "validation_command_summary_ref_count", "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref",
    "post_pnt_closed_material_confirmation_result_memo_draft_ref", "post_pnt_closed_material_confirmation_result_memo_draft_bodyfree", "post_pnt_closed_material_confirmation_result_memo_draft_materialized_here", "post_pnt_closed_material_confirmation_result_memo_draft_execution_allowed_here", "pcm_op07_ready_for_op08",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    "pcm_op07_status_ref", "bodyfree_validation_plan_result_memo_draft_status_ref", "pcm_op07_allowed_status_refs", "pcm_op07_allowed_status_ref_count", "pcm_op07_result_memo_draft_materialized_stopped", "pcm_op07_wait_or_stop_result_memo_draft_materialized_stopped", "pcm_op07_repair_required_for_result_memo_draft_inputs", "pcm_op07_bodyfree_leak_promotion_or_autorun_blocked", "pcm_op07_reason_refs", "pcm_op07_reason_ref_count", "pcm_op07_blocker_refs", "pcm_op07_blocker_ref_count",
    "op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count", "op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count", "op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count", "op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count",
    "pcm_op07_does_not_close_result_memo_as_op08", "pcm_op07_does_not_execute_validation_commands", "pcm_op07_does_not_claim_full_backend_rn_or_real_device_green", "pcm_op07_does_not_execute_selected_post_nci_next_boundary", "pcm_op07_does_not_execute_selected_pcm_next_boundary", "pcm_op07_does_not_call_dhr_op05", "pcm_op07_does_not_call_dhr_op06", "pcm_op07_does_not_execute_dmd_r52_or_release", "pcm_op07_does_not_start_actual_review", "pcm_op07_does_not_request_raw_evidence", "pcm_op07_does_not_execute_repair", "pcm_op07_does_not_start_p5_p6_p8_p7_or_release", "pcm_op07_does_not_change_api_db_rn_runtime_response_key", "pcm_op07_does_not_materialize_p8_question_spec", "pcm_op07_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented", "pcm_op07_implemented", *P7_R54_AHR_POST_PNT_PCM_OP07_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_material_present", "op07_contract_valid", "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_next_required_step", "op07_ready_for_op08",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref", "selected_post_nci_next_boundary_not_executed", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_pcm_next_work_class_ref", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_not_executed", "selected_pcm_next_boundary_execution_allowed_here", "selected_pcm_next_boundary_envelope_materialized_here",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate", "execution_allowed_here",
    "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref", "validation_result_status_refs_recorded",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "pnt_op08_builder_not_called", "pnt_op08_material_not_synthesized", "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    "post_pnt_closed_material_confirmation_result_memo_closure_ref", "post_pnt_closed_material_confirmation_result_memo_closure_bodyfree", "post_pnt_closed_material_confirmation_result_memo_closed_here", "post_pnt_closed_material_confirmation_result_memo_execution_allowed_here",
    "pcm_op08_status_ref", "bodyfree_post_pnt_closed_material_confirmation_closure_status_ref", "pcm_op08_allowed_status_refs", "pcm_op08_allowed_status_ref_count", "pcm_op08_closed_stopped", "pcm_op08_waiting_for_explicit_pnt_op08_closed_material", "pcm_op08_repair_required_for_post_pnt_confirmation_inputs", "pcm_op08_bodyfree_leak_promotion_or_autorun_blocked", "pcm_op08_reason_refs", "pcm_op08_reason_ref_count", "pcm_op08_blocker_refs", "pcm_op08_blocker_ref_count",
    "op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count", "op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count", "op08_input_promotion_claim_refs", "op08_input_promotion_claim_ref_count", "op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count",
    "pcm_op08_records_next_design_candidate_hold_or_stop_only", "pcm_op08_does_not_execute_selected_post_nci_next_boundary", "pcm_op08_does_not_execute_selected_pcm_next_boundary", "pcm_op08_does_not_call_dhr_op05", "pcm_op08_does_not_call_dhr_op06", "pcm_op08_does_not_execute_dmd_r52_or_release", "pcm_op08_does_not_start_actual_review", "pcm_op08_does_not_request_raw_evidence", "pcm_op08_does_not_execute_repair", "pcm_op08_does_not_start_p5_p6_p8_p7_or_release", "pcm_op08_does_not_change_api_db_rn_runtime_response_key", "pcm_op08_does_not_materialize_p8_question_spec", "pcm_op08_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pcm_no_touch_contract", "body_free_markers", "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented", "pcm_op07_implemented", "pcm_op08_implemented", *P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FALSE_FLAG_REFS, "body_free",
)



def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_PNT_PCM_DEFAULT_REVIEW_SESSION_ID,
        max_length=180,
    )


def _clean_ref(value: Any, *, default: str = "missing", max_length: int = 240) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _dedupe_clean_refs(values: Sequence[Any], *, max_length: int = 240) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _clean_ref(value, default="", max_length=max_length)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PNT_PCM_NO_TOUCH_CONTRACT_KEYS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PNT_PCM_BODY_FREE_MARKER_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS}


def _false_flags(
    false_flag_refs: Sequence[str] = P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS,
) -> dict[str, bool]:
    return {key: False for key in false_flag_refs}


def _required_fields_present(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:8]}")


def _scan_forbidden_payload_key_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PNT_PCM_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_body_like_value_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    suspect_tokens = (
        "raw_input", "input_body", "comment_text", "comment_text_body",
        "body_full_packet", "reviewer_free_text", "question_text",
        "draft_question_text", "answer_text", "absolute_path", "relative_path",
        "file_path", "local_path", "hash", "sha256", "terminal_output",
        "stdout", "stderr", "traceback",
    )
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PNT_PCM_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            elif isinstance(child, str) and child.strip() and any(token in key_lower for token in suspect_tokens):
                paths.append(child_path)
            elif (
                child is True
                and any(token in key_lower for token in suspect_tokens)
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
            if key_text in P7_R54_AHR_POST_PNT_PCM_PROMOTION_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_promotion_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_promotion_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _scan_no_touch_mutation_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PNT_PCM_NO_TOUCH_CONTRACT_KEYS and child is True:
                paths.append(child_path)
            paths.extend(_scan_no_touch_mutation_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_no_touch_mutation_paths(child, path=f"{path}[{index}]"))
    return paths


def _bodyfree_no_touch_scan_quads(value: Any, *, path: str) -> tuple[list[str], list[str], list[str], list[str]]:
    return (
        _dedupe_clean_refs(_scan_forbidden_payload_key_paths(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_body_like_value_paths(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_promotion_claim_refs(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_no_touch_mutation_paths(value, path=path), max_length=340),
    )


def _filter_allowed_prior_implemented_flag_paths(
    paths: Sequence[str],
    *,
    allowed_implemented_keys: Sequence[str],
) -> list[str]:
    allowed = set(allowed_implemented_keys)
    return [path for path in paths if path.rsplit(".", 1)[-1] not in allowed]


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    operation_step_ref: str,
    source: str,
    required_false_flag_refs: Sequence[str] = P7_R54_AHR_POST_PNT_PCM_REQUIRED_FALSE_FLAG_REFS,
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version mismatch")
    if data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step mismatch")
    if data.get("phase") != P7_R54_AHR_POST_PNT_PCM_PHASE:
        raise ValueError(f"{source} phase mismatch")
    if data.get("scope") != P7_R54_AHR_POST_PNT_PCM_SCOPE:
        raise ValueError(f"{source} scope mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE:
        raise ValueError(f"{source} source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require/check GitHub")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError(f"{source} public contract changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if tuple((data.get("pcm_no_touch_contract") or {}).keys()) != tuple(P7_R54_AHR_POST_PNT_PCM_NO_TOUCH_CONTRACT_KEYS):
        raise ValueError(f"{source} no-touch contract keys changed")
    if any(value is not False for value in (data.get("pcm_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract must stay false")
    if tuple((data.get("body_free_markers") or {}).keys()) != tuple(P7_R54_AHR_POST_PNT_PCM_BODY_FREE_MARKER_REFS):
        raise ValueError(f"{source} body-free marker keys changed")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free markers must stay false")
    if any(key in P7_R54_AHR_POST_PNT_PCM_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")
    for key in required_false_flag_refs:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")


def _op00_contract_valid(op00: Mapping[str, Any] | None) -> bool:
    if not isinstance(op00, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08_contract(op00) is True
    except ValueError:
        return False


def _pnt_op08_contract_valid(op08: Mapping[str, Any] | None) -> bool:
    if not isinstance(op08, Mapping):
        return False
    try:
        return pnt.assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(op08) is True
    except ValueError:
        return False


def _closed_pnt_op08_not_called_blockers(op08: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    for key in (
        "dhr_op05_not_called",
        "dhr_op06_not_called",
        "dmd_r52_not_executed",
        "p5_p6_p8_p7_release_not_started",
        "p8_question_design_not_started",
        "p8_question_implementation_not_started",
        "api_db_rn_runtime_response_key_not_changed",
    ):
        if key in op08 and op08.get(key) is not True:
            blockers.append(f"pnt_op08_{key}_not_true")
    for key in (
        "selected_post_nci_next_boundary_not_executed",
        "selected_handoff_or_stop_not_executed",
    ):
        if key in op08 and op08.get(key) is not True:
            blockers.append(f"pnt_op08_{key}_not_true")
    return blockers


def _op01_status_reason_blocker_next(
    *,
    op00_valid: bool,
    pnt_op08_present: bool,
    pnt_op08_contract_valid: bool,
    pnt_op08_status_ref: str,
    pnt_op08_closed: bool,
    pnt_op08_waiting: bool,
    pnt_op08_repair: bool,
    pnt_op08_blocked: bool,
    selected_pnt_lane_ref: str,
    selected_post_nci_next_boundary_not_executed_present: bool,
    selected_handoff_or_stop_not_executed_present: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    explicit_boundary_blockers: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("pnt_op08_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("pnt_op08_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("pnt_op08_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("pnt_op08_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    blockers.extend(explicit_boundary_blockers)
    if pnt_op08_blocked or pnt_op08_status_ref == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF:
        blockers.append("pnt_op08_status_bodyfree_leak_promotion_or_autorun_blocked")
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
            ["pnt_op08_closed_material_failed_bodyfree_no_promotion_boundary_before_pcm_op02"],
            _dedupe_clean_refs(blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_PNT_OP08_CLOSED_MATERIAL_REF,
        )
    if not op00_valid:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF,
            ["pcm_op00_contract_invalid_before_pnt_op08_closed_material_intake"],
            ["pcm_op00_contract_invalid"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF,
        )
    if not pnt_op08_present:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF,
            ["explicit_pnt_op08_bodyfree_result_memo_closure_material_not_provided_yet"],
            ["explicit_pnt_op08_closed_material_missing"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF,
        )
    if pnt_op08_waiting or pnt_op08_status_ref == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_PNT_OP08_TO_CLOSE_REF,
            ["pnt_op08_result_memo_closure_waiting_before_post_pnt_confirmation"],
            ["pnt_op08_waiting_for_input_refs"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_PNT_OP08_CLOSURE_REF,
        )
    if pnt_op08_repair or pnt_op08_status_ref == pnt.P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF,
            ["pnt_op08_result_memo_closure_repair_required_before_pcm_op02"],
            ["pnt_op08_repair_required_for_closure_inputs"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF,
        )
    if not pnt_op08_contract_valid:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF,
            ["pnt_op08_result_memo_closure_contract_repair_required_before_pcm_op02"],
            ["pnt_op08_result_memo_closure_contract_invalid"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF,
        )
    if not selected_post_nci_next_boundary_not_executed_present:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF,
            ["pnt_op08_selected_post_nci_next_boundary_non_execution_presence_missing_before_pcm_op02"],
            ["selected_post_nci_next_boundary_not_executed_missing"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF,
        )
    if not selected_handoff_or_stop_not_executed_present:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF,
            ["pnt_op08_selected_handoff_or_stop_non_execution_presence_missing_before_pcm_op02"],
            ["selected_handoff_or_stop_not_executed_missing"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF,
        )
    if pnt_op08_closed and selected_pnt_lane_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_READY_FOR_OP02_REF,
            ["pnt_op08_closed_bodyfree_single_material_ready_for_pcm_op02_contract_validation"],
            [],
            P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF,
        ["pnt_op08_closed_material_incomplete_before_pcm_op02_contract_validation"],
        ["pnt_op08_closed_status_or_selected_pnt_lane_missing"],
        P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF,
    )



def _op01_contract_valid(op01: Mapping[str, Any] | None) -> bool:
    if not isinstance(op01, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract(op01) is True
    except ValueError:
        return False


def _op02_contract_valid(op02: Mapping[str, Any] | None) -> bool:
    if not isinstance(op02, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_contract(op02) is True
    except ValueError:
        return False



def _op03_contract_valid(op03: Mapping[str, Any] | None) -> bool:
    if not isinstance(op03, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract(op03) is True
    except ValueError:
        return False


def _scan_multi_lane_material_key_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PNT_PCM_DECISION_TABLE_OR_MULTI_LANE_MATERIAL_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_multi_lane_material_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_multi_lane_material_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _pcm_op03_lane_flags(selected_lane_ref: str) -> dict[str, bool]:
    return {
        "pcm_op03_dhr_op05_manual_handoff_boundary_design_candidate_present": selected_lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF,
        "pcm_op03_retry_start_route_boundary_candidate_present": selected_lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF,
        "pcm_op03_wait_external_bodyfree_claim_hold_present": selected_lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REINTAKE_CANDIDATE_REF,
        "pcm_op03_repair_boundary_candidate_present": selected_lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF,
        "pcm_op03_manual_hold_unresolved_stop_present": selected_lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_MANUAL_HOLD_UNRESOLVED_POST_RDB08_CANDIDATE_REF,
        "pcm_op03_blocked_bodyfree_promotion_autorun_stop_present": selected_lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_CANDIDATE_REF,
    }


def _input_true_lane_flag_refs(value: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    candidate_refs = tuple(
        dict.fromkeys(
            P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS
            + getattr(pnt, "P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS", ())
        )
    )
    return [key for key in candidate_refs if value.get(key) is True]


def _op02_status_reason_blocker_next(
    *,
    op01_present: bool,
    op01_valid: bool,
    op01_ready: bool,
    pnt_op08_closed: bool,
    pnt_op08_contract_valid: bool,
    lane_present: bool,
    lane_allowed: bool,
    status_present: bool,
    status_matches_lane: bool,
    outcome_present: bool,
    outcome_allowed: bool,
    outcome_matches_lane: bool,
    boundary_present: bool,
    boundary_matches_lane: bool,
    boundary_kind_present: bool,
    boundary_kind_matches_lane: bool,
    boundary_not_executed_present: bool,
    boundary_not_executed: bool,
    handoff_ref_present: bool,
    handoff_ref_matches_boundary: bool,
    handoff_ref_matches_lane: bool,
    handoff_kind_present: bool,
    handoff_kind_matches_lane: bool,
    handoff_not_executed_present: bool,
    handoff_not_executed: bool,
    next_design_present: bool,
    next_design_matches_lane: bool,
    next_design_allowed_matches_lane: bool,
    manual_wait_matches_lane: bool,
    manual_stop_matches_lane: bool,
    repair_design_matches_lane: bool,
    dhr_op05_not_called: bool,
    dhr_op06_not_called: bool,
    dmd_r52_not_executed: bool,
    p5_p6_p8_p7_release_not_started: bool,
    p8_question_design_not_started: bool,
    p8_question_implementation_not_started: bool,
    api_db_rn_runtime_response_key_not_changed: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    multi_lane_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op02_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op02_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("op02_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op02_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if boundary_not_executed_present and boundary_not_executed is not True:
        blockers.append("selected_post_nci_next_boundary_not_executed_false")
    if handoff_not_executed_present and handoff_not_executed is not True:
        blockers.append("selected_handoff_or_stop_not_executed_false")
    for flag_name, flag_value in (
        ("dhr_op05_not_called_not_true", dhr_op05_not_called),
        ("dhr_op06_not_called_not_true", dhr_op06_not_called),
        ("dmd_r52_not_executed_not_true", dmd_r52_not_executed),
        ("p5_p6_p8_p7_release_not_started_not_true", p5_p6_p8_p7_release_not_started),
        ("p8_question_design_not_started_not_true", p8_question_design_not_started),
        ("p8_question_implementation_not_started_not_true", p8_question_implementation_not_started),
        ("api_db_rn_runtime_response_key_not_changed_not_true", api_db_rn_runtime_response_key_not_changed),
    ):
        if flag_value is not True:
            blockers.append(flag_name)
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_BLOCKED_LEAK_PROMOTION_OR_AUTORUN_REF,
            ["closed_pnt_op08_material_contract_blocked_before_single_lane_confirmation"],
            _dedupe_clean_refs(blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF,
        )

    repair_blockers: list[str] = []
    if multi_lane_paths:
        repair_blockers.append("decision_table_or_multi_lane_material_present_before_contract_validation")
    if not op01_present:
        repair_blockers.append("pcm_op01_material_missing")
    if op01_present and not op01_valid:
        repair_blockers.append("pcm_op01_contract_invalid")
    if op01_valid and not op01_ready:
        repair_blockers.append("pcm_op01_not_ready_for_closed_pnt_op08_material_contract_validation")
    if op01_valid and not pnt_op08_contract_valid:
        repair_blockers.append("pnt_op08_contract_invalid_before_pcm_op02")
    if op01_valid and not pnt_op08_closed:
        repair_blockers.append("pnt_op08_not_closed_bodyfree_stopped_before_pcm_op02")
    if not status_present:
        repair_blockers.append("selected_pnt_status_ref_missing")
    if lane_present is not True:
        repair_blockers.append("selected_pnt_lane_ref_missing")
    elif not lane_allowed:
        repair_blockers.append("selected_pnt_lane_ref_unknown_or_not_allowed")
    if lane_allowed and status_present and not status_matches_lane:
        repair_blockers.append("selected_pnt_status_ref_does_not_match_selected_pnt_lane_ref")
    if not outcome_present:
        repair_blockers.append("selected_post_nci_outcome_group_ref_missing")
    elif not outcome_allowed:
        repair_blockers.append("selected_post_nci_outcome_group_ref_unknown_or_not_allowed")
    if lane_allowed and outcome_allowed and not outcome_matches_lane:
        repair_blockers.append("selected_post_nci_outcome_group_ref_does_not_match_lane")
    if not boundary_present:
        repair_blockers.append("selected_post_nci_next_boundary_ref_missing")
    elif lane_allowed and not boundary_matches_lane:
        repair_blockers.append("selected_post_nci_next_boundary_ref_does_not_match_lane")
    if not boundary_kind_present:
        repair_blockers.append("selected_post_nci_next_boundary_kind_ref_missing")
    elif lane_allowed and not boundary_kind_matches_lane:
        repair_blockers.append("selected_post_nci_next_boundary_kind_ref_does_not_match_lane")
    if not boundary_not_executed_present:
        repair_blockers.append("selected_post_nci_next_boundary_not_executed_missing")
    if not handoff_ref_present:
        repair_blockers.append("selected_handoff_or_stop_ref_missing")
    elif not handoff_ref_matches_boundary:
        repair_blockers.append("selected_handoff_or_stop_ref_and_selected_post_nci_next_boundary_ref_mismatch")
    elif lane_allowed and not handoff_ref_matches_lane:
        repair_blockers.append("selected_handoff_or_stop_ref_does_not_match_lane")
    if not handoff_kind_present:
        repair_blockers.append("selected_handoff_or_stop_kind_ref_missing")
    elif lane_allowed and not handoff_kind_matches_lane:
        repair_blockers.append("selected_handoff_or_stop_kind_ref_does_not_match_lane")
    if not handoff_not_executed_present:
        repair_blockers.append("selected_handoff_or_stop_not_executed_missing")
    if not next_design_present:
        repair_blockers.append("next_design_document_candidate_ref_missing")
    elif lane_allowed and not next_design_matches_lane:
        repair_blockers.append("next_design_document_candidate_ref_does_not_match_lane")
    if lane_allowed and not next_design_allowed_matches_lane:
        repair_blockers.append("next_design_document_allowed_does_not_match_lane")
    if lane_allowed and not manual_wait_matches_lane:
        repair_blockers.append("manual_wait_required_does_not_match_lane")
    if lane_allowed and not manual_stop_matches_lane:
        repair_blockers.append("manual_stop_required_does_not_match_lane")
    if lane_allowed and not repair_design_matches_lane:
        repair_blockers.append("repair_design_candidate_does_not_match_lane")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_REPAIR_REQUIRED_FOR_CONTRACT_REF,
            ["closed_pnt_op08_material_contract_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF,
        )
    return (
        P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_CONTRACT_VALID_STOPPED_REF,
        ["closed_pnt_op08_material_contract_valid_ready_for_single_lane_confirmation"],
        [],
        P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
    )


def _op03_status_reason_blocker_next(
    *,
    op02_present: bool,
    op02_valid: bool,
    op02_contract_valid_stopped: bool,
    op02_status_ref: str,
    lane_ref: str,
    lane_allowed: bool,
    multi_lane_paths: Sequence[str],
    ambiguous_lane_flags: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, bool, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op03_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op03_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("op03_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op03_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op02_status_ref == P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_BLOCKED_LEAK_PROMOTION_OR_AUTORUN_REF:
        blockers.append("pcm_op02_blocked_before_single_lane_confirmation")
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_BLOCKED_PROMOTION_OR_AUTORUN_REF,
            False,
            ["single_selected_lane_confirmation_blocked_before_next_work_class_resolution"],
            _dedupe_clean_refs(blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_SINGLE_LANE_CONFIRMATION_REF,
        )
    if not op02_present:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_WAITING_FOR_SINGLE_SELECTED_LANE_MATERIAL_REF,
            False,
            ["pcm_op02_closed_material_contract_validation_material_not_provided_yet"],
            ["pcm_op02_material_missing"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_SINGLE_SELECTED_PNT_LANE_MATERIAL_REF,
        )

    repair_blockers: list[str] = []
    if not op02_valid:
        repair_blockers.append("pcm_op02_contract_invalid")
    if op02_valid and not op02_contract_valid_stopped:
        repair_blockers.append("pcm_op02_not_contract_valid_stopped_for_single_lane_confirmation")
    if multi_lane_paths:
        repair_blockers.append("decision_table_or_multi_lane_material_present")
    if len(ambiguous_lane_flags) > 1:
        repair_blockers.append("multiple_selected_lane_flags_true")
    if lane_ref in ("", "missing"):
        repair_blockers.append("selected_pnt_lane_ref_missing")
    elif not lane_allowed:
        repair_blockers.append("selected_pnt_lane_ref_unknown_or_not_allowed")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_LANE_REF,
            False,
            ["single_selected_lane_confirmation_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_MULTI_OR_AMBIGUOUS_PNT_LANE_MATERIAL_REF,
        )
    return (
        P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_SINGLE_SELECTED_LANE_CONFIRMED_STOPPED_REF,
        True,
        ["single_selected_pnt_lane_confirmed_stopped_without_next_work_class_resolution"],
        [],
        P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
    )

def build_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build PCM-OP00 scope / explicit closed material / no-execution refreeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_PNT_PCM_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_PNT_PCM_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_PNT_PCM_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_PNT_PCM_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_pnt_op08_ref": P7_R54_AHR_POST_PNT_PCM_EXPECTED_FROM_PNT_OP08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
        "pcm_scope_refrozen": True,
        "explicit_pnt_op08_closed_material_required": True,
        "pnt_op08_default_builder_call_allowed": False,
        "pnt_op08_default_material_synthesis_allowed": False,
        "pnt_op08_decision_table_as_single_lane_allowed": False,
        "selected_post_nci_next_boundary_execution_allowed_here": False,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "repair_execution_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "pcm_op00_scope_confirmed": True,
        "pcm_op00_explicit_closed_material_boundary_confirmed": True,
        "pcm_op00_no_execution_boundary_confirmed": True,
        "pcm_op00_no_touch_boundary_confirmed": True,
        "pcm_op00_no_promotion_boundary_confirmed": True,
        "source_mode_local_received_zip_only_confirmed": True,
        "github_connection_check_not_required_by_mash_instruction": True,
        "github_connection_check_performed": False,
        "pcm_op00_does_not_intake_pnt_op08_material": True,
        "pcm_op00_does_not_synthesize_pnt_op08_material": True,
        "pcm_op00_does_not_use_pnt_r11_decision_table_as_current_lane": True,
        "pcm_op00_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op00_does_not_call_dhr_op05": True,
        "pcm_op00_does_not_start_p8_question_design": True,
        "pcm_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op00_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP00_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP00 scope / explicit closed material / no-execution refreeze contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP00_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP00")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP00_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP00",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP00_REQUIRED_FALSE_FLAG_REFS,
    )
    if data.get("pcm_op00_implemented") is not True:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 implemented flag must be true after R2 OP00")
    for key in (
        "pcm_scope_refrozen",
        "explicit_pnt_op08_closed_material_required",
        "pcm_op00_scope_confirmed",
        "pcm_op00_explicit_closed_material_boundary_confirmed",
        "pcm_op00_no_execution_boundary_confirmed",
        "pcm_op00_no_touch_boundary_confirmed",
        "pcm_op00_no_promotion_boundary_confirmed",
        "source_mode_local_received_zip_only_confirmed",
        "github_connection_check_not_required_by_mash_instruction",
        "pcm_op00_does_not_intake_pnt_op08_material",
        "pcm_op00_does_not_synthesize_pnt_op08_material",
        "pcm_op00_does_not_use_pnt_r11_decision_table_as_current_lane",
        "pcm_op00_does_not_execute_selected_post_nci_next_boundary",
        "pcm_op00_does_not_call_dhr_op05",
        "pcm_op00_does_not_start_p8_question_design",
        "pcm_op00_does_not_change_api_db_rn_runtime_response_key",
        "pcm_op00_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP00 required true boundary changed: {key}")
    for key in (
        "pnt_op08_default_builder_call_allowed",
        "pnt_op08_default_material_synthesis_allowed",
        "pnt_op08_decision_table_as_single_lane_allowed",
        "selected_post_nci_next_boundary_execution_allowed_here",
        "selected_pcm_next_boundary_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "repair_execution_allowed_here",
        "raw_evidence_request_allowed_here",
        "p8_question_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "github_connection_check_performed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP00 forbidden execution/claim changed: {key}")
    for field, count_field in (
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP00 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP00 next step must be PCM-OP01")
    return True


def build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake(
    pnt_op08_bodyfree_result_memo_closure_material: Mapping[str, Any] | None = None,
    *,
    pnt_op08_bodyfree_result_memo_closure: Mapping[str, Any] | None = None,
    bodyfree_post_nci_triage_result_memo_closure: Mapping[str, Any] | None = None,
    pnt_op08_bodyfree_post_nci_triage_result_memo_closure: Mapping[str, Any] | None = None,
    pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08: Mapping[str, Any] | None = None,
    scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Intake one explicit closed PNT-OP08 material without synthesizing PNT material."""

    op00_input = (
        pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08
        or scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08
    )
    op00 = dict(op00_input) if isinstance(op00_input, Mapping) else build_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08(review_session_id=review_session_id)
    op00_present = isinstance(op00, Mapping)
    op00_valid = _op00_contract_valid(op00)

    pnt_op08_input = (
        pnt_op08_bodyfree_result_memo_closure_material
        or pnt_op08_bodyfree_result_memo_closure
        or pnt_op08_bodyfree_post_nci_triage_result_memo_closure
        or bodyfree_post_nci_triage_result_memo_closure
    )
    pnt_op08_present = isinstance(pnt_op08_input, Mapping)
    pnt_op08 = dict(pnt_op08_input) if pnt_op08_present else {}
    pnt_op08_contract_valid = _pnt_op08_contract_valid(pnt_op08) if pnt_op08_present else False
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(
        pnt_op08,
        path="pnt_op08_bodyfree_result_memo_closure_material",
    )

    pnt_op08_status_ref = _clean_ref(pnt_op08.get("pnt_op08_status_ref"), default="pnt_op08_status_missing", max_length=360)
    pnt_op08_closed = bool(
        pnt_op08.get("pnt_op08_closed_bodyfree_stopped") is True
        or pnt_op08.get("pnt_op08_bodyfree_post_nci_triage_closed_stopped") is True
    )
    pnt_op08_waiting = bool(pnt_op08.get("pnt_op08_waiting_for_input_refs") is True)
    pnt_op08_repair = bool(pnt_op08.get("pnt_op08_repair_required") is True)
    pnt_op08_blocked = bool(pnt_op08.get("pnt_op08_bodyfree_leak_promotion_or_autorun_blocked") is True)
    selected_pnt_lane_ref = _clean_ref(pnt_op08.get("selected_pnt_lane_ref"), default="", max_length=360)
    selected_post_nci_next_boundary_not_executed_present = "selected_post_nci_next_boundary_not_executed" in pnt_op08
    selected_handoff_or_stop_not_executed_present = "selected_handoff_or_stop_not_executed" in pnt_op08
    explicit_boundary_blockers = _closed_pnt_op08_not_called_blockers(pnt_op08)

    status_ref, reasons, blockers, next_required_step = _op01_status_reason_blocker_next(
        op00_valid=op00_valid,
        pnt_op08_present=pnt_op08_present,
        pnt_op08_contract_valid=pnt_op08_contract_valid,
        pnt_op08_status_ref=pnt_op08_status_ref,
        pnt_op08_closed=pnt_op08_closed,
        pnt_op08_waiting=pnt_op08_waiting,
        pnt_op08_repair=pnt_op08_repair,
        pnt_op08_blocked=pnt_op08_blocked,
        selected_pnt_lane_ref=selected_pnt_lane_ref,
        selected_post_nci_next_boundary_not_executed_present=selected_post_nci_next_boundary_not_executed_present,
        selected_handoff_or_stop_not_executed_present=selected_handoff_or_stop_not_executed_present,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        explicit_boundary_blockers=explicit_boundary_blockers,
    )
    ready = status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_READY_FOR_OP02_REF
    waiting_explicit = status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF
    waiting_pnt = status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_PNT_OP08_TO_CLOSE_REF
    repair = status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF
    blocked = status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    session_id = _safe_review_session_id(review_session_id or pnt_op08.get("review_session_id") or op00.get("review_session_id"))

    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_material_present": op00_present,
        "op00_contract_valid": op00_valid,
        "op00_schema_version": _clean_ref(op00.get("schema_version"), default="pcm_op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id"), default="pcm_op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step"), default="pcm_op00_next_required_step_missing", max_length=360),
        "explicit_pnt_op08_closed_material_required": True,
        "pnt_op08_default_builder_call_allowed": False,
        "pnt_op08_default_material_synthesis_allowed": False,
        "pnt_op08_decision_table_as_single_lane_allowed": False,
        "pnt_op08_default_builder_called_here": False,
        "pnt_op08_default_material_synthesized_here": False,
        "pnt_r11_decision_table_used_as_single_lane_here": False,
        "pnt_op08_material_present": pnt_op08_present,
        "pnt_op08_contract_valid": pnt_op08_contract_valid,
        "pnt_op08_schema_version": _clean_ref(pnt_op08.get("schema_version"), default="pnt_op08_schema_missing", max_length=260),
        "pnt_op08_material_ref": _clean_ref(pnt_op08.get("material_id"), default="pnt_op08_material_missing", max_length=260),
        "pnt_op08_operation_step_ref": _clean_ref(pnt_op08.get("operation_step_ref"), default="pnt_op08_operation_step_missing", max_length=360),
        "pnt_op08_status_ref": pnt_op08_status_ref,
        "bodyfree_post_nci_triage_result_memo_closure_status_ref": _clean_ref(pnt_op08.get("bodyfree_post_nci_triage_result_memo_closure_status_ref"), default="pnt_op08_closure_status_missing", max_length=360),
        "pnt_op08_closed_bodyfree_stopped": pnt_op08_closed,
        "pnt_op08_waiting_for_input_refs": pnt_op08_waiting,
        "pnt_op08_repair_required": pnt_op08_repair,
        "pnt_op08_blocked_bodyfree_promotion_autorun": pnt_op08_blocked,
        "selected_pnt_status_ref": _clean_ref(pnt_op08.get("selected_pnt_status_ref"), default="selected_pnt_status_missing", max_length=360),
        "selected_pnt_lane_ref": selected_pnt_lane_ref or "selected_pnt_lane_missing",
        "selected_pnt_lane_ref_present": bool(selected_pnt_lane_ref),
        "selected_post_nci_outcome_group_ref": _clean_ref(pnt_op08.get("selected_post_nci_outcome_group_ref"), default="selected_post_nci_outcome_group_missing", max_length=360),
        "selected_post_nci_next_boundary_ref": _clean_ref(pnt_op08.get("selected_post_nci_next_boundary_ref"), default="selected_post_nci_next_boundary_missing", max_length=420),
        "selected_post_nci_next_boundary_kind_ref": _clean_ref(pnt_op08.get("selected_post_nci_next_boundary_kind_ref"), default="selected_post_nci_next_boundary_kind_missing", max_length=420),
        "selected_post_nci_next_boundary_not_executed": bool(pnt_op08.get("selected_post_nci_next_boundary_not_executed") is True),
        "selected_post_nci_next_boundary_not_executed_present": selected_post_nci_next_boundary_not_executed_present,
        "selected_handoff_or_stop_ref": _clean_ref(pnt_op08.get("selected_handoff_or_stop_ref"), default="selected_handoff_or_stop_missing", max_length=420),
        "selected_handoff_or_stop_kind_ref": _clean_ref(pnt_op08.get("selected_handoff_or_stop_kind_ref"), default="selected_handoff_or_stop_kind_missing", max_length=420),
        "selected_handoff_or_stop_not_executed": bool(pnt_op08.get("selected_handoff_or_stop_not_executed") is True),
        "selected_handoff_or_stop_not_executed_present": selected_handoff_or_stop_not_executed_present,
        "next_design_document_candidate_ref": _clean_ref(pnt_op08.get("next_design_document_candidate_ref"), default="next_design_document_candidate_missing", max_length=420),
        "next_design_document_allowed": bool(pnt_op08.get("next_design_document_allowed") is True),
        "manual_wait_required": bool(pnt_op08.get("manual_wait_required") is True),
        "manual_stop_required": bool(pnt_op08.get("manual_stop_required") is True),
        "repair_design_candidate": bool(pnt_op08.get("repair_design_candidate") is True),
        "target_test_result_status_ref": _clean_ref(pnt_op08.get("target_test_result_status_ref"), default="not_run", max_length=120),
        "selected_regression_result_status_ref": _clean_ref(pnt_op08.get("selected_regression_result_status_ref"), default="not_run", max_length=120),
        "compileall_result_status_ref": _clean_ref(pnt_op08.get("compileall_result_status_ref"), default="not_run", max_length=120),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "dhr_op05_not_called": bool(pnt_op08.get("dhr_op05_not_called") is True),
        "dhr_op06_not_called": bool(pnt_op08.get("dhr_op06_not_called") is True),
        "dmd_r52_not_executed": bool(pnt_op08.get("dmd_r52_not_executed") is True),
        "p5_p6_p8_p7_release_not_started": bool(pnt_op08.get("p5_p6_p8_p7_release_not_started") is True),
        "p8_question_design_not_started": bool(pnt_op08.get("p8_question_design_not_started") is True),
        "p8_question_implementation_not_started": bool(pnt_op08.get("p8_question_implementation_not_started") is True),
        "api_db_rn_runtime_response_key_not_changed": bool(pnt_op08.get("api_db_rn_runtime_response_key_not_changed") is True),
        "pnt_op08_input_forbidden_payload_key_path_refs": forbidden_paths,
        "pnt_op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "pnt_op08_input_body_like_value_path_refs": body_like_paths,
        "pnt_op08_input_body_like_value_path_count": len(body_like_paths),
        "pnt_op08_input_promotion_claim_refs": promotion_claims,
        "pnt_op08_input_promotion_claim_ref_count": len(promotion_claims),
        "pnt_op08_input_no_touch_mutation_path_refs": no_touch_paths,
        "pnt_op08_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op01_status_ref": status_ref,
        "bodyfree_pnt_op08_closed_material_intake_status_ref": status_ref,
        "pcm_op01_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP01_ALLOWED_STATUS_REFS),
        "pcm_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP01_ALLOWED_STATUS_REFS),
        "pcm_op01_ready_for_contract_validation": ready,
        "pcm_op01_waiting_for_explicit_pnt_op08_closed_material": waiting_explicit,
        "pcm_op01_waiting_for_pnt_op08_to_close": waiting_pnt,
        "pcm_op01_repair_required": repair,
        "pcm_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "pcm_op01_reason_refs": _dedupe_clean_refs(reasons, max_length=360),
        "pcm_op01_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=360)),
        "pcm_op01_blocker_refs": _dedupe_clean_refs(blockers, max_length=360),
        "pcm_op01_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=360)),
        "pcm_op01_does_not_validate_closed_material_contract": True,
        "pcm_op01_does_not_confirm_single_selected_lane": True,
        "pcm_op01_does_not_resolve_next_work_class": True,
        "pcm_op01_does_not_materialize_next_design_candidate": True,
        "pcm_op01_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op01_does_not_call_dhr_op05": True,
        "pcm_op01_does_not_call_dhr_op06": True,
        "pcm_op01_does_not_execute_dmd_r52_or_release": True,
        "pcm_op01_does_not_start_actual_review": True,
        "pcm_op01_does_not_request_raw_evidence": True,
        "pcm_op01_does_not_execute_repair": True,
        "pcm_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op01_does_not_materialize_p8_question_spec": True,
        "pcm_op01_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP01_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP01 explicit closed PNT-OP08 material intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP01_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP01")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP01",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP01_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("pcm_op00_implemented", "pcm_op01_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP01 implemented flag must be true after R2: {key}")
    if data.get("op00_schema_version") != P7_R54_AHR_POST_PNT_PCM_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 OP00 schema version changed")
    if data.get("op00_contract_valid") is True and data.get("op00_next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 OP00 next step changed")
    if data.get("bodyfree_pnt_op08_closed_material_intake_status_ref") != data.get("pcm_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 status alias changed")
    if tuple(data.get("pcm_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 allowed status refs changed")
    for key in (
        "explicit_pnt_op08_closed_material_required",
        "pcm_op01_does_not_validate_closed_material_contract",
        "pcm_op01_does_not_confirm_single_selected_lane",
        "pcm_op01_does_not_resolve_next_work_class",
        "pcm_op01_does_not_materialize_next_design_candidate",
        "pcm_op01_does_not_execute_selected_post_nci_next_boundary",
        "pcm_op01_does_not_call_dhr_op05",
        "pcm_op01_does_not_call_dhr_op06",
        "pcm_op01_does_not_execute_dmd_r52_or_release",
        "pcm_op01_does_not_start_actual_review",
        "pcm_op01_does_not_request_raw_evidence",
        "pcm_op01_does_not_execute_repair",
        "pcm_op01_does_not_start_p5_p6_p8_p7_or_release",
        "pcm_op01_does_not_change_api_db_rn_runtime_response_key",
        "pcm_op01_does_not_materialize_p8_question_spec",
        "pcm_op01_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP01 required true boundary changed: {key}")
    for key in (
        "pnt_op08_default_builder_call_allowed",
        "pnt_op08_default_material_synthesis_allowed",
        "pnt_op08_decision_table_as_single_lane_allowed",
        "pnt_op08_default_builder_called_here",
        "pnt_op08_default_material_synthesized_here",
        "pnt_r11_decision_table_used_as_single_lane_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP01 forbidden claim changed: {key}")
    for field, count_field in (
        ("pnt_op08_input_forbidden_payload_key_path_refs", "pnt_op08_input_forbidden_payload_key_path_count"),
        ("pnt_op08_input_body_like_value_path_refs", "pnt_op08_input_body_like_value_path_count"),
        ("pnt_op08_input_promotion_claim_refs", "pnt_op08_input_promotion_claim_ref_count"),
        ("pnt_op08_input_no_touch_mutation_path_refs", "pnt_op08_input_no_touch_mutation_path_count"),
        ("pcm_op01_reason_refs", "pcm_op01_reason_ref_count"),
        ("pcm_op01_blocker_refs", "pcm_op01_blocker_ref_count"),
        ("pcm_op01_allowed_status_refs", "pcm_op01_allowed_status_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP01 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 not-yet steps changed")
    status_ref = data.get("pcm_op01_status_ref")
    flags = [
        data.get("pcm_op01_ready_for_contract_validation") is True,
        data.get("pcm_op01_waiting_for_explicit_pnt_op08_closed_material") is True,
        data.get("pcm_op01_waiting_for_pnt_op08_to_close") is True,
        data.get("pcm_op01_repair_required") is True,
        data.get("pcm_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_READY_FOR_OP02_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 ready branch next step changed")
        for key in (
            "pnt_op08_material_present",
            "pnt_op08_contract_valid",
            "pnt_op08_closed_bodyfree_stopped",
            "selected_pnt_lane_ref_present",
            "selected_post_nci_next_boundary_not_executed",
            "selected_post_nci_next_boundary_not_executed_present",
            "selected_handoff_or_stop_not_executed",
            "selected_handoff_or_stop_not_executed_present",
            "dhr_op05_not_called",
            "dhr_op06_not_called",
            "dmd_r52_not_executed",
            "p5_p6_p8_p7_release_not_started",
            "p8_question_design_not_started",
            "p8_question_implementation_not_started",
            "api_db_rn_runtime_response_key_not_changed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP01 ready required true field changed: {key}")
        if data.get("selected_pnt_lane_ref") not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 selected lane not allowed")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 explicit wait branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_WAITING_FOR_PNT_OP08_TO_CLOSE_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_PNT_OP08_CLOSURE_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 PNT wait branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_REPAIR_REQUIRED_FOR_PNT_OP08_CLOSED_MATERIAL_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_PNT_OP08_CLOSED_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_PNT_OP08_CLOSED_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 blocked branch next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP01 unknown status ref")
    if status_ref != P7_R54_AHR_POST_PNT_PCM_OP01_STATUS_BLOCKED_PNT_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF:
        for field in (
            "pnt_op08_input_forbidden_payload_key_path_refs",
            "pnt_op08_input_body_like_value_path_refs",
            "pnt_op08_input_promotion_claim_refs",
            "pnt_op08_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP01 unexpected body/no-touch scan refs outside blocked branch: {field}")
    return True



def build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation(
    pcm_op01_explicit_closed_pnt_op08_material_intake: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PCM-OP02 closed PNT-OP08 material contract validation material.

    PCM-OP02 reads the explicit PCM-OP01 intake material.  It does not confirm a
    single lane yet, does not resolve next work class, and does not execute any
    selected downstream boundary.
    """

    session_id = _safe_review_session_id(review_session_id)
    op01 = pcm_op01_explicit_closed_pnt_op08_material_intake
    op01_present = isinstance(op01, Mapping)
    op01_valid = _op01_contract_valid(op01)
    op01_status_ref = _clean_ref(op01.get("pcm_op01_status_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=300)
    op01_ready = bool(op01_valid and op01 and op01.get("pcm_op01_ready_for_contract_validation") is True)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op01 or {}, path="pcm_op01")
    promotion_claims = _filter_allowed_prior_implemented_flag_paths(
        promotion_claims,
        allowed_implemented_keys=("pcm_op00_implemented", "pcm_op01_implemented"),
    )
    multi_lane_paths = _dedupe_clean_refs(_scan_multi_lane_material_key_paths(op01 or {}, path="pcm_op01"), max_length=340)

    lane_ref = _clean_ref(op01.get("selected_pnt_lane_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=260)
    selected_status_ref = _clean_ref(op01.get("selected_pnt_status_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=300)
    outcome_ref = _clean_ref(op01.get("selected_post_nci_outcome_group_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=260)
    boundary_ref = _clean_ref(op01.get("selected_post_nci_next_boundary_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=420)
    boundary_kind_ref = _clean_ref(op01.get("selected_post_nci_next_boundary_kind_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=420)
    handoff_ref = _clean_ref(op01.get("selected_handoff_or_stop_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=420)
    handoff_kind_ref = _clean_ref(op01.get("selected_handoff_or_stop_kind_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=420)
    next_design_ref = _clean_ref(op01.get("next_design_document_candidate_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=460)

    lane_allowed = lane_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS
    expected_status_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_STATUS_REF_MAP.get(lane_ref, "missing")
    expected_outcome_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP.get(lane_ref, "missing")
    expected_boundary_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP.get(lane_ref, "missing")
    expected_boundary_kind_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP.get(lane_ref, "missing")
    expected_handoff_kind_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_ENVELOPE_KIND_REF_MAP.get(lane_ref, "missing")
    expected_next_design_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP.get(lane_ref, "missing")
    expected_next_design_allowed = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP.get(lane_ref, False)
    expected_manual_wait = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP.get(lane_ref, False)
    expected_manual_stop = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP.get(lane_ref, False)
    expected_repair_design = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP.get(lane_ref, False)

    selected_status_present = selected_status_ref not in ("", "missing")
    lane_present = lane_ref not in ("", "missing")
    outcome_present = outcome_ref not in ("", "missing")
    outcome_allowed = outcome_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_OUTCOME_GROUP_REFS
    boundary_present = boundary_ref not in ("", "missing")
    boundary_kind_present = boundary_kind_ref not in ("", "missing")
    handoff_ref_present = handoff_ref not in ("", "missing")
    handoff_kind_present = handoff_kind_ref not in ("", "missing")
    next_design_present = next_design_ref not in ("", "missing")

    boundary_not_executed_present = bool(isinstance(op01, Mapping) and "selected_post_nci_next_boundary_not_executed" in op01)
    boundary_not_executed = bool(isinstance(op01, Mapping) and op01.get("selected_post_nci_next_boundary_not_executed") is True)
    handoff_not_executed_present = bool(isinstance(op01, Mapping) and "selected_handoff_or_stop_not_executed" in op01)
    handoff_not_executed = bool(isinstance(op01, Mapping) and op01.get("selected_handoff_or_stop_not_executed") is True)

    pnt_op08_contract_valid = bool(isinstance(op01, Mapping) and op01.get("pnt_op08_contract_valid") is True)
    pnt_op08_closed = bool(isinstance(op01, Mapping) and op01.get("pnt_op08_closed_bodyfree_stopped") is True)
    pnt_op08_status_ref = _clean_ref(op01.get("pnt_op08_status_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=300)

    next_design_allowed = bool(isinstance(op01, Mapping) and op01.get("next_design_document_allowed") is True)
    manual_wait_required = bool(isinstance(op01, Mapping) and op01.get("manual_wait_required") is True)
    manual_stop_required = bool(isinstance(op01, Mapping) and op01.get("manual_stop_required") is True)
    repair_design_candidate = bool(isinstance(op01, Mapping) and op01.get("repair_design_candidate") is True)

    dhr_op05_not_called = bool((not op01_present) or (isinstance(op01, Mapping) and op01.get("dhr_op05_not_called") is True))
    dhr_op06_not_called = bool((not op01_present) or (isinstance(op01, Mapping) and op01.get("dhr_op06_not_called") is True))
    dmd_r52_not_executed = bool((not op01_present) or (isinstance(op01, Mapping) and op01.get("dmd_r52_not_executed") is True))
    p5_p6_p8_p7_release_not_started = bool((not op01_present) or (isinstance(op01, Mapping) and op01.get("p5_p6_p8_p7_release_not_started") is True))
    p8_question_design_not_started = bool((not op01_present) or (isinstance(op01, Mapping) and op01.get("p8_question_design_not_started") is True))
    p8_question_implementation_not_started = bool((not op01_present) or (isinstance(op01, Mapping) and op01.get("p8_question_implementation_not_started") is True))
    api_db_rn_runtime_response_key_not_changed = bool((not op01_present) or (isinstance(op01, Mapping) and op01.get("api_db_rn_runtime_response_key_not_changed") is True))

    status_ref, reason_refs, blocker_refs, next_required_step = _op02_status_reason_blocker_next(
        op01_present=op01_present,
        op01_valid=op01_valid,
        op01_ready=op01_ready,
        pnt_op08_closed=pnt_op08_closed,
        pnt_op08_contract_valid=pnt_op08_contract_valid,
        lane_present=lane_present,
        lane_allowed=lane_allowed,
        status_present=selected_status_present,
        status_matches_lane=bool(lane_allowed and selected_status_ref == expected_status_ref),
        outcome_present=outcome_present,
        outcome_allowed=outcome_allowed,
        outcome_matches_lane=bool(lane_allowed and outcome_ref == expected_outcome_ref),
        boundary_present=boundary_present,
        boundary_matches_lane=bool(lane_allowed and boundary_ref == expected_boundary_ref),
        boundary_kind_present=boundary_kind_present,
        boundary_kind_matches_lane=bool(lane_allowed and boundary_kind_ref == expected_boundary_kind_ref),
        boundary_not_executed_present=boundary_not_executed_present,
        boundary_not_executed=boundary_not_executed,
        handoff_ref_present=handoff_ref_present,
        handoff_ref_matches_boundary=bool(handoff_ref_present and handoff_ref == boundary_ref),
        handoff_ref_matches_lane=bool(lane_allowed and handoff_ref == expected_boundary_ref),
        handoff_kind_present=handoff_kind_present,
        handoff_kind_matches_lane=bool(lane_allowed and handoff_kind_ref == expected_handoff_kind_ref),
        handoff_not_executed_present=handoff_not_executed_present,
        handoff_not_executed=handoff_not_executed,
        next_design_present=next_design_present,
        next_design_matches_lane=bool(lane_allowed and next_design_ref == expected_next_design_ref),
        next_design_allowed_matches_lane=bool(lane_allowed and next_design_allowed is expected_next_design_allowed),
        manual_wait_matches_lane=bool(lane_allowed and manual_wait_required is expected_manual_wait),
        manual_stop_matches_lane=bool(lane_allowed and manual_stop_required is expected_manual_stop),
        repair_design_matches_lane=bool(lane_allowed and repair_design_candidate is expected_repair_design),
        dhr_op05_not_called=dhr_op05_not_called,
        dhr_op06_not_called=dhr_op06_not_called,
        dmd_r52_not_executed=dmd_r52_not_executed,
        p5_p6_p8_p7_release_not_started=p5_p6_p8_p7_release_not_started,
        p8_question_design_not_started=p8_question_design_not_started,
        p8_question_implementation_not_started=p8_question_implementation_not_started,
        api_db_rn_runtime_response_key_not_changed=api_db_rn_runtime_response_key_not_changed,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        multi_lane_paths=multi_lane_paths,
    )
    contract_valid = status_ref == P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_CONTRACT_VALID_STOPPED_REF

    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_material_present": op01_present,
        "op01_contract_valid": op01_valid,
        "op01_schema_version": _clean_ref(op01.get("schema_version") if isinstance(op01, Mapping) else None, default="missing", max_length=300),
        "op01_material_ref": _clean_ref(op01.get("material_id") if isinstance(op01, Mapping) else None, default="missing", max_length=300),
        "op01_status_ref": op01_status_ref,
        "op01_next_required_step": _clean_ref(op01.get("next_required_step") if isinstance(op01, Mapping) else None, default="missing", max_length=420),
        "op01_ready_for_contract_validation": op01_ready,
        "pnt_op08_status_ref": pnt_op08_status_ref,
        "pnt_op08_closed_bodyfree_stopped": pnt_op08_closed,
        "pnt_op08_contract_valid": pnt_op08_contract_valid,
        "selected_pnt_status_ref": selected_status_ref,
        "selected_pnt_status_ref_present": selected_status_present,
        "selected_pnt_status_ref_matches_lane": bool(lane_allowed and selected_status_ref == expected_status_ref),
        "selected_pnt_lane_ref": lane_ref,
        "selected_pnt_lane_ref_present": lane_present,
        "selected_pnt_lane_ref_allowed": lane_allowed,
        "selected_post_nci_outcome_group_ref": outcome_ref,
        "selected_post_nci_outcome_group_ref_present": outcome_present,
        "selected_post_nci_outcome_group_ref_allowed": outcome_allowed,
        "selected_post_nci_outcome_group_ref_matches_lane": bool(lane_allowed and outcome_ref == expected_outcome_ref),
        "selected_post_nci_next_boundary_ref": boundary_ref,
        "selected_post_nci_next_boundary_ref_present": boundary_present,
        "selected_post_nci_next_boundary_ref_matches_lane": bool(lane_allowed and boundary_ref == expected_boundary_ref),
        "selected_post_nci_next_boundary_kind_ref": boundary_kind_ref,
        "selected_post_nci_next_boundary_kind_ref_present": boundary_kind_present,
        "selected_post_nci_next_boundary_kind_ref_matches_lane": bool(lane_allowed and boundary_kind_ref == expected_boundary_kind_ref),
        "selected_post_nci_next_boundary_not_executed": boundary_not_executed,
        "selected_post_nci_next_boundary_not_executed_present": boundary_not_executed_present,
        "selected_handoff_or_stop_ref": handoff_ref,
        "selected_handoff_or_stop_ref_present": handoff_ref_present,
        "selected_handoff_or_stop_ref_matches_selected_post_nci_next_boundary_ref": bool(handoff_ref_present and handoff_ref == boundary_ref),
        "selected_handoff_or_stop_ref_matches_lane": bool(lane_allowed and handoff_ref == expected_boundary_ref),
        "selected_handoff_or_stop_kind_ref": handoff_kind_ref,
        "selected_handoff_or_stop_kind_ref_present": handoff_kind_present,
        "selected_handoff_or_stop_kind_ref_matches_lane": bool(lane_allowed and handoff_kind_ref == expected_handoff_kind_ref),
        "selected_handoff_or_stop_not_executed": handoff_not_executed,
        "selected_handoff_or_stop_not_executed_present": handoff_not_executed_present,
        "next_design_document_candidate_ref": next_design_ref,
        "next_design_document_candidate_ref_present": next_design_present,
        "next_design_document_candidate_ref_matches_lane": bool(lane_allowed and next_design_ref == expected_next_design_ref),
        "next_design_document_allowed": next_design_allowed,
        "next_design_document_allowed_matches_lane": bool(lane_allowed and next_design_allowed is expected_next_design_allowed),
        "manual_wait_required": manual_wait_required,
        "manual_wait_required_matches_lane": bool(lane_allowed and manual_wait_required is expected_manual_wait),
        "manual_stop_required": manual_stop_required,
        "manual_stop_required_matches_lane": bool(lane_allowed and manual_stop_required is expected_manual_stop),
        "repair_design_candidate": repair_design_candidate,
        "repair_design_candidate_matches_lane": bool(lane_allowed and repair_design_candidate is expected_repair_design),
        "dhr_op05_not_called": dhr_op05_not_called,
        "dhr_op06_not_called": dhr_op06_not_called,
        "dmd_r52_not_executed": dmd_r52_not_executed,
        "p5_p6_p8_p7_release_not_started": p5_p6_p8_p7_release_not_started,
        "p8_question_design_not_started": p8_question_design_not_started,
        "p8_question_implementation_not_started": p8_question_implementation_not_started,
        "api_db_rn_runtime_response_key_not_changed": api_db_rn_runtime_response_key_not_changed,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "closed_pnt_op08_material_contract_valid": contract_valid,
        "pcm_op02_status_ref": status_ref,
        "bodyfree_closed_pnt_op08_material_contract_validation_status_ref": status_ref,
        "pcm_op02_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP02_ALLOWED_STATUS_REFS),
        "pcm_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP02_ALLOWED_STATUS_REFS),
        "pcm_op02_contract_valid_stopped": contract_valid,
        "pcm_op02_repair_required": status_ref == P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_REPAIR_REQUIRED_FOR_CONTRACT_REF,
        "pcm_op02_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_BLOCKED_LEAK_PROMOTION_OR_AUTORUN_REF,
        "pcm_op02_reason_refs": _dedupe_clean_refs(reason_refs, max_length=360),
        "pcm_op02_reason_ref_count": len(_dedupe_clean_refs(reason_refs, max_length=360)),
        "pcm_op02_blocker_refs": _dedupe_clean_refs(blocker_refs, max_length=360),
        "pcm_op02_blocker_ref_count": len(_dedupe_clean_refs(blocker_refs, max_length=360)),
        "op02_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op02_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op02_input_body_like_value_path_refs": list(body_like_paths),
        "op02_input_body_like_value_path_count": len(body_like_paths),
        "op02_input_promotion_claim_refs": list(promotion_claims),
        "op02_input_promotion_claim_ref_count": len(promotion_claims),
        "op02_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op02_input_no_touch_mutation_path_count": len(no_touch_paths),
        "op02_input_multi_lane_material_key_path_refs": list(multi_lane_paths),
        "op02_input_multi_lane_material_key_path_count": len(multi_lane_paths),
        "pcm_op02_does_not_confirm_single_selected_lane": True,
        "pcm_op02_does_not_resolve_next_work_class": True,
        "pcm_op02_does_not_materialize_next_design_candidate": True,
        "pcm_op02_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op02_does_not_execute_selected_pcm_next_boundary": True,
        "pcm_op02_does_not_call_dhr_op05": True,
        "pcm_op02_does_not_call_dhr_op06": True,
        "pcm_op02_does_not_execute_dmd_r52_or_release": True,
        "pcm_op02_does_not_start_actual_review": True,
        "pcm_op02_does_not_request_raw_evidence": True,
        "pcm_op02_does_not_execute_repair": True,
        "pcm_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op02_does_not_materialize_p8_question_spec": True,
        "pcm_op02_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP02_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "pcm_op02_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP02 closed PNT-OP08 material contract validation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP02")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP02_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP02",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP02_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP02 implemented flag must be true after R3: {key}")
    if data.get("bodyfree_closed_pnt_op08_material_contract_validation_status_ref") != data.get("pcm_op02_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 status alias changed")
    if tuple(data.get("pcm_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 allowed status refs changed")
    for key in (
        "pcm_op02_does_not_confirm_single_selected_lane",
        "pcm_op02_does_not_resolve_next_work_class",
        "pcm_op02_does_not_materialize_next_design_candidate",
        "pcm_op02_does_not_execute_selected_post_nci_next_boundary",
        "pcm_op02_does_not_execute_selected_pcm_next_boundary",
        "pcm_op02_does_not_call_dhr_op05",
        "pcm_op02_does_not_call_dhr_op06",
        "pcm_op02_does_not_execute_dmd_r52_or_release",
        "pcm_op02_does_not_start_actual_review",
        "pcm_op02_does_not_request_raw_evidence",
        "pcm_op02_does_not_execute_repair",
        "pcm_op02_does_not_start_p5_p6_p8_p7_or_release",
        "pcm_op02_does_not_change_api_db_rn_runtime_response_key",
        "pcm_op02_does_not_materialize_p8_question_spec",
        "pcm_op02_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP02 required true boundary changed: {key}")
    for key in (
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP02 unverified green claim changed: {key}")
    for field, count_field in (
        ("pcm_op02_allowed_status_refs", "pcm_op02_allowed_status_ref_count"),
        ("pcm_op02_reason_refs", "pcm_op02_reason_ref_count"),
        ("pcm_op02_blocker_refs", "pcm_op02_blocker_ref_count"),
        ("op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count"),
        ("op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count"),
        ("op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count"),
        ("op02_input_no_touch_mutation_path_refs", "op02_input_no_touch_mutation_path_count"),
        ("op02_input_multi_lane_material_key_path_refs", "op02_input_multi_lane_material_key_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP02 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 not-yet steps changed")

    status_ref = data.get("pcm_op02_status_ref")
    flags = [
        data.get("pcm_op02_contract_valid_stopped") is True,
        data.get("pcm_op02_repair_required") is True,
        data.get("pcm_op02_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PNT_PCM_OP02_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 exactly one contract status branch must be selected")
    if status_ref == P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_CONTRACT_VALID_STOPPED_REF:
        for key in (
            "op01_material_present",
            "op01_contract_valid",
            "op01_ready_for_contract_validation",
            "pnt_op08_closed_bodyfree_stopped",
            "pnt_op08_contract_valid",
            "selected_pnt_status_ref_present",
            "selected_pnt_status_ref_matches_lane",
            "selected_pnt_lane_ref_present",
            "selected_pnt_lane_ref_allowed",
            "selected_post_nci_outcome_group_ref_present",
            "selected_post_nci_outcome_group_ref_allowed",
            "selected_post_nci_outcome_group_ref_matches_lane",
            "selected_post_nci_next_boundary_ref_present",
            "selected_post_nci_next_boundary_ref_matches_lane",
            "selected_post_nci_next_boundary_kind_ref_present",
            "selected_post_nci_next_boundary_kind_ref_matches_lane",
            "selected_post_nci_next_boundary_not_executed",
            "selected_post_nci_next_boundary_not_executed_present",
            "selected_handoff_or_stop_ref_present",
            "selected_handoff_or_stop_ref_matches_selected_post_nci_next_boundary_ref",
            "selected_handoff_or_stop_ref_matches_lane",
            "selected_handoff_or_stop_kind_ref_present",
            "selected_handoff_or_stop_kind_ref_matches_lane",
            "selected_handoff_or_stop_not_executed",
            "selected_handoff_or_stop_not_executed_present",
            "next_design_document_candidate_ref_present",
            "next_design_document_candidate_ref_matches_lane",
            "next_design_document_allowed_matches_lane",
            "manual_wait_required_matches_lane",
            "manual_stop_required_matches_lane",
            "repair_design_candidate_matches_lane",
            "dhr_op05_not_called",
            "dhr_op06_not_called",
            "dmd_r52_not_executed",
            "p5_p6_p8_p7_release_not_started",
            "p8_question_design_not_started",
            "p8_question_implementation_not_started",
            "api_db_rn_runtime_response_key_not_changed",
            "closed_pnt_op08_material_contract_valid",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP02 valid branch contract flag changed: {key}")
        if data.get("pcm_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 valid branch cannot carry blockers")
        if data.get("op02_input_multi_lane_material_key_path_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 valid branch cannot carry multi-lane refs")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 valid next step changed")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_REPAIR_REQUIRED_FOR_CONTRACT_REF:
        if not data.get("pcm_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 repair branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 repair next step changed")
    else:
        if not data.get("pcm_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 blocked branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_CLOSED_PNT_OP08_MATERIAL_CONTRACT_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_PNT_PCM_OP02_STATUS_BLOCKED_LEAK_PROMOTION_OR_AUTORUN_REF:
        for field in (
            "op02_input_forbidden_payload_key_path_refs",
            "op02_input_body_like_value_path_refs",
            "op02_input_promotion_claim_refs",
            "op02_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP02 non-blocked branch cannot carry body/no-touch scan blockers")
    return True


def build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation(
    pcm_op02_closed_material_contract_validation: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PCM-OP03 single selected lane confirmation material.

    PCM-OP03 confirms that the material is one selected lane, not a decision
    table, six-outcome summary, all-lane target summary, or ambiguous multi-lane
    material.  It still does not resolve next work class or execute anything.
    """

    session_id = _safe_review_session_id(review_session_id)
    op02 = pcm_op02_closed_material_contract_validation
    op02_present = isinstance(op02, Mapping)
    op02_valid = _op02_contract_valid(op02)
    op02_status_ref = _clean_ref(op02.get("pcm_op02_status_ref") if isinstance(op02, Mapping) else None, default="missing", max_length=300)
    op02_contract_valid_stopped = bool(op02_valid and op02 and op02.get("closed_pnt_op08_material_contract_valid") is True)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op02 or {}, path="pcm_op02")
    promotion_claims = _filter_allowed_prior_implemented_flag_paths(
        promotion_claims,
        allowed_implemented_keys=("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented"),
    )
    multi_lane_paths = _dedupe_clean_refs(_scan_multi_lane_material_key_paths(op02 or {}, path="pcm_op02"), max_length=340)
    ambiguous_lane_flags = _dedupe_clean_refs(_input_true_lane_flag_refs(op02), max_length=260)

    lane_ref = _clean_ref(op02.get("selected_pnt_lane_ref") if isinstance(op02, Mapping) else None, default="missing", max_length=260)
    lane_allowed = lane_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS
    status_ref, confirmed, reason_refs, blocker_refs, next_required_step = _op03_status_reason_blocker_next(
        op02_present=op02_present,
        op02_valid=op02_valid,
        op02_contract_valid_stopped=op02_contract_valid_stopped,
        op02_status_ref=op02_status_ref,
        lane_ref=lane_ref,
        lane_allowed=lane_allowed,
        multi_lane_paths=multi_lane_paths,
        ambiguous_lane_flags=ambiguous_lane_flags,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    selected_lane_ref = lane_ref if confirmed else "missing"
    lane_flags = _pcm_op03_lane_flags(selected_lane_ref)
    single_lane_flag_count = sum(value is True for value in lane_flags.values())

    selected_pnt_status_ref = _clean_ref(op02.get("selected_pnt_status_ref") if confirmed and isinstance(op02, Mapping) else None, default="missing", max_length=300)
    outcome_ref = _clean_ref(op02.get("selected_post_nci_outcome_group_ref") if confirmed and isinstance(op02, Mapping) else None, default="missing", max_length=260)
    boundary_ref = _clean_ref(op02.get("selected_post_nci_next_boundary_ref") if confirmed and isinstance(op02, Mapping) else None, default="missing", max_length=420)
    boundary_kind_ref = _clean_ref(op02.get("selected_post_nci_next_boundary_kind_ref") if confirmed and isinstance(op02, Mapping) else None, default="missing", max_length=420)
    handoff_ref = _clean_ref(op02.get("selected_handoff_or_stop_ref") if confirmed and isinstance(op02, Mapping) else None, default="missing", max_length=420)
    handoff_kind_ref = _clean_ref(op02.get("selected_handoff_or_stop_kind_ref") if confirmed and isinstance(op02, Mapping) else None, default="missing", max_length=420)
    next_design_ref = _clean_ref(op02.get("next_design_document_candidate_ref") if confirmed and isinstance(op02, Mapping) else None, default="missing", max_length=460)

    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_material_present": op02_present,
        "op02_contract_valid": op02_valid,
        "op02_schema_version": _clean_ref(op02.get("schema_version") if isinstance(op02, Mapping) else None, default="missing", max_length=300),
        "op02_material_ref": _clean_ref(op02.get("material_id") if isinstance(op02, Mapping) else None, default="missing", max_length=300),
        "op02_status_ref": op02_status_ref,
        "op02_next_required_step": _clean_ref(op02.get("next_required_step") if isinstance(op02, Mapping) else None, default="missing", max_length=420),
        "op02_contract_valid_stopped": op02_contract_valid_stopped,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": selected_lane_ref,
        "selected_pnt_lane_ref_allowed": bool(confirmed and lane_allowed),
        "single_selected_pnt_lane_confirmed": confirmed,
        "single_selected_pnt_lane_material_present": bool(confirmed),
        "selected_post_nci_outcome_group_ref": outcome_ref,
        "selected_post_nci_next_boundary_ref": boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": bool(confirmed),
        "selected_handoff_or_stop_ref": handoff_ref,
        "selected_handoff_or_stop_kind_ref": handoff_kind_ref,
        "selected_handoff_or_stop_not_executed": bool(confirmed),
        "next_design_document_candidate_ref": next_design_ref,
        "next_design_document_allowed": bool(confirmed and isinstance(op02, Mapping) and op02.get("next_design_document_allowed") is True),
        "manual_wait_required": bool(confirmed and isinstance(op02, Mapping) and op02.get("manual_wait_required") is True),
        "manual_stop_required": bool(confirmed and isinstance(op02, Mapping) and op02.get("manual_stop_required") is True),
        "repair_design_candidate": bool(confirmed and isinstance(op02, Mapping) and op02.get("repair_design_candidate") is True),
        "selected_pcm_next_work_class_not_resolved_here": True,
        "selected_pcm_next_boundary_not_materialized_here": True,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "allowed_pnt_lane_refs": list(P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS),
        "allowed_pnt_lane_ref_count": len(P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS),
        "allowed_pnt_outcome_group_refs": list(P7_R54_AHR_POST_PNT_PCM_ALLOWED_OUTCOME_GROUP_REFS),
        "allowed_pnt_outcome_group_ref_count": len(P7_R54_AHR_POST_PNT_PCM_ALLOWED_OUTCOME_GROUP_REFS),
        "pcm_op03_lane_flag_refs": list(P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS),
        "pcm_op03_lane_flag_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS),
        **lane_flags,
        "single_lane_flag_count": single_lane_flag_count,
        "decision_table_material_rejected": any("decision_table" in ref for ref in multi_lane_paths),
        "multi_lane_material_rejected": bool(multi_lane_paths or len(ambiguous_lane_flags) > 1),
        "multi_lane_material_key_path_refs": list(multi_lane_paths),
        "multi_lane_material_key_path_count": len(multi_lane_paths),
        "ambiguous_lane_flag_refs": list(ambiguous_lane_flags),
        "ambiguous_lane_flag_ref_count": len(ambiguous_lane_flags),
        "pcm_op03_status_ref": status_ref,
        "bodyfree_single_selected_lane_confirmation_status_ref": status_ref,
        "pcm_op03_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP03_ALLOWED_STATUS_REFS),
        "pcm_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP03_ALLOWED_STATUS_REFS),
        "pcm_op03_single_selected_lane_confirmed_stopped": status_ref == P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_SINGLE_SELECTED_LANE_CONFIRMED_STOPPED_REF,
        "pcm_op03_waiting_for_single_selected_lane_material": status_ref == P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_WAITING_FOR_SINGLE_SELECTED_LANE_MATERIAL_REF,
        "pcm_op03_repair_required_for_multi_or_ambiguous_lane": status_ref == P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_LANE_REF,
        "pcm_op03_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_BLOCKED_PROMOTION_OR_AUTORUN_REF,
        "pcm_op03_reason_refs": _dedupe_clean_refs(reason_refs, max_length=360),
        "pcm_op03_reason_ref_count": len(_dedupe_clean_refs(reason_refs, max_length=360)),
        "pcm_op03_blocker_refs": _dedupe_clean_refs(blocker_refs, max_length=360),
        "pcm_op03_blocker_ref_count": len(_dedupe_clean_refs(blocker_refs, max_length=360)),
        "op03_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op03_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op03_input_body_like_value_path_refs": list(body_like_paths),
        "op03_input_body_like_value_path_count": len(body_like_paths),
        "op03_input_promotion_claim_refs": list(promotion_claims),
        "op03_input_promotion_claim_ref_count": len(promotion_claims),
        "op03_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op03_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op03_does_not_resolve_next_work_class": True,
        "pcm_op03_does_not_materialize_next_design_candidate": True,
        "pcm_op03_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op03_does_not_execute_selected_pcm_next_boundary": True,
        "pcm_op03_does_not_call_dhr_op05": True,
        "pcm_op03_does_not_call_dhr_op06": True,
        "pcm_op03_does_not_execute_dmd_r52_or_release": True,
        "pcm_op03_does_not_start_actual_review": True,
        "pcm_op03_does_not_request_raw_evidence": True,
        "pcm_op03_does_not_execute_repair": True,
        "pcm_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op03_does_not_materialize_p8_question_spec": True,
        "pcm_op03_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP03_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "pcm_op02_implemented": True,
        "pcm_op03_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP03 single selected lane confirmation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP03")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP03_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP03",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP03_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP03 implemented flag must be true after R3: {key}")
    if data.get("bodyfree_single_selected_lane_confirmation_status_ref") != data.get("pcm_op03_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 status alias changed")
    if tuple(data.get("pcm_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 allowed status refs changed")
    for key in (
        "selected_pcm_next_work_class_not_resolved_here",
        "selected_pcm_next_boundary_not_materialized_here",
        "pcm_op03_does_not_resolve_next_work_class",
        "pcm_op03_does_not_materialize_next_design_candidate",
        "pcm_op03_does_not_execute_selected_post_nci_next_boundary",
        "pcm_op03_does_not_execute_selected_pcm_next_boundary",
        "pcm_op03_does_not_call_dhr_op05",
        "pcm_op03_does_not_call_dhr_op06",
        "pcm_op03_does_not_execute_dmd_r52_or_release",
        "pcm_op03_does_not_start_actual_review",
        "pcm_op03_does_not_request_raw_evidence",
        "pcm_op03_does_not_execute_repair",
        "pcm_op03_does_not_start_p5_p6_p8_p7_or_release",
        "pcm_op03_does_not_change_api_db_rn_runtime_response_key",
        "pcm_op03_does_not_materialize_p8_question_spec",
        "pcm_op03_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP03 required true boundary changed: {key}")
    for key in (
        "selected_pcm_next_boundary_execution_allowed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP03 forbidden claim changed: {key}")
    for field, count_field in (
        ("allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count"),
        ("allowed_pnt_outcome_group_refs", "allowed_pnt_outcome_group_ref_count"),
        ("pcm_op03_lane_flag_refs", "pcm_op03_lane_flag_ref_count"),
        ("multi_lane_material_key_path_refs", "multi_lane_material_key_path_count"),
        ("ambiguous_lane_flag_refs", "ambiguous_lane_flag_ref_count"),
        ("pcm_op03_allowed_status_refs", "pcm_op03_allowed_status_ref_count"),
        ("pcm_op03_reason_refs", "pcm_op03_reason_ref_count"),
        ("pcm_op03_blocker_refs", "pcm_op03_blocker_ref_count"),
        ("op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count"),
        ("op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count"),
        ("op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count"),
        ("op03_input_no_touch_mutation_path_refs", "op03_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP03 {count_field} changed")
    if tuple(data.get("allowed_pnt_lane_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 allowed lane refs changed")
    if tuple(data.get("allowed_pnt_outcome_group_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_OUTCOME_GROUP_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 allowed outcome group refs changed")
    if tuple(data.get("pcm_op03_lane_flag_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 lane flag refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 not-yet steps changed")

    status_ref = data.get("pcm_op03_status_ref")
    branch_flags = [
        data.get("pcm_op03_single_selected_lane_confirmed_stopped") is True,
        data.get("pcm_op03_waiting_for_single_selected_lane_material") is True,
        data.get("pcm_op03_repair_required_for_multi_or_ambiguous_lane") is True,
        data.get("pcm_op03_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PNT_PCM_OP03_ALLOWED_STATUS_REFS or sum(branch_flags) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 exactly one single-lane status branch must be selected")
    lane_flag_sum = sum(data.get(key) is True for key in P7_R54_AHR_POST_PNT_PCM_OP03_LANE_FLAG_REFS)
    if data.get("single_lane_flag_count") != lane_flag_sum:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 lane flag count changed")
    if status_ref == P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_SINGLE_SELECTED_LANE_CONFIRMED_STOPPED_REF:
        lane_ref = data.get("selected_pnt_lane_ref")
        if lane_ref not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 confirmed lane is not allowed")
        if data.get("single_selected_pnt_lane_confirmed") is not True or data.get("single_selected_pnt_lane_material_present") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 confirmed branch single-lane flags changed")
        if lane_flag_sum != 1:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 confirmed branch must set exactly one lane flag")
        if any(data.get(key) is not value for key, value in _pcm_op03_lane_flags(str(lane_ref)).items()):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 lane flags do not match selected lane")
        if data.get("selected_pnt_status_ref") != pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_STATUS_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 status does not match lane")
        if data.get("selected_post_nci_outcome_group_ref") != pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 outcome group does not match lane")
        if data.get("selected_post_nci_next_boundary_ref") != pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 boundary ref does not match lane")
        if data.get("selected_post_nci_next_boundary_kind_ref") != pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 boundary kind does not match lane")
        if data.get("selected_handoff_or_stop_ref") != data.get("selected_post_nci_next_boundary_ref"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 selected handoff ref changed")
        if data.get("next_design_document_candidate_ref") != pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 next design candidate ref changed")
        if data.get("next_design_document_allowed") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 next design allowed flag changed")
        if data.get("manual_wait_required") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 manual wait flag changed")
        if data.get("manual_stop_required") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 manual stop flag changed")
        if data.get("repair_design_candidate") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 repair design flag changed")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True or data.get("selected_handoff_or_stop_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 confirmed branch must stay non-executed")
        if data.get("pcm_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 confirmed branch cannot carry blockers")
        if data.get("multi_lane_material_key_path_refs") or data.get("ambiguous_lane_flag_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 confirmed branch cannot carry ambiguous lane refs")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 confirmed next step changed")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_WAITING_FOR_SINGLE_SELECTED_LANE_MATERIAL_REF:
        if lane_flag_sum != 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 waiting branch cannot set lane flags")
        if not data.get("pcm_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 waiting branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_SINGLE_SELECTED_PNT_LANE_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_REPAIR_REQUIRED_FOR_MULTI_OR_AMBIGUOUS_LANE_REF:
        if lane_flag_sum != 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 repair branch cannot set confirmed lane flags")
        if not data.get("pcm_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 repair branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_MULTI_OR_AMBIGUOUS_PNT_LANE_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 repair next step changed")
    else:
        if lane_flag_sum != 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 blocked branch cannot set lane flags")
        if not data.get("pcm_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 blocked branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_SINGLE_LANE_CONFIRMATION_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_PNT_PCM_OP03_STATUS_BLOCKED_PROMOTION_OR_AUTORUN_REF:
        for field in (
            "op03_input_forbidden_payload_key_path_refs",
            "op03_input_body_like_value_path_refs",
            "op03_input_promotion_claim_refs",
            "op03_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP03 non-blocked branch cannot carry body/no-touch scan blockers")
    return True


def _op04_contract_valid(op04: Mapping[str, Any] | None) -> bool:
    if not isinstance(op04, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_contract(op04) is True
    except ValueError:
        return False


def _op04_status_reason_blocker_next(
    *,
    op03_present: bool,
    op03_valid: bool,
    op03_single_selected_lane_confirmed: bool,
    lane_ref: str,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op04_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op04_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("op04_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op04_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF,
            ["next_work_class_resolution_blocked_before_envelope_materialization"],
            _dedupe_clean_refs(blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_WORK_CLASS_RESOLVER_REF,
        )

    repair_blockers: list[str] = []
    if not op03_present:
        repair_blockers.append("pcm_op03_single_selected_lane_confirmation_material_missing")
    if op03_present and not op03_valid:
        repair_blockers.append("pcm_op03_single_selected_lane_confirmation_contract_invalid")
    if op03_present and not op03_single_selected_lane_confirmed:
        repair_blockers.append("pcm_op03_single_selected_lane_not_confirmed_for_next_work_class_resolution")
    if op03_single_selected_lane_confirmed and lane_ref not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
        repair_blockers.append("selected_pnt_lane_ref_unknown_or_not_allowed_for_next_work_class_resolution")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF,
            ["next_work_class_resolution_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_WORK_CLASS_INPUTS_REF,
        )

    return (
        P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_NEXT_WORK_CLASS_RESOLVED_STOPPED_REF,
        ["single_selected_pnt_lane_resolved_to_pcm_next_work_class_without_execution"],
        [],
        P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
    )


def _op05_status_reason_blocker_next(
    *,
    op04_present: bool,
    op04_valid: bool,
    op04_resolved: bool,
    next_work_class_ref: str,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op05_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op05_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("op05_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op05_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF,
            ["next_design_candidate_envelope_blocked_before_guard_without_downstream_promotion"],
            _dedupe_clean_refs(blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_DESIGN_CANDIDATE_ENVELOPE_REF,
        )

    repair_blockers: list[str] = []
    if not op04_present:
        repair_blockers.append("pcm_op04_next_work_class_resolver_material_missing")
    if op04_present and not op04_valid:
        repair_blockers.append("pcm_op04_next_work_class_resolver_contract_invalid")
    if op04_valid and not op04_resolved:
        repair_blockers.append("pcm_op04_next_work_class_not_resolved_for_envelope_materialization")
    if op04_resolved and next_work_class_ref not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS:
        repair_blockers.append("selected_pcm_next_work_class_ref_unknown_or_not_allowed")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF,
            ["next_design_candidate_envelope_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=340),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_DESIGN_CANDIDATE_ENVELOPE_INPUTS_REF,
        )

    if next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF,
            ["wait_hold_envelope_materialized_without_raw_evidence_request"],
            [],
            P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
        )
    if next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF,
            ["stop_envelope_materialized_without_next_design_promotion"],
            [],
            P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF,
        ["next_design_candidate_envelope_materialized_without_downstream_execution"],
        [],
        P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
    )


def build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver(
    pcm_op03_single_selected_lane_confirmation: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Resolve one confirmed PCM-OP03 lane to a next work class without execution."""

    session_id = _safe_review_session_id(review_session_id)
    op03 = pcm_op03_single_selected_lane_confirmation
    op03_present = isinstance(op03, Mapping)
    op03_valid = _op03_contract_valid(op03)
    op03_status_ref = _clean_ref(op03.get("pcm_op03_status_ref") if isinstance(op03, Mapping) else None, default="missing", max_length=300)
    op03_single_selected_lane_confirmed = bool(
        op03_valid
        and op03
        and op03.get("pcm_op03_single_selected_lane_confirmed_stopped") is True
        and op03.get("single_selected_pnt_lane_confirmed") is True
    )
    lane_ref = _clean_ref(op03.get("selected_pnt_lane_ref") if isinstance(op03, Mapping) else None, default="missing", max_length=260)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op03 or {}, path="pcm_op03")
    promotion_claims = _filter_allowed_prior_implemented_flag_paths(
        promotion_claims,
        allowed_implemented_keys=("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented"),
    )

    status_ref, reason_refs, blocker_refs, next_required_step = _op04_status_reason_blocker_next(
        op03_present=op03_present,
        op03_valid=op03_valid,
        op03_single_selected_lane_confirmed=op03_single_selected_lane_confirmed,
        lane_ref=lane_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    resolved = status_ref == P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_NEXT_WORK_CLASS_RESOLVED_STOPPED_REF

    if resolved:
        selected_pnt_status_ref = _clean_ref(op03.get("selected_pnt_status_ref"), default="missing", max_length=300)  # type: ignore[union-attr]
        selected_outcome_group_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[lane_ref]
        selected_post_nci_next_boundary_ref = _clean_ref(op03.get("selected_post_nci_next_boundary_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_kind_ref = _clean_ref(op03.get("selected_post_nci_next_boundary_kind_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_not_executed = bool(op03.get("selected_post_nci_next_boundary_not_executed") is True)  # type: ignore[union-attr]
        selected_handoff_or_stop_ref = _clean_ref(op03.get("selected_handoff_or_stop_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_handoff_or_stop_kind_ref = _clean_ref(op03.get("selected_handoff_or_stop_kind_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_handoff_or_stop_not_executed = bool(op03.get("selected_handoff_or_stop_not_executed") is True)  # type: ignore[union-attr]
        selected_pcm_next_work_class_ref = P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref]
        selected_pcm_next_boundary_ref = P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[lane_ref]
        selected_pcm_next_boundary_kind_ref = P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF_MAP[lane_ref]
        next_design_document_candidate_ref = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[lane_ref]
        next_design_document_allowed = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[lane_ref]
        manual_wait_required = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[lane_ref]
        manual_stop_required = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[lane_ref]
        repair_design_candidate = pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[lane_ref]
    else:
        selected_pnt_status_ref = status_ref
        selected_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_handoff_or_stop_ref = "missing"
        selected_handoff_or_stop_kind_ref = "missing"
        selected_handoff_or_stop_not_executed = False
        selected_pcm_next_work_class_ref = "missing"
        selected_pcm_next_boundary_ref = "missing"
        selected_pcm_next_boundary_kind_ref = "missing"
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False

    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_material_present": op03_present,
        "op03_contract_valid": op03_valid,
        "op03_schema_version": _clean_ref(op03.get("schema_version") if isinstance(op03, Mapping) else None, default="missing", max_length=260),
        "op03_material_ref": _clean_ref(op03.get("material_id") if isinstance(op03, Mapping) else None, default="missing", max_length=260),
        "op03_status_ref": op03_status_ref,
        "op03_next_required_step": _clean_ref(op03.get("next_required_step") if isinstance(op03, Mapping) else None, default="missing", max_length=360),
        "op03_single_selected_lane_confirmed_stopped": op03_single_selected_lane_confirmed,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": lane_ref if resolved else "missing",
        "selected_pnt_lane_ref_allowed": bool(resolved and lane_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS),
        "selected_post_nci_outcome_group_ref": selected_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_handoff_or_stop_not_executed,
        "selected_pcm_next_work_class_ref": selected_pcm_next_work_class_ref,
        "selected_pcm_next_work_class_ref_allowed": selected_pcm_next_work_class_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS,
        "selected_pcm_next_boundary_ref": selected_pcm_next_boundary_ref,
        "selected_pcm_next_boundary_kind_ref": selected_pcm_next_boundary_kind_ref,
        "selected_pcm_next_boundary_not_executed": bool(resolved),
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "allowed_pnt_lane_refs": list(P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS),
        "allowed_pnt_lane_ref_count": len(P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS),
        "allowed_next_work_class_refs": list(P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS),
        "allowed_next_work_class_ref_count": len(P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS),
        "lane_to_next_work_class_refs": dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS),
        "lane_to_selected_pcm_next_boundary_refs": dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP),
        "lane_to_selected_pcm_next_boundary_kind_refs": dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF_MAP),
        "lane_to_next_design_document_candidate_refs": dict(pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP),
        "pcm_op04_status_ref": status_ref,
        "bodyfree_next_work_class_resolver_status_ref": status_ref,
        "pcm_op04_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP04_ALLOWED_STATUS_REFS),
        "pcm_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP04_ALLOWED_STATUS_REFS),
        "pcm_op04_next_work_class_resolved_stopped": resolved,
        "pcm_op04_repair_required_for_next_work_class_inputs": status_ref == P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF,
        "pcm_op04_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF,
        "pcm_op04_reason_refs": _dedupe_clean_refs(reason_refs, max_length=360),
        "pcm_op04_reason_ref_count": len(_dedupe_clean_refs(reason_refs, max_length=360)),
        "pcm_op04_blocker_refs": _dedupe_clean_refs(blocker_refs, max_length=360),
        "pcm_op04_blocker_ref_count": len(_dedupe_clean_refs(blocker_refs, max_length=360)),
        "op04_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op04_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op04_input_body_like_value_path_refs": list(body_like_paths),
        "op04_input_body_like_value_path_count": len(body_like_paths),
        "op04_input_promotion_claim_refs": list(promotion_claims),
        "op04_input_promotion_claim_ref_count": len(promotion_claims),
        "op04_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op04_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op04_does_not_materialize_next_design_candidate_envelope": True,
        "pcm_op04_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op04_does_not_execute_selected_pcm_next_boundary": True,
        "pcm_op04_does_not_call_dhr_op05": True,
        "pcm_op04_does_not_call_dhr_op06": True,
        "pcm_op04_does_not_execute_dmd_r52_or_release": True,
        "pcm_op04_does_not_start_actual_review": True,
        "pcm_op04_does_not_request_raw_evidence": True,
        "pcm_op04_does_not_execute_repair": True,
        "pcm_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op04_does_not_materialize_p8_question_spec": True,
        "pcm_op04_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP04_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "pcm_op02_implemented": True,
        "pcm_op03_implemented": True,
        "pcm_op04_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP04 next work class resolver contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP04")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP04_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP04_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP04",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP04_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP04 implemented flag must be true after R4: {key}")
    if data.get("bodyfree_next_work_class_resolver_status_ref") != data.get("pcm_op04_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 status alias changed")
    if tuple(data.get("pcm_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 allowed status refs changed")
    for key in (
        "execution_allowed_here", "selected_pcm_next_boundary_execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP04 execution allowance changed: {key}")
    for key in (
        "pcm_op04_does_not_materialize_next_design_candidate_envelope", "pcm_op04_does_not_execute_selected_post_nci_next_boundary", "pcm_op04_does_not_execute_selected_pcm_next_boundary", "pcm_op04_does_not_call_dhr_op05", "pcm_op04_does_not_call_dhr_op06", "pcm_op04_does_not_execute_dmd_r52_or_release", "pcm_op04_does_not_start_actual_review", "pcm_op04_does_not_request_raw_evidence", "pcm_op04_does_not_execute_repair", "pcm_op04_does_not_start_p5_p6_p8_p7_or_release", "pcm_op04_does_not_change_api_db_rn_runtime_response_key", "pcm_op04_does_not_materialize_p8_question_spec", "pcm_op04_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP04 required true boundary changed: {key}")
    for field, count_field in (
        ("allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count"), ("allowed_next_work_class_refs", "allowed_next_work_class_ref_count"), ("pcm_op04_allowed_status_refs", "pcm_op04_allowed_status_ref_count"), ("pcm_op04_reason_refs", "pcm_op04_reason_ref_count"), ("pcm_op04_blocker_refs", "pcm_op04_blocker_ref_count"), ("op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count"), ("op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count"), ("op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count"), ("op04_input_no_touch_mutation_path_refs", "op04_input_no_touch_mutation_path_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP04 {count_field} changed")
    if tuple(data.get("allowed_pnt_lane_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 allowed lane refs changed")
    if tuple(data.get("allowed_next_work_class_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 allowed next work class refs changed")
    if data.get("lane_to_next_work_class_refs") != dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 lane to next work class map changed")
    if data.get("lane_to_selected_pcm_next_boundary_refs") != dict(P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 lane to selected PCM boundary map changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP04_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 not-yet steps changed")
    status_ref = data.get("pcm_op04_status_ref")
    branch_flags = [
        data.get("pcm_op04_next_work_class_resolved_stopped") is True,
        data.get("pcm_op04_repair_required_for_next_work_class_inputs") is True,
        data.get("pcm_op04_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PNT_PCM_OP04_ALLOWED_STATUS_REFS or sum(branch_flags) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 exactly one resolver status branch must be selected")
    if status_ref == P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_NEXT_WORK_CLASS_RESOLVED_STOPPED_REF:
        lane_ref = data.get("selected_pnt_lane_ref")
        if data.get("op03_contract_valid") is not True or data.get("op03_single_selected_lane_confirmed_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 resolved branch requires valid confirmed OP03")
        if lane_ref not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 resolved lane is not allowed")
        if data.get("selected_pcm_next_work_class_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 next work class changed")
        if data.get("selected_pcm_next_boundary_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 selected PCM boundary changed")
        if data.get("selected_pcm_next_boundary_kind_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 selected PCM boundary kind changed")
        if data.get("selected_pcm_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 resolved branch must keep selected PCM boundary non-executed")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True or data.get("selected_handoff_or_stop_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 resolved branch must keep upstream boundary non-executed")
        if data.get("next_design_document_candidate_ref") != pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 next design document candidate changed")
        if data.get("next_design_document_allowed") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 next design document allowed flag changed")
        if data.get("manual_wait_required") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 manual wait flag changed")
        if data.get("manual_stop_required") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 manual stop flag changed")
        if data.get("repair_design_candidate") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 repair design candidate flag changed")
        if data.get("pcm_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 resolved branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 resolved next step changed")
    else:
        if not data.get("pcm_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 non-resolved branch must carry blockers")
        if data.get("selected_pcm_next_boundary_not_executed") is not False:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 non-resolved branch cannot select a PCM boundary")
        if status_ref == P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF and data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_WORK_CLASS_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 repair next step changed")
        if status_ref == P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF and data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_WORK_CLASS_RESOLVER_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_PNT_PCM_OP04_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF:
        for field in ("op04_input_forbidden_payload_key_path_refs", "op04_input_body_like_value_path_refs", "op04_input_promotion_claim_refs", "op04_input_no_touch_mutation_path_refs"):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP04 non-blocked branch cannot carry scan blockers")
    return True


def build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization(
    pcm_op04_next_work_class_resolver: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Materialize a body-free next-design / wait / stop envelope without execution."""

    session_id = _safe_review_session_id(review_session_id)
    op04 = pcm_op04_next_work_class_resolver
    op04_present = isinstance(op04, Mapping)
    op04_valid = _op04_contract_valid(op04)
    op04_status_ref = _clean_ref(op04.get("pcm_op04_status_ref") if isinstance(op04, Mapping) else None, default="missing", max_length=300)
    op04_resolved = bool(op04_valid and op04 and op04.get("pcm_op04_next_work_class_resolved_stopped") is True)
    next_work_class_ref = _clean_ref(op04.get("selected_pcm_next_work_class_ref") if isinstance(op04, Mapping) else None, default="missing", max_length=260)
    lane_ref = _clean_ref(op04.get("selected_pnt_lane_ref") if isinstance(op04, Mapping) else None, default="missing", max_length=260)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op04 or {}, path="pcm_op04")
    promotion_claims = _filter_allowed_prior_implemented_flag_paths(
        promotion_claims,
        allowed_implemented_keys=("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented"),
    )
    status_ref, reason_refs, blocker_refs, next_required_step = _op05_status_reason_blocker_next(
        op04_present=op04_present,
        op04_valid=op04_valid,
        op04_resolved=op04_resolved,
        next_work_class_ref=next_work_class_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    materialized = status_ref in (
        P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF,
    )

    if materialized:
        selected_pnt_status_ref = _clean_ref(op04.get("selected_pnt_status_ref"), default="missing", max_length=300)  # type: ignore[union-attr]
        selected_outcome_group_ref = _clean_ref(op04.get("selected_post_nci_outcome_group_ref"), default="missing", max_length=260)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_ref = _clean_ref(op04.get("selected_post_nci_next_boundary_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_kind_ref = _clean_ref(op04.get("selected_post_nci_next_boundary_kind_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_not_executed = bool(op04.get("selected_post_nci_next_boundary_not_executed") is True)  # type: ignore[union-attr]
        selected_handoff_or_stop_ref = _clean_ref(op04.get("selected_handoff_or_stop_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_handoff_or_stop_kind_ref = _clean_ref(op04.get("selected_handoff_or_stop_kind_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_handoff_or_stop_not_executed = bool(op04.get("selected_handoff_or_stop_not_executed") is True)  # type: ignore[union-attr]
        selected_pcm_next_boundary_ref = _clean_ref(op04.get("selected_pcm_next_boundary_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_pcm_next_boundary_kind_ref = _clean_ref(op04.get("selected_pcm_next_boundary_kind_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_pcm_next_boundary_not_executed = bool(op04.get("selected_pcm_next_boundary_not_executed") is True)  # type: ignore[union-attr]
        next_design_document_candidate_ref = _clean_ref(op04.get("next_design_document_candidate_ref"), default="missing", max_length=460)  # type: ignore[union-attr]
        next_design_document_allowed = bool(op04.get("next_design_document_allowed") is True)  # type: ignore[union-attr]
        manual_wait_required = bool(op04.get("manual_wait_required") is True)  # type: ignore[union-attr]
        manual_stop_required = bool(op04.get("manual_stop_required") is True)  # type: ignore[union-attr]
        repair_design_candidate = bool(op04.get("repair_design_candidate") is True)  # type: ignore[union-attr]
    else:
        selected_pnt_status_ref = status_ref
        selected_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_handoff_or_stop_ref = "missing"
        selected_handoff_or_stop_kind_ref = "missing"
        selected_handoff_or_stop_not_executed = False
        lane_ref = "missing"
        selected_pcm_next_boundary_ref = "missing"
        selected_pcm_next_boundary_kind_ref = "missing"
        selected_pcm_next_boundary_not_executed = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False

    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_material_present": op04_present,
        "op04_contract_valid": op04_valid,
        "op04_schema_version": _clean_ref(op04.get("schema_version") if isinstance(op04, Mapping) else None, default="missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id") if isinstance(op04, Mapping) else None, default="missing", max_length=260),
        "op04_status_ref": op04_status_ref,
        "op04_next_required_step": _clean_ref(op04.get("next_required_step") if isinstance(op04, Mapping) else None, default="missing", max_length=360),
        "op04_next_work_class_resolved_stopped": op04_resolved,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": lane_ref if materialized else "missing",
        "selected_post_nci_outcome_group_ref": selected_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_handoff_or_stop_not_executed,
        "selected_pcm_next_work_class_ref": next_work_class_ref if materialized else "missing",
        "selected_pcm_next_work_class_ref_allowed": next_work_class_ref in P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS,
        "selected_pcm_next_boundary_ref": selected_pcm_next_boundary_ref,
        "selected_pcm_next_boundary_kind_ref": selected_pcm_next_boundary_kind_ref,
        "selected_pcm_next_boundary_not_executed": selected_pcm_next_boundary_not_executed,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "selected_pcm_next_boundary_envelope_materialized_here": materialized,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "pcm_op05_dhr_op05_design_candidate_envelope_materialized_without_call": bool(materialized and lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF),
        "pcm_op05_retry_start_design_candidate_envelope_materialized_without_actual_review": bool(materialized and lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_RETRY_OR_START_ACTUAL_LOCAL_ONLY_REVIEW_ROUTE_CANDIDATE_REF),
        "pcm_op05_repair_design_candidate_envelope_materialized_without_repair_execution": bool(materialized and lane_ref == P7_R54_AHR_POST_PNT_PCM_LANE_REPAIR_RDB_CANDIDATE_OR_UPSTREAM_RESULT_CANDIDATE_REF),
        "pcm_op05_wait_hold_envelope_materialized_without_raw_evidence": bool(materialized and next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF),
        "pcm_op05_stop_envelope_materialized_without_next_design_promotion": bool(materialized and next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF),
        "pcm_op05_status_ref": status_ref,
        "bodyfree_next_design_candidate_envelope_status_ref": status_ref,
        "pcm_op05_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP05_ALLOWED_STATUS_REFS),
        "pcm_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP05_ALLOWED_STATUS_REFS),
        "pcm_op05_next_design_candidate_envelope_materialized_stopped": status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF,
        "pcm_op05_wait_hold_envelope_materialized_stopped": status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF,
        "pcm_op05_stop_envelope_materialized_stopped": status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF,
        "pcm_op05_repair_required_for_next_work_class_inputs": status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF,
        "pcm_op05_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF,
        "pcm_op05_reason_refs": _dedupe_clean_refs(reason_refs, max_length=360),
        "pcm_op05_reason_ref_count": len(_dedupe_clean_refs(reason_refs, max_length=360)),
        "pcm_op05_blocker_refs": _dedupe_clean_refs(blocker_refs, max_length=360),
        "pcm_op05_blocker_ref_count": len(_dedupe_clean_refs(blocker_refs, max_length=360)),
        "op05_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op05_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op05_input_body_like_value_path_refs": list(body_like_paths),
        "op05_input_body_like_value_path_count": len(body_like_paths),
        "op05_input_promotion_claim_refs": list(promotion_claims),
        "op05_input_promotion_claim_ref_count": len(promotion_claims),
        "op05_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op05_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op05_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op05_does_not_execute_selected_pcm_next_boundary": True,
        "pcm_op05_does_not_call_dhr_op05": True,
        "pcm_op05_does_not_call_dhr_op06": True,
        "pcm_op05_does_not_execute_dmd_r52_or_release": True,
        "pcm_op05_does_not_start_actual_review": True,
        "pcm_op05_does_not_request_raw_evidence": True,
        "pcm_op05_does_not_execute_repair": True,
        "pcm_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op05_does_not_materialize_p8_question_spec": True,
        "pcm_op05_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP05_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "pcm_op02_implemented": True,
        "pcm_op03_implemented": True,
        "pcm_op04_implemented": True,
        "pcm_op05_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP05 next design candidate / hold / stop envelope materialization contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP05")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP05_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP05_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP05",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP05_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP05 implemented flag must be true after R4: {key}")
    if data.get("bodyfree_next_design_candidate_envelope_status_ref") != data.get("pcm_op05_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 status alias changed")
    if tuple(data.get("pcm_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 allowed status refs changed")
    for key in (
        "execution_allowed_here", "selected_pcm_next_boundary_execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP05 execution allowance changed: {key}")
    for key in (
        "pcm_op05_does_not_execute_selected_post_nci_next_boundary", "pcm_op05_does_not_execute_selected_pcm_next_boundary", "pcm_op05_does_not_call_dhr_op05", "pcm_op05_does_not_call_dhr_op06", "pcm_op05_does_not_execute_dmd_r52_or_release", "pcm_op05_does_not_start_actual_review", "pcm_op05_does_not_request_raw_evidence", "pcm_op05_does_not_execute_repair", "pcm_op05_does_not_start_p5_p6_p8_p7_or_release", "pcm_op05_does_not_change_api_db_rn_runtime_response_key", "pcm_op05_does_not_materialize_p8_question_spec", "pcm_op05_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP05 required true boundary changed: {key}")
    for field, count_field in (
        ("pcm_op05_allowed_status_refs", "pcm_op05_allowed_status_ref_count"), ("pcm_op05_reason_refs", "pcm_op05_reason_ref_count"), ("pcm_op05_blocker_refs", "pcm_op05_blocker_ref_count"), ("op05_input_forbidden_payload_key_path_refs", "op05_input_forbidden_payload_key_path_count"), ("op05_input_body_like_value_path_refs", "op05_input_body_like_value_path_count"), ("op05_input_promotion_claim_refs", "op05_input_promotion_claim_ref_count"), ("op05_input_no_touch_mutation_path_refs", "op05_input_no_touch_mutation_path_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP05 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP05_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PNT_PCM_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 not-yet steps changed")
    status_ref = data.get("pcm_op05_status_ref")
    branch_flags = [
        data.get("pcm_op05_next_design_candidate_envelope_materialized_stopped") is True,
        data.get("pcm_op05_wait_hold_envelope_materialized_stopped") is True,
        data.get("pcm_op05_stop_envelope_materialized_stopped") is True,
        data.get("pcm_op05_repair_required_for_next_work_class_inputs") is True,
        data.get("pcm_op05_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PNT_PCM_OP05_ALLOWED_STATUS_REFS or sum(branch_flags) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 exactly one envelope status branch must be selected")
    materialized = status_ref in (
        P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF,
    )
    if materialized:
        lane_ref = data.get("selected_pnt_lane_ref")
        next_work_class_ref = data.get("selected_pcm_next_work_class_ref")
        if data.get("op04_contract_valid") is not True or data.get("op04_next_work_class_resolved_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 materialized branch requires valid resolved OP04")
        if lane_ref not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 materialized lane is not allowed")
        if next_work_class_ref != P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 next work class changed")
        if data.get("selected_pcm_next_boundary_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 selected PCM boundary changed")
        if data.get("selected_pcm_next_boundary_not_executed") is not True or data.get("selected_pcm_next_boundary_envelope_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 selected PCM envelope must materialize without execution")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True or data.get("selected_handoff_or_stop_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 upstream boundary must stay non-executed")
        if data.get("next_design_document_candidate_ref") != pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 next design document candidate changed")
        if data.get("next_design_document_allowed") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 next design document allowed flag changed")
        if data.get("manual_wait_required") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 manual wait flag changed")
        if data.get("manual_stop_required") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 manual stop flag changed")
        if data.get("repair_design_candidate") is not pnt.P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 repair design candidate flag changed")
        if next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF and status_ref != P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_NEXT_DESIGN_CANDIDATE_ENVELOPE_MATERIALIZED_STOPPED_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 next design branch status changed")
        if next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF and status_ref != P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_WAIT_HOLD_ENVELOPE_MATERIALIZED_STOPPED_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 wait branch status changed")
        if next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF and status_ref != P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_STOP_ENVELOPE_MATERIALIZED_STOPPED_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 stop branch status changed")
        if data.get("pcm_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 materialized branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 materialized next step changed")
    else:
        if not data.get("pcm_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 non-materialized branch must carry blockers")
        if data.get("selected_pcm_next_boundary_envelope_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 non-materialized branch cannot materialize envelope")
        if status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF and data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_NEXT_DESIGN_CANDIDATE_ENVELOPE_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 repair next step changed")
        if status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF and data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_NEXT_DESIGN_CANDIDATE_ENVELOPE_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF:
        for field in ("op05_input_forbidden_payload_key_path_refs", "op05_input_body_like_value_path_refs", "op05_input_promotion_claim_refs", "op05_input_no_touch_mutation_path_refs"):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP05 non-blocked branch cannot carry scan blockers")
    return True


def _op05_contract_valid(op05: Mapping[str, Any] | None) -> bool:
    if not isinstance(op05, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract(op05) is True
    except ValueError:
        return False


def _op06_status_reason_blocker_next(
    *,
    op05_present: bool,
    op05_valid: bool,
    op05_status_ref: str,
    op05_envelope_materialized_stopped: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op06_guard_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op06_guard_body_like_value_detected")
    if promotion_claims:
        blockers.append("op06_guard_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op06_guard_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op05_status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_BLOCKED_NEXT_WORK_CLASS_PROMOTION_AUTORUN_REF:
        blockers.append("pcm_op05_envelope_blocked_before_bodyfree_guard")
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_BLOCKED_GUARD_REF,
            ["bodyfree_no_touch_no_promotion_guard_blocked_without_downstream_execution"],
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_REF,
        )

    repair_blockers: list[str] = []
    if not op05_present:
        repair_blockers.append("pcm_op05_next_design_candidate_envelope_material_missing")
    elif not op05_valid:
        repair_blockers.append("pcm_op05_next_design_candidate_envelope_contract_invalid")
    if op05_status_ref == P7_R54_AHR_POST_PNT_PCM_OP05_STATUS_REPAIR_REQUIRED_FOR_NEXT_WORK_CLASS_INPUTS_REF:
        repair_blockers.append("pcm_op05_envelope_repair_required_before_guard")
    if op05_present and op05_valid and not op05_envelope_materialized_stopped:
        repair_blockers.append("pcm_op05_envelope_not_materialized_for_bodyfree_guard")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF,
            ["bodyfree_no_touch_no_promotion_guard_inputs_require_repair_without_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=360),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_INPUTS_REF,
        )

    return (
        P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_GUARD_PASSED_REF,
        ["bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed_for_op05_envelope"],
        [],
        P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
    )


def build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(
    op05_next_design_candidate_envelope_material: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PCM-OP06 body-free/no-touch/no-promotion/no-auto-execution guard material."""

    session_id = _safe_review_session_id(review_session_id)
    op05 = op05_next_design_candidate_envelope_material
    op05_present = isinstance(op05, Mapping)
    op05_valid = _op05_contract_valid(op05 if isinstance(op05, Mapping) else None)
    op05_status_ref = _clean_ref(op05.get("pcm_op05_status_ref") if isinstance(op05, Mapping) else None, default="missing", max_length=300)
    op05_next_required_step = _clean_ref(op05.get("next_required_step") if isinstance(op05, Mapping) else None, default="missing", max_length=420)
    op05_envelope_materialized_stopped = bool(
        op05_valid
        and op05_status_ref in P7_R54_AHR_POST_PNT_PCM_OP05_ALLOWED_STATUS_REFS
        and op05.get("selected_pcm_next_boundary_envelope_materialized_here") is True  # type: ignore[union-attr]
        and op05.get("selected_pcm_next_boundary_not_executed") is True  # type: ignore[union-attr]
    )
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op05 or {}, path="pcm_op05")
    promotion_claims = _filter_allowed_prior_implemented_flag_paths(
        promotion_claims,
        allowed_implemented_keys=(
            "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented",
            "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented",
        ),
    )
    status_ref, reason_refs, blocker_refs, next_required_step = _op06_status_reason_blocker_next(
        op05_present=op05_present,
        op05_valid=op05_valid,
        op05_status_ref=op05_status_ref,
        op05_envelope_materialized_stopped=op05_envelope_materialized_stopped,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    guard_passed = status_ref == P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_GUARD_PASSED_REF

    if guard_passed and isinstance(op05, Mapping):
        selected_pnt_status_ref = _clean_ref(op05.get("selected_pnt_status_ref"), default="missing", max_length=300)
        selected_pnt_lane_ref = _clean_ref(op05.get("selected_pnt_lane_ref"), default="missing", max_length=300)
        selected_post_nci_outcome_group_ref = _clean_ref(op05.get("selected_post_nci_outcome_group_ref"), default="missing", max_length=260)
        selected_post_nci_next_boundary_ref = _clean_ref(op05.get("selected_post_nci_next_boundary_ref"), default="missing", max_length=420)
        selected_post_nci_next_boundary_kind_ref = _clean_ref(op05.get("selected_post_nci_next_boundary_kind_ref"), default="missing", max_length=420)
        selected_post_nci_next_boundary_not_executed = bool(op05.get("selected_post_nci_next_boundary_not_executed") is True)
        selected_handoff_or_stop_ref = _clean_ref(op05.get("selected_handoff_or_stop_ref"), default="missing", max_length=420)
        selected_handoff_or_stop_kind_ref = _clean_ref(op05.get("selected_handoff_or_stop_kind_ref"), default="missing", max_length=420)
        selected_handoff_or_stop_not_executed = bool(op05.get("selected_handoff_or_stop_not_executed") is True)
        selected_pcm_next_work_class_ref = _clean_ref(op05.get("selected_pcm_next_work_class_ref"), default="missing", max_length=260)
        selected_pcm_next_boundary_ref = _clean_ref(op05.get("selected_pcm_next_boundary_ref"), default="missing", max_length=420)
        selected_pcm_next_boundary_kind_ref = _clean_ref(op05.get("selected_pcm_next_boundary_kind_ref"), default="missing", max_length=420)
        selected_pcm_next_boundary_not_executed = bool(op05.get("selected_pcm_next_boundary_not_executed") is True)
        selected_pcm_next_boundary_envelope_materialized_here = bool(op05.get("selected_pcm_next_boundary_envelope_materialized_here") is True)
        next_design_document_candidate_ref = _clean_ref(op05.get("next_design_document_candidate_ref"), default="missing", max_length=420)
        next_design_document_allowed = bool(op05.get("next_design_document_allowed") is True)
        manual_wait_required = bool(op05.get("manual_wait_required") is True)
        manual_stop_required = bool(op05.get("manual_stop_required") is True)
        repair_design_candidate = bool(op05.get("repair_design_candidate") is True)
    else:
        selected_pnt_status_ref = status_ref
        selected_pnt_lane_ref = "missing"
        selected_post_nci_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_handoff_or_stop_ref = "missing"
        selected_handoff_or_stop_kind_ref = "missing"
        selected_handoff_or_stop_not_executed = False
        selected_pcm_next_work_class_ref = "missing"
        selected_pcm_next_boundary_ref = "missing"
        selected_pcm_next_boundary_kind_ref = "missing"
        selected_pcm_next_boundary_not_executed = False
        selected_pcm_next_boundary_envelope_materialized_here = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False

    blocker_refs = _dedupe_clean_refs(blocker_refs, max_length=360)
    reason_refs = _dedupe_clean_refs(reason_refs, max_length=360)
    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_material_present": op05_present,
        "op05_contract_valid": op05_valid,
        "op05_schema_version": _clean_ref(op05.get("schema_version") if isinstance(op05, Mapping) else None, default="missing", max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id") if isinstance(op05, Mapping) else None, default="missing", max_length=300),
        "op05_status_ref": op05_status_ref,
        "op05_next_required_step": op05_next_required_step,
        "op05_envelope_materialized_stopped": op05_envelope_materialized_stopped,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": selected_pnt_lane_ref,
        "selected_post_nci_outcome_group_ref": selected_post_nci_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_handoff_or_stop_not_executed,
        "selected_pcm_next_work_class_ref": selected_pcm_next_work_class_ref,
        "selected_pcm_next_boundary_ref": selected_pcm_next_boundary_ref,
        "selected_pcm_next_boundary_kind_ref": selected_pcm_next_boundary_kind_ref,
        "selected_pcm_next_boundary_not_executed": selected_pcm_next_boundary_not_executed,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "selected_pcm_next_boundary_envelope_materialized_here": selected_pcm_next_boundary_envelope_materialized_here,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "execution_allowed_here": False,
        "guard_subject_step_refs": list(P7_R54_AHR_POST_PNT_PCM_OP05_IMPLEMENTED_STEPS),
        "guard_subject_step_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP05_IMPLEMENTED_STEPS),
        "guard_scope_ref": "pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_over_op00_op05_and_input_material",
        "validation_commands_executed_here": False,
        "pytest_executed_here": False,
        "pcm_target_tests_executed_here": False,
        "selected_regression_executed_here": False,
        "compileall_executed_here": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "pcm_op06_status_ref": status_ref,
        "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref": status_ref,
        "pcm_op06_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP06_ALLOWED_STATUS_REFS),
        "pcm_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP06_ALLOWED_STATUS_REFS),
        "pcm_op06_guard_passed": guard_passed,
        "pcm_op06_repair_required_for_guard_inputs": status_ref == P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF,
        "pcm_op06_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_BLOCKED_GUARD_REF,
        "pcm_op06_reason_refs": reason_refs,
        "pcm_op06_reason_ref_count": len(reason_refs),
        "pcm_op06_blocker_refs": blocker_refs,
        "pcm_op06_blocker_ref_count": len(blocker_refs),
        "op06_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op06_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op06_input_body_like_value_path_refs": list(body_like_paths),
        "op06_input_body_like_value_path_count": len(body_like_paths),
        "op06_input_promotion_claim_refs": list(promotion_claims),
        "op06_input_promotion_claim_ref_count": len(promotion_claims),
        "op06_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op06_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op06_does_not_execute_validation_commands": True,
        "pcm_op06_does_not_claim_full_backend_rn_or_real_device_green": True,
        "pcm_op06_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op06_does_not_execute_selected_pcm_next_boundary": True,
        "pcm_op06_does_not_call_dhr_op05": True,
        "pcm_op06_does_not_call_dhr_op06": True,
        "pcm_op06_does_not_execute_dmd_r52_or_release": True,
        "pcm_op06_does_not_start_actual_review": True,
        "pcm_op06_does_not_request_raw_evidence": True,
        "pcm_op06_does_not_execute_repair": True,
        "pcm_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op06_does_not_materialize_p8_question_spec": True,
        "pcm_op06_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP06_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "pcm_op02_implemented": True,
        "pcm_op03_implemented": True,
        "pcm_op04_implemented": True,
        "pcm_op05_implemented": True,
        "pcm_op06_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP06 guard contract without executing downstream work."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP06")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP06_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP06_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP06",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP06_REQUIRED_FALSE_FLAG_REFS,
    )
    if data.get("bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref") != data.get("pcm_op06_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 status alias mismatch")
    if tuple(data.get("pcm_op06_allowed_status_refs", ())) != P7_R54_AHR_POST_PNT_PCM_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 allowed status refs mismatch")
    if data.get("pcm_op06_allowed_status_ref_count") != len(P7_R54_AHR_POST_PNT_PCM_OP06_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 allowed status count mismatch")
    status_ref = data.get("pcm_op06_status_ref")
    if status_ref not in P7_R54_AHR_POST_PNT_PCM_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 unknown status")
    for key in (
        "validation_commands_executed_here", "pytest_executed_here", "pcm_target_tests_executed_here",
        "selected_regression_executed_here", "compileall_executed_here", "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
        "selected_pcm_next_boundary_execution_allowed_here", "execution_allowed_here", "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here",
        "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP06 no-execution/no-claim flag changed: {key}")
    for key in (
        "pcm_op06_does_not_execute_validation_commands", "pcm_op06_does_not_claim_full_backend_rn_or_real_device_green",
        "pcm_op06_does_not_execute_selected_post_nci_next_boundary", "pcm_op06_does_not_execute_selected_pcm_next_boundary",
        "pcm_op06_does_not_call_dhr_op05", "pcm_op06_does_not_call_dhr_op06", "pcm_op06_does_not_execute_dmd_r52_or_release",
        "pcm_op06_does_not_start_actual_review", "pcm_op06_does_not_request_raw_evidence", "pcm_op06_does_not_execute_repair",
        "pcm_op06_does_not_start_p5_p6_p8_p7_or_release", "pcm_op06_does_not_change_api_db_rn_runtime_response_key",
        "pcm_op06_does_not_materialize_p8_question_spec", "pcm_op06_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP06 non-execution statement missing: {key}")
    for list_key, count_key in (
        ("guard_subject_step_refs", "guard_subject_step_ref_count"),
        ("pcm_op06_reason_refs", "pcm_op06_reason_ref_count"),
        ("pcm_op06_blocker_refs", "pcm_op06_blocker_ref_count"),
        ("op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count"),
        ("op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count"),
        ("op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count"),
        ("op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_key) != len(tuple(data.get(list_key, ()))):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP06 count mismatch: {list_key}")
    if tuple(data.get("guard_subject_step_refs", ())) != P7_R54_AHR_POST_PNT_PCM_OP05_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 guard subject steps mismatch")
    if tuple(data.get("claim_boundary_refs", ())) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 claim boundary refs mismatch")
    if tuple(data.get("not_claimed_boundary_refs", ())) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 not-claimed boundary refs mismatch")
    if tuple(data.get("fixed_non_promotion_refs", ())) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 fixed non-promotion refs mismatch")
    if tuple(data.get("implemented_steps", ())) != P7_R54_AHR_POST_PNT_PCM_OP06_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_steps", ())) != P7_R54_AHR_POST_PNT_PCM_OP06_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 not-yet steps mismatch")
    for key in ("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP06 implemented flag must be true: {key}")
    branch_flags = (
        data.get("pcm_op06_guard_passed") is True,
        data.get("pcm_op06_repair_required_for_guard_inputs") is True,
        data.get("pcm_op06_bodyfree_leak_promotion_or_autorun_blocked") is True,
    )
    if sum(1 for flag in branch_flags if flag) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 must choose exactly one branch")
    blocker_count = int(data.get("pcm_op06_blocker_ref_count") or 0)
    if status_ref == P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_GUARD_PASSED_REF:
        if data.get("op05_contract_valid") is not True or data.get("op05_envelope_materialized_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 guard pass requires valid OP05 envelope")
        if data.get("selected_pnt_lane_ref") not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 guard pass requires allowed lane")
        lane_ref = str(data.get("selected_pnt_lane_ref"))
        if data.get("selected_pcm_next_work_class_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 next work class mismatch")
        if data.get("selected_pcm_next_boundary_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 selected PCM boundary mismatch")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True or data.get("selected_handoff_or_stop_not_executed") is not True or data.get("selected_pcm_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 selected boundaries must remain not executed")
        if data.get("selected_pcm_next_boundary_envelope_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 requires OP05 envelope materialized before guard pass")
        if blocker_count != 0 or data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 guard pass must continue only to OP07 with no blockers")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_INPUTS_REF or blocker_count == 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 repair branch must stop with repair blockers")
    else:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_REF or blocker_count == 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP06 blocked branch must stop with blockers")
    return True


def _op06_contract_valid(op06: Mapping[str, Any] | None) -> bool:
    if not isinstance(op06, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    except ValueError:
        return False


def _op07_status_reason_blocker_next(
    *,
    op06_present: bool,
    op06_valid: bool,
    op06_status_ref: str,
    op06_guard_passed: bool,
    selected_pcm_next_work_class_ref: str,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op07_result_memo_draft_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op07_result_memo_draft_body_like_value_detected")
    if promotion_claims:
        blockers.append("op07_result_memo_draft_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op07_result_memo_draft_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op06_status_ref == P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_BLOCKED_GUARD_REF:
        blockers.append("pcm_op06_guard_blocked_before_result_memo_draft")
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_BLOCKED_RESULT_MEMO_DRAFT_REF,
            ["validation_plan_result_memo_draft_blocked_without_execution"],
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_RESULT_MEMO_DRAFT_REF,
        )

    repair_blockers: list[str] = []
    if not op06_present:
        repair_blockers.append("pcm_op06_guard_material_missing")
    elif not op06_valid:
        repair_blockers.append("pcm_op06_guard_contract_invalid")
    if op06_status_ref == P7_R54_AHR_POST_PNT_PCM_OP06_STATUS_REPAIR_REQUIRED_FOR_GUARD_INPUTS_REF:
        repair_blockers.append("pcm_op06_guard_repair_required_before_result_memo_draft")
    if op06_present and op06_valid and not op06_guard_passed:
        repair_blockers.append("pcm_op06_guard_not_passed_for_result_memo_draft")
    if selected_pcm_next_work_class_ref not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS:
        repair_blockers.append("pcm_op06_selected_next_work_class_missing_or_unknown")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF,
            ["validation_plan_result_memo_draft_inputs_require_repair_without_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=360),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_RESULT_MEMO_DRAFT_INPUTS_REF,
        )

    if selected_pcm_next_work_class_ref in (P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF, P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF):
        return (
            P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
            ["validation_plan_wait_or_stop_result_memo_draft_materialized_without_execution"],
            [],
            P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        ["validation_plan_next_design_candidate_result_memo_draft_materialized_without_execution"],
        [],
        P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
    )


def build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material(
    op06_bodyfree_guard_material: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PCM-OP07 validation plan and body-free result memo draft material."""

    session_id = _safe_review_session_id(review_session_id)
    op06 = op06_bodyfree_guard_material
    op06_present = isinstance(op06, Mapping)
    op06_valid = _op06_contract_valid(op06 if isinstance(op06, Mapping) else None)
    op06_status_ref = _clean_ref(op06.get("pcm_op06_status_ref") if isinstance(op06, Mapping) else None, default="missing", max_length=300)
    op06_next_required_step = _clean_ref(op06.get("next_required_step") if isinstance(op06, Mapping) else None, default="missing", max_length=420)
    op06_guard_passed = bool(op06_valid and op06.get("pcm_op06_guard_passed") is True) if isinstance(op06, Mapping) else False
    selected_pcm_next_work_class_ref = _clean_ref(op06.get("selected_pcm_next_work_class_ref") if isinstance(op06, Mapping) else None, default="missing", max_length=260)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op06 or {}, path="pcm_op06")
    promotion_claims = _filter_allowed_prior_implemented_flag_paths(
        promotion_claims,
        allowed_implemented_keys=(
            "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented",
            "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented",
        ),
    )
    status_ref, reason_refs, blocker_refs, next_required_step = _op07_status_reason_blocker_next(
        op06_present=op06_present,
        op06_valid=op06_valid,
        op06_status_ref=op06_status_ref,
        op06_guard_passed=op06_guard_passed,
        selected_pcm_next_work_class_ref=selected_pcm_next_work_class_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    materialized = status_ref in (
        P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    )

    if materialized and isinstance(op06, Mapping):
        selected_pnt_status_ref = _clean_ref(op06.get("selected_pnt_status_ref"), default="missing", max_length=300)
        selected_pnt_lane_ref = _clean_ref(op06.get("selected_pnt_lane_ref"), default="missing", max_length=300)
        selected_post_nci_outcome_group_ref = _clean_ref(op06.get("selected_post_nci_outcome_group_ref"), default="missing", max_length=260)
        selected_post_nci_next_boundary_ref = _clean_ref(op06.get("selected_post_nci_next_boundary_ref"), default="missing", max_length=420)
        selected_post_nci_next_boundary_kind_ref = _clean_ref(op06.get("selected_post_nci_next_boundary_kind_ref"), default="missing", max_length=420)
        selected_post_nci_next_boundary_not_executed = bool(op06.get("selected_post_nci_next_boundary_not_executed") is True)
        selected_handoff_or_stop_ref = _clean_ref(op06.get("selected_handoff_or_stop_ref"), default="missing", max_length=420)
        selected_handoff_or_stop_kind_ref = _clean_ref(op06.get("selected_handoff_or_stop_kind_ref"), default="missing", max_length=420)
        selected_handoff_or_stop_not_executed = bool(op06.get("selected_handoff_or_stop_not_executed") is True)
        selected_pcm_next_boundary_ref = _clean_ref(op06.get("selected_pcm_next_boundary_ref"), default="missing", max_length=420)
        selected_pcm_next_boundary_kind_ref = _clean_ref(op06.get("selected_pcm_next_boundary_kind_ref"), default="missing", max_length=420)
        selected_pcm_next_boundary_not_executed = bool(op06.get("selected_pcm_next_boundary_not_executed") is True)
        selected_pcm_next_boundary_envelope_materialized_here = bool(op06.get("selected_pcm_next_boundary_envelope_materialized_here") is True)
        next_design_document_candidate_ref = _clean_ref(op06.get("next_design_document_candidate_ref"), default="missing", max_length=420)
        next_design_document_allowed = bool(op06.get("next_design_document_allowed") is True)
        manual_wait_required = bool(op06.get("manual_wait_required") is True)
        manual_stop_required = bool(op06.get("manual_stop_required") is True)
        repair_design_candidate = bool(op06.get("repair_design_candidate") is True)
    else:
        selected_pnt_status_ref = status_ref
        selected_pnt_lane_ref = "missing"
        selected_post_nci_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_handoff_or_stop_ref = "missing"
        selected_handoff_or_stop_kind_ref = "missing"
        selected_handoff_or_stop_not_executed = False
        selected_pcm_next_work_class_ref = "missing"
        selected_pcm_next_boundary_ref = "missing"
        selected_pcm_next_boundary_kind_ref = "missing"
        selected_pcm_next_boundary_not_executed = False
        selected_pcm_next_boundary_envelope_materialized_here = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False

    reason_refs = _dedupe_clean_refs(reason_refs, max_length=360)
    blocker_refs = _dedupe_clean_refs(blocker_refs, max_length=360)
    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_material_present": op06_present,
        "op06_contract_valid": op06_valid,
        "op06_schema_version": _clean_ref(op06.get("schema_version") if isinstance(op06, Mapping) else None, default="missing", max_length=260),
        "op06_material_ref": _clean_ref(op06.get("material_id") if isinstance(op06, Mapping) else None, default="missing", max_length=300),
        "op06_status_ref": op06_status_ref,
        "op06_next_required_step": op06_next_required_step,
        "op06_guard_passed": op06_guard_passed,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": selected_pnt_lane_ref,
        "selected_post_nci_outcome_group_ref": selected_post_nci_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_handoff_or_stop_not_executed,
        "selected_pcm_next_work_class_ref": selected_pcm_next_work_class_ref,
        "selected_pcm_next_boundary_ref": selected_pcm_next_boundary_ref,
        "selected_pcm_next_boundary_kind_ref": selected_pcm_next_boundary_kind_ref,
        "selected_pcm_next_boundary_not_executed": selected_pcm_next_boundary_not_executed,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "selected_pcm_next_boundary_envelope_materialized_here": selected_pcm_next_boundary_envelope_materialized_here,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "execution_allowed_here": False,
        "validation_plan_ref": "pcm_op07_target_selected_regression_compileall_validation_plan_refs_without_execution",
        "validation_plan_recorded": materialized,
        "validation_plan_bodyfree": True,
        "validation_plan_execution_allowed_here": False,
        "validation_commands_executed_here": False,
        "pytest_executed_here": False,
        "pcm_target_tests_executed_here": False,
        "selected_regression_executed_here": False,
        "compileall_executed_here": False,
        "target_test_ref_refs": list(P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS),
        "target_test_ref_count": len(P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS),
        "selected_regression_test_ref_refs": list(P7_R54_AHR_POST_PNT_PCM_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_count": len(P7_R54_AHR_POST_PNT_PCM_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_ref_refs": list(P7_R54_AHR_POST_PNT_PCM_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_count": len(P7_R54_AHR_POST_PNT_PCM_COMPILEALL_TARGET_REF_REFS),
        "validation_command_summary_refs": list(P7_R54_AHR_POST_PNT_PCM_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_VALIDATION_COMMAND_SUMMARY_REFS),
        "target_test_result_status_ref": "pcm_op07_target_test_plan_recorded_not_executed_here",
        "selected_regression_result_status_ref": "pcm_op07_selected_regression_plan_recorded_not_executed_here",
        "compileall_result_status_ref": "pcm_op07_compileall_plan_recorded_not_executed_here",
        "post_pnt_closed_material_confirmation_result_memo_draft_ref": "pcm_op07_post_pnt_closed_material_confirmation_result_memo_draft_bodyfree_without_closure",
        "post_pnt_closed_material_confirmation_result_memo_draft_bodyfree": True,
        "post_pnt_closed_material_confirmation_result_memo_draft_materialized_here": materialized,
        "post_pnt_closed_material_confirmation_result_memo_draft_execution_allowed_here": False,
        "pcm_op07_ready_for_op08": materialized,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "pcm_op07_status_ref": status_ref,
        "bodyfree_validation_plan_result_memo_draft_status_ref": status_ref,
        "pcm_op07_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP07_ALLOWED_STATUS_REFS),
        "pcm_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP07_ALLOWED_STATUS_REFS),
        "pcm_op07_result_memo_draft_materialized_stopped": status_ref == P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        "pcm_op07_wait_or_stop_result_memo_draft_materialized_stopped": status_ref == P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        "pcm_op07_repair_required_for_result_memo_draft_inputs": status_ref == P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF,
        "pcm_op07_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_BLOCKED_RESULT_MEMO_DRAFT_REF,
        "pcm_op07_reason_refs": reason_refs,
        "pcm_op07_reason_ref_count": len(reason_refs),
        "pcm_op07_blocker_refs": blocker_refs,
        "pcm_op07_blocker_ref_count": len(blocker_refs),
        "op07_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op07_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op07_input_body_like_value_path_refs": list(body_like_paths),
        "op07_input_body_like_value_path_count": len(body_like_paths),
        "op07_input_promotion_claim_refs": list(promotion_claims),
        "op07_input_promotion_claim_ref_count": len(promotion_claims),
        "op07_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op07_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op07_does_not_close_result_memo_as_op08": True,
        "pcm_op07_does_not_execute_validation_commands": True,
        "pcm_op07_does_not_claim_full_backend_rn_or_real_device_green": True,
        "pcm_op07_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op07_does_not_execute_selected_pcm_next_boundary": True,
        "pcm_op07_does_not_call_dhr_op05": True,
        "pcm_op07_does_not_call_dhr_op06": True,
        "pcm_op07_does_not_execute_dmd_r52_or_release": True,
        "pcm_op07_does_not_start_actual_review": True,
        "pcm_op07_does_not_request_raw_evidence": True,
        "pcm_op07_does_not_execute_repair": True,
        "pcm_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op07_does_not_materialize_p8_question_spec": True,
        "pcm_op07_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP07_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "pcm_op02_implemented": True,
        "pcm_op03_implemented": True,
        "pcm_op04_implemented": True,
        "pcm_op05_implemented": True,
        "pcm_op06_implemented": True,
        "pcm_op07_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP07 validation-plan/result-memo-draft contract without running validation."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP07")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP07_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP07_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP07",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP07_REQUIRED_FALSE_FLAG_REFS,
    )
    if data.get("bodyfree_validation_plan_result_memo_draft_status_ref") != data.get("pcm_op07_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 status alias mismatch")
    if tuple(data.get("pcm_op07_allowed_status_refs", ())) != P7_R54_AHR_POST_PNT_PCM_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 allowed status refs mismatch")
    if data.get("pcm_op07_allowed_status_ref_count") != len(P7_R54_AHR_POST_PNT_PCM_OP07_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 allowed status count mismatch")
    status_ref = data.get("pcm_op07_status_ref")
    if status_ref not in P7_R54_AHR_POST_PNT_PCM_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 unknown status")
    for key in (
        "validation_plan_execution_allowed_here", "validation_commands_executed_here", "pytest_executed_here",
        "pcm_target_tests_executed_here", "selected_regression_executed_here", "compileall_executed_here",
        "post_pnt_closed_material_confirmation_result_memo_draft_execution_allowed_here", "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "selected_pcm_next_boundary_execution_allowed_here",
        "execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here",
        "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here", "json_schema_file_creation_allowed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP07 no-execution/no-claim flag changed: {key}")
    for key in (
        "pcm_op07_does_not_close_result_memo_as_op08", "pcm_op07_does_not_execute_validation_commands",
        "pcm_op07_does_not_claim_full_backend_rn_or_real_device_green", "pcm_op07_does_not_execute_selected_post_nci_next_boundary",
        "pcm_op07_does_not_execute_selected_pcm_next_boundary", "pcm_op07_does_not_call_dhr_op05", "pcm_op07_does_not_call_dhr_op06",
        "pcm_op07_does_not_execute_dmd_r52_or_release", "pcm_op07_does_not_start_actual_review", "pcm_op07_does_not_request_raw_evidence",
        "pcm_op07_does_not_execute_repair", "pcm_op07_does_not_start_p5_p6_p8_p7_or_release",
        "pcm_op07_does_not_change_api_db_rn_runtime_response_key", "pcm_op07_does_not_materialize_p8_question_spec",
        "pcm_op07_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP07 non-execution statement missing: {key}")
    for list_key, count_key in (
        ("target_test_ref_refs", "target_test_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_count"),
        ("compileall_target_ref_refs", "compileall_target_ref_count"),
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("pcm_op07_reason_refs", "pcm_op07_reason_ref_count"),
        ("pcm_op07_blocker_refs", "pcm_op07_blocker_ref_count"),
        ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"),
        ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"),
        ("op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count"),
        ("op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_key) != len(tuple(data.get(list_key, ()))):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP07 count mismatch: {list_key}")
    if tuple(data.get("target_test_ref_refs", ())) != P7_R54_AHR_POST_PNT_PCM_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 target test refs mismatch")
    if tuple(data.get("selected_regression_test_ref_refs", ())) != P7_R54_AHR_POST_PNT_PCM_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 selected regression refs mismatch")
    if tuple(data.get("compileall_target_ref_refs", ())) != P7_R54_AHR_POST_PNT_PCM_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 compileall refs mismatch")
    if tuple(data.get("validation_command_summary_refs", ())) != P7_R54_AHR_POST_PNT_PCM_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 validation command refs mismatch")
    if tuple(data.get("claim_boundary_refs", ())) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 claim boundary refs mismatch")
    if tuple(data.get("not_claimed_boundary_refs", ())) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 not-claimed boundary refs mismatch")
    if tuple(data.get("fixed_non_promotion_refs", ())) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 fixed non-promotion refs mismatch")
    if tuple(data.get("implemented_steps", ())) != P7_R54_AHR_POST_PNT_PCM_OP07_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_steps", ())) != P7_R54_AHR_POST_PNT_PCM_OP07_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 not-yet steps mismatch")
    for key in ("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented", "pcm_op07_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP07 implemented flag must be true: {key}")
    branch_flags = (
        data.get("pcm_op07_result_memo_draft_materialized_stopped") is True,
        data.get("pcm_op07_wait_or_stop_result_memo_draft_materialized_stopped") is True,
        data.get("pcm_op07_repair_required_for_result_memo_draft_inputs") is True,
        data.get("pcm_op07_bodyfree_leak_promotion_or_autorun_blocked") is True,
    )
    if sum(1 for flag in branch_flags if flag) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 must choose exactly one branch")
    blocker_count = int(data.get("pcm_op07_blocker_ref_count") or 0)
    if status_ref in (
        P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    ):
        if data.get("op06_contract_valid") is not True or data.get("op06_guard_passed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 materialized draft requires valid OP06 guard pass")
        if data.get("selected_pnt_lane_ref") not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 materialized draft requires allowed lane")
        lane_ref = str(data.get("selected_pnt_lane_ref"))
        if data.get("selected_pcm_next_work_class_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 next work class mismatch")
        expected_wait_stop = data.get("selected_pcm_next_work_class_ref") in (P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF, P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_STOP_REF)
        if expected_wait_stop and status_ref != P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 wait/stop outcome must use wait-or-stop draft status")
        if not expected_wait_stop and status_ref != P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 next-design outcome must use result draft status")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True or data.get("selected_handoff_or_stop_not_executed") is not True or data.get("selected_pcm_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 selected boundaries must remain not executed")
        if data.get("validation_plan_recorded") is not True or data.get("validation_plan_bodyfree") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 validation plan must be recorded body-free")
        if data.get("post_pnt_closed_material_confirmation_result_memo_draft_bodyfree") is not True or data.get("post_pnt_closed_material_confirmation_result_memo_draft_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 draft must be body-free materialized")
        if data.get("pcm_op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 materialized draft must be ready for OP08 only")
        if blocker_count != 0 or data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 materialized draft must continue only to OP08 with no blockers")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_RESULT_MEMO_DRAFT_INPUTS_REF or blocker_count == 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 repair branch must stop with repair blockers")
    else:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_RESULT_MEMO_DRAFT_REF or blocker_count == 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP07 blocked branch must stop with blockers")
    return True


def _op07_contract_valid(op07: Mapping[str, Any] | None) -> bool:
    if not isinstance(op07, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    except ValueError:
        return False


def _op08_status_reason_blocker_next(
    *,
    op07_present: bool,
    op07_valid: bool,
    op07_status_ref: str,
    op07_ready_for_op08: bool,
    selected_pcm_next_work_class_ref: str,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op08_closure_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op08_closure_body_like_value_detected")
    if promotion_claims:
        blockers.append("op08_closure_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op08_closure_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op07_status_ref == P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_BLOCKED_RESULT_MEMO_DRAFT_REF:
        blockers.append("pcm_op07_result_memo_draft_blocked_before_op08_closure")
    if blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
            ["post_pnt_closed_material_confirmation_closure_blocked_without_execution"],
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF,
        )

    if not op07_present:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF,
            ["explicit_closed_pnt_op08_material_required_before_pcm_op08_closure"],
            ["pcm_op07_result_memo_draft_material_missing", "explicit_pnt_op08_closed_material_required"],
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF,
        )

    repair_blockers: list[str] = []
    if not op07_valid:
        repair_blockers.append("pcm_op07_result_memo_draft_contract_invalid")
    if op07_status_ref == P7_R54_AHR_POST_PNT_PCM_OP07_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS_REF:
        repair_blockers.append("pcm_op07_result_memo_draft_repair_required_before_op08_closure")
    if op07_present and op07_valid and not op07_ready_for_op08:
        repair_blockers.append("pcm_op07_not_ready_for_op08_closure")
    if selected_pcm_next_work_class_ref not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_NEXT_WORK_CLASS_REFS:
        repair_blockers.append("selected_pcm_next_work_class_missing_or_unknown_before_op08")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_REPAIR_REQUIRED_FOR_POST_PNT_CONFIRMATION_INPUTS_REF,
            ["post_pnt_closed_material_confirmation_closure_inputs_require_repair_without_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=360),
            P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF,
        )

    return (
        P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_CLOSED_STOPPED_REF,
        ["post_pnt_closed_material_confirmation_closed_with_next_design_candidate_hold_or_stop_recorded_without_execution"],
        [],
        _op08_next_required_step_for_next_work_class(selected_pcm_next_work_class_ref),
    )


def _op08_next_required_step_for_next_work_class(next_work_class_ref: str) -> str:
    if next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF:
        return P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_STOP_AFTER_OP08_NEXT_DESIGN_CANDIDATE_REF
    if next_work_class_ref == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF:
        return P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_HOLD_AFTER_OP08_REF
    return P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_STOP_AFTER_OP08_REF


def build_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure(
    op07_validation_plan_result_memo_draft_material: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
    target_test_result_status_ref: Any = None,
    selected_regression_result_status_ref: Any = None,
    compileall_result_status_ref: Any = None,
) -> dict[str, Any]:
    """Build PCM-OP08 body-free result memo closure without downstream execution."""

    session_id = _safe_review_session_id(review_session_id)
    op07 = op07_validation_plan_result_memo_draft_material
    op07_present = isinstance(op07, Mapping)
    op07_valid = _op07_contract_valid(op07 if isinstance(op07, Mapping) else None)
    op07_status_ref = _clean_ref(op07.get("pcm_op07_status_ref") if isinstance(op07, Mapping) else None, default="missing", max_length=300)
    op07_next_required_step = _clean_ref(op07.get("next_required_step") if isinstance(op07, Mapping) else None, default="missing", max_length=420)
    op07_ready_for_op08 = bool(op07_valid and op07.get("pcm_op07_ready_for_op08") is True) if isinstance(op07, Mapping) else False
    selected_pcm_next_work_class_ref = _clean_ref(op07.get("selected_pcm_next_work_class_ref") if isinstance(op07, Mapping) else None, default="missing", max_length=260)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op07 or {}, path="pcm_op07")
    promotion_claims = _filter_allowed_prior_implemented_flag_paths(
        promotion_claims,
        allowed_implemented_keys=(
            "pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented",
            "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented",
            "pcm_op06_implemented", "pcm_op07_implemented",
        ),
    )
    status_ref, reason_refs, blocker_refs, next_required_step = _op08_status_reason_blocker_next(
        op07_present=op07_present,
        op07_valid=op07_valid,
        op07_status_ref=op07_status_ref,
        op07_ready_for_op08=op07_ready_for_op08,
        selected_pcm_next_work_class_ref=selected_pcm_next_work_class_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    closed = status_ref == P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_CLOSED_STOPPED_REF

    if closed and isinstance(op07, Mapping):
        selected_pnt_status_ref = _clean_ref(op07.get("selected_pnt_status_ref"), default="missing", max_length=300)
        selected_pnt_lane_ref = _clean_ref(op07.get("selected_pnt_lane_ref"), default="missing", max_length=300)
        selected_post_nci_outcome_group_ref = _clean_ref(op07.get("selected_post_nci_outcome_group_ref"), default="missing", max_length=260)
        selected_post_nci_next_boundary_ref = _clean_ref(op07.get("selected_post_nci_next_boundary_ref"), default="missing", max_length=420)
        selected_post_nci_next_boundary_kind_ref = _clean_ref(op07.get("selected_post_nci_next_boundary_kind_ref"), default="missing", max_length=420)
        selected_post_nci_next_boundary_not_executed = bool(op07.get("selected_post_nci_next_boundary_not_executed") is True)
        selected_handoff_or_stop_ref = _clean_ref(op07.get("selected_handoff_or_stop_ref"), default="missing", max_length=420)
        selected_handoff_or_stop_kind_ref = _clean_ref(op07.get("selected_handoff_or_stop_kind_ref"), default="missing", max_length=420)
        selected_handoff_or_stop_not_executed = bool(op07.get("selected_handoff_or_stop_not_executed") is True)
        selected_pcm_next_boundary_ref = _clean_ref(op07.get("selected_pcm_next_boundary_ref"), default="missing", max_length=420)
        selected_pcm_next_boundary_kind_ref = _clean_ref(op07.get("selected_pcm_next_boundary_kind_ref"), default="missing", max_length=420)
        selected_pcm_next_boundary_not_executed = bool(op07.get("selected_pcm_next_boundary_not_executed") is True)
        selected_pcm_next_boundary_envelope_materialized_here = bool(op07.get("selected_pcm_next_boundary_envelope_materialized_here") is True)
        next_design_document_candidate_ref = _clean_ref(op07.get("next_design_document_candidate_ref"), default="missing", max_length=420)
        next_design_document_allowed = bool(op07.get("next_design_document_allowed") is True)
        manual_wait_required = bool(op07.get("manual_wait_required") is True)
        manual_stop_required = bool(op07.get("manual_stop_required") is True)
        repair_design_candidate = bool(op07.get("repair_design_candidate") is True)
    else:
        selected_pnt_status_ref = status_ref
        selected_pnt_lane_ref = "missing"
        selected_post_nci_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_handoff_or_stop_ref = "missing"
        selected_handoff_or_stop_kind_ref = "missing"
        selected_handoff_or_stop_not_executed = False
        selected_pcm_next_work_class_ref = "missing"
        selected_pcm_next_boundary_ref = "missing"
        selected_pcm_next_boundary_kind_ref = "missing"
        selected_pcm_next_boundary_not_executed = False
        selected_pcm_next_boundary_envelope_materialized_here = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False

    inherited_target_status_ref = op07.get("target_test_result_status_ref") if isinstance(op07, Mapping) else None
    inherited_regression_status_ref = op07.get("selected_regression_result_status_ref") if isinstance(op07, Mapping) else None
    inherited_compileall_status_ref = op07.get("compileall_result_status_ref") if isinstance(op07, Mapping) else None
    target_status_ref = _clean_ref(target_test_result_status_ref, default=_clean_ref(inherited_target_status_ref, default="pcm_op08_target_test_result_not_recorded_here", max_length=120), max_length=120)
    regression_status_ref = _clean_ref(selected_regression_result_status_ref, default=_clean_ref(inherited_regression_status_ref, default="pcm_op08_selected_regression_result_not_recorded_here", max_length=120), max_length=120)
    compile_status_ref = _clean_ref(compileall_result_status_ref, default=_clean_ref(inherited_compileall_status_ref, default="pcm_op08_compileall_result_not_recorded_here", max_length=120), max_length=120)

    reason_refs = _dedupe_clean_refs(reason_refs, max_length=360)
    blocker_refs = _dedupe_clean_refs(blocker_refs, max_length=360)
    return {
        "schema_version": P7_R54_AHR_POST_PNT_PCM_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "step": P7_R54_AHR_POST_PNT_PCM_STEP,
        "scope": P7_R54_AHR_POST_PNT_PCM_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PNT_PCM_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PNT_PCM_PHASE,
        "material_id": "p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PNT_PCM_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_material_present": op07_present,
        "op07_contract_valid": op07_valid,
        "op07_schema_version": _clean_ref(op07.get("schema_version") if isinstance(op07, Mapping) else None, default="missing", max_length=260),
        "op07_material_ref": _clean_ref(op07.get("material_id") if isinstance(op07, Mapping) else None, default="missing", max_length=300),
        "op07_status_ref": op07_status_ref,
        "op07_next_required_step": op07_next_required_step,
        "op07_ready_for_op08": op07_ready_for_op08,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": selected_pnt_lane_ref,
        "selected_post_nci_outcome_group_ref": selected_post_nci_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_handoff_or_stop_not_executed,
        "selected_pcm_next_work_class_ref": selected_pcm_next_work_class_ref,
        "selected_pcm_next_boundary_ref": selected_pcm_next_boundary_ref,
        "selected_pcm_next_boundary_kind_ref": selected_pcm_next_boundary_kind_ref,
        "selected_pcm_next_boundary_not_executed": selected_pcm_next_boundary_not_executed,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "selected_pcm_next_boundary_envelope_materialized_here": selected_pcm_next_boundary_envelope_materialized_here,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "execution_allowed_here": False,
        "target_test_result_status_ref": target_status_ref,
        "selected_regression_result_status_ref": regression_status_ref,
        "compileall_result_status_ref": compile_status_ref,
        "validation_result_status_refs_recorded": True,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "pnt_op08_builder_not_called": True,
        "pnt_op08_material_not_synthesized": True,
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "actual_review_not_started": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "api_db_rn_runtime_response_key_not_changed": True,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "post_pnt_closed_material_confirmation_result_memo_closure_ref": "pcm_op08_post_pnt_closed_material_confirmation_result_memo_bodyfree_closure",
        "post_pnt_closed_material_confirmation_result_memo_closure_bodyfree": True,
        "post_pnt_closed_material_confirmation_result_memo_closed_here": closed,
        "post_pnt_closed_material_confirmation_result_memo_execution_allowed_here": False,
        "pcm_op08_status_ref": status_ref,
        "bodyfree_post_pnt_closed_material_confirmation_closure_status_ref": status_ref,
        "pcm_op08_allowed_status_refs": list(P7_R54_AHR_POST_PNT_PCM_OP08_ALLOWED_STATUS_REFS),
        "pcm_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_PNT_PCM_OP08_ALLOWED_STATUS_REFS),
        "pcm_op08_closed_stopped": closed,
        "pcm_op08_waiting_for_explicit_pnt_op08_closed_material": status_ref == P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF,
        "pcm_op08_repair_required_for_post_pnt_confirmation_inputs": status_ref == P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_REPAIR_REQUIRED_FOR_POST_PNT_CONFIRMATION_INPUTS_REF,
        "pcm_op08_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
        "pcm_op08_reason_refs": reason_refs,
        "pcm_op08_reason_ref_count": len(reason_refs),
        "pcm_op08_blocker_refs": blocker_refs,
        "pcm_op08_blocker_ref_count": len(blocker_refs),
        "op08_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op08_input_body_like_value_path_refs": list(body_like_paths),
        "op08_input_body_like_value_path_count": len(body_like_paths),
        "op08_input_promotion_claim_refs": list(promotion_claims),
        "op08_input_promotion_claim_ref_count": len(promotion_claims),
        "op08_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op08_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op08_records_next_design_candidate_hold_or_stop_only": True,
        "pcm_op08_does_not_execute_selected_post_nci_next_boundary": True,
        "pcm_op08_does_not_execute_selected_pcm_next_boundary": True,
        "pcm_op08_does_not_call_dhr_op05": True,
        "pcm_op08_does_not_call_dhr_op06": True,
        "pcm_op08_does_not_execute_dmd_r52_or_release": True,
        "pcm_op08_does_not_start_actual_review": True,
        "pcm_op08_does_not_request_raw_evidence": True,
        "pcm_op08_does_not_execute_repair": True,
        "pcm_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "pcm_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "pcm_op08_does_not_materialize_p8_question_spec": True,
        "pcm_op08_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PNT_PCM_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pcm_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FALSE_FLAG_REFS),
        "pcm_op00_implemented": True,
        "pcm_op01_implemented": True,
        "pcm_op02_implemented": True,
        "pcm_op03_implemented": True,
        "pcm_op04_implemented": True,
        "pcm_op05_implemented": True,
        "pcm_op06_implemented": True,
        "pcm_op07_implemented": True,
        "pcm_op08_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PCM-OP08 body-free result memo closure contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPNT-PCM-OP08")
    if set(data) != set(P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PNT_PCM_OP08_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF,
        source="P7-R54-AHR-PostPNT-PCM-OP08",
        required_false_flag_refs=P7_R54_AHR_POST_PNT_PCM_OP08_REQUIRED_FALSE_FLAG_REFS,
    )
    if data.get("bodyfree_post_pnt_closed_material_confirmation_closure_status_ref") != data.get("pcm_op08_status_ref"):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 status alias mismatch")
    if tuple(data.get("pcm_op08_allowed_status_refs", ())) != P7_R54_AHR_POST_PNT_PCM_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 allowed status refs mismatch")
    if data.get("pcm_op08_allowed_status_ref_count") != len(P7_R54_AHR_POST_PNT_PCM_OP08_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 allowed status count mismatch")
    status_ref = data.get("pcm_op08_status_ref")
    if status_ref not in P7_R54_AHR_POST_PNT_PCM_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 unknown status")
    for key in (
        "selected_pcm_next_boundary_execution_allowed_here", "execution_allowed_here",
        "post_pnt_closed_material_confirmation_result_memo_execution_allowed_here",
        "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
        "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP08 no-execution/no-claim flag changed: {key}")
    for key in (
        "pnt_op08_builder_not_called", "pnt_op08_material_not_synthesized", "dhr_op05_not_called",
        "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started",
        "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started",
        "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
        "post_pnt_closed_material_confirmation_result_memo_closure_bodyfree",
        "validation_result_status_refs_recorded", "pcm_op08_records_next_design_candidate_hold_or_stop_only",
        "pcm_op08_does_not_execute_selected_post_nci_next_boundary", "pcm_op08_does_not_execute_selected_pcm_next_boundary",
        "pcm_op08_does_not_call_dhr_op05", "pcm_op08_does_not_call_dhr_op06",
        "pcm_op08_does_not_execute_dmd_r52_or_release", "pcm_op08_does_not_start_actual_review",
        "pcm_op08_does_not_request_raw_evidence", "pcm_op08_does_not_execute_repair",
        "pcm_op08_does_not_start_p5_p6_p8_p7_or_release", "pcm_op08_does_not_change_api_db_rn_runtime_response_key",
        "pcm_op08_does_not_materialize_p8_question_spec", "pcm_op08_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP08 required true boundary changed: {key}")
    for list_key, count_key in (
        ("pcm_op08_reason_refs", "pcm_op08_reason_ref_count"),
        ("pcm_op08_blocker_refs", "pcm_op08_blocker_ref_count"),
        ("op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count"),
        ("op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count"),
        ("op08_input_promotion_claim_refs", "op08_input_promotion_claim_ref_count"),
        ("op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_key) != len(tuple(data.get(list_key, ()))):
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP08 count mismatch: {list_key}")
    if tuple(data.get("claim_boundary_refs", ())) != P7_R54_AHR_POST_PNT_PCM_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 claim boundary refs mismatch")
    if tuple(data.get("not_claimed_boundary_refs", ())) != P7_R54_AHR_POST_PNT_PCM_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 not-claimed boundary refs mismatch")
    if tuple(data.get("fixed_non_promotion_refs", ())) != P7_R54_AHR_POST_PNT_PCM_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 fixed non-promotion refs mismatch")
    if tuple(data.get("implemented_steps", ())) != P7_R54_AHR_POST_PNT_PCM_OP08_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_steps", ())) != P7_R54_AHR_POST_PNT_PCM_OP08_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 not-yet steps mismatch")
    for key in ("pcm_op00_implemented", "pcm_op01_implemented", "pcm_op02_implemented", "pcm_op03_implemented", "pcm_op04_implemented", "pcm_op05_implemented", "pcm_op06_implemented", "pcm_op07_implemented", "pcm_op08_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPNT-PCM-OP08 implemented flag must be true: {key}")
    branch_flags = (
        data.get("pcm_op08_closed_stopped") is True,
        data.get("pcm_op08_waiting_for_explicit_pnt_op08_closed_material") is True,
        data.get("pcm_op08_repair_required_for_post_pnt_confirmation_inputs") is True,
        data.get("pcm_op08_bodyfree_leak_promotion_or_autorun_blocked") is True,
    )
    if sum(1 for flag in branch_flags if flag) != 1:
        raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 must choose exactly one branch")
    blocker_count = int(data.get("pcm_op08_blocker_ref_count") or 0)
    if status_ref == P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_CLOSED_STOPPED_REF:
        if data.get("op07_contract_valid") is not True or data.get("op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 closed branch requires valid OP07 ready material")
        if data.get("selected_pnt_lane_ref") not in P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 closed branch requires allowed lane")
        lane_ref = str(data.get("selected_pnt_lane_ref"))
        expected_next_work_class = P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_WORK_CLASS_REFS[lane_ref]
        if data.get("selected_pcm_next_work_class_ref") != expected_next_work_class:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 next work class mismatch")
        if data.get("selected_pcm_next_boundary_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 selected PCM boundary mismatch")
        if data.get("selected_pcm_next_boundary_kind_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 selected PCM boundary kind mismatch")
        if expected_next_work_class == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF:
            if data.get("next_design_document_candidate_ref") != P7_R54_AHR_POST_PNT_PCM_LANE_TO_NEXT_DESIGN_OR_HOLD_STOP_REFS[lane_ref]:
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 next design candidate ref mismatch")
            if data.get("next_design_document_allowed") is not True:
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 next design branch must allow only the next design document")
        elif expected_next_work_class == P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_WAIT_HOLD_REF:
            if data.get("next_design_document_allowed") is not False or data.get("manual_wait_required") is not True or data.get("manual_stop_required") is not False:
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 wait branch must hold without next design promotion")
        else:
            if data.get("next_design_document_allowed") is not False or data.get("manual_wait_required") is not False or data.get("manual_stop_required") is not True:
                raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 stop branch must stop without next design promotion")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True or data.get("selected_handoff_or_stop_not_executed") is not True or data.get("selected_pcm_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 selected boundaries must remain not executed")
        if data.get("selected_pcm_next_boundary_envelope_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 closed branch requires OP05 envelope already materialized")
        if data.get("post_pnt_closed_material_confirmation_result_memo_closed_here") is not True:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 closed branch must close result memo here")
        if blocker_count != 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 closed branch must not have blockers")
        expected_next_required_step = _op08_next_required_step_for_next_work_class(expected_next_work_class)
        if data.get("next_required_step") != expected_next_required_step:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 closed branch next step mismatch")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_WAITING_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF:
        if data.get("op07_material_present") is not False or data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_WAIT_FOR_EXPLICIT_PNT_OP08_CLOSED_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 waiting branch must wait for explicit closed material")
        if blocker_count == 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 waiting branch must explain missing material")
    elif status_ref == P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_REPAIR_REQUIRED_FOR_POST_PNT_CONFIRMATION_INPUTS_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF or blocker_count == 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 repair branch must stop with repair blockers")
    else:
        if data.get("next_required_step") != P7_R54_AHR_POST_PNT_PCM_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF or blocker_count == 0:
            raise ValueError("P7-R54-AHR-PostPNT-PCM-OP08 blocked branch must stop with blockers")
    return True

build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08 = (
    build_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op00_scope_explicit_closed_material_no_execution_refreeze_after_pnt_op08_contract
)
build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op01_explicit_closed_pnt_op08_material_intake = (
    build_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op01_explicit_closed_pnt_op08_material_intake_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op01_explicit_closed_pnt_op08_material_intake_contract
)
build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_closed_material_contract_validation = (
    build_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_closed_material_contract_validation_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op02_closed_material_contract_validation_contract
)
build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op03_single_selected_lane_confirmation = (
    build_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op03_single_selected_lane_confirmation_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op03_single_selected_lane_confirmation_contract
)

build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_next_work_class_resolver = (
    build_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_next_work_class_resolver_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op04_next_work_class_resolver_contract
)
build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op05_next_design_candidate_envelope_materialization = (
    build_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op05_next_design_candidate_envelope_materialization_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op05_next_design_candidate_envelope_materialization_contract
)
build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard = (
    build_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract
)
build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op07_validation_plan_result_memo_draft_material = (
    build_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op07_validation_plan_result_memo_draft_material_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op07_validation_plan_result_memo_draft_material_contract
)
build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_bodyfree_closure = (
    build_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_bodyfree_closure_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_op08_bodyfree_post_pnt_closed_material_next_boundary_confirmation_closure_contract
)

build_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_r1_helper_skeleton_constants_summary = (
    build_p7_r54_ahr_post_pnt_pcm_r1_helper_skeleton_constants_summary
)
assert_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_r1_helper_skeleton_constants_summary_contract = (
    assert_p7_r54_ahr_post_pnt_pcm_r1_helper_skeleton_constants_summary_contract
)

__all__ = tuple(
    name
    for name in globals()
    if name.startswith("P7_R54_AHR_POST_PNT_PCM_")
    or name.startswith("build_p7_r54_ahr_post_pnt")
    or name.startswith("assert_p7_r54_ahr_post_pnt")
)
