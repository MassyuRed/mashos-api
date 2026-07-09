# -*- coding: utf-8 -*-
"""Post-PCM DHR-OP05 manual handoff boundary helpers.

R0/R1 implemented first; R2 adds DHB-OP00/OP01; R3 adds DHB-OP02/OP03; R4 adds DHB-OP04/OP05; R5 adds DHB-OP06/OP07; R6 adds DHB-OP08 closure only.

This module is intentionally a thin body-free boundary after the already-closed
PCM-OP08 next-boundary confirmation material. R0 freezes the design-reflection
scope before implementation; R1 adds helper skeleton constants, allowed refs,
forbidden refs, existing DHR-OP05 reference strings, and a small constants-summary
contract.

Important boundary:
* DHB requires one explicit closed PCM-OP08 material in future OP01 work.
* This module never synthesizes PCM-OP08 material, never calls a PCM builder, and
  never infers the current DHR-OP05 lane from target/regression/compileall green.
* This module records existing DHR-OP05 builder/assert names as strings only. It
  does not import or call the existing DHR-OP05 builder/assert.
* This module does not execute DHR-OP05, DHR-OP06, DHR-OP07, DMD, R52, actual
  review, P8, release, API/DB/RN/runtime/response-key changes, validation
  commands, full-backend/RN/real-device claims, actual rows, question rows, or
  question text materialization.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707 as pcm


P7_R54_AHR_POST_PCM_DHB_PHASE: Final = "P7"
P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_PCM_DHB_STEP: Final = (
    "R54-AHR-PostPCM_DHROP05ManualHandoffBoundary_20260708"
)
P7_R54_AHR_POST_PCM_DHB_SCOPE: Final = (
    "p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary"
)
P7_R54_AHR_POST_PCM_DHB_POLICY_KIND: Final = (
    "r54_ahr_post_pcm_explicit_dhr_op05_lane_manual_handoff_bodyfree_boundary"
)
P7_R54_AHR_POST_PCM_DHB_DEFAULT_REVIEW_SESSION_ID: Final = (
    "p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708"
)
P7_R54_AHR_POST_PCM_DHB_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-PCM DHR-OP05 Manual Handoff Boundary / Preflight Re-entry"
)
P7_R54_AHR_POST_PCM_DHB_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-PCM DHR-OP05 Manual Handoff Boundary / Preflight Re-entry"
)
P7_R54_AHR_POST_PCM_DHB_BOUNDARY_PREFIX_REF: Final = "DHB"
P7_R54_AHR_POST_PCM_DHB_BOUNDARY_PREFIX_MEANING_REF: Final = (
    "DHR-OP05 Manual Handoff Boundary"
)
P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF: Final = "R0_design_reflection_pre_freeze"
P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF: Final = "R1_helper_skeleton_constants"
P7_R54_AHR_POST_PCM_DHB_EXPECTED_FROM_PCM_OP08_REF: Final = (
    "one explicit closed PCM-OP08 body-free material must select the DHR-OP05 lane; "
    "PCM R11 memo, target green, selected regression green, compileall green, or "
    "decision table alone must not be treated as the current DHR-OP05 lane"
)
P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_DHB_OP00_scope_no_execution_refreeze_after_PCM_R11"
)

P7_R54_AHR_POST_PCM_DHB_R1_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.r1_helper_skeleton_constants_summary.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op00_scope_no_execution_refreeze_after_pcm_r11.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op01_explicit_pcm_op08_closed_material_intake.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op02_pcm_op08_contract_validation.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op03_dhr_op05_lane_exact_confirmation.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op04_dhr_op05_manual_handoff_envelope_without_call.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op05_existing_dhr_op05_compatibility_crosswalk_without_call.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op07_validation_plan_result_memo_draft_material.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_pcm.dhb.op08_bodyfree_dhr_op05_manual_handoff_boundary_closure.bodyfree.v1"
)

P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF: Final = (
    "DHB-OP00_scope_no_execution_refreeze_after_PCM_R11"
)
P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF: Final = (
    "DHB-OP01_explicit_PCM_OP08_closed_material_intake"
)
P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF: Final = (
    "DHB-OP02_PCM_OP08_contract_validation"
)
P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF: Final = (
    "DHB-OP03_DHR_OP05_lane_exact_confirmation"
)
P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF: Final = (
    "DHB-OP04_DHR_OP05_manual_handoff_envelope_without_call"
)
P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF: Final = (
    "DHB-OP05_existing_DHR_OP05_compatibility_crosswalk_without_call"
)
P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF: Final = (
    "DHB-OP06_bodyfree_no_touch_no_promotion_no_auto_execution_guard"
)
P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF: Final = (
    "DHB-OP07_validation_plan_result_memo_draft_material"
)
P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF: Final = (
    "DHB-OP08_bodyfree_DHR_OP05_manual_handoff_boundary_closure"
)
P7_R54_AHR_POST_PCM_DHB_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_R0_R1_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_R0_R1_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_STEP_REFS
)

P7_R54_AHR_POST_PCM_DHB_EXPLICIT_PCM_OP08_CLOSED_MATERIAL_REQUIRED: Final = True
P7_R54_AHR_POST_PCM_DHB_PCM_OP08_MATERIAL_SYNTHESIS_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_PCM_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_PCM_R11_MEMO_AS_CURRENT_LANE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_PCM_TARGET_GREEN_AS_CURRENT_LANE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_PCM_DECISION_TABLE_AS_SINGLE_LANE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_DHR_OP05_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_DHR_OP05_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_DHR_OP06_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_DHR_OP07_MATERIALIZATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_DMD_R52_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_ACTUAL_REVIEW_START_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_ACTUAL_ROWS_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_QUESTION_NEED_OBSERVATION_ROWS_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_REPAIR_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_RAW_EVIDENCE_REQUEST_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_P8_QUESTION_DESIGN_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_P8_QUESTION_IMPLEMENTATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_QUESTION_TEXT_MATERIALIZATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_API_DB_RN_RUNTIME_RESPONSE_KEY_CHANGE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_P7_COMPLETE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_RELEASE_DECISION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_FULL_BACKEND_SUITE_GREEN_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_RN_CONTRACT_GREEN_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_RN_REAL_DEVICE_MODAL_VERIFICATION_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_PCM_DHB_BODY_FREE: Final = True

P7_R54_AHR_POST_PCM_DHB_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(300).zip",
    "implemented_docs": "EmlisAIの実装済み資料(104).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_system_update_20260706(4).zip",
    "cocolon_app": "Cocolon(276).zip",
    "backend": "mashos-api(192).zip",
}
P7_R54_AHR_POST_PCM_DHB_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/04_forbidden_mixing_design_and_implementation.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/08_artifact_delivery_rules.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/09_work_start_checklist.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/11_cocolon_area_specific_do_not_break.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/14_cocolon_joint_development_and_karen_thought_boundary.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/15_trust_based_joint_development_boundary_2026_06_05.txt",
    "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
    "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostPCM_DHROP05ManualHandoffBoundary_PreDesignMemo_20260708.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostPCM_DHROP05ManualHandoffBoundary_DetailedDesign_ImplementationOrder_20260708.md",
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_PCM_DHB_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "PCM-OP08 material synthesis",
    "PCM builder call",
    "PCM R11 memo as current selected DHR-OP05 lane",
    "PCM target/regression/compileall green as current selected lane",
    "PCM decision table or all-lane summary as single selected lane",
    "DHR-OP05 call / builder call / preflight scan execution",
    "DHR-OP06 call",
    "DHR-OP07 materialization",
    "DMD execution",
    "R52 actual execution",
    "actual review start",
    "actual rows / question need observation rows creation",
    "raw evidence request",
    "repair execution",
    "P8 start",
    "P8 question design / implementation",
    "question_text / draft_question_text / answer_text materialization",
    "API / DB / RN / runtime / response key change",
    "json / schema file creation",
    "P7 completion",
    "release decision",
)
P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "DHB R0/R1 only freezes the Post-PCM DHR-OP05 manual handoff scope and constants",
    "DHB helper body must require one explicit closed PCM-OP08 material in future OP01 work",
    "DHB helper body must not synthesize PCM-OP08 material",
    "DHB helper body must not call PCM builders",
    "DHB constants keep PCM R11 memo, target green, regression green, compileall green, and decision table out of current-lane inference",
    "DHB constants record existing DHR-OP05 builder/assert refs as strings only",
    "DHB constants keep DHR-OP05 call and existing DHR-OP05 builder call unavailable",
    "DHB constants keep DHR-OP06, DHR-OP07, DMD, R52, actual review, P8, and release unavailable",
    "DHB constants keep API / DB / RN / runtime / response key no-touch",
)
P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "dhb_op00_implemented",
    "dhb_op01_implemented",
    "dhb_op02_implemented",
    "dhb_op03_implemented",
    "dhb_op04_implemented",
    "dhb_op05_implemented",
    "dhb_op06_implemented",
    "dhb_op07_implemented",
    "dhb_op08_implemented",
    "pcm_op08_material_synthesized_here",
    "pcm_builder_called_here",
    "pcm_r11_memo_used_as_current_lane_here",
    "pcm_target_green_used_as_current_lane_here",
    "pcm_decision_table_used_as_single_lane_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "existing_dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
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
P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_pcm_op08_material_synthesis",
    "no_pcm_builder_call",
    "no_pcm_r11_memo_as_current_lane",
    "no_pcm_target_regression_compileall_green_as_current_lane",
    "no_pcm_decision_table_as_single_lane",
    "no_dhr_op05_call_or_builder_call",
    "no_existing_dhr_op05_builder_call_in_dhb",
    "no_dhr_op06_or_dhr_op07",
    "no_dmd_or_r52_execution",
    "no_actual_review_execution",
    "no_actual_rows_or_question_need_rows_creation",
    "no_raw_evidence_request",
    "no_repair_execution",
    "no_p8_question_text_or_question_spec_materialization",
    "no_api_db_rn_runtime_response_key_change",
    "no_json_schema_file_creation_in_r0_r1",
    "no_p7_complete_or_release_decision",
)

P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_OP08_SCHEMA_VERSION
)
P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_OP08_STEP_REF
)
P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_OP08_STATUS_CLOSED_STOPPED_REF
)
P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_LANE_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_REF
)
P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_WORK_CLASS_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_WORK_CLASS_NEXT_DESIGN_CANDIDATE_REF
)
P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_SELECTED_NEXT_BOUNDARY_DHR_OP05_PREFLIGHT_DESIGN_WITHOUT_CALL_REF
)
P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_BOUNDARY_KIND_NEXT_DESIGN_CANDIDATE_REF
)
P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF: Final = (
    pcm.P7_R54_AHR_POST_PNT_PCM_NEXT_DESIGN_DOCUMENT_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_REF
)
P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS: Final[tuple[str, ...]] = tuple(
    lane_ref
    for lane_ref in pcm.P7_R54_AHR_POST_PNT_PCM_ALLOWED_LANE_REFS
    if lane_ref != P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
)

P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF: Final = (
    "build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan"
)
P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF: Final = (
    "assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract"
)
P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_SCHEMA_VERSION_REF: Final = (
    "cocolon.emlis.p7_r54.ahr.post_elr19.dhr.op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan.bodyfree.v1"
)
P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHR_PREFLIGHT_SCAN_CLEAR_BODYFREE",
    "DHR_PREFLIGHT_SCAN_REPAIR_REQUIRED",
    "DHR_PREFLIGHT_SCAN_WAITING_OR_INCOMPLETE",
)

P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_STATUS_PCM_OP08_MATERIAL_INTAKE_READY_FOR_CONTRACT_VALIDATION",
    "DHB_STATUS_WAITING_FOR_EXPLICIT_PCM_OP08_CLOSED_MATERIAL",
    "DHB_STATUS_REPAIR_REQUIRED_FOR_PCM_OP08_MATERIAL_INTAKE",
    "DHB_STATUS_BLOCKED_PCM_OP08_MATERIAL_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_STATUS_PCM_OP08_CONTRACT_VALID_STOPPED",
    "DHB_STATUS_REPAIR_REQUIRED_FOR_PCM_OP08_CONTRACT",
    "DHB_STATUS_BLOCKED_PCM_OP08_CONTRACT_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_STATUS_DHR_OP05_LANE_CONFIRMED_STOPPED",
    "DHB_STATUS_NOT_DHR_OP05_LANE_ROUTE_PRESERVED_STOPPED",
    "DHB_STATUS_REPAIR_REQUIRED_FOR_DHR_OP05_LANE_CONFIRMATION",
    "DHB_STATUS_BLOCKED_DHR_OP05_LANE_CONFIRMATION_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_STATUS_DHR_OP05_MANUAL_HANDOFF_ENVELOPE_MATERIALIZED_STOPPED",
    "DHB_STATUS_NOT_DHR_OP05_LANE_NO_HANDOFF_ENVELOPE_STOPPED",
    "DHB_STATUS_REPAIR_REQUIRED_FOR_DHR_OP05_HANDOFF_ENVELOPE_INPUTS",
    "DHB_STATUS_BLOCKED_DHR_OP05_HANDOFF_ENVELOPE_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_STATUS_DHR_OP05_COMPATIBILITY_CROSSWALK_RECORDED_WITHOUT_CALL",
    "DHB_STATUS_DHR_OP05_COMPATIBILITY_REPAIR_REQUIRED",
    "DHB_STATUS_DHR_OP05_COMPATIBILITY_BLOCKED_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_STATUS_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD_PASSED",
    "DHB_STATUS_REPAIR_REQUIRED_FOR_BODYFREE_NO_TOUCH_GUARD_INPUTS",
    "DHB_STATUS_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD",
)
P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_STATUS_VALIDATION_PLAN_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED",
    "DHB_STATUS_WAIT_OR_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED",
    "DHB_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS",
    "DHB_STATUS_BLOCKED_RESULT_MEMO_DRAFT_BODYFREE_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHB_OP08_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_CLOSED_STOPPED",
    "DHB_OP08_NOT_DHR_OP05_LANE_ROUTE_PRESERVED_STOPPED",
    "DHB_OP08_WAITING_FOR_EXPLICIT_PCM_OP08_DHR_LANE",
    "DHB_OP08_REPAIR_REQUIRED_FOR_DHR_OP05_HANDOFF_BOUNDARY_INPUTS",
    "DHB_OP08_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_PCM_DHB_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS
    )
)

P7_R54_AHR_POST_PCM_DHB_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
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
    "question_answer_body",
    "local_path",
    "absolute_path",
    "hash",
    "sha256",
    "stdout",
    "stderr",
    "traceback",
)
P7_R54_AHR_POST_PCM_DHB_NO_TOUCH_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "api_db_rn_runtime_response_key_changed",
)
P7_R54_AHR_POST_PCM_DHB_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "body_free",
    "raw_input_included",
    "comment_text_body_included",
    "question_text_included",
    "reviewer_free_text_included",
    "body_full_packet_generated",
)
P7_R54_AHR_POST_PCM_DHB_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "existing_dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS
)
P7_R54_AHR_POST_PCM_DHB_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
)
P7_R54_AHR_POST_PCM_DHB_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_result_20260707.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
)
P7_R54_AHR_POST_PCM_DHB_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_PCM_DHB_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "R1 target validation may run the DHB R0/R1 skeleton test only",
    "R1 compileall may run the new DHB helper and adjacent existing reference modules",
    "R1 does not run DHR-OP05 builder, DHR-OP05 preflight, downstream execution, full backend suite, RN contract, or real-device checks",
)

P7_R54_AHR_POST_PCM_DHB_R1_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "expected_from_pcm_op08_ref",
    "expected_next_required_step_ref",
    "implemented_step_refs",
    "not_yet_implemented_step_refs",
    "dhb_step_refs",
    "local_received_zip_refs",
    "support_material_refs",
    "not_stage_refs",
    "claim_boundary_refs",
    "not_claimed_boundary_refs",
    "fixed_non_promotion_refs",
    "explicit_pcm_op08_closed_material_required",
    "pcm_op08_material_synthesis_allowed_here",
    "pcm_builder_call_allowed_here",
    "pcm_r11_memo_as_current_lane_allowed_here",
    "pcm_target_green_as_current_lane_allowed_here",
    "pcm_decision_table_as_single_lane_allowed_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "repair_execution_allowed_here",
    "raw_evidence_request_allowed_here",
    "p8_question_design_allowed_here",
    "p8_question_implementation_allowed_here",
    "question_text_materialization_allowed_here",
    "api_db_rn_runtime_response_key_change_allowed_here",
    "json_schema_file_creation_allowed_here",
    "p7_complete_allowed_here",
    "release_decision_allowed_here",
    "full_backend_suite_green_claim_allowed_here",
    "rn_contract_green_claim_allowed_here",
    "rn_real_device_modal_verification_claim_allowed_here",
    "allowed_pcm_op08_schema_version_ref",
    "allowed_pcm_op08_step_ref",
    "allowed_pcm_op08_closed_status_ref",
    "dhr_op05_lane_ref",
    "expected_selected_pcm_next_work_class_ref",
    "expected_selected_pcm_next_boundary_ref",
    "expected_selected_pcm_next_boundary_kind_ref",
    "expected_next_design_document_candidate_ref",
    "allowed_non_dhr_lane_refs",
    "allowed_status_refs",
    "existing_dhr_op05_builder_ref",
    "existing_dhr_op05_assert_ref",
    "existing_dhr_op05_schema_version_ref",
    "existing_dhr_op05_compatibility_status_refs",
    "forbidden_payload_key_refs",
    "no_touch_contract_keys",
    "body_free_marker_refs",
    "promotion_claim_field_refs",
    "required_false_flag_refs",
    "target_test_ref_refs",
    "selected_regression_test_ref_refs",
    "compileall_target_ref_refs",
    "validation_command_summary_refs",
    "public_contract",
    *P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS,
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "next_required_step",
    "body_free",
)


def build_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary(
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Return a body-free R0/R1 constants summary without calling PCM/DHR builders."""

    safe_review_session_id = clean_identifier(
        review_session_id,
        default=P7_R54_AHR_POST_PCM_DHB_DEFAULT_REVIEW_SESSION_ID,
        max_length=180,
    )
    data: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_R1_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
        "material_id": "p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_20260708",
        "review_session_id": safe_review_session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_PCM_DHB_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_PCM_DHB_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_PCM_DHB_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_PCM_DHB_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_pcm_op08_ref": P7_R54_AHR_POST_PCM_DHB_EXPECTED_FROM_PCM_OP08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "implemented_step_refs": P7_R54_AHR_POST_PCM_DHB_R0_R1_IMPLEMENTED_STEPS,
        "not_yet_implemented_step_refs": P7_R54_AHR_POST_PCM_DHB_R0_R1_NOT_YET_IMPLEMENTED_STEPS,
        "dhb_step_refs": P7_R54_AHR_POST_PCM_DHB_STEP_REFS,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_PCM_DHB_LOCAL_RECEIVED_ZIP_REFS),
        "support_material_refs": P7_R54_AHR_POST_PCM_DHB_SUPPORT_MATERIAL_REFS,
        "not_stage_refs": P7_R54_AHR_POST_PCM_DHB_NOT_STAGE_REFS,
        "claim_boundary_refs": P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS,
        "not_claimed_boundary_refs": P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS,
        "fixed_non_promotion_refs": P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS,
        "explicit_pcm_op08_closed_material_required": P7_R54_AHR_POST_PCM_DHB_EXPLICIT_PCM_OP08_CLOSED_MATERIAL_REQUIRED,
        "pcm_op08_material_synthesis_allowed_here": P7_R54_AHR_POST_PCM_DHB_PCM_OP08_MATERIAL_SYNTHESIS_ALLOWED_HERE,
        "pcm_builder_call_allowed_here": P7_R54_AHR_POST_PCM_DHB_PCM_BUILDER_CALL_ALLOWED_HERE,
        "pcm_r11_memo_as_current_lane_allowed_here": P7_R54_AHR_POST_PCM_DHB_PCM_R11_MEMO_AS_CURRENT_LANE_ALLOWED_HERE,
        "pcm_target_green_as_current_lane_allowed_here": P7_R54_AHR_POST_PCM_DHB_PCM_TARGET_GREEN_AS_CURRENT_LANE_ALLOWED_HERE,
        "pcm_decision_table_as_single_lane_allowed_here": P7_R54_AHR_POST_PCM_DHB_PCM_DECISION_TABLE_AS_SINGLE_LANE_ALLOWED_HERE,
        "dhr_op05_call_allowed_here": P7_R54_AHR_POST_PCM_DHB_DHR_OP05_CALL_ALLOWED_HERE,
        "dhr_op05_builder_call_allowed_here": P7_R54_AHR_POST_PCM_DHB_DHR_OP05_BUILDER_CALL_ALLOWED_HERE,
        "existing_dhr_op05_builder_call_allowed_here": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_CALL_ALLOWED_HERE,
        "dhr_op06_call_allowed_here": P7_R54_AHR_POST_PCM_DHB_DHR_OP06_CALL_ALLOWED_HERE,
        "dhr_op07_materialization_allowed_here": P7_R54_AHR_POST_PCM_DHB_DHR_OP07_MATERIALIZATION_ALLOWED_HERE,
        "dmd_r52_execution_allowed_here": P7_R54_AHR_POST_PCM_DHB_DMD_R52_EXECUTION_ALLOWED_HERE,
        "actual_review_start_allowed_here": P7_R54_AHR_POST_PCM_DHB_ACTUAL_REVIEW_START_ALLOWED_HERE,
        "actual_rows_creation_allowed_here": P7_R54_AHR_POST_PCM_DHB_ACTUAL_ROWS_CREATION_ALLOWED_HERE,
        "question_need_observation_rows_creation_allowed_here": P7_R54_AHR_POST_PCM_DHB_QUESTION_NEED_OBSERVATION_ROWS_CREATION_ALLOWED_HERE,
        "repair_execution_allowed_here": P7_R54_AHR_POST_PCM_DHB_REPAIR_EXECUTION_ALLOWED_HERE,
        "raw_evidence_request_allowed_here": P7_R54_AHR_POST_PCM_DHB_RAW_EVIDENCE_REQUEST_ALLOWED_HERE,
        "p8_question_design_allowed_here": P7_R54_AHR_POST_PCM_DHB_P8_QUESTION_DESIGN_ALLOWED_HERE,
        "p8_question_implementation_allowed_here": P7_R54_AHR_POST_PCM_DHB_P8_QUESTION_IMPLEMENTATION_ALLOWED_HERE,
        "question_text_materialization_allowed_here": P7_R54_AHR_POST_PCM_DHB_QUESTION_TEXT_MATERIALIZATION_ALLOWED_HERE,
        "api_db_rn_runtime_response_key_change_allowed_here": P7_R54_AHR_POST_PCM_DHB_API_DB_RN_RUNTIME_RESPONSE_KEY_CHANGE_ALLOWED_HERE,
        "json_schema_file_creation_allowed_here": P7_R54_AHR_POST_PCM_DHB_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE,
        "p7_complete_allowed_here": P7_R54_AHR_POST_PCM_DHB_P7_COMPLETE_ALLOWED_HERE,
        "release_decision_allowed_here": P7_R54_AHR_POST_PCM_DHB_RELEASE_DECISION_ALLOWED_HERE,
        "full_backend_suite_green_claim_allowed_here": P7_R54_AHR_POST_PCM_DHB_FULL_BACKEND_SUITE_GREEN_CLAIM_ALLOWED_HERE,
        "rn_contract_green_claim_allowed_here": P7_R54_AHR_POST_PCM_DHB_RN_CONTRACT_GREEN_CLAIM_ALLOWED_HERE,
        "rn_real_device_modal_verification_claim_allowed_here": P7_R54_AHR_POST_PCM_DHB_RN_REAL_DEVICE_MODAL_VERIFICATION_CLAIM_ALLOWED_HERE,
        "allowed_pcm_op08_schema_version_ref": P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        "allowed_pcm_op08_step_ref": P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        "allowed_pcm_op08_closed_status_ref": P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        "dhr_op05_lane_ref": P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF,
        "expected_selected_pcm_next_work_class_ref": P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_WORK_CLASS_REF,
        "expected_selected_pcm_next_boundary_ref": P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_REF,
        "expected_selected_pcm_next_boundary_kind_ref": P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF,
        "expected_next_design_document_candidate_ref": P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF,
        "allowed_non_dhr_lane_refs": P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS,
        "allowed_status_refs": P7_R54_AHR_POST_PCM_DHB_ALLOWED_STATUS_REFS,
        "existing_dhr_op05_builder_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF,
        "existing_dhr_op05_assert_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF,
        "existing_dhr_op05_schema_version_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_SCHEMA_VERSION_REF,
        "existing_dhr_op05_compatibility_status_refs": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS,
        "forbidden_payload_key_refs": P7_R54_AHR_POST_PCM_DHB_FORBIDDEN_PAYLOAD_KEY_REFS,
        "no_touch_contract_keys": P7_R54_AHR_POST_PCM_DHB_NO_TOUCH_CONTRACT_KEYS,
        "body_free_marker_refs": P7_R54_AHR_POST_PCM_DHB_BODY_FREE_MARKER_REFS,
        "promotion_claim_field_refs": P7_R54_AHR_POST_PCM_DHB_PROMOTION_CLAIM_FIELD_REFS,
        "required_false_flag_refs": P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS,
        "target_test_ref_refs": P7_R54_AHR_POST_PCM_DHB_TARGET_TEST_REF_REFS,
        "selected_regression_test_ref_refs": P7_R54_AHR_POST_PCM_DHB_SELECTED_REGRESSION_TEST_REF_REFS,
        "compileall_target_ref_refs": P7_R54_AHR_POST_PCM_DHB_COMPILEALL_TARGET_REF_REFS,
        "validation_command_summary_refs": P7_R54_AHR_POST_PCM_DHB_VALIDATION_COMMAND_SUMMARY_REFS,
        "public_contract": public_contract_flags(),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "next_required_step": P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
        "body_free": True,
    }
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS:
        data[key] = False
    return data


def assert_p7_r54_ahr_post_pcm_dhb_r1_helper_skeleton_constants_summary_contract(
    data: Mapping[str, Any],
) -> bool:
    """Validate the R0/R1 constants summary without validating future OP00+ output."""

    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_R1_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_PCM_DHB_R1_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 schema version mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 operation step mismatch")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must remain body-free")
    if data.get("source_mode") != P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must not require/check GitHub")
    if tuple(data.get("implemented_step_refs", ())) != P7_R54_AHR_POST_PCM_DHB_R0_R1_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_step_refs", ())) != P7_R54_AHR_POST_PCM_DHB_R0_R1_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must leave DHB-OP00..OP08 not yet implemented")
    if tuple(data.get("dhb_step_refs", ())) != P7_R54_AHR_POST_PCM_DHB_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 DHB step refs mismatch")
    if data.get("explicit_pcm_op08_closed_material_required") is not True:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must require explicit future closed PCM-OP08 material")
    if data.get("pcm_op08_material_synthesis_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must not allow PCM-OP08 material synthesis")
    if data.get("pcm_builder_call_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must not allow PCM builder calls")
    if data.get("pcm_r11_memo_as_current_lane_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must not allow PCM R11 memo as current lane")
    if data.get("pcm_target_green_as_current_lane_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must not allow target green as current lane")
    if data.get("pcm_decision_table_as_single_lane_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must reject PCM decision table as a single lane")
    if data.get("allowed_pcm_op08_schema_version_ref") != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 PCM-OP08 schema ref mismatch")
    if data.get("allowed_pcm_op08_step_ref") != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 PCM-OP08 step ref mismatch")
    if data.get("allowed_pcm_op08_closed_status_ref") != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 PCM-OP08 closed status ref mismatch")
    if data.get("dhr_op05_lane_ref") != P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 DHR-OP05 lane ref mismatch")
    if tuple(data.get("allowed_non_dhr_lane_refs", ())) != P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 non-DHR lane refs mismatch")
    if tuple(data.get("allowed_status_refs", ())) != P7_R54_AHR_POST_PCM_DHB_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 allowed status refs mismatch")
    if data.get("existing_dhr_op05_builder_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 existing DHR-OP05 builder ref mismatch")
    if data.get("existing_dhr_op05_assert_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 existing DHR-OP05 assert ref mismatch")
    if data.get("existing_dhr_op05_builder_call_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 must not allow existing DHR-OP05 builder call")
    if tuple(data.get("forbidden_payload_key_refs", ())) != P7_R54_AHR_POST_PCM_DHB_FORBIDDEN_PAYLOAD_KEY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 forbidden payload refs mismatch")
    if tuple(data.get("no_touch_contract_keys", ())) != P7_R54_AHR_POST_PCM_DHB_NO_TOUCH_CONTRACT_KEYS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 no-touch keys mismatch")
    if tuple(data.get("promotion_claim_field_refs", ())) != P7_R54_AHR_POST_PCM_DHB_PROMOTION_CLAIM_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 promotion claim refs mismatch")
    if tuple(data.get("target_test_ref_refs", ())) != P7_R54_AHR_POST_PCM_DHB_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 target test refs mismatch")
    if tuple(data.get("compileall_target_ref_refs", ())) != P7_R54_AHR_POST_PCM_DHB_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 compileall target refs mismatch")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 public contract changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-R1 next step must be DHB-OP00")
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-R1 forbidden promotion flag set: {key}")
    for key in (
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "repair_execution_allowed_here",
        "raw_evidence_request_allowed_here",
        "p8_question_design_allowed_here",
        "p8_question_implementation_allowed_here",
        "question_text_materialization_allowed_here",
        "api_db_rn_runtime_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "p7_complete_allowed_here",
        "release_decision_allowed_here",
        "full_backend_suite_green_claim_allowed_here",
        "rn_contract_green_claim_allowed_here",
        "rn_real_device_modal_verification_claim_allowed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-R1 no-execution flag changed: {key}")
    return True



# ---------------------------------------------------------------------------
# R2: DHB-OP00 / DHB-OP01 only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PCM_DHB_R2_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
)
P7_R54_AHR_POST_PCM_DHB_R2_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
)

P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_CLOSED_MATERIAL_REF: Final = (
    "wait_for_one_explicit_pcm_op08_closed_material_without_lane_synthesis"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_MATERIAL_INTAKE_REF: Final = (
    "repair_pcm_op08_material_intake_without_dhr_op05_promotion"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_MATERIAL_INTAKE_REF: Final = (
    "blocked_pcm_op08_material_leak_promotion_or_autorun"
)

P7_R54_AHR_POST_PCM_DHB_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)

P7_R54_AHR_POST_PCM_DHB_OP00_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key != "dhb_op00_implemented"
)
P7_R54_AHR_POST_PCM_DHB_OP01_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key not in {"dhb_op00_implemented", "dhb_op01_implemented"}
)

P7_R54_AHR_POST_PCM_DHB_MULTI_LANE_MATERIAL_KEY_REFS: Final[tuple[str, ...]] = (
    "decision_table",
    "lane_decision_table",
    "pcm_r11_decision_table",
    "all_lane_summary",
    "all_lanes_summary",
    "six_outcome_summary",
    "multi_lane_summary",
    "all_lanes",
)
P7_R54_AHR_POST_PCM_DHB_PCM_OP08_MINIMUM_SHAPE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "operation_step_ref",
    "body_free",
    "selected_pcm_next_boundary_not_executed",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
)

P7_R54_AHR_POST_PCM_DHB_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_design_target_ref", "boundary_prefix_ref", "boundary_prefix_meaning_ref",
    "expected_from_pcm_op08_ref", "expected_next_required_step_ref",
    "dhb_scope_refrozen", "explicit_pcm_op08_closed_material_required",
    "pcm_op08_material_synthesis_allowed_here", "pcm_builder_call_allowed_here", "pcm_r11_memo_as_current_lane_allowed_here", "pcm_target_green_as_current_lane_allowed_here", "pcm_decision_table_as_single_lane_allowed_here",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "existing_dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dhr_op07_materialization_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "actual_rows_creation_allowed_here", "question_need_observation_rows_creation_allowed_here", "repair_execution_allowed_here", "raw_evidence_request_allowed_here", "p8_question_design_allowed_here", "p8_question_implementation_allowed_here", "question_text_materialization_allowed_here", "api_db_rn_runtime_response_key_change_allowed_here", "json_schema_file_creation_allowed_here", "p7_complete_allowed_here", "release_decision_allowed_here", "full_backend_suite_green_claim_allowed_here", "rn_contract_green_claim_allowed_here", "rn_real_device_modal_verification_claim_allowed_here",
    "dhb_op00_scope_confirmed", "dhb_op00_explicit_pcm_op08_boundary_confirmed", "dhb_op00_no_execution_boundary_confirmed", "dhb_op00_no_touch_boundary_confirmed", "dhb_op00_no_promotion_boundary_confirmed",
    "source_mode_local_received_zip_only_confirmed", "github_connection_check_skipped_by_instruction", "github_connection_check_performed",
    "dhb_op00_does_not_intake_pcm_op08_material", "dhb_op00_does_not_synthesize_pcm_op08_material", "dhb_op00_does_not_use_pcm_r11_decision_table_as_current_lane", "dhb_op00_does_not_execute_selected_pcm_next_boundary", "dhb_op00_does_not_call_dhr_op05", "dhb_op00_does_not_start_p8_question_design", "dhb_op00_does_not_change_api_db_rn_runtime_response_key", "dhb_op00_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", *P7_R54_AHR_POST_PCM_DHB_OP00_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PCM_DHB_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_material_present", "op00_contract_valid", "op00_schema_version", "op00_material_ref", "op00_next_required_step",
    "explicit_pcm_op08_closed_material_required", "pcm_op08_material_synthesis_allowed_here", "pcm_builder_call_allowed_here", "pcm_r11_memo_as_current_lane_allowed_here", "pcm_target_green_as_current_lane_allowed_here", "pcm_decision_table_as_single_lane_allowed_here", "pcm_op08_material_synthesized_here", "pcm_builder_called_here", "pcm_r11_memo_used_as_current_lane_here", "pcm_target_green_used_as_current_lane_here", "pcm_decision_table_used_as_single_lane_here",
    "pcm_op08_material_present", "pcm_op08_shaped_material_valid", "pcm_op08_schema_version", "pcm_op08_material_ref", "pcm_op08_operation_step_ref", "pcm_op08_status_ref", "bodyfree_post_pnt_closed_material_confirmation_closure_status_ref", "pcm_op08_closed_bodyfree_stopped",
    "selected_pnt_lane_ref", "selected_pnt_lane_ref_present", "selected_pcm_next_work_class_ref", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_not_executed", "selected_pcm_next_boundary_not_executed_present", "next_design_document_candidate_ref", "next_design_document_allowed",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "pcm_op08_input_forbidden_payload_key_path_refs", "pcm_op08_input_forbidden_payload_key_path_count", "pcm_op08_input_body_like_value_path_refs", "pcm_op08_input_body_like_value_path_count", "pcm_op08_input_promotion_claim_refs", "pcm_op08_input_promotion_claim_ref_count", "pcm_op08_input_no_touch_mutation_path_refs", "pcm_op08_input_no_touch_mutation_path_count", "pcm_op08_input_multi_lane_material_key_path_refs", "pcm_op08_input_multi_lane_material_key_path_count",
    "dhb_op01_status_ref", "bodyfree_pcm_op08_closed_material_intake_status_ref", "dhb_op01_allowed_status_refs", "dhb_op01_allowed_status_ref_count",
    "dhb_op01_ready_for_contract_validation", "dhb_op01_waiting_for_explicit_pcm_op08_closed_material", "dhb_op01_repair_required", "dhb_op01_bodyfree_leak_promotion_or_autorun_blocked", "dhb_op01_reason_refs", "dhb_op01_reason_ref_count", "dhb_op01_blocker_refs", "dhb_op01_blocker_ref_count",
    "dhb_op01_does_not_validate_pcm_op08_contract", "dhb_op01_does_not_confirm_dhr_op05_lane", "dhb_op01_does_not_materialize_dhr_op05_handoff_envelope", "dhb_op01_does_not_execute_selected_pcm_next_boundary", "dhb_op01_does_not_call_dhr_op05", "dhb_op01_does_not_call_dhr_op06", "dhb_op01_does_not_execute_dmd_r52_or_release", "dhb_op01_does_not_start_actual_review", "dhb_op01_does_not_request_raw_evidence", "dhb_op01_does_not_execute_repair", "dhb_op01_does_not_start_p8_question_design", "dhb_op01_does_not_change_api_db_rn_runtime_response_key", "dhb_op01_does_not_materialize_p8_question_text", "dhb_op01_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", *P7_R54_AHR_POST_PCM_DHB_OP01_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_PCM_DHB_DEFAULT_REVIEW_SESSION_ID,
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


def _false_flags(
    false_flag_refs: Sequence[str] = P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS,
) -> dict[str, bool]:
    return {key: False for key in false_flag_refs}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PCM_DHB_NO_TOUCH_CONTRACT_KEYS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_PCM_DHB_BODY_FREE_MARKER_REFS}


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
            if key_text in P7_R54_AHR_POST_PCM_DHB_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_body_like_value_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    suspect_tokens = ("raw", "body", "comment", "question", "answer", "reviewer", "stdout", "stderr", "traceback", "hash", "path")
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PCM_DHB_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            elif (
                isinstance(child, str)
                and child.strip()
                and "bodyfree" not in key_lower
                and key_lower != "body_free"
                and any(token in key_lower for token in suspect_tokens)
            ):
                paths.append(child_path)
            elif (
                child is True
                and "bodyfree" not in key_lower
                and key_lower != "body_free"
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
            if key_text in P7_R54_AHR_POST_PCM_DHB_PROMOTION_CLAIM_FIELD_REFS and child is True:
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
            if key_text in P7_R54_AHR_POST_PCM_DHB_NO_TOUCH_CONTRACT_KEYS and child is True:
                paths.append(child_path)
            paths.extend(_scan_no_touch_mutation_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_no_touch_mutation_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_multi_lane_material_key_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PCM_DHB_MULTI_LANE_MATERIAL_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_multi_lane_material_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_multi_lane_material_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _bodyfree_no_touch_scan_quads(value: Any, *, path: str) -> tuple[list[str], list[str], list[str], list[str]]:
    return (
        _dedupe_clean_refs(_scan_forbidden_payload_key_paths(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_body_like_value_paths(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_promotion_claim_refs(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_no_touch_mutation_paths(value, path=path), max_length=340),
    )


def _assert_base_bodyfree_boundary(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    operation_step_ref: str,
    source: str,
    required_false_flag_refs: Sequence[str],
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version mismatch")
    if data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step mismatch")
    if data.get("phase") != P7_R54_AHR_POST_PCM_DHB_PHASE:
        raise ValueError(f"{source} phase mismatch")
    if data.get("scope") != P7_R54_AHR_POST_PCM_DHB_SCOPE:
        raise ValueError(f"{source} scope mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE:
        raise ValueError(f"{source} source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require/check GitHub")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError(f"{source} public contract changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if tuple((data.get("dhb_no_touch_contract") or {}).keys()) != tuple(P7_R54_AHR_POST_PCM_DHB_NO_TOUCH_CONTRACT_KEYS):
        raise ValueError(f"{source} no-touch contract keys changed")
    if any(value is not False for value in (data.get("dhb_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract must stay false")
    if tuple((data.get("body_free_markers") or {}).keys()) != tuple(P7_R54_AHR_POST_PCM_DHB_BODY_FREE_MARKER_REFS):
        raise ValueError(f"{source} body-free marker keys changed")
    if any(value is not False for value in (data.get("body_free_markers") or {}).values()):
        raise ValueError(f"{source} body-free markers must stay false")
    if any(key in P7_R54_AHR_POST_PCM_DHB_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")
    for key in required_false_flag_refs:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")


def _op00_contract_valid(op00: Mapping[str, Any] | None) -> bool:
    if not isinstance(op00, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11_contract(op00) is True
    except ValueError:
        return False


def _pcm_op08_status_ref(op08: Mapping[str, Any]) -> str:
    return _clean_ref(
        op08.get("pcm_op08_status_ref") or op08.get("bodyfree_post_pnt_closed_material_confirmation_closure_status_ref"),
        default="pcm_op08_status_missing",
        max_length=360,
    )


def _pcm_op08_minimum_shape_blockers(op08: Mapping[str, Any] | None) -> list[str]:
    blockers: list[str] = []
    if not isinstance(op08, Mapping):
        return ["explicit_pcm_op08_material_not_mapping"]
    for key in P7_R54_AHR_POST_PCM_DHB_PCM_OP08_MINIMUM_SHAPE_FIELD_REFS:
        if key not in op08:
            blockers.append(f"pcm_op08_required_shape_field_missing:{key}")
    if op08.get("schema_version") != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF:
        blockers.append("pcm_op08_schema_version_mismatch")
    if op08.get("operation_step_ref") != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF:
        blockers.append("pcm_op08_operation_step_ref_mismatch")
    if op08.get("body_free") is not True:
        blockers.append("pcm_op08_body_free_not_true")
    if _pcm_op08_status_ref(op08) != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF:
        blockers.append("pcm_op08_not_closed_stopped")
    if op08.get("selected_pcm_next_boundary_not_executed") is not True:
        blockers.append("pcm_op08_selected_pcm_next_boundary_not_executed_not_true")
    for key in (
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "json_schema_file_creation_allowed_here",
    ):
        if key in op08 and op08.get(key) is not False:
            blockers.append(f"pcm_op08_forbidden_execution_allowance_not_false:{key}")
    if "api_db_rn_response_key_change_allowed_here" in op08 and op08.get("api_db_rn_response_key_change_allowed_here") is not False:
        blockers.append("pcm_op08_forbidden_execution_allowance_not_false:api_db_rn_response_key_change_allowed_here")
    if "api_db_rn_runtime_response_key_change_allowed_here" in op08 and op08.get("api_db_rn_runtime_response_key_change_allowed_here") is not False:
        blockers.append("pcm_op08_forbidden_execution_allowance_not_false:api_db_rn_runtime_response_key_change_allowed_here")
    return blockers


def _op01_status_reason_blocker_next(
    *,
    op00_valid: bool,
    pcm_op08_present: bool,
    pcm_op08_shape_blockers: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    multi_lane_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths:
        reasons.append("bodyfree_leak_promotion_or_autorun_detected_in_pcm_op08_intake_input")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[3],
            reasons,
            blockers,
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_MATERIAL_INTAKE_REF,
        )
    if not pcm_op08_present:
        reasons.append("explicit_pcm_op08_closed_material_missing")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[1],
            reasons,
            blockers,
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_CLOSED_MATERIAL_REF,
        )
    if not op00_valid:
        reasons.append("op00_scope_refreeze_missing_or_invalid_before_pcm_op08_intake")
        blockers.append("op00_contract_valid_false")
    if multi_lane_paths:
        reasons.append("multi_lane_or_decision_table_material_cannot_be_used_as_explicit_pcm_op08_selected_material")
        blockers.extend(multi_lane_paths)
    if pcm_op08_shape_blockers:
        reasons.append("explicit_pcm_op08_material_shape_invalid")
        blockers.extend(pcm_op08_shape_blockers)
    if blockers:
        return (
            P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[2],
            reasons,
            blockers,
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_MATERIAL_INTAKE_REF,
        )
    reasons.append("explicit_pcm_op08_closed_material_intake_ready_for_contract_validation")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[0],
        reasons,
        blockers,
        P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    )


def build_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build DHB-OP00 scope / no-execution refreeze material after PCM R11."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_PCM_DHB_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_PCM_DHB_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_PCM_DHB_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_PCM_DHB_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_pcm_op08_ref": P7_R54_AHR_POST_PCM_DHB_EXPECTED_FROM_PCM_OP08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
        "dhb_scope_refrozen": True,
        "explicit_pcm_op08_closed_material_required": True,
        "pcm_op08_material_synthesis_allowed_here": False,
        "pcm_builder_call_allowed_here": False,
        "pcm_r11_memo_as_current_lane_allowed_here": False,
        "pcm_target_green_as_current_lane_allowed_here": False,
        "pcm_decision_table_as_single_lane_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "existing_dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dhr_op07_materialization_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "actual_rows_creation_allowed_here": False,
        "question_need_observation_rows_creation_allowed_here": False,
        "repair_execution_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "p8_question_implementation_allowed_here": False,
        "question_text_materialization_allowed_here": False,
        "api_db_rn_runtime_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "p7_complete_allowed_here": False,
        "release_decision_allowed_here": False,
        "full_backend_suite_green_claim_allowed_here": False,
        "rn_contract_green_claim_allowed_here": False,
        "rn_real_device_modal_verification_claim_allowed_here": False,
        "dhb_op00_scope_confirmed": True,
        "dhb_op00_explicit_pcm_op08_boundary_confirmed": True,
        "dhb_op00_no_execution_boundary_confirmed": True,
        "dhb_op00_no_touch_boundary_confirmed": True,
        "dhb_op00_no_promotion_boundary_confirmed": True,
        "source_mode_local_received_zip_only_confirmed": True,
        "github_connection_check_skipped_by_instruction": True,
        "github_connection_check_performed": False,
        "dhb_op00_does_not_intake_pcm_op08_material": True,
        "dhb_op00_does_not_synthesize_pcm_op08_material": True,
        "dhb_op00_does_not_use_pcm_r11_decision_table_as_current_lane": True,
        "dhb_op00_does_not_execute_selected_pcm_next_boundary": True,
        "dhb_op00_does_not_call_dhr_op05": True,
        "dhb_op00_does_not_start_p8_question_design": True,
        "dhb_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "dhb_op00_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP00_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op00_scope_no_execution_refreeze_after_pcm_r11_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP00 scope / no-execution refreeze contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP00_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP00")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP00",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP00_REQUIRED_FALSE_FLAG_REFS,
    )
    if data.get("dhb_op00_implemented") is not True:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 implemented flag must be true after R2")
    for key in (
        "dhb_scope_refrozen",
        "explicit_pcm_op08_closed_material_required",
        "dhb_op00_scope_confirmed",
        "dhb_op00_explicit_pcm_op08_boundary_confirmed",
        "dhb_op00_no_execution_boundary_confirmed",
        "dhb_op00_no_touch_boundary_confirmed",
        "dhb_op00_no_promotion_boundary_confirmed",
        "source_mode_local_received_zip_only_confirmed",
        "github_connection_check_skipped_by_instruction",
        "dhb_op00_does_not_intake_pcm_op08_material",
        "dhb_op00_does_not_synthesize_pcm_op08_material",
        "dhb_op00_does_not_use_pcm_r11_decision_table_as_current_lane",
        "dhb_op00_does_not_execute_selected_pcm_next_boundary",
        "dhb_op00_does_not_call_dhr_op05",
        "dhb_op00_does_not_start_p8_question_design",
        "dhb_op00_does_not_change_api_db_rn_runtime_response_key",
        "dhb_op00_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP00 required true boundary changed: {key}")
    for key in (
        "pcm_op08_material_synthesis_allowed_here",
        "pcm_builder_call_allowed_here",
        "pcm_r11_memo_as_current_lane_allowed_here",
        "pcm_target_green_as_current_lane_allowed_here",
        "pcm_decision_table_as_single_lane_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "repair_execution_allowed_here",
        "raw_evidence_request_allowed_here",
        "p8_question_design_allowed_here",
        "p8_question_implementation_allowed_here",
        "question_text_materialization_allowed_here",
        "api_db_rn_runtime_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "p7_complete_allowed_here",
        "release_decision_allowed_here",
        "full_backend_suite_green_claim_allowed_here",
        "rn_contract_green_claim_allowed_here",
        "rn_real_device_modal_verification_claim_allowed_here",
        "github_connection_check_performed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP00 forbidden allowance changed: {key}")
    for field, count_field in (
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP00 {count_field} changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 next step must be DHB-OP01")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 not-claimed boundary refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP00 fixed non-promotion refs changed")
    return True


def build_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake(
    explicit_pcm_op08_closed_material: Mapping[str, Any] | None = None,
    op00_scope_refreeze: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Intake one explicit PCM-OP08 closed material without lane inference or DHR calls."""

    op00 = op00_scope_refreeze if isinstance(op00_scope_refreeze, Mapping) else {}
    pcm_op08 = explicit_pcm_op08_closed_material if isinstance(explicit_pcm_op08_closed_material, Mapping) else {}
    op00_present = isinstance(op00_scope_refreeze, Mapping)
    op00_valid = _op00_contract_valid(op00_scope_refreeze)
    pcm_op08_present = isinstance(explicit_pcm_op08_closed_material, Mapping)
    shape_blockers = _pcm_op08_minimum_shape_blockers(explicit_pcm_op08_closed_material if pcm_op08_present else None)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(
        explicit_pcm_op08_closed_material or {},
        path="explicit_pcm_op08_closed_material",
    )
    multi_lane_paths = _dedupe_clean_refs(
        _scan_multi_lane_material_key_paths(explicit_pcm_op08_closed_material or {}, path="explicit_pcm_op08_closed_material"),
        max_length=340,
    )
    status_ref, reason_refs, blocker_refs, next_required_step = _op01_status_reason_blocker_next(
        op00_valid=op00_valid,
        pcm_op08_present=pcm_op08_present,
        pcm_op08_shape_blockers=shape_blockers,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        multi_lane_paths=multi_lane_paths,
    )
    ready = status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[0]
    waiting = status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[1]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[2]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[3]
    session_id = _safe_review_session_id(
        review_session_id
        or pcm_op08.get("review_session_id")
        or op00.get("review_session_id")
    )
    pcm_status = _pcm_op08_status_ref(pcm_op08) if pcm_op08_present else "pcm_op08_status_missing"
    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_material_present": op00_present,
        "op00_contract_valid": op00_valid,
        "op00_schema_version": _clean_ref(op00.get("schema_version"), default="dhb_op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id"), default="dhb_op00_material_missing", max_length=300),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step"), default="dhb_op00_next_required_step_missing", max_length=360),
        "explicit_pcm_op08_closed_material_required": True,
        "pcm_op08_material_synthesis_allowed_here": False,
        "pcm_builder_call_allowed_here": False,
        "pcm_r11_memo_as_current_lane_allowed_here": False,
        "pcm_target_green_as_current_lane_allowed_here": False,
        "pcm_decision_table_as_single_lane_allowed_here": False,
        "pcm_op08_material_synthesized_here": False,
        "pcm_builder_called_here": False,
        "pcm_r11_memo_used_as_current_lane_here": False,
        "pcm_target_green_used_as_current_lane_here": False,
        "pcm_decision_table_used_as_single_lane_here": False,
        "pcm_op08_material_present": pcm_op08_present,
        "pcm_op08_shaped_material_valid": bool(pcm_op08_present and not shape_blockers and not multi_lane_paths),
        "pcm_op08_schema_version": _clean_ref(pcm_op08.get("schema_version"), default="pcm_op08_schema_missing", max_length=260),
        "pcm_op08_material_ref": _clean_ref(pcm_op08.get("material_id"), default="pcm_op08_material_missing", max_length=300),
        "pcm_op08_operation_step_ref": _clean_ref(pcm_op08.get("operation_step_ref"), default="pcm_op08_operation_step_missing", max_length=360),
        "pcm_op08_status_ref": pcm_status,
        "bodyfree_post_pnt_closed_material_confirmation_closure_status_ref": _clean_ref(pcm_op08.get("bodyfree_post_pnt_closed_material_confirmation_closure_status_ref"), default=pcm_status, max_length=360),
        "pcm_op08_closed_bodyfree_stopped": pcm_status == P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        "selected_pnt_lane_ref": _clean_ref(pcm_op08.get("selected_pnt_lane_ref"), default="selected_pnt_lane_missing", max_length=360),
        "selected_pnt_lane_ref_present": bool(pcm_op08.get("selected_pnt_lane_ref")),
        "selected_pcm_next_work_class_ref": _clean_ref(pcm_op08.get("selected_pcm_next_work_class_ref"), default="selected_pcm_next_work_class_missing", max_length=360),
        "selected_pcm_next_boundary_ref": _clean_ref(pcm_op08.get("selected_pcm_next_boundary_ref"), default="selected_pcm_next_boundary_missing", max_length=420),
        "selected_pcm_next_boundary_kind_ref": _clean_ref(pcm_op08.get("selected_pcm_next_boundary_kind_ref"), default="selected_pcm_next_boundary_kind_missing", max_length=420),
        "selected_pcm_next_boundary_not_executed": bool(pcm_op08.get("selected_pcm_next_boundary_not_executed") is True),
        "selected_pcm_next_boundary_not_executed_present": "selected_pcm_next_boundary_not_executed" in pcm_op08,
        "next_design_document_candidate_ref": _clean_ref(pcm_op08.get("next_design_document_candidate_ref"), default="next_design_document_candidate_missing", max_length=420),
        "next_design_document_allowed": bool(pcm_op08.get("next_design_document_allowed") is True),
        "dhr_op05_not_called": bool(pcm_op08.get("dhr_op05_not_called") is True),
        "dhr_op06_not_called": bool(pcm_op08.get("dhr_op06_not_called") is True),
        "dmd_r52_not_executed": bool(pcm_op08.get("dmd_r52_not_executed") is True),
        "actual_review_not_started": bool(pcm_op08.get("actual_review_not_started") is True),
        "p5_p6_p8_p7_release_not_started": bool(pcm_op08.get("p5_p6_p8_p7_release_not_started") is True),
        "p8_question_design_not_started": bool(pcm_op08.get("p8_question_design_not_started") is True),
        "p8_question_implementation_not_started": bool(pcm_op08.get("p8_question_implementation_not_started") is True),
        "api_db_rn_runtime_response_key_not_changed": bool(pcm_op08.get("api_db_rn_runtime_response_key_not_changed") is True),
        "pcm_op08_input_forbidden_payload_key_path_refs": forbidden_paths,
        "pcm_op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "pcm_op08_input_body_like_value_path_refs": body_like_paths,
        "pcm_op08_input_body_like_value_path_count": len(body_like_paths),
        "pcm_op08_input_promotion_claim_refs": promotion_claims,
        "pcm_op08_input_promotion_claim_ref_count": len(promotion_claims),
        "pcm_op08_input_no_touch_mutation_path_refs": no_touch_paths,
        "pcm_op08_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pcm_op08_input_multi_lane_material_key_path_refs": multi_lane_paths,
        "pcm_op08_input_multi_lane_material_key_path_count": len(multi_lane_paths),
        "dhb_op01_status_ref": status_ref,
        "bodyfree_pcm_op08_closed_material_intake_status_ref": status_ref,
        "dhb_op01_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS),
        "dhb_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS),
        "dhb_op01_ready_for_contract_validation": ready,
        "dhb_op01_waiting_for_explicit_pcm_op08_closed_material": waiting,
        "dhb_op01_repair_required": repair,
        "dhb_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "dhb_op01_reason_refs": _dedupe_clean_refs(reason_refs, max_length=360),
        "dhb_op01_reason_ref_count": len(_dedupe_clean_refs(reason_refs, max_length=360)),
        "dhb_op01_blocker_refs": _dedupe_clean_refs(blocker_refs, max_length=360),
        "dhb_op01_blocker_ref_count": len(_dedupe_clean_refs(blocker_refs, max_length=360)),
        "dhb_op01_does_not_validate_pcm_op08_contract": True,
        "dhb_op01_does_not_confirm_dhr_op05_lane": True,
        "dhb_op01_does_not_materialize_dhr_op05_handoff_envelope": True,
        "dhb_op01_does_not_execute_selected_pcm_next_boundary": True,
        "dhb_op01_does_not_call_dhr_op05": True,
        "dhb_op01_does_not_call_dhr_op06": True,
        "dhb_op01_does_not_execute_dmd_r52_or_release": True,
        "dhb_op01_does_not_start_actual_review": True,
        "dhb_op01_does_not_request_raw_evidence": True,
        "dhb_op01_does_not_execute_repair": True,
        "dhb_op01_does_not_start_p8_question_design": True,
        "dhb_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "dhb_op01_does_not_materialize_p8_question_text": True,
        "dhb_op01_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP01_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP01 explicit PCM-OP08 closed material intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP01_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP01")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP01",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP01_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("dhb_op00_implemented", "dhb_op01_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP01 implemented flag must be true after R2: {key}")
    if data.get("op00_contract_valid") is True and data.get("op00_next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 OP00 next step changed")
    if data.get("bodyfree_pcm_op08_closed_material_intake_status_ref") != data.get("dhb_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 status alias changed")
    if tuple(data.get("dhb_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 allowed status refs changed")
    if data.get("dhb_op01_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 allowed status count changed")
    for key in (
        "explicit_pcm_op08_closed_material_required",
        "dhb_op01_does_not_validate_pcm_op08_contract",
        "dhb_op01_does_not_confirm_dhr_op05_lane",
        "dhb_op01_does_not_materialize_dhr_op05_handoff_envelope",
        "dhb_op01_does_not_execute_selected_pcm_next_boundary",
        "dhb_op01_does_not_call_dhr_op05",
        "dhb_op01_does_not_call_dhr_op06",
        "dhb_op01_does_not_execute_dmd_r52_or_release",
        "dhb_op01_does_not_start_actual_review",
        "dhb_op01_does_not_request_raw_evidence",
        "dhb_op01_does_not_execute_repair",
        "dhb_op01_does_not_start_p8_question_design",
        "dhb_op01_does_not_change_api_db_rn_runtime_response_key",
        "dhb_op01_does_not_materialize_p8_question_text",
        "dhb_op01_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP01 required true boundary changed: {key}")
    for key in (
        "pcm_op08_material_synthesis_allowed_here",
        "pcm_builder_call_allowed_here",
        "pcm_r11_memo_as_current_lane_allowed_here",
        "pcm_target_green_as_current_lane_allowed_here",
        "pcm_decision_table_as_single_lane_allowed_here",
        "pcm_op08_material_synthesized_here",
        "pcm_builder_called_here",
        "pcm_r11_memo_used_as_current_lane_here",
        "pcm_target_green_used_as_current_lane_here",
        "pcm_decision_table_used_as_single_lane_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP01 forbidden claim changed: {key}")
    for field, count_field in (
        ("pcm_op08_input_forbidden_payload_key_path_refs", "pcm_op08_input_forbidden_payload_key_path_count"),
        ("pcm_op08_input_body_like_value_path_refs", "pcm_op08_input_body_like_value_path_count"),
        ("pcm_op08_input_promotion_claim_refs", "pcm_op08_input_promotion_claim_ref_count"),
        ("pcm_op08_input_no_touch_mutation_path_refs", "pcm_op08_input_no_touch_mutation_path_count"),
        ("pcm_op08_input_multi_lane_material_key_path_refs", "pcm_op08_input_multi_lane_material_key_path_count"),
        ("dhb_op01_reason_refs", "dhb_op01_reason_ref_count"),
        ("dhb_op01_blocker_refs", "dhb_op01_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP01 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 not-claimed boundary refs changed")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 not-yet steps changed")
    status_ref = data.get("dhb_op01_status_ref")
    flags = [
        data.get("dhb_op01_ready_for_contract_validation") is True,
        data.get("dhb_op01_waiting_for_explicit_pcm_op08_closed_material") is True,
        data.get("dhb_op01_repair_required") is True,
        data.get("dhb_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 ready branch next step changed")
        for key in (
            "op00_contract_valid",
            "pcm_op08_material_present",
            "pcm_op08_shaped_material_valid",
            "pcm_op08_closed_bodyfree_stopped",
            "selected_pcm_next_boundary_not_executed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP01 ready required true field changed: {key}")
        if data.get("pcm_op08_schema_version") != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 ready schema version mismatch")
        if data.get("pcm_op08_operation_step_ref") != P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 ready operation step mismatch")
        for field in (
            "pcm_op08_input_forbidden_payload_key_path_refs",
            "pcm_op08_input_body_like_value_path_refs",
            "pcm_op08_input_promotion_claim_refs",
            "pcm_op08_input_no_touch_mutation_path_refs",
            "pcm_op08_input_multi_lane_material_key_path_refs",
        ):
            if data.get(field):
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP01 ready branch scan refs must be empty: {field}")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_CLOSED_MATERIAL_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 wait branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_MATERIAL_INTAKE_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_MATERIAL_INTAKE_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 blocked branch next step changed")
    else:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP01 unknown status ref")
    if status_ref != P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[3]:
        for field in (
            "pcm_op08_input_forbidden_payload_key_path_refs",
            "pcm_op08_input_body_like_value_path_refs",
            "pcm_op08_input_promotion_claim_refs",
            "pcm_op08_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP01 unexpected body/no-touch scan refs outside blocked branch: {field}")
    return True


# ---------------------------------------------------------------------------
# R3: DHB-OP02 / DHB-OP03 only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PCM_DHB_R3_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py",
)
P7_R54_AHR_POST_PCM_DHB_R3_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
)

P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_CONTRACT_REF: Final = (
    "repair_pcm_op08_contract_material_before_dhr_op05_lane_confirmation"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_CONTRACT_REF: Final = (
    "blocked_pcm_op08_contract_leak_promotion_or_autorun_without_dhr_op05_lane_confirmation"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF: Final = (
    "follow_pcm_r11_lane_specific_decision_table_outside_dhb_without_execution"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_LANE_CONFIRMATION_REF: Final = (
    "repair_dhr_op05_lane_confirmation_inputs_before_any_dhr_op05_call"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_LANE_CONFIRMATION_REF: Final = (
    "blocked_dhr_op05_lane_confirmation_leak_promotion_or_autorun_without_next_design_promotion"
)

P7_R54_AHR_POST_PCM_DHB_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP02_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key not in {"dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented"}
)
P7_R54_AHR_POST_PCM_DHB_OP03_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhb_op00_implemented",
        "dhb_op01_implemented",
        "dhb_op02_implemented",
        "dhb_op03_implemented",
    }
)

P7_R54_AHR_POST_PCM_DHB_OP02_PCM_CONTRACT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "operation_step_ref",
    "body_free",
    "selected_pnt_lane_ref",
    "selected_pcm_next_work_class_ref",
    "selected_pcm_next_boundary_ref",
    "selected_pcm_next_boundary_kind_ref",
    "selected_pcm_next_boundary_not_executed",
    "next_design_document_candidate_ref",
    "next_design_document_allowed",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "dhr_op06_call_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "p8_question_design_allowed_here",
    "api_db_rn_runtime_response_key_change_allowed_here",
    "p7_complete",
    "release_allowed",
)

P7_R54_AHR_POST_PCM_DHB_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_material_present", "op01_contract_valid", "op01_schema_version", "op01_material_ref", "op01_status_ref", "op01_ready_for_contract_validation", "op01_next_required_step",
    "pcm_op08_contract_required_field_refs", "pcm_op08_contract_required_field_ref_count", "pcm_op08_contract_missing_field_refs", "pcm_op08_contract_missing_field_ref_count",
    "pcm_op08_schema_version", "pcm_op08_schema_version_matches", "pcm_op08_operation_step_ref", "pcm_op08_operation_step_ref_matches", "pcm_op08_status_ref", "pcm_op08_status_ref_matches", "pcm_op08_material_ref",
    "pcm_op08_body_free", "pcm_op08_closed_bodyfree_stopped", "pcm_op08_contract_field_set_valid", "pcm_op08_contract_valid",
    "selected_pnt_lane_ref", "selected_pnt_lane_ref_present", "selected_pnt_lane_ref_allowed", "selected_pcm_next_work_class_ref", "selected_pcm_next_work_class_ref_present", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_ref_present", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_kind_ref_present", "selected_pcm_next_boundary_not_executed", "selected_pcm_next_boundary_not_executed_present", "next_design_document_candidate_ref", "next_design_document_candidate_ref_present", "next_design_document_allowed", "next_design_document_allowed_present",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count", "op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count", "op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count", "op02_input_no_touch_mutation_path_refs", "op02_input_no_touch_mutation_path_count", "op02_input_multi_lane_material_key_path_refs", "op02_input_multi_lane_material_key_path_count",
    "dhb_op02_status_ref", "bodyfree_pcm_op08_contract_validation_status_ref", "dhb_op02_allowed_status_refs", "dhb_op02_allowed_status_ref_count",
    "dhb_op02_pcm_op08_contract_valid_stopped", "dhb_op02_repair_required", "dhb_op02_bodyfree_leak_promotion_or_autorun_blocked", "dhb_op02_reason_refs", "dhb_op02_reason_ref_count", "dhb_op02_blocker_refs", "dhb_op02_blocker_ref_count",
    "dhb_op02_does_not_confirm_dhr_op05_lane", "dhb_op02_does_not_materialize_dhr_op05_handoff_envelope", "dhb_op02_does_not_execute_selected_pcm_next_boundary", "dhb_op02_does_not_call_dhr_op05", "dhb_op02_does_not_call_dhr_op06", "dhb_op02_does_not_execute_dmd_r52_or_release", "dhb_op02_does_not_start_actual_review", "dhb_op02_does_not_request_raw_evidence", "dhb_op02_does_not_execute_repair", "dhb_op02_does_not_start_p8_question_design", "dhb_op02_does_not_change_api_db_rn_runtime_response_key", "dhb_op02_does_not_materialize_p8_question_text", "dhb_op02_does_not_create_json_schema_file",
    "dhr_op05_lane_confirmed_here", "dhr_op05_handoff_envelope_materialized_here", "selected_pcm_next_boundary_executed_here",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", *P7_R54_AHR_POST_PCM_DHB_OP02_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PCM_DHB_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_material_present", "op02_contract_valid", "op02_schema_version", "op02_material_ref", "op02_status_ref", "op02_next_required_step",
    "selected_pnt_lane_ref", "selected_pnt_lane_ref_present", "selected_pnt_lane_ref_allowed", "dhr_op05_lane_ref", "dhr_op05_lane_selected", "dhr_op05_lane_confirmed", "non_dhr_lane_route_preserved",
    "selected_pcm_next_work_class_ref", "selected_pcm_next_work_class_ref_matches_dhr_op05_lane", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_ref_matches_dhr_op05_lane", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_kind_ref_matches_dhr_op05_lane", "selected_pcm_next_boundary_not_executed", "next_design_document_candidate_ref", "next_design_document_candidate_ref_matches_dhr_op05_lane", "next_design_document_allowed", "next_design_document_allowed_matches_dhr_op05_lane",
    "preserved_non_dhr_lane_ref", "preserved_pcm_next_work_class_ref", "preserved_pcm_next_boundary_ref", "preserved_pcm_next_boundary_kind_ref", "preserved_next_design_document_candidate_ref", "preserved_pcm_route_without_execution", "allowed_non_dhr_lane_refs", "allowed_non_dhr_lane_ref_count",
    "dhr_op05_manual_handoff_envelope_materialized", "dhr_op05_handoff_envelope_ready", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "selected_pcm_next_boundary_execution_allowed_here",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count", "op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count", "op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count", "op03_input_no_touch_mutation_path_refs", "op03_input_no_touch_mutation_path_count", "op03_input_multi_lane_material_key_path_refs", "op03_input_multi_lane_material_key_path_count",
    "dhb_op03_status_ref", "bodyfree_dhr_op05_lane_exact_confirmation_status_ref", "dhb_op03_allowed_status_refs", "dhb_op03_allowed_status_ref_count",
    "dhb_op03_dhr_op05_lane_confirmed_stopped", "dhb_op03_not_dhr_op05_lane_route_preserved_stopped", "dhb_op03_repair_required", "dhb_op03_bodyfree_leak_promotion_or_autorun_blocked", "dhb_op03_reason_refs", "dhb_op03_reason_ref_count", "dhb_op03_blocker_refs", "dhb_op03_blocker_ref_count",
    "dhb_op03_does_not_materialize_dhr_op05_handoff_envelope", "dhb_op03_does_not_execute_selected_pcm_next_boundary", "dhb_op03_does_not_call_dhr_op05", "dhb_op03_does_not_call_dhr_op06", "dhb_op03_does_not_execute_dmd_r52_or_release", "dhb_op03_does_not_start_actual_review", "dhb_op03_does_not_request_raw_evidence", "dhb_op03_does_not_execute_repair", "dhb_op03_does_not_start_p8_question_design", "dhb_op03_does_not_change_api_db_rn_runtime_response_key", "dhb_op03_does_not_materialize_p8_question_text", "dhb_op03_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", *P7_R54_AHR_POST_PCM_DHB_OP03_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op01_contract_valid(op01: Mapping[str, Any] | None) -> bool:
    if not isinstance(op01, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op01_explicit_pcm_op08_closed_material_intake_contract(op01) is True
    except ValueError:
        return False


def _op02_contract_valid(op02: Mapping[str, Any] | None) -> bool:
    if not isinstance(op02, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation_contract(op02) is True
    except ValueError:
        return False


def _op02_missing_pcm_contract_field_refs(op01: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(op01, Mapping):
        return list(P7_R54_AHR_POST_PCM_DHB_OP02_PCM_CONTRACT_REQUIRED_FIELD_REFS)
    field_to_op01_field = {
        "schema_version": "pcm_op08_schema_version",
        "operation_step_ref": "pcm_op08_operation_step_ref",
        "body_free": "body_free",
        "selected_pnt_lane_ref": "selected_pnt_lane_ref",
        "selected_pcm_next_work_class_ref": "selected_pcm_next_work_class_ref",
        "selected_pcm_next_boundary_ref": "selected_pcm_next_boundary_ref",
        "selected_pcm_next_boundary_kind_ref": "selected_pcm_next_boundary_kind_ref",
        "selected_pcm_next_boundary_not_executed": "selected_pcm_next_boundary_not_executed",
        "next_design_document_candidate_ref": "next_design_document_candidate_ref",
        "next_design_document_allowed": "next_design_document_allowed",
        "dhr_op05_call_allowed_here": "dhr_op05_called_here",
        "dhr_op05_builder_call_allowed_here": "dhr_op05_builder_called_here",
        "dhr_op06_call_allowed_here": "dhr_op06_called_here",
        "dmd_r52_execution_allowed_here": "dmd_execution_started_here",
        "actual_review_start_allowed_here": "actual_review_started_here",
        "p8_question_design_allowed_here": "p8_question_design_started",
        "api_db_rn_runtime_response_key_change_allowed_here": "api_db_rn_runtime_response_key_not_changed",
        "p7_complete": "p7_complete",
        "release_allowed": "release_allowed",
    }
    missing: list[str] = []
    for required_field, op01_field in field_to_op01_field.items():
        if op01_field not in op01:
            missing.append(required_field)
    return missing


def _op02_status_reason_blocker_next(
    *,
    op01_present: bool,
    op01_valid: bool,
    op01_ready: bool,
    op01_blocked: bool,
    missing_field_refs: Sequence[str],
    schema_matches: bool,
    operation_step_matches: bool,
    status_matches: bool,
    pcm_op08_body_free: bool,
    pcm_op08_closed_bodyfree_stopped: bool,
    lane_present: bool,
    lane_allowed: bool,
    selected_work_class_present: bool,
    selected_boundary_present: bool,
    selected_boundary_kind_present: bool,
    selected_boundary_not_executed_present: bool,
    selected_boundary_not_executed: bool,
    next_design_present: bool,
    next_design_allowed_present: bool,
    dhr_op05_not_called: bool,
    dhr_op06_not_called: bool,
    dmd_r52_not_executed: bool,
    actual_review_not_started: bool,
    p5_p6_p8_p7_release_not_started: bool,
    p8_question_design_not_started: bool,
    p8_question_implementation_not_started: bool,
    api_db_rn_runtime_response_key_not_changed: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    multi_lane_paths: Sequence[str],
    op01_blocker_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths or op01_blocked:
        reasons.append("bodyfree_leak_promotion_or_autorun_detected_before_pcm_op08_contract_validation")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        if op01_blocked:
            blockers.append("op01_intake_blocked")
            blockers.extend(op01_blocker_refs)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[2],
            reasons,
            blockers,
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_CONTRACT_REF,
        )
    if not op01_present:
        reasons.append("op01_intake_material_missing")
        blockers.append("op01_material_present_false")
    if not op01_valid:
        reasons.append("op01_intake_contract_invalid")
        blockers.append("op01_contract_valid_false")
    if not op01_ready:
        reasons.append("op01_not_ready_for_pcm_op08_contract_validation")
        blockers.append("op01_ready_for_contract_validation_false")
    if multi_lane_paths:
        reasons.append("multi_lane_or_decision_table_material_cannot_be_validated_as_single_pcm_op08_contract")
        blockers.extend(multi_lane_paths)
    if missing_field_refs:
        reasons.append("pcm_op08_contract_required_fields_missing")
        blockers.extend(f"pcm_op08_contract_required_field_missing:{field}" for field in missing_field_refs)
    contract_checks = (
        (schema_matches, "pcm_op08_schema_version_mismatch"),
        (operation_step_matches, "pcm_op08_operation_step_ref_mismatch"),
        (status_matches, "pcm_op08_status_ref_mismatch"),
        (pcm_op08_body_free, "pcm_op08_body_free_not_true"),
        (pcm_op08_closed_bodyfree_stopped, "pcm_op08_not_closed_bodyfree_stopped"),
        (lane_present, "selected_pnt_lane_ref_missing"),
        (lane_allowed, "selected_pnt_lane_ref_unknown_or_not_allowed"),
        (selected_work_class_present, "selected_pcm_next_work_class_ref_missing"),
        (selected_boundary_present, "selected_pcm_next_boundary_ref_missing"),
        (selected_boundary_kind_present, "selected_pcm_next_boundary_kind_ref_missing"),
        (selected_boundary_not_executed_present, "selected_pcm_next_boundary_not_executed_missing"),
        (selected_boundary_not_executed, "selected_pcm_next_boundary_not_executed_not_true"),
        (next_design_present, "next_design_document_candidate_ref_missing"),
        (next_design_allowed_present, "next_design_document_allowed_missing"),
        (dhr_op05_not_called, "dhr_op05_not_called_not_true"),
        (dhr_op06_not_called, "dhr_op06_not_called_not_true"),
        (dmd_r52_not_executed, "dmd_r52_not_executed_not_true"),
        (actual_review_not_started, "actual_review_not_started_not_true"),
        (p5_p6_p8_p7_release_not_started, "p5_p6_p8_p7_release_not_started_not_true"),
        (p8_question_design_not_started, "p8_question_design_not_started_not_true"),
        (p8_question_implementation_not_started, "p8_question_implementation_not_started_not_true"),
        (api_db_rn_runtime_response_key_not_changed, "api_db_rn_runtime_response_key_not_changed_not_true"),
    )
    for ok, blocker in contract_checks:
        if not ok:
            blockers.append(blocker)
    if blockers:
        if "pcm_op08_contract_required_fields_missing" not in reasons:
            reasons.append("pcm_op08_contract_validation_repair_required")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[1],
            reasons,
            blockers,
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_CONTRACT_REF,
        )
    reasons.append("pcm_op08_contract_valid_stopped_before_dhr_op05_lane_confirmation")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[0],
        reasons,
        blockers,
        P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    )


def build_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation(
    op01_explicit_pcm_op08_closed_material_intake: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Validate the OP01 PCM-OP08 material contract without confirming DHR-OP05 lane."""

    session_id = _safe_review_session_id(review_session_id)
    op01 = op01_explicit_pcm_op08_closed_material_intake
    op01_present = isinstance(op01, Mapping)
    op01_valid = _op01_contract_valid(op01)
    op01_status_ref = _clean_ref(op01.get("dhb_op01_status_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360)
    op01_ready = bool(op01_valid and isinstance(op01, Mapping) and op01.get("dhb_op01_ready_for_contract_validation") is True)
    op01_blocked = bool(isinstance(op01, Mapping) and op01.get("dhb_op01_bodyfree_leak_promotion_or_autorun_blocked") is True)
    op01_blocker_refs = _dedupe_clean_refs(op01.get("dhb_op01_blocker_refs") if isinstance(op01, Mapping) else (), max_length=360)

    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op01 or {}, path="dhb_op01")
    multi_lane_paths = _dedupe_clean_refs(_scan_multi_lane_material_key_paths(op01 or {}, path="dhb_op01"), max_length=340)
    missing_field_refs = _dedupe_clean_refs(_op02_missing_pcm_contract_field_refs(op01), max_length=240)

    pcm_schema = _clean_ref(op01.get("pcm_op08_schema_version") if isinstance(op01, Mapping) else None, default="pcm_op08_schema_missing", max_length=300)
    pcm_operation_step = _clean_ref(op01.get("pcm_op08_operation_step_ref") if isinstance(op01, Mapping) else None, default="pcm_op08_operation_step_missing", max_length=380)
    pcm_status = _clean_ref(op01.get("pcm_op08_status_ref") if isinstance(op01, Mapping) else None, default="pcm_op08_status_missing", max_length=360)
    pcm_material_ref = _clean_ref(op01.get("pcm_op08_material_ref") if isinstance(op01, Mapping) else None, default="pcm_op08_material_missing", max_length=320)
    lane_ref = _clean_ref(op01.get("selected_pnt_lane_ref") if isinstance(op01, Mapping) else None, default="selected_pnt_lane_missing", max_length=360)
    selected_work_class_ref = _clean_ref(op01.get("selected_pcm_next_work_class_ref") if isinstance(op01, Mapping) else None, default="selected_pcm_next_work_class_missing", max_length=360)
    selected_boundary_ref = _clean_ref(op01.get("selected_pcm_next_boundary_ref") if isinstance(op01, Mapping) else None, default="selected_pcm_next_boundary_missing", max_length=420)
    selected_boundary_kind_ref = _clean_ref(op01.get("selected_pcm_next_boundary_kind_ref") if isinstance(op01, Mapping) else None, default="selected_pcm_next_boundary_kind_missing", max_length=420)
    next_design_ref = _clean_ref(op01.get("next_design_document_candidate_ref") if isinstance(op01, Mapping) else None, default="next_design_document_candidate_missing", max_length=460)

    lane_present = lane_ref not in ("", "selected_pnt_lane_missing", "missing")
    lane_allowed = (
        lane_ref == P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
        or lane_ref in P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS
    )
    selected_work_class_present = selected_work_class_ref not in ("", "selected_pcm_next_work_class_missing", "missing")
    selected_boundary_present = selected_boundary_ref not in ("", "selected_pcm_next_boundary_missing", "missing")
    selected_boundary_kind_present = selected_boundary_kind_ref not in ("", "selected_pcm_next_boundary_kind_missing", "missing")
    selected_boundary_not_executed_present = bool(isinstance(op01, Mapping) and op01.get("selected_pcm_next_boundary_not_executed_present") is True)
    selected_boundary_not_executed = bool(isinstance(op01, Mapping) and op01.get("selected_pcm_next_boundary_not_executed") is True)
    next_design_present = next_design_ref not in ("", "next_design_document_candidate_missing", "missing")
    next_design_allowed_present = bool(isinstance(op01, Mapping) and "next_design_document_allowed" in op01)
    next_design_allowed = bool(isinstance(op01, Mapping) and op01.get("next_design_document_allowed") is True)
    pcm_body_free = bool(isinstance(op01, Mapping) and op01.get("body_free") is True)
    pcm_closed_bodyfree_stopped = bool(isinstance(op01, Mapping) and op01.get("pcm_op08_closed_bodyfree_stopped") is True)

    dhr_op05_not_called = bool(isinstance(op01, Mapping) and op01.get("dhr_op05_not_called") is True)
    dhr_op06_not_called = bool(isinstance(op01, Mapping) and op01.get("dhr_op06_not_called") is True)
    dmd_r52_not_executed = bool(isinstance(op01, Mapping) and op01.get("dmd_r52_not_executed") is True)
    actual_review_not_started = bool(isinstance(op01, Mapping) and op01.get("actual_review_not_started") is True)
    p5_p6_p8_p7_release_not_started = bool(isinstance(op01, Mapping) and op01.get("p5_p6_p8_p7_release_not_started") is True)
    p8_question_design_not_started = bool(isinstance(op01, Mapping) and op01.get("p8_question_design_not_started") is True)
    p8_question_implementation_not_started = bool(isinstance(op01, Mapping) and op01.get("p8_question_implementation_not_started") is True)
    api_db_rn_runtime_response_key_not_changed = bool(isinstance(op01, Mapping) and op01.get("api_db_rn_runtime_response_key_not_changed") is True)

    status_ref, reason_refs, blocker_refs, next_required_step = _op02_status_reason_blocker_next(
        op01_present=op01_present,
        op01_valid=op01_valid,
        op01_ready=op01_ready,
        op01_blocked=op01_blocked,
        missing_field_refs=missing_field_refs,
        schema_matches=pcm_schema == P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        operation_step_matches=pcm_operation_step == P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        status_matches=pcm_status == P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        pcm_op08_body_free=pcm_body_free,
        pcm_op08_closed_bodyfree_stopped=pcm_closed_bodyfree_stopped,
        lane_present=lane_present,
        lane_allowed=lane_allowed,
        selected_work_class_present=selected_work_class_present,
        selected_boundary_present=selected_boundary_present,
        selected_boundary_kind_present=selected_boundary_kind_present,
        selected_boundary_not_executed_present=selected_boundary_not_executed_present,
        selected_boundary_not_executed=selected_boundary_not_executed,
        next_design_present=next_design_present,
        next_design_allowed_present=next_design_allowed_present,
        dhr_op05_not_called=dhr_op05_not_called,
        dhr_op06_not_called=dhr_op06_not_called,
        dmd_r52_not_executed=dmd_r52_not_executed,
        actual_review_not_started=actual_review_not_started,
        p5_p6_p8_p7_release_not_started=p5_p6_p8_p7_release_not_started,
        p8_question_design_not_started=p8_question_design_not_started,
        p8_question_implementation_not_started=p8_question_implementation_not_started,
        api_db_rn_runtime_response_key_not_changed=api_db_rn_runtime_response_key_not_changed,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        multi_lane_paths=multi_lane_paths,
        op01_blocker_refs=op01_blocker_refs,
    )
    contract_valid = status_ref == P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[0]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[1]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[2]

    reason_refs = _dedupe_clean_refs(reason_refs, max_length=360)
    blocker_refs = _dedupe_clean_refs(blocker_refs, max_length=360)
    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_material_present": op01_present,
        "op01_contract_valid": op01_valid,
        "op01_schema_version": _clean_ref(op01.get("schema_version") if isinstance(op01, Mapping) else None, default="op01_schema_missing", max_length=300),
        "op01_material_ref": _clean_ref(op01.get("material_id") if isinstance(op01, Mapping) else None, default="op01_material_missing", max_length=320),
        "op01_status_ref": op01_status_ref,
        "op01_ready_for_contract_validation": op01_ready,
        "op01_next_required_step": _clean_ref(op01.get("next_required_step") if isinstance(op01, Mapping) else None, default="op01_next_required_step_missing", max_length=360),
        "pcm_op08_contract_required_field_refs": list(P7_R54_AHR_POST_PCM_DHB_OP02_PCM_CONTRACT_REQUIRED_FIELD_REFS),
        "pcm_op08_contract_required_field_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP02_PCM_CONTRACT_REQUIRED_FIELD_REFS),
        "pcm_op08_contract_missing_field_refs": missing_field_refs,
        "pcm_op08_contract_missing_field_ref_count": len(missing_field_refs),
        "pcm_op08_schema_version": pcm_schema,
        "pcm_op08_schema_version_matches": pcm_schema == P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_SCHEMA_VERSION_REF,
        "pcm_op08_operation_step_ref": pcm_operation_step,
        "pcm_op08_operation_step_ref_matches": pcm_operation_step == P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_STEP_REF,
        "pcm_op08_status_ref": pcm_status,
        "pcm_op08_status_ref_matches": pcm_status == P7_R54_AHR_POST_PCM_DHB_ALLOWED_PCM_OP08_CLOSED_STATUS_REF,
        "pcm_op08_material_ref": pcm_material_ref,
        "pcm_op08_body_free": pcm_body_free,
        "pcm_op08_closed_bodyfree_stopped": pcm_closed_bodyfree_stopped,
        "pcm_op08_contract_field_set_valid": not missing_field_refs,
        "pcm_op08_contract_valid": contract_valid,
        "selected_pnt_lane_ref": lane_ref,
        "selected_pnt_lane_ref_present": lane_present,
        "selected_pnt_lane_ref_allowed": lane_allowed,
        "selected_pcm_next_work_class_ref": selected_work_class_ref,
        "selected_pcm_next_work_class_ref_present": selected_work_class_present,
        "selected_pcm_next_boundary_ref": selected_boundary_ref,
        "selected_pcm_next_boundary_ref_present": selected_boundary_present,
        "selected_pcm_next_boundary_kind_ref": selected_boundary_kind_ref,
        "selected_pcm_next_boundary_kind_ref_present": selected_boundary_kind_present,
        "selected_pcm_next_boundary_not_executed": selected_boundary_not_executed,
        "selected_pcm_next_boundary_not_executed_present": selected_boundary_not_executed_present,
        "next_design_document_candidate_ref": next_design_ref,
        "next_design_document_candidate_ref_present": next_design_present,
        "next_design_document_allowed": next_design_allowed,
        "next_design_document_allowed_present": next_design_allowed_present,
        "dhr_op05_not_called": dhr_op05_not_called,
        "dhr_op06_not_called": dhr_op06_not_called,
        "dmd_r52_not_executed": dmd_r52_not_executed,
        "actual_review_not_started": actual_review_not_started,
        "p5_p6_p8_p7_release_not_started": p5_p6_p8_p7_release_not_started,
        "p8_question_design_not_started": p8_question_design_not_started,
        "p8_question_implementation_not_started": p8_question_implementation_not_started,
        "api_db_rn_runtime_response_key_not_changed": api_db_rn_runtime_response_key_not_changed,
        "op02_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op02_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op02_input_body_like_value_path_refs": body_like_paths,
        "op02_input_body_like_value_path_count": len(body_like_paths),
        "op02_input_promotion_claim_refs": promotion_claims,
        "op02_input_promotion_claim_ref_count": len(promotion_claims),
        "op02_input_no_touch_mutation_path_refs": no_touch_paths,
        "op02_input_no_touch_mutation_path_count": len(no_touch_paths),
        "op02_input_multi_lane_material_key_path_refs": multi_lane_paths,
        "op02_input_multi_lane_material_key_path_count": len(multi_lane_paths),
        "dhb_op02_status_ref": status_ref,
        "bodyfree_pcm_op08_contract_validation_status_ref": status_ref,
        "dhb_op02_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS),
        "dhb_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS),
        "dhb_op02_pcm_op08_contract_valid_stopped": contract_valid,
        "dhb_op02_repair_required": repair,
        "dhb_op02_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "dhb_op02_reason_refs": reason_refs,
        "dhb_op02_reason_ref_count": len(reason_refs),
        "dhb_op02_blocker_refs": blocker_refs,
        "dhb_op02_blocker_ref_count": len(blocker_refs),
        "dhb_op02_does_not_confirm_dhr_op05_lane": True,
        "dhb_op02_does_not_materialize_dhr_op05_handoff_envelope": True,
        "dhb_op02_does_not_execute_selected_pcm_next_boundary": True,
        "dhb_op02_does_not_call_dhr_op05": True,
        "dhb_op02_does_not_call_dhr_op06": True,
        "dhb_op02_does_not_execute_dmd_r52_or_release": True,
        "dhb_op02_does_not_start_actual_review": True,
        "dhb_op02_does_not_request_raw_evidence": True,
        "dhb_op02_does_not_execute_repair": True,
        "dhb_op02_does_not_start_p8_question_design": True,
        "dhb_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "dhb_op02_does_not_materialize_p8_question_text": True,
        "dhb_op02_does_not_create_json_schema_file": True,
        "dhr_op05_lane_confirmed_here": False,
        "dhr_op05_handoff_envelope_materialized_here": False,
        "selected_pcm_next_boundary_executed_here": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP02_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "dhb_op02_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op02_pcm_op08_contract_validation_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP02 PCM-OP08 contract validation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP02")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP02",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP02_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP02 implemented flag must be true after R3: {key}")
    if data.get("bodyfree_pcm_op08_contract_validation_status_ref") != data.get("dhb_op02_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 status alias changed")
    if tuple(data.get("dhb_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 allowed status refs changed")
    if data.get("dhb_op02_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 allowed status count changed")
    if tuple(data.get("pcm_op08_contract_required_field_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP02_PCM_CONTRACT_REQUIRED_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 required PCM field refs changed")
    for key in (
        "dhb_op02_does_not_confirm_dhr_op05_lane",
        "dhb_op02_does_not_materialize_dhr_op05_handoff_envelope",
        "dhb_op02_does_not_execute_selected_pcm_next_boundary",
        "dhb_op02_does_not_call_dhr_op05",
        "dhb_op02_does_not_call_dhr_op06",
        "dhb_op02_does_not_execute_dmd_r52_or_release",
        "dhb_op02_does_not_start_actual_review",
        "dhb_op02_does_not_request_raw_evidence",
        "dhb_op02_does_not_execute_repair",
        "dhb_op02_does_not_start_p8_question_design",
        "dhb_op02_does_not_change_api_db_rn_runtime_response_key",
        "dhb_op02_does_not_materialize_p8_question_text",
        "dhb_op02_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP02 required true boundary changed: {key}")
    for key in (
        "dhr_op05_lane_confirmed_here",
        "dhr_op05_handoff_envelope_materialized_here",
        "selected_pcm_next_boundary_executed_here",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "p8_question_design_started",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP02 forbidden claim changed: {key}")
    for field, count_field in (
        ("pcm_op08_contract_required_field_refs", "pcm_op08_contract_required_field_ref_count"),
        ("pcm_op08_contract_missing_field_refs", "pcm_op08_contract_missing_field_ref_count"),
        ("op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count"),
        ("op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count"),
        ("op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count"),
        ("op02_input_no_touch_mutation_path_refs", "op02_input_no_touch_mutation_path_count"),
        ("op02_input_multi_lane_material_key_path_refs", "op02_input_multi_lane_material_key_path_count"),
        ("dhb_op02_reason_refs", "dhb_op02_reason_ref_count"),
        ("dhb_op02_blocker_refs", "dhb_op02_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP02 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 not-yet steps changed")
    status_ref = data.get("dhb_op02_status_ref")
    flags = [
        data.get("dhb_op02_pcm_op08_contract_valid_stopped") is True,
        data.get("dhb_op02_repair_required") is True,
        data.get("dhb_op02_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 valid branch next step changed")
        for key in (
            "op01_material_present",
            "op01_contract_valid",
            "op01_ready_for_contract_validation",
            "pcm_op08_schema_version_matches",
            "pcm_op08_operation_step_ref_matches",
            "pcm_op08_status_ref_matches",
            "pcm_op08_body_free",
            "pcm_op08_closed_bodyfree_stopped",
            "pcm_op08_contract_field_set_valid",
            "pcm_op08_contract_valid",
            "selected_pnt_lane_ref_present",
            "selected_pnt_lane_ref_allowed",
            "selected_pcm_next_work_class_ref_present",
            "selected_pcm_next_boundary_ref_present",
            "selected_pcm_next_boundary_kind_ref_present",
            "selected_pcm_next_boundary_not_executed",
            "selected_pcm_next_boundary_not_executed_present",
            "next_design_document_candidate_ref_present",
            "next_design_document_allowed_present",
            "dhr_op05_not_called",
            "dhr_op06_not_called",
            "dmd_r52_not_executed",
            "actual_review_not_started",
            "p5_p6_p8_p7_release_not_started",
            "p8_question_design_not_started",
            "p8_question_implementation_not_started",
            "api_db_rn_runtime_response_key_not_changed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP02 valid required true field changed: {key}")
        if data.get("dhb_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 valid branch cannot carry blockers")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_PCM_OP08_CONTRACT_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_PCM_OP08_CONTRACT_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP02 blocked branch next step changed")
    return True


def _op03_dhr_consistency_blockers(op02: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(op02, Mapping):
        return ["op02_material_not_mapping"]
    blockers: list[str] = []
    if op02.get("selected_pcm_next_work_class_ref") != P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_WORK_CLASS_REF:
        blockers.append("selected_pcm_next_work_class_ref_not_dhr_op05_next_design_candidate")
    if op02.get("selected_pcm_next_boundary_ref") != P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_REF:
        blockers.append("selected_pcm_next_boundary_ref_not_dhr_op05_preflight_design_without_call")
    if op02.get("selected_pcm_next_boundary_kind_ref") != P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF:
        blockers.append("selected_pcm_next_boundary_kind_ref_not_dhr_op05_next_design_candidate_boundary")
    if op02.get("next_design_document_candidate_ref") != P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF:
        blockers.append("next_design_document_candidate_ref_not_dhr_op05_manual_handoff_boundary")
    if op02.get("next_design_document_allowed") is not True:
        blockers.append("next_design_document_allowed_not_true_for_dhr_op05_lane")
    if op02.get("selected_pcm_next_boundary_not_executed") is not True:
        blockers.append("selected_pcm_next_boundary_not_executed_not_true_for_dhr_op05_lane")
    return blockers


def _op03_status_reason_blocker_next(
    *,
    op02_present: bool,
    op02_valid: bool,
    op02_contract_valid: bool,
    op02_blocked: bool,
    lane_present: bool,
    lane_allowed: bool,
    dhr_lane_selected: bool,
    non_dhr_lane_selected: bool,
    dhr_consistency_blockers: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    multi_lane_paths: Sequence[str],
    op02_blocker_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths or op02_blocked:
        reasons.append("bodyfree_leak_promotion_or_autorun_detected_before_dhr_op05_lane_confirmation")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        if op02_blocked:
            blockers.append("op02_contract_validation_blocked")
            blockers.extend(op02_blocker_refs)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[3],
            reasons,
            blockers,
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_LANE_CONFIRMATION_REF,
        )
    if not op02_present:
        reasons.append("op02_contract_validation_material_missing")
        blockers.append("op02_material_present_false")
    if not op02_valid:
        reasons.append("op02_contract_validation_contract_invalid")
        blockers.append("op02_contract_valid_false")
    if not op02_contract_valid:
        reasons.append("op02_pcm_op08_contract_not_valid_for_lane_confirmation")
        blockers.append("op02_pcm_op08_contract_valid_false")
        blockers.extend(op02_blocker_refs)
    if multi_lane_paths:
        reasons.append("multi_lane_material_cannot_be_used_for_dhr_op05_lane_confirmation")
        blockers.extend(multi_lane_paths)
    if not lane_present:
        blockers.append("selected_pnt_lane_ref_missing")
    if not lane_allowed:
        blockers.append("selected_pnt_lane_ref_unknown_or_not_allowed")
    if blockers:
        if "op02_pcm_op08_contract_not_valid_for_lane_confirmation" not in reasons:
            reasons.append("dhr_op05_lane_confirmation_repair_required")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[2],
            reasons,
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_LANE_CONFIRMATION_REF,
        )
    if dhr_lane_selected:
        if dhr_consistency_blockers:
            reasons.append("dhr_op05_lane_selected_but_expected_boundary_or_design_ref_mismatch")
            return (
                P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[2],
                reasons,
                _dedupe_clean_refs(dhr_consistency_blockers, max_length=360),
                P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_LANE_CONFIRMATION_REF,
            )
        reasons.append("dhr_op05_lane_exactly_confirmed_stopped_before_handoff_envelope")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[0],
            reasons,
            [],
            P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
        )
    if non_dhr_lane_selected:
        reasons.append("not_dhr_op05_lane_route_preserved_without_handoff_envelope")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[1],
            reasons,
            [],
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF,
        )
    reasons.append("dhr_op05_lane_confirmation_repair_required")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[2],
        reasons,
        ["selected_pnt_lane_ref_not_routeable"],
        P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_LANE_CONFIRMATION_REF,
    )


def build_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation(
    op02_pcm_op08_contract_validation: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Confirm the DHR-OP05 lane or preserve a non-DHR route without materializing an envelope."""

    session_id = _safe_review_session_id(review_session_id)
    op02 = op02_pcm_op08_contract_validation
    op02_present = isinstance(op02, Mapping)
    op02_valid = _op02_contract_valid(op02)
    op02_status_ref = _clean_ref(op02.get("dhb_op02_status_ref") if isinstance(op02, Mapping) else None, default="missing", max_length=360)
    op02_contract_valid = bool(op02_valid and isinstance(op02, Mapping) and op02.get("pcm_op08_contract_valid") is True)
    op02_blocked = bool(isinstance(op02, Mapping) and op02.get("dhb_op02_bodyfree_leak_promotion_or_autorun_blocked") is True)
    op02_blocker_refs = _dedupe_clean_refs(op02.get("dhb_op02_blocker_refs") if isinstance(op02, Mapping) else (), max_length=360)

    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op02 or {}, path="dhb_op02")
    multi_lane_paths = _dedupe_clean_refs(_scan_multi_lane_material_key_paths(op02 or {}, path="dhb_op02"), max_length=340)

    lane_ref = _clean_ref(op02.get("selected_pnt_lane_ref") if isinstance(op02, Mapping) else None, default="selected_pnt_lane_missing", max_length=360)
    selected_work_class_ref = _clean_ref(op02.get("selected_pcm_next_work_class_ref") if isinstance(op02, Mapping) else None, default="selected_pcm_next_work_class_missing", max_length=360)
    selected_boundary_ref = _clean_ref(op02.get("selected_pcm_next_boundary_ref") if isinstance(op02, Mapping) else None, default="selected_pcm_next_boundary_missing", max_length=420)
    selected_boundary_kind_ref = _clean_ref(op02.get("selected_pcm_next_boundary_kind_ref") if isinstance(op02, Mapping) else None, default="selected_pcm_next_boundary_kind_missing", max_length=420)
    selected_boundary_not_executed = bool(isinstance(op02, Mapping) and op02.get("selected_pcm_next_boundary_not_executed") is True)
    next_design_ref = _clean_ref(op02.get("next_design_document_candidate_ref") if isinstance(op02, Mapping) else None, default="next_design_document_candidate_missing", max_length=460)
    next_design_allowed = bool(isinstance(op02, Mapping) and op02.get("next_design_document_allowed") is True)

    lane_present = lane_ref not in ("", "selected_pnt_lane_missing", "missing")
    lane_allowed = lane_ref == P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF or lane_ref in P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS
    dhr_lane_selected = lane_ref == P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
    non_dhr_lane_selected = lane_ref in P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS
    dhr_consistency_blockers = _op03_dhr_consistency_blockers(op02) if dhr_lane_selected else []

    status_ref, reason_refs, blocker_refs, next_required_step = _op03_status_reason_blocker_next(
        op02_present=op02_present,
        op02_valid=op02_valid,
        op02_contract_valid=op02_contract_valid,
        op02_blocked=op02_blocked,
        lane_present=lane_present,
        lane_allowed=lane_allowed,
        dhr_lane_selected=dhr_lane_selected,
        non_dhr_lane_selected=non_dhr_lane_selected,
        dhr_consistency_blockers=dhr_consistency_blockers,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        multi_lane_paths=multi_lane_paths,
        op02_blocker_refs=op02_blocker_refs,
    )
    confirmed = status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[0]
    route_preserved = status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[1]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[2]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[3]
    reason_refs = _dedupe_clean_refs(reason_refs, max_length=360)
    blocker_refs = _dedupe_clean_refs(blocker_refs, max_length=360)

    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_material_present": op02_present,
        "op02_contract_valid": op02_valid,
        "op02_schema_version": _clean_ref(op02.get("schema_version") if isinstance(op02, Mapping) else None, default="op02_schema_missing", max_length=300),
        "op02_material_ref": _clean_ref(op02.get("material_id") if isinstance(op02, Mapping) else None, default="op02_material_missing", max_length=320),
        "op02_status_ref": op02_status_ref,
        "op02_next_required_step": _clean_ref(op02.get("next_required_step") if isinstance(op02, Mapping) else None, default="op02_next_required_step_missing", max_length=360),
        "selected_pnt_lane_ref": lane_ref,
        "selected_pnt_lane_ref_present": lane_present,
        "selected_pnt_lane_ref_allowed": lane_allowed,
        "dhr_op05_lane_ref": P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF,
        "dhr_op05_lane_selected": dhr_lane_selected,
        "dhr_op05_lane_confirmed": confirmed,
        "non_dhr_lane_route_preserved": route_preserved,
        "selected_pcm_next_work_class_ref": selected_work_class_ref,
        "selected_pcm_next_work_class_ref_matches_dhr_op05_lane": selected_work_class_ref == P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_WORK_CLASS_REF,
        "selected_pcm_next_boundary_ref": selected_boundary_ref,
        "selected_pcm_next_boundary_ref_matches_dhr_op05_lane": selected_boundary_ref == P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_REF,
        "selected_pcm_next_boundary_kind_ref": selected_boundary_kind_ref,
        "selected_pcm_next_boundary_kind_ref_matches_dhr_op05_lane": selected_boundary_kind_ref == P7_R54_AHR_POST_PCM_DHB_EXPECTED_SELECTED_PCM_NEXT_BOUNDARY_KIND_REF,
        "selected_pcm_next_boundary_not_executed": selected_boundary_not_executed,
        "next_design_document_candidate_ref": next_design_ref,
        "next_design_document_candidate_ref_matches_dhr_op05_lane": next_design_ref == P7_R54_AHR_POST_PCM_DHB_EXPECTED_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF,
        "next_design_document_allowed": next_design_allowed,
        "next_design_document_allowed_matches_dhr_op05_lane": next_design_allowed is True,
        "preserved_non_dhr_lane_ref": lane_ref if route_preserved else "none",
        "preserved_pcm_next_work_class_ref": selected_work_class_ref if route_preserved else "none",
        "preserved_pcm_next_boundary_ref": selected_boundary_ref if route_preserved else "none",
        "preserved_pcm_next_boundary_kind_ref": selected_boundary_kind_ref if route_preserved else "none",
        "preserved_next_design_document_candidate_ref": next_design_ref if route_preserved else "none",
        "preserved_pcm_route_without_execution": route_preserved,
        "allowed_non_dhr_lane_refs": list(P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS),
        "allowed_non_dhr_lane_ref_count": len(P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS),
        "dhr_op05_manual_handoff_envelope_materialized": False,
        "dhr_op05_handoff_envelope_ready": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "dhr_op05_not_called": bool(isinstance(op02, Mapping) and op02.get("dhr_op05_not_called") is True),
        "dhr_op06_not_called": bool(isinstance(op02, Mapping) and op02.get("dhr_op06_not_called") is True),
        "dmd_r52_not_executed": bool(isinstance(op02, Mapping) and op02.get("dmd_r52_not_executed") is True),
        "actual_review_not_started": bool(isinstance(op02, Mapping) and op02.get("actual_review_not_started") is True),
        "p5_p6_p8_p7_release_not_started": bool(isinstance(op02, Mapping) and op02.get("p5_p6_p8_p7_release_not_started") is True),
        "p8_question_design_not_started": bool(isinstance(op02, Mapping) and op02.get("p8_question_design_not_started") is True),
        "p8_question_implementation_not_started": bool(isinstance(op02, Mapping) and op02.get("p8_question_implementation_not_started") is True),
        "api_db_rn_runtime_response_key_not_changed": bool(isinstance(op02, Mapping) and op02.get("api_db_rn_runtime_response_key_not_changed") is True),
        "op03_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op03_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op03_input_body_like_value_path_refs": body_like_paths,
        "op03_input_body_like_value_path_count": len(body_like_paths),
        "op03_input_promotion_claim_refs": promotion_claims,
        "op03_input_promotion_claim_ref_count": len(promotion_claims),
        "op03_input_no_touch_mutation_path_refs": no_touch_paths,
        "op03_input_no_touch_mutation_path_count": len(no_touch_paths),
        "op03_input_multi_lane_material_key_path_refs": multi_lane_paths,
        "op03_input_multi_lane_material_key_path_count": len(multi_lane_paths),
        "dhb_op03_status_ref": status_ref,
        "bodyfree_dhr_op05_lane_exact_confirmation_status_ref": status_ref,
        "dhb_op03_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS),
        "dhb_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS),
        "dhb_op03_dhr_op05_lane_confirmed_stopped": confirmed,
        "dhb_op03_not_dhr_op05_lane_route_preserved_stopped": route_preserved,
        "dhb_op03_repair_required": repair,
        "dhb_op03_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "dhb_op03_reason_refs": reason_refs,
        "dhb_op03_reason_ref_count": len(reason_refs),
        "dhb_op03_blocker_refs": blocker_refs,
        "dhb_op03_blocker_ref_count": len(blocker_refs),
        "dhb_op03_does_not_materialize_dhr_op05_handoff_envelope": True,
        "dhb_op03_does_not_execute_selected_pcm_next_boundary": True,
        "dhb_op03_does_not_call_dhr_op05": True,
        "dhb_op03_does_not_call_dhr_op06": True,
        "dhb_op03_does_not_execute_dmd_r52_or_release": True,
        "dhb_op03_does_not_start_actual_review": True,
        "dhb_op03_does_not_request_raw_evidence": True,
        "dhb_op03_does_not_execute_repair": True,
        "dhb_op03_does_not_start_p8_question_design": True,
        "dhb_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "dhb_op03_does_not_materialize_p8_question_text": True,
        "dhb_op03_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP03_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "dhb_op02_implemented": True,
        "dhb_op03_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP03 DHR-OP05 exact lane confirmation / non-DHR preservation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP03")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP03",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP03_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP03 implemented flag must be true after R3: {key}")
    if data.get("bodyfree_dhr_op05_lane_exact_confirmation_status_ref") != data.get("dhb_op03_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 status alias changed")
    if tuple(data.get("dhb_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 allowed status refs changed")
    if data.get("dhb_op03_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 allowed status count changed")
    if tuple(data.get("allowed_non_dhr_lane_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 allowed non-DHR lane refs changed")
    for key in (
        "dhb_op03_does_not_materialize_dhr_op05_handoff_envelope",
        "dhb_op03_does_not_execute_selected_pcm_next_boundary",
        "dhb_op03_does_not_call_dhr_op05",
        "dhb_op03_does_not_call_dhr_op06",
        "dhb_op03_does_not_execute_dmd_r52_or_release",
        "dhb_op03_does_not_start_actual_review",
        "dhb_op03_does_not_request_raw_evidence",
        "dhb_op03_does_not_execute_repair",
        "dhb_op03_does_not_start_p8_question_design",
        "dhb_op03_does_not_change_api_db_rn_runtime_response_key",
        "dhb_op03_does_not_materialize_p8_question_text",
        "dhb_op03_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP03 required true boundary changed: {key}")
    for key in (
        "dhr_op05_manual_handoff_envelope_materialized",
        "dhr_op05_handoff_envelope_ready",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "selected_pcm_next_boundary_execution_allowed_here",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dmd_execution_started_here",
        "actual_review_started_here",
        "p8_question_design_started",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP03 forbidden claim changed: {key}")
    for field, count_field in (
        ("allowed_non_dhr_lane_refs", "allowed_non_dhr_lane_ref_count"),
        ("op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count"),
        ("op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count"),
        ("op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count"),
        ("op03_input_no_touch_mutation_path_refs", "op03_input_no_touch_mutation_path_count"),
        ("op03_input_multi_lane_material_key_path_refs", "op03_input_multi_lane_material_key_path_count"),
        ("dhb_op03_reason_refs", "dhb_op03_reason_ref_count"),
        ("dhb_op03_blocker_refs", "dhb_op03_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP03 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 not-yet steps changed")
    status_ref = data.get("dhb_op03_status_ref")
    flags = [
        data.get("dhb_op03_dhr_op05_lane_confirmed_stopped") is True,
        data.get("dhb_op03_not_dhr_op05_lane_route_preserved_stopped") is True,
        data.get("dhb_op03_repair_required") is True,
        data.get("dhb_op03_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 confirmed branch next step changed")
        for key in (
            "op02_material_present",
            "op02_contract_valid",
            "selected_pnt_lane_ref_present",
            "selected_pnt_lane_ref_allowed",
            "dhr_op05_lane_selected",
            "dhr_op05_lane_confirmed",
            "selected_pcm_next_work_class_ref_matches_dhr_op05_lane",
            "selected_pcm_next_boundary_ref_matches_dhr_op05_lane",
            "selected_pcm_next_boundary_kind_ref_matches_dhr_op05_lane",
            "selected_pcm_next_boundary_not_executed",
            "next_design_document_candidate_ref_matches_dhr_op05_lane",
            "next_design_document_allowed_matches_dhr_op05_lane",
            "dhr_op05_not_called",
            "dhr_op06_not_called",
            "dmd_r52_not_executed",
            "actual_review_not_started",
            "p5_p6_p8_p7_release_not_started",
            "p8_question_design_not_started",
            "api_db_rn_runtime_response_key_not_changed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP03 confirmed required true field changed: {key}")
        if data.get("non_dhr_lane_route_preserved") is not False or data.get("dhb_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 confirmed branch cannot preserve non-DHR or carry blockers")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 non-DHR branch next step changed")
        if data.get("dhr_op05_lane_confirmed") is not False or data.get("dhr_op05_lane_selected") is not False:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 non-DHR branch must not confirm DHR lane")
        if data.get("non_dhr_lane_route_preserved") is not True or data.get("preserved_pcm_route_without_execution") is not True:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 non-DHR branch must preserve route")
        if data.get("selected_pnt_lane_ref") not in P7_R54_AHR_POST_PCM_DHB_ALLOWED_NON_DHR_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 non-DHR branch lane changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_LANE_CONFIRMATION_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_LANE_CONFIRMATION_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP03 blocked branch next step changed")
    return True


# ---------------------------------------------------------------------------
# R4: DHB-OP04 / DHB-OP05 only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PCM_DHB_R4_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py",
)
P7_R54_AHR_POST_PCM_DHB_R4_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
)

P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_ENVELOPE_INPUTS_REF: Final = (
    "repair_dhr_op05_manual_handoff_envelope_inputs_before_any_dhr_op05_call"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_HANDOFF_ENVELOPE_REF: Final = (
    "blocked_dhr_op05_manual_handoff_envelope_leak_promotion_or_autorun_without_next_design_promotion"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_COMPATIBILITY_CROSSWALK_REF: Final = (
    "repair_dhr_op05_compatibility_crosswalk_inputs_before_any_dhr_op05_builder_call"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_COMPATIBILITY_CROSSWALK_REF: Final = (
    "blocked_dhr_op05_compatibility_crosswalk_fake_result_promotion_or_autorun_without_dhr_op05_result"
)

P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_CROSSWALK_REFS: Final[tuple[str, ...]] = (
    "existing_dhr_op05_bodyfree_preflight_scan_ref_recorded",
    "existing_dhr_op05_dmd_direct_call_not_safe_ref_recorded",
    "existing_dhr_op05_body_like_payload_repair_ref_recorded",
    "existing_dhr_op05_no_bodyfull_actual_dmd_p8_release_ref_recorded",
    "existing_dhr_op05_clear_does_not_auto_allow_dhr_op06_ref_recorded",
)
P7_R54_AHR_POST_PCM_DHB_FAKE_DHR_OP05_RESULT_CLAIM_KEY_REFS: Final[tuple[str, ...]] = (
    "dhr_op05_preflight_status_ref",
    "dhr_op05_preflight_scan_status_ref",
    "dhr_op05_preflight_result_ref",
    "dhr_op05_preflight_scan_result_ref",
    "dhr_op05_result_status_ref",
    "dhr_op05_result_ref",
    "dhr_op05_result",
    "existing_dhr_op05_status_ref",
    "existing_dhr_op05_result_ref",
    "existing_dhr_op05_result",
)

P7_R54_AHR_POST_PCM_DHB_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP04_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhb_op00_implemented",
        "dhb_op01_implemented",
        "dhb_op02_implemented",
        "dhb_op03_implemented",
        "dhb_op04_implemented",
    }
)
P7_R54_AHR_POST_PCM_DHB_OP05_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhb_op00_implemented",
        "dhb_op01_implemented",
        "dhb_op02_implemented",
        "dhb_op03_implemented",
        "dhb_op04_implemented",
        "dhb_op05_implemented",
    }
)

P7_R54_AHR_POST_PCM_DHB_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_material_present", "op03_contract_valid", "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_next_required_step",
    "op03_dhr_op05_lane_confirmed", "op03_non_dhr_lane_route_preserved", "op03_repair_required", "op03_blocked",
    "pcm_op08_material_ref", "pcm_op08_contract_valid", "selected_pnt_lane_ref", "selected_pcm_next_work_class_ref", "selected_pcm_next_boundary_ref", "selected_pcm_next_boundary_kind_ref", "selected_pcm_next_boundary_not_executed", "next_design_document_candidate_ref", "next_design_document_allowed",
    "existing_dhr_op05_builder_ref", "existing_dhr_op05_assert_ref", "existing_dhr_op05_schema_version_ref", "existing_dhr_op05_compatibility_status_refs", "existing_dhr_op05_compatibility_status_ref_count", "existing_dhr_op05_builder_call_allowed_here", "existing_dhr_op05_builder_called_here",
    "dhr_op05_lane_confirmed", "dhr_op05_manual_handoff_envelope_materialized", "dhr_op05_manual_handoff_envelope_ready", "dhr_op05_handoff_envelope_ready", "dhr_op05_preflight_reentry_candidate_allowed", "dhr_op05_call_still_requires_separate_explicit_instruction", "dhr_op05_handoff_envelope_material_id", "dhr_op05_handoff_envelope_is_builder_input", "dhr_op05_handoff_envelope_is_execution_result",
    "non_dhr_lane_route_preserved", "non_dhr_lane_handoff_envelope_materialized", "preserved_non_dhr_lane_ref", "preserved_pcm_next_boundary_ref", "preserved_pcm_route_without_execution",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "selected_pcm_next_boundary_execution_allowed_here", "dhr_op06_call_allowed_here", "dhr_op07_materialization_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "actual_rows_creation_allowed_here", "question_need_observation_rows_creation_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "p8_question_implementation_allowed_here", "question_text_materialization_allowed_here", "api_db_rn_runtime_response_key_change_allowed_here", "json_schema_file_creation_allowed_here", "p7_complete_allowed_here", "release_decision_allowed_here",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count", "op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count", "op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count", "op04_input_no_touch_mutation_path_refs", "op04_input_no_touch_mutation_path_count", "op04_input_multi_lane_material_key_path_refs", "op04_input_multi_lane_material_key_path_count",
    "dhb_op04_status_ref", "bodyfree_dhr_op05_manual_handoff_envelope_status_ref", "dhb_op04_allowed_status_refs", "dhb_op04_allowed_status_ref_count",
    "dhb_op04_dhr_op05_manual_handoff_envelope_materialized_stopped", "dhb_op04_not_dhr_op05_lane_no_handoff_envelope_stopped", "dhb_op04_repair_required", "dhb_op04_bodyfree_leak_promotion_or_autorun_blocked", "dhb_op04_reason_refs", "dhb_op04_reason_ref_count", "dhb_op04_blocker_refs", "dhb_op04_blocker_ref_count",
    "op04_does_not_call_dhr_op05", "op04_does_not_call_dhr_op06", "op04_does_not_execute_dmd_r52", "op04_does_not_start_actual_review", "op04_does_not_start_p8_question_design", "op04_does_not_change_api_db_rn_runtime_response_key", "op04_does_not_materialize_p8_question_text", "op04_does_not_create_json_schema_file", "op04_does_not_create_dhr_op05_result", "op04_does_not_generate_existing_dhr_op05_status",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", *P7_R54_AHR_POST_PCM_DHB_OP04_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PCM_DHB_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_material_present", "op04_contract_valid", "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_next_required_step",
    "op04_handoff_envelope_ready", "op04_handoff_envelope_materialized", "op04_blocked", "op04_repair_required", "op04_non_dhr_no_handoff_envelope",
    "existing_dhr_op05_builder_ref", "existing_dhr_op05_assert_ref", "existing_dhr_op05_schema_version_ref", "existing_dhr_op05_compatibility_status_refs", "existing_dhr_op05_compatibility_status_ref_count", "existing_dhr_op05_builder_call_allowed_here", "existing_dhr_op05_builder_called_here",
    "dhr_op05_manual_handoff_envelope_ref", "dhr_op05_manual_handoff_envelope_ready", "dhr_op05_compatibility_crosswalk_recorded", "dhr_op05_compatibility_crosswalk_refs", "dhr_op05_compatibility_crosswalk_ref_count",
    "existing_dhr_op05_bodyfree_preflight_scan_ref_recorded", "existing_dhr_op05_dmd_direct_call_not_safe_ref_recorded", "existing_dhr_op05_body_like_payload_repair_ref_recorded", "existing_dhr_op05_no_bodyfull_actual_dmd_p8_release_ref_recorded", "existing_dhr_op05_clear_does_not_auto_allow_dhr_op06_ref_recorded",
    "existing_dhr_op05_status_refs_are_compatibility_refs_only", "existing_dhr_op05_status_generated_here", "existing_dhr_op05_clear_status_generated_here", "dhr_op05_result_generated_here", "dhr_op05_preflight_scan_executed_here", "dhr_op05_builder_input_materialized_here",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "selected_pcm_next_boundary_execution_allowed_here", "dhr_op06_call_allowed_here", "dhr_op07_materialization_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "actual_rows_creation_allowed_here", "question_need_observation_rows_creation_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "p8_question_implementation_allowed_here", "question_text_materialization_allowed_here", "api_db_rn_runtime_response_key_change_allowed_here", "json_schema_file_creation_allowed_here", "p7_complete_allowed_here", "release_decision_allowed_here",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "op05_input_forbidden_payload_key_path_refs", "op05_input_forbidden_payload_key_path_count", "op05_input_body_like_value_path_refs", "op05_input_body_like_value_path_count", "op05_input_promotion_claim_refs", "op05_input_promotion_claim_ref_count", "op05_input_no_touch_mutation_path_refs", "op05_input_no_touch_mutation_path_count", "op05_input_fake_dhr_op05_result_claim_path_refs", "op05_input_fake_dhr_op05_result_claim_path_count",
    "dhb_op05_status_ref", "bodyfree_dhr_op05_compatibility_crosswalk_status_ref", "dhb_op05_allowed_status_refs", "dhb_op05_allowed_status_ref_count",
    "dhb_op05_compatibility_crosswalk_recorded_without_call", "dhb_op05_compatibility_repair_required", "dhb_op05_compatibility_blocked_promotion_or_autorun", "dhb_op05_reason_refs", "dhb_op05_reason_ref_count", "dhb_op05_blocker_refs", "dhb_op05_blocker_ref_count",
    "op05_does_not_call_dhr_op05", "op05_does_not_call_existing_dhr_op05_builder", "op05_does_not_generate_dhr_op05_result", "op05_does_not_generate_dhr_op05_clear", "op05_does_not_call_dhr_op06", "op05_does_not_execute_dmd_r52", "op05_does_not_start_actual_review", "op05_does_not_start_p8_question_design", "op05_does_not_change_api_db_rn_runtime_response_key", "op05_does_not_materialize_p8_question_text", "op05_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", "dhb_op05_implemented", *P7_R54_AHR_POST_PCM_DHB_OP05_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op03_contract_valid(op03: Mapping[str, Any] | None) -> bool:
    if not isinstance(op03, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op03_dhr_op05_lane_exact_confirmation_contract(op03) is True
    except ValueError:
        return False


def _op04_contract_valid(op04: Mapping[str, Any] | None) -> bool:
    if not isinstance(op04, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(op04) is True
    except ValueError:
        return False


def _scan_fake_dhr_op05_result_claim_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_text in {"existing_dhr_op05_compatibility_status_refs", "existing_dhr_op05_compatibility_status_ref_count"}:
                continue
            if "does_not" in key_lower or key_lower.endswith("_not_generated"):
                continue
            if key_text in P7_R54_AHR_POST_PCM_DHB_FAKE_DHR_OP05_RESULT_CLAIM_KEY_REFS:
                if child not in (None, "", "none", False):
                    paths.append(child_path)
            elif "dhr_op05" in key_lower and ("status" in key_lower or "result" in key_lower):
                if isinstance(child, str) and "DHR_PREFLIGHT_SCAN" in child:
                    paths.append(child_path)
                elif child is True:
                    paths.append(child_path)
            paths.extend(_scan_fake_dhr_op05_result_claim_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_fake_dhr_op05_result_claim_paths(child, path=f"{path}[{index}]"))
    return paths


def _op04_status_reason_blocker_next(
    *,
    op03_present: bool,
    op03_valid: bool,
    op03_confirmed: bool,
    op03_non_dhr_route_preserved: bool,
    op03_repair_required: bool,
    op03_blocked: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    multi_lane_paths: Sequence[str],
    op03_blocker_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths or op03_blocked:
        reasons.append("bodyfree_leak_promotion_or_autorun_detected_before_dhr_op05_handoff_envelope")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        if op03_blocked:
            blockers.append("op03_lane_confirmation_blocked")
            blockers.extend(op03_blocker_refs)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[3],
            reasons,
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_HANDOFF_ENVELOPE_REF,
        )
    if multi_lane_paths:
        reasons.append("multi_lane_material_cannot_materialize_dhr_op05_handoff_envelope")
        blockers.extend(multi_lane_paths)
    if not op03_present:
        reasons.append("op03_lane_confirmation_material_missing")
        blockers.append("op03_material_present_false")
    if not op03_valid:
        reasons.append("op03_lane_confirmation_contract_invalid")
        blockers.append("op03_contract_valid_false")
    if op03_repair_required:
        reasons.append("op03_lane_confirmation_repair_required")
        blockers.append("op03_repair_required")
        blockers.extend(op03_blocker_refs)
    if blockers:
        return (
            P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[2],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_ENVELOPE_INPUTS_REF,
        )
    if op03_confirmed:
        reasons.append("dhr_op05_manual_handoff_envelope_materialized_without_call")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[0],
            reasons,
            [],
            P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
        )
    if op03_non_dhr_route_preserved:
        reasons.append("not_dhr_op05_lane_no_handoff_envelope_materialized")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[1],
            reasons,
            [],
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF,
        )
    reasons.append("dhr_op05_handoff_envelope_inputs_repair_required")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[2],
        reasons,
        ["op03_dhr_op05_lane_not_confirmed"],
        P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_ENVELOPE_INPUTS_REF,
    )


def build_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call(
    op03_dhr_op05_lane_exact_confirmation: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Materialize a DHR-OP05 manual handoff envelope candidate without calling DHR-OP05."""

    session_id = _safe_review_session_id(review_session_id)
    op03 = op03_dhr_op05_lane_exact_confirmation
    op03_present = isinstance(op03, Mapping)
    op03_valid = _op03_contract_valid(op03)
    op03_status_ref = _clean_ref(op03.get("dhb_op03_status_ref") if isinstance(op03, Mapping) else None, default="missing", max_length=360)
    op03_confirmed = bool(op03_valid and isinstance(op03, Mapping) and op03.get("dhr_op05_lane_confirmed") is True)
    op03_non_dhr_route_preserved = bool(op03_valid and isinstance(op03, Mapping) and op03.get("non_dhr_lane_route_preserved") is True)
    op03_repair_required = bool(isinstance(op03, Mapping) and op03.get("dhb_op03_repair_required") is True)
    op03_blocked = bool(isinstance(op03, Mapping) and op03.get("dhb_op03_bodyfree_leak_promotion_or_autorun_blocked") is True)
    op03_blocker_refs = _dedupe_clean_refs(op03.get("dhb_op03_blocker_refs") if isinstance(op03, Mapping) else (), max_length=360)

    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op03 or {}, path="dhb_op03")
    multi_lane_paths = _dedupe_clean_refs(_scan_multi_lane_material_key_paths(op03 or {}, path="dhb_op03"), max_length=340)
    status_ref, reason_refs, blocker_refs, next_required_step = _op04_status_reason_blocker_next(
        op03_present=op03_present,
        op03_valid=op03_valid,
        op03_confirmed=op03_confirmed,
        op03_non_dhr_route_preserved=op03_non_dhr_route_preserved,
        op03_repair_required=op03_repair_required,
        op03_blocked=op03_blocked,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        multi_lane_paths=multi_lane_paths,
        op03_blocker_refs=op03_blocker_refs,
    )
    envelope_materialized = status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[0]
    non_dhr_no_envelope = status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[1]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[2]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[3]
    reason_refs = _dedupe_clean_refs(reason_refs, max_length=360)
    blocker_refs = _dedupe_clean_refs(blocker_refs, max_length=360)
    selected_lane_ref = _clean_ref(op03.get("selected_pnt_lane_ref") if isinstance(op03, Mapping) else None, default="selected_pnt_lane_missing", max_length=360)
    selected_work_class_ref = _clean_ref(op03.get("selected_pcm_next_work_class_ref") if isinstance(op03, Mapping) else None, default="selected_pcm_next_work_class_missing", max_length=360)
    selected_boundary_ref = _clean_ref(op03.get("selected_pcm_next_boundary_ref") if isinstance(op03, Mapping) else None, default="selected_pcm_next_boundary_missing", max_length=420)
    selected_boundary_kind_ref = _clean_ref(op03.get("selected_pcm_next_boundary_kind_ref") if isinstance(op03, Mapping) else None, default="selected_pcm_next_boundary_kind_missing", max_length=420)
    selected_boundary_not_executed = bool(isinstance(op03, Mapping) and op03.get("selected_pcm_next_boundary_not_executed") is True)
    next_design_ref = _clean_ref(op03.get("next_design_document_candidate_ref") if isinstance(op03, Mapping) else None, default="next_design_document_candidate_missing", max_length=460)
    next_design_allowed = bool(isinstance(op03, Mapping) and op03.get("next_design_document_allowed") is True)
    handoff_material_id = (
        "p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_20260708"
        if envelope_materialized
        else "none"
    )

    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_material_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_material_present": op03_present,
        "op03_contract_valid": op03_valid,
        "op03_schema_version": _clean_ref(op03.get("schema_version") if isinstance(op03, Mapping) else None, default="op03_schema_missing", max_length=300),
        "op03_material_ref": _clean_ref(op03.get("material_id") if isinstance(op03, Mapping) else None, default="op03_material_missing", max_length=320),
        "op03_status_ref": op03_status_ref,
        "op03_next_required_step": _clean_ref(op03.get("next_required_step") if isinstance(op03, Mapping) else None, default="op03_next_required_step_missing", max_length=360),
        "op03_dhr_op05_lane_confirmed": op03_confirmed,
        "op03_non_dhr_lane_route_preserved": op03_non_dhr_route_preserved,
        "op03_repair_required": op03_repair_required,
        "op03_blocked": op03_blocked,
        "pcm_op08_material_ref": _clean_ref(op03.get("op02_material_ref") if isinstance(op03, Mapping) else None, default="pcm_op08_material_ref_missing", max_length=360),
        "pcm_op08_contract_valid": bool(op03_confirmed and isinstance(op03, Mapping) and op03.get("op02_contract_valid") is True),
        "selected_pnt_lane_ref": selected_lane_ref,
        "selected_pcm_next_work_class_ref": selected_work_class_ref,
        "selected_pcm_next_boundary_ref": selected_boundary_ref,
        "selected_pcm_next_boundary_kind_ref": selected_boundary_kind_ref,
        "selected_pcm_next_boundary_not_executed": selected_boundary_not_executed,
        "next_design_document_candidate_ref": next_design_ref,
        "next_design_document_allowed": next_design_allowed,
        "existing_dhr_op05_builder_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF,
        "existing_dhr_op05_assert_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF,
        "existing_dhr_op05_schema_version_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_SCHEMA_VERSION_REF,
        "existing_dhr_op05_compatibility_status_refs": list(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS),
        "existing_dhr_op05_compatibility_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS),
        "existing_dhr_op05_builder_call_allowed_here": False,
        "existing_dhr_op05_builder_called_here": False,
        "dhr_op05_lane_confirmed": op03_confirmed,
        "dhr_op05_manual_handoff_envelope_materialized": envelope_materialized,
        "dhr_op05_manual_handoff_envelope_ready": envelope_materialized,
        "dhr_op05_handoff_envelope_ready": envelope_materialized,
        "dhr_op05_preflight_reentry_candidate_allowed": envelope_materialized,
        "dhr_op05_call_still_requires_separate_explicit_instruction": envelope_materialized,
        "dhr_op05_handoff_envelope_material_id": handoff_material_id,
        "dhr_op05_handoff_envelope_is_builder_input": False,
        "dhr_op05_handoff_envelope_is_execution_result": False,
        "non_dhr_lane_route_preserved": op03_non_dhr_route_preserved,
        "non_dhr_lane_handoff_envelope_materialized": False,
        "preserved_non_dhr_lane_ref": selected_lane_ref if non_dhr_no_envelope else "none",
        "preserved_pcm_next_boundary_ref": selected_boundary_ref if non_dhr_no_envelope else "none",
        "preserved_pcm_route_without_execution": non_dhr_no_envelope,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dhr_op07_materialization_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "actual_rows_creation_allowed_here": False,
        "question_need_observation_rows_creation_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "p8_question_implementation_allowed_here": False,
        "question_text_materialization_allowed_here": False,
        "api_db_rn_runtime_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "p7_complete_allowed_here": False,
        "release_decision_allowed_here": False,
        "dhr_op05_not_called": bool(isinstance(op03, Mapping) and op03.get("dhr_op05_not_called") is True),
        "dhr_op06_not_called": bool(isinstance(op03, Mapping) and op03.get("dhr_op06_not_called") is True),
        "dmd_r52_not_executed": bool(isinstance(op03, Mapping) and op03.get("dmd_r52_not_executed") is True),
        "actual_review_not_started": bool(isinstance(op03, Mapping) and op03.get("actual_review_not_started") is True),
        "p5_p6_p8_p7_release_not_started": bool(isinstance(op03, Mapping) and op03.get("p5_p6_p8_p7_release_not_started") is True),
        "p8_question_design_not_started": bool(isinstance(op03, Mapping) and op03.get("p8_question_design_not_started") is True),
        "p8_question_implementation_not_started": bool(isinstance(op03, Mapping) and op03.get("p8_question_implementation_not_started") is True),
        "api_db_rn_runtime_response_key_not_changed": bool(isinstance(op03, Mapping) and op03.get("api_db_rn_runtime_response_key_not_changed") is True),
        "op04_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op04_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op04_input_body_like_value_path_refs": body_like_paths,
        "op04_input_body_like_value_path_count": len(body_like_paths),
        "op04_input_promotion_claim_refs": promotion_claims,
        "op04_input_promotion_claim_ref_count": len(promotion_claims),
        "op04_input_no_touch_mutation_path_refs": no_touch_paths,
        "op04_input_no_touch_mutation_path_count": len(no_touch_paths),
        "op04_input_multi_lane_material_key_path_refs": multi_lane_paths,
        "op04_input_multi_lane_material_key_path_count": len(multi_lane_paths),
        "dhb_op04_status_ref": status_ref,
        "bodyfree_dhr_op05_manual_handoff_envelope_status_ref": status_ref,
        "dhb_op04_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS),
        "dhb_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS),
        "dhb_op04_dhr_op05_manual_handoff_envelope_materialized_stopped": envelope_materialized,
        "dhb_op04_not_dhr_op05_lane_no_handoff_envelope_stopped": non_dhr_no_envelope,
        "dhb_op04_repair_required": repair,
        "dhb_op04_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "dhb_op04_reason_refs": reason_refs,
        "dhb_op04_reason_ref_count": len(reason_refs),
        "dhb_op04_blocker_refs": blocker_refs,
        "dhb_op04_blocker_ref_count": len(blocker_refs),
        "op04_does_not_call_dhr_op05": True,
        "op04_does_not_call_dhr_op06": True,
        "op04_does_not_execute_dmd_r52": True,
        "op04_does_not_start_actual_review": True,
        "op04_does_not_start_p8_question_design": True,
        "op04_does_not_change_api_db_rn_runtime_response_key": True,
        "op04_does_not_materialize_p8_question_text": True,
        "op04_does_not_create_json_schema_file": True,
        "op04_does_not_create_dhr_op05_result": True,
        "op04_does_not_generate_existing_dhr_op05_status": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP04_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "dhb_op02_implemented": True,
        "dhb_op03_implemented": True,
        "dhb_op04_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op04_dhr_op05_manual_handoff_envelope_without_call_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP04 manual handoff envelope materialization without DHR-OP05 call."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP04")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP04_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP04",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP04_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP04 implemented flag must be true after R4: {key}")
    if data.get("bodyfree_dhr_op05_manual_handoff_envelope_status_ref") != data.get("dhb_op04_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 status alias changed")
    if tuple(data.get("dhb_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 allowed status refs changed")
    if data.get("dhb_op04_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 allowed status count changed")
    if data.get("existing_dhr_op05_builder_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 existing builder ref changed")
    if data.get("existing_dhr_op05_assert_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 existing assert ref changed")
    if data.get("existing_dhr_op05_schema_version_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 existing schema ref changed")
    if tuple(data.get("existing_dhr_op05_compatibility_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 compatibility status refs changed")
    if data.get("existing_dhr_op05_compatibility_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 compatibility status count changed")
    for key in (
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "selected_pcm_next_boundary_execution_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "p8_question_implementation_allowed_here",
        "question_text_materialization_allowed_here",
        "api_db_rn_runtime_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "p7_complete_allowed_here",
        "release_decision_allowed_here",
        "dhr_op05_handoff_envelope_is_builder_input",
        "dhr_op05_handoff_envelope_is_execution_result",
        "non_dhr_lane_handoff_envelope_materialized",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP04 forbidden claim changed: {key}")
    for key in (
        "op04_does_not_call_dhr_op05",
        "op04_does_not_call_dhr_op06",
        "op04_does_not_execute_dmd_r52",
        "op04_does_not_start_actual_review",
        "op04_does_not_start_p8_question_design",
        "op04_does_not_change_api_db_rn_runtime_response_key",
        "op04_does_not_materialize_p8_question_text",
        "op04_does_not_create_json_schema_file",
        "op04_does_not_create_dhr_op05_result",
        "op04_does_not_generate_existing_dhr_op05_status",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP04 required true boundary changed: {key}")
    for field, count_field in (
        ("existing_dhr_op05_compatibility_status_refs", "existing_dhr_op05_compatibility_status_ref_count"),
        ("op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count"),
        ("op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count"),
        ("op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count"),
        ("op04_input_no_touch_mutation_path_refs", "op04_input_no_touch_mutation_path_count"),
        ("op04_input_multi_lane_material_key_path_refs", "op04_input_multi_lane_material_key_path_count"),
        ("dhb_op04_reason_refs", "dhb_op04_reason_ref_count"),
        ("dhb_op04_blocker_refs", "dhb_op04_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP04 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP04_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 not-yet steps changed")
    status_ref = data.get("dhb_op04_status_ref")
    flags = [
        data.get("dhb_op04_dhr_op05_manual_handoff_envelope_materialized_stopped") is True,
        data.get("dhb_op04_not_dhr_op05_lane_no_handoff_envelope_stopped") is True,
        data.get("dhb_op04_repair_required") is True,
        data.get("dhb_op04_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 materialized branch next step changed")
        for key in (
            "op03_material_present",
            "op03_contract_valid",
            "op03_dhr_op05_lane_confirmed",
            "pcm_op08_contract_valid",
            "dhr_op05_lane_confirmed",
            "selected_pcm_next_boundary_not_executed",
            "next_design_document_allowed",
            "dhr_op05_manual_handoff_envelope_materialized",
            "dhr_op05_manual_handoff_envelope_ready",
            "dhr_op05_handoff_envelope_ready",
            "dhr_op05_preflight_reentry_candidate_allowed",
            "dhr_op05_call_still_requires_separate_explicit_instruction",
            "dhr_op05_not_called",
            "dhr_op06_not_called",
            "dmd_r52_not_executed",
            "actual_review_not_started",
            "p5_p6_p8_p7_release_not_started",
            "p8_question_design_not_started",
            "api_db_rn_runtime_response_key_not_changed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP04 materialized required true field changed: {key}")
        if data.get("dhr_op05_handoff_envelope_material_id") == "none" or data.get("dhb_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 materialized branch cannot omit envelope id or carry blockers")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 non-DHR branch next step changed")
        if data.get("dhr_op05_manual_handoff_envelope_materialized") is not False or data.get("dhr_op05_handoff_envelope_ready") is not False:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 non-DHR branch must not materialize envelope")
        if data.get("non_dhr_lane_route_preserved") is not True or data.get("preserved_pcm_route_without_execution") is not True:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 non-DHR branch must preserve route")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_ENVELOPE_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_HANDOFF_ENVELOPE_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP04 blocked branch next step changed")
    return True


def _op05_status_reason_blocker_next(
    *,
    op04_present: bool,
    op04_valid: bool,
    op04_handoff_ready: bool,
    op04_handoff_materialized: bool,
    op04_blocked: bool,
    op04_repair_required: bool,
    fake_result_paths: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    op04_blocker_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths or fake_result_paths or op04_blocked:
        reasons.append("bodyfree_leak_fake_dhr_result_promotion_or_autorun_detected_before_compatibility_crosswalk")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        blockers.extend(fake_result_paths)
        if op04_blocked:
            blockers.append("op04_handoff_envelope_blocked")
            blockers.extend(op04_blocker_refs)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[2],
            reasons,
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_COMPATIBILITY_CROSSWALK_REF,
        )
    if not op04_present:
        reasons.append("op04_handoff_envelope_material_missing")
        blockers.append("op04_material_present_false")
    if not op04_valid:
        reasons.append("op04_handoff_envelope_contract_invalid")
        blockers.append("op04_contract_valid_false")
    if op04_repair_required:
        reasons.append("op04_handoff_envelope_repair_required")
        blockers.append("op04_repair_required")
        blockers.extend(op04_blocker_refs)
    if not op04_handoff_ready or not op04_handoff_materialized:
        reasons.append("op04_dhr_op05_handoff_envelope_not_ready")
        blockers.append("op04_handoff_envelope_ready_false")
    if blockers:
        return (
            P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[1],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_COMPATIBILITY_CROSSWALK_REF,
        )
    reasons.append("dhr_op05_compatibility_crosswalk_recorded_without_builder_call")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[0],
        reasons,
        [],
        P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    )


def build_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call(
    op04_dhr_op05_manual_handoff_envelope: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Record existing DHR-OP05 compatibility refs without calling its builder or generating its result."""

    session_id = _safe_review_session_id(review_session_id)
    op04 = op04_dhr_op05_manual_handoff_envelope
    op04_present = isinstance(op04, Mapping)
    op04_valid = _op04_contract_valid(op04)
    op04_status_ref = _clean_ref(op04.get("dhb_op04_status_ref") if isinstance(op04, Mapping) else None, default="missing", max_length=360)
    op04_handoff_ready = bool(op04_valid and isinstance(op04, Mapping) and op04.get("dhr_op05_handoff_envelope_ready") is True)
    op04_handoff_materialized = bool(op04_valid and isinstance(op04, Mapping) and op04.get("dhr_op05_manual_handoff_envelope_materialized") is True)
    op04_blocked = bool(isinstance(op04, Mapping) and op04.get("dhb_op04_bodyfree_leak_promotion_or_autorun_blocked") is True)
    op04_repair_required = bool(isinstance(op04, Mapping) and op04.get("dhb_op04_repair_required") is True)
    op04_non_dhr_no_handoff = bool(isinstance(op04, Mapping) and op04.get("dhb_op04_not_dhr_op05_lane_no_handoff_envelope_stopped") is True)
    op04_blocker_refs = _dedupe_clean_refs(op04.get("dhb_op04_blocker_refs") if isinstance(op04, Mapping) else (), max_length=360)

    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op04 or {}, path="dhb_op04")
    fake_result_paths = _dedupe_clean_refs(_scan_fake_dhr_op05_result_claim_paths(op04 or {}, path="dhb_op04"), max_length=360)
    status_ref, reason_refs, blocker_refs, next_required_step = _op05_status_reason_blocker_next(
        op04_present=op04_present,
        op04_valid=op04_valid,
        op04_handoff_ready=op04_handoff_ready,
        op04_handoff_materialized=op04_handoff_materialized,
        op04_blocked=op04_blocked,
        op04_repair_required=op04_repair_required,
        fake_result_paths=fake_result_paths,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        op04_blocker_refs=op04_blocker_refs,
    )
    crosswalk_recorded = status_ref == P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[0]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[1]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[2]
    reason_refs = _dedupe_clean_refs(reason_refs, max_length=360)
    blocker_refs = _dedupe_clean_refs(blocker_refs, max_length=360)

    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_material_present": op04_present,
        "op04_contract_valid": op04_valid,
        "op04_schema_version": _clean_ref(op04.get("schema_version") if isinstance(op04, Mapping) else None, default="op04_schema_missing", max_length=300),
        "op04_material_ref": _clean_ref(op04.get("material_id") if isinstance(op04, Mapping) else None, default="op04_material_missing", max_length=320),
        "op04_status_ref": op04_status_ref,
        "op04_next_required_step": _clean_ref(op04.get("next_required_step") if isinstance(op04, Mapping) else None, default="op04_next_required_step_missing", max_length=360),
        "op04_handoff_envelope_ready": op04_handoff_ready,
        "op04_handoff_envelope_materialized": op04_handoff_materialized,
        "op04_blocked": op04_blocked,
        "op04_repair_required": op04_repair_required,
        "op04_non_dhr_no_handoff_envelope": op04_non_dhr_no_handoff,
        "existing_dhr_op05_builder_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF,
        "existing_dhr_op05_assert_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF,
        "existing_dhr_op05_schema_version_ref": P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_SCHEMA_VERSION_REF,
        "existing_dhr_op05_compatibility_status_refs": list(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS),
        "existing_dhr_op05_compatibility_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS),
        "existing_dhr_op05_builder_call_allowed_here": False,
        "existing_dhr_op05_builder_called_here": False,
        "dhr_op05_manual_handoff_envelope_ref": _clean_ref(op04.get("dhr_op05_handoff_envelope_material_id") if isinstance(op04, Mapping) else None, default="none", max_length=360) if crosswalk_recorded else "none",
        "dhr_op05_manual_handoff_envelope_ready": crosswalk_recorded,
        "dhr_op05_compatibility_crosswalk_recorded": crosswalk_recorded,
        "dhr_op05_compatibility_crosswalk_refs": list(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_CROSSWALK_REFS) if crosswalk_recorded else [],
        "dhr_op05_compatibility_crosswalk_ref_count": len(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_CROSSWALK_REFS) if crosswalk_recorded else 0,
        "existing_dhr_op05_bodyfree_preflight_scan_ref_recorded": crosswalk_recorded,
        "existing_dhr_op05_dmd_direct_call_not_safe_ref_recorded": crosswalk_recorded,
        "existing_dhr_op05_body_like_payload_repair_ref_recorded": crosswalk_recorded,
        "existing_dhr_op05_no_bodyfull_actual_dmd_p8_release_ref_recorded": crosswalk_recorded,
        "existing_dhr_op05_clear_does_not_auto_allow_dhr_op06_ref_recorded": crosswalk_recorded,
        "existing_dhr_op05_status_refs_are_compatibility_refs_only": True,
        "existing_dhr_op05_status_generated_here": False,
        "existing_dhr_op05_clear_status_generated_here": False,
        "dhr_op05_result_generated_here": False,
        "dhr_op05_preflight_scan_executed_here": False,
        "dhr_op05_builder_input_materialized_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dhr_op07_materialization_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "actual_rows_creation_allowed_here": False,
        "question_need_observation_rows_creation_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "p8_question_implementation_allowed_here": False,
        "question_text_materialization_allowed_here": False,
        "api_db_rn_runtime_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "p7_complete_allowed_here": False,
        "release_decision_allowed_here": False,
        "dhr_op05_not_called": bool(isinstance(op04, Mapping) and op04.get("dhr_op05_not_called") is True),
        "dhr_op06_not_called": bool(isinstance(op04, Mapping) and op04.get("dhr_op06_not_called") is True),
        "dmd_r52_not_executed": bool(isinstance(op04, Mapping) and op04.get("dmd_r52_not_executed") is True),
        "actual_review_not_started": bool(isinstance(op04, Mapping) and op04.get("actual_review_not_started") is True),
        "p5_p6_p8_p7_release_not_started": bool(isinstance(op04, Mapping) and op04.get("p5_p6_p8_p7_release_not_started") is True),
        "p8_question_design_not_started": bool(isinstance(op04, Mapping) and op04.get("p8_question_design_not_started") is True),
        "p8_question_implementation_not_started": bool(isinstance(op04, Mapping) and op04.get("p8_question_implementation_not_started") is True),
        "api_db_rn_runtime_response_key_not_changed": bool(isinstance(op04, Mapping) and op04.get("api_db_rn_runtime_response_key_not_changed") is True),
        "op05_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op05_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op05_input_body_like_value_path_refs": body_like_paths,
        "op05_input_body_like_value_path_count": len(body_like_paths),
        "op05_input_promotion_claim_refs": promotion_claims,
        "op05_input_promotion_claim_ref_count": len(promotion_claims),
        "op05_input_no_touch_mutation_path_refs": no_touch_paths,
        "op05_input_no_touch_mutation_path_count": len(no_touch_paths),
        "op05_input_fake_dhr_op05_result_claim_path_refs": fake_result_paths,
        "op05_input_fake_dhr_op05_result_claim_path_count": len(fake_result_paths),
        "dhb_op05_status_ref": status_ref,
        "bodyfree_dhr_op05_compatibility_crosswalk_status_ref": status_ref,
        "dhb_op05_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS),
        "dhb_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS),
        "dhb_op05_compatibility_crosswalk_recorded_without_call": crosswalk_recorded,
        "dhb_op05_compatibility_repair_required": repair,
        "dhb_op05_compatibility_blocked_promotion_or_autorun": blocked,
        "dhb_op05_reason_refs": reason_refs,
        "dhb_op05_reason_ref_count": len(reason_refs),
        "dhb_op05_blocker_refs": blocker_refs,
        "dhb_op05_blocker_ref_count": len(blocker_refs),
        "op05_does_not_call_dhr_op05": True,
        "op05_does_not_call_existing_dhr_op05_builder": True,
        "op05_does_not_generate_dhr_op05_result": True,
        "op05_does_not_generate_dhr_op05_clear": True,
        "op05_does_not_call_dhr_op06": True,
        "op05_does_not_execute_dmd_r52": True,
        "op05_does_not_start_actual_review": True,
        "op05_does_not_start_p8_question_design": True,
        "op05_does_not_change_api_db_rn_runtime_response_key": True,
        "op05_does_not_materialize_p8_question_text": True,
        "op05_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP05_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "dhb_op02_implemented": True,
        "dhb_op03_implemented": True,
        "dhb_op04_implemented": True,
        "dhb_op05_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP05 compatibility crosswalk without DHR-OP05 builder call."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP05")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP05_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP05",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP05_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", "dhb_op05_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP05 implemented flag must be true after R4: {key}")
    if data.get("bodyfree_dhr_op05_compatibility_crosswalk_status_ref") != data.get("dhb_op05_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 status alias changed")
    if tuple(data.get("dhb_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 allowed status refs changed")
    if data.get("dhb_op05_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 allowed status count changed")
    if data.get("existing_dhr_op05_builder_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_BUILDER_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 existing builder ref changed")
    if data.get("existing_dhr_op05_assert_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_ASSERT_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 existing assert ref changed")
    if data.get("existing_dhr_op05_schema_version_ref") != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 existing schema ref changed")
    if tuple(data.get("existing_dhr_op05_compatibility_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 compatibility status refs changed")
    if data.get("existing_dhr_op05_compatibility_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 compatibility status count changed")
    for key in (
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_status_generated_here",
        "existing_dhr_op05_clear_status_generated_here",
        "dhr_op05_result_generated_here",
        "dhr_op05_preflight_scan_executed_here",
        "dhr_op05_builder_input_materialized_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "selected_pcm_next_boundary_execution_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "p8_question_implementation_allowed_here",
        "question_text_materialization_allowed_here",
        "api_db_rn_runtime_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "p7_complete_allowed_here",
        "release_decision_allowed_here",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP05 forbidden claim changed: {key}")
    for key in (
        "existing_dhr_op05_status_refs_are_compatibility_refs_only",
        "op05_does_not_call_dhr_op05",
        "op05_does_not_call_existing_dhr_op05_builder",
        "op05_does_not_generate_dhr_op05_result",
        "op05_does_not_generate_dhr_op05_clear",
        "op05_does_not_call_dhr_op06",
        "op05_does_not_execute_dmd_r52",
        "op05_does_not_start_actual_review",
        "op05_does_not_start_p8_question_design",
        "op05_does_not_change_api_db_rn_runtime_response_key",
        "op05_does_not_materialize_p8_question_text",
        "op05_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP05 required true boundary changed: {key}")
    for field, count_field in (
        ("existing_dhr_op05_compatibility_status_refs", "existing_dhr_op05_compatibility_status_ref_count"),
        ("dhr_op05_compatibility_crosswalk_refs", "dhr_op05_compatibility_crosswalk_ref_count"),
        ("op05_input_forbidden_payload_key_path_refs", "op05_input_forbidden_payload_key_path_count"),
        ("op05_input_body_like_value_path_refs", "op05_input_body_like_value_path_count"),
        ("op05_input_promotion_claim_refs", "op05_input_promotion_claim_ref_count"),
        ("op05_input_no_touch_mutation_path_refs", "op05_input_no_touch_mutation_path_count"),
        ("op05_input_fake_dhr_op05_result_claim_path_refs", "op05_input_fake_dhr_op05_result_claim_path_count"),
        ("dhb_op05_reason_refs", "dhb_op05_reason_ref_count"),
        ("dhb_op05_blocker_refs", "dhb_op05_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP05 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP05_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 not-yet steps changed")
    status_ref = data.get("dhb_op05_status_ref")
    flags = [
        data.get("dhb_op05_compatibility_crosswalk_recorded_without_call") is True,
        data.get("dhb_op05_compatibility_repair_required") is True,
        data.get("dhb_op05_compatibility_blocked_promotion_or_autorun") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 crosswalk branch next step changed")
        for key in (
            "op04_material_present",
            "op04_contract_valid",
            "op04_handoff_envelope_ready",
            "op04_handoff_envelope_materialized",
            "dhr_op05_manual_handoff_envelope_ready",
            "dhr_op05_compatibility_crosswalk_recorded",
            "existing_dhr_op05_bodyfree_preflight_scan_ref_recorded",
            "existing_dhr_op05_dmd_direct_call_not_safe_ref_recorded",
            "existing_dhr_op05_body_like_payload_repair_ref_recorded",
            "existing_dhr_op05_no_bodyfull_actual_dmd_p8_release_ref_recorded",
            "existing_dhr_op05_clear_does_not_auto_allow_dhr_op06_ref_recorded",
            "dhr_op05_not_called",
            "dhr_op06_not_called",
            "dmd_r52_not_executed",
            "actual_review_not_started",
            "p5_p6_p8_p7_release_not_started",
            "p8_question_design_not_started",
            "api_db_rn_runtime_response_key_not_changed",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP05 crosswalk required true field changed: {key}")
        if tuple(data.get("dhr_op05_compatibility_crosswalk_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_EXISTING_DHR_OP05_COMPATIBILITY_CROSSWALK_REFS:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 crosswalk refs changed")
        if data.get("dhr_op05_manual_handoff_envelope_ref") == "none" or data.get("dhb_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 crosswalk branch cannot omit handoff ref or carry blockers")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_COMPATIBILITY_CROSSWALK_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 repair branch next step changed")
        if data.get("dhr_op05_compatibility_crosswalk_recorded") is not False:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 repair branch must not record crosswalk")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_DHR_OP05_COMPATIBILITY_CROSSWALK_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 blocked branch next step changed")
        if data.get("dhr_op05_compatibility_crosswalk_recorded") is not False:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP05 blocked branch must not record crosswalk")
    return True


# R5: DHB-OP06 / DHB-OP07 only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PCM_DHB_R5_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py",
)
P7_R54_AHR_POST_PCM_DHB_R5_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_PCM_DHB_R5_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_op01_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_op03_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_op05_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_op07_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_result_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_op01_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_op05_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_op07_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_result_20260707.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_PCM_DHB_R5_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_PCM_DHB_R5_RESULT_MEMO_EXPECTED_FILE_REFS: Final[tuple[str, ...]] = (
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_OP00_OP07_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R7_TargetValidation_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R8_SelectedRegression_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R9_Compileall_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R10_ResultMemoClosure_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R11_NextWorkDecision_20260708.md",
)
P7_R54_AHR_POST_PCM_DHB_OP07_TARGET_VALIDATION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py "
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py "
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py "
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py "
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py -p no:cacheprovider"
)
P7_R54_AHR_POST_PCM_DHB_OP07_SELECTED_REGRESSION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "<DHB R5 target tests plus selected adjacent PCM/PNT/NCI/Post-ELR19 DHR reference tests> -p no:cacheprovider"
)
P7_R54_AHR_POST_PCM_DHB_OP07_COMPILEALL_COMMAND_REF: Final = (
    "PYTHONPATH=services/ai_inference python -m compileall -q "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py"
)
P7_R54_AHR_POST_PCM_DHB_OP07_VALIDATION_COMMAND_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP07_TARGET_VALIDATION_COMMAND_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_SELECTED_REGRESSION_COMMAND_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_COMPILEALL_COMMAND_REF,
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_GUARD_INPUTS_REF: Final = (
    "repair_bodyfree_no_touch_guard_inputs_before_any_dhr_op05_call"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_GUARD_REF: Final = (
    "stop_blocked_bodyfree_leak_promotion_or_autorun_without_next_design_promotion"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_RESULT_MEMO_DRAFT_INPUTS_REF: Final = (
    "repair_validation_plan_result_memo_draft_inputs_before_any_green_claim"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_OR_STOP_AFTER_RESULT_MEMO_DRAFT_REF: Final = (
    "wait_or_stop_after_bodyfree_validation_plan_result_memo_draft_without_execution"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_RESULT_MEMO_DRAFT_REF: Final = (
    "stop_blocked_result_memo_draft_bodyfree_leak_promotion_or_autorun_without_green_claim"
)
P7_R54_AHR_POST_PCM_DHB_R5_VALIDATION_GREEN_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "target_validation_green_confirmed_here",
    "selected_regression_green_confirmed_here",
    "compileall_green_confirmed_here",
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_confirmed",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)

P7_R54_AHR_POST_PCM_DHB_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP06_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhb_op00_implemented",
        "dhb_op01_implemented",
        "dhb_op02_implemented",
        "dhb_op03_implemented",
        "dhb_op04_implemented",
        "dhb_op05_implemented",
        "dhb_op06_implemented",
    }
)
P7_R54_AHR_POST_PCM_DHB_OP07_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhb_op00_implemented",
        "dhb_op01_implemented",
        "dhb_op02_implemented",
        "dhb_op03_implemented",
        "dhb_op04_implemented",
        "dhb_op05_implemented",
        "dhb_op06_implemented",
        "dhb_op07_implemented",
    }
)

P7_R54_AHR_POST_PCM_DHB_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_material_present", "op05_contract_valid", "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_next_required_step",
    "op05_crosswalk_recorded", "op05_repair_required", "op05_blocked", "op05_handoff_envelope_ref", "op05_compatibility_crosswalk_recorded",
    "op06_scanned_material_label_refs", "op06_scanned_material_count",
    "op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count", "op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count", "op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count", "op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count",
    "dhb_op06_status_ref", "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref", "dhb_op06_allowed_status_refs", "dhb_op06_allowed_status_ref_count",
    "dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed", "dhb_op06_repair_required", "dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_blocked", "dhb_op06_reason_refs", "dhb_op06_reason_ref_count", "dhb_op06_blocker_refs", "dhb_op06_blocker_ref_count",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "existing_dhr_op05_builder_call_allowed_here", "existing_dhr_op05_builder_called_here", "selected_pcm_next_boundary_execution_allowed_here", "dhr_op06_call_allowed_here", "dhr_op07_materialization_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "actual_rows_creation_allowed_here", "question_need_observation_rows_creation_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "p8_question_implementation_allowed_here", "question_text_materialization_allowed_here", "api_db_rn_runtime_response_key_change_allowed_here", "json_schema_file_creation_allowed_here", "p7_complete_allowed_here", "release_decision_allowed_here",
    "dhr_op05_called_here", "dhr_op05_builder_called_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_execution_started_here", "r52_actual_execution_started_here", "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_question_design_started", "p8_question_implementation_started", "p7_complete", "release_allowed", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "rn_real_device_modal_verified_claimed_here",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "op06_does_not_call_dhr_op05", "op06_does_not_call_existing_dhr_op05_builder", "op06_does_not_call_dhr_op06", "op06_does_not_execute_dmd_r52", "op06_does_not_start_actual_review", "op06_does_not_start_p8_question_design", "op06_does_not_change_api_db_rn_runtime_response_key", "op06_does_not_materialize_p8_question_text", "op06_does_not_claim_validation_green", "op06_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", "dhb_op05_implemented", "dhb_op06_implemented", *P7_R54_AHR_POST_PCM_DHB_OP06_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_PCM_DHB_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_material_present", "op06_contract_valid", "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_next_required_step",
    "op06_guard_passed", "op06_repair_required", "op06_blocked", "op06_op05_crosswalk_recorded",
    "op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count", "op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count", "op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count", "op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count",
    "target_validation_command_refs", "target_validation_command_ref_count", "selected_regression_command_refs", "selected_regression_command_ref_count", "compileall_command_refs", "compileall_command_ref_count", "result_memo_expected_file_refs", "result_memo_expected_file_ref_count",
    "target_validation_test_ref_refs", "target_validation_test_ref_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count", "compileall_target_ref_refs", "compileall_target_ref_ref_count",
    "validation_commands_executed_here", "target_validation_green_confirmed_here", "selected_regression_green_confirmed_here", "compileall_green_confirmed_here", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here",
    "dhr_op05_not_called", "dhr_op05_builder_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "actual_rows_not_created", "question_need_observation_rows_not_created", "p8_question_design_not_started", "question_text_not_materialized", "api_db_rn_runtime_response_key_not_changed", "release_decision_not_made",
    "dhb_op07_status_ref", "bodyfree_validation_plan_result_memo_draft_status_ref", "dhb_op07_allowed_status_refs", "dhb_op07_allowed_status_ref_count",
    "dhb_op07_validation_plan_result_memo_draft_materialized_stopped", "dhb_op07_wait_or_stop_result_memo_draft_materialized_stopped", "dhb_op07_repair_required", "dhb_op07_bodyfree_leak_promotion_or_autorun_blocked", "dhb_op07_reason_refs", "dhb_op07_reason_ref_count", "dhb_op07_blocker_refs", "dhb_op07_blocker_ref_count",
    "op07_does_not_execute_validation_commands", "op07_does_not_claim_target_green", "op07_does_not_claim_selected_regression_green", "op07_does_not_claim_compileall_green", "op07_keeps_full_backend_suite_unconfirmed", "op07_keeps_rn_contract_unconfirmed", "op07_keeps_rn_real_device_unconfirmed", "op07_does_not_call_dhr_op05", "op07_does_not_call_dhr_op06", "op07_does_not_execute_dmd_r52", "op07_does_not_start_actual_review", "op07_does_not_start_p8_question_design", "op07_does_not_change_api_db_rn_runtime_response_key", "op07_does_not_make_release_decision", "op07_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", "dhb_op05_implemented", "dhb_op06_implemented", "dhb_op07_implemented", *P7_R54_AHR_POST_PCM_DHB_OP07_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op05_contract_valid(op05: Mapping[str, Any] | None) -> bool:
    if not isinstance(op05, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op05_existing_dhr_op05_compatibility_crosswalk_without_call_contract(op05) is True
    except ValueError:
        return False


def _op06_contract_valid(op06: Mapping[str, Any] | None) -> bool:
    if not isinstance(op06, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op06) is True
    except ValueError:
        return False


def _scan_r5_validation_green_promotion_claim_refs(value: Any, *, path: str = "artifact") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PCM_DHB_R5_VALIDATION_GREEN_PROMOTION_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_r5_validation_green_promotion_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_r5_validation_green_promotion_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _op06_scan_input(
    op05: Mapping[str, Any] | None,
    additional_bodyfree_materials: Sequence[Mapping[str, Any]] | None,
) -> tuple[dict[str, Any], list[str]]:
    scan_input: dict[str, Any] = {}
    labels: list[str] = []
    if isinstance(op05, Mapping):
        scan_input["dhb_op05"] = op05
        labels.append("dhb_op05")
    if additional_bodyfree_materials:
        clean_materials: list[Mapping[str, Any]] = []
        for index, material in enumerate(additional_bodyfree_materials):
            if isinstance(material, Mapping):
                clean_materials.append(material)
                labels.append(f"additional_bodyfree_material_{index}")
            else:
                scan_input[f"additional_bodyfree_material_{index}_invalid"] = {"invalid_material_type_ref": type(material).__name__}
                labels.append(f"additional_bodyfree_material_{index}_invalid")
        if clean_materials:
            scan_input["additional_bodyfree_materials"] = clean_materials
    if not scan_input:
        scan_input["missing_dhb_op05_material"] = {"missing_op05_material_ref": "op05_material_missing"}
    return scan_input, labels


def _op06_status_reason_blocker_next(
    *,
    op05_present: bool,
    op05_valid: bool,
    op05_blocked: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    op05_blocker_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths or op05_blocked:
        reasons.append("bodyfree_leak_no_touch_promotion_or_auto_execution_detected_in_dhb_materials")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        if op05_blocked:
            blockers.append("op05_compatibility_crosswalk_blocked")
            blockers.extend(op05_blocker_refs)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[2],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_GUARD_REF,
        )
    if not op05_present:
        reasons.append("op05_compatibility_crosswalk_material_missing")
        blockers.append("op05_material_present_false")
    if not op05_valid:
        reasons.append("op05_compatibility_crosswalk_contract_invalid")
        blockers.append("op05_contract_valid_false")
    if blockers:
        return (
            P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[1],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_GUARD_INPUTS_REF,
        )
    reasons.append("bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[0],
        reasons,
        [],
        P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    )


def build_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard(
    op05_existing_dhr_op05_compatibility_crosswalk: Mapping[str, Any] | None = None,
    *,
    additional_bodyfree_materials: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Run the DHB OP06 body-free/no-touch/no-promotion guard without downstream execution."""

    op05 = op05_existing_dhr_op05_compatibility_crosswalk
    op05_present = isinstance(op05, Mapping)
    op05_valid = _op05_contract_valid(op05)
    op05_status_ref = _clean_ref(op05.get("dhb_op05_status_ref") if isinstance(op05, Mapping) else None, default="missing", max_length=360)
    op05_crosswalk_recorded = bool(isinstance(op05, Mapping) and op05.get("dhb_op05_compatibility_crosswalk_recorded_without_call") is True)
    op05_repair_required = bool(isinstance(op05, Mapping) and op05.get("dhb_op05_compatibility_repair_required") is True)
    op05_blocked = bool(isinstance(op05, Mapping) and op05.get("dhb_op05_compatibility_blocked_promotion_or_autorun") is True)
    op05_blocker_refs = _dedupe_clean_refs(op05.get("dhb_op05_blocker_refs") if isinstance(op05, Mapping) else (), max_length=360)
    scan_input, scan_labels = _op06_scan_input(op05, additional_bodyfree_materials)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(
        scan_input,
        path="dhb_op06_materials",
    )
    status_ref, reason_refs, blocker_refs, next_required_step = _op06_status_reason_blocker_next(
        op05_present=op05_present,
        op05_valid=op05_valid,
        op05_blocked=op05_blocked,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        op05_blocker_refs=op05_blocker_refs,
    )
    passed = status_ref == P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[0]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[1]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[2]
    session_id = _safe_review_session_id(
        review_session_id or (op05.get("review_session_id") if isinstance(op05, Mapping) else None)
    )
    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_material_present": op05_present,
        "op05_contract_valid": op05_valid,
        "op05_schema_version": _clean_ref(op05.get("schema_version") if isinstance(op05, Mapping) else None, default="op05_schema_missing", max_length=300),
        "op05_material_ref": _clean_ref(op05.get("material_id") if isinstance(op05, Mapping) else None, default="op05_material_missing", max_length=320),
        "op05_status_ref": op05_status_ref,
        "op05_next_required_step": _clean_ref(op05.get("next_required_step") if isinstance(op05, Mapping) else None, default="op05_next_required_step_missing", max_length=360),
        "op05_crosswalk_recorded": op05_crosswalk_recorded,
        "op05_repair_required": op05_repair_required,
        "op05_blocked": op05_blocked,
        "op05_handoff_envelope_ref": _clean_ref(op05.get("dhr_op05_manual_handoff_envelope_ref") if isinstance(op05, Mapping) else None, default="none", max_length=360),
        "op05_compatibility_crosswalk_recorded": bool(isinstance(op05, Mapping) and op05.get("dhr_op05_compatibility_crosswalk_recorded") is True),
        "op06_scanned_material_label_refs": scan_labels,
        "op06_scanned_material_count": len(scan_labels),
        "op06_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op06_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op06_input_body_like_value_path_refs": body_like_paths,
        "op06_input_body_like_value_path_count": len(body_like_paths),
        "op06_input_promotion_claim_refs": promotion_claims,
        "op06_input_promotion_claim_ref_count": len(promotion_claims),
        "op06_input_no_touch_mutation_path_refs": no_touch_paths,
        "op06_input_no_touch_mutation_path_count": len(no_touch_paths),
        "dhb_op06_status_ref": status_ref,
        "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref": status_ref,
        "dhb_op06_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS),
        "dhb_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS),
        "dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed": passed,
        "dhb_op06_repair_required": repair,
        "dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_blocked": blocked,
        "dhb_op06_reason_refs": reason_refs,
        "dhb_op06_reason_ref_count": len(reason_refs),
        "dhb_op06_blocker_refs": blocker_refs,
        "dhb_op06_blocker_ref_count": len(blocker_refs),
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "existing_dhr_op05_builder_call_allowed_here": False,
        "existing_dhr_op05_builder_called_here": False,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dhr_op07_materialization_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "actual_rows_creation_allowed_here": False,
        "question_need_observation_rows_creation_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "p8_question_implementation_allowed_here": False,
        "question_text_materialization_allowed_here": False,
        "api_db_rn_runtime_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "p7_complete_allowed_here": False,
        "release_decision_allowed_here": False,
        "dhr_op05_called_here": False,
        "dhr_op05_builder_called_here": False,
        "dhr_op06_called_here": False,
        "dhr_op07_materialized_here": False,
        "dmd_execution_started_here": False,
        "r52_actual_execution_started_here": False,
        "actual_review_started_here": False,
        "actual_rows_created_here": False,
        "question_need_observation_rows_created_here": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "p7_complete": False,
        "release_allowed": False,
        "full_backend_suite_green_claimed_here": False,
        "rn_contract_green_claimed_here": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "actual_review_not_started": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "api_db_rn_runtime_response_key_not_changed": True,
        "op06_does_not_call_dhr_op05": True,
        "op06_does_not_call_existing_dhr_op05_builder": True,
        "op06_does_not_call_dhr_op06": True,
        "op06_does_not_execute_dmd_r52": True,
        "op06_does_not_start_actual_review": True,
        "op06_does_not_start_p8_question_design": True,
        "op06_does_not_change_api_db_rn_runtime_response_key": True,
        "op06_does_not_materialize_p8_question_text": True,
        "op06_does_not_claim_validation_green": True,
        "op06_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP06_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "dhb_op02_implemented": True,
        "dhb_op03_implemented": True,
        "dhb_op04_implemented": True,
        "dhb_op05_implemented": True,
        "dhb_op06_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP06 body-free/no-touch/no-promotion/no-auto-execution guard contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP06")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP06_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP06",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP06_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", "dhb_op05_implemented", "dhb_op06_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP06 implemented flag must be true after R5: {key}")
    if data.get("bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref") != data.get("dhb_op06_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 status alias changed")
    if tuple(data.get("dhb_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 allowed status refs changed")
    if data.get("dhb_op06_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 allowed status count changed")
    for key in (
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "selected_pcm_next_boundary_execution_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "p8_question_implementation_allowed_here",
        "question_text_materialization_allowed_here",
        "api_db_rn_runtime_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "p7_complete_allowed_here",
        "release_decision_allowed_here",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP06 forbidden claim changed: {key}")
    for key in (
        "dhr_op05_not_called",
        "dhr_op06_not_called",
        "dmd_r52_not_executed",
        "actual_review_not_started",
        "p5_p6_p8_p7_release_not_started",
        "p8_question_design_not_started",
        "p8_question_implementation_not_started",
        "api_db_rn_runtime_response_key_not_changed",
        "op06_does_not_call_dhr_op05",
        "op06_does_not_call_existing_dhr_op05_builder",
        "op06_does_not_call_dhr_op06",
        "op06_does_not_execute_dmd_r52",
        "op06_does_not_start_actual_review",
        "op06_does_not_start_p8_question_design",
        "op06_does_not_change_api_db_rn_runtime_response_key",
        "op06_does_not_materialize_p8_question_text",
        "op06_does_not_claim_validation_green",
        "op06_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP06 required true boundary changed: {key}")
    for field, count_field in (
        ("op06_scanned_material_label_refs", "op06_scanned_material_count"),
        ("op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count"),
        ("op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count"),
        ("op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count"),
        ("op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count"),
        ("dhb_op06_reason_refs", "dhb_op06_reason_ref_count"),
        ("dhb_op06_blocker_refs", "dhb_op06_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP06 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP06_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 not-yet steps changed")
    status_ref = data.get("dhb_op06_status_ref")
    flags = [
        data.get("dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed") is True,
        data.get("dhb_op06_repair_required") is True,
        data.get("dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 passed branch next step changed")
        if data.get("op05_material_present") is not True or data.get("op05_contract_valid") is not True:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 passed branch requires valid OP05 material")
        if data.get("dhb_op06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 passed branch cannot carry blockers")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_BODYFREE_NO_TOUCH_GUARD_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_NO_TOUCH_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP06 blocked branch next step changed")
    return True


def _op07_status_reason_blocker_next(
    *,
    op06_present: bool,
    op06_valid: bool,
    op06_guard_passed: bool,
    op06_repair_required: bool,
    op06_blocked: bool,
    op06_op05_crosswalk_recorded: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
    op06_blocker_refs: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths or op06_blocked:
        reasons.append("bodyfree_leak_green_promotion_or_autorun_detected_before_result_memo_draft")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        if op06_blocked:
            blockers.append("op06_bodyfree_guard_blocked")
            blockers.extend(op06_blocker_refs)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[3],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_RESULT_MEMO_DRAFT_REF,
        )
    if not op06_present:
        reasons.append("op06_bodyfree_guard_material_missing")
        blockers.append("op06_material_present_false")
    if not op06_valid:
        reasons.append("op06_bodyfree_guard_contract_invalid")
        blockers.append("op06_contract_valid_false")
    if op06_repair_required:
        reasons.append("op06_bodyfree_guard_repair_required")
        blockers.append("op06_repair_required")
        blockers.extend(op06_blocker_refs)
    if blockers:
        return (
            P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[2],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_RESULT_MEMO_DRAFT_INPUTS_REF,
        )
    if op06_guard_passed and op06_op05_crosswalk_recorded:
        reasons.append("validation_plan_result_memo_draft_materialized_without_green_claim")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[0],
            reasons,
            [],
            P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
        )
    reasons.append("clean_bodyfree_material_preserved_but_dhr_op05_crosswalk_not_recorded_wait_or_stop")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[1],
        reasons,
        [],
        P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_OR_STOP_AFTER_RESULT_MEMO_DRAFT_REF,
    )


def build_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material(
    op06_bodyfree_guard: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Record validation and result-memo draft material without executing or claiming green."""

    op06 = op06_bodyfree_guard
    op06_present = isinstance(op06, Mapping)
    op06_valid = _op06_contract_valid(op06)
    op06_status_ref = _clean_ref(op06.get("dhb_op06_status_ref") if isinstance(op06, Mapping) else None, default="missing", max_length=360)
    op06_guard_passed = bool(isinstance(op06, Mapping) and op06.get("dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed") is True)
    op06_repair_required = bool(isinstance(op06, Mapping) and op06.get("dhb_op06_repair_required") is True)
    op06_blocked = bool(isinstance(op06, Mapping) and op06.get("dhb_op06_bodyfree_no_touch_no_promotion_no_auto_execution_guard_blocked") is True)
    op06_op05_crosswalk_recorded = bool(isinstance(op06, Mapping) and op06.get("op05_compatibility_crosswalk_recorded") is True)
    op06_blocker_refs = _dedupe_clean_refs(op06.get("dhb_op06_blocker_refs") if isinstance(op06, Mapping) else (), max_length=360)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op06 or {}, path="dhb_op06")
    promotion_claims = _dedupe_clean_refs(
        tuple(promotion_claims)
        + tuple(_scan_r5_validation_green_promotion_claim_refs(op06 or {}, path="dhb_op06")),
        max_length=360,
    )
    status_ref, reason_refs, blocker_refs, next_required_step = _op07_status_reason_blocker_next(
        op06_present=op06_present,
        op06_valid=op06_valid,
        op06_guard_passed=op06_guard_passed,
        op06_repair_required=op06_repair_required,
        op06_blocked=op06_blocked,
        op06_op05_crosswalk_recorded=op06_op05_crosswalk_recorded,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
        op06_blocker_refs=op06_blocker_refs,
    )
    materialized = status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[0]
    wait_or_stop = status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[1]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[2]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[3]
    session_id = _safe_review_session_id(
        review_session_id or (op06.get("review_session_id") if isinstance(op06, Mapping) else None)
    )
    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_material_present": op06_present,
        "op06_contract_valid": op06_valid,
        "op06_schema_version": _clean_ref(op06.get("schema_version") if isinstance(op06, Mapping) else None, default="op06_schema_missing", max_length=300),
        "op06_material_ref": _clean_ref(op06.get("material_id") if isinstance(op06, Mapping) else None, default="op06_material_missing", max_length=320),
        "op06_status_ref": op06_status_ref,
        "op06_next_required_step": _clean_ref(op06.get("next_required_step") if isinstance(op06, Mapping) else None, default="op06_next_required_step_missing", max_length=360),
        "op06_guard_passed": op06_guard_passed,
        "op06_repair_required": op06_repair_required,
        "op06_blocked": op06_blocked,
        "op06_op05_crosswalk_recorded": op06_op05_crosswalk_recorded,
        "op07_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op07_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op07_input_body_like_value_path_refs": body_like_paths,
        "op07_input_body_like_value_path_count": len(body_like_paths),
        "op07_input_promotion_claim_refs": promotion_claims,
        "op07_input_promotion_claim_ref_count": len(promotion_claims),
        "op07_input_no_touch_mutation_path_refs": no_touch_paths,
        "op07_input_no_touch_mutation_path_count": len(no_touch_paths),
        "target_validation_command_refs": (P7_R54_AHR_POST_PCM_DHB_OP07_TARGET_VALIDATION_COMMAND_REF,),
        "target_validation_command_ref_count": 1,
        "selected_regression_command_refs": (P7_R54_AHR_POST_PCM_DHB_OP07_SELECTED_REGRESSION_COMMAND_REF,),
        "selected_regression_command_ref_count": 1,
        "compileall_command_refs": (P7_R54_AHR_POST_PCM_DHB_OP07_COMPILEALL_COMMAND_REF,),
        "compileall_command_ref_count": 1,
        "result_memo_expected_file_refs": list(P7_R54_AHR_POST_PCM_DHB_R5_RESULT_MEMO_EXPECTED_FILE_REFS),
        "result_memo_expected_file_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R5_RESULT_MEMO_EXPECTED_FILE_REFS),
        "target_validation_test_ref_refs": list(P7_R54_AHR_POST_PCM_DHB_R5_TARGET_TEST_REF_REFS),
        "target_validation_test_ref_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R5_TARGET_TEST_REF_REFS),
        "selected_regression_test_ref_refs": list(P7_R54_AHR_POST_PCM_DHB_R5_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R5_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_ref_refs": list(P7_R54_AHR_POST_PCM_DHB_R5_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R5_COMPILEALL_TARGET_REF_REFS),
        "validation_commands_executed_here": False,
        "target_validation_green_confirmed_here": False,
        "selected_regression_green_confirmed_here": False,
        "compileall_green_confirmed_here": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "rn_contract_green_claimed_here": False,
        "dhr_op05_not_called": True,
        "dhr_op05_builder_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "actual_review_not_started": True,
        "actual_rows_not_created": True,
        "question_need_observation_rows_not_created": True,
        "p8_question_design_not_started": True,
        "question_text_not_materialized": True,
        "api_db_rn_runtime_response_key_not_changed": True,
        "release_decision_not_made": True,
        "dhb_op07_status_ref": status_ref,
        "bodyfree_validation_plan_result_memo_draft_status_ref": status_ref,
        "dhb_op07_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS),
        "dhb_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS),
        "dhb_op07_validation_plan_result_memo_draft_materialized_stopped": materialized,
        "dhb_op07_wait_or_stop_result_memo_draft_materialized_stopped": wait_or_stop,
        "dhb_op07_repair_required": repair,
        "dhb_op07_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "dhb_op07_reason_refs": reason_refs,
        "dhb_op07_reason_ref_count": len(reason_refs),
        "dhb_op07_blocker_refs": blocker_refs,
        "dhb_op07_blocker_ref_count": len(blocker_refs),
        "op07_does_not_execute_validation_commands": True,
        "op07_does_not_claim_target_green": True,
        "op07_does_not_claim_selected_regression_green": True,
        "op07_does_not_claim_compileall_green": True,
        "op07_keeps_full_backend_suite_unconfirmed": True,
        "op07_keeps_rn_contract_unconfirmed": True,
        "op07_keeps_rn_real_device_unconfirmed": True,
        "op07_does_not_call_dhr_op05": True,
        "op07_does_not_call_dhr_op06": True,
        "op07_does_not_execute_dmd_r52": True,
        "op07_does_not_start_actual_review": True,
        "op07_does_not_start_p8_question_design": True,
        "op07_does_not_change_api_db_rn_runtime_response_key": True,
        "op07_does_not_make_release_decision": True,
        "op07_does_not_create_json_schema_file": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP07_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "dhb_op02_implemented": True,
        "dhb_op03_implemented": True,
        "dhb_op04_implemented": True,
        "dhb_op05_implemented": True,
        "dhb_op06_implemented": True,
        "dhb_op07_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP07 validation-plan/result-memo draft material contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP07")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP07_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP07",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP07_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in ("dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", "dhb_op05_implemented", "dhb_op06_implemented", "dhb_op07_implemented"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP07 implemented flag must be true after R5: {key}")
    if data.get("bodyfree_validation_plan_result_memo_draft_status_ref") != data.get("dhb_op07_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 status alias changed")
    if tuple(data.get("dhb_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 allowed status refs changed")
    if data.get("dhb_op07_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 allowed status count changed")
    for key in (
        "validation_commands_executed_here",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP07 must not claim green/execution: {key}")
    for key in (
        "dhr_op05_not_called",
        "dhr_op05_builder_not_called",
        "dhr_op06_not_called",
        "dmd_r52_not_executed",
        "actual_review_not_started",
        "actual_rows_not_created",
        "question_need_observation_rows_not_created",
        "p8_question_design_not_started",
        "question_text_not_materialized",
        "api_db_rn_runtime_response_key_not_changed",
        "release_decision_not_made",
        "op07_does_not_execute_validation_commands",
        "op07_does_not_claim_target_green",
        "op07_does_not_claim_selected_regression_green",
        "op07_does_not_claim_compileall_green",
        "op07_keeps_full_backend_suite_unconfirmed",
        "op07_keeps_rn_contract_unconfirmed",
        "op07_keeps_rn_real_device_unconfirmed",
        "op07_does_not_call_dhr_op05",
        "op07_does_not_call_dhr_op06",
        "op07_does_not_execute_dmd_r52",
        "op07_does_not_start_actual_review",
        "op07_does_not_start_p8_question_design",
        "op07_does_not_change_api_db_rn_runtime_response_key",
        "op07_does_not_make_release_decision",
        "op07_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP07 required true boundary changed: {key}")
    for field, count_field in (
        ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"),
        ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"),
        ("op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count"),
        ("op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count"),
        ("target_validation_command_refs", "target_validation_command_ref_count"),
        ("selected_regression_command_refs", "selected_regression_command_ref_count"),
        ("compileall_command_refs", "compileall_command_ref_count"),
        ("result_memo_expected_file_refs", "result_memo_expected_file_ref_count"),
        ("target_validation_test_ref_refs", "target_validation_test_ref_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count"),
        ("compileall_target_ref_refs", "compileall_target_ref_ref_count"),
        ("dhb_op07_reason_refs", "dhb_op07_reason_ref_count"),
        ("dhb_op07_blocker_refs", "dhb_op07_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP07 {count_field} changed")
    if tuple(data.get("target_validation_command_refs") or ()) != (P7_R54_AHR_POST_PCM_DHB_OP07_TARGET_VALIDATION_COMMAND_REF,):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 target command refs changed")
    if tuple(data.get("selected_regression_command_refs") or ()) != (P7_R54_AHR_POST_PCM_DHB_OP07_SELECTED_REGRESSION_COMMAND_REF,):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 selected regression command refs changed")
    if tuple(data.get("compileall_command_refs") or ()) != (P7_R54_AHR_POST_PCM_DHB_OP07_COMPILEALL_COMMAND_REF,):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 compileall command refs changed")
    if tuple(data.get("target_validation_test_ref_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R5_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 target test refs changed")
    if tuple(data.get("selected_regression_test_ref_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R5_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 selected regression test refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R5_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 compileall target refs changed")
    if tuple(data.get("result_memo_expected_file_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R5_RESULT_MEMO_EXPECTED_FILE_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 result memo expected refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP07_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 not-yet steps changed")
    status_ref = data.get("dhb_op07_status_ref")
    flags = [
        data.get("dhb_op07_validation_plan_result_memo_draft_materialized_stopped") is True,
        data.get("dhb_op07_wait_or_stop_result_memo_draft_materialized_stopped") is True,
        data.get("dhb_op07_repair_required") is True,
        data.get("dhb_op07_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 must select exactly one status branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 materialized branch next step changed")
        if data.get("op06_material_present") is not True or data.get("op06_contract_valid") is not True or data.get("op06_guard_passed") is not True:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 materialized branch requires valid passed OP06")
        if data.get("op06_op05_crosswalk_recorded") is not True or data.get("dhb_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 materialized branch requires OP05 crosswalk and no blockers")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_OR_STOP_AFTER_RESULT_MEMO_DRAFT_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 wait/stop branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_RESULT_MEMO_DRAFT_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_RESULT_MEMO_DRAFT_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP07 blocked branch next step changed")
    return True


# ---------------------------------------------------------------------------

# R6: DHB-OP08 closure only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_PCM_DHB_R6_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py",
)
P7_R54_AHR_POST_PCM_DHB_R6_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_PCM_DHB_R6_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op00_op01_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op02_op03_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op04_op05_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op06_op07_20260707.py",
    "tests/test_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_pcm_op08_result_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_op01_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_op05_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_op07_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_result_20260707.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_PCM_DHB_R6_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pnt_closed_material_next_boundary_confirmation_20260707.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_PCM_DHB_R6_RESULT_MEMO_EXPECTED_FILE_REFS: Final[tuple[str, ...]] = (
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_OP00_OP08_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R7_TargetValidation_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R8_SelectedRegression_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R9_Compileall_Result_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R10_ResultMemoClosure_20260708.md",
    "mashos-api/ai/tests/R54_AHR_PostPCM_DHROP05ManualHandoffBoundary_DHB_R11_NextWorkDecision_20260708.md",
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_STOP_BEFORE_DHR_OP05_CALL_REF: Final = (
    "stop_before_dhr_op05_call_and_require_separate_explicit_manual_execution_instruction"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_DHR_LANE_REF: Final = (
    "wait_for_one_explicit_pcm_op08_closed_material_selecting_dhr_op05_lane"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_BOUNDARY_INPUTS_REF: Final = (
    "repair_pcm_op08_or_dhb_bodyfree_handoff_inputs_before_any_dhr_op05_call"
)
P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "stop_blocked_bodyfree_leak_promotion_or_autorun_without_next_design_promotion"
)
P7_R54_AHR_POST_PCM_DHB_OP08_EXECUTION_ALLOWANCE_REF: Final = "none_until_separate_explicit_instruction"
P7_R54_AHR_POST_PCM_DHB_OP08_NEXT_WORK_CANDIDATE_WHEN_DHR_CLOSED_REF: Final = (
    "DHR-OP05 manual call / existing DHR-OP05 preflight scan execution consideration"
)
P7_R54_AHR_POST_PCM_DHB_OP08_NEXT_WORK_CANDIDATE_WHEN_NON_DHR_REF: Final = (
    "follow PCM R11 lane-specific decision table outside DHB"
)
P7_R54_AHR_POST_PCM_DHB_OP08_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_PCM_DHB_PROMOTION_CLAIM_FIELD_REFS
        + P7_R54_AHR_POST_PCM_DHB_R5_VALIDATION_GREEN_PROMOTION_CLAIM_FIELD_REFS
        + (
            "dmd_r52_executed_here",
            "api_db_rn_runtime_response_key_changed",
            "validation_commands_executed_here",
            "target_validation_green_confirmed_here",
            "selected_regression_green_confirmed_here",
            "compileall_green_confirmed_here",
            "dhr_op05_manual_call_executed_here",
            "existing_dhr_op05_preflight_scan_executed_here",
        )
    )
)
P7_R54_AHR_POST_PCM_DHB_OP08_BLOCKED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[3],
    P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[2],
    P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[3],
    P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[3],
    P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[2],
    P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[2],
    P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[3],
)
P7_R54_AHR_POST_PCM_DHB_OP08_REPAIR_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[2],
    P7_R54_AHR_POST_PCM_DHB_OP02_ALLOWED_STATUS_REFS[1],
    P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[2],
    P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[2],
    P7_R54_AHR_POST_PCM_DHB_OP05_ALLOWED_STATUS_REFS[1],
    P7_R54_AHR_POST_PCM_DHB_OP06_ALLOWED_STATUS_REFS[1],
    P7_R54_AHR_POST_PCM_DHB_OP07_ALLOWED_STATUS_REFS[2],
)
P7_R54_AHR_POST_PCM_DHB_OP08_WAITING_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[1],
)
P7_R54_AHR_POST_PCM_DHB_OP08_NON_DHR_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_OP03_ALLOWED_STATUS_REFS[1],
    P7_R54_AHR_POST_PCM_DHB_OP04_ALLOWED_STATUS_REFS[1],
)

P7_R54_AHR_POST_PCM_DHB_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_PCM_DHB_R0_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_R1_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP00_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP01_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP02_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP03_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP06_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP07_STEP_REF,
    P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
)
P7_R54_AHR_POST_PCM_DHB_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R54_AHR_POST_PCM_DHB_OP08_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_PCM_DHB_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhb_op00_implemented",
        "dhb_op01_implemented",
        "dhb_op02_implemented",
        "dhb_op03_implemented",
        "dhb_op04_implemented",
        "dhb_op05_implemented",
        "dhb_op06_implemented",
        "dhb_op07_implemented",
        "dhb_op08_implemented",
    }
)
P7_R54_AHR_POST_PCM_DHB_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_material_present", "op07_contract_valid", "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_next_required_step",
    "op07_validation_plan_materialized", "op07_wait_or_stop", "op07_repair_required", "op07_blocked", "op07_op06_guard_passed", "op07_op06_op05_crosswalk_recorded",
    "op08_upstream_material_label_refs", "op08_upstream_material_count", "op08_upstream_status_refs", "op08_upstream_status_ref_count",
    "op08_waiting_status_ref_detected", "op08_non_dhr_route_status_ref_detected", "op08_repair_status_ref_detected", "op08_blocked_status_ref_detected",
    "op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count", "op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count", "op08_input_promotion_claim_refs", "op08_input_promotion_claim_ref_count", "op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count",
    "target_validation_green_confirmed_here", "selected_regression_green_confirmed_here", "compileall_green_confirmed_here", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here",
    "dhb_op08_status_ref", "bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref", "dhb_op08_allowed_status_refs", "dhb_op08_allowed_status_ref_count",
    "dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped", "dhb_op08_not_dhr_op05_lane_route_preserved_stopped", "dhb_op08_waiting_for_explicit_pcm_op08_dhr_lane", "dhb_op08_repair_required", "dhb_op08_bodyfree_leak_promotion_or_autorun_blocked",
    "explicit_pcm_op08_dhr_lane_confirmed", "non_dhr_lane_route_preserved", "dhr_op05_manual_handoff_envelope_materialized", "dhr_op05_manual_handoff_envelope_ready", "dhr_op05_preflight_reentry_candidate_allowed", "dhr_op05_call_still_requires_separate_explicit_instruction",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "existing_dhr_op05_builder_call_allowed_here", "existing_dhr_op05_builder_called_here", "selected_pcm_next_boundary_execution_allowed_here", "dhr_op06_call_allowed_here", "dhr_op07_materialization_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "actual_rows_creation_allowed_here", "question_need_observation_rows_creation_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "p8_question_implementation_allowed_here", "question_text_materialization_allowed_here", "api_db_rn_runtime_response_key_change_allowed_here", "json_schema_file_creation_allowed_here", "p7_complete_allowed_here", "release_decision_allowed_here",
    "dhr_op05_called_here", "dhr_op05_builder_called_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_execution_started_here", "dmd_r52_executed_here", "r52_actual_execution_started_here", "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_question_design_started", "p8_question_implementation_started", "api_db_rn_runtime_response_key_changed", "p7_complete", "release_allowed",
    "dhr_op05_not_called", "dhr_op05_builder_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "actual_review_not_started", "actual_rows_not_created", "question_need_observation_rows_not_created", "p8_question_design_not_started", "question_text_not_materialized", "api_db_rn_runtime_response_key_not_changed", "release_decision_not_made",
    "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "op08_does_not_execute_validation_commands", "op08_does_not_claim_target_green", "op08_does_not_claim_selected_regression_green", "op08_does_not_claim_compileall_green", "op08_keeps_full_backend_suite_unconfirmed", "op08_keeps_rn_contract_unconfirmed", "op08_keeps_rn_real_device_unconfirmed", "op08_does_not_call_dhr_op05", "op08_does_not_call_existing_dhr_op05_builder", "op08_does_not_call_dhr_op06", "op08_does_not_execute_dmd_r52", "op08_does_not_start_actual_review", "op08_does_not_create_actual_rows", "op08_does_not_create_question_need_observation_rows", "op08_does_not_start_p8_question_design", "op08_does_not_materialize_question_text", "op08_does_not_change_api_db_rn_runtime_response_key", "op08_does_not_make_release_decision", "op08_does_not_create_json_schema_file",
    "next_work_candidate_ref", "execution_allowance_ref", "dhb_op08_reason_refs", "dhb_op08_reason_ref_count", "dhb_op08_blocker_refs", "dhb_op08_blocker_ref_count",
    "target_validation_test_ref_refs", "target_validation_test_ref_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count", "compileall_target_ref_refs", "compileall_target_ref_ref_count", "result_memo_expected_file_refs", "result_memo_expected_file_ref_count",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "dhb_no_touch_contract", "body_free_markers", "dhb_op00_implemented", "dhb_op01_implemented", "dhb_op02_implemented", "dhb_op03_implemented", "dhb_op04_implemented", "dhb_op05_implemented", "dhb_op06_implemented", "dhb_op07_implemented", "dhb_op08_implemented", *P7_R54_AHR_POST_PCM_DHB_OP08_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _op07_contract_valid(op07: Mapping[str, Any] | None) -> bool:
    if not isinstance(op07, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_pcm_dhb_op07_validation_plan_result_memo_draft_material_contract(op07) is True
    except ValueError:
        return False


def _scan_op08_promotion_claim_refs(value: Any, *, path: str = "artifact") -> list[str]:
    refs: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_PCM_DHB_OP08_PROMOTION_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_op08_promotion_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_op08_promotion_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _op08_upstream_materials(
    op07: Mapping[str, Any] | None,
    upstream_dhb_materials: Sequence[Mapping[str, Any]] | None,
) -> tuple[list[Mapping[str, Any]], list[str]]:
    materials: list[Mapping[str, Any]] = []
    labels: list[str] = []
    if isinstance(op07, Mapping):
        materials.append(op07)
        labels.append("op07_validation_plan_result_memo_draft")
    for index, material in enumerate(upstream_dhb_materials or ()):  # type: ignore[arg-type]
        if isinstance(material, Mapping):
            materials.append(material)
            step_ref = _clean_ref(material.get("operation_step_ref"), default=f"upstream_material_{index}", max_length=180)
            labels.append(step_ref)
    return materials, labels


def _op08_status_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    status_keys = (
        "dhb_op01_status_ref",
        "dhb_op02_status_ref",
        "dhb_op03_status_ref",
        "dhb_op04_status_ref",
        "dhb_op05_status_ref",
        "dhb_op06_status_ref",
        "dhb_op07_status_ref",
        "bodyfree_pcm_op08_closed_material_intake_status_ref",
        "bodyfree_pcm_op08_contract_validation_status_ref",
        "bodyfree_dhr_op05_lane_exact_confirmation_status_ref",
        "bodyfree_dhr_op05_manual_handoff_envelope_status_ref",
        "bodyfree_dhr_op05_compatibility_crosswalk_status_ref",
        "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref",
        "bodyfree_validation_plan_result_memo_draft_status_ref",
    )
    refs: list[str] = []
    for material in materials:
        for key in status_keys:
            if key in material:
                refs.append(_clean_ref(material.get(key), default="missing", max_length=360))
    return _dedupe_clean_refs(refs, max_length=360)


def _op08_scan_quads(materials: Sequence[Mapping[str, Any]]) -> tuple[list[str], list[str], list[str], list[str]]:
    scan_input = {f"op08_material_{index}": material for index, material in enumerate(materials)}
    forbidden_paths, body_like_paths, _, no_touch_paths = _bodyfree_no_touch_scan_quads(scan_input, path="dhb_op08_materials")
    promotion_claims = _dedupe_clean_refs(_scan_op08_promotion_claim_refs(scan_input, path="dhb_op08_materials"), max_length=360)
    return forbidden_paths, body_like_paths, promotion_claims, no_touch_paths


def _op08_status_reason_blocker_next(
    *,
    op07_present: bool,
    op07_valid: bool,
    op07_materialized: bool,
    op07_wait_or_stop: bool,
    op07_repair_required: bool,
    op07_blocked: bool,
    op07_op06_guard_passed: bool,
    op07_op06_op05_crosswalk_recorded: bool,
    status_refs: Sequence[str],
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str, str]:
    reasons: list[str] = []
    blockers: list[str] = []
    has_blocked_status = any(status_ref in P7_R54_AHR_POST_PCM_DHB_OP08_BLOCKED_STATUS_REFS for status_ref in status_refs)
    has_waiting_status = any(status_ref in P7_R54_AHR_POST_PCM_DHB_OP08_WAITING_STATUS_REFS for status_ref in status_refs)
    has_non_dhr_status = any(status_ref in P7_R54_AHR_POST_PCM_DHB_OP08_NON_DHR_STATUS_REFS for status_ref in status_refs)
    has_repair_status = any(status_ref in P7_R54_AHR_POST_PCM_DHB_OP08_REPAIR_STATUS_REFS for status_ref in status_refs)

    if forbidden_paths or body_like_paths or promotion_claims or no_touch_paths or op07_blocked or has_blocked_status:
        reasons.append("bodyfree_leak_promotion_or_autorun_detected_before_dhb_op08_closure")
        blockers.extend(forbidden_paths)
        blockers.extend(body_like_paths)
        blockers.extend(promotion_claims)
        blockers.extend(no_touch_paths)
        if op07_blocked:
            blockers.append("op07_result_memo_draft_blocked")
        if has_blocked_status:
            blockers.extend(status_ref for status_ref in status_refs if status_ref in P7_R54_AHR_POST_PCM_DHB_OP08_BLOCKED_STATUS_REFS)
        return (
            P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[4],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
            "blocked_without_next_design_promotion",
        )

    if has_waiting_status:
        reasons.append("explicit_pcm_op08_material_missing_or_not_confirmed_as_dhr_lane")
        blockers.append(P7_R54_AHR_POST_PCM_DHB_OP01_ALLOWED_STATUS_REFS[1])
        return (
            P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[2],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_DHR_LANE_REF,
            "hold_until_explicit_pcm_op08_dhr_lane_material_exists",
        )

    if op07_present and op07_valid and op07_materialized and op07_op06_guard_passed and op07_op06_op05_crosswalk_recorded and not has_repair_status:
        reasons.append("dhb_op08_closed_dhr_op05_manual_handoff_boundary_stopped_without_call")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0],
            _dedupe_clean_refs(reasons, max_length=360),
            [],
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_STOP_BEFORE_DHR_OP05_CALL_REF,
            P7_R54_AHR_POST_PCM_DHB_OP08_NEXT_WORK_CANDIDATE_WHEN_DHR_CLOSED_REF,
        )

    if has_non_dhr_status:
        reasons.append("non_dhr_op05_lane_route_preserved_without_dhr_op05_handoff_envelope")
        return (
            P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[1],
            _dedupe_clean_refs(reasons, max_length=360),
            [],
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF,
            P7_R54_AHR_POST_PCM_DHB_OP08_NEXT_WORK_CANDIDATE_WHEN_NON_DHR_REF,
        )

    if not op07_present:
        reasons.append("op07_validation_plan_result_memo_draft_missing_before_op08_closure")
        blockers.append("op07_material_present_false")
    if not op07_valid:
        reasons.append("op07_validation_plan_result_memo_draft_contract_invalid_before_op08_closure")
        blockers.append("op07_contract_valid_false")
    if op07_repair_required:
        reasons.append("op07_result_memo_draft_repair_required_before_op08_closure")
        blockers.append("op07_repair_required")
    if has_repair_status:
        reasons.append("upstream_dhb_repair_status_detected_before_op08_closure")
        blockers.extend(status_ref for status_ref in status_refs if status_ref in P7_R54_AHR_POST_PCM_DHB_OP08_REPAIR_STATUS_REFS)
    if op07_wait_or_stop and not has_non_dhr_status:
        reasons.append("op07_wait_or_stop_requires_upstream_route_status_to_close_exactly")
        blockers.append("op07_wait_or_stop_without_explicit_non_dhr_or_wait_status")
    if blockers or not (op07_present and op07_valid):
        return (
            P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[3],
            _dedupe_clean_refs(reasons, max_length=360),
            _dedupe_clean_refs(blockers, max_length=360),
            P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_BOUNDARY_INPUTS_REF,
            "repair_upstream_pcm_or_dhb_bodyfree_handoff_inputs",
        )

    reasons.append("op08_closure_inputs_ambiguous_without_dhr_lane_wait_repair_or_blocked_status")
    blockers.append("op08_closure_inputs_ambiguous")
    return (
        P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[3],
        _dedupe_clean_refs(reasons, max_length=360),
        _dedupe_clean_refs(blockers, max_length=360),
        P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_BOUNDARY_INPUTS_REF,
        "repair_upstream_pcm_or_dhb_bodyfree_handoff_inputs",
    )


def build_p7_r54_ahr_post_pcm_dhb_op08_bodyfree_dhr_op05_manual_handoff_boundary_closure(
    op07_validation_plan_result_memo_draft: Mapping[str, Any] | None = None,
    *,
    upstream_dhb_materials: Sequence[Mapping[str, Any]] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Close DHB-OP08 without allowing or calling DHR-OP05 or downstream execution."""

    op07 = op07_validation_plan_result_memo_draft
    op07_present = isinstance(op07, Mapping)
    op07_valid = _op07_contract_valid(op07)
    op07_status_ref = _clean_ref(op07.get("dhb_op07_status_ref") if isinstance(op07, Mapping) else None, default="missing", max_length=360)
    op07_materialized = bool(isinstance(op07, Mapping) and op07.get("dhb_op07_validation_plan_result_memo_draft_materialized_stopped") is True)
    op07_wait_or_stop = bool(isinstance(op07, Mapping) and op07.get("dhb_op07_wait_or_stop_result_memo_draft_materialized_stopped") is True)
    op07_repair_required = bool(isinstance(op07, Mapping) and op07.get("dhb_op07_repair_required") is True)
    op07_blocked = bool(isinstance(op07, Mapping) and op07.get("dhb_op07_bodyfree_leak_promotion_or_autorun_blocked") is True)
    op07_op06_guard_passed = bool(isinstance(op07, Mapping) and op07.get("op06_guard_passed") is True)
    op07_op06_op05_crosswalk_recorded = bool(isinstance(op07, Mapping) and op07.get("op06_op05_crosswalk_recorded") is True)
    materials, labels = _op08_upstream_materials(op07, upstream_dhb_materials)
    status_refs = _op08_status_refs(materials)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _op08_scan_quads(materials)
    status_ref, reason_refs, blocker_refs, next_required_step, next_work_candidate = _op08_status_reason_blocker_next(
        op07_present=op07_present,
        op07_valid=op07_valid,
        op07_materialized=op07_materialized,
        op07_wait_or_stop=op07_wait_or_stop,
        op07_repair_required=op07_repair_required,
        op07_blocked=op07_blocked,
        op07_op06_guard_passed=op07_op06_guard_passed,
        op07_op06_op05_crosswalk_recorded=op07_op06_op05_crosswalk_recorded,
        status_refs=status_refs,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    closed = status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]
    non_dhr = status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[1]
    waiting = status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[2]
    repair = status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[3]
    blocked = status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[4]
    session_id = _safe_review_session_id(
        review_session_id or (op07.get("review_session_id") if isinstance(op07, Mapping) else None)
    )
    return {
        "schema_version": P7_R54_AHR_POST_PCM_DHB_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "step": P7_R54_AHR_POST_PCM_DHB_STEP,
        "scope": P7_R54_AHR_POST_PCM_DHB_SCOPE,
        "policy_kind": P7_R54_AHR_POST_PCM_DHB_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_PCM_DHB_PHASE,
        "material_id": "p7_r54_ahr_post_pcm_dhb_op08_bodyfree_manual_handoff_boundary_closure_20260708",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_PCM_DHB_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_material_present": op07_present,
        "op07_contract_valid": op07_valid,
        "op07_schema_version": _clean_ref(op07.get("schema_version") if isinstance(op07, Mapping) else None, default="op07_schema_missing", max_length=300),
        "op07_material_ref": _clean_ref(op07.get("material_id") if isinstance(op07, Mapping) else None, default="op07_material_missing", max_length=320),
        "op07_status_ref": op07_status_ref,
        "op07_next_required_step": _clean_ref(op07.get("next_required_step") if isinstance(op07, Mapping) else None, default="op07_next_required_step_missing", max_length=360),
        "op07_validation_plan_materialized": op07_materialized,
        "op07_wait_or_stop": op07_wait_or_stop,
        "op07_repair_required": op07_repair_required,
        "op07_blocked": op07_blocked,
        "op07_op06_guard_passed": op07_op06_guard_passed,
        "op07_op06_op05_crosswalk_recorded": op07_op06_op05_crosswalk_recorded,
        "op08_upstream_material_label_refs": labels,
        "op08_upstream_material_count": len(labels),
        "op08_upstream_status_refs": status_refs,
        "op08_upstream_status_ref_count": len(status_refs),
        "op08_waiting_status_ref_detected": any(status in P7_R54_AHR_POST_PCM_DHB_OP08_WAITING_STATUS_REFS for status in status_refs),
        "op08_non_dhr_route_status_ref_detected": any(status in P7_R54_AHR_POST_PCM_DHB_OP08_NON_DHR_STATUS_REFS for status in status_refs),
        "op08_repair_status_ref_detected": any(status in P7_R54_AHR_POST_PCM_DHB_OP08_REPAIR_STATUS_REFS for status in status_refs),
        "op08_blocked_status_ref_detected": any(status in P7_R54_AHR_POST_PCM_DHB_OP08_BLOCKED_STATUS_REFS for status in status_refs),
        "op08_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op08_input_body_like_value_path_refs": body_like_paths,
        "op08_input_body_like_value_path_count": len(body_like_paths),
        "op08_input_promotion_claim_refs": promotion_claims,
        "op08_input_promotion_claim_ref_count": len(promotion_claims),
        "op08_input_no_touch_mutation_path_refs": no_touch_paths,
        "op08_input_no_touch_mutation_path_count": len(no_touch_paths),
        "target_validation_green_confirmed_here": False,
        "selected_regression_green_confirmed_here": False,
        "compileall_green_confirmed_here": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "rn_contract_green_claimed_here": False,
        "dhb_op08_status_ref": status_ref,
        "bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref": status_ref,
        "dhb_op08_allowed_status_refs": list(P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS),
        "dhb_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS),
        "dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped": closed,
        "dhb_op08_not_dhr_op05_lane_route_preserved_stopped": non_dhr,
        "dhb_op08_waiting_for_explicit_pcm_op08_dhr_lane": waiting,
        "dhb_op08_repair_required": repair,
        "dhb_op08_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "explicit_pcm_op08_dhr_lane_confirmed": closed,
        "non_dhr_lane_route_preserved": non_dhr,
        "dhr_op05_manual_handoff_envelope_materialized": closed,
        "dhr_op05_manual_handoff_envelope_ready": closed,
        "dhr_op05_preflight_reentry_candidate_allowed": closed,
        "dhr_op05_call_still_requires_separate_explicit_instruction": closed,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "existing_dhr_op05_builder_call_allowed_here": False,
        "existing_dhr_op05_builder_called_here": False,
        "selected_pcm_next_boundary_execution_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dhr_op07_materialization_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "actual_rows_creation_allowed_here": False,
        "question_need_observation_rows_creation_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "p8_question_implementation_allowed_here": False,
        "question_text_materialization_allowed_here": False,
        "api_db_rn_runtime_response_key_change_allowed_here": False,
        "json_schema_file_creation_allowed_here": False,
        "p7_complete_allowed_here": False,
        "release_decision_allowed_here": False,
        "dhr_op05_called_here": False,
        "dhr_op05_builder_called_here": False,
        "dhr_op06_called_here": False,
        "dhr_op07_materialized_here": False,
        "dmd_execution_started_here": False,
        "dmd_r52_executed_here": False,
        "r52_actual_execution_started_here": False,
        "actual_review_started_here": False,
        "actual_rows_created_here": False,
        "question_need_observation_rows_created_here": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "api_db_rn_runtime_response_key_changed": False,
        "p7_complete": False,
        "release_allowed": False,
        "dhr_op05_not_called": True,
        "dhr_op05_builder_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "actual_review_not_started": True,
        "actual_rows_not_created": True,
        "question_need_observation_rows_not_created": True,
        "p8_question_design_not_started": True,
        "question_text_not_materialized": True,
        "api_db_rn_runtime_response_key_not_changed": True,
        "release_decision_not_made": True,
        "op08_does_not_execute_validation_commands": True,
        "op08_does_not_claim_target_green": True,
        "op08_does_not_claim_selected_regression_green": True,
        "op08_does_not_claim_compileall_green": True,
        "op08_keeps_full_backend_suite_unconfirmed": True,
        "op08_keeps_rn_contract_unconfirmed": True,
        "op08_keeps_rn_real_device_unconfirmed": True,
        "op08_does_not_call_dhr_op05": True,
        "op08_does_not_call_existing_dhr_op05_builder": True,
        "op08_does_not_call_dhr_op06": True,
        "op08_does_not_execute_dmd_r52": True,
        "op08_does_not_start_actual_review": True,
        "op08_does_not_create_actual_rows": True,
        "op08_does_not_create_question_need_observation_rows": True,
        "op08_does_not_start_p8_question_design": True,
        "op08_does_not_materialize_question_text": True,
        "op08_does_not_change_api_db_rn_runtime_response_key": True,
        "op08_does_not_make_release_decision": True,
        "op08_does_not_create_json_schema_file": True,
        "next_work_candidate_ref": next_work_candidate,
        "execution_allowance_ref": P7_R54_AHR_POST_PCM_DHB_OP08_EXECUTION_ALLOWANCE_REF,
        "dhb_op08_reason_refs": reason_refs,
        "dhb_op08_reason_ref_count": len(reason_refs),
        "dhb_op08_blocker_refs": blocker_refs,
        "dhb_op08_blocker_ref_count": len(blocker_refs),
        "target_validation_test_ref_refs": list(P7_R54_AHR_POST_PCM_DHB_R6_TARGET_TEST_REF_REFS),
        "target_validation_test_ref_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R6_TARGET_TEST_REF_REFS),
        "selected_regression_test_ref_refs": list(P7_R54_AHR_POST_PCM_DHB_R6_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R6_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_ref_refs": list(P7_R54_AHR_POST_PCM_DHB_R6_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R6_COMPILEALL_TARGET_REF_REFS),
        "result_memo_expected_file_refs": list(P7_R54_AHR_POST_PCM_DHB_R6_RESULT_MEMO_EXPECTED_FILE_REFS),
        "result_memo_expected_file_ref_count": len(P7_R54_AHR_POST_PCM_DHB_R6_RESULT_MEMO_EXPECTED_FILE_REFS),
        "claim_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_PCM_DHB_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "dhb_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(P7_R54_AHR_POST_PCM_DHB_OP08_REQUIRED_FALSE_FLAG_REFS),
        "dhb_op00_implemented": True,
        "dhb_op01_implemented": True,
        "dhb_op02_implemented": True,
        "dhb_op03_implemented": True,
        "dhb_op04_implemented": True,
        "dhb_op05_implemented": True,
        "dhb_op06_implemented": True,
        "dhb_op07_implemented": True,
        "dhb_op08_implemented": True,
        "body_free": True,
    }


def assert_p7_r54_ahr_post_pcm_dhb_op08_bodyfree_dhr_op05_manual_handoff_boundary_closure_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHB-OP08 closure without DHR-OP05 call permission or downstream execution."""

    _required_fields_present(data, required=P7_R54_AHR_POST_PCM_DHB_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostPCM-DHB-OP08")
    if set(data) != set(P7_R54_AHR_POST_PCM_DHB_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_PCM_DHB_OP08_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF,
        source="P7-R54-AHR-PostPCM-DHB-OP08",
        required_false_flag_refs=P7_R54_AHR_POST_PCM_DHB_OP08_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "dhb_op00_implemented",
        "dhb_op01_implemented",
        "dhb_op02_implemented",
        "dhb_op03_implemented",
        "dhb_op04_implemented",
        "dhb_op05_implemented",
        "dhb_op06_implemented",
        "dhb_op07_implemented",
        "dhb_op08_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP08 implemented flag must be true after R6: {key}")
    if data.get("bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref") != data.get("dhb_op08_status_ref"):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 status alias changed")
    if tuple(data.get("dhb_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 allowed status refs changed")
    if data.get("dhb_op08_allowed_status_ref_count") != len(P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 allowed status count changed")
    for key in (
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "selected_pcm_next_boundary_execution_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "p8_question_implementation_allowed_here",
        "question_text_materialization_allowed_here",
        "api_db_rn_runtime_response_key_change_allowed_here",
        "json_schema_file_creation_allowed_here",
        "p7_complete_allowed_here",
        "release_decision_allowed_here",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "api_db_rn_runtime_response_key_changed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP08 must not claim execution/promotion/green: {key}")
    for key in (
        "dhr_op05_not_called",
        "dhr_op05_builder_not_called",
        "dhr_op06_not_called",
        "dmd_r52_not_executed",
        "actual_review_not_started",
        "actual_rows_not_created",
        "question_need_observation_rows_not_created",
        "p8_question_design_not_started",
        "question_text_not_materialized",
        "api_db_rn_runtime_response_key_not_changed",
        "release_decision_not_made",
        "op08_does_not_execute_validation_commands",
        "op08_does_not_claim_target_green",
        "op08_does_not_claim_selected_regression_green",
        "op08_does_not_claim_compileall_green",
        "op08_keeps_full_backend_suite_unconfirmed",
        "op08_keeps_rn_contract_unconfirmed",
        "op08_keeps_rn_real_device_unconfirmed",
        "op08_does_not_call_dhr_op05",
        "op08_does_not_call_existing_dhr_op05_builder",
        "op08_does_not_call_dhr_op06",
        "op08_does_not_execute_dmd_r52",
        "op08_does_not_start_actual_review",
        "op08_does_not_create_actual_rows",
        "op08_does_not_create_question_need_observation_rows",
        "op08_does_not_start_p8_question_design",
        "op08_does_not_materialize_question_text",
        "op08_does_not_change_api_db_rn_runtime_response_key",
        "op08_does_not_make_release_decision",
        "op08_does_not_create_json_schema_file",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP08 required true boundary changed: {key}")
    for field, count_field in (
        ("op08_upstream_material_label_refs", "op08_upstream_material_count"),
        ("op08_upstream_status_refs", "op08_upstream_status_ref_count"),
        ("op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count"),
        ("op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count"),
        ("op08_input_promotion_claim_refs", "op08_input_promotion_claim_ref_count"),
        ("op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count"),
        ("dhb_op08_reason_refs", "dhb_op08_reason_ref_count"),
        ("dhb_op08_blocker_refs", "dhb_op08_blocker_ref_count"),
        ("target_validation_test_ref_refs", "target_validation_test_ref_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count"),
        ("compileall_target_ref_refs", "compileall_target_ref_ref_count"),
        ("result_memo_expected_file_refs", "result_memo_expected_file_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP08 {count_field} changed")
    if tuple(data.get("target_validation_test_ref_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R6_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 target test refs changed")
    if tuple(data.get("selected_regression_test_ref_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R6_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 selected regression test refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R6_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 compileall target refs changed")
    if tuple(data.get("result_memo_expected_file_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_R6_RESULT_MEMO_EXPECTED_FILE_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 result memo expected refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_PCM_DHB_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP08_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_PCM_DHB_OP08_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 not-yet steps changed")
    if data.get("execution_allowance_ref") != P7_R54_AHR_POST_PCM_DHB_OP08_EXECUTION_ALLOWANCE_REF:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 execution allowance changed")
    status_ref = data.get("dhb_op08_status_ref")
    flags = [
        data.get("dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped") is True,
        data.get("dhb_op08_not_dhr_op05_lane_route_preserved_stopped") is True,
        data.get("dhb_op08_waiting_for_explicit_pcm_op08_dhr_lane") is True,
        data.get("dhb_op08_repair_required") is True,
        data.get("dhb_op08_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 must select exactly one closure branch")
    if status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_STOP_BEFORE_DHR_OP05_CALL_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 closed branch next step changed")
        for key in (
            "op07_material_present",
            "op07_contract_valid",
            "op07_validation_plan_materialized",
            "op07_op06_guard_passed",
            "op07_op06_op05_crosswalk_recorded",
            "explicit_pcm_op08_dhr_lane_confirmed",
            "dhr_op05_manual_handoff_envelope_materialized",
            "dhr_op05_call_still_requires_separate_explicit_instruction",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostPCM-DHB-OP08 closed branch missing true field: {key}")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_FOLLOW_PCM_R11_LANE_SPECIFIC_DECISION_TABLE_OUTSIDE_DHB_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 non-DHR branch next step changed")
        if data.get("non_dhr_lane_route_preserved") is not True:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 non-DHR branch must preserve route")
        if data.get("dhr_op05_manual_handoff_envelope_materialized") is not False:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 non-DHR branch must not materialize DHR envelope")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_WAIT_FOR_EXPLICIT_PCM_OP08_DHR_LANE_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 waiting branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_REPAIR_DHR_OP05_HANDOFF_BOUNDARY_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 repair branch next step changed")
    elif status_ref == P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[4]:
        if data.get("next_required_step") != P7_R54_AHR_POST_PCM_DHB_NEXT_STEP_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF:
            raise ValueError("P7-R54-AHR-PostPCM-DHB-OP08 blocked branch next step changed")
    return True
