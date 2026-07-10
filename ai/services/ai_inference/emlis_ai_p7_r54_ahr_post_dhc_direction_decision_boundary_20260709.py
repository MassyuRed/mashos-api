# -*- coding: utf-8 -*-
"""Post-DHC direction decision boundary helpers.

R0-R6. R0 freezes DHD as a body-free direction decision boundary between
DHR-OP06 consideration and P7 readfeel reconnection. R1 exposes constants and
a strict helper-skeleton summary. R2 implements DHD-OP00 Post-DHC no-execution
refreeze and DHD-OP01 body-free DHC R11 closure-material intake. R3 classifies
the explicit current DHC outcome in DHD-OP02 and determines DHR-OP06
consideration eligibility without a builder call in DHD-OP03.
R4 determines P7 readfeel reconnection eligibility in DHD-OP04 and compares
that candidate with DHR-OP06 consideration in DHD-OP05 without executing
either direction.
R5 applies the no-touch/no-promotion/no-question-system guard in DHD-OP06 and
materializes only a count-only validation-plan/result-memo draft in DHD-OP07.
R6 closes each allowed next-design decision as a stopped DHD-OP08 material.

Important boundary:
* DHD does not synthesize a DHC result from R11 or validation green.
* DHD does not call a DHC builder, the existing DHR-OP05 builder, or DHR-OP06.
* DHD keeps the DHR-OP06 builder as a string reference only because that
  builder has an implicit OP05 fallback when no OP05 material is supplied.
* P7 readfeel reconnection is a future design candidate, not P7 completion,
  P8 question-system start, release readiness, or runtime execution.
* R0-R6 do not change API, DB, RN, runtime, response keys, or JSON/schema files.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709 as dhc
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr


P7_R54_AHR_POST_DHC_DHD_PHASE: Final = "P7"
P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_DHC_DHD_STEP: Final = (
    "R54-AHR-PostDHC_DirectionDecisionBoundary_20260709"
)
P7_R54_AHR_POST_DHC_DHD_SCOPE: Final = (
    "p7_r54_ahr_post_dhc_direction_decision_boundary"
)
P7_R54_AHR_POST_DHC_DHD_POLICY_KIND: Final = (
    "r54_ahr_post_dhc_dhr_op06_consideration_vs_p7_readfeel_direction_decision_boundary"
)
P7_R54_AHR_POST_DHC_DHD_DEFAULT_REVIEW_SESSION_ID: Final = (
    "p7_r54_ahr_post_dhc_direction_decision_boundary_20260709"
)
P7_R54_AHR_POST_DHC_DHD_SELECTED_PHASE_REF: Final = (
    "P7 Product Quality Runner / Long-run Product Gate"
)
P7_R54_AHR_POST_DHC_DHD_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-DHC Direction Decision Boundary"
)
P7_R54_AHR_POST_DHC_DHD_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-DHC Direction Decision Boundary"
)
P7_R54_AHR_POST_DHC_DHD_SELECTED_NEXT_BOUNDARY_REF: Final = (
    "DHR-OP06 branch resolver consideration vs P7 readfeel reconnection decision boundary"
)
P7_R54_AHR_POST_DHC_DHD_BOUNDARY_PREFIX_REF: Final = "DHD"
P7_R54_AHR_POST_DHC_DHD_BOUNDARY_PREFIX_MEANING_REF: Final = (
    "DHC Downstream Direction Decision / DHR-OP06 vs P7 Readfeel Reconnection"
)
P7_R54_AHR_POST_DHC_DHD_R0_STEP_REF: Final = "R0_design_reflection_pre_freeze"
P7_R54_AHR_POST_DHC_DHD_R1_STEP_REF: Final = "R1_constants_helper_skeleton"
P7_R54_AHR_POST_DHC_DHD_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_DHD_OP00_post_DHC_basis_no_execution_refreeze"
)
P7_R54_AHR_POST_DHC_DHD_CURRENT_EXECUTION_ALLOWANCE_REF: Final = "none"
P7_R54_AHR_POST_DHC_DHD_DHC_R11_NOT_DHR_OP06_PERMISSION_REF: Final = (
    "DHC_R11_is_not_DHR_OP06_permission"
)
P7_R54_AHR_POST_DHC_DHD_DHC_VALIDATION_NOT_RUNTIME_REF: Final = (
    "DHC_validation_green_is_not_current_runtime_execution"
)
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_BUILDER_CALL_PROHIBITION_REF: Final = (
    "DHD_must_not_call_existing_DHR_OP06_builder"
)
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_IMPLICIT_OP05_FALLBACK_PROHIBITION_REF: Final = (
    "DHD_must_not_use_DHR_OP06_implicit_OP05_builder_fallback"
)
P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_NOT_COMPLETE_REF: Final = (
    "P7_readfeel_reconnection_is_not_P7_complete_or_release_ready"
)

P7_R54_AHR_POST_DHC_DHD_R1_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "r1_helper_skeleton_constants_summary.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op00_post_dhc_basis_no_execution_refreeze.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op01_dhc_r11_closure_material_intake.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op02_dhc_outcome_class_current_material_sufficiency_check.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op03_dhr_op06_consideration_eligibility_without_call.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op04_p7_readfeel_reconnection_eligibility.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op05_direction_comparator.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op06_no_touch_no_promotion_no_question_system_guard.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op07_validation_plan_result_memo_draft_material.bodyfree.v1"
)
P7_R54_AHR_POST_DHC_DHD_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_dhc.dhd."
    "op08_stopped_next_design_decision_closure.bodyfree.v1"
)

P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF: Final = (
    "DHD-OP00_post_DHC_basis_no_execution_refreeze"
)
P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF: Final = (
    "DHD-OP01_DHC_R11_closure_material_intake"
)
P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF: Final = (
    "DHD-OP02_DHC_outcome_class_current_material_sufficiency_check"
)
P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF: Final = (
    "DHD-OP03_DHR_OP06_consideration_eligibility_without_call"
)
P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF: Final = (
    "DHD-OP04_P7_readfeel_reconnection_eligibility"
)
P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF: Final = "DHD-OP05_direction_comparator"
P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF: Final = (
    "DHD-OP06_no_touch_no_promotion_no_question_system_guard"
)
P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF: Final = (
    "DHD-OP07_validation_plan_result_memo_draft_material"
)
P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF: Final = (
    "DHD-OP08_stopped_next_design_decision_closure"
)
P7_R54_AHR_POST_DHC_DHD_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_SCHEMA_VERSION_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP00_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP01_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP02_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP03_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP04_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP05_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP06_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP07_SCHEMA_VERSION,
    P7_R54_AHR_POST_DHC_DHD_OP08_SCHEMA_VERSION,
)
P7_R54_AHR_POST_DHC_DHD_R0_R1_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_R0_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_R1_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_R0_R1_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_STEP_REFS
)

P7_R54_AHR_POST_DHC_DHD_DHC_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DHC_RESULT_SYNTHESIS_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DHC_R11_AS_CURRENT_SELECTED_RESULT_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DHC_VALIDATION_GREEN_AS_RUNTIME_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DHR_OP05_RUNTIME_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_RUNTIME_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_CONSIDERATION_DECISION_ALLOWED_IN_R1: Final = False
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_IMPLICIT_OP05_FALLBACK_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DHR_OP07_MATERIALIZATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_DMD_R52_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_ACTUAL_REVIEW_START_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_ACTUAL_ROWS_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_QUESTION_NEED_OBSERVATION_ROWS_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_RECONNECTION_DECISION_ALLOWED_IN_R1: Final = False
P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_EVALUATION_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_P8_QUESTION_DESIGN_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_P8_QUESTION_IMPLEMENTATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_QUESTION_TEXT_MATERIALIZATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_API_DB_RN_RUNTIME_RESPONSE_KEY_CHANGE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_P7_COMPLETE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_RELEASE_DECISION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_FULL_BACKEND_SUITE_GREEN_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_RN_CONTRACT_GREEN_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_RN_REAL_DEVICE_MODAL_VERIFICATION_CLAIM_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_DHC_DHD_BODY_FREE: Final = True

P7_R54_AHR_POST_DHC_DHD_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(305).zip",
    "implemented_docs": "EmlisAIの実装済み資料(107).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_system_update_20260706(7).zip",
    "cocolon_app": "Cocolon(279).zip",
    "backend": "mashos-api(195).zip",
}
P7_R54_AHR_POST_DHC_DHD_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
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
    "Cocolon_EmlisAI_P7_R54AHR_PostDHC_DirectionDecisionBoundary_DetailedDesign_ImplementationOrder_20260709(1).md",
)
P7_R54_AHR_POST_DHC_DHD_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "DHC result synthesis or DHC builder execution",
    "DHR-OP05 runtime or existing DHR-OP05 builder execution",
    "DHR-OP06 builder call or implicit OP05 fallback",
    "DHR-OP07 / DMD / R52 execution",
    "actual review start or actual rows creation",
    "P7 readfeel evaluation execution",
    "P8 question-system design or implementation",
    "question_text materialization",
    "API / DB / RN / runtime / response key change",
    "JSON / schema file creation",
    "P7 completion",
    "release decision",
)
P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "DHD R0/R1 freezes a direction decision boundary, not an execution boundary",
    "DHD keeps DHC R11 separate from current selected DHC-OP08 material",
    "DHD keeps DHC validation green separate from current runtime execution",
    "DHD keeps DHR-OP06 consideration separate from DHR-OP06 builder call",
    "DHD keeps DHR-OP06 implicit OP05 fallback prohibited",
    "DHD keeps P7 readfeel reconnection separate from P7 completion and release",
    "DHD keeps P8 question-system design and question text outside this boundary",
    "DHD keeps API / DB / RN / runtime / response keys untouched",
)
P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "dhd_op04_implemented",
    "dhd_op05_implemented",
    "dhd_op06_implemented",
    "dhd_op07_implemented",
    "dhd_op08_implemented",
    "dhc_builder_called_here",
    "dhc_result_synthesized_here",
    "current_dhc_result_selected_here",
    "current_existing_dhr_op05_result_wrapper_selected_here",
    "dhr_op05_runtime_call_started_here",
    "existing_dhr_op05_builder_runtime_called_here",
    "dhr_op06_consideration_decided_here",
    "dhr_op06_builder_called_here",
    "dhr_op06_implicit_op05_fallback_used_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p7_readfeel_reconnection_decided_here",
    "p7_readfeel_evaluation_started_here",
    "next_runtime_execution_allowed_here",
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
    "json_schema_file_created",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_DHC_builder_call_or_result_synthesis",
    "no_DHC_R11_or_validation_green_as_current_runtime_result",
    "no_DHR_OP05_runtime_or_existing_builder_call",
    "no_DHR_OP06_builder_call",
    "no_DHR_OP06_implicit_OP05_fallback",
    "no_DHR_OP07_DMD_R52_execution",
    "no_actual_review_or_rows_creation",
    "no_P7_readfeel_evaluation_execution_in_R1",
    "no_P8_question_system_or_question_text_materialization",
    "no_API_DB_RN_runtime_response_key_change",
    "no_JSON_schema_file_creation",
    "no_P7_complete_or_release_decision",
)

P7_R54_AHR_POST_DHC_DHD_DHC_R11_RESULT_MEMO_REF: Final = (
    "tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R11_NextWorkDecision_20260709.md"
)
P7_R54_AHR_POST_DHC_DHD_DHC_R10_CLOSURE_REF: Final = (
    "tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R10_ResultMemoClosure_20260709.md"
)
P7_R54_AHR_POST_DHC_DHD_DHC_VALIDATION_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R7_TargetValidation_Result_20260709.md",
    "tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R8_SelectedRegression_Result_20260709.md",
    "tests/R54_AHR_PostDHB_DHROP05ManualCallExecutionConsideration_DHC_R9_Compileall_Result_20260709.md",
)
P7_R54_AHR_POST_DHC_DHD_DHC_R11_RECOMMENDED_NEXT_WORK_CANDIDATE_REF: Final = (
    "Post-DHC DHR-OP06 branch resolver consideration vs P7 readfeel reconnection decision boundary / no auto execution"
)
P7_R54_AHR_POST_DHC_DHD_DHC_OP08_SCHEMA_VERSION_REF: Final = (
    dhc.P7_R54_AHR_POST_DHB_DHC_OP08_SCHEMA_VERSION
)
P7_R54_AHR_POST_DHC_DHD_DHC_OP08_STEP_REF: Final = (
    dhc.P7_R54_AHR_POST_DHB_DHC_OP08_STEP_REF
)
P7_R54_AHR_POST_DHC_DHD_DHC_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    dhc.P7_R54_AHR_POST_DHB_DHC_OP08_ALLOWED_STATUS_REFS
)
P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASS_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        dhc.P7_R54_AHR_POST_DHB_DHC_OP05_RESULT_CLASSIFICATION_REFS
        + (dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NON_DHR_LANE_CLASSIFICATION_REF,)
    )
)
P7_R54_AHR_POST_DHC_DHD_DHC_OP08_NEXT_WORK_CANDIDATE_REFS: Final[tuple[str, ...]] = (
    dhc.P7_R54_AHR_POST_DHB_DHC_OP08_NEXT_WORK_CANDIDATE_REFS
)
P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF: Final = (
    "build_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate"
)
P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_IMPORT_PATH_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709."
    + P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF
)

P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF: Final = (
    dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_REF
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_IMPORT_PATH_REF: Final = (
    dhc.P7_R54_AHR_POST_DHB_DHC_EXISTING_DHR_OP05_BUILDER_IMPORT_PATH_REF
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCHEMA_VERSION_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_SCHEMA_VERSION
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_STEP_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_ALLOWED_STATUS_REFS
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STATUS_SCAN_CLEAR_BODYFREE_REF
)

P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF: Final = (
    "build_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver"
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_IMPORT_PATH_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704."
    + P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ASSERT_REF: Final = (
    "assert_p7_r54_ahr_post_elr19_dhr_op06_handoff_or_retry_deterministic_branch_resolver_contract"
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ASSERT_IMPORT_PATH_REF: Final = (
    "emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704."
    + P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ASSERT_REF
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_SCHEMA_VERSION_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_SCHEMA_VERSION
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_STEP_REF: Final = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_STEP_REF
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_OP06_ALLOWED_STATUS_REFS
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BRANCH_REFS: Final[tuple[str, ...]] = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_REFS
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_RESOLVER_PRIORITY_REFS: Final[tuple[str, ...]] = (
    dhr.P7_R54_AHR_POST_ELR19_DHR_BRANCH_RESOLVER_PRIORITY_REFS
)
P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_IMPLICIT_OP05_FALLBACK_REF: Final = (
    "existing_DHR_OP06_builder_builds_DHR_OP05_when_explicit_OP05_material_is_none"
)

P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_AXIS_REFS: Final[tuple[str, ...]] = (
    "single_input_product_readfeel_and_read_feeling",
    "continued_input_value_and_wants_to_input_again",
    "blind_QA_non_template_naturalness",
    "external_pilot_readiness_observation",
    "question_need_observation_bodyfree_only_during_P7",
)
P7_R54_AHR_POST_DHC_DHD_EXPECTED_R11_ONLY_DIRECTION_REF: Final = (
    "P7_readfeel_reconnection_product_QA_return_detailed_design_candidate"
)
P7_R54_AHR_POST_DHC_DHD_KEPT_NOT_PROMOTED_DIRECTION_REF: Final = (
    "DHR_OP06_consideration_detailed_design_candidate_pending_explicit_current_material"
)

P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_POST_DHC_SCOPE_REFROZEN_STOPPED",
    "DHD_STATUS_POST_DHC_SCOPE_REPAIR_REQUIRED",
    "DHD_STATUS_POST_DHC_SCOPE_BLOCKED_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_DHC_R11_INTAKE_READY",
    "DHD_STATUS_DHC_R11_INTAKE_READY_WITH_EXPLICIT_DHC_OP08_MATERIAL",
    "DHD_STATUS_WAITING_FOR_EXPLICIT_DHC_R11_MATERIAL",
    "DHD_STATUS_DHC_R11_REPAIR_REQUIRED",
    "DHD_STATUS_BLOCKED_DHC_R11_BODY_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS: Final[tuple[str, ...]] = (
    "DHD_DHC_OUTCOME_SCAN_CLEAR_SELECTED",
    "DHD_DHC_OUTCOME_R11_ONLY_NO_CURRENT_SELECTED_RESULT",
    "DHD_DHC_OUTCOME_SCAN_CLEAR_CAPABLE_TEST_VALIDATED_NOT_RUNTIME",
    "DHD_DHC_OUTCOME_WAITING_OR_INCOMPLETE",
    "DHD_DHC_OUTCOME_REPAIR_REQUIRED",
    "DHD_DHC_OUTCOME_NOT_CALLED",
    "DHD_DHC_OUTCOME_NON_DHR_LANE_ROUTE_PRESERVED",
    "DHD_DHC_OUTCOME_BLOCKED",
)
P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_DHC_OUTCOME_CLASSIFIED_READY",
    "DHD_STATUS_DHC_OUTCOME_R11_ONLY_NO_CURRENT_SELECTED_RESULT",
    "DHD_STATUS_DHC_OUTCOME_WAITING_REPAIR_OR_NOT_CALLED_STOPPED",
    "DHD_STATUS_DHC_OUTCOME_REPAIR_REQUIRED",
    "DHD_STATUS_DHC_OUTCOME_BLOCKED_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_DHR_OP06_CONSIDERATION_ELIGIBLE_WITH_EXPLICIT_SCAN_CLEAR_MATERIAL",
    "DHD_STATUS_DHR_OP06_CONSIDERATION_DEFERRED_PENDING_EXPLICIT_CURRENT_MATERIAL",
    "DHD_STATUS_DHR_OP06_CONSIDERATION_NOT_ALLOWED_FOR_WAITING_REPAIR_OR_NOT_CALLED",
    "DHD_STATUS_DHR_OP06_CONSIDERATION_BLOCKED_BY_IMPLICIT_FALLBACK_OR_AUTORUN",
)
P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_P7_READFEEL_RECONNECTION_ELIGIBLE",
    "DHD_STATUS_P7_READFEEL_RECONNECTION_ELIGIBLE_BUT_MIN_CASE_SET_REQUIRED",
    "DHD_STATUS_P7_READFEEL_RECONNECTION_DEFERRED_UNTIL_REPAIR_OR_WAIT_CLOSED",
    "DHD_STATUS_P7_READFEEL_RECONNECTION_BLOCKED_BY_UNSAFE_DHC_OUTCOME",
)
P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_DIRECTION_COMPARISON_CLOSED_READY",
    "DHD_STATUS_DIRECTION_COMPARISON_REPAIR_OR_WAIT_REQUIRED",
    "DHD_STATUS_DIRECTION_COMPARISON_CURRENT_MATERIAL_SELECTION_REQUIRED",
    "DHD_STATUS_DIRECTION_COMPARISON_BLOCKED_NO_TOUCH",
)
P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS: Final[tuple[str, ...]] = (
    "DHD_DECISION_DHR_OP06_CONSIDERATION_DESIGN_FIRST",
    "DHD_DECISION_P7_READFEEL_RECONNECTION_DESIGN_FIRST",
    "DHD_DECISION_EXPLICIT_CURRENT_DHC_MATERIAL_SELECTION_REQUIRED",
    "DHD_DECISION_REPAIR_OR_WAIT_BOUNDARY_REQUIRED",
    "DHD_DECISION_NON_DHR_LANE_ROUTE_PRESERVED",
    "DHD_DECISION_NO_TOUCH_REPAIR_OR_HOLD_REQUIRED",
)
P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_NO_TOUCH_NO_PROMOTION_NO_QUESTION_SYSTEM_GUARD_PASSED",
    "DHD_STATUS_REPAIR_REQUIRED_FOR_NO_TOUCH_GUARD_INPUTS",
    "DHD_STATUS_BLOCKED_NO_TOUCH_NO_PROMOTION_NO_QUESTION_SYSTEM_GUARD",
)
P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_STATUS_VALIDATION_PLAN_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED",
    "DHD_STATUS_REPAIR_REQUIRED_FOR_VALIDATION_PLAN_INPUTS",
    "DHD_STATUS_BLOCKED_VALIDATION_PLAN_BODYFREE_LEAK_PROMOTION_OR_AUTORUN",
)
P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    "DHD_OP08_DHR_OP06_CONSIDERATION_DESIGN_CLOSED_STOPPED",
    "DHD_OP08_P7_READFEEL_RECONNECTION_DESIGN_CLOSED_STOPPED",
    "DHD_OP08_EXPLICIT_CURRENT_DHC_MATERIAL_SELECTION_REQUIRED_CLOSED_STOPPED",
    "DHD_OP08_REPAIR_OR_WAIT_BOUNDARY_CLOSED_STOPPED",
    "DHD_OP08_NON_DHR_LANE_ROUTE_PRESERVED_CLOSED_STOPPED",
    "DHD_OP08_BLOCKED_NO_TOUCH_NO_PROMOTION",
)
P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS: Final[tuple[str, ...]] = (
    "DHR_OP06_consideration_detailed_design_without_call",
    "P7_readfeel_reconnection_product_QA_return_detailed_design",
    "explicit_current_DHC_OP08_or_current_OP05_material_selection_boundary",
    "explicit_DHR_OP04_or_OP05_material_repair_or_wait_boundary",
    "DHB_non_DHR_lane_route_preserved_decision_boundary",
    "no_touch_no_promotion_repair_boundary",
)
P7_R54_AHR_POST_DHC_DHD_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS
    )
)

P7_R54_AHR_POST_DHC_DHD_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
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
    "private_user_dictionary_text",
    "local_path",
    "absolute_path",
    "hash",
    "sha256",
    "stdout",
    "stderr",
    "traceback",
)
P7_R54_AHR_POST_DHC_DHD_NO_TOUCH_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "response_key_changed",
    "api_db_rn_runtime_response_key_changed",
)
P7_R54_AHR_POST_DHC_DHD_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
    "body_free",
    "raw_input_included",
    "comment_text_body_included",
    "question_text_included",
    "private_user_dictionary_text_included",
    "body_full_packet_generated",
)
P7_R54_AHR_POST_DHC_DHD_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "current_dhc_result_selected_here",
    "current_existing_dhr_op05_result_wrapper_selected_here",
    "dhr_op06_consideration_decided_here",
    "dhr_op06_builder_called_here",
    "dhr_op06_implicit_op05_fallback_used_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "dmd_r52_executed_here",
    "r52_actual_execution_started_here",
    "actual_review_started_here",
    "actual_rows_created_here",
    "question_need_observation_rows_created_here",
    "p7_readfeel_reconnection_decided_here",
    "p7_readfeel_evaluation_started_here",
    "next_runtime_execution_allowed_here",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized_here",
    "p7_complete",
    "release_allowed",
)
P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
)

P7_R54_AHR_POST_DHC_DHD_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_r0_r1_20260709.py",
)
P7_R54_AHR_POST_DHC_DHD_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op08_result_20260709.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_DHC_DHD_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_blind_qa_material_20260612.py",
    "tests/test_emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material_r10_r11_20260617.py",
    "tests/test_emlis_ai_complete_product_quality_scorecard_blind_qa.py",
)
P7_R54_AHR_POST_DHC_DHD_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhc_direction_decision_boundary_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
)
P7_R54_AHR_POST_DHC_DHD_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "R1 target validation may run the DHD R0/R1 skeleton test only",
    "R1 compileall may run the new DHD helper and adjacent reference modules",
    "R1 does not run DHC/DHR builders, P7 readfeel evaluation, full backend suite, RN contract, or real-device checks",
)

P7_R54_AHR_POST_DHC_DHD_R1_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "selected_phase_ref",
    "selected_stage_ref",
    "selected_design_target_ref",
    "selected_next_boundary_ref",
    "boundary_prefix_ref",
    "boundary_prefix_meaning_ref",
    "expected_next_required_step_ref",
    "current_execution_allowance_ref",
    "dhc_r11_not_dhr_op06_permission_ref",
    "dhc_validation_not_runtime_ref",
    "dhr_op06_builder_call_prohibition_ref",
    "dhr_op06_implicit_op05_fallback_prohibition_ref",
    "p7_readfeel_not_complete_ref",
    "dhc_r11_is_not_dhr_op06_permission",
    "dhc_validation_green_is_not_current_runtime_execution",
    "dhd_does_not_call_dhr_op06",
    "dhd_does_not_start_p8",
    "dhd_does_not_claim_p7_complete_or_release",
    "implemented_step_refs",
    "not_yet_implemented_step_refs",
    "dhd_step_refs",
    "dhd_schema_version_refs",
    "local_received_zip_refs",
    "support_material_refs",
    "not_stage_refs",
    "claim_boundary_refs",
    "not_claimed_boundary_refs",
    "fixed_non_promotion_refs",
    "dhc_builder_call_allowed_here",
    "dhc_result_synthesis_allowed_here",
    "dhc_r11_as_current_selected_result_allowed_here",
    "dhc_validation_green_as_runtime_allowed_here",
    "dhr_op05_runtime_call_allowed_here",
    "existing_dhr_op05_builder_runtime_call_allowed_here",
    "dhr_op06_consideration_decision_allowed_in_r1",
    "dhr_op06_builder_call_allowed_here",
    "dhr_op06_implicit_op05_fallback_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "p7_readfeel_reconnection_decision_allowed_in_r1",
    "p7_readfeel_evaluation_execution_allowed_here",
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
    "dhc_r11_result_memo_ref",
    "dhc_r10_closure_ref",
    "dhc_validation_summary_refs",
    "dhc_r11_recommended_next_work_candidate_ref",
    "dhc_op08_schema_version_ref",
    "dhc_op08_step_ref",
    "dhc_op08_allowed_status_refs",
    "dhc_outcome_class_refs",
    "dhc_op08_next_work_candidate_refs",
    "dhc_op08_builder_ref",
    "dhc_op08_builder_import_path_ref",
    "dhc_op08_builder_import_available",
    "existing_dhr_op05_builder_ref",
    "existing_dhr_op05_builder_import_path_ref",
    "existing_dhr_op05_builder_import_available",
    "existing_dhr_op05_schema_version_ref",
    "existing_dhr_op05_step_ref",
    "existing_dhr_op05_allowed_status_refs",
    "existing_dhr_op05_scan_clear_status_ref",
    "existing_dhr_op06_builder_ref",
    "existing_dhr_op06_builder_import_path_ref",
    "existing_dhr_op06_builder_import_available",
    "existing_dhr_op06_assert_ref",
    "existing_dhr_op06_assert_import_path_ref",
    "existing_dhr_op06_assert_import_available",
    "existing_dhr_op06_schema_version_ref",
    "existing_dhr_op06_step_ref",
    "existing_dhr_op06_allowed_status_refs",
    "existing_dhr_op06_branch_refs",
    "existing_dhr_op06_resolver_priority_refs",
    "existing_dhr_op06_implicit_op05_fallback_ref",
    "p7_readfeel_axis_refs",
    "expected_r11_only_direction_ref",
    "kept_not_promoted_direction_ref",
    "allowed_status_refs",
    "dhc_outcome_classification_refs",
    "direction_decision_refs",
    "next_design_candidate_refs",
    "forbidden_payload_key_refs",
    "no_touch_contract_keys",
    "body_free_marker_refs",
    "promotion_claim_field_refs",
    "required_false_flag_refs",
    "target_test_ref_refs",
    "selected_regression_test_ref_refs",
    "optional_product_readfeel_regression_ref_refs",
    "compileall_target_ref_refs",
    "validation_command_summary_refs",
    "public_contract",
    *P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS,
    "next_required_step",
    "body_free",
)


def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_DHC_DHD_DEFAULT_REVIEW_SESSION_ID,
        max_length=180,
    )


def build_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary(
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Return the DHD R0/R1 body-free skeleton without calling any builder."""

    safe_review_session_id = _safe_review_session_id(review_session_id)
    data: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_DHC_DHD_R1_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
        "step": P7_R54_AHR_POST_DHC_DHD_STEP,
        "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
        "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
        "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_R1_STEP_REF,
        "material_id": "p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_20260709",
        "review_session_id": safe_review_session_id,
        "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_phase_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_PHASE_REF,
        "selected_stage_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_DESIGN_TARGET_REF,
        "selected_next_boundary_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_NEXT_BOUNDARY_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_DHC_DHD_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_DHC_DHD_BOUNDARY_PREFIX_MEANING_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_DHC_DHD_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "current_execution_allowance_ref": P7_R54_AHR_POST_DHC_DHD_CURRENT_EXECUTION_ALLOWANCE_REF,
        "dhc_r11_not_dhr_op06_permission_ref": P7_R54_AHR_POST_DHC_DHD_DHC_R11_NOT_DHR_OP06_PERMISSION_REF,
        "dhc_validation_not_runtime_ref": P7_R54_AHR_POST_DHC_DHD_DHC_VALIDATION_NOT_RUNTIME_REF,
        "dhr_op06_builder_call_prohibition_ref": P7_R54_AHR_POST_DHC_DHD_DHR_OP06_BUILDER_CALL_PROHIBITION_REF,
        "dhr_op06_implicit_op05_fallback_prohibition_ref": P7_R54_AHR_POST_DHC_DHD_DHR_OP06_IMPLICIT_OP05_FALLBACK_PROHIBITION_REF,
        "p7_readfeel_not_complete_ref": P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_NOT_COMPLETE_REF,
        "dhc_r11_is_not_dhr_op06_permission": True,
        "dhc_validation_green_is_not_current_runtime_execution": True,
        "dhd_does_not_call_dhr_op06": True,
        "dhd_does_not_start_p8": True,
        "dhd_does_not_claim_p7_complete_or_release": True,
        "implemented_step_refs": P7_R54_AHR_POST_DHC_DHD_R0_R1_IMPLEMENTED_STEPS,
        "not_yet_implemented_step_refs": P7_R54_AHR_POST_DHC_DHD_R0_R1_NOT_YET_IMPLEMENTED_STEPS,
        "dhd_step_refs": P7_R54_AHR_POST_DHC_DHD_STEP_REFS,
        "dhd_schema_version_refs": P7_R54_AHR_POST_DHC_DHD_SCHEMA_VERSION_REFS,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_DHC_DHD_LOCAL_RECEIVED_ZIP_REFS),
        "support_material_refs": P7_R54_AHR_POST_DHC_DHD_SUPPORT_MATERIAL_REFS,
        "not_stage_refs": P7_R54_AHR_POST_DHC_DHD_NOT_STAGE_REFS,
        "claim_boundary_refs": P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS,
        "not_claimed_boundary_refs": P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS,
        "fixed_non_promotion_refs": P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS,
        "dhc_builder_call_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHC_BUILDER_CALL_ALLOWED_HERE,
        "dhc_result_synthesis_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHC_RESULT_SYNTHESIS_ALLOWED_HERE,
        "dhc_r11_as_current_selected_result_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHC_R11_AS_CURRENT_SELECTED_RESULT_ALLOWED_HERE,
        "dhc_validation_green_as_runtime_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHC_VALIDATION_GREEN_AS_RUNTIME_ALLOWED_HERE,
        "dhr_op05_runtime_call_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHR_OP05_RUNTIME_CALL_ALLOWED_HERE,
        "existing_dhr_op05_builder_runtime_call_allowed_here": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_RUNTIME_CALL_ALLOWED_HERE,
        "dhr_op06_consideration_decision_allowed_in_r1": P7_R54_AHR_POST_DHC_DHD_DHR_OP06_CONSIDERATION_DECISION_ALLOWED_IN_R1,
        "dhr_op06_builder_call_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHR_OP06_BUILDER_CALL_ALLOWED_HERE,
        "dhr_op06_implicit_op05_fallback_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHR_OP06_IMPLICIT_OP05_FALLBACK_ALLOWED_HERE,
        "dhr_op07_materialization_allowed_here": P7_R54_AHR_POST_DHC_DHD_DHR_OP07_MATERIALIZATION_ALLOWED_HERE,
        "dmd_r52_execution_allowed_here": P7_R54_AHR_POST_DHC_DHD_DMD_R52_EXECUTION_ALLOWED_HERE,
        "actual_review_start_allowed_here": P7_R54_AHR_POST_DHC_DHD_ACTUAL_REVIEW_START_ALLOWED_HERE,
        "actual_rows_creation_allowed_here": P7_R54_AHR_POST_DHC_DHD_ACTUAL_ROWS_CREATION_ALLOWED_HERE,
        "question_need_observation_rows_creation_allowed_here": P7_R54_AHR_POST_DHC_DHD_QUESTION_NEED_OBSERVATION_ROWS_CREATION_ALLOWED_HERE,
        "p7_readfeel_reconnection_decision_allowed_in_r1": P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_RECONNECTION_DECISION_ALLOWED_IN_R1,
        "p7_readfeel_evaluation_execution_allowed_here": P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_EVALUATION_EXECUTION_ALLOWED_HERE,
        "p8_question_design_allowed_here": P7_R54_AHR_POST_DHC_DHD_P8_QUESTION_DESIGN_ALLOWED_HERE,
        "p8_question_implementation_allowed_here": P7_R54_AHR_POST_DHC_DHD_P8_QUESTION_IMPLEMENTATION_ALLOWED_HERE,
        "question_text_materialization_allowed_here": P7_R54_AHR_POST_DHC_DHD_QUESTION_TEXT_MATERIALIZATION_ALLOWED_HERE,
        "api_db_rn_runtime_response_key_change_allowed_here": P7_R54_AHR_POST_DHC_DHD_API_DB_RN_RUNTIME_RESPONSE_KEY_CHANGE_ALLOWED_HERE,
        "json_schema_file_creation_allowed_here": P7_R54_AHR_POST_DHC_DHD_JSON_SCHEMA_FILE_CREATION_ALLOWED_HERE,
        "p7_complete_allowed_here": P7_R54_AHR_POST_DHC_DHD_P7_COMPLETE_ALLOWED_HERE,
        "release_decision_allowed_here": P7_R54_AHR_POST_DHC_DHD_RELEASE_DECISION_ALLOWED_HERE,
        "full_backend_suite_green_claim_allowed_here": P7_R54_AHR_POST_DHC_DHD_FULL_BACKEND_SUITE_GREEN_CLAIM_ALLOWED_HERE,
        "rn_contract_green_claim_allowed_here": P7_R54_AHR_POST_DHC_DHD_RN_CONTRACT_GREEN_CLAIM_ALLOWED_HERE,
        "rn_real_device_modal_verification_claim_allowed_here": P7_R54_AHR_POST_DHC_DHD_RN_REAL_DEVICE_MODAL_VERIFICATION_CLAIM_ALLOWED_HERE,
        "dhc_r11_result_memo_ref": P7_R54_AHR_POST_DHC_DHD_DHC_R11_RESULT_MEMO_REF,
        "dhc_r10_closure_ref": P7_R54_AHR_POST_DHC_DHD_DHC_R10_CLOSURE_REF,
        "dhc_validation_summary_refs": P7_R54_AHR_POST_DHC_DHD_DHC_VALIDATION_SUMMARY_REFS,
        "dhc_r11_recommended_next_work_candidate_ref": P7_R54_AHR_POST_DHC_DHD_DHC_R11_RECOMMENDED_NEXT_WORK_CANDIDATE_REF,
        "dhc_op08_schema_version_ref": P7_R54_AHR_POST_DHC_DHD_DHC_OP08_SCHEMA_VERSION_REF,
        "dhc_op08_step_ref": P7_R54_AHR_POST_DHC_DHD_DHC_OP08_STEP_REF,
        "dhc_op08_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_DHC_OP08_ALLOWED_STATUS_REFS,
        "dhc_outcome_class_refs": P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASS_REFS,
        "dhc_op08_next_work_candidate_refs": P7_R54_AHR_POST_DHC_DHD_DHC_OP08_NEXT_WORK_CANDIDATE_REFS,
        "dhc_op08_builder_ref": P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF,
        "dhc_op08_builder_import_path_ref": P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_IMPORT_PATH_REF,
        "dhc_op08_builder_import_available": hasattr(dhc, P7_R54_AHR_POST_DHC_DHD_DHC_OP08_BUILDER_REF),
        "existing_dhr_op05_builder_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF,
        "existing_dhr_op05_builder_import_path_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_IMPORT_PATH_REF,
        "existing_dhr_op05_builder_import_available": hasattr(dhr, P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_BUILDER_REF),
        "existing_dhr_op05_schema_version_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCHEMA_VERSION_REF,
        "existing_dhr_op05_step_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_STEP_REF,
        "existing_dhr_op05_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_ALLOWED_STATUS_REFS,
        "existing_dhr_op05_scan_clear_status_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF,
        "existing_dhr_op06_builder_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF,
        "existing_dhr_op06_builder_import_path_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_IMPORT_PATH_REF,
        "existing_dhr_op06_builder_import_available": hasattr(dhr, P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF),
        "existing_dhr_op06_assert_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ASSERT_REF,
        "existing_dhr_op06_assert_import_path_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ASSERT_IMPORT_PATH_REF,
        "existing_dhr_op06_assert_import_available": hasattr(dhr, P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ASSERT_REF),
        "existing_dhr_op06_schema_version_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_SCHEMA_VERSION_REF,
        "existing_dhr_op06_step_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_STEP_REF,
        "existing_dhr_op06_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ALLOWED_STATUS_REFS,
        "existing_dhr_op06_branch_refs": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BRANCH_REFS,
        "existing_dhr_op06_resolver_priority_refs": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_RESOLVER_PRIORITY_REFS,
        "existing_dhr_op06_implicit_op05_fallback_ref": P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_IMPLICIT_OP05_FALLBACK_REF,
        "p7_readfeel_axis_refs": P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_AXIS_REFS,
        "expected_r11_only_direction_ref": P7_R54_AHR_POST_DHC_DHD_EXPECTED_R11_ONLY_DIRECTION_REF,
        "kept_not_promoted_direction_ref": P7_R54_AHR_POST_DHC_DHD_KEPT_NOT_PROMOTED_DIRECTION_REF,
        "allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_ALLOWED_STATUS_REFS,
        "dhc_outcome_classification_refs": P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS,
        "direction_decision_refs": P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS,
        "next_design_candidate_refs": P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS,
        "forbidden_payload_key_refs": P7_R54_AHR_POST_DHC_DHD_FORBIDDEN_PAYLOAD_KEY_REFS,
        "no_touch_contract_keys": P7_R54_AHR_POST_DHC_DHD_NO_TOUCH_CONTRACT_KEYS,
        "body_free_marker_refs": P7_R54_AHR_POST_DHC_DHD_BODY_FREE_MARKER_REFS,
        "promotion_claim_field_refs": P7_R54_AHR_POST_DHC_DHD_PROMOTION_CLAIM_FIELD_REFS,
        "required_false_flag_refs": P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS,
        "target_test_ref_refs": P7_R54_AHR_POST_DHC_DHD_TARGET_TEST_REF_REFS,
        "selected_regression_test_ref_refs": P7_R54_AHR_POST_DHC_DHD_SELECTED_REGRESSION_TEST_REF_REFS,
        "optional_product_readfeel_regression_ref_refs": P7_R54_AHR_POST_DHC_DHD_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS,
        "compileall_target_ref_refs": P7_R54_AHR_POST_DHC_DHD_COMPILEALL_TARGET_REF_REFS,
        "validation_command_summary_refs": P7_R54_AHR_POST_DHC_DHD_VALIDATION_COMMAND_SUMMARY_REFS,
        "public_contract": public_contract_flags(),
        "next_required_step": P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF,
        "body_free": True,
    }
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS:
        data[key] = False
    return data


def assert_p7_r54_ahr_post_dhc_dhd_r1_helper_skeleton_constants_summary_contract(
    data: Mapping[str, Any],
) -> bool:
    """Validate R0/R1 without validating or executing future DHD-OP00+."""

    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_R1_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_R1_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 schema version mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_R1_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 operation step mismatch")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 must remain body-free")
    if data.get("source_mode") != P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 must not require/check GitHub")
    if not isinstance(data.get("review_session_id"), str) or not data.get("review_session_id"):
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 review session id missing")
    if data.get("boundary_prefix_ref") != P7_R54_AHR_POST_DHC_DHD_BOUNDARY_PREFIX_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 boundary prefix mismatch")
    if data.get("current_execution_allowance_ref") != "none":
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 execution allowance must remain none")
    if tuple(data.get("implemented_step_refs", ())) != P7_R54_AHR_POST_DHC_DHD_R0_R1_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_step_refs", ())) != P7_R54_AHR_POST_DHC_DHD_R0_R1_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 must leave DHD-OP00..OP08 not implemented")
    if tuple(data.get("dhd_step_refs", ())) != P7_R54_AHR_POST_DHC_DHD_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 step refs mismatch")
    if tuple(data.get("dhd_schema_version_refs", ())) != P7_R54_AHR_POST_DHC_DHD_SCHEMA_VERSION_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 schema refs mismatch")
    for key in (
        "dhc_r11_is_not_dhr_op06_permission",
        "dhc_validation_green_is_not_current_runtime_execution",
        "dhd_does_not_call_dhr_op06",
        "dhd_does_not_start_p8",
        "dhd_does_not_claim_p7_complete_or_release",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostDHC-DHD-R1 required boundary changed: {key}")
    for key in (
        "dhc_builder_call_allowed_here",
        "dhc_result_synthesis_allowed_here",
        "dhc_r11_as_current_selected_result_allowed_here",
        "dhc_validation_green_as_runtime_allowed_here",
        "dhr_op05_runtime_call_allowed_here",
        "existing_dhr_op05_builder_runtime_call_allowed_here",
        "dhr_op06_consideration_decision_allowed_in_r1",
        "dhr_op06_builder_call_allowed_here",
        "dhr_op06_implicit_op05_fallback_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "p7_readfeel_reconnection_decision_allowed_in_r1",
        "p7_readfeel_evaluation_execution_allowed_here",
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
            raise ValueError(f"P7-R54-AHR-PostDHC-DHD-R1 allowed flag must remain false: {key}")
    if data.get("dhc_r11_result_memo_ref") != P7_R54_AHR_POST_DHC_DHD_DHC_R11_RESULT_MEMO_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHC R11 ref mismatch")
    if data.get("dhc_op08_schema_version_ref") != P7_R54_AHR_POST_DHC_DHD_DHC_OP08_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHC-OP08 schema ref mismatch")
    if data.get("dhc_op08_step_ref") != P7_R54_AHR_POST_DHC_DHD_DHC_OP08_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHC-OP08 step ref mismatch")
    if tuple(data.get("dhc_op08_allowed_status_refs", ())) != P7_R54_AHR_POST_DHC_DHD_DHC_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHC-OP08 status refs mismatch")
    if data.get("dhc_op08_builder_import_available") is not True:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHC-OP08 string ref unavailable")
    if data.get("existing_dhr_op05_builder_import_available") is not True:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP05 string ref unavailable")
    if data.get("existing_dhr_op05_schema_version_ref") != P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP05 schema ref mismatch")
    if data.get("existing_dhr_op06_builder_ref") != P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BUILDER_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP06 builder ref mismatch")
    if data.get("existing_dhr_op06_builder_import_available") is not True:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP06 string ref unavailable")
    if data.get("existing_dhr_op06_assert_import_available") is not True:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP06 assert string ref unavailable")
    if data.get("existing_dhr_op06_schema_version_ref") != P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_SCHEMA_VERSION_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP06 schema ref mismatch")
    if tuple(data.get("existing_dhr_op06_allowed_status_refs", ())) != P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP06 status refs mismatch")
    if tuple(data.get("existing_dhr_op06_branch_refs", ())) != P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP06_BRANCH_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 DHR-OP06 branch refs mismatch")
    if tuple(data.get("allowed_status_refs", ())) != P7_R54_AHR_POST_DHC_DHD_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 allowed status refs mismatch")
    if tuple(data.get("dhc_outcome_classification_refs", ())) != P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 outcome refs mismatch")
    if tuple(data.get("direction_decision_refs", ())) != P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 decision refs mismatch")
    if tuple(data.get("next_design_candidate_refs", ())) != P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 next candidate refs mismatch")
    if tuple(data.get("forbidden_payload_key_refs", ())) != P7_R54_AHR_POST_DHC_DHD_FORBIDDEN_PAYLOAD_KEY_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 forbidden payload refs mismatch")
    if tuple(data.get("no_touch_contract_keys", ())) != P7_R54_AHR_POST_DHC_DHD_NO_TOUCH_CONTRACT_KEYS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 no-touch refs mismatch")
    if tuple(data.get("promotion_claim_field_refs", ())) != P7_R54_AHR_POST_DHC_DHD_PROMOTION_CLAIM_FIELD_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 promotion refs mismatch")
    if tuple(data.get("target_test_ref_refs", ())) != P7_R54_AHR_POST_DHC_DHD_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 target refs mismatch")
    if tuple(data.get("compileall_target_ref_refs", ())) != P7_R54_AHR_POST_DHC_DHD_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 compileall refs mismatch")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 public contract changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF:
        raise ValueError("P7-R54-AHR-PostDHC-DHD-R1 next step must be DHD-OP00")
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHC-DHD-R1 forbidden flag must remain false: {key}")
    for key in P7_R54_AHR_POST_DHC_DHD_NO_TOUCH_CONTRACT_KEYS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostDHC-DHD-R1 no-touch key must remain false: {key}")
    return True


# ---------------------------------------------------------------------------
# R2: DHD-OP00 / DHD-OP01 only.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHC_DHD_R2_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op00_op01_20260709.py",
)
P7_R54_AHR_POST_DHC_DHD_R2_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhc_direction_decision_boundary_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
    "services/ai_inference/emlis_ai_p7_contracts.py",
)
P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_WAIT_FOR_EXPLICIT_DHC_R11_MATERIAL_REF: Final = (
    "wait_for_explicit_DHC_R11_material_before_DHD_OP08_closure_without_downstream"
)
P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_DHC_R11_INTAKE_REF: Final = (
    "repair_DHC_R11_intake_before_DHD_OP08_closure_without_downstream"
)
P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_DHC_R11_INTAKE_REF: Final = (
    "blocked_DHC_R11_body_leak_promotion_or_autorun_then_DHD_OP08_stop"
)

P7_R54_AHR_POST_DHC_DHD_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_R0_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_R1_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_R0_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_R1_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP00_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key != "dhd_op00_implemented"
)
P7_R54_AHR_POST_DHC_DHD_OP01_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key not in {"dhd_op00_implemented", "dhd_op01_implemented"}
)

P7_R54_AHR_POST_DHC_DHD_DHC_R11_ALLOWED_NEXT_WORK_CANDIDATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_DHC_R11_RECOMMENDED_NEXT_WORK_CANDIDATE_REF,
    P7_R54_AHR_POST_DHC_DHD_SELECTED_NEXT_BOUNDARY_REF,
)
P7_R54_AHR_POST_DHC_DHD_DHC_R11_AUTORUN_OR_PROMOTION_KEY_REFS: Final[tuple[str, ...]] = (
    "dhc_builder_call",
    "dhc_result_synthesis",
    "dhr_op05_runtime_call",
    "existing_dhr_op05_builder_runtime_call",
    "dhr_op06_call",
    "dhr_op06_builder_call",
    "dhr_op06_called_here",
    "dhr_op07_materialization",
    "dmd_execution",
    "r52_actual_execution",
    "actual_review_start",
    "actual_rows_creation",
    "question_need_observation_rows_creation",
    "p7_readfeel_evaluation_start",
    "p8_start",
    "p8_question_design",
    "p8_question_implementation",
    "question_text_materialization",
    "p7_complete",
    "release_decision",
)

P7_R54_AHR_POST_DHC_DHD_OP00_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "selected_phase_ref",
    "selected_stage_ref",
    "selected_design_target_ref",
    "selected_next_boundary_ref",
    "boundary_prefix_ref",
    "boundary_prefix_meaning_ref",
    "current_execution_allowance_ref",
    "dhc_r11_result_memo_ref",
    "dhc_r10_closure_ref",
    "dhc_validation_summary_refs",
    "dhd_op00_status_ref",
    "dhd_op00_allowed_status_refs",
    "dhd_op00_allowed_status_ref_count",
    "dhd_op00_scope_confirmed",
    "dhd_op00_repair_required",
    "dhd_op00_bodyfree_leak_promotion_or_autorun_blocked",
    "dhc_r11_is_not_dhr_op06_permission",
    "dhc_validation_green_is_not_current_runtime_execution",
    "dhd_does_not_call_dhr_op06",
    "dhd_does_not_start_p8",
    "dhd_does_not_claim_p7_complete_or_release",
    "dhc_builder_call_allowed_here",
    "dhc_result_synthesis_allowed_here",
    "dhc_r11_as_current_selected_result_allowed_here",
    "dhc_validation_green_as_runtime_allowed_here",
    "dhr_op05_runtime_call_allowed_here",
    "existing_dhr_op05_builder_runtime_call_allowed_here",
    "dhr_op06_consideration_decision_allowed_in_r1",
    "dhr_op06_builder_call_allowed_here",
    "dhr_op06_implicit_op05_fallback_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "p7_readfeel_reconnection_decision_allowed_in_r1",
    "p7_readfeel_evaluation_execution_allowed_here",
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
    "dhd_op00_does_not_intake_dhc_r11_material",
    "dhd_op00_does_not_synthesize_dhc_result",
    "dhd_op00_does_not_call_dhc_builder",
    "dhd_op00_does_not_call_dhr_op05",
    "dhd_op00_does_not_call_existing_dhr_op05_builder",
    "dhd_op00_does_not_call_dhr_op06_builder",
    "dhd_op00_does_not_use_dhr_op06_implicit_op05_fallback",
    "dhd_op00_does_not_run_p7_readfeel_evaluation",
    "dhd_op00_does_not_start_p8_question_system",
    "dhd_op00_does_not_change_api_db_rn_runtime_response_key",
    "dhd_op00_does_not_create_json_schema_file",
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
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP01_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op00_schema_version_ref",
    "op00_material_ref",
    "op00_next_required_step_ref",
    "dhc_r11_material_supplied",
    "dhc_r11_material_present",
    "dhc_r11_contract_valid",
    "dhc_r11_material_ref",
    "dhc_r11_source_mode_ref",
    "dhc_r11_current_execution_allowance_ref",
    "dhc_r11_dhr_op06_call_ref",
    "dhc_r11_dhr_op07_materialization_ref",
    "dhc_r11_p8_question_design_ref",
    "dhc_r11_release_decision_ref",
    "dhc_r11_recommended_next_work_candidate_ref",
    "dhc_r11_body_free",
    "explicit_dhc_op08_material_supplied",
    "explicit_dhc_op08_material_present",
    "explicit_dhc_op08_material_ref",
    "current_existing_dhr_op05_result_wrapper_supplied",
    "current_existing_dhr_op05_result_wrapper_present",
    "current_existing_dhr_op05_result_wrapper_ref",
    "optional_material_shapes_valid",
    "dhc_r11_input_forbidden_payload_key_path_refs",
    "dhc_r11_input_forbidden_payload_key_path_count",
    "dhc_r11_input_body_like_value_path_refs",
    "dhc_r11_input_body_like_value_path_count",
    "dhc_r11_input_promotion_or_autorun_claim_path_refs",
    "dhc_r11_input_promotion_or_autorun_claim_path_count",
    "dhc_r11_input_no_touch_mutation_path_refs",
    "dhc_r11_input_no_touch_mutation_path_count",
    "dhd_op01_status_ref",
    "bodyfree_dhc_r11_closure_material_intake_status_ref",
    "dhd_op01_allowed_status_refs",
    "dhd_op01_allowed_status_ref_count",
    "dhd_op01_intake_ready",
    "dhd_op01_intake_ready_with_explicit_dhc_op08_material",
    "dhd_op01_ready_for_op02_dhc_outcome_check",
    "dhd_op01_waiting_for_explicit_dhc_r11_material",
    "dhd_op01_repair_required",
    "dhd_op01_bodyfree_leak_promotion_or_autorun_blocked",
    "dhd_op01_reason_refs",
    "dhd_op01_reason_ref_count",
    "dhd_op01_blocker_refs",
    "dhd_op01_blocker_ref_count",
    "dhc_builder_call_allowed_here",
    "dhc_result_synthesis_allowed_here",
    "dhc_r11_as_current_selected_result_allowed_here",
    "dhc_validation_green_as_runtime_allowed_here",
    "dhr_op05_runtime_call_allowed_here",
    "existing_dhr_op05_builder_runtime_call_allowed_here",
    "dhr_op06_consideration_decision_allowed_in_r1",
    "dhr_op06_builder_call_allowed_here",
    "dhr_op06_implicit_op05_fallback_allowed_here",
    "dhr_op07_materialization_allowed_here",
    "dmd_r52_execution_allowed_here",
    "actual_review_start_allowed_here",
    "actual_rows_creation_allowed_here",
    "question_need_observation_rows_creation_allowed_here",
    "p7_readfeel_reconnection_decision_allowed_in_r1",
    "p7_readfeel_evaluation_execution_allowed_here",
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
    "dhd_op01_does_not_synthesize_dhc_result",
    "dhd_op01_does_not_call_dhc_builder",
    "dhd_op01_does_not_call_dhr_op05",
    "dhd_op01_does_not_call_existing_dhr_op05_builder",
    "dhd_op01_does_not_call_dhr_op06_builder",
    "dhd_op01_does_not_use_dhr_op06_implicit_op05_fallback",
    "dhd_op01_does_not_select_current_dhc_result",
    "dhd_op01_does_not_select_current_dhr_op05_wrapper",
    "dhd_op01_does_not_decide_dhr_op06_consideration",
    "dhd_op01_does_not_decide_or_run_p7_readfeel_reconnection",
    "dhd_op01_does_not_execute_dmd_r52_or_release",
    "dhd_op01_does_not_start_actual_review",
    "dhd_op01_does_not_create_actual_rows",
    "dhd_op01_does_not_create_question_need_observation_rows",
    "dhd_op01_does_not_start_p8_question_system",
    "dhd_op01_does_not_materialize_question_text",
    "dhd_op01_does_not_change_api_db_rn_runtime_response_key",
    "dhd_op01_does_not_create_json_schema_file",
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
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP00_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP00_REQUIRED_FALSE_FLAG_REFS
    )
)
P7_R54_AHR_POST_DHC_DHD_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP01_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP01_REQUIRED_FALSE_FLAG_REFS
    )
)


def _clean_ref(value: Any, *, default: str = "missing", max_length: int = 320) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _dedupe_clean_refs(values: Sequence[Any], *, max_length: int = 360) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for value in values:
        ref = _clean_ref(value, default="", max_length=max_length)
        if ref and ref not in seen:
            refs.append(ref)
            seen.add(ref)
    return refs


def _false_flags(refs: Sequence[str]) -> dict[str, bool]:
    return {key: False for key in refs}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_DHC_DHD_NO_TOUCH_CONTRACT_KEYS}


def _body_free_markers() -> dict[str, bool]:
    markers = {key: False for key in P7_R54_AHR_POST_DHC_DHD_BODY_FREE_MARKER_REFS}
    markers["body_free"] = True
    return markers


def _required_fields_present(
    data: Mapping[str, Any], *, required: Sequence[str], source: str
) -> None:
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:8]}")


def _scan_forbidden_payload_key_paths(value: Any, *, path: str) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_DHC_DHD_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_body_like_value_paths(value: Any, *, path: str) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if (
                str(key) in P7_R54_AHR_POST_DHC_DHD_FORBIDDEN_PAYLOAD_KEY_REFS
                and child not in (None, "", False)
            ):
                paths.append(child_path)
            paths.extend(_scan_body_like_value_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_body_like_value_paths(child, path=f"{path}[{index}]"))
    return paths


def _is_none_or_false_ref(value: Any) -> bool:
    if value is None or value is False:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "none", "false"}
    return False


def _scan_promotion_or_autorun_claim_paths(value: Any, *, path: str) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_ref = str(key)
            child_path = f"{path}.{key_ref}"
            if key_ref in P7_R54_AHR_POST_DHC_DHD_PROMOTION_CLAIM_FIELD_REFS and child is True:
                paths.append(child_path)
            if (
                key_ref in P7_R54_AHR_POST_DHC_DHD_DHC_R11_AUTORUN_OR_PROMOTION_KEY_REFS
                and not _is_none_or_false_ref(child)
            ):
                paths.append(child_path)
            if key_ref in {"current_execution_allowance", "current_execution_allowance_ref"}:
                if not _is_none_or_false_ref(child):
                    paths.append(child_path)
            paths.extend(_scan_promotion_or_autorun_claim_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_promotion_or_autorun_claim_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_no_touch_mutation_paths(value: Any, *, path: str) -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in P7_R54_AHR_POST_DHC_DHD_NO_TOUCH_CONTRACT_KEYS and child is True:
                paths.append(child_path)
            paths.extend(_scan_no_touch_mutation_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_no_touch_mutation_paths(child, path=f"{path}[{index}]"))
    return paths


def _op00_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhc_dhd_op00_post_dhc_basis_no_execution_refreeze_contract(data)
    except ValueError:
        return False
    return True


def _dhc_r11_material_contract_valid(material: Any) -> bool:
    if not isinstance(material, Mapping):
        return False
    required = (
        "source_mode",
        "current_execution_allowance",
        "dhr_op06_call",
        "dhr_op07_materialization",
        "p8_question_design",
        "release_decision",
        "recommended_next_work_candidate",
        "body_free",
    )
    if any(key not in material for key in required):
        return False
    if material.get("source_mode") != P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE:
        return False
    if material.get("body_free") is not True:
        return False
    if not _is_none_or_false_ref(material.get("current_execution_allowance")):
        return False
    for key in (
        "dhr_op06_call",
        "dhr_op07_materialization",
        "p8_question_design",
        "release_decision",
    ):
        if not _is_none_or_false_ref(material.get(key)):
            return False
    candidate_ref = _clean_ref(
        material.get("recommended_next_work_candidate"), default="", max_length=400
    )
    return candidate_ref in P7_R54_AHR_POST_DHC_DHD_DHC_R11_ALLOWED_NEXT_WORK_CANDIDATE_REFS


def build_p7_r54_ahr_post_dhc_dhd_op00_post_dhc_basis_no_execution_refreeze(
    *,
    review_session_id: str | None = None,
    dhc_r11_result_memo_ref: str | None = None,
    dhc_r10_closure_ref: str | None = None,
    dhc_validation_summary_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build DHD-OP00 without intaking DHC material or calling any builder."""

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP00_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP00_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op00_post_dhc_basis_no_execution_refreeze_20260709",
            "review_session_id": _safe_review_session_id(review_session_id),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "selected_phase_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_PHASE_REF,
            "selected_stage_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_STAGE_REF,
            "selected_design_target_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_DESIGN_TARGET_REF,
            "selected_next_boundary_ref": P7_R54_AHR_POST_DHC_DHD_SELECTED_NEXT_BOUNDARY_REF,
            "boundary_prefix_ref": P7_R54_AHR_POST_DHC_DHD_BOUNDARY_PREFIX_REF,
            "boundary_prefix_meaning_ref": P7_R54_AHR_POST_DHC_DHD_BOUNDARY_PREFIX_MEANING_REF,
            "current_execution_allowance_ref": "none",
            "dhc_r11_result_memo_ref": _clean_ref(
                dhc_r11_result_memo_ref,
                default=P7_R54_AHR_POST_DHC_DHD_DHC_R11_RESULT_MEMO_REF,
                max_length=400,
            ),
            "dhc_r10_closure_ref": _clean_ref(
                dhc_r10_closure_ref,
                default=P7_R54_AHR_POST_DHC_DHD_DHC_R10_CLOSURE_REF,
                max_length=400,
            ),
            "dhc_validation_summary_refs": _dedupe_clean_refs(
                dhc_validation_summary_refs
                if dhc_validation_summary_refs is not None
                else P7_R54_AHR_POST_DHC_DHD_DHC_VALIDATION_SUMMARY_REFS,
                max_length=400,
            ),
            "dhd_op00_status_ref": P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS[0],
            "dhd_op00_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS,
            "dhd_op00_allowed_status_ref_count": len(P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS),
            "dhd_op00_scope_confirmed": True,
            "dhd_op00_repair_required": False,
            "dhd_op00_bodyfree_leak_promotion_or_autorun_blocked": False,
            "dhc_r11_is_not_dhr_op06_permission": True,
            "dhc_validation_green_is_not_current_runtime_execution": True,
            "dhd_does_not_call_dhr_op06": True,
            "dhd_does_not_start_p8": True,
            "dhd_does_not_claim_p7_complete_or_release": True,
            "dhc_builder_call_allowed_here": False,
            "dhc_result_synthesis_allowed_here": False,
            "dhc_r11_as_current_selected_result_allowed_here": False,
            "dhc_validation_green_as_runtime_allowed_here": False,
            "dhr_op05_runtime_call_allowed_here": False,
            "existing_dhr_op05_builder_runtime_call_allowed_here": False,
            "dhr_op06_consideration_decision_allowed_in_r1": False,
            "dhr_op06_builder_call_allowed_here": False,
            "dhr_op06_implicit_op05_fallback_allowed_here": False,
            "dhr_op07_materialization_allowed_here": False,
            "dmd_r52_execution_allowed_here": False,
            "actual_review_start_allowed_here": False,
            "actual_rows_creation_allowed_here": False,
            "question_need_observation_rows_creation_allowed_here": False,
            "p7_readfeel_reconnection_decision_allowed_in_r1": False,
            "p7_readfeel_evaluation_execution_allowed_here": False,
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
            "dhd_op00_does_not_intake_dhc_r11_material": True,
            "dhd_op00_does_not_synthesize_dhc_result": True,
            "dhd_op00_does_not_call_dhc_builder": True,
            "dhd_op00_does_not_call_dhr_op05": True,
            "dhd_op00_does_not_call_existing_dhr_op05_builder": True,
            "dhd_op00_does_not_call_dhr_op06_builder": True,
            "dhd_op00_does_not_use_dhr_op06_implicit_op05_fallback": True,
            "dhd_op00_does_not_run_p7_readfeel_evaluation": True,
            "dhd_op00_does_not_start_p8_question_system": True,
            "dhd_op00_does_not_change_api_db_rn_runtime_response_key": True,
            "dhd_op00_does_not_create_json_schema_file": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS),
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP00_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP00_NOT_YET_IMPLEMENTED_STEPS),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R2_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R2_COMPILEALL_TARGET_REF_REFS),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "next_required_step": P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op00_post_dhc_basis_no_execution_refreeze_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert the DHD-OP00 no-execution refreeze contract."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP00_REQUIRED_FIELD_REFS, source="DHD-OP00"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP00 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP00_SCHEMA_VERSION:
        raise ValueError("DHD-OP00 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP00_STEP_REF:
        raise ValueError("DHD-OP00 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE:
        raise ValueError("DHD-OP00 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHD-OP00 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHD-OP00 must remain body-free")
    if data.get("current_execution_allowance_ref") != "none":
        raise ValueError("DHD-OP00 current execution allowance must remain none")
    if data.get("dhd_op00_status_ref") != P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS[0]:
        raise ValueError("DHD-OP00 must remain scope-refrozen stopped")
    if tuple(data.get("dhd_op00_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP00 allowed status refs changed")
    if data.get("dhd_op00_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHC_DHD_OP00_ALLOWED_STATUS_REFS):
        raise ValueError("DHD-OP00 allowed status count changed")
    for key in (
        "dhd_op00_scope_confirmed",
        "dhc_r11_is_not_dhr_op06_permission",
        "dhc_validation_green_is_not_current_runtime_execution",
        "dhd_does_not_call_dhr_op06",
        "dhd_does_not_start_p8",
        "dhd_does_not_claim_p7_complete_or_release",
        "dhd_op00_does_not_intake_dhc_r11_material",
        "dhd_op00_does_not_synthesize_dhc_result",
        "dhd_op00_does_not_call_dhc_builder",
        "dhd_op00_does_not_call_dhr_op05",
        "dhd_op00_does_not_call_existing_dhr_op05_builder",
        "dhd_op00_does_not_call_dhr_op06_builder",
        "dhd_op00_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op00_does_not_run_p7_readfeel_evaluation",
        "dhd_op00_does_not_start_p8_question_system",
        "dhd_op00_does_not_change_api_db_rn_runtime_response_key",
        "dhd_op00_does_not_create_json_schema_file",
        "dhd_op00_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP00 required true field changed: {key}")
    for key in (
        "dhd_op00_repair_required",
        "dhd_op00_bodyfree_leak_promotion_or_autorun_blocked",
        "dhc_builder_call_allowed_here",
        "dhc_result_synthesis_allowed_here",
        "dhc_r11_as_current_selected_result_allowed_here",
        "dhc_validation_green_as_runtime_allowed_here",
        "dhr_op05_runtime_call_allowed_here",
        "existing_dhr_op05_builder_runtime_call_allowed_here",
        "dhr_op06_consideration_decision_allowed_in_r1",
        "dhr_op06_builder_call_allowed_here",
        "dhr_op06_implicit_op05_fallback_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "p7_readfeel_reconnection_decision_allowed_in_r1",
        "p7_readfeel_evaluation_execution_allowed_here",
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
            raise ValueError(f"DHD-OP00 forbidden allowance changed: {key}")
    for key in P7_R54_AHR_POST_DHC_DHD_OP00_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHD-OP00 required false flag changed: {key}")
    for field, count_field in (
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP00 count field changed: {count_field}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP00_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP00 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R2_TARGET_TEST_REF_REFS:
        raise ValueError("DHD-OP00 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R2_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHD-OP00 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHD-OP00 public contract changed")
    if any(value is not False for value in (data.get("dhd_no_touch_contract") or {}).values()):
        raise ValueError("DHD-OP00 no-touch contract must remain false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHD-OP00 body-free marker changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF:
        raise ValueError("DHD-OP00 next step must be DHD-OP01")
    return True


def _dhd_op01_status(
    *,
    op00_valid: bool,
    r11_supplied: bool,
    r11_present: bool,
    r11_valid: bool,
    optional_shapes_valid: bool,
    explicit_dhc_op08_present: bool,
    scan_blocked: bool,
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if scan_blocked:
        blockers.append("dhd_op01_bodyfree_leak_promotion_or_autorun_detected")
        return (
            P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[4],
            reasons,
            blockers,
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_DHC_R11_INTAKE_REF,
        )
    if not op00_valid:
        blockers.append("dhd_op01_op00_refreeze_missing_or_invalid")
        return (
            P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[3],
            reasons,
            blockers,
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_DHC_R11_INTAKE_REF,
        )
    if not r11_supplied:
        reasons.append("dhd_op01_waiting_for_explicit_dhc_r11_bodyfree_material")
        return (
            P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[2],
            reasons,
            blockers,
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_WAIT_FOR_EXPLICIT_DHC_R11_MATERIAL_REF,
        )
    if not r11_present or not r11_valid or not optional_shapes_valid:
        blockers.append("dhd_op01_dhc_r11_or_optional_material_shape_invalid")
        return (
            P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[3],
            reasons,
            blockers,
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_DHC_R11_INTAKE_REF,
        )
    if explicit_dhc_op08_present:
        reasons.append("dhd_op01_dhc_r11_intake_ready_with_explicit_dhc_op08_material_unselected")
        return (
            P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[1],
            reasons,
            blockers,
            P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF,
        )
    reasons.append("dhd_op01_dhc_r11_intake_ready_without_current_result_synthesis")
    return (
        P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[0],
        reasons,
        blockers,
        P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF,
    )


def build_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake(
    *,
    op00_post_dhc_basis_refreeze: Mapping[str, Any] | None = None,
    explicit_dhc_r11_bodyfree_next_work_decision_material: Mapping[str, Any] | None = None,
    optional_explicit_dhc_op08_result_memo_closure_material: Mapping[str, Any] | None = None,
    optional_current_existing_dhr_op05_result_wrapper: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Intake explicit DHC R11 metadata without synthesizing or selecting results."""

    op00 = op00_post_dhc_basis_refreeze
    op00_present = isinstance(op00, Mapping)
    op00_contract_valid = _op00_valid(op00)
    r11 = explicit_dhc_r11_bodyfree_next_work_decision_material
    r11_supplied = r11 is not None
    r11_present = isinstance(r11, Mapping)
    r11_contract_valid = _dhc_r11_material_contract_valid(r11)
    explicit_dhc_op08_supplied = optional_explicit_dhc_op08_result_memo_closure_material is not None
    explicit_dhc_op08_present = isinstance(
        optional_explicit_dhc_op08_result_memo_closure_material, Mapping
    )
    current_op05_supplied = optional_current_existing_dhr_op05_result_wrapper is not None
    current_op05_present = isinstance(optional_current_existing_dhr_op05_result_wrapper, Mapping)
    optional_shapes_valid = bool(
        (not explicit_dhc_op08_supplied or explicit_dhc_op08_present)
        and (not current_op05_supplied or current_op05_present)
    )

    input_materials = (
        ("explicit_dhc_r11", r11),
        ("optional_explicit_dhc_op08", optional_explicit_dhc_op08_result_memo_closure_material),
        ("optional_current_dhr_op05", optional_current_existing_dhr_op05_result_wrapper),
    )
    forbidden_paths: list[str] = []
    body_like_paths: list[str] = []
    promotion_paths: list[str] = []
    no_touch_paths: list[str] = []
    for root, material in input_materials:
        if material is None:
            continue
        forbidden_paths.extend(_scan_forbidden_payload_key_paths(material, path=root))
        body_like_paths.extend(_scan_body_like_value_paths(material, path=root))
        promotion_paths.extend(_scan_promotion_or_autorun_claim_paths(material, path=root))
        no_touch_paths.extend(_scan_no_touch_mutation_paths(material, path=root))
    forbidden_paths = _dedupe_clean_refs(forbidden_paths)
    body_like_paths = _dedupe_clean_refs(body_like_paths)
    promotion_paths = _dedupe_clean_refs(promotion_paths)
    no_touch_paths = _dedupe_clean_refs(no_touch_paths)
    scan_blocked = bool(forbidden_paths or body_like_paths or promotion_paths or no_touch_paths)

    status_ref, reasons, blockers, next_required_step = _dhd_op01_status(
        op00_valid=op00_contract_valid,
        r11_supplied=r11_supplied,
        r11_present=r11_present,
        r11_valid=r11_contract_valid,
        optional_shapes_valid=optional_shapes_valid,
        explicit_dhc_op08_present=explicit_dhc_op08_present,
        scan_blocked=scan_blocked,
    )
    intake_ready = status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[0]
    intake_ready_with_op08 = status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[1]
    waiting = status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[2]
    repair = status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[3]
    blocked = status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[4]
    reason_refs = _dedupe_clean_refs(reasons)
    blocker_refs = _dedupe_clean_refs(blockers)
    r11_map = r11 if isinstance(r11, Mapping) else {}
    op00_map = op00 if isinstance(op00, Mapping) else {}
    dhc_op08_map = (
        optional_explicit_dhc_op08_result_memo_closure_material
        if isinstance(optional_explicit_dhc_op08_result_memo_closure_material, Mapping)
        else {}
    )
    op05_map = (
        optional_current_existing_dhr_op05_result_wrapper
        if isinstance(optional_current_existing_dhr_op05_result_wrapper, Mapping)
        else {}
    )

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP01_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP01_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op00_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op00_material_present": op00_present,
            "op00_contract_valid": op00_contract_valid,
            "op00_schema_version_ref": _clean_ref(
                op00_map.get("schema_version"), default="op00_schema_missing"
            ),
            "op00_material_ref": _clean_ref(
                op00_map.get("material_id"), default="op00_material_missing"
            ),
            "op00_next_required_step_ref": _clean_ref(
                op00_map.get("next_required_step"), default="op00_next_step_missing"
            ),
            "dhc_r11_material_supplied": r11_supplied,
            "dhc_r11_material_present": r11_present,
            "dhc_r11_contract_valid": r11_contract_valid,
            "dhc_r11_material_ref": _clean_ref(
                r11_map.get("material_id"), default=P7_R54_AHR_POST_DHC_DHD_DHC_R11_RESULT_MEMO_REF
            ),
            "dhc_r11_source_mode_ref": _clean_ref(
                r11_map.get("source_mode"), default="dhc_r11_source_mode_missing"
            ),
            "dhc_r11_current_execution_allowance_ref": _clean_ref(
                r11_map.get("current_execution_allowance"),
                default="dhc_r11_execution_allowance_missing",
            ),
            "dhc_r11_dhr_op06_call_ref": _clean_ref(
                r11_map.get("dhr_op06_call"), default="dhc_r11_dhr_op06_call_missing"
            ),
            "dhc_r11_dhr_op07_materialization_ref": _clean_ref(
                r11_map.get("dhr_op07_materialization"),
                default="dhc_r11_dhr_op07_materialization_missing",
            ),
            "dhc_r11_p8_question_design_ref": _clean_ref(
                r11_map.get("p8_question_design"), default="dhc_r11_p8_question_design_missing"
            ),
            "dhc_r11_release_decision_ref": _clean_ref(
                r11_map.get("release_decision"), default="dhc_r11_release_decision_missing"
            ),
            "dhc_r11_recommended_next_work_candidate_ref": _clean_ref(
                r11_map.get("recommended_next_work_candidate"),
                default="dhc_r11_next_work_candidate_missing",
                max_length=400,
            ),
            "dhc_r11_body_free": bool(r11_present and r11_map.get("body_free") is True),
            "explicit_dhc_op08_material_supplied": explicit_dhc_op08_supplied,
            "explicit_dhc_op08_material_present": explicit_dhc_op08_present,
            "explicit_dhc_op08_material_ref": _clean_ref(
                dhc_op08_map.get("material_id"), default="explicit_dhc_op08_material_missing"
            ),
            "current_existing_dhr_op05_result_wrapper_supplied": current_op05_supplied,
            "current_existing_dhr_op05_result_wrapper_present": current_op05_present,
            "current_existing_dhr_op05_result_wrapper_ref": _clean_ref(
                op05_map.get("material_id"), default="current_dhr_op05_wrapper_missing"
            ),
            "optional_material_shapes_valid": optional_shapes_valid,
            "dhc_r11_input_forbidden_payload_key_path_refs": forbidden_paths,
            "dhc_r11_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "dhc_r11_input_body_like_value_path_refs": body_like_paths,
            "dhc_r11_input_body_like_value_path_count": len(body_like_paths),
            "dhc_r11_input_promotion_or_autorun_claim_path_refs": promotion_paths,
            "dhc_r11_input_promotion_or_autorun_claim_path_count": len(promotion_paths),
            "dhc_r11_input_no_touch_mutation_path_refs": no_touch_paths,
            "dhc_r11_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhd_op01_status_ref": status_ref,
            "bodyfree_dhc_r11_closure_material_intake_status_ref": status_ref,
            "dhd_op01_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS,
            "dhd_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS),
            "dhd_op01_intake_ready": intake_ready,
            "dhd_op01_intake_ready_with_explicit_dhc_op08_material": intake_ready_with_op08,
            "dhd_op01_ready_for_op02_dhc_outcome_check": intake_ready or intake_ready_with_op08,
            "dhd_op01_waiting_for_explicit_dhc_r11_material": waiting,
            "dhd_op01_repair_required": repair,
            "dhd_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
            "dhd_op01_reason_refs": reason_refs,
            "dhd_op01_reason_ref_count": len(reason_refs),
            "dhd_op01_blocker_refs": blocker_refs,
            "dhd_op01_blocker_ref_count": len(blocker_refs),
            "dhc_builder_call_allowed_here": False,
            "dhc_result_synthesis_allowed_here": False,
            "dhc_r11_as_current_selected_result_allowed_here": False,
            "dhc_validation_green_as_runtime_allowed_here": False,
            "dhr_op05_runtime_call_allowed_here": False,
            "existing_dhr_op05_builder_runtime_call_allowed_here": False,
            "dhr_op06_consideration_decision_allowed_in_r1": False,
            "dhr_op06_builder_call_allowed_here": False,
            "dhr_op06_implicit_op05_fallback_allowed_here": False,
            "dhr_op07_materialization_allowed_here": False,
            "dmd_r52_execution_allowed_here": False,
            "actual_review_start_allowed_here": False,
            "actual_rows_creation_allowed_here": False,
            "question_need_observation_rows_creation_allowed_here": False,
            "p7_readfeel_reconnection_decision_allowed_in_r1": False,
            "p7_readfeel_evaluation_execution_allowed_here": False,
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
            "dhd_op01_does_not_synthesize_dhc_result": True,
            "dhd_op01_does_not_call_dhc_builder": True,
            "dhd_op01_does_not_call_dhr_op05": True,
            "dhd_op01_does_not_call_existing_dhr_op05_builder": True,
            "dhd_op01_does_not_call_dhr_op06_builder": True,
            "dhd_op01_does_not_use_dhr_op06_implicit_op05_fallback": True,
            "dhd_op01_does_not_select_current_dhc_result": True,
            "dhd_op01_does_not_select_current_dhr_op05_wrapper": True,
            "dhd_op01_does_not_decide_dhr_op06_consideration": True,
            "dhd_op01_does_not_decide_or_run_p7_readfeel_reconnection": True,
            "dhd_op01_does_not_execute_dmd_r52_or_release": True,
            "dhd_op01_does_not_start_actual_review": True,
            "dhd_op01_does_not_create_actual_rows": True,
            "dhd_op01_does_not_create_question_need_observation_rows": True,
            "dhd_op01_does_not_start_p8_question_system": True,
            "dhd_op01_does_not_materialize_question_text": True,
            "dhd_op01_does_not_change_api_db_rn_runtime_response_key": True,
            "dhd_op01_does_not_create_json_schema_file": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS),
            "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP01_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP01_NOT_YET_IMPLEMENTED_STEPS),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R2_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R2_COMPILEALL_TARGET_REF_REFS),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert the DHD-OP01 body-free DHC R11 intake contract."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP01_REQUIRED_FIELD_REFS, source="DHD-OP01"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP01 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP01_SCHEMA_VERSION:
        raise ValueError("DHD-OP01 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP01_STEP_REF:
        raise ValueError("DHD-OP01 step mismatch")
    if data.get("source_mode") != P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE:
        raise ValueError("DHD-OP01 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("DHD-OP01 must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError("DHD-OP01 must remain body-free")
    for key in (
        "dhd_op01_does_not_synthesize_dhc_result",
        "dhd_op01_does_not_call_dhc_builder",
        "dhd_op01_does_not_call_dhr_op05",
        "dhd_op01_does_not_call_existing_dhr_op05_builder",
        "dhd_op01_does_not_call_dhr_op06_builder",
        "dhd_op01_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op01_does_not_select_current_dhc_result",
        "dhd_op01_does_not_select_current_dhr_op05_wrapper",
        "dhd_op01_does_not_decide_dhr_op06_consideration",
        "dhd_op01_does_not_decide_or_run_p7_readfeel_reconnection",
        "dhd_op01_does_not_execute_dmd_r52_or_release",
        "dhd_op01_does_not_start_actual_review",
        "dhd_op01_does_not_create_actual_rows",
        "dhd_op01_does_not_create_question_need_observation_rows",
        "dhd_op01_does_not_start_p8_question_system",
        "dhd_op01_does_not_materialize_question_text",
        "dhd_op01_does_not_change_api_db_rn_runtime_response_key",
        "dhd_op01_does_not_create_json_schema_file",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP01 required true field changed: {key}")
    for key in (
        "dhc_builder_call_allowed_here",
        "dhc_result_synthesis_allowed_here",
        "dhc_r11_as_current_selected_result_allowed_here",
        "dhc_validation_green_as_runtime_allowed_here",
        "dhr_op05_runtime_call_allowed_here",
        "existing_dhr_op05_builder_runtime_call_allowed_here",
        "dhr_op06_consideration_decision_allowed_in_r1",
        "dhr_op06_builder_call_allowed_here",
        "dhr_op06_implicit_op05_fallback_allowed_here",
        "dhr_op07_materialization_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "actual_rows_creation_allowed_here",
        "question_need_observation_rows_creation_allowed_here",
        "p7_readfeel_reconnection_decision_allowed_in_r1",
        "p7_readfeel_evaluation_execution_allowed_here",
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
            raise ValueError(f"DHD-OP01 forbidden allowance changed: {key}")
    for key in P7_R54_AHR_POST_DHC_DHD_OP01_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"DHD-OP01 required false flag changed: {key}")
    if tuple(data.get("dhd_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP01 allowed status refs changed")
    if data.get("dhd_op01_allowed_status_ref_count") != len(P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS):
        raise ValueError("DHD-OP01 allowed status count changed")
    if data.get("bodyfree_dhc_r11_closure_material_intake_status_ref") != data.get("dhd_op01_status_ref"):
        raise ValueError("DHD-OP01 status alias changed")
    branch_flags = (
        data.get("dhd_op01_intake_ready") is True,
        data.get("dhd_op01_intake_ready_with_explicit_dhc_op08_material") is True,
        data.get("dhd_op01_waiting_for_explicit_dhc_r11_material") is True,
        data.get("dhd_op01_repair_required") is True,
        data.get("dhd_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
    )
    if data.get("dhd_op01_status_ref") not in P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP01 status is not allowed")
    if sum(branch_flags) != 1:
        raise ValueError("DHD-OP01 must select exactly one status branch")
    ready = data.get("dhd_op01_status_ref") in P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[:2]
    if data.get("dhd_op01_ready_for_op02_dhc_outcome_check") is not ready:
        raise ValueError("DHD-OP01 OP02 readiness alias changed")
    if ready:
        if not all(
            data.get(key) is True
            for key in ("op00_contract_valid", "dhc_r11_material_present", "dhc_r11_contract_valid")
        ):
            raise ValueError("DHD-OP01 ready branch requires valid OP00 and DHC R11 material")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF:
            raise ValueError("DHD-OP01 ready next step changed")
    if data.get("dhd_op01_intake_ready_with_explicit_dhc_op08_material") is True:
        if data.get("explicit_dhc_op08_material_present") is not True:
            raise ValueError("DHD-OP01 explicit DHC-OP08 ready status requires mapping presence")
    if data.get("dhd_op01_waiting_for_explicit_dhc_r11_material") is True:
        if data.get("dhc_r11_material_supplied") is not False:
            raise ValueError("DHD-OP01 waiting branch must mean DHC R11 was not supplied")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_WAIT_FOR_EXPLICIT_DHC_R11_MATERIAL_REF:
            raise ValueError("DHD-OP01 waiting next step changed")
    if data.get("dhd_op01_repair_required") is True:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_DHC_R11_INTAKE_REF:
            raise ValueError("DHD-OP01 repair next step changed")
    if data.get("dhd_op01_bodyfree_leak_promotion_or_autorun_blocked") is True:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_DHC_R11_INTAKE_REF:
            raise ValueError("DHD-OP01 blocked next step changed")
    for field, count_field in (
        ("dhc_r11_input_forbidden_payload_key_path_refs", "dhc_r11_input_forbidden_payload_key_path_count"),
        ("dhc_r11_input_body_like_value_path_refs", "dhc_r11_input_body_like_value_path_count"),
        (
            "dhc_r11_input_promotion_or_autorun_claim_path_refs",
            "dhc_r11_input_promotion_or_autorun_claim_path_count",
        ),
        ("dhc_r11_input_no_touch_mutation_path_refs", "dhc_r11_input_no_touch_mutation_path_count"),
        ("dhd_op01_reason_refs", "dhd_op01_reason_ref_count"),
        ("dhd_op01_blocker_refs", "dhd_op01_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP01 count field changed: {count_field}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP01_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP01 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R2_TARGET_TEST_REF_REFS:
        raise ValueError("DHD-OP01 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R2_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHD-OP01 compileall refs changed")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError("DHD-OP01 public contract changed")
    if any(value is not False for value in (data.get("dhd_no_touch_contract") or {}).values()):
        raise ValueError("DHD-OP01 no-touch contract must remain false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError("DHD-OP01 body-free marker changed")
    return True


# ---------------------------------------------------------------------------
# R3: DHD-OP02 / DHD-OP03 only.
# OP02 classifies supplied, already-existing DHC material. OP03 determines
# consideration eligibility. Neither operation calls a DHC/DHR builder or
# turns validation green, next-step order, or implicit fallback into runtime
# permission.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHC_DHD_R3_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_R2_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op02_op03_20260709.py",
)
P7_R54_AHR_POST_DHC_DHD_R3_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_R2_COMPILEALL_TARGET_REF_REFS
)

P7_R54_AHR_POST_DHC_DHD_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_OP01_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_OP02_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key not in {"dhd_op00_implemented", "dhd_op01_implemented", "dhd_op02_implemented"}
)
P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
    }
)

P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP02_REF: Final = (
    "blocked_DHC_outcome_material_then_DHD_OP08_stop_without_downstream"
)
P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP03_REF: Final = (
    "blocked_DHR_OP06_consideration_fallback_or_autorun_then_DHD_OP08_stop"
)
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_UNRESOLVED_BRANCH_REASON_REF: Final = (
    "explicit_current_DHR_OP05_scan_clear_stopped_has_unresolved_handoff_or_retry_branch"
)
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_CONSIDERATION_NOT_PERMISSION_REF: Final = (
    "DHR_OP06_consideration_candidate_is_not_builder_call_or_execution_permission"
)
P7_R54_AHR_POST_DHC_DHD_DHR_OP06_CONSIDERATION_NOT_DIRECTION_DECISION_REF: Final = (
    "DHR_OP06_consideration_eligibility_does_not_choose_final_Post_DHC_direction"
)

P7_R54_AHR_POST_DHC_DHD_OP02_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op01_schema_version_ref",
    "op01_material_ref",
    "op01_status_ref",
    "op01_ready_for_op02_dhc_outcome_check",
    "explicit_current_dhc_op08_material_supplied",
    "explicit_current_dhc_op08_material_present",
    "explicit_current_dhc_op08_material_contract_valid",
    "explicit_current_dhc_op08_schema_version_ref",
    "explicit_current_dhc_op08_step_ref",
    "explicit_current_dhc_op08_status_ref",
    "explicit_current_dhc_op08_result_class_ref",
    "explicit_current_dhc_op08_next_work_candidate_ref",
    "explicit_current_op05_wrapper_supplied",
    "explicit_current_op05_wrapper_present",
    "explicit_current_op05_wrapper_contract_valid",
    "explicit_current_op05_wrapper_body_free",
    "explicit_current_op05_wrapper_schema_version_ref",
    "explicit_current_op05_wrapper_step_ref",
    "explicit_current_op05_wrapper_status_ref",
    "explicit_current_op05_wrapper_scan_clear_stopped",
    "dhd_op02_status_ref",
    "bodyfree_dhc_outcome_classification_status_ref",
    "dhd_op02_allowed_status_refs",
    "dhd_op02_allowed_status_ref_count",
    "dhc_outcome_class_ref",
    "dhc_outcome_classification_refs",
    "dhc_outcome_classification_ref_count",
    "current_dhc_result_selected",
    "current_dhc_scan_clear_result_selected",
    "scan_clear_capable_test_validation_only",
    "current_material_sufficient_for_dhr_op06_consideration",
    "dhr_op06_permission_produced_here",
    "op02_input_forbidden_payload_key_path_refs",
    "op02_input_forbidden_payload_key_path_count",
    "op02_input_body_like_value_path_refs",
    "op02_input_body_like_value_path_count",
    "op02_input_promotion_or_autorun_claim_path_refs",
    "op02_input_promotion_or_autorun_claim_path_count",
    "op02_input_no_touch_mutation_path_refs",
    "op02_input_no_touch_mutation_path_count",
    "dhd_op02_reason_refs",
    "dhd_op02_reason_ref_count",
    "dhd_op02_blocker_refs",
    "dhd_op02_blocker_ref_count",
    "dhd_op02_does_not_synthesize_dhc_result",
    "dhd_op02_does_not_call_dhc_builder",
    "dhd_op02_does_not_call_existing_dhr_op05_builder",
    "dhd_op02_does_not_call_dhr_op06_builder",
    "dhd_op02_does_not_use_dhr_op06_implicit_op05_fallback",
    "dhd_op02_keeps_r11_and_test_green_unselected",
    "dhd_op02_does_not_produce_dhr_op06_permission",
    "dhd_op02_does_not_run_p7_readfeel_evaluation",
    "dhd_op02_does_not_start_p8_or_release",
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
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP03_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op02_schema_version_ref",
    "op02_material_ref",
    "op02_status_ref",
    "op02_dhc_outcome_class_ref",
    "current_dhc_result_selected",
    "current_dhc_scan_clear_result_selected",
    "scan_clear_capable_test_validation_only",
    "explicit_current_op05_material_supplied",
    "explicit_current_op05_material_present",
    "explicit_current_op05_material_contract_valid_ref",
    "explicit_current_op05_material_body_free",
    "explicit_current_op05_material_schema_version_ref",
    "explicit_current_op05_material_step_ref",
    "explicit_current_op05_material_status_ref",
    "explicit_current_op05_material_scan_clear_stopped",
    "allow_dhr_op06_consideration_candidate",
    "allow_dhr_op06_builder_call",
    "allow_dhr_op06_implicit_op05_fallback",
    "allow_input_types_valid",
    "explicit_current_material_required",
    "explicit_current_material_satisfied",
    "unresolved_branch_reason_confirmed",
    "dhr_op06_consideration_is_not_based_only_on_next_operation_order",
    "dhd_op03_status_ref",
    "bodyfree_dhr_op06_consideration_eligibility_status_ref",
    "dhd_op03_allowed_status_refs",
    "dhd_op03_allowed_status_ref_count",
    "dhr_op06_consideration_candidate",
    "dhr_op06_consideration_eligibility_decided_here",
    "why_dhr_op06_consideration_may_be_needed_refs",
    "why_dhr_op06_consideration_may_be_needed_ref_count",
    "why_dhr_op06_consideration_is_not_enough_refs",
    "why_dhr_op06_consideration_is_not_enough_ref_count",
    "dhr_op06_consideration_blocker_refs",
    "dhr_op06_consideration_blocker_ref_count",
    "op03_input_forbidden_payload_key_path_refs",
    "op03_input_forbidden_payload_key_path_count",
    "op03_input_body_like_value_path_refs",
    "op03_input_body_like_value_path_count",
    "op03_input_promotion_or_autorun_claim_path_refs",
    "op03_input_promotion_or_autorun_claim_path_count",
    "op03_input_no_touch_mutation_path_refs",
    "op03_input_no_touch_mutation_path_count",
    "dhr_op06_permission_produced_here",
    "dhr_op06_builder_call_allowed_here",
    "dhr_op06_implicit_op05_fallback_allowed_here",
    "dhd_op03_does_not_call_dhc_builder",
    "dhd_op03_does_not_call_existing_dhr_op05_builder",
    "dhd_op03_does_not_call_dhr_op06_builder",
    "dhd_op03_does_not_use_dhr_op06_implicit_op05_fallback",
    "dhd_op03_does_not_materialize_dhr_op07_or_execute_dmd_r52",
    "dhd_op03_does_not_run_p7_readfeel_evaluation",
    "dhd_op03_does_not_start_p8_or_release",
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
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP02_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FALSE_FLAG_REFS
    )
)
P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP03_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FALSE_FLAG_REFS
    )
)


def _op01_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhc_dhd_op01_dhc_r11_closure_material_intake_contract(data)
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def _dhc_op08_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        dhc.assert_p7_r54_ahr_post_dhb_dhc_op08_result_memo_closure_stopped_next_work_candidate_contract(
            data
        )
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def _existing_dhr_op05_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op05_bodyfree_leak_promotion_claim_dmd_compatibility_preflight_scan_contract(
            data
        )
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def _op02_status_and_outcome(
    *,
    op01_present: bool,
    op01_valid: bool,
    op01_status_ref: str,
    op01_ready: bool,
    op08_supplied: bool,
    op08_present: bool,
    op08_valid: bool,
    op08_status_ref: str,
    scan_clear_capable_test_validation_only: bool,
    blocked: bool,
) -> tuple[str, str, list[str], list[str]]:
    if blocked or (
        op01_valid
        and op01_status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[4]
    ):
        return (
            P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[4],
            P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7],
            ["DHD_OP02_blocked_bodyfree_leak_promotion_or_autorun"],
            ["stop_and_repair_DHD_OP02_no_touch_no_promotion_violation"],
        )
    if not op01_present or not op01_valid:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[3],
            P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[4],
            ["DHD_OP02_missing_or_invalid_OP01_intake_material"],
            ["repair_DHD_OP01_material_before_current_DHC_outcome_classification"],
        )
    if op01_status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[2]:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[2],
            P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[3],
            ["DHD_OP02_OP01_waiting_for_explicit_DHC_R11_material"],
            ["collect_explicit_DHC_R11_material_without_DHC_result_synthesis"],
        )
    if op01_status_ref == P7_R54_AHR_POST_DHC_DHD_OP01_ALLOWED_STATUS_REFS[3] or not op01_ready:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[3],
            P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[4],
            ["DHD_OP02_OP01_intake_requires_repair"],
            ["repair_DHD_OP01_material_before_current_DHC_outcome_classification"],
        )
    if op08_supplied and (not op08_present or not op08_valid):
        return (
            P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[3],
            P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[4],
            ["DHD_OP02_explicit_current_DHC_OP08_material_invalid"],
            ["repair_explicit_current_DHC_OP08_material_without_builder_call"],
        )
    if op08_valid:
        status_index = P7_R54_AHR_POST_DHC_DHD_DHC_OP08_ALLOWED_STATUS_REFS.index(
            op08_status_ref
        )
        status_and_outcome = (
            (
                P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[0],
                P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[0],
                "DHD_OP02_explicit_current_DHC_OP08_scan_clear_selected",
                "",
            ),
            (
                P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[2],
                P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[3],
                "DHD_OP02_explicit_current_DHC_OP08_waiting_or_incomplete",
                "collect_or_repair_explicit_current_DHC_material",
            ),
            (
                P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[3],
                P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[4],
                "DHD_OP02_explicit_current_DHC_OP08_repair_required",
                "repair_explicit_current_DHC_material_before_direction_comparison",
            ),
            (
                P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[2],
                P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[5],
                "DHD_OP02_explicit_current_DHC_OP08_not_called",
                "wait_for_explicit_manual_call_request_and_current_material",
            ),
            (
                P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[0],
                P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[6],
                "DHD_OP02_explicit_current_DHC_OP08_preserves_non_DHR_lane",
                "preserve_non_DHR_lane_route_without_DHR_OP06_consideration",
            ),
            (
                P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[4],
                P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7],
                "DHD_OP02_explicit_current_DHC_OP08_blocked",
                "stop_and_repair_DHC_OP08_no_touch_no_promotion_violation",
            ),
        )[status_index]
        status_ref, outcome_ref, reason_ref, blocker_ref = status_and_outcome
        return status_ref, outcome_ref, [reason_ref], [blocker_ref] if blocker_ref else []
    if scan_clear_capable_test_validation_only:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[1],
            P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[2],
            ["DHD_OP02_scan_clear_capable_test_validation_is_not_current_runtime_result"],
            ["explicit_current_DHC_OP08_material_required_for_runtime_result_selection"],
        )
    return (
        P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[1],
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[1],
        ["DHD_OP02_DHC_R11_only_has_no_current_selected_result"],
        ["explicit_current_DHC_OP08_material_required_before_scan_clear_selection"],
    )


def build_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check(
    op01_dhc_r11_intake: Mapping[str, Any] | None = None,
    *,
    optional_explicit_dhc_op08_result_memo_closure_material: Mapping[str, Any] | None = None,
    optional_current_existing_dhr_op05_result_wrapper: Mapping[str, Any] | None = None,
    scan_clear_capable_test_validation_only: bool = False,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Classify existing DHC outcome material without synthesizing or executing it."""

    op01 = op01_dhc_r11_intake
    op08 = optional_explicit_dhc_op08_result_memo_closure_material
    op05 = optional_current_existing_dhr_op05_result_wrapper
    op01_present = isinstance(op01, Mapping)
    op08_supplied = op08 is not None
    op08_present = isinstance(op08, Mapping)
    op05_supplied = op05 is not None
    op05_present = isinstance(op05, Mapping)
    op01_contract_valid = _op01_valid(op01)
    op08_contract_valid = _dhc_op08_valid(op08)
    op05_contract_valid = _existing_dhr_op05_valid(op05)
    op01_map = op01 if op01_present else {}
    op08_map = op08 if op08_present else {}
    op05_map = op05 if op05_present else {}
    op01_status_ref = _clean_ref(
        op01_map.get("dhd_op01_status_ref"), default="op01_status_missing"
    )
    op01_ready = bool(
        op01_contract_valid
        and op01_map.get("dhd_op01_ready_for_op02_dhc_outcome_check") is True
    )
    op08_status_ref = _clean_ref(
        op08_map.get("dhc_op08_status_ref"), default="explicit_current_dhc_op08_status_missing"
    )
    op05_status_ref = _clean_ref(
        op05_map.get("dhr_op05_status_ref"), default="explicit_current_dhr_op05_status_missing"
    )
    op05_scan_clear = bool(
        op05_contract_valid
        and op05_status_ref
        == P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF
    )
    test_validation_input_type_valid = type(scan_clear_capable_test_validation_only) is bool
    test_validation_only = bool(
        test_validation_input_type_valid and scan_clear_capable_test_validation_only
    )
    scan_root = {
        "op01_dhc_r11_intake": op01 if op01_present else {},
        "explicit_current_dhc_op08_material": op08 if op08_present else {},
        "explicit_current_dhr_op05_wrapper": op05 if op05_present else {},
    }
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(scan_root, path="dhd_op02_input")
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(scan_root, path="dhd_op02_input")
    )
    promotion_paths = _dedupe_clean_refs(
        _scan_promotion_or_autorun_claim_paths(scan_root, path="dhd_op02_input")
    )
    no_touch_paths = _dedupe_clean_refs(
        _scan_no_touch_mutation_paths(scan_root, path="dhd_op02_input")
    )
    blocked_input = bool(
        forbidden_paths
        or body_like_paths
        or promotion_paths
        or no_touch_paths
        or not test_validation_input_type_valid
    )
    status_ref, outcome_ref, reasons, blockers = _op02_status_and_outcome(
        op01_present=op01_present,
        op01_valid=op01_contract_valid,
        op01_status_ref=op01_status_ref,
        op01_ready=op01_ready,
        op08_supplied=op08_supplied,
        op08_present=op08_present,
        op08_valid=op08_contract_valid,
        op08_status_ref=op08_status_ref,
        scan_clear_capable_test_validation_only=test_validation_only,
        blocked=blocked_input,
    )
    if not test_validation_input_type_valid:
        blockers.append("scan_clear_capable_test_validation_only_must_be_boolean")
    if op01_contract_valid and op01_map.get("explicit_dhc_op08_material_present") is True and not op08_present:
        reasons.append("OP01_presence_record_does_not_select_or_replace_explicit_current_DHC_OP08_material")
    if op05_supplied and not op05_contract_valid:
        reasons.append("explicit_current_DHR_OP05_wrapper_invalid_for_future_DHD_OP03_eligibility")
    current_dhc_result_selected = bool(op08_contract_valid)
    current_dhc_scan_clear_result_selected = bool(
        outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[0]
    )
    current_material_sufficient = bool(
        current_dhc_scan_clear_result_selected and op05_scan_clear
    )
    reason_refs = _dedupe_clean_refs(reasons)
    blocker_refs = _dedupe_clean_refs(
        [*blockers, *forbidden_paths, *body_like_paths, *promotion_paths, *no_touch_paths]
    )
    next_required_step = (
        P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP02_REF
        if status_ref == P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[4]
        else P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF
    )

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP02_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op01_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op01_material_present": op01_present,
            "op01_contract_valid": op01_contract_valid,
            "op01_schema_version_ref": _clean_ref(
                op01_map.get("schema_version"), default="op01_schema_missing"
            ),
            "op01_material_ref": _clean_ref(
                op01_map.get("material_id"), default="op01_material_missing"
            ),
            "op01_status_ref": op01_status_ref,
            "op01_ready_for_op02_dhc_outcome_check": op01_ready,
            "explicit_current_dhc_op08_material_supplied": op08_supplied,
            "explicit_current_dhc_op08_material_present": op08_present,
            "explicit_current_dhc_op08_material_contract_valid": op08_contract_valid,
            "explicit_current_dhc_op08_schema_version_ref": _clean_ref(
                op08_map.get("schema_version"), default="explicit_current_dhc_op08_schema_missing"
            ),
            "explicit_current_dhc_op08_step_ref": _clean_ref(
                op08_map.get("operation_step_ref"), default="explicit_current_dhc_op08_step_missing"
            ),
            "explicit_current_dhc_op08_status_ref": op08_status_ref,
            "explicit_current_dhc_op08_result_class_ref": _clean_ref(
                op08_map.get("dhc_result_classification_ref"),
                default="explicit_current_dhc_result_class_missing",
            ),
            "explicit_current_dhc_op08_next_work_candidate_ref": _clean_ref(
                op08_map.get("next_work_candidate_ref"),
                default="explicit_current_dhc_next_work_candidate_missing",
            ),
            "explicit_current_op05_wrapper_supplied": op05_supplied,
            "explicit_current_op05_wrapper_present": op05_present,
            "explicit_current_op05_wrapper_contract_valid": op05_contract_valid,
            "explicit_current_op05_wrapper_body_free": bool(
                op05_present and op05_map.get("body_free") is True
            ),
            "explicit_current_op05_wrapper_schema_version_ref": _clean_ref(
                op05_map.get("schema_version"), default="explicit_current_dhr_op05_schema_missing"
            ),
            "explicit_current_op05_wrapper_step_ref": _clean_ref(
                op05_map.get("operation_step_ref"), default="explicit_current_dhr_op05_step_missing"
            ),
            "explicit_current_op05_wrapper_status_ref": op05_status_ref,
            "explicit_current_op05_wrapper_scan_clear_stopped": op05_scan_clear,
            "dhd_op02_status_ref": status_ref,
            "bodyfree_dhc_outcome_classification_status_ref": status_ref,
            "dhd_op02_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS,
            "dhd_op02_allowed_status_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS
            ),
            "dhc_outcome_class_ref": outcome_ref,
            "dhc_outcome_classification_refs": P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS,
            "dhc_outcome_classification_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS
            ),
            "current_dhc_result_selected": current_dhc_result_selected,
            "current_dhc_scan_clear_result_selected": current_dhc_scan_clear_result_selected,
            "scan_clear_capable_test_validation_only": bool(
                outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[2]
            ),
            "current_material_sufficient_for_dhr_op06_consideration": current_material_sufficient,
            "dhr_op06_permission_produced_here": False,
            "op02_input_forbidden_payload_key_path_refs": forbidden_paths,
            "op02_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op02_input_body_like_value_path_refs": body_like_paths,
            "op02_input_body_like_value_path_count": len(body_like_paths),
            "op02_input_promotion_or_autorun_claim_path_refs": promotion_paths,
            "op02_input_promotion_or_autorun_claim_path_count": len(promotion_paths),
            "op02_input_no_touch_mutation_path_refs": no_touch_paths,
            "op02_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhd_op02_reason_refs": reason_refs,
            "dhd_op02_reason_ref_count": len(reason_refs),
            "dhd_op02_blocker_refs": blocker_refs,
            "dhd_op02_blocker_ref_count": len(blocker_refs),
            "dhd_op02_does_not_synthesize_dhc_result": True,
            "dhd_op02_does_not_call_dhc_builder": True,
            "dhd_op02_does_not_call_existing_dhr_op05_builder": True,
            "dhd_op02_does_not_call_dhr_op06_builder": True,
            "dhd_op02_does_not_use_dhr_op06_implicit_op05_fallback": True,
            "dhd_op02_keeps_r11_and_test_green_unselected": True,
            "dhd_op02_does_not_produce_dhr_op06_permission": True,
            "dhd_op02_does_not_run_p7_readfeel_evaluation": True,
            "dhd_op02_does_not_start_p8_or_release": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "fixed_non_promotion_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP02_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(
                P7_R54_AHR_POST_DHC_DHD_OP02_NOT_YET_IMPLEMENTED_STEPS
            ),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R3_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(
                P7_R54_AHR_POST_DHC_DHD_R3_COMPILEALL_TARGET_REF_REFS
            ),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "dhd_op02_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def _assert_r3_shared_contract(
    data: Mapping[str, Any], *, source: str, required_false_refs: Sequence[str]
) -> None:
    if data.get("source_mode") != P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE:
        raise ValueError(f"{source} source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require/check GitHub")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    for key in required_false_refs:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag changed: {key}")
    if data.get("public_contract") != public_contract_flags():
        raise ValueError(f"{source} public contract changed")
    if any(value is not False for value in (data.get("dhd_no_touch_contract") or {}).values()):
        raise ValueError(f"{source} no-touch contract must remain false")
    if data.get("body_free_markers", {}).get("body_free") is not True:
        raise ValueError(f"{source} body-free marker changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError(f"{source} not-claimed boundary must remain false")


def assert_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert strict DHD-OP02 classification and no-execution boundaries."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FIELD_REFS, source="DHD-OP02"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP02 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP02_SCHEMA_VERSION:
        raise ValueError("DHD-OP02 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP02_STEP_REF:
        raise ValueError("DHD-OP02 step mismatch")
    _assert_r3_shared_contract(
        data,
        source="DHD-OP02",
        required_false_refs=P7_R54_AHR_POST_DHC_DHD_OP02_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "dhd_op02_does_not_synthesize_dhc_result",
        "dhd_op02_does_not_call_dhc_builder",
        "dhd_op02_does_not_call_existing_dhr_op05_builder",
        "dhd_op02_does_not_call_dhr_op06_builder",
        "dhd_op02_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op02_keeps_r11_and_test_green_unselected",
        "dhd_op02_does_not_produce_dhr_op06_permission",
        "dhd_op02_does_not_run_p7_readfeel_evaluation",
        "dhd_op02_does_not_start_p8_or_release",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP02 required true field changed: {key}")
    if data.get("dhr_op06_permission_produced_here") is not False:
        raise ValueError("DHD-OP02 must not produce DHR-OP06 permission")
    if tuple(data.get("dhd_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP02 allowed status refs changed")
    if data.get("dhd_op02_allowed_status_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS
    ):
        raise ValueError("DHD-OP02 allowed status count changed")
    if tuple(data.get("dhc_outcome_classification_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS:
        raise ValueError("DHD-OP02 outcome refs changed")
    if data.get("dhc_outcome_classification_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS
    ):
        raise ValueError("DHD-OP02 outcome ref count changed")
    status_ref = data.get("dhd_op02_status_ref")
    outcome_ref = data.get("dhc_outcome_class_ref")
    if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP02 status is not allowed")
    if outcome_ref not in P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS:
        raise ValueError("DHD-OP02 outcome class is not allowed")
    if data.get("bodyfree_dhc_outcome_classification_status_ref") != status_ref:
        raise ValueError("DHD-OP02 status alias changed")
    scan_clear = outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[0]
    test_only = outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[2]
    if data.get("current_dhc_scan_clear_result_selected") is not scan_clear:
        raise ValueError("DHD-OP02 current scan-clear selection changed")
    if data.get("scan_clear_capable_test_validation_only") is not test_only:
        raise ValueError("DHD-OP02 test-validation-only classification changed")
    if scan_clear:
        if not all(
            data.get(key) is True
            for key in (
                "explicit_current_dhc_op08_material_present",
                "explicit_current_dhc_op08_material_contract_valid",
                "current_dhc_result_selected",
            )
        ):
            raise ValueError("DHD-OP02 scan-clear selection requires valid explicit current OP08")
        if data.get("explicit_current_dhc_op08_status_ref") != P7_R54_AHR_POST_DHC_DHD_DHC_OP08_ALLOWED_STATUS_REFS[0]:
            raise ValueError("DHD-OP02 scan-clear selected OP08 status changed")
    if outcome_ref in P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[1:3]:
        if data.get("current_dhc_result_selected") is not False:
            raise ValueError("DHD-OP02 R11/test-only outcome must remain unselected")
    expected_sufficient = bool(
        scan_clear and data.get("explicit_current_op05_wrapper_scan_clear_stopped") is True
    )
    if data.get("current_material_sufficient_for_dhr_op06_consideration") is not expected_sufficient:
        raise ValueError("DHD-OP02 current-material sufficiency changed")
    for field, count_field in (
        ("op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count"),
        ("op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count"),
        (
            "op02_input_promotion_or_autorun_claim_path_refs",
            "op02_input_promotion_or_autorun_claim_path_count",
        ),
        ("op02_input_no_touch_mutation_path_refs", "op02_input_no_touch_mutation_path_count"),
        ("dhd_op02_reason_refs", "dhd_op02_reason_ref_count"),
        ("dhd_op02_blocker_refs", "dhd_op02_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP02 count field changed: {count_field}")
    blocked = status_ref == P7_R54_AHR_POST_DHC_DHD_OP02_ALLOWED_STATUS_REFS[4]
    expected_next = (
        P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP02_REF
        if blocked
        else P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF
    )
    if data.get("next_required_step") != expected_next:
        raise ValueError("DHD-OP02 next step changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP02_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP02 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R3_TARGET_TEST_REF_REFS:
        raise ValueError("DHD-OP02 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R3_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHD-OP02 compileall refs changed")
    return True


def build_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call(
    op02_dhc_outcome_classification: Mapping[str, Any] | None = None,
    *,
    optional_current_existing_dhr_op05_result_wrapper: Mapping[str, Any] | None = None,
    allow_dhr_op06_consideration_candidate: bool = False,
    allow_dhr_op06_builder_call: bool = False,
    allow_dhr_op06_implicit_op05_fallback: bool = False,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Determine DHR-OP06 consideration eligibility without calling its builder."""

    op02 = op02_dhc_outcome_classification
    op05 = optional_current_existing_dhr_op05_result_wrapper
    op02_present = isinstance(op02, Mapping)
    op05_supplied = op05 is not None
    op05_present = isinstance(op05, Mapping)
    op02_contract_valid = False
    if op02_present:
        try:
            assert_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_contract(
                op02
            )
        except (AssertionError, TypeError, ValueError):
            op02_contract_valid = False
        else:
            op02_contract_valid = True
    op05_contract_valid = _existing_dhr_op05_valid(op05)
    op02_map = op02 if op02_present else {}
    op05_map = op05 if op05_present else {}
    outcome_ref = _clean_ref(
        op02_map.get("dhc_outcome_class_ref"), default="op02_dhc_outcome_class_missing"
    )
    op05_status_ref = _clean_ref(
        op05_map.get("dhr_op05_status_ref"), default="explicit_current_dhr_op05_status_missing"
    )
    op05_scan_clear = bool(
        op05_contract_valid
        and op05_status_ref
        == P7_R54_AHR_POST_DHC_DHD_EXISTING_DHR_OP05_SCAN_CLEAR_STATUS_REF
    )
    current_scan_clear_selected = bool(
        op02_contract_valid
        and outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[0]
        and op02_map.get("current_dhc_scan_clear_result_selected") is True
    )
    explicit_current_material_satisfied = bool(
        current_scan_clear_selected and op05_scan_clear
    )
    allow_types_valid = all(
        type(value) is bool
        for value in (
            allow_dhr_op06_consideration_candidate,
            allow_dhr_op06_builder_call,
            allow_dhr_op06_implicit_op05_fallback,
        )
    )
    allow_candidate = bool(
        type(allow_dhr_op06_consideration_candidate) is bool
        and allow_dhr_op06_consideration_candidate
    )
    builder_call_requested = bool(
        type(allow_dhr_op06_builder_call) is bool and allow_dhr_op06_builder_call
    )
    implicit_fallback_requested = bool(
        type(allow_dhr_op06_implicit_op05_fallback) is bool
        and allow_dhr_op06_implicit_op05_fallback
    )
    scan_root = {
        "op02_dhc_outcome_classification": op02 if op02_present else {},
        "explicit_current_dhr_op05_wrapper": op05 if op05_present else {},
    }
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(scan_root, path="dhd_op03_input")
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(scan_root, path="dhd_op03_input")
    )
    promotion_paths = _dedupe_clean_refs(
        _scan_promotion_or_autorun_claim_paths(scan_root, path="dhd_op03_input")
    )
    no_touch_paths = _dedupe_clean_refs(
        _scan_no_touch_mutation_paths(scan_root, path="dhd_op03_input")
    )
    blocked = bool(
        not allow_types_valid
        or not op02_contract_valid
        or builder_call_requested
        or implicit_fallback_requested
        or forbidden_paths
        or body_like_paths
        or promotion_paths
        or no_touch_paths
        or outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7]
    )
    not_allowed_outcomes = {
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[index]
        for index in (3, 4, 5, 6)
    }
    if blocked:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[3]
    elif outcome_ref in not_allowed_outcomes:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[2]
    elif explicit_current_material_satisfied and allow_candidate:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[0]
    else:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[1]
    candidate = status_ref == P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[0]
    may_be_needed: list[str] = []
    not_enough: list[str] = [
        P7_R54_AHR_POST_DHC_DHD_DHR_OP06_CONSIDERATION_NOT_PERMISSION_REF,
        P7_R54_AHR_POST_DHC_DHD_DHR_OP06_CONSIDERATION_NOT_DIRECTION_DECISION_REF,
    ]
    blockers: list[str] = []
    if current_scan_clear_selected:
        may_be_needed.append("explicit_current_DHC_OP08_scan_clear_result_selected")
    else:
        not_enough.append("explicit_current_DHC_OP08_scan_clear_result_not_selected")
    if op05_scan_clear:
        may_be_needed.extend(
            (
                "explicit_current_DHR_OP05_wrapper_scan_clear_stopped",
                P7_R54_AHR_POST_DHC_DHD_DHR_OP06_UNRESOLVED_BRANCH_REASON_REF,
            )
        )
    else:
        not_enough.append("explicit_current_DHR_OP05_scan_clear_wrapper_missing_or_invalid")
    if not allow_candidate:
        not_enough.append("DHR_OP06_consideration_candidate_not_allowed_by_input")
    if outcome_ref in not_allowed_outcomes:
        not_enough.append("DHC_outcome_waiting_repair_not_called_or_non_DHR_lane")
    if not allow_types_valid:
        blockers.append("DHD_OP03_allow_inputs_must_be_boolean")
    if not op02_contract_valid:
        blockers.append("DHD_OP03_requires_valid_DHD_OP02_material")
    if builder_call_requested:
        blockers.append("DHD_OP03_DHR_OP06_builder_call_request_is_prohibited")
    if implicit_fallback_requested:
        blockers.append("DHD_OP03_DHR_OP06_implicit_OP05_fallback_request_is_prohibited")
    if outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7]:
        blockers.append("DHD_OP03_blocked_DHC_outcome_cannot_be_considered")
    may_be_needed_refs = _dedupe_clean_refs(may_be_needed)
    not_enough_refs = _dedupe_clean_refs(not_enough)
    blocker_refs = _dedupe_clean_refs(
        [*blockers, *forbidden_paths, *body_like_paths, *promotion_paths, *no_touch_paths]
    )
    next_required_step = (
        P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP03_REF
        if blocked
        else P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF
    )

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP03_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op02_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op02_material_present": op02_present,
            "op02_contract_valid": op02_contract_valid,
            "op02_schema_version_ref": _clean_ref(
                op02_map.get("schema_version"), default="op02_schema_missing"
            ),
            "op02_material_ref": _clean_ref(
                op02_map.get("material_id"), default="op02_material_missing"
            ),
            "op02_status_ref": _clean_ref(
                op02_map.get("dhd_op02_status_ref"), default="op02_status_missing"
            ),
            "op02_dhc_outcome_class_ref": outcome_ref,
            "current_dhc_result_selected": bool(
                op02_contract_valid and op02_map.get("current_dhc_result_selected") is True
            ),
            "current_dhc_scan_clear_result_selected": current_scan_clear_selected,
            "scan_clear_capable_test_validation_only": bool(
                op02_contract_valid
                and op02_map.get("scan_clear_capable_test_validation_only") is True
            ),
            "explicit_current_op05_material_supplied": op05_supplied,
            "explicit_current_op05_material_present": op05_present,
            "explicit_current_op05_material_contract_valid_ref": op05_contract_valid,
            "explicit_current_op05_material_body_free": bool(
                op05_present and op05_map.get("body_free") is True
            ),
            "explicit_current_op05_material_schema_version_ref": _clean_ref(
                op05_map.get("schema_version"), default="explicit_current_dhr_op05_schema_missing"
            ),
            "explicit_current_op05_material_step_ref": _clean_ref(
                op05_map.get("operation_step_ref"), default="explicit_current_dhr_op05_step_missing"
            ),
            "explicit_current_op05_material_status_ref": op05_status_ref,
            "explicit_current_op05_material_scan_clear_stopped": op05_scan_clear,
            "allow_dhr_op06_consideration_candidate": allow_candidate,
            "allow_dhr_op06_builder_call": builder_call_requested,
            "allow_dhr_op06_implicit_op05_fallback": implicit_fallback_requested,
            "allow_input_types_valid": allow_types_valid,
            "explicit_current_material_required": True,
            "explicit_current_material_satisfied": explicit_current_material_satisfied,
            "unresolved_branch_reason_confirmed": explicit_current_material_satisfied,
            "dhr_op06_consideration_is_not_based_only_on_next_operation_order": explicit_current_material_satisfied,
            "dhd_op03_status_ref": status_ref,
            "bodyfree_dhr_op06_consideration_eligibility_status_ref": status_ref,
            "dhd_op03_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS,
            "dhd_op03_allowed_status_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS
            ),
            "dhr_op06_consideration_candidate": candidate,
            "dhr_op06_consideration_eligibility_decided_here": True,
            "why_dhr_op06_consideration_may_be_needed_refs": may_be_needed_refs,
            "why_dhr_op06_consideration_may_be_needed_ref_count": len(may_be_needed_refs),
            "why_dhr_op06_consideration_is_not_enough_refs": not_enough_refs,
            "why_dhr_op06_consideration_is_not_enough_ref_count": len(not_enough_refs),
            "dhr_op06_consideration_blocker_refs": blocker_refs,
            "dhr_op06_consideration_blocker_ref_count": len(blocker_refs),
            "op03_input_forbidden_payload_key_path_refs": forbidden_paths,
            "op03_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op03_input_body_like_value_path_refs": body_like_paths,
            "op03_input_body_like_value_path_count": len(body_like_paths),
            "op03_input_promotion_or_autorun_claim_path_refs": promotion_paths,
            "op03_input_promotion_or_autorun_claim_path_count": len(promotion_paths),
            "op03_input_no_touch_mutation_path_refs": no_touch_paths,
            "op03_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhr_op06_permission_produced_here": False,
            "dhr_op06_builder_call_allowed_here": False,
            "dhr_op06_implicit_op05_fallback_allowed_here": False,
            "dhd_op03_does_not_call_dhc_builder": True,
            "dhd_op03_does_not_call_existing_dhr_op05_builder": True,
            "dhd_op03_does_not_call_dhr_op06_builder": True,
            "dhd_op03_does_not_use_dhr_op06_implicit_op05_fallback": True,
            "dhd_op03_does_not_materialize_dhr_op07_or_execute_dmd_r52": True,
            "dhd_op03_does_not_run_p7_readfeel_evaluation": True,
            "dhd_op03_does_not_start_p8_or_release": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "fixed_non_promotion_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP03_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(
                P7_R54_AHR_POST_DHC_DHD_OP03_NOT_YET_IMPLEMENTED_STEPS
            ),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R3_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(
                P7_R54_AHR_POST_DHC_DHD_R3_COMPILEALL_TARGET_REF_REFS
            ),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "dhd_op02_implemented": True,
            "dhd_op03_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert strict DHD-OP03 eligibility and no-builder-call boundaries."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FIELD_REFS, source="DHD-OP03"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP03 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP03_SCHEMA_VERSION:
        raise ValueError("DHD-OP03 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP03_STEP_REF:
        raise ValueError("DHD-OP03 step mismatch")
    _assert_r3_shared_contract(
        data,
        source="DHD-OP03",
        required_false_refs=P7_R54_AHR_POST_DHC_DHD_OP03_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "explicit_current_material_required",
        "dhr_op06_consideration_eligibility_decided_here",
        "dhd_op03_does_not_call_dhc_builder",
        "dhd_op03_does_not_call_existing_dhr_op05_builder",
        "dhd_op03_does_not_call_dhr_op06_builder",
        "dhd_op03_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op03_does_not_materialize_dhr_op07_or_execute_dmd_r52",
        "dhd_op03_does_not_run_p7_readfeel_evaluation",
        "dhd_op03_does_not_start_p8_or_release",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP03 required true field changed: {key}")
    for key in (
        "dhr_op06_permission_produced_here",
        "dhr_op06_builder_call_allowed_here",
        "dhr_op06_implicit_op05_fallback_allowed_here",
        "dhr_op06_builder_called_here",
        "dhr_op06_implicit_op05_fallback_used_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "p8_question_design_started",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHD-OP03 forbidden execution/promotion changed: {key}")
    if tuple(data.get("dhd_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP03 allowed status refs changed")
    if data.get("dhd_op03_allowed_status_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS
    ):
        raise ValueError("DHD-OP03 allowed status count changed")
    status_ref = data.get("dhd_op03_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP03 status is not allowed")
    if data.get("bodyfree_dhr_op06_consideration_eligibility_status_ref") != status_ref:
        raise ValueError("DHD-OP03 status alias changed")
    eligible = status_ref == P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[0]
    blocked = status_ref == P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[3]
    if data.get("dhr_op06_consideration_candidate") is not eligible:
        raise ValueError("DHD-OP03 candidate/status mismatch")
    expected_satisfied = bool(
        data.get("current_dhc_scan_clear_result_selected") is True
        and data.get("explicit_current_op05_material_scan_clear_stopped") is True
        and data.get("op02_contract_valid") is True
        and data.get("explicit_current_op05_material_contract_valid_ref") is True
    )
    if data.get("explicit_current_material_satisfied") is not expected_satisfied:
        raise ValueError("DHD-OP03 explicit current material sufficiency changed")
    if data.get("unresolved_branch_reason_confirmed") is not expected_satisfied:
        raise ValueError("DHD-OP03 unresolved branch reason changed")
    if data.get("dhr_op06_consideration_is_not_based_only_on_next_operation_order") is not expected_satisfied:
        raise ValueError("DHD-OP03 next-operation-only guard changed")
    if eligible:
        if not expected_satisfied or data.get("allow_dhr_op06_consideration_candidate") is not True:
            raise ValueError("DHD-OP03 eligible branch requires explicit material and allowance")
        if data.get("allow_dhr_op06_builder_call") is not False:
            raise ValueError("DHD-OP03 eligible branch cannot allow builder call")
        if data.get("allow_dhr_op06_implicit_op05_fallback") is not False:
            raise ValueError("DHD-OP03 eligible branch cannot allow implicit fallback")
        if P7_R54_AHR_POST_DHC_DHD_DHR_OP06_UNRESOLVED_BRANCH_REASON_REF not in (
            data.get("why_dhr_op06_consideration_may_be_needed_refs") or []
        ):
            raise ValueError("DHD-OP03 eligible branch must record unresolved branch reason")
    if data.get("allow_dhr_op06_builder_call") is True or data.get(
        "allow_dhr_op06_implicit_op05_fallback"
    ) is True:
        if not blocked:
            raise ValueError("DHD-OP03 builder/fallback request must be blocked")
    for field, count_field in (
        (
            "why_dhr_op06_consideration_may_be_needed_refs",
            "why_dhr_op06_consideration_may_be_needed_ref_count",
        ),
        (
            "why_dhr_op06_consideration_is_not_enough_refs",
            "why_dhr_op06_consideration_is_not_enough_ref_count",
        ),
        ("dhr_op06_consideration_blocker_refs", "dhr_op06_consideration_blocker_ref_count"),
        ("op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count"),
        ("op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count"),
        (
            "op03_input_promotion_or_autorun_claim_path_refs",
            "op03_input_promotion_or_autorun_claim_path_count",
        ),
        ("op03_input_no_touch_mutation_path_refs", "op03_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP03 count field changed: {count_field}")
    expected_next = (
        P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP03_REF
        if blocked
        else P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF
    )
    if data.get("next_required_step") != expected_next:
        raise ValueError("DHD-OP03 next step changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP03_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP03 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R3_TARGET_TEST_REF_REFS:
        raise ValueError("DHD-OP03 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R3_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHD-OP03 compileall refs changed")
    return True


# ---------------------------------------------------------------------------
# R4: DHD-OP04 / DHD-OP05 only.
# OP04 records eligibility to reconnect with P7 product-readfeel evaluation;
# it never creates or evaluates cases. OP05 selects one body-free next-design
# direction (or an explicit hold) and never turns that selection into runtime.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHC_DHD_R4_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_R3_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op04_op05_20260709.py",
)
P7_R54_AHR_POST_DHC_DHD_R4_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_R3_COMPILEALL_TARGET_REF_REFS
)
P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS: Final[
    tuple[str, ...]
] = P7_R54_AHR_POST_DHC_DHD_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS

P7_R54_AHR_POST_DHC_DHD_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_OP03_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_OP04_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
    }
)
P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
    }
)

P7_R54_AHR_POST_DHC_DHD_PRODUCT_VALUE_RETURN_PRESSURE_REF: Final = (
    "R54_AHR_boundary_reinforcement_should_return_to_Cocolon_product_readfeel_value"
)
P7_R54_AHR_POST_DHC_DHD_MINIMUM_CASE_SET_REQUIRED_REF: Final = (
    "separate_P7_product_readfeel_blind_QA_continued_input_pilot_minimum_case_set_required"
)
P7_R54_AHR_POST_DHC_DHD_P7_COMPLETION_STILL_UNCONFIRMED_REFS: Final[
    tuple[str, ...]
] = (
    "baseline_corpus_batch_evaluation_unconfirmed_here",
    "long_run_multi_input_value_progression_unconfirmed_here",
    "Product_Pass_vs_Release_Ready_separation_not_completed_here",
    "question_need_observation_collection_not_completed_here",
)
P7_R54_AHR_POST_DHC_DHD_DIRECTION_COMPARISON_AXIS_REFS: Final[tuple[str, ...]] = (
    "avoid_understood_pretending",
    "Cocolon_product_value_and_response_strength",
    "continued_input_value",
    "external_pilot_connection",
    "no_downstream_execution_P8_or_release_promotion",
    "avoid_R54_AHR_boundary_reinforcement_becoming_the_goal",
    "explicit_current_material_sufficiency",
)

P7_R54_AHR_POST_DHC_DHD_OP04_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op02_schema_version_ref",
    "op02_material_ref",
    "op02_status_ref",
    "dhc_outcome_class_ref",
    "current_dhc_result_selected",
    "current_dhc_scan_clear_result_selected",
    "scan_clear_capable_test_validation_only",
    "op03_material_present",
    "op03_contract_valid",
    "op03_schema_version_ref",
    "op03_material_ref",
    "op03_status_ref",
    "dhr_op06_consideration_candidate",
    "explicit_current_material_satisfied_for_dhr_op06_consideration",
    "p7_roadmap_readfeel_axis_refs_supplied",
    "p7_roadmap_readfeel_axis_refs",
    "p7_roadmap_readfeel_axis_ref_count",
    "p7_roadmap_readfeel_axis_refs_complete",
    "optional_existing_p7_runner_refs_supplied",
    "optional_existing_p7_runner_refs",
    "optional_existing_p7_runner_ref_count",
    "optional_existing_p7_runner_refs_recognized",
    "existing_p7_runner_executed_here",
    "dhd_op04_status_ref",
    "bodyfree_p7_readfeel_reconnection_eligibility_status_ref",
    "dhd_op04_allowed_status_refs",
    "dhd_op04_allowed_status_ref_count",
    "p7_readfeel_reconnection_candidate",
    "product_value_return_pressure_ref",
    "minimum_case_set_required",
    "minimum_case_set_required_ref",
    "minimum_case_set_created_here",
    "blind_qa_return_required",
    "continued_input_observation_required",
    "pilot_readiness_observation_required",
    "p7_completion_still_unconfirmed_refs",
    "p7_completion_still_unconfirmed_ref_count",
    "question_need_observation_allowed_as_bodyfree",
    "question_need_observation_material_created_here",
    "p7_readfeel_actual_case_created_here",
    "p7_readfeel_actual_evaluation_started_here",
    "op04_input_forbidden_payload_key_path_refs",
    "op04_input_forbidden_payload_key_path_count",
    "op04_input_body_like_value_path_refs",
    "op04_input_body_like_value_path_count",
    "op04_input_promotion_or_autorun_claim_path_refs",
    "op04_input_promotion_or_autorun_claim_path_count",
    "op04_input_no_touch_mutation_path_refs",
    "op04_input_no_touch_mutation_path_count",
    "dhd_op04_reason_refs",
    "dhd_op04_reason_ref_count",
    "dhd_op04_blocker_refs",
    "dhd_op04_blocker_ref_count",
    "dhd_op04_does_not_call_dhc_or_dhr_builder",
    "dhd_op04_does_not_create_or_evaluate_readfeel_cases",
    "dhd_op04_does_not_materialize_question_text",
    "dhd_op04_does_not_start_p8",
    "dhd_op04_does_not_claim_p7_complete_or_release",
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
    "optional_product_readfeel_regression_ref_refs",
    "public_contract",
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "dhd_op04_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP05_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op02_schema_version_ref",
    "op02_material_ref",
    "op02_status_ref",
    "dhc_outcome_class_ref",
    "current_dhc_result_selected",
    "current_dhc_scan_clear_result_selected",
    "op03_material_present",
    "op03_contract_valid",
    "op03_schema_version_ref",
    "op03_material_ref",
    "op03_status_ref",
    "op04_material_present",
    "op04_contract_valid",
    "op04_schema_version_ref",
    "op04_material_ref",
    "op04_status_ref",
    "dhd_op05_status_ref",
    "bodyfree_direction_comparator_status_ref",
    "dhd_op05_allowed_status_refs",
    "dhd_op05_allowed_status_ref_count",
    "direction_decision_ref",
    "direction_decision_refs",
    "direction_decision_ref_count",
    "direction_comparison_axis_refs",
    "direction_comparison_axis_ref_count",
    "dhr_op06_consideration_candidate",
    "dhr_op06_consideration_has_direct_branch_resolution_reason",
    "p7_readfeel_reconnection_candidate",
    "current_dhc_material_selection_required",
    "repair_or_wait_boundary_required",
    "non_dhr_lane_route_preservation_required",
    "no_touch_repair_or_hold_required",
    "decision_reason_refs",
    "decision_reason_ref_count",
    "decision_blocker_refs",
    "decision_blocker_ref_count",
    "selected_next_design_candidate_ref",
    "selected_next_design_candidate_refs",
    "selected_next_design_candidate_ref_count",
    "next_runtime_execution_allowed_here",
    "dhr_op06_builder_call_allowed_here",
    "dhr_op06_implicit_op05_fallback_allowed_here",
    "p7_readfeel_evaluation_execution_allowed_here",
    "op05_input_forbidden_payload_key_path_refs",
    "op05_input_forbidden_payload_key_path_count",
    "op05_input_body_like_value_path_refs",
    "op05_input_body_like_value_path_count",
    "op05_input_promotion_or_autorun_claim_path_refs",
    "op05_input_promotion_or_autorun_claim_path_count",
    "op05_input_no_touch_mutation_path_refs",
    "op05_input_no_touch_mutation_path_count",
    "dhd_op05_does_not_call_dhc_or_dhr_builder",
    "dhd_op05_does_not_use_dhr_op06_implicit_op05_fallback",
    "dhd_op05_does_not_execute_selected_direction",
    "dhd_op05_does_not_create_or_evaluate_readfeel_cases",
    "dhd_op05_does_not_start_p8",
    "dhd_op05_does_not_claim_p7_complete_or_release",
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
    "optional_product_readfeel_regression_ref_refs",
    "public_contract",
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "dhd_op04_implemented",
    "dhd_op05_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP04_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FALSE_FLAG_REFS
    )
)
P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP05_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FALSE_FLAG_REFS
    )
)


def _op03_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhc_dhd_op03_dhr_op06_consideration_eligibility_without_call_contract(
            data
        )
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def _known_ref_sequence(
    value: Any,
    *,
    allowed_refs: Sequence[str],
    default_refs: Sequence[str] = (),
) -> tuple[bool, bool, list[str], bool]:
    supplied = value is not None
    if value is None:
        refs = list(default_refs)
        return supplied, True, refs, tuple(refs) == tuple(allowed_refs)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return supplied, False, [], False
    raw_values = list(value)
    shape_valid = all(isinstance(item, str) and bool(item.strip()) for item in raw_values)
    if not shape_valid:
        return supplied, False, [], False
    cleaned = _dedupe_clean_refs(raw_values)
    recognized = [ref for ref in cleaned if ref in allowed_refs]
    all_recognized = len(recognized) == len(cleaned)
    complete = all_recognized and set(recognized) == set(allowed_refs)
    return supplied, all_recognized, recognized, complete


def build_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility(
    op02_dhc_outcome_classification: Mapping[str, Any] | None = None,
    op03_dhr_op06_consideration_eligibility: Mapping[str, Any] | None = None,
    *,
    p7_roadmap_readfeel_axis_refs: Sequence[str] | None = None,
    optional_existing_p7_runner_refs: Sequence[str] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Record P7 readfeel reconnection eligibility without creating/evaluating cases."""

    op02 = op02_dhc_outcome_classification
    op03 = op03_dhr_op06_consideration_eligibility
    op02_present = isinstance(op02, Mapping)
    op03_present = isinstance(op03, Mapping)
    op02_contract_valid = False
    if op02_present:
        try:
            assert_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_contract(
                op02
            )
        except (AssertionError, TypeError, ValueError):
            op02_contract_valid = False
        else:
            op02_contract_valid = True
    op03_contract_valid = _op03_valid(op03)
    op02_map = op02 if op02_present else {}
    op03_map = op03 if op03_present else {}
    outcome_ref = _clean_ref(
        op02_map.get("dhc_outcome_class_ref"), default="op02_dhc_outcome_class_missing"
    )
    op03_status_ref = _clean_ref(
        op03_map.get("dhd_op03_status_ref"), default="op03_status_missing"
    )
    axes_supplied, axes_input_valid, axis_refs, axes_complete = _known_ref_sequence(
        p7_roadmap_readfeel_axis_refs,
        allowed_refs=P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_AXIS_REFS,
        default_refs=P7_R54_AHR_POST_DHC_DHD_P7_READFEEL_AXIS_REFS,
    )
    (
        runner_refs_supplied,
        runner_refs_recognized,
        runner_refs,
        _runner_ref_set_complete,
    ) = _known_ref_sequence(
        optional_existing_p7_runner_refs,
        allowed_refs=P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS,
    )
    scan_root = {
        "op02_dhc_outcome_classification": op02 if op02_present else {},
        "op03_dhr_op06_consideration_eligibility": op03 if op03_present else {},
    }
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(scan_root, path="dhd_op04_input")
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(scan_root, path="dhd_op04_input")
    )
    promotion_paths = _dedupe_clean_refs(
        _scan_promotion_or_autorun_claim_paths(scan_root, path="dhd_op04_input")
    )
    no_touch_paths = _dedupe_clean_refs(
        _scan_no_touch_mutation_paths(scan_root, path="dhd_op04_input")
    )
    blocked = bool(
        not op02_contract_valid
        or not op03_contract_valid
        or not axes_input_valid
        or not runner_refs_recognized
        or forbidden_paths
        or body_like_paths
        or promotion_paths
        or no_touch_paths
        or outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7]
        or op03_status_ref == P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[3]
    )
    deferred_outcomes = {
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[index]
        for index in (3, 4, 5, 6)
    }
    deferred = bool(
        not blocked
        and (
            outcome_ref in deferred_outcomes
            or op03_status_ref == P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[2]
        )
    )
    candidate = bool(not blocked and not deferred and axes_complete)
    if blocked:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[3]
    elif deferred:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[2]
    elif (
        candidate
        and outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[0]
        and op03_status_ref == P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[0]
    ):
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[0]
    else:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[1]
    reasons: list[str] = [
        "R54_AHR_boundary_reinforcement_must_reconnect_to_Cocolon_product_value",
        "P7_completion_baseline_long_run_and_release_separation_remain_unconfirmed_here",
    ]
    blockers: list[str] = []
    if outcome_ref in {
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[1],
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[2],
    }:
        reasons.append("R11_or_test_validation_only_cannot_be_promoted_to_DHR_OP06_current_material")
    if op03_contract_valid and op03_map.get("explicit_current_material_satisfied") is False:
        reasons.append("DHR_OP06_consideration_lacks_explicit_current_material_or_allowance")
    if candidate:
        reasons.extend(
            (
                "P7_Product_Read_Feel_Blind_QA_and_continued_input_return_is_a_safe_design_candidate",
                "question_need_is_observation_only_without_question_text_or_P8_start",
            )
        )
    if not axes_complete:
        blockers.append("complete_canonical_P7_readfeel_axis_refs_required_before_reconnection_candidate")
    if not axes_input_valid:
        blockers.append("P7_readfeel_axis_refs_input_invalid")
    if not runner_refs_recognized:
        blockers.append("optional_existing_P7_runner_refs_must_be_known_bodyfree_refs")
    if deferred:
        blockers.append("close_DHC_waiting_repair_not_called_or_non_DHR_route_before_readfeel_reconnection")
    if outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7]:
        blockers.append("unsafe_blocked_DHC_outcome_requires_no_touch_hold")
    reason_refs = _dedupe_clean_refs(reasons)
    blocker_refs = _dedupe_clean_refs(
        [*blockers, *forbidden_paths, *body_like_paths, *promotion_paths, *no_touch_paths]
    )

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP04_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op03_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op02_material_present": op02_present,
            "op02_contract_valid": op02_contract_valid,
            "op02_schema_version_ref": _clean_ref(
                op02_map.get("schema_version"), default="op02_schema_missing"
            ),
            "op02_material_ref": _clean_ref(
                op02_map.get("material_id"), default="op02_material_missing"
            ),
            "op02_status_ref": _clean_ref(
                op02_map.get("dhd_op02_status_ref"), default="op02_status_missing"
            ),
            "dhc_outcome_class_ref": outcome_ref,
            "current_dhc_result_selected": bool(
                op02_contract_valid and op02_map.get("current_dhc_result_selected") is True
            ),
            "current_dhc_scan_clear_result_selected": bool(
                op02_contract_valid
                and op02_map.get("current_dhc_scan_clear_result_selected") is True
            ),
            "scan_clear_capable_test_validation_only": bool(
                op02_contract_valid
                and op02_map.get("scan_clear_capable_test_validation_only") is True
            ),
            "op03_material_present": op03_present,
            "op03_contract_valid": op03_contract_valid,
            "op03_schema_version_ref": _clean_ref(
                op03_map.get("schema_version"), default="op03_schema_missing"
            ),
            "op03_material_ref": _clean_ref(
                op03_map.get("material_id"), default="op03_material_missing"
            ),
            "op03_status_ref": op03_status_ref,
            "dhr_op06_consideration_candidate": bool(
                op03_contract_valid
                and op03_map.get("dhr_op06_consideration_candidate") is True
            ),
            "explicit_current_material_satisfied_for_dhr_op06_consideration": bool(
                op03_contract_valid and op03_map.get("explicit_current_material_satisfied") is True
            ),
            "p7_roadmap_readfeel_axis_refs_supplied": axes_supplied,
            "p7_roadmap_readfeel_axis_refs": axis_refs,
            "p7_roadmap_readfeel_axis_ref_count": len(axis_refs),
            "p7_roadmap_readfeel_axis_refs_complete": axes_complete,
            "optional_existing_p7_runner_refs_supplied": runner_refs_supplied,
            "optional_existing_p7_runner_refs": runner_refs,
            "optional_existing_p7_runner_ref_count": len(runner_refs),
            "optional_existing_p7_runner_refs_recognized": runner_refs_recognized,
            "existing_p7_runner_executed_here": False,
            "dhd_op04_status_ref": status_ref,
            "bodyfree_p7_readfeel_reconnection_eligibility_status_ref": status_ref,
            "dhd_op04_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS,
            "dhd_op04_allowed_status_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS
            ),
            "p7_readfeel_reconnection_candidate": candidate,
            "product_value_return_pressure_ref": P7_R54_AHR_POST_DHC_DHD_PRODUCT_VALUE_RETURN_PRESSURE_REF,
            "minimum_case_set_required": True,
            "minimum_case_set_required_ref": P7_R54_AHR_POST_DHC_DHD_MINIMUM_CASE_SET_REQUIRED_REF,
            "minimum_case_set_created_here": False,
            "blind_qa_return_required": candidate,
            "continued_input_observation_required": candidate,
            "pilot_readiness_observation_required": candidate,
            "p7_completion_still_unconfirmed_refs": list(
                P7_R54_AHR_POST_DHC_DHD_P7_COMPLETION_STILL_UNCONFIRMED_REFS
            ),
            "p7_completion_still_unconfirmed_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_P7_COMPLETION_STILL_UNCONFIRMED_REFS
            ),
            "question_need_observation_allowed_as_bodyfree": True,
            "question_need_observation_material_created_here": False,
            "p7_readfeel_actual_case_created_here": False,
            "p7_readfeel_actual_evaluation_started_here": False,
            "op04_input_forbidden_payload_key_path_refs": forbidden_paths,
            "op04_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op04_input_body_like_value_path_refs": body_like_paths,
            "op04_input_body_like_value_path_count": len(body_like_paths),
            "op04_input_promotion_or_autorun_claim_path_refs": promotion_paths,
            "op04_input_promotion_or_autorun_claim_path_count": len(promotion_paths),
            "op04_input_no_touch_mutation_path_refs": no_touch_paths,
            "op04_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhd_op04_reason_refs": reason_refs,
            "dhd_op04_reason_ref_count": len(reason_refs),
            "dhd_op04_blocker_refs": blocker_refs,
            "dhd_op04_blocker_ref_count": len(blocker_refs),
            "dhd_op04_does_not_call_dhc_or_dhr_builder": True,
            "dhd_op04_does_not_create_or_evaluate_readfeel_cases": True,
            "dhd_op04_does_not_materialize_question_text": True,
            "dhd_op04_does_not_start_p8": True,
            "dhd_op04_does_not_claim_p7_complete_or_release": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "fixed_non_promotion_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP04_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(
                P7_R54_AHR_POST_DHC_DHD_OP04_NOT_YET_IMPLEMENTED_STEPS
            ),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R4_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(
                P7_R54_AHR_POST_DHC_DHD_R4_COMPILEALL_TARGET_REF_REFS
            ),
            "optional_product_readfeel_regression_ref_refs": list(
                P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
            ),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "dhd_op02_implemented": True,
            "dhd_op03_implemented": True,
            "dhd_op04_implemented": True,
            "next_required_step": P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHD-OP04 body-free eligibility without readfeel execution."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FIELD_REFS, source="DHD-OP04"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP04 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP04_SCHEMA_VERSION:
        raise ValueError("DHD-OP04 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP04_STEP_REF:
        raise ValueError("DHD-OP04 step mismatch")
    _assert_r3_shared_contract(
        data,
        source="DHD-OP04",
        required_false_refs=P7_R54_AHR_POST_DHC_DHD_OP04_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "minimum_case_set_required",
        "question_need_observation_allowed_as_bodyfree",
        "dhd_op04_does_not_call_dhc_or_dhr_builder",
        "dhd_op04_does_not_create_or_evaluate_readfeel_cases",
        "dhd_op04_does_not_materialize_question_text",
        "dhd_op04_does_not_start_p8",
        "dhd_op04_does_not_claim_p7_complete_or_release",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP04 required true field changed: {key}")
    for key in (
        "existing_p7_runner_executed_here",
        "minimum_case_set_created_here",
        "question_need_observation_material_created_here",
        "p7_readfeel_actual_case_created_here",
        "p7_readfeel_actual_evaluation_started_here",
        "p7_readfeel_evaluation_started_here",
        "question_need_observation_rows_created_here",
        "question_text_materialized_here",
        "p8_question_design_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHD-OP04 forbidden execution/promotion changed: {key}")
    if data.get("product_value_return_pressure_ref") != P7_R54_AHR_POST_DHC_DHD_PRODUCT_VALUE_RETURN_PRESSURE_REF:
        raise ValueError("DHD-OP04 product value pressure ref changed")
    if data.get("minimum_case_set_required_ref") != P7_R54_AHR_POST_DHC_DHD_MINIMUM_CASE_SET_REQUIRED_REF:
        raise ValueError("DHD-OP04 minimum case set ref changed")
    if tuple(data.get("dhd_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP04 allowed status refs changed")
    if data.get("dhd_op04_allowed_status_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS
    ):
        raise ValueError("DHD-OP04 allowed status count changed")
    status_ref = data.get("dhd_op04_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP04 status is not allowed")
    if data.get("bodyfree_p7_readfeel_reconnection_eligibility_status_ref") != status_ref:
        raise ValueError("DHD-OP04 status alias changed")
    candidate = data.get("p7_readfeel_reconnection_candidate") is True
    if candidate:
        if data.get("p7_roadmap_readfeel_axis_refs_complete") is not True:
            raise ValueError("DHD-OP04 candidate requires complete roadmap axes")
        if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[:2]:
            raise ValueError("DHD-OP04 candidate status changed")
        for key in (
            "blind_qa_return_required",
            "continued_input_observation_required",
            "pilot_readiness_observation_required",
        ):
            if data.get(key) is not True:
                raise ValueError(f"DHD-OP04 candidate product requirement changed: {key}")
    else:
        for key in (
            "blind_qa_return_required",
            "continued_input_observation_required",
            "pilot_readiness_observation_required",
        ):
            if data.get(key) is not False:
                raise ValueError(f"DHD-OP04 non-candidate requirement changed: {key}")
    if tuple(data.get("p7_completion_still_unconfirmed_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_P7_COMPLETION_STILL_UNCONFIRMED_REFS:
        raise ValueError("DHD-OP04 P7 unconfirmed refs changed")
    if data.get("p7_completion_still_unconfirmed_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_P7_COMPLETION_STILL_UNCONFIRMED_REFS
    ):
        raise ValueError("DHD-OP04 P7 unconfirmed ref count changed")
    for field, count_field in (
        ("p7_roadmap_readfeel_axis_refs", "p7_roadmap_readfeel_axis_ref_count"),
        ("optional_existing_p7_runner_refs", "optional_existing_p7_runner_ref_count"),
        ("p7_completion_still_unconfirmed_refs", "p7_completion_still_unconfirmed_ref_count"),
        ("op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count"),
        ("op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count"),
        (
            "op04_input_promotion_or_autorun_claim_path_refs",
            "op04_input_promotion_or_autorun_claim_path_count",
        ),
        ("op04_input_no_touch_mutation_path_refs", "op04_input_no_touch_mutation_path_count"),
        ("dhd_op04_reason_refs", "dhd_op04_reason_ref_count"),
        ("dhd_op04_blocker_refs", "dhd_op04_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP04 count field changed: {count_field}")
    if tuple(data.get("optional_product_readfeel_regression_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS:
        raise ValueError("DHD-OP04 optional readfeel regression refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP04_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP04 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R4_TARGET_TEST_REF_REFS:
        raise ValueError("DHD-OP04 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R4_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHD-OP04 compileall refs changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF:
        raise ValueError("DHD-OP04 next step changed")
    return True


def _op04_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhc_dhd_op04_p7_readfeel_reconnection_eligibility_contract(
            data
        )
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def build_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator(
    op02_dhc_outcome_classification: Mapping[str, Any] | None = None,
    op03_dhr_op06_consideration_eligibility: Mapping[str, Any] | None = None,
    op04_p7_readfeel_reconnection_eligibility: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Select a body-free next-design direction without executing it."""

    op02 = op02_dhc_outcome_classification
    op03 = op03_dhr_op06_consideration_eligibility
    op04 = op04_p7_readfeel_reconnection_eligibility
    op02_present = isinstance(op02, Mapping)
    op03_present = isinstance(op03, Mapping)
    op04_present = isinstance(op04, Mapping)
    op02_contract_valid = False
    if op02_present:
        try:
            assert_p7_r54_ahr_post_dhc_dhd_op02_dhc_outcome_class_current_material_sufficiency_check_contract(
                op02
            )
        except (AssertionError, TypeError, ValueError):
            op02_contract_valid = False
        else:
            op02_contract_valid = True
    op03_contract_valid = _op03_valid(op03)
    op04_contract_valid = _op04_valid(op04)
    op02_map = op02 if op02_present else {}
    op03_map = op03 if op03_present else {}
    op04_map = op04 if op04_present else {}
    outcome_ref = _clean_ref(
        op02_map.get("dhc_outcome_class_ref"), default="op02_dhc_outcome_class_missing"
    )
    op03_status_ref = _clean_ref(
        op03_map.get("dhd_op03_status_ref"), default="op03_status_missing"
    )
    op04_status_ref = _clean_ref(
        op04_map.get("dhd_op04_status_ref"), default="op04_status_missing"
    )
    dhr_candidate = bool(
        op03_contract_valid and op03_map.get("dhr_op06_consideration_candidate") is True
    )
    p7_candidate = bool(
        op04_contract_valid and op04_map.get("p7_readfeel_reconnection_candidate") is True
    )
    direct_branch_reason = bool(
        dhr_candidate
        and P7_R54_AHR_POST_DHC_DHD_DHR_OP06_UNRESOLVED_BRANCH_REASON_REF
        in (op03_map.get("why_dhr_op06_consideration_may_be_needed_refs") or [])
    )
    scan_root = {
        "op02_dhc_outcome_classification": op02 if op02_present else {},
        "op03_dhr_op06_consideration_eligibility": op03 if op03_present else {},
        "op04_p7_readfeel_reconnection_eligibility": op04 if op04_present else {},
    }
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(scan_root, path="dhd_op05_input")
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(scan_root, path="dhd_op05_input")
    )
    promotion_paths = _dedupe_clean_refs(
        _scan_promotion_or_autorun_claim_paths(scan_root, path="dhd_op05_input")
    )
    no_touch_paths = _dedupe_clean_refs(
        _scan_no_touch_mutation_paths(scan_root, path="dhd_op05_input")
    )
    blocked = bool(
        not op02_contract_valid
        or not op03_contract_valid
        or not op04_contract_valid
        or forbidden_paths
        or body_like_paths
        or promotion_paths
        or no_touch_paths
        or outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[7]
        or op03_status_ref == P7_R54_AHR_POST_DHC_DHD_OP03_ALLOWED_STATUS_REFS[3]
        or op04_status_ref == P7_R54_AHR_POST_DHC_DHD_OP04_ALLOWED_STATUS_REFS[3]
    )
    reasons: list[str] = []
    blockers: list[str] = []
    if blocked:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[3]
        decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5]
        reasons.append("DHD_OP05_no_touch_repair_or_hold_required")
        blockers.append("repair_invalid_or_unsafe_direction_comparator_inputs")
    elif outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[6]:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[0]
        decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[4]
        reasons.append("DHD_OP05_preserves_non_DHR_lane_route_without_DHR_or_readfeel_promotion")
    elif outcome_ref in {
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[index]
        for index in (3, 4, 5)
    }:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[1]
        decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[3]
        reasons.append("DHD_OP05_waiting_repair_or_not_called_boundary_must_close_first")
        blockers.append("collect_or_repair_explicit_current_DHC_DHR_material_before_direction_design")
    elif outcome_ref in {
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[1],
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[2],
    }:
        if p7_candidate:
            status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[0]
            decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[1]
            reasons.extend(
                (
                    "DHD_OP05_R11_or_test_only_cannot_select_DHR_OP06_consideration_design_first",
                    "DHD_OP05_returns_to_P7_product_readfeel_without_claiming_P7_complete",
                )
            )
        else:
            status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[2]
            decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[2]
            reasons.append("DHD_OP05_R11_only_has_no_current_selected_DHC_material_and_no_safe_readfeel_candidate")
            blockers.append("select_explicit_current_DHC_OP08_or_DHR_OP05_material_without_synthesis")
    elif outcome_ref == P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[0]:
        if dhr_candidate and direct_branch_reason:
            status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[0]
            decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[0]
            reasons.extend(
                (
                    "DHD_OP05_explicit_current_scan_clear_material_supports_DHR_OP06_consideration_design",
                    "DHD_OP05_unresolved_DHR_branch_is_recorded_without_builder_call",
                )
            )
            if p7_candidate:
                reasons.append("DHD_OP05_compared_P7_readfeel_candidate_but_resolves_explicit_DHR_branch_design_first")
        elif p7_candidate:
            status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[0]
            decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[1]
            reasons.append("DHD_OP05_DHR_consideration_lacks_direct_candidate_reason_so_P7_readfeel_design_first")
        else:
            status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[2]
            decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[2]
            reasons.append("DHD_OP05_scan_clear_selected_but_comparison_candidates_lack_sufficient_material")
            blockers.append("complete_explicit_current_OP05_or_P7_readfeel_axis_material")
    else:
        status_ref = P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS[3]
        decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5]
        reasons.append("DHD_OP05_unknown_DHC_outcome_requires_no_touch_hold")
        blockers.append("repair_unknown_DHC_outcome_before_direction_comparison")
    decision_index = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS.index(decision_ref)
    selected_candidate_ref = P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[
        decision_index
    ]
    current_material_selection_required = (
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[2]
    )
    repair_or_wait_required = (
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[3]
    )
    non_dhr_route_required = (
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[4]
    )
    no_touch_hold_required = (
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5]
    )
    reason_refs = _dedupe_clean_refs(reasons)
    blocker_refs = _dedupe_clean_refs(
        [*blockers, *forbidden_paths, *body_like_paths, *promotion_paths, *no_touch_paths]
    )

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP05_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op04_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op02_material_present": op02_present,
            "op02_contract_valid": op02_contract_valid,
            "op02_schema_version_ref": _clean_ref(
                op02_map.get("schema_version"), default="op02_schema_missing"
            ),
            "op02_material_ref": _clean_ref(
                op02_map.get("material_id"), default="op02_material_missing"
            ),
            "op02_status_ref": _clean_ref(
                op02_map.get("dhd_op02_status_ref"), default="op02_status_missing"
            ),
            "dhc_outcome_class_ref": outcome_ref,
            "current_dhc_result_selected": bool(
                op02_contract_valid and op02_map.get("current_dhc_result_selected") is True
            ),
            "current_dhc_scan_clear_result_selected": bool(
                op02_contract_valid
                and op02_map.get("current_dhc_scan_clear_result_selected") is True
            ),
            "op03_material_present": op03_present,
            "op03_contract_valid": op03_contract_valid,
            "op03_schema_version_ref": _clean_ref(
                op03_map.get("schema_version"), default="op03_schema_missing"
            ),
            "op03_material_ref": _clean_ref(
                op03_map.get("material_id"), default="op03_material_missing"
            ),
            "op03_status_ref": op03_status_ref,
            "op04_material_present": op04_present,
            "op04_contract_valid": op04_contract_valid,
            "op04_schema_version_ref": _clean_ref(
                op04_map.get("schema_version"), default="op04_schema_missing"
            ),
            "op04_material_ref": _clean_ref(
                op04_map.get("material_id"), default="op04_material_missing"
            ),
            "op04_status_ref": op04_status_ref,
            "dhd_op05_status_ref": status_ref,
            "bodyfree_direction_comparator_status_ref": status_ref,
            "dhd_op05_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS,
            "dhd_op05_allowed_status_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS
            ),
            "direction_decision_ref": decision_ref,
            "direction_decision_refs": P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS,
            "direction_decision_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS
            ),
            "direction_comparison_axis_refs": P7_R54_AHR_POST_DHC_DHD_DIRECTION_COMPARISON_AXIS_REFS,
            "direction_comparison_axis_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_DIRECTION_COMPARISON_AXIS_REFS
            ),
            "dhr_op06_consideration_candidate": dhr_candidate,
            "dhr_op06_consideration_has_direct_branch_resolution_reason": direct_branch_reason,
            "p7_readfeel_reconnection_candidate": p7_candidate,
            "current_dhc_material_selection_required": current_material_selection_required,
            "repair_or_wait_boundary_required": repair_or_wait_required,
            "non_dhr_lane_route_preservation_required": non_dhr_route_required,
            "no_touch_repair_or_hold_required": no_touch_hold_required,
            "decision_reason_refs": reason_refs,
            "decision_reason_ref_count": len(reason_refs),
            "decision_blocker_refs": blocker_refs,
            "decision_blocker_ref_count": len(blocker_refs),
            "selected_next_design_candidate_ref": selected_candidate_ref,
            "selected_next_design_candidate_refs": P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS,
            "selected_next_design_candidate_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS
            ),
            "next_runtime_execution_allowed_here": False,
            "dhr_op06_builder_call_allowed_here": False,
            "dhr_op06_implicit_op05_fallback_allowed_here": False,
            "p7_readfeel_evaluation_execution_allowed_here": False,
            "op05_input_forbidden_payload_key_path_refs": forbidden_paths,
            "op05_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op05_input_body_like_value_path_refs": body_like_paths,
            "op05_input_body_like_value_path_count": len(body_like_paths),
            "op05_input_promotion_or_autorun_claim_path_refs": promotion_paths,
            "op05_input_promotion_or_autorun_claim_path_count": len(promotion_paths),
            "op05_input_no_touch_mutation_path_refs": no_touch_paths,
            "op05_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhd_op05_does_not_call_dhc_or_dhr_builder": True,
            "dhd_op05_does_not_use_dhr_op06_implicit_op05_fallback": True,
            "dhd_op05_does_not_execute_selected_direction": True,
            "dhd_op05_does_not_create_or_evaluate_readfeel_cases": True,
            "dhd_op05_does_not_start_p8": True,
            "dhd_op05_does_not_claim_p7_complete_or_release": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "fixed_non_promotion_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP05_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(
                P7_R54_AHR_POST_DHC_DHD_OP05_NOT_YET_IMPLEMENTED_STEPS
            ),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R4_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(
                P7_R54_AHR_POST_DHC_DHD_R4_COMPILEALL_TARGET_REF_REFS
            ),
            "optional_product_readfeel_regression_ref_refs": list(
                P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
            ),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "dhd_op02_implemented": True,
            "dhd_op03_implemented": True,
            "dhd_op04_implemented": True,
            "dhd_op05_implemented": True,
            "next_required_step": P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert the DHD-OP05 body-free next-design comparison contract."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FIELD_REFS, source="DHD-OP05"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP05 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP05_SCHEMA_VERSION:
        raise ValueError("DHD-OP05 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP05_STEP_REF:
        raise ValueError("DHD-OP05 step mismatch")
    _assert_r3_shared_contract(
        data,
        source="DHD-OP05",
        required_false_refs=P7_R54_AHR_POST_DHC_DHD_OP05_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "dhd_op05_does_not_call_dhc_or_dhr_builder",
        "dhd_op05_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op05_does_not_execute_selected_direction",
        "dhd_op05_does_not_create_or_evaluate_readfeel_cases",
        "dhd_op05_does_not_start_p8",
        "dhd_op05_does_not_claim_p7_complete_or_release",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP05 required true field changed: {key}")
    for key in (
        "next_runtime_execution_allowed_here",
        "dhr_op06_builder_call_allowed_here",
        "dhr_op06_builder_called_here",
        "dhr_op06_implicit_op05_fallback_allowed_here",
        "dhr_op06_implicit_op05_fallback_used_here",
        "p7_readfeel_evaluation_execution_allowed_here",
        "p7_readfeel_evaluation_started_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "p8_question_design_started",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHD-OP05 forbidden execution/promotion changed: {key}")
    if tuple(data.get("dhd_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP05 allowed status refs changed")
    if data.get("dhd_op05_allowed_status_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS
    ):
        raise ValueError("DHD-OP05 allowed status count changed")
    status_ref = data.get("dhd_op05_status_ref")
    decision_ref = data.get("direction_decision_ref")
    if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP05 status is not allowed")
    if decision_ref not in P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS:
        raise ValueError("DHD-OP05 direction decision is not allowed")
    if data.get("bodyfree_direction_comparator_status_ref") != status_ref:
        raise ValueError("DHD-OP05 status alias changed")
    if tuple(data.get("direction_decision_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS:
        raise ValueError("DHD-OP05 direction refs changed")
    if data.get("direction_decision_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS
    ):
        raise ValueError("DHD-OP05 direction ref count changed")
    decision_index = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS.index(decision_ref)
    if data.get("selected_next_design_candidate_ref") != P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[
        decision_index
    ]:
        raise ValueError("DHD-OP05 selected next-design candidate changed")
    if tuple(data.get("selected_next_design_candidate_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS:
        raise ValueError("DHD-OP05 selected candidate refs changed")
    if data.get("selected_next_design_candidate_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS
    ):
        raise ValueError("DHD-OP05 selected candidate ref count changed")
    if tuple(data.get("direction_comparison_axis_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_DIRECTION_COMPARISON_AXIS_REFS:
        raise ValueError("DHD-OP05 comparison axis refs changed")
    expected_flags = (
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[2],
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[3],
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[4],
        decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[5],
    )
    actual_flags = (
        data.get("current_dhc_material_selection_required") is True,
        data.get("repair_or_wait_boundary_required") is True,
        data.get("non_dhr_lane_route_preservation_required") is True,
        data.get("no_touch_repair_or_hold_required") is True,
    )
    if actual_flags != expected_flags:
        raise ValueError("DHD-OP05 decision branch flags changed")
    if decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[0]:
        if data.get("dhr_op06_consideration_candidate") is not True:
            raise ValueError("DHD-OP05 DHR design-first requires consideration candidate")
        if data.get("dhr_op06_consideration_has_direct_branch_resolution_reason") is not True:
            raise ValueError("DHD-OP05 DHR design-first requires direct branch reason")
        if data.get("current_dhc_scan_clear_result_selected") is not True:
            raise ValueError("DHD-OP05 DHR design-first requires current scan clear")
    if decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[1]:
        if data.get("p7_readfeel_reconnection_candidate") is not True:
            raise ValueError("DHD-OP05 P7 readfeel design-first requires candidate")
    if data.get("dhc_outcome_class_ref") in {
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[1],
        P7_R54_AHR_POST_DHC_DHD_DHC_OUTCOME_CLASSIFICATION_REFS[2],
    } and decision_ref == P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[0]:
        raise ValueError("DHD-OP05 R11/test-only must not select DHR consideration design-first")
    for field, count_field in (
        ("direction_comparison_axis_refs", "direction_comparison_axis_ref_count"),
        ("decision_reason_refs", "decision_reason_ref_count"),
        ("decision_blocker_refs", "decision_blocker_ref_count"),
        ("selected_next_design_candidate_refs", "selected_next_design_candidate_ref_count"),
        ("op05_input_forbidden_payload_key_path_refs", "op05_input_forbidden_payload_key_path_count"),
        ("op05_input_body_like_value_path_refs", "op05_input_body_like_value_path_count"),
        (
            "op05_input_promotion_or_autorun_claim_path_refs",
            "op05_input_promotion_or_autorun_claim_path_count",
        ),
        ("op05_input_no_touch_mutation_path_refs", "op05_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP05 count field changed: {count_field}")
    if tuple(data.get("optional_product_readfeel_regression_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS:
        raise ValueError("DHD-OP05 optional readfeel regression refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP05_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP05 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP05_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP05 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R4_TARGET_TEST_REF_REFS:
        raise ValueError("DHD-OP05 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R4_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHD-OP05 compileall refs changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF:
        raise ValueError("DHD-OP05 next step changed")
    return True


# ---------------------------------------------------------------------------
# R5: DHD-OP06 / DHD-OP07 only.
# OP06 guards a stopped direction decision against execution/promotion. OP07
# materializes a count-only validation plan and expected result-memo refs. It
# does not execute commands, claim green, or create result-memo files.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_R4_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op06_op07_20260709.py",
)
P7_R54_AHR_POST_DHC_DHD_R5_SELECTED_REGRESSION_TEST_REF_REFS: Final[
    tuple[str, ...]
] = (
    *P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_r0_r1_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op00_op01_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op02_op03_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op04_op05_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op06_op07_20260709.py",
    "tests/test_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_dhc_op08_result_20260709.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op00_op01_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op02_op03_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op04_op05_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op06_op07_20260708.py",
    "tests/test_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_dhb_op08_result_20260708.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_R4_COMPILEALL_TARGET_REF_REFS
)
P7_R54_AHR_POST_DHC_DHD_R5_RESULT_MEMO_EXPECTED_FILE_REFS: Final[
    tuple[str, ...]
] = (
    "mashos-api/ai/tests/R54_AHR_PostDHC_DirectionDecisionBoundary_DHD_R7_TargetValidation_Result_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHC_DirectionDecisionBoundary_DHD_R8_SelectedRegression_Result_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHC_DirectionDecisionBoundary_DHD_R9_Compileall_Result_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHC_DirectionDecisionBoundary_DHD_R10_ResultMemoClosure_20260709.md",
    "mashos-api/ai/tests/R54_AHR_PostDHC_DirectionDecisionBoundary_DHD_R11_NextWorkDecision_20260709.md",
)
P7_R54_AHR_POST_DHC_DHD_R5_NEXT_WORK_DECISION_MEMO_DRAFT_REFS: Final[
    tuple[str, ...]
] = P7_R54_AHR_POST_DHC_DHD_R5_RESULT_MEMO_EXPECTED_FILE_REFS[-2:]

P7_R54_AHR_POST_DHC_DHD_OP07_TARGET_VALIDATION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_r0_r1_20260709.py "
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op00_op01_20260709.py "
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op02_op03_20260709.py "
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op04_op05_20260709.py "
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op06_op07_20260709.py "
    "-p no:cacheprovider"
)
P7_R54_AHR_POST_DHC_DHD_OP07_SELECTED_REGRESSION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "<DHD R5 target tests plus selected adjacent DHC DHB and existing DHR tests> "
    "-p no:cacheprovider"
)
P7_R54_AHR_POST_DHC_DHD_OP07_OPTIONAL_PRODUCT_READFEEL_REGRESSION_COMMAND_REF: Final = (
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=services/ai_inference pytest -q --assert=plain "
    "tests/test_emlis_ai_p7_blind_qa_material_20260612.py "
    "tests/test_emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material_r10_r11_20260617.py "
    "tests/test_emlis_ai_complete_product_quality_scorecard_blind_qa.py "
    "-p no:cacheprovider"
)
P7_R54_AHR_POST_DHC_DHD_OP07_COMPILEALL_COMMAND_REF: Final = (
    "PYTHONPATH=services/ai_inference python -m compileall -q "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhc_direction_decision_boundary_20260709.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dhb_dhr_op05_manual_call_execution_consideration_20260709.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_pcm_dhr_op05_manual_handoff_boundary_20260708.py "
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py "
    "services/ai_inference/emlis_ai_p7_contracts.py"
)
P7_R54_AHR_POST_DHC_DHD_OP07_EXPECTED_VALIDATION_COMMAND_SUMMARY_REFS: Final[
    tuple[str, ...]
] = (
    "target_validation_command_is_reference_only_not_executed_here",
    "selected_regression_command_is_reference_only_not_executed_here",
    "optional_product_readfeel_regression_is_reference_only_not_actual_readfeel_evaluation",
    "compileall_command_is_reference_only_not_executed_here",
)

P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP06_GUARD_INPUTS_REF: Final = (
    "repair_DHD_OP06_no_touch_guard_inputs_before_validation_plan_or_direction_closure"
)
P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP06_GUARD_REF: Final = (
    "blocked_DHD_OP06_no_touch_no_promotion_no_question_system_guard_before_validation_plan"
)
P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP07_PLAN_INPUTS_REF: Final = (
    "repair_DHD_OP07_validation_plan_inputs_without_validation_execution_or_green_claim"
)
P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP07_PLAN_REF: Final = (
    "blocked_DHD_OP07_validation_plan_bodyfree_leak_promotion_or_green_claim"
)

P7_R54_AHR_POST_DHC_DHD_R5_VALIDATION_GREEN_CLAIM_FIELD_REFS: Final[
    tuple[str, ...]
] = (
    "validation_commands_executed_here",
    "target_validation_green_confirmed_here",
    "selected_regression_green_confirmed_here",
    "optional_product_readfeel_regression_green_confirmed_here",
    "compileall_green_confirmed_here",
    "full_backend_suite_green_confirmed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_confirmed",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
    "result_memo_files_created_here",
)
P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            "dhc_builder_called_here",
            "dhc_result_synthesized_here",
            "dhr_op05_runtime_call_started_here",
            "existing_dhr_op05_builder_runtime_called_here",
            "dhr_op06_builder_called_here",
            "dhr_op06_implicit_op05_fallback_used_here",
            "dhr_op07_materialized_here",
            "dmd_execution_started_here",
            "dmd_r52_executed_here",
            "r52_actual_execution_started_here",
            "actual_review_started_here",
            "actual_rows_created_here",
            "question_need_observation_rows_created_here",
            "p7_readfeel_actual_case_created_here",
            "p7_readfeel_actual_evaluation_started_here",
            "p7_readfeel_evaluation_started_here",
            "existing_p7_runner_executed_here",
            "p8_question_design_started",
            "p8_question_implementation_started",
            "question_text_materialized_here",
            "api_changed",
            "db_changed",
            "rn_changed",
            "runtime_changed",
            "response_key_changed",
            "api_db_rn_runtime_response_key_changed",
            "json_schema_file_created",
            "json_schema_file_created_here",
            "p7_complete",
            "release_allowed",
            *P7_R54_AHR_POST_DHC_DHD_R5_VALIDATION_GREEN_CLAIM_FIELD_REFS,
        )
    )
)

P7_R54_AHR_POST_DHC_DHD_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_OP05_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_OP06_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
        "dhd_op06_implemented",
    }
)
P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
        "dhd_op06_implemented",
        "dhd_op07_implemented",
    }
)

P7_R54_AHR_POST_DHC_DHD_OP06_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op05_material_present",
    "op05_contract_valid",
    "op05_schema_version_ref",
    "op05_material_ref",
    "op05_status_ref",
    "op05_direction_decision_ref",
    "op05_selected_next_design_candidate_ref",
    "op05_next_required_step_ref",
    "op06_guard_field_refs",
    "op06_guard_field_ref_count",
    "op06_input_forbidden_payload_key_path_refs",
    "op06_input_forbidden_payload_key_path_count",
    "op06_input_body_like_value_path_refs",
    "op06_input_body_like_value_path_count",
    "op06_input_guard_true_field_path_refs",
    "op06_input_guard_true_field_path_count",
    "op06_input_no_touch_mutation_path_refs",
    "op06_input_no_touch_mutation_path_count",
    "dhd_op06_status_ref",
    "bodyfree_no_touch_no_promotion_no_question_system_guard_status_ref",
    "dhd_op06_allowed_status_refs",
    "dhd_op06_allowed_status_ref_count",
    "dhd_op06_no_touch_no_promotion_no_question_system_guard_passed",
    "dhd_op06_repair_required_for_no_touch_guard_inputs",
    "dhd_op06_blocked_no_touch_no_promotion_no_question_system_guard",
    "dhd_op06_reason_refs",
    "dhd_op06_reason_ref_count",
    "dhd_op06_blocker_refs",
    "dhd_op06_blocker_ref_count",
    "dhd_op06_does_not_call_dhc_or_dhr_builder",
    "dhd_op06_does_not_use_dhr_op06_implicit_op05_fallback",
    "dhd_op06_does_not_execute_selected_direction",
    "dhd_op06_does_not_materialize_dhr_op07_or_execute_dmd_r52",
    "dhd_op06_does_not_start_actual_review_or_create_rows",
    "dhd_op06_does_not_create_question_need_observation_rows",
    "dhd_op06_does_not_start_p8_or_materialize_question_text",
    "dhd_op06_does_not_change_api_db_rn_runtime_response_key",
    "dhd_op06_does_not_create_json_schema_file",
    "dhd_op06_does_not_claim_validation_or_environment_green",
    "dhd_op06_does_not_claim_p7_complete_or_release",
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
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "dhd_op04_implemented",
    "dhd_op05_implemented",
    "dhd_op06_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP07_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op06_material_present",
    "op06_contract_valid",
    "op06_schema_version_ref",
    "op06_material_ref",
    "op06_status_ref",
    "op06_next_required_step_ref",
    "op06_guard_passed",
    "op06_repair_required",
    "op06_blocked",
    "op06_upstream_direction_decision_ref",
    "op06_upstream_selected_next_design_candidate_ref",
    "op07_input_forbidden_payload_key_path_refs",
    "op07_input_forbidden_payload_key_path_count",
    "op07_input_body_like_value_path_refs",
    "op07_input_body_like_value_path_count",
    "op07_input_guard_true_field_path_refs",
    "op07_input_guard_true_field_path_count",
    "op07_input_no_touch_mutation_path_refs",
    "op07_input_no_touch_mutation_path_count",
    "target_validation_command_refs",
    "target_validation_command_ref_count",
    "selected_regression_command_refs",
    "selected_regression_command_ref_count",
    "optional_product_readfeel_regression_command_refs",
    "optional_product_readfeel_regression_command_ref_count",
    "compileall_command_refs",
    "compileall_command_ref_count",
    "expected_validation_command_summary_refs",
    "expected_validation_command_summary_ref_count",
    "target_test_ref_refs",
    "target_test_ref_ref_count",
    "selected_regression_test_ref_refs",
    "selected_regression_test_ref_ref_count",
    "optional_product_readfeel_regression_ref_refs",
    "optional_product_readfeel_regression_ref_ref_count",
    "compileall_target_ref_refs",
    "compileall_target_ref_ref_count",
    "result_memo_expected_file_refs",
    "result_memo_expected_file_ref_count",
    "next_work_decision_memo_draft_refs",
    "next_work_decision_memo_draft_ref_count",
    "validation_commands_executed_here",
    "target_validation_green_confirmed_here",
    "selected_regression_green_confirmed_here",
    "optional_product_readfeel_regression_green_confirmed_here",
    "compileall_green_confirmed_here",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "raw_pytest_stdout_included",
    "raw_pytest_stderr_included",
    "raw_traceback_included",
    "raw_body_included",
    "comment_text_body_included",
    "question_text_body_included",
    "result_memo_policy_count_only_bodyfree",
    "validation_plan_is_not_validation_result",
    "validation_plan_does_not_claim_green",
    "result_memo_files_created_here",
    "dhd_op07_status_ref",
    "bodyfree_validation_plan_result_memo_draft_status_ref",
    "dhd_op07_allowed_status_refs",
    "dhd_op07_allowed_status_ref_count",
    "dhd_op07_validation_plan_result_memo_draft_materialized_stopped",
    "dhd_op07_repair_required_for_validation_plan_inputs",
    "dhd_op07_blocked_validation_plan_bodyfree_leak_promotion_or_green_claim",
    "dhd_op07_reason_refs",
    "dhd_op07_reason_ref_count",
    "dhd_op07_blocker_refs",
    "dhd_op07_blocker_ref_count",
    "dhd_op07_does_not_execute_validation_commands",
    "dhd_op07_does_not_claim_target_selected_compileall_or_optional_readfeel_green",
    "dhd_op07_keeps_full_backend_suite_unconfirmed",
    "dhd_op07_keeps_rn_contract_unconfirmed",
    "dhd_op07_keeps_rn_real_device_unconfirmed",
    "dhd_op07_does_not_create_result_memo_files",
    "dhd_op07_does_not_call_dhc_or_dhr_builder",
    "dhd_op07_does_not_execute_selected_direction",
    "dhd_op07_does_not_materialize_dhr_op07_or_execute_dmd_r52",
    "dhd_op07_does_not_start_actual_review_or_create_rows",
    "dhd_op07_does_not_create_question_need_observation_rows",
    "dhd_op07_does_not_start_p8_or_materialize_question_text",
    "dhd_op07_does_not_change_api_db_rn_runtime_response_key",
    "dhd_op07_does_not_create_json_schema_file",
    "dhd_op07_does_not_claim_p7_complete_or_release",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "public_contract",
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "dhd_op04_implemented",
    "dhd_op05_implemented",
    "dhd_op06_implemented",
    "dhd_op07_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP06_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FALSE_FLAG_REFS
    )
)
P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP07_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FALSE_FLAG_REFS
    )
)


def _op05_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhc_dhd_op05_direction_comparator_contract(data)
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def _scan_true_field_paths(
    value: Any, *, field_refs: Sequence[str], path: str
) -> list[str]:
    refs = set(field_refs)
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in refs and child is True:
                paths.append(child_path)
            paths.extend(
                _scan_true_field_paths(child, field_refs=field_refs, path=child_path)
            )
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(
                _scan_true_field_paths(
                    child, field_refs=field_refs, path=f"{path}[{index}]"
                )
            )
    return paths


def _op06_status(
    *, blocked: bool, op05_present: bool, op05_valid: bool
) -> tuple[str, list[str], list[str], str]:
    if blocked:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[2],
            ["DHD_OP06_no_touch_no_promotion_no_question_system_guard_blocked"],
            ["repair_bodyfree_leak_promotion_autorun_or_green_claim_before_validation_plan"],
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP06_GUARD_REF,
        )
    if not op05_present or not op05_valid:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[1],
            ["DHD_OP05_direction_comparator_missing_or_contract_invalid_before_guard"],
            ["repair_DHD_OP05_direction_material_before_no_touch_guard"],
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP06_GUARD_INPUTS_REF,
        )
    return (
        P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[0],
        ["DHD_OP06_no_touch_no_promotion_no_question_system_guard_passed_and_stopped"],
        [],
        P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
    )


def build_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard(
    op05_direction_comparator: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Guard a stopped DHD direction decision without executing or promoting it."""

    op05 = op05_direction_comparator
    op05_present = isinstance(op05, Mapping)
    op05_contract_valid = _op05_valid(op05)
    op05_map = op05 if op05_present else {}
    scan_root = {"op05_direction_comparator": op05 if op05_present else {}}
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(scan_root, path="dhd_op06_input")
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(scan_root, path="dhd_op06_input")
    )
    guard_true_paths = _dedupe_clean_refs(
        _scan_true_field_paths(
            scan_root,
            field_refs=P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS,
            path="dhd_op06_input",
        )
    )
    no_touch_paths = _dedupe_clean_refs(
        _scan_no_touch_mutation_paths(scan_root, path="dhd_op06_input")
    )
    blocked_input = bool(
        forbidden_paths or body_like_paths or guard_true_paths or no_touch_paths
    )
    status_ref, reasons, blockers, next_required_step = _op06_status(
        blocked=blocked_input,
        op05_present=op05_present,
        op05_valid=op05_contract_valid,
    )
    guard_passed = status_ref == P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[0]
    repair = status_ref == P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[1]
    blocked = status_ref == P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[2]
    reason_refs = _dedupe_clean_refs(reasons)
    blocker_refs = _dedupe_clean_refs(
        [*blockers, *forbidden_paths, *body_like_paths, *guard_true_paths, *no_touch_paths]
    )

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP06_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op05_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op05_material_present": op05_present,
            "op05_contract_valid": op05_contract_valid,
            "op05_schema_version_ref": _clean_ref(
                op05_map.get("schema_version"), default="op05_schema_missing"
            ),
            "op05_material_ref": _clean_ref(
                op05_map.get("material_id"), default="op05_material_missing"
            ),
            "op05_status_ref": _clean_ref(
                op05_map.get("dhd_op05_status_ref"), default="op05_status_missing"
            ),
            "op05_direction_decision_ref": _clean_ref(
                op05_map.get("direction_decision_ref"), default="op05_direction_decision_missing"
            ),
            "op05_selected_next_design_candidate_ref": _clean_ref(
                op05_map.get("selected_next_design_candidate_ref"),
                default="op05_selected_next_design_candidate_missing",
            ),
            "op05_next_required_step_ref": _clean_ref(
                op05_map.get("next_required_step"), default="op05_next_step_missing"
            ),
            "op06_guard_field_refs": P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS,
            "op06_guard_field_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS
            ),
            "op06_input_forbidden_payload_key_path_refs": forbidden_paths,
            "op06_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op06_input_body_like_value_path_refs": body_like_paths,
            "op06_input_body_like_value_path_count": len(body_like_paths),
            "op06_input_guard_true_field_path_refs": guard_true_paths,
            "op06_input_guard_true_field_path_count": len(guard_true_paths),
            "op06_input_no_touch_mutation_path_refs": no_touch_paths,
            "op06_input_no_touch_mutation_path_count": len(no_touch_paths),
            "dhd_op06_status_ref": status_ref,
            "bodyfree_no_touch_no_promotion_no_question_system_guard_status_ref": status_ref,
            "dhd_op06_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS,
            "dhd_op06_allowed_status_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS
            ),
            "dhd_op06_no_touch_no_promotion_no_question_system_guard_passed": guard_passed,
            "dhd_op06_repair_required_for_no_touch_guard_inputs": repair,
            "dhd_op06_blocked_no_touch_no_promotion_no_question_system_guard": blocked,
            "dhd_op06_reason_refs": reason_refs,
            "dhd_op06_reason_ref_count": len(reason_refs),
            "dhd_op06_blocker_refs": blocker_refs,
            "dhd_op06_blocker_ref_count": len(blocker_refs),
            "dhd_op06_does_not_call_dhc_or_dhr_builder": True,
            "dhd_op06_does_not_use_dhr_op06_implicit_op05_fallback": True,
            "dhd_op06_does_not_execute_selected_direction": True,
            "dhd_op06_does_not_materialize_dhr_op07_or_execute_dmd_r52": True,
            "dhd_op06_does_not_start_actual_review_or_create_rows": True,
            "dhd_op06_does_not_create_question_need_observation_rows": True,
            "dhd_op06_does_not_start_p8_or_materialize_question_text": True,
            "dhd_op06_does_not_change_api_db_rn_runtime_response_key": True,
            "dhd_op06_does_not_create_json_schema_file": True,
            "dhd_op06_does_not_claim_validation_or_environment_green": True,
            "dhd_op06_does_not_claim_p7_complete_or_release": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "fixed_non_promotion_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP06_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(
                P7_R54_AHR_POST_DHC_DHD_OP06_NOT_YET_IMPLEMENTED_STEPS
            ),
            "target_test_ref_refs": list(P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS),
            "compileall_target_ref_refs": list(
                P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS
            ),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "dhd_op02_implemented": True,
            "dhd_op03_implemented": True,
            "dhd_op04_implemented": True,
            "dhd_op05_implemented": True,
            "dhd_op06_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHD-OP06 no-touch/no-promotion/no-question-system guard."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FIELD_REFS, source="DHD-OP06"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP06 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP06_SCHEMA_VERSION:
        raise ValueError("DHD-OP06 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP06_STEP_REF:
        raise ValueError("DHD-OP06 step mismatch")
    _assert_r3_shared_contract(
        data,
        source="DHD-OP06",
        required_false_refs=P7_R54_AHR_POST_DHC_DHD_OP06_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "dhd_op06_does_not_call_dhc_or_dhr_builder",
        "dhd_op06_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op06_does_not_execute_selected_direction",
        "dhd_op06_does_not_materialize_dhr_op07_or_execute_dmd_r52",
        "dhd_op06_does_not_start_actual_review_or_create_rows",
        "dhd_op06_does_not_create_question_need_observation_rows",
        "dhd_op06_does_not_start_p8_or_materialize_question_text",
        "dhd_op06_does_not_change_api_db_rn_runtime_response_key",
        "dhd_op06_does_not_create_json_schema_file",
        "dhd_op06_does_not_claim_validation_or_environment_green",
        "dhd_op06_does_not_claim_p7_complete_or_release",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
        "dhd_op06_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP06 required true field changed: {key}")
    for key in P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS:
        if key in data and data.get(key) is not False:
            raise ValueError(f"DHD-OP06 guarded output field changed: {key}")
    if tuple(data.get("op06_guard_field_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS:
        raise ValueError("DHD-OP06 guard field refs changed")
    if data.get("op06_guard_field_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS
    ):
        raise ValueError("DHD-OP06 guard field ref count changed")
    if tuple(data.get("dhd_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP06 allowed status refs changed")
    if data.get("dhd_op06_allowed_status_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS
    ):
        raise ValueError("DHD-OP06 allowed status count changed")
    status_ref = data.get("dhd_op06_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP06 status is not allowed")
    if data.get("op05_contract_valid") is True:
        carried_decision_ref = data.get("op05_direction_decision_ref")
        if carried_decision_ref not in P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS:
            raise ValueError("DHD-OP06 carried direction decision is not allowed")
        carried_decision_index = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS.index(
            carried_decision_ref
        )
        if data.get("op05_selected_next_design_candidate_ref") != (
            P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[carried_decision_index]
        ):
            raise ValueError("DHD-OP06 carried direction/candidate pair changed")
    if data.get("bodyfree_no_touch_no_promotion_no_question_system_guard_status_ref") != status_ref:
        raise ValueError("DHD-OP06 status alias changed")
    branch_flags = (
        data.get("dhd_op06_no_touch_no_promotion_no_question_system_guard_passed") is True,
        data.get("dhd_op06_repair_required_for_no_touch_guard_inputs") is True,
        data.get("dhd_op06_blocked_no_touch_no_promotion_no_question_system_guard") is True,
    )
    if sum(branch_flags) != 1:
        raise ValueError("DHD-OP06 must select exactly one guard branch")
    if status_ref == P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[0]:
        if data.get("op05_contract_valid") is not True:
            raise ValueError("DHD-OP06 passed branch requires valid OP05")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF:
            raise ValueError("DHD-OP06 passed next step changed")
        if any(
            data.get(field)
            for field in (
                "op06_input_forbidden_payload_key_path_refs",
                "op06_input_body_like_value_path_refs",
                "op06_input_guard_true_field_path_refs",
                "op06_input_no_touch_mutation_path_refs",
            )
        ):
            raise ValueError("DHD-OP06 passed branch cannot retain guard violations")
    elif status_ref == P7_R54_AHR_POST_DHC_DHD_OP06_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP06_GUARD_INPUTS_REF:
            raise ValueError("DHD-OP06 repair next step changed")
    else:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP06_GUARD_REF:
            raise ValueError("DHD-OP06 blocked next step changed")
        if not any(
            data.get(field)
            for field in (
                "op06_input_forbidden_payload_key_path_refs",
                "op06_input_body_like_value_path_refs",
                "op06_input_guard_true_field_path_refs",
                "op06_input_no_touch_mutation_path_refs",
            )
        ):
            raise ValueError("DHD-OP06 blocked branch requires a recorded violation path")
    for field, count_field in (
        ("op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count"),
        ("op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count"),
        ("op06_input_guard_true_field_path_refs", "op06_input_guard_true_field_path_count"),
        ("op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count"),
        ("dhd_op06_reason_refs", "dhd_op06_reason_ref_count"),
        ("dhd_op06_blocker_refs", "dhd_op06_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP06 count field changed: {count_field}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP06_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP06 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP06_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP06 not-yet steps changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS:
        raise ValueError("DHD-OP06 target refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("DHD-OP06 compileall refs changed")
    return True


def _op06_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhc_dhd_op06_no_touch_no_promotion_no_question_system_guard_contract(
            data
        )
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def _op07_status(
    *, blocked: bool, op06_present: bool, op06_valid: bool, op06_guard_passed: bool
) -> tuple[str, list[str], list[str], str]:
    if blocked:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[2],
            ["DHD_OP07_validation_plan_bodyfree_or_green_claim_guard_blocked"],
            ["repair_validation_plan_bodyfree_leak_promotion_or_green_claim"],
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP07_PLAN_REF,
        )
    if not op06_present or not op06_valid or not op06_guard_passed:
        return (
            P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[1],
            ["DHD_OP06_guard_missing_repair_or_blocked_before_validation_plan_draft"],
            ["repair_DHD_OP06_guard_before_materializing_validation_plan"],
            P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP07_PLAN_INPUTS_REF,
        )
    return (
        P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[0],
        ["DHD_OP07_validation_plan_result_memo_draft_materialized_count_only_without_execution"],
        [],
        P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
    )


def build_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material(
    op06_no_touch_no_promotion_no_question_system_guard: Mapping[str, Any] | None = None,
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Materialize count-only validation-plan refs without executing validation."""

    op06 = op06_no_touch_no_promotion_no_question_system_guard
    op06_present = isinstance(op06, Mapping)
    op06_contract_valid = _op06_valid(op06)
    op06_map = op06 if op06_present else {}
    op06_status_ref = _clean_ref(
        op06_map.get("dhd_op06_status_ref"), default="op06_status_missing"
    )
    op06_guard_passed = bool(
        op06_contract_valid
        and op06_map.get("dhd_op06_no_touch_no_promotion_no_question_system_guard_passed")
        is True
    )
    scan_root = {
        "op06_no_touch_no_promotion_no_question_system_guard": (
            op06 if op06_present else {}
        )
    }
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(scan_root, path="dhd_op07_input")
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(scan_root, path="dhd_op07_input")
    )
    guard_true_paths = _dedupe_clean_refs(
        _scan_true_field_paths(
            scan_root,
            field_refs=P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS,
            path="dhd_op07_input",
        )
    )
    no_touch_paths = _dedupe_clean_refs(
        _scan_no_touch_mutation_paths(scan_root, path="dhd_op07_input")
    )
    blocked_input = bool(
        forbidden_paths or body_like_paths or guard_true_paths or no_touch_paths
    )
    status_ref, reasons, blockers, next_required_step = _op07_status(
        blocked=blocked_input,
        op06_present=op06_present,
        op06_valid=op06_contract_valid,
        op06_guard_passed=op06_guard_passed,
    )
    materialized = status_ref == P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[0]
    repair = status_ref == P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[1]
    blocked = status_ref == P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[2]
    reason_refs = _dedupe_clean_refs(reasons)
    blocker_refs = _dedupe_clean_refs(
        [*blockers, *forbidden_paths, *body_like_paths, *guard_true_paths, *no_touch_paths]
    )

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP07_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op06_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op06_material_present": op06_present,
            "op06_contract_valid": op06_contract_valid,
            "op06_schema_version_ref": _clean_ref(
                op06_map.get("schema_version"), default="op06_schema_missing"
            ),
            "op06_material_ref": _clean_ref(
                op06_map.get("material_id"), default="op06_material_missing"
            ),
            "op06_status_ref": op06_status_ref,
            "op06_next_required_step_ref": _clean_ref(
                op06_map.get("next_required_step"), default="op06_next_step_missing"
            ),
            "op06_guard_passed": op06_guard_passed,
            "op06_repair_required": bool(
                op06_contract_valid
                and op06_map.get("dhd_op06_repair_required_for_no_touch_guard_inputs")
                is True
            ),
            "op06_blocked": bool(
                op06_contract_valid
                and op06_map.get(
                    "dhd_op06_blocked_no_touch_no_promotion_no_question_system_guard"
                )
                is True
            ),
            "op06_upstream_direction_decision_ref": _clean_ref(
                op06_map.get("op05_direction_decision_ref"),
                default="op05_direction_decision_missing",
            ),
            "op06_upstream_selected_next_design_candidate_ref": _clean_ref(
                op06_map.get("op05_selected_next_design_candidate_ref"),
                default="op05_selected_next_design_candidate_missing",
            ),
            "op07_input_forbidden_payload_key_path_refs": forbidden_paths,
            "op07_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op07_input_body_like_value_path_refs": body_like_paths,
            "op07_input_body_like_value_path_count": len(body_like_paths),
            "op07_input_guard_true_field_path_refs": guard_true_paths,
            "op07_input_guard_true_field_path_count": len(guard_true_paths),
            "op07_input_no_touch_mutation_path_refs": no_touch_paths,
            "op07_input_no_touch_mutation_path_count": len(no_touch_paths),
            "target_validation_command_refs": (
                P7_R54_AHR_POST_DHC_DHD_OP07_TARGET_VALIDATION_COMMAND_REF,
            ),
            "target_validation_command_ref_count": 1,
            "selected_regression_command_refs": (
                P7_R54_AHR_POST_DHC_DHD_OP07_SELECTED_REGRESSION_COMMAND_REF,
            ),
            "selected_regression_command_ref_count": 1,
            "optional_product_readfeel_regression_command_refs": (
                P7_R54_AHR_POST_DHC_DHD_OP07_OPTIONAL_PRODUCT_READFEEL_REGRESSION_COMMAND_REF,
            ),
            "optional_product_readfeel_regression_command_ref_count": 1,
            "compileall_command_refs": (
                P7_R54_AHR_POST_DHC_DHD_OP07_COMPILEALL_COMMAND_REF,
            ),
            "compileall_command_ref_count": 1,
            "expected_validation_command_summary_refs": P7_R54_AHR_POST_DHC_DHD_OP07_EXPECTED_VALIDATION_COMMAND_SUMMARY_REFS,
            "expected_validation_command_summary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP07_EXPECTED_VALIDATION_COMMAND_SUMMARY_REFS
            ),
            "target_test_ref_refs": P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS,
            "target_test_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS
            ),
            "selected_regression_test_ref_refs": P7_R54_AHR_POST_DHC_DHD_R5_SELECTED_REGRESSION_TEST_REF_REFS,
            "selected_regression_test_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R5_SELECTED_REGRESSION_TEST_REF_REFS
            ),
            "optional_product_readfeel_regression_ref_refs": P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS,
            "optional_product_readfeel_regression_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
            ),
            "compileall_target_ref_refs": P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS,
            "compileall_target_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS
            ),
            "result_memo_expected_file_refs": P7_R54_AHR_POST_DHC_DHD_R5_RESULT_MEMO_EXPECTED_FILE_REFS,
            "result_memo_expected_file_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R5_RESULT_MEMO_EXPECTED_FILE_REFS
            ),
            "next_work_decision_memo_draft_refs": P7_R54_AHR_POST_DHC_DHD_R5_NEXT_WORK_DECISION_MEMO_DRAFT_REFS,
            "next_work_decision_memo_draft_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R5_NEXT_WORK_DECISION_MEMO_DRAFT_REFS
            ),
            "validation_commands_executed_here": False,
            "target_validation_green_confirmed_here": False,
            "selected_regression_green_confirmed_here": False,
            "optional_product_readfeel_regression_green_confirmed_here": False,
            "compileall_green_confirmed_here": False,
            "full_backend_suite_green_confirmed": False,
            "rn_contract_green_confirmed": False,
            "raw_pytest_stdout_included": False,
            "raw_pytest_stderr_included": False,
            "raw_traceback_included": False,
            "raw_body_included": False,
            "comment_text_body_included": False,
            "question_text_body_included": False,
            "result_memo_policy_count_only_bodyfree": True,
            "validation_plan_is_not_validation_result": True,
            "validation_plan_does_not_claim_green": True,
            "result_memo_files_created_here": False,
            "dhd_op07_status_ref": status_ref,
            "bodyfree_validation_plan_result_memo_draft_status_ref": status_ref,
            "dhd_op07_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS,
            "dhd_op07_allowed_status_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS
            ),
            "dhd_op07_validation_plan_result_memo_draft_materialized_stopped": materialized,
            "dhd_op07_repair_required_for_validation_plan_inputs": repair,
            "dhd_op07_blocked_validation_plan_bodyfree_leak_promotion_or_green_claim": blocked,
            "dhd_op07_reason_refs": reason_refs,
            "dhd_op07_reason_ref_count": len(reason_refs),
            "dhd_op07_blocker_refs": blocker_refs,
            "dhd_op07_blocker_ref_count": len(blocker_refs),
            "dhd_op07_does_not_execute_validation_commands": True,
            "dhd_op07_does_not_claim_target_selected_compileall_or_optional_readfeel_green": True,
            "dhd_op07_keeps_full_backend_suite_unconfirmed": True,
            "dhd_op07_keeps_rn_contract_unconfirmed": True,
            "dhd_op07_keeps_rn_real_device_unconfirmed": True,
            "dhd_op07_does_not_create_result_memo_files": True,
            "dhd_op07_does_not_call_dhc_or_dhr_builder": True,
            "dhd_op07_does_not_execute_selected_direction": True,
            "dhd_op07_does_not_materialize_dhr_op07_or_execute_dmd_r52": True,
            "dhd_op07_does_not_start_actual_review_or_create_rows": True,
            "dhd_op07_does_not_create_question_need_observation_rows": True,
            "dhd_op07_does_not_start_p8_or_materialize_question_text": True,
            "dhd_op07_does_not_change_api_db_rn_runtime_response_key": True,
            "dhd_op07_does_not_create_json_schema_file": True,
            "dhd_op07_does_not_claim_p7_complete_or_release": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "fixed_non_promotion_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP07_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(
                P7_R54_AHR_POST_DHC_DHD_OP07_NOT_YET_IMPLEMENTED_STEPS
            ),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "dhd_op02_implemented": True,
            "dhd_op03_implemented": True,
            "dhd_op04_implemented": True,
            "dhd_op05_implemented": True,
            "dhd_op06_implemented": True,
            "dhd_op07_implemented": True,
            "next_required_step": next_required_step,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHD-OP07 count-only validation-plan/result-memo draft material."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FIELD_REFS, source="DHD-OP07"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP07 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP07_SCHEMA_VERSION:
        raise ValueError("DHD-OP07 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP07_STEP_REF:
        raise ValueError("DHD-OP07 step mismatch")
    _assert_r3_shared_contract(
        data,
        source="DHD-OP07",
        required_false_refs=P7_R54_AHR_POST_DHC_DHD_OP07_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "result_memo_policy_count_only_bodyfree",
        "validation_plan_is_not_validation_result",
        "validation_plan_does_not_claim_green",
        "dhd_op07_does_not_execute_validation_commands",
        "dhd_op07_does_not_claim_target_selected_compileall_or_optional_readfeel_green",
        "dhd_op07_keeps_full_backend_suite_unconfirmed",
        "dhd_op07_keeps_rn_contract_unconfirmed",
        "dhd_op07_keeps_rn_real_device_unconfirmed",
        "dhd_op07_does_not_create_result_memo_files",
        "dhd_op07_does_not_call_dhc_or_dhr_builder",
        "dhd_op07_does_not_execute_selected_direction",
        "dhd_op07_does_not_materialize_dhr_op07_or_execute_dmd_r52",
        "dhd_op07_does_not_start_actual_review_or_create_rows",
        "dhd_op07_does_not_create_question_need_observation_rows",
        "dhd_op07_does_not_start_p8_or_materialize_question_text",
        "dhd_op07_does_not_change_api_db_rn_runtime_response_key",
        "dhd_op07_does_not_create_json_schema_file",
        "dhd_op07_does_not_claim_p7_complete_or_release",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
        "dhd_op06_implemented",
        "dhd_op07_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP07 required true field changed: {key}")
    for key in (
        "validation_commands_executed_here",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "optional_product_readfeel_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
        "full_backend_suite_green_claimed_here",
        "rn_contract_green_claimed_here",
        "result_memo_files_created_here",
        "raw_pytest_stdout_included",
        "raw_pytest_stderr_included",
        "raw_traceback_included",
        "raw_body_included",
        "comment_text_body_included",
        "question_text_body_included",
        "dhr_op06_builder_called_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "actual_review_started_here",
        "question_need_observation_rows_created_here",
        "p8_question_design_started",
        "question_text_materialized_here",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHD-OP07 forbidden result/execution claim changed: {key}")
    if tuple(data.get("dhd_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP07 allowed status refs changed")
    if data.get("dhd_op07_allowed_status_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS
    ):
        raise ValueError("DHD-OP07 allowed status count changed")
    status_ref = data.get("dhd_op07_status_ref")
    if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP07 status is not allowed")
    if data.get("op06_guard_passed") is True:
        carried_decision_ref = data.get("op06_upstream_direction_decision_ref")
        if carried_decision_ref not in P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS:
            raise ValueError("DHD-OP07 carried direction decision is not allowed")
        carried_decision_index = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS.index(
            carried_decision_ref
        )
        if data.get("op06_upstream_selected_next_design_candidate_ref") != (
            P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[carried_decision_index]
        ):
            raise ValueError("DHD-OP07 carried direction/candidate pair changed")
    if data.get("bodyfree_validation_plan_result_memo_draft_status_ref") != status_ref:
        raise ValueError("DHD-OP07 status alias changed")
    branch_flags = (
        data.get("dhd_op07_validation_plan_result_memo_draft_materialized_stopped") is True,
        data.get("dhd_op07_repair_required_for_validation_plan_inputs") is True,
        data.get("dhd_op07_blocked_validation_plan_bodyfree_leak_promotion_or_green_claim")
        is True,
    )
    if sum(branch_flags) != 1:
        raise ValueError("DHD-OP07 must select exactly one plan branch")
    if status_ref == P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[0]:
        if data.get("op06_contract_valid") is not True or data.get("op06_guard_passed") is not True:
            raise ValueError("DHD-OP07 materialized branch requires passed OP06 guard")
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF:
            raise ValueError("DHD-OP07 materialized next step changed")
    elif status_ref == P7_R54_AHR_POST_DHC_DHD_OP07_ALLOWED_STATUS_REFS[1]:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_REPAIR_OP07_PLAN_INPUTS_REF:
            raise ValueError("DHD-OP07 repair next step changed")
    else:
        if data.get("next_required_step") != P7_R54_AHR_POST_DHC_DHD_NEXT_STEP_BLOCKED_OP07_PLAN_REF:
            raise ValueError("DHD-OP07 blocked next step changed")
        if not any(
            data.get(field)
            for field in (
                "op07_input_forbidden_payload_key_path_refs",
                "op07_input_body_like_value_path_refs",
                "op07_input_guard_true_field_path_refs",
                "op07_input_no_touch_mutation_path_refs",
            )
        ):
            raise ValueError("DHD-OP07 blocked branch requires a recorded violation path")
    exact_ref_fields = (
        ("target_test_ref_refs", P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS),
        (
            "selected_regression_test_ref_refs",
            P7_R54_AHR_POST_DHC_DHD_R5_SELECTED_REGRESSION_TEST_REF_REFS,
        ),
        (
            "optional_product_readfeel_regression_ref_refs",
            P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS,
        ),
        ("compileall_target_ref_refs", P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS),
        (
            "result_memo_expected_file_refs",
            P7_R54_AHR_POST_DHC_DHD_R5_RESULT_MEMO_EXPECTED_FILE_REFS,
        ),
        (
            "next_work_decision_memo_draft_refs",
            P7_R54_AHR_POST_DHC_DHD_R5_NEXT_WORK_DECISION_MEMO_DRAFT_REFS,
        ),
        (
            "expected_validation_command_summary_refs",
            P7_R54_AHR_POST_DHC_DHD_OP07_EXPECTED_VALIDATION_COMMAND_SUMMARY_REFS,
        ),
    )
    for field, expected in exact_ref_fields:
        if tuple(data.get(field) or ()) != tuple(expected):
            raise ValueError(f"DHD-OP07 exact ref field changed: {field}")
    for field, count_field in (
        ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"),
        ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"),
        ("op07_input_guard_true_field_path_refs", "op07_input_guard_true_field_path_count"),
        ("op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count"),
        ("target_validation_command_refs", "target_validation_command_ref_count"),
        ("selected_regression_command_refs", "selected_regression_command_ref_count"),
        (
            "optional_product_readfeel_regression_command_refs",
            "optional_product_readfeel_regression_command_ref_count",
        ),
        ("compileall_command_refs", "compileall_command_ref_count"),
        (
            "expected_validation_command_summary_refs",
            "expected_validation_command_summary_ref_count",
        ),
        ("target_test_ref_refs", "target_test_ref_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count"),
        (
            "optional_product_readfeel_regression_ref_refs",
            "optional_product_readfeel_regression_ref_ref_count",
        ),
        ("compileall_target_ref_refs", "compileall_target_ref_ref_count"),
        ("result_memo_expected_file_refs", "result_memo_expected_file_ref_count"),
        ("next_work_decision_memo_draft_refs", "next_work_decision_memo_draft_ref_count"),
        ("dhd_op07_reason_refs", "dhd_op07_reason_ref_count"),
        ("dhd_op07_blocker_refs", "dhd_op07_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP07 count field changed: {count_field}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP07_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP07 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP07_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP07 not-yet steps changed")
    return True


# ---------------------------------------------------------------------------
# R6: DHD-OP08 stopped next-design decision closure only.
# OP08 preserves the selected body-free design direction and closes stopped.
# It does not execute that direction, run validation, create result memos, or
# promote DHD to P8, P7 completion, or release readiness.
# ---------------------------------------------------------------------------

P7_R54_AHR_POST_DHC_DHD_R6_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS,
    "tests/test_r54_ahr_post_dhc_direction_decision_boundary_dhd_op08_result_20260709.py",
)
P7_R54_AHR_POST_DHC_DHD_R6_SELECTED_REGRESSION_TEST_REF_REFS: Final[
    tuple[str, ...]
] = (
    *P7_R54_AHR_POST_DHC_DHD_R6_TARGET_TEST_REF_REFS,
    *P7_R54_AHR_POST_DHC_DHD_R5_SELECTED_REGRESSION_TEST_REF_REFS[
        len(P7_R54_AHR_POST_DHC_DHD_R5_TARGET_TEST_REF_REFS) :
    ],
)
P7_R54_AHR_POST_DHC_DHD_R6_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_DHC_DHD_R5_COMPILEALL_TARGET_REF_REFS
)
P7_R54_AHR_POST_DHC_DHD_R6_RESULT_MEMO_EXPECTED_FILE_REFS: Final[
    tuple[str, ...]
] = P7_R54_AHR_POST_DHC_DHD_R5_RESULT_MEMO_EXPECTED_FILE_REFS
P7_R54_AHR_POST_DHC_DHD_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_POST_DHC_DHD_OP07_IMPLEMENTED_STEPS,
    P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
)
P7_R54_AHR_POST_DHC_DHD_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    key
    for key in P7_R54_AHR_POST_DHC_DHD_REQUIRED_FALSE_FLAG_REFS
    if key
    not in {
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
        "dhd_op06_implemented",
        "dhd_op07_implemented",
        "dhd_op08_implemented",
    }
)

P7_R54_AHR_POST_DHC_DHD_OP08_BASE_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "op07_material_present",
    "op07_contract_valid",
    "op07_schema_version_ref",
    "op07_material_ref",
    "op07_status_ref",
    "op07_validation_plan_materialized_stopped",
    "op07_validation_plan_is_not_validation_result",
    "op07_validation_plan_does_not_claim_green",
    "op07_validation_commands_executed_here",
    "op07_result_memo_files_created_here",
    "op07_carried_direction_decision_ref",
    "op07_carried_selected_next_design_candidate_ref",
    "optional_op05_material_supplied",
    "optional_op05_material_present",
    "optional_op05_contract_valid",
    "optional_op05_schema_version_ref",
    "optional_op05_material_ref",
    "optional_op05_status_ref",
    "optional_op05_direction_decision_ref",
    "optional_op05_selected_next_design_candidate_ref",
    "optional_op05_consistency_required",
    "optional_op05_consistency_satisfied",
    "optional_op05_matches_op07",
    "op08_input_forbidden_payload_key_path_refs",
    "op08_input_forbidden_payload_key_path_count",
    "op08_input_body_like_value_path_refs",
    "op08_input_body_like_value_path_count",
    "op08_input_guard_true_field_path_refs",
    "op08_input_guard_true_field_path_count",
    "op08_input_no_touch_mutation_path_refs",
    "op08_input_no_touch_mutation_path_count",
    "op08_input_repair_or_blocked",
    "op08_upstream_no_touch_decision_preserved",
    "dhd_op08_status_ref",
    "bodyfree_stopped_next_design_decision_closure_status_ref",
    "dhd_op08_allowed_status_refs",
    "dhd_op08_allowed_status_ref_count",
    "direction_decision_ref",
    "direction_decision_refs",
    "direction_decision_ref_count",
    "selected_next_design_candidate_ref",
    "selected_next_design_candidate_refs",
    "selected_next_design_candidate_ref_count",
    "dhd_op08_dhr_op06_consideration_design_closed_stopped",
    "dhd_op08_p7_readfeel_reconnection_design_closed_stopped",
    "dhd_op08_explicit_current_dhc_material_selection_required_closed_stopped",
    "dhd_op08_repair_or_wait_boundary_closed_stopped",
    "dhd_op08_non_dhr_lane_route_preserved_closed_stopped",
    "dhd_op08_blocked_no_touch_no_promotion",
    "dhd_op08_closed_stopped",
    "current_execution_allowance_ref",
    "next_runtime_execution_allowed_here",
    "target_test_ref_refs",
    "target_test_ref_ref_count",
    "selected_regression_test_ref_refs",
    "selected_regression_test_ref_ref_count",
    "optional_product_readfeel_regression_ref_refs",
    "optional_product_readfeel_regression_ref_ref_count",
    "compileall_target_ref_refs",
    "compileall_target_ref_ref_count",
    "result_memo_expected_file_refs",
    "result_memo_expected_file_ref_count",
    "validation_commands_executed_here",
    "target_validation_green_confirmed_here",
    "selected_regression_green_confirmed_here",
    "optional_product_readfeel_regression_green_confirmed_here",
    "compileall_green_confirmed_here",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "raw_pytest_stdout_included",
    "raw_pytest_stderr_included",
    "raw_traceback_included",
    "raw_body_included",
    "comment_text_body_included",
    "question_text_body_included",
    "closure_is_not_validation_result",
    "closure_does_not_claim_green",
    "result_memo_files_created_here",
    "dhd_op08_reason_refs",
    "dhd_op08_reason_ref_count",
    "dhd_op08_blocker_refs",
    "dhd_op08_blocker_ref_count",
    "dhd_op08_does_not_call_dhc_or_dhr_builder",
    "dhd_op08_does_not_use_dhr_op06_implicit_op05_fallback",
    "dhd_op08_does_not_execute_selected_direction",
    "dhd_op08_does_not_materialize_dhr_op07_or_execute_dmd_r52",
    "dhd_op08_does_not_start_actual_review_or_create_rows",
    "dhd_op08_does_not_create_question_need_observation_rows",
    "dhd_op08_does_not_start_p8_or_materialize_question_text",
    "dhd_op08_does_not_change_api_db_rn_runtime_response_key",
    "dhd_op08_does_not_create_json_schema_file",
    "dhd_op08_does_not_create_result_memo_files",
    "dhd_op08_does_not_claim_validation_or_environment_green",
    "dhd_op08_does_not_claim_p7_complete_or_release",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "not_claimed_boundary_refs",
    "not_claimed_boundary_ref_count",
    "not_claimed_boundary",
    "fixed_non_promotion_refs",
    "fixed_non_promotion_ref_count",
    "implemented_steps",
    "not_yet_implemented_steps",
    "public_contract",
    "dhd_no_touch_contract",
    "body_free_markers",
    "dhd_op00_implemented",
    "dhd_op01_implemented",
    "dhd_op02_implemented",
    "dhd_op03_implemented",
    "dhd_op04_implemented",
    "dhd_op05_implemented",
    "dhd_op06_implemented",
    "dhd_op07_implemented",
    "dhd_op08_implemented",
    "next_required_step",
    "body_free",
)
P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        P7_R54_AHR_POST_DHC_DHD_OP08_BASE_FIELD_REFS
        + P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FALSE_FLAG_REFS
    )
)


def _op07_valid(data: Any) -> bool:
    if not isinstance(data, Mapping):
        return False
    try:
        assert_p7_r54_ahr_post_dhc_dhd_op07_validation_plan_result_memo_draft_material_contract(
            data
        )
    except (AssertionError, TypeError, ValueError):
        return False
    return True


def build_p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure(
    op07_validation_plan_result_memo_draft_material: Mapping[str, Any] | None = None,
    *,
    optional_op05_direction_comparator: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Close a DHD next-design decision as stopped without executing it."""

    op07 = op07_validation_plan_result_memo_draft_material
    op05 = optional_op05_direction_comparator
    op07_present = isinstance(op07, Mapping)
    op05_supplied = op05 is not None
    op05_present = isinstance(op05, Mapping)
    op07_contract_valid = _op07_valid(op07)
    op05_contract_valid = _op05_valid(op05)
    op07_map = op07 if op07_present else {}
    op05_map = op05 if op05_present else {}
    op07_status_ref = _clean_ref(
        op07_map.get("dhd_op07_status_ref"), default="op07_status_missing"
    )
    op07_materialized = bool(
        op07_contract_valid
        and op07_map.get("dhd_op07_validation_plan_result_memo_draft_materialized_stopped")
        is True
    )
    op07_decision_ref = _clean_ref(
        op07_map.get("op06_upstream_direction_decision_ref"),
        default="op07_carried_direction_decision_missing",
    )
    op07_candidate_ref = _clean_ref(
        op07_map.get("op06_upstream_selected_next_design_candidate_ref"),
        default="op07_carried_selected_candidate_missing",
    )
    op05_decision_ref = _clean_ref(
        op05_map.get("direction_decision_ref"),
        default="optional_op05_direction_decision_missing",
    )
    op05_candidate_ref = _clean_ref(
        op05_map.get("selected_next_design_candidate_ref"),
        default="optional_op05_selected_candidate_missing",
    )
    op05_matches_op07 = bool(
        op05_supplied
        and op05_contract_valid
        and op05_decision_ref == op07_decision_ref
        and op05_candidate_ref == op07_candidate_ref
    )
    op05_consistency_satisfied = bool(not op05_supplied or op05_matches_op07)
    scan_root = {
        "op07_validation_plan_result_memo_draft_material": (
            op07 if op07_present else {}
        ),
        "optional_op05_direction_comparator": op05 if op05_present else {},
    }
    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(scan_root, path="dhd_op08_input")
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(scan_root, path="dhd_op08_input")
    )
    guard_true_paths = _dedupe_clean_refs(
        _scan_true_field_paths(
            scan_root,
            field_refs=P7_R54_AHR_POST_DHC_DHD_OP06_GUARD_TRUE_FIELD_REFS,
            path="dhd_op08_input",
        )
    )
    no_touch_paths = _dedupe_clean_refs(
        _scan_no_touch_mutation_paths(scan_root, path="dhd_op08_input")
    )
    safe_pair = False
    decision_index = 5
    if (
        op07_contract_valid
        and op07_materialized
        and op07_decision_ref in P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS
    ):
        candidate_index = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS.index(
            op07_decision_ref
        )
        safe_pair = bool(
            op07_candidate_ref
            == P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[candidate_index]
        )
        if safe_pair:
            decision_index = candidate_index
    input_repair_or_blocked = bool(
        not op07_contract_valid
        or not op07_materialized
        or not safe_pair
        or not op05_consistency_satisfied
        or forbidden_paths
        or body_like_paths
        or guard_true_paths
        or no_touch_paths
    )
    reasons: list[str] = []
    blockers: list[str] = []
    if input_repair_or_blocked:
        decision_index = 5
        reasons.append("DHD_OP08_invalid_or_unsafe_closure_input_closed_as_no_touch_hold")
        if not op07_contract_valid or not op07_materialized:
            blockers.append("valid_materialized_DHD_OP07_plan_required_before_closure")
        if op07_contract_valid and op07_materialized and not safe_pair:
            blockers.append("repair_OP07_direction_decision_and_candidate_pair_before_closure")
        if op05_supplied and not op05_consistency_satisfied:
            blockers.append("repair_optional_OP05_and_OP07_direction_consistency_before_closure")
    else:
        reasons.append(
            (
                "DHD_OP08_DHR_OP06_consideration_design_closed_stopped_without_call",
                "DHD_OP08_P7_readfeel_reconnection_design_closed_stopped_without_evaluation",
                "DHD_OP08_explicit_current_DHC_material_selection_required_closed_without_synthesis",
                "DHD_OP08_repair_or_wait_boundary_closed_stopped_without_downstream",
                "DHD_OP08_non_DHR_lane_route_preserved_closed_stopped",
                "DHD_OP08_no_touch_repair_or_hold_closed_stopped_without_promotion",
            )[decision_index]
        )
    status_ref = P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS[decision_index]
    decision_ref = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS[decision_index]
    selected_candidate_ref = P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[
        decision_index
    ]
    reason_refs = _dedupe_clean_refs(reasons)
    blocker_refs = _dedupe_clean_refs(
        [*blockers, *forbidden_paths, *body_like_paths, *guard_true_paths, *no_touch_paths]
    )
    branch_flags = [index == decision_index for index in range(6)]

    data: dict[str, Any] = {}
    data.update(_false_flags(P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FALSE_FLAG_REFS))
    data.update(
        {
            "schema_version": P7_R54_AHR_POST_DHC_DHD_OP08_SCHEMA_VERSION,
            "phase": P7_R54_AHR_POST_DHC_DHD_PHASE,
            "step": P7_R54_AHR_POST_DHC_DHD_STEP,
            "scope": P7_R54_AHR_POST_DHC_DHD_SCOPE,
            "policy_kind": P7_R54_AHR_POST_DHC_DHD_POLICY_KIND,
            "operation_step_ref": P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF,
            "material_id": "p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure_20260709",
            "review_session_id": _safe_review_session_id(
                review_session_id or op07_map.get("review_session_id")
            ),
            "source_mode": P7_R54_AHR_POST_DHC_DHD_SOURCE_MODE,
            "git_connection_required": False,
            "git_checked": False,
            "op07_material_present": op07_present,
            "op07_contract_valid": op07_contract_valid,
            "op07_schema_version_ref": _clean_ref(
                op07_map.get("schema_version"), default="op07_schema_missing"
            ),
            "op07_material_ref": _clean_ref(
                op07_map.get("material_id"), default="op07_material_missing"
            ),
            "op07_status_ref": op07_status_ref,
            "op07_validation_plan_materialized_stopped": op07_materialized,
            "op07_validation_plan_is_not_validation_result": bool(
                op07_contract_valid
                and op07_map.get("validation_plan_is_not_validation_result") is True
            ),
            "op07_validation_plan_does_not_claim_green": bool(
                op07_contract_valid
                and op07_map.get("validation_plan_does_not_claim_green") is True
            ),
            "op07_validation_commands_executed_here": bool(
                op07_contract_valid
                and op07_map.get("validation_commands_executed_here") is True
            ),
            "op07_result_memo_files_created_here": bool(
                op07_contract_valid
                and op07_map.get("result_memo_files_created_here") is True
            ),
            "op07_carried_direction_decision_ref": op07_decision_ref,
            "op07_carried_selected_next_design_candidate_ref": op07_candidate_ref,
            "optional_op05_material_supplied": op05_supplied,
            "optional_op05_material_present": op05_present,
            "optional_op05_contract_valid": op05_contract_valid,
            "optional_op05_schema_version_ref": _clean_ref(
                op05_map.get("schema_version"), default="optional_op05_schema_missing"
            ),
            "optional_op05_material_ref": _clean_ref(
                op05_map.get("material_id"), default="optional_op05_material_missing"
            ),
            "optional_op05_status_ref": _clean_ref(
                op05_map.get("dhd_op05_status_ref"), default="optional_op05_status_missing"
            ),
            "optional_op05_direction_decision_ref": op05_decision_ref,
            "optional_op05_selected_next_design_candidate_ref": op05_candidate_ref,
            "optional_op05_consistency_required": op05_supplied,
            "optional_op05_consistency_satisfied": op05_consistency_satisfied,
            "optional_op05_matches_op07": op05_matches_op07,
            "op08_input_forbidden_payload_key_path_refs": forbidden_paths,
            "op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
            "op08_input_body_like_value_path_refs": body_like_paths,
            "op08_input_body_like_value_path_count": len(body_like_paths),
            "op08_input_guard_true_field_path_refs": guard_true_paths,
            "op08_input_guard_true_field_path_count": len(guard_true_paths),
            "op08_input_no_touch_mutation_path_refs": no_touch_paths,
            "op08_input_no_touch_mutation_path_count": len(no_touch_paths),
            "op08_input_repair_or_blocked": input_repair_or_blocked,
            "op08_upstream_no_touch_decision_preserved": bool(
                not input_repair_or_blocked and decision_index == 5
            ),
            "dhd_op08_status_ref": status_ref,
            "bodyfree_stopped_next_design_decision_closure_status_ref": status_ref,
            "dhd_op08_allowed_status_refs": P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS,
            "dhd_op08_allowed_status_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS
            ),
            "direction_decision_ref": decision_ref,
            "direction_decision_refs": P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS,
            "direction_decision_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS
            ),
            "selected_next_design_candidate_ref": selected_candidate_ref,
            "selected_next_design_candidate_refs": P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS,
            "selected_next_design_candidate_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS
            ),
            "dhd_op08_dhr_op06_consideration_design_closed_stopped": branch_flags[0],
            "dhd_op08_p7_readfeel_reconnection_design_closed_stopped": branch_flags[1],
            "dhd_op08_explicit_current_dhc_material_selection_required_closed_stopped": branch_flags[2],
            "dhd_op08_repair_or_wait_boundary_closed_stopped": branch_flags[3],
            "dhd_op08_non_dhr_lane_route_preserved_closed_stopped": branch_flags[4],
            "dhd_op08_blocked_no_touch_no_promotion": branch_flags[5],
            "dhd_op08_closed_stopped": True,
            "current_execution_allowance_ref": P7_R54_AHR_POST_DHC_DHD_CURRENT_EXECUTION_ALLOWANCE_REF,
            "next_runtime_execution_allowed_here": False,
            "target_test_ref_refs": P7_R54_AHR_POST_DHC_DHD_R6_TARGET_TEST_REF_REFS,
            "target_test_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R6_TARGET_TEST_REF_REFS
            ),
            "selected_regression_test_ref_refs": P7_R54_AHR_POST_DHC_DHD_R6_SELECTED_REGRESSION_TEST_REF_REFS,
            "selected_regression_test_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R6_SELECTED_REGRESSION_TEST_REF_REFS
            ),
            "optional_product_readfeel_regression_ref_refs": P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS,
            "optional_product_readfeel_regression_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS
            ),
            "compileall_target_ref_refs": P7_R54_AHR_POST_DHC_DHD_R6_COMPILEALL_TARGET_REF_REFS,
            "compileall_target_ref_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R6_COMPILEALL_TARGET_REF_REFS
            ),
            "result_memo_expected_file_refs": P7_R54_AHR_POST_DHC_DHD_R6_RESULT_MEMO_EXPECTED_FILE_REFS,
            "result_memo_expected_file_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_R6_RESULT_MEMO_EXPECTED_FILE_REFS
            ),
            "validation_commands_executed_here": False,
            "target_validation_green_confirmed_here": False,
            "selected_regression_green_confirmed_here": False,
            "optional_product_readfeel_regression_green_confirmed_here": False,
            "compileall_green_confirmed_here": False,
            "full_backend_suite_green_confirmed": False,
            "rn_contract_green_confirmed": False,
            "raw_pytest_stdout_included": False,
            "raw_pytest_stderr_included": False,
            "raw_traceback_included": False,
            "raw_body_included": False,
            "comment_text_body_included": False,
            "question_text_body_included": False,
            "closure_is_not_validation_result": True,
            "closure_does_not_claim_green": True,
            "result_memo_files_created_here": False,
            "dhd_op08_reason_refs": reason_refs,
            "dhd_op08_reason_ref_count": len(reason_refs),
            "dhd_op08_blocker_refs": blocker_refs,
            "dhd_op08_blocker_ref_count": len(blocker_refs),
            "dhd_op08_does_not_call_dhc_or_dhr_builder": True,
            "dhd_op08_does_not_use_dhr_op06_implicit_op05_fallback": True,
            "dhd_op08_does_not_execute_selected_direction": True,
            "dhd_op08_does_not_materialize_dhr_op07_or_execute_dmd_r52": True,
            "dhd_op08_does_not_start_actual_review_or_create_rows": True,
            "dhd_op08_does_not_create_question_need_observation_rows": True,
            "dhd_op08_does_not_start_p8_or_materialize_question_text": True,
            "dhd_op08_does_not_change_api_db_rn_runtime_response_key": True,
            "dhd_op08_does_not_create_json_schema_file": True,
            "dhd_op08_does_not_create_result_memo_files": True,
            "dhd_op08_does_not_claim_validation_or_environment_green": True,
            "dhd_op08_does_not_claim_p7_complete_or_release": True,
            "claim_boundary_refs": list(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "claim_boundary_ref_count": len(P7_R54_AHR_POST_DHC_DHD_CLAIM_BOUNDARY_REFS),
            "not_claimed_boundary_refs": list(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_NOT_CLAIMED_BOUNDARY_REFS
            ),
            "not_claimed_boundary": _not_claimed_boundary(),
            "fixed_non_promotion_refs": list(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "fixed_non_promotion_ref_count": len(
                P7_R54_AHR_POST_DHC_DHD_FIXED_NON_PROMOTION_REFS
            ),
            "implemented_steps": list(P7_R54_AHR_POST_DHC_DHD_OP08_IMPLEMENTED_STEPS),
            "not_yet_implemented_steps": list(
                P7_R54_AHR_POST_DHC_DHD_OP08_NOT_YET_IMPLEMENTED_STEPS
            ),
            "public_contract": public_contract_flags(),
            "dhd_no_touch_contract": _no_touch_contract(),
            "body_free_markers": _body_free_markers(),
            "dhd_op00_implemented": True,
            "dhd_op01_implemented": True,
            "dhd_op02_implemented": True,
            "dhd_op03_implemented": True,
            "dhd_op04_implemented": True,
            "dhd_op05_implemented": True,
            "dhd_op06_implemented": True,
            "dhd_op07_implemented": True,
            "dhd_op08_implemented": True,
            "next_required_step": selected_candidate_ref,
            "body_free": True,
        }
    )
    return data


def assert_p7_r54_ahr_post_dhc_dhd_op08_stopped_next_design_decision_closure_contract(
    data: Mapping[str, Any],
) -> bool:
    """Assert DHD-OP08 stopped closure and no-execution boundaries."""

    _required_fields_present(
        data, required=P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FIELD_REFS, source="DHD-OP08"
    )
    if set(data) != set(P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("DHD-OP08 field set changed")
    if data.get("schema_version") != P7_R54_AHR_POST_DHC_DHD_OP08_SCHEMA_VERSION:
        raise ValueError("DHD-OP08 schema mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_DHC_DHD_OP08_STEP_REF:
        raise ValueError("DHD-OP08 step mismatch")
    _assert_r3_shared_contract(
        data,
        source="DHD-OP08",
        required_false_refs=P7_R54_AHR_POST_DHC_DHD_OP08_REQUIRED_FALSE_FLAG_REFS,
    )
    for key in (
        "dhd_op08_closed_stopped",
        "closure_is_not_validation_result",
        "closure_does_not_claim_green",
        "dhd_op08_does_not_call_dhc_or_dhr_builder",
        "dhd_op08_does_not_use_dhr_op06_implicit_op05_fallback",
        "dhd_op08_does_not_execute_selected_direction",
        "dhd_op08_does_not_materialize_dhr_op07_or_execute_dmd_r52",
        "dhd_op08_does_not_start_actual_review_or_create_rows",
        "dhd_op08_does_not_create_question_need_observation_rows",
        "dhd_op08_does_not_start_p8_or_materialize_question_text",
        "dhd_op08_does_not_change_api_db_rn_runtime_response_key",
        "dhd_op08_does_not_create_json_schema_file",
        "dhd_op08_does_not_create_result_memo_files",
        "dhd_op08_does_not_claim_validation_or_environment_green",
        "dhd_op08_does_not_claim_p7_complete_or_release",
        "dhd_op00_implemented",
        "dhd_op01_implemented",
        "dhd_op02_implemented",
        "dhd_op03_implemented",
        "dhd_op04_implemented",
        "dhd_op05_implemented",
        "dhd_op06_implemented",
        "dhd_op07_implemented",
        "dhd_op08_implemented",
    ):
        if data.get(key) is not True:
            raise ValueError(f"DHD-OP08 required true field changed: {key}")
    for key in (
        "next_runtime_execution_allowed_here",
        "op07_validation_commands_executed_here",
        "op07_result_memo_files_created_here",
        "validation_commands_executed_here",
        "target_validation_green_confirmed_here",
        "selected_regression_green_confirmed_here",
        "optional_product_readfeel_regression_green_confirmed_here",
        "compileall_green_confirmed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "result_memo_files_created_here",
        "raw_pytest_stdout_included",
        "raw_pytest_stderr_included",
        "raw_traceback_included",
        "raw_body_included",
        "comment_text_body_included",
        "question_text_body_included",
        "dhr_op06_builder_called_here",
        "dhr_op06_implicit_op05_fallback_used_here",
        "dhr_op07_materialized_here",
        "dmd_execution_started_here",
        "dmd_r52_executed_here",
        "r52_actual_execution_started_here",
        "actual_review_started_here",
        "actual_rows_created_here",
        "question_need_observation_rows_created_here",
        "p7_readfeel_evaluation_started_here",
        "p8_question_design_started",
        "p8_question_implementation_started",
        "question_text_materialized_here",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"DHD-OP08 forbidden execution/result claim changed: {key}")
    if data.get("current_execution_allowance_ref") != P7_R54_AHR_POST_DHC_DHD_CURRENT_EXECUTION_ALLOWANCE_REF:
        raise ValueError("DHD-OP08 current execution allowance changed")
    if tuple(data.get("dhd_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP08 allowed status refs changed")
    if data.get("dhd_op08_allowed_status_ref_count") != len(
        P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS
    ):
        raise ValueError("DHD-OP08 allowed status count changed")
    status_ref = data.get("dhd_op08_status_ref")
    decision_ref = data.get("direction_decision_ref")
    candidate_ref = data.get("selected_next_design_candidate_ref")
    if status_ref not in P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("DHD-OP08 status is not allowed")
    if decision_ref not in P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS:
        raise ValueError("DHD-OP08 direction decision is not allowed")
    decision_index = P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS.index(decision_ref)
    if status_ref != P7_R54_AHR_POST_DHC_DHD_OP08_ALLOWED_STATUS_REFS[decision_index]:
        raise ValueError("DHD-OP08 status/decision pair changed")
    if candidate_ref != P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS[decision_index]:
        raise ValueError("DHD-OP08 decision/candidate pair changed")
    if data.get("bodyfree_stopped_next_design_decision_closure_status_ref") != status_ref:
        raise ValueError("DHD-OP08 status alias changed")
    branch_flags = (
        data.get("dhd_op08_dhr_op06_consideration_design_closed_stopped") is True,
        data.get("dhd_op08_p7_readfeel_reconnection_design_closed_stopped") is True,
        data.get("dhd_op08_explicit_current_dhc_material_selection_required_closed_stopped")
        is True,
        data.get("dhd_op08_repair_or_wait_boundary_closed_stopped") is True,
        data.get("dhd_op08_non_dhr_lane_route_preserved_closed_stopped") is True,
        data.get("dhd_op08_blocked_no_touch_no_promotion") is True,
    )
    if sum(branch_flags) != 1 or branch_flags[decision_index] is not True:
        raise ValueError("DHD-OP08 must select exactly one matching closure branch")
    if data.get("next_required_step") != candidate_ref:
        raise ValueError("DHD-OP08 next design candidate changed")
    input_repair_or_blocked = data.get("op08_input_repair_or_blocked") is True
    expected_upstream_no_touch_preserved = bool(
        not input_repair_or_blocked and decision_index == 5
    )
    if data.get("op08_upstream_no_touch_decision_preserved") is not (
        expected_upstream_no_touch_preserved
    ):
        raise ValueError("DHD-OP08 upstream no-touch preservation marker changed")
    if data.get("op07_contract_valid") is True:
        if data.get("op07_material_present") is not True:
            raise ValueError("DHD-OP08 valid OP07 must be present")
    if data.get("op07_validation_plan_materialized_stopped") is True:
        if data.get("op07_contract_valid") is not True:
            raise ValueError("DHD-OP08 materialized OP07 must be contract-valid")
    op05_supplied = data.get("optional_op05_material_supplied") is True
    op05_matches = data.get("optional_op05_matches_op07") is True
    if data.get("optional_op05_consistency_required") is not op05_supplied:
        raise ValueError("DHD-OP08 optional OP05 consistency requirement changed")
    if data.get("optional_op05_consistency_satisfied") is not bool(
        not op05_supplied or op05_matches
    ):
        raise ValueError("DHD-OP08 optional OP05 consistency result changed")
    if not op05_supplied:
        if data.get("optional_op05_material_present") is not False:
            raise ValueError("DHD-OP08 omitted OP05 cannot be marked present")
        if data.get("optional_op05_contract_valid") is not False:
            raise ValueError("DHD-OP08 omitted OP05 cannot be marked valid")
        if data.get("optional_op05_matches_op07") is not False:
            raise ValueError("DHD-OP08 omitted OP05 cannot be marked matching")
    if data.get("optional_op05_contract_valid") is True:
        if data.get("optional_op05_material_present") is not True:
            raise ValueError("DHD-OP08 valid optional OP05 must be present")
    if input_repair_or_blocked:
        if decision_index != 5 or not data.get("dhd_op08_blocker_refs"):
            raise ValueError("DHD-OP08 invalid input must close as blocked no-touch with blockers")
    else:
        if data.get("op07_contract_valid") is not True:
            raise ValueError("DHD-OP08 normal closure requires valid OP07")
        if data.get("op07_validation_plan_materialized_stopped") is not True:
            raise ValueError("DHD-OP08 normal closure requires materialized OP07 plan")
        if data.get("optional_op05_consistency_satisfied") is not True:
            raise ValueError("DHD-OP08 normal closure requires optional OP05 consistency")
        if data.get("dhd_op08_blocker_refs"):
            raise ValueError("DHD-OP08 normal closure cannot retain blockers")
        if data.get("op07_carried_direction_decision_ref") != decision_ref:
            raise ValueError("DHD-OP08 cannot replace the OP07-carried decision")
        if data.get("op07_carried_selected_next_design_candidate_ref") != candidate_ref:
            raise ValueError("DHD-OP08 cannot replace the OP07-carried candidate")
    if op05_supplied:
        if data.get("optional_op05_consistency_required") is not True:
            raise ValueError("DHD-OP08 supplied OP05 must require consistency")
        if not input_repair_or_blocked:
            if data.get("optional_op05_contract_valid") is not True:
                raise ValueError("DHD-OP08 normal supplied OP05 must be valid")
            if data.get("optional_op05_matches_op07") is not True:
                raise ValueError("DHD-OP08 normal supplied OP05 must match OP07")
            if data.get("optional_op05_direction_decision_ref") != decision_ref:
                raise ValueError("DHD-OP08 cannot replace the supplied OP05 decision")
            if data.get("optional_op05_selected_next_design_candidate_ref") != candidate_ref:
                raise ValueError("DHD-OP08 cannot replace the supplied OP05 candidate")
    if tuple(data.get("direction_decision_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_DIRECTION_DECISION_REFS:
        raise ValueError("DHD-OP08 direction refs changed")
    if tuple(data.get("selected_next_design_candidate_refs") or ()) != P7_R54_AHR_POST_DHC_DHD_NEXT_DESIGN_CANDIDATE_REFS:
        raise ValueError("DHD-OP08 next candidate refs changed")
    exact_ref_fields = (
        ("target_test_ref_refs", P7_R54_AHR_POST_DHC_DHD_R6_TARGET_TEST_REF_REFS),
        (
            "selected_regression_test_ref_refs",
            P7_R54_AHR_POST_DHC_DHD_R6_SELECTED_REGRESSION_TEST_REF_REFS,
        ),
        (
            "optional_product_readfeel_regression_ref_refs",
            P7_R54_AHR_POST_DHC_DHD_R4_OPTIONAL_PRODUCT_READFEEL_REGRESSION_REF_REFS,
        ),
        ("compileall_target_ref_refs", P7_R54_AHR_POST_DHC_DHD_R6_COMPILEALL_TARGET_REF_REFS),
        (
            "result_memo_expected_file_refs",
            P7_R54_AHR_POST_DHC_DHD_R6_RESULT_MEMO_EXPECTED_FILE_REFS,
        ),
    )
    for field, expected in exact_ref_fields:
        if tuple(data.get(field) or ()) != tuple(expected):
            raise ValueError(f"DHD-OP08 exact ref field changed: {field}")
    for field, count_field in (
        ("op08_input_forbidden_payload_key_path_refs", "op08_input_forbidden_payload_key_path_count"),
        ("op08_input_body_like_value_path_refs", "op08_input_body_like_value_path_count"),
        ("op08_input_guard_true_field_path_refs", "op08_input_guard_true_field_path_count"),
        ("op08_input_no_touch_mutation_path_refs", "op08_input_no_touch_mutation_path_count"),
        ("target_test_ref_refs", "target_test_ref_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_ref_count"),
        (
            "optional_product_readfeel_regression_ref_refs",
            "optional_product_readfeel_regression_ref_ref_count",
        ),
        ("compileall_target_ref_refs", "compileall_target_ref_ref_count"),
        ("result_memo_expected_file_refs", "result_memo_expected_file_ref_count"),
        ("dhd_op08_reason_refs", "dhd_op08_reason_ref_count"),
        ("dhd_op08_blocker_refs", "dhd_op08_blocker_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"DHD-OP08 count field changed: {count_field}")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP08_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP08 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_POST_DHC_DHD_OP08_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("DHD-OP08 not-yet steps changed")
    return True
