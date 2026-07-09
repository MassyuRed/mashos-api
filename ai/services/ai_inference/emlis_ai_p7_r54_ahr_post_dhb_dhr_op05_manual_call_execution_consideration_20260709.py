# -*- coding: utf-8 -*-
"""Post-DHB DHR-OP05 manual call execution consideration helpers.

R0/R1 implemented first only. R0 freezes the design-reflection scope before any
DHC-OP00+ implementation. R1 adds the DHC helper skeleton constants, status
refs, false flags, forbidden refs, existing DHR-OP04/DHR-OP05 reference strings,
and imported existing DHR reference handles.

Important boundary:
* DHC is not a DHB reimplementation and does not synthesize DHB-OP08 material.
* DHC does not treat a DHB handoff envelope as DHR-OP04 actual source claim
  separation.
* DHC keeps the existing DHR-OP05 builder callable referenced but uncalled at
  R1. Future code may call it only inside DHC-OP04 after explicit OP04 material
  and explicit manual-call permission are both confirmed.
* DHC R1 does not execute DHR-OP05, DHR-OP06, DHR-OP07, DMD, R52, actual review,
  actual rows, question rows, P8, release, API/DB/RN/runtime/response-key
  changes, validation commands, or json/schema file creation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Callable, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708 as dhb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr


P7_R54_AHR_POST_DHB_DHC_PHASE: Final = "P7"
P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_DHB_DHC_STEP: Final = (
    "R54-AHR-PostDHB_DHROP05ManualCallExecutionConsideration_20260709"
)
P7_R54_AHR_POST_DHB_DHC_SCOPE: Final = (
    "p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration"
)
P7_R54_AHR_POST_DHB_DHC_POLICY_KIND: Final = (
    "r54_ahr_post_dhb_controlled_manual_dhr_op05_preflight_scan_boundary"
)
P7_R54_AHR_POST_DHB_DHC_DEFAULT_REVIEW_SESSION_ID: Final = (
    "p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709"
)
P7_R54_AHR_POST_DHB_DHC_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-DHB DHR-OP05 Manual Call / Existing Preflight Scan Execution Consideration"
)
P7_R54_AHR_POST_DHB_DHC_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-DHB DHR-OP05 Manual Call / Existing DHR-OP05 Preflight Scan Execution Consideration"
)
P7_R54_AHR_POST_DHB_DHC_BOUNDARY_PREFIX_REF: Final = "DHC"
P7_R54_AHR_POST_DHB_DHC_BOUNDARY_PREFIX_MEANING_REF: Final = (
    "DHR-OP05 Manual Call Consideration / Existing Preflight Scan Boundary"
)
P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF: Final = "R0_design_reflection_pre_freeze"
P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF: Final = "R1_helper_skeleton_constants"
P7_R54_AHR_POST_DHB_DHC_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_DHC_OP00_scope_no_execution_refreeze_after_DHB_R11"
)
P7_R54_AHR_POST_DHB_DHC_CURRENT_EXECUTION_ALLOWANCE_REF: Final = (
    "none_until_DHC_OP03_permission_gate_and_DHC_OP04_manual_call_boundary"
)
P7_R54_AHR_POST_DHB_DHC_BUILDER_CALL_BOUNDARY_REF: Final = (
    "existing_DHR_OP05_builder_call_may_exist_only_inside_future_DHC_OP04_with_explicit_OP04_and_manual_permission"
)
P7_R54_AHR_POST_DHB_DHC_IMPLICIT_OP04_FALLBACK_REF: Final = (
    "implicit_DHR_OP04_builder_fallback_is_present_in_existing_DHR_OP05_builder_but_disallowed_by_DHC"
)

P7_R54_AHR_POST_DHB_DHC_R1_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.r1_helper_skeleton_constants_summary.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op00_scope_no_execution_refreeze_after_dhb_r11.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op01_explicit_dhb_op08_closed_handoff_material_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op02_existing_dhr_op05_builder_input_eligibility_check.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op03_manual_call_permission_gate.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op04_existing_dhr_op05_preflight_scan_manual_call_boundary.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op05_existing_dhr_op05_result_classification.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op06_no_touch_no_promotion_no_auto_downstream_guard.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op07_validation_plan_result_memo_draft_material.bodyfree.v1"
)
P7_R54_AHR_POST_DHB_DHC_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op08_result_memo_closure_stopped_next_work_candidate.bodyfree.v1"
)

P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF: Final = (
    "DHC-OP00_scope_no_execution_refreeze_after_DHB_R11"
)
P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF: Final = (
    "DHC-OP01_explicit_DHB_OP08_closed_handoff_material_intake"
)
P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF: Final = (
    "DHC-OP02_existing_DHR_OP05_builder_input_eligibility_check"
)
P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF: Final = (
    "DHC-OP03_manual_call_permission_gate"
)
P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF: Final = (
    "DHC-OP04_existing_DHR_OP05_preflight_scan_manual_call_boundary"
)
P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF: Final = (
    "DHC-OP05_DHR_OP05_result_classification"
)
P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF: Final = (
    "DHC-OP06_no_touch_no_promotion_no_auto_downstream_guard"
)
P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF: Final = (
    "DHC-OP07_validation_plan_result_memo_draft_material"
)
P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF: Final = (
    "DHC-OP08_result_memo_closure_stopped_next_work_candidate"
)
P7_R54_AHR_POST_DHB_DHC_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_SCHEMA_VERSION_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP00_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP01_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP02_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP03_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP04_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP05_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP06_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP07_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHB_DHC_OP08_SCHEMA_VERSION,
)
P7_R54_AHR_POST_DHB_DHC_R0_R1_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_R0_R1_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_STEP_REFS
)

P7_R54_AHR_POST_DHB_DHC_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REQUIRED: Final = True
P7_R54_AHR_POST_DHB_DHC_DHB_OP08_MATERIAL_SYNTHESIS_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DHB_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DHB_R11_MEMO_AS_DHB_OP08_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DHB_HANDOFF_ENVELOPE_AS_DHR_OP04_INPUT_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REQUIRED: Final = True
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_CALL_ALLOWED_IN_R1: Final = False
P7_R54_AHR_POST_DHB_DHC_IMPLICIT_OP04_BUILDER_FALLBACK_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_IMPLICIT_OP04_BUILDER_FALLBACK_USED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_MANUAL_CALL_REQUESTED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_MANUAL_CALL_PERMISSION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_CALLED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_RESULT_PRESENT_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_CONTRACT_VALID_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DHR_OP05_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DHR_OP05_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DHR_OP06_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DHR_OP07_MATERIALIZATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_DMD_R52_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_ACTUAL_REVIEW_START_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_ACTUAL_ROWS_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_QUESTION_NEED_OBSERVATION_ROWS_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_REPAIR_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_RAW_EVIDENCE_REQUEST_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_P8_QUESTION_DESIGN_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_P8_QUESTION_IMPLEMENTATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_QUESTION_TEXT_MATERIALIZATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_API_DB_RN_RUNTIME_RESPONSE_KEY_CHANGE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_P7_COMPLETE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_RELEASE_DECISION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_FULL_BACKEND_SUITE_GREEN_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_RN_CONTRACT_GREEN_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_RN_REAL_DEVICE_MODAL_VERIFICATION_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHB_DHC_BODY_FREE: Final = True

P7_R54_AHR_POST_DHB_DHC_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(302).zip",
    "implemented_docs": "EmlisAIの実装済み資料(105).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_system_update_20260706(5).zip",
    "cocolon_app": "Cocolon(277).zip",
    "backend": "mashos-api(193).zip",
}
P7_R54_AHR_POST_DHB_DHC_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/manifest.json",
    "Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/09_work_start_checklist.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/14_cocolon_joint_development_and_karen_thought_boundary.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/15_trust_based_joint_development_boundary_2026_06_05.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt",
    "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
    "Cocolon_前提資料/cocolon_thought_material_for_karen.md",
    "Cocolon_前提資料/emlis_ai_state_answer_human_follow_definition_2026_05_26.md",
    "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostDHB_DHROP05ManualCallExecutionConsideration_PreDesignMemo_20260709.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DetailedDesign_ImplementationOrder_20260709.md",
)
P7_R54_AHR_POST_DHB_DHC_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "DHB reimplementation",
    "DHB-OP08 material synthesis",
    "DHB handoff envelope to DHR-OP04 actual source claim conversion",
    "DHR-OP05 execution in R1",
    "existing DHR-OP05 builder call in R1",
    "DHR-OP06 / DHR-OP07 execution",
    "DMD / R52 execution",
    "actual review start or actual rows creation",
    "question need observation rows creation",
    "P8 question design / implementation",
    "question_text / draft_question_text / answer_text materialization",
    "API / DB / RN / runtime / response key change",
    "json / schema file creation",
    "P7 completion",
    "release decision",
)
P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "DHC R0/R1 freezes the Post-DHB controlled manual call consideration scope and constants",
    "DHC helper body must require explicit DHB-OP08 closure material in future OP01 work",
    "DHC helper body must not synthesize DHB-OP08 material or re-run DHB",
    "DHC helper body must not treat DHB handoff envelope as DHR-OP04 actual source claim separation",
    "DHC helper body must require explicit DHR-OP04 actual source claim separation before any future builder call",
    "DHC constants keep existing DHR-OP05 builder/assert refs as string refs and imported refs",
    "DHC constants keep existing DHR-OP05 builder call unavailable until future DHC-OP04 permission",
    "DHC constants keep implicit DHR-OP04 fallback disallowed",
    "DHC constants keep DHR-OP06, DHR-OP07, DMD, R52, actual review, P8, and release unavailable",
    "DHC constants keep API / DB / RN / runtime / response key no-touch",
)
P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "dhc_op00_implemented",
    "dhc_op01_implemented",
    "dhc_op02_implemented",
    "dhc_op03_implemented",
    "dhc_op04_implemented",
    "dhc_op05_implemented",
    "dhc_op06_implemented",
    "dhc_op07_implemented",
    "dhc_op08_implemented",
    "dhb_op08_material_synthesized_here",
    "dhb_builder_called_here",
    "dhb_r11_memo_used_as_dhb_op08_here",
    "dhb_handoff_envelope_used_as_dhr_op04_input_here",
    "existing_dhr_op04_assert_called_here",
    "implicit_op04_builder_fallback_allowed_here",
    "implicit_op04_builder_fallback_used_here",
    "manual_call_requested_here",
    "manual_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
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
    "raw_evidence_request_created_here",
    "repair_executed_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "api_db_rn_runtime_response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_dhb_op08_material_synthesis",
    "no_dhb_builder_call",
    "no_dhb_r11_memo_as_dhb_op08_material",
    "no_dhb_handoff_envelope_as_dhr_op04_actual_source_claim_separation",
    "no_existing_dhr_op04_assert_call_in_r1",
    "no_implicit_dhr_op04_fallback",
    "no_manual_call_permission_in_r1",
    "no_existing_dhr_op05_builder_call_in_r1",
    "no_dhr_op05_result_classification_in_r1",
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

P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_SCHEMA_VERSION_REF: Final = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_SCHEMA_VERSION
P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_STEP_REF: Final = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_STEP_REF
P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_CLOSED_STATUS_REF: Final = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS[0]
P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = dhb.P7_R54_AHR_POST_PCM_DHB_OP08_ALLOWED_STATUS_REFS
P7_R54_AHR_POST_DHB_DHC_DHB_OP04_HANDOFF_ENVELOPE_STEP_REF: Final = dhb.P7_R54_AHR_POST_PCM_DHB_OP04_STEP_REF
P7_R54_AHR_POST_DHB_DHC_DHB_OP05_COMPATIBILITY_CROSSWALK_STEP_REF: Final = dhb.P7_R54_AHR_POST_PCM_DHB_OP05_STEP_REF
P7_R54_AHR_POST_DHB_DHC_DHB_DHR_OP05_LANE_REF: Final = dhb.P7_R54_AHR_POST_PCM_DHB_DHR_OP05_LANE_REF
P7_R54_AHR_POST_DHB_DHC_DHB_R11_SAFE_NEXT_WORK_CANDIDATE_REF: Final = (
    "DHR-OP05 manual call / existing DHR-OP05 preflight scan execution consideration"
)

P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_SCHEMA_VERSION_REF: Final = dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_SCHEMA_VERSION
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_STEP_REF: Final = dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_REF: Final = (
    "assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract"
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_IMPORT_PATH_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704."
    + P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_REF
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_IMPORT_CALLABLE_REF: Final[Callable[[Mapping[str, Any]], bool]] = (
    dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_ALLOWED_STATUS_REFS
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_CONFIRMED_STATUS_REF: Final = dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF

P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF: Final = (
    "build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan"
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_PATH_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704."
    + P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_CALLABLE_REF: Final[Callable[..., dict[str, Any]]] = (
    dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF: Final = (
    "assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract"
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_IMPORT_PATH_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704."
    + P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_IMPORT_CALLABLE_REF: Final[Callable[[Mapping[str, Any]], bool]] = (
    dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract
)
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCHEMA_VERSION_REF: Final = dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_SCHEMA_VERSION
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_ALLOWED_STATUS_REFS
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF: Final = dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_REPAIR_REQUIRED_STATUS_REF: Final = dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_REPAIR_REQUIRED_REF
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_WAITING_OR_INCOMPLETE_STATUS_REF: Final = dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_WAITING_OR_INCOMPLETE_REF
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_NOT_CALLED_STATUS_REF: Final = "existing_dhr_op05_not_called"
P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_CONTRACT_INVALID_STATUS_REF: Final = "existing_dhr_op05_contract_invalid"

P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_STATUS_SCOPE_REFROZEN_STOPPED",
    "DHC_STATUS_SCOPE_REPAIR_REQUIRED",
    "DHC_STATUS_SCOPE_BLOCKED_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_STATUS_DHB_OP08_DHR_HANDOFF_CLOSED_INTAKE_READY",
    "DHC_STATUS_DHB_OP08_NOT_DHR_LANE_ROUTE_PRESERVED_STOPPED",
    "DHC_STATUS_WAITING_FOR_EXPLICIT_DHB_OP08_CLOSED_MATERIAL",
    "DHC_STATUS_REPAIR_REQUIRED_FOR_DHB_OP08_INTAKE",
    "DHC_STATUS_BLOCKED_DHB_OP08_BODY_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_STATUS_DHR_OP05_BUILDER_INPUT_ELIGIBLE_EXPLICIT_OP04",
    "DHC_STATUS_WAITING_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION",
    "DHC_STATUS_DHR_OP04_CONTRACT_REPAIR_REQUIRED",
    "DHC_STATUS_DHB_ENVELOPE_ONLY_NOT_BUILDER_INPUT_STOPPED",
    "DHC_STATUS_BLOCKED_DHR_OP04_INPUT_BODY_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_STATUS_MANUAL_CALL_ALLOWED_EXPLICIT_OP04_ONLY",
    "DHC_STATUS_MANUAL_CALL_NOT_REQUESTED_STOPPED",
    "DHC_STATUS_WAITING_FOR_EXPLICIT_MANUAL_CALL_REQUEST",
    "DHC_STATUS_WAITING_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION",
    "DHC_STATUS_REPAIR_REQUIRED_FOR_MANUAL_CALL_PERMISSION_INPUTS",
    "DHC_STATUS_BLOCKED_MANUAL_CALL_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_STATUS_EXISTING_DHR_OP05_PREFLIGHT_SCAN_CALLED_BODYFREE",
    "DHC_STATUS_EXISTING_DHR_OP05_PREFLIGHT_SCAN_NOT_CALLED_STOPPED",
    "DHC_STATUS_EXISTING_DHR_OP05_PREFLIGHT_SCAN_CALL_REPAIR_REQUIRED",
    "DHC_STATUS_EXISTING_DHR_OP05_PREFLIGHT_SCAN_CALL_BLOCKED_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS: Final[tuple[str, ...]] = (
    "DHC_RESULT_SCAN_CLEAR_STOPPED",
    "DHC_RESULT_WAITING_OR_INCOMPLETE_STOPPED",
    "DHC_RESULT_REPAIR_REQUIRED_STOPPED",
    "DHC_RESULT_NOT_CALLED_STOPPED",
    "DHC_RESULT_BLOCKED_STOPPED",
)
P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_STATUS_NO_TOUCH_NO_PROMOTION_NO_AUTO_DOWNSTREAM_GUARD_PASSED",
    "DHC_STATUS_REPAIR_REQUIRED_FOR_NO_TOUCH_GUARD_INPUTS",
    "DHC_STATUS_BLOCKED_NO_TOUCH_NO_PROMOTION_NO_AUTO_DOWNSTREAM_GUARD",
)
P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_STATUS_VALIDATION_PLAN_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED",
    "DHC_STATUS_REPAIR_REQUIRED_FOR_VALIDATION_PLAN_INPUTS",
    "DHC_STATUS_BLOCKED_VALIDATION_PLAN_BODYFREE_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHC_OP08_SCAN_CLEAR_CLOSED_STOPPED",
    "DHC_OP08_WAITING_OR_INCOMPLETE_CLOSED_STOPPED",
    "DHC_OP08_REPAIR_REQUIRED_CLOSED_STOPPED",
    "DHC_OP08_NOT_CALLED_CLOSED_STOPPED",
    "DHC_OP08_NON_DHR_LANE_ROUTE_PRESERVED_STOPPED",
    "DHC_OP08_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHB_DHC_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS
    )
)

P7_R54_AHR_POST_DHB_DHC_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_POST_DHB_DHC_NO_TOUCH_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "api_db_rn_runtime_response_key_changed",
)
P7_R54_AHR_POST_DHB_DHC_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "body_free",
    "raw_input_included",
    "comment_text_body_included",
    "question_text_included",
    "reviewer_free_text_included",
    "body_full_packet_generated",
)
P7_R54_AHR_POST_DHB_DHC_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "manual_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
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
    "question_text_materialized_here",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "api_db_rn_runtime_response_key_changed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS
)
P7_R54_AHR_POST_DHB_DHC_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
)
P7_R54_AHR_POST_DHB_DHC_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_r0_r1_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
)
P7_R54_AHR_POST_DHB_DHC_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
)
P7_R54_AHR_POST_DHB_DHC_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "R1 target validation may run the DHC R0/R1 skeleton test only",
    "R1 compileall may run the new DHC helper and adjacent existing reference modules",
    "R1 does not run DHR-OP05 builder, DHR-OP05 preflight, DHR-OP06+, full backend suite, RN contract, or real-device checks",
)

P7_R54_AHR_POST_DHB_DHC_R1_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "expected_next_required_step_ref",
    "current_execution_allowance_ref",
    "builder_call_boundary_ref",
    "implicit_op04_fallback_ref",
    "implemented_step_refs",
    "not_yet_implemented_step_refs",
    "dhc_step_refs",
    "dhc_schema_version_refs",
    "local_received_zip_refs",
    "support_material_refs",
    "not_stage_refs",
    "claim_boundary_refs",
    "not_claimed_boundary_refs",
    "fixed_non_promotion_refs",
    "explicit_dhb_op08_closed_material_required",
    "dhb_op08_material_synthesis_allowed_here",
    "dhb_builder_call_allowed_here",
    "dhb_r11_memo_as_dhb_op08_allowed_here",
    "dhb_handoff_envelope_as_dhr_op04_input_allowed_here",
    "explicit_dhr_op04_actual_source_claim_separation_required",
    "existing_dhr_op04_assert_call_allowed_in_r1",
    "implicit_op04_builder_fallback_allowed_here",
    "implicit_op04_builder_fallback_used_here",
    "manual_call_requested_here",
    "manual_call_permission_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
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
    "allowed_dhb_op08_schema_version_ref",
    "allowed_dhb_op08_step_ref",
    "allowed_dhb_op08_closed_status_ref",
    "dhb_op08_allowed_status_refs",
    "dhb_op04_handoff_envelope_step_ref",
    "dhb_op05_compatibility_crosswalk_step_ref",
    "dhb_dhr_op05_lane_ref",
    "dhb_r11_safe_next_work_candidate_ref",
    "existing_dhr_op04_schema_version_ref",
    "existing_dhr_op04_step_ref",
    "existing_dhr_op04_assert_ref",
    "existing_dhr_op04_assert_import_path_ref",
    "existing_dhr_op04_assert_import_available",
    "existing_dhr_op04_allowed_status_refs",
    "existing_dhr_op04_confirmed_status_ref",
    "existing_dhr_op05_builder_ref",
    "existing_dhr_op05_builder_import_path_ref",
    "existing_dhr_op05_builder_import_available",
    "existing_dhr_op05_assert_ref",
    "existing_dhr_op05_assert_import_path_ref",
    "existing_dhr_op05_assert_import_available",
    "existing_dhr_op05_schema_version_ref",
    "existing_dhr_op05_allowed_status_refs",
    "existing_dhr_op05_scan_clear_status_ref",
    "existing_dhr_op05_repair_required_status_ref",
    "existing_dhr_op05_waiting_or_incomplete_status_ref",
    "existing_dhr_op05_not_called_status_ref",
    "existing_dhr_op05_contract_invalid_status_ref",
    "allowed_status_refs",
    "op05_result_classification_refs",
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
    *P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS,
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "next_required_step",
    "body_free",
)


def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_DHB_DHC_DEFAULT_REVIEW_SESSION_ID,
        max_length=180,
    )


def build_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary(
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Return a body-free R0/R1 constants summary without calling DHB/DHR builders."""

    safe_review_session_id = _safe_review_session_id(review_session_id)
    data: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_DHB_DHC_R1_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
        "step": P7_R54_AHR_POST_DHB_DHC_STEP,
        "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
        "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
        "material_id": "p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_20260709",
        "review_session_id": safe_review_session_id,
        "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_DHB_DHC_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_DHB_DHC_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_DHB_DHC_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_DHB_DHC_BOUNDARY_PREFIX_MEANING_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_DHB_DHC_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "current_execution_allowance_ref": P7_R54_AHR_POST_DHB_DHC_CURRENT_EXECUTION_ALLOWANCE_REF,
        "builder_call_boundary_ref": P7_R54_AHR_POST_DHB_DHC_BUILDER_CALL_BOUNDARY_REF,
        "implicit_op04_fallback_ref": P7_R54_AHR_POST_DHB_DHC_IMPLICIT_OP04_FALLBACK_REF,
        "implemented_step_refs": P7_R54_AHR_POST_DHB_DHC_R0_R1_IMPLEMENTED_STEPS,
        "not_yet_implemented_step_refs": P7_R54_AHR_POST_DHB_DHC_R0_R1_NOT_YET_IMPLEMENTED_STEPS,
        "dhc_step_refs": P7_R54_AHR_POST_DHB_DHC_STEP_REFS,
        "dhc_schema_version_refs": P7_R54_AHR_POST_DHB_DHC_SCHEMA_VERSION_REFS,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_DHB_DHC_LOCAL_RECEIVED_ZIP_REFS),
        "support_material_refs": P7_R54_AHR_POST_DHB_DHC_SUPPORT_MATERIAL_REFS,
        "not_stage_refs": P7_R54_AHR_POST_DHB_DHC_NOT_STAGE_REFS,
        "claim_boundary_refs": P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS,
        "not_claimed_boundary_refs": P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS,
        "fixed_non_promotion_refs": P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS,
        "explicit_dhb_op08_closed_material_required": P7_R54_AHR_POST_DHB_DHC_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REQUIRED,
        "dhb_op08_material_synthesis_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHB_OP08_MATERIAL_SYNTHESIS_ALLOWED_HERE,
        "dhb_builder_call_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHB_BUILDER_CALL_ALLOWED_HERE,
        "dhb_r11_memo_as_dhb_op08_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHB_R11_MEMO_AS_DHB_OP08_ALLOWED_HERE,
        "dhb_handoff_envelope_as_dhr_op04_input_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHB_HANDOFF_ENVELOPE_AS_DHR_OP04_INPUT_ALLOWED_HERE,
        "explicit_dhr_op04_actual_source_claim_separation_required": P7_R54_AHR_POST_DHB_DHC_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REQUIRED,
        "existing_dhr_op04_assert_call_allowed_in_r1": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_CALL_ALLOWED_IN_R1,
        "implicit_op04_builder_fallback_allowed_here": P7_R54_AHR_POST_DHB_DHC_IMPLICIT_OP04_BUILDER_FALLBACK_ALLOWED_HERE,
        "implicit_op04_builder_fallback_used_here": P7_R54_AHR_POST_DHB_DHC_IMPLICIT_OP04_BUILDER_FALLBACK_USED_HERE,
        "manual_call_requested_here": P7_R54_AHR_POST_DHB_DHC_MANUAL_CALL_REQUESTED_HERE,
        "manual_call_permission_allowed_here": P7_R54_AHR_POST_DHB_DHC_MANUAL_CALL_PERMISSION_ALLOWED_HERE,
        "existing_dhr_op05_builder_call_allowed_here": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_CALL_ALLOWED_HERE,
        "existing_dhr_op05_builder_called_here": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_CALLED_HERE,
        "existing_dhr_op05_result_present": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_RESULT_PRESENT_HERE,
        "existing_dhr_op05_contract_valid": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_CONTRACT_VALID_HERE,
        "dhr_op05_call_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHR_OP05_CALL_ALLOWED_HERE,
        "dhr_op05_builder_call_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHR_OP05_BUILDER_CALL_ALLOWED_HERE,
        "dhr_op06_call_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHR_OP06_CALL_ALLOWED_HERE,
        "dhr_op07_materialization_allowed_here": P7_R54_AHR_POST_DHB_DHC_DHR_OP07_MATERIALIZATION_ALLOWED_HERE,
        "dmd_r52_execution_allowed_here": P7_R54_AHR_POST_DHB_DHC_DMD_R52_EXECUTION_ALLOWED_HERE,
        "actual_review_start_allowed_here": P7_R54_AHR_POST_DHB_DHC_ACTUAL_REVIEW_START_ALLOWED_HERE,
        "actual_rows_creation_allowed_here": P7_R54_AHR_POST_DHB_DHC_ACTUAL_ROWS_CREATION_ALLOWED_HERE,
        "question_need_observation_rows_creation_allowed_here": P7_R54_AHR_POST_DHB_DHC_QUESTION_NEED_OBSERVATION_ROWS_CREATION_ALLOWED_HERE,
        "repair_execution_allowed_here": P7_R54_AHR_POST_DHB_DHC_REPAIR_EXECUTION_ALLOWED_HERE,
        "raw_evidence_request_allowed_here": P7_R54_AHR_POST_DHB_DHC_RAW_EVIDENCE_REQUEST_ALLOWED_HERE,
        "p8_question_design_allowed_here": P7_R54_AHR_POST_DHB_DHC_P8_QUESTION_DESIGN_ALLOWED_HERE,
        "p8_question_implementation_allowed_here": P7_R54_AHR_POST_DHB_DHC_P8_QUESTION_IMPLEMENTATION_ALLOWED_HERE,
        "question_text_materialization_allowed_here": P7_R54_AHR_POST_DHB_DHC_QUESTION_TEXT_MATERIALIZATION_ALLOWED_HERE,
        "api_db_rn_runtime_response_key_change_allowed_here": P7_R54_AHR_POST_DHB_DHC_API_DB_RN_RUNTIME_RESPONSE_KEY_CHANGE_ALLOWED_HERE,
        "json_schema_file_creation_allowed_here": P7_R54_AHR_POST_DHB_DHC_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE,
        "p7_complete_allowed_here": P7_R54_AHR_POST_DHB_DHC_P7_COMPLETE_ALLOWED_HERE,
        "release_decision_allowed_here": P7_R54_AHR_POST_DHB_DHC_RELEASE_DECISION_ALLOWED_HERE,
        "full_backend_suite_green_claim_allowed_here": P7_R54_AHR_POST_DHB_DHC_FULL_BACKEND_SUITE_GREEN_CLAIM_ALLOWED_HERE,
        "rn_contract_green_claim_allowed_here": P7_R54_AHR_POST_DHB_DHC_RN_CONTRACT_GREEN_CLAIM_ALLOWED_HERE,
        "rn_real_device_modal_verification_claim_allowed_here": P7_R54_AHR_POST_DHB_DHC_RN_REAL_DEVICE_MODAL_VERIFICATION_CLAIM_ALLOWED_HERE,
        "allowed_dhb_op08_schema_version_ref": P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_SCHEMA_VERSION_REF,
        "allowed_dhb_op08_step_ref": P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_STEP_REF,
        "allowed_dhb_op08_closed_status_ref": P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_CLOSED_STATUS_REF,
        "dhb_op08_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS,
        "dhb_op04_handoff_envelope_step_ref": P7_R54_AHR_POST_DHB_DHC_DHB_OP04_HANDOFF_ENVELOPE_STEP_REF,
        "dhb_op05_compatibility_crosswalk_step_ref": P7_R54_AHR_POST_DHB_DHC_DHB_OP05_COMPATIBILITY_CROSSWALK_STEP_REF,
        "dhb_dhr_op05_lane_ref": P7_R54_AHR_POST_DHB_DHC_DHB_DHR_OP05_LANE_REF,
        "dhb_r11_safe_next_work_candidate_ref": P7_R54_AHR_POST_DHB_DHC_DHB_R11_SAFE_NEXT_WORK_CANDIDATE_REF,
        "existing_dhr_op04_schema_version_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_SCHEMA_VERSION_REF,
        "existing_dhr_op04_step_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_STEP_REF,
        "existing_dhr_op04_assert_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_REF,
        "existing_dhr_op04_assert_import_path_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_IMPORT_PATH_REF,
        "existing_dhr_op04_assert_import_available": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_IMPORT_CALLABLE_REF
        is dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract,
        "existing_dhr_op04_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ALLOWED_STATUS_REFS,
        "existing_dhr_op04_confirmed_status_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_CONFIRMED_STATUS_REF,
        "existing_dhr_op05_builder_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF,
        "existing_dhr_op05_builder_import_path_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_PATH_REF,
        "existing_dhr_op05_builder_import_available": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_CALLABLE_REF
        is dhr.build_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan,
        "existing_dhr_op05_assert_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF,
        "existing_dhr_op05_assert_import_path_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_IMPORT_PATH_REF,
        "existing_dhr_op05_assert_import_available": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_IMPORT_CALLABLE_REF
        is dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract,
        "existing_dhr_op05_schema_version_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCHEMA_VERSION_REF,
        "existing_dhr_op05_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ALLOWED_STATUS_REFS,
        "existing_dhr_op05_scan_clear_status_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF,
        "existing_dhr_op05_repair_required_status_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_REPAIR_REQUIRED_STATUS_REF,
        "existing_dhr_op05_waiting_or_incomplete_status_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_WAITING_OR_INCOMPLETE_STATUS_REF,
        "existing_dhr_op05_not_called_status_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_NOT_CALLED_STATUS_REF,
        "existing_dhr_op05_contract_invalid_status_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_CONTRACT_INVALID_STATUS_REF,
        "allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_ALLOWED_STATUS_REFS,
        "op05_result_classification_refs": P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS,
        "forbidden_payload_key_refs": P7_R54_AHR_POST_DHB_DHC_FORBIDDEN_PAYLOAD_KEY_REFS,
        "no_touch_contract_keys": P7_R54_AHR_POST_DHB_DHC_NO_TOUCH_CONTRACT_KEYS,
        "body_free_marker_refs": P7_R54_AHR_POST_DHB_DHC_BODY_FREE_MARKER_REFS,
        "promotion_claim_field_refs": P7_R54_AHR_POST_DHB_DHC_PROMOTION_CLAIM_FIELD_REFS,
        "required_false_flag_refs": P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS,
        "target_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_TARGET_TEST_REF_REFS,
        "selected_regression_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_SELECTED_REGRESSION_TEST_REF_REFS,
        "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_COMPILEALL_TARGET_REF_REFS,
        "validation_command_summary_refs": P7_R54_AHR_POST_DHB_DHC_VALIDATION_COMMAND_SUMMARY_REFS,
        "public_contract": public_contract_flags(),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "next_required_step": P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
        "body_free": True,
    }
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS:
        data[key] = False
    return data


def assert_p7_r54_ahr_post_dhb_dhc_r1_helper_skeleton_constants_summary_contract(
    data: Mapping[str, Any],
) -> bool:
    """Validate the DHC R0/R1 constants summary without validating future OP00+ output."""

    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_R1_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_R1_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 schema version mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 operation step mismatch")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must remain body-free")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not require/check GitHub")
    if tuple(data.get("implemented_step_refs", ())) != P7_R54_AHR_POST_DHB_DHC_R0_R1_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_step_refs", ())) != P7_R54_AHR_POST_DHB_DHC_R0_R1_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must leave DHC-OP00..OP08 not yet implemented")
    if tuple(data.get("dhc_step_refs", ())) != P7_R54_AHR_POST_DHB_DHC_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHC step refs mismatch")
    if tuple(data.get("dhc_schema_version_refs", ())) != P7_R54_AHR_POST_DHB_DHC_SCHEMA_VERSION_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 schema version refs mismatch")
    if data.get("boundary_prefix_ref") != P7_R54_AHR_POST_DHB_DHC_BOUNDARY_PREFIX_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 boundary prefix mismatch")
    if data.get("explicit_dhb_op08_closed_material_required") is not True:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must require explicit future DHB-OP08 material")
    if data.get("dhb_op08_material_synthesis_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not allow DHB-OP08 material synthesis")
    if data.get("dhb_builder_call_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not allow DHB builder calls")
    if data.get("dhb_r11_memo_as_dhb_op08_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not allow DHB R11 memo as DHB-OP08 material")
    if data.get("dhb_handoff_envelope_as_dhr_op04_input_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not allow DHB envelope as DHR-OP04 input")
    if data.get("explicit_dhr_op04_actual_source_claim_separation_required") is not True:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must require explicit DHR-OP04 actual source claim separation")
    if data.get("existing_dhr_op04_assert_call_allowed_in_r1") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not call DHR-OP04 assert in R1")
    if data.get("implicit_op04_builder_fallback_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not allow implicit OP04 builder fallback")
    if data.get("manual_call_permission_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not allow manual call permission")
    if data.get("existing_dhr_op05_builder_call_allowed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not allow existing DHR-OP05 builder call")
    if data.get("existing_dhr_op05_builder_called_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not call existing DHR-OP05 builder")
    if data.get("existing_dhr_op05_result_present") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not produce DHR-OP05 result")
    for key in (
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
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
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHB-DHC-R1 allowed flag must remain false: {key}")
    if data.get("allowed_dhb_op08_schema_version_ref") != P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHB-OP08 schema ref mismatch")
    if data.get("allowed_dhb_op08_step_ref") != P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHB-OP08 step ref mismatch")
    if data.get("allowed_dhb_op08_closed_status_ref") != P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_CLOSED_STATUS_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHB-OP08 closed status ref mismatch")
    if tuple(data.get("dhb_op08_allowed_status_refs", ())) != P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHB-OP08 allowed status refs mismatch")
    if data.get("existing_dhr_op04_schema_version_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHR-OP04 schema ref mismatch")
    if data.get("existing_dhr_op04_step_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHR-OP04 step ref mismatch")
    if data.get("existing_dhr_op04_assert_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHR-OP04 assert ref mismatch")
    if data.get("existing_dhr_op04_assert_import_available") is not True:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHR-OP04 assert import unavailable")
    if tuple(data.get("existing_dhr_op04_allowed_status_refs", ())) != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 DHR-OP04 allowed status refs mismatch")
    if data.get("existing_dhr_op05_builder_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 existing DHR-OP05 builder ref mismatch")
    if data.get("existing_dhr_op05_builder_import_available") is not True:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 existing DHR-OP05 builder import unavailable")
    if data.get("existing_dhr_op05_assert_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 existing DHR-OP05 assert ref mismatch")
    if data.get("existing_dhr_op05_assert_import_available") is not True:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 existing DHR-OP05 assert import unavailable")
    if data.get("existing_dhr_op05_schema_version_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 existing DHR-OP05 schema ref mismatch")
    if tuple(data.get("existing_dhr_op05_allowed_status_refs", ())) != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 existing DHR-OP05 allowed status refs mismatch")
    if tuple(data.get("allowed_status_refs", ())) != P7_R54_AHR_POST_DHB_DHC_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 allowed status refs mismatch")
    if tuple(data.get("op05_result_classification_refs", ())) != P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 OP05 classification refs mismatch")
    if tuple(data.get("forbidden_payload_key_refs", ())) != P7_R54_AHR_POST_DHB_DHC_FORBIDDEN_PAYLOAD_KEY_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 forbidden payload refs mismatch")
    if tuple(data.get("no_touch_contract_keys", ())) != P7_R54_AHR_POST_DHB_DHC_NO_TOUCH_CONTRACT_KEYS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 no-touch keys mismatch")
    if tuple(data.get("promotion_claim_field_refs", ())) != P7_R54_AHR_POST_DHB_DHC_PROMOTION_CLAIM_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 promotion claim refs mismatch")
    if tuple(data.get("target_test_ref_refs", ())) != P7_R54_AHR_POST_DHB_DHC_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 target test refs mismatch")
    if tuple(data.get("compileall_target_ref_refs", ())) != P7_R54_AHR_POST_DHB_DHC_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 compileall target refs mismatch")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 public contract changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 next step must be DHC-OP00")
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHB-DHC-R1 forbidden flag must remain false: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_NO_TOUCH_CONTRACT_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHB-DHC-R1 no-touch key must remain false: {key}")
    if data.get("full_backend_suite_green_confirmed") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not claim full backend suite green")
    if data.get("rn_contract_green_confirmed") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not claim RN contract green")
    if data.get("rn_real_device_modal_verified_claimed_here") is not False:
        raise ValueError("P7-R54-AHR-PostDHB-DHC-R1 must not claim RN real-device modal verification")
    return True


# ---------------------------------------------------------------------------
# R2: DHC-OP00 / DHC-OP01 only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHB_DHC_R2_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op00_op01_20260709.py",
)
P7_R54_AHR_POST_DHB_DHC_R2_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REF: Final = (
    "wait_for_explicit_DHB_OP08_closed_material_without_DHB_synthesis_or_DHR_OP05_call"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF: Final = (
    "repair_explicit_DHB_OP08_intake_material_without_DHR_OP05_promotion"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF: Final = (
    "blocked_DHB_OP08_intake_body_leak_promotion_or_autorun_without_DHR_OP05_call"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_PRESERVE_NON_DHR_LANE_ROUTE_REF: Final = (
    "preserve_non_DHR_OP05_lane_route_from_DHB_without_DHR_OP05_call"
)

P7_R54_AHR_POST_DHB_DHC_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP00_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS if key != "dhc_op00_implemented"
)
P7_R54_AHR_POST_DHB_DHC_OP01_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key not in {"dhc_op00_implemented", "dhc_op01_implemented"}
)
P7_R54_AHR_POST_DHB_DHC_OP00_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "current_execution_allowance_ref",
    "dhc_op00_status_ref",
    "dhc_op00_allowed_status_refs",
    "dhc_op00_allowed_status_ref_count",
    "dhc_op00_scope_confirmed",
    "dhc_op00_repair_required",
    "dhc_op00_bodyfree_leak_promotion_or_autorun_blocked",
    "dhb_closure_is_not_dhr_op05_execution",
    "dhb_closure_is_not_p8_start",
    "dhb_target_green_is_not_release_readiness",
    "explicit_dhb_op08_closed_material_required",
    "dhb_op08_material_synthesis_allowed_here",
    "dhb_builder_call_allowed_here",
    "dhb_r11_memo_as_dhb_op08_allowed_here",
    "dhb_handoff_envelope_as_dhr_op04_input_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
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
    "dhc_op00_does_not_intake_dhb_op08_material",
    "dhc_op00_does_not_synthesize_dhb_op08_material",
    "dhc_op00_does_not_call_dhb_builder",
    "dhc_op00_does_not_call_dhr_op05",
    "dhc_op00_does_not_call_existing_dhr_op05_builder",
    "dhc_op00_does_not_call_dhr_op06",
    "dhc_op00_does_not_start_p8_question_design",
    "dhc_op00_does_not_change_api_db_rn_runtime_response_key",
    "dhc_op00_does_not_create_json_schema_file",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "target_test_ref_refs",
    "compileall_target_ref_refs",
    "public_contract",
    "dhc_no_touch_contract",
    "body_free_markers",
    "dhc_op00_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP01_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op00_material_present",
    "op00_contract_valid",
    "op00_schema_version",
    "op00_material_ref",
    "op00_next_required_step",
    "explicit_dhb_op08_closed_material_required",
    "dhb_op08_material_synthesis_allowed_here",
    "dhb_builder_call_allowed_here",
    "dhb_r11_memo_as_dhb_op08_allowed_here",
    "dhb_handoff_envelope_as_dhr_op04_input_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "dhr_op05_call_allowed_here",
    "dhr_op05_builder_call_allowed_here",
    "dhr_op06_call_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
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
    "dhb_op08_material_synthesized_here",
    "dhb_builder_called_here",
    "dhb_r11_memo_used_as_dhb_op08_here",
    "dhb_op08_material_present",
    "dhb_op08_shaped_material_valid",
    "dhb_op08_schema_version",
    "dhb_op08_material_ref",
    "dhb_op08_operation_step_ref",
    "dhb_op08_status_ref",
    "bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref",
    "dhb_op08_body_free",
    "dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped",
    "dhb_op08_not_dhr_op05_lane_route_preserved_stopped",
    "dhr_op05_manual_handoff_envelope_ready_upstream",
    "dhr_op05_manual_handoff_envelope_created_here",
    "dhr_op05_call_still_requires_separate_explicit_instruction",
    "dhr_lane_closed_intake_ready",
    "non_dhr_lane_route_preserved",
    "dhr_op05_lane_confirmed_from_explicit_dhb_op08",
    "dhr_op05_not_called_in_dhb_op08",
    "existing_dhr_op05_builder_not_called_in_dhb_op08",
    "dhb_op08_input_forbidden_payload_key_path_refs",
    "dhb_op08_input_forbidden_payload_key_path_count",
    "dhb_op08_input_body_like_value_path_refs",
    "dhb_op08_input_body_like_value_path_count",
    "dhb_op08_input_promotion_claim_refs",
    "dhb_op08_input_promotion_claim_ref_count",
    "dhb_op08_input_no_touch_mutation_path_refs",
    "dhb_op08_input_no_touch_mutation_path_count",
    "dhc_op01_status_ref",
    "bodyfree_dhb_op08_closed_handoff_material_intake_status_ref",
    "dhc_op01_allowed_status_refs",
    "dhc_op01_allowed_status_ref_count",
    "dhc_op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check",
    "dhc_op01_non_dhr_lane_route_preserved_stopped",
    "dhc_op01_waiting_for_explicit_dhb_op08_closed_material",
    "dhc_op01_repair_required",
    "dhc_op01_bodyfree_leak_promotion_or_autorun_blocked",
    "dhc_op01_reason_refs",
    "dhc_op01_reason_ref_count",
    "dhc_op01_blocker_refs",
    "dhc_op01_blocker_ref_count",
    "dhc_op01_does_not_validate_dhr_op04_material",
    "dhc_op01_does_not_call_dhr_op04_assert",
    "dhc_op01_does_not_call_dhr_op05",
    "dhc_op01_does_not_call_existing_dhr_op05_builder",
    "dhc_op01_does_not_call_dhr_op06",
    "dhc_op01_does_not_execute_dmd_r52_or_release",
    "dhc_op01_does_not_start_actual_review",
    "dhc_op01_does_not_create_actual_rows",
    "dhc_op01_does_not_create_question_need_observation_rows",
    "dhc_op01_does_not_start_p8_question_design",
    "dhc_op01_does_not_change_api_db_rn_runtime_response_key",
    "dhc_op01_does_not_materialize_question_text",
    "dhc_op01_does_not_create_json_schema_file",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "target_test_ref_refs",
    "compileall_target_ref_refs",
    "public_contract",
    "dhc_no_touch_contract",
    "body_free_markers",
    "dhc_op00_implemented",
    "dhc_op01_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP00_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP00_REQUIRED_FALSE_FLAG_REFS)
)
P7_R54_AHR_POST_DHB_DHC_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP01_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP01_REQUIRED_FALSE_FLAG_REFS)
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


def _false_flags(refs: Sequence[str]) -> dict[str, bool]:
    return {key: False for key in refs}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHB_DHC_NO_TOUCH_CONTRACT_KEYS}


def _body_free_markers() -> dict[str, bool]:
    markers = {key: False for key in P7_R54_AHR_POST_DHB_DHC_BODY_FREE_MARKER_REFS}
    markers["body_free"] = True
    return markers


def _required_fields_present(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:8]}")


def _scan_forbidden_payload_key_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_DHB_DHC_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_body_like_value_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_DHB_DHC_FORBIDDEN_PAYLOAD_KEY_REFS and child not in (None, "", False):
                paths.append(child_path)
            paths.extend(_scan_body_like_value_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_body_like_value_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_promotion_claim_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_DHB_DHC_PROMOTION_CLAIM_FIELD_REFS and child is True:
                paths.append(child_path)
            paths.extend(_scan_promotion_claim_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_promotion_claim_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_no_touch_mutation_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_DHB_DHC_NO_TOUCH_CONTRACT_KEYS and child is True:
                paths.append(child_path)
            paths.extend(_scan_no_touch_mutation_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_no_touch_mutation_paths(child, path=f"{path}[{index}]"))
    return paths


def _counted_refs(refs: Sequence[Any]) -> tuple[list[str], int]:
    cleaned = _dedupe_clean_refs(refs, max_length=360)
    return cleaned, len(cleaned)


def _op00_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11_contract(data)
    except ValueError:
        return False
    return True


def build_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11(
    *, review_session_id: str | None = None
) -> dict[str, Any]:
    """Build DHC-OP00 scope refreeze material without intaking DHB-OP08 or calling builders."""

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP00_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP00_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11_20260709",
            "review_session_id": _safe_review_session_id(review_session_id),
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "selected_stage_ref": P7_R54_AHR_POST_DHB_DHC_SELECTED_STAGE_REF,
            "selected_design_target_ref": P7_R54_AHR_POST_DHB_DHC_SELECTED_DESIGN_TARGET_REF,
            "boundary_prefix_ref": P7_R54_AHR_POST_DHB_DHC_BOUNDARY_PREFIX_REF,
            "boundary_prefix_meaning_ref": P7_R54_AHR_POST_DHB_DHC_BOUNDARY_PREFIX_MEANING_REF,
            "current_execution_allowance_ref": P7_R54_AHR_POST_DHB_DHC_CURRENT_EXECUTION_ALLOWANCE_REF,
            "dhc_op00_status_ref": P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS[0],
            "dhc_op00_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS,
            "dhc_op00_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS),
            "dhc_op00_scope_confirmed": True,
            "dhc_op00_repair_required": False,
            "dhc_op00_bodyfree_leak_promotion_or_autorun_blocked": False,
            "dhb_closure_is_not_dhr_op05_execution": True,
            "dhb_closure_is_not_p8_start": True,
            "dhb_target_green_is_not_release_readiness": True,
            "explicit_dhb_op08_closed_material_required": True,
            "dhb_op08_material_synthesis_allowed_here": False,
            "dhb_builder_call_allowed_here": False,
            "dhb_r11_memo_as_dhb_op08_allowed_here": False,
            "dhb_handoff_envelope_as_dhr_op04_input_allowed_here": False,
            "existing_dhr_op05_builder_call_allowed_here": False,
            "existing_dhr_op05_builder_called_here": False,
            "dhr_op05_call_allowed_here": False,
            "dhr_op05_builder_call_allowed_here": False,
            "dhr_op06_call_allowed_here": False,
            "dhr_op07_materialization_allowed_here": False,
            "dmd_r52_execution_allowed_here": False,
            "actual_review_start_allowed_here": False,
            "actual_rows_creation_allowed_here": False,
            "question_need_observation_rows_creation_allowed_here": False,
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
            "dhc_op00_does_not_intake_dhb_op08_material": True,
            "dhc_op00_does_not_synthesize_dhb_op08_material": True,
            "dhc_op00_does_not_call_dhb_builder": True,
            "dhc_op00_does_not_call_dhr_op05": True,
            "dhc_op00_does_not_call_existing_dhr_op05_builder": True,
            "dhc_op00_does_not_call_dhr_op06": True,
            "dhc_op00_does_not_start_p8_question_design": True,
            "dhc_op00_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op00_does_not_create_json_schema_file": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP00_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP00_NOT_YET_IMPLEMENTED_STEPS),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R2_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R2_COMPILEALL_TARGET_REF_REFS),
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "next_required_step": P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op00_scope_no_execution_refreeze_after_dhb_r11_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DHC-OP00 scope refreeze contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP00_REQUIRED_FIELD_REFS, source="DHC-OP00")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP00 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP00_SCHEMA_VERSION:
        raise ValueError("DHC-OP00 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF:
        raise ValueError("DHC-OP00 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP00 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP00 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP00 must remain body-free")
    for key in (
        "dhc_op00_scope_confirmed",
        "dhb_closure_is_not_dhr_op05_execution",
        "dhb_closure_is_not_p8_start",
        "dhb_target_green_is_not_release_readiness",
        "explicit_dhb_op08_closed_material_required",
        "dhc_op00_does_not_intake_dhb_op08_material",
        "dhc_op00_does_not_synthesize_dhb_op08_material",
        "dhc_op00_does_not_call_dhb_builder",
        "dhc_op00_does_not_call_dhr_op05",
        "dhc_op00_does_not_call_existing_dhr_op05_builder",
        "dhc_op00_does_not_call_dhr_op06",
        "dhc_op00_does_not_start_p8_question_design",
        "dhc_op00_does_not_change_api_db_rn_runtime_response_key",
        "dhc_op00_does_not_create_json_schema_file",
        "dhc_op00_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP00 required true field changed: {key}")
    for key in (
        "dhc_op00_repair_required",
        "dhc_op00_bodyfree_leak_promotion_or_autorun_blocked",
        "dhb_op08_material_synthesis_allowed_here",
        "dhb_builder_call_allowed_here",
        "dhb_r11_memo_as_dhb_op08_allowed_here",
        "dhb_handoff_envelope_as_dhr_op04_input_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
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
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP00 forbidden field changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP00_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP00 required false flag changed: {key}")
    if tuple(data.get("dhc_op00_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP00 allowed status refs changed")
    if data.get("dhc_op00_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS):
        raise ValueError("DHC-OP00 allowed status count changed")
    if data.get("dhc_op00_status_ref") != P7_R54_AHR_POST_DHB_DHC_OP00_ALLOWED_STATUS_REFS[0]:
        raise ValueError("DHC-OP00 status must be scope refrozen")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP00_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP00 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R2_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP00 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R2_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP00 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP00 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP00 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP00 body-free marker changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF:
        raise ValueError("DHC-OP00 next step must be DHC-OP01")
    for field, count_field in (
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP00 count field changed: {count_field}")
    return True


def _dhc_op01_status(
    *,
    op00_valid: bool,
    material_present: bool,
    shaped_valid: bool,
    closed_dhr_lane: bool,
    non_dhr_lane: bool,
    upstream_waiting: bool,
    upstream_repair: bool,
    upstream_blocked: bool,
    scan_blocked: bool,
) -> tuple[str, list[str], list[str], str]:
    if scan_blocked or upstream_blocked:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[4],
            ["explicit_DHB_OP08_material_contains_or_reports_bodyfree_leak_promotion_or_autorun"],
            ["stop_before_DHR_OP05_call_and_repair_bodyfree_boundary"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF,
        )
    if not material_present:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[2],
            ["waiting_for_explicit_DHB_OP08_closed_material"],
            [],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REF,
        )
    if not op00_valid or not shaped_valid:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[3],
            ["explicit_DHB_OP08_material_or_OP00_scope_refreeze_invalid"],
            ["repair_DHC_OP01_inputs_without_DHR_OP05_call"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF,
        )
    if upstream_waiting:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[2],
            ["explicit_DHB_OP08_material_is_waiting_not_closed"],
            [],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REF,
        )
    if upstream_repair:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[3],
            ["explicit_DHB_OP08_material_reports_repair_required"],
            ["repair_DHB_OP08_closure_material_before_DHR_OP05_call"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF,
        )
    if non_dhr_lane:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[1],
            ["explicit_DHB_OP08_material_preserves_non_DHR_OP05_lane_route"],
            [],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_PRESERVE_NON_DHR_LANE_ROUTE_REF,
        )
    if closed_dhr_lane:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[0],
            ["explicit_DHB_OP08_DHR_OP05_manual_handoff_boundary_closed_without_call"],
            [],
            P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[3],
        ["explicit_DHB_OP08_status_not_usable_for_DHC_OP02"],
        ["repair_or_preserve_route_without_DHR_OP05_call"],
        P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF,
    )


def build_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake(
    op00_scope_refreeze: Mapping[str, Any] | None = None,
    explicit_dhb_op08_bodyfree_closure_material: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Intake explicit DHB-OP08 closure material without synthesizing DHB or calling builders."""

    op00 = op00_scope_refreeze
    op00_present = isinstance(op00, Mapping)
    op00_valid = _op00_valid(op00)
    material = explicit_dhb_op08_bodyfree_closure_material
    material_present = isinstance(material, Mapping)
    forbidden_paths = _scan_forbidden_payload_key_paths(material, path="explicit_dhb_op08") if material_present else []
    body_like_paths = _scan_body_like_value_paths(material, path="explicit_dhb_op08") if material_present else []
    promotion_paths = _scan_promotion_claim_paths(material, path="explicit_dhb_op08") if material_present else []
    no_touch_paths = _scan_no_touch_mutation_paths(material, path="explicit_dhb_op08") if material_present else []
    scan_blocked = bool(forbidden_paths or body_like_paths or promotion_paths or no_touch_paths)
    dhb_schema = _clean_ref(material.get("schema_version") if material_present else None, default="dhb_op08_schema_missing", max_length=320)
    dhb_step = _clean_ref(material.get("operation_step_ref") if material_present else None, default="dhb_op08_step_missing", max_length=320)
    dhb_material_ref = _clean_ref(material.get("material_id") if material_present else None, default="dhb_op08_material_missing", max_length=320)
    dhb_status = _clean_ref(material.get("dhb_op08_status_ref") if material_present else None, default="dhb_op08_status_missing", max_length=320)
    dhb_status_alias = _clean_ref(
        material.get("bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref") if material_present else None,
        default=dhb_status,
        max_length=320,
    )
    no_execution_flags_ok = bool(
        material_present
        and material.get("git_checked") is False
        and material.get("git_connection_required") is False
        and material.get("dhr_op05_called_here") is False
        and material.get("existing_dhr_op05_builder_called_here") is False
        and material.get("dhr_op06_called_here") is False
        and material.get("p8_question_design_started") is False
        and material.get("release_allowed") is False
    )
    shaped_valid = bool(
        material_present
        and dhb_schema == P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_SCHEMA_VERSION_REF
        and dhb_step == P7_R54_AHR_POST_DHB_DHC_ALLOWED_DHB_OP08_STEP_REF
        and material.get("body_free") is True
        and dhb_status == dhb_status_alias
        and dhb_status in P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS
        and no_execution_flags_ok
    )
    closed_dhr_lane = bool(
        shaped_valid
        and dhb_status == P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS[0]
        and material.get("dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped") is True
        and material.get("dhr_op05_manual_handoff_envelope_ready") is True
        and material.get("dhr_op05_call_still_requires_separate_explicit_instruction") is True
    )
    non_dhr_lane = bool(
        shaped_valid
        and dhb_status == P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS[1]
        and material.get("dhb_op08_not_dhr_op05_lane_route_preserved_stopped") is True
        and material.get("non_dhr_lane_route_preserved") is True
    )
    upstream_waiting = bool(shaped_valid and dhb_status == P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS[2])
    upstream_repair = bool(shaped_valid and dhb_status == P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS[3])
    upstream_blocked = bool(shaped_valid and dhb_status == P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS[4])
    status_ref, reasons, blockers, next_required_step = _dhc_op01_status(
        op00_valid=op00_valid,
        material_present=material_present,
        shaped_valid=shaped_valid,
        closed_dhr_lane=closed_dhr_lane,
        non_dhr_lane=non_dhr_lane,
        upstream_waiting=upstream_waiting,
        upstream_repair=upstream_repair,
        upstream_blocked=upstream_blocked,
        scan_blocked=scan_blocked,
    )
    ready = status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[0]
    route_preserved = status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[1]
    waiting = status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[2]
    repair = status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[3]
    blocked = status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[4]
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers)
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP01_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP01_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_20260709",
            "review_session_id": _safe_review_session_id(review_session_id or (op00.get("review_session_id") if op00_present else None)),
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op00_material_present": op00_present,
            "op00_contract_valid": op00_valid,
            "op00_schema_version": _clean_ref(op00.get("schema_version") if op00_present else None, default="op00_schema_missing", max_length=320),
            "op00_material_ref": _clean_ref(op00.get("material_id") if op00_present else None, default="op00_material_missing", max_length=320),
            "op00_next_required_step": _clean_ref(op00.get("next_required_step") if op00_present else None, default="op00_next_step_missing", max_length=320),
            "explicit_dhb_op08_closed_material_required": True,
            "dhb_op08_material_synthesis_allowed_here": False,
            "dhb_builder_call_allowed_here": False,
            "dhb_r11_memo_as_dhb_op08_allowed_here": False,
            "dhb_handoff_envelope_as_dhr_op04_input_allowed_here": False,
            "existing_dhr_op05_builder_call_allowed_here": False,
            "dhr_op05_call_allowed_here": False,
            "dhr_op05_builder_call_allowed_here": False,
            "dhr_op06_call_allowed_here": False,
            "dhr_op07_materialization_allowed_here": False,
            "dmd_r52_execution_allowed_here": False,
            "actual_review_start_allowed_here": False,
            "actual_rows_creation_allowed_here": False,
            "question_need_observation_rows_creation_allowed_here": False,
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
            "dhb_op08_material_synthesized_here": False,
            "dhb_builder_called_here": False,
            "dhb_r11_memo_used_as_dhb_op08_here": False,
            "dhb_op08_material_present": material_present,
            "dhb_op08_shaped_material_valid": shaped_valid,
            "dhb_op08_schema_version": dhb_schema,
            "dhb_op08_material_ref": dhb_material_ref,
            "dhb_op08_operation_step_ref": dhb_step,
            "dhb_op08_status_ref": dhb_status,
            "bodyfree_dhr_op05_manual_handoff_boundary_closure_status_ref": dhb_status_alias,
            "dhb_op08_body_free": bool(material_present and material.get("body_free") is True),
            "dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped": bool(material_present and material.get("dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped") is True),
            "dhb_op08_not_dhr_op05_lane_route_preserved_stopped": bool(material_present and material.get("dhb_op08_not_dhr_op05_lane_route_preserved_stopped") is True),
            "dhr_op05_manual_handoff_envelope_ready_upstream": bool(material_present and material.get("dhr_op05_manual_handoff_envelope_ready") is True),
            "dhr_op05_manual_handoff_envelope_created_here": False,
            "dhr_op05_call_still_requires_separate_explicit_instruction": bool(material_present and material.get("dhr_op05_call_still_requires_separate_explicit_instruction") is True),
            "dhr_lane_closed_intake_ready": ready,
            "non_dhr_lane_route_preserved": route_preserved,
            "dhr_op05_lane_confirmed_from_explicit_dhb_op08": ready,
            "dhr_op05_not_called_in_dhb_op08": bool(material_present and material.get("dhr_op05_called_here") is False),
            "existing_dhr_op05_builder_not_called_in_dhb_op08": bool(material_present and material.get("existing_dhr_op05_builder_called_here") is False),
            "dhb_op08_input_forbidden_payload_key_path_refs": forbidden_paths,
            "dhb_op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "dhb_op08_input_body_like_value_path_refs": body_like_paths,
            "dhb_op08_input_body_like_value_path_count": len(body_like_paths),
            "dhb_op08_input_promotion_claim_refs": promotion_paths,
            "dhb_op08_input_promotion_claim_ref_count": len(promotion_paths),
            "dhb_op08_input_no_touch_mutation_path_refs": no_touch_paths,
            "dhb_op08_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhc_op01_status_ref": status_ref,
            "bodyfree_dhb_op08_closed_handoff_material_intake_status_ref": status_ref,
            "dhc_op01_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS,
            "dhc_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS),
            "dhc_op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check": ready,
            "dhc_op01_non_dhr_lane_route_preserved_stopped": route_preserved,
            "dhc_op01_waiting_for_explicit_dhb_op08_closed_material": waiting,
            "dhc_op01_repair_required": repair,
            "dhc_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
            "dhc_op01_reason_refs": reason_refs,
            "dhc_op01_reason_ref_count": reason_count,
            "dhc_op01_blocker_refs": blocker_refs,
            "dhc_op01_blocker_ref_count": blocker_count,
            "dhc_op01_does_not_validate_dhr_op04_material": True,
            "dhc_op01_does_not_call_dhr_op04_assert": True,
            "dhc_op01_does_not_call_dhr_op05": True,
            "dhc_op01_does_not_call_existing_dhr_op05_builder": True,
            "dhc_op01_does_not_call_dhr_op06": True,
            "dhc_op01_does_not_execute_dmd_r52_or_release": True,
            "dhc_op01_does_not_start_actual_review": True,
            "dhc_op01_does_not_create_actual_rows": True,
            "dhc_op01_does_not_create_question_need_observation_rows": True,
            "dhc_op01_does_not_start_p8_question_design": True,
            "dhc_op01_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op01_does_not_materialize_question_text": True,
            "dhc_op01_does_not_create_json_schema_file": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP01_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP01_NOT_YET_IMPLEMENTED_STEPS),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R2_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R2_COMPILEALL_TARGET_REF_REFS),
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "dhc_op01_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DHC-OP01 explicit DHB-OP08 intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP01_REQUIRED_FIELD_REFS, source="DHC-OP01")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP01 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP01_SCHEMA_VERSION:
        raise ValueError("DHC-OP01 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF:
        raise ValueError("DHC-OP01 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP01 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP01 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP01 must remain body-free")
    for key in (
        "explicit_dhb_op08_closed_material_required",
        "dhc_op01_does_not_validate_dhr_op04_material",
        "dhc_op01_does_not_call_dhr_op04_assert",
        "dhc_op01_does_not_call_dhr_op05",
        "dhc_op01_does_not_call_existing_dhr_op05_builder",
        "dhc_op01_does_not_call_dhr_op06",
        "dhc_op01_does_not_execute_dmd_r52_or_release",
        "dhc_op01_does_not_start_actual_review",
        "dhc_op01_does_not_create_actual_rows",
        "dhc_op01_does_not_create_question_need_observation_rows",
        "dhc_op01_does_not_start_p8_question_design",
        "dhc_op01_does_not_change_api_db_rn_runtime_response_key",
        "dhc_op01_does_not_materialize_question_text",
        "dhc_op01_does_not_create_json_schema_file",
        "dhc_op00_implemented",
        "dhc_op01_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP01 required true field changed: {key}")
    for key in (
        "dhb_op08_material_synthesis_allowed_here",
        "dhb_builder_call_allowed_here",
        "dhb_r11_memo_as_dhb_op08_allowed_here",
        "dhb_handoff_envelope_as_dhr_op04_input_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
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
        "dhb_op08_material_synthesized_here",
        "dhb_builder_called_here",
        "dhb_r11_memo_used_as_dhb_op08_here",
        "dhr_op05_manual_handoff_envelope_created_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP01 forbidden claim changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP01_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP01 required false flag changed: {key}")
    if tuple(data.get("dhc_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP01 allowed status refs changed")
    if data.get("dhc_op01_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS):
        raise ValueError("DHC-OP01 allowed status count changed")
    if data.get("bodyfree_dhb_op08_closed_handoff_material_intake_status_ref") != data.get("dhc_op01_status_ref"):
        raise ValueError("DHC-OP01 status alias changed")
    for field, count_field in (
        ("dhb_op08_input_forbidden_payload_key_path_refs", "dhb_op08_input_forbidden_payload_key_path_count"),
        ("dhb_op08_input_body_like_value_path_refs", "dhb_op08_input_body_like_value_path_count"),
        ("dhb_op08_input_promotion_claim_refs", "dhb_op08_input_promotion_claim_ref_count"),
        ("dhb_op08_input_no_touch_mutation_path_refs", "dhb_op08_input_no_touch_mutation_path_count"),
        ("dhc_op01_reason_refs", "dhc_op01_reason_ref_count"),
        ("dhc_op01_blocker_refs", "dhc_op01_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP01 count field changed: {count_field}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP01_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP01 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R2_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP01 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R2_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP01 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP01 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP01 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP01 body-free marker changed")
    status_ref = data.get("dhc_op01_status_ref")
    flags = [
        data.get("dhc_op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check") is True,
        data.get("dhc_op01_non_dhr_lane_route_preserved_stopped") is True,
        data.get("dhc_op01_waiting_for_explicit_dhb_op08_closed_material") is True,
        data.get("dhc_op01_repair_required") is True,
        data.get("dhc_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("DHC-OP01 must select exactly one branch")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF:
            raise ValueError("DHC-OP01 ready next step changed")
        for key in (
            "op00_contract_valid",
            "dhb_op08_material_present",
            "dhb_op08_shaped_material_valid",
            "dhb_op08_body_free",
            "dhb_op08_dhr_op05_manual_handoff_boundary_closed_stopped",
            "dhr_op05_manual_handoff_envelope_ready_upstream",
            "dhr_op05_call_still_requires_separate_explicit_instruction",
            "dhr_lane_closed_intake_ready",
            "dhr_op05_lane_confirmed_from_explicit_dhb_op08",
            "dhr_op05_not_called_in_dhb_op08",
            "existing_dhr_op05_builder_not_called_in_dhb_op08",
        ):
            if data.get(key) is not True:
                raise ValueError(f"DHC-OP01 ready true field missing: {key}")
        for field in (
            "dhb_op08_input_forbidden_payload_key_path_refs",
            "dhb_op08_input_body_like_value_path_refs",
            "dhb_op08_input_promotion_claim_refs",
            "dhb_op08_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError(f"DHC-OP01 ready scan refs must be empty: {field}")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_PRESERVE_NON_DHR_LANE_ROUTE_REF:
            raise ValueError("DHC-OP01 non-DHR next step changed")
        for key in (
            "op00_contract_valid",
            "dhb_op08_material_present",
            "dhb_op08_shaped_material_valid",
            "dhb_op08_not_dhr_op05_lane_route_preserved_stopped",
            "non_dhr_lane_route_preserved",
        ):
            if data.get(key) is not True:
                raise ValueError(f"DHC-OP01 non-DHR true field missing: {key}")
        if data.get("dhr_lane_closed_intake_ready") is not False:
            raise ValueError("DHC-OP01 non-DHR must not be DHR ready")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHB_OP08_CLOSED_MATERIAL_REF:
            raise ValueError("DHC-OP01 waiting next step changed")
        if data.get("dhb_op08_material_present") is not False and data.get("dhb_op08_status_ref") != P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS[2]:
            raise ValueError("DHC-OP01 waiting branch must be missing material or upstream waiting material")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF:
            raise ValueError("DHC-OP01 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[4]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHB_OP08_INTAKE_REF:
            raise ValueError("DHC-OP01 blocked next step changed")
        if not (
            data.get("dhb_op08_status_ref") == P7_R54_AHR_POST_DHB_DHC_DHB_OP08_ALLOWED_STATUS_REFS[4]
            or data.get("dhb_op08_input_forbidden_payload_key_path_refs")
            or data.get("dhb_op08_input_body_like_value_path_refs")
            or data.get("dhb_op08_input_promotion_claim_refs")
            or data.get("dhb_op08_input_no_touch_mutation_path_refs")
        ):
            raise ValueError("DHC-OP01 blocked branch must record scan refs or upstream blocked status")
    return True



# ---------------------------------------------------------------------------
# R3: DHC-OP02 / DHC-OP03 only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHB_DHC_R3_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op00_op01_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op02_op03_20260709.py",
)
P7_R54_AHR_POST_DHB_DHC_R3_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF: Final = (
    "wait_for_explicit_DHR_OP04_actual_source_claim_separation_without_DHB_envelope_conversion"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF: Final = (
    "repair_explicit_DHR_OP04_actual_source_claim_separation_without_existing_DHR_OP05_builder_call"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_DHB_ENVELOPE_ONLY_NOT_BUILDER_INPUT_REF: Final = (
    "stop_DHB_handoff_envelope_only_not_DHR_OP04_builder_input_collect_explicit_OP04_material"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHR_OP04_INPUT_BODY_LEAK_PROMOTION_OR_AUTORUN_REF: Final = (
    "blocked_DHR_OP04_input_body_leak_promotion_or_autorun_without_existing_DHR_OP05_builder_call"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_MANUAL_CALL_NOT_REQUESTED_STOP_REF: Final = (
    "manual_call_not_requested_stop_before_existing_DHR_OP05_builder_call"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_MANUAL_CALL_REQUEST_REF: Final = (
    "wait_for_explicit_manual_call_request_and_allow_existing_DHR_OP05_builder_call_flag"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_MANUAL_CALL_PERMISSION_INPUTS_REF: Final = (
    "repair_manual_call_permission_inputs_without_existing_DHR_OP05_builder_call"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_MANUAL_CALL_PROMOTION_OR_AUTORUN_REF: Final = (
    "blocked_manual_call_permission_body_leak_promotion_or_autorun_without_existing_DHR_OP05_builder_call"
)

P7_R54_AHR_POST_DHB_DHC_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP02_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key not in {
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "existing_dhr_op04_assert_called_here",
    }
)
P7_R54_AHR_POST_DHB_DHC_OP03_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key not in {
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
        "existing_dhr_op04_assert_called_here",
        "manual_call_requested_here",
        "manual_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
    }
)

P7_R54_AHR_POST_DHB_DHC_DHR_OP04_INPUT_PROMOTION_FIELD_REFS: Final[tuple[str, ...]] = (
    "helper_green_promoted_to_actual_source",
    "target_green_promoted_to_actual_source",
    "result_memo_green_promoted_to_actual_source",
    "fixture_promoted_to_actual_source",
    "historical_reuse_promoted_to_actual_source",
    "candidate_shape_promoted_to_actual_source",
    "actual_operation_receipt_created_by_helper_here",
    "actual_rows_created_by_helper_here",
)

P7_R54_AHR_POST_DHB_DHC_OP02_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op01_material_present",
    "op01_contract_valid",
    "op01_schema_version",
    "op01_material_ref",
    "op01_status_ref",
    "op01_next_required_step",
    "op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check",
    "explicit_dhr_op04_actual_source_claim_separation_required",
    "explicit_dhr_op04_material_present",
    "explicit_dhr_op04_shaped_material_valid",
    "explicit_dhr_op04_contract_valid",
    "explicit_dhr_op04_schema_version",
    "explicit_dhr_op04_operation_step_ref",
    "explicit_dhr_op04_material_ref",
    "explicit_dhr_op04_status_ref",
    "explicit_dhr_op04_body_free",
    "explicit_dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan",
    "explicit_dhr_op04_actual_source_claim_confirmed_for_downstream_handoff",
    "explicit_dhr_op04_actual_source_claim_bodyfree",
    "explicit_dhr_op04_actual_operation_receipt_created_by_helper_here",
    "explicit_dhr_op04_actual_rows_created_by_helper_here",
    "explicit_dhr_op04_candidate_shape_promoted_to_actual_source",
    "explicit_dhr_op04_helper_green_promoted_to_actual_source",
    "explicit_dhr_op04_target_green_promoted_to_actual_source",
    "explicit_dhr_op04_result_memo_green_promoted_to_actual_source",
    "explicit_dhr_op04_fixture_promoted_to_actual_source",
    "explicit_dhr_op04_historical_reuse_promoted_to_actual_source",
    "existing_dhr_op04_assert_ref",
    "existing_dhr_op04_assert_import_path_ref",
    "existing_dhr_op04_assert_import_available",
    "existing_dhr_op04_assert_called_here",
    "existing_dhr_op04_assert_failure_ref",
    "dhr_op04_builder_called_here",
    "optional_dhb_op04_manual_handoff_envelope_present",
    "optional_dhb_op05_compatibility_crosswalk_present",
    "dhb_handoff_envelope_used_as_dhr_op04_input_here",
    "dhb_envelope_only_without_explicit_op04",
    "dhc_op02_input_forbidden_payload_key_path_refs",
    "dhc_op02_input_forbidden_payload_key_path_count",
    "dhc_op02_input_body_like_value_path_refs",
    "dhc_op02_input_body_like_value_path_count",
    "dhc_op02_input_promotion_claim_refs",
    "dhc_op02_input_promotion_claim_ref_count",
    "dhc_op02_input_no_touch_mutation_path_refs",
    "dhc_op02_input_no_touch_mutation_path_count",
    "dhc_op02_status_ref",
    "bodyfree_existing_dhr_op05_builder_input_eligibility_status_ref",
    "dhc_op02_allowed_status_refs",
    "dhc_op02_allowed_status_ref_count",
    "dhc_op02_existing_dhr_op05_builder_input_eligible_explicit_op04",
    "dhc_op02_waiting_for_explicit_dhr_op04_actual_source_claim_separation",
    "dhc_op02_dhr_op04_contract_repair_required",
    "dhc_op02_dhb_envelope_only_not_builder_input_stopped",
    "dhc_op02_bodyfree_leak_promotion_or_autorun_blocked",
    "dhc_op02_reason_refs",
    "dhc_op02_reason_ref_count",
    "dhc_op02_blocker_refs",
    "dhc_op02_blocker_ref_count",
    "manual_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "api_db_rn_runtime_response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "dhc_op02_does_not_call_dhr_op04_builder",
    "dhc_op02_does_not_call_dhr_op05",
    "dhc_op02_does_not_call_existing_dhr_op05_builder",
    "dhc_op02_does_not_call_dhr_op06",
    "dhc_op02_does_not_execute_dmd_r52_or_release",
    "dhc_op02_does_not_start_actual_review",
    "dhc_op02_does_not_create_actual_rows",
    "dhc_op02_does_not_create_question_need_observation_rows",
    "dhc_op02_does_not_start_p8_question_design",
    "dhc_op02_does_not_change_api_db_rn_runtime_response_key",
    "dhc_op02_does_not_materialize_question_text",
    "dhc_op02_does_not_create_json_schema_file",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "target_test_ref_refs",
    "compileall_target_ref_refs",
    "public_contract",
    "dhc_no_touch_contract",
    "body_free_markers",
    "dhc_op00_implemented",
    "dhc_op01_implemented",
    "dhc_op02_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP03_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op02_material_present",
    "op02_contract_valid",
    "op02_schema_version",
    "op02_material_ref",
    "op02_status_ref",
    "op02_next_required_step",
    "op02_existing_dhr_op05_builder_input_eligible_explicit_op04",
    "op02_explicit_dhr_op04_material_present",
    "op02_explicit_dhr_op04_contract_valid",
    "op02_existing_dhr_op04_assert_called_here",
    "manual_call_requested",
    "manual_call_requested_here",
    "manual_call_request_ref",
    "manual_call_request_ref_present",
    "allow_existing_dhr_op05_builder_call_input",
    "allow_implicit_op04_builder_fallback_input",
    "implicit_op04_builder_fallback_requested_here",
    "implicit_op04_builder_fallback_allowed_here",
    "implicit_op04_builder_fallback_used_here",
    "manual_call_allowed",
    "manual_call_allowed_here",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_result_generated_here",
    "existing_dhr_op05_contract_valid",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_call_allowed_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_r52_execution_allowed_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_allowed_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "release_decision_allowed_here",
    "api_db_rn_runtime_response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "permission_allowed_but_existing_builder_not_called_until_dhc_op04",
    "dhc_op03_permission_input_forbidden_payload_key_path_refs",
    "dhc_op03_permission_input_forbidden_payload_key_path_count",
    "dhc_op03_permission_input_body_like_value_path_refs",
    "dhc_op03_permission_input_body_like_value_path_count",
    "dhc_op03_permission_input_promotion_claim_refs",
    "dhc_op03_permission_input_promotion_claim_ref_count",
    "dhc_op03_permission_input_no_touch_mutation_path_refs",
    "dhc_op03_permission_input_no_touch_mutation_path_count",
    "dhc_op03_status_ref",
    "bodyfree_manual_call_permission_status_ref",
    "dhc_op03_allowed_status_refs",
    "dhc_op03_allowed_status_ref_count",
    "dhc_op03_manual_call_allowed_explicit_op04_only",
    "dhc_op03_manual_call_not_requested_stopped",
    "dhc_op03_waiting_for_explicit_manual_call_request",
    "dhc_op03_waiting_for_explicit_dhr_op04_actual_source_claim_separation",
    "dhc_op03_repair_required_for_manual_call_permission_inputs",
    "dhc_op03_bodyfree_leak_promotion_or_autorun_blocked",
    "dhc_op03_reason_refs",
    "dhc_op03_reason_ref_count",
    "dhc_op03_blocker_refs",
    "dhc_op03_blocker_ref_count",
    "dhc_op03_does_not_call_existing_dhr_op05_builder",
    "dhc_op03_does_not_generate_existing_dhr_op05_result",
    "dhc_op03_does_not_call_dhr_op06",
    "dhc_op03_does_not_execute_dmd_r52_or_release",
    "dhc_op03_does_not_start_actual_review",
    "dhc_op03_does_not_create_actual_rows",
    "dhc_op03_does_not_create_question_need_observation_rows",
    "dhc_op03_does_not_start_p8_question_design",
    "dhc_op03_does_not_change_api_db_rn_runtime_response_key",
    "dhc_op03_does_not_materialize_question_text",
    "dhc_op03_does_not_create_json_schema_file",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "target_test_ref_refs",
    "compileall_target_ref_refs",
    "public_contract",
    "dhc_no_touch_contract",
    "body_free_markers",
    "dhc_op00_implemented",
    "dhc_op01_implemented",
    "dhc_op02_implemented",
    "dhc_op03_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP02_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP02_REQUIRED_FALSE_FLAG_REFS)
)
P7_R54_AHR_POST_DHB_DHC_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP03_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP03_REQUIRED_FALSE_FLAG_REFS)
)


def _op01_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op01_explicit_dhb_op08_closed_handoff_material_intake_contract(data)
    except ValueError:
        return False
    return True


def _op02_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(data)
    except ValueError:
        return False
    return True


def _dhr_op04_contract_valid(data: Any) -> tuple[bool, bool, str]:
    if not isinstance(data, Mapping):
        return False, False, "explicit_dhr_op04_material_missing"
    called = True
    try:
        P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_IMPORT_CALLABLE_REF(data)
    except Exception as exc:  # noqa: BLE001 - deliberately body-free sanitized failure category only.
        return False, called, _clean_ref(type(exc).__name__, default="existing_dhr_op04_assert_failed", max_length=120)
    return True, called, "none"


def _dhr_op04_promotion_claim_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_DHB_DHC_DHR_OP04_INPUT_PROMOTION_FIELD_REFS and child is True:
                paths.append(child_path)
            paths.extend(_dhr_op04_promotion_claim_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_dhr_op04_promotion_claim_paths(child, path=f"{path}[{index}]"))
    return paths


def _dhc_op02_status(
    *,
    op01_valid: bool,
    op01_ready: bool,
    explicit_present: bool,
    explicit_contract_valid: bool,
    explicit_ready_for_scan: bool,
    envelope_present: bool,
    scan_blocked: bool,
) -> tuple[str, list[str], list[str], str]:
    if scan_blocked:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[4],
            ["explicit_DHR_OP04_or_optional_DHB_reference_contains_body_leak_promotion_or_autorun"],
            ["stop_before_manual_call_permission_and_repair_DHR_OP04_input_boundary"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHR_OP04_INPUT_BODY_LEAK_PROMOTION_OR_AUTORUN_REF,
        )
    if not op01_valid or not op01_ready:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[2],
            ["DHC_OP01_DHR_lane_intake_is_not_ready_for_OP02"],
            ["repair_or_complete_DHC_OP01_before_DHR_OP05_builder_input_eligibility"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF,
        )
    if not explicit_present and envelope_present:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[3],
            ["DHB_handoff_envelope_present_but_not_DHR_OP04_actual_source_claim_separation"],
            ["collect_explicit_DHR_OP04_actual_source_claim_separation_before_builder_permission"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_DHB_ENVELOPE_ONLY_NOT_BUILDER_INPUT_REF,
        )
    if not explicit_present:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[1],
            ["waiting_for_explicit_DHR_OP04_actual_source_claim_separation"],
            [],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF,
        )
    if not explicit_contract_valid or not explicit_ready_for_scan:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[2],
            ["explicit_DHR_OP04_actual_source_claim_separation_contract_invalid_or_not_ready"],
            ["repair_explicit_DHR_OP04_material_before_manual_call_permission"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF,
        )
    return (
        P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[0],
        ["explicit_DHR_OP04_actual_source_claim_separation_contract_valid_and_ready_for_preflight"],
        [],
        P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    )


def build_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check(
    op01_dhb_op08_intake: Mapping[str, Any] | None = None,
    explicit_dhr_op04_actual_source_claim_separation: Mapping[str, Any] | None = None,
    optional_dhb_op04_manual_handoff_envelope: Mapping[str, Any] | None = None,
    optional_dhb_op05_compatibility_crosswalk: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Check explicit DHR-OP04 eligibility without converting DHB envelope or calling DHR-OP05."""

    op01 = op01_dhb_op08_intake
    op01_present = isinstance(op01, Mapping)
    op01_valid = _op01_valid(op01)
    op01_status = _clean_ref(op01.get("dhc_op01_status_ref") if op01_present else None, default="op01_status_missing", max_length=320)
    op01_ready = bool(
        op01_valid
        and op01_status == P7_R54_AHR_POST_DHB_DHC_OP01_ALLOWED_STATUS_REFS[0]
        and op01.get("dhc_op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check") is True
    )
    explicit_op04 = explicit_dhr_op04_actual_source_claim_separation
    explicit_present = isinstance(explicit_op04, Mapping)
    envelope_present = isinstance(optional_dhb_op04_manual_handoff_envelope, Mapping)
    crosswalk_present = isinstance(optional_dhb_op05_compatibility_crosswalk, Mapping)
    scan_root = {
        "explicit_dhr_op04_actual_source_claim_separation": explicit_op04 if explicit_present else {},
        "optional_dhb_op04_manual_handoff_envelope": optional_dhb_op04_manual_handoff_envelope if envelope_present else {},
        "optional_dhb_op05_compatibility_crosswalk": optional_dhb_op05_compatibility_crosswalk if crosswalk_present else {},
    }
    forbidden_paths = _scan_forbidden_payload_key_paths(scan_root, path="dhc_op02_input")
    body_like_paths = _scan_body_like_value_paths(scan_root, path="dhc_op02_input")
    promotion_paths = _dedupe_clean_refs(
        _scan_promotion_claim_paths(scan_root, path="dhc_op02_input")
        + _dhr_op04_promotion_claim_paths(scan_root, path="dhc_op02_input"),
        max_length=360,
    )
    no_touch_paths = _scan_no_touch_mutation_paths(scan_root, path="dhc_op02_input")
    scan_blocked = bool(forbidden_paths or body_like_paths or promotion_paths or no_touch_paths)
    explicit_schema = _clean_ref(explicit_op04.get("schema_version") if explicit_present else None, default="dhr_op04_schema_missing", max_length=320)
    explicit_step = _clean_ref(explicit_op04.get("operation_step_ref") if explicit_present else None, default="dhr_op04_step_missing", max_length=320)
    explicit_material_ref = _clean_ref(explicit_op04.get("material_id") if explicit_present else None, default="dhr_op04_material_missing", max_length=320)
    explicit_status = _clean_ref(explicit_op04.get("dhr_op04_status_ref") if explicit_present else None, default="dhr_op04_status_missing", max_length=320)
    explicit_body_free = bool(explicit_present and explicit_op04.get("body_free") is True)
    explicit_ready_for_scan = bool(
        explicit_present and explicit_op04.get("dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan") is True
    )
    explicit_shaped_valid = bool(
        explicit_present
        and explicit_schema == P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_SCHEMA_VERSION_REF
        and explicit_step == P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_STEP_REF
        and explicit_body_free
        and explicit_status in P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ALLOWED_STATUS_REFS
    )
    contract_valid, assert_called, assert_failure_ref = (False, False, "explicit_dhr_op04_material_missing")
    if explicit_present and not scan_blocked:
        contract_valid, assert_called, assert_failure_ref = _dhr_op04_contract_valid(explicit_op04)
    explicit_contract_valid = bool(explicit_shaped_valid and contract_valid)
    status_ref, reasons, blockers, next_required_step = _dhc_op02_status(
        op01_valid=op01_valid,
        op01_ready=op01_ready,
        explicit_present=explicit_present,
        explicit_contract_valid=explicit_contract_valid,
        explicit_ready_for_scan=explicit_ready_for_scan,
        envelope_present=envelope_present,
        scan_blocked=scan_blocked,
    )
    eligible = status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[0]
    waiting = status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[1]
    repair = status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[2]
    envelope_only = status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[3]
    blocked = status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[4]
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers)
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP02_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP02_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_20260709",
            "review_session_id": _safe_review_session_id(review_session_id or (op01.get("review_session_id") if op01_present else None)),
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op01_material_present": op01_present,
            "op01_contract_valid": op01_valid,
            "op01_schema_version": _clean_ref(op01.get("schema_version") if op01_present else None, default="op01_schema_missing", max_length=320),
            "op01_material_ref": _clean_ref(op01.get("material_id") if op01_present else None, default="op01_material_missing", max_length=320),
            "op01_status_ref": op01_status,
            "op01_next_required_step": _clean_ref(op01.get("next_required_step") if op01_present else None, default="op01_next_step_missing", max_length=320),
            "op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check": op01_ready,
            "explicit_dhr_op04_actual_source_claim_separation_required": True,
            "explicit_dhr_op04_material_present": explicit_present,
            "explicit_dhr_op04_shaped_material_valid": explicit_shaped_valid,
            "explicit_dhr_op04_contract_valid": explicit_contract_valid,
            "explicit_dhr_op04_schema_version": explicit_schema,
            "explicit_dhr_op04_operation_step_ref": explicit_step,
            "explicit_dhr_op04_material_ref": explicit_material_ref,
            "explicit_dhr_op04_status_ref": explicit_status,
            "explicit_dhr_op04_body_free": explicit_body_free,
            "explicit_dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan": explicit_ready_for_scan,
            "explicit_dhr_op04_actual_source_claim_confirmed_for_downstream_handoff": bool(explicit_present and explicit_op04.get("actual_source_claim_confirmed_for_downstream_handoff") is True),
            "explicit_dhr_op04_actual_source_claim_bodyfree": bool(explicit_present and explicit_op04.get("actual_source_claim_bodyfree") is True),
            "explicit_dhr_op04_actual_operation_receipt_created_by_helper_here": bool(explicit_present and explicit_op04.get("actual_operation_receipt_created_by_helper_here") is True),
            "explicit_dhr_op04_actual_rows_created_by_helper_here": bool(explicit_present and explicit_op04.get("actual_rows_created_by_helper_here") is True),
            "explicit_dhr_op04_candidate_shape_promoted_to_actual_source": bool(explicit_present and explicit_op04.get("candidate_shape_promoted_to_actual_source") is True),
            "explicit_dhr_op04_helper_green_promoted_to_actual_source": bool(explicit_present and explicit_op04.get("helper_green_promoted_to_actual_source") is True),
            "explicit_dhr_op04_target_green_promoted_to_actual_source": bool(explicit_present and explicit_op04.get("target_green_promoted_to_actual_source") is True),
            "explicit_dhr_op04_result_memo_green_promoted_to_actual_source": bool(explicit_present and explicit_op04.get("result_memo_green_promoted_to_actual_source") is True),
            "explicit_dhr_op04_fixture_promoted_to_actual_source": bool(explicit_present and explicit_op04.get("fixture_promoted_to_actual_source") is True),
            "explicit_dhr_op04_historical_reuse_promoted_to_actual_source": bool(explicit_present and explicit_op04.get("historical_reuse_promoted_to_actual_source") is True),
            "existing_dhr_op04_assert_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_REF,
            "existing_dhr_op04_assert_import_path_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_IMPORT_PATH_REF,
            "existing_dhr_op04_assert_import_available": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ASSERT_IMPORT_CALLABLE_REF
            is dhr.assert_p7_r54_ahr_post_elr19_dhr_op04_actual_source_claim_separation_invalid_source_classification_contract,
            "existing_dhr_op04_assert_called_here": assert_called,
            "existing_dhr_op04_assert_failure_ref": assert_failure_ref,
            "dhr_op04_builder_called_here": False,
            "optional_dhb_op04_manual_handoff_envelope_present": envelope_present,
            "optional_dhb_op05_compatibility_crosswalk_present": crosswalk_present,
            "dhb_handoff_envelope_used_as_dhr_op04_input_here": False,
            "dhb_envelope_only_without_explicit_op04": bool(envelope_present and not explicit_present),
            "dhc_op02_input_forbidden_payload_key_path_refs": forbidden_paths,
            "dhc_op02_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "dhc_op02_input_body_like_value_path_refs": body_like_paths,
            "dhc_op02_input_body_like_value_path_count": len(body_like_paths),
            "dhc_op02_input_promotion_claim_refs": promotion_paths,
            "dhc_op02_input_promotion_claim_ref_count": len(promotion_paths),
            "dhc_op02_input_no_touch_mutation_path_refs": no_touch_paths,
            "dhc_op02_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhc_op02_status_ref": status_ref,
            "bodyfree_existing_dhr_op05_builder_input_eligibility_status_ref": status_ref,
            "dhc_op02_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS,
            "dhc_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS),
            "dhc_op02_existing_dhr_op05_builder_input_eligible_explicit_op04": eligible,
            "dhc_op02_waiting_for_explicit_dhr_op04_actual_source_claim_separation": waiting,
            "dhc_op02_dhr_op04_contract_repair_required": repair,
            "dhc_op02_dhb_envelope_only_not_builder_input_stopped": envelope_only,
            "dhc_op02_bodyfree_leak_promotion_or_autorun_blocked": blocked,
            "dhc_op02_reason_refs": reason_refs,
            "dhc_op02_reason_ref_count": reason_count,
            "dhc_op02_blocker_refs": blocker_refs,
            "dhc_op02_blocker_ref_count": blocker_count,
            "manual_call_allowed_here": False,
            "existing_dhr_op05_builder_call_allowed_here": False,
            "existing_dhr_op05_builder_called_here": False,
            "existing_dhr_op05_result_present": False,
            "existing_dhr_op05_contract_valid": False,
            "dhr_op05_called_here": False,
            "dhr_op05_builder_called_here": False,
            "dhr_op06_called_here": False,
            "dhr_op07_materialized_here": False,
            "dmd_execution_started_here": False,
            "dmd_r52_executed_here": False,
            "actual_review_started_here": False,
            "actual_rows_created_here": False,
            "question_need_observation_rows_created_here": False,
            "p8_question_design_started": False,
            "p8_question_implementation_started": False,
            "question_text_materialized_here": False,
            "api_db_rn_runtime_response_key_changed": False,
            "json_schema_file_created_here": False,
            "p7_complete": False,
            "release_allowed": False,
            "dhc_op02_does_not_call_dhr_op04_builder": True,
            "dhc_op02_does_not_call_dhr_op05": True,
            "dhc_op02_does_not_call_existing_dhr_op05_builder": True,
            "dhc_op02_does_not_call_dhr_op06": True,
            "dhc_op02_does_not_execute_dmd_r52_or_release": True,
            "dhc_op02_does_not_start_actual_review": True,
            "dhc_op02_does_not_create_actual_rows": True,
            "dhc_op02_does_not_create_question_need_observation_rows": True,
            "dhc_op02_does_not_start_p8_question_design": True,
            "dhc_op02_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op02_does_not_materialize_question_text": True,
            "dhc_op02_does_not_create_json_schema_file": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP02_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP02_NOT_YET_IMPLEMENTED_STEPS),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R3_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R3_COMPILEALL_TARGET_REF_REFS),
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "dhc_op01_implemented": True,
            "dhc_op02_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op02_existing_dhr_op05_builder_input_eligibility_check_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert DHC-OP02 explicit DHR-OP04 eligibility without allowing DHR-OP05 execution."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP02_REQUIRED_FIELD_REFS, source="DHC-OP02")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP02 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP02_SCHEMA_VERSION:
        raise ValueError("DHC-OP02 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF:
        raise ValueError("DHC-OP02 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP02 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP02 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP02 must remain body-free")
    for key in (
        "explicit_dhr_op04_actual_source_claim_separation_required",
        "dhc_op02_does_not_call_dhr_op04_builder",
        "dhc_op02_does_not_call_dhr_op05",
        "dhc_op02_does_not_call_existing_dhr_op05_builder",
        "dhc_op02_does_not_call_dhr_op06",
        "dhc_op02_does_not_execute_dmd_r52_or_release",
        "dhc_op02_does_not_start_actual_review",
        "dhc_op02_does_not_create_actual_rows",
        "dhc_op02_does_not_create_question_need_observation_rows",
        "dhc_op02_does_not_start_p8_question_design",
        "dhc_op02_does_not_change_api_db_rn_runtime_response_key",
        "dhc_op02_does_not_materialize_question_text",
        "dhc_op02_does_not_create_json_schema_file",
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP02 required true field changed: {key}")
    for key in (
        "dhr_op04_builder_called_here",
        "dhb_handoff_envelope_used_as_dhr_op04_input_here",
        "manual_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_result_present",
        "existing_dhr_op05_contract_valid",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created_here",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP02 forbidden execution/promotion flag changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP02_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP02 required false flag changed: {key}")
    for field, count_field in (
        ("dhc_op02_input_forbidden_payload_key_path_refs", "dhc_op02_input_forbidden_payload_key_path_count"),
        ("dhc_op02_input_body_like_value_path_refs", "dhc_op02_input_body_like_value_path_count"),
        ("dhc_op02_input_promotion_claim_refs", "dhc_op02_input_promotion_claim_ref_count"),
        ("dhc_op02_input_no_touch_mutation_path_refs", "dhc_op02_input_no_touch_mutation_path_count"),
        ("dhc_op02_reason_refs", "dhc_op02_reason_ref_count"),
        ("dhc_op02_blocker_refs", "dhc_op02_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP02 count field changed: {count_field}")
    if tuple(data.get("dhc_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP02 allowed status refs changed")
    if data.get("dhc_op02_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS):
        raise ValueError("DHC-OP02 allowed status count changed")
    if data.get("bodyfree_existing_dhr_op05_builder_input_eligibility_status_ref") != data.get("dhc_op02_status_ref"):
        raise ValueError("DHC-OP02 status alias changed")
    if data.get("existing_dhr_op04_assert_import_available") is not True:
        raise ValueError("DHC-OP02 DHR-OP04 assert import unavailable")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP02_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP02 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R3_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP02 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R3_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP02 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP02 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP02 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP02 body-free marker changed")
    status_ref = data.get("dhc_op02_status_ref")
    flags = [
        data.get("dhc_op02_existing_dhr_op05_builder_input_eligible_explicit_op04") is True,
        data.get("dhc_op02_waiting_for_explicit_dhr_op04_actual_source_claim_separation") is True,
        data.get("dhc_op02_dhr_op04_contract_repair_required") is True,
        data.get("dhc_op02_dhb_envelope_only_not_builder_input_stopped") is True,
        data.get("dhc_op02_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("DHC-OP02 must select exactly one branch")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF:
            raise ValueError("DHC-OP02 eligible next step changed")
        for key in (
            "op01_contract_valid",
            "op01_ready_for_op02_existing_dhr_op05_builder_input_eligibility_check",
            "explicit_dhr_op04_material_present",
            "explicit_dhr_op04_shaped_material_valid",
            "explicit_dhr_op04_contract_valid",
            "explicit_dhr_op04_body_free",
            "explicit_dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan",
            "existing_dhr_op04_assert_called_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"DHC-OP02 eligible true field missing: {key}")
        for field in (
            "dhc_op02_input_forbidden_payload_key_path_refs",
            "dhc_op02_input_body_like_value_path_refs",
            "dhc_op02_input_promotion_claim_refs",
            "dhc_op02_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError(f"DHC-OP02 eligible scan refs must be empty: {field}")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF:
            raise ValueError("DHC-OP02 waiting next step changed")
        if data.get("explicit_dhr_op04_material_present") is not False:
            raise ValueError("DHC-OP02 waiting branch must not have explicit DHR-OP04 material")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") not in {
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF,
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_DHB_OP08_INTAKE_REF,
        }:
            raise ValueError("DHC-OP02 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_DHB_ENVELOPE_ONLY_NOT_BUILDER_INPUT_REF:
            raise ValueError("DHC-OP02 envelope-only next step changed")
        if data.get("dhb_envelope_only_without_explicit_op04") is not True:
            raise ValueError("DHC-OP02 envelope-only branch must preserve envelope-only reason")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[4]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_DHR_OP04_INPUT_BODY_LEAK_PROMOTION_OR_AUTORUN_REF:
            raise ValueError("DHC-OP02 blocked next step changed")
        if not (
            data.get("dhc_op02_input_forbidden_payload_key_path_refs")
            or data.get("dhc_op02_input_body_like_value_path_refs")
            or data.get("dhc_op02_input_promotion_claim_refs")
            or data.get("dhc_op02_input_no_touch_mutation_path_refs")
        ):
            raise ValueError("DHC-OP02 blocked branch must record scan refs")
    return True


def _dhc_op03_status(
    *,
    op02_valid: bool,
    op02_status: str,
    op02_eligible: bool,
    manual_call_requested: bool,
    manual_call_request_ref_present: bool,
    allow_existing_builder_call: bool,
    allow_implicit_fallback: bool,
    scan_blocked: bool,
) -> tuple[str, list[str], list[str], str]:
    if scan_blocked or allow_implicit_fallback:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[5],
            ["manual_call_permission_inputs_contain_body_leak_promotion_autorun_or_implicit_fallback_request"],
            ["stop_before_existing_DHR_OP05_builder_call_and_repair_permission_boundary"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_MANUAL_CALL_PROMOTION_OR_AUTORUN_REF,
        )
    if not op02_valid:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[4],
            ["DHC_OP02_input_eligibility_material_invalid_or_missing"],
            ["repair_DHC_OP02_material_before_manual_call_permission"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_MANUAL_CALL_PERMISSION_INPUTS_REF,
        )
    if not op02_eligible:
        if op02_status in {
            P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[1],
            P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[3],
        }:
            return (
                P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[3],
                ["waiting_for_explicit_DHR_OP04_actual_source_claim_separation_before_manual_call_permission"],
                [],
                P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF,
            )
        return (
            P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[4],
            ["DHC_OP02_not_eligible_for_manual_call_permission"],
            ["repair_or_unblock_DHC_OP02_before_manual_call_permission"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_MANUAL_CALL_PERMISSION_INPUTS_REF,
        )
    if not manual_call_requested:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[1],
            ["manual_call_not_requested"],
            [],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_MANUAL_CALL_NOT_REQUESTED_STOP_REF,
        )
    if not manual_call_request_ref_present or not allow_existing_builder_call:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[2],
            ["waiting_for_explicit_manual_call_request_ref_or_builder_call_allow_flag"],
            [],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_MANUAL_CALL_REQUEST_REF,
        )
    return (
        P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[0],
        ["manual_call_permission_allowed_for_future_DHC_OP04_with_explicit_OP04_only"],
        [],
        P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    )


def build_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate(
    op02_input_eligibility: Mapping[str, Any] | None = None,
    *,
    manual_call_requested: bool = False,
    manual_call_request_ref: str | None = None,
    allow_existing_dhr_op05_builder_call: bool = False,
    allow_implicit_op04_builder_fallback: bool = False,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Gate manual-call permission without calling the existing DHR-OP05 builder."""

    op02 = op02_input_eligibility
    op02_present = isinstance(op02, Mapping)
    op02_valid = _op02_valid(op02)
    op02_status = _clean_ref(op02.get("dhc_op02_status_ref") if op02_present else None, default="op02_status_missing", max_length=320)
    op02_eligible = bool(
        op02_valid
        and op02_status == P7_R54_AHR_POST_DHB_DHC_OP02_ALLOWED_STATUS_REFS[0]
        and op02.get("dhc_op02_existing_dhr_op05_builder_input_eligible_explicit_op04") is True
    )
    request_ref = _clean_ref(manual_call_request_ref, default="manual_call_request_ref_missing", max_length=240)
    request_ref_present = bool(manual_call_request_ref and request_ref != "manual_call_request_ref_missing")
    permission_input_scan = {
        "op02_input_eligibility": op02 if op02_present else {},
        "manual_call_request_ref": request_ref,
        "allow_existing_dhr_op05_builder_call": bool(allow_existing_dhr_op05_builder_call),
        "allow_implicit_op04_builder_fallback": bool(allow_implicit_op04_builder_fallback),
    }
    forbidden_paths = _scan_forbidden_payload_key_paths(permission_input_scan, path="dhc_op03_permission_input")
    body_like_paths = _scan_body_like_value_paths(permission_input_scan, path="dhc_op03_permission_input")
    promotion_paths = _scan_promotion_claim_paths(permission_input_scan, path="dhc_op03_permission_input")
    no_touch_paths = _scan_no_touch_mutation_paths(permission_input_scan, path="dhc_op03_permission_input")
    # The permission gate is allowed to carry its own request/allow booleans; OP03
    # blocks only upstream body/no-touch/autodownstream mutations or implicit fallback.
    promotion_paths = [
        path
        for path in promotion_paths
        if not path.endswith(".allow_existing_dhr_op05_builder_call")
    ]
    scan_blocked = bool(forbidden_paths or body_like_paths or promotion_paths or no_touch_paths)
    status_ref, reasons, blockers, next_required_step = _dhc_op03_status(
        op02_valid=op02_valid,
        op02_status=op02_status,
        op02_eligible=op02_eligible,
        manual_call_requested=bool(manual_call_requested),
        manual_call_request_ref_present=request_ref_present,
        allow_existing_builder_call=bool(allow_existing_dhr_op05_builder_call),
        allow_implicit_fallback=bool(allow_implicit_op04_builder_fallback),
        scan_blocked=scan_blocked,
    )
    allowed = status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[0]
    not_requested = status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[1]
    waiting_request = status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[2]
    waiting_op04 = status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[3]
    repair = status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[4]
    blocked = status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[5]
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers)
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP03_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP03_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_20260709",
            "review_session_id": _safe_review_session_id(review_session_id or (op02.get("review_session_id") if op02_present else None)),
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op02_material_present": op02_present,
            "op02_contract_valid": op02_valid,
            "op02_schema_version": _clean_ref(op02.get("schema_version") if op02_present else None, default="op02_schema_missing", max_length=320),
            "op02_material_ref": _clean_ref(op02.get("material_id") if op02_present else None, default="op02_material_missing", max_length=320),
            "op02_status_ref": op02_status,
            "op02_next_required_step": _clean_ref(op02.get("next_required_step") if op02_present else None, default="op02_next_step_missing", max_length=320),
            "op02_existing_dhr_op05_builder_input_eligible_explicit_op04": op02_eligible,
            "op02_explicit_dhr_op04_material_present": bool(op02_present and op02.get("explicit_dhr_op04_material_present") is True),
            "op02_explicit_dhr_op04_contract_valid": bool(op02_present and op02.get("explicit_dhr_op04_contract_valid") is True),
            "op02_existing_dhr_op04_assert_called_here": bool(op02_present and op02.get("existing_dhr_op04_assert_called_here") is True),
            "manual_call_requested": bool(manual_call_requested),
            "manual_call_requested_here": bool(manual_call_requested),
            "manual_call_request_ref": request_ref,
            "manual_call_request_ref_present": request_ref_present,
            "allow_existing_dhr_op05_builder_call_input": bool(allow_existing_dhr_op05_builder_call),
            "allow_implicit_op04_builder_fallback_input": bool(allow_implicit_op04_builder_fallback),
            "implicit_op04_builder_fallback_requested_here": bool(allow_implicit_op04_builder_fallback),
            "implicit_op04_builder_fallback_allowed_here": False,
            "implicit_op04_builder_fallback_used_here": False,
            "manual_call_allowed": allowed,
            "manual_call_allowed_here": allowed,
            "existing_dhr_op05_builder_call_allowed_here": allowed,
            "existing_dhr_op05_builder_called_here": False,
            "existing_dhr_op05_result_present": False,
            "existing_dhr_op05_result_generated_here": False,
            "existing_dhr_op05_contract_valid": False,
            "dhr_op05_called_here": False,
            "dhr_op05_builder_called_here": False,
            "dhr_op06_call_allowed_here": False,
            "dhr_op06_called_here": False,
            "dhr_op07_materialized_here": False,
            "dmd_r52_execution_allowed_here": False,
            "dmd_execution_started_here": False,
            "dmd_r52_executed_here": False,
            "actual_review_started_here": False,
            "actual_rows_created_here": False,
            "question_need_observation_rows_created_here": False,
            "p8_question_design_allowed_here": False,
            "p8_question_design_started": False,
            "p8_question_implementation_started": False,
            "question_text_materialized_here": False,
            "release_decision_allowed_here": False,
            "api_db_rn_runtime_response_key_changed": False,
            "json_schema_file_created_here": False,
            "p7_complete": False,
            "release_allowed": False,
            "permission_allowed_but_existing_builder_not_called_until_dhc_op04": allowed,
            "dhc_op03_permission_input_forbidden_payload_key_path_refs": forbidden_paths,
            "dhc_op03_permission_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "dhc_op03_permission_input_body_like_value_path_refs": body_like_paths,
            "dhc_op03_permission_input_body_like_value_path_count": len(body_like_paths),
            "dhc_op03_permission_input_promotion_claim_refs": promotion_paths,
            "dhc_op03_permission_input_promotion_claim_ref_count": len(promotion_paths),
            "dhc_op03_permission_input_no_touch_mutation_path_refs": no_touch_paths,
            "dhc_op03_permission_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhc_op03_status_ref": status_ref,
            "bodyfree_manual_call_permission_status_ref": status_ref,
            "dhc_op03_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS,
            "dhc_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS),
            "dhc_op03_manual_call_allowed_explicit_op04_only": allowed,
            "dhc_op03_manual_call_not_requested_stopped": not_requested,
            "dhc_op03_waiting_for_explicit_manual_call_request": waiting_request,
            "dhc_op03_waiting_for_explicit_dhr_op04_actual_source_claim_separation": waiting_op04,
            "dhc_op03_repair_required_for_manual_call_permission_inputs": repair,
            "dhc_op03_bodyfree_leak_promotion_or_autorun_blocked": blocked,
            "dhc_op03_reason_refs": reason_refs,
            "dhc_op03_reason_ref_count": reason_count,
            "dhc_op03_blocker_refs": blocker_refs,
            "dhc_op03_blocker_ref_count": blocker_count,
            "dhc_op03_does_not_call_existing_dhr_op05_builder": True,
            "dhc_op03_does_not_generate_existing_dhr_op05_result": True,
            "dhc_op03_does_not_call_dhr_op06": True,
            "dhc_op03_does_not_execute_dmd_r52_or_release": True,
            "dhc_op03_does_not_start_actual_review": True,
            "dhc_op03_does_not_create_actual_rows": True,
            "dhc_op03_does_not_create_question_need_observation_rows": True,
            "dhc_op03_does_not_start_p8_question_design": True,
            "dhc_op03_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op03_does_not_materialize_question_text": True,
            "dhc_op03_does_not_create_json_schema_file": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP03_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHB_DHC_OP03_NOT_YET_IMPLEMENTED_STEPS),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R3_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(P7_R54_AHR_POST_DHB_DHC_R3_COMPILEALL_TARGET_REF_REFS),
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "dhc_op01_implemented": True,
            "dhc_op02_implemented": True,
            "dhc_op03_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(data: Mapping[str, Any]) -> bool:
    """Assert DHC-OP03 manual-call permission gate without builder execution."""

    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP03_REQUIRED_FIELD_REFS, source="DHC-OP03")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP03 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP03_SCHEMA_VERSION:
        raise ValueError("DHC-OP03 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF:
        raise ValueError("DHC-OP03 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP03 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP03 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP03 must remain body-free")
    for key in (
        "dhc_op03_does_not_call_existing_dhr_op05_builder",
        "dhc_op03_does_not_generate_existing_dhr_op05_result",
        "dhc_op03_does_not_call_dhr_op06",
        "dhc_op03_does_not_execute_dmd_r52_or_release",
        "dhc_op03_does_not_start_actual_review",
        "dhc_op03_does_not_create_actual_rows",
        "dhc_op03_does_not_create_question_need_observation_rows",
        "dhc_op03_does_not_start_p8_question_design",
        "dhc_op03_does_not_change_api_db_rn_runtime_response_key",
        "dhc_op03_does_not_materialize_question_text",
        "dhc_op03_does_not_create_json_schema_file",
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP03 required true field changed: {key}")
    for key in (
        "implicit_op04_builder_fallback_allowed_here",
        "implicit_op04_builder_fallback_used_here",
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_result_present",
        "existing_dhr_op05_result_generated_here",
        "existing_dhr_op05_contract_valid",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
        "dhr_op06_call_allowed_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_r52_execution_allowed_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_allowed_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "release_decision_allowed_here",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created_here",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP03 forbidden execution/promotion flag changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP03_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP03 required false flag changed: {key}")
    for field, count_field in (
        ("dhc_op03_permission_input_forbidden_payload_key_path_refs", "dhc_op03_permission_input_forbidden_payload_key_path_count"),
        ("dhc_op03_permission_input_body_like_value_path_refs", "dhc_op03_permission_input_body_like_value_path_count"),
        ("dhc_op03_permission_input_promotion_claim_refs", "dhc_op03_permission_input_promotion_claim_ref_count"),
        ("dhc_op03_permission_input_no_touch_mutation_path_refs", "dhc_op03_permission_input_no_touch_mutation_path_count"),
        ("dhc_op03_reason_refs", "dhc_op03_reason_ref_count"),
        ("dhc_op03_blocker_refs", "dhc_op03_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP03 count field changed: {count_field}")
    if tuple(data.get("dhc_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP03 allowed status refs changed")
    if data.get("dhc_op03_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS):
        raise ValueError("DHC-OP03 allowed status count changed")
    if data.get("bodyfree_manual_call_permission_status_ref") != data.get("dhc_op03_status_ref"):
        raise ValueError("DHC-OP03 status alias changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP03_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP03 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R3_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP03 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R3_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP03 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP03 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP03 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP03 body-free marker changed")
    status_ref = data.get("dhc_op03_status_ref")
    flags = [
        data.get("dhc_op03_manual_call_allowed_explicit_op04_only") is True,
        data.get("dhc_op03_manual_call_not_requested_stopped") is True,
        data.get("dhc_op03_waiting_for_explicit_manual_call_request") is True,
        data.get("dhc_op03_waiting_for_explicit_dhr_op04_actual_source_claim_separation") is True,
        data.get("dhc_op03_repair_required_for_manual_call_permission_inputs") is True,
        data.get("dhc_op03_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("DHC-OP03 must select exactly one branch")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF:
            raise ValueError("DHC-OP03 allowed next step changed")
        for key in (
            "op02_contract_valid",
            "op02_existing_dhr_op05_builder_input_eligible_explicit_op04",
            "op02_explicit_dhr_op04_material_present",
            "op02_explicit_dhr_op04_contract_valid",
            "manual_call_requested",
            "manual_call_requested_here",
            "manual_call_request_ref_present",
            "allow_existing_dhr_op05_builder_call_input",
            "manual_call_allowed",
            "manual_call_allowed_here",
            "existing_dhr_op05_builder_call_allowed_here",
            "permission_allowed_but_existing_builder_not_called_until_dhc_op04",
        ):
            if data.get(key) is not True:
                raise ValueError(f"DHC-OP03 allowed branch true field missing: {key}")
        if data.get("allow_implicit_op04_builder_fallback_input") is not False:
            raise ValueError("DHC-OP03 allowed branch cannot request implicit OP04 fallback")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_MANUAL_CALL_NOT_REQUESTED_STOP_REF:
            raise ValueError("DHC-OP03 not-requested next step changed")
        if data.get("manual_call_requested") is not False or data.get("manual_call_allowed") is not False:
            raise ValueError("DHC-OP03 not-requested branch cannot allow manual call")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_MANUAL_CALL_REQUEST_REF:
            raise ValueError("DHC-OP03 waiting manual request next step changed")
        if data.get("manual_call_allowed") is not False or data.get("existing_dhr_op05_builder_call_allowed_here") is not False:
            raise ValueError("DHC-OP03 waiting manual request branch cannot allow builder")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAIT_FOR_EXPLICIT_DHR_OP04_ACTUAL_SOURCE_CLAIM_SEPARATION_REF:
            raise ValueError("DHC-OP03 waiting OP04 next step changed")
        if data.get("op02_existing_dhr_op05_builder_input_eligible_explicit_op04") is not False:
            raise ValueError("DHC-OP03 waiting OP04 branch cannot carry eligible OP02")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[4]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_MANUAL_CALL_PERMISSION_INPUTS_REF:
            raise ValueError("DHC-OP03 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[5]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_MANUAL_CALL_PROMOTION_OR_AUTORUN_REF:
            raise ValueError("DHC-OP03 blocked next step changed")
        if data.get("allow_implicit_op04_builder_fallback_input") is not True and not (
            data.get("dhc_op03_permission_input_forbidden_payload_key_path_refs")
            or data.get("dhc_op03_permission_input_body_like_value_path_refs")
            or data.get("dhc_op03_permission_input_promotion_claim_refs")
            or data.get("dhc_op03_permission_input_no_touch_mutation_path_refs")
        ):
            raise ValueError("DHC-OP03 blocked branch must record implicit fallback or scan refs")
    return True


# ---------------------------------------------------------------------------
# R4 / DHC-OP04〜OP05: controlled existing DHR-OP05 manual call and result
# classification.  This section is intentionally limited to the existing
# DHR-OP05 builder call boundary and the DHC-side stopped classification.
# It does not execute DHR-OP06, DHR-OP07, DMD, R52, actual review, P8, or
# release decisions.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHB_DHC_R4_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op00_op01_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op02_op03_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op04_op05_20260709.py",
)
P7_R54_AHR_POST_DHB_DHC_R4_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
)
P7_R54_AHR_POST_DHB_DHC_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)

P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_CLASSIFY_EXISTING_DHR_OP05_RESULT_REF: Final = (
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_NOT_CALLED_STOP_REF: Final = (
    "existing_DHR_OP05_preflight_scan_not_called_stop_before_builder_execution"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_CALL_REPAIR_REF: Final = (
    "repair_existing_DHR_OP05_preflight_scan_manual_call_boundary_without_DHR_OP06"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_BLOCKED_REF: Final = (
    "blocked_existing_DHR_OP05_manual_call_bodyfree_leak_promotion_or_autorun_without_DHR_OP06"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_SCAN_CLEAR_STOPPED_REF: Final = (
    "scan_clear_stopped_before_DHR_OP06_consideration_or_P7_readfeel_reconnection_boundary"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAITING_OR_INCOMPLETE_STOPPED_REF: Final = (
    "waiting_or_incomplete_stopped_collect_or_repair_explicit_actual_source_claim_without_P8_promotion"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_REQUIRED_STOPPED_REF: Final = (
    "repair_required_stopped_before_any_DHR_OP06_consideration"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_NOT_CALLED_STOPPED_REF: Final = (
    "not_called_stopped_wait_for_explicit_manual_call_request_and_explicit_DHR_OP04_material"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_STOPPED_REF: Final = (
    "blocked_stopped_repair_no_touch_no_promotion_violation"
)

P7_R54_AHR_POST_DHB_DHC_OP04_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key not in {
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
        "dhc_op04_implemented",
        "existing_dhr_op04_assert_called_here",
        "manual_call_requested_here",
        "manual_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_result_present",
        "existing_dhr_op05_contract_valid",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
    }
)
P7_R54_AHR_POST_DHB_DHC_OP05_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key not in {
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
        "dhc_op04_implemented",
        "dhc_op05_implemented",
        "existing_dhr_op04_assert_called_here",
        "manual_call_requested_here",
        "manual_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_result_present",
        "existing_dhr_op05_contract_valid",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
    }
)

P7_R54_AHR_POST_DHB_DHC_OP04_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op03_material_present",
    "op03_contract_valid",
    "op03_schema_version",
    "op03_material_ref",
    "op03_status_ref",
    "op03_next_required_step",
    "op03_manual_call_allowed",
    "op03_existing_dhr_op05_builder_call_allowed_here",
    "op03_permission_allows_dhc_op04_manual_call",
    "manual_call_requested",
    "manual_call_requested_here",
    "manual_call_request_ref",
    "manual_call_request_ref_present",
    "allow_existing_dhr_op05_builder_call_input",
    "allow_implicit_op04_builder_fallback_input",
    "implicit_op04_builder_fallback_allowed_here",
    "implicit_op04_builder_fallback_used_here",
    "explicit_dhr_op04_actual_source_claim_separation_required",
    "explicit_dhr_op04_material_present",
    "explicit_dhr_op04_schema_version",
    "explicit_dhr_op04_operation_step_ref",
    "explicit_dhr_op04_material_ref",
    "explicit_dhr_op04_status_ref",
    "explicit_dhr_op04_contract_valid",
    "explicit_dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan",
    "existing_dhr_op04_assert_called_here",
    "existing_dhr_op04_assert_failure_ref",
    "dhr_op04_builder_called_here",
    "existing_dhr_op05_builder_ref",
    "existing_dhr_op05_builder_import_path_ref",
    "existing_dhr_op05_assert_ref",
    "existing_dhr_op05_assert_import_path_ref",
    "existing_dhr_op05_builder_call_allowed_here",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_builder_called_count",
    "existing_dhr_op05_assert_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
    "existing_dhr_op05_status_ref",
    "existing_dhr_op05_preflight_scan_passed",
    "existing_dhr_op05_preflight_repair_required",
    "existing_dhr_op05_preflight_waiting_or_incomplete",
    "existing_dhr_op05_next_required_step",
    "existing_dhr_op05_builder_exception_type_ref",
    "existing_dhr_op05_assert_exception_type_ref",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_call_allowed_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_r52_execution_allowed_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_allowed_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "release_decision_allowed_here",
    "api_db_rn_runtime_response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "dhc_op04_call_input_forbidden_payload_key_path_refs",
    "dhc_op04_call_input_forbidden_payload_key_path_count",
    "dhc_op04_call_input_body_like_value_path_refs",
    "dhc_op04_call_input_body_like_value_path_count",
    "dhc_op04_call_input_promotion_claim_refs",
    "dhc_op04_call_input_promotion_claim_ref_count",
    "dhc_op04_call_input_no_touch_mutation_path_refs",
    "dhc_op04_call_input_no_touch_mutation_path_count",
    "dhc_op04_status_ref",
    "bodyfree_existing_dhr_op05_preflight_scan_manual_call_status_ref",
    "dhc_op04_allowed_status_refs",
    "dhc_op04_allowed_status_ref_count",
    "dhc_op04_existing_dhr_op05_preflight_scan_called_bodyfree",
    "dhc_op04_existing_dhr_op05_preflight_scan_not_called_stopped",
    "dhc_op04_existing_dhr_op05_preflight_scan_call_repair_required",
    "dhc_op04_existing_dhr_op05_preflight_scan_call_blocked",
    "dhc_op04_reason_refs",
    "dhc_op04_reason_ref_count",
    "dhc_op04_blocker_refs",
    "dhc_op04_blocker_ref_count",
    "dhc_op04_does_not_call_dhr_op06",
    "dhc_op04_does_not_execute_dmd_r52_or_release",
    "dhc_op04_does_not_start_actual_review",
    "dhc_op04_does_not_create_actual_rows",
    "dhc_op04_does_not_create_question_need_observation_rows",
    "dhc_op04_does_not_start_p8_question_design",
    "dhc_op04_does_not_change_api_db_rn_runtime_response_key",
    "dhc_op04_does_not_materialize_question_text",
    "dhc_op04_does_not_create_json_schema_file",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "target_test_ref_refs",
    "compileall_target_ref_refs",
    "public_contract",
    "dhc_no_touch_contract",
    "body_free_markers",
    "dhc_op00_implemented",
    "dhc_op01_implemented",
    "dhc_op02_implemented",
    "dhc_op03_implemented",
    "dhc_op04_implemented",
    "dhc_op05_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP05_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op04_material_present",
    "op04_contract_valid",
    "op04_schema_version",
    "op04_material_ref",
    "op04_status_ref",
    "op04_next_required_step",
    "op04_existing_dhr_op05_builder_called_here",
    "op04_existing_dhr_op05_result_present",
    "op04_existing_dhr_op05_contract_valid",
    "op04_existing_dhr_op05_status_ref",
    "op04_dhc_op04_blocked",
    "explicit_existing_dhr_op05_result_present",
    "explicit_existing_dhr_op05_result_contract_valid",
    "existing_dhr_op05_schema_version_ref",
    "existing_dhr_op05_material_ref",
    "existing_dhr_op05_status_ref",
    "existing_dhr_op05_preflight_scan_passed",
    "existing_dhr_op05_preflight_repair_required",
    "existing_dhr_op05_preflight_waiting_or_incomplete",
    "existing_dhr_op05_next_required_step",
    "existing_dhr_op05_next_required_step_is_not_dhc_execution_permission",
    "dhc_result_classification_ref",
    "bodyfree_existing_dhr_op05_result_classification_ref",
    "dhc_op05_result_classification_refs",
    "dhc_op05_result_classification_ref_count",
    "dhc_op05_scan_clear_stopped",
    "dhc_op05_waiting_or_incomplete_stopped",
    "dhc_op05_repair_required_stopped",
    "dhc_op05_not_called_stopped",
    "dhc_op05_blocked_stopped",
    "dhr_op05_call_attempted",
    "existing_dhr_op05_builder_called_here",
    "existing_dhr_op05_result_present",
    "existing_dhr_op05_contract_valid",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_call_allowed_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_r52_execution_allowed_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_question_design_allowed_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "release_decision_allowed_here",
    "api_db_rn_runtime_response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "dhc_op05_does_not_call_existing_dhr_op05_builder_again",
    "dhc_op05_does_not_call_dhr_op06",
    "dhc_op05_does_not_execute_dmd_r52_or_release",
    "dhc_op05_does_not_start_actual_review",
    "dhc_op05_does_not_create_actual_rows",
    "dhc_op05_does_not_create_question_need_observation_rows",
    "dhc_op05_does_not_start_p8_question_design",
    "dhc_op05_does_not_change_api_db_rn_runtime_response_key",
    "dhc_op05_does_not_materialize_question_text",
    "dhc_op05_does_not_create_json_schema_file",
    "dhc_op05_reason_refs",
    "dhc_op05_reason_ref_count",
    "dhc_op05_blocker_refs",
    "dhc_op05_blocker_ref_count",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "target_test_ref_refs",
    "compileall_target_ref_refs",
    "public_contract",
    "dhc_no_touch_contract",
    "body_free_markers",
    "dhc_op00_implemented",
    "dhc_op01_implemented",
    "dhc_op02_implemented",
    "dhc_op03_implemented",
    "dhc_op04_implemented",
    "dhc_op05_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP04_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP04_REQUIRED_FALSE_FLAG_REFS)
)
P7_R54_AHR_POST_DHB_DHC_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP05_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP05_REQUIRED_FALSE_FLAG_REFS)
)


def _op03_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op03_manual_call_permission_gate_contract(data)
    except ValueError:
        return False
    return True


def _op04_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op04_existing_dhr_op05_preflight_scan_manual_call_boundary_contract(data)
    except ValueError:
        return False
    return True


def _existing_dhr_op05_contract_valid(data: Any) -> tuple[bool, bool, str]:
    if not isinstance(data, Mapping):
        return False, False, "existing_dhr_op05_result_missing"
    called = True
    try:
        getattr(dhr, P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF)(data)
    except Exception as exc:  # noqa: BLE001 - body-free sanitized exception type only.
        return False, called, _clean_ref(type(exc).__name__, default="existing_dhr_op05_assert_failed", max_length=120)
    return True, called, "none"


def _dhc_op04_manual_call_context_material(*, review_session_id: str, manual_call_request_ref: str) -> dict[str, Any]:
    return {
        "schema_version": "cocolon.emlis.p7_r54.ahr.post_dhb.dhc.op04_manual_call_context.bodyfree.v1",
        "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
        "material_id": "p7_r54_ahr_post_dhb_dhc_op04_manual_call_context_20260709",
        "review_session_id": review_session_id,
        "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
        "manual_call_request_ref": manual_call_request_ref,
        "body_free": True,
        "implicit_op04_builder_fallback_allowed_here": False,
        "implicit_op04_builder_fallback_used_here": False,
        "dhr_op06_called_here": False,
        "dmd_execution_started_here": False,
        "p8_question_design_started": False,
        "release_allowed": False,
    }


def _dhc_op04_status(
    *,
    scan_blocked: bool,
    op03_valid: bool,
    op03_allows_call: bool,
    explicit_present: bool,
    explicit_contract_valid: bool,
    explicit_ready_for_scan: bool,
    allow_implicit_op04_builder_fallback: bool,
    builder_attempted: bool,
    existing_result_present: bool,
    existing_contract_valid: bool,
) -> tuple[str, list[str], list[str], str]:
    if scan_blocked or allow_implicit_op04_builder_fallback:
        blockers = ["blocked_existing_DHR_OP05_manual_call_bodyfree_leak_promotion_or_autorun"]
        if allow_implicit_op04_builder_fallback:
            blockers.append("implicit_DHR_OP04_builder_fallback_request_blocked")
        return (
            P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[3],
            ["DHC_OP04_bodyfree_or_implicit_fallback_guard_blocked_manual_call"],
            _dedupe_clean_refs(blockers, max_length=260),
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_BLOCKED_REF,
        )
    if not op03_valid:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[2],
            ["DHC_OP03_permission_material_invalid_before_manual_call"],
            ["repair_DHC_OP03_permission_material_without_existing_DHR_OP05_builder_call"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_CALL_REPAIR_REF,
        )
    if not op03_allows_call:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[1],
            ["DHC_OP03_manual_call_permission_not_allowed"],
            ["stop_before_existing_DHR_OP05_builder_call"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_NOT_CALLED_STOP_REF,
        )
    if not explicit_present:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[1],
            ["explicit_DHR_OP04_actual_source_claim_separation_missing"],
            ["do_not_call_existing_DHR_OP05_builder_without_explicit_OP04_material"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_NOT_CALLED_STOPPED_REF,
        )
    if not explicit_contract_valid or not explicit_ready_for_scan:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[2],
            ["explicit_DHR_OP04_actual_source_claim_separation_invalid_or_not_ready"],
            ["repair_explicit_DHR_OP04_material_before_existing_DHR_OP05_builder_call"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_CALL_REPAIR_REF,
        )
    if not builder_attempted or not existing_result_present or not existing_contract_valid:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[2],
            ["existing_DHR_OP05_builder_call_attempt_failed_or_contract_invalid"],
            ["repair_existing_DHR_OP05_builder_call_result_without_traceback_or_raw_exception"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_CALL_REPAIR_REF,
        )
    return (
        P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[0],
        ["existing_DHR_OP05_preflight_scan_called_once_with_explicit_OP04_material"],
        [],
        P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    )


def _dhc_op05_classification(
    *,
    op04_blocked: bool,
    op04_repair: bool,
    existing_result_present: bool,
    existing_contract_valid: bool,
    existing_status_ref: str,
) -> tuple[str, list[str], list[str], str]:
    if op04_blocked:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[4],
            ["DHC_OP04_blocked_before_or_during_existing_DHR_OP05_manual_call"],
            ["repair_no_touch_no_promotion_violation_before_any_downstream_consideration"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_STOPPED_REF,
        )
    if not existing_result_present:
        if op04_repair:
            return (
                P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2],
                ["DHC_OP04_manual_call_boundary_requires_repair_before_result_classification"],
                ["repair_existing_DHR_OP05_call_boundary_without_DHR_OP06"],
                P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_REQUIRED_STOPPED_REF,
            )
        return (
            P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[3],
            ["existing_DHR_OP05_preflight_scan_not_called"],
            ["wait_for_explicit_manual_call_request_and_explicit_DHR_OP04_material"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_NOT_CALLED_STOPPED_REF,
        )
    if not existing_contract_valid:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2],
            ["existing_DHR_OP05_result_contract_invalid"],
            ["repair_existing_DHR_OP05_result_contract_without_traceback_or_raw_output"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_REQUIRED_STOPPED_REF,
        )
    if existing_status_ref == P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0],
            ["existing_DHR_OP05_preflight_scan_clear_recorded_and_stopped"],
            [],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_SCAN_CLEAR_STOPPED_REF,
        )
    if existing_status_ref == P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_WAITING_OR_INCOMPLETE_STATUS_REF:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[1],
            ["existing_DHR_OP05_preflight_scan_waiting_or_incomplete_recorded_and_stopped"],
            ["explicit_actual_source_claim_still_missing_or_incomplete"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAITING_OR_INCOMPLETE_STOPPED_REF,
        )
    if existing_status_ref == P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_REPAIR_REQUIRED_STATUS_REF:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2],
            ["existing_DHR_OP05_preflight_scan_repair_required_recorded_and_stopped"],
            ["repair_bodyfree_leak_promotion_or_invalid_source_before_DHR_OP06_consideration"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_REQUIRED_STOPPED_REF,
        )
    return (
        P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2],
        ["existing_DHR_OP05_result_status_ref_unknown_or_not_allowed"],
        ["repair_existing_DHR_OP05_result_status_without_downstream_execution"],
        P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_REQUIRED_STOPPED_REF,
    )


def build_p7_r54_ahr_post_dhb_dhc_op04_existing_dhr_op05_preflight_scan_manual_call_boundary(
    op03_manual_call_permission: Mapping[str, Any] | None = None,
    explicit_dhr_op04_actual_source_claim_separation: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
    allow_implicit_op04_builder_fallback: bool = False,
) -> dict[str, Any]:
    """Call the existing DHR-OP05 builder only inside DHC-OP04 when permission is explicit."""

    op03 = op03_manual_call_permission
    op03_present = isinstance(op03, Mapping)
    op03_valid = _op03_valid(op03)
    op03_status_ref = _clean_ref(op03.get("dhc_op03_status_ref") if op03_present else None, default="op03_status_missing", max_length=320)
    op03_allows_call = bool(
        op03_valid
        and op03_status_ref == P7_R54_AHR_POST_DHB_DHC_OP03_ALLOWED_STATUS_REFS[0]
        and op03.get("manual_call_allowed") is True
        and op03.get("existing_dhr_op05_builder_call_allowed_here") is True
        and op03.get("allow_implicit_op04_builder_fallback_input") is False
    )
    explicit_op04 = explicit_dhr_op04_actual_source_claim_separation
    explicit_present = isinstance(explicit_op04, Mapping)
    manual_call_request_ref = _clean_ref(
        op03.get("manual_call_request_ref") if op03_present else None,
        default="manual_call_request_ref_missing",
        max_length=260,
    )
    session_id = _safe_review_session_id(review_session_id or (op03.get("review_session_id") if op03_present else None))
    scan_root = {
        "op03_manual_call_permission": op03 if op03_present else {},
        "explicit_dhr_op04_actual_source_claim_separation": explicit_op04 if explicit_present else {},
        "allow_implicit_op04_builder_fallback": allow_implicit_op04_builder_fallback,
    }
    forbidden_paths = _scan_forbidden_payload_key_paths(scan_root, path="dhc_op04_call_input")
    body_like_paths = _scan_body_like_value_paths(scan_root, path="dhc_op04_call_input")
    # OP03 permission flags are expected to be true on the allowed branch, so
    # OP04 promotion scanning only treats the explicit OP04 material and an
    # explicit implicit-fallback request as promotion/blocking material.
    promotion_scan_root = {
        "explicit_dhr_op04_actual_source_claim_separation": explicit_op04 if explicit_present else {},
    }
    promotion_values = (
        _scan_promotion_claim_paths(promotion_scan_root, path="dhc_op04_call_input")
        + _dhr_op04_promotion_claim_paths(promotion_scan_root, path="dhc_op04_call_input")
    )
    if allow_implicit_op04_builder_fallback:
        promotion_values.append("dhc_op04_call_input.allow_implicit_op04_builder_fallback")
    promotion_paths = _dedupe_clean_refs(promotion_values, max_length=360)
    no_touch_paths = _scan_no_touch_mutation_paths(scan_root, path="dhc_op04_call_input")
    scan_blocked = bool(forbidden_paths or body_like_paths or promotion_paths or no_touch_paths)
    explicit_schema = _clean_ref(explicit_op04.get("schema_version") if explicit_present else None, default="dhr_op04_schema_missing", max_length=320)
    explicit_step = _clean_ref(explicit_op04.get("operation_step_ref") if explicit_present else None, default="dhr_op04_step_missing", max_length=320)
    explicit_material_ref = _clean_ref(explicit_op04.get("material_id") if explicit_present else None, default="dhr_op04_material_missing", max_length=320)
    explicit_status = _clean_ref(explicit_op04.get("dhr_op04_status_ref") if explicit_present else None, default="dhr_op04_status_missing", max_length=320)
    explicit_ready_for_scan = bool(
        explicit_present and explicit_op04.get("dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan") is True
    )
    explicit_shaped_valid = bool(
        explicit_present
        and explicit_schema == P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_SCHEMA_VERSION_REF
        and explicit_step == P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_STEP_REF
        and explicit_op04.get("body_free") is True
        and explicit_status in P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP04_ALLOWED_STATUS_REFS
    )
    explicit_contract_valid = False
    existing_dhr_op04_assert_called_here = False
    existing_dhr_op04_assert_failure_ref = "explicit_dhr_op04_material_missing"
    if explicit_present and not scan_blocked:
        contract_valid, existing_dhr_op04_assert_called_here, existing_dhr_op04_assert_failure_ref = _dhr_op04_contract_valid(explicit_op04)
        explicit_contract_valid = bool(explicit_shaped_valid and contract_valid)
    builder_called = False
    builder_called_count = 0
    assert_called = False
    existing_result_present = False
    existing_contract_valid = False
    existing_status_ref = P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_NOT_CALLED_STATUS_REF
    existing_preflight_scan_passed = False
    existing_preflight_repair_required = False
    existing_preflight_waiting_or_incomplete = False
    existing_next_required_step = "existing_dhr_op05_next_step_missing"
    builder_exception_type_ref = "none"
    assert_exception_type_ref = "none"
    builder_result: dict[str, Any] | None = None
    may_call_builder = bool(
        not scan_blocked
        and not allow_implicit_op04_builder_fallback
        and op03_allows_call
        and explicit_present
        and explicit_contract_valid
        and explicit_ready_for_scan
    )
    if may_call_builder:
        builder_called = True
        builder_called_count = 1
        try:
            builder_result = getattr(dhr, P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF)(
                actual_source_claim_separation=explicit_op04,
                additional_bodyfree_materials=[
                    _dhc_op04_manual_call_context_material(
                        review_session_id=session_id,
                        manual_call_request_ref=manual_call_request_ref,
                    )
                ],
                review_session_id=session_id,
            )
            existing_result_present = isinstance(builder_result, Mapping)
        except Exception as exc:  # noqa: BLE001 - body-free sanitized exception type only.
            builder_result = None
            existing_result_present = False
            builder_exception_type_ref = _clean_ref(type(exc).__name__, default="existing_dhr_op05_builder_failed", max_length=120)
        if isinstance(builder_result, Mapping):
            assert_called = True
            try:
                getattr(dhr, P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF)(builder_result)
                existing_contract_valid = True
            except Exception as exc:  # noqa: BLE001 - body-free sanitized exception type only.
                existing_contract_valid = False
                assert_exception_type_ref = _clean_ref(type(exc).__name__, default="existing_dhr_op05_assert_failed", max_length=120)
            existing_status_ref = _clean_ref(
                builder_result.get("dhr_op05_status_ref"),
                default=P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_CONTRACT_INVALID_STATUS_REF,
                max_length=320,
            )
            existing_preflight_scan_passed = bool(builder_result.get("preflight_scan_passed") is True)
            existing_preflight_repair_required = bool(builder_result.get("preflight_repair_required") is True)
            existing_preflight_waiting_or_incomplete = bool(builder_result.get("preflight_waiting_or_incomplete") is True)
            existing_next_required_step = _clean_ref(builder_result.get("next_required_step"), default="existing_dhr_op05_next_step_missing", max_length=320)
    status_ref, reasons, blockers, next_required_step = _dhc_op04_status(
        scan_blocked=scan_blocked,
        op03_valid=op03_valid,
        op03_allows_call=op03_allows_call,
        explicit_present=explicit_present,
        explicit_contract_valid=explicit_contract_valid,
        explicit_ready_for_scan=explicit_ready_for_scan,
        allow_implicit_op04_builder_fallback=allow_implicit_op04_builder_fallback,
        builder_attempted=builder_called,
        existing_result_present=existing_result_present,
        existing_contract_valid=existing_contract_valid,
    )
    called_bodyfree = status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[0]
    not_called = status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[1]
    repair = status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[2]
    blocked = status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[3]
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers)
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP04_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP04_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op04_existing_dhr_op05_preflight_scan_manual_call_boundary_20260709",
            "review_session_id": session_id,
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op03_material_present": op03_present,
            "op03_contract_valid": op03_valid,
            "op03_schema_version": _clean_ref(op03.get("schema_version") if op03_present else None, default="op03_schema_missing", max_length=320),
            "op03_material_ref": _clean_ref(op03.get("material_id") if op03_present else None, default="op03_material_missing", max_length=320),
            "op03_status_ref": op03_status_ref,
            "op03_next_required_step": _clean_ref(op03.get("next_required_step") if op03_present else None, default="op03_next_step_missing", max_length=320),
            "op03_manual_call_allowed": bool(op03_present and op03.get("manual_call_allowed") is True),
            "op03_existing_dhr_op05_builder_call_allowed_here": bool(op03_present and op03.get("existing_dhr_op05_builder_call_allowed_here") is True),
            "op03_permission_allows_dhc_op04_manual_call": op03_allows_call,
            "manual_call_requested": bool(op03_present and op03.get("manual_call_requested") is True),
            "manual_call_requested_here": bool(op03_present and op03.get("manual_call_requested_here") is True),
            "manual_call_request_ref": manual_call_request_ref,
            "manual_call_request_ref_present": manual_call_request_ref != "manual_call_request_ref_missing",
            "allow_existing_dhr_op05_builder_call_input": bool(op03_present and op03.get("allow_existing_dhr_op05_builder_call_input") is True),
            "allow_implicit_op04_builder_fallback_input": allow_implicit_op04_builder_fallback,
            "implicit_op04_builder_fallback_allowed_here": False,
            "implicit_op04_builder_fallback_used_here": False,
            "explicit_dhr_op04_actual_source_claim_separation_required": True,
            "explicit_dhr_op04_material_present": explicit_present,
            "explicit_dhr_op04_schema_version": explicit_schema,
            "explicit_dhr_op04_operation_step_ref": explicit_step,
            "explicit_dhr_op04_material_ref": explicit_material_ref,
            "explicit_dhr_op04_status_ref": explicit_status,
            "explicit_dhr_op04_contract_valid": explicit_contract_valid,
            "explicit_dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan": explicit_ready_for_scan,
            "existing_dhr_op04_assert_called_here": existing_dhr_op04_assert_called_here,
            "existing_dhr_op04_assert_failure_ref": existing_dhr_op04_assert_failure_ref,
            "dhr_op04_builder_called_here": False,
            "existing_dhr_op05_builder_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF,
            "existing_dhr_op05_builder_import_path_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_PATH_REF,
            "existing_dhr_op05_assert_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_REF,
            "existing_dhr_op05_assert_import_path_ref": P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ASSERT_IMPORT_PATH_REF,
            "existing_dhr_op05_builder_call_allowed_here": may_call_builder,
            "existing_dhr_op05_builder_called_here": builder_called,
            "existing_dhr_op05_builder_called_count": builder_called_count,
            "existing_dhr_op05_assert_called_here": assert_called,
            "existing_dhr_op05_result_present": existing_result_present,
            "existing_dhr_op05_contract_valid": existing_contract_valid,
            "existing_dhr_op05_status_ref": existing_status_ref,
            "existing_dhr_op05_preflight_scan_passed": existing_preflight_scan_passed,
            "existing_dhr_op05_preflight_repair_required": existing_preflight_repair_required,
            "existing_dhr_op05_preflight_waiting_or_incomplete": existing_preflight_waiting_or_incomplete,
            "existing_dhr_op05_next_required_step": existing_next_required_step,
            "existing_dhr_op05_builder_exception_type_ref": builder_exception_type_ref,
            "existing_dhr_op05_assert_exception_type_ref": assert_exception_type_ref,
            "dhr_op05_called_here": builder_called,
            "dhr_op05_builder_called_here": builder_called,
            "dhr_op06_call_allowed_here": False,
            "dhr_op06_called_here": False,
            "dhr_op07_materialized_here": False,
            "dmd_r52_execution_allowed_here": False,
            "dmd_execution_started_here": False,
            "dmd_r52_executed_here": False,
            "actual_review_started_here": False,
            "actual_rows_created_here": False,
            "question_need_observation_rows_created_here": False,
            "p8_question_design_allowed_here": False,
            "p8_question_design_started": False,
            "p8_question_implementation_started": False,
            "question_text_materialized_here": False,
            "release_decision_allowed_here": False,
            "api_db_rn_runtime_response_key_changed": False,
            "json_schema_file_created_here": False,
            "p7_complete": False,
            "release_allowed": False,
            "dhc_op04_call_input_forbidden_payload_key_path_refs": list(forbidden_paths),
            "dhc_op04_call_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "dhc_op04_call_input_body_like_value_path_refs": list(body_like_paths),
            "dhc_op04_call_input_body_like_value_path_count": len(body_like_paths),
            "dhc_op04_call_input_promotion_claim_refs": list(promotion_paths),
            "dhc_op04_call_input_promotion_claim_ref_count": len(promotion_paths),
            "dhc_op04_call_input_no_touch_mutation_path_refs": list(no_touch_paths),
            "dhc_op04_call_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhc_op04_status_ref": status_ref,
            "bodyfree_existing_dhr_op05_preflight_scan_manual_call_status_ref": status_ref,
            "dhc_op04_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS,
            "dhc_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS),
            "dhc_op04_existing_dhr_op05_preflight_scan_called_bodyfree": called_bodyfree,
            "dhc_op04_existing_dhr_op05_preflight_scan_not_called_stopped": not_called,
            "dhc_op04_existing_dhr_op05_preflight_scan_call_repair_required": repair,
            "dhc_op04_existing_dhr_op05_preflight_scan_call_blocked": blocked,
            "dhc_op04_reason_refs": reason_refs,
            "dhc_op04_reason_ref_count": reason_count,
            "dhc_op04_blocker_refs": blocker_refs,
            "dhc_op04_blocker_ref_count": blocker_count,
            "dhc_op04_does_not_call_dhr_op06": True,
            "dhc_op04_does_not_execute_dmd_r52_or_release": True,
            "dhc_op04_does_not_start_actual_review": True,
            "dhc_op04_does_not_create_actual_rows": True,
            "dhc_op04_does_not_create_question_need_observation_rows": True,
            "dhc_op04_does_not_start_p8_question_design": True,
            "dhc_op04_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op04_does_not_materialize_question_text": True,
            "dhc_op04_does_not_create_json_schema_file": True,
            "claim_boundary_refs": P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS,
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS,
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS,
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP04_IMPLEMENTED_STEPS,
            "not_yet_implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP04_NOT_YET_IMPLEMENTED_STEPS,
            "target_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R4_TARGET_TEST_REF_REFS,
            "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_R4_COMPILEALL_TARGET_REF_REFS,
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "dhc_op01_implemented": True,
            "dhc_op02_implemented": True,
            "dhc_op03_implemented": True,
            "dhc_op04_implemented": True,
            "dhc_op05_implemented": False,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op04_existing_dhr_op05_preflight_scan_manual_call_boundary_contract(
    data: Mapping[str, Any],
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHB-DHC-OP04")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP04 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP04_SCHEMA_VERSION:
        raise ValueError("DHC-OP04 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF:
        raise ValueError("DHC-OP04 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP04 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP04 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP04 must remain body-free")
    for key in (
        "dhc_op04_does_not_call_dhr_op06",
        "dhc_op04_does_not_execute_dmd_r52_or_release",
        "dhc_op04_does_not_start_actual_review",
        "dhc_op04_does_not_create_actual_rows",
        "dhc_op04_does_not_create_question_need_observation_rows",
        "dhc_op04_does_not_start_p8_question_design",
        "dhc_op04_does_not_change_api_db_rn_runtime_response_key",
        "dhc_op04_does_not_materialize_question_text",
        "dhc_op04_does_not_create_json_schema_file",
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
        "dhc_op04_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP04 required true field changed: {key}")
    if data.get("dhc_op05_implemented") is not False:
        raise ValueError("DHC-OP04 must stop before OP05 implementation marker")
    for key in (
        "implicit_op04_builder_fallback_allowed_here",
        "implicit_op04_builder_fallback_used_here",
        "dhr_op06_call_allowed_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_r52_execution_allowed_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_allowed_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "release_decision_allowed_here",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created_here",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP04 forbidden downstream flag changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP04_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP04 required false flag changed: {key}")
    for field, count_field in (
        ("dhc_op04_call_input_forbidden_payload_key_path_refs", "dhc_op04_call_input_forbidden_payload_key_path_count"),
        ("dhc_op04_call_input_body_like_value_path_refs", "dhc_op04_call_input_body_like_value_path_count"),
        ("dhc_op04_call_input_promotion_claim_refs", "dhc_op04_call_input_promotion_claim_ref_count"),
        ("dhc_op04_call_input_no_touch_mutation_path_refs", "dhc_op04_call_input_no_touch_mutation_path_count"),
        ("dhc_op04_reason_refs", "dhc_op04_reason_ref_count"),
        ("dhc_op04_blocker_refs", "dhc_op04_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP04 count field changed: {count_field}")
    if tuple(data.get("dhc_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP04 allowed status refs changed")
    if data.get("dhc_op04_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS):
        raise ValueError("DHC-OP04 allowed status count changed")
    if data.get("bodyfree_existing_dhr_op05_preflight_scan_manual_call_status_ref") != data.get("dhc_op04_status_ref"):
        raise ValueError("DHC-OP04 status alias changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP04_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP04 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R4_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP04 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R4_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP04 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP04 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP04 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP04 body-free marker changed")
    status_ref = data.get("dhc_op04_status_ref")
    flags = [
        data.get("dhc_op04_existing_dhr_op05_preflight_scan_called_bodyfree") is True,
        data.get("dhc_op04_existing_dhr_op05_preflight_scan_not_called_stopped") is True,
        data.get("dhc_op04_existing_dhr_op05_preflight_scan_call_repair_required") is True,
        data.get("dhc_op04_existing_dhr_op05_preflight_scan_call_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("DHC-OP04 must select exactly one branch")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[0]:
        for key in (
            "op03_contract_valid",
            "op03_permission_allows_dhc_op04_manual_call",
            "manual_call_requested",
            "manual_call_requested_here",
            "manual_call_request_ref_present",
            "allow_existing_dhr_op05_builder_call_input",
            "explicit_dhr_op04_material_present",
            "explicit_dhr_op04_contract_valid",
            "explicit_dhr_op04_ready_for_bodyfree_leak_promotion_claim_preflight_scan",
            "existing_dhr_op04_assert_called_here",
            "existing_dhr_op05_builder_call_allowed_here",
            "existing_dhr_op05_builder_called_here",
            "existing_dhr_op05_assert_called_here",
            "existing_dhr_op05_result_present",
            "existing_dhr_op05_contract_valid",
            "dhr_op05_called_here",
            "dhr_op05_builder_called_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"DHC-OP04 called branch true field missing: {key}")
        if data.get("existing_dhr_op05_builder_called_count") != 1:
            raise ValueError("DHC-OP04 called branch must call existing builder exactly once")
        if data.get("existing_dhr_op05_status_ref") not in P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_ALLOWED_STATUS_REFS:
            raise ValueError("DHC-OP04 called branch must carry existing DHR-OP05 status")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF:
            raise ValueError("DHC-OP04 called branch next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[1]:
        if data.get("existing_dhr_op05_builder_called_here") is not False or data.get("existing_dhr_op05_result_present") is not False:
            raise ValueError("DHC-OP04 not-called branch cannot call builder")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_CALL_REPAIR_REF:
            raise ValueError("DHC-OP04 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP04_BLOCKED_REF:
            raise ValueError("DHC-OP04 blocked next step changed")
        if data.get("existing_dhr_op05_builder_called_here") is not False:
            raise ValueError("DHC-OP04 blocked branch must not call builder")
    return True


def build_p7_r54_ahr_post_dhb_dhc_op05_existing_dhr_op05_result_classification(
    op04_existing_dhr_op05_preflight_scan_manual_call_boundary: Mapping[str, Any] | None = None,
    existing_dhr_op05_preflight_scan_result: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Classify an existing DHR-OP05 result and stop before DHR-OP06 or any downstream execution."""

    op04 = op04_existing_dhr_op05_preflight_scan_manual_call_boundary
    op04_present = isinstance(op04, Mapping)
    op04_valid = _op04_valid(op04)
    op04_status_ref = _clean_ref(op04.get("dhc_op04_status_ref") if op04_present else None, default="op04_status_missing", max_length=320)
    op04_blocked = op04_status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[3]
    op04_repair = op04_status_ref == P7_R54_AHR_POST_DHB_DHC_OP04_ALLOWED_STATUS_REFS[2]
    explicit_result_present = isinstance(existing_dhr_op05_preflight_scan_result, Mapping)
    result_from_explicit = existing_dhr_op05_preflight_scan_result if explicit_result_present else None
    existing_result_present = bool(
        explicit_result_present
        or (op04_valid and op04.get("existing_dhr_op05_result_present") is True)
    )
    explicit_contract_valid = False
    explicit_assert_called = False
    explicit_assert_failure_ref = "none"
    if explicit_result_present:
        explicit_contract_valid, explicit_assert_called, explicit_assert_failure_ref = _existing_dhr_op05_contract_valid(result_from_explicit)
    op04_existing_contract_valid = bool(op04_valid and op04.get("existing_dhr_op05_contract_valid") is True)
    existing_contract_valid = bool(explicit_contract_valid if explicit_result_present else op04_existing_contract_valid)
    existing_status_ref = _clean_ref(
        result_from_explicit.get("dhr_op05_status_ref") if isinstance(result_from_explicit, Mapping) else (op04.get("existing_dhr_op05_status_ref") if op04_present else None),
        default=P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_NOT_CALLED_STATUS_REF,
        max_length=320,
    )
    existing_material_ref = _clean_ref(
        result_from_explicit.get("material_id") if isinstance(result_from_explicit, Mapping) else (op04.get("existing_dhr_op05_material_ref") if op04_present else None),
        default="existing_dhr_op05_material_not_nested_in_dhc_op04",
        max_length=320,
    )
    existing_schema_ref = _clean_ref(
        result_from_explicit.get("schema_version") if isinstance(result_from_explicit, Mapping) else None,
        default=P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCHEMA_VERSION_REF if existing_result_present else "existing_dhr_op05_schema_missing",
        max_length=320,
    )
    existing_next_required_step = _clean_ref(
        result_from_explicit.get("next_required_step") if isinstance(result_from_explicit, Mapping) else (op04.get("existing_dhr_op05_next_required_step") if op04_present else None),
        default="existing_dhr_op05_next_step_missing",
        max_length=320,
    )
    preflight_scan_passed = bool(
        result_from_explicit.get("preflight_scan_passed") is True if isinstance(result_from_explicit, Mapping) else (op04.get("existing_dhr_op05_preflight_scan_passed") is True if op04_present else False)
    )
    preflight_repair_required = bool(
        result_from_explicit.get("preflight_repair_required") is True if isinstance(result_from_explicit, Mapping) else (op04.get("existing_dhr_op05_preflight_repair_required") is True if op04_present else False)
    )
    preflight_waiting_or_incomplete = bool(
        result_from_explicit.get("preflight_waiting_or_incomplete") is True if isinstance(result_from_explicit, Mapping) else (op04.get("existing_dhr_op05_preflight_waiting_or_incomplete") is True if op04_present else False)
    )
    classification_ref, reasons, blockers, next_required_step = _dhc_op05_classification(
        op04_blocked=op04_blocked,
        op04_repair=op04_repair,
        existing_result_present=existing_result_present,
        existing_contract_valid=existing_contract_valid,
        existing_status_ref=existing_status_ref,
    )
    scan_clear = classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]
    waiting = classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[1]
    repair = classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2]
    not_called = classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[3]
    blocked = classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[4]
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers)
    session_id = _safe_review_session_id(review_session_id or (op04.get("review_session_id") if op04_present else None))
    dhr_op05_call_attempted = bool(op04_present and op04.get("existing_dhr_op05_builder_called_here") is True)
    builder_called_here = dhr_op05_call_attempted
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP05_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP05_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op05_existing_dhr_op05_result_classification_20260709",
            "review_session_id": session_id,
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op04_material_present": op04_present,
            "op04_contract_valid": op04_valid,
            "op04_schema_version": _clean_ref(op04.get("schema_version") if op04_present else None, default="op04_schema_missing", max_length=320),
            "op04_material_ref": _clean_ref(op04.get("material_id") if op04_present else None, default="op04_material_missing", max_length=320),
            "op04_status_ref": op04_status_ref,
            "op04_next_required_step": _clean_ref(op04.get("next_required_step") if op04_present else None, default="op04_next_step_missing", max_length=320),
            "op04_existing_dhr_op05_builder_called_here": builder_called_here,
            "op04_existing_dhr_op05_result_present": bool(op04_present and op04.get("existing_dhr_op05_result_present") is True),
            "op04_existing_dhr_op05_contract_valid": op04_existing_contract_valid,
            "op04_existing_dhr_op05_status_ref": _clean_ref(op04.get("existing_dhr_op05_status_ref") if op04_present else None, default="op04_existing_status_missing", max_length=320),
            "op04_dhc_op04_blocked": op04_blocked,
            "explicit_existing_dhr_op05_result_present": explicit_result_present,
            "explicit_existing_dhr_op05_result_contract_valid": explicit_contract_valid,
            "existing_dhr_op05_schema_version_ref": existing_schema_ref,
            "existing_dhr_op05_material_ref": existing_material_ref,
            "existing_dhr_op05_status_ref": existing_status_ref,
            "existing_dhr_op05_preflight_scan_passed": preflight_scan_passed,
            "existing_dhr_op05_preflight_repair_required": preflight_repair_required,
            "existing_dhr_op05_preflight_waiting_or_incomplete": preflight_waiting_or_incomplete,
            "existing_dhr_op05_next_required_step": existing_next_required_step,
            "existing_dhr_op05_next_required_step_is_not_dhc_execution_permission": True,
            "dhc_result_classification_ref": classification_ref,
            "bodyfree_existing_dhr_op05_result_classification_ref": classification_ref,
            "dhc_op05_result_classification_refs": P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS,
            "dhc_op05_result_classification_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS),
            "dhc_op05_scan_clear_stopped": scan_clear,
            "dhc_op05_waiting_or_incomplete_stopped": waiting,
            "dhc_op05_repair_required_stopped": repair,
            "dhc_op05_not_called_stopped": not_called,
            "dhc_op05_blocked_stopped": blocked,
            "dhr_op05_call_attempted": dhr_op05_call_attempted,
            "existing_dhr_op05_builder_called_here": builder_called_here,
            "existing_dhr_op05_result_present": existing_result_present,
            "existing_dhr_op05_contract_valid": existing_contract_valid,
            "dhr_op05_called_here": builder_called_here,
            "dhr_op05_builder_called_here": builder_called_here,
            "dhr_op06_call_allowed_here": False,
            "dhr_op06_called_here": False,
            "dhr_op07_materialized_here": False,
            "dmd_r52_execution_allowed_here": False,
            "dmd_execution_started_here": False,
            "dmd_r52_executed_here": False,
            "actual_review_started_here": False,
            "actual_rows_created_here": False,
            "question_need_observation_rows_created_here": False,
            "p8_question_design_allowed_here": False,
            "p8_question_design_started": False,
            "p8_question_implementation_started": False,
            "question_text_materialized_here": False,
            "release_decision_allowed_here": False,
            "api_db_rn_runtime_response_key_changed": False,
            "json_schema_file_created_here": False,
            "p7_complete": False,
            "release_allowed": False,
            "dhc_op05_does_not_call_existing_dhr_op05_builder_again": True,
            "dhc_op05_does_not_call_dhr_op06": True,
            "dhc_op05_does_not_execute_dmd_r52_or_release": True,
            "dhc_op05_does_not_start_actual_review": True,
            "dhc_op05_does_not_create_actual_rows": True,
            "dhc_op05_does_not_create_question_need_observation_rows": True,
            "dhc_op05_does_not_start_p8_question_design": True,
            "dhc_op05_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op05_does_not_materialize_question_text": True,
            "dhc_op05_does_not_create_json_schema_file": True,
            "dhc_op05_reason_refs": reason_refs,
            "dhc_op05_reason_ref_count": reason_count,
            "dhc_op05_blocker_refs": blocker_refs,
            "dhc_op05_blocker_ref_count": blocker_count,
            "claim_boundary_refs": P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS,
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS,
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS,
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP05_IMPLEMENTED_STEPS,
            "not_yet_implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP05_NOT_YET_IMPLEMENTED_STEPS,
            "target_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R4_TARGET_TEST_REF_REFS,
            "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_R4_COMPILEALL_TARGET_REF_REFS,
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "dhc_op01_implemented": True,
            "dhc_op02_implemented": True,
            "dhc_op03_implemented": True,
            "dhc_op04_implemented": True,
            "dhc_op05_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    # Keep sanitized explicit assert failure visible only as a safe category when an explicit
    # result was supplied; it is intentionally not part of the public contract surface.
    _ = explicit_assert_called, explicit_assert_failure_ref
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op05_existing_dhr_op05_result_classification_contract(
    data: Mapping[str, Any],
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHB-DHC-OP05")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP05 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP05_SCHEMA_VERSION:
        raise ValueError("DHC-OP05 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF:
        raise ValueError("DHC-OP05 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP05 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP05 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP05 must remain body-free")
    for key in (
        "existing_dhr_op05_next_required_step_is_not_dhc_execution_permission",
        "dhc_op05_does_not_call_existing_dhr_op05_builder_again",
        "dhc_op05_does_not_call_dhr_op06",
        "dhc_op05_does_not_execute_dmd_r52_or_release",
        "dhc_op05_does_not_start_actual_review",
        "dhc_op05_does_not_create_actual_rows",
        "dhc_op05_does_not_create_question_need_observation_rows",
        "dhc_op05_does_not_start_p8_question_design",
        "dhc_op05_does_not_change_api_db_rn_runtime_response_key",
        "dhc_op05_does_not_materialize_question_text",
        "dhc_op05_does_not_create_json_schema_file",
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
        "dhc_op04_implemented",
        "dhc_op05_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP05 required true field changed: {key}")
    for key in (
        "dhr_op06_call_allowed_here",
        "dhr_op06_called_here",
        "dhr_op07_materialized_here",
        "dmd_r52_execution_allowed_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_allowed_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "release_decision_allowed_here",
        "api_db_rn_runtime_response_key_changed",
        "json_schema_file_created_here",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP05 forbidden downstream flag changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP05_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP05 required false flag changed: {key}")
    for field, count_field in (
        ("dhc_op05_result_classification_refs", "dhc_op05_result_classification_ref_count"),
        ("dhc_op05_reason_refs", "dhc_op05_reason_ref_count"),
        ("dhc_op05_blocker_refs", "dhc_op05_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP05 count field changed: {count_field}")
    if tuple(data.get("dhc_op05_result_classification_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS:
        raise ValueError("DHC-OP05 classification refs changed")
    if data.get("bodyfree_existing_dhr_op05_result_classification_ref") != data.get("dhc_result_classification_ref"):
        raise ValueError("DHC-OP05 classification alias changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP05_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP05 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP05_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP05 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R4_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP05 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R4_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP05 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP05 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP05 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP05 body-free marker changed")
    classification_ref = data.get("dhc_result_classification_ref")
    flags = [
        data.get("dhc_op05_scan_clear_stopped") is True,
        data.get("dhc_op05_waiting_or_incomplete_stopped") is True,
        data.get("dhc_op05_repair_required_stopped") is True,
        data.get("dhc_op05_not_called_stopped") is True,
        data.get("dhc_op05_blocked_stopped") is True,
    ]
    if classification_ref not in P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS or sum(flags) != 1:
        raise ValueError("DHC-OP05 must select exactly one classification")
    if classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_SCAN_CLEAR_STOPPED_REF:
            raise ValueError("DHC-OP05 scan-clear next step changed")
        if data.get("existing_dhr_op05_status_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF:
            raise ValueError("DHC-OP05 scan-clear classification requires existing scan clear")
        if data.get("existing_dhr_op05_preflight_scan_passed") is not True:
            raise ValueError("DHC-OP05 scan-clear classification requires preflight passed")
    elif classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_WAITING_OR_INCOMPLETE_STOPPED_REF:
            raise ValueError("DHC-OP05 waiting next step changed")
        if data.get("existing_dhr_op05_status_ref") != P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_WAITING_OR_INCOMPLETE_STATUS_REF:
            raise ValueError("DHC-OP05 waiting classification requires existing waiting status")
    elif classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_REQUIRED_STOPPED_REF:
            raise ValueError("DHC-OP05 repair next step changed")
    elif classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[3]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_NOT_CALLED_STOPPED_REF:
            raise ValueError("DHC-OP05 not-called next step changed")
        if data.get("existing_dhr_op05_builder_called_here") is not False or data.get("existing_dhr_op05_result_present") is not False:
            raise ValueError("DHC-OP05 not-called classification cannot carry existing result")
    elif classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[4]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_STOPPED_REF:
            raise ValueError("DHC-OP05 blocked next step changed")
        if data.get("dhr_op06_called_here") is not False:
            raise ValueError("DHC-OP05 blocked classification cannot call DHR-OP06")
    return True


# ---------------------------------------------------------------------------
# R5 / DHC-OP06〜OP07: no-touch / no-promotion / no-auto-downstream guard and
# body-free validation-plan/result-memo draft material.  This section consumes
# the stopped DHC-OP05 classification only.  It does not call DHR-OP06,
# DHR-OP07, DMD, R52, actual review, P8, validation commands, or release
# decisions.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op00_op01_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op02_op03_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op04_op05_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op06_op07_20260709.py",
)
P7_R54_AHR_POST_DHB_DHC_R5_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
)
P7_R54_AHR_POST_DHB_DHC_R5_RESULT_MEMO_EXPECTED_FILE_REFS: Final[tuple[str, ...]] = (
    "mashos-api/ai/tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R7_TargetValidation_Result_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R8_SelectedRegression_Result_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R9_Compileall_Result_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R10_ResultMemoClosure_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R11_NextWorkDecision_20260709.md",
)
P7_R54_AHR_POST_DHB_DHC_OP07_TARGET_VALIDATION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op00_op01_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op02_op03_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op04_op05_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op06_op07_20260709.py -p no:cacheprovider"
)
P7_R54_AHR_POST_DHB_DHC_OP07_SELECTED_REGRESSION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "<DHC R5 target tests plus selected adjacent DHB and existing DHR reference tests> -p no:cacheprovider"
)
P7_R54_AHR_POST_DHB_DHC_OP07_COMPILEALL_COMMAND_REF: Final = (
    "PYTHONPATH=services/ai_inference python -m compileall -q "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py "
    "services/ai_inference/emlis_ai_p7_contracts.py"
)
P7_R54_AHR_POST_DHB_DHC_OP07_VALIDATION_COMMAND_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP07_TARGET_VALIDATION_COMMAND_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_SELECTED_REGRESSION_COMMAND_REF,
    P7_R54_AHR_POST_DHB_DHC_OP07_COMPILEALL_COMMAND_REF,
)

P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP06_TO_OP07_REF: Final = P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP06_NO_TOUCH_GUARD_INPUTS_REF: Final = (
    "repair_DHC_OP06_no_touch_guard_inputs_before_validation_plan_or_any_DHR_OP06_execution"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_OP06_NO_TOUCH_NO_PROMOTION_GUARD_REF: Final = (
    "blocked_DHC_OP06_no_touch_no_promotion_no_auto_downstream_guard_before_any_validation_plan_or_DHR_OP06"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP07_TO_OP08_REF: Final = P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP07_VALIDATION_PLAN_INPUTS_REF: Final = (
    "repair_DHC_OP07_validation_plan_inputs_without_validation_execution_or_green_claim"
)
P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_OP07_VALIDATION_PLAN_REF: Final = (
    "blocked_DHC_OP07_validation_plan_bodyfree_leak_promotion_or_autorun_without_green_claim"
)

P7_R54_AHR_POST_DHB_DHC_R5_VALIDATION_GREEN_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "target_validation_green_confirmed_here",
    "selected_regression_green_confirmed_here",
    "compileall_green_confirmed_here",
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_confirmed",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_DHB_DHC_OP06_DOWNSTREAM_GUARD_FIELD_REFS: Final[tuple[str, ...]] = (
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "api_db_rn_runtime_response_key_changed",
    "json_schema_file_created_here",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_DHB_DHC_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_R0_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_R1_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP00_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP01_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP02_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP03_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP04_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP05_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHB_DHC_OP06_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)

P7_R54_AHR_POST_DHB_DHC_R5_UPSTREAM_DHR_OP05_FIELD_REFS: Final[frozenset[str]] = frozenset(
    {
        "existing_dhr_op04_assert_called_here",
        "manual_call_requested_here",
        "manual_call_allowed_here",
        "existing_dhr_op05_builder_call_allowed_here",
        "existing_dhr_op05_builder_called_here",
        "existing_dhr_op05_result_present",
        "existing_dhr_op05_contract_valid",
        "dhr_op05_called_here",
        "dhr_op05_builder_called_here",
    }
)
P7_R54_AHR_POST_DHB_DHC_OP06_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
        "dhc_op04_implemented",
        "dhc_op05_implemented",
        "dhc_op06_implemented",
        *P7_R54_AHR_POST_DHB_DHC_R5_UPSTREAM_DHR_OP05_FIELD_REFS,
    }
)
P7_R54_AHR_POST_DHB_DHC_OP07_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhc_op00_implemented",
        "dhc_op01_implemented",
        "dhc_op02_implemented",
        "dhc_op03_implemented",
        "dhc_op04_implemented",
        "dhc_op05_implemented",
        "dhc_op06_implemented",
        "dhc_op07_implemented",
        *P7_R54_AHR_POST_DHB_DHC_R5_UPSTREAM_DHR_OP05_FIELD_REFS,
    }
)

P7_R54_AHR_POST_DHB_DHC_OP06_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "operation_step_ref", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_material_present", "op05_contract_valid", "op05_schema_version", "op05_material_ref", "op05_classification_ref", "op05_next_required_step",
    "op05_scan_clear_stopped", "op05_waiting_or_incomplete_stopped", "op05_repair_required_stopped", "op05_not_called_stopped", "op05_blocked_stopped",
    "op05_existing_dhr_op05_status_ref", "op05_existing_dhr_op05_next_required_step", "op05_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission",
    "dhr_op05_call_attempted", "existing_dhr_op05_builder_called_here", "existing_dhr_op05_result_present", "existing_dhr_op05_contract_valid", "dhr_op05_called_here", "dhr_op05_builder_called_here",
    "op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count", "op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count",
    "op06_input_downstream_promotion_claim_refs", "op06_input_downstream_promotion_claim_ref_count", "op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count",
    "dhr_op06_call_allowed_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_r52_execution_allowed_here", "dmd_execution_started_here", "dmd_r52_executed_here", "r52_actual_execution_started_here",
    "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "question_text_materialized_here",
    "api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed", "api_db_rn_runtime_response_key_changed", "json_schema_file_created_here", "p7_complete", "release_allowed",
    "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "rn_real_device_modal_verified_claimed_here",
    "dhc_op06_status_ref", "bodyfree_no_touch_no_promotion_no_auto_downstream_guard_status_ref", "dhc_op06_allowed_status_refs", "dhc_op06_allowed_status_ref_count",
    "dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_passed", "dhc_op06_repair_required_for_no_touch_guard_inputs", "dhc_op06_blocked_no_touch_no_promotion_no_auto_downstream_guard",
    "dhc_op06_reason_refs", "dhc_op06_reason_ref_count", "dhc_op06_blocker_refs", "dhc_op06_blocker_ref_count",
    "dhc_op06_does_not_call_dhr_op06", "dhc_op06_does_not_materialize_dhr_op07", "dhc_op06_does_not_execute_dmd_r52_or_release", "dhc_op06_does_not_start_actual_review", "dhc_op06_does_not_create_actual_rows", "dhc_op06_does_not_create_question_need_observation_rows",
    "dhc_op06_does_not_start_p8_question_design", "dhc_op06_does_not_change_api_db_rn_runtime_response_key", "dhc_op06_does_not_materialize_question_text", "dhc_op06_does_not_claim_full_backend_suite_green", "dhc_op06_does_not_claim_rn_contract_green", "dhc_op06_does_not_claim_rn_real_device_modal_verified", "dhc_op06_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "target_test_ref_refs", "compileall_target_ref_refs", "public_contract", "dhc_no_touch_contract", "body_free_markers",
    "dhc_op00_implemented", "dhc_op01_implemented", "dhc_op02_implemented", "dhc_op03_implemented", "dhc_op04_implemented", "dhc_op05_implemented", "dhc_op06_implemented", "dhc_op07_implemented",
    "next_required_step", "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP07_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "operation_step_ref", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_material_present", "op06_contract_valid", "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_next_required_step", "op06_guard_passed", "op06_repair_required", "op06_blocked",
    "op06_upstream_existing_dhr_op05_builder_called_here", "op06_upstream_existing_dhr_op05_result_present", "op06_upstream_existing_dhr_op05_contract_valid", "op06_upstream_dhr_op05_called_here", "op06_upstream_dhr_op05_builder_called_here",
    "op06_upstream_op05_classification_ref", "op06_upstream_op05_scan_clear_stopped", "op06_upstream_op05_waiting_or_incomplete_stopped", "op06_upstream_op05_repair_required_stopped", "op06_upstream_op05_not_called_stopped", "op06_upstream_op05_blocked_stopped", "op06_upstream_existing_dhr_op05_status_ref", "op06_upstream_existing_dhr_op05_next_required_step", "op06_upstream_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission",
    "op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count", "op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count", "op07_input_downstream_promotion_claim_refs", "op07_input_downstream_promotion_claim_ref_count", "op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count",
    "target_validation_command_refs", "target_validation_command_ref_count", "selected_regression_command_refs", "selected_regression_command_ref_count", "compileall_command_refs", "compileall_command_ref_count",
    "result_memo_expected_file_refs", "result_memo_expected_file_ref_count", "target_validation_test_ref_refs", "target_validation_test_ref_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count", "compileall_target_ref_refs", "compileall_target_ref_ref_count",
    "validation_commands_executed_here", "target_validation_green_confirmed_here", "selected_regression_green_confirmed_here", "compileall_green_confirmed_here", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here",
    "raw_pytest_stdout_included", "raw_pytest_stderr_included", "raw_traceback_included", "raw_body_included", "comment_text_body_included", "question_text_body_included", "result_memo_policy_count_only_bodyfree", "validation_plan_is_not_validation_result", "validation_plan_does_not_claim_green",
    "existing_dhr_op05_builder_called_here", "existing_dhr_op05_result_present", "existing_dhr_op05_contract_valid", "dhr_op05_called_here", "dhr_op05_builder_called_here",
    "dhr_op06_call_allowed_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_r52_execution_allowed_here", "dmd_execution_started_here", "dmd_r52_executed_here", "r52_actual_execution_started_here", "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "question_text_materialized_here", "api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed", "api_db_rn_runtime_response_key_changed", "json_schema_file_created_here", "p7_complete", "release_allowed",
    "dhc_op07_status_ref", "bodyfree_validation_plan_result_memo_draft_status_ref", "dhc_op07_allowed_status_refs", "dhc_op07_allowed_status_ref_count", "dhc_op07_validation_plan_result_memo_draft_materialized_stopped", "dhc_op07_repair_required_for_validation_plan_inputs", "dhc_op07_blocked_validation_plan_bodyfree_leak_promotion_or_autorun",
    "dhc_op07_reason_refs", "dhc_op07_reason_ref_count", "dhc_op07_blocker_refs", "dhc_op07_blocker_ref_count",
    "dhc_op07_does_not_execute_validation_commands", "dhc_op07_does_not_claim_target_green", "dhc_op07_does_not_claim_selected_regression_green", "dhc_op07_does_not_claim_compileall_green", "dhc_op07_keeps_full_backend_suite_unconfirmed", "dhc_op07_keeps_rn_contract_unconfirmed", "dhc_op07_keeps_rn_real_device_unconfirmed", "dhc_op07_does_not_call_dhr_op06", "dhc_op07_does_not_materialize_dhr_op07", "dhc_op07_does_not_execute_dmd_r52", "dhc_op07_does_not_start_actual_review", "dhc_op07_does_not_create_actual_rows", "dhc_op07_does_not_create_question_need_observation_rows", "dhc_op07_does_not_start_p8_question_design", "dhc_op07_does_not_materialize_question_text", "dhc_op07_does_not_change_api_db_rn_runtime_response_key", "dhc_op07_does_not_make_release_decision", "dhc_op07_does_not_create_json_schema_file",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "target_test_ref_refs", "compileall_target_ref_refs", "public_contract", "dhc_no_touch_contract", "body_free_markers",
    "dhc_op00_implemented", "dhc_op01_implemented", "dhc_op02_implemented", "dhc_op03_implemented", "dhc_op04_implemented", "dhc_op05_implemented", "dhc_op06_implemented", "dhc_op07_implemented", "dhc_op08_implemented",
    "next_required_step", "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP06_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP06_REQUIRED_FALSE_FLAG_REFS)
)
P7_R54_AHR_POST_DHB_DHC_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP07_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP07_REQUIRED_FALSE_FLAG_REFS)
)


def _op05_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op05_existing_dhr_op05_result_classification_contract(data)
    except ValueError:
        return False
    return True


def _op06_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_contract(data)
    except ValueError:
        return False
    return True


def _scan_true_field_paths(value: Any, *, field_refs: Sequence[str], path: str) -> list[str]:
    refs = set(field_refs)
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in refs and child is True:
                paths.append(child_path)
            paths.extend(_scan_true_field_paths(child, field_refs=field_refs, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_true_field_paths(child, field_refs=field_refs, path=f"{path}[{index}]"))
    return paths


def _dhc_op06_status(
    *,
    blocked: bool,
    op05_valid: bool,
    op05_present: bool,
) -> tuple[str, list[str], list[str], str]:
    if blocked:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[2],
            ["DHC_OP06_no_touch_no_promotion_no_auto_downstream_guard_blocked"],
            ["repair_bodyfree_leak_promotion_or_autorun_before_any_DHR_OP06_consideration"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_OP06_NO_TOUCH_NO_PROMOTION_GUARD_REF,
        )
    if not op05_present or not op05_valid:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[1],
            ["DHC_OP05_classification_missing_or_contract_invalid_before_no_touch_guard"],
            ["repair_DHC_OP05_classification_before_validation_plan_draft"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP06_NO_TOUCH_GUARD_INPUTS_REF,
        )
    return (
        P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[0],
        ["DHC_OP06_downstream_no_touch_guard_passed_and_stopped"],
        [],
        P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP06_TO_OP07_REF,
    )


def _dhc_op07_status(
    *,
    blocked: bool,
    op06_valid: bool,
    op06_present: bool,
    op06_guard_passed: bool,
) -> tuple[str, list[str], list[str], str]:
    if blocked:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[2],
            ["DHC_OP07_validation_plan_bodyfree_or_green_claim_guard_blocked"],
            ["repair_validation_plan_bodyfree_leak_promotion_or_autorun_before_result_memo"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_OP07_VALIDATION_PLAN_REF,
        )
    if not op06_present or not op06_valid or not op06_guard_passed:
        return (
            P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[1],
            ["DHC_OP06_guard_missing_repair_or_blocked_before_validation_plan_draft"],
            ["repair_DHC_OP06_guard_before_materializing_validation_plan"],
            P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP07_VALIDATION_PLAN_INPUTS_REF,
        )
    return (
        P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[0],
        ["validation_plan_result_memo_draft_materialized_count_only_without_execution"],
        [],
        P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_OP07_TO_OP08_REF,
    )


def build_p7_r54_ahr_post_dhb_dhc_op06_no_touch_no_promotion_no_auto_downstream_guard(
    op05_existing_dhr_op05_result_classification: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Guard a stopped DHC-OP05 classification against downstream auto-promotion."""

    op05 = op05_existing_dhr_op05_result_classification
    op05_present = isinstance(op05, Mapping)
    op05_contract_valid = _op05_valid(op05)
    scan_root = {"op05_existing_dhr_op05_result_classification": op05 if op05_present else {}}
    forbidden_paths = _scan_forbidden_payload_key_paths(scan_root, path="dhc_op06_input")
    body_like_paths = _scan_body_like_value_paths(scan_root, path="dhc_op06_input")
    downstream_paths = _scan_true_field_paths(
        scan_root,
        field_refs=P7_R54_AHR_POST_DHB_DHC_OP06_DOWNSTREAM_GUARD_FIELD_REFS,
        path="dhc_op06_input",
    )
    no_touch_paths = _scan_no_touch_mutation_paths(scan_root, path="dhc_op06_input")
    blocked_input = bool(forbidden_paths or body_like_paths or downstream_paths or no_touch_paths)
    status_ref, reasons, blockers, next_required_step = _dhc_op06_status(
        blocked=blocked_input,
        op05_valid=op05_contract_valid,
        op05_present=op05_present,
    )
    guard_passed = status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[0]
    repair = status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[1]
    blocked = status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[2]
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers + forbidden_paths + body_like_paths + downstream_paths + no_touch_paths)
    session_id = _safe_review_session_id(review_session_id or (op05.get("review_session_id") if op05_present else None))
    op05_classification_ref = _clean_ref(op05.get("dhc_result_classification_ref") if op05_present else None, default="op05_classification_missing", max_length=320)
    op05_existing_status_ref = _clean_ref(op05.get("existing_dhr_op05_status_ref") if op05_present else None, default="existing_dhr_op05_status_missing", max_length=320)
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP06_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP06_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_20260709",
            "review_session_id": session_id,
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op05_material_present": op05_present,
            "op05_contract_valid": op05_contract_valid,
            "op05_schema_version": _clean_ref(op05.get("schema_version") if op05_present else None, default="op05_schema_missing", max_length=320),
            "op05_material_ref": _clean_ref(op05.get("material_id") if op05_present else None, default="op05_material_missing", max_length=320),
            "op05_classification_ref": op05_classification_ref,
            "op05_next_required_step": _clean_ref(op05.get("next_required_step") if op05_present else None, default="op05_next_step_missing", max_length=360),
            "op05_scan_clear_stopped": bool(op05_present and op05.get("dhc_op05_scan_clear_stopped") is True),
            "op05_waiting_or_incomplete_stopped": bool(op05_present and op05.get("dhc_op05_waiting_or_incomplete_stopped") is True),
            "op05_repair_required_stopped": bool(op05_present and op05.get("dhc_op05_repair_required_stopped") is True),
            "op05_not_called_stopped": bool(op05_present and op05.get("dhc_op05_not_called_stopped") is True),
            "op05_blocked_stopped": bool(op05_present and op05.get("dhc_op05_blocked_stopped") is True),
            "op05_existing_dhr_op05_status_ref": op05_existing_status_ref,
            "op05_existing_dhr_op05_next_required_step": _clean_ref(op05.get("existing_dhr_op05_next_required_step") if op05_present else None, default="existing_dhr_op05_next_step_missing", max_length=360),
            "op05_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission": bool(op05_present and op05.get("existing_dhr_op05_next_required_step_is_not_dhc_execution_permission") is True),
            "dhr_op05_call_attempted": bool(op05_present and op05.get("dhr_op05_call_attempted") is True),
            "existing_dhr_op05_builder_called_here": bool(op05_present and op05.get("existing_dhr_op05_builder_called_here") is True),
            "existing_dhr_op05_result_present": bool(op05_present and op05.get("existing_dhr_op05_result_present") is True),
            "existing_dhr_op05_contract_valid": bool(op05_present and op05.get("existing_dhr_op05_contract_valid") is True),
            "dhr_op05_called_here": bool(op05_present and op05.get("dhr_op05_called_here") is True),
            "dhr_op05_builder_called_here": bool(op05_present and op05.get("dhr_op05_builder_called_here") is True),
            "op06_input_forbidden_payload_key_path_refs": list(forbidden_paths),
            "op06_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op06_input_body_like_value_path_refs": list(body_like_paths),
            "op06_input_body_like_value_path_count": len(body_like_paths),
            "op06_input_downstream_promotion_claim_refs": list(downstream_paths),
            "op06_input_downstream_promotion_claim_ref_count": len(downstream_paths),
            "op06_input_no_touch_mutation_path_refs": list(no_touch_paths),
            "op06_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhr_op06_call_allowed_here": False,
            "dhr_op06_called_here": False,
            "dhr_op07_materialized_here": False,
            "dmd_r52_execution_allowed_here": False,
            "dmd_execution_started_here": False,
            "dmd_r52_executed_here": False,
            "r52_actual_execution_started_here": False,
            "actual_review_started_here": False,
            "actual_rows_created_here": False,
            "question_need_observation_rows_created_here": False,
            "p8_start_allowed": False,
            "p8_question_design_started": False,
            "p8_question_implementation_started": False,
            "question_text_materialized_here": False,
            "api_changed": False,
            "db_changed": False,
            "rn_changed": False,
            "runtime_changed": False,
            "response_key_changed": False,
            "api_db_rn_runtime_response_key_changed": False,
            "json_schema_file_created_here": False,
            "p7_complete": False,
            "release_allowed": False,
            "full_backend_suite_green_claimed_here": False,
            "rn_contract_green_claimed_here": False,
            "rn_real_device_modal_verified_claimed_here": False,
            "dhc_op06_status_ref": status_ref,
            "bodyfree_no_touch_no_promotion_no_auto_downstream_guard_status_ref": status_ref,
            "dhc_op06_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS,
            "dhc_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS),
            "dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_passed": guard_passed,
            "dhc_op06_repair_required_for_no_touch_guard_inputs": repair,
            "dhc_op06_blocked_no_touch_no_promotion_no_auto_downstream_guard": blocked,
            "dhc_op06_reason_refs": reason_refs,
            "dhc_op06_reason_ref_count": reason_count,
            "dhc_op06_blocker_refs": blocker_refs,
            "dhc_op06_blocker_ref_count": blocker_count,
            "dhc_op06_does_not_call_dhr_op06": True,
            "dhc_op06_does_not_materialize_dhr_op07": True,
            "dhc_op06_does_not_execute_dmd_r52_or_release": True,
            "dhc_op06_does_not_start_actual_review": True,
            "dhc_op06_does_not_create_actual_rows": True,
            "dhc_op06_does_not_create_question_need_observation_rows": True,
            "dhc_op06_does_not_start_p8_question_design": True,
            "dhc_op06_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op06_does_not_materialize_question_text": True,
            "dhc_op06_does_not_claim_full_backend_suite_green": True,
            "dhc_op06_does_not_claim_rn_contract_green": True,
            "dhc_op06_does_not_claim_rn_real_device_modal_verified": True,
            "dhc_op06_does_not_create_json_schema_file": True,
            "claim_boundary_refs": P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS,
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS,
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS,
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP06_IMPLEMENTED_STEPS,
            "not_yet_implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP06_NOT_YET_IMPLEMENTED_STEPS,
            "target_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS,
            "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS,
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "dhc_op01_implemented": True,
            "dhc_op02_implemented": True,
            "dhc_op03_implemented": True,
            "dhc_op04_implemented": True,
            "dhc_op05_implemented": True,
            "dhc_op06_implemented": True,
            "dhc_op07_implemented": False,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_contract(
    data: Mapping[str, Any],
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHB-DHC-OP06")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP06 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP06_SCHEMA_VERSION:
        raise ValueError("DHC-OP06 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP06_STEP_REF:
        raise ValueError("DHC-OP06 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP06 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP06 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP06 must remain body-free")
    for key in (
        "dhc_op06_does_not_call_dhr_op06", "dhc_op06_does_not_materialize_dhr_op07", "dhc_op06_does_not_execute_dmd_r52_or_release", "dhc_op06_does_not_start_actual_review", "dhc_op06_does_not_create_actual_rows", "dhc_op06_does_not_create_question_need_observation_rows", "dhc_op06_does_not_start_p8_question_design", "dhc_op06_does_not_change_api_db_rn_runtime_response_key", "dhc_op06_does_not_materialize_question_text", "dhc_op06_does_not_claim_full_backend_suite_green", "dhc_op06_does_not_claim_rn_contract_green", "dhc_op06_does_not_claim_rn_real_device_modal_verified", "dhc_op06_does_not_create_json_schema_file",
        "dhc_op00_implemented", "dhc_op01_implemented", "dhc_op02_implemented", "dhc_op03_implemented", "dhc_op04_implemented", "dhc_op05_implemented", "dhc_op06_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP06 required true field changed: {key}")
    for key in (
        "dhr_op06_call_allowed_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_r52_execution_allowed_here", "dmd_execution_started_here", "dmd_r52_executed_here", "r52_actual_execution_started_here", "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "question_text_materialized_here", "api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed", "api_db_rn_runtime_response_key_changed", "json_schema_file_created_here", "p7_complete", "release_allowed", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "rn_real_device_modal_verified_claimed_here", "dhc_op07_implemented",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP06 forbidden downstream/claim field changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP06_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP06 required false flag changed: {key}")
    for field, count_field in (
        ("op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count"),
        ("op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count"),
        ("op06_input_downstream_promotion_claim_refs", "op06_input_downstream_promotion_claim_ref_count"),
        ("op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count"),
        ("dhc_op06_reason_refs", "dhc_op06_reason_ref_count"),
        ("dhc_op06_blocker_refs", "dhc_op06_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP06 count field changed: {count_field}")
    if data.get("bodyfree_no_touch_no_promotion_no_auto_downstream_guard_status_ref") != data.get("dhc_op06_status_ref"):
        raise ValueError("DHC-OP06 status alias changed")
    if tuple(data.get("dhc_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP06 allowed status refs changed")
    if data.get("dhc_op06_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS):
        raise ValueError("DHC-OP06 allowed status count changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP06_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP06 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP06_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP06 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP06 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP06 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP06 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP06 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP06 body-free marker changed")
    status_ref = data.get("dhc_op06_status_ref")
    flags = [
        data.get("dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_passed") is True,
        data.get("dhc_op06_repair_required_for_no_touch_guard_inputs") is True,
        data.get("dhc_op06_blocked_no_touch_no_promotion_no_auto_downstream_guard") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("DHC-OP06 must select exactly one guard branch")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[0]:
        if data.get("op05_contract_valid") is not True or data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF:
            raise ValueError("DHC-OP06 passed branch must carry valid OP05 and next OP07")
        if data.get("op06_input_downstream_promotion_claim_refs") or data.get("op06_input_no_touch_mutation_path_refs"):
            raise ValueError("DHC-OP06 passed branch cannot carry downstream blockers")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP06_NO_TOUCH_GUARD_INPUTS_REF:
            raise ValueError("DHC-OP06 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_OP06_NO_TOUCH_NO_PROMOTION_GUARD_REF:
            raise ValueError("DHC-OP06 blocked next step changed")
        if not data.get("dhc_op06_blocker_refs"):
            raise ValueError("DHC-OP06 blocked branch must record blocker refs")
    return True


def build_p7_r54_ahr_post_dhb_dhc_op07_validation_plan_result_memo_draft_material(
    op06_no_touch_no_promotion_no_auto_downstream_guard: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Materialize count-only validation plan and result-memo draft refs without executing validation."""

    op06 = op06_no_touch_no_promotion_no_auto_downstream_guard
    op06_present = isinstance(op06, Mapping)
    op06_contract_valid = _op06_valid(op06)
    op06_status_ref = _clean_ref(op06.get("dhc_op06_status_ref") if op06_present else None, default="op06_status_missing", max_length=320)
    op06_guard_passed = bool(op06_contract_valid and op06.get("dhc_op06_no_touch_no_promotion_no_auto_downstream_guard_passed") is True)
    op06_repair = bool(op06_status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[1])
    op06_blocked = bool(op06_status_ref == P7_R54_AHR_POST_DHB_DHC_OP06_ALLOWED_STATUS_REFS[2])
    scan_root = {"op06_no_touch_no_promotion_no_auto_downstream_guard": op06 if op06_present else {}}
    forbidden_paths = _scan_forbidden_payload_key_paths(scan_root, path="dhc_op07_input")
    body_like_paths = _scan_body_like_value_paths(scan_root, path="dhc_op07_input")
    downstream_paths = _scan_true_field_paths(
        scan_root,
        field_refs=(*P7_R54_AHR_POST_DHB_DHC_OP06_DOWNSTREAM_GUARD_FIELD_REFS, *P7_R54_AHR_POST_DHB_DHC_R5_VALIDATION_GREEN_PROMOTION_CLAIM_FIELD_REFS),
        path="dhc_op07_input",
    )
    no_touch_paths = _scan_no_touch_mutation_paths(scan_root, path="dhc_op07_input")
    blocked_input = bool(forbidden_paths or body_like_paths or downstream_paths or no_touch_paths or op06_blocked)
    status_ref, reasons, blockers, next_required_step = _dhc_op07_status(
        blocked=blocked_input,
        op06_valid=op06_contract_valid,
        op06_present=op06_present,
        op06_guard_passed=op06_guard_passed,
    )
    materialized = status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[0]
    repair = status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[1]
    blocked = status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[2]
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers + forbidden_paths + body_like_paths + downstream_paths + no_touch_paths)
    session_id = _safe_review_session_id(review_session_id or (op06.get("review_session_id") if op06_present else None))
    upstream_builder_called = bool(op06_present and op06.get("existing_dhr_op05_builder_called_here") is True)
    upstream_result_present = bool(op06_present and op06.get("existing_dhr_op05_result_present") is True)
    upstream_contract_valid = bool(op06_present and op06.get("existing_dhr_op05_contract_valid") is True)
    upstream_dhr_op05_called = bool(op06_present and op06.get("dhr_op05_called_here") is True)
    upstream_dhr_op05_builder_called = bool(op06_present and op06.get("dhr_op05_builder_called_here") is True)
    upstream_op05_classification_ref = _clean_ref(
        op06.get("op05_classification_ref") if op06_present else None,
        default="op05_classification_missing",
        max_length=320,
    )
    upstream_op05_scan_clear_stopped = bool(op06_present and op06.get("op05_scan_clear_stopped") is True)
    upstream_op05_waiting_or_incomplete_stopped = bool(op06_present and op06.get("op05_waiting_or_incomplete_stopped") is True)
    upstream_op05_repair_required_stopped = bool(op06_present and op06.get("op05_repair_required_stopped") is True)
    upstream_op05_not_called_stopped = bool(op06_present and op06.get("op05_not_called_stopped") is True)
    upstream_op05_blocked_stopped = bool(op06_present and op06.get("op05_blocked_stopped") is True)
    upstream_existing_dhr_op05_status_ref = _clean_ref(
        op06.get("op05_existing_dhr_op05_status_ref") if op06_present else None,
        default="existing_dhr_op05_status_missing_from_op06",
        max_length=320,
    )
    upstream_existing_dhr_op05_next_required_step = _clean_ref(
        op06.get("op05_existing_dhr_op05_next_required_step") if op06_present else None,
        default="existing_dhr_op05_next_step_missing_from_op06",
        max_length=360,
    )
    upstream_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission = bool(
        op06_present and op06.get("op05_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission") is True
    )
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP07_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHB_DHC_OP07_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
            "step": P7_R54_AHR_POST_DHB_DHC_STEP,
            "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhb_dhc_op07_validation_plan_result_memo_draft_material_20260709",
            "review_session_id": session_id,
            "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op06_material_present": op06_present,
            "op06_contract_valid": op06_contract_valid,
            "op06_schema_version": _clean_ref(op06.get("schema_version") if op06_present else None, default="op06_schema_missing", max_length=320),
            "op06_material_ref": _clean_ref(op06.get("material_id") if op06_present else None, default="op06_material_missing", max_length=320),
            "op06_status_ref": op06_status_ref,
            "op06_next_required_step": _clean_ref(op06.get("next_required_step") if op06_present else None, default="op06_next_step_missing", max_length=360),
            "op06_guard_passed": op06_guard_passed,
            "op06_repair_required": op06_repair,
            "op06_blocked": op06_blocked,
            "op06_upstream_existing_dhr_op05_builder_called_here": upstream_builder_called,
            "op06_upstream_existing_dhr_op05_result_present": upstream_result_present,
            "op06_upstream_existing_dhr_op05_contract_valid": upstream_contract_valid,
            "op06_upstream_dhr_op05_called_here": upstream_dhr_op05_called,
            "op06_upstream_dhr_op05_builder_called_here": upstream_dhr_op05_builder_called,
            "op06_upstream_op05_classification_ref": upstream_op05_classification_ref,
            "op06_upstream_op05_scan_clear_stopped": upstream_op05_scan_clear_stopped,
            "op06_upstream_op05_waiting_or_incomplete_stopped": upstream_op05_waiting_or_incomplete_stopped,
            "op06_upstream_op05_repair_required_stopped": upstream_op05_repair_required_stopped,
            "op06_upstream_op05_not_called_stopped": upstream_op05_not_called_stopped,
            "op06_upstream_op05_blocked_stopped": upstream_op05_blocked_stopped,
            "op06_upstream_existing_dhr_op05_status_ref": upstream_existing_dhr_op05_status_ref,
            "op06_upstream_existing_dhr_op05_next_required_step": upstream_existing_dhr_op05_next_required_step,
            "op06_upstream_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission": upstream_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission,
            "op07_input_forbidden_payload_key_path_refs": list(forbidden_paths),
            "op07_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op07_input_body_like_value_path_refs": list(body_like_paths),
            "op07_input_body_like_value_path_count": len(body_like_paths),
            "op07_input_downstream_promotion_claim_refs": list(downstream_paths),
            "op07_input_downstream_promotion_claim_ref_count": len(downstream_paths),
            "op07_input_no_touch_mutation_path_refs": list(no_touch_paths),
            "op07_input_no_touch_mutation_path_count": len(no_touch_paths),
            "target_validation_command_refs": (P7_R54_AHR_POST_DHB_DHC_OP07_TARGET_VALIDATION_COMMAND_REF,),
            "target_validation_command_ref_count": 1,
            "selected_regression_command_refs": (P7_R54_AHR_POST_DHB_DHC_OP07_SELECTED_REGRESSION_COMMAND_REF,),
            "selected_regression_command_ref_count": 1,
            "compileall_command_refs": (P7_R54_AHR_POST_DHB_DHC_OP07_COMPILEALL_COMMAND_REF,),
            "compileall_command_ref_count": 1,
            "result_memo_expected_file_refs": P7_R54_AHR_POST_DHB_DHC_R5_RESULT_MEMO_EXPECTED_FILE_REFS,
            "result_memo_expected_file_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R5_RESULT_MEMO_EXPECTED_FILE_REFS),
            "target_validation_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS,
            "target_validation_test_ref_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS),
            "selected_regression_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R5_SELECTED_REGRESSION_TEST_REF_REFS,
            "selected_regression_test_ref_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R5_SELECTED_REGRESSION_TEST_REF_REFS),
            "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS,
            "compileall_target_ref_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS),
            "validation_commands_executed_here": False,
            "target_validation_green_confirmed_here": False,
            "selected_regression_green_confirmed_here": False,
            "compileall_green_confirmed_here": False,
            "full_backend_suite_green_confirmed": False,
            "rn_contract_green_confirmed": False,
            "rn_real_device_modal_verified_claimed_here": False,
            "full_backend_suite_green_claimed_here": False,
            "rn_contract_green_claimed_here": False,
            "raw_pytest_stdout_included": False,
            "raw_pytest_stderr_included": False,
            "raw_traceback_included": False,
            "raw_body_included": False,
            "comment_text_body_included": False,
            "question_text_body_included": False,
            "result_memo_policy_count_only_bodyfree": True,
            "validation_plan_is_not_validation_result": True,
            "validation_plan_does_not_claim_green": True,
            "existing_dhr_op05_builder_called_here": upstream_builder_called,
            "existing_dhr_op05_result_present": upstream_result_present,
            "existing_dhr_op05_contract_valid": upstream_contract_valid,
            "dhr_op05_called_here": upstream_dhr_op05_called,
            "dhr_op05_builder_called_here": upstream_dhr_op05_builder_called,
            "dhr_op06_call_allowed_here": False,
            "dhr_op06_called_here": False,
            "dhr_op07_materialized_here": False,
            "dmd_r52_execution_allowed_here": False,
            "dmd_execution_started_here": False,
            "dmd_r52_executed_here": False,
            "r52_actual_execution_started_here": False,
            "actual_review_started_here": False,
            "actual_rows_created_here": False,
            "question_need_observation_rows_created_here": False,
            "p8_start_allowed": False,
            "p8_question_design_started": False,
            "p8_question_implementation_started": False,
            "question_text_materialized_here": False,
            "api_changed": False,
            "db_changed": False,
            "rn_changed": False,
            "runtime_changed": False,
            "response_key_changed": False,
            "api_db_rn_runtime_response_key_changed": False,
            "json_schema_file_created_here": False,
            "p7_complete": False,
            "release_allowed": False,
            "dhc_op07_status_ref": status_ref,
            "bodyfree_validation_plan_result_memo_draft_status_ref": status_ref,
            "dhc_op07_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS,
            "dhc_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS),
            "dhc_op07_validation_plan_result_memo_draft_materialized_stopped": materialized,
            "dhc_op07_repair_required_for_validation_plan_inputs": repair,
            "dhc_op07_blocked_validation_plan_bodyfree_leak_promotion_or_autorun": blocked,
            "dhc_op07_reason_refs": reason_refs,
            "dhc_op07_reason_ref_count": reason_count,
            "dhc_op07_blocker_refs": blocker_refs,
            "dhc_op07_blocker_ref_count": blocker_count,
            "dhc_op07_does_not_execute_validation_commands": True,
            "dhc_op07_does_not_claim_target_green": True,
            "dhc_op07_does_not_claim_selected_regression_green": True,
            "dhc_op07_does_not_claim_compileall_green": True,
            "dhc_op07_keeps_full_backend_suite_unconfirmed": True,
            "dhc_op07_keeps_rn_contract_unconfirmed": True,
            "dhc_op07_keeps_rn_real_device_unconfirmed": True,
            "dhc_op07_does_not_call_dhr_op06": True,
            "dhc_op07_does_not_materialize_dhr_op07": True,
            "dhc_op07_does_not_execute_dmd_r52": True,
            "dhc_op07_does_not_start_actual_review": True,
            "dhc_op07_does_not_create_actual_rows": True,
            "dhc_op07_does_not_create_question_need_observation_rows": True,
            "dhc_op07_does_not_start_p8_question_design": True,
            "dhc_op07_does_not_materialize_question_text": True,
            "dhc_op07_does_not_change_api_db_rn_runtime_response_key": True,
            "dhc_op07_does_not_make_release_decision": True,
            "dhc_op07_does_not_create_json_schema_file": True,
            "claim_boundary_refs": P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS,
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS,
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS,
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP07_IMPLEMENTED_STEPS,
            "not_yet_implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP07_NOT_YET_IMPLEMENTED_STEPS,
            "target_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS,
            "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS,
            "public_contract": public_contract_flags(),
            "dhc_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhc_op00_implemented": True,
            "dhc_op01_implemented": True,
            "dhc_op02_implemented": True,
            "dhc_op03_implemented": True,
            "dhc_op04_implemented": True,
            "dhc_op05_implemented": True,
            "dhc_op06_implemented": True,
            "dhc_op07_implemented": True,
            "dhc_op08_implemented": False,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op07_validation_plan_result_memo_draft_material_contract(
    data: Mapping[str, Any],
) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHB-DHC-OP07")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP07 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP07_SCHEMA_VERSION:
        raise ValueError("DHC-OP07 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP07_STEP_REF:
        raise ValueError("DHC-OP07 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE:
        raise ValueError("DHC-OP07 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP07 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP07 must remain body-free")
    for key in (
        "result_memo_policy_count_only_bodyfree", "validation_plan_is_not_validation_result", "validation_plan_does_not_claim_green",
        "dhc_op07_does_not_execute_validation_commands", "dhc_op07_does_not_claim_target_green", "dhc_op07_does_not_claim_selected_regression_green", "dhc_op07_does_not_claim_compileall_green", "dhc_op07_keeps_full_backend_suite_unconfirmed", "dhc_op07_keeps_rn_contract_unconfirmed", "dhc_op07_keeps_rn_real_device_unconfirmed", "dhc_op07_does_not_call_dhr_op06", "dhc_op07_does_not_materialize_dhr_op07", "dhc_op07_does_not_execute_dmd_r52", "dhc_op07_does_not_start_actual_review", "dhc_op07_does_not_create_actual_rows", "dhc_op07_does_not_create_question_need_observation_rows", "dhc_op07_does_not_start_p8_question_design", "dhc_op07_does_not_materialize_question_text", "dhc_op07_does_not_change_api_db_rn_runtime_response_key", "dhc_op07_does_not_make_release_decision", "dhc_op07_does_not_create_json_schema_file",
        "dhc_op00_implemented", "dhc_op01_implemented", "dhc_op02_implemented", "dhc_op03_implemented", "dhc_op04_implemented", "dhc_op05_implemented", "dhc_op06_implemented", "dhc_op07_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP07 required true field changed: {key}")
    for key in (
        "validation_commands_executed_here", "target_validation_green_confirmed_here", "selected_regression_green_confirmed_here", "compileall_green_confirmed_here", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here",
        "raw_pytest_stdout_included", "raw_pytest_stderr_included", "raw_traceback_included", "raw_body_included", "comment_text_body_included", "question_text_body_included",
        "dhr_op06_call_allowed_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_r52_execution_allowed_here", "dmd_execution_started_here", "dmd_r52_executed_here", "r52_actual_execution_started_here", "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "question_text_materialized_here", "api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed", "api_db_rn_runtime_response_key_changed", "json_schema_file_created_here", "p7_complete", "release_allowed", "dhc_op08_implemented",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP07 forbidden execution/green/downstream field changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP07_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP07 required false flag changed: {key}")
    for field, count_field in (
        ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"),
        ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"),
        ("op07_input_downstream_promotion_claim_refs", "op07_input_downstream_promotion_claim_ref_count"),
        ("op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count"),
        ("target_validation_command_refs", "target_validation_command_ref_count"),
        ("selected_regression_command_refs", "selected_regression_command_ref_count"),
        ("compileall_command_refs", "compileall_command_ref_count"),
        ("result_memo_expected_file_refs", "result_memo_expected_file_ref_count"),
        ("target_validation_test_ref_refs", "target_validation_test_ref_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count"),
        ("compileall_target_ref_refs", "compileall_target_ref_ref_count"),
        ("dhc_op07_reason_refs", "dhc_op07_reason_ref_count"),
        ("dhc_op07_blocker_refs", "dhc_op07_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP07 count field changed: {count_field}")
    if data.get("bodyfree_validation_plan_result_memo_draft_status_ref") != data.get("dhc_op07_status_ref"):
        raise ValueError("DHC-OP07 status alias changed")
    if tuple(data.get("dhc_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP07 allowed status refs changed")
    if data.get("dhc_op07_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS):
        raise ValueError("DHC-OP07 allowed status count changed")
    if tuple(data.get("target_validation_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP07 target validation test refs changed")
    if tuple(data.get("selected_regression_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R5_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("DHC-OP07 selected regression test refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP07 compileall target refs changed")
    if tuple(data.get("result_memo_expected_file_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R5_RESULT_MEMO_EXPECTED_FILE_REFS:
        raise ValueError("DHC-OP07 result memo expected refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP07_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP07 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP07_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP07 not-yet steps changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHC-OP07 public contract changed")
    if any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()):
        raise ValueError("DHC-OP07 no-touch contract must be false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP07 body-free marker changed")
    status_ref = data.get("dhc_op07_status_ref")
    flags = [
        data.get("dhc_op07_validation_plan_result_memo_draft_materialized_stopped") is True,
        data.get("dhc_op07_repair_required_for_validation_plan_inputs") is True,
        data.get("dhc_op07_blocked_validation_plan_bodyfree_leak_promotion_or_autorun") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("DHC-OP07 must select exactly one validation-plan branch")
    op05_flags = [
        data.get("op06_upstream_op05_scan_clear_stopped") is True,
        data.get("op06_upstream_op05_waiting_or_incomplete_stopped") is True,
        data.get("op06_upstream_op05_repair_required_stopped") is True,
        data.get("op06_upstream_op05_not_called_stopped") is True,
        data.get("op06_upstream_op05_blocked_stopped") is True,
    ]
    if data.get("op06_upstream_op05_classification_ref") not in (*P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS, "op05_classification_missing"):
        raise ValueError("DHC-OP07 upstream OP05 classification ref changed")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[0]:
        if data.get("op06_contract_valid") is not True or data.get("op06_guard_passed") is not True:
            raise ValueError("DHC-OP07 materialized branch requires valid OP06 guard passed")
        if sum(op05_flags) != 1 or data.get("op06_upstream_op05_classification_ref") not in P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS:
            raise ValueError("DHC-OP07 materialized branch must preserve exactly one upstream OP05 classification")
        if data.get("op06_upstream_existing_dhr_op05_next_required_step_is_not_dhc_execution_permission") is not True:
            raise ValueError("DHC-OP07 must preserve existing DHR-OP05 next-step non-permission boundary")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF:
            raise ValueError("DHC-OP07 materialized next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_REPAIR_OP07_VALIDATION_PLAN_INPUTS_REF:
            raise ValueError("DHC-OP07 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[2]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHB_DHC_NEXT_STEP_BLOCKED_OP07_VALIDATION_PLAN_REF:
            raise ValueError("DHC-OP07 blocked next step changed")
        if not data.get("dhc_op07_blocker_refs"):
            raise ValueError("DHC-OP07 blocked branch must record blocker refs")
    return True


# ---------------------------------------------------------------------------
# R6 / DHC-OP08: result memo closure and stopped next-work candidate.
# OP08 closes the DHC boundary only. It does not create result memo files,
# execute validation, call DHR-OP06, materialize DHR-OP07, execute DMD/R52,
# start actual review, start P8, or make release decisions.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHB_DHC_R6_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHB_DHC_R5_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op08_result_20260709.py",
)
P7_R54_AHR_POST_DHB_DHC_R6_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHB_DHC_R6_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_DHB_DHC_R6_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DHB_DHC_R5_COMPILEALL_TARGET_REF_REFS
P7_R54_AHR_POST_DHB_DHC_R6_RESULT_MEMO_EXPECTED_FILE_REFS: Final[tuple[str, ...]] = P7_R54_AHR_POST_DHB_DHC_R5_RESULT_MEMO_EXPECTED_FILE_REFS
P7_R54_AHR_POST_DHB_DHC_OP08_TARGET_VALIDATION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op00_op01_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op02_op03_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op04_op05_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op06_op07_20260709.py "
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op08_result_20260709.py -p no:cacheprovider"
)
P7_R54_AHR_POST_DHB_DHC_OP08_SELECTED_REGRESSION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "<DHC R6 target tests plus selected adjacent DHB and existing DHR reference tests> -p no:cacheprovider"
)
P7_R54_AHR_POST_DHB_DHC_OP08_COMPILEALL_COMMAND_REF: Final = P7_R54_AHR_POST_DHB_DHC_OP07_COMPILEALL_COMMAND_REF

P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_SCAN_CLEAR_REF: Final = "consider_DHR_OP06_branch_resolver_or_P7_readfeel_reconnection_boundary_without_auto_execution"
P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_WAITING_OR_INCOMPLETE_REF: Final = "collect_or_repair_explicit_DHR_OP04_actual_source_claim_separation_without_P8_promotion"
P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_REPAIR_REQUIRED_REF: Final = "repair_bodyfree_leak_promotion_or_invalid_source_before_any_DHR_OP06_consideration"
P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NOT_CALLED_REF: Final = "wait_for_explicit_manual_call_request_and_explicit_DHR_OP04_material"
P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NON_DHR_LANE_REF: Final = "preserve_lane_specific_route_from_DHB_without_DHR_OP05_call"
P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_BLOCKED_REF: Final = "stop_and_repair_no_touch_no_promotion_violation"
P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_CANDIDATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_SCAN_CLEAR_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_WAITING_OR_INCOMPLETE_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NOT_CALLED_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NON_DHR_LANE_REF,
    P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_BLOCKED_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP08_NON_DHR_LANE_CLASSIFICATION_REF: Final = "DHC_RESULT_NON_DHR_LANE_ROUTE_PRESERVED_STOPPED"
P7_R54_AHR_POST_DHB_DHC_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHB_DHC_OP07_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHB_DHC_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_DHB_DHC_OP08_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHB_DHC_REQUIRED_FALSE_FLAG_REFS
    if key not in {
        "dhc_op00_implemented", "dhc_op01_implemented", "dhc_op02_implemented", "dhc_op03_implemented", "dhc_op04_implemented", "dhc_op05_implemented", "dhc_op06_implemented", "dhc_op07_implemented", "dhc_op08_implemented",
        "existing_dhr_op05_builder_called_here", "existing_dhr_op05_result_present", "existing_dhr_op05_contract_valid", "dhr_op05_called_here", "dhr_op05_builder_called_here",
    }
)
P7_R54_AHR_POST_DHB_DHC_OP08_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "operation_step_ref", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_material_present", "op07_contract_valid", "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_next_required_step", "op07_materialized", "op07_repair_required", "op07_blocked",
    "op08_explicit_classification_input_ref", "op08_non_dhr_lane_route_preserved", "dhc_result_classification_ref", "existing_dhr_op05_status_ref", "existing_dhr_op05_next_required_step",
    "dhr_op05_call_attempted", "existing_dhr_op05_builder_called_here", "existing_dhr_op05_result_present", "existing_dhr_op05_contract_valid", "dhr_op05_called_here", "dhr_op05_builder_called_here",
    "op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count", "op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count", "op08_input_downstream_promotion_claim_refs", "op08_input_downstream_promotion_claim_ref_count", "op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count",
    "target_validation_command_refs", "target_validation_command_ref_count", "selected_regression_command_refs", "selected_regression_command_ref_count", "compileall_command_refs", "compileall_command_ref_count",
    "result_memo_expected_file_refs", "result_memo_expected_file_ref_count", "target_validation_test_ref_refs", "target_validation_test_ref_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count", "compileall_target_ref_refs", "compileall_target_ref_ref_count",
    "validation_commands_executed_here", "target_validation_green_confirmed_here", "selected_regression_green_confirmed_here", "compileall_green_confirmed_here", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here",
    "raw_pytest_stdout_included", "raw_pytest_stderr_included", "raw_traceback_included", "raw_body_included", "comment_text_body_included", "question_text_body_included", "result_memo_policy_count_only_bodyfree", "result_memo_closure_is_not_validation_result", "result_memo_closure_does_not_claim_green", "result_memo_files_created_here",
    "dhr_op06_call_allowed_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_r52_execution_allowed_here", "dmd_execution_started_here", "dmd_r52_executed_here", "r52_actual_execution_started_here", "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "question_text_materialized_here", "api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed", "api_db_rn_runtime_response_key_changed", "json_schema_file_created_here", "p7_complete", "release_allowed",
    "dhc_op08_status_ref", "bodyfree_result_memo_closure_status_ref", "dhc_op08_allowed_status_refs", "dhc_op08_allowed_status_ref_count",
    "dhc_op08_scan_clear_closed_stopped", "dhc_op08_waiting_or_incomplete_closed_stopped", "dhc_op08_repair_required_closed_stopped", "dhc_op08_not_called_closed_stopped", "dhc_op08_non_dhr_lane_route_preserved_stopped", "dhc_op08_blocked_bodyfree_leak_promotion_or_autorun",
    "next_work_candidate_ref", "next_work_candidate_refs", "next_work_candidate_ref_count", "dhc_op08_reason_refs", "dhc_op08_reason_ref_count", "dhc_op08_blocker_refs", "dhc_op08_blocker_ref_count",
    "dhc_op08_does_not_call_dhr_op06", "dhc_op08_does_not_materialize_dhr_op07", "dhc_op08_does_not_execute_dmd_r52", "dhc_op08_does_not_start_actual_review", "dhc_op08_does_not_create_actual_rows", "dhc_op08_does_not_create_question_need_observation_rows", "dhc_op08_does_not_start_p8_question_design", "dhc_op08_does_not_materialize_question_text", "dhc_op08_does_not_change_api_db_rn_runtime_response_key", "dhc_op08_does_not_make_release_decision", "dhc_op08_does_not_create_json_schema_file", "dhc_op08_does_not_create_result_memo_files", "dhc_op08_does_not_claim_target_green", "dhc_op08_does_not_claim_selected_regression_green", "dhc_op08_does_not_claim_compileall_green", "dhc_op08_keeps_full_backend_suite_unconfirmed", "dhc_op08_keeps_rn_contract_unconfirmed", "dhc_op08_keeps_rn_real_device_unconfirmed",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "target_test_ref_refs", "compileall_target_ref_refs", "public_contract", "dhc_no_touch_contract", "body_free_markers",
    "dhc_op00_implemented", "dhc_op01_implemented", "dhc_op02_implemented", "dhc_op03_implemented", "dhc_op04_implemented", "dhc_op05_implemented", "dhc_op06_implemented", "dhc_op07_implemented", "dhc_op08_implemented",
    "next_required_step", "body_free",
)
P7_R54_AHR_POST_DHB_DHC_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(dict.fromkeys(P7_R54_AHR_POST_DHB_DHC_OP08_BASE_FIELD_REFS + P7_R54_AHR_POST_DHB_DHC_OP08_REQUIRED_FALSE_FLAG_REFS))


def _op07_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhb_dhc_op07_validation_plan_result_memo_draft_material_contract(data)
    except ValueError:
        return False
    return True


def _op08_status_and_next(*, blocked: bool, op07_present: bool, op07_valid: bool, op07_materialized: bool, op07_repair: bool, op07_blocked: bool, classification_ref: str, non_dhr_lane_route_preserved: bool) -> tuple[str, str, list[str], list[str]]:
    if blocked or op07_blocked or classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[4]:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[5], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_BLOCKED_REF, ["DHC_OP08_blocked_bodyfree_leak_promotion_or_autorun"], ["stop_and_repair_no_touch_no_promotion_violation"]
    if non_dhr_lane_route_preserved or classification_ref == P7_R54_AHR_POST_DHB_DHC_OP08_NON_DHR_LANE_CLASSIFICATION_REF:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[4], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NON_DHR_LANE_REF, ["DHC_OP08_preserves_non_DHR_lane_route_without_DHR_OP05_call"], []
    if not op07_present:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[3], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NOT_CALLED_REF, ["DHC_OP08_missing_OP07_material_closed_as_not_called"], ["wait_for_explicit_manual_call_request_and_explicit_DHR_OP04_material"]
    if not op07_valid or op07_repair or not op07_materialized:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[2], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_REPAIR_REQUIRED_REF, ["DHC_OP08_OP07_material_invalid_or_repair_required_before_closure"], ["repair_DHC_OP07_material_before_result_memo_closure"]
    if classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0]:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[0], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_SCAN_CLEAR_REF, ["DHC_OP08_scan_clear_closed_but_no_downstream_auto_execution"], []
    if classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[1]:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[1], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_WAITING_OR_INCOMPLETE_REF, ["DHC_OP08_waiting_or_incomplete_closed_without_P8_promotion"], ["collect_or_repair_explicit_DHR_OP04_actual_source_claim_separation"]
    if classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[2]:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[2], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_REPAIR_REQUIRED_REF, ["DHC_OP08_repair_required_closed_before_DHR_OP06_consideration"], ["repair_bodyfree_leak_promotion_or_invalid_source"]
    if classification_ref == P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[3]:
        return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[3], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NOT_CALLED_REF, ["DHC_OP08_not_called_closed_waiting_for_explicit_request_and_OP04_material"], ["wait_for_explicit_manual_call_request_and_explicit_DHR_OP04_material"]
    return P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[2], P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_REPAIR_REQUIRED_REF, ["DHC_OP08_classification_missing_or_unknown_before_closure"], ["repair_DHC_OP05_classification_ref_before_next_work_decision"]


def build_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate(
    op07_validation_plan_result_memo_draft_material: Mapping[str, Any] | None = None,
    *,
    dhc_result_classification_ref: str | None = None,
    op05_existing_dhr_op05_result_classification: Mapping[str, Any] | None = None,
    existing_dhr_op05_status_ref: str | None = None,
    existing_dhr_op05_next_required_step: str | None = None,
    non_dhr_lane_route_preserved: bool = False,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Close DHC-OP08 as body-free stopped next-work candidate material only."""
    op07 = op07_validation_plan_result_memo_draft_material
    op05 = op05_existing_dhr_op05_result_classification
    op07_present = isinstance(op07, Mapping)
    op05_present = isinstance(op05, Mapping)
    op07_contract_valid = _op07_valid(op07)
    op05_contract_valid = _op05_valid(op05)
    op07_status_ref = _clean_ref(op07.get("dhc_op07_status_ref") if op07_present else None, default="op07_status_missing", max_length=320)
    op07_materialized = bool(op07_contract_valid and op07.get("dhc_op07_validation_plan_result_memo_draft_materialized_stopped") is True)
    op07_repair = bool(op07_status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[1])
    op07_blocked = bool(op07_status_ref == P7_R54_AHR_POST_DHB_DHC_OP07_ALLOWED_STATUS_REFS[2])
    op05_explicit_invalid = bool(op05_present and not op05_contract_valid)
    op05_classification_input = op05.get("dhc_result_classification_ref") if op05_present and op05_contract_valid else None
    op05_existing_status_input = op05.get("existing_dhr_op05_status_ref") if op05_present and op05_contract_valid else None
    op05_existing_next_input = op05.get("existing_dhr_op05_next_required_step") if op05_present and op05_contract_valid else None
    op07_classification_input = op07.get("op06_upstream_op05_classification_ref") if op07_present and op07_contract_valid and not op05_explicit_invalid else None
    op07_existing_status_input = op07.get("op06_upstream_existing_dhr_op05_status_ref") if op07_present and op07_contract_valid and not op05_explicit_invalid else None
    op07_existing_next_input = op07.get("op06_upstream_existing_dhr_op05_next_required_step") if op07_present and op07_contract_valid and not op05_explicit_invalid else None
    explicit_op05_classification_mismatch = bool(
        op05_contract_valid
        and op07_contract_valid
        and op05_classification_input is not None
        and op07_classification_input is not None
        and op05_classification_input != op07_classification_input
    )
    explicit_op05_status_mismatch = bool(
        op05_contract_valid
        and op07_contract_valid
        and op05_existing_status_input is not None
        and op07_existing_status_input is not None
        and op05_existing_status_input != op07_existing_status_input
    )
    classification_ref = _clean_ref(
        dhc_result_classification_ref
        if dhc_result_classification_ref is not None
        else (op05_classification_input if op05_classification_input is not None else op07_classification_input),
        default=P7_R54_AHR_POST_DHB_DHC_OP08_NON_DHR_LANE_CLASSIFICATION_REF if non_dhr_lane_route_preserved else "dhc_result_classification_missing",
        max_length=360,
    )
    existing_status_ref = _clean_ref(
        existing_dhr_op05_status_ref
        if existing_dhr_op05_status_ref is not None
        else (op05_existing_status_input if op05_existing_status_input is not None else op07_existing_status_input),
        default="existing_dhr_op05_status_not_supplied" if not op05_explicit_invalid else "existing_dhr_op05_status_invalid_explicit_material",
        max_length=320,
    )
    existing_next_step = _clean_ref(
        existing_dhr_op05_next_required_step
        if existing_dhr_op05_next_required_step is not None
        else (op05_existing_next_input if op05_existing_next_input is not None else op07_existing_next_input),
        default="existing_dhr_op05_next_required_step_not_supplied" if not op05_explicit_invalid else "existing_dhr_op05_next_required_step_invalid_explicit_material",
        max_length=360,
    )
    scan_root = {"op07_validation_plan_result_memo_draft_material": op07 if op07_present else {}}
    forbidden_paths = _scan_forbidden_payload_key_paths(scan_root, path="dhc_op08_input")
    body_like_paths = _scan_body_like_value_paths(scan_root, path="dhc_op08_input")
    downstream_paths = _scan_true_field_paths(scan_root, field_refs=(*P7_R54_AHR_POST_DHB_DHC_OP06_DOWNSTREAM_GUARD_FIELD_REFS, *P7_R54_AHR_POST_DHB_DHC_R5_VALIDATION_GREEN_PROMOTION_CLAIM_FIELD_REFS), path="dhc_op08_input")
    no_touch_paths = _scan_no_touch_mutation_paths(scan_root, path="dhc_op08_input")
    blocked_input = bool(forbidden_paths or body_like_paths or downstream_paths or no_touch_paths or op07_blocked)
    status_ref, next_work_candidate_ref, reasons, blockers = _op08_status_and_next(
        blocked=blocked_input,
        op07_present=op07_present,
        op07_valid=op07_contract_valid,
        op07_materialized=op07_materialized,
        op07_repair=bool(op07_repair or op05_explicit_invalid or explicit_op05_classification_mismatch or explicit_op05_status_mismatch),
        op07_blocked=op07_blocked,
        classification_ref=classification_ref,
        non_dhr_lane_route_preserved=non_dhr_lane_route_preserved,
    )
    if op05_explicit_invalid:
        reasons.append("DHC_OP08_explicit_OP05_classification_material_invalid_repair_required")
        blockers.append("repair_explicit_DHC_OP05_classification_material_before_closure")
    if explicit_op05_classification_mismatch:
        reasons.append("DHC_OP08_explicit_OP05_classification_mismatch_with_OP07_upstream_repair_required")
        blockers.append("repair_OP05_classification_mismatch_before_next_work_decision")
    if explicit_op05_status_mismatch:
        reasons.append("DHC_OP08_explicit_existing_DHR_OP05_status_mismatch_with_OP07_upstream_repair_required")
        blockers.append("repair_existing_DHR_OP05_status_mismatch_before_next_work_decision")
    reason_refs, reason_count = _counted_refs(reasons)
    blocker_refs, blocker_count = _counted_refs(blockers + forbidden_paths + body_like_paths + downstream_paths + no_touch_paths)
    session_id = _safe_review_session_id(review_session_id or (op07.get("review_session_id") if op07_present else (op05.get("review_session_id") if op05_present else None)))
    upstream_builder_called = bool((op07_present and op07.get("existing_dhr_op05_builder_called_here") is True) or (op05_present and op05.get("existing_dhr_op05_builder_called_here") is True))
    upstream_result_present = bool((op07_present and op07.get("existing_dhr_op05_result_present") is True) or (op05_present and op05.get("existing_dhr_op05_result_present") is True))
    upstream_contract_valid = bool((op07_present and op07.get("existing_dhr_op05_contract_valid") is True) or (op05_present and op05.get("existing_dhr_op05_contract_valid") is True and op05_contract_valid))
    upstream_dhr_op05_called = bool((op07_present and op07.get("dhr_op05_called_here") is True) or (op05_present and op05.get("dhr_op05_called_here") is True))
    upstream_dhr_op05_builder_called = bool((op07_present and op07.get("dhr_op05_builder_called_here") is True) or (op05_present and op05.get("dhr_op05_builder_called_here") is True))
    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHB_DHC_OP08_REQUIRED_FALSE_FLAG_REFS))
    data.update({
        "schema_version": P7_R54_AHR_POST_DHB_DHC_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHB_DHC_PHASE,
        "step": P7_R54_AHR_POST_DHB_DHC_STEP,
        "scope": P7_R54_AHR_POST_DHB_DHC_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHB_DHC_POLICY_KIND,
        "operation_step_ref": P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF,
        "material_id": "p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate_20260709",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_material_present": op07_present,
        "op07_contract_valid": op07_contract_valid,
        "op07_schema_version": _clean_ref(op07.get("schema_version") if op07_present else None, default="op07_schema_missing", max_length=320),
        "op07_material_ref": _clean_ref(op07.get("material_id") if op07_present else None, default="op07_material_missing", max_length=320),
        "op07_status_ref": op07_status_ref,
        "op07_next_required_step": _clean_ref(op07.get("next_required_step") if op07_present else None, default="op07_next_step_missing", max_length=360),
        "op07_materialized": op07_materialized,
        "op07_repair_required": op07_repair,
        "op07_blocked": op07_blocked,
        "op08_explicit_classification_input_ref": classification_ref,
        "op08_non_dhr_lane_route_preserved": bool(non_dhr_lane_route_preserved),
        "dhc_result_classification_ref": classification_ref,
        "existing_dhr_op05_status_ref": existing_status_ref,
        "existing_dhr_op05_next_required_step": existing_next_step,
        "dhr_op05_call_attempted": upstream_builder_called or upstream_dhr_op05_called or upstream_dhr_op05_builder_called,
        "existing_dhr_op05_builder_called_here": upstream_builder_called,
        "existing_dhr_op05_result_present": upstream_result_present,
        "existing_dhr_op05_contract_valid": upstream_contract_valid,
        "dhr_op05_called_here": upstream_dhr_op05_called,
        "dhr_op05_builder_called_here": upstream_dhr_op05_builder_called,
        "op08_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op08_input_body_like_value_path_refs": list(body_like_paths),
        "op08_input_body_like_value_path_count": len(body_like_paths),
        "op08_input_downstream_promotion_claim_refs": list(downstream_paths),
        "op08_input_downstream_promotion_claim_ref_count": len(downstream_paths),
        "op08_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op08_input_no_touch_mutation_path_count": len(no_touch_paths),
        "target_validation_command_refs": (P7_R54_AHR_POST_DHB_DHC_OP08_TARGET_VALIDATION_COMMAND_REF,),
        "target_validation_command_ref_count": 1,
        "selected_regression_command_refs": (P7_R54_AHR_POST_DHB_DHC_OP08_SELECTED_REGRESSION_COMMAND_REF,),
        "selected_regression_command_ref_count": 1,
        "compileall_command_refs": (P7_R54_AHR_POST_DHB_DHC_OP08_COMPILEALL_COMMAND_REF,),
        "compileall_command_ref_count": 1,
        "result_memo_expected_file_refs": P7_R54_AHR_POST_DHB_DHC_R6_RESULT_MEMO_EXPECTED_FILE_REFS,
        "result_memo_expected_file_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R6_RESULT_MEMO_EXPECTED_FILE_REFS),
        "target_validation_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R6_TARGET_TEST_REF_REFS,
        "target_validation_test_ref_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R6_TARGET_TEST_REF_REFS),
        "selected_regression_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R6_SELECTED_REGRESSION_TEST_REF_REFS,
        "selected_regression_test_ref_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R6_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_R6_COMPILEALL_TARGET_REF_REFS,
        "compileall_target_ref_ref_count": len(P7_R54_AHR_POST_DHB_DHC_R6_COMPILEALL_TARGET_REF_REFS),
        "validation_commands_executed_here": False,
        "target_validation_green_confirmed_here": False,
        "selected_regression_green_confirmed_here": False,
        "compileall_green_confirmed_here": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "full_backend_suite_green_claimed_here": False,
        "rn_contract_green_claimed_here": False,
        "raw_pytest_stdout_included": False,
        "raw_pytest_stderr_included": False,
        "raw_traceback_included": False,
        "raw_body_included": False,
        "comment_text_body_included": False,
        "question_text_body_included": False,
        "result_memo_policy_count_only_bodyfree": True,
        "result_memo_closure_is_not_validation_result": True,
        "result_memo_closure_does_not_claim_green": True,
        "result_memo_files_created_here": False,
        "dhr_op06_call_allowed_here": False,
        "dhr_op06_called_here": False,
        "dhr_op07_materialized_here": False,
        "dmd_r52_execution_allowed_here": False,
        "dmd_execution_started_here": False,
        "dmd_r52_executed_here": False,
        "r52_actual_execution_started_here": False,
        "actual_review_started_here": False,
        "actual_rows_created_here": False,
        "question_need_observation_rows_created_here": False,
        "p8_start_allowed": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "question_text_materialized_here": False,
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "response_key_changed": False,
        "api_db_rn_runtime_response_key_changed": False,
        "json_schema_file_created_here": False,
        "p7_complete": False,
        "release_allowed": False,
        "dhc_op08_status_ref": status_ref,
        "bodyfree_result_memo_closure_status_ref": status_ref,
        "dhc_op08_allowed_status_refs": P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS,
        "dhc_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS),
        "dhc_op08_scan_clear_closed_stopped": status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[0],
        "dhc_op08_waiting_or_incomplete_closed_stopped": status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[1],
        "dhc_op08_repair_required_closed_stopped": status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[2],
        "dhc_op08_not_called_closed_stopped": status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[3],
        "dhc_op08_non_dhr_lane_route_preserved_stopped": status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[4],
        "dhc_op08_blocked_bodyfree_leak_promotion_or_autorun": status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[5],
        "next_work_candidate_ref": next_work_candidate_ref,
        "next_work_candidate_refs": P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_CANDIDATE_REFS,
        "next_work_candidate_ref_count": len(P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_CANDIDATE_REFS),
        "dhc_op08_reason_refs": reason_refs,
        "dhc_op08_reason_ref_count": reason_count,
        "dhc_op08_blocker_refs": blocker_refs,
        "dhc_op08_blocker_ref_count": blocker_count,
        "dhc_op08_does_not_call_dhr_op06": True,
        "dhc_op08_does_not_materialize_dhr_op07": True,
        "dhc_op08_does_not_execute_dmd_r52": True,
        "dhc_op08_does_not_start_actual_review": True,
        "dhc_op08_does_not_create_actual_rows": True,
        "dhc_op08_does_not_create_question_need_observation_rows": True,
        "dhc_op08_does_not_start_p8_question_design": True,
        "dhc_op08_does_not_materialize_question_text": True,
        "dhc_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "dhc_op08_does_not_make_release_decision": True,
        "dhc_op08_does_not_create_json_schema_file": True,
        "dhc_op08_does_not_create_result_memo_files": True,
        "dhc_op08_does_not_claim_target_green": True,
        "dhc_op08_does_not_claim_selected_regression_green": True,
        "dhc_op08_does_not_claim_compileall_green": True,
        "dhc_op08_keeps_full_backend_suite_unconfirmed": True,
        "dhc_op08_keeps_rn_contract_unconfirmed": True,
        "dhc_op08_keeps_rn_real_device_unconfirmed": True,
        "claim_boundary_refs": P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS,
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS,
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHB_DHC_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS,
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHB_DHC_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP08_IMPLEMENTED_STEPS,
        "not_yet_implemented_steps": P7_R54_AHR_POST_DHB_DHC_OP08_NOT_YET_IMPLEMENTED_STEPS,
        "target_test_ref_refs": P7_R54_AHR_POST_DHB_DHC_R6_TARGET_TEST_REF_REFS,
        "compileall_target_ref_refs": P7_R54_AHR_POST_DHB_DHC_R6_COMPILEALL_TARGET_REF_REFS,
        "public_contract": public_contract_flags(),
        "dhc_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "dhc_op00_implemented": True,
        "dhc_op01_implemented": True,
        "dhc_op02_implemented": True,
        "dhc_op03_implemented": True,
        "dhc_op04_implemented": True,
        "dhc_op05_implemented": True,
        "dhc_op06_implemented": True,
        "dhc_op07_implemented": True,
        "dhc_op08_implemented": True,
        "next_required_step": next_work_candidate_ref,
        "body_free": True,
    })
    return data


def assert_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate_contract(data: Mapping[str, Any]) -> bool:
    _required_fields_present(data, required=P7_R54_AHR_POST_DHB_DHC_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostDHB-DHC-OP08")
    if set(data) != set(P7_R54_AHR_POST_DHB_DHC_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("DHC-OP08 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHB_DHC_OP08_SCHEMA_VERSION:
        raise ValueError("DHC-OP08 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF:
        raise ValueError("DHC-OP08 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHB_DHC_SOURCE_MODE or data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHC-OP08 local source/git boundary changed")
    if data.get("body_free") is not True:
        raise ValueError("DHC-OP08 must remain body-free")
    for key in (
        "result_memo_policy_count_only_bodyfree", "result_memo_closure_is_not_validation_result", "result_memo_closure_does_not_claim_green",
        "dhc_op08_does_not_call_dhr_op06", "dhc_op08_does_not_materialize_dhr_op07", "dhc_op08_does_not_execute_dmd_r52", "dhc_op08_does_not_start_actual_review", "dhc_op08_does_not_create_actual_rows", "dhc_op08_does_not_create_question_need_observation_rows", "dhc_op08_does_not_start_p8_question_design", "dhc_op08_does_not_materialize_question_text", "dhc_op08_does_not_change_api_db_rn_runtime_response_key", "dhc_op08_does_not_make_release_decision", "dhc_op08_does_not_create_json_schema_file", "dhc_op08_does_not_create_result_memo_files", "dhc_op08_does_not_claim_target_green", "dhc_op08_does_not_claim_selected_regression_green", "dhc_op08_does_not_claim_compileall_green", "dhc_op08_keeps_full_backend_suite_unconfirmed", "dhc_op08_keeps_rn_contract_unconfirmed", "dhc_op08_keeps_rn_real_device_unconfirmed",
        "dhc_op00_implemented", "dhc_op01_implemented", "dhc_op02_implemented", "dhc_op03_implemented", "dhc_op04_implemented", "dhc_op05_implemented", "dhc_op06_implemented", "dhc_op07_implemented", "dhc_op08_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHC-OP08 required true field changed: {key}")
    for key in (
        "validation_commands_executed_here", "target_validation_green_confirmed_here", "selected_regression_green_confirmed_here", "compileall_green_confirmed_here", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "raw_pytest_stdout_included", "raw_pytest_stderr_included", "raw_traceback_included", "raw_body_included", "comment_text_body_included", "question_text_body_included", "result_memo_files_created_here", "dhr_op06_call_allowed_here", "dhr_op06_called_here", "dhr_op07_materialized_here", "dmd_r52_execution_allowed_here", "dmd_execution_started_here", "dmd_r52_executed_here", "r52_actual_execution_started_here", "actual_review_started_here", "actual_rows_created_here", "question_need_observation_rows_created_here", "p8_start_allowed", "p8_question_design_started", "p8_question_implementation_started", "question_text_materialized_here", "api_changed", "db_changed", "rn_changed", "runtime_changed", "response_key_changed", "api_db_rn_runtime_response_key_changed", "json_schema_file_created_here", "p7_complete", "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP08 forbidden execution/green/downstream field changed: {key}")
    for key in P7_R54_AHR_POST_DHB_DHC_OP08_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHC-OP08 required false flag changed: {key}")
    for field, count_field in (
        ("op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count"), ("op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count"), ("op08_input_downstream_promotion_claim_refs", "op08_input_downstream_promotion_claim_ref_count"), ("op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count"), ("target_validation_command_refs", "target_validation_command_ref_count"), ("selected_regression_command_refs", "selected_regression_command_ref_count"), ("compileall_command_refs", "compileall_command_ref_count"), ("result_memo_expected_file_refs", "result_memo_expected_file_ref_count"), ("target_validation_test_ref_refs", "target_validation_test_ref_ref_count"), ("selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count"), ("compileall_target_ref_refs", "compileall_target_ref_ref_count"), ("next_work_candidate_refs", "next_work_candidate_ref_count"), ("dhc_op08_reason_refs", "dhc_op08_reason_ref_count"), ("dhc_op08_blocker_refs", "dhc_op08_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHC-OP08 count field changed: {count_field}")
    if data.get("bodyfree_result_memo_closure_status_ref") != data.get("dhc_op08_status_ref"):
        raise ValueError("DHC-OP08 status alias changed")
    if tuple(data.get("dhc_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("DHC-OP08 allowed status refs changed")
    if tuple(data.get("next_work_candidate_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_CANDIDATE_REFS:
        raise ValueError("DHC-OP08 next-work candidates changed")
    if tuple(data.get("target_validation_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R6_TARGET_TEST_REF_REFS:
        raise ValueError("DHC-OP08 target refs changed")
    if tuple(data.get("selected_regression_test_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R6_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("DHC-OP08 selected regression refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHB_DHC_R6_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHC-OP08 compileall refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP08_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHB_DHC_OP08_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHC-OP08 step progression changed")
    if data.get("public_contract") != public_contract_flags() or any(value is not False for value in (data.get("dhc_no_touch_contract") or {}).values()) or data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHC-OP08 public/no-touch/body-free boundary changed")
    status_ref = data.get("dhc_op08_status_ref")
    flags = [data.get("dhc_op08_scan_clear_closed_stopped") is True, data.get("dhc_op08_waiting_or_incomplete_closed_stopped") is True, data.get("dhc_op08_repair_required_closed_stopped") is True, data.get("dhc_op08_not_called_closed_stopped") is True, data.get("dhc_op08_non_dhr_lane_route_preserved_stopped") is True, data.get("dhc_op08_blocked_bodyfree_leak_promotion_or_autorun") is True]
    expected_next = {
        P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[0]: P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_SCAN_CLEAR_REF,
        P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[1]: P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_WAITING_OR_INCOMPLETE_REF,
        P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[2]: P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_REPAIR_REQUIRED_REF,
        P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[3]: P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NOT_CALLED_REF,
        P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[4]: P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_NON_DHR_LANE_REF,
        P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[5]: P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_BLOCKED_REF,
    }
    if status_ref not in expected_next or sum(flags) != 1 or data.get("next_work_candidate_ref") != expected_next[status_ref] or data.get("next_required_step") != expected_next[status_ref]:
        raise ValueError("DHC-OP08 closure branch or next-work mismatch")
    if status_ref in (P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[1], P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[2], P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[3], P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[5]) and not data.get("dhc_op08_blocker_refs"):
        raise ValueError("DHC-OP08 non-clear branch must record blocker refs")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[0] and (data.get("dhc_result_classification_ref") != P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS[0] or data.get("op07_contract_valid") is not True or data.get("op07_materialized") is not True):
        raise ValueError("DHC-OP08 scan-clear branch requirements changed")
    if status_ref == P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS[4] and data.get("op08_non_dhr_lane_route_preserved") is not True:
        raise ValueError("DHC-OP08 non-DHR branch requirements changed")
    return True
