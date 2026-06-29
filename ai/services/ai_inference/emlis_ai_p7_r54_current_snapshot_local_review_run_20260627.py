# -*- coding: utf-8 -*-
"""P7-R54 current snapshot local review run CLR00-CLR03 helpers.

This module materializes the first four body-free boundary steps from the
2026-06-27 current snapshot local run design.

R54-CLR-00 freezes the scope and no-touch boundary. It does not mark the
snapshot as used by actual review yet.

R54-CLR-01 refreezes the 2026-06-27 received snapshot refs as the actual review
basis. R54-CLR-02 reconciles historical helper refs as structural / regression
context only. R54-CLR-03 intakes the existing R55 actual-review-evidence-missing
hold before any local review execution.

No API, DB, RN, runtime, public response contract, P8 question implementation,
body-full packet generation, actual human review, disposal, P5 finalization,
P6/P8 start, P7 completion, or release permission is performed here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    public_contract_flags,
    safe_mapping,
)
import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as r54ev
import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54handoff
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55
import emlis_ai_product_readfeel_p4_r11_summary_decision_handoff as p4r11


P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr00_scope_no_touch_boundary_freeze.bodyfree.v1"
)
P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr01_current_snapshot_basis_refreeze.bodyfree.v1"
)
P7_R54_CLR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr02_historical_helper_refs_reconcile.bodyfree.v1"
)
P7_R54_CLR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.current_snapshot_local_run.clr03_r55_hold_evidence_missing_intake.bodyfree.v1"
)
P7_R54_CLR00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
)
P7_R54_CLR01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION: Final = (
    P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION
)
P7_R54_CLR02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION: Final = (
    P7_R54_CLR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
)
P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION: Final = (
    P7_R54_CLR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION
)

P7_R54_CLR_STEP: Final = "R54_current_snapshot_local_review_run_20260627"
P7_R54_CLR_SCOPE: Final = "p5_human_blind_qa_actual_local_review_current_snapshot_local_run"
P7_R54_CLR_POLICY_KIND: Final = "r54_actual_review_current_snapshot_local_run_bodyfree_boundary"
P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r54_actual_local_review_current_snapshot_20260627"

P7_R54_CLR00_STEP_REF: Final = "R54-CLR-00_scope_no_touch_boundary_freeze"
P7_R54_CLR01_STEP_REF: Final = "R54-CLR-01_current_snapshot_basis_refreeze"
P7_R54_CLR02_STEP_REF: Final = "R54-CLR-02_historical_helper_refs_reconcile"
P7_R54_CLR03_STEP_REF: Final = "R54-CLR-03_r55_hold_evidence_missing_intake"
P7_R54_CLR04_STEP_REF: Final = "R54-CLR-04_local_only_preflight"
P7_R54_CLR05_STEP_REF: Final = "R54-CLR-05_24_case_manifest_freeze"
P7_R54_CLR06_STEP_REF: Final = "R54-CLR-06_body_full_packet_generation_request_bodyfree_evidence"
P7_R54_CLR07_STEP_REF: Final = "R54-CLR-07_local_packet_generation_operation_receipt_intake"
P7_R54_CLR08_STEP_REF: Final = "R54-CLR-08_packet_completeness_export_denylist_scan"
P7_R54_CLR09_STEP_REF: Final = "R54-CLR-09_reviewer_selection_form_freeze"
P7_R54_CLR10_STEP_REF: Final = "R54-CLR-10_actual_human_review_local_only_operation"
P7_R54_CLR11_STEP_REF: Final = "R54-CLR-11_sanitized_review_result_row_intake"
P7_R54_CLR12_STEP_REF: Final = "R54-CLR-12_rating_row_normalization"
P7_R54_CLR13_STEP_REF: Final = "R54-CLR-13_readfeel_blocker_execution_blocker_ingestion"
P7_R54_CLR14_STEP_REF: Final = "R54-CLR-14_question_need_observation_normalization"
P7_R54_CLR15_STEP_REF: Final = "R54-CLR-15_rating_question_consistency_guard"
P7_R54_CLR16_STEP_REF: Final = "R54-CLR-16_pause_abort_expiration_protocol"
P7_R54_CLR17_STEP_REF: Final = "R54-CLR-17_purge_disposal_receipt"
P7_R54_CLR18_STEP_REF: Final = "R54-CLR-18_bodyfree_post_review_summary"
P7_R54_CLR19_STEP_REF: Final = "R54-CLR-19_p5_decision_candidate_separation"
P7_R54_CLR20_STEP_REF: Final = "R54-CLR-20_p6_candidate_only_handoff"
P7_R54_CLR21_STEP_REF: Final = "R54-CLR-21_p8_material_candidate_only_handoff"
P7_R54_CLR22_STEP_REF: Final = "R54-CLR-22_final_no_body_leak_no_question_text_no_touch_validation"
P7_R54_CLR23_STEP_REF: Final = "R54-CLR-23_r52_reintake_handoff"
P7_R54_CLR24_STEP_REF: Final = "R54-CLR-24_validation_command_matrix_documentation_output"
P7_R54_CLR02_NEXT_REQUIRED_STEP_REF: Final = P7_R54_CLR02_STEP_REF
P7_R54_CLR03_NEXT_REQUIRED_STEP_REF: Final = P7_R54_CLR03_STEP_REF
P7_R54_CLR04_NEXT_REQUIRED_STEP_REF: Final = P7_R54_CLR04_STEP_REF

P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01: Final[tuple[str, ...]] = (
    P7_R54_CLR02_STEP_REF,
    P7_R54_CLR03_STEP_REF,
    P7_R54_CLR04_STEP_REF,
    P7_R54_CLR05_STEP_REF,
    P7_R54_CLR06_STEP_REF,
    P7_R54_CLR07_STEP_REF,
    P7_R54_CLR08_STEP_REF,
    P7_R54_CLR09_STEP_REF,
    P7_R54_CLR10_STEP_REF,
    P7_R54_CLR11_STEP_REF,
    P7_R54_CLR12_STEP_REF,
    P7_R54_CLR13_STEP_REF,
    P7_R54_CLR14_STEP_REF,
    P7_R54_CLR15_STEP_REF,
    P7_R54_CLR16_STEP_REF,
    P7_R54_CLR17_STEP_REF,
    P7_R54_CLR18_STEP_REF,
    P7_R54_CLR19_STEP_REF,
    P7_R54_CLR20_STEP_REF,
    P7_R54_CLR21_STEP_REF,
    P7_R54_CLR22_STEP_REF,
    P7_R54_CLR23_STEP_REF,
    P7_R54_CLR24_STEP_REF,
)
P7_R54_CLR00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_CLR00_STEP_REF,)
P7_R54_CLR00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_CLR01_STEP_REF,
    *P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01,
)
P7_R54_CLR01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_CLR00_STEP_REF, P7_R54_CLR01_STEP_REF)
P7_R54_CLR01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01
P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR02: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[1:]
P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR03: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR01[2:]
P7_R54_CLR02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_CLR00_STEP_REF,
    P7_R54_CLR01_STEP_REF,
    P7_R54_CLR02_STEP_REF,
)
P7_R54_CLR02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR02
P7_R54_CLR03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_CLR00_STEP_REF,
    P7_R54_CLR01_STEP_REF,
    P7_R54_CLR02_STEP_REF,
    P7_R54_CLR03_STEP_REF,
)
P7_R54_CLR03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_CLR_FUTURE_STEP_REFS_AFTER_CLR03

P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF: Final = "current_received_snapshot_20260627_only"
P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = "current_received_snapshot_only"
P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(258).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(82).zip",
    "rn_zip_ref": "Cocolon(255).zip",
    "backend_zip_ref": "mashos-api(168).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_RoadmapStageDecision_R54ActualReviewRun_PreDesignMemo_20260627.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R54ActualLocalReviewOperation_CurrentSnapshotLocalRun_DetailedDesign_ImplementationOrder_20260627.md",
}
P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS: Final[tuple[str, ...]] = tuple(
    P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()
)

P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS: Final[tuple[str, ...]] = (
    "r54_op_20260625",
    "r54_ev_20260626",
    "r55_20260623",
)
P7_R54_CLR_HISTORICAL_HELPER_REF_GROUPS: Final[tuple[str, ...]] = P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS
P7_R54_CLR_HISTORICAL_HELPER_REFS: Final[dict[str, dict[str, str]]] = {
    "r54_op_20260625": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
    "r54_ev_20260626": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
    "r55_20260623": dict(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
}
P7_R54_CLR01_CURRENT_REF_COMPARISON_STATUS_REF: Final = (
    "HISTORICAL_HELPER_REFS_DIFFER_FROM_20260627_CURRENT_SNAPSHOT"
)
P7_R54_CLR01_REFREEZE_STATUS_REF: Final = "CURRENT_SNAPSHOT_20260627_BASIS_REFROZEN_FOR_R54_ACTUAL_REVIEW"
P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_STATUS_REF: Final = P7_R54_CLR01_REFREEZE_STATUS_REF

P7_R54_CLR02_HISTORICAL_RECONCILE_STATUS_REF: Final = (
    "HISTORICAL_HELPER_REFS_RECONCILED_AS_STRUCTURAL_REFS_ONLY_FOR_20260627_CURRENT_RUN"
)
P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_STATUS_REF: Final = (
    "R55_HOLD_ACTUAL_REVIEW_EVIDENCE_MISSING_INTAKEN_FOR_20260627_CURRENT_RUN"
)
P7_R54_CLR03_R52_REINTAKE_BLOCKED_STATUS_REF: Final = (
    "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
)
P7_R54_CLR03_REVIEW_OPERATION_STATE_BEFORE_RUN_REF: Final = "not_started"
P7_R54_CLR03_P5_DECISION_CANDIDATE_BEFORE_RUN_REF: Final = "P5_NOT_REVIEWED"
P7_R54_CLR03_NEXT_REQUIRED_STEP_AFTER_INTAKE_REF: Final = P7_R54_CLR04_STEP_REF
P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT: Final = r55.P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
P7_R54_CLR03_MISSING_EVIDENCE_REFS: Final[tuple[str, ...]] = r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS

P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS: Final[tuple[str, ...]] = (
    "r54_op_20260625",
    "r54_ev_20260626",
    "r55_20260623",
    "r52_20260621",
    "r53_20260621",
    "r54_bodyfree_handoff_20260622",
    "p4_r11_20260624",
)
P7_R54_CLR02_HISTORICAL_HELPER_REF_GROUPS: Final[tuple[str, ...]] = (
    P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS
)
P7_R54_CLR02_HISTORICAL_RECONCILE_REF_DETAILS: Final[dict[str, dict[str, Any]]] = {
    "r54_op_20260625": {
        "module_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625",
        "helper_role_ref": "historical_operation_reentry_structural_contract_ref",
        "operation_step_ref": r54op.P7_R54_OPERATION_REENTRY_STEP,
        "operation_scope_ref": r54op.P7_R54_OPERATION_REENTRY_SCOPE,
        "policy_kind_ref": r54op.P7_R54_OPERATION_REENTRY_POLICY_KIND,
        "received_snapshot_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "used_for_helper_regression_only": True,
        "used_for_actual_review_basis": False,
    },
    "r54_ev_20260626": {
        "module_ref": "emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626",
        "helper_role_ref": "historical_execution_evidence_materialization_structural_contract_ref",
        "operation_step_ref": r54ev.P7_R54_EV_STEP,
        "operation_scope_ref": r54ev.P7_R54_EV_SCOPE,
        "policy_kind_ref": r54ev.P7_R54_EV_POLICY_KIND,
        "received_snapshot_refs": dict(r54ev.P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "used_for_helper_regression_only": True,
        "used_for_actual_review_basis": False,
    },
    "r55_20260623": {
        "module_ref": "emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization",
        "helper_role_ref": "historical_r52_reintake_hold_decision_structural_ref",
        "operation_step_ref": r55.P7_R55_STEP,
        "operation_scope_ref": r55.P7_R55_SCOPE,
        "policy_kind_ref": r55.P7_R55_POLICY_KIND,
        "received_snapshot_refs": dict(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "used_for_helper_regression_only": True,
        "used_for_actual_review_basis": False,
    },
    "r52_20260621": {
        "module_ref": "emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate",
        "helper_role_ref": "historical_r52_decision_gate_structural_ref",
        "operation_step_ref": r52.P7_R52_STEP,
        "operation_scope_ref": r52.P7_R52_SCOPE,
        "policy_kind_ref": r52.P7_R52_POLICY_KIND,
        "received_snapshot_refs": dict(r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "used_for_helper_regression_only": True,
        "used_for_actual_review_basis": False,
    },
    "r53_20260621": {
        "module_ref": "emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization",
        "helper_role_ref": "historical_actual_local_review_execution_materialization_structural_ref",
        "operation_step_ref": r53.P7_R53_STEP,
        "operation_scope_ref": r53.P7_R53_SCOPE,
        "policy_kind_ref": r53.P7_R53_POLICY_KIND,
        "received_snapshot_refs": dict(r53.P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "used_for_helper_regression_only": True,
        "used_for_actual_review_basis": False,
    },
    "r54_bodyfree_handoff_20260622": {
        "module_ref": "emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff",
        "helper_role_ref": "historical_bodyfree_result_handoff_structural_ref",
        "operation_step_ref": r54handoff.P7_R54_STEP,
        "operation_scope_ref": r54handoff.P7_R54_SCOPE,
        "policy_kind_ref": r54handoff.P7_R54_POLICY_KIND,
        "received_snapshot_refs": dict(r54handoff.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "used_for_helper_regression_only": True,
        "used_for_actual_review_basis": False,
    },
    "p4_r11_20260624": {
        "module_ref": "emlis_ai_product_readfeel_p4_r11_summary_decision_handoff",
        "helper_role_ref": "historical_current_only_surface_audit_summary_decision_ref",
        "operation_step_ref": "P4_R11_summary_decision_handoff_20260624",
        "operation_scope_ref": "p4_r11_residual_family_current_only_surface_audit_summary_decision_handoff",
        "policy_kind_ref": "current_only_surface_audit_not_r54_actual_review_evidence",
        "summary_schema_version_ref": p4r11.PRODUCT_READFEEL_P4_R11_SUMMARY_DECISION_HANDOFF_VERSION_20260624,
        "r54_return_next_step_ref": p4r11.P4_R11_NEXT_STEP_R54_ACTUAL_LOCAL_ONLY_HUMAN_REVIEW_20260624,
        "used_for_helper_regression_only": True,
        "used_for_actual_review_basis": False,
    },
}

P7_R54_CLR_OUT_OF_SCOPE_REFS: Final[tuple[str, ...]] = (
    "p8_question_design_or_implementation",
    "p8_question_trigger_logic",
    "p8_question_text_or_draft_question_text",
    "question_text_or_draft_question_text",
    "api_route_or_request_response_key_change",
    "api_route_or_response_key_change",
    "db_schema_or_migration_change",
    "rn_ui_or_visible_contract_change",
    "emlis_runtime_surface_change",
    "user_label_connection_runtime_change",
    "body_full_packet_generation",
    "actual_human_review_execution",
    "actual_human_review_execution_or_completion_claim",
    "p5_final_confirmation",
    "p6_p8_or_release_promotion",
)

P7_R54_CLR_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "request_key_changed",
    "response_key_changed",
    "response_shape_changed",
    "db_schema_changed",
    "db_migration_changed",
    "db_migration_added",
    "db_physical_schema_changed",
    "rn_ui_changed",
    "rn_visible_contract_changed",
    "public_response_top_level_key_added",
    "public_response_key_changed",
    "runtime_gate_threshold_changed",
    "user_label_connection_runtime_changed",
    "emlis_visible_output_generation_changed",
    "subscription_or_plan_access_policy_changed",
    "question_implementation_started_here",
    "question_trigger_logic_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_answer_persistence_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "body_full_packet_generation_started_here",
    "body_full_generation_requested_here",
    "body_full_packet_generation_requested_here",
    "body_full_packet_generated_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
    "disposal_verified",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "real_device_modal_verified",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "reviewer_free_text_included",
    "reviewer_note_included",
    "reviewer_notes_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
)

P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
)
P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "operation_current_refs",
    "operation_current_ref_count",
    "operation_current_ref_keys",
    "operation_current_ref_key_count",
    "required_current_snapshot_ref_keys",
    "required_current_snapshot_ref_key_count",
    "all_required_current_refs_present",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
)
P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "public_contract",
    "r54_clr_no_touch_contract",
    "body_free_markers",
    "body_free",
)
P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "scope_boundary_confirmed",
    "no_touch_boundary_confirmed",
    "no_touch_boundary_frozen",
    *P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "operation_current_refs_are_current_snapshot_candidate",
    "current_snapshot_basis_refreeze_required_next",
    "allowed_operation_step_refs",
    "out_of_scope_refs",
    "existing_r54_op00_contract_available",
    "existing_r54_ev00_contract_available",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_actual_review_basis",
    "historical_helper_ref_groups",
    "historical_helper_refs_must_be_separated",
    "historical_helper_refs_used_as_actual_review_basis",
    "old_helper_refs_allowed_as_actual_review_basis",
    "operation_current_refs_required_before_actual_review",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *P7_R54_CLR_FALSE_FLAG_REFS,
)
P7_R54_CLR_SCOPE_NO_TOUCH_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS

P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr00_schema_version",
    "clr00_material_ref",
    "clr00_next_required_step",
    "clr00_scope_boundary_confirmed",
    "clr00_no_touch_boundary_confirmed",
    "current_snapshot_basis_refreeze_status_ref",
    "current_snapshot_basis_refrozen",
    "current_snapshot_source_mode",
    *P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "operation_current_refs_match_current_snapshot_20260627",
    "operation_current_refs_match_20260627_snapshot",
    "historical_helper_ref_groups",
    "historical_helper_ref_group_count",
    "historical_helper_refs",
    "historical_helper_refs_separated",
    "historical_helper_refs_are_historical_here",
    "historical_helper_refs_are_structural_refs_only",
    "historical_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "historical_helper_refs_can_be_used_for_actual_review_basis",
    "historical_helper_refs_used_as_actual_review_basis",
    "old_helper_refs_allowed_as_actual_review_basis",
    "old_helper_refs_match_current_snapshot_20260627",
    "r54_op_current_refs_are_historical_here",
    "r54_ev_current_refs_are_historical_here",
    "r55_current_refs_are_historical_here",
    "r54_op_refs_used_as_actual_review_basis",
    "r54_ev_refs_used_as_actual_review_basis",
    "r55_refs_used_as_actual_review_basis",
    "r54_op_current_refs_match_current_snapshot_20260627",
    "r54_ev_current_refs_match_current_snapshot_20260627",
    "r55_current_refs_match_current_snapshot_20260627",
    "r54_op_current_refs_match_20260627_snapshot",
    "r54_ev_current_refs_match_20260627_snapshot",
    "r55_current_refs_match_20260627_snapshot",
    "differing_operation_current_ref_keys_by_historical_group",
    "historical_helper_current_refs_match_20260627_snapshot",
    "historical_helper_differing_operation_current_ref_keys",
    "historical_helper_differing_operation_current_ref_key_counts",
    "differing_operation_current_ref_group_count",
    "historical_helper_ref_comparison_status_ref",
    "current_snapshot_basis_refreeze_completed_here",
    "current_refs_refreeze_does_not_rewrite_historical_helpers",
    "historical_helper_refs_reconcile_required_next",
    "current_refs_override_uses_thin_20260627_boundary_layer",
    "existing_helper_constants_not_rewritten",
    "existing_helper_constants_rewritten",
    "existing_helper_refs_preserved_as_received",
    "new_thin_boundary_helper_only",
    "new_full_operation_helper_required",
    "new_full_operation_helper_required_here",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *P7_R54_CLR_FALSE_FLAG_REFS,
)
P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_REQUIRED_FIELD_REFS
)

P7_R54_CLR02_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr01_schema_version",
    "clr01_material_ref",
    "clr01_next_required_step",
    "clr01_current_snapshot_basis_refrozen",
    "clr01_current_refs_refreeze_does_not_rewrite_historical_helpers",
    "historical_reconcile_status_ref",
    "historical_helper_ref_groups",
    "historical_helper_ref_group_count",
    "historical_ref_details",
    "historical_ref_detail_count",
    "historical_helper_refs_reconciled",
    "historical_helper_refs_reconciled_as_bodyfree_context_only",
    "historical_helper_refs_are_structural_refs_only",
    "structural_contract_reused",
    "helper_regression_context_preserved",
    "historical_refs_can_be_used_for_helper_regression_only",
    "historical_refs_can_be_used_for_actual_review_basis",
    "historical_refs_used_as_actual_review_basis",
    "older_helper_refs_mixed_into_actual_review_basis",
    "p4_r11_audit_rows_converted_to_r54_actual_review_cases",
    "p4_r11_audit_rows_mixed_into_r54_review_cases",
    "current_snapshot_basis_preserved",
    "operation_current_refs_still_actual_review_basis",
    "current_snapshot_refreeze_does_not_rewrite_historical_helpers",
    "historical_helper_current_refs_preserved",
    "existing_helper_constants_not_rewritten",
    "existing_helper_constants_rewritten",
    "r54_op_structural_ref_reconciled",
    "r54_ev_structural_ref_reconciled",
    "r55_hold_structural_ref_reconciled",
    "r52_decision_gate_structural_ref_reconciled",
    "r53_execution_materialization_structural_ref_reconciled",
    "r54_bodyfree_handoff_structural_ref_reconciled",
    "p4_r11_current_only_audit_structural_ref_reconciled",
    *P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *P7_R54_CLR_FALSE_FLAG_REFS,
)
P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_CLR_COMMON_REQUIRED_FIELD_REFS,
    "clr02_schema_version",
    "clr02_material_ref",
    "clr02_next_required_step",
    "clr02_historical_helper_refs_reconciled",
    "r55_hold_intake_status_ref",
    "r55_gap_assessment_schema_version",
    "r55_gap_assessment_material_ref",
    "r55_r52_decision_schema_version",
    "r55_r52_decision_material_ref",
    "r55_current_received_snapshot_refs",
    "r55_current_received_snapshot_ref_count",
    "r55_actual_review_basis_ref",
    "r55_actual_review_basis_allowed",
    "r55_gap_status_ref",
    "r55_p5_decision_status_ref",
    "r55_decision_ref",
    "r55_decision_status",
    "r55_next_required_step",
    "r55_handoff_status_ref",
    "r55_review_operation_state_ref",
    "r55_hold_state_preserved",
    "r55_hold_is_current_pre_run_assumption",
    "r55_hold_released_here",
    "r55_decision_reclassified_here",
    "required_case_count",
    "reviewed_case_count_before_run",
    "rating_row_count_before_run",
    "question_observation_row_count_before_run",
    "disposal_verified_before_run",
    "missing_evidence_refs",
    "missing_evidence_ref_count",
    "actual_review_evidence_missing_before_run",
    "actual_review_evidence_complete_before_run",
    "actual_human_review_run_before_clr03",
    "actual_rating_rows_materialized_before_run",
    "actual_question_need_observation_rows_materialized_before_run",
    "actual_disposal_receipt_materialized_before_run",
    "r52_reintake_blocked_by_actual_review_evidence_missing",
    "r52_reintake_handoff_status_ref",
    "p5_decision_candidate_before_run_ref",
    "p5_human_blind_qa_confirmed_final_before_run",
    "p6_hold",
    "p8_hold",
    "release_hold",
    "p6_limited_human_readfeel_start_allowed_before_run",
    "p8_start_allowed_before_run",
    "release_allowed_before_run",
    "evidence_missing_classified_as_p5_repair_required",
    "evidence_missing_classified_as_p8_material_candidate",
    "bodyfree_forbidden_payload_scan_clear",
    "blocked_by_body_free_boundary_risk",
    "blocked_by_no_touch_violation",
    *P7_R54_CLR_CURRENT_REF_REQUIRED_FIELD_REFS,
    "current_snapshot_basis_preserved",
    "historical_helper_refs_reconciled_before_hold_intake",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "human_review_completion_claim_blocked_here",
    "actual_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_CLR_NO_TOUCH_BODYFREE_REQUIRED_FIELD_REFS,
    *P7_R54_CLR_FALSE_FLAG_REFS,
)

P7_R54_CLR_FORBIDDEN_BODY_OR_QUESTION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "returned_emlis_body",
        "history_surface",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "question_text",
        "draft_question_text",
        "local_absolute_path",
        "body_hash",
        "packet_content",
        "terminal_output_body",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
    }
)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID, max_length=220)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_CLR_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    markers = body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)
    markers.update(
        {
            "raw_body_included": False,
            "returned_emlis_body_included": False,
            "history_surface_included": False,
            "reviewer_note_included": False,
            "reviewer_notes_included": False,
            "reviewer_notes_body_included": False,
            "packet_content_included": False,
            "question_text_included": False,
            "draft_question_text_included": False,
            "local_path_included": False,
            "local_absolute_path_included": False,
            "body_hash_included": False,
            "terminal_output_body_included": False,
        }
    )
    return markers


def _no_touch_contract() -> dict[str, bool]:
    return {
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "public_response_key_changed": False,
        "question_implementation_started_here": False,
        "body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "full_backend_suite_green_confirmed": False,
        "real_device_modal_verified": False,
    }


def _contains_forbidden_clr_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R54_CLR_FORBIDDEN_BODY_OR_QUESTION_KEYS:
                return True
            if _contains_forbidden_clr_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_clr_key(child) for child in value)
    return False


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {', '.join(missing[:8])}")
    extra = [field for field in data if field not in required]
    if extra:
        raise ValueError(f"{source} contains unexpected fields: {', '.join(extra[:8])}")


def _assert_bodyfree_no_touch_base(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, operation_step_ref: str, source: str
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE or data.get("current_phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_CLR_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_CLR_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_CLR_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r54_clr_no_touch_contract") or {}, source=f"{source}.r54_clr_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for key in P7_R54_CLR_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")
    if _contains_forbidden_clr_key(data):
        raise ValueError(f"{source} contains a forbidden body or question payload key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_current_refs(data: Mapping[str, Any], *, source: str, actual_basis: bool) -> None:
    refs = safe_mapping(data.get("operation_current_refs"))
    if refs != P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} operation current refs changed")
    if data.get("operation_current_ref_count") != len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} operation current ref count changed")
    if tuple(data.get("operation_current_ref_keys") or ()) != P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS:
        raise ValueError(f"{source} operation current ref keys changed")
    if data.get("operation_current_ref_key_count") != len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} operation current ref key count changed")
    if tuple(data.get("required_current_snapshot_ref_keys") or ()) != P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS:
        raise ValueError(f"{source} required current snapshot ref keys changed")
    if data.get("required_current_snapshot_ref_key_count") != len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} required current snapshot ref key count changed")
    if data.get("all_required_current_refs_present") is not True:
        raise ValueError(f"{source} must carry all required current refs")
    if data.get("actual_review_basis_ref") != P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual review basis allowed ref changed")
    if data.get("operation_current_refs_are_actual_review_basis") is not actual_basis:
        raise ValueError(f"{source} current refs actual review basis flag changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not actual_basis:
        raise ValueError(f"{source} current refs used-as-actual-review-basis flag changed")


def _historical_diff_keys_by_group() -> dict[str, list[str]]:
    return {
        group_ref: [
            key
            for key, current_value in P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS.items()
            if refs.get(key) != current_value
        ]
        for group_ref, refs in P7_R54_CLR_HISTORICAL_HELPER_REFS.items()
    }


def build_p7_r54_clr00_scope_no_touch_boundary_freeze(
    *, review_session_id: Any = P7_R54_CLR_DEFAULT_REVIEW_SESSION_ID
) -> dict[str, Any]:
    """Build R54-CLR-00 body-free scope / no-touch boundary material."""

    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR00_STEP_REF,
        "operation_step_ref": P7_R54_CLR00_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr00_scope_no_touch_boundary_20260627",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "scope_boundary_confirmed": True,
        "no_touch_boundary_confirmed": True,
        "no_touch_boundary_frozen": True,
        "operation_current_refs": dict(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "required_current_snapshot_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": False,
        "operation_current_refs_used_as_actual_review_basis": False,
        "operation_current_refs_are_current_snapshot_candidate": True,
        "current_snapshot_basis_refreeze_required_next": True,
        "allowed_operation_step_refs": [P7_R54_CLR00_STEP_REF, P7_R54_CLR01_STEP_REF],
        "out_of_scope_refs": list(P7_R54_CLR_OUT_OF_SCOPE_REFS),
        "existing_r54_op00_contract_available": hasattr(
            r54op, "assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract"
        ),
        "existing_r54_ev00_contract_available": hasattr(
            r54ev, "assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract"
        ),
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_actual_review_basis": False,
        "historical_helper_ref_groups": list(P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs_must_be_separated": True,
        "historical_helper_refs_used_as_actual_review_basis": False,
        "old_helper_refs_allowed_as_actual_review_basis": False,
        "operation_current_refs_required_before_actual_review": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_CLR00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_CLR00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_CLR01_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR00 scope/no-touch boundary",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_CLR00_STEP_REF,
        operation_step_ref=P7_R54_CLR00_STEP_REF,
        source="P7-R54-CLR00 scope/no-touch boundary",
    )
    _assert_current_refs(data, source="P7-R54-CLR00 scope/no-touch boundary", actual_basis=False)
    for key in (
        "scope_boundary_confirmed",
        "no_touch_boundary_confirmed",
        "no_touch_boundary_frozen",
        "operation_current_refs_are_current_snapshot_candidate",
        "current_snapshot_basis_refreeze_required_next",
        "existing_helper_refs_can_be_used_for_helper_regression_only",
        "historical_helper_refs_must_be_separated",
        "operation_current_refs_required_before_actual_review",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-CLR00 must keep {key}=True")
    for key in (
        "existing_helper_refs_can_be_used_for_actual_review_basis",
        "historical_helper_refs_used_as_actual_review_basis",
        "old_helper_refs_allowed_as_actual_review_basis",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-CLR00 must keep {key}=False")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError("P7-R54-CLR00 historical helper ref groups changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR00 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_CLR01_STEP_REF:
        raise ValueError("P7-R54-CLR00 next required step changed")
    return True


def build_p7_r54_clr01_current_snapshot_basis_refreeze(
    *,
    scope_no_touch_boundary_freeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-CLR-01 body-free current snapshot basis refreeze material."""

    clr00 = dict(scope_no_touch_boundary_freeze or build_p7_r54_clr00_scope_no_touch_boundary_freeze())
    assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract(clr00)
    differing = _historical_diff_keys_by_group()
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR01_STEP_REF,
        "operation_step_ref": P7_R54_CLR01_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr01_current_snapshot_basis_refreeze_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or clr00.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr00_schema_version": clr00["schema_version"],
        "clr00_material_ref": clr00["material_id"],
        "clr00_next_required_step": clr00["next_required_step"],
        "clr00_scope_boundary_confirmed": clr00["scope_boundary_confirmed"],
        "clr00_no_touch_boundary_confirmed": clr00["no_touch_boundary_confirmed"],
        "current_snapshot_basis_refreeze_status_ref": P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_STATUS_REF,
        "current_snapshot_basis_refrozen": True,
        "current_snapshot_source_mode": P7_SOURCE_MODE,
        "operation_current_refs": dict(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "required_current_snapshot_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "operation_current_refs_match_current_snapshot_20260627": True,
        "operation_current_refs_match_20260627_snapshot": True,
        "historical_helper_ref_groups": list(P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_ref_group_count": len(P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs": {key: dict(value) for key, value in P7_R54_CLR_HISTORICAL_HELPER_REFS.items()},
        "historical_helper_refs_separated": True,
        "historical_helper_refs_are_historical_here": True,
        "historical_helper_refs_are_structural_refs_only": True,
        "historical_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "historical_helper_refs_can_be_used_for_actual_review_basis": False,
        "historical_helper_refs_used_as_actual_review_basis": False,
        "old_helper_refs_allowed_as_actual_review_basis": False,
        "old_helper_refs_match_current_snapshot_20260627": False,
        "r54_op_current_refs_are_historical_here": True,
        "r54_ev_current_refs_are_historical_here": True,
        "r55_current_refs_are_historical_here": True,
        "r54_op_refs_used_as_actual_review_basis": False,
        "r54_ev_refs_used_as_actual_review_basis": False,
        "r55_refs_used_as_actual_review_basis": False,
        "r54_op_current_refs_match_current_snapshot_20260627": False,
        "r54_ev_current_refs_match_current_snapshot_20260627": False,
        "r55_current_refs_match_current_snapshot_20260627": False,
        "r54_op_current_refs_match_20260627_snapshot": False,
        "r54_ev_current_refs_match_20260627_snapshot": False,
        "r55_current_refs_match_20260627_snapshot": False,
        "differing_operation_current_ref_keys_by_historical_group": differing,
        "historical_helper_current_refs_match_20260627_snapshot": {
            group_ref: False for group_ref in P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS
        },
        "historical_helper_differing_operation_current_ref_keys": differing,
        "historical_helper_differing_operation_current_ref_key_counts": {
            group_ref: len(keys) for group_ref, keys in differing.items()
        },
        "differing_operation_current_ref_group_count": len(differing),
        "historical_helper_ref_comparison_status_ref": P7_R54_CLR01_CURRENT_REF_COMPARISON_STATUS_REF,
        "current_snapshot_basis_refreeze_completed_here": True,
        "current_refs_refreeze_does_not_rewrite_historical_helpers": True,
        "historical_helper_refs_reconcile_required_next": True,
        "current_refs_override_uses_thin_20260627_boundary_layer": True,
        "existing_helper_constants_not_rewritten": True,
        "existing_helper_constants_rewritten": False,
        "existing_helper_refs_preserved_as_received": True,
        "new_thin_boundary_helper_only": True,
        "new_full_operation_helper_required": False,
        "new_full_operation_helper_required_here": False,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_CLR01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_CLR01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_CLR02_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR01 current snapshot basis refreeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_CLR01_STEP_REF,
        operation_step_ref=P7_R54_CLR01_STEP_REF,
        source="P7-R54-CLR01 current snapshot basis refreeze",
    )
    _assert_current_refs(data, source="P7-R54-CLR01 current snapshot basis refreeze", actual_basis=True)
    if data.get("clr00_schema_version") != P7_R54_CLR_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR01 CLR00 schema version changed")
    if data.get("clr00_next_required_step") != P7_R54_CLR01_STEP_REF:
        raise ValueError("P7-R54-CLR01 must follow CLR00")
    for key in (
        "clr00_scope_boundary_confirmed",
        "clr00_no_touch_boundary_confirmed",
        "current_snapshot_basis_refrozen",
        "operation_current_refs_match_current_snapshot_20260627",
        "operation_current_refs_match_20260627_snapshot",
        "historical_helper_refs_separated",
        "historical_helper_refs_are_historical_here",
        "historical_helper_refs_are_structural_refs_only",
        "historical_helper_refs_can_be_used_for_helper_regression_only",
        "existing_helper_refs_can_be_used_for_helper_regression_only",
        "r54_op_current_refs_are_historical_here",
        "r54_ev_current_refs_are_historical_here",
        "r55_current_refs_are_historical_here",
        "current_snapshot_basis_refreeze_completed_here",
        "current_refs_refreeze_does_not_rewrite_historical_helpers",
        "historical_helper_refs_reconcile_required_next",
        "current_refs_override_uses_thin_20260627_boundary_layer",
        "existing_helper_constants_not_rewritten",
        "existing_helper_refs_preserved_as_received",
        "new_thin_boundary_helper_only",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-CLR01 must keep {key}=True")
    for key in (
        "historical_helper_refs_can_be_used_for_actual_review_basis",
        "historical_helper_refs_used_as_actual_review_basis",
        "old_helper_refs_allowed_as_actual_review_basis",
        "old_helper_refs_match_current_snapshot_20260627",
        "r54_op_refs_used_as_actual_review_basis",
        "r54_ev_refs_used_as_actual_review_basis",
        "r55_refs_used_as_actual_review_basis",
        "r54_op_current_refs_match_current_snapshot_20260627",
        "r54_ev_current_refs_match_current_snapshot_20260627",
        "r55_current_refs_match_current_snapshot_20260627",
        "r54_op_current_refs_match_20260627_snapshot",
        "r54_ev_current_refs_match_20260627_snapshot",
        "r55_current_refs_match_20260627_snapshot",
        "existing_helper_constants_rewritten",
        "new_full_operation_helper_required",
        "new_full_operation_helper_required_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-CLR01 must keep {key}=False")
    if data.get("current_snapshot_source_mode") != P7_SOURCE_MODE:
        raise ValueError("P7-R54-CLR01 current snapshot source mode changed")
    if data.get("current_snapshot_basis_refreeze_status_ref") != P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_STATUS_REF:
        raise ValueError("P7-R54-CLR01 refreeze status changed")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError("P7-R54-CLR01 historical helper groups changed")
    if data.get("historical_helper_ref_group_count") != len(P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-CLR01 historical helper group count changed")
    if safe_mapping(data.get("historical_helper_refs")) != P7_R54_CLR_HISTORICAL_HELPER_REFS:
        raise ValueError("P7-R54-CLR01 historical helper refs changed")
    differing = safe_mapping(data.get("differing_operation_current_ref_keys_by_historical_group"))
    if set(differing) != set(P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-CLR01 differing historical ref groups changed")
    for group_ref in P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS:
        if not differing.get(group_ref):
            raise ValueError(f"P7-R54-CLR01 must show historical refs differ for {group_ref}")
    if data.get("differing_operation_current_ref_group_count") != len(P7_R54_CLR_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError("P7-R54-CLR01 differing historical ref group count changed")
    if data.get("historical_helper_ref_comparison_status_ref") != P7_R54_CLR01_CURRENT_REF_COMPARISON_STATUS_REF:
        raise ValueError("P7-R54-CLR01 historical helper comparison status changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR01_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR01 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_CLR02_STEP_REF:
        raise ValueError("P7-R54-CLR01 next required step changed")
    return True



def build_p7_r54_clr02_historical_helper_refs_reconcile(
    *,
    current_snapshot_basis_refreeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-CLR-02 body-free historical helper refs reconcile material."""

    clr01 = dict(current_snapshot_basis_refreeze or build_p7_r54_clr01_current_snapshot_basis_refreeze())
    assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract(clr01)
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR02_STEP_REF,
        "operation_step_ref": P7_R54_CLR02_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr02_historical_helper_refs_reconcile_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or clr01.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr01_schema_version": clr01["schema_version"],
        "clr01_material_ref": clr01["material_id"],
        "clr01_next_required_step": clr01["next_required_step"],
        "clr01_current_snapshot_basis_refrozen": clr01["current_snapshot_basis_refrozen"],
        "clr01_current_refs_refreeze_does_not_rewrite_historical_helpers": clr01[
            "current_refs_refreeze_does_not_rewrite_historical_helpers"
        ],
        "historical_reconcile_status_ref": P7_R54_CLR02_HISTORICAL_RECONCILE_STATUS_REF,
        "historical_helper_ref_groups": list(P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS),
        "historical_helper_ref_group_count": len(P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS),
        "historical_ref_details": {
            key: dict(value) for key, value in P7_R54_CLR02_HISTORICAL_RECONCILE_REF_DETAILS.items()
        },
        "historical_ref_detail_count": len(P7_R54_CLR02_HISTORICAL_RECONCILE_REF_DETAILS),
        "historical_helper_refs_reconciled": True,
        "historical_helper_refs_reconciled_as_bodyfree_context_only": True,
        "historical_helper_refs_are_structural_refs_only": True,
        "structural_contract_reused": True,
        "helper_regression_context_preserved": True,
        "historical_refs_can_be_used_for_helper_regression_only": True,
        "historical_refs_can_be_used_for_actual_review_basis": False,
        "historical_refs_used_as_actual_review_basis": False,
        "older_helper_refs_mixed_into_actual_review_basis": False,
        "p4_r11_audit_rows_converted_to_r54_actual_review_cases": False,
        "p4_r11_audit_rows_mixed_into_r54_review_cases": False,
        "current_snapshot_basis_preserved": True,
        "operation_current_refs_still_actual_review_basis": True,
        "current_snapshot_refreeze_does_not_rewrite_historical_helpers": True,
        "historical_helper_current_refs_preserved": True,
        "existing_helper_constants_not_rewritten": True,
        "existing_helper_constants_rewritten": False,
        "r54_op_structural_ref_reconciled": True,
        "r54_ev_structural_ref_reconciled": True,
        "r55_hold_structural_ref_reconciled": True,
        "r52_decision_gate_structural_ref_reconciled": True,
        "r53_execution_materialization_structural_ref_reconciled": True,
        "r54_bodyfree_handoff_structural_ref_reconciled": True,
        "p4_r11_current_only_audit_structural_ref_reconciled": True,
        "operation_current_refs": dict(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "required_current_snapshot_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_CLR02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_CLR02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_CLR03_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr02_historical_helper_refs_reconcile_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_CLR02_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR02 historical helper refs reconcile",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION,
        policy_section=P7_R54_CLR02_STEP_REF,
        operation_step_ref=P7_R54_CLR02_STEP_REF,
        source="P7-R54-CLR02 historical helper refs reconcile",
    )
    _assert_current_refs(data, source="P7-R54-CLR02 historical helper refs reconcile", actual_basis=True)
    if data.get("clr01_schema_version") != P7_R54_CLR_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR02 CLR01 schema version changed")
    if data.get("clr01_next_required_step") != P7_R54_CLR02_STEP_REF:
        raise ValueError("P7-R54-CLR02 must follow CLR01")
    if data.get("historical_reconcile_status_ref") != P7_R54_CLR02_HISTORICAL_RECONCILE_STATUS_REF:
        raise ValueError("P7-R54-CLR02 historical reconcile status changed")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS:
        raise ValueError("P7-R54-CLR02 historical helper groups changed")
    if data.get("historical_helper_ref_group_count") != len(P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS):
        raise ValueError("P7-R54-CLR02 historical helper group count changed")
    if safe_mapping(data.get("historical_ref_details")) != P7_R54_CLR02_HISTORICAL_RECONCILE_REF_DETAILS:
        raise ValueError("P7-R54-CLR02 historical ref details changed")
    if data.get("historical_ref_detail_count") != len(P7_R54_CLR02_HISTORICAL_RECONCILE_REF_DETAILS):
        raise ValueError("P7-R54-CLR02 historical ref detail count changed")
    for group_ref in P7_R54_CLR02_HISTORICAL_RECONCILE_REF_GROUP_REFS:
        details = safe_mapping(data.get("historical_ref_details")).get(group_ref) or {}
        if details.get("used_for_helper_regression_only") is not True:
            raise ValueError(f"P7-R54-CLR02 must keep {group_ref} helper regression only")
        if details.get("used_for_actual_review_basis") is not False:
            raise ValueError(f"P7-R54-CLR02 must not use {group_ref} as actual review basis")
    for key in (
        "clr01_current_snapshot_basis_refrozen",
        "clr01_current_refs_refreeze_does_not_rewrite_historical_helpers",
        "historical_helper_refs_reconciled",
        "historical_helper_refs_reconciled_as_bodyfree_context_only",
        "historical_helper_refs_are_structural_refs_only",
        "structural_contract_reused",
        "helper_regression_context_preserved",
        "historical_refs_can_be_used_for_helper_regression_only",
        "current_snapshot_basis_preserved",
        "operation_current_refs_still_actual_review_basis",
        "current_snapshot_refreeze_does_not_rewrite_historical_helpers",
        "historical_helper_current_refs_preserved",
        "existing_helper_constants_not_rewritten",
        "r54_op_structural_ref_reconciled",
        "r54_ev_structural_ref_reconciled",
        "r55_hold_structural_ref_reconciled",
        "r52_decision_gate_structural_ref_reconciled",
        "r53_execution_materialization_structural_ref_reconciled",
        "r54_bodyfree_handoff_structural_ref_reconciled",
        "p4_r11_current_only_audit_structural_ref_reconciled",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-CLR02 must keep {key}=True")
    for key in (
        "historical_refs_can_be_used_for_actual_review_basis",
        "historical_refs_used_as_actual_review_basis",
        "older_helper_refs_mixed_into_actual_review_basis",
        "p4_r11_audit_rows_converted_to_r54_actual_review_cases",
        "p4_r11_audit_rows_mixed_into_r54_review_cases",
        "existing_helper_constants_rewritten",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-CLR02 must keep {key}=False")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR02_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR02 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_CLR03_STEP_REF:
        raise ValueError("P7-R54-CLR02 next required step changed")
    return True


def build_p7_r54_clr03_r55_hold_evidence_missing_intake(
    *,
    historical_helper_refs_reconcile: Mapping[str, Any] | None = None,
    r55_gap_assessment: Mapping[str, Any] | None = None,
    r55_r52_reintake_decision: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build R54-CLR-03 body-free R55 hold / evidence missing intake material."""

    clr02 = dict(historical_helper_refs_reconcile or build_p7_r54_clr02_historical_helper_refs_reconcile())
    assert_p7_r54_clr02_historical_helper_refs_reconcile_contract(clr02)
    gap = safe_mapping(r55_gap_assessment) if r55_gap_assessment is not None else r55.build_p7_r55_actual_review_evidence_gap_assessment_bodyfree()
    r55.assert_p7_r55_actual_review_evidence_gap_assessment_bodyfree_contract(gap)
    decision = (
        safe_mapping(r55_r52_reintake_decision)
        if r55_r52_reintake_decision is not None
        else r55.build_p7_r55_r52_reintake_decision_materialization_bodyfree(actual_review_evidence_gap_assessment=gap)
    )
    r55.assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(decision)
    material: dict[str, Any] = {
        "schema_version": P7_R54_CLR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_CLR_STEP,
        "scope": P7_R54_CLR_SCOPE,
        "policy_kind": P7_R54_CLR_POLICY_KIND,
        "policy_section": P7_R54_CLR03_STEP_REF,
        "operation_step_ref": P7_R54_CLR03_STEP_REF,
        "current_phase": P7_PHASE,
        "material_id": "p7_r54_clr03_r55_hold_evidence_missing_intake_20260627",
        "review_session_id": _safe_review_session_id(review_session_id or clr02.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "clr02_schema_version": clr02["schema_version"],
        "clr02_material_ref": clr02["material_id"],
        "clr02_next_required_step": clr02["next_required_step"],
        "clr02_historical_helper_refs_reconciled": clr02["historical_helper_refs_reconciled"],
        "r55_hold_intake_status_ref": P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_STATUS_REF,
        "r55_gap_assessment_schema_version": gap["schema_version"],
        "r55_gap_assessment_material_ref": gap["material_id"],
        "r55_r52_decision_schema_version": decision["schema_version"],
        "r55_r52_decision_material_ref": decision["material_id"],
        "r55_current_received_snapshot_refs": dict(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r55_current_received_snapshot_ref_count": len(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r55_actual_review_basis_ref": r55.P7_R55_ACTUAL_REVIEW_BASIS_REF,
        "r55_actual_review_basis_allowed": r55.P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "r55_gap_status_ref": gap["gap_status_ref"],
        "r55_p5_decision_status_ref": gap["p5_decision_status_ref"],
        "r55_decision_ref": decision["r55_decision_ref"],
        "r55_decision_status": decision["decision_status"],
        "r55_next_required_step": decision["next_required_step"],
        "r55_handoff_status_ref": gap["r54_handoff_status"],
        "r55_review_operation_state_ref": gap["r54_review_operation_state_ref"],
        "r55_hold_state_preserved": True,
        "r55_hold_is_current_pre_run_assumption": True,
        "r55_hold_released_here": False,
        "r55_decision_reclassified_here": False,
        "required_case_count": P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count_before_run": 0,
        "rating_row_count_before_run": 0,
        "question_observation_row_count_before_run": 0,
        "disposal_verified_before_run": False,
        "missing_evidence_refs": list(P7_R54_CLR03_MISSING_EVIDENCE_REFS),
        "missing_evidence_ref_count": len(P7_R54_CLR03_MISSING_EVIDENCE_REFS),
        "actual_review_evidence_missing_before_run": True,
        "actual_review_evidence_complete_before_run": False,
        "actual_human_review_run_before_clr03": False,
        "actual_rating_rows_materialized_before_run": False,
        "actual_question_need_observation_rows_materialized_before_run": False,
        "actual_disposal_receipt_materialized_before_run": False,
        "r52_reintake_blocked_by_actual_review_evidence_missing": True,
        "r52_reintake_handoff_status_ref": P7_R54_CLR03_R52_REINTAKE_BLOCKED_STATUS_REF,
        "p5_decision_candidate_before_run_ref": P7_R54_CLR03_P5_DECISION_CANDIDATE_BEFORE_RUN_REF,
        "p5_human_blind_qa_confirmed_final_before_run": False,
        "p6_hold": True,
        "p8_hold": True,
        "release_hold": True,
        "p6_limited_human_readfeel_start_allowed_before_run": False,
        "p8_start_allowed_before_run": False,
        "release_allowed_before_run": False,
        "evidence_missing_classified_as_p5_repair_required": False,
        "evidence_missing_classified_as_p8_material_candidate": False,
        "bodyfree_forbidden_payload_scan_clear": True,
        "blocked_by_body_free_boundary_risk": False,
        "blocked_by_no_touch_violation": False,
        "operation_current_refs": dict(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "operation_current_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "required_current_snapshot_ref_keys": list(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_snapshot_ref_key_count": len(P7_R54_CLR_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "all_required_current_refs_present": True,
        "actual_review_basis_ref": P7_R54_CLR_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_CLR_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "current_snapshot_basis_preserved": True,
        "historical_helper_refs_reconciled_before_hold_intake": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "human_review_completion_claim_blocked_here": True,
        "actual_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_CLR03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_CLR03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_CLR04_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_clr_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_REQUIRED_FIELD_REFS,
        source="P7-R54-CLR03 R55 hold evidence missing intake",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_CLR_R55_HOLD_EVIDENCE_MISSING_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_CLR03_STEP_REF,
        operation_step_ref=P7_R54_CLR03_STEP_REF,
        source="P7-R54-CLR03 R55 hold evidence missing intake",
    )
    _assert_current_refs(data, source="P7-R54-CLR03 R55 hold evidence missing intake", actual_basis=True)
    if data.get("clr02_schema_version") != P7_R54_CLR_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-R54-CLR03 CLR02 schema version changed")
    if data.get("clr02_next_required_step") != P7_R54_CLR03_STEP_REF:
        raise ValueError("P7-R54-CLR03 must follow CLR02")
    if data.get("r55_hold_intake_status_ref") != P7_R54_CLR03_R55_HOLD_EVIDENCE_MISSING_INTAKE_STATUS_REF:
        raise ValueError("P7-R54-CLR03 R55 hold intake status changed")
    if safe_mapping(data.get("r55_current_received_snapshot_refs")) != r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("P7-R54-CLR03 R55 historical snapshot refs changed")
    if data.get("r55_current_received_snapshot_ref_count") != len(r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError("P7-R54-CLR03 R55 snapshot ref count changed")
    if data.get("r55_actual_review_basis_ref") != r55.P7_R55_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-CLR03 R55 basis ref changed")
    if data.get("r55_actual_review_basis_allowed") != r55.P7_R55_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError("P7-R54-CLR03 R55 basis allowed ref changed")
    if data.get("r55_gap_status_ref") != r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF:
        raise ValueError("P7-R54-CLR03 must keep R55 actual review evidence missing")
    if data.get("r55_p5_decision_status_ref") != r55.P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF:
        raise ValueError("P7-R54-CLR03 R55 P5 decision status changed")
    if data.get("r55_decision_ref") != r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("P7-R54-CLR03 R55 decision ref changed")
    if data.get("r55_decision_status") != r55.P7_R55_DEFAULT_DECISION_STATUS_REF:
        raise ValueError("P7-R54-CLR03 R55 decision status changed")
    if data.get("r55_next_required_step") != r55.P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-CLR03 R55 next required step changed")
    if data.get("r55_handoff_status_ref") != r55.P7_R55_R54_DEFAULT_HANDOFF_EXPECTED_STATUS_REF:
        raise ValueError("P7-R54-CLR03 R55 handoff status changed")
    if data.get("r55_review_operation_state_ref") != r55.P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF:
        raise ValueError("P7-R54-CLR03 R55 review operation state changed")
    if data.get("required_case_count") != P7_R54_CLR_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-CLR03 required case count changed")
    if data.get("reviewed_case_count_before_run") != 0:
        raise ValueError("P7-R54-CLR03 reviewed case count before run must remain 0")
    if data.get("rating_row_count_before_run") != 0 or data.get("question_observation_row_count_before_run") != 0:
        raise ValueError("P7-R54-CLR03 must not materialize rating/question rows before run")
    if tuple(data.get("missing_evidence_refs") or ()) != P7_R54_CLR03_MISSING_EVIDENCE_REFS:
        raise ValueError("P7-R54-CLR03 missing evidence refs changed")
    if data.get("missing_evidence_ref_count") != len(P7_R54_CLR03_MISSING_EVIDENCE_REFS):
        raise ValueError("P7-R54-CLR03 missing evidence ref count changed")
    for key in (
        "clr02_historical_helper_refs_reconciled",
        "r55_hold_state_preserved",
        "r55_hold_is_current_pre_run_assumption",
        "actual_review_evidence_missing_before_run",
        "r52_reintake_blocked_by_actual_review_evidence_missing",
        "p6_hold",
        "p8_hold",
        "release_hold",
        "bodyfree_forbidden_payload_scan_clear",
        "current_snapshot_basis_preserved",
        "historical_helper_refs_reconciled_before_hold_intake",
        "body_full_generation_blocked_until_later_preflight",
        "body_full_generation_blocked_until_preflight",
        "human_review_completion_claim_blocked_here",
        "actual_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-CLR03 must keep {key}=True")
    for key in (
        "r55_hold_released_here",
        "r55_decision_reclassified_here",
        "disposal_verified_before_run",
        "actual_review_evidence_complete_before_run",
        "actual_human_review_run_before_clr03",
        "actual_rating_rows_materialized_before_run",
        "actual_question_need_observation_rows_materialized_before_run",
        "actual_disposal_receipt_materialized_before_run",
        "p5_human_blind_qa_confirmed_final_before_run",
        "p6_limited_human_readfeel_start_allowed_before_run",
        "p8_start_allowed_before_run",
        "release_allowed_before_run",
        "evidence_missing_classified_as_p5_repair_required",
        "evidence_missing_classified_as_p8_material_candidate",
        "blocked_by_body_free_boundary_risk",
        "blocked_by_no_touch_violation",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-CLR03 must keep {key}=False")
    if data.get("r52_reintake_handoff_status_ref") != P7_R54_CLR03_R52_REINTAKE_BLOCKED_STATUS_REF:
        raise ValueError("P7-R54-CLR03 R52 handoff status must remain blocked by evidence missing")
    if data.get("p5_decision_candidate_before_run_ref") != P7_R54_CLR03_P5_DECISION_CANDIDATE_BEFORE_RUN_REF:
        raise ValueError("P7-R54-CLR03 P5 candidate before run changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_CLR03_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_CLR03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-CLR03 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_CLR04_STEP_REF:
        raise ValueError("P7-R54-CLR03 next required step changed")
    return True


build_p7_r54_current_snapshot_local_run_clr00_scope_no_touch_boundary_freeze = (
    build_p7_r54_clr00_scope_no_touch_boundary_freeze
)
assert_p7_r54_current_snapshot_local_run_clr00_scope_no_touch_boundary_freeze_contract = (
    assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract
)
build_p7_r54_current_snapshot_local_run_clr01_current_snapshot_basis_refreeze = (
    build_p7_r54_clr01_current_snapshot_basis_refreeze
)
assert_p7_r54_current_snapshot_local_run_clr01_current_snapshot_basis_refreeze_contract = (
    assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract
)
build_p7_r54_current_snapshot_scope_no_touch_boundary_freeze_bodyfree = (
    build_p7_r54_clr00_scope_no_touch_boundary_freeze
)
assert_p7_r54_current_snapshot_scope_no_touch_boundary_freeze_bodyfree_contract = (
    assert_p7_r54_clr00_scope_no_touch_boundary_freeze_contract
)
build_p7_r54_current_snapshot_basis_refreeze_bodyfree = build_p7_r54_clr01_current_snapshot_basis_refreeze
assert_p7_r54_current_snapshot_basis_refreeze_bodyfree_contract = (
    assert_p7_r54_clr01_current_snapshot_basis_refreeze_contract
)
build_p7_r54_current_snapshot_local_run_clr02_historical_helper_refs_reconcile = (
    build_p7_r54_clr02_historical_helper_refs_reconcile
)
assert_p7_r54_current_snapshot_local_run_clr02_historical_helper_refs_reconcile_contract = (
    assert_p7_r54_clr02_historical_helper_refs_reconcile_contract
)
build_p7_r54_current_snapshot_historical_helper_refs_reconcile_bodyfree = (
    build_p7_r54_clr02_historical_helper_refs_reconcile
)
assert_p7_r54_current_snapshot_historical_helper_refs_reconcile_bodyfree_contract = (
    assert_p7_r54_clr02_historical_helper_refs_reconcile_contract
)
build_p7_r54_current_snapshot_local_run_clr03_r55_hold_evidence_missing_intake = (
    build_p7_r54_clr03_r55_hold_evidence_missing_intake
)
assert_p7_r54_current_snapshot_local_run_clr03_r55_hold_evidence_missing_intake_contract = (
    assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract
)
build_p7_r54_current_snapshot_r55_hold_evidence_missing_intake_bodyfree = (
    build_p7_r54_clr03_r55_hold_evidence_missing_intake
)
assert_p7_r54_current_snapshot_r55_hold_evidence_missing_intake_bodyfree_contract = (
    assert_p7_r54_clr03_r55_hold_evidence_missing_intake_contract
)
