# -*- coding: utf-8 -*-
"""Post-RDB08 selected next-stage candidate intake helpers.

NCI is intentionally a thin, body-free, backend-internal boundary after the
already-closed RDB-OP08 result manual decision memo.  This implementation
currently covers NCI-OP00 through NCI-OP08.

* NCI-OP00 refreezes scope / no-execution / no-promotion after RDB-OP08.  It
  does not intake the RDB-OP08 result memo yet, does not execute the selected
  next-stage candidate, and never calls DHR-OP05 or starts P8.
* NCI-OP01 intakes the RDB-OP08 body-free result memo closure, verifies the
  existing RDB-OP08 contract, records only safe refs, and stops at material
  readiness for NCI-OP02 selected candidate shape validation.
* NCI-OP02 validates selected_next_stage_candidate shape without execution.
* NCI-OP03 resolves the selected candidate lane without calling downstream
  operations.
* NCI-OP04 materializes the next design target or stop material without
  executing it.
* NCI-OP05 guards OP00-OP04 with body-free / no-touch / no-promotion /
  no-auto-execution checks before OP06 validation planning.
* NCI-OP06 records target / selected regression / compileall validation plan refs without executing tests.
* NCI-OP07 drafts a body-free handoff-or-stop envelope without executing any selected candidate.
* NCI-OP08 closes the body-free result memo with the selected handoff-or-stop envelope and still does not execute it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb


P7_R54_AHR_POST_RDB08_NCI_PHASE: Final = "P7"
P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_RDB08_NCI_STEP: Final = (
    "R54-AHR-PostRDB08_SelectedNextStageCandidateIntake_20260706"
)
P7_R54_AHR_POST_RDB08_NCI_SCOPE: Final = (
    "p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_boundary"
)
P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND: Final = (
    "r54_ahr_post_rdb08_selected_next_stage_candidate_intake_bodyfree_boundary"
)
P7_R54_AHR_POST_RDB08_NCI_DEFAULT_REVIEW_SESSION_ID: Final = (
    rdb.P7_R54_AHR_POST_MRB08_RDB_DEFAULT_REVIEW_SESSION_ID
)

P7_R54_AHR_POST_RDB08_NCI_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op00_scope_no_execution_no_promotion_refreeze_after_rdb08.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op01_rdb08_bodyfree_result_memo_closure_intake.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op02_selected_next_stage_candidate_shape_validation.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op03_selected_candidate_lane_consistency_resolver.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op04_next_design_target_or_stop_materialization.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op06_selected_regression_compileall_validation_plan.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op07_handoff_or_stop_envelope_draft_material.bodyfree.v1"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_rdb08.nci."
    "op08_selected_candidate_intake_result_memo_closure.bodyfree.v1"
)

P7_R54_AHR_POST_RDB08_NCI_OP00_STEP_REF: Final = (
    "NCI-OP00_scope_no_execution_no_promotion_refreeze_after_RDB_OP08"
)
P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF: Final = (
    "NCI-OP01_RDB_OP08_bodyfree_result_memo_closure_intake"
)
P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF: Final = (
    "NCI-OP02_selected_next_stage_candidate_shape_validation"
)
P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF: Final = (
    "NCI-OP03_selected_candidate_lane_consistency_resolver"
)
P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF: Final = (
    "NCI-OP04_next_design_target_or_stop_materialization"
)
P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF: Final = (
    "NCI-OP05_bodyfree_no_touch_no_promotion_no_auto_execution_guard"
)
P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF: Final = (
    "NCI-OP06_selected_regression_compileall_validation_plan"
)
P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF: Final = (
    "NCI-OP07_handoff_or_stop_envelope_draft_material"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF: Final = (
    "NCI-OP08_bodyfree_selected_candidate_intake_result_memo_closure"
)
P7_R54_AHR_POST_RDB08_NCI_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP00_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF,
)
P7_R54_AHR_POST_RDB08_NCI_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP00_STEP_REF,
)
P7_R54_AHR_POST_RDB08_NCI_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[1:]
)
P7_R54_AHR_POST_RDB08_NCI_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[:2]
)
P7_R54_AHR_POST_RDB08_NCI_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[2:]
)
P7_R54_AHR_POST_RDB08_NCI_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[:3]
)
P7_R54_AHR_POST_RDB08_NCI_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[3:]
)
P7_R54_AHR_POST_RDB08_NCI_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[:4]
)
P7_R54_AHR_POST_RDB08_NCI_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[4:]
)
P7_R54_AHR_POST_RDB08_NCI_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[:5]
)
P7_R54_AHR_POST_RDB08_NCI_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[5:]
)
P7_R54_AHR_POST_RDB08_NCI_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[:6]
)
P7_R54_AHR_POST_RDB08_NCI_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[6:]
)
P7_R54_AHR_POST_RDB08_NCI_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[:7]
)
P7_R54_AHR_POST_RDB08_NCI_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[7:]
)
P7_R54_AHR_POST_RDB08_NCI_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[:8]
)
P7_R54_AHR_POST_RDB08_NCI_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS[8:]
)
P7_R54_AHR_POST_RDB08_NCI_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STEP_REFS
)
P7_R54_AHR_POST_RDB08_NCI_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_RDB08_NCI_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-RDB08 Selected Next-Stage Candidate Intake / Manual Lane Confirmation Boundary"
)
P7_R54_AHR_POST_RDB08_NCI_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-RDB08 Selected Next-Stage Candidate Intake / Manual Lane Confirmation Boundary"
)
P7_R54_AHR_POST_RDB08_NCI_BOUNDARY_PREFIX_REF: Final = "NCI"
P7_R54_AHR_POST_RDB08_NCI_BOUNDARY_PREFIX_MEANING_REF: Final = (
    "Next Candidate Intake"
)
P7_R54_AHR_POST_RDB08_NCI_EXPECTED_FROM_RDB08_REF: Final = (
    "RDB-OP08 body-free result memo closure records selected_next_stage_candidate; "
    "it is not selected candidate execution, DHR-OP05 permission, P8 start, or release permission"
)
P7_R54_AHR_POST_RDB08_NCI_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_nci_op01_rdb08_closure_intake_without_candidate_execution"
)

P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_RDB08_CLOSURE_REF: Final = (
    "wait_for_rdb08_closure_or_validation_refs_before_candidate_shape_validation"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF: Final = (
    "repair_rdb08_result_memo_closure_intake_without_candidate_execution"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_RDB08_INTAKE_REF: Final = (
    "blocked_post_rdb08_candidate_intake_bodyfree_leak_or_promotion"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_CANDIDATE_SHAPE_REF: Final = (
    "repair_selected_next_stage_candidate_shape_before_lane_resolution"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_CANDIDATE_SHAPE_REF: Final = (
    "blocked_selected_next_stage_candidate_shape_bodyfree_leak_promotion_or_p8"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_LANE_CONSISTENCY_REF: Final = (
    "repair_selected_candidate_lane_consistency_before_next_design_target_materialization"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP04_MATERIALIZATION_REF: Final = (
    "repair_nci_op04_next_design_target_or_stop_materialization_input"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP04_MATERIALIZATION_REF: Final = (
    "blocked_nci_op04_bodyfree_leak_promotion_or_autorun_before_guard"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP05_GUARD_REF: Final = (
    "repair_nci_op05_bodyfree_no_touch_no_promotion_guard_input"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP05_GUARD_REF: Final = (
    "blocked_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF: Final = (
    "wait_for_nci_op05_guard_pass_before_validation_plan"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_REF: Final = (
    "repair_nci_op06_selected_regression_compileall_validation_plan_input"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF: Final = (
    "blocked_nci_op06_validation_plan_bodyfree_leak_promotion_or_touch"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP07_ENVELOPE_REF: Final = (
    "blocked_nci_op07_handoff_or_stop_envelope_bodyfree_leak_promotion_or_touch"
)

P7_R54_AHR_POST_RDB08_NCI_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(293).zip",
    "implemented_docs": "EmlisAIの実装済み資料(100).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_system_update_20260706(1).zip",
    "cocolon_app": "Cocolon(273).zip",
    "backend": "mashos-api(186).zip",
}
P7_R54_AHR_POST_RDB08_NCI_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/07_latest_snapshot_diff.md",
    "Cocolon_前提資料/work_attitude_rules_for_karen/00_read_first.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/04_forbidden_mixing_design_and_implementation.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/08_artifact_delivery_rules.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/09_work_start_checklist.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/10_stop_judgment_and_unwritten_rules.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/14_cocolon_joint_development_and_karen_thought_boundary.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/15_trust_based_joint_development_boundary_2026_06_05.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt",
    "Cocolon_前提資料/cocolon_thought_material_for_karen.md",
    "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
    "Cocolon_前提資料/emlis_ai_state_answer_human_follow_definition_2026_05_26.md",
    "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostRDB08_SelectedCandidateIntake_PreDesignMemo_20260706.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostRDB08_SelectedNextStageCandidateIntake_ManualLaneConfirmation_DetailedDesign_ImplementationOrder_20260706.md",
    "mashos-api/ai/tests/R54_AHR_PostMRB08_DHROP04ResultManualDecision_RDB_OP00_OP08_Result_20260705.md",
)
P7_R54_AHR_POST_RDB08_NCI_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "RDB-OP08 selected candidate execution",
    "DHR-OP04 recall",
    "DHR-OP05 call",
    "DHR-OP06 call",
    "DHR-OP07 materialization",
    "DMD execution",
    "R52 actual execution",
    "actual body-full packet generation",
    "actual local-only human review execution",
    "actual operation receipt creation",
    "actual rows creation",
    "actual disposal / purge execution",
    "P5 finalization",
    "P6 start",
    "P8 start",
    "P8 question design",
    "P8 question implementation",
    "P7 completion",
    "release decision",
    "API / DB / RN / runtime / response key change",
)
P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "RDB-OP08 closure is only body-free result manual decision memo closure",
    "RDB-OP08 selected_next_stage_candidate remains not executed",
    "NCI-OP00 does not intake the RDB-OP08 closure yet",
    "NCI-OP01 reads RDB-OP08 safe refs only and does not resolve selected candidate lane",
    "NCI-OP01 does not validate selected candidate kind/ref shape yet",
    "NCI-OP02 validates candidate shape but does not resolve selected candidate lane",
    "NCI-OP03 resolves lane without executing selected next-stage candidate",
    "NCI-OP04 materializes only body-free next design target or stop material",
    "NCI-OP05 guards OP00-OP04 body-free/no-touch/no-promotion before validation planning",
    "NCI-OP06 records validation plan refs without executing target tests selected regression or compileall",
    "NCI-OP07 drafts handoff-or-stop envelope without executing selected candidate",
    "NCI-OP08 closes body-free result memo with handoff-or-stop envelope without executing selected candidate",
    "NCI-OP03/OP04/OP05/OP06/OP07/OP08 do not call DHR-OP05 or later",
    "NCI-OP03/OP04/OP05/OP06/OP07/OP08 do not start P8 question design",
)
P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "selected_next_stage_candidate_executed_here",
    "candidate_execution_started_here",
    "dhr_op04_recalled_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_claimed_here",
    "rn_contract_green_claimed_here",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_rdb_op08_candidate_execution",
    "no_dhr_op04_recall",
    "no_dhr_op05_call",
    "no_dhr_op06_call",
    "no_dhr_op07_materialization",
    "no_dmd_execution",
    "no_r52_actual_execution",
    "no_actual_review_execution",
    "no_actual_rows_creation",
    "no_p5_p6_p8_p7_release_promotion",
    "no_api_db_rn_runtime_response_key_change",
    "no_p8_question_text_or_question_spec_materialization",
)

P7_R54_AHR_POST_RDB08_NCI_NO_TOUCH_CONTRACT_KEYS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "public_response_top_level_key_added",
    "db_schema_changed",
    "db_write_path_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_generation_changed",
    "runtime_prompt_changed",
    "p8_question_surface_changed",
    "question_schema_changed",
    "question_trigger_changed",
    "question_answer_storage_changed",
)
P7_R54_AHR_POST_RDB08_NCI_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = (
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
    "private_user_dictionary_text_included",
    "local_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_POST_RDB08_NCI_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = (
    "raw_input",
    "input_body",
    "comment_text",
    "comment_text_body",
    "returned_surface_body",
    "body_full_packet",
    "body_full_packet_body",
    "reviewer_free_text",
    "reviewer_note_body",
    "question_text",
    "draft_question_text",
    "answer_text",
    "private_user_dictionary_text",
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
)
P7_R54_AHR_POST_RDB08_NCI_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = (
    "selected_next_stage_candidate_executed_here",
    "candidate_execution_started_here",
    "manual_decision_auto_executes_downstream",
    "downstream_auto_execution_allowed",
    "dhr_op04_recalled_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_design_started_here",
    "p8_question_implementation_started",
    "p8_question_implementation_started_here",
    "p8_question_spec_created",
    "p8_question_substitution_allowed",
    "question_text_materialized",
    "p7_complete",
    "release_allowed",
    "release_decision_created_here",
    "full_backend_suite_green_claimed_here",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_claimed_here",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
)
P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "selected_next_stage_candidate_executed_here",
    "candidate_execution_started_here",
    "dhr_op04_recalled_here",
    "dhr_op05_called_here",
    "dhr_op05_builder_called_here",
    "dhr_op06_called_here",
    "dhr_op07_materialized_here",
    "dmd_execution_started_here",
    "r52_actual_execution_started_here",
    "actual_body_full_packet_generated_here",
    "actual_local_human_review_execution_started_here",
    "actual_operation_receipt_created_here",
    "actual_rows_created_here",
    "actual_question_need_observation_rows_created_here",
    "actual_disposal_or_purge_executed_here",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
)

P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF: Final = (
    "NCI_STATUS_RDB08_CLOSURE_READY_FOR_CANDIDATE_SHAPE_CHECK"
)
P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_WAITING_FOR_RDB08_CLOSURE_REF: Final = (
    "NCI_STATUS_WAITING_FOR_RDB08_CLOSURE_OR_VALIDATION_REFS"
)
P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF: Final = (
    "NCI_STATUS_REPAIR_REQUIRED_FOR_RDB08_CLOSURE_INPUTS"
)
P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "NCI_STATUS_BLOCKED_RDB08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_RDB08_NCI_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_WAITING_FOR_RDB08_CLOSURE_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)

P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS: Final[tuple[str, ...]] = (
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
)

P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_REF_REFS: Final[tuple[str, ...]] = (
    rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_MRB08_CLOSURE_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
)
P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_SELECTED_STATUS_REFS: Final[tuple[str, ...]] = (
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF,
    rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
)
P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_REF_MAP: Final[Mapping[str, tuple[str, ...]]] = {
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_MANUAL_HOLD_UNRESOLVED_REF,
        rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_MRB08_CLOSURE_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_BLOCKED_POST_MRB08_REF,
    ),
}
P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_STATUS_MAP: Final[Mapping[str, tuple[str, ...]]] = {
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_INCOMPLETE_UNRESOLVED_MANUAL_HOLD_STOPPED_REF,
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF,
    ),
}
P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_DECISION_LANE_MAP: Final[Mapping[str, tuple[str, ...]]] = {
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_CONFIRMED_DHR_OP05_HANDOFF_CANDIDATE_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_RETRY_OR_START_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_EXTERNAL_CLAIM_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_RESULT_OR_MRB08_REF,
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_REPAIR_BRANCH_STATUS_MISMATCH_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_MANUAL_HOLD_UNRESOLVED_REF,
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_WAIT_MRB08_CLOSURE_REF,
    ),
    rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF: (
        rdb.P7_R54_AHR_POST_MRB08_RDB_DECISION_LANE_BLOCKED_REF,
    ),
}

P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_READY_FOR_OP03_REF: Final = (
    "NCI_STATUS_SELECTED_CANDIDATE_SHAPE_READY_FOR_LANE_RESOLUTION"
)
P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_REPAIR_SELECTED_CANDIDATE_SHAPE_REF: Final = (
    "NCI_STATUS_REPAIR_REQUIRED_FOR_SELECTED_CANDIDATE_SHAPE"
)
P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_OR_P8_REF: Final = (
    "NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_SHAPE_BODYFREE_PROMOTION_OR_P8"
)
P7_R54_AHR_POST_RDB08_NCI_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_READY_FOR_OP03_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_REPAIR_SELECTED_CANDIDATE_SHAPE_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_OR_P8_REF,
)

P7_R54_AHR_POST_RDB08_NCI_STATUS_DHR_OP05_DESIGN_TARGET_CANDIDATE_STOPPED_REF: Final = (
    "NCI_STATUS_DHR_OP05_DESIGN_TARGET_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_STATUS_RETRY_OR_START_ROUTE_CANDIDATE_STOPPED_REF: Final = (
    "NCI_STATUS_RETRY_OR_START_ROUTE_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_STATUS_WAIT_EXTERNAL_CLAIM_CANDIDATE_STOPPED_REF: Final = (
    "NCI_STATUS_WAIT_EXTERNAL_CLAIM_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED_REF: Final = (
    "NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF: Final = (
    "NCI_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_STOPPED_REF: Final = (
    "NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_STATUS_DHR_OP05_DESIGN_TARGET_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_RDB08_NCI_STATUS_RETRY_OR_START_ROUTE_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_RDB08_NCI_STATUS_WAIT_EXTERNAL_CLAIM_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_RDB08_NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_RDB08_NCI_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF,
    P7_R54_AHR_POST_RDB08_NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_STOPPED_REF,
)

P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF: Final = (
    "dhr_op05_manual_handoff_boundary_design_candidate"
)
P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF: Final = (
    "retry_or_start_actual_local_only_review_route_candidate"
)
P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: Final = (
    "wait_external_bodyfree_claim_reintake_candidate"
)
P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF: Final = (
    "repair_rdb_candidate_or_upstream_result_candidate"
)
P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF: Final = (
    "manual_hold_unresolved_post_rdb08_candidate"
)
P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "blocked_bodyfree_leak_promotion_or_autorun_candidate"
)
P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF,
    P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF,
    P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
    P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
    P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF,
    P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)

P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF: Final = (
    "prepare_post_nci_dhr_op05_manual_handoff_boundary_design_without_call"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_RETRY_OR_START_REF: Final = (
    "return_to_actual_local_only_review_retry_start_boundary_without_execution"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_WAIT_EXTERNAL_CLAIM_REF: Final = (
    "wait_for_external_bodyfree_claim_reintake_without_raw_evidence"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF: Final = (
    "repair_rdb_candidate_or_upstream_result_boundary_without_promotion"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF: Final = (
    "manual_hold_post_rdb08_unresolved_without_promotion"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF: Final = (
    "blocked_post_rdb08_candidate_intake_bodyfree_leak_or_promotion"
)

P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_DHR_OP05_BOUNDARY_REF: Final = (
    "dhr_op05_manual_handoff_boundary_design_candidate_without_call"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_RETRY_OR_START_REF: Final = (
    "retry_or_start_actual_local_only_review_route_candidate_without_execution"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_WAIT_EXTERNAL_CLAIM_REF: Final = (
    "external_bodyfree_claim_reintake_wait_candidate_without_raw_evidence"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_REPAIR_BOUNDARY_REF: Final = (
    "repair_rdb_candidate_or_upstream_result_boundary_candidate_without_promotion"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_MANUAL_HOLD_REF: Final = (
    "manual_hold_unresolved_post_rdb08_stop_without_promotion"
)
P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_BLOCKED_REF: Final = (
    "blocked_post_rdb08_bodyfree_leak_promotion_or_autorun_stop"
)

P7_R54_AHR_POST_RDB08_NCI_DHR_OP05_EXISTING_OPERATION_REF: Final = (
    "DHR-OP05_bodyfree_leak_promotion_claim_DMD_compatibility_preflight_scan"
)
P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_NEXT_DESIGN_TARGET_MATERIALIZED_REF: Final = (
    "NCI_STATUS_NEXT_DESIGN_TARGET_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_STOP_MATERIALIZED_REF: Final = (
    "NCI_STATUS_STOP_MATERIALIZED_FOR_UNRESOLVED_OR_BLOCKED_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_REPAIR_REQUIRED_REF: Final = (
    "NCI_STATUS_REPAIR_REQUIRED_FOR_NEXT_DESIGN_TARGET_OR_STOP_MATERIALIZATION_INPUTS"
)
P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "NCI_STATUS_BLOCKED_OP04_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_RDB08_NCI_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_NEXT_DESIGN_TARGET_MATERIALIZED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_STOP_MATERIALIZED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF: Final = (
    "NCI_STATUS_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD_PASSED"
)
P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_REPAIR_REQUIRED_REF: Final = (
    "NCI_STATUS_REPAIR_REQUIRED_FOR_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_INPUTS"
)
P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "NCI_STATUS_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD"
)
P7_R54_AHR_POST_RDB08_NCI_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)

P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF: Final = (
    "NCI_STATUS_SELECTED_REGRESSION_COMPILEALL_VALIDATION_PLAN_RECORDED"
)
P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF: Final = (
    "NCI_STATUS_WAITING_FOR_OP05_GUARD_BEFORE_VALIDATION_PLAN"
)
P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_REPAIR_REQUIRED_REF: Final = (
    "NCI_STATUS_REPAIR_REQUIRED_FOR_VALIDATION_PLAN_INPUTS"
)
P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "NCI_STATUS_BLOCKED_VALIDATION_PLAN_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_RDB08_NCI_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)

P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_HANDOFF_ENVELOPE_DRAFT_REF: Final = (
    "NCI_STATUS_HANDOFF_ENVELOPE_DRAFT_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF: Final = (
    "NCI_STATUS_STOP_ENVELOPE_DRAFT_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_REPAIR_REQUIRED_REF: Final = (
    "NCI_STATUS_REPAIR_REQUIRED_FOR_HANDOFF_OR_STOP_ENVELOPE_INPUTS"
)
P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "NCI_STATUS_BLOCKED_HANDOFF_OR_STOP_ENVELOPE_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_RDB08_NCI_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_HANDOFF_ENVELOPE_DRAFT_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_RDB08_NCI_OP07_HANDOFF_ENVELOPE_KIND_REF: Final = (
    "bodyfree_handoff_envelope_draft_without_execution"
)
P7_R54_AHR_POST_RDB08_NCI_OP07_STOP_ENVELOPE_KIND_REF: Final = (
    "bodyfree_stop_envelope_draft_without_promotion"
)

P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF: Final = (
    "NCI_OP08_BODYFREE_SELECTED_CANDIDATE_INTAKE_CLOSED_STOPPED"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF: Final = (
    "NCI_OP08_WAITING_FOR_RDB08_OR_NCI_INPUT_REFS"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_REPAIR_REQUIRED_REF: Final = (
    "NCI_OP08_REPAIR_REQUIRED_FOR_SELECTED_CANDIDATE_INTAKE_INPUTS"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "NCI_OP08_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_WAIT_REF: Final = (
    "wait_for_nci_op07_handoff_or_stop_envelope_and_bodyfree_result_memo_refs_before_closure"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_REPAIR_REF: Final = (
    "repair_nci_selected_candidate_intake_closure_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_BLOCKED_REF: Final = (
    "blocked_nci_op08_bodyfree_result_memo_leak_promotion_or_autorun"
)

P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op00_op01_20260706.py",
    "tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op02_op03_20260706.py",
    "tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op04_op05_20260706.py",
    "tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op06_op07_20260706.py",
    "tests/test_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_result_20260706.py",
)
P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op00_op01_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op02_op03_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_op05_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op06_op07_20260705.py",
    "tests/test_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op08_result_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705.py",
    "tests/test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_result_20260705.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op04_op05_20260704.py",
    "tests/test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op06_op07_20260704.py",
)
P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_20260706.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "run_nci_target_tests_op00_to_op08",
    "run_selected_rdb_dri_dhr_regression_without_full_backend_green_claim",
    "run_compileall_for_nci_rdb_dri_dhr_helper_files",
)

P7_R54_AHR_POST_RDB08_NCI_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_design_target_ref", "boundary_prefix_ref", "boundary_prefix_meaning_ref",
    "expected_from_rdb08_ref", "expected_next_required_step_ref", "not_stage_refs", "not_stage_ref_count",
    "support_material_refs", "support_material_ref_count", "local_received_zip_refs", "local_received_zip_ref_count",
    "body_free", "nci_op00_scope_confirmed", "nci_op00_no_execution_boundary_confirmed", "nci_op00_no_touch_boundary_confirmed", "nci_op00_no_promotion_boundary_confirmed",
    "source_mode_local_received_zip_only_confirmed", "github_connection_check_not_required_by_mash_instruction", "github_connection_check_performed",
    "nci_op00_does_not_intake_rdb_op08_result_memo", "nci_op00_does_not_execute_selected_next_stage_candidate", "nci_op00_does_not_call_dhr_op05", "nci_op00_does_not_start_p8_question_design", "nci_op00_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary",
    "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS,
)
P7_R54_AHR_POST_RDB08_NCI_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_schema_version", "op00_material_ref", "op00_next_required_step", "op00_scope_confirmed", "op00_no_execution_boundary_confirmed", "op00_no_touch_boundary_confirmed", "op00_no_promotion_boundary_confirmed", "op00_contract_valid",
    "rdb_op08_material_present", "rdb_op08_contract_valid", "rdb_op08_schema_version", "rdb_op08_operation_step_ref", "rdb_op08_material_ref",
    "rdb_op08_status_ref", "bodyfree_result_manual_decision_memo_closure_status_ref", "rdb_op08_closed_bodyfree_stopped", "rdb_op08_waiting_for_op03_op04_op05_or_validation_refs", "rdb_op08_repair_required_for_result_manual_decision_closure_inputs", "rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun",
    "rdb_selected_status_ref", "mrb_selected_branch_ref", "dhr_op04_result_status_ref", "decision_lane_ref", "manual_decision_material_ref", "manual_decision_material_kind_ref", "manual_decision_material_present",
    "selected_next_stage_candidate_ref", "selected_next_stage_candidate_kind_ref", "selected_next_stage_candidate_not_executed", "rdb_op08_next_required_step_ref", "allowed_rdb_candidate_kind_refs", "allowed_rdb_candidate_kind_ref_count",
    "rdb_target_green_confirmed", "selected_regression_green_confirmed", "compileall_green_confirmed", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "rdb_op08_closure_is_not_candidate_execution", "rdb_op08_closure_is_not_dhr_op05_call", "rdb_op08_closure_is_not_dhr_op06_call", "rdb_op08_closure_is_not_dmd_or_r52_execution", "rdb_op08_closure_is_not_p8_start", "rdb_op08_closure_is_not_p7_complete", "rdb_op08_closure_is_not_release_ready",
    "rdb_op08_selected_candidate_not_executed_preserved", "rdb_op08_dhr_op05_not_called", "rdb_op08_dhr_op06_not_called", "rdb_op08_dmd_r52_not_executed", "rdb_op08_p5_p6_p8_p7_release_not_started", "rdb_op08_p8_question_design_not_started", "rdb_op08_p8_question_implementation_not_started",
    "rdb_op08_input_forbidden_payload_key_path_refs", "rdb_op08_input_forbidden_payload_key_path_count", "rdb_op08_input_body_like_value_path_refs", "rdb_op08_input_body_like_value_path_count", "rdb_op08_input_promotion_claim_refs", "rdb_op08_input_promotion_claim_ref_count",
    "nci_op01_status_ref", "rdb08_result_memo_closure_intake_status_ref", "nci_op01_allowed_status_refs", "nci_op01_allowed_status_ref_count",
    "nci_op01_ready_for_candidate_shape_validation", "nci_op01_waiting_for_rdb08_closure", "nci_op01_repair_required", "nci_op01_bodyfree_leak_promotion_or_autorun_blocked",
    "nci_op01_reason_refs", "nci_op01_reason_ref_count", "nci_op01_blocker_refs", "nci_op01_blocker_ref_count",
    "nci_op01_does_not_validate_candidate_shape", "nci_op01_does_not_resolve_selected_candidate_lane", "nci_op01_does_not_materialize_next_design_target_or_stop", "nci_op01_does_not_execute_selected_next_stage_candidate",
    "nci_op01_does_not_recall_dhr_op04", "nci_op01_does_not_call_dhr_op05", "nci_op01_does_not_call_dhr_op06", "nci_op01_does_not_execute_dmd_r52_or_release", "nci_op01_does_not_start_p5_p6_p8_p7_or_release", "nci_op01_does_not_change_api_db_rn_runtime_response_key", "nci_op01_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_RDB08_NCI_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_schema_version", "op01_material_ref", "op01_status_ref", "op01_next_required_step", "op01_contract_valid", "op01_ready_for_candidate_shape_validation",
    "rdb08_candidate_ref", "rdb08_candidate_kind_ref", "rdb08_selected_status_ref", "rdb08_decision_lane_ref", "rdb08_next_required_step_ref", "rdb08_manual_decision_material_ref", "rdb08_manual_decision_material_present",
    "candidate_shape_valid", "candidate_kind_allowed", "candidate_ref_allowed", "candidate_ref_matches_kind", "candidate_status_allowed", "candidate_status_matches_kind_ref_lane", "candidate_not_executed_confirmed", "candidate_next_required_step_matches_ref", "candidate_decision_lane_present", "candidate_manual_decision_material_present_when_required", "p8_question_candidate_detected",
    "candidate_shape_status_ref", "nci_op02_status_ref", "nci_op02_allowed_status_refs", "nci_op02_allowed_status_ref_count", "allowed_rdb_candidate_kind_refs", "allowed_rdb_candidate_kind_ref_count", "allowed_rdb_candidate_ref_refs", "allowed_rdb_candidate_ref_ref_count",
    "candidate_shape_reason_refs", "candidate_shape_reason_ref_count", "candidate_shape_blocker_refs", "candidate_shape_blocker_ref_count", "op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count", "op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count", "op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count",
    "nci_op02_ready_for_lane_resolution", "nci_op02_repair_required_for_selected_candidate_shape", "nci_op02_bodyfree_leak_promotion_or_p8_blocked",
    "nci_op02_does_not_resolve_selected_candidate_lane", "nci_op02_does_not_materialize_next_design_target_or_stop", "nci_op02_does_not_execute_selected_next_stage_candidate", "nci_op02_does_not_call_dhr_op05", "nci_op02_does_not_start_p8_question_design", "nci_op02_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RDB08_NCI_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_schema_version", "op02_material_ref", "op02_status_ref", "op02_next_required_step", "op02_contract_valid", "op02_candidate_shape_valid",
    "rdb08_candidate_ref", "rdb08_candidate_kind_ref", "rdb08_selected_status_ref", "rdb08_decision_lane_ref", "rdb08_next_required_step_ref",
    "candidate_lane_consistency_checked", "candidate_lane_consistent", "candidate_lane_consistency_reason_refs", "candidate_lane_consistency_reason_ref_count", "candidate_lane_consistency_blocker_refs", "candidate_lane_consistency_blocker_ref_count",
    "nci_status_ref", "nci_lane_ref", "nci_op03_allowed_status_refs", "nci_op03_allowed_status_ref_count", "nci_allowed_lane_refs", "nci_allowed_lane_ref_count",
    "selected_next_design_or_stop_ref", "selected_next_design_or_stop_kind_ref", "selected_next_design_or_stop_not_executed", "selected_next_stage_candidate_not_executed_preserved", "exactly_one_nci_lane_selected",
    "dhr_op05_design_target_candidate_present", "retry_or_start_route_candidate_present", "external_claim_wait_candidate_present", "repair_route_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here", "p8_question_substitution_allowed", "question_text_materialized",
    "nci_op03_does_not_execute_selected_next_stage_candidate", "nci_op03_does_not_call_dhr_op05", "nci_op03_does_not_start_actual_review", "nci_op03_does_not_request_raw_evidence", "nci_op03_does_not_execute_repair", "nci_op03_does_not_start_p8_question_design", "nci_op03_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RDB08_NCI_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_next_required_step", "op03_contract_valid", "op03_candidate_lane_consistent", "op03_exactly_one_nci_lane_selected",
    "candidate_from_rdb08_ref", "candidate_from_rdb08_kind_ref", "candidate_from_rdb08_selected_status_ref", "candidate_from_rdb08_decision_lane_ref",
    "nci_status_ref", "nci_lane_ref", "nci_op04_status_ref", "next_design_target_or_stop_materialization_status_ref", "nci_op04_allowed_status_refs", "nci_op04_allowed_status_ref_count",
    "next_design_target_or_stop_ref", "next_design_target_or_stop_kind_ref", "next_design_target_or_stop_not_executed", "next_design_target_materialized", "stop_materialized", "handoff_candidate_materialized", "stop_candidate_materialized",
    "dhr_op05_existing_operation_ref", "dhr_op05_design_target_candidate_present", "retry_or_start_route_candidate_present", "external_claim_wait_candidate_present", "repair_route_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present",
    "dhr_op05_allowed_meaning_ref", "retry_or_start_allowed_meaning_ref", "waiting_claim_allowed_meaning_ref", "repair_allowed_meaning_ref", "stop_allowed_meaning_ref",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here", "p8_question_design_started_here", "p8_question_implementation_started_here", "question_text_materialized", "p8_question_substitution_allowed",
    "op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count", "op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count", "op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count",
    "nci_op04_reason_refs", "nci_op04_reason_ref_count", "nci_op04_blocker_refs", "nci_op04_blocker_ref_count",
    "nci_op04_does_not_execute_selected_next_stage_candidate", "nci_op04_does_not_call_dhr_op05", "nci_op04_does_not_start_actual_review", "nci_op04_does_not_request_raw_evidence", "nci_op04_does_not_execute_repair", "nci_op04_does_not_start_p8_question_design", "nci_op04_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RDB08_NCI_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_next_required_step", "op04_contract_valid", "op04_next_design_target_or_stop_not_executed",
    "selected_nci_status_ref", "selected_nci_lane_ref", "selected_next_design_target_or_stop_ref", "selected_next_design_target_or_stop_kind_ref", "selected_next_design_target_or_stop_not_executed",
    "nci_op05_guard_status_ref", "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref", "nci_op05_allowed_status_refs", "nci_op05_allowed_status_ref_count",
    "bodyfree_guard_passed", "no_touch_guard_passed", "no_promotion_guard_passed", "no_auto_execution_guard_passed", "selected_candidate_not_executed_guard_passed", "op04_contract_guard_passed",
    "api_db_rn_runtime_response_key_or_p8_question_touch_detected", "api_db_rn_runtime_response_key_or_p8_question_touch_blocked",
    "forbidden_payload_key_path_refs", "forbidden_payload_key_path_count", "body_like_value_path_refs", "body_like_value_path_count", "promotion_claim_refs", "promotion_claim_ref_count", "no_touch_mutation_path_refs", "no_touch_mutation_path_count",
    "guard_reason_refs", "guard_reason_ref_count", "guard_blocker_refs", "guard_blocker_ref_count",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here", "p8_question_design_started_here", "p8_question_implementation_started_here", "question_text_materialized", "p8_question_substitution_allowed",
    "nci_op05_does_not_execute_selected_next_stage_candidate", "nci_op05_does_not_call_dhr_op05", "nci_op05_does_not_start_actual_review", "nci_op05_does_not_request_raw_evidence", "nci_op05_does_not_execute_repair", "nci_op05_does_not_start_p8_question_design", "nci_op05_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)



P7_R54_AHR_POST_RDB08_NCI_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_next_required_step", "op05_contract_valid", "op05_guard_passed",
    "selected_nci_status_ref", "selected_nci_lane_ref", "selected_next_design_target_or_stop_ref", "selected_next_design_target_or_stop_kind_ref", "selected_next_design_target_or_stop_not_executed",
    "nci_op06_validation_plan_status_ref", "selected_regression_compileall_validation_plan_status_ref", "nci_op06_allowed_status_refs", "nci_op06_allowed_status_ref_count",
    "target_test_refs", "target_test_ref_count", "selected_regression_test_refs", "selected_regression_test_ref_count", "compileall_target_refs", "compileall_target_ref_count", "validation_command_summary_refs", "validation_command_summary_ref_count",
    "target_tests_planned", "selected_regression_planned", "compileall_planned", "op06_validation_plan_recorded", "op06_does_not_execute_validation_commands",
    "full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "actual_review_execution_confirmed",
    "op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count", "op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count", "op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count", "op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count",
    "nci_op06_reason_refs", "nci_op06_reason_ref_count", "nci_op06_blocker_refs", "nci_op06_blocker_ref_count",
    "nci_op06_does_not_execute_selected_next_stage_candidate", "nci_op06_does_not_call_dhr_op05", "nci_op06_does_not_call_dhr_op06", "nci_op06_does_not_execute_dmd_r52_or_release", "nci_op06_does_not_start_actual_review", "nci_op06_does_not_start_p8_question_design", "nci_op06_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_RDB08_NCI_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_next_required_step", "op06_contract_valid", "op06_validation_plan_recorded",
    "nci_op07_status_ref", "handoff_or_stop_envelope_status_ref", "nci_op07_allowed_status_refs", "nci_op07_allowed_status_ref_count",
    "handoff_or_stop_envelope_ref", "handoff_or_stop_envelope_kind_ref", "handoff_or_stop_envelope_bodyfree", "handoff_envelope_present", "stop_envelope_present",
    "selected_nci_status_ref", "selected_nci_lane_ref", "selected_next_design_or_stop_ref", "selected_next_design_or_stop_kind_ref", "selected_next_design_or_stop_not_executed",
    "dhr_op05_design_target_candidate_present", "retry_or_start_route_candidate_present", "external_claim_wait_candidate_present", "repair_route_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present",
    "op05_guard_passed", "op06_target_tests_planned", "op06_selected_regression_planned", "op06_compileall_planned", "nci_op07_ready_for_op08",
    "validation_command_summary_refs", "validation_command_summary_ref_count",
    "op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count", "op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count", "op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count", "op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count",
    "nci_op07_reason_refs", "nci_op07_reason_ref_count", "nci_op07_blocker_refs", "nci_op07_blocker_ref_count",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here", "p8_question_design_started_here", "p8_question_implementation_started_here", "question_text_materialized", "p8_question_substitution_allowed",
    "nci_op07_does_not_execute_handoff_or_stop_envelope", "nci_op07_does_not_execute_selected_next_stage_candidate", "nci_op07_does_not_call_dhr_op05", "nci_op07_does_not_start_actual_review", "nci_op07_does_not_request_raw_evidence", "nci_op07_does_not_execute_repair", "nci_op07_does_not_start_p8_question_design", "nci_op07_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)



def _clean_ref(value: Any, *, default: str = "missing", max_length: int = 240) -> str:
    return clean_identifier(value, default=default, max_length=max_length)


def _safe_review_session_id(value: Any = None) -> str:
    return _clean_ref(value, default=P7_R54_AHR_POST_RDB08_NCI_DEFAULT_REVIEW_SESSION_ID, max_length=180)


P7_R54_AHR_POST_RDB08_NCI_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_material_present", "op04_contract_valid", "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_next_required_step",
    "op05_guard_present", "op05_contract_valid", "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_next_required_step", "op05_guard_passed",
    "op06_validation_plan_present", "op06_contract_valid", "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_next_required_step", "op06_validation_plan_recorded",
    "op07_envelope_present", "op07_contract_valid", "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_next_required_step", "op07_ready_for_op08",
    "op07_handoff_or_stop_envelope_ref", "op07_handoff_or_stop_envelope_kind_ref", "op07_handoff_or_stop_envelope_bodyfree", "op07_handoff_envelope_present", "op07_stop_envelope_present",
    "validation_summary_bodyfree_present", "validation_summary_bodyfree_accepted", "validation_summary_bodyfree_ref",
    "validation_summary_forbidden_payload_key_path_refs", "validation_summary_forbidden_payload_key_path_count", "validation_summary_body_like_value_path_refs", "validation_summary_body_like_value_path_count", "validation_summary_promotion_claim_refs", "validation_summary_promotion_claim_ref_count", "validation_summary_no_touch_mutation_path_refs", "validation_summary_no_touch_mutation_path_count",
    "result_memo_bodyfree_present", "result_memo_bodyfree_accepted", "result_memo_bodyfree_ref",
    "result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count", "result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count", "result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count", "result_memo_no_touch_mutation_path_refs", "result_memo_no_touch_mutation_path_count",
    "op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count", "op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count", "op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count", "op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count",
    "nci_op08_status_ref", "bodyfree_selected_candidate_intake_closure_status_ref", "nci_op08_allowed_status_refs", "nci_op08_allowed_status_ref_count",
    "nci_op08_closed_bodyfree_stopped", "nci_op08_waiting_for_input_refs", "nci_op08_repair_required", "nci_op08_blocked_bodyfree_promotion_autorun",
    "nci_op08_reason_refs", "nci_op08_reason_ref_count", "nci_op08_blocker_refs", "nci_op08_blocker_ref_count",
    "selected_nci_status_ref", "selected_nci_lane_ref", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_next_design_or_stop_ref", "selected_next_design_or_stop_kind_ref", "selected_next_design_or_stop_not_executed",
    "rdb08_selected_next_stage_candidate_ref", "rdb08_selected_next_stage_candidate_kind_ref", "rdb08_selected_next_stage_candidate_not_executed", "rdb08_selected_status_ref", "rdb08_decision_lane_ref",
    "dhr_op05_design_target_candidate_present", "retry_or_start_route_candidate_present", "external_claim_wait_candidate_present", "repair_route_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present",
    "validation_command_summary_refs", "validation_command_summary_ref_count", "target_test_refs", "target_test_ref_count", "selected_regression_test_refs", "selected_regression_test_ref_count", "compileall_target_refs", "compileall_target_ref_count",
    "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref", "combined_run_status_ref", "nci_target_green_confirmed", "selected_regression_green_confirmed", "compileall_green_confirmed", "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "full_backend_green_claim_not_made_here", "rn_green_claim_not_made_here",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started",
    "nci_op08_does_not_execute_handoff_or_stop_envelope", "nci_op08_does_not_execute_selected_next_stage_candidate", "nci_op08_does_not_call_dhr_op05", "nci_op08_does_not_call_dhr_op06", "nci_op08_does_not_execute_dmd_r52_or_release", "nci_op08_does_not_start_actual_review", "nci_op08_does_not_request_raw_evidence", "nci_op08_does_not_execute_repair", "nci_op08_does_not_start_p5_p6_p8_p7_or_release", "nci_op08_does_not_materialize_p8_question_spec", "nci_op08_does_not_change_api_db_rn_runtime_response_key",
    "p8_question_substitution_allowed", "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count", "implemented_steps", "not_yet_implemented_steps", "next_required_step",
    "public_contract", "nci_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


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
    return {key: False for key in P7_R54_AHR_POST_RDB08_NCI_NO_TOUCH_CONTRACT_KEYS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_RDB08_NCI_BODY_FREE_MARKER_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS}


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS}


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
            if key_text in P7_R54_AHR_POST_RDB08_NCI_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            paths.extend(_scan_forbidden_payload_key_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_forbidden_payload_key_paths(child, path=f"{path}[{index}]"))
    return paths


def _scan_body_like_value_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    suspect_exact_or_token_refs = (
        "raw_input", "input_body", "comment_text", "comment_text_body",
        "returned_surface_body", "body_full_packet", "body_full_packet_body",
        "reviewer_free_text", "reviewer_note_body", "question_text",
        "draft_question_text", "answer_text", "private_user_dictionary_text",
        "absolute_path", "relative_path", "file_path", "local_path",
        "input_hash", "body_hash", "sha256", "terminal_output",
        "stdout", "stderr", "traceback",
    )
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_RDB08_NCI_FORBIDDEN_PAYLOAD_KEY_REFS:
                paths.append(child_path)
            elif isinstance(child, str) and len(child.strip()) > 0 and any(token in key_lower for token in suspect_exact_or_token_refs):
                paths.append(child_path)
            elif (
                child is True
                and any(token in key_lower for token in suspect_exact_or_token_refs)
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
            if key_text in P7_R54_AHR_POST_RDB08_NCI_PROMOTION_CLAIM_FIELD_REFS and child is True:
                refs.append(child_path)
            refs.extend(_scan_promotion_claim_refs(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            refs.extend(_scan_promotion_claim_refs(child, path=f"{path}[{index}]"))
    return refs


def _assert_false_mapping(data: Mapping[str, Any], *, field: str, source: str) -> None:
    mapping = data.get(field)
    if not isinstance(mapping, Mapping):
        raise ValueError(f"{source} {field} must be a mapping")
    true_keys = [str(key) for key, value in mapping.items() if value is True]
    if true_keys:
        raise ValueError(f"{source} {field} must keep false markers: {true_keys[:6]}")


def _assert_public_contract_false(data: Mapping[str, Any], *, source: str) -> None:
    if data.get("public_contract") != public_contract_flags():
        raise ValueError(f"{source} public contract changed")


def _assert_base_bodyfree_boundary(data: Mapping[str, Any], *, schema_version: str, operation_step_ref: str, source: str) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_R54_AHR_POST_RDB08_NCI_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_RDB08_NCI_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_RDB08_NCI_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("operation_step_ref") != operation_step_ref or data.get("policy_section") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git connection flags changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must stay body-free")
    _assert_public_contract_false(data, source=source)
    _assert_false_mapping(data, field="nci_no_touch_contract", source=source)
    _assert_false_mapping(data, field="body_free_markers", source=source)
    for key in P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")
    if any(key in P7_R54_AHR_POST_RDB08_NCI_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")


def _op00_contract_valid(op00: Mapping[str, Any] | None) -> bool:
    if not isinstance(op00, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract(op00) is True
    except ValueError:
        return False


def _rdb_op08_contract_valid(op08: Mapping[str, Any] | None) -> bool:
    if not isinstance(op08, Mapping):
        return False
    try:
        return rdb.assert_p7_r54_ahr_post_mrb08_rdb_op08_bodyfree_result_manual_decision_memo_closure_contract(op08) is True
    except ValueError:
        return False


def _op01_status_reason_blocker_next(
    *,
    op00_valid: bool,
    op08_present: bool,
    op08_contract_valid: bool,
    op08_status_ref: str,
    op08_closed: bool,
    op08_waiting: bool,
    op08_repair: bool,
    op08_blocked: bool,
    candidate_ref: str,
    candidate_kind_ref: str,
    candidate_not_executed: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("rdb_op08_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("rdb_op08_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("rdb_op08_input_promotion_or_autorun_claim_detected")
    if op08_blocked or op08_status_ref == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("rdb_op08_status_bodyfree_leak_promotion_or_autorun_blocked")
    if blockers:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["rdb_op08_result_memo_failed_bodyfree_no_promotion_boundary_before_nci_op02"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_RDB08_INTAKE_REF,
        )
    if not op00_valid:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF,
            ["nci_op00_contract_invalid_before_rdb_op08_intake"],
            ["nci_op00_contract_invalid"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF,
        )
    if not op08_present:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_WAITING_FOR_RDB08_CLOSURE_REF,
            ["rdb_op08_result_memo_closure_not_provided_yet"],
            ["rdb_op08_result_memo_closure_missing"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_RDB08_CLOSURE_REF,
        )
    if not op08_contract_valid:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF,
            ["rdb_op08_result_memo_closure_contract_repair_required_before_nci_op02"],
            ["rdb_op08_result_memo_closure_contract_invalid"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF,
        )
    if op08_waiting or op08_status_ref == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_WAITING_FOR_RDB08_CLOSURE_REF,
            ["rdb_op08_result_memo_closure_waiting_before_selected_candidate_shape_validation"],
            ["rdb_op08_waiting_for_op03_op04_op05_or_validation_refs"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_RDB08_CLOSURE_REF,
        )
    if op08_repair or op08_status_ref == rdb.P7_R54_AHR_POST_MRB08_RDB_OP08_STATUS_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF,
            ["rdb_op08_result_memo_closure_repair_required_before_nci_op02"],
            ["rdb_op08_repair_required_for_result_manual_decision_closure_inputs"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF,
        )
    if not candidate_not_executed:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF,
            ["rdb_op08_selected_candidate_non_execution_boundary_not_preserved"],
            ["selected_next_stage_candidate_not_executed_missing_or_false"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF,
        )
    if op08_closed and candidate_ref and candidate_kind_ref:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF,
            ["rdb_op08_closed_bodyfree_candidate_refs_ready_for_nci_op02_shape_validation"],
            [],
            P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF,
        ["rdb_op08_result_memo_closure_incomplete_before_selected_candidate_shape_validation"],
        ["rdb_op08_selected_candidate_ref_or_kind_missing"],
        P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_RDB08_INTAKE_REF,
    )


def build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build NCI-OP00 body-free scope / no-execution / no-promotion refreeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb08_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_RDB08_NCI_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_RDB08_NCI_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_RDB08_NCI_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_RDB08_NCI_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_rdb08_ref": P7_R54_AHR_POST_RDB08_NCI_EXPECTED_FROM_RDB08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_RDB08_NCI_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "not_stage_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_STAGE_REFS),
        "not_stage_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_STAGE_REFS),
        "support_material_refs": list(P7_R54_AHR_POST_RDB08_NCI_SUPPORT_MATERIAL_REFS),
        "support_material_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_SUPPORT_MATERIAL_REFS),
        "local_received_zip_refs": dict(P7_R54_AHR_POST_RDB08_NCI_LOCAL_RECEIVED_ZIP_REFS),
        "local_received_zip_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_LOCAL_RECEIVED_ZIP_REFS),
        "body_free": True,
        "nci_op00_scope_confirmed": True,
        "nci_op00_no_execution_boundary_confirmed": True,
        "nci_op00_no_touch_boundary_confirmed": True,
        "nci_op00_no_promotion_boundary_confirmed": True,
        "source_mode_local_received_zip_only_confirmed": True,
        "github_connection_check_not_required_by_mash_instruction": True,
        "github_connection_check_performed": False,
        "nci_op00_does_not_intake_rdb_op08_result_memo": True,
        "nci_op00_does_not_execute_selected_next_stage_candidate": True,
        "nci_op00_does_not_call_dhr_op05": True,
        "nci_op00_does_not_start_p8_question_design": True,
        "nci_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
    }


def assert_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert NCI-OP00 scope / no-execution / no-promotion refreeze contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP00_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP00")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_RDB08_NCI_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP00_STEP_REF,
        source="P7-R54-AHR-PostRDB08-NCI-OP00",
    )
    for key in (
        "nci_op00_scope_confirmed",
        "nci_op00_no_execution_boundary_confirmed",
        "nci_op00_no_touch_boundary_confirmed",
        "nci_op00_no_promotion_boundary_confirmed",
        "source_mode_local_received_zip_only_confirmed",
        "github_connection_check_not_required_by_mash_instruction",
        "nci_op00_does_not_intake_rdb_op08_result_memo",
        "nci_op00_does_not_execute_selected_next_stage_candidate",
        "nci_op00_does_not_call_dhr_op05",
        "nci_op00_does_not_start_p8_question_design",
        "nci_op00_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP00 required true boundary changed: {key}")
    if data.get("github_connection_check_performed") is not False:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 git check must stay unperformed")
    if data.get("boundary_prefix_ref") != P7_R54_AHR_POST_RDB08_NCI_BOUNDARY_PREFIX_REF:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 boundary prefix changed")
    if data.get("boundary_prefix_meaning_ref") != P7_R54_AHR_POST_RDB08_NCI_BOUNDARY_PREFIX_MEANING_REF:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 boundary prefix meaning changed")
    if data.get("expected_next_required_step_ref") != P7_R54_AHR_POST_RDB08_NCI_EXPECTED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 expected next step changed")
    for field, count_field in (
        ("not_stage_refs", "not_stage_ref_count"),
        ("support_material_refs", "support_material_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP00 {count_field} changed")
    if data.get("local_received_zip_ref_count") != len(data.get("local_received_zip_refs") or {}):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 local zip count changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 not-claimed refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP00 next step changed")
    return True


def build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake(
    *,
    scope_no_execution_no_promotion_refreeze_after_rdb_op08: Mapping[str, Any] | None = None,
    rdb_op08_bodyfree_result_memo_closure: Mapping[str, Any] | None = None,
    rdb_op08_bodyfree_result_manual_decision_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build NCI-OP01 body-free RDB-OP08 result memo closure intake material."""

    if rdb_op08_bodyfree_result_memo_closure is None and isinstance(rdb_op08_bodyfree_result_manual_decision_memo_closure, Mapping):
        rdb_op08_bodyfree_result_memo_closure = rdb_op08_bodyfree_result_manual_decision_memo_closure

    op00 = (
        scope_no_execution_no_promotion_refreeze_after_rdb_op08
        if isinstance(scope_no_execution_no_promotion_refreeze_after_rdb_op08, Mapping)
        else build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08(review_session_id=review_session_id)
    )
    op08_map = rdb_op08_bodyfree_result_memo_closure if isinstance(rdb_op08_bodyfree_result_memo_closure, Mapping) else {}
    op00_valid = _op00_contract_valid(op00)
    op08_present = isinstance(rdb_op08_bodyfree_result_memo_closure, Mapping)
    op08_contract_valid = _rdb_op08_contract_valid(op08_map if op08_present else None)

    forbidden_paths = _dedupe_clean_refs(
        _scan_forbidden_payload_key_paths(op08_map, path="rdb_op08_bodyfree_result_memo_closure"),
        max_length=340,
    )
    body_like_paths = _dedupe_clean_refs(
        _scan_body_like_value_paths(op08_map, path="rdb_op08_bodyfree_result_memo_closure"),
        max_length=340,
    )
    promotion_claims = _dedupe_clean_refs(
        _scan_promotion_claim_refs(op08_map, path="rdb_op08_bodyfree_result_memo_closure"),
        max_length=340,
    )

    op08_status_ref = _clean_ref(op08_map.get("rdb_op08_status_ref"), default="rdb_op08_status_missing", max_length=340)
    op08_closed = bool(op08_map.get("rdb_op08_closed_bodyfree_stopped") is True)
    op08_waiting = bool(op08_map.get("rdb_op08_waiting_for_op03_op04_op05_or_validation_refs") is True)
    op08_repair = bool(op08_map.get("rdb_op08_repair_required_for_result_manual_decision_closure_inputs") is True)
    op08_blocked = bool(op08_map.get("rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun") is True)
    candidate_ref = _clean_ref(op08_map.get("selected_next_stage_candidate_ref"), default="", max_length=360)
    candidate_kind_ref = _clean_ref(op08_map.get("selected_next_stage_candidate_kind_ref"), default="", max_length=360)
    candidate_not_executed = bool(op08_map.get("selected_next_stage_candidate_not_executed") is True)

    status_ref, reasons, blockers, next_required_step = _op01_status_reason_blocker_next(
        op00_valid=op00_valid,
        op08_present=op08_present,
        op08_contract_valid=op08_contract_valid,
        op08_status_ref=op08_status_ref,
        op08_closed=op08_closed,
        op08_waiting=op08_waiting,
        op08_repair=op08_repair,
        op08_blocked=op08_blocked,
        candidate_ref=candidate_ref,
        candidate_kind_ref=candidate_kind_ref,
        candidate_not_executed=candidate_not_executed,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF
    waiting = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_WAITING_FOR_RDB08_CLOSURE_REF
    repair = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_REPAIR_RDB08_INTAKE_REF
    blocked = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF

    session_id = _safe_review_session_id(review_session_id or op00.get("review_session_id") or op08_map.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op01_rdb08_bodyfree_result_memo_closure_intake_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_schema_version": _clean_ref(op00.get("schema_version"), default="nci_op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id"), default="nci_op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step"), default="nci_op00_next_step_missing", max_length=260),
        "op00_scope_confirmed": bool(op00.get("nci_op00_scope_confirmed") is True),
        "op00_no_execution_boundary_confirmed": bool(op00.get("nci_op00_no_execution_boundary_confirmed") is True),
        "op00_no_touch_boundary_confirmed": bool(op00.get("nci_op00_no_touch_boundary_confirmed") is True),
        "op00_no_promotion_boundary_confirmed": bool(op00.get("nci_op00_no_promotion_boundary_confirmed") is True),
        "op00_contract_valid": op00_valid,
        "rdb_op08_material_present": op08_present,
        "rdb_op08_contract_valid": op08_contract_valid,
        "rdb_op08_schema_version": _clean_ref(op08_map.get("schema_version"), default="rdb_op08_schema_missing", max_length=260),
        "rdb_op08_operation_step_ref": _clean_ref(op08_map.get("operation_step_ref"), default="rdb_op08_operation_step_missing", max_length=260),
        "rdb_op08_material_ref": _clean_ref(op08_map.get("material_id"), default="rdb_op08_material_missing", max_length=260),
        "rdb_op08_status_ref": op08_status_ref,
        "bodyfree_result_manual_decision_memo_closure_status_ref": _clean_ref(op08_map.get("bodyfree_result_manual_decision_memo_closure_status_ref"), default="bodyfree_result_manual_decision_memo_closure_status_missing", max_length=340),
        "rdb_op08_closed_bodyfree_stopped": op08_closed,
        "rdb_op08_waiting_for_op03_op04_op05_or_validation_refs": op08_waiting,
        "rdb_op08_repair_required_for_result_manual_decision_closure_inputs": op08_repair,
        "rdb_op08_blocked_bodyfree_result_memo_leak_promotion_or_autorun": op08_blocked,
        "rdb_selected_status_ref": _clean_ref(op08_map.get("rdb_selected_status_ref"), default="rdb_selected_status_missing", max_length=340),
        "mrb_selected_branch_ref": _clean_ref(op08_map.get("mrb_selected_branch_ref"), default="mrb_selected_branch_missing", max_length=340),
        "dhr_op04_result_status_ref": _clean_ref(op08_map.get("dhr_op04_result_status_ref"), default="dhr_op04_result_status_missing", max_length=340),
        "decision_lane_ref": _clean_ref(op08_map.get("decision_lane_ref"), default="decision_lane_missing", max_length=340),
        "manual_decision_material_ref": _clean_ref(op08_map.get("manual_decision_material_ref"), default="manual_decision_material_missing", max_length=340),
        "manual_decision_material_kind_ref": _clean_ref(op08_map.get("manual_decision_material_kind_ref"), default="manual_decision_material_kind_missing", max_length=340),
        "manual_decision_material_present": bool(op08_map.get("manual_decision_material_present") is True),
        "selected_next_stage_candidate_ref": candidate_ref or "selected_next_stage_candidate_missing",
        "selected_next_stage_candidate_kind_ref": candidate_kind_ref or "selected_next_stage_candidate_kind_missing",
        "selected_next_stage_candidate_not_executed": candidate_not_executed,
        "rdb_op08_next_required_step_ref": _clean_ref(op08_map.get("next_required_step"), default="rdb_op08_next_required_step_missing", max_length=360),
        "allowed_rdb_candidate_kind_refs": list(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS),
        "allowed_rdb_candidate_kind_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS),
        "rdb_target_green_confirmed": bool(op08_map.get("rdb_target_green_confirmed") is True),
        "selected_regression_green_confirmed": bool(op08_map.get("selected_regression_green_confirmed") is True),
        "compileall_green_confirmed": bool(op08_map.get("compileall_green_confirmed") is True),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "rdb_op08_closure_is_not_candidate_execution": True,
        "rdb_op08_closure_is_not_dhr_op05_call": True,
        "rdb_op08_closure_is_not_dhr_op06_call": True,
        "rdb_op08_closure_is_not_dmd_or_r52_execution": True,
        "rdb_op08_closure_is_not_p8_start": True,
        "rdb_op08_closure_is_not_p7_complete": True,
        "rdb_op08_closure_is_not_release_ready": True,
        "rdb_op08_selected_candidate_not_executed_preserved": candidate_not_executed,
        "rdb_op08_dhr_op05_not_called": bool(op08_map.get("dhr_op05_not_called") is True),
        "rdb_op08_dhr_op06_not_called": bool(op08_map.get("dhr_op06_not_called") is True),
        "rdb_op08_dmd_r52_not_executed": bool(op08_map.get("dmd_r52_not_executed") is True),
        "rdb_op08_p5_p6_p8_p7_release_not_started": bool(op08_map.get("p5_p6_p8_p7_release_not_started") is True),
        "rdb_op08_p8_question_design_not_started": bool(op08_map.get("p8_question_design_not_started") is True),
        "rdb_op08_p8_question_implementation_not_started": bool(op08_map.get("p8_question_implementation_not_started") is True),
        "rdb_op08_input_forbidden_payload_key_path_refs": forbidden_paths,
        "rdb_op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "rdb_op08_input_body_like_value_path_refs": body_like_paths,
        "rdb_op08_input_body_like_value_path_count": len(body_like_paths),
        "rdb_op08_input_promotion_claim_refs": promotion_claims,
        "rdb_op08_input_promotion_claim_ref_count": len(promotion_claims),
        "nci_op01_status_ref": status_ref,
        "rdb08_result_memo_closure_intake_status_ref": status_ref,
        "nci_op01_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP01_ALLOWED_STATUS_REFS),
        "nci_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP01_ALLOWED_STATUS_REFS),
        "nci_op01_ready_for_candidate_shape_validation": ready,
        "nci_op01_waiting_for_rdb08_closure": waiting,
        "nci_op01_repair_required": repair,
        "nci_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "nci_op01_reason_refs": reasons,
        "nci_op01_reason_ref_count": len(reasons),
        "nci_op01_blocker_refs": blockers,
        "nci_op01_blocker_ref_count": len(blockers),
        "nci_op01_does_not_validate_candidate_shape": True,
        "nci_op01_does_not_resolve_selected_candidate_lane": True,
        "nci_op01_does_not_materialize_next_design_target_or_stop": True,
        "nci_op01_does_not_execute_selected_next_stage_candidate": True,
        "nci_op01_does_not_recall_dhr_op04": True,
        "nci_op01_does_not_call_dhr_op05": True,
        "nci_op01_does_not_call_dhr_op06": True,
        "nci_op01_does_not_execute_dmd_r52_or_release": True,
        "nci_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "nci_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "nci_op01_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert NCI-OP01 RDB-OP08 body-free result memo closure intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP01_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP01")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_RDB08_NCI_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF,
        source="P7-R54-AHR-PostRDB08-NCI-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_RDB08_NCI_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 OP00 schema version changed")
    if data.get("op00_contract_valid") is True and data.get("op00_next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 OP00 next step changed")
    if data.get("rdb08_result_memo_closure_intake_status_ref") != data.get("nci_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 status alias changed")
    if tuple(data.get("nci_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 allowed status refs changed")
    if tuple(data.get("allowed_rdb_candidate_kind_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 allowed candidate kinds changed")
    for key in (
        "rdb_op08_closure_is_not_candidate_execution",
        "rdb_op08_closure_is_not_dhr_op05_call",
        "rdb_op08_closure_is_not_dhr_op06_call",
        "rdb_op08_closure_is_not_dmd_or_r52_execution",
        "rdb_op08_closure_is_not_p8_start",
        "rdb_op08_closure_is_not_p7_complete",
        "rdb_op08_closure_is_not_release_ready",
        "nci_op01_does_not_validate_candidate_shape",
        "nci_op01_does_not_resolve_selected_candidate_lane",
        "nci_op01_does_not_materialize_next_design_target_or_stop",
        "nci_op01_does_not_execute_selected_next_stage_candidate",
        "nci_op01_does_not_recall_dhr_op04",
        "nci_op01_does_not_call_dhr_op05",
        "nci_op01_does_not_call_dhr_op06",
        "nci_op01_does_not_execute_dmd_r52_or_release",
        "nci_op01_does_not_start_p5_p6_p8_p7_or_release",
        "nci_op01_does_not_change_api_db_rn_runtime_response_key",
        "nci_op01_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP01 required true boundary changed: {key}")
    for field, count_field in (
        ("allowed_rdb_candidate_kind_refs", "allowed_rdb_candidate_kind_ref_count"),
        ("rdb_op08_input_forbidden_payload_key_path_refs", "rdb_op08_input_forbidden_payload_key_path_count"),
        ("rdb_op08_input_body_like_value_path_refs", "rdb_op08_input_body_like_value_path_count"),
        ("rdb_op08_input_promotion_claim_refs", "rdb_op08_input_promotion_claim_ref_count"),
        ("nci_op01_reason_refs", "nci_op01_reason_ref_count"),
        ("nci_op01_blocker_refs", "nci_op01_blocker_ref_count"),
        ("nci_op01_allowed_status_refs", "nci_op01_allowed_status_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP01 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 not-yet steps changed")
    for key in ("full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP01 forbidden green claim changed: {key}")
    status_ref = data.get("nci_op01_status_ref")
    flags = [
        data.get("nci_op01_ready_for_candidate_shape_validation") is True,
        data.get("nci_op01_waiting_for_rdb08_closure") is True,
        data.get("nci_op01_repair_required") is True,
        data.get("nci_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_RDB08_NCI_OP01_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 exactly one intake status branch must be selected")
    if status_ref == P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_READY_FOR_OP02_REF:
        if data.get("op00_contract_valid") is not True or data.get("rdb_op08_contract_valid") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 ready branch requires valid OP00 and RDB-OP08")
        if data.get("rdb_op08_closed_bodyfree_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 ready branch requires closed RDB-OP08")
        if data.get("selected_next_stage_candidate_not_executed") is not True or data.get("rdb_op08_selected_candidate_not_executed_preserved") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 ready branch requires non-executed selected candidate")
        if data.get("rdb_op08_next_required_step_ref") != data.get("selected_next_stage_candidate_ref"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 ready branch requires RDB next_required_step to match selected candidate")
        if data.get("nci_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 ready next step changed")
    else:
        if not data.get("nci_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 non-ready branch must carry blockers")
        if data.get("next_required_step") == P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 non-ready branch cannot continue to OP02")
    if status_ref != P7_R54_AHR_POST_RDB08_NCI_OP01_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        for field in (
            "rdb_op08_input_forbidden_payload_key_path_refs",
            "rdb_op08_input_body_like_value_path_refs",
            "rdb_op08_input_promotion_claim_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP01 non-blocked branch cannot carry body-free scan blockers")
    return True


def _op01_contract_valid_for_op02(op01: Mapping[str, Any] | None) -> bool:
    if op01 is None:
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract(op01)
    except Exception:
        return False


def _candidate_shape_values(op01: Mapping[str, Any]) -> dict[str, str | bool]:
    return {
        "candidate_ref": _clean_ref(op01.get("selected_next_stage_candidate_ref"), default="selected_next_stage_candidate_missing", max_length=360),
        "candidate_kind": _clean_ref(op01.get("selected_next_stage_candidate_kind_ref"), default="selected_next_stage_candidate_kind_missing", max_length=360),
        "selected_status": _clean_ref(op01.get("rdb_selected_status_ref"), default="rdb_selected_status_missing", max_length=360),
        "decision_lane": _clean_ref(op01.get("decision_lane_ref"), default="decision_lane_missing", max_length=360),
        "next_required_step": _clean_ref(op01.get("rdb_op08_next_required_step_ref"), default="rdb_op08_next_required_step_missing", max_length=360),
        "manual_material_ref": _clean_ref(op01.get("manual_decision_material_ref"), default="manual_decision_material_missing", max_length=360),
        "manual_material_present": bool(op01.get("manual_decision_material_present") is True),
        "candidate_not_executed": bool(op01.get("selected_next_stage_candidate_not_executed") is True),
    }


def _candidate_manual_material_present_when_required(kind: str, present: bool) -> bool:
    if kind in {
        rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF,
        rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF,
    }:
        return True
    return present


def _p8_question_candidate_detected(material: Mapping[str, Any]) -> bool:
    if material.get("p8_question_substitution_allowed") is True:
        return True
    if material.get("question_text_materialized") is True:
        return True
    if material.get("p8_question_design_started") is True or material.get("p8_question_implementation_started") is True:
        return True
    return False


def _op02_status_reason_blocker_next(
    *,
    op01_valid: bool,
    op01_ready: bool,
    candidate_kind_allowed: bool,
    candidate_ref_allowed: bool,
    candidate_ref_matches_kind: bool,
    candidate_status_allowed: bool,
    candidate_status_matches_kind_ref_lane: bool,
    candidate_not_executed: bool,
    candidate_next_matches_ref: bool,
    candidate_decision_lane_present: bool,
    candidate_manual_material_present_when_required: bool,
    p8_question_candidate_detected: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    reasons: list[str] = []
    blockers: list[str] = []
    if forbidden_paths or body_like_paths:
        blockers.append("op02_input_forbidden_bodyfree_payload_detected")
    if promotion_claims:
        blockers.append("op02_input_promotion_or_execution_claim_detected")
    if p8_question_candidate_detected:
        blockers.append("op02_input_p8_question_candidate_or_materialization_detected")
    if blockers:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_OR_P8_REF,
            ["selected_candidate_shape_blocked_before_lane_resolution"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_CANDIDATE_SHAPE_REF,
        )
    checks = {
        "op01_contract_valid": op01_valid,
        "op01_ready_for_candidate_shape_validation": op01_ready,
        "candidate_kind_allowed": candidate_kind_allowed,
        "candidate_ref_allowed": candidate_ref_allowed,
        "candidate_ref_matches_kind": candidate_ref_matches_kind,
        "candidate_status_allowed": candidate_status_allowed,
        "candidate_status_matches_kind_ref_lane": candidate_status_matches_kind_ref_lane,
        "candidate_not_executed_confirmed": candidate_not_executed,
        "candidate_next_required_step_matches_ref": candidate_next_matches_ref,
        "candidate_decision_lane_present": candidate_decision_lane_present,
        "candidate_manual_decision_material_present_when_required": candidate_manual_material_present_when_required,
    }
    failed = [name for name, passed in checks.items() if passed is not True]
    if failed:
        blockers.extend(f"{name}_failed" for name in failed)
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_REPAIR_SELECTED_CANDIDATE_SHAPE_REF,
            ["selected_candidate_shape_requires_repair_before_lane_resolution"],
            _dedupe_clean_refs(blockers),
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_CANDIDATE_SHAPE_REF,
        )
    reasons.append("selected_next_stage_candidate_shape_ready_for_lane_resolution_without_execution")
    return (
        P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_READY_FOR_OP03_REF,
        reasons,
        [],
        P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF,
    )


def build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation(
    nci_op01_rdb08_closure_intake: Mapping[str, Any] | None = None,
    *,
    rdb08_closure_intake: Mapping[str, Any] | None = None,
    rdb_op08_closure_intake: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Validate selected_next_stage_candidate shape without execution or lane resolution."""

    op01 = dict(nci_op01_rdb08_closure_intake or rdb08_closure_intake or rdb_op08_closure_intake or {})
    if not op01:
        op01 = build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake()
    op01_valid = _op01_contract_valid_for_op02(op01)
    op01_ready = bool(op01.get("nci_op01_ready_for_candidate_shape_validation") is True)
    shape = _candidate_shape_values(op01)
    candidate_ref = str(shape["candidate_ref"])
    candidate_kind = str(shape["candidate_kind"])
    selected_status = str(shape["selected_status"])
    decision_lane = str(shape["decision_lane"])
    next_required_step_ref = str(shape["next_required_step"])
    manual_material_present = bool(shape["manual_material_present"])
    candidate_not_executed = bool(shape["candidate_not_executed"])

    forbidden_paths = _scan_forbidden_payload_key_paths(op01, path="nci_op01")
    body_like_paths = _scan_body_like_value_paths(op01, path="nci_op01")
    promotion_claims = _scan_promotion_claim_refs(op01, path="nci_op01")
    p8_candidate_detected = _p8_question_candidate_detected(op01)

    kind_allowed = candidate_kind in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS
    ref_allowed = candidate_ref in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_REF_REFS
    ref_matches_kind = candidate_ref in P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_REF_MAP.get(candidate_kind, ())
    status_allowed = selected_status in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_SELECTED_STATUS_REFS
    status_matches_kind = selected_status in P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_STATUS_MAP.get(candidate_kind, ())
    lane_matches_kind = decision_lane in P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_DECISION_LANE_MAP.get(candidate_kind, ())
    status_matches_kind_ref_lane = bool(status_matches_kind and ref_matches_kind and lane_matches_kind)
    next_matches_ref = bool(next_required_step_ref == candidate_ref)
    lane_present = bool(decision_lane and decision_lane != "decision_lane_missing")
    manual_present_when_required = _candidate_manual_material_present_when_required(candidate_kind, manual_material_present)

    status_ref, reasons, blockers, next_required_step = _op02_status_reason_blocker_next(
        op01_valid=op01_valid,
        op01_ready=op01_ready,
        candidate_kind_allowed=kind_allowed,
        candidate_ref_allowed=ref_allowed,
        candidate_ref_matches_kind=ref_matches_kind,
        candidate_status_allowed=status_allowed,
        candidate_status_matches_kind_ref_lane=status_matches_kind_ref_lane,
        candidate_not_executed=candidate_not_executed,
        candidate_next_matches_ref=next_matches_ref,
        candidate_decision_lane_present=lane_present,
        candidate_manual_material_present_when_required=manual_present_when_required,
        p8_question_candidate_detected=p8_candidate_detected,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
    )
    ready = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_READY_FOR_OP03_REF
    repair = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_REPAIR_SELECTED_CANDIDATE_SHAPE_REF
    blocked = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_OR_P8_REF
    session_id = _safe_review_session_id(review_session_id or op01.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op02_selected_candidate_shape_validation_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_schema_version": _clean_ref(op01.get("schema_version"), default="nci_op01_schema_missing", max_length=260),
        "op01_material_ref": _clean_ref(op01.get("material_id"), default="nci_op01_material_missing", max_length=260),
        "op01_status_ref": _clean_ref(op01.get("nci_op01_status_ref"), default="nci_op01_status_missing", max_length=260),
        "op01_next_required_step": _clean_ref(op01.get("next_required_step"), default="nci_op01_next_step_missing", max_length=260),
        "op01_contract_valid": op01_valid,
        "op01_ready_for_candidate_shape_validation": op01_ready,
        "rdb08_candidate_ref": candidate_ref,
        "rdb08_candidate_kind_ref": candidate_kind,
        "rdb08_selected_status_ref": selected_status,
        "rdb08_decision_lane_ref": decision_lane,
        "rdb08_next_required_step_ref": next_required_step_ref,
        "rdb08_manual_decision_material_ref": str(shape["manual_material_ref"]),
        "rdb08_manual_decision_material_present": manual_material_present,
        "candidate_shape_valid": ready,
        "candidate_kind_allowed": kind_allowed,
        "candidate_ref_allowed": ref_allowed,
        "candidate_ref_matches_kind": ref_matches_kind,
        "candidate_status_allowed": status_allowed,
        "candidate_status_matches_kind_ref_lane": status_matches_kind_ref_lane,
        "candidate_not_executed_confirmed": candidate_not_executed,
        "candidate_next_required_step_matches_ref": next_matches_ref,
        "candidate_decision_lane_present": lane_present,
        "candidate_manual_decision_material_present_when_required": manual_present_when_required,
        "p8_question_candidate_detected": p8_candidate_detected,
        "candidate_shape_status_ref": status_ref,
        "nci_op02_status_ref": status_ref,
        "nci_op02_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP02_ALLOWED_STATUS_REFS),
        "nci_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP02_ALLOWED_STATUS_REFS),
        "allowed_rdb_candidate_kind_refs": list(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS),
        "allowed_rdb_candidate_kind_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS),
        "allowed_rdb_candidate_ref_refs": list(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_REF_REFS),
        "allowed_rdb_candidate_ref_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_REF_REFS),
        "candidate_shape_reason_refs": reasons,
        "candidate_shape_reason_ref_count": len(reasons),
        "candidate_shape_blocker_refs": blockers,
        "candidate_shape_blocker_ref_count": len(blockers),
        "op02_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op02_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op02_input_body_like_value_path_refs": body_like_paths,
        "op02_input_body_like_value_path_count": len(body_like_paths),
        "op02_input_promotion_claim_refs": promotion_claims,
        "op02_input_promotion_claim_ref_count": len(promotion_claims),
        "nci_op02_ready_for_lane_resolution": ready,
        "nci_op02_repair_required_for_selected_candidate_shape": repair,
        "nci_op02_bodyfree_leak_promotion_or_p8_blocked": blocked,
        "nci_op02_does_not_resolve_selected_candidate_lane": True,
        "nci_op02_does_not_materialize_next_design_target_or_stop": True,
        "nci_op02_does_not_execute_selected_next_stage_candidate": True,
        "nci_op02_does_not_call_dhr_op05": True,
        "nci_op02_does_not_start_p8_question_design": True,
        "nci_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert NCI-OP02 selected_next_stage_candidate shape validation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP02")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_RDB08_NCI_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP02_STEP_REF,
        source="P7-R54-AHR-PostRDB08-NCI-OP02",
    )
    if data.get("candidate_shape_status_ref") != data.get("nci_op02_status_ref"):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 status alias changed")
    if tuple(data.get("nci_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 allowed status refs changed")
    if tuple(data.get("allowed_rdb_candidate_kind_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_KIND_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 allowed candidate kinds changed")
    if tuple(data.get("allowed_rdb_candidate_ref_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_ALLOWED_RDB_CANDIDATE_REF_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 allowed candidate refs changed")
    for key in (
        "nci_op02_does_not_resolve_selected_candidate_lane",
        "nci_op02_does_not_materialize_next_design_target_or_stop",
        "nci_op02_does_not_execute_selected_next_stage_candidate",
        "nci_op02_does_not_call_dhr_op05",
        "nci_op02_does_not_start_p8_question_design",
        "nci_op02_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP02 required true boundary changed: {key}")
    for field, count_field in (
        ("nci_op02_allowed_status_refs", "nci_op02_allowed_status_ref_count"),
        ("allowed_rdb_candidate_kind_refs", "allowed_rdb_candidate_kind_ref_count"),
        ("allowed_rdb_candidate_ref_refs", "allowed_rdb_candidate_ref_ref_count"),
        ("candidate_shape_reason_refs", "candidate_shape_reason_ref_count"),
        ("candidate_shape_blocker_refs", "candidate_shape_blocker_ref_count"),
        ("op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count"),
        ("op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count"),
        ("op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP02 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 not-yet steps changed")
    status_ref = data.get("nci_op02_status_ref")
    flags = [
        data.get("nci_op02_ready_for_lane_resolution") is True,
        data.get("nci_op02_repair_required_for_selected_candidate_shape") is True,
        data.get("nci_op02_bodyfree_leak_promotion_or_p8_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_RDB08_NCI_OP02_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 exactly one shape status branch must be selected")
    if status_ref == P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_READY_FOR_OP03_REF:
        ready_keys = (
            "op01_contract_valid", "op01_ready_for_candidate_shape_validation", "candidate_shape_valid",
            "candidate_kind_allowed", "candidate_ref_allowed", "candidate_ref_matches_kind", "candidate_status_allowed",
            "candidate_status_matches_kind_ref_lane", "candidate_not_executed_confirmed",
            "candidate_next_required_step_matches_ref", "candidate_decision_lane_present",
            "candidate_manual_decision_material_present_when_required",
        )
        for key in ready_keys:
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP02 ready branch requires {key}")
        if data.get("p8_question_candidate_detected") is not False:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 ready branch cannot detect P8 question candidate")
        if data.get("candidate_shape_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 ready branch next/blocker changed")
    else:
        if not data.get("candidate_shape_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 non-ready branch must carry blockers")
        if data.get("next_required_step") == P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 non-ready branch cannot continue to OP03")
    if status_ref != P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_OR_P8_REF:
        for field in (
            "op02_input_forbidden_payload_key_path_refs",
            "op02_input_body_like_value_path_refs",
            "op02_input_promotion_claim_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP02 non-blocked branch cannot carry body-free scan blockers")
    return True


def _op02_contract_valid_for_op03(op02: Mapping[str, Any] | None) -> bool:
    if op02 is None:
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation_contract(op02)
    except Exception:
        return False


def _op03_lane_info(op02: Mapping[str, Any], *, op02_valid: bool) -> dict[str, str | bool]:
    kind = _clean_ref(op02.get("rdb08_candidate_kind_ref"), default="candidate_kind_missing", max_length=360)
    status = _clean_ref(op02.get("rdb08_selected_status_ref"), default="selected_status_missing", max_length=360)
    ref = _clean_ref(op02.get("rdb08_candidate_ref"), default="candidate_ref_missing", max_length=360)
    decision_lane = _clean_ref(op02.get("rdb08_decision_lane_ref"), default="decision_lane_missing", max_length=360)
    op02_status = op02.get("nci_op02_status_ref")
    if op02_status == P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_OR_P8_REF:
        return {
            "nci_status": P7_R54_AHR_POST_RDB08_NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_STOPPED_REF,
            "lane": P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            "target_ref": P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF,
            "target_kind": P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_BLOCKED_REF,
            "consistent": False,
            "blocked": True,
            "repair": False,
        }
    if not op02_valid or op02_status != P7_R54_AHR_POST_RDB08_NCI_OP02_STATUS_READY_FOR_OP03_REF:
        return {
            "nci_status": P7_R54_AHR_POST_RDB08_NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED_REF,
            "lane": P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
            "target_ref": P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF,
            "target_kind": P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_REPAIR_BOUNDARY_REF,
            "consistent": False,
            "blocked": False,
            "repair": True,
        }
    if kind == rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF:
        lane_info = (
            P7_R54_AHR_POST_RDB08_NCI_STATUS_DHR_OP05_DESIGN_TARGET_CANDIDATE_STOPPED_REF,
            P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_DHR_OP05_BOUNDARY_REF,
        )
    elif kind == rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF:
        lane_info = (
            P7_R54_AHR_POST_RDB08_NCI_STATUS_RETRY_OR_START_ROUTE_CANDIDATE_STOPPED_REF,
            P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_RETRY_OR_START_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_RETRY_OR_START_REF,
        )
    elif kind == rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF:
        lane_info = (
            P7_R54_AHR_POST_RDB08_NCI_STATUS_WAIT_EXTERNAL_CLAIM_CANDIDATE_STOPPED_REF,
            P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_WAIT_EXTERNAL_CLAIM_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_WAIT_EXTERNAL_CLAIM_REF,
        )
    elif kind == rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF:
        lane_info = (
            P7_R54_AHR_POST_RDB08_NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED_REF,
            P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_REPAIR_BOUNDARY_REF,
        )
    elif kind == rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_UNRESOLVED_REF:
        lane_info = (
            P7_R54_AHR_POST_RDB08_NCI_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF,
            P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_MANUAL_HOLD_REF,
        )
    elif kind == rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_BLOCKED_REF:
        lane_info = (
            P7_R54_AHR_POST_RDB08_NCI_STATUS_BLOCKED_SELECTED_CANDIDATE_STOPPED_REF,
            P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_BLOCKED_REF,
        )
    else:
        lane_info = (
            P7_R54_AHR_POST_RDB08_NCI_STATUS_REPAIR_ROUTE_CANDIDATE_STOPPED_REF,
            P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF,
            P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_REPAIR_BOUNDARY_REF,
        )
    consistent = bool(
        ref in P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_REF_MAP.get(kind, ())
        and status in P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_STATUS_MAP.get(kind, ())
        and decision_lane in P7_R54_AHR_POST_RDB08_NCI_CANDIDATE_KIND_TO_DECISION_LANE_MAP.get(kind, ())
    )
    return {
        "nci_status": lane_info[0],
        "lane": lane_info[1],
        "target_ref": lane_info[2],
        "target_kind": lane_info[3],
        "consistent": consistent,
        "blocked": lane_info[1] == P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
        "repair": lane_info[1] == P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
    }


def build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver(
    nci_op02_selected_candidate_shape_validation: Mapping[str, Any] | None = None,
    *,
    selected_candidate_shape_validation: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Resolve selected candidate lane without downstream execution or OP04 materialization."""

    op02 = dict(nci_op02_selected_candidate_shape_validation or selected_candidate_shape_validation or {})
    if not op02:
        op02 = build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation()
    op02_valid = _op02_contract_valid_for_op03(op02)
    lane_info = _op03_lane_info(op02, op02_valid=op02_valid)
    blocked = bool(lane_info["blocked"])
    repair = bool(lane_info["repair"] and not bool(lane_info["consistent"]))
    consistent = bool(lane_info["consistent"] and op02_valid and not blocked)
    blockers = list(op02.get("candidate_shape_blocker_refs") or [])
    if not consistent:
        blockers.append("selected_candidate_lane_consistency_not_ready")
    if blocked:
        blockers.append("selected_candidate_lane_blocked_bodyfree_promotion_or_p8")
    blockers = _dedupe_clean_refs(blockers)
    reasons = ["selected_candidate_lane_resolved_without_execution"] if consistent else ["selected_candidate_lane_resolved_to_stop_or_repair_without_execution"]
    lane = str(lane_info["lane"])
    lane_flags = {
        "dhr_op05_design_target_candidate_present": lane == P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF,
        "retry_or_start_route_candidate_present": lane == P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF,
        "external_claim_wait_candidate_present": lane == P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
        "repair_route_candidate_present": lane == P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
        "unresolved_manual_hold_candidate_present": lane == P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF,
        "blocked_candidate_present": lane == P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    }
    next_required_step = P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF
    if blocked:
        next_required_step = P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF
    elif repair and not consistent:
        next_required_step = P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_LANE_CONSISTENCY_REF
    session_id = _safe_review_session_id(review_session_id or op02.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_schema_version": _clean_ref(op02.get("schema_version"), default="nci_op02_schema_missing", max_length=260),
        "op02_material_ref": _clean_ref(op02.get("material_id"), default="nci_op02_material_missing", max_length=260),
        "op02_status_ref": _clean_ref(op02.get("nci_op02_status_ref"), default="nci_op02_status_missing", max_length=260),
        "op02_next_required_step": _clean_ref(op02.get("next_required_step"), default="nci_op02_next_step_missing", max_length=260),
        "op02_contract_valid": op02_valid,
        "op02_candidate_shape_valid": bool(op02.get("candidate_shape_valid") is True),
        "rdb08_candidate_ref": _clean_ref(op02.get("rdb08_candidate_ref"), default="rdb08_candidate_ref_missing", max_length=360),
        "rdb08_candidate_kind_ref": _clean_ref(op02.get("rdb08_candidate_kind_ref"), default="rdb08_candidate_kind_missing", max_length=360),
        "rdb08_selected_status_ref": _clean_ref(op02.get("rdb08_selected_status_ref"), default="rdb08_selected_status_missing", max_length=360),
        "rdb08_decision_lane_ref": _clean_ref(op02.get("rdb08_decision_lane_ref"), default="rdb08_decision_lane_missing", max_length=360),
        "rdb08_next_required_step_ref": _clean_ref(op02.get("rdb08_next_required_step_ref"), default="rdb08_next_required_step_missing", max_length=360),
        "candidate_lane_consistency_checked": True,
        "candidate_lane_consistent": consistent,
        "candidate_lane_consistency_reason_refs": reasons,
        "candidate_lane_consistency_reason_ref_count": len(reasons),
        "candidate_lane_consistency_blocker_refs": blockers,
        "candidate_lane_consistency_blocker_ref_count": len(blockers),
        "nci_status_ref": str(lane_info["nci_status"]),
        "nci_lane_ref": lane,
        "nci_op03_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP03_ALLOWED_STATUS_REFS),
        "nci_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP03_ALLOWED_STATUS_REFS),
        "nci_allowed_lane_refs": list(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS),
        "nci_allowed_lane_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS),
        "selected_next_design_or_stop_ref": str(lane_info["target_ref"]),
        "selected_next_design_or_stop_kind_ref": str(lane_info["target_kind"]),
        "selected_next_design_or_stop_not_executed": True,
        "selected_next_stage_candidate_not_executed_preserved": bool(op02.get("candidate_not_executed_confirmed") is True),
        "exactly_one_nci_lane_selected": sum(1 for value in lane_flags.values() if value is True) == 1,
        **lane_flags,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_called_here": False,
        "dhr_op06_builder_called_here": False,
        "dmd_builder_called_here": False,
        "r52_actual_execution_called_here": False,
        "actual_local_human_review_operation_started_here": False,
        "raw_evidence_request_created_here": False,
        "repair_executed_here": False,
        "p8_question_substitution_allowed": False,
        "question_text_materialized": False,
        "nci_op03_does_not_execute_selected_next_stage_candidate": True,
        "nci_op03_does_not_call_dhr_op05": True,
        "nci_op03_does_not_start_actual_review": True,
        "nci_op03_does_not_request_raw_evidence": True,
        "nci_op03_does_not_execute_repair": True,
        "nci_op03_does_not_start_p8_question_design": True,
        "nci_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert NCI-OP03 selected candidate lane consistency resolver contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP03")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_RDB08_NCI_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP03_STEP_REF,
        source="P7-R54-AHR-PostRDB08-NCI-OP03",
    )
    if tuple(data.get("nci_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 allowed status refs changed")
    if tuple(data.get("nci_allowed_lane_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 allowed lane refs changed")
    for key in (
        "selected_next_design_or_stop_not_executed",
        "candidate_lane_consistency_checked",
        "exactly_one_nci_lane_selected",
        "nci_op03_does_not_execute_selected_next_stage_candidate",
        "nci_op03_does_not_call_dhr_op05",
        "nci_op03_does_not_start_actual_review",
        "nci_op03_does_not_request_raw_evidence",
        "nci_op03_does_not_execute_repair",
        "nci_op03_does_not_start_p8_question_design",
        "nci_op03_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP03 required true boundary changed: {key}")
    for key in (
        "dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here",
        "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here",
        "raw_evidence_request_created_here", "repair_executed_here", "p8_question_substitution_allowed", "question_text_materialized",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP03 forbidden execution/promotion flag changed: {key}")
    for field, count_field in (
        ("candidate_lane_consistency_reason_refs", "candidate_lane_consistency_reason_ref_count"),
        ("candidate_lane_consistency_blocker_refs", "candidate_lane_consistency_blocker_ref_count"),
        ("nci_op03_allowed_status_refs", "nci_op03_allowed_status_ref_count"),
        ("nci_allowed_lane_refs", "nci_allowed_lane_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP03 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 not-yet steps changed")
    lane_flags = [
        data.get("dhr_op05_design_target_candidate_present") is True,
        data.get("retry_or_start_route_candidate_present") is True,
        data.get("external_claim_wait_candidate_present") is True,
        data.get("repair_route_candidate_present") is True,
        data.get("unresolved_manual_hold_candidate_present") is True,
        data.get("blocked_candidate_present") is True,
    ]
    if sum(lane_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 exactly one lane flag must be true")
    if data.get("nci_status_ref") not in P7_R54_AHR_POST_RDB08_NCI_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 status ref unknown")
    if data.get("nci_lane_ref") not in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 lane ref unknown")
    if data.get("nci_lane_ref") == P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 blocked lane next step changed")
    elif data.get("candidate_lane_consistent") is True:
        if data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 consistent lane must proceed only to OP04 materialization")
        if data.get("candidate_lane_consistency_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 consistent lane cannot carry blockers")
    else:
        if not data.get("candidate_lane_consistency_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP03 inconsistent lane must carry blockers")
    return True


def _op03_contract_valid_for_op04(op03: Mapping[str, Any] | None) -> bool:
    if op03 is None:
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract(op03)
    except Exception:
        return False


def _lane_flags_from_lane(lane_ref: str) -> dict[str, bool]:
    return {
        "dhr_op05_design_target_candidate_present": lane_ref == P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF,
        "retry_or_start_route_candidate_present": lane_ref == P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF,
        "external_claim_wait_candidate_present": lane_ref == P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
        "repair_route_candidate_present": lane_ref == P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF,
        "unresolved_manual_hold_candidate_present": lane_ref == P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF,
        "blocked_candidate_present": lane_ref == P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    }


def _op04_status_reason_blocker_next(*, op03_valid: bool, lane_ref: str, forbidden_paths: Sequence[str], body_like_paths: Sequence[str], promotion_claims: Sequence[str]) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op03_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op03_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("op03_input_promotion_or_autorun_claim_detected")
    if blockers:
        return (P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF, ["op03_material_failed_bodyfree_no_promotion_boundary_before_op05_guard"], _dedupe_clean_refs(blockers, max_length=320), P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP04_MATERIALIZATION_REF)
    if not op03_valid:
        return (P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_REPAIR_REQUIRED_REF, ["op03_lane_consistency_material_invalid_before_next_design_target_or_stop_materialization"], ["nci_op03_contract_invalid"], P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP04_MATERIALIZATION_REF)
    if lane_ref in (P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF, P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF):
        return (P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_STOP_MATERIALIZED_REF, ["selected_nci_lane_materialized_as_stop_without_execution"], [], P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF)
    return (P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_NEXT_DESIGN_TARGET_MATERIALIZED_REF, ["selected_nci_lane_materialized_as_next_design_target_without_execution"], [], P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF)


def build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(
    nci_op03_selected_candidate_lane_consistency_resolver: Mapping[str, Any] | None = None,
    *,
    selected_candidate_lane_consistency_resolver: Mapping[str, Any] | None = None,
    lane_consistency_resolver: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Materialize a next design target or stop material without executing it."""

    op03 = dict(nci_op03_selected_candidate_lane_consistency_resolver or selected_candidate_lane_consistency_resolver or lane_consistency_resolver or {})
    if not op03:
        op03 = build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver()
    op03_valid = _op03_contract_valid_for_op04(op03)
    lane_ref = _clean_ref(op03.get("nci_lane_ref"), default="nci_lane_missing", max_length=360)
    nci_status_ref = _clean_ref(op03.get("nci_status_ref"), default="nci_status_missing", max_length=360)
    selected_ref = _clean_ref(op03.get("selected_next_design_or_stop_ref"), default="selected_next_design_or_stop_missing", max_length=360)
    selected_kind = _clean_ref(op03.get("selected_next_design_or_stop_kind_ref"), default="selected_next_design_or_stop_kind_missing", max_length=360)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op03, path="nci_op03"), max_length=340)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op03, path="nci_op03"), max_length=340)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op03, path="nci_op03"), max_length=340)
    status_ref, reasons, blockers, next_required_step = _op04_status_reason_blocker_next(op03_valid=op03_valid, lane_ref=lane_ref, forbidden_paths=forbidden_paths, body_like_paths=body_like_paths, promotion_claims=promotion_claims)
    lane_flags = _lane_flags_from_lane(lane_ref)
    stop_lane = lane_ref in (P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF, P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF)
    normal_materialized = status_ref in (P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_NEXT_DESIGN_TARGET_MATERIALIZED_REF, P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_STOP_MATERIALIZED_REF)
    session_id = _safe_review_session_id(review_session_id or op03.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_schema_version": _clean_ref(op03.get("schema_version"), default="nci_op03_schema_missing", max_length=260),
        "op03_material_ref": _clean_ref(op03.get("material_id"), default="nci_op03_material_missing", max_length=260),
        "op03_status_ref": _clean_ref(op03.get("nci_status_ref"), default="nci_op03_status_missing", max_length=260),
        "op03_next_required_step": _clean_ref(op03.get("next_required_step"), default="nci_op03_next_step_missing", max_length=360),
        "op03_contract_valid": op03_valid,
        "op03_candidate_lane_consistent": bool(op03.get("candidate_lane_consistent") is True),
        "op03_exactly_one_nci_lane_selected": bool(op03.get("exactly_one_nci_lane_selected") is True),
        "candidate_from_rdb08_ref": _clean_ref(op03.get("rdb08_candidate_ref"), default="rdb08_candidate_missing", max_length=360),
        "candidate_from_rdb08_kind_ref": _clean_ref(op03.get("rdb08_candidate_kind_ref"), default="rdb08_candidate_kind_missing", max_length=360),
        "candidate_from_rdb08_selected_status_ref": _clean_ref(op03.get("rdb08_selected_status_ref"), default="rdb08_selected_status_missing", max_length=360),
        "candidate_from_rdb08_decision_lane_ref": _clean_ref(op03.get("rdb08_decision_lane_ref"), default="rdb08_decision_lane_missing", max_length=360),
        "nci_status_ref": nci_status_ref,
        "nci_lane_ref": lane_ref,
        "nci_op04_status_ref": status_ref,
        "next_design_target_or_stop_materialization_status_ref": status_ref,
        "nci_op04_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP04_ALLOWED_STATUS_REFS),
        "nci_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP04_ALLOWED_STATUS_REFS),
        "next_design_target_or_stop_ref": selected_ref,
        "next_design_target_or_stop_kind_ref": selected_kind,
        "next_design_target_or_stop_not_executed": bool(op03.get("selected_next_design_or_stop_not_executed") is True) and normal_materialized,
        "next_design_target_materialized": bool(normal_materialized and not stop_lane),
        "stop_materialized": bool(normal_materialized and stop_lane),
        "handoff_candidate_materialized": bool(normal_materialized and not stop_lane),
        "stop_candidate_materialized": bool(normal_materialized and stop_lane),
        "dhr_op05_existing_operation_ref": P7_R54_AHR_POST_RDB08_NCI_DHR_OP05_EXISTING_OPERATION_REF,
        **lane_flags,
        "dhr_op05_allowed_meaning_ref": "DHR-OP05 manual handoff boundary may be designed next; DHR-OP05 is not called here",
        "retry_or_start_allowed_meaning_ref": "actual local-only review retry/start boundary may be considered next; actual review is not started here",
        "waiting_claim_allowed_meaning_ref": "external body-free claim reintake may be waited for; raw evidence is not requested here",
        "repair_allowed_meaning_ref": "RDB candidate or upstream result repair boundary may be considered; repair is not executed here",
        "stop_allowed_meaning_ref": "unresolved or blocked lane stops as body-free material without promotion",
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_called_here": False,
        "dhr_op06_builder_called_here": False,
        "dmd_builder_called_here": False,
        "r52_actual_execution_called_here": False,
        "actual_local_human_review_operation_started_here": False,
        "raw_evidence_request_created_here": False,
        "repair_executed_here": False,
        "p8_question_design_started_here": False,
        "p8_question_implementation_started_here": False,
        "question_text_materialized": False,
        "p8_question_substitution_allowed": False,
        "op04_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op04_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op04_input_body_like_value_path_refs": body_like_paths,
        "op04_input_body_like_value_path_count": len(body_like_paths),
        "op04_input_promotion_claim_refs": promotion_claims,
        "op04_input_promotion_claim_ref_count": len(promotion_claims),
        "nci_op04_reason_refs": reasons,
        "nci_op04_reason_ref_count": len(reasons),
        "nci_op04_blocker_refs": blockers,
        "nci_op04_blocker_ref_count": len(blockers),
        "nci_op04_does_not_execute_selected_next_stage_candidate": True,
        "nci_op04_does_not_call_dhr_op05": True,
        "nci_op04_does_not_start_actual_review": True,
        "nci_op04_does_not_request_raw_evidence": True,
        "nci_op04_does_not_execute_repair": True,
        "nci_op04_does_not_start_p8_question_design": True,
        "nci_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract(data: Mapping[str, Any]) -> bool:
    """Assert NCI-OP04 next design target / stop materialization contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP04")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RDB08_NCI_OP04_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP04_STEP_REF, source="P7-R54-AHR-PostRDB08-NCI-OP04")
    if data.get("nci_op04_status_ref") != data.get("next_design_target_or_stop_materialization_status_ref"):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 status alias changed")
    if tuple(data.get("nci_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 allowed status refs changed")
    if data.get("nci_lane_ref") not in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 lane ref unknown")
    for key in ("nci_op04_does_not_execute_selected_next_stage_candidate", "nci_op04_does_not_call_dhr_op05", "nci_op04_does_not_start_actual_review", "nci_op04_does_not_request_raw_evidence", "nci_op04_does_not_execute_repair", "nci_op04_does_not_start_p8_question_design", "nci_op04_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP04 required true boundary changed: {key}")
    for key in ("dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here", "p8_question_design_started_here", "p8_question_implementation_started_here", "question_text_materialized", "p8_question_substitution_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP04 forbidden execution/promotion flag changed: {key}")
    for field, count_field in (("nci_op04_allowed_status_refs", "nci_op04_allowed_status_ref_count"), ("op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count"), ("op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count"), ("op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count"), ("nci_op04_reason_refs", "nci_op04_reason_ref_count"), ("nci_op04_blocker_refs", "nci_op04_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP04 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP04_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 step refs changed")
    lane_flag_count = sum(1 for key in ("dhr_op05_design_target_candidate_present", "retry_or_start_route_candidate_present", "external_claim_wait_candidate_present", "repair_route_candidate_present", "unresolved_manual_hold_candidate_present", "blocked_candidate_present") if data.get(key) is True)
    if lane_flag_count != 1:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 exactly one lane flag must be true")
    status_ref = data.get("nci_op04_status_ref")
    if status_ref == P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_NEXT_DESIGN_TARGET_MATERIALIZED_REF:
        if data.get("op03_contract_valid") is not True or data.get("next_design_target_materialized") is not True or data.get("stop_materialized") is not False or data.get("handoff_candidate_materialized") is not True or data.get("stop_candidate_materialized") is not False or data.get("next_design_target_or_stop_not_executed") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF or data.get("nci_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 next design target branch changed")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_STOP_MATERIALIZED_REF:
        if data.get("op03_contract_valid") is not True or data.get("stop_materialized") is not True or data.get("next_design_target_materialized") is not False or data.get("handoff_candidate_materialized") is not False or data.get("stop_candidate_materialized") is not True or data.get("next_design_target_or_stop_not_executed") is not True or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF or data.get("nci_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 stop branch changed")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if data.get("next_design_target_or_stop_not_executed") is not False or not data.get("nci_op04_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP04_MATERIALIZATION_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 blocked branch changed")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP04_STATUS_REPAIR_REQUIRED_REF:
        if data.get("next_design_target_or_stop_not_executed") is not False or not data.get("nci_op04_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP04_MATERIALIZATION_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 repair branch changed")
    else:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP04 status ref unknown")
    return True


def _op04_contract_valid_for_op05(op04: Mapping[str, Any] | None) -> bool:
    if op04 is None:
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract(op04)
    except Exception:
        return False


def _scan_no_touch_mutation_paths(value: Any, *, path: str = "artifact") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in P7_R54_AHR_POST_RDB08_NCI_NO_TOUCH_CONTRACT_KEYS and child is True:
                paths.append(child_path)
            if key_text in ("nci_no_touch_contract", "public_contract") and isinstance(child, Mapping):
                paths.extend(f"{child_path}.{child_key}" for child_key, child_value in child.items() if child_value is True)
            if key_text in ("changed_file_refs", "modified_file_refs") and isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
                for index, item in enumerate(child):
                    text = str(item).lower()
                    if any(token in text for token in ("api", "db", "schema", "rn", "runtime", "response", "question")):
                        paths.append(f"{child_path}[{index}]")
            paths.extend(_scan_no_touch_mutation_paths(child, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_scan_no_touch_mutation_paths(child, path=f"{path}[{index}]"))
    return paths


def _op05_status_reason_blocker_next(*, op04_valid: bool, forbidden_paths: Sequence[str], body_like_paths: Sequence[str], promotion_claims: Sequence[str], no_touch_paths: Sequence[str]) -> tuple[str, list[str], list[str], str]:
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
        return (P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF, ["op04_material_failed_bodyfree_no_touch_no_promotion_no_auto_execution_guard"], _dedupe_clean_refs(blockers, max_length=320), P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP05_GUARD_REF)
    if not op04_valid:
        return (P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_REPAIR_REQUIRED_REF, ["op04_next_design_target_or_stop_materialization_contract_invalid_before_validation_plan"], ["nci_op04_contract_invalid"], P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP05_GUARD_REF)
    return (P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF, ["nci_op00_to_op04_bodyfree_no_touch_no_promotion_guard_passed_without_execution"], [], P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF)


def build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(
    nci_op04_next_design_target_or_stop_materialization: Mapping[str, Any] | None = None,
    *,
    next_design_target_or_stop_materialization: Mapping[str, Any] | None = None,
    guard_input_material: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Guard OP00-OP04 material before OP06 validation planning."""
    op04 = dict(nci_op04_next_design_target_or_stop_materialization or next_design_target_or_stop_materialization or guard_input_material or {})
    if not op04:
        op04 = build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization()
    op04_valid = _op04_contract_valid_for_op05(op04)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op04, path="nci_op04"), max_length=340)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op04, path="nci_op04"), max_length=340)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op04, path="nci_op04"), max_length=340)
    no_touch_paths = _dedupe_clean_refs(_scan_no_touch_mutation_paths(op04, path="nci_op04"), max_length=340)
    status_ref, reasons, blockers, next_required_step = _op05_status_reason_blocker_next(op04_valid=op04_valid, forbidden_paths=forbidden_paths, body_like_paths=body_like_paths, promotion_claims=promotion_claims, no_touch_paths=no_touch_paths)
    passed = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF
    blocked = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    session_id = _safe_review_session_id(review_session_id or op04.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_schema_version": _clean_ref(op04.get("schema_version"), default="nci_op04_schema_missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id"), default="nci_op04_material_missing", max_length=260),
        "op04_status_ref": _clean_ref(op04.get("nci_op04_status_ref"), default="nci_op04_status_missing", max_length=260),
        "op04_next_required_step": _clean_ref(op04.get("next_required_step"), default="nci_op04_next_step_missing", max_length=360),
        "op04_contract_valid": op04_valid,
        "op04_next_design_target_or_stop_not_executed": bool(op04.get("next_design_target_or_stop_not_executed") is True),
        "selected_nci_status_ref": _clean_ref(op04.get("nci_status_ref"), default="selected_nci_status_missing", max_length=360),
        "selected_nci_lane_ref": _clean_ref(op04.get("nci_lane_ref"), default="selected_nci_lane_missing", max_length=360),
        "selected_next_design_target_or_stop_ref": _clean_ref(op04.get("next_design_target_or_stop_ref"), default="selected_next_design_target_or_stop_missing", max_length=360),
        "selected_next_design_target_or_stop_kind_ref": _clean_ref(op04.get("next_design_target_or_stop_kind_ref"), default="selected_next_design_target_or_stop_kind_missing", max_length=360),
        "selected_next_design_target_or_stop_not_executed": bool(op04.get("next_design_target_or_stop_not_executed") is True) and passed,
        "nci_op05_guard_status_ref": status_ref,
        "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref": status_ref,
        "nci_op05_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP05_ALLOWED_STATUS_REFS),
        "nci_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP05_ALLOWED_STATUS_REFS),
        "bodyfree_guard_passed": bool(passed and not forbidden_paths and not body_like_paths),
        "no_touch_guard_passed": bool(passed and not no_touch_paths),
        "no_promotion_guard_passed": bool(passed and not promotion_claims),
        "no_auto_execution_guard_passed": bool(passed and not promotion_claims),
        "selected_candidate_not_executed_guard_passed": bool(passed and op04.get("next_design_target_or_stop_not_executed") is True),
        "op04_contract_guard_passed": bool(passed and op04_valid),
        "api_db_rn_runtime_response_key_or_p8_question_touch_detected": bool(no_touch_paths),
        "api_db_rn_runtime_response_key_or_p8_question_touch_blocked": bool(blocked and no_touch_paths),
        "forbidden_payload_key_path_refs": forbidden_paths,
        "forbidden_payload_key_path_count": len(forbidden_paths),
        "body_like_value_path_refs": body_like_paths,
        "body_like_value_path_count": len(body_like_paths),
        "promotion_claim_refs": promotion_claims,
        "promotion_claim_ref_count": len(promotion_claims),
        "no_touch_mutation_path_refs": no_touch_paths,
        "no_touch_mutation_path_count": len(no_touch_paths),
        "guard_reason_refs": reasons,
        "guard_reason_ref_count": len(reasons),
        "guard_blocker_refs": blockers,
        "guard_blocker_ref_count": len(blockers),
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_called_here": False,
        "dhr_op06_builder_called_here": False,
        "dmd_builder_called_here": False,
        "r52_actual_execution_called_here": False,
        "actual_local_human_review_operation_started_here": False,
        "raw_evidence_request_created_here": False,
        "repair_executed_here": False,
        "p8_question_design_started_here": False,
        "p8_question_implementation_started_here": False,
        "question_text_materialized": False,
        "p8_question_substitution_allowed": False,
        "nci_op05_does_not_execute_selected_next_stage_candidate": True,
        "nci_op05_does_not_call_dhr_op05": True,
        "nci_op05_does_not_start_actual_review": True,
        "nci_op05_does_not_request_raw_evidence": True,
        "nci_op05_does_not_execute_repair": True,
        "nci_op05_does_not_start_p8_question_design": True,
        "nci_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(data: Mapping[str, Any]) -> bool:
    """Assert NCI-OP05 body-free/no-touch/no-promotion/no-auto-execution guard."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP05")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RDB08_NCI_OP05_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP05_STEP_REF, source="P7-R54-AHR-PostRDB08-NCI-OP05")
    if data.get("nci_op05_guard_status_ref") != data.get("bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref"):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 status alias changed")
    if tuple(data.get("nci_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 allowed status refs changed")
    if data.get("selected_nci_lane_ref") not in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 lane ref unknown")
    for key in ("nci_op05_does_not_execute_selected_next_stage_candidate", "nci_op05_does_not_call_dhr_op05", "nci_op05_does_not_start_actual_review", "nci_op05_does_not_request_raw_evidence", "nci_op05_does_not_execute_repair", "nci_op05_does_not_start_p8_question_design", "nci_op05_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP05 required true boundary changed: {key}")
    for key in ("dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here", "p8_question_design_started_here", "p8_question_implementation_started_here", "question_text_materialized", "p8_question_substitution_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP05 forbidden execution/promotion flag changed: {key}")
    for field, count_field in (("nci_op05_allowed_status_refs", "nci_op05_allowed_status_ref_count"), ("forbidden_payload_key_path_refs", "forbidden_payload_key_path_count"), ("body_like_value_path_refs", "body_like_value_path_count"), ("promotion_claim_refs", "promotion_claim_ref_count"), ("no_touch_mutation_path_refs", "no_touch_mutation_path_count"), ("guard_reason_refs", "guard_reason_ref_count"), ("guard_blocker_refs", "guard_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP05 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 not-claimed boundary must stay false")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP05_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 step refs changed")
    status_ref = data.get("nci_op05_guard_status_ref")
    if status_ref == P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF:
        for key in ("bodyfree_guard_passed", "no_touch_guard_passed", "no_promotion_guard_passed", "no_auto_execution_guard_passed", "selected_candidate_not_executed_guard_passed", "op04_contract_guard_passed", "selected_next_design_target_or_stop_not_executed"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP05 pass branch requires {key}")
        if data.get("guard_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 pass branch next/blocker changed")
        for field in ("forbidden_payload_key_path_refs", "body_like_value_path_refs", "promotion_claim_refs", "no_touch_mutation_path_refs"):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 pass branch cannot carry guard evidence")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if not data.get("guard_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP05_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 blocked branch changed")
        if not any(data.get(field) for field in ("forbidden_payload_key_path_refs", "body_like_value_path_refs", "promotion_claim_refs", "no_touch_mutation_path_refs")):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 blocked branch requires guard evidence")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_REPAIR_REQUIRED_REF:
        if data.get("op04_contract_guard_passed") is not False or not data.get("guard_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP05_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 repair branch changed")
    else:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 status ref unknown")
    if data.get("api_db_rn_runtime_response_key_or_p8_question_touch_blocked") is True and data.get("api_db_rn_runtime_response_key_or_p8_question_touch_detected") is not True:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP05 touch block must have touch detection")
    return True


def _op05_contract_valid_for_op06(op05: Mapping[str, Any] | None) -> bool:
    if op05 is None:
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op05)
    except Exception:
        return False


def _op06_status_reason_blocker_next(
    *,
    op05_valid: bool,
    op05_guard_passed: bool,
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
            P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["op05_guard_material_failed_bodyfree_no_touch_no_promotion_boundary_before_validation_plan"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF,
        )
    if not op05_valid:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_REPAIR_REQUIRED_REF,
            ["op05_guard_material_contract_invalid_before_validation_plan"],
            ["nci_op05_contract_invalid"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_REF,
        )
    if not op05_guard_passed:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF,
            ["op05_guard_has_not_passed_so_validation_plan_must_wait_without_execution"],
            ["nci_op05_guard_not_passed"],
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF,
        )
    return (
        P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF,
        ["validation_plan_refs_recorded_without_executing_tests_regression_or_compileall"],
        [],
        P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF,
    )


def build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan(
    nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard: Mapping[str, Any] | None = None,
    *,
    bodyfree_no_touch_no_promotion_no_auto_execution_guard: Mapping[str, Any] | None = None,
    validation_plan_input_material: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Record target / selected regression / compileall validation plan refs without executing them."""
    op05 = dict(
        nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard
        or bodyfree_no_touch_no_promotion_no_auto_execution_guard
        or validation_plan_input_material
        or {}
    )
    if not op05:
        op05 = build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard()
    op05_valid = _op05_contract_valid_for_op06(op05)
    op05_guard_passed = bool(op05.get("nci_op05_guard_status_ref") == P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF and op05.get("bodyfree_guard_passed") is True and op05.get("no_touch_guard_passed") is True and op05.get("no_promotion_guard_passed") is True and op05.get("no_auto_execution_guard_passed") is True)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op05, path="nci_op05"), max_length=340)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op05, path="nci_op05"), max_length=340)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op05, path="nci_op05"), max_length=340)
    no_touch_paths = _dedupe_clean_refs(_scan_no_touch_mutation_paths(op05, path="nci_op05"), max_length=340)
    status_ref, reasons, blockers, next_required_step = _op06_status_reason_blocker_next(
        op05_valid=op05_valid,
        op05_guard_passed=op05_guard_passed,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    plan_recorded = status_ref == P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF
    session_id = _safe_review_session_id(review_session_id or op05.get("review_session_id"))
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_schema_version": _clean_ref(op05.get("schema_version"), default="nci_op05_schema_missing", max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id"), default="nci_op05_material_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05.get("nci_op05_guard_status_ref"), default="nci_op05_status_missing", max_length=260),
        "op05_next_required_step": _clean_ref(op05.get("next_required_step"), default="nci_op05_next_step_missing", max_length=360),
        "op05_contract_valid": op05_valid,
        "op05_guard_passed": op05_guard_passed,
        "selected_nci_status_ref": _clean_ref(op05.get("selected_nci_status_ref"), default="selected_nci_status_missing", max_length=360),
        "selected_nci_lane_ref": _clean_ref(op05.get("selected_nci_lane_ref"), default="selected_nci_lane_missing", max_length=360),
        "selected_next_design_target_or_stop_ref": _clean_ref(op05.get("selected_next_design_target_or_stop_ref"), default="selected_next_design_target_or_stop_missing", max_length=360),
        "selected_next_design_target_or_stop_kind_ref": _clean_ref(op05.get("selected_next_design_target_or_stop_kind_ref"), default="selected_next_design_target_or_stop_kind_missing", max_length=360),
        "selected_next_design_target_or_stop_not_executed": bool(plan_recorded and op05.get("selected_next_design_target_or_stop_not_executed") is True),
        "nci_op06_validation_plan_status_ref": status_ref,
        "selected_regression_compileall_validation_plan_status_ref": status_ref,
        "nci_op06_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP06_ALLOWED_STATUS_REFS),
        "nci_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP06_ALLOWED_STATUS_REFS),
        "target_test_refs": list(P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS),
        "target_test_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS),
        "selected_regression_test_refs": list(P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_refs": list(P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS),
        "validation_command_summary_refs": list(P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS),
        "target_tests_planned": plan_recorded,
        "selected_regression_planned": plan_recorded,
        "compileall_planned": plan_recorded,
        "op06_validation_plan_recorded": plan_recorded,
        "op06_does_not_execute_validation_commands": True,
        "full_backend_suite_green_claimed_here": False,
        "rn_contract_green_claimed_here": False,
        "actual_review_execution_confirmed": False,
        "op06_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op06_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op06_input_body_like_value_path_refs": body_like_paths,
        "op06_input_body_like_value_path_count": len(body_like_paths),
        "op06_input_promotion_claim_refs": promotion_claims,
        "op06_input_promotion_claim_ref_count": len(promotion_claims),
        "op06_input_no_touch_mutation_path_refs": no_touch_paths,
        "op06_input_no_touch_mutation_path_count": len(no_touch_paths),
        "nci_op06_reason_refs": reasons,
        "nci_op06_reason_ref_count": len(reasons),
        "nci_op06_blocker_refs": blockers,
        "nci_op06_blocker_ref_count": len(blockers),
        "nci_op06_does_not_execute_selected_next_stage_candidate": True,
        "nci_op06_does_not_call_dhr_op05": True,
        "nci_op06_does_not_call_dhr_op06": True,
        "nci_op06_does_not_execute_dmd_r52_or_release": True,
        "nci_op06_does_not_start_actual_review": True,
        "nci_op06_does_not_start_p8_question_design": True,
        "nci_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract(data: Mapping[str, Any]) -> bool:
    """Assert NCI-OP06 validation plan material contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP06")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RDB08_NCI_OP06_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP06_STEP_REF, source="P7-R54-AHR-PostRDB08-NCI-OP06")
    if data.get("nci_op06_validation_plan_status_ref") != data.get("selected_regression_compileall_validation_plan_status_ref"):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 status alias changed")
    if tuple(data.get("nci_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 allowed status refs changed")
    if data.get("selected_nci_lane_ref") not in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 lane ref unknown")
    for key in ("nci_op06_does_not_execute_selected_next_stage_candidate", "nci_op06_does_not_call_dhr_op05", "nci_op06_does_not_call_dhr_op06", "nci_op06_does_not_execute_dmd_r52_or_release", "nci_op06_does_not_start_actual_review", "nci_op06_does_not_start_p8_question_design", "nci_op06_does_not_change_api_db_rn_runtime_response_key", "op06_does_not_execute_validation_commands"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP06 required true boundary changed: {key}")
    for key in ("full_backend_suite_green_claimed_here", "rn_contract_green_claimed_here", "actual_review_execution_confirmed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP06 forbidden green/execution claim changed: {key}")
    for field, count_field in (("nci_op06_allowed_status_refs", "nci_op06_allowed_status_ref_count"), ("target_test_refs", "target_test_ref_count"), ("selected_regression_test_refs", "selected_regression_test_ref_count"), ("compileall_target_refs", "compileall_target_ref_count"), ("validation_command_summary_refs", "validation_command_summary_ref_count"), ("op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count"), ("op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count"), ("op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count"), ("op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count"), ("nci_op06_reason_refs", "nci_op06_reason_ref_count"), ("nci_op06_blocker_refs", "nci_op06_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP06 {count_field} changed")
    if tuple(data.get("target_test_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 target test refs changed")
    if tuple(data.get("selected_regression_test_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 selected regression refs changed")
    if tuple(data.get("compileall_target_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 compileall refs changed")
    if tuple(data.get("validation_command_summary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 command summary refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP06_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 step refs changed")
    status_ref = data.get("nci_op06_validation_plan_status_ref")
    if status_ref == P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF:
        for key in ("op05_contract_valid", "op05_guard_passed", "target_tests_planned", "selected_regression_planned", "compileall_planned", "op06_validation_plan_recorded", "selected_next_design_target_or_stop_not_executed"):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP06 recorded branch requires {key}")
        if data.get("nci_op06_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 recorded branch next/blocker changed")
        for field in ("op06_input_forbidden_payload_key_path_refs", "op06_input_body_like_value_path_refs", "op06_input_promotion_claim_refs", "op06_input_no_touch_mutation_path_refs"):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 recorded branch cannot carry guard evidence")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF:
        if data.get("op05_contract_valid") is not True or data.get("op05_guard_passed") is not False or not data.get("nci_op06_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 waiting branch changed")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_REPAIR_REQUIRED_REF:
        if data.get("op05_contract_valid") is not False or not data.get("nci_op06_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 repair branch changed")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if not data.get("nci_op06_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 blocked branch changed")
        if not any(data.get(field) for field in ("op06_input_forbidden_payload_key_path_refs", "op06_input_body_like_value_path_refs", "op06_input_promotion_claim_refs", "op06_input_no_touch_mutation_path_refs")):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 blocked branch requires guard evidence")
    else:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP06 status ref unknown")
    return True


def _op06_contract_valid_for_op07(op06: Mapping[str, Any] | None) -> bool:
    if op06 is None:
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract(op06)
    except Exception:
        return False


def _op07_status_reason_blocker_next(
    *,
    op06_valid: bool,
    op06_plan_recorded: bool,
    op05_guard_passed: bool,
    lane_ref: str,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str, bool, bool, bool]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op06_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op06_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("op06_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op06_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if blockers:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["op06_validation_plan_failed_bodyfree_no_touch_no_promotion_boundary_before_envelope"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP07_ENVELOPE_REF,
            False,
            True,
            False,
        )
    if not op06_valid:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF,
            ["op06_validation_plan_invalid_so_stop_envelope_is_drafted_without_execution"],
            ["nci_op06_contract_invalid"],
            P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF,
            False,
            True,
            True,
        )
    if not op06_plan_recorded or not op05_guard_passed:
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF,
            ["validation_plan_or_op05_guard_not_ready_so_stop_envelope_is_drafted"],
            ["nci_op06_validation_plan_not_recorded_or_op05_guard_not_passed"],
            P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF,
            False,
            True,
            True,
        )
    if lane_ref in (P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF, P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF):
        return (
            P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF,
            ["selected_nci_lane_is_stop_lane_so_stop_envelope_is_drafted_without_promotion"],
            [],
            P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF,
            False,
            True,
            True,
        )
    return (
        P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_HANDOFF_ENVELOPE_DRAFT_REF,
        ["selected_nci_lane_is_handoff_candidate_so_handoff_envelope_is_drafted_without_execution"],
        [],
        P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF,
        True,
        False,
        True,
    )


def _safe_lane_for_op07(op06: Mapping[str, Any], *, op06_valid: bool) -> str:
    lane_ref = _clean_ref(op06.get("selected_nci_lane_ref"), default="selected_nci_lane_missing", max_length=360)
    if op06_valid and lane_ref in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        return lane_ref
    if lane_ref in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        return lane_ref
    return P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF


def _safe_next_design_or_stop_for_op07(op06: Mapping[str, Any], lane_ref: str, *, op06_valid: bool) -> tuple[str, str]:
    if op06_valid:
        return (
            _clean_ref(op06.get("selected_next_design_target_or_stop_ref"), default="selected_next_design_or_stop_missing", max_length=360),
            _clean_ref(op06.get("selected_next_design_target_or_stop_kind_ref"), default="selected_next_design_or_stop_kind_missing", max_length=360),
        )
    if lane_ref == P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        return P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF, P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_BLOCKED_REF
    return P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF, P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_MANUAL_HOLD_REF


def build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(
    nci_op06_selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    *,
    selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    handoff_or_stop_input_material: Mapping[str, Any] | None = None,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Draft a body-free handoff-or-stop envelope without executing selected candidate."""
    op06 = dict(
        nci_op06_selected_regression_compileall_validation_plan
        or selected_regression_compileall_validation_plan
        or handoff_or_stop_input_material
        or {}
    )
    if not op06:
        op06 = build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan()
    op06_valid = _op06_contract_valid_for_op07(op06)
    op06_plan_recorded = bool(op06.get("op06_validation_plan_recorded") is True and op06.get("nci_op06_validation_plan_status_ref") == P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF)
    op05_guard_passed = bool(op06.get("op05_guard_passed") is True)
    lane_ref = _safe_lane_for_op07(op06, op06_valid=op06_valid)
    selected_ref, selected_kind = _safe_next_design_or_stop_for_op07(op06, lane_ref, op06_valid=op06_valid)
    forbidden_paths = _dedupe_clean_refs(_scan_forbidden_payload_key_paths(op06, path="nci_op06"), max_length=340)
    body_like_paths = _dedupe_clean_refs(_scan_body_like_value_paths(op06, path="nci_op06"), max_length=340)
    promotion_claims = _dedupe_clean_refs(_scan_promotion_claim_refs(op06, path="nci_op06"), max_length=340)
    no_touch_paths = _dedupe_clean_refs(_scan_no_touch_mutation_paths(op06, path="nci_op06"), max_length=340)
    status_ref, reasons, blockers, next_required_step, handoff_present, stop_present, ready_for_op08 = _op07_status_reason_blocker_next(
        op06_valid=op06_valid,
        op06_plan_recorded=op06_plan_recorded,
        op05_guard_passed=op05_guard_passed,
        lane_ref=lane_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    lane_flags = _lane_flags_from_lane(lane_ref)
    session_id = _safe_review_session_id(review_session_id or op06.get("review_session_id"))
    envelope_kind = P7_R54_AHR_POST_RDB08_NCI_OP07_HANDOFF_ENVELOPE_KIND_REF if handoff_present else P7_R54_AHR_POST_RDB08_NCI_OP07_STOP_ENVELOPE_KIND_REF
    envelope_ref = f"nci_op07_{'handoff' if handoff_present else 'stop'}_envelope_for_{selected_ref}"
    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_schema_version": _clean_ref(op06.get("schema_version"), default="nci_op06_schema_missing", max_length=260),
        "op06_material_ref": _clean_ref(op06.get("material_id"), default="nci_op06_material_missing", max_length=260),
        "op06_status_ref": _clean_ref(op06.get("nci_op06_validation_plan_status_ref"), default="nci_op06_status_missing", max_length=260),
        "op06_next_required_step": _clean_ref(op06.get("next_required_step"), default="nci_op06_next_step_missing", max_length=360),
        "op06_contract_valid": op06_valid,
        "op06_validation_plan_recorded": op06_plan_recorded,
        "nci_op07_status_ref": status_ref,
        "handoff_or_stop_envelope_status_ref": status_ref,
        "nci_op07_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP07_ALLOWED_STATUS_REFS),
        "nci_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP07_ALLOWED_STATUS_REFS),
        "handoff_or_stop_envelope_ref": _clean_ref(envelope_ref, default="nci_op07_envelope_missing", max_length=420),
        "handoff_or_stop_envelope_kind_ref": envelope_kind,
        "handoff_or_stop_envelope_bodyfree": True,
        "handoff_envelope_present": handoff_present,
        "stop_envelope_present": stop_present,
        "selected_nci_status_ref": _clean_ref(op06.get("selected_nci_status_ref"), default="selected_nci_status_missing", max_length=360),
        "selected_nci_lane_ref": lane_ref,
        "selected_next_design_or_stop_ref": selected_ref,
        "selected_next_design_or_stop_kind_ref": selected_kind,
        "selected_next_design_or_stop_not_executed": bool(ready_for_op08 and op06.get("selected_next_design_target_or_stop_not_executed") is True),
        **lane_flags,
        "op05_guard_passed": op05_guard_passed,
        "op06_target_tests_planned": bool(op06.get("target_tests_planned") is True),
        "op06_selected_regression_planned": bool(op06.get("selected_regression_planned") is True),
        "op06_compileall_planned": bool(op06.get("compileall_planned") is True),
        "nci_op07_ready_for_op08": ready_for_op08,
        "validation_command_summary_refs": list(op06.get("validation_command_summary_refs") or P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(list(op06.get("validation_command_summary_refs") or P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS)),
        "op07_input_forbidden_payload_key_path_refs": forbidden_paths,
        "op07_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op07_input_body_like_value_path_refs": body_like_paths,
        "op07_input_body_like_value_path_count": len(body_like_paths),
        "op07_input_promotion_claim_refs": promotion_claims,
        "op07_input_promotion_claim_ref_count": len(promotion_claims),
        "op07_input_no_touch_mutation_path_refs": no_touch_paths,
        "op07_input_no_touch_mutation_path_count": len(no_touch_paths),
        "nci_op07_reason_refs": reasons,
        "nci_op07_reason_ref_count": len(reasons),
        "nci_op07_blocker_refs": blockers,
        "nci_op07_blocker_ref_count": len(blockers),
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_called_here": False,
        "dhr_op06_builder_called_here": False,
        "dmd_builder_called_here": False,
        "r52_actual_execution_called_here": False,
        "actual_local_human_review_operation_started_here": False,
        "raw_evidence_request_created_here": False,
        "repair_executed_here": False,
        "p8_question_design_started_here": False,
        "p8_question_implementation_started_here": False,
        "question_text_materialized": False,
        "p8_question_substitution_allowed": False,
        "nci_op07_does_not_execute_handoff_or_stop_envelope": True,
        "nci_op07_does_not_execute_selected_next_stage_candidate": True,
        "nci_op07_does_not_call_dhr_op05": True,
        "nci_op07_does_not_start_actual_review": True,
        "nci_op07_does_not_request_raw_evidence": True,
        "nci_op07_does_not_execute_repair": True,
        "nci_op07_does_not_start_p8_question_design": True,
        "nci_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract(data: Mapping[str, Any]) -> bool:
    """Assert NCI-OP07 handoff-or-stop envelope draft material contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP07")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RDB08_NCI_OP07_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP07_STEP_REF, source="P7-R54-AHR-PostRDB08-NCI-OP07")
    if data.get("nci_op07_status_ref") != data.get("handoff_or_stop_envelope_status_ref"):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 status alias changed")
    if tuple(data.get("nci_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 allowed status refs changed")
    if data.get("selected_nci_lane_ref") not in P7_R54_AHR_POST_RDB08_NCI_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 lane ref unknown")
    lane_flags = [
        data.get("dhr_op05_design_target_candidate_present") is True,
        data.get("retry_or_start_route_candidate_present") is True,
        data.get("external_claim_wait_candidate_present") is True,
        data.get("repair_route_candidate_present") is True,
        data.get("unresolved_manual_hold_candidate_present") is True,
        data.get("blocked_candidate_present") is True,
    ]
    if sum(lane_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 exactly one lane flag must be true")
    for key in ("nci_op07_does_not_execute_handoff_or_stop_envelope", "nci_op07_does_not_execute_selected_next_stage_candidate", "nci_op07_does_not_call_dhr_op05", "nci_op07_does_not_start_actual_review", "nci_op07_does_not_request_raw_evidence", "nci_op07_does_not_execute_repair", "nci_op07_does_not_start_p8_question_design", "nci_op07_does_not_change_api_db_rn_runtime_response_key"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP07 required true boundary changed: {key}")
    for key in ("dhr_op05_call_allowed_here", "dhr_op05_builder_called_here", "dhr_op06_builder_called_here", "dmd_builder_called_here", "r52_actual_execution_called_here", "actual_local_human_review_operation_started_here", "raw_evidence_request_created_here", "repair_executed_here", "p8_question_design_started_here", "p8_question_implementation_started_here", "question_text_materialized", "p8_question_substitution_allowed"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP07 forbidden execution/promotion flag changed: {key}")
    for field, count_field in (("nci_op07_allowed_status_refs", "nci_op07_allowed_status_ref_count"), ("validation_command_summary_refs", "validation_command_summary_ref_count"), ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"), ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"), ("op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count"), ("op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count"), ("nci_op07_reason_refs", "nci_op07_reason_ref_count"), ("nci_op07_blocker_refs", "nci_op07_blocker_ref_count"), ("claim_boundary_refs", "claim_boundary_ref_count"), ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"), ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count")):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP07 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP07_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 step refs changed")
    if data.get("handoff_or_stop_envelope_bodyfree") is not True:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 envelope must stay body-free")
    if (data.get("handoff_envelope_present") is True) == (data.get("stop_envelope_present") is True):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 exactly one envelope kind must be present")
    status_ref = data.get("nci_op07_status_ref")
    if status_ref == P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_HANDOFF_ENVELOPE_DRAFT_REF:
        if data.get("op06_contract_valid") is not True or data.get("op06_validation_plan_recorded") is not True or data.get("op05_guard_passed") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 handoff branch requires valid OP06 and OP05 guard")
        if data.get("handoff_envelope_present") is not True or data.get("stop_envelope_present") is not False or data.get("nci_op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 handoff branch envelope flags changed")
        if data.get("selected_nci_lane_ref") in (P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF, P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 stop lane cannot use handoff envelope")
        if data.get("nci_op07_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 handoff branch next/blocker changed")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_STOP_ENVELOPE_DRAFT_REF:
        if data.get("handoff_envelope_present") is not False or data.get("stop_envelope_present") is not True or data.get("nci_op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 stop branch envelope flags changed")
        if data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 stop branch next step changed")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        if data.get("handoff_envelope_present") is not False or data.get("stop_envelope_present") is not True or data.get("nci_op07_ready_for_op08") is not False:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 blocked branch envelope flags changed")
        if not data.get("nci_op07_blocker_refs") or data.get("next_required_step") != P7_R54_AHR_POST_RDB08_NCI_NEXT_STEP_BLOCKED_OP07_ENVELOPE_REF:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 blocked branch next/blocker changed")
        if not any(data.get(field) for field in ("op07_input_forbidden_payload_key_path_refs", "op07_input_body_like_value_path_refs", "op07_input_promotion_claim_refs", "op07_input_no_touch_mutation_path_refs")):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 blocked branch requires guard evidence")
    elif status_ref == P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_REPAIR_REQUIRED_REF:
        if not data.get("nci_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 repair branch requires blockers")
    else:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP07 status ref unknown")
    return True


def _op07_contract_valid_for_op08(op07: Mapping[str, Any] | None) -> bool:
    if op07 is None:
        return False
    try:
        return assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract(op07)
    except Exception:
        return False


def _safe_mapping_copy_when_bodyfree(value: Mapping[str, Any] | None, *, accepted: bool) -> dict[str, Any]:
    if not accepted or not isinstance(value, Mapping):
        return {}
    return dict(value)


def _bodyfree_no_touch_scan_quads(value: Any, *, path: str) -> tuple[list[str], list[str], list[str], list[str]]:
    return (
        _dedupe_clean_refs(_scan_forbidden_payload_key_paths(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_body_like_value_paths(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_promotion_claim_refs(value, path=path), max_length=340),
        _dedupe_clean_refs(_scan_no_touch_mutation_paths(value, path=path), max_length=340),
    )


def _build_op08_upstream_materials(
    *,
    nci_op04_next_design_target_or_stop_materialization: Mapping[str, Any] | None = None,
    next_design_target_or_stop_materialization: Mapping[str, Any] | None = None,
    nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard: Mapping[str, Any] | None = None,
    bodyfree_no_touch_no_promotion_no_auto_execution_guard: Mapping[str, Any] | None = None,
    nci_op06_selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    nci_op07_handoff_or_stop_envelope_draft_material: Mapping[str, Any] | None = None,
    handoff_or_stop_envelope_draft_material: Mapping[str, Any] | None = None,
    selected_candidate_lane_consistency_resolver: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], bool, bool, bool, bool]:
    op04_input = nci_op04_next_design_target_or_stop_materialization or next_design_target_or_stop_materialization
    op05_input = nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard or bodyfree_no_touch_no_promotion_no_auto_execution_guard
    op06_input = nci_op06_selected_regression_compileall_validation_plan or selected_regression_compileall_validation_plan
    op07_input = nci_op07_handoff_or_stop_envelope_draft_material or handoff_or_stop_envelope_draft_material

    op04_present = isinstance(op04_input, Mapping)
    op05_present = isinstance(op05_input, Mapping)
    op06_present = isinstance(op06_input, Mapping)
    op07_present = isinstance(op07_input, Mapping)

    op04: dict[str, Any] = dict(op04_input) if op04_present else {}
    if not op04 and isinstance(selected_candidate_lane_consistency_resolver, Mapping):
        op04 = build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization(
            selected_candidate_lane_consistency_resolver,
            review_session_id=review_session_id,
        )
        op04_present = True

    op05: dict[str, Any] = dict(op05_input) if op05_present else {}
    if not op05 and op04:
        op05 = build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(
            op04,
            review_session_id=review_session_id,
        )
        op05_present = True

    op06: dict[str, Any] = dict(op06_input) if op06_present else {}
    if not op06 and op05:
        op06 = build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan(
            op05,
            review_session_id=review_session_id,
        )
        op06_present = True

    op07: dict[str, Any] = dict(op07_input) if op07_present else {}
    if not op07 and op06:
        op07 = build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material(
            op06,
            review_session_id=review_session_id,
        )
        op07_present = True

    return op04, op05, op06, op07, op04_present, op05_present, op06_present, op07_present


def build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure(
    *,
    nci_op07_handoff_or_stop_envelope_draft_material: Mapping[str, Any] | None = None,
    handoff_or_stop_envelope_draft_material: Mapping[str, Any] | None = None,
    nci_op06_selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard: Mapping[str, Any] | None = None,
    bodyfree_no_touch_no_promotion_no_auto_execution_guard: Mapping[str, Any] | None = None,
    nci_op04_next_design_target_or_stop_materialization: Mapping[str, Any] | None = None,
    next_design_target_or_stop_materialization: Mapping[str, Any] | None = None,
    selected_candidate_lane_consistency_resolver: Mapping[str, Any] | None = None,
    validation_summary_bodyfree: Mapping[str, Any] | None = None,
    result_memo_bodyfree: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Close NCI-OP00〜OP07 as a body-free selected candidate intake result memo and stop."""

    op04, op05, op06, op07, op04_present, op05_present, op06_present, op07_present = _build_op08_upstream_materials(
        nci_op04_next_design_target_or_stop_materialization=nci_op04_next_design_target_or_stop_materialization,
        next_design_target_or_stop_materialization=next_design_target_or_stop_materialization,
        nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard=nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard,
        bodyfree_no_touch_no_promotion_no_auto_execution_guard=bodyfree_no_touch_no_promotion_no_auto_execution_guard,
        nci_op06_selected_regression_compileall_validation_plan=nci_op06_selected_regression_compileall_validation_plan,
        selected_regression_compileall_validation_plan=selected_regression_compileall_validation_plan,
        nci_op07_handoff_or_stop_envelope_draft_material=nci_op07_handoff_or_stop_envelope_draft_material,
        handoff_or_stop_envelope_draft_material=handoff_or_stop_envelope_draft_material,
        selected_candidate_lane_consistency_resolver=selected_candidate_lane_consistency_resolver,
        review_session_id=review_session_id,
    )

    op04_valid = _op04_contract_valid_for_op05(op04) if op04 else False
    op05_valid = _op05_contract_valid_for_op06(op05) if op05 else False
    op06_valid = _op06_contract_valid_for_op07(op06) if op06 else False
    op07_valid = _op07_contract_valid_for_op08(op07) if op07 else False
    op05_guard_passed = bool(op05_valid and op05.get("nci_op05_guard_status_ref") == P7_R54_AHR_POST_RDB08_NCI_OP05_STATUS_GUARD_PASSED_REF)
    op06_plan_recorded = bool(op06_valid and op06.get("op06_validation_plan_recorded") is True and op06.get("nci_op06_validation_plan_status_ref") == P7_R54_AHR_POST_RDB08_NCI_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF)
    op07_ready = bool(op07_valid and op07.get("nci_op07_ready_for_op08") is True and op07.get("next_required_step") == P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF)

    validation_present = isinstance(validation_summary_bodyfree, Mapping)
    memo_present = isinstance(result_memo_bodyfree, Mapping)
    validation_forbidden, validation_body_like, validation_promotion, validation_no_touch = _bodyfree_no_touch_scan_quads(validation_summary_bodyfree or {}, path="nci_op08.validation_summary")
    memo_forbidden, memo_body_like, memo_promotion, memo_no_touch = _bodyfree_no_touch_scan_quads(result_memo_bodyfree or {}, path="nci_op08.result_memo")
    op07_forbidden, op07_body_like, op07_promotion, op07_no_touch = _bodyfree_no_touch_scan_quads(op07, path="nci_op07")
    validation_accepted = bool(validation_present and not validation_forbidden and not validation_body_like and not validation_promotion and not validation_no_touch)
    memo_accepted = bool(memo_present and not memo_forbidden and not memo_body_like and not memo_promotion and not memo_no_touch)

    reasons: list[str] = []
    blockers: list[str] = []
    op07_status_ref = _clean_ref(op07.get("nci_op07_status_ref"), default="nci_op07_status_missing", max_length=320)
    op07_blocked_status = op07_status_ref == P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    op07_repair_status = op07_status_ref == P7_R54_AHR_POST_RDB08_NCI_OP07_STATUS_REPAIR_REQUIRED_REF

    if op07_forbidden or op07_body_like or op07_promotion or op07_no_touch or validation_forbidden or validation_body_like or validation_promotion or validation_no_touch or memo_forbidden or memo_body_like or memo_promotion or memo_no_touch or op07_blocked_status:
        status_ref = P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
        next_required_step = P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_BLOCKED_REF
        reasons.append("nci_op08_bodyfree_result_memo_or_upstream_envelope_scan_blocked")
        if op07_blocked_status:
            blockers.append("nci_op07_status_bodyfree_leak_promotion_or_autorun_blocked")
        if op07_forbidden:
            blockers.append("nci_op07_forbidden_payload_key_detected_before_result_memo_closure")
        if op07_body_like:
            blockers.append("nci_op07_body_like_value_detected_before_result_memo_closure")
        if op07_promotion:
            blockers.append("nci_op07_promotion_or_autorun_claim_detected_before_result_memo_closure")
        if op07_no_touch:
            blockers.append("nci_op07_api_db_rn_runtime_response_key_or_p8_question_touch_detected_before_result_memo_closure")
        if validation_forbidden:
            blockers.append("nci_op08_validation_summary_forbidden_payload_key_detected")
        if validation_body_like:
            blockers.append("nci_op08_validation_summary_body_like_value_detected")
        if validation_promotion:
            blockers.append("nci_op08_validation_summary_promotion_claim_detected")
        if validation_no_touch:
            blockers.append("nci_op08_validation_summary_no_touch_mutation_detected")
        if memo_forbidden:
            blockers.append("nci_op08_result_memo_forbidden_payload_key_detected")
        if memo_body_like:
            blockers.append("nci_op08_result_memo_body_like_value_detected")
        if memo_promotion:
            blockers.append("nci_op08_result_memo_promotion_claim_detected")
        if memo_no_touch:
            blockers.append("nci_op08_result_memo_no_touch_mutation_detected")
    elif not op07_present or not validation_present or not memo_present:
        status_ref = P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF
        next_required_step = P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_WAIT_REF
        reasons.append("nci_op08_waiting_for_op07_envelope_validation_summary_or_result_memo_refs")
        if not op07_present:
            blockers.append("nci_op07_handoff_or_stop_envelope_missing")
        if not validation_present:
            blockers.append("validation_summary_bodyfree_missing")
        if not memo_present:
            blockers.append("result_memo_bodyfree_missing")
    elif not op04_valid or not op05_valid or not op06_valid or not op07_valid or not op07_ready or not op05_guard_passed or not op06_plan_recorded or op07_repair_status:
        status_ref = P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_REPAIR_REQUIRED_REF
        next_required_step = P7_R54_AHR_POST_RDB08_NCI_OP08_NEXT_STEP_REPAIR_REF
        reasons.append("nci_op08_repair_required_for_op04_op05_op06_op07_or_envelope_inputs")
        if not op04_valid:
            blockers.append("nci_op04_contract_invalid_or_missing")
        if not op05_valid:
            blockers.append("nci_op05_contract_invalid_or_missing")
        if not op06_valid:
            blockers.append("nci_op06_contract_invalid_or_missing")
        if not op07_valid:
            blockers.append("nci_op07_contract_invalid")
        elif not op07_ready:
            blockers.append("nci_op07_not_ready_for_op08")
        if not op05_guard_passed:
            blockers.append("nci_op05_guard_not_passed")
        if not op06_plan_recorded:
            blockers.append("nci_op06_validation_plan_not_recorded")
        if op07_repair_status:
            blockers.append("nci_op07_status_repair_required")
    else:
        status_ref = P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF
        next_required_step = _clean_ref(op07.get("selected_next_design_or_stop_ref"), default=P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF, max_length=360)
        reasons.append("nci_op08_bodyfree_selected_candidate_intake_closed_with_handoff_or_stop_envelope_without_execution")

    target_status = _clean_ref((validation_summary_bodyfree or {}).get("target_test_result_status_ref"), default="not_run", max_length=120)
    selected_status = _clean_ref((validation_summary_bodyfree or {}).get("selected_regression_result_status_ref"), default="not_run", max_length=120)
    compileall_status = _clean_ref((validation_summary_bodyfree or {}).get("compileall_result_status_ref"), default="not_run", max_length=120)
    combined_status = _clean_ref((validation_summary_bodyfree or {}).get("combined_run_status_ref"), default="not_run", max_length=120)

    selected_nci_lane_ref = _clean_ref(op07.get("selected_nci_lane_ref"), default=P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF, max_length=360)
    lane_flags = _lane_flags_from_lane(selected_nci_lane_ref)
    selected_handoff_or_stop_ref = _clean_ref(op07.get("selected_next_design_or_stop_ref"), default="selected_handoff_or_stop_missing", max_length=360)
    selected_handoff_or_stop_kind_ref = _clean_ref(op07.get("handoff_or_stop_envelope_kind_ref"), default="handoff_or_stop_envelope_kind_missing", max_length=360)
    selected_not_executed = bool(op07.get("selected_next_design_or_stop_not_executed") is True and op07.get("nci_op07_does_not_execute_handoff_or_stop_envelope") is True and status_ref == P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF)
    rdb_candidate_not_executed = bool(op04.get("nci_op04_does_not_execute_selected_next_stage_candidate") is True and op04.get("next_design_target_or_stop_not_executed") is True)

    status_flags = {
        "nci_op08_closed_bodyfree_stopped": status_ref == P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF,
        "nci_op08_waiting_for_input_refs": status_ref == P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
        "nci_op08_repair_required": status_ref == P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_REPAIR_REQUIRED_REF,
        "nci_op08_blocked_bodyfree_promotion_autorun": status_ref == P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    }
    session_id = _safe_review_session_id(review_session_id or op07.get("review_session_id") or op06.get("review_session_id") or op05.get("review_session_id") or op04.get("review_session_id"))

    return {
        "schema_version": P7_R54_AHR_POST_RDB08_NCI_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "step": P7_R54_AHR_POST_RDB08_NCI_STEP,
        "scope": P7_R54_AHR_POST_RDB08_NCI_SCOPE,
        "policy_kind": P7_R54_AHR_POST_RDB08_NCI_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_RDB08_NCI_PHASE,
        "material_id": "p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_20260706",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_RDB08_NCI_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_material_present": op04_present,
        "op04_contract_valid": op04_valid,
        "op04_schema_version": _clean_ref(op04.get("schema_version"), default="nci_op04_schema_missing", max_length=260),
        "op04_material_ref": _clean_ref(op04.get("material_id"), default="nci_op04_material_missing", max_length=260),
        "op04_status_ref": _clean_ref(op04.get("nci_op04_status_ref"), default="nci_op04_status_missing", max_length=320),
        "op04_next_required_step": _clean_ref(op04.get("next_required_step"), default="nci_op04_next_step_missing", max_length=360),
        "op05_guard_present": op05_present,
        "op05_contract_valid": op05_valid,
        "op05_schema_version": _clean_ref(op05.get("schema_version"), default="nci_op05_schema_missing", max_length=260),
        "op05_material_ref": _clean_ref(op05.get("material_id"), default="nci_op05_material_missing", max_length=260),
        "op05_status_ref": _clean_ref(op05.get("nci_op05_guard_status_ref"), default="nci_op05_status_missing", max_length=320),
        "op05_next_required_step": _clean_ref(op05.get("next_required_step"), default="nci_op05_next_step_missing", max_length=360),
        "op05_guard_passed": op05_guard_passed,
        "op06_validation_plan_present": op06_present,
        "op06_contract_valid": op06_valid,
        "op06_schema_version": _clean_ref(op06.get("schema_version"), default="nci_op06_schema_missing", max_length=260),
        "op06_material_ref": _clean_ref(op06.get("material_id"), default="nci_op06_material_missing", max_length=260),
        "op06_status_ref": _clean_ref(op06.get("nci_op06_validation_plan_status_ref"), default="nci_op06_status_missing", max_length=320),
        "op06_next_required_step": _clean_ref(op06.get("next_required_step"), default="nci_op06_next_step_missing", max_length=360),
        "op06_validation_plan_recorded": op06_plan_recorded,
        "op07_envelope_present": op07_present,
        "op07_contract_valid": op07_valid,
        "op07_schema_version": _clean_ref(op07.get("schema_version"), default="nci_op07_schema_missing", max_length=260),
        "op07_material_ref": _clean_ref(op07.get("material_id"), default="nci_op07_material_missing", max_length=260),
        "op07_status_ref": op07_status_ref,
        "op07_next_required_step": _clean_ref(op07.get("next_required_step"), default="nci_op07_next_step_missing", max_length=360),
        "op07_ready_for_op08": op07_ready,
        "op07_handoff_or_stop_envelope_ref": _clean_ref(op07.get("handoff_or_stop_envelope_ref"), default="op07_handoff_or_stop_envelope_missing", max_length=360),
        "op07_handoff_or_stop_envelope_kind_ref": _clean_ref(op07.get("handoff_or_stop_envelope_kind_ref"), default="op07_handoff_or_stop_envelope_kind_missing", max_length=360),
        "op07_handoff_or_stop_envelope_bodyfree": bool(op07.get("handoff_or_stop_envelope_bodyfree") is True),
        "op07_handoff_envelope_present": bool(op07.get("handoff_envelope_present") is True),
        "op07_stop_envelope_present": bool(op07.get("stop_envelope_present") is True),
        "validation_summary_bodyfree_present": validation_present,
        "validation_summary_bodyfree_accepted": validation_accepted,
        "validation_summary_bodyfree_ref": _safe_mapping_copy_when_bodyfree(validation_summary_bodyfree, accepted=validation_accepted),
        "validation_summary_forbidden_payload_key_path_refs": validation_forbidden,
        "validation_summary_forbidden_payload_key_path_count": len(validation_forbidden),
        "validation_summary_body_like_value_path_refs": validation_body_like,
        "validation_summary_body_like_value_path_count": len(validation_body_like),
        "validation_summary_promotion_claim_refs": validation_promotion,
        "validation_summary_promotion_claim_ref_count": len(validation_promotion),
        "validation_summary_no_touch_mutation_path_refs": validation_no_touch,
        "validation_summary_no_touch_mutation_path_count": len(validation_no_touch),
        "result_memo_bodyfree_present": memo_present,
        "result_memo_bodyfree_accepted": memo_accepted,
        "result_memo_bodyfree_ref": _safe_mapping_copy_when_bodyfree(result_memo_bodyfree, accepted=memo_accepted),
        "result_memo_forbidden_payload_key_path_refs": memo_forbidden,
        "result_memo_forbidden_payload_key_path_count": len(memo_forbidden),
        "result_memo_body_like_value_path_refs": memo_body_like,
        "result_memo_body_like_value_path_count": len(memo_body_like),
        "result_memo_promotion_claim_refs": memo_promotion,
        "result_memo_promotion_claim_ref_count": len(memo_promotion),
        "result_memo_no_touch_mutation_path_refs": memo_no_touch,
        "result_memo_no_touch_mutation_path_count": len(memo_no_touch),
        "op07_input_forbidden_payload_key_path_refs": op07_forbidden,
        "op07_input_forbidden_payload_key_path_count": len(op07_forbidden),
        "op07_input_body_like_value_path_refs": op07_body_like,
        "op07_input_body_like_value_path_count": len(op07_body_like),
        "op07_input_promotion_claim_refs": op07_promotion,
        "op07_input_promotion_claim_ref_count": len(op07_promotion),
        "op07_input_no_touch_mutation_path_refs": op07_no_touch,
        "op07_input_no_touch_mutation_path_count": len(op07_no_touch),
        "nci_op08_status_ref": status_ref,
        "bodyfree_selected_candidate_intake_closure_status_ref": status_ref,
        "nci_op08_allowed_status_refs": list(P7_R54_AHR_POST_RDB08_NCI_OP08_ALLOWED_STATUS_REFS),
        "nci_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_OP08_ALLOWED_STATUS_REFS),
        **status_flags,
        "nci_op08_reason_refs": _dedupe_clean_refs(reasons, max_length=360),
        "nci_op08_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=360)),
        "nci_op08_blocker_refs": _dedupe_clean_refs(blockers, max_length=360),
        "nci_op08_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=360)),
        "selected_nci_status_ref": _clean_ref(op07.get("selected_nci_status_ref"), default="selected_nci_status_missing", max_length=360),
        "selected_nci_lane_ref": selected_nci_lane_ref,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_not_executed,
        "selected_next_design_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_next_design_or_stop_kind_ref": _clean_ref(op07.get("selected_next_design_or_stop_kind_ref"), default="selected_next_design_or_stop_kind_missing", max_length=360),
        "selected_next_design_or_stop_not_executed": selected_not_executed,
        "rdb08_selected_next_stage_candidate_ref": _clean_ref(op04.get("candidate_from_rdb08_ref"), default="rdb08_selected_next_stage_candidate_missing", max_length=360),
        "rdb08_selected_next_stage_candidate_kind_ref": _clean_ref(op04.get("candidate_from_rdb08_kind_ref"), default="rdb08_selected_next_stage_candidate_kind_missing", max_length=360),
        "rdb08_selected_next_stage_candidate_not_executed": rdb_candidate_not_executed,
        "rdb08_selected_status_ref": _clean_ref(op04.get("candidate_from_rdb08_selected_status_ref"), default="rdb08_selected_status_missing", max_length=360),
        "rdb08_decision_lane_ref": _clean_ref(op04.get("candidate_from_rdb08_decision_lane_ref"), default="rdb08_decision_lane_missing", max_length=360),
        **lane_flags,
        "validation_command_summary_refs": list(P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS),
        "target_test_refs": list(P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS),
        "target_test_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS),
        "selected_regression_test_refs": list(P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_refs": list(P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS),
        "target_test_result_status_ref": target_status,
        "selected_regression_result_status_ref": selected_status,
        "compileall_result_status_ref": compileall_status,
        "combined_run_status_ref": combined_status,
        "nci_target_green_confirmed": target_status == "passed",
        "selected_regression_green_confirmed": selected_status == "passed",
        "compileall_green_confirmed": compileall_status == "passed",
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "full_backend_green_claim_not_made_here": True,
        "rn_green_claim_not_made_here": True,
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "nci_op08_does_not_execute_handoff_or_stop_envelope": True,
        "nci_op08_does_not_execute_selected_next_stage_candidate": True,
        "nci_op08_does_not_call_dhr_op05": True,
        "nci_op08_does_not_call_dhr_op06": True,
        "nci_op08_does_not_execute_dmd_r52_or_release": True,
        "nci_op08_does_not_start_actual_review": True,
        "nci_op08_does_not_request_raw_evidence": True,
        "nci_op08_does_not_execute_repair": True,
        "nci_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "nci_op08_does_not_materialize_p8_question_spec": True,
        "nci_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "p8_question_substitution_allowed": False,
        "claim_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_RDB08_NCI_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "nci_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract(data: Mapping[str, Any]) -> bool:
    """Assert NCI-OP08 body-free selected candidate intake result memo closure contract."""
    _required_fields_present(data, required=P7_R54_AHR_POST_RDB08_NCI_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostRDB08-NCI-OP08")
    if set(data) != set(P7_R54_AHR_POST_RDB08_NCI_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 field set changed")
    _assert_base_bodyfree_boundary(data, schema_version=P7_R54_AHR_POST_RDB08_NCI_OP08_SCHEMA_VERSION, operation_step_ref=P7_R54_AHR_POST_RDB08_NCI_OP08_STEP_REF, source="P7-R54-AHR-PostRDB08-NCI-OP08")
    status_ref = data.get("nci_op08_status_ref")
    flags = [
        data.get("nci_op08_closed_bodyfree_stopped") is True,
        data.get("nci_op08_waiting_for_input_refs") is True,
        data.get("nci_op08_repair_required") is True,
        data.get("nci_op08_blocked_bodyfree_promotion_autorun") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_RDB08_NCI_OP08_ALLOWED_STATUS_REFS or sum(flags) != 1 or data.get("bodyfree_selected_candidate_intake_closure_status_ref") != status_ref:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 exactly one closure status must be selected")
    for field, count_field in (
        ("nci_op08_allowed_status_refs", "nci_op08_allowed_status_ref_count"),
        ("validation_summary_forbidden_payload_key_path_refs", "validation_summary_forbidden_payload_key_path_count"),
        ("validation_summary_body_like_value_path_refs", "validation_summary_body_like_value_path_count"),
        ("validation_summary_promotion_claim_refs", "validation_summary_promotion_claim_ref_count"),
        ("validation_summary_no_touch_mutation_path_refs", "validation_summary_no_touch_mutation_path_count"),
        ("result_memo_forbidden_payload_key_path_refs", "result_memo_forbidden_payload_key_path_count"),
        ("result_memo_body_like_value_path_refs", "result_memo_body_like_value_path_count"),
        ("result_memo_promotion_claim_refs", "result_memo_promotion_claim_ref_count"),
        ("result_memo_no_touch_mutation_path_refs", "result_memo_no_touch_mutation_path_count"),
        ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"),
        ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"),
        ("op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count"),
        ("op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count"),
        ("nci_op08_reason_refs", "nci_op08_reason_ref_count"),
        ("nci_op08_blocker_refs", "nci_op08_blocker_ref_count"),
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("target_test_refs", "target_test_ref_count"),
        ("selected_regression_test_refs", "selected_regression_test_ref_count"),
        ("compileall_target_refs", "compileall_target_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP08 {count_field} changed")
    if tuple(data.get("nci_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 allowed status refs changed")
    if tuple(data.get("validation_command_summary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 validation command refs changed")
    if tuple(data.get("target_test_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 target test refs changed")
    if tuple(data.get("selected_regression_test_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 selected regression refs changed")
    if tuple(data.get("compileall_target_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 compileall refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_RDB08_NCI_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP08_IMPLEMENTED_STEPS) or data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_RDB08_NCI_OP08_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 step refs changed")
    lane_flags = [
        data.get("dhr_op05_design_target_candidate_present") is True,
        data.get("retry_or_start_route_candidate_present") is True,
        data.get("external_claim_wait_candidate_present") is True,
        data.get("repair_route_candidate_present") is True,
        data.get("unresolved_manual_hold_candidate_present") is True,
        data.get("blocked_candidate_present") is True,
    ]
    if sum(lane_flags) != 1:
        raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 exactly one lane flag must be true")
    for key in (
        "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started",
        "nci_op08_does_not_execute_handoff_or_stop_envelope", "nci_op08_does_not_execute_selected_next_stage_candidate", "nci_op08_does_not_call_dhr_op05", "nci_op08_does_not_call_dhr_op06", "nci_op08_does_not_execute_dmd_r52_or_release", "nci_op08_does_not_start_actual_review", "nci_op08_does_not_request_raw_evidence", "nci_op08_does_not_execute_repair", "nci_op08_does_not_start_p5_p6_p8_p7_or_release", "nci_op08_does_not_materialize_p8_question_spec", "nci_op08_does_not_change_api_db_rn_runtime_response_key", "full_backend_green_claim_not_made_here", "rn_green_claim_not_made_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP08 required true boundary changed: {key}")
    for key in ("full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here", "p8_question_substitution_allowed", "p8_start_allowed", "release_allowed", "question_text_materialized"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostRDB08-NCI-OP08 forbidden green/p8/release claim changed: {key}")
    if status_ref == P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_CLOSED_BODYFREE_STOPPED_REF:
        if data.get("op04_contract_valid") is not True or data.get("op05_contract_valid") is not True or data.get("op06_contract_valid") is not True or data.get("op07_contract_valid") is not True or data.get("op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 closed branch requires valid OP04/OP05/OP06/OP07")
        if data.get("validation_summary_bodyfree_accepted") is not True or data.get("result_memo_bodyfree_accepted") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 closed branch requires accepted validation/result memo refs")
        if data.get("selected_handoff_or_stop_not_executed") is not True or data.get("selected_next_design_or_stop_not_executed") is not True or data.get("rdb08_selected_next_stage_candidate_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 closed branch requires all selected refs to remain not executed")
        if data.get("nci_op08_blocker_refs") or data.get("next_required_step") != data.get("selected_handoff_or_stop_ref"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 closed branch blockers/next changed")
    else:
        if not data.get("nci_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 non-closed branch must carry blockers")
        if data.get("selected_handoff_or_stop_not_executed") is not False or data.get("selected_next_design_or_stop_not_executed") is not False:
            raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 non-closed branch cannot expose executable handoff")
    if status_ref != P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        for field in (
            "validation_summary_forbidden_payload_key_path_refs", "validation_summary_body_like_value_path_refs", "validation_summary_promotion_claim_refs", "validation_summary_no_touch_mutation_path_refs",
            "result_memo_forbidden_payload_key_path_refs", "result_memo_body_like_value_path_refs", "result_memo_promotion_claim_refs", "result_memo_no_touch_mutation_path_refs",
            "op07_input_forbidden_payload_key_path_refs", "op07_input_body_like_value_path_refs", "op07_input_promotion_claim_refs", "op07_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostRDB08-NCI-OP08 non-blocked branch cannot carry body-free scan blockers")
    return True


# Full-title aliases for adjacent R54-AHR tests/helpers.
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08 = (
    build_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op00_scope_no_execution_no_promotion_refreeze_after_rdb_op08_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake = (
    build_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op01_rdb_op08_bodyfree_result_memo_closure_intake_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op02_selected_next_stage_candidate_shape_validation = (
    build_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op02_selected_next_stage_candidate_shape_validation_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op02_selected_next_stage_candidate_shape_validation_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op03_selected_candidate_lane_consistency_resolver = (
    build_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op03_selected_candidate_lane_consistency_resolver_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op03_selected_candidate_lane_consistency_resolver_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op04_next_design_target_or_stop_materialization = (
    build_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op04_next_design_target_or_stop_materialization_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op04_next_design_target_or_stop_materialization_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard = (
    build_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op06_selected_regression_compileall_validation_plan = (
    build_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op06_selected_regression_compileall_validation_plan_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op06_selected_regression_compileall_validation_plan_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op07_handoff_or_stop_envelope_draft_material = (
    build_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op07_handoff_or_stop_envelope_draft_material_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op07_handoff_or_stop_envelope_draft_material_contract
)
build_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure = (
    build_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure
)
assert_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract = (
    assert_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract
)
