# -*- coding: utf-8 -*-
"""Post-NCI selected handoff-or-stop decision triage helpers.

R0/R1/R2/R3/R4/R5/R6 scope.

This module is intentionally a thin body-free boundary after the already-closed
NCI-OP08 selected candidate intake result memo.  R0 freezes the work boundary;
R1 adds the PNT helper file, constants, allowed refs, forbidden refs, and a
small constants-summary contract.  R2 implements PNT-OP00 and PNT-OP01.
R3 implements PNT-OP02 and PNT-OP03: selected handoff-or-stop shape validation
and lane resolution without downstream execution.
R4 implements PNT-OP04 and PNT-OP05: next boundary selection materialization
and body-free/no-touch/no-promotion/no-auto-execution guard only.
R5 implements PNT-OP06 and PNT-OP07: validation plan refs and
body-free result memo draft material only; validation commands are not run here.
R6 implements PNT-OP08: body-free result memo closure with next boundary
selection; selected next boundary refs are recorded but not executed here.

Important boundary:
* PNT-OP01 requires an explicit NCI-OP08 material input.
* This module never calls the NCI-OP08 default builder and never synthesizes a
  current NCI lane.
* This module does not execute selected_handoff_or_stop_ref, DHR-OP05, DHR-OP06,
  DMD, R52, actual review, P8, release, API/DB/RN/runtime/response-key changes,
  validation commands, full-backend/RN/real-device claims, downstream
  builders after OP08, or question text materialization.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import clean_identifier, public_contract_flags
import emlis_ai_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_20260706 as nci


P7_R54_AHR_POST_NCI_PNT_PHASE: Final = "P7"
P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE: Final = "local_received_zip_only"
P7_R54_AHR_POST_NCI_PNT_STEP: Final = (
    "R54-AHR-PostNCI_SelectedHandoffOrStopDecisionTriage_20260707"
)
P7_R54_AHR_POST_NCI_PNT_SCOPE: Final = (
    "p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_boundary"
)
P7_R54_AHR_POST_NCI_PNT_POLICY_KIND: Final = (
    "r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_bodyfree_boundary"
)
P7_R54_AHR_POST_NCI_PNT_DEFAULT_REVIEW_SESSION_ID: Final = (
    "p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707"
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_STAGE_REF: Final = (
    "P7-R54-AHR Post-NCI Selected Handoff-or-Stop Decision Triage / Next Boundary Selection"
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_DESIGN_TARGET_REF: Final = (
    "P7-R54-AHR Post-NCI Selected Handoff-or-Stop Decision Triage / Next Boundary Selection"
)
P7_R54_AHR_POST_NCI_PNT_BOUNDARY_PREFIX_REF: Final = "PNT"
P7_R54_AHR_POST_NCI_PNT_BOUNDARY_PREFIX_MEANING_REF: Final = "Post-NCI Triage"
P7_R54_AHR_POST_NCI_PNT_R0_STEP_REF: Final = "R0_work_pre_freeze"
P7_R54_AHR_POST_NCI_PNT_R1_STEP_REF: Final = "R1_helper_skeleton_constants"
P7_R54_AHR_POST_NCI_PNT_EXPECTED_FROM_NCI_OP08_REF: Final = (
    "NCI-OP08 body-free stopped closure records selected_handoff_or_stop_ref; "
    "it is not handoff execution, DHR-OP05 permission, P8 start, P7 complete, or release readiness"
)
P7_R54_AHR_POST_NCI_PNT_EXPECTED_NEXT_REQUIRED_STEP_REF: Final = (
    "continue_to_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08"
)

P7_R54_AHR_POST_NCI_PNT_OP00_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op00_scope_explicit_input_no_execution_refreeze_after_nci_op08.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP01_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op01_nci_op08_closure_intake.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP02_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op02_selected_handoff_or_stop_shape_validation.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP03_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op03_selected_handoff_or_stop_lane_consistency_resolver.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP04_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op04_next_boundary_selection.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP05_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP06_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op06_selected_regression_compileall_validation_plan.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP07_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op07_post_nci_triage_result_memo_draft_material.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_OP08_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt."
    "op08_result_memo_closure.bodyfree.v1"
)
P7_R54_AHR_POST_NCI_PNT_R1_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.post_nci.pnt.r1_helper_skeleton_constants_summary.bodyfree.v1"
)

P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF: Final = (
    "PNT-OP00_scope_explicit_input_no_execution_refreeze_after_NCI_OP08"
)
P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF: Final = (
    "PNT-OP01_explicit_NCI_OP08_bodyfree_result_memo_closure_intake"
)
P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF: Final = (
    "PNT-OP02_selected_handoff_or_stop_shape_validation"
)
P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF: Final = (
    "PNT-OP03_selected_handoff_or_stop_lane_consistency_resolver"
)
P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF: Final = (
    "PNT-OP04_next_boundary_selection_materialization"
)
P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF: Final = (
    "PNT-OP05_bodyfree_no_touch_no_promotion_no_auto_execution_guard"
)
P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF: Final = (
    "PNT-OP06_selected_regression_compileall_validation_plan"
)
P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF: Final = (
    "PNT-OP07_post_nci_triage_result_memo_draft_material"
)
P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF: Final = (
    "PNT-OP08_bodyfree_post_nci_triage_result_memo_closure"
)
P7_R54_AHR_POST_NCI_PNT_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
)
P7_R54_AHR_POST_NCI_PNT_R0_R1_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_R0_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_R1_STEP_REF,
)
P7_R54_AHR_POST_NCI_PNT_R0_R1_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS
)

P7_R54_AHR_POST_NCI_PNT_EXPLICIT_NCI_OP08_MATERIAL_REQUIRED: Final = True
P7_R54_AHR_POST_NCI_PNT_NCI_OP08_DEFAULT_BUILDER_CALL_ALLOWED: Final = False
P7_R54_AHR_POST_NCI_PNT_NCI_OP08_DEFAULT_MATERIAL_SYNTHESIS_ALLOWED: Final = False
P7_R54_AHR_POST_NCI_PNT_NCI_OP08_TEST_FIXTURE_GENERATION_ALLOWED_ONLY_INSIDE_TESTS: Final = True
P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_OR_STOP_EXECUTION_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_NCI_PNT_DHR_OP05_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_NCI_PNT_DHR_OP05_BUILDER_CALL_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_NCI_PNT_P8_QUESTION_DESIGN_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_NCI_PNT_API_DB_RN_RESPONSE_KEY_CHANGE_ALLOWED_HERE: Final = False
P7_R54_AHR_POST_NCI_PNT_BODY_FREE: Final = True

P7_R54_AHR_POST_NCI_PNT_LOCAL_RECEIVED_ZIP_REFS: Final[Mapping[str, str]] = {
    "premise": "Cocolon_前提資料(295).zip",
    "implemented_docs": "EmlisAIの実装済み資料(101).zip",
    "roadmap": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_system_update_20260706(2).zip",
    "cocolon_app": "Cocolon(274).zip",
    "backend": "mashos-api(187).zip",
}
P7_R54_AHR_POST_NCI_PNT_SUPPORT_MATERIAL_REFS: Final[tuple[str, ...]] = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/07_latest_snapshot_diff.md",
    "Cocolon_前提資料/work_attitude_rules_for_karen/99_integrated_paste_each_time.txt",
    "Cocolon_前提資料/work_attitude_rules_for_karen/manifest.json",
    "Cocolon_前提資料/emlis_ai_correction_policy_withdrawal_retention_redesign_2026_05_31.md",
    "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "Cocolon_EmlisAI_P7_PostNCI_NextStageSelection_PreDesignMemo_20260707.md",
    "Cocolon_EmlisAI_P7_R54AHR_PostNCI_SelectedHandoffOrStopDecisionTriage_NextBoundarySelection_DetailedDesign_ImplementationOrder_20260707.md",
    "mashos-api/ai/tests/R54_AHR_PostRDB08_SelectedNextStageCandidateIntake_NCI_OP00_OP08_Result_20260706.md",
)
P7_R54_AHR_POST_NCI_PNT_NOT_STAGE_REFS: Final[tuple[str, ...]] = (
    "selected_handoff_or_stop_ref execution",
    "handoff_or_stop_envelope execution",
    "DHR-OP05 call / builder call / preflight scan execution",
    "DHR-OP06 call",
    "DHR-OP07 materialization",
    "DMD execution",
    "R52 actual execution",
    "actual review start",
    "actual body-full packet generation",
    "actual operation receipt / rows / question need observation rows / disposal creation",
    "P5 finalization",
    "P6 start",
    "P8 start",
    "P8 question design / implementation",
    "question_text / draft_question_text / answer_text materialization",
    "API / DB / RN / runtime / response key change",
    "P7 completion",
    "release decision",
)
P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "PNT R0/R1 only freezes the post-NCI scope and provides helper skeleton constants",
    "PNT helper body must require explicit NCI-OP08 material in future OP01 work",
    "PNT helper body must not call the NCI-OP08 default builder without explicit material",
    "PNT constants classify DHR-OP05 / retry-start / wait / repair / hold / blocked lanes only as stopped candidates",
    "PNT constants keep selected_handoff_or_stop_ref not executed",
    "PNT constants keep P8 question design and release unavailable",
    "PNT constants keep API / DB / RN / runtime / response key no-touch",
)
P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "pnt_op00_implemented",
    "pnt_op01_implemented",
    "selected_handoff_or_stop_executed_here",
    "handoff_or_stop_envelope_executed_here",
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
    "p8_start_allowed",
    "p8_question_design_started",
    "p8_question_implementation_started",
    "question_text_materialized",
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
P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS: Final[tuple[str, ...]] = (
    "no_selected_handoff_or_stop_execution",
    "no_handoff_or_stop_envelope_execution",
    "no_nci_op08_default_builder_call_without_explicit_material",
    "no_dhr_op05_call_or_builder_call",
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

P7_R54_AHR_POST_NCI_PNT_NO_TOUCH_CONTRACT_KEYS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        nci.P7_R54_AHR_POST_RDB08_NCI_NO_TOUCH_CONTRACT_KEYS
        + (
            "api_changed",
            "db_changed",
            "rn_changed",
            "runtime_changed",
            "response_key_changed",
            "p8_question_design_changed",
            "p8_question_implementation_changed",
        )
    )
)
P7_R54_AHR_POST_NCI_PNT_BODY_FREE_MARKER_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        nci.P7_R54_AHR_POST_RDB08_NCI_BODY_FREE_MARKER_REFS
        + (
            "raw_evidence_included",
            "body_included",
            "body_full_packet_included",
            "hash_included",
            "question_schema_included",
            "question_answer_body_included",
        )
    )
)
P7_R54_AHR_POST_NCI_PNT_FORBIDDEN_PAYLOAD_KEY_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        nci.P7_R54_AHR_POST_RDB08_NCI_FORBIDDEN_PAYLOAD_KEY_REFS
        + (
            "raw_answer",
            "raw_evidence",
            "body",
            "body_full_packet",
            "comment_text_body",
            "reviewer_comment",
            "reviewer_free_text",
            "question_text",
            "draft_question_text",
            "answer_text",
            "hash",
            "stdout_body",
            "stderr_body",
            "traceback_body",
        )
    )
)
P7_R54_AHR_POST_NCI_PNT_PROMOTION_CLAIM_FIELD_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        nci.P7_R54_AHR_POST_RDB08_NCI_PROMOTION_CLAIM_FIELD_REFS
        + (
            "selected_handoff_or_stop_executed_here",
            "selected_handoff_or_stop_execution_allowed_here",
            "handoff_or_stop_envelope_executed_here",
            "selected_post_nci_next_boundary_executed_here",
            "selected_post_nci_next_boundary_execution_allowed_here",
            "nci_op08_default_builder_called_here",
            "nci_op08_default_material_synthesized_here",
            "dhr_op05_call_allowed_here",
            "dhr_op05_builder_call_allowed_here",
            "dhr_op06_call_allowed_here",
            "dmd_r52_execution_allowed_here",
            "actual_review_start_allowed_here",
            "actual_review_started_here",
            "raw_evidence_request_allowed_here",
            "repair_execution_allowed_here",
            "p8_question_design_allowed_here",
            "api_db_rn_response_key_change_allowed_here",
            "api_changed",
            "db_changed",
            "rn_changed",
            "runtime_changed",
            "response_key_changed",
            "pnt_op00_implemented",
            "pnt_op01_implemented",
        )
    )
)
P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        nci.P7_R54_AHR_POST_RDB08_NCI_REQUIRED_FALSE_FLAG_REFS
        + (
            "selected_handoff_or_stop_executed_here",
            "handoff_or_stop_envelope_executed_here",
            "selected_post_nci_next_boundary_executed_here",
            "nci_op08_default_builder_called_here",
            "nci_op08_default_material_synthesized_here",
            "actual_review_started_here",
            "api_changed",
            "db_changed",
            "rn_changed",
            "runtime_changed",
            "response_key_changed",
            "pnt_op00_implemented",
            "pnt_op01_implemented",
        )
    )
)

P7_R54_AHR_POST_NCI_PNT_NCI_OP08_REQUIRED_KEY_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "operation_step_ref",
    "nci_op08_status_ref",
    "bodyfree_selected_candidate_intake_closure_status_ref",
    "nci_op08_closed_bodyfree_stopped",
    "selected_nci_status_ref",
    "selected_nci_lane_ref",
    "selected_handoff_or_stop_ref",
    "selected_handoff_or_stop_kind_ref",
    "selected_handoff_or_stop_not_executed",
    "selected_next_design_or_stop_ref",
    "selected_next_design_or_stop_kind_ref",
    "selected_next_design_or_stop_not_executed",
    "rdb08_selected_next_stage_candidate_ref",
    "rdb08_selected_next_stage_candidate_kind_ref",
    "rdb08_selected_next_stage_candidate_not_executed",
    "op07_handoff_or_stop_envelope_ref",
    "op07_handoff_or_stop_envelope_kind_ref",
    "op07_handoff_or_stop_envelope_bodyfree",
    "op07_handoff_envelope_present",
    "op07_stop_envelope_present",
    "validation_command_summary_refs",
    "target_test_result_status_ref",
    "selected_regression_result_status_ref",
    "compileall_result_status_ref",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified_claimed_here",
    "nci_op08_does_not_execute_handoff_or_stop_envelope",
    "nci_op08_does_not_execute_selected_next_stage_candidate",
    "nci_op08_does_not_call_dhr_op05",
    "nci_op08_does_not_call_dhr_op06",
    "nci_op08_does_not_execute_dmd_r52_or_release",
    "nci_op08_does_not_start_actual_review",
    "nci_op08_does_not_request_raw_evidence",
    "nci_op08_does_not_execute_repair",
    "nci_op08_does_not_start_p5_p6_p8_p7_or_release",
    "nci_op08_does_not_materialize_p8_question_spec",
    "nci_op08_does_not_change_api_db_rn_runtime_response_key",
    "p8_question_substitution_allowed",
    "p8_start_allowed",
    "release_allowed",
    "question_text_materialized",
    "body_free",
)

P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_READY_FOR_OP02_REF: Final = (
    "PNT_STATUS_NCI_OP08_CLOSURE_INTAKE_READY_FOR_HANDOFF_OR_STOP_SHAPE"
)
P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF: Final = (
    "PNT_STATUS_WAITING_FOR_EXPLICIT_NCI_OP08_CLOSURE"
)
P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_NCI_OP08_TO_CLOSE_REF: Final = (
    "PNT_STATUS_WAITING_FOR_NCI_OP08_TO_CLOSE"
)
P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF: Final = (
    "PNT_STATUS_REPAIR_REQUIRED_FOR_NCI_OP08_BEFORE_POST_NCI_TRIAGE"
)
P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_BLOCKED_NCI_OP08_REF: Final = (
    "PNT_STATUS_BLOCKED_NCI_OP08_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_NCI_PNT_OP01_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_READY_FOR_OP02_REF,
    P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF,
    P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_NCI_OP08_TO_CLOSE_REF,
    P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF,
    P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_BLOCKED_NCI_OP08_REF,
)

P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_SHAPE_VALID_STOPPED_REF: Final = (
    "PNT_STATUS_SELECTED_HANDOFF_OR_STOP_SHAPE_VALID_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_REPAIR_REQUIRED_REF: Final = (
    "PNT_STATUS_REPAIR_REQUIRED_FOR_SELECTED_HANDOFF_OR_STOP_SHAPE"
)
P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    "PNT_STATUS_BLOCKED_SELECTED_HANDOFF_OR_STOP_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_NCI_PNT_OP02_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_SHAPE_VALID_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)

P7_R54_AHR_POST_NCI_PNT_STATUS_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_STOPPED_REF: Final = (
    "PNT_STATUS_DHR_OP05_MANUAL_HANDOFF_BOUNDARY_DESIGN_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_STATUS_RETRY_START_ROUTE_BOUNDARY_CANDIDATE_STOPPED_REF: Final = (
    "PNT_STATUS_RETRY_START_ROUTE_BOUNDARY_DESIGN_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_STATUS_WAIT_EXTERNAL_BODYFREE_CLAIM_HOLD_STOPPED_REF: Final = (
    "PNT_STATUS_WAIT_EXTERNAL_BODYFREE_CLAIM_HOLD_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_STATUS_REPAIR_BOUNDARY_CANDIDATE_STOPPED_REF: Final = (
    "PNT_STATUS_REPAIR_BOUNDARY_DESIGN_CANDIDATE_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF: Final = (
    "PNT_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF: Final = (
    "PNT_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_OP03_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STATUS_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_STATUS_RETRY_START_ROUTE_BOUNDARY_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_STATUS_WAIT_EXTERNAL_BODYFREE_CLAIM_HOLD_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_STATUS_REPAIR_BOUNDARY_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF,
)

P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_LANE_DHR_OP05_DESIGN_TARGET_REF
)
P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_LANE_RETRY_OR_START_ROUTE_REF
)
P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF
)
P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_LANE_REPAIR_RDB_OR_UPSTREAM_RESULT_REF
)
P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_LANE_MANUAL_HOLD_UNRESOLVED_REF
)
P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
)
P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)

P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_DHR_OP05_BOUNDARY_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_DHR_OP05_BOUNDARY_REF
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_RETRY_START_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_RETRY_OR_START_REF
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_WAIT_EXTERNAL_CLAIM_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_WAIT_EXTERNAL_CLAIM_REF
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_REPAIR_BOUNDARY_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_REPAIR_BOUNDARY_REF
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_MANUAL_HOLD_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_MANUAL_HOLD_REF
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_BLOCKED_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_BLOCKED_REF
)
P7_R54_AHR_POST_NCI_PNT_ALLOWED_SELECTED_HANDOFF_OR_STOP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_DHR_OP05_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_RETRY_START_REF,
    P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_WAIT_EXTERNAL_CLAIM_REF,
    P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_REPAIR_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_MANUAL_HOLD_REF,
    P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_BLOCKED_REF,
)
P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_OP07_HANDOFF_ENVELOPE_KIND_REF
)
P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF: Final = (
    nci.P7_R54_AHR_POST_RDB08_NCI_OP07_STOP_ENVELOPE_KIND_REF
)
P7_R54_AHR_POST_NCI_PNT_ALLOWED_HANDOFF_LANE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF,
)
P7_R54_AHR_POST_NCI_PNT_ALLOWED_STOP_LANE_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
)

P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_NEXT_DESIGN_CANDIDATE_REF: Final = "next_design_candidate"
P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_WAIT_HOLD_REF: Final = "wait_hold"
P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_STOP_REF: Final = "stop"
P7_R54_AHR_POST_NCI_PNT_ALLOWED_OUTCOME_GROUP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_WAIT_HOLD_REF,
    P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_STOP_REF,
)
P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_DHR_OP05_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_RETRY_START_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_WAIT_EXTERNAL_CLAIM_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_REPAIR_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_MANUAL_HOLD_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: P7_R54_AHR_POST_NCI_PNT_SELECTED_STOP_BLOCKED_REF,
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_STATUS_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_STATUS_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_STATUS_RETRY_START_ROUTE_BOUNDARY_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: P7_R54_AHR_POST_NCI_PNT_STATUS_WAIT_EXTERNAL_BODYFREE_CLAIM_HOLD_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_STATUS_REPAIR_BOUNDARY_CANDIDATE_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: P7_R54_AHR_POST_NCI_PNT_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF,
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_ENVELOPE_KIND_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF,
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_WAIT_HOLD_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_NEXT_DESIGN_CANDIDATE_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_STOP_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_STOP_REF,
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_DHR_OP05_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_RETRY_OR_START_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_WAIT_EXTERNAL_CLAIM_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_DESIGN_KIND_REPAIR_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_MANUAL_HOLD_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: nci.P7_R54_AHR_POST_RDB08_NCI_NEXT_STOP_KIND_BLOCKED_REF,
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_TRIAGE_KIND_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: "dhr_op05_manual_handoff_boundary_design_candidate_triage_without_call",
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: "retry_start_route_boundary_design_candidate_triage_without_execution",
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: "wait_external_bodyfree_claim_hold_triage_without_raw_evidence",
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: "repair_boundary_design_candidate_triage_without_repair_execution",
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: "manual_hold_unresolved_stop_triage_without_promotion",
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: "blocked_bodyfree_leak_promotion_or_autorun_stop_triage_without_promotion",
}

P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_DHR_OP05_BOUNDARY_REF: Final = (
    "P7-R54-AHR Post-NCI DHR-OP05 Manual Handoff Boundary / Preflight Re-entry Design Candidate"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_RETRY_START_REF: Final = (
    "P7-R54-AHR Post-NCI Actual Local-Only Review Retry/Start Boundary Selection Candidate"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_WAIT_EXTERNAL_CLAIM_REF: Final = (
    "bodyfree_external_claim_reintake_wait_hold_without_raw_evidence"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_REPAIR_BOUNDARY_REF: Final = (
    "P7-R54-AHR Post-NCI RDB/Upstream Result Repair Boundary Candidate"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_MANUAL_HOLD_STOP_REF: Final = (
    "manual_hold_post_rdb08_unresolved_without_promotion_stop"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_BLOCKED_STOP_REF: Final = (
    "blocked_post_rdb08_candidate_intake_bodyfree_leak_or_promotion_stop"
)
P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP: Final[Mapping[str, str]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_DHR_OP05_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_RETRY_START_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_WAIT_EXTERNAL_CLAIM_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_REPAIR_BOUNDARY_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_MANUAL_HOLD_STOP_REF,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: P7_R54_AHR_POST_NCI_PNT_NEXT_DESIGN_DOCUMENT_BLOCKED_STOP_REF,
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP: Final[Mapping[str, bool]] = {
    P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF: True,
    P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF: True,
    P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF: False,
    P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF: True,
    P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF: False,
    P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF: False,
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP: Final[Mapping[str, bool]] = {
    lane_ref: lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF
    for lane_ref in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP: Final[Mapping[str, bool]] = {
    lane_ref: lane_ref in P7_R54_AHR_POST_NCI_PNT_ALLOWED_STOP_LANE_REFS
    for lane_ref in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS
}
P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP: Final[Mapping[str, bool]] = {
    lane_ref: lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF
    for lane_ref in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS
}

P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_NEXT_BOUNDARY_MATERIALIZED_STOPPED_REF: Final = (
    "PNT_STATUS_NEXT_BOUNDARY_SELECTION_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED_REF: Final = (
    "PNT_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_REPAIR_REQUIRED_REF: Final = (
    "PNT_STATUS_REPAIR_REQUIRED_FOR_BOUNDARY_SELECTION_INPUTS"
)
P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF: Final = (
    "PNT_STATUS_BLOCKED_BOUNDARY_SELECTION_PROMOTION_AUTORUN"
)
P7_R54_AHR_POST_NCI_PNT_OP04_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_NEXT_BOUNDARY_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF,
)
P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_GUARD_PASSED_REF: Final = (
    "PNT_STATUS_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD_PASSED"
)
P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_REPAIR_REQUIRED_REF: Final = (
    "PNT_STATUS_REPAIR_REQUIRED_FOR_BODYFREE_NO_TOUCH_NO_PROMOTION_GUARD_INPUTS"
)
P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF: Final = (
    "PNT_STATUS_BLOCKED_BODYFREE_NO_TOUCH_NO_PROMOTION_NO_AUTO_EXECUTION_GUARD"
)
P7_R54_AHR_POST_NCI_PNT_OP05_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_GUARD_PASSED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF,
)
P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF: Final = (
    "PNT_STATUS_SELECTED_REGRESSION_COMPILEALL_VALIDATION_PLAN_RECORDED"
)
P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF: Final = (
    "PNT_STATUS_WAITING_FOR_OP05_GUARD_BEFORE_VALIDATION_PLAN"
)
P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_REPAIR_REQUIRED_REF: Final = (
    "PNT_STATUS_REPAIR_REQUIRED_FOR_VALIDATION_PLAN_INPUTS"
)
P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF: Final = (
    "PNT_STATUS_BLOCKED_VALIDATION_PLAN_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_NCI_PNT_OP06_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF,
    P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF,
)
P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF: Final = (
    "PNT_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF: Final = (
    "PNT_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_REPAIR_REQUIRED_REF: Final = (
    "PNT_STATUS_REPAIR_REQUIRED_FOR_RESULT_MEMO_DRAFT_INPUTS"
)
P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF: Final = (
    "PNT_STATUS_BLOCKED_RESULT_MEMO_DRAFT_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_NCI_PNT_OP07_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF,
)
P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF: Final = (
    "PNT_OP08_BODYFREE_POST_NCI_TRIAGE_CLOSED_STOPPED"
)
P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF: Final = (
    "PNT_OP08_WAITING_FOR_NCI_OP08_OR_PNT_INPUT_REFS"
)
P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_REPAIR_REQUIRED_REF: Final = (
    "PNT_OP08_REPAIR_REQUIRED_FOR_POST_NCI_TRIAGE_INPUTS"
)
P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF: Final = (
    "PNT_OP08_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN"
)
P7_R54_AHR_POST_NCI_PNT_OP08_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
    P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_REPAIR_REQUIRED_REF,
    P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF,
)

P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS: Final[tuple[str, ...]] = (
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_op01_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_op03_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_op05_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_op07_20260707.py",
    "tests/test_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_result_20260707.py",
)
P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS: Final[tuple[str, ...]] = (
    nci.P7_R54_AHR_POST_RDB08_NCI_TARGET_TEST_REF_REFS
    + nci.P7_R54_AHR_POST_RDB08_NCI_SELECTED_REGRESSION_TEST_REF_REFS
)
P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_20260707.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_rdb08_selected_next_stage_candidate_intake_20260706.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705.py",
    "services/ai_inference/emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704.py",
)
P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS: Final[tuple[str, ...]] = (
    "run_pnt_target_tests_op00_to_op08_after_later_implementation",
    "run_selected_nci_rdb_dri_dhr_regression_without_full_backend_green_claim",
    "run_compileall_for_pnt_nci_rdb_dri_dhr_helper_files",
)



# R2 implemented step ranges.  R1 summary remains historical; OP00/OP01
# materials use the R2 ranges below.
_PNT_R2_REQUIRED_FALSE_EXCLUDE_REFS: Final[frozenset[str]] = frozenset(
    {
        "pnt_op00_implemented",
        "pnt_op01_implemented",
    }
)
P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS = tuple(
    key
    for key in P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS
    if key not in _PNT_R2_REQUIRED_FALSE_EXCLUDE_REFS
)
P7_R54_AHR_POST_NCI_PNT_OP00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF,
)
P7_R54_AHR_POST_NCI_PNT_OP00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[1:]
)
P7_R54_AHR_POST_NCI_PNT_OP01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:2]
)
P7_R54_AHR_POST_NCI_PNT_OP01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[2:]
)

P7_R54_AHR_POST_NCI_PNT_OP02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:3]
)
P7_R54_AHR_POST_NCI_PNT_OP02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[3:]
)
P7_R54_AHR_POST_NCI_PNT_OP03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:4]
)
P7_R54_AHR_POST_NCI_PNT_OP03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[4:]
)
P7_R54_AHR_POST_NCI_PNT_OP04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:5]
)
P7_R54_AHR_POST_NCI_PNT_OP04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[5:]
)
P7_R54_AHR_POST_NCI_PNT_OP05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:6]
)
P7_R54_AHR_POST_NCI_PNT_OP05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[6:]
)
P7_R54_AHR_POST_NCI_PNT_OP06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:7]
)
P7_R54_AHR_POST_NCI_PNT_OP06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[7:]
)
P7_R54_AHR_POST_NCI_PNT_OP07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:8]
)
P7_R54_AHR_POST_NCI_PNT_OP07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[8:]
)
P7_R54_AHR_POST_NCI_PNT_OP08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_STEP_REFS[:9]
)
P7_R54_AHR_POST_NCI_PNT_OP08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF: Final = (
    "wait_for_explicit_nci_op08_bodyfree_result_memo_closure"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_NCI_OP08_CLOSURE_REF: Final = (
    "wait_for_nci_op08_closure_before_post_nci_triage"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NCI_OP08_CLOSURE_REF: Final = (
    "repair_nci_op08_closure_before_post_nci_triage"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NCI_OP08_CLOSURE_REF: Final = (
    "blocked_post_nci_triage_due_to_nci_op08_block"
)

P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_SHAPE_REF: Final = (
    "repair_selected_handoff_or_stop_shape_without_downstream_promotion"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_SHAPE_REF: Final = (
    "blocked_selected_handoff_or_stop_shape_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_LANE_REF: Final = (
    "repair_selected_handoff_or_stop_lane_consistency_without_downstream_promotion"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_LANE_REF: Final = (
    "blocked_selected_handoff_or_stop_lane_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NEXT_BOUNDARY_SELECTION_REF: Final = (
    "repair_post_nci_next_boundary_selection_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NEXT_BOUNDARY_SELECTION_REF: Final = (
    "blocked_post_nci_next_boundary_selection_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP05_GUARD_INPUTS_REF: Final = (
    "repair_pnt_op05_bodyfree_no_touch_no_promotion_guard_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP05_GUARD_REF: Final = (
    "blocked_pnt_op05_bodyfree_no_touch_no_promotion_guard_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF: Final = (
    "wait_for_pnt_op05_bodyfree_no_touch_no_promotion_guard_before_validation_plan"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_INPUTS_REF: Final = (
    "repair_pnt_op06_validation_plan_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF: Final = (
    "blocked_pnt_op06_validation_plan_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP07_RESULT_MEMO_DRAFT_INPUTS_REF: Final = (
    "repair_pnt_op07_result_memo_draft_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP07_RESULT_MEMO_DRAFT_REF: Final = (
    "blocked_pnt_op07_result_memo_draft_bodyfree_leak_promotion_or_autorun"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP08_INPUT_REFS_REF: Final = (
    "wait_for_nci_op08_or_pnt_op07_result_memo_draft_before_pnt_op08_closure"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF: Final = (
    "repair_pnt_op08_result_memo_closure_inputs_without_downstream_promotion"
)
P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF: Final = (
    "blocked_pnt_op08_result_memo_closure_bodyfree_leak_promotion_or_autorun"
)

P7_R54_AHR_POST_NCI_PNT_OP00_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "selected_stage_ref", "selected_design_target_ref", "boundary_prefix_ref", "boundary_prefix_meaning_ref",
    "expected_from_nci_op08_ref", "expected_next_required_step_ref",
    "pnt_scope_refrozen", "explicit_nci_op08_material_required", "nci_op08_default_builder_call_allowed", "nci_op08_default_material_synthesis_allowed",
    "selected_handoff_or_stop_execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here",
    "pnt_op00_scope_confirmed", "pnt_op00_explicit_input_boundary_confirmed", "pnt_op00_no_execution_boundary_confirmed", "pnt_op00_no_touch_boundary_confirmed", "pnt_op00_no_promotion_boundary_confirmed",
    "source_mode_local_received_zip_only_confirmed", "github_connection_check_not_required_by_mash_instruction", "github_connection_check_performed",
    "pnt_op00_does_not_intake_nci_op08_material", "pnt_op00_does_not_synthesize_nci_op08_material", "pnt_op00_does_not_execute_selected_handoff_or_stop", "pnt_op00_does_not_call_dhr_op05", "pnt_op00_does_not_start_p8_question_design", "pnt_op00_does_not_change_api_db_rn_runtime_response_key",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_NCI_PNT_OP01_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op00_material_present", "op00_contract_valid", "op00_schema_version", "op00_material_ref", "op00_next_required_step",
    "explicit_nci_op08_material_required", "nci_op08_default_builder_call_allowed", "nci_op08_default_material_synthesis_allowed", "nci_op08_default_builder_called_here", "nci_op08_default_material_synthesized_here",
    "nci_op08_material_present", "nci_op08_contract_valid", "nci_op08_schema_version", "nci_op08_material_ref", "nci_op08_operation_step_ref", "nci_op08_status_ref", "bodyfree_selected_candidate_intake_closure_status_ref",
    "nci_op08_closed_bodyfree_stopped", "nci_op08_waiting_for_input_refs", "nci_op08_repair_required", "nci_op08_blocked_bodyfree_promotion_autorun",
    "selected_nci_status_ref", "selected_nci_lane_ref", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_ref_present", "selected_handoff_or_stop_kind_ref_present", "selected_handoff_or_stop_not_executed", "selected_handoff_or_stop_not_executed_present",
    "selected_next_design_or_stop_ref", "selected_next_design_or_stop_kind_ref", "selected_next_design_or_stop_not_executed",
    "rdb08_selected_next_stage_candidate_ref", "rdb08_selected_next_stage_candidate_kind_ref", "rdb08_selected_next_stage_candidate_not_executed",
    "op07_handoff_or_stop_envelope_ref", "op07_handoff_or_stop_envelope_kind_ref", "op07_handoff_or_stop_envelope_bodyfree", "op07_handoff_envelope_present", "op07_stop_envelope_present",
    "validation_command_summary_refs", "validation_command_summary_ref_count", "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref", "combined_run_status_ref",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "nci_op08_does_not_execute_handoff_or_stop_envelope", "nci_op08_does_not_execute_selected_next_stage_candidate", "nci_op08_does_not_call_dhr_op05", "nci_op08_does_not_call_dhr_op06", "nci_op08_does_not_execute_dmd_r52_or_release", "nci_op08_does_not_start_actual_review", "nci_op08_does_not_request_raw_evidence", "nci_op08_does_not_execute_repair", "nci_op08_does_not_start_p5_p6_p8_p7_or_release", "nci_op08_does_not_materialize_p8_question_spec", "nci_op08_does_not_change_api_db_rn_runtime_response_key",
    "p8_question_substitution_allowed", "p8_start_allowed", "release_allowed", "question_text_materialized",
    "nci_op08_input_forbidden_payload_key_path_refs", "nci_op08_input_forbidden_payload_key_path_count", "nci_op08_input_body_like_value_path_refs", "nci_op08_input_body_like_value_path_count", "nci_op08_input_promotion_claim_refs", "nci_op08_input_promotion_claim_ref_count", "nci_op08_input_no_touch_mutation_path_refs", "nci_op08_input_no_touch_mutation_path_count",
    "pnt_op01_status_ref", "bodyfree_nci_op08_closure_intake_status_ref", "pnt_op01_allowed_status_refs", "pnt_op01_allowed_status_ref_count", "pnt_op01_ready_for_handoff_or_stop_shape_validation", "pnt_op01_waiting_for_explicit_nci_op08_closure", "pnt_op01_waiting_for_nci_op08_to_close", "pnt_op01_repair_required", "pnt_op01_bodyfree_leak_promotion_or_autorun_blocked",
    "pnt_op01_reason_refs", "pnt_op01_reason_ref_count", "pnt_op01_blocker_refs", "pnt_op01_blocker_ref_count",
    "pnt_op01_does_not_validate_selected_handoff_or_stop_shape", "pnt_op01_does_not_resolve_selected_handoff_or_stop_lane", "pnt_op01_does_not_materialize_next_boundary_selection", "pnt_op01_does_not_execute_selected_handoff_or_stop", "pnt_op01_does_not_call_dhr_op05", "pnt_op01_does_not_call_dhr_op06", "pnt_op01_does_not_execute_dmd_r52_or_release", "pnt_op01_does_not_start_actual_review", "pnt_op01_does_not_request_raw_evidence", "pnt_op01_does_not_execute_repair", "pnt_op01_does_not_start_p5_p6_p8_p7_or_release", "pnt_op01_does_not_change_api_db_rn_runtime_response_key", "pnt_op01_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_NCI_PNT_OP02_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op01_material_present", "op01_contract_valid", "op01_schema_version", "op01_material_ref", "op01_status_ref", "op01_next_required_step", "op01_ready_for_handoff_or_stop_shape_validation",
    "selected_nci_lane_ref", "selected_nci_lane_allowed", "selected_handoff_or_stop_ref", "selected_handoff_or_stop_ref_present", "selected_handoff_or_stop_ref_allowed",
    "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_kind_ref_present", "selected_handoff_or_stop_kind_ref_allowed", "selected_handoff_or_stop_not_executed",
    "selected_next_design_or_stop_ref", "selected_next_design_or_stop_kind_ref", "selected_next_design_or_stop_not_executed", "selected_ref_matches_next_design_or_stop_ref", "selected_next_design_or_stop_kind_matches_lane",
    "rdb08_selected_next_stage_candidate_ref", "rdb08_selected_next_stage_candidate_kind_ref", "rdb08_selected_next_stage_candidate_not_executed",
    "op07_handoff_or_stop_envelope_ref", "op07_handoff_or_stop_envelope_kind_ref", "op07_handoff_or_stop_envelope_bodyfree", "op07_handoff_envelope_present", "op07_stop_envelope_present",
    "expected_selected_handoff_or_stop_ref", "expected_selected_handoff_or_stop_kind_ref", "expected_selected_next_design_or_stop_kind_ref", "expected_envelope_group_ref",
    "selected_handoff_or_stop_ref_matches_lane", "selected_handoff_or_stop_kind_matches_lane", "handoff_or_stop_envelope_kind_consistent", "handoff_or_stop_envelope_presence_consistent",
    "selected_handoff_or_stop_shape_valid", "pnt_op02_status_ref", "bodyfree_selected_handoff_or_stop_shape_status_ref", "pnt_op02_allowed_status_refs", "pnt_op02_allowed_status_ref_count",
    "pnt_op02_shape_valid_stopped", "pnt_op02_repair_required", "pnt_op02_bodyfree_leak_promotion_or_autorun_blocked",
    "pnt_op02_reason_refs", "pnt_op02_reason_ref_count", "pnt_op02_blocker_refs", "pnt_op02_blocker_ref_count",
    "op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count", "op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count", "op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count", "op02_input_no_touch_mutation_path_refs", "op02_input_no_touch_mutation_path_count",
    "pnt_op02_does_not_resolve_selected_handoff_or_stop_lane", "pnt_op02_does_not_materialize_next_boundary_selection", "pnt_op02_does_not_execute_selected_handoff_or_stop", "pnt_op02_does_not_call_dhr_op05", "pnt_op02_does_not_call_dhr_op06", "pnt_op02_does_not_execute_dmd_r52_or_release", "pnt_op02_does_not_start_actual_review", "pnt_op02_does_not_request_raw_evidence", "pnt_op02_does_not_execute_repair", "pnt_op02_does_not_start_p5_p6_p8_p7_or_release", "pnt_op02_does_not_change_api_db_rn_runtime_response_key", "pnt_op02_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS: Final[tuple[str, ...]] = (
    "dhr_op05_manual_handoff_boundary_design_candidate_present",
    "retry_start_route_boundary_candidate_present",
    "wait_external_bodyfree_claim_hold_present",
    "repair_boundary_candidate_present",
    "manual_hold_unresolved_stop_present",
    "blocked_bodyfree_promotion_autorun_stop_present",
)

P7_R54_AHR_POST_NCI_PNT_OP03_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op02_material_present", "op02_contract_valid", "op02_schema_version", "op02_material_ref", "op02_status_ref", "op02_next_required_step", "op02_shape_valid_stopped",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_pnt_triage_kind_ref", "selected_pnt_outcome_group_ref", "selected_pnt_lane_resolved",
    "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_post_nci_next_boundary_candidate_ref", "selected_post_nci_next_boundary_candidate_kind_ref", "selected_post_nci_next_boundary_not_executed",
    "selected_post_nci_next_boundary_execution_allowed_here", "selected_post_nci_next_boundary_materialized_here",
    "allowed_pnt_status_refs", "allowed_pnt_status_ref_count", "allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count", "allowed_pnt_outcome_group_refs", "allowed_pnt_outcome_group_ref_count", "pnt_op03_lane_flag_refs", "pnt_op03_lane_flag_ref_count",
    *P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS,
    "pnt_op03_status_ref", "bodyfree_selected_handoff_or_stop_lane_resolver_status_ref", "pnt_op03_allowed_status_refs", "pnt_op03_allowed_status_ref_count",
    "pnt_op03_dhr_op05_manual_handoff_boundary_design_candidate_stopped", "pnt_op03_retry_start_route_boundary_candidate_stopped", "pnt_op03_wait_external_bodyfree_claim_hold_stopped", "pnt_op03_repair_boundary_candidate_stopped", "pnt_op03_manual_hold_unresolved_stopped", "pnt_op03_blocked_bodyfree_promotion_autorun_stopped",
    "pnt_op03_reason_refs", "pnt_op03_reason_ref_count", "pnt_op03_blocker_refs", "pnt_op03_blocker_ref_count",
    "op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count", "op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count", "op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count", "op03_input_no_touch_mutation_path_refs", "op03_input_no_touch_mutation_path_count",
    "pnt_op03_does_not_materialize_next_boundary_selection", "pnt_op03_does_not_execute_selected_handoff_or_stop", "pnt_op03_does_not_call_dhr_op05", "pnt_op03_does_not_call_dhr_op06", "pnt_op03_does_not_execute_dmd_r52_or_release", "pnt_op03_does_not_start_actual_review", "pnt_op03_does_not_request_raw_evidence", "pnt_op03_does_not_execute_repair", "pnt_op03_does_not_start_p5_p6_p8_p7_or_release", "pnt_op03_does_not_change_api_db_rn_runtime_response_key", "pnt_op03_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)



P7_R54_AHR_POST_NCI_PNT_OP04_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op03_material_present", "op03_contract_valid", "op03_schema_version", "op03_material_ref", "op03_status_ref", "op03_next_required_step", "op03_lane_resolved",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_pnt_triage_kind_ref", "selected_pnt_outcome_group_ref",
    "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref",
    "selected_post_nci_next_boundary_not_executed", "selected_post_nci_next_boundary_execution_allowed_here", "selected_post_nci_next_boundary_materialized_here",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate",
    "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here",
    "allowed_pnt_status_refs", "allowed_pnt_status_ref_count", "allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count", "allowed_pnt_outcome_group_refs", "allowed_pnt_outcome_group_ref_count",
    "pnt_op04_status_ref", "bodyfree_next_boundary_selection_status_ref", "pnt_op04_allowed_status_refs", "pnt_op04_allowed_status_ref_count",
    "pnt_op04_next_boundary_selection_materialized_stopped", "pnt_op04_stop_selection_materialized_stopped", "pnt_op04_repair_required", "pnt_op04_bodyfree_leak_promotion_or_autorun_blocked",
    "pnt_op04_reason_refs", "pnt_op04_reason_ref_count", "pnt_op04_blocker_refs", "pnt_op04_blocker_ref_count",
    "op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count", "op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count", "op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count", "op04_input_no_touch_mutation_path_refs", "op04_input_no_touch_mutation_path_count",
    "pnt_op04_does_not_execute_selected_handoff_or_stop", "pnt_op04_does_not_call_dhr_op05", "pnt_op04_does_not_call_dhr_op06", "pnt_op04_does_not_execute_dmd_r52_or_release", "pnt_op04_does_not_start_actual_review", "pnt_op04_does_not_request_raw_evidence", "pnt_op04_does_not_execute_repair", "pnt_op04_does_not_start_p5_p6_p8_p7_or_release", "pnt_op04_does_not_change_api_db_rn_runtime_response_key", "pnt_op04_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_NCI_PNT_OP05_GUARD_SUBJECT_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF,
    P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF,
)
P7_R54_AHR_POST_NCI_PNT_OP05_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op04_material_present", "op04_contract_valid", "op04_schema_version", "op04_material_ref", "op04_status_ref", "op04_next_required_step", "op04_selection_materialized_or_stopped",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref",
    "selected_post_nci_next_boundary_not_executed", "selected_post_nci_next_boundary_execution_allowed_here", "selected_post_nci_next_boundary_materialized_here",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate",
    "guard_subject_step_refs", "guard_subject_step_ref_count", "guard_scope_ref",
    "pnt_op05_status_ref", "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref", "pnt_op05_allowed_status_refs", "pnt_op05_allowed_status_ref_count",
    "pnt_op05_guard_passed", "pnt_op05_repair_required", "pnt_op05_bodyfree_leak_promotion_or_autorun_blocked",
    "pnt_op05_reason_refs", "pnt_op05_reason_ref_count", "pnt_op05_blocker_refs", "pnt_op05_blocker_ref_count",
    "guard_forbidden_payload_key_path_refs", "guard_forbidden_payload_key_path_count", "guard_body_like_value_path_refs", "guard_body_like_value_path_count", "guard_promotion_claim_refs", "guard_promotion_claim_ref_count", "guard_no_touch_mutation_path_refs", "guard_no_touch_mutation_path_count",
    "selected_handoff_or_stop_execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here",
    "pnt_op05_does_not_execute_selected_handoff_or_stop", "pnt_op05_does_not_call_dhr_op05", "pnt_op05_does_not_call_dhr_op06", "pnt_op05_does_not_execute_dmd_r52_or_release", "pnt_op05_does_not_start_actual_review", "pnt_op05_does_not_request_raw_evidence", "pnt_op05_does_not_execute_repair", "pnt_op05_does_not_start_p5_p6_p8_p7_or_release", "pnt_op05_does_not_change_api_db_rn_runtime_response_key", "pnt_op05_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_NCI_PNT_OP06_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op05_material_present", "op05_contract_valid", "op05_schema_version", "op05_material_ref", "op05_status_ref", "op05_next_required_step", "op05_guard_passed",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref",
    "selected_post_nci_next_boundary_not_executed", "selected_post_nci_next_boundary_execution_allowed_here", "selected_post_nci_next_boundary_materialized_here",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate",
    "validation_plan_ref", "validation_plan_recorded", "validation_plan_bodyfree", "validation_plan_execution_allowed_here",
    "validation_commands_executed_here", "pytest_executed_here", "pnt_target_tests_executed_here", "selected_regression_executed_here", "compileall_executed_here",
    "target_test_ref_refs", "target_test_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_count", "compileall_target_ref_refs", "compileall_target_ref_count",
    "validation_command_summary_refs", "validation_command_summary_ref_count", "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "pnt_op06_status_ref", "bodyfree_selected_regression_compileall_validation_plan_status_ref", "pnt_op06_allowed_status_refs", "pnt_op06_allowed_status_ref_count",
    "pnt_op06_validation_plan_recorded", "pnt_op06_waiting_for_op05_guard", "pnt_op06_repair_required", "pnt_op06_bodyfree_leak_promotion_or_autorun_blocked",
    "pnt_op06_reason_refs", "pnt_op06_reason_ref_count", "pnt_op06_blocker_refs", "pnt_op06_blocker_ref_count",
    "op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count", "op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count", "op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count", "op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count",
    "selected_handoff_or_stop_execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here",
    "pnt_op06_does_not_execute_validation_commands", "pnt_op06_does_not_claim_full_backend_rn_or_real_device_green", "pnt_op06_does_not_execute_selected_handoff_or_stop", "pnt_op06_does_not_call_dhr_op05", "pnt_op06_does_not_call_dhr_op06", "pnt_op06_does_not_execute_dmd_r52_or_release", "pnt_op06_does_not_start_actual_review", "pnt_op06_does_not_request_raw_evidence", "pnt_op06_does_not_execute_repair", "pnt_op06_does_not_start_p5_p6_p8_p7_or_release", "pnt_op06_does_not_change_api_db_rn_runtime_response_key", "pnt_op06_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)

P7_R54_AHR_POST_NCI_PNT_OP07_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op06_material_present", "op06_contract_valid", "op06_schema_version", "op06_material_ref", "op06_status_ref", "op06_next_required_step", "op06_validation_plan_recorded",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref",
    "selected_post_nci_next_boundary_not_executed", "selected_post_nci_next_boundary_execution_allowed_here", "selected_post_nci_next_boundary_materialized_here",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate",
    "validation_plan_ref", "validation_plan_recorded", "validation_command_summary_refs", "validation_command_summary_ref_count",
    "target_test_ref_refs", "target_test_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_count", "compileall_target_ref_refs", "compileall_target_ref_count",
    "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref",
    "post_nci_triage_result_memo_draft_ref", "post_nci_triage_result_memo_draft_bodyfree", "post_nci_triage_result_memo_draft_materialized_here", "post_nci_triage_result_memo_draft_execution_allowed_here", "pnt_op07_ready_for_op08",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "pnt_op07_status_ref", "bodyfree_post_nci_triage_result_memo_draft_status_ref", "pnt_op07_allowed_status_refs", "pnt_op07_allowed_status_ref_count",
    "pnt_op07_result_memo_draft_materialized_stopped", "pnt_op07_stop_result_memo_draft_materialized_stopped", "pnt_op07_repair_required", "pnt_op07_bodyfree_leak_promotion_or_autorun_blocked",
    "pnt_op07_reason_refs", "pnt_op07_reason_ref_count", "pnt_op07_blocker_refs", "pnt_op07_blocker_ref_count",
    "op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count", "op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count", "op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count", "op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count",
    "selected_handoff_or_stop_execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here",
    "pnt_op07_does_not_close_result_memo_as_op08", "pnt_op07_does_not_execute_selected_handoff_or_stop", "pnt_op07_does_not_call_dhr_op05", "pnt_op07_does_not_call_dhr_op06", "pnt_op07_does_not_execute_dmd_r52_or_release", "pnt_op07_does_not_start_actual_review", "pnt_op07_does_not_request_raw_evidence", "pnt_op07_does_not_execute_repair", "pnt_op07_does_not_start_p5_p6_p8_p7_or_release", "pnt_op07_does_not_change_api_db_rn_runtime_response_key", "pnt_op07_does_not_materialize_p8_question_spec",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


P7_R54_AHR_POST_NCI_PNT_OP08_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "op07_material_present", "op07_contract_valid", "op07_schema_version", "op07_material_ref", "op07_status_ref", "op07_next_required_step", "op07_ready_for_op08",
    "nci_op08_material_present", "nci_op08_contract_valid", "nci_op08_schema_version", "nci_op08_material_ref", "nci_op08_status_ref", "nci_op08_closed_bodyfree_stopped",
    "post_nci_triage_result_memo_draft_ref", "post_nci_triage_result_memo_draft_bodyfree", "post_nci_triage_result_memo_draft_materialized_here",
    "bodyfree_post_nci_triage_result_memo_closure_ref", "bodyfree_post_nci_triage_result_memo_closure_bodyfree", "bodyfree_post_nci_triage_result_memo_closure_materialized_here", "bodyfree_post_nci_triage_result_memo_closure_execution_allowed_here",
    "selected_pnt_status_ref", "selected_pnt_lane_ref", "selected_post_nci_outcome_group_ref", "selected_post_nci_next_boundary_ref", "selected_post_nci_next_boundary_kind_ref",
    "selected_post_nci_next_boundary_not_executed", "selected_post_nci_next_boundary_execution_allowed_here", "selected_post_nci_next_boundary_materialized_here",
    "selected_handoff_or_stop_ref", "selected_handoff_or_stop_kind_ref", "selected_handoff_or_stop_not_executed",
    "next_design_document_candidate_ref", "next_design_document_allowed", "manual_wait_required", "manual_stop_required", "repair_design_candidate",
    "validation_plan_ref", "validation_plan_recorded", "validation_command_summary_refs", "validation_command_summary_ref_count",
    "target_test_ref_refs", "target_test_ref_count", "selected_regression_test_ref_refs", "selected_regression_test_ref_count", "compileall_target_ref_refs", "compileall_target_ref_count",
    "target_test_result_status_ref", "selected_regression_result_status_ref", "compileall_result_status_ref",
    "full_backend_suite_green_confirmed", "rn_contract_green_confirmed", "rn_real_device_modal_verified_claimed_here",
    "pnt_op08_status_ref", "bodyfree_post_nci_triage_result_memo_closure_status_ref", "pnt_op08_allowed_status_refs", "pnt_op08_allowed_status_ref_count",
    "pnt_op08_bodyfree_post_nci_triage_closed_stopped", "pnt_op08_waiting_for_input_refs", "pnt_op08_repair_required", "pnt_op08_bodyfree_leak_promotion_or_autorun_blocked",
    "pnt_op08_reason_refs", "pnt_op08_reason_ref_count", "pnt_op08_blocker_refs", "pnt_op08_blocker_ref_count",
    "op08_op07_input_forbidden_payload_key_path_refs", "op08_op07_input_forbidden_payload_key_path_count", "op08_op07_input_body_like_value_path_refs", "op08_op07_input_body_like_value_path_count", "op08_op07_input_promotion_claim_refs", "op08_op07_input_promotion_claim_ref_count", "op08_op07_input_no_touch_mutation_path_refs", "op08_op07_input_no_touch_mutation_path_count",
    "op08_nci_input_forbidden_payload_key_path_refs", "op08_nci_input_forbidden_payload_key_path_count", "op08_nci_input_body_like_value_path_refs", "op08_nci_input_body_like_value_path_count", "op08_nci_input_promotion_claim_refs", "op08_nci_input_promotion_claim_ref_count", "op08_nci_input_no_touch_mutation_path_refs", "op08_nci_input_no_touch_mutation_path_count",
    "selected_handoff_or_stop_execution_allowed_here", "dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "dhr_op06_call_allowed_here", "dmd_r52_execution_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "p8_question_design_allowed_here", "api_db_rn_response_key_change_allowed_here",
    "pnt_op08_does_not_execute_selected_handoff_or_stop", "pnt_op08_does_not_execute_selected_post_nci_next_boundary", "pnt_op08_does_not_call_dhr_op05", "pnt_op08_does_not_call_dhr_op06", "pnt_op08_does_not_execute_dmd_r52_or_release", "pnt_op08_does_not_start_actual_review", "pnt_op08_does_not_request_raw_evidence", "pnt_op08_does_not_execute_repair", "pnt_op08_does_not_start_p5_p6_p8_p7_or_release", "pnt_op08_does_not_change_api_db_rn_runtime_response_key", "pnt_op08_does_not_materialize_p8_question_spec",
    "dhr_op05_not_called", "dhr_op06_not_called", "dmd_r52_not_executed", "p5_p6_p8_p7_release_not_started", "p8_question_design_not_started", "p8_question_implementation_not_started", "api_db_rn_runtime_response_key_not_changed",
    "claim_boundary_refs", "claim_boundary_ref_count", "not_claimed_boundary_refs", "not_claimed_boundary_ref_count", "not_claimed_boundary", "fixed_non_promotion_refs", "fixed_non_promotion_ref_count",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract", "pnt_no_touch_contract", "body_free_markers", *P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS, "body_free",
)


def _safe_review_session_id(value: Any = None) -> str:
    return clean_identifier(
        value,
        default=P7_R54_AHR_POST_NCI_PNT_DEFAULT_REVIEW_SESSION_ID,
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
    return {key: False for key in P7_R54_AHR_POST_NCI_PNT_NO_TOUCH_CONTRACT_KEYS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_NCI_PNT_BODY_FREE_MARKER_REFS}


def _not_claimed_boundary() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS}


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS}


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
            if key_text in P7_R54_AHR_POST_NCI_PNT_FORBIDDEN_PAYLOAD_KEY_REFS:
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
            if key_text in P7_R54_AHR_POST_NCI_PNT_FORBIDDEN_PAYLOAD_KEY_REFS:
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
            if key_text in P7_R54_AHR_POST_NCI_PNT_PROMOTION_CLAIM_FIELD_REFS and child is True:
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
            if key_text in P7_R54_AHR_POST_NCI_PNT_NO_TOUCH_CONTRACT_KEYS and child is True:
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
    if data.get("phase") != P7_R54_AHR_POST_NCI_PNT_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_AHR_POST_NCI_PNT_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_AHR_POST_NCI_PNT_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_AHR_POST_NCI_PNT_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("operation_step_ref") != operation_step_ref or data.get("policy_section") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} git connection flags changed")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must stay body-free")
    _assert_public_contract_false(data, source=source)
    _assert_false_mapping(data, field="pnt_no_touch_contract", source=source)
    _assert_false_mapping(data, field="body_free_markers", source=source)
    for key in P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} required false flag promoted: {key}")
    if any(key in P7_R54_AHR_POST_NCI_PNT_FORBIDDEN_PAYLOAD_KEY_REFS for key in data):
        raise ValueError(f"{source} contains a forbidden body payload key")


def _op00_contract_valid(op00: Mapping[str, Any] | None) -> bool:
    if not isinstance(op00, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract(op00) is True
    except ValueError:
        return False


def _nci_op08_contract_valid(op08: Mapping[str, Any] | None) -> bool:
    if not isinstance(op08, Mapping):
        return False
    try:
        return nci.assert_p7_r54_ahr_post_rdb08_nci_op08_bodyfree_selected_candidate_intake_result_memo_closure_contract(op08) is True
    except ValueError:
        return False


def _pnt_op01_status_reason_blocker_next(
    *,
    op00_valid: bool,
    op08_present: bool,
    op08_contract_valid: bool,
    op08_status_ref: str,
    op08_closed: bool,
    op08_waiting: bool,
    op08_repair: bool,
    op08_blocked: bool,
    selected_handoff_or_stop_ref: str,
    selected_handoff_or_stop_kind_ref: str,
    selected_handoff_or_stop_not_executed_present: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("nci_op08_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("nci_op08_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("nci_op08_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("nci_op08_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op08_blocked or op08_status_ref == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("nci_op08_status_bodyfree_leak_promotion_or_autorun_blocked")
    if blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_BLOCKED_NCI_OP08_REF,
            ["nci_op08_result_memo_failed_bodyfree_no_promotion_boundary_before_pnt_op02"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NCI_OP08_CLOSURE_REF,
        )
    if not op00_valid:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF,
            ["pnt_op00_contract_invalid_before_nci_op08_intake"],
            ["pnt_op00_contract_invalid"],
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NCI_OP08_CLOSURE_REF,
        )
    if not op08_present:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF,
            ["explicit_nci_op08_bodyfree_result_memo_closure_not_provided_yet"],
            ["explicit_nci_op08_bodyfree_result_memo_closure_missing"],
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF,
        )
    if op08_waiting or op08_status_ref == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_NCI_OP08_TO_CLOSE_REF,
            ["nci_op08_result_memo_closure_waiting_before_post_nci_triage"],
            ["nci_op08_waiting_for_input_refs"],
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_NCI_OP08_CLOSURE_REF,
        )
    if not op08_contract_valid:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF,
            ["nci_op08_result_memo_closure_contract_repair_required_before_pnt_op02"],
            ["nci_op08_result_memo_closure_contract_invalid"],
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NCI_OP08_CLOSURE_REF,
        )
    if op08_repair or op08_status_ref == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_REPAIR_REQUIRED_REF:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF,
            ["nci_op08_result_memo_closure_repair_required_before_pnt_op02"],
            ["nci_op08_repair_required_for_closure_inputs"],
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NCI_OP08_CLOSURE_REF,
        )
    if not selected_handoff_or_stop_not_executed_present:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF,
            ["nci_op08_selected_handoff_or_stop_non_execution_presence_missing_before_pnt_op02"],
            ["selected_handoff_or_stop_not_executed_missing"],
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NCI_OP08_CLOSURE_REF,
        )
    if op08_closed and selected_handoff_or_stop_ref and selected_handoff_or_stop_kind_ref:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_READY_FOR_OP02_REF,
            ["nci_op08_closed_bodyfree_selected_handoff_or_stop_refs_ready_for_pnt_op02_shape_validation"],
            [],
            P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF,
        ["nci_op08_result_memo_closure_incomplete_before_selected_handoff_or_stop_shape_validation"],
        ["nci_op08_selected_handoff_or_stop_ref_or_kind_missing"],
        P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NCI_OP08_CLOSURE_REF,
    )


def build_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08(
    *, review_session_id: Any = None
) -> dict[str, Any]:
    """Build PNT-OP00 body-free scope / explicit-input / no-execution refreeze material."""

    session_id = _safe_review_session_id(review_session_id)
    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP00_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_NCI_PNT_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_NCI_PNT_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_NCI_PNT_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_NCI_PNT_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_nci_op08_ref": P7_R54_AHR_POST_NCI_PNT_EXPECTED_FROM_NCI_OP08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF,
        "pnt_scope_refrozen": True,
        "explicit_nci_op08_material_required": True,
        "nci_op08_default_builder_call_allowed": False,
        "nci_op08_default_material_synthesis_allowed": False,
        "selected_handoff_or_stop_execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "pnt_op00_scope_confirmed": True,
        "pnt_op00_explicit_input_boundary_confirmed": True,
        "pnt_op00_no_execution_boundary_confirmed": True,
        "pnt_op00_no_touch_boundary_confirmed": True,
        "pnt_op00_no_promotion_boundary_confirmed": True,
        "source_mode_local_received_zip_only_confirmed": True,
        "github_connection_check_not_required_by_mash_instruction": True,
        "github_connection_check_performed": False,
        "pnt_op00_does_not_intake_nci_op08_material": True,
        "pnt_op00_does_not_synthesize_nci_op08_material": True,
        "pnt_op00_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op00_does_not_call_dhr_op05": True,
        "pnt_op00_does_not_start_p8_question_design": True,
        "pnt_op00_does_not_change_api_db_rn_runtime_response_key": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP00 scope / explicit-input / no-execution refreeze contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP00_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP00")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP00_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP00_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP00",
    )
    for key in (
        "pnt_scope_refrozen",
        "explicit_nci_op08_material_required",
        "pnt_op00_scope_confirmed",
        "pnt_op00_explicit_input_boundary_confirmed",
        "pnt_op00_no_execution_boundary_confirmed",
        "pnt_op00_no_touch_boundary_confirmed",
        "pnt_op00_no_promotion_boundary_confirmed",
        "source_mode_local_received_zip_only_confirmed",
        "github_connection_check_not_required_by_mash_instruction",
        "pnt_op00_does_not_intake_nci_op08_material",
        "pnt_op00_does_not_synthesize_nci_op08_material",
        "pnt_op00_does_not_execute_selected_handoff_or_stop",
        "pnt_op00_does_not_call_dhr_op05",
        "pnt_op00_does_not_start_p8_question_design",
        "pnt_op00_does_not_change_api_db_rn_runtime_response_key",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP00 required true boundary changed: {key}")
    for key in (
        "nci_op08_default_builder_call_allowed",
        "nci_op08_default_material_synthesis_allowed",
        "selected_handoff_or_stop_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "p8_question_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "github_connection_check_performed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP00 required false boundary changed: {key}")
    for field, count_field in (
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP00 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP00_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP00_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP00 next step must be PNT-OP01")
    return True


def build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake(
    *,
    nci_op08_bodyfree_selected_candidate_intake_result_memo_closure: Mapping[str, Any] | None = None,
    nci_op08_bodyfree_result_memo_closure: Mapping[str, Any] | None = None,
    bodyfree_selected_candidate_intake_result_memo_closure: Mapping[str, Any] | None = None,
    pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08: Mapping[str, Any] | None = None,
    scope_explicit_input_no_execution_refreeze_after_nci_op08: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Intake an explicit NCI-OP08 body-free closure without synthesizing NCI material."""

    op00_input = (
        pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08
        or scope_explicit_input_no_execution_refreeze_after_nci_op08
    )
    op00 = dict(op00_input) if isinstance(op00_input, Mapping) else build_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08(review_session_id=review_session_id)
    op00_present = isinstance(op00, Mapping)
    op00_valid = _op00_contract_valid(op00)

    op08_input = (
        nci_op08_bodyfree_selected_candidate_intake_result_memo_closure
        or nci_op08_bodyfree_result_memo_closure
        or bodyfree_selected_candidate_intake_result_memo_closure
    )
    op08_present = isinstance(op08_input, Mapping)
    op08 = dict(op08_input) if op08_present else {}
    op08_contract_valid = _nci_op08_contract_valid(op08) if op08_present else False
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(
        op08,
        path="nci_op08_bodyfree_selected_candidate_intake_result_memo_closure",
    )

    op08_status_ref = _clean_ref(op08.get("nci_op08_status_ref"), default="nci_op08_status_missing", max_length=360)
    op08_closed = bool(op08.get("nci_op08_closed_bodyfree_stopped") is True)
    op08_waiting = bool(op08.get("nci_op08_waiting_for_input_refs") is True)
    op08_repair = bool(op08.get("nci_op08_repair_required") is True)
    op08_blocked = bool(op08.get("nci_op08_blocked_bodyfree_promotion_autorun") is True)
    selected_ref = _clean_ref(op08.get("selected_handoff_or_stop_ref"), default="", max_length=360)
    selected_kind = _clean_ref(op08.get("selected_handoff_or_stop_kind_ref"), default="", max_length=360)
    selected_not_executed_present = "selected_handoff_or_stop_not_executed" in op08

    status_ref, reasons, blockers, next_required_step = _pnt_op01_status_reason_blocker_next(
        op00_valid=op00_valid,
        op08_present=op08_present,
        op08_contract_valid=op08_contract_valid,
        op08_status_ref=op08_status_ref,
        op08_closed=op08_closed,
        op08_waiting=op08_waiting,
        op08_repair=op08_repair,
        op08_blocked=op08_blocked,
        selected_handoff_or_stop_ref=selected_ref,
        selected_handoff_or_stop_kind_ref=selected_kind,
        selected_handoff_or_stop_not_executed_present=selected_not_executed_present,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    ready = status_ref == P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_READY_FOR_OP02_REF
    waiting_explicit = status_ref == P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_EXPLICIT_NCI_OP08_CLOSURE_REF
    waiting_nci = status_ref == P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_WAITING_FOR_NCI_OP08_TO_CLOSE_REF
    repair = status_ref == P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_REPAIR_NCI_OP08_REF
    blocked = status_ref == P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_BLOCKED_NCI_OP08_REF
    session_id = _safe_review_session_id(review_session_id or op08.get("review_session_id") or op00.get("review_session_id"))

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP01_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op00_material_present": op00_present,
        "op00_contract_valid": op00_valid,
        "op00_schema_version": _clean_ref(op00.get("schema_version"), default="pnt_op00_schema_missing", max_length=260),
        "op00_material_ref": _clean_ref(op00.get("material_id"), default="pnt_op00_material_missing", max_length=260),
        "op00_next_required_step": _clean_ref(op00.get("next_required_step"), default="pnt_op00_next_required_step_missing", max_length=360),
        "explicit_nci_op08_material_required": True,
        "nci_op08_default_builder_call_allowed": False,
        "nci_op08_default_material_synthesis_allowed": False,
        "nci_op08_default_builder_called_here": False,
        "nci_op08_default_material_synthesized_here": False,
        "nci_op08_material_present": op08_present,
        "nci_op08_contract_valid": op08_contract_valid,
        "nci_op08_schema_version": _clean_ref(op08.get("schema_version"), default="nci_op08_schema_missing", max_length=260),
        "nci_op08_material_ref": _clean_ref(op08.get("material_id"), default="nci_op08_material_missing", max_length=260),
        "nci_op08_operation_step_ref": _clean_ref(op08.get("operation_step_ref"), default="nci_op08_operation_step_missing", max_length=360),
        "nci_op08_status_ref": op08_status_ref,
        "bodyfree_selected_candidate_intake_closure_status_ref": _clean_ref(op08.get("bodyfree_selected_candidate_intake_closure_status_ref"), default="nci_op08_closure_status_missing", max_length=360),
        "nci_op08_closed_bodyfree_stopped": op08_closed,
        "nci_op08_waiting_for_input_refs": op08_waiting,
        "nci_op08_repair_required": op08_repair,
        "nci_op08_blocked_bodyfree_promotion_autorun": op08_blocked,
        "selected_nci_status_ref": _clean_ref(op08.get("selected_nci_status_ref"), default="selected_nci_status_missing", max_length=360),
        "selected_nci_lane_ref": _clean_ref(op08.get("selected_nci_lane_ref"), default="selected_nci_lane_missing", max_length=360),
        "selected_handoff_or_stop_ref": selected_ref or "selected_handoff_or_stop_missing",
        "selected_handoff_or_stop_kind_ref": selected_kind or "selected_handoff_or_stop_kind_missing",
        "selected_handoff_or_stop_ref_present": bool(selected_ref),
        "selected_handoff_or_stop_kind_ref_present": bool(selected_kind),
        "selected_handoff_or_stop_not_executed": bool(op08.get("selected_handoff_or_stop_not_executed") is True),
        "selected_handoff_or_stop_not_executed_present": selected_not_executed_present,
        "selected_next_design_or_stop_ref": _clean_ref(op08.get("selected_next_design_or_stop_ref"), default="selected_next_design_or_stop_missing", max_length=360),
        "selected_next_design_or_stop_kind_ref": _clean_ref(op08.get("selected_next_design_or_stop_kind_ref"), default="selected_next_design_or_stop_kind_missing", max_length=360),
        "selected_next_design_or_stop_not_executed": bool(op08.get("selected_next_design_or_stop_not_executed") is True),
        "rdb08_selected_next_stage_candidate_ref": _clean_ref(op08.get("rdb08_selected_next_stage_candidate_ref"), default="rdb08_selected_next_stage_candidate_missing", max_length=360),
        "rdb08_selected_next_stage_candidate_kind_ref": _clean_ref(op08.get("rdb08_selected_next_stage_candidate_kind_ref"), default="rdb08_selected_next_stage_candidate_kind_missing", max_length=360),
        "rdb08_selected_next_stage_candidate_not_executed": bool(op08.get("rdb08_selected_next_stage_candidate_not_executed") is True),
        "op07_handoff_or_stop_envelope_ref": _clean_ref(op08.get("op07_handoff_or_stop_envelope_ref"), default="op07_handoff_or_stop_envelope_missing", max_length=360),
        "op07_handoff_or_stop_envelope_kind_ref": _clean_ref(op08.get("op07_handoff_or_stop_envelope_kind_ref"), default="op07_handoff_or_stop_envelope_kind_missing", max_length=360),
        "op07_handoff_or_stop_envelope_bodyfree": bool(op08.get("op07_handoff_or_stop_envelope_bodyfree") is True),
        "op07_handoff_envelope_present": bool(op08.get("op07_handoff_envelope_present") is True),
        "op07_stop_envelope_present": bool(op08.get("op07_stop_envelope_present") is True),
        "validation_command_summary_refs": list(op08.get("validation_command_summary_refs") or ()),
        "validation_command_summary_ref_count": len(op08.get("validation_command_summary_refs") or ()),
        "target_test_result_status_ref": _clean_ref(op08.get("target_test_result_status_ref"), default="not_run", max_length=120),
        "selected_regression_result_status_ref": _clean_ref(op08.get("selected_regression_result_status_ref"), default="not_run", max_length=120),
        "compileall_result_status_ref": _clean_ref(op08.get("compileall_result_status_ref"), default="not_run", max_length=120),
        "combined_run_status_ref": _clean_ref(op08.get("combined_run_status_ref"), default="not_run", max_length=120),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "nci_op08_does_not_execute_handoff_or_stop_envelope": bool(op08.get("nci_op08_does_not_execute_handoff_or_stop_envelope") is True),
        "nci_op08_does_not_execute_selected_next_stage_candidate": bool(op08.get("nci_op08_does_not_execute_selected_next_stage_candidate") is True),
        "nci_op08_does_not_call_dhr_op05": bool(op08.get("nci_op08_does_not_call_dhr_op05") is True),
        "nci_op08_does_not_call_dhr_op06": bool(op08.get("nci_op08_does_not_call_dhr_op06") is True),
        "nci_op08_does_not_execute_dmd_r52_or_release": bool(op08.get("nci_op08_does_not_execute_dmd_r52_or_release") is True),
        "nci_op08_does_not_start_actual_review": bool(op08.get("nci_op08_does_not_start_actual_review") is True),
        "nci_op08_does_not_request_raw_evidence": bool(op08.get("nci_op08_does_not_request_raw_evidence") is True),
        "nci_op08_does_not_execute_repair": bool(op08.get("nci_op08_does_not_execute_repair") is True),
        "nci_op08_does_not_start_p5_p6_p8_p7_or_release": bool(op08.get("nci_op08_does_not_start_p5_p6_p8_p7_or_release") is True),
        "nci_op08_does_not_materialize_p8_question_spec": bool(op08.get("nci_op08_does_not_materialize_p8_question_spec") is True),
        "nci_op08_does_not_change_api_db_rn_runtime_response_key": bool(op08.get("nci_op08_does_not_change_api_db_rn_runtime_response_key") is True),
        "p8_question_substitution_allowed": bool(op08.get("p8_question_substitution_allowed") is True),
        "p8_start_allowed": bool(op08.get("p8_start_allowed") is True),
        "release_allowed": bool(op08.get("release_allowed") is True),
        "question_text_materialized": bool(op08.get("question_text_materialized") is True),
        "nci_op08_input_forbidden_payload_key_path_refs": forbidden_paths,
        "nci_op08_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "nci_op08_input_body_like_value_path_refs": body_like_paths,
        "nci_op08_input_body_like_value_path_count": len(body_like_paths),
        "nci_op08_input_promotion_claim_refs": promotion_claims,
        "nci_op08_input_promotion_claim_ref_count": len(promotion_claims),
        "nci_op08_input_no_touch_mutation_path_refs": no_touch_paths,
        "nci_op08_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pnt_op01_status_ref": status_ref,
        "bodyfree_nci_op08_closure_intake_status_ref": status_ref,
        "pnt_op01_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP01_ALLOWED_STATUS_REFS),
        "pnt_op01_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP01_ALLOWED_STATUS_REFS),
        "pnt_op01_ready_for_handoff_or_stop_shape_validation": ready,
        "pnt_op01_waiting_for_explicit_nci_op08_closure": waiting_explicit,
        "pnt_op01_waiting_for_nci_op08_to_close": waiting_nci,
        "pnt_op01_repair_required": repair,
        "pnt_op01_bodyfree_leak_promotion_or_autorun_blocked": blocked,
        "pnt_op01_reason_refs": _dedupe_clean_refs(reasons, max_length=360),
        "pnt_op01_reason_ref_count": len(_dedupe_clean_refs(reasons, max_length=360)),
        "pnt_op01_blocker_refs": _dedupe_clean_refs(blockers, max_length=360),
        "pnt_op01_blocker_ref_count": len(_dedupe_clean_refs(blockers, max_length=360)),
        "pnt_op01_does_not_validate_selected_handoff_or_stop_shape": True,
        "pnt_op01_does_not_resolve_selected_handoff_or_stop_lane": True,
        "pnt_op01_does_not_materialize_next_boundary_selection": True,
        "pnt_op01_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op01_does_not_call_dhr_op05": True,
        "pnt_op01_does_not_call_dhr_op06": True,
        "pnt_op01_does_not_execute_dmd_r52_or_release": True,
        "pnt_op01_does_not_start_actual_review": True,
        "pnt_op01_does_not_request_raw_evidence": True,
        "pnt_op01_does_not_execute_repair": True,
        "pnt_op01_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op01_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op01_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP01 explicit NCI-OP08 body-free result memo closure intake contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP01_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP01")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP01_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP01_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP01",
    )
    if data.get("op00_schema_version") != P7_R54_AHR_POST_NCI_PNT_OP00_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 OP00 schema version changed")
    if data.get("op00_contract_valid") is True and data.get("op00_next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP01_STEP_REF:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 OP00 next step changed")
    if data.get("bodyfree_nci_op08_closure_intake_status_ref") != data.get("pnt_op01_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 status alias changed")
    if tuple(data.get("pnt_op01_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP01_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 allowed status refs changed")
    for key in (
        "explicit_nci_op08_material_required",
        "pnt_op01_does_not_validate_selected_handoff_or_stop_shape",
        "pnt_op01_does_not_resolve_selected_handoff_or_stop_lane",
        "pnt_op01_does_not_materialize_next_boundary_selection",
        "pnt_op01_does_not_execute_selected_handoff_or_stop",
        "pnt_op01_does_not_call_dhr_op05",
        "pnt_op01_does_not_call_dhr_op06",
        "pnt_op01_does_not_execute_dmd_r52_or_release",
        "pnt_op01_does_not_start_actual_review",
        "pnt_op01_does_not_request_raw_evidence",
        "pnt_op01_does_not_execute_repair",
        "pnt_op01_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op01_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op01_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP01 required true boundary changed: {key}")
    for key in (
        "nci_op08_default_builder_call_allowed",
        "nci_op08_default_material_synthesis_allowed",
        "nci_op08_default_builder_called_here",
        "nci_op08_default_material_synthesized_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP01 forbidden claim changed: {key}")
    for field, count_field in (
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("nci_op08_input_forbidden_payload_key_path_refs", "nci_op08_input_forbidden_payload_key_path_count"),
        ("nci_op08_input_body_like_value_path_refs", "nci_op08_input_body_like_value_path_count"),
        ("nci_op08_input_promotion_claim_refs", "nci_op08_input_promotion_claim_ref_count"),
        ("nci_op08_input_no_touch_mutation_path_refs", "nci_op08_input_no_touch_mutation_path_count"),
        ("pnt_op01_reason_refs", "pnt_op01_reason_ref_count"),
        ("pnt_op01_blocker_refs", "pnt_op01_blocker_ref_count"),
        ("pnt_op01_allowed_status_refs", "pnt_op01_allowed_status_ref_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP01 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP01_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP01_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 not-yet steps changed")
    status_ref = data.get("pnt_op01_status_ref")
    flags = [
        data.get("pnt_op01_ready_for_handoff_or_stop_shape_validation") is True,
        data.get("pnt_op01_waiting_for_explicit_nci_op08_closure") is True,
        data.get("pnt_op01_waiting_for_nci_op08_to_close") is True,
        data.get("pnt_op01_repair_required") is True,
        data.get("pnt_op01_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP01_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 exactly one intake status branch must be selected")
    if status_ref == P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_READY_FOR_OP02_REF:
        if data.get("op00_contract_valid") is not True or data.get("nci_op08_contract_valid") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 ready branch requires valid OP00 and NCI-OP08")
        if data.get("nci_op08_closed_bodyfree_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 ready branch requires closed NCI-OP08")
        if data.get("selected_handoff_or_stop_ref_present") is not True or data.get("selected_handoff_or_stop_kind_ref_present") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 ready branch requires selected handoff-or-stop refs")
        if data.get("selected_handoff_or_stop_not_executed_present") is not True or data.get("selected_handoff_or_stop_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 ready branch requires non-executed selected handoff-or-stop")
        if data.get("pnt_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 ready branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 ready next step changed")
    else:
        if not data.get("pnt_op01_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 non-ready branch must carry blockers")
        if data.get("next_required_step") == P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 non-ready branch cannot continue to OP02")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_OP01_STATUS_BLOCKED_NCI_OP08_REF:
        for field in (
            "nci_op08_input_forbidden_payload_key_path_refs",
            "nci_op08_input_body_like_value_path_refs",
            "nci_op08_input_promotion_claim_refs",
            "nci_op08_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP01 non-blocked branch cannot carry body-free scan blockers")
    return True



def _op01_contract_valid(op01: Mapping[str, Any] | None) -> bool:
    if not isinstance(op01, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract(op01) is True
    except ValueError:
        return False


def _op02_contract_valid(op02: Mapping[str, Any] | None) -> bool:
    if not isinstance(op02, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation_contract(op02) is True
    except ValueError:
        return False


def _lane_flags(selected_lane_ref: str) -> dict[str, bool]:
    return {
        "dhr_op05_manual_handoff_boundary_design_candidate_present": selected_lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_REF,
        "retry_start_route_boundary_candidate_present": selected_lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_RETRY_START_ROUTE_CANDIDATE_REF,
        "wait_external_bodyfree_claim_hold_present": selected_lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
        "repair_boundary_candidate_present": selected_lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_REPAIR_BOUNDARY_CANDIDATE_REF,
        "manual_hold_unresolved_stop_present": selected_lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_MANUAL_HOLD_UNRESOLVED_REF,
        "blocked_bodyfree_promotion_autorun_stop_present": selected_lane_ref == P7_R54_AHR_POST_NCI_PNT_LANE_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
    }


def _op02_status_reason_blocker_next(
    *,
    op01_present: bool,
    op01_valid: bool,
    op01_ready: bool,
    lane_allowed: bool,
    selected_ref_present: bool,
    selected_ref_allowed: bool,
    selected_kind_present: bool,
    selected_kind_allowed: bool,
    selected_not_executed: bool,
    selected_next_not_executed: bool,
    rdb_candidate_not_executed: bool,
    op07_envelope_bodyfree: bool,
    selected_ref_matches_lane: bool,
    selected_ref_matches_next: bool,
    selected_kind_matches_lane: bool,
    next_kind_matches_lane: bool,
    envelope_kind_consistent: bool,
    envelope_presence_consistent: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
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
    if selected_not_executed is not True:
        blockers.append("selected_handoff_or_stop_not_executed_false")
    if selected_next_not_executed is not True:
        blockers.append("selected_next_design_or_stop_not_executed_false")
    if rdb_candidate_not_executed is not True:
        blockers.append("rdb08_selected_next_stage_candidate_not_executed_false")
    if op07_envelope_bodyfree is not True:
        blockers.append("op07_handoff_or_stop_envelope_not_bodyfree")
    if blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
            ["selected_handoff_or_stop_shape_blocked_before_lane_resolver"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_SHAPE_REF,
        )

    repair_blockers: list[str] = []
    if not op01_present:
        repair_blockers.append("pnt_op01_material_missing")
    if op01_present and not op01_valid:
        repair_blockers.append("pnt_op01_contract_invalid")
    if op01_valid and not op01_ready:
        repair_blockers.append("pnt_op01_not_ready_for_selected_handoff_or_stop_shape_validation")
    if not lane_allowed:
        repair_blockers.append("selected_nci_lane_ref_unknown_or_not_allowed")
    if not selected_ref_present:
        repair_blockers.append("selected_handoff_or_stop_ref_missing")
    elif not selected_ref_allowed:
        repair_blockers.append("selected_handoff_or_stop_ref_unknown_or_not_allowed")
    if not selected_kind_present:
        repair_blockers.append("selected_handoff_or_stop_kind_ref_missing")
    elif not selected_kind_allowed:
        repair_blockers.append("selected_handoff_or_stop_kind_ref_unknown_or_not_allowed")
    if lane_allowed and selected_ref_allowed and not selected_ref_matches_lane:
        repair_blockers.append("selected_handoff_or_stop_ref_does_not_match_selected_nci_lane")
    if selected_ref_present and not selected_ref_matches_next:
        repair_blockers.append("selected_handoff_or_stop_ref_and_selected_next_design_or_stop_ref_mismatch")
    if lane_allowed and selected_kind_allowed and not selected_kind_matches_lane:
        repair_blockers.append("selected_handoff_or_stop_kind_ref_does_not_match_expected_envelope_kind")
    if lane_allowed and not next_kind_matches_lane:
        repair_blockers.append("selected_next_design_or_stop_kind_ref_does_not_match_selected_nci_lane")
    if selected_kind_allowed and not envelope_kind_consistent:
        repair_blockers.append("op07_handoff_or_stop_envelope_kind_ref_mismatch")
    if lane_allowed and selected_kind_allowed and not envelope_presence_consistent:
        repair_blockers.append("op07_handoff_or_stop_envelope_presence_mismatch")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_REPAIR_REQUIRED_REF,
            ["selected_handoff_or_stop_shape_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_SHAPE_REF,
        )
    return (
        P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_SHAPE_VALID_STOPPED_REF,
        ["selected_handoff_or_stop_shape_valid_ready_for_pnt_op03_lane_resolver"],
        [],
        P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF,
    )


def build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation(
    pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PNT-OP02 selected_handoff_or_stop shape validation material.

    PNT-OP02 reads only the explicit PNT-OP01 intake material.  It does not call
    NCI-OP08 builders, does not synthesize NCI material, and does not resolve the
    selected lane into a next-boundary decision yet.
    """

    session_id = _safe_review_session_id(review_session_id)
    op01 = pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake
    op01_present = isinstance(op01, Mapping)
    op01_valid = _op01_contract_valid(op01)
    op01_ready = bool(op01_valid and op01 and op01.get("pnt_op01_ready_for_handoff_or_stop_shape_validation") is True)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op01 or {}, path="pnt_op01")

    lane_ref = _clean_ref(op01.get("selected_nci_lane_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=260)
    selected_ref = _clean_ref(op01.get("selected_handoff_or_stop_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360)
    selected_kind = _clean_ref(op01.get("selected_handoff_or_stop_kind_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360)
    selected_next_ref = _clean_ref(op01.get("selected_next_design_or_stop_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360)
    selected_next_kind = _clean_ref(op01.get("selected_next_design_or_stop_kind_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360)
    op07_kind = _clean_ref(op01.get("op07_handoff_or_stop_envelope_kind_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360)

    expected_ref = P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP.get(lane_ref, "missing")
    expected_kind = P7_R54_AHR_POST_NCI_PNT_LANE_TO_ENVELOPE_KIND_REF_MAP.get(lane_ref, "missing")
    expected_next_kind = P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP.get(lane_ref, "missing")
    expected_group = P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP.get(lane_ref, "missing")

    lane_allowed = lane_ref in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS
    selected_ref_present = selected_ref not in ("", "missing")
    selected_ref_allowed = selected_ref in P7_R54_AHR_POST_NCI_PNT_ALLOWED_SELECTED_HANDOFF_OR_STOP_REFS
    selected_kind_present = selected_kind not in ("", "missing")
    selected_kind_allowed = selected_kind in (
        P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF,
        P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF,
    )
    selected_not_executed = bool(op01_present and op01 and op01.get("selected_handoff_or_stop_not_executed") is True)
    selected_next_not_executed = bool(op01_present and op01 and op01.get("selected_next_design_or_stop_not_executed") is True)
    rdb_candidate_not_executed = bool(op01_present and op01 and op01.get("rdb08_selected_next_stage_candidate_not_executed") is True)
    op07_envelope_bodyfree = bool(op01_present and op01 and op01.get("op07_handoff_or_stop_envelope_bodyfree") is True)
    selected_ref_matches_lane = bool(lane_allowed and selected_ref == expected_ref)
    selected_ref_matches_next = bool(selected_ref_present and selected_ref == selected_next_ref)
    selected_kind_matches_lane = bool(lane_allowed and selected_kind == expected_kind)
    next_kind_matches_lane = bool(lane_allowed and selected_next_kind == expected_next_kind)
    envelope_kind_consistent = bool(selected_kind_allowed and op07_kind == selected_kind)
    envelope_presence_consistent = bool(
        (expected_kind == P7_R54_AHR_POST_NCI_PNT_HANDOFF_ENVELOPE_KIND_REF and op01_present and op01 and op01.get("op07_handoff_envelope_present") is True and op01.get("op07_stop_envelope_present") is False)
        or (expected_kind == P7_R54_AHR_POST_NCI_PNT_STOP_ENVELOPE_KIND_REF and op01_present and op01 and op01.get("op07_stop_envelope_present") is True and op01.get("op07_handoff_envelope_present") is False)
    )

    status_ref, reason_refs, blocker_refs, next_required_step = _op02_status_reason_blocker_next(
        op01_present=op01_present,
        op01_valid=op01_valid,
        op01_ready=op01_ready,
        lane_allowed=lane_allowed,
        selected_ref_present=selected_ref_present,
        selected_ref_allowed=selected_ref_allowed,
        selected_kind_present=selected_kind_present,
        selected_kind_allowed=selected_kind_allowed,
        selected_not_executed=selected_not_executed,
        selected_next_not_executed=selected_next_not_executed,
        rdb_candidate_not_executed=rdb_candidate_not_executed,
        op07_envelope_bodyfree=op07_envelope_bodyfree,
        selected_ref_matches_lane=selected_ref_matches_lane,
        selected_ref_matches_next=selected_ref_matches_next,
        selected_kind_matches_lane=selected_kind_matches_lane,
        next_kind_matches_lane=next_kind_matches_lane,
        envelope_kind_consistent=envelope_kind_consistent,
        envelope_presence_consistent=envelope_presence_consistent,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    shape_valid = status_ref == P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_SHAPE_VALID_STOPPED_REF

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP02_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op01_material_present": op01_present,
        "op01_contract_valid": op01_valid,
        "op01_schema_version": _clean_ref(op01.get("schema_version") if isinstance(op01, Mapping) else None, default="missing", max_length=260),
        "op01_material_ref": _clean_ref(op01.get("material_id") if isinstance(op01, Mapping) else None, default="missing", max_length=260),
        "op01_status_ref": _clean_ref(op01.get("pnt_op01_status_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=260),
        "op01_next_required_step": _clean_ref(op01.get("next_required_step") if isinstance(op01, Mapping) else None, default="missing", max_length=360),
        "op01_ready_for_handoff_or_stop_shape_validation": op01_ready,
        "selected_nci_lane_ref": lane_ref,
        "selected_nci_lane_allowed": lane_allowed,
        "selected_handoff_or_stop_ref": selected_ref,
        "selected_handoff_or_stop_ref_present": selected_ref_present,
        "selected_handoff_or_stop_ref_allowed": selected_ref_allowed,
        "selected_handoff_or_stop_kind_ref": selected_kind,
        "selected_handoff_or_stop_kind_ref_present": selected_kind_present,
        "selected_handoff_or_stop_kind_ref_allowed": selected_kind_allowed,
        "selected_handoff_or_stop_not_executed": selected_not_executed,
        "selected_next_design_or_stop_ref": selected_next_ref,
        "selected_next_design_or_stop_kind_ref": selected_next_kind,
        "selected_next_design_or_stop_not_executed": selected_next_not_executed,
        "selected_ref_matches_next_design_or_stop_ref": selected_ref_matches_next,
        "selected_next_design_or_stop_kind_matches_lane": next_kind_matches_lane,
        "rdb08_selected_next_stage_candidate_ref": _clean_ref(op01.get("rdb08_selected_next_stage_candidate_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360),
        "rdb08_selected_next_stage_candidate_kind_ref": _clean_ref(op01.get("rdb08_selected_next_stage_candidate_kind_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360),
        "rdb08_selected_next_stage_candidate_not_executed": rdb_candidate_not_executed,
        "op07_handoff_or_stop_envelope_ref": _clean_ref(op01.get("op07_handoff_or_stop_envelope_ref") if isinstance(op01, Mapping) else None, default="missing", max_length=360),
        "op07_handoff_or_stop_envelope_kind_ref": op07_kind,
        "op07_handoff_or_stop_envelope_bodyfree": op07_envelope_bodyfree,
        "op07_handoff_envelope_present": bool(op01_present and op01 and op01.get("op07_handoff_envelope_present") is True),
        "op07_stop_envelope_present": bool(op01_present and op01 and op01.get("op07_stop_envelope_present") is True),
        "expected_selected_handoff_or_stop_ref": expected_ref,
        "expected_selected_handoff_or_stop_kind_ref": expected_kind,
        "expected_selected_next_design_or_stop_kind_ref": expected_next_kind,
        "expected_envelope_group_ref": expected_group,
        "selected_handoff_or_stop_ref_matches_lane": selected_ref_matches_lane,
        "selected_handoff_or_stop_kind_matches_lane": selected_kind_matches_lane,
        "handoff_or_stop_envelope_kind_consistent": envelope_kind_consistent,
        "handoff_or_stop_envelope_presence_consistent": envelope_presence_consistent,
        "selected_handoff_or_stop_shape_valid": shape_valid,
        "pnt_op02_status_ref": status_ref,
        "bodyfree_selected_handoff_or_stop_shape_status_ref": status_ref,
        "pnt_op02_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP02_ALLOWED_STATUS_REFS),
        "pnt_op02_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP02_ALLOWED_STATUS_REFS),
        "pnt_op02_shape_valid_stopped": shape_valid,
        "pnt_op02_repair_required": status_ref == P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_REPAIR_REQUIRED_REF,
        "pnt_op02_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF,
        "pnt_op02_reason_refs": reason_refs,
        "pnt_op02_reason_ref_count": len(reason_refs),
        "pnt_op02_blocker_refs": blocker_refs,
        "pnt_op02_blocker_ref_count": len(blocker_refs),
        "op02_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op02_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op02_input_body_like_value_path_refs": list(body_like_paths),
        "op02_input_body_like_value_path_count": len(body_like_paths),
        "op02_input_promotion_claim_refs": list(promotion_claims),
        "op02_input_promotion_claim_ref_count": len(promotion_claims),
        "op02_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op02_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pnt_op02_does_not_resolve_selected_handoff_or_stop_lane": True,
        "pnt_op02_does_not_materialize_next_boundary_selection": True,
        "pnt_op02_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op02_does_not_call_dhr_op05": True,
        "pnt_op02_does_not_call_dhr_op06": True,
        "pnt_op02_does_not_execute_dmd_r52_or_release": True,
        "pnt_op02_does_not_start_actual_review": True,
        "pnt_op02_does_not_request_raw_evidence": True,
        "pnt_op02_does_not_execute_repair": True,
        "pnt_op02_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op02_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op02_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP02 selected_handoff_or_stop shape validation contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP02_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP02")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP02_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP02_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP02_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP02",
    )
    if data.get("bodyfree_selected_handoff_or_stop_shape_status_ref") != data.get("pnt_op02_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 status alias changed")
    if tuple(data.get("pnt_op02_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP02_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 allowed status refs changed")
    for key in (
        "pnt_op02_does_not_resolve_selected_handoff_or_stop_lane",
        "pnt_op02_does_not_materialize_next_boundary_selection",
        "pnt_op02_does_not_execute_selected_handoff_or_stop",
        "pnt_op02_does_not_call_dhr_op05",
        "pnt_op02_does_not_call_dhr_op06",
        "pnt_op02_does_not_execute_dmd_r52_or_release",
        "pnt_op02_does_not_start_actual_review",
        "pnt_op02_does_not_request_raw_evidence",
        "pnt_op02_does_not_execute_repair",
        "pnt_op02_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op02_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op02_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP02 required true boundary changed: {key}")
    for field, count_field in (
        ("pnt_op02_allowed_status_refs", "pnt_op02_allowed_status_ref_count"),
        ("pnt_op02_reason_refs", "pnt_op02_reason_ref_count"),
        ("pnt_op02_blocker_refs", "pnt_op02_blocker_ref_count"),
        ("op02_input_forbidden_payload_key_path_refs", "op02_input_forbidden_payload_key_path_count"),
        ("op02_input_body_like_value_path_refs", "op02_input_body_like_value_path_count"),
        ("op02_input_promotion_claim_refs", "op02_input_promotion_claim_ref_count"),
        ("op02_input_no_touch_mutation_path_refs", "op02_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP02 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP02_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP02_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 not-yet steps changed")

    status_ref = data.get("pnt_op02_status_ref")
    flags = [
        data.get("pnt_op02_shape_valid_stopped") is True,
        data.get("pnt_op02_repair_required") is True,
        data.get("pnt_op02_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP02_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 exactly one shape status branch must be selected")
    if status_ref == P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_SHAPE_VALID_STOPPED_REF:
        for key in (
            "op01_material_present",
            "op01_contract_valid",
            "op01_ready_for_handoff_or_stop_shape_validation",
            "selected_nci_lane_allowed",
            "selected_handoff_or_stop_ref_present",
            "selected_handoff_or_stop_ref_allowed",
            "selected_handoff_or_stop_kind_ref_present",
            "selected_handoff_or_stop_kind_ref_allowed",
            "selected_handoff_or_stop_not_executed",
            "selected_next_design_or_stop_not_executed",
            "rdb08_selected_next_stage_candidate_not_executed",
            "op07_handoff_or_stop_envelope_bodyfree",
            "selected_ref_matches_next_design_or_stop_ref",
            "selected_next_design_or_stop_kind_matches_lane",
            "selected_handoff_or_stop_ref_matches_lane",
            "selected_handoff_or_stop_kind_matches_lane",
            "handoff_or_stop_envelope_kind_consistent",
            "handoff_or_stop_envelope_presence_consistent",
            "selected_handoff_or_stop_shape_valid",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP02 valid branch shape flag changed: {key}")
        if data.get("pnt_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 valid branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 valid next step changed")
    elif status_ref == P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_REPAIR_REQUIRED_REF:
        if not data.get("pnt_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 repair branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_SHAPE_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 repair next step changed")
    else:
        if not data.get("pnt_op02_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 blocked branch must carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_SHAPE_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        for field in (
            "op02_input_forbidden_payload_key_path_refs",
            "op02_input_body_like_value_path_refs",
            "op02_input_promotion_claim_refs",
            "op02_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP02 non-blocked branch cannot carry scan blockers")
    return True


def _op03_status_reason_blocker_next(
    *,
    op02_present: bool,
    op02_valid: bool,
    op02_shape_valid: bool,
    op02_status_ref: str,
    lane_ref: str,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, str, str, str, str, bool, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op03_input_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op03_input_body_like_value_detected")
    if promotion_claims:
        blockers.append("op03_input_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op03_input_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op02_status_ref == P7_R54_AHR_POST_NCI_PNT_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("op02_shape_validation_blocked_before_lane_resolver")
    if blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF,
            "missing",
            "missing",
            "missing",
            "missing",
            False,
            ["selected_handoff_or_stop_lane_resolver_blocked_without_downstream_promotion"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_LANE_REF,
        )
    repair_blockers: list[str] = []
    if not op02_present:
        repair_blockers.append("pnt_op02_shape_material_missing")
    if op02_present and not op02_valid:
        repair_blockers.append("pnt_op02_shape_contract_invalid")
    if op02_valid and not op02_shape_valid:
        repair_blockers.append("pnt_op02_shape_not_valid_for_lane_resolver")
    if lane_ref not in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS:
        repair_blockers.append("selected_nci_lane_ref_unknown_or_not_allowed_for_resolver")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_STATUS_REPAIR_BOUNDARY_CANDIDATE_STOPPED_REF,
            "missing",
            "missing",
            "missing",
            "missing",
            False,
            ["selected_handoff_or_stop_lane_resolver_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_LANE_REF,
        )
    return (
        P7_R54_AHR_POST_NCI_PNT_LANE_TO_STATUS_REF_MAP[lane_ref],
        lane_ref,
        P7_R54_AHR_POST_NCI_PNT_LANE_TO_TRIAGE_KIND_REF_MAP[lane_ref],
        P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[lane_ref],
        P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP[lane_ref],
        True,
        ["selected_handoff_or_stop_lane_resolved_stopped_without_execution"],
        [],
        P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF,
    )


def build_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver(
    pnt_op02_selected_handoff_or_stop_shape_validation: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PNT-OP03 selected handoff-or-stop lane consistency resolver material."""

    session_id = _safe_review_session_id(review_session_id)
    op02 = pnt_op02_selected_handoff_or_stop_shape_validation
    op02_present = isinstance(op02, Mapping)
    op02_valid = _op02_contract_valid(op02)
    op02_status_ref = _clean_ref(op02.get("pnt_op02_status_ref") if isinstance(op02, Mapping) else None, default="missing", max_length=260)
    op02_shape_valid = bool(op02_valid and op02 and op02.get("selected_handoff_or_stop_shape_valid") is True)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op02 or {}, path="pnt_op02")
    lane_ref = _clean_ref(op02.get("selected_nci_lane_ref") if isinstance(op02, Mapping) else None, default="missing", max_length=260)

    status_ref, selected_lane_ref, triage_kind_ref, outcome_group_ref, next_boundary_ref, resolved, reason_refs, blocker_refs, next_required_step = _op03_status_reason_blocker_next(
        op02_present=op02_present,
        op02_valid=op02_valid,
        op02_shape_valid=op02_shape_valid,
        op02_status_ref=op02_status_ref,
        lane_ref=lane_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    flags = _lane_flags(selected_lane_ref)
    selected_kind = _clean_ref(op02.get("selected_handoff_or_stop_kind_ref") if isinstance(op02, Mapping) else None, default="missing", max_length=360)
    selected_not_executed = bool(op02_valid and op02 and op02.get("selected_handoff_or_stop_not_executed") is True)
    next_candidate_kind = P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP.get(selected_lane_ref, "missing")
    if not resolved:
        selected_kind = "missing"
        selected_not_executed = False
        next_candidate_kind = "missing"

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP03_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op02_material_present": op02_present,
        "op02_contract_valid": op02_valid,
        "op02_schema_version": _clean_ref(op02.get("schema_version") if isinstance(op02, Mapping) else None, default="missing", max_length=260),
        "op02_material_ref": _clean_ref(op02.get("material_id") if isinstance(op02, Mapping) else None, default="missing", max_length=260),
        "op02_status_ref": op02_status_ref,
        "op02_next_required_step": _clean_ref(op02.get("next_required_step") if isinstance(op02, Mapping) else None, default="missing", max_length=360),
        "op02_shape_valid_stopped": op02_shape_valid,
        "selected_pnt_status_ref": status_ref,
        "selected_pnt_lane_ref": selected_lane_ref,
        "selected_pnt_triage_kind_ref": triage_kind_ref,
        "selected_pnt_outcome_group_ref": outcome_group_ref,
        "selected_pnt_lane_resolved": resolved,
        "selected_handoff_or_stop_ref": next_boundary_ref,
        "selected_handoff_or_stop_kind_ref": selected_kind,
        "selected_handoff_or_stop_not_executed": selected_not_executed,
        "selected_post_nci_next_boundary_candidate_ref": next_boundary_ref,
        "selected_post_nci_next_boundary_candidate_kind_ref": next_candidate_kind,
        "selected_post_nci_next_boundary_not_executed": bool(resolved),
        "selected_post_nci_next_boundary_execution_allowed_here": False,
        "selected_post_nci_next_boundary_materialized_here": False,
        "allowed_pnt_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP03_ALLOWED_STATUS_REFS),
        "allowed_pnt_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP03_ALLOWED_STATUS_REFS),
        "allowed_pnt_lane_refs": list(P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS),
        "allowed_pnt_lane_ref_count": len(P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS),
        "allowed_pnt_outcome_group_refs": list(P7_R54_AHR_POST_NCI_PNT_ALLOWED_OUTCOME_GROUP_REFS),
        "allowed_pnt_outcome_group_ref_count": len(P7_R54_AHR_POST_NCI_PNT_ALLOWED_OUTCOME_GROUP_REFS),
        "pnt_op03_lane_flag_refs": list(P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS),
        "pnt_op03_lane_flag_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS),
        **flags,
        "pnt_op03_status_ref": status_ref,
        "bodyfree_selected_handoff_or_stop_lane_resolver_status_ref": status_ref,
        "pnt_op03_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP03_ALLOWED_STATUS_REFS),
        "pnt_op03_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP03_ALLOWED_STATUS_REFS),
        "pnt_op03_dhr_op05_manual_handoff_boundary_design_candidate_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_STATUS_DHR_OP05_BOUNDARY_DESIGN_CANDIDATE_STOPPED_REF,
        "pnt_op03_retry_start_route_boundary_candidate_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_STATUS_RETRY_START_ROUTE_BOUNDARY_CANDIDATE_STOPPED_REF,
        "pnt_op03_wait_external_bodyfree_claim_hold_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_STATUS_WAIT_EXTERNAL_BODYFREE_CLAIM_HOLD_STOPPED_REF,
        "pnt_op03_repair_boundary_candidate_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_STATUS_REPAIR_BOUNDARY_CANDIDATE_STOPPED_REF,
        "pnt_op03_manual_hold_unresolved_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_STATUS_MANUAL_HOLD_UNRESOLVED_STOPPED_REF,
        "pnt_op03_blocked_bodyfree_promotion_autorun_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF,
        "pnt_op03_reason_refs": reason_refs,
        "pnt_op03_reason_ref_count": len(reason_refs),
        "pnt_op03_blocker_refs": blocker_refs,
        "pnt_op03_blocker_ref_count": len(blocker_refs),
        "op03_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op03_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op03_input_body_like_value_path_refs": list(body_like_paths),
        "op03_input_body_like_value_path_count": len(body_like_paths),
        "op03_input_promotion_claim_refs": list(promotion_claims),
        "op03_input_promotion_claim_ref_count": len(promotion_claims),
        "op03_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op03_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pnt_op03_does_not_materialize_next_boundary_selection": True,
        "pnt_op03_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op03_does_not_call_dhr_op05": True,
        "pnt_op03_does_not_call_dhr_op06": True,
        "pnt_op03_does_not_execute_dmd_r52_or_release": True,
        "pnt_op03_does_not_start_actual_review": True,
        "pnt_op03_does_not_request_raw_evidence": True,
        "pnt_op03_does_not_execute_repair": True,
        "pnt_op03_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op03_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op03_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP03 selected handoff-or-stop lane consistency resolver contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP03_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP03")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP03_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP03_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP03_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP03",
    )
    if data.get("bodyfree_selected_handoff_or_stop_lane_resolver_status_ref") != data.get("pnt_op03_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 status alias changed")
    if data.get("selected_pnt_status_ref") != data.get("pnt_op03_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 selected status alias changed")
    if tuple(data.get("pnt_op03_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP03_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 allowed status refs changed")
    for key in (
        "pnt_op03_does_not_materialize_next_boundary_selection",
        "pnt_op03_does_not_execute_selected_handoff_or_stop",
        "pnt_op03_does_not_call_dhr_op05",
        "pnt_op03_does_not_call_dhr_op06",
        "pnt_op03_does_not_execute_dmd_r52_or_release",
        "pnt_op03_does_not_start_actual_review",
        "pnt_op03_does_not_request_raw_evidence",
        "pnt_op03_does_not_execute_repair",
        "pnt_op03_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op03_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op03_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP03 required true boundary changed: {key}")
    for field, count_field in (
        ("allowed_pnt_status_refs", "allowed_pnt_status_ref_count"),
        ("allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count"),
        ("allowed_pnt_outcome_group_refs", "allowed_pnt_outcome_group_ref_count"),
        ("pnt_op03_lane_flag_refs", "pnt_op03_lane_flag_ref_count"),
        ("pnt_op03_allowed_status_refs", "pnt_op03_allowed_status_ref_count"),
        ("pnt_op03_reason_refs", "pnt_op03_reason_ref_count"),
        ("pnt_op03_blocker_refs", "pnt_op03_blocker_ref_count"),
        ("op03_input_forbidden_payload_key_path_refs", "op03_input_forbidden_payload_key_path_count"),
        ("op03_input_body_like_value_path_refs", "op03_input_body_like_value_path_count"),
        ("op03_input_promotion_claim_refs", "op03_input_promotion_claim_ref_count"),
        ("op03_input_no_touch_mutation_path_refs", "op03_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP03 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP03_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP03_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 not-yet steps changed")
    status_ref = data.get("pnt_op03_status_ref")
    branch_flags = [
        data.get("pnt_op03_dhr_op05_manual_handoff_boundary_design_candidate_stopped") is True,
        data.get("pnt_op03_retry_start_route_boundary_candidate_stopped") is True,
        data.get("pnt_op03_wait_external_bodyfree_claim_hold_stopped") is True,
        data.get("pnt_op03_repair_boundary_candidate_stopped") is True,
        data.get("pnt_op03_manual_hold_unresolved_stopped") is True,
        data.get("pnt_op03_blocked_bodyfree_promotion_autorun_stopped") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP03_ALLOWED_STATUS_REFS or sum(branch_flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 exactly one resolver status branch must be selected")
    resolved = data.get("selected_pnt_lane_resolved") is True
    lane_flag_sum = sum(data.get(key) is True for key in P7_R54_AHR_POST_NCI_PNT_OP03_LANE_FLAG_REFS)
    if resolved:
        lane_ref = data.get("selected_pnt_lane_ref")
        if lane_ref not in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 resolved lane is not allowed")
        if lane_flag_sum != 1:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 resolved lane must set exactly one lane flag")
        expected_flags = _lane_flags(str(lane_ref))
        if any(data.get(key) is not value for key, value in expected_flags.items()):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 lane flags do not match selected lane")
        if data.get("selected_pnt_status_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_STATUS_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 status does not match selected lane")
        if data.get("selected_pnt_outcome_group_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 outcome group does not match selected lane")
        if data.get("selected_handoff_or_stop_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 selected handoff-or-stop does not match selected lane")
        if data.get("selected_post_nci_next_boundary_candidate_ref") != data.get("selected_handoff_or_stop_ref"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 next boundary candidate ref changed")
        if data.get("selected_post_nci_next_boundary_candidate_kind_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 next boundary candidate kind changed")
        if data.get("selected_handoff_or_stop_not_executed") is not True or data.get("selected_post_nci_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 resolved lane must remain non-executed")
        if data.get("selected_post_nci_next_boundary_execution_allowed_here") is not False or data.get("selected_post_nci_next_boundary_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 resolved lane cannot execute/materialize OP04")
        if data.get("pnt_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 resolved branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 resolved next step changed")
    else:
        if lane_flag_sum != 0:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 unresolved branch cannot set lane flags")
        if not data.get("pnt_op03_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 unresolved branch must carry blockers")
        if data.get("next_required_step") not in (
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_SELECTED_HANDOFF_OR_STOP_LANE_REF,
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_SELECTED_HANDOFF_OR_STOP_LANE_REF,
        ):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 unresolved next step changed")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_STOPPED_REF or resolved:
        for field in (
            "op03_input_forbidden_payload_key_path_refs",
            "op03_input_body_like_value_path_refs",
            "op03_input_promotion_claim_refs",
            "op03_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP03 non-blocked scan branch cannot carry scan blockers")
    return True


def _op03_contract_valid(op03: Mapping[str, Any] | None) -> bool:
    if not isinstance(op03, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract(op03) is True
    except ValueError:
        return False


def _op04_contract_valid(op04: Mapping[str, Any] | None) -> bool:
    if not isinstance(op04, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization_contract(op04) is True
    except ValueError:
        return False


def _op04_status_reason_blocker_next(
    *,
    op03_present: bool,
    op03_valid: bool,
    op03_resolved: bool,
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
            P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF,
            ["next_boundary_selection_blocked_before_guard_without_downstream_promotion"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NEXT_BOUNDARY_SELECTION_REF,
        )

    repair_blockers: list[str] = []
    if not op03_present:
        repair_blockers.append("pnt_op03_lane_resolver_material_missing")
    if op03_present and not op03_valid:
        repair_blockers.append("pnt_op03_lane_resolver_contract_invalid")
    if op03_valid and not op03_resolved:
        repair_blockers.append("pnt_op03_lane_not_resolved_for_next_boundary_selection")
    if op03_resolved and lane_ref not in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS:
        repair_blockers.append("selected_pnt_lane_ref_unknown_or_not_allowed_for_next_boundary_selection")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_REPAIR_REQUIRED_REF,
            ["next_boundary_selection_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NEXT_BOUNDARY_SELECTION_REF,
        )

    if lane_ref in P7_R54_AHR_POST_NCI_PNT_ALLOWED_STOP_LANE_REFS:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED_REF,
            ["post_nci_stop_selection_materialized_bodyfree_without_promotion"],
            [],
            P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_NEXT_BOUNDARY_MATERIALIZED_STOPPED_REF,
        ["post_nci_next_boundary_selection_materialized_bodyfree_without_execution"],
        [],
        P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF,
    )


def build_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization(
    pnt_op03_selected_handoff_or_stop_lane_consistency_resolver: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PNT-OP04 next boundary selection materialization.

    OP04 turns a resolved OP03 lane into stopped body-free selection material. It
    records a next design candidate, wait hold, or stop candidate, but it does
    not execute the selected handoff-or-stop or call downstream builders.
    """

    session_id = _safe_review_session_id(review_session_id)
    op03 = pnt_op03_selected_handoff_or_stop_lane_consistency_resolver
    op03_present = isinstance(op03, Mapping)
    op03_valid = _op03_contract_valid(op03)
    op03_status_ref = _clean_ref(op03.get("pnt_op03_status_ref") if isinstance(op03, Mapping) else None, default="missing", max_length=260)
    op03_resolved = bool(op03_valid and op03 and op03.get("selected_pnt_lane_resolved") is True)
    lane_ref = _clean_ref(op03.get("selected_pnt_lane_ref") if isinstance(op03, Mapping) else None, default="missing", max_length=260)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op03 or {}, path="pnt_op03")

    status_ref, reason_refs, blocker_refs, next_required_step = _op04_status_reason_blocker_next(
        op03_present=op03_present,
        op03_valid=op03_valid,
        op03_resolved=op03_resolved,
        lane_ref=lane_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    materialized = status_ref in (
        P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_NEXT_BOUNDARY_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED_REF,
    )
    if materialized:
        selected_pnt_status_ref = _clean_ref(op03.get("selected_pnt_status_ref"), default="missing", max_length=260)  # type: ignore[union-attr]
        selected_triage_kind_ref = _clean_ref(op03.get("selected_pnt_triage_kind_ref"), default="missing", max_length=320)  # type: ignore[union-attr]
        selected_outcome_group_ref = P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[lane_ref]
        selected_handoff_or_stop_ref = _clean_ref(op03.get("selected_handoff_or_stop_ref"), default="missing", max_length=360)  # type: ignore[union-attr]
        selected_handoff_or_stop_kind_ref = _clean_ref(op03.get("selected_handoff_or_stop_kind_ref"), default="missing", max_length=360)  # type: ignore[union-attr]
        selected_handoff_or_stop_not_executed = bool(op03.get("selected_handoff_or_stop_not_executed") is True)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_ref = _clean_ref(op03.get("selected_post_nci_next_boundary_candidate_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_kind_ref = _clean_ref(op03.get("selected_post_nci_next_boundary_candidate_kind_ref"), default="missing", max_length=420)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_not_executed = True
        next_design_document_candidate_ref = P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[lane_ref]
        next_design_document_allowed = P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[lane_ref]
        manual_wait_required = P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[lane_ref]
        manual_stop_required = P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[lane_ref]
        repair_design_candidate = P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[lane_ref]
    else:
        selected_pnt_status_ref = status_ref
        selected_triage_kind_ref = "missing"
        selected_outcome_group_ref = "missing"
        selected_handoff_or_stop_ref = "missing"
        selected_handoff_or_stop_kind_ref = "missing"
        selected_handoff_or_stop_not_executed = False
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP04_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op03_material_present": op03_present,
        "op03_contract_valid": op03_valid,
        "op03_schema_version": _clean_ref(op03.get("schema_version") if isinstance(op03, Mapping) else None, default="missing", max_length=260),
        "op03_material_ref": _clean_ref(op03.get("material_id") if isinstance(op03, Mapping) else None, default="missing", max_length=260),
        "op03_status_ref": op03_status_ref,
        "op03_next_required_step": _clean_ref(op03.get("next_required_step") if isinstance(op03, Mapping) else None, default="missing", max_length=360),
        "op03_lane_resolved": op03_resolved,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": lane_ref if materialized else "missing",
        "selected_pnt_triage_kind_ref": selected_triage_kind_ref,
        "selected_pnt_outcome_group_ref": selected_outcome_group_ref,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_handoff_or_stop_not_executed,
        "selected_post_nci_outcome_group_ref": selected_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_post_nci_next_boundary_execution_allowed_here": False,
        "selected_post_nci_next_boundary_materialized_here": materialized,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "allowed_pnt_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP04_ALLOWED_STATUS_REFS),
        "allowed_pnt_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP04_ALLOWED_STATUS_REFS),
        "allowed_pnt_lane_refs": list(P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS),
        "allowed_pnt_lane_ref_count": len(P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS),
        "allowed_pnt_outcome_group_refs": list(P7_R54_AHR_POST_NCI_PNT_ALLOWED_OUTCOME_GROUP_REFS),
        "allowed_pnt_outcome_group_ref_count": len(P7_R54_AHR_POST_NCI_PNT_ALLOWED_OUTCOME_GROUP_REFS),
        "pnt_op04_status_ref": status_ref,
        "bodyfree_next_boundary_selection_status_ref": status_ref,
        "pnt_op04_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP04_ALLOWED_STATUS_REFS),
        "pnt_op04_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP04_ALLOWED_STATUS_REFS),
        "pnt_op04_next_boundary_selection_materialized_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_NEXT_BOUNDARY_MATERIALIZED_STOPPED_REF,
        "pnt_op04_stop_selection_materialized_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED_REF,
        "pnt_op04_repair_required": status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_REPAIR_REQUIRED_REF,
        "pnt_op04_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF,
        "pnt_op04_reason_refs": reason_refs,
        "pnt_op04_reason_ref_count": len(reason_refs),
        "pnt_op04_blocker_refs": blocker_refs,
        "pnt_op04_blocker_ref_count": len(blocker_refs),
        "op04_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op04_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op04_input_body_like_value_path_refs": list(body_like_paths),
        "op04_input_body_like_value_path_count": len(body_like_paths),
        "op04_input_promotion_claim_refs": list(promotion_claims),
        "op04_input_promotion_claim_ref_count": len(promotion_claims),
        "op04_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op04_input_no_touch_mutation_path_count": len(no_touch_paths),
        "pnt_op04_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op04_does_not_call_dhr_op05": True,
        "pnt_op04_does_not_call_dhr_op06": True,
        "pnt_op04_does_not_execute_dmd_r52_or_release": True,
        "pnt_op04_does_not_start_actual_review": True,
        "pnt_op04_does_not_request_raw_evidence": True,
        "pnt_op04_does_not_execute_repair": True,
        "pnt_op04_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op04_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op04_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP04 next boundary selection materialization contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP04_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP04")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP04_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP04_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP04_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP04",
    )
    if data.get("bodyfree_next_boundary_selection_status_ref") != data.get("pnt_op04_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 status alias changed")
    if tuple(data.get("pnt_op04_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP04_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 allowed status refs changed")
    for key in (
        "pnt_op04_does_not_execute_selected_handoff_or_stop",
        "pnt_op04_does_not_call_dhr_op05",
        "pnt_op04_does_not_call_dhr_op06",
        "pnt_op04_does_not_execute_dmd_r52_or_release",
        "pnt_op04_does_not_start_actual_review",
        "pnt_op04_does_not_request_raw_evidence",
        "pnt_op04_does_not_execute_repair",
        "pnt_op04_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op04_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op04_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP04 required true boundary changed: {key}")
    for field, count_field in (
        ("allowed_pnt_status_refs", "allowed_pnt_status_ref_count"),
        ("allowed_pnt_lane_refs", "allowed_pnt_lane_ref_count"),
        ("allowed_pnt_outcome_group_refs", "allowed_pnt_outcome_group_ref_count"),
        ("pnt_op04_allowed_status_refs", "pnt_op04_allowed_status_ref_count"),
        ("pnt_op04_reason_refs", "pnt_op04_reason_ref_count"),
        ("pnt_op04_blocker_refs", "pnt_op04_blocker_ref_count"),
        ("op04_input_forbidden_payload_key_path_refs", "op04_input_forbidden_payload_key_path_count"),
        ("op04_input_body_like_value_path_refs", "op04_input_body_like_value_path_count"),
        ("op04_input_promotion_claim_refs", "op04_input_promotion_claim_ref_count"),
        ("op04_input_no_touch_mutation_path_refs", "op04_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP04 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP04_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP04_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 not-yet steps changed")
    if any(data.get(key) is not False for key in ("dhr_op05_call_allowed_here", "dhr_op05_builder_call_allowed_here", "actual_review_start_allowed_here", "raw_evidence_request_allowed_here", "repair_execution_allowed_here", "selected_post_nci_next_boundary_execution_allowed_here")):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 execution allowance changed")
    status_ref = data.get("pnt_op04_status_ref")
    flags = [
        data.get("pnt_op04_next_boundary_selection_materialized_stopped") is True,
        data.get("pnt_op04_stop_selection_materialized_stopped") is True,
        data.get("pnt_op04_repair_required") is True,
        data.get("pnt_op04_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP04_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 exactly one selection status branch must be selected")
    materialized = status_ref in (
        P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_NEXT_BOUNDARY_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED_REF,
    )
    if materialized:
        lane_ref = data.get("selected_pnt_lane_ref")
        if data.get("op03_contract_valid") is not True or data.get("op03_lane_resolved") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 materialized branch requires resolved valid OP03")
        if lane_ref not in P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 materialized lane is not allowed")
        if data.get("selected_post_nci_next_boundary_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_SELECTED_HANDOFF_OR_STOP_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 next boundary ref changed")
        if data.get("selected_post_nci_next_boundary_kind_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_OR_STOP_KIND_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 next boundary kind changed")
        if data.get("selected_post_nci_outcome_group_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_OUTCOME_GROUP_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 outcome group changed")
        if data.get("next_design_document_candidate_ref") != P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_CANDIDATE_REF_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 next design document ref changed")
        if data.get("next_design_document_allowed") is not P7_R54_AHR_POST_NCI_PNT_LANE_TO_NEXT_DESIGN_DOCUMENT_ALLOWED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 next design document allowance changed")
        if data.get("manual_wait_required") is not P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_WAIT_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 manual wait flag changed")
        if data.get("manual_stop_required") is not P7_R54_AHR_POST_NCI_PNT_LANE_TO_MANUAL_STOP_REQUIRED_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 manual stop flag changed")
        if data.get("repair_design_candidate") is not P7_R54_AHR_POST_NCI_PNT_LANE_TO_REPAIR_DESIGN_CANDIDATE_MAP[lane_ref]:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 repair design candidate flag changed")
        if data.get("selected_handoff_or_stop_not_executed") is not True or data.get("selected_post_nci_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 materialized selection must stay non-executed")
        if data.get("selected_post_nci_next_boundary_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 materialized branch must materialize selection")
        if data.get("pnt_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 materialized branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 materialized next step changed")
    else:
        if not data.get("pnt_op04_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 non-materialized branch must carry blockers")
        if data.get("selected_post_nci_next_boundary_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 non-materialized branch cannot materialize selection")
        if status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_REPAIR_REQUIRED_REF and data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_NEXT_BOUNDARY_SELECTION_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 repair next step changed")
        if status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF and data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_NEXT_BOUNDARY_SELECTION_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF:
        for field in (
            "op04_input_forbidden_payload_key_path_refs",
            "op04_input_body_like_value_path_refs",
            "op04_input_promotion_claim_refs",
            "op04_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP04 non-blocked branch cannot carry scan blockers")
    return True


def _op05_status_reason_blocker_next(
    *,
    op04_present: bool,
    op04_valid: bool,
    op04_status_ref: str,
    op04_selection_materialized_or_stopped: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op05_guard_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op05_guard_body_like_value_detected")
    if promotion_claims:
        blockers.append("op05_guard_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op05_guard_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op04_status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_BLOCKED_PROMOTION_AUTORUN_REF:
        blockers.append("pnt_op04_boundary_selection_blocked_before_guard")
    if blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF,
            ["bodyfree_no_touch_no_promotion_guard_blocked_without_downstream_promotion"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP05_GUARD_REF,
        )

    repair_blockers: list[str] = []
    if not op04_present:
        repair_blockers.append("pnt_op04_next_boundary_selection_material_missing")
    if op04_present and not op04_valid:
        repair_blockers.append("pnt_op04_next_boundary_selection_contract_invalid")
    if op04_valid and not op04_selection_materialized_or_stopped:
        repair_blockers.append("pnt_op04_selection_not_materialized_or_stopped_for_guard")
    if op04_status_ref == P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_REPAIR_REQUIRED_REF:
        repair_blockers.append("pnt_op04_boundary_selection_repair_required_before_guard")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_REPAIR_REQUIRED_REF,
            ["bodyfree_no_touch_no_promotion_guard_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP05_GUARD_INPUTS_REF,
        )
    return (
        P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_GUARD_PASSED_REF,
        ["bodyfree_no_touch_no_promotion_no_auto_execution_guard_passed_without_downstream_execution"],
        [],
        P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF,
    )


def build_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard(
    pnt_op04_next_boundary_selection_materialization: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PNT-OP05 body-free/no-touch/no-promotion/no-auto-execution guard."""

    session_id = _safe_review_session_id(review_session_id)
    op04 = pnt_op04_next_boundary_selection_materialization
    op04_present = isinstance(op04, Mapping)
    op04_valid = _op04_contract_valid(op04)
    op04_status_ref = _clean_ref(op04.get("pnt_op04_status_ref") if isinstance(op04, Mapping) else None, default="missing", max_length=260)
    op04_selection_materialized_or_stopped = bool(
        op04_valid
        and op04_status_ref in (
            P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_NEXT_BOUNDARY_MATERIALIZED_STOPPED_REF,
            P7_R54_AHR_POST_NCI_PNT_OP04_STATUS_STOP_SELECTION_MATERIALIZED_STOPPED_REF,
        )
        and op04
        and op04.get("selected_post_nci_next_boundary_materialized_here") is True
    )
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op04 or {}, path="pnt_op04")
    status_ref, reason_refs, blocker_refs, next_required_step = _op05_status_reason_blocker_next(
        op04_present=op04_present,
        op04_valid=op04_valid,
        op04_status_ref=op04_status_ref,
        op04_selection_materialized_or_stopped=op04_selection_materialized_or_stopped,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    guard_passed = status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_GUARD_PASSED_REF

    def _copy_ref(key: str, default: str = "missing", max_length: int = 420) -> str:
        return _clean_ref(op04.get(key) if isinstance(op04, Mapping) else None, default=default, max_length=max_length)

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP05_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op04_material_present": op04_present,
        "op04_contract_valid": op04_valid,
        "op04_schema_version": _copy_ref("schema_version", max_length=260),
        "op04_material_ref": _copy_ref("material_id", max_length=260),
        "op04_status_ref": op04_status_ref,
        "op04_next_required_step": _copy_ref("next_required_step", max_length=360),
        "op04_selection_materialized_or_stopped": op04_selection_materialized_or_stopped,
        "selected_pnt_status_ref": _copy_ref("selected_pnt_status_ref", max_length=260),
        "selected_pnt_lane_ref": _copy_ref("selected_pnt_lane_ref", max_length=260),
        "selected_post_nci_outcome_group_ref": _copy_ref("selected_post_nci_outcome_group_ref", max_length=260),
        "selected_post_nci_next_boundary_ref": _copy_ref("selected_post_nci_next_boundary_ref"),
        "selected_post_nci_next_boundary_kind_ref": _copy_ref("selected_post_nci_next_boundary_kind_ref"),
        "selected_post_nci_next_boundary_not_executed": bool(op04_valid and op04 and op04.get("selected_post_nci_next_boundary_not_executed") is True),
        "selected_post_nci_next_boundary_execution_allowed_here": False,
        "selected_post_nci_next_boundary_materialized_here": bool(op04_valid and op04 and op04.get("selected_post_nci_next_boundary_materialized_here") is True),
        "next_design_document_candidate_ref": _copy_ref("next_design_document_candidate_ref"),
        "next_design_document_allowed": bool(op04_valid and op04 and op04.get("next_design_document_allowed") is True),
        "manual_wait_required": bool(op04_valid and op04 and op04.get("manual_wait_required") is True),
        "manual_stop_required": bool(op04_valid and op04 and op04.get("manual_stop_required") is True),
        "repair_design_candidate": bool(op04_valid and op04 and op04.get("repair_design_candidate") is True),
        "guard_subject_step_refs": list(P7_R54_AHR_POST_NCI_PNT_OP05_GUARD_SUBJECT_STEP_REFS),
        "guard_subject_step_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP05_GUARD_SUBJECT_STEP_REFS),
        "guard_scope_ref": "pnt_op00_to_op04_and_explicit_nci_op08_material_bodyfree_no_touch_no_promotion_guard",
        "pnt_op05_status_ref": status_ref,
        "bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref": status_ref,
        "pnt_op05_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP05_ALLOWED_STATUS_REFS),
        "pnt_op05_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP05_ALLOWED_STATUS_REFS),
        "pnt_op05_guard_passed": guard_passed,
        "pnt_op05_repair_required": status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_REPAIR_REQUIRED_REF,
        "pnt_op05_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF,
        "pnt_op05_reason_refs": reason_refs,
        "pnt_op05_reason_ref_count": len(reason_refs),
        "pnt_op05_blocker_refs": blocker_refs,
        "pnt_op05_blocker_ref_count": len(blocker_refs),
        "guard_forbidden_payload_key_path_refs": list(forbidden_paths),
        "guard_forbidden_payload_key_path_count": len(forbidden_paths),
        "guard_body_like_value_path_refs": list(body_like_paths),
        "guard_body_like_value_path_count": len(body_like_paths),
        "guard_promotion_claim_refs": list(promotion_claims),
        "guard_promotion_claim_ref_count": len(promotion_claims),
        "guard_no_touch_mutation_path_refs": list(no_touch_paths),
        "guard_no_touch_mutation_path_count": len(no_touch_paths),
        "selected_handoff_or_stop_execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "pnt_op05_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op05_does_not_call_dhr_op05": True,
        "pnt_op05_does_not_call_dhr_op06": True,
        "pnt_op05_does_not_execute_dmd_r52_or_release": True,
        "pnt_op05_does_not_start_actual_review": True,
        "pnt_op05_does_not_request_raw_evidence": True,
        "pnt_op05_does_not_execute_repair": True,
        "pnt_op05_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op05_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op05_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP05_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP05 body-free/no-touch/no-promotion/no-auto-execution guard contract."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP05_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP05")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP05_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP05_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP05_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP05",
    )
    if data.get("bodyfree_no_touch_no_promotion_no_auto_execution_guard_status_ref") != data.get("pnt_op05_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 status alias changed")
    if tuple(data.get("pnt_op05_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP05_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 allowed status refs changed")
    if tuple(data.get("guard_subject_step_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP05_GUARD_SUBJECT_STEP_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 guard subject refs changed")
    for key in (
        "selected_handoff_or_stop_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP05 execution allowance changed: {key}")
    for key in (
        "pnt_op05_does_not_execute_selected_handoff_or_stop",
        "pnt_op05_does_not_call_dhr_op05",
        "pnt_op05_does_not_call_dhr_op06",
        "pnt_op05_does_not_execute_dmd_r52_or_release",
        "pnt_op05_does_not_start_actual_review",
        "pnt_op05_does_not_request_raw_evidence",
        "pnt_op05_does_not_execute_repair",
        "pnt_op05_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op05_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op05_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP05 required true boundary changed: {key}")
    for field, count_field in (
        ("guard_subject_step_refs", "guard_subject_step_ref_count"),
        ("pnt_op05_allowed_status_refs", "pnt_op05_allowed_status_ref_count"),
        ("pnt_op05_reason_refs", "pnt_op05_reason_ref_count"),
        ("pnt_op05_blocker_refs", "pnt_op05_blocker_ref_count"),
        ("guard_forbidden_payload_key_path_refs", "guard_forbidden_payload_key_path_count"),
        ("guard_body_like_value_path_refs", "guard_body_like_value_path_count"),
        ("guard_promotion_claim_refs", "guard_promotion_claim_ref_count"),
        ("guard_no_touch_mutation_path_refs", "guard_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP05 {count_field} changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP05_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP05_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 not-yet steps changed")
    status_ref = data.get("pnt_op05_status_ref")
    flags = [
        data.get("pnt_op05_guard_passed") is True,
        data.get("pnt_op05_repair_required") is True,
        data.get("pnt_op05_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP05_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 exactly one guard status branch must be selected")
    if status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_GUARD_PASSED_REF:
        if data.get("op04_contract_valid") is not True or data.get("op04_selection_materialized_or_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 passed branch requires valid OP04 materialization")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 passed branch requires non-executed next boundary")
        if data.get("selected_post_nci_next_boundary_execution_allowed_here") is not False:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 passed branch cannot allow execution")
        if data.get("pnt_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 passed branch cannot carry blockers")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 passed next step changed")
    else:
        if not data.get("pnt_op05_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 non-passed branch must carry blockers")
        if status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_REPAIR_REQUIRED_REF and data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP05_GUARD_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 repair next step changed")
        if status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF and data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP05_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF:
        for field in (
            "guard_forbidden_payload_key_path_refs",
            "guard_body_like_value_path_refs",
            "guard_promotion_claim_refs",
            "guard_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP05 non-blocked branch cannot carry scan blockers")
    return True


def _op05_contract_valid(op05: Mapping[str, Any] | None) -> bool:
    if not isinstance(op05, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract(op05) is True
    except ValueError:
        return False


def _op06_status_reason_blocker_next(
    *,
    op05_present: bool,
    op05_valid: bool,
    op05_status_ref: str,
    op05_guard_passed: bool,
    forbidden_paths: Sequence[str],
    body_like_paths: Sequence[str],
    promotion_claims: Sequence[str],
    no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if forbidden_paths:
        blockers.append("op06_validation_plan_forbidden_payload_key_detected")
    if body_like_paths:
        blockers.append("op06_validation_plan_body_like_value_detected")
    if promotion_claims:
        blockers.append("op06_validation_plan_promotion_or_autorun_claim_detected")
    if no_touch_paths:
        blockers.append("op06_validation_plan_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op05_status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_BLOCKED_REF:
        blockers.append("pnt_op05_guard_blocked_before_validation_plan")
    if blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF,
            ["validation_plan_blocked_without_running_commands_or_downstream_promotion"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF,
        )

    repair_blockers: list[str] = []
    if op05_present and not op05_valid:
        repair_blockers.append("pnt_op05_guard_contract_invalid")
    if op05_status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_REPAIR_REQUIRED_REF:
        repair_blockers.append("pnt_op05_guard_repair_required_before_validation_plan")
    if op05_valid and not op05_guard_passed:
        repair_blockers.append("pnt_op05_guard_not_passed_for_validation_plan")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_REPAIR_REQUIRED_REF,
            ["validation_plan_repair_required_without_running_commands_or_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_INPUTS_REF,
        )

    if not op05_present:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF,
            ["waiting_for_pnt_op05_guard_before_validation_plan_refs"],
            ["pnt_op05_guard_material_missing"],
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF,
        )

    return (
        P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF,
        ["selected_regression_compileall_validation_plan_refs_recorded_without_execution"],
        [],
        P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF,
    )


def build_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan(
    pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PNT-OP06 validation plan refs without executing validation commands."""

    session_id = _safe_review_session_id(review_session_id)
    op05 = pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard
    op05_present = isinstance(op05, Mapping)
    op05_valid = _op05_contract_valid(op05)
    op05_status_ref = _clean_ref(op05.get("pnt_op05_status_ref") if isinstance(op05, Mapping) else None, default="missing", max_length=260)
    op05_guard_passed = bool(
        op05_valid
        and op05_status_ref == P7_R54_AHR_POST_NCI_PNT_OP05_STATUS_GUARD_PASSED_REF
        and op05
        and op05.get("pnt_op05_guard_passed") is True
    )
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op05 or {}, path="pnt_op05")
    status_ref, reason_refs, blocker_refs, next_required_step = _op06_status_reason_blocker_next(
        op05_present=op05_present,
        op05_valid=op05_valid,
        op05_status_ref=op05_status_ref,
        op05_guard_passed=op05_guard_passed,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    validation_plan_recorded = status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF

    def _copy_ref(key: str, default: str = "missing", max_length: int = 420) -> str:
        return _clean_ref(op05.get(key) if isinstance(op05, Mapping) else None, default=default, max_length=max_length)

    if validation_plan_recorded:
        selected_pnt_status_ref = _copy_ref("selected_pnt_status_ref", max_length=260)
        selected_pnt_lane_ref = _copy_ref("selected_pnt_lane_ref", max_length=260)
        selected_post_nci_outcome_group_ref = _copy_ref("selected_post_nci_outcome_group_ref", max_length=260)
        selected_post_nci_next_boundary_ref = _copy_ref("selected_post_nci_next_boundary_ref", max_length=420)
        selected_post_nci_next_boundary_kind_ref = _copy_ref("selected_post_nci_next_boundary_kind_ref", max_length=420)
        selected_post_nci_next_boundary_not_executed = bool(op05.get("selected_post_nci_next_boundary_not_executed") is True)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_execution_allowed_here = False
        selected_post_nci_next_boundary_materialized_here = bool(op05.get("selected_post_nci_next_boundary_materialized_here") is True)  # type: ignore[union-attr]
        next_design_document_candidate_ref = _copy_ref("next_design_document_candidate_ref", max_length=420)
        next_design_document_allowed = bool(op05.get("next_design_document_allowed") is True)  # type: ignore[union-attr]
        manual_wait_required = bool(op05.get("manual_wait_required") is True)  # type: ignore[union-attr]
        manual_stop_required = bool(op05.get("manual_stop_required") is True)  # type: ignore[union-attr]
        repair_design_candidate = bool(op05.get("repair_design_candidate") is True)  # type: ignore[union-attr]
    else:
        selected_pnt_status_ref = status_ref
        selected_pnt_lane_ref = "missing"
        selected_post_nci_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_post_nci_next_boundary_execution_allowed_here = False
        selected_post_nci_next_boundary_materialized_here = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP06_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op05_material_present": op05_present,
        "op05_contract_valid": op05_valid,
        "op05_schema_version": _copy_ref("schema_version", max_length=260),
        "op05_material_ref": _copy_ref("material_id", max_length=260),
        "op05_status_ref": op05_status_ref,
        "op05_next_required_step": _copy_ref("next_required_step", max_length=360),
        "op05_guard_passed": op05_guard_passed,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": selected_pnt_lane_ref,
        "selected_post_nci_outcome_group_ref": selected_post_nci_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_post_nci_next_boundary_execution_allowed_here": selected_post_nci_next_boundary_execution_allowed_here,
        "selected_post_nci_next_boundary_materialized_here": selected_post_nci_next_boundary_materialized_here,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "validation_plan_ref": "pnt_op06_selected_regression_compileall_validation_plan_refs_without_execution",
        "validation_plan_recorded": validation_plan_recorded,
        "validation_plan_bodyfree": True,
        "validation_plan_execution_allowed_here": False,
        "validation_commands_executed_here": False,
        "pytest_executed_here": False,
        "pnt_target_tests_executed_here": False,
        "selected_regression_executed_here": False,
        "compileall_executed_here": False,
        "target_test_ref_refs": list(P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS),
        "target_test_ref_count": len(P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS),
        "selected_regression_test_ref_refs": list(P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_count": len(P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS),
        "compileall_target_ref_refs": list(P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_count": len(P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS),
        "validation_command_summary_refs": list(P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS),
        "target_test_result_status_ref": "pnt_op06_target_test_plan_recorded_not_executed_here",
        "selected_regression_result_status_ref": "pnt_op06_selected_regression_plan_recorded_not_executed_here",
        "compileall_result_status_ref": "pnt_op06_compileall_plan_recorded_not_executed_here",
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "pnt_op06_status_ref": status_ref,
        "bodyfree_selected_regression_compileall_validation_plan_status_ref": status_ref,
        "pnt_op06_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP06_ALLOWED_STATUS_REFS),
        "pnt_op06_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP06_ALLOWED_STATUS_REFS),
        "pnt_op06_validation_plan_recorded": status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF,
        "pnt_op06_waiting_for_op05_guard": status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF,
        "pnt_op06_repair_required": status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_REPAIR_REQUIRED_REF,
        "pnt_op06_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF,
        "pnt_op06_reason_refs": reason_refs,
        "pnt_op06_reason_ref_count": len(reason_refs),
        "pnt_op06_blocker_refs": blocker_refs,
        "pnt_op06_blocker_ref_count": len(blocker_refs),
        "op06_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op06_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op06_input_body_like_value_path_refs": list(body_like_paths),
        "op06_input_body_like_value_path_count": len(body_like_paths),
        "op06_input_promotion_claim_refs": list(promotion_claims),
        "op06_input_promotion_claim_ref_count": len(promotion_claims),
        "op06_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op06_input_no_touch_mutation_path_count": len(no_touch_paths),
        "selected_handoff_or_stop_execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "pnt_op06_does_not_execute_validation_commands": True,
        "pnt_op06_does_not_claim_full_backend_rn_or_real_device_green": True,
        "pnt_op06_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op06_does_not_call_dhr_op05": True,
        "pnt_op06_does_not_call_dhr_op06": True,
        "pnt_op06_does_not_execute_dmd_r52_or_release": True,
        "pnt_op06_does_not_start_actual_review": True,
        "pnt_op06_does_not_request_raw_evidence": True,
        "pnt_op06_does_not_execute_repair": True,
        "pnt_op06_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op06_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op06_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP06_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP06 validation plan refs contract without command execution."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP06_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP06")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP06_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP06_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP06_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP06",
    )
    if data.get("bodyfree_selected_regression_compileall_validation_plan_status_ref") != data.get("pnt_op06_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 status alias changed")
    if tuple(data.get("pnt_op06_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP06_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 allowed status refs changed")
    for key in (
        "validation_plan_execution_allowed_here",
        "validation_commands_executed_here",
        "pytest_executed_here",
        "pnt_target_tests_executed_here",
        "selected_regression_executed_here",
        "compileall_executed_here",
        "selected_handoff_or_stop_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP06 forbidden execution/claim changed: {key}")
    for key in (
        "pnt_op06_does_not_execute_validation_commands",
        "pnt_op06_does_not_claim_full_backend_rn_or_real_device_green",
        "pnt_op06_does_not_execute_selected_handoff_or_stop",
        "pnt_op06_does_not_call_dhr_op05",
        "pnt_op06_does_not_call_dhr_op06",
        "pnt_op06_does_not_execute_dmd_r52_or_release",
        "pnt_op06_does_not_start_actual_review",
        "pnt_op06_does_not_request_raw_evidence",
        "pnt_op06_does_not_execute_repair",
        "pnt_op06_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op06_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op06_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP06 required true boundary changed: {key}")
    for field, count_field in (
        ("target_test_ref_refs", "target_test_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_count"),
        ("compileall_target_ref_refs", "compileall_target_ref_count"),
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("pnt_op06_allowed_status_refs", "pnt_op06_allowed_status_ref_count"),
        ("pnt_op06_reason_refs", "pnt_op06_reason_ref_count"),
        ("pnt_op06_blocker_refs", "pnt_op06_blocker_ref_count"),
        ("op06_input_forbidden_payload_key_path_refs", "op06_input_forbidden_payload_key_path_count"),
        ("op06_input_body_like_value_path_refs", "op06_input_body_like_value_path_count"),
        ("op06_input_promotion_claim_refs", "op06_input_promotion_claim_ref_count"),
        ("op06_input_no_touch_mutation_path_refs", "op06_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP06 {count_field} changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 target refs changed")
    if tuple(data.get("selected_regression_test_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 selected regression refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 compileall refs changed")
    if tuple(data.get("validation_command_summary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 validation command summary refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP06_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP06_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 not-yet steps changed")
    status_ref = data.get("pnt_op06_status_ref")
    flags = [
        data.get("pnt_op06_validation_plan_recorded") is True,
        data.get("pnt_op06_waiting_for_op05_guard") is True,
        data.get("pnt_op06_repair_required") is True,
        data.get("pnt_op06_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP06_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 exactly one status branch must be selected")
    if status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF:
        if data.get("op05_contract_valid") is not True or data.get("op05_guard_passed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 recorded branch requires OP05 guard pass")
        if data.get("validation_plan_recorded") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 recorded branch must record validation plan")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 recorded branch requires non-executed boundary")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 recorded next step changed")
        if data.get("pnt_op06_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 recorded branch cannot carry blockers")
    elif status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP05_GUARD_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 waiting next step changed")
    elif status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_REPAIR_REQUIRED_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP06_VALIDATION_PLAN_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP06_VALIDATION_PLAN_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF:
        for field in (
            "op06_input_forbidden_payload_key_path_refs",
            "op06_input_body_like_value_path_refs",
            "op06_input_promotion_claim_refs",
            "op06_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP06 non-blocked branch cannot carry scan blockers")
    return True


def _op06_contract_valid(op06: Mapping[str, Any] | None) -> bool:
    if not isinstance(op06, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan_contract(op06) is True
    except ValueError:
        return False


def _op07_status_reason_blocker_next(
    *,
    op06_present: bool,
    op06_valid: bool,
    op06_status_ref: str,
    op06_validation_plan_recorded: bool,
    selected_post_nci_outcome_group_ref: str,
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
    if op06_status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_BLOCKED_REF:
        blockers.append("pnt_op06_validation_plan_blocked_before_result_memo_draft")
    if blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF,
            ["post_nci_triage_result_memo_draft_blocked_without_op08_closure_or_downstream_promotion"],
            _dedupe_clean_refs(blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP07_RESULT_MEMO_DRAFT_REF,
        )

    repair_blockers: list[str] = []
    if not op06_present:
        repair_blockers.append("pnt_op06_validation_plan_material_missing")
    if op06_present and not op06_valid:
        repair_blockers.append("pnt_op06_validation_plan_contract_invalid")
    if op06_status_ref in (
        P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_WAITING_FOR_OP05_GUARD_REF,
        P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_REPAIR_REQUIRED_REF,
    ):
        repair_blockers.append("pnt_op06_validation_plan_not_ready_for_result_memo_draft")
    if op06_valid and not op06_validation_plan_recorded:
        repair_blockers.append("pnt_op06_validation_plan_not_recorded_for_result_memo_draft")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_REPAIR_REQUIRED_REF,
            ["post_nci_triage_result_memo_draft_repair_required_without_op08_closure_or_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=320),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP07_RESULT_MEMO_DRAFT_INPUTS_REF,
        )

    if selected_post_nci_outcome_group_ref == P7_R54_AHR_POST_NCI_PNT_OUTCOME_GROUP_STOP_REF:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
            ["post_nci_triage_stop_result_memo_draft_materialized_bodyfree_without_op08_closure"],
            [],
            P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        )
    return (
        P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        ["post_nci_triage_result_memo_draft_materialized_bodyfree_without_op08_closure"],
        [],
        P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
    )


def build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material(
    pnt_op06_selected_regression_compileall_validation_plan: Mapping[str, Any] | None = None,
    *,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build PNT-OP07 body-free result memo draft material without OP08 closure."""

    session_id = _safe_review_session_id(review_session_id)
    op06 = pnt_op06_selected_regression_compileall_validation_plan
    op06_present = isinstance(op06, Mapping)
    op06_valid = _op06_contract_valid(op06)
    op06_status_ref = _clean_ref(op06.get("pnt_op06_status_ref") if isinstance(op06, Mapping) else None, default="missing", max_length=260)
    op06_validation_plan_recorded = bool(
        op06_valid
        and op06_status_ref == P7_R54_AHR_POST_NCI_PNT_OP06_STATUS_VALIDATION_PLAN_RECORDED_REF
        and op06
        and op06.get("validation_plan_recorded") is True
        and op06.get("pnt_op06_validation_plan_recorded") is True
    )
    selected_post_nci_outcome_group_ref = _clean_ref(op06.get("selected_post_nci_outcome_group_ref") if isinstance(op06, Mapping) else None, default="missing", max_length=260)
    forbidden_paths, body_like_paths, promotion_claims, no_touch_paths = _bodyfree_no_touch_scan_quads(op06 or {}, path="pnt_op06")
    status_ref, reason_refs, blocker_refs, next_required_step = _op07_status_reason_blocker_next(
        op06_present=op06_present,
        op06_valid=op06_valid,
        op06_status_ref=op06_status_ref,
        op06_validation_plan_recorded=op06_validation_plan_recorded,
        selected_post_nci_outcome_group_ref=selected_post_nci_outcome_group_ref,
        forbidden_paths=forbidden_paths,
        body_like_paths=body_like_paths,
        promotion_claims=promotion_claims,
        no_touch_paths=no_touch_paths,
    )
    draft_materialized = status_ref in (
        P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    )

    def _copy_ref(key: str, default: str = "missing", max_length: int = 420) -> str:
        return _clean_ref(op06.get(key) if isinstance(op06, Mapping) else None, default=default, max_length=max_length)

    if draft_materialized:
        selected_pnt_status_ref = _copy_ref("selected_pnt_status_ref", max_length=260)
        selected_pnt_lane_ref = _copy_ref("selected_pnt_lane_ref", max_length=260)
        selected_post_nci_next_boundary_ref = _copy_ref("selected_post_nci_next_boundary_ref", max_length=420)
        selected_post_nci_next_boundary_kind_ref = _copy_ref("selected_post_nci_next_boundary_kind_ref", max_length=420)
        selected_post_nci_next_boundary_not_executed = bool(op06.get("selected_post_nci_next_boundary_not_executed") is True)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_execution_allowed_here = False
        selected_post_nci_next_boundary_materialized_here = bool(op06.get("selected_post_nci_next_boundary_materialized_here") is True)  # type: ignore[union-attr]
        next_design_document_candidate_ref = _copy_ref("next_design_document_candidate_ref", max_length=420)
        next_design_document_allowed = bool(op06.get("next_design_document_allowed") is True)  # type: ignore[union-attr]
        manual_wait_required = bool(op06.get("manual_wait_required") is True)  # type: ignore[union-attr]
        manual_stop_required = bool(op06.get("manual_stop_required") is True)  # type: ignore[union-attr]
        repair_design_candidate = bool(op06.get("repair_design_candidate") is True)  # type: ignore[union-attr]
        validation_plan_recorded = True
        draft_ref = _clean_ref(
            "pnt_op07_post_nci_triage_result_memo_draft_for_" + selected_post_nci_next_boundary_ref,
            default="pnt_op07_post_nci_triage_result_memo_draft",
            max_length=420,
        )
    else:
        selected_pnt_status_ref = status_ref
        selected_pnt_lane_ref = "missing"
        selected_post_nci_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_post_nci_next_boundary_execution_allowed_here = False
        selected_post_nci_next_boundary_materialized_here = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False
        validation_plan_recorded = False
        draft_ref = "missing"

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP07_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op06_material_present": op06_present,
        "op06_contract_valid": op06_valid,
        "op06_schema_version": _copy_ref("schema_version", max_length=260),
        "op06_material_ref": _copy_ref("material_id", max_length=260),
        "op06_status_ref": op06_status_ref,
        "op06_next_required_step": _copy_ref("next_required_step", max_length=360),
        "op06_validation_plan_recorded": op06_validation_plan_recorded,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": selected_pnt_lane_ref,
        "selected_post_nci_outcome_group_ref": selected_post_nci_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_post_nci_next_boundary_execution_allowed_here": selected_post_nci_next_boundary_execution_allowed_here,
        "selected_post_nci_next_boundary_materialized_here": selected_post_nci_next_boundary_materialized_here,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "validation_plan_ref": _copy_ref("validation_plan_ref", max_length=320),
        "validation_plan_recorded": validation_plan_recorded,
        "validation_command_summary_refs": list(op06.get("validation_command_summary_refs") if isinstance(op06, Mapping) and isinstance(op06.get("validation_command_summary_refs"), Sequence) and not isinstance(op06.get("validation_command_summary_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS),
        "validation_command_summary_ref_count": len(list(op06.get("validation_command_summary_refs") if isinstance(op06, Mapping) and isinstance(op06.get("validation_command_summary_refs"), Sequence) and not isinstance(op06.get("validation_command_summary_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS)),
        "target_test_ref_refs": list(op06.get("target_test_ref_refs") if isinstance(op06, Mapping) and isinstance(op06.get("target_test_ref_refs"), Sequence) and not isinstance(op06.get("target_test_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS),
        "target_test_ref_count": len(list(op06.get("target_test_ref_refs") if isinstance(op06, Mapping) and isinstance(op06.get("target_test_ref_refs"), Sequence) and not isinstance(op06.get("target_test_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS)),
        "selected_regression_test_ref_refs": list(op06.get("selected_regression_test_ref_refs") if isinstance(op06, Mapping) and isinstance(op06.get("selected_regression_test_ref_refs"), Sequence) and not isinstance(op06.get("selected_regression_test_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS),
        "selected_regression_test_ref_count": len(list(op06.get("selected_regression_test_ref_refs") if isinstance(op06, Mapping) and isinstance(op06.get("selected_regression_test_ref_refs"), Sequence) and not isinstance(op06.get("selected_regression_test_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS)),
        "compileall_target_ref_refs": list(op06.get("compileall_target_ref_refs") if isinstance(op06, Mapping) and isinstance(op06.get("compileall_target_ref_refs"), Sequence) and not isinstance(op06.get("compileall_target_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS),
        "compileall_target_ref_count": len(list(op06.get("compileall_target_ref_refs") if isinstance(op06, Mapping) and isinstance(op06.get("compileall_target_ref_refs"), Sequence) and not isinstance(op06.get("compileall_target_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS)),
        "target_test_result_status_ref": _copy_ref("target_test_result_status_ref", max_length=260),
        "selected_regression_result_status_ref": _copy_ref("selected_regression_result_status_ref", max_length=260),
        "compileall_result_status_ref": _copy_ref("compileall_result_status_ref", max_length=260),
        "post_nci_triage_result_memo_draft_ref": draft_ref,
        "post_nci_triage_result_memo_draft_bodyfree": draft_materialized,
        "post_nci_triage_result_memo_draft_materialized_here": draft_materialized,
        "post_nci_triage_result_memo_draft_execution_allowed_here": False,
        "pnt_op07_ready_for_op08": draft_materialized,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "pnt_op07_status_ref": status_ref,
        "bodyfree_post_nci_triage_result_memo_draft_status_ref": status_ref,
        "pnt_op07_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP07_ALLOWED_STATUS_REFS),
        "pnt_op07_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP07_ALLOWED_STATUS_REFS),
        "pnt_op07_result_memo_draft_materialized_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        "pnt_op07_stop_result_memo_draft_materialized_stopped": status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        "pnt_op07_repair_required": status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_REPAIR_REQUIRED_REF,
        "pnt_op07_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF,
        "pnt_op07_reason_refs": reason_refs,
        "pnt_op07_reason_ref_count": len(reason_refs),
        "pnt_op07_blocker_refs": blocker_refs,
        "pnt_op07_blocker_ref_count": len(blocker_refs),
        "op07_input_forbidden_payload_key_path_refs": list(forbidden_paths),
        "op07_input_forbidden_payload_key_path_count": len(forbidden_paths),
        "op07_input_body_like_value_path_refs": list(body_like_paths),
        "op07_input_body_like_value_path_count": len(body_like_paths),
        "op07_input_promotion_claim_refs": list(promotion_claims),
        "op07_input_promotion_claim_ref_count": len(promotion_claims),
        "op07_input_no_touch_mutation_path_refs": list(no_touch_paths),
        "op07_input_no_touch_mutation_path_count": len(no_touch_paths),
        "selected_handoff_or_stop_execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "pnt_op07_does_not_close_result_memo_as_op08": True,
        "pnt_op07_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op07_does_not_call_dhr_op05": True,
        "pnt_op07_does_not_call_dhr_op06": True,
        "pnt_op07_does_not_execute_dmd_r52_or_release": True,
        "pnt_op07_does_not_start_actual_review": True,
        "pnt_op07_does_not_request_raw_evidence": True,
        "pnt_op07_does_not_execute_repair": True,
        "pnt_op07_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op07_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op07_does_not_materialize_p8_question_spec": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP07_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP07 result memo draft material contract without OP08 closure."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP07_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP07")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP07_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP07_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP07_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP07",
    )
    if data.get("bodyfree_post_nci_triage_result_memo_draft_status_ref") != data.get("pnt_op07_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 status alias changed")
    if tuple(data.get("pnt_op07_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP07_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 allowed status refs changed")
    for key in (
        "post_nci_triage_result_memo_draft_execution_allowed_here",
        "selected_handoff_or_stop_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP07 forbidden execution/claim changed: {key}")
    for key in (
        "pnt_op07_does_not_close_result_memo_as_op08",
        "pnt_op07_does_not_execute_selected_handoff_or_stop",
        "pnt_op07_does_not_call_dhr_op05",
        "pnt_op07_does_not_call_dhr_op06",
        "pnt_op07_does_not_execute_dmd_r52_or_release",
        "pnt_op07_does_not_start_actual_review",
        "pnt_op07_does_not_request_raw_evidence",
        "pnt_op07_does_not_execute_repair",
        "pnt_op07_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op07_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op07_does_not_materialize_p8_question_spec",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP07 required true boundary changed: {key}")
    for field, count_field in (
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("target_test_ref_refs", "target_test_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_count"),
        ("compileall_target_ref_refs", "compileall_target_ref_count"),
        ("pnt_op07_allowed_status_refs", "pnt_op07_allowed_status_ref_count"),
        ("pnt_op07_reason_refs", "pnt_op07_reason_ref_count"),
        ("pnt_op07_blocker_refs", "pnt_op07_blocker_ref_count"),
        ("op07_input_forbidden_payload_key_path_refs", "op07_input_forbidden_payload_key_path_count"),
        ("op07_input_body_like_value_path_refs", "op07_input_body_like_value_path_count"),
        ("op07_input_promotion_claim_refs", "op07_input_promotion_claim_ref_count"),
        ("op07_input_no_touch_mutation_path_refs", "op07_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP07 {count_field} changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 target refs changed")
    if tuple(data.get("selected_regression_test_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 selected regression refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 compileall refs changed")
    if tuple(data.get("validation_command_summary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 validation command summary refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP07_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP07_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 not-yet steps changed")
    status_ref = data.get("pnt_op07_status_ref")
    flags = [
        data.get("pnt_op07_result_memo_draft_materialized_stopped") is True,
        data.get("pnt_op07_stop_result_memo_draft_materialized_stopped") is True,
        data.get("pnt_op07_repair_required") is True,
        data.get("pnt_op07_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP07_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 exactly one status branch must be selected")
    if status_ref in (
        P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
        P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_STOP_RESULT_MEMO_DRAFT_MATERIALIZED_STOPPED_REF,
    ):
        if data.get("op06_contract_valid") is not True or data.get("op06_validation_plan_recorded") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 materialized branch requires OP06 plan recorded")
        if data.get("post_nci_triage_result_memo_draft_bodyfree") is not True or data.get("post_nci_triage_result_memo_draft_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 materialized branch must have body-free draft")
        if data.get("pnt_op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 materialized branch must be ready for OP08")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 materialized branch requires non-executed boundary")
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 materialized next step changed")
        if data.get("pnt_op07_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 materialized branch cannot carry blockers")
    elif status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_REPAIR_REQUIRED_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP07_RESULT_MEMO_DRAFT_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 repair next step changed")
    elif status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF:
        if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP07_RESULT_MEMO_DRAFT_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF:
        for field in (
            "op07_input_forbidden_payload_key_path_refs",
            "op07_input_body_like_value_path_refs",
            "op07_input_promotion_claim_refs",
            "op07_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP07 non-blocked branch cannot carry scan blockers")
    return True


def _op07_contract_valid(op07: Mapping[str, Any] | None) -> bool:
    if not isinstance(op07, Mapping):
        return False
    try:
        return assert_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material_contract(op07) is True
    except ValueError:
        return False


def _op08_status_reason_blocker_next(
    *,
    op07_present: bool,
    op07_valid: bool,
    op07_status_ref: str,
    op07_ready_for_op08: bool,
    nci_present: bool,
    nci_valid: bool,
    nci_status_ref: str,
    nci_closed: bool,
    op07_forbidden_paths: Sequence[str],
    op07_body_like_paths: Sequence[str],
    op07_promotion_claims: Sequence[str],
    op07_no_touch_paths: Sequence[str],
    nci_forbidden_paths: Sequence[str],
    nci_body_like_paths: Sequence[str],
    nci_promotion_claims: Sequence[str],
    nci_no_touch_paths: Sequence[str],
) -> tuple[str, list[str], list[str], str]:
    blockers: list[str] = []
    if op07_forbidden_paths:
        blockers.append("op08_result_memo_closure_op07_forbidden_payload_key_detected")
    if op07_body_like_paths:
        blockers.append("op08_result_memo_closure_op07_body_like_value_detected")
    if op07_promotion_claims:
        blockers.append("op08_result_memo_closure_op07_promotion_or_autorun_claim_detected")
    if op07_no_touch_paths:
        blockers.append("op08_result_memo_closure_op07_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if nci_forbidden_paths:
        blockers.append("op08_result_memo_closure_nci_op08_forbidden_payload_key_detected")
    if nci_body_like_paths:
        blockers.append("op08_result_memo_closure_nci_op08_body_like_value_detected")
    if nci_promotion_claims:
        blockers.append("op08_result_memo_closure_nci_op08_promotion_or_autorun_claim_detected")
    if nci_no_touch_paths:
        blockers.append("op08_result_memo_closure_nci_op08_api_db_rn_runtime_response_key_or_p8_question_touch_detected")
    if op07_status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_BLOCKED_REF:
        blockers.append("pnt_op07_result_memo_draft_blocked_before_op08_closure")
    if nci_status_ref == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF:
        blockers.append("nci_op08_status_bodyfree_leak_promotion_or_autorun_blocked_before_pnt_op08_closure")
    if blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF,
            ["post_nci_triage_result_memo_closure_blocked_without_downstream_promotion"],
            _dedupe_clean_refs(blockers, max_length=340),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF,
        )

    waiting_blockers: list[str] = []
    if not op07_present:
        waiting_blockers.append("pnt_op07_result_memo_draft_missing_for_op08_closure")
    if not nci_present:
        waiting_blockers.append("nci_op08_bodyfree_result_memo_closure_missing_for_pnt_op08_closure")
    if nci_valid and nci_status_ref == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF:
        waiting_blockers.append("nci_op08_waiting_for_input_refs_before_pnt_op08_closure")
    if waiting_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
            ["waiting_for_nci_op08_or_pnt_op07_result_memo_draft_before_closure"],
            _dedupe_clean_refs(waiting_blockers, max_length=340),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP08_INPUT_REFS_REF,
        )

    repair_blockers: list[str] = []
    if not op07_valid:
        repair_blockers.append("pnt_op07_result_memo_draft_contract_invalid")
    if not nci_valid:
        repair_blockers.append("nci_op08_bodyfree_result_memo_closure_contract_invalid")
    if op07_valid and not op07_ready_for_op08:
        repair_blockers.append("pnt_op07_result_memo_draft_not_ready_for_op08_closure")
    if op07_status_ref == P7_R54_AHR_POST_NCI_PNT_OP07_STATUS_REPAIR_REQUIRED_REF:
        repair_blockers.append("pnt_op07_result_memo_draft_repair_required_before_op08_closure")
    if nci_valid and nci_status_ref == nci.P7_R54_AHR_POST_RDB08_NCI_OP08_STATUS_REPAIR_REQUIRED_REF:
        repair_blockers.append("nci_op08_repair_required_before_pnt_op08_closure")
    if nci_valid and not nci_closed:
        repair_blockers.append("nci_op08_not_closed_bodyfree_stopped_before_pnt_op08_closure")
    if repair_blockers:
        return (
            P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_REPAIR_REQUIRED_REF,
            ["post_nci_triage_result_memo_closure_repair_required_without_downstream_promotion"],
            _dedupe_clean_refs(repair_blockers, max_length=340),
            P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF,
        )

    return (
        P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF,
        ["post_nci_triage_result_memo_closed_bodyfree_with_next_boundary_selection_without_execution"],
        [],
        "closed_branch_uses_selected_post_nci_next_boundary_ref",
    )


def build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure(
    pnt_op07_post_nci_triage_result_memo_draft_material: Mapping[str, Any] | None = None,
    *,
    nci_op08_bodyfree_selected_candidate_intake_result_memo_closure: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Close PNT-OP00〜OP07 body-free result memo with next boundary selection, without execution."""

    session_id = _safe_review_session_id(review_session_id)
    op07 = pnt_op07_post_nci_triage_result_memo_draft_material
    nci_op08 = nci_op08_bodyfree_selected_candidate_intake_result_memo_closure
    op07_present = isinstance(op07, Mapping)
    nci_present = isinstance(nci_op08, Mapping)
    op07_valid = _op07_contract_valid(op07)
    nci_valid = _nci_op08_contract_valid(nci_op08)
    op07_status_ref = _clean_ref(op07.get("pnt_op07_status_ref") if isinstance(op07, Mapping) else None, default="missing", max_length=260)
    nci_status_ref = _clean_ref(nci_op08.get("nci_op08_status_ref") if isinstance(nci_op08, Mapping) else None, default="missing", max_length=260)
    op07_ready_for_op08 = bool(
        op07_valid
        and op07
        and op07.get("pnt_op07_ready_for_op08") is True
        and op07.get("next_required_step") == P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF
    )
    nci_closed = bool(nci_valid and nci_op08 and nci_op08.get("nci_op08_closed_bodyfree_stopped") is True)

    op07_forbidden, op07_body_like, op07_promotion, op07_no_touch = _bodyfree_no_touch_scan_quads(op07 or {}, path="pnt_op07")
    nci_forbidden, nci_body_like, nci_promotion, nci_no_touch = _bodyfree_no_touch_scan_quads(nci_op08 or {}, path="nci_op08")
    status_ref, reason_refs, blocker_refs, next_required_step = _op08_status_reason_blocker_next(
        op07_present=op07_present,
        op07_valid=op07_valid,
        op07_status_ref=op07_status_ref,
        op07_ready_for_op08=op07_ready_for_op08,
        nci_present=nci_present,
        nci_valid=nci_valid,
        nci_status_ref=nci_status_ref,
        nci_closed=nci_closed,
        op07_forbidden_paths=op07_forbidden,
        op07_body_like_paths=op07_body_like,
        op07_promotion_claims=op07_promotion,
        op07_no_touch_paths=op07_no_touch,
        nci_forbidden_paths=nci_forbidden,
        nci_body_like_paths=nci_body_like,
        nci_promotion_claims=nci_promotion,
        nci_no_touch_paths=nci_no_touch,
    )
    closed = status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF

    def _copy_op07_ref(key: str, default: str = "missing", max_length: int = 420) -> str:
        return _clean_ref(op07.get(key) if isinstance(op07, Mapping) else None, default=default, max_length=max_length)

    def _copy_nci_ref(key: str, default: str = "missing", max_length: int = 420) -> str:
        return _clean_ref(nci_op08.get(key) if isinstance(nci_op08, Mapping) else None, default=default, max_length=max_length)

    if closed:
        selected_pnt_status_ref = _copy_op07_ref("selected_pnt_status_ref", max_length=260)
        selected_pnt_lane_ref = _copy_op07_ref("selected_pnt_lane_ref", max_length=260)
        selected_post_nci_outcome_group_ref = _copy_op07_ref("selected_post_nci_outcome_group_ref", max_length=260)
        selected_post_nci_next_boundary_ref = _copy_op07_ref("selected_post_nci_next_boundary_ref", max_length=420)
        selected_post_nci_next_boundary_kind_ref = _copy_op07_ref("selected_post_nci_next_boundary_kind_ref", max_length=420)
        selected_post_nci_next_boundary_not_executed = bool(op07.get("selected_post_nci_next_boundary_not_executed") is True)  # type: ignore[union-attr]
        selected_post_nci_next_boundary_execution_allowed_here = False
        selected_post_nci_next_boundary_materialized_here = bool(op07.get("selected_post_nci_next_boundary_materialized_here") is True)  # type: ignore[union-attr]
        selected_handoff_or_stop_ref = _copy_nci_ref("selected_handoff_or_stop_ref", default=selected_post_nci_next_boundary_ref, max_length=420)
        selected_handoff_or_stop_kind_ref = _copy_nci_ref("selected_handoff_or_stop_kind_ref", default=selected_post_nci_next_boundary_kind_ref, max_length=420)
        selected_handoff_or_stop_not_executed = bool(nci_op08.get("selected_handoff_or_stop_not_executed") is True)  # type: ignore[union-attr]
        next_design_document_candidate_ref = _copy_op07_ref("next_design_document_candidate_ref", max_length=420)
        next_design_document_allowed = bool(op07.get("next_design_document_allowed") is True)  # type: ignore[union-attr]
        manual_wait_required = bool(op07.get("manual_wait_required") is True)  # type: ignore[union-attr]
        manual_stop_required = bool(op07.get("manual_stop_required") is True)  # type: ignore[union-attr]
        repair_design_candidate = bool(op07.get("repair_design_candidate") is True)  # type: ignore[union-attr]
        validation_plan_recorded = bool(op07.get("validation_plan_recorded") is True)  # type: ignore[union-attr]
        closure_ref = _clean_ref(
            "pnt_op08_bodyfree_post_nci_triage_result_memo_closure_for_" + selected_post_nci_next_boundary_ref,
            default="pnt_op08_bodyfree_post_nci_triage_result_memo_closure",
            max_length=420,
        )
        next_required_step = selected_post_nci_next_boundary_ref
    else:
        selected_pnt_status_ref = status_ref
        selected_pnt_lane_ref = "missing"
        selected_post_nci_outcome_group_ref = "missing"
        selected_post_nci_next_boundary_ref = "missing"
        selected_post_nci_next_boundary_kind_ref = "missing"
        selected_post_nci_next_boundary_not_executed = False
        selected_post_nci_next_boundary_execution_allowed_here = False
        selected_post_nci_next_boundary_materialized_here = False
        selected_handoff_or_stop_ref = "missing"
        selected_handoff_or_stop_kind_ref = "missing"
        selected_handoff_or_stop_not_executed = False
        next_design_document_candidate_ref = "missing"
        next_design_document_allowed = False
        manual_wait_required = False
        manual_stop_required = False
        repair_design_candidate = False
        validation_plan_recorded = False
        closure_ref = "missing"

    validation_command_summary_refs = list(op07.get("validation_command_summary_refs") if isinstance(op07, Mapping) and isinstance(op07.get("validation_command_summary_refs"), Sequence) and not isinstance(op07.get("validation_command_summary_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS)
    target_test_refs = list(op07.get("target_test_ref_refs") if isinstance(op07, Mapping) and isinstance(op07.get("target_test_ref_refs"), Sequence) and not isinstance(op07.get("target_test_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS)
    selected_regression_refs = list(op07.get("selected_regression_test_ref_refs") if isinstance(op07, Mapping) and isinstance(op07.get("selected_regression_test_ref_refs"), Sequence) and not isinstance(op07.get("selected_regression_test_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS)
    compileall_refs = list(op07.get("compileall_target_ref_refs") if isinstance(op07, Mapping) and isinstance(op07.get("compileall_target_ref_refs"), Sequence) and not isinstance(op07.get("compileall_target_ref_refs"), (str, bytes, bytearray)) else P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS)

    return {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_OP08_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "policy_section": P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        "current_phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "material_id": "p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_20260707",
        "review_session_id": session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "op07_material_present": op07_present,
        "op07_contract_valid": op07_valid,
        "op07_schema_version": _copy_op07_ref("schema_version", max_length=260),
        "op07_material_ref": _copy_op07_ref("material_id", max_length=260),
        "op07_status_ref": op07_status_ref,
        "op07_next_required_step": _copy_op07_ref("next_required_step", max_length=420),
        "op07_ready_for_op08": op07_ready_for_op08,
        "nci_op08_material_present": nci_present,
        "nci_op08_contract_valid": nci_valid,
        "nci_op08_schema_version": _copy_nci_ref("schema_version", max_length=260),
        "nci_op08_material_ref": _copy_nci_ref("material_id", max_length=260),
        "nci_op08_status_ref": nci_status_ref,
        "nci_op08_closed_bodyfree_stopped": nci_closed,
        "post_nci_triage_result_memo_draft_ref": _copy_op07_ref("post_nci_triage_result_memo_draft_ref", max_length=420),
        "post_nci_triage_result_memo_draft_bodyfree": bool(op07_valid and op07 and op07.get("post_nci_triage_result_memo_draft_bodyfree") is True),
        "post_nci_triage_result_memo_draft_materialized_here": bool(op07_valid and op07 and op07.get("post_nci_triage_result_memo_draft_materialized_here") is True),
        "bodyfree_post_nci_triage_result_memo_closure_ref": closure_ref,
        "bodyfree_post_nci_triage_result_memo_closure_bodyfree": closed,
        "bodyfree_post_nci_triage_result_memo_closure_materialized_here": closed,
        "bodyfree_post_nci_triage_result_memo_closure_execution_allowed_here": False,
        "selected_pnt_status_ref": selected_pnt_status_ref,
        "selected_pnt_lane_ref": selected_pnt_lane_ref,
        "selected_post_nci_outcome_group_ref": selected_post_nci_outcome_group_ref,
        "selected_post_nci_next_boundary_ref": selected_post_nci_next_boundary_ref,
        "selected_post_nci_next_boundary_kind_ref": selected_post_nci_next_boundary_kind_ref,
        "selected_post_nci_next_boundary_not_executed": selected_post_nci_next_boundary_not_executed,
        "selected_post_nci_next_boundary_execution_allowed_here": selected_post_nci_next_boundary_execution_allowed_here,
        "selected_post_nci_next_boundary_materialized_here": selected_post_nci_next_boundary_materialized_here,
        "selected_handoff_or_stop_ref": selected_handoff_or_stop_ref,
        "selected_handoff_or_stop_kind_ref": selected_handoff_or_stop_kind_ref,
        "selected_handoff_or_stop_not_executed": selected_handoff_or_stop_not_executed,
        "next_design_document_candidate_ref": next_design_document_candidate_ref,
        "next_design_document_allowed": next_design_document_allowed,
        "manual_wait_required": manual_wait_required,
        "manual_stop_required": manual_stop_required,
        "repair_design_candidate": repair_design_candidate,
        "validation_plan_ref": _copy_op07_ref("validation_plan_ref", max_length=320),
        "validation_plan_recorded": validation_plan_recorded,
        "validation_command_summary_refs": validation_command_summary_refs,
        "validation_command_summary_ref_count": len(validation_command_summary_refs),
        "target_test_ref_refs": target_test_refs,
        "target_test_ref_count": len(target_test_refs),
        "selected_regression_test_ref_refs": selected_regression_refs,
        "selected_regression_test_ref_count": len(selected_regression_refs),
        "compileall_target_ref_refs": compileall_refs,
        "compileall_target_ref_count": len(compileall_refs),
        "target_test_result_status_ref": _copy_op07_ref("target_test_result_status_ref", max_length=260),
        "selected_regression_result_status_ref": _copy_op07_ref("selected_regression_result_status_ref", max_length=260),
        "compileall_result_status_ref": _copy_op07_ref("compileall_result_status_ref", max_length=260),
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "pnt_op08_status_ref": status_ref,
        "bodyfree_post_nci_triage_result_memo_closure_status_ref": status_ref,
        "pnt_op08_allowed_status_refs": list(P7_R54_AHR_POST_NCI_PNT_OP08_ALLOWED_STATUS_REFS),
        "pnt_op08_allowed_status_ref_count": len(P7_R54_AHR_POST_NCI_PNT_OP08_ALLOWED_STATUS_REFS),
        "pnt_op08_bodyfree_post_nci_triage_closed_stopped": closed,
        "pnt_op08_waiting_for_input_refs": status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF,
        "pnt_op08_repair_required": status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_REPAIR_REQUIRED_REF,
        "pnt_op08_bodyfree_leak_promotion_or_autorun_blocked": status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF,
        "pnt_op08_reason_refs": reason_refs,
        "pnt_op08_reason_ref_count": len(reason_refs),
        "pnt_op08_blocker_refs": blocker_refs,
        "pnt_op08_blocker_ref_count": len(blocker_refs),
        "op08_op07_input_forbidden_payload_key_path_refs": list(op07_forbidden),
        "op08_op07_input_forbidden_payload_key_path_count": len(op07_forbidden),
        "op08_op07_input_body_like_value_path_refs": list(op07_body_like),
        "op08_op07_input_body_like_value_path_count": len(op07_body_like),
        "op08_op07_input_promotion_claim_refs": list(op07_promotion),
        "op08_op07_input_promotion_claim_ref_count": len(op07_promotion),
        "op08_op07_input_no_touch_mutation_path_refs": list(op07_no_touch),
        "op08_op07_input_no_touch_mutation_path_count": len(op07_no_touch),
        "op08_nci_input_forbidden_payload_key_path_refs": list(nci_forbidden),
        "op08_nci_input_forbidden_payload_key_path_count": len(nci_forbidden),
        "op08_nci_input_body_like_value_path_refs": list(nci_body_like),
        "op08_nci_input_body_like_value_path_count": len(nci_body_like),
        "op08_nci_input_promotion_claim_refs": list(nci_promotion),
        "op08_nci_input_promotion_claim_ref_count": len(nci_promotion),
        "op08_nci_input_no_touch_mutation_path_refs": list(nci_no_touch),
        "op08_nci_input_no_touch_mutation_path_count": len(nci_no_touch),
        "selected_handoff_or_stop_execution_allowed_here": False,
        "dhr_op05_call_allowed_here": False,
        "dhr_op05_builder_call_allowed_here": False,
        "dhr_op06_call_allowed_here": False,
        "dmd_r52_execution_allowed_here": False,
        "actual_review_start_allowed_here": False,
        "raw_evidence_request_allowed_here": False,
        "repair_execution_allowed_here": False,
        "p8_question_design_allowed_here": False,
        "api_db_rn_response_key_change_allowed_here": False,
        "pnt_op08_does_not_execute_selected_handoff_or_stop": True,
        "pnt_op08_does_not_execute_selected_post_nci_next_boundary": True,
        "pnt_op08_does_not_call_dhr_op05": True,
        "pnt_op08_does_not_call_dhr_op06": True,
        "pnt_op08_does_not_execute_dmd_r52_or_release": True,
        "pnt_op08_does_not_start_actual_review": True,
        "pnt_op08_does_not_request_raw_evidence": True,
        "pnt_op08_does_not_execute_repair": True,
        "pnt_op08_does_not_start_p5_p6_p8_p7_or_release": True,
        "pnt_op08_does_not_change_api_db_rn_runtime_response_key": True,
        "pnt_op08_does_not_materialize_p8_question_spec": True,
        "dhr_op05_not_called": True,
        "dhr_op06_not_called": True,
        "dmd_r52_not_executed": True,
        "p5_p6_p8_p7_release_not_started": True,
        "p8_question_design_not_started": True,
        "p8_question_implementation_not_started": True,
        "api_db_rn_runtime_response_key_not_changed": True,
        "claim_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS),
        "not_claimed_boundary_refs": list(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary_ref_count": len(P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS),
        "not_claimed_boundary": _not_claimed_boundary(),
        "fixed_non_promotion_refs": list(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "fixed_non_promotion_ref_count": len(P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS),
        "implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_POST_NCI_PNT_OP08_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_required_step,
        "public_contract": public_contract_flags(),
        "pnt_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        **_false_flags(),
        "body_free": True,
    }


def assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract(
    data: Mapping[str, Any]
) -> bool:
    """Assert PNT-OP08 body-free result memo closure contract without downstream execution."""

    _required_fields_present(data, required=P7_R54_AHR_POST_NCI_PNT_OP08_REQUIRED_FIELD_REFS, source="P7-R54-AHR-PostNCI-PNT-OP08")
    if set(data) != set(P7_R54_AHR_POST_NCI_PNT_OP08_REQUIRED_FIELD_REFS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 field set changed")
    _assert_base_bodyfree_boundary(
        data,
        schema_version=P7_R54_AHR_POST_NCI_PNT_OP08_SCHEMA_VERSION,
        operation_step_ref=P7_R54_AHR_POST_NCI_PNT_OP08_STEP_REF,
        source="P7-R54-AHR-PostNCI-PNT-OP08",
    )
    if data.get("bodyfree_post_nci_triage_result_memo_closure_status_ref") != data.get("pnt_op08_status_ref"):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 status alias changed")
    if tuple(data.get("pnt_op08_allowed_status_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_OP08_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 allowed status refs changed")
    for key in (
        "bodyfree_post_nci_triage_result_memo_closure_execution_allowed_here",
        "selected_handoff_or_stop_execution_allowed_here",
        "selected_post_nci_next_boundary_execution_allowed_here",
        "dhr_op05_call_allowed_here",
        "dhr_op05_builder_call_allowed_here",
        "dhr_op06_call_allowed_here",
        "dmd_r52_execution_allowed_here",
        "actual_review_start_allowed_here",
        "raw_evidence_request_allowed_here",
        "repair_execution_allowed_here",
        "p8_question_design_allowed_here",
        "api_db_rn_response_key_change_allowed_here",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified_claimed_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP08 forbidden execution/claim changed: {key}")
    for key in (
        "pnt_op08_does_not_execute_selected_handoff_or_stop",
        "pnt_op08_does_not_execute_selected_post_nci_next_boundary",
        "pnt_op08_does_not_call_dhr_op05",
        "pnt_op08_does_not_call_dhr_op06",
        "pnt_op08_does_not_execute_dmd_r52_or_release",
        "pnt_op08_does_not_start_actual_review",
        "pnt_op08_does_not_request_raw_evidence",
        "pnt_op08_does_not_execute_repair",
        "pnt_op08_does_not_start_p5_p6_p8_p7_or_release",
        "pnt_op08_does_not_change_api_db_rn_runtime_response_key",
        "pnt_op08_does_not_materialize_p8_question_spec",
        "dhr_op05_not_called",
        "dhr_op06_not_called",
        "dmd_r52_not_executed",
        "p5_p6_p8_p7_release_not_started",
        "p8_question_design_not_started",
        "p8_question_implementation_not_started",
        "api_db_rn_runtime_response_key_not_changed",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP08 required true boundary changed: {key}")
    for field, count_field in (
        ("validation_command_summary_refs", "validation_command_summary_ref_count"),
        ("target_test_ref_refs", "target_test_ref_count"),
        ("selected_regression_test_ref_refs", "selected_regression_test_ref_count"),
        ("compileall_target_ref_refs", "compileall_target_ref_count"),
        ("pnt_op08_allowed_status_refs", "pnt_op08_allowed_status_ref_count"),
        ("pnt_op08_reason_refs", "pnt_op08_reason_ref_count"),
        ("pnt_op08_blocker_refs", "pnt_op08_blocker_ref_count"),
        ("op08_op07_input_forbidden_payload_key_path_refs", "op08_op07_input_forbidden_payload_key_path_count"),
        ("op08_op07_input_body_like_value_path_refs", "op08_op07_input_body_like_value_path_count"),
        ("op08_op07_input_promotion_claim_refs", "op08_op07_input_promotion_claim_ref_count"),
        ("op08_op07_input_no_touch_mutation_path_refs", "op08_op07_input_no_touch_mutation_path_count"),
        ("op08_nci_input_forbidden_payload_key_path_refs", "op08_nci_input_forbidden_payload_key_path_count"),
        ("op08_nci_input_body_like_value_path_refs", "op08_nci_input_body_like_value_path_count"),
        ("op08_nci_input_promotion_claim_refs", "op08_nci_input_promotion_claim_ref_count"),
        ("op08_nci_input_no_touch_mutation_path_refs", "op08_nci_input_no_touch_mutation_path_count"),
        ("claim_boundary_refs", "claim_boundary_ref_count"),
        ("not_claimed_boundary_refs", "not_claimed_boundary_ref_count"),
        ("fixed_non_promotion_refs", "fixed_non_promotion_ref_count"),
    ):
        if data.get(count_field) != len(data.get(field) or []):
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-OP08 {count_field} changed")
    if tuple(data.get("target_test_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 target refs changed")
    if tuple(data.get("selected_regression_test_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 selected regression refs changed")
    if tuple(data.get("compileall_target_ref_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 compileall refs changed")
    if tuple(data.get("validation_command_summary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 validation command summary refs changed")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 claim boundary refs changed")
    if tuple(data.get("not_claimed_boundary_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 not-claimed boundary refs changed")
    if any(value is not False for value in (data.get("not_claimed_boundary") or {}).values()):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 not-claimed boundary must stay false")
    if tuple(data.get("fixed_non_promotion_refs") or ()) != P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 fixed non-promotion refs changed")
    if data.get("implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP08_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 implemented steps changed")
    if data.get("not_yet_implemented_steps") != list(P7_R54_AHR_POST_NCI_PNT_OP08_NOT_YET_IMPLEMENTED_STEPS):
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 not-yet steps changed")
    status_ref = data.get("pnt_op08_status_ref")
    flags = [
        data.get("pnt_op08_bodyfree_post_nci_triage_closed_stopped") is True,
        data.get("pnt_op08_waiting_for_input_refs") is True,
        data.get("pnt_op08_repair_required") is True,
        data.get("pnt_op08_bodyfree_leak_promotion_or_autorun_blocked") is True,
    ]
    if status_ref not in P7_R54_AHR_POST_NCI_PNT_OP08_ALLOWED_STATUS_REFS or sum(flags) != 1:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 exactly one status branch must be selected")
    if status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_CLOSED_STOPPED_REF:
        if data.get("op07_contract_valid") is not True or data.get("op07_ready_for_op08") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 closed branch requires OP07 ready")
        if data.get("nci_op08_contract_valid") is not True or data.get("nci_op08_closed_bodyfree_stopped") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 closed branch requires closed NCI-OP08")
        if data.get("bodyfree_post_nci_triage_result_memo_closure_bodyfree") is not True or data.get("bodyfree_post_nci_triage_result_memo_closure_materialized_here") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 closed branch requires body-free closure")
        if data.get("selected_post_nci_next_boundary_not_executed") is not True or data.get("selected_handoff_or_stop_not_executed") is not True:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 closed branch requires selected refs not executed")
        if data.get("next_required_step") != data.get("selected_post_nci_next_boundary_ref"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 closed branch next step must record selected boundary ref")
        if data.get("pnt_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 closed branch cannot carry blockers")
    else:
        if not data.get("pnt_op08_blocker_refs"):
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 non-closed branch must carry blockers")
        if data.get("selected_post_nci_next_boundary_not_executed") is not False or data.get("selected_handoff_or_stop_not_executed") is not False:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 non-closed branch cannot expose selected executable refs")
        if status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_WAITING_FOR_INPUT_REFS_REF and data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_WAIT_FOR_OP08_INPUT_REFS_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 waiting next step changed")
        if status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_REPAIR_REQUIRED_REF and data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_REPAIR_OP08_CLOSURE_INPUTS_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 repair next step changed")
        if status_ref == P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF and data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_NEXT_STEP_BLOCKED_OP08_CLOSURE_REF:
            raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 blocked next step changed")
    if status_ref != P7_R54_AHR_POST_NCI_PNT_OP08_STATUS_BLOCKED_REF:
        for field in (
            "op08_op07_input_forbidden_payload_key_path_refs",
            "op08_op07_input_body_like_value_path_refs",
            "op08_op07_input_promotion_claim_refs",
            "op08_op07_input_no_touch_mutation_path_refs",
            "op08_nci_input_forbidden_payload_key_path_refs",
            "op08_nci_input_body_like_value_path_refs",
            "op08_nci_input_promotion_claim_refs",
            "op08_nci_input_no_touch_mutation_path_refs",
        ):
            if data.get(field):
                raise ValueError("P7-R54-AHR-PostNCI-PNT-OP08 non-blocked branch cannot carry scan blockers")
    return True

def build_p7_r54_ahr_post_nci_pnt_r1_helper_skeleton_constants_summary(
    *,
    review_session_id: str | None = None,
) -> dict[str, Any]:
    """Return a body-free R0/R1 constants summary without calling NCI builders."""

    safe_review_session_id = clean_identifier(
        review_session_id,
        default=P7_R54_AHR_POST_NCI_PNT_DEFAULT_REVIEW_SESSION_ID,
        max_length=160,
    )
    data: dict[str, Any] = {
        "schema_version": P7_R54_AHR_POST_NCI_PNT_R1_SCHEMA_VERSION,
        "phase": P7_R54_AHR_POST_NCI_PNT_PHASE,
        "step": P7_R54_AHR_POST_NCI_PNT_STEP,
        "scope": P7_R54_AHR_POST_NCI_PNT_SCOPE,
        "policy_kind": P7_R54_AHR_POST_NCI_PNT_POLICY_KIND,
        "operation_step_ref": P7_R54_AHR_POST_NCI_PNT_R1_STEP_REF,
        "material_id": "p7_r54_ahr_post_nci_pnt_r1_helper_skeleton_constants_summary_20260707",
        "review_session_id": safe_review_session_id,
        "source_mode": P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "selected_stage_ref": P7_R54_AHR_POST_NCI_PNT_SELECTED_STAGE_REF,
        "selected_design_target_ref": P7_R54_AHR_POST_NCI_PNT_SELECTED_DESIGN_TARGET_REF,
        "boundary_prefix_ref": P7_R54_AHR_POST_NCI_PNT_BOUNDARY_PREFIX_REF,
        "boundary_prefix_meaning_ref": P7_R54_AHR_POST_NCI_PNT_BOUNDARY_PREFIX_MEANING_REF,
        "expected_from_nci_op08_ref": P7_R54_AHR_POST_NCI_PNT_EXPECTED_FROM_NCI_OP08_REF,
        "expected_next_required_step_ref": P7_R54_AHR_POST_NCI_PNT_EXPECTED_NEXT_REQUIRED_STEP_REF,
        "implemented_step_refs": P7_R54_AHR_POST_NCI_PNT_R0_R1_IMPLEMENTED_STEPS,
        "not_yet_implemented_step_refs": P7_R54_AHR_POST_NCI_PNT_R0_R1_NOT_YET_IMPLEMENTED_STEPS,
        "pnt_step_refs": P7_R54_AHR_POST_NCI_PNT_STEP_REFS,
        "local_received_zip_refs": dict(P7_R54_AHR_POST_NCI_PNT_LOCAL_RECEIVED_ZIP_REFS),
        "support_material_refs": P7_R54_AHR_POST_NCI_PNT_SUPPORT_MATERIAL_REFS,
        "not_stage_refs": P7_R54_AHR_POST_NCI_PNT_NOT_STAGE_REFS,
        "claim_boundary_refs": P7_R54_AHR_POST_NCI_PNT_CLAIM_BOUNDARY_REFS,
        "not_claimed_boundary_refs": P7_R54_AHR_POST_NCI_PNT_NOT_CLAIMED_BOUNDARY_REFS,
        "fixed_non_promotion_refs": P7_R54_AHR_POST_NCI_PNT_FIXED_NON_PROMOTION_REFS,
        "explicit_nci_op08_material_required": P7_R54_AHR_POST_NCI_PNT_EXPLICIT_NCI_OP08_MATERIAL_REQUIRED,
        "nci_op08_default_builder_call_allowed": P7_R54_AHR_POST_NCI_PNT_NCI_OP08_DEFAULT_BUILDER_CALL_ALLOWED,
        "nci_op08_default_material_synthesis_allowed": P7_R54_AHR_POST_NCI_PNT_NCI_OP08_DEFAULT_MATERIAL_SYNTHESIS_ALLOWED,
        "nci_op08_test_fixture_generation_allowed_only_inside_tests": P7_R54_AHR_POST_NCI_PNT_NCI_OP08_TEST_FIXTURE_GENERATION_ALLOWED_ONLY_INSIDE_TESTS,
        "selected_handoff_or_stop_execution_allowed_here": P7_R54_AHR_POST_NCI_PNT_SELECTED_HANDOFF_OR_STOP_EXECUTION_ALLOWED_HERE,
        "dhr_op05_call_allowed_here": P7_R54_AHR_POST_NCI_PNT_DHR_OP05_CALL_ALLOWED_HERE,
        "dhr_op05_builder_call_allowed_here": P7_R54_AHR_POST_NCI_PNT_DHR_OP05_BUILDER_CALL_ALLOWED_HERE,
        "p8_question_design_allowed_here": P7_R54_AHR_POST_NCI_PNT_P8_QUESTION_DESIGN_ALLOWED_HERE,
        "api_db_rn_response_key_change_allowed_here": P7_R54_AHR_POST_NCI_PNT_API_DB_RN_RESPONSE_KEY_CHANGE_ALLOWED_HERE,
        "allowed_lane_refs": P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS,
        "allowed_selected_handoff_or_stop_refs": P7_R54_AHR_POST_NCI_PNT_ALLOWED_SELECTED_HANDOFF_OR_STOP_REFS,
        "allowed_outcome_group_refs": P7_R54_AHR_POST_NCI_PNT_ALLOWED_OUTCOME_GROUP_REFS,
        "allowed_handoff_lane_refs": P7_R54_AHR_POST_NCI_PNT_ALLOWED_HANDOFF_LANE_REFS,
        "allowed_stop_lane_refs": P7_R54_AHR_POST_NCI_PNT_ALLOWED_STOP_LANE_REFS,
        "required_nci_op08_key_refs": P7_R54_AHR_POST_NCI_PNT_NCI_OP08_REQUIRED_KEY_REFS,
        "no_touch_contract_keys": P7_R54_AHR_POST_NCI_PNT_NO_TOUCH_CONTRACT_KEYS,
        "body_free_marker_refs": P7_R54_AHR_POST_NCI_PNT_BODY_FREE_MARKER_REFS,
        "forbidden_payload_key_refs": P7_R54_AHR_POST_NCI_PNT_FORBIDDEN_PAYLOAD_KEY_REFS,
        "promotion_claim_field_refs": P7_R54_AHR_POST_NCI_PNT_PROMOTION_CLAIM_FIELD_REFS,
        "required_false_flag_refs": P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS,
        "target_test_ref_refs": P7_R54_AHR_POST_NCI_PNT_TARGET_TEST_REF_REFS,
        "selected_regression_test_ref_refs": P7_R54_AHR_POST_NCI_PNT_SELECTED_REGRESSION_TEST_REF_REFS,
        "compileall_target_ref_refs": P7_R54_AHR_POST_NCI_PNT_COMPILEALL_TARGET_REF_REFS,
        "validation_command_summary_refs": P7_R54_AHR_POST_NCI_PNT_VALIDATION_COMMAND_SUMMARY_REFS,
        "pnt_op00_implemented": False,
        "pnt_op01_implemented": False,
        "selected_handoff_or_stop_executed_here": False,
        "handoff_or_stop_envelope_executed_here": False,
        "nci_op08_default_builder_called_here": False,
        "nci_op08_default_material_synthesized_here": False,
        "dhr_op05_called_here": False,
        "dhr_op05_builder_called_here": False,
        "dhr_op06_called_here": False,
        "dhr_op07_materialized_here": False,
        "dmd_execution_started_here": False,
        "r52_actual_execution_started_here": False,
        "actual_review_started_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_rows_created_here": False,
        "actual_question_need_observation_rows_created_here": False,
        "actual_disposal_or_purge_executed_here": False,
        "p8_start_allowed": False,
        "p8_question_design_started": False,
        "p8_question_implementation_started": False,
        "question_text_materialized": False,
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "response_key_changed": False,
        "p7_complete": False,
        "release_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified_claimed_here": False,
        "next_required_step": P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF,
        "body_free": True,
    }
    return data


def assert_p7_r54_ahr_post_nci_pnt_r1_helper_skeleton_constants_summary_contract(
    data: Mapping[str, Any],
) -> bool:
    """Validate the R0/R1 skeleton summary without validating future OP00+ output."""

    if data.get("schema_version") != P7_R54_AHR_POST_NCI_PNT_R1_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 schema version mismatch")
    if data.get("operation_step_ref") != P7_R54_AHR_POST_NCI_PNT_R1_STEP_REF:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 operation step mismatch")
    if data.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 must remain body-free")
    if data.get("source_mode") != P7_R54_AHR_POST_NCI_PNT_SOURCE_MODE:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 source mode mismatch")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 must not require/check GitHub")
    if tuple(data.get("implemented_step_refs", ())) != P7_R54_AHR_POST_NCI_PNT_R0_R1_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 implemented steps mismatch")
    if tuple(data.get("not_yet_implemented_step_refs", ())) != P7_R54_AHR_POST_NCI_PNT_R0_R1_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 must leave PNT-OP00..OP08 not yet implemented")
    if data.get("explicit_nci_op08_material_required") is not True:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 must require explicit future NCI-OP08 material")
    if data.get("nci_op08_default_builder_call_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 must not allow NCI-OP08 default builder calls")
    if data.get("nci_op08_default_material_synthesis_allowed") is not False:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 must not allow NCI-OP08 material synthesis")
    if tuple(data.get("allowed_lane_refs", ())) != P7_R54_AHR_POST_NCI_PNT_ALLOWED_LANE_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 allowed lane refs mismatch")
    if tuple(data.get("allowed_selected_handoff_or_stop_refs", ())) != P7_R54_AHR_POST_NCI_PNT_ALLOWED_SELECTED_HANDOFF_OR_STOP_REFS:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 allowed selected handoff-or-stop refs mismatch")
    if data.get("next_required_step") != P7_R54_AHR_POST_NCI_PNT_OP00_STEP_REF:
        raise ValueError("P7-R54-AHR-PostNCI-PNT-R1 next step must be PNT-OP00")
    for key in P7_R54_AHR_POST_NCI_PNT_REQUIRED_FALSE_FLAG_REFS:
        if key in data and data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-PostNCI-PNT-R1 forbidden promotion flag set: {key}")
    return True


build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08 = (
    build_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op00_scope_explicit_input_no_execution_refreeze_after_nci_op08_contract
)
build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake = (
    build_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op01_explicit_nci_op08_bodyfree_result_memo_closure_intake_contract
)

build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation = (
    build_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op02_selected_handoff_or_stop_shape_validation_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op02_selected_handoff_or_stop_shape_validation_contract
)
build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver = (
    build_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op03_selected_handoff_or_stop_lane_consistency_resolver_contract
)
build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_next_boundary_selection_materialization = (
    build_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op04_next_boundary_selection_materialization_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op04_next_boundary_selection_materialization_contract
)
build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard = (
    build_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op05_bodyfree_no_touch_no_promotion_no_auto_execution_guard_contract
)
build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan = (
    build_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op06_selected_regression_compileall_validation_plan_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op06_selected_regression_compileall_validation_plan_contract
)
build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op07_post_nci_triage_result_memo_draft_material = (
    build_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op07_post_nci_triage_result_memo_draft_material_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op07_post_nci_triage_result_memo_draft_material_contract
)

build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_bodyfree_post_nci_triage_result_memo_closure = (
    build_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract = (
    assert_p7_r54_ahr_post_nci_pnt_op08_bodyfree_post_nci_triage_result_memo_closure_contract
)

build_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_r1_helper_skeleton_constants_summary = (
    build_p7_r54_ahr_post_nci_pnt_r1_helper_skeleton_constants_summary
)
assert_p7_r54_ahr_post_nci_selected_handoff_or_stop_decision_triage_pnt_r1_helper_skeleton_constants_summary_contract = (
    assert_p7_r54_ahr_post_nci_pnt_r1_helper_skeleton_constants_summary_contract
)

__all__ = tuple(
    name
    for name in globals()
    if name.startswith("P7_R54_AHR_POST_NCI_PNT_")
    or name.startswith("build_p7_r54_ahr_post_nci")
    or name.startswith("assert_p7_r54_ahr_post_nci")
)
