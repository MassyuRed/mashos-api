# -*- coding: utf-8 -*-
"""P7-R54 actual review execution evidence materialization EV00-EV22 helpers.

R54-EV-00 freezes the scope / no-touch boundary for the actual local-only human
review execution evidence work.
R54-EV-01 inspects the existing 2026-06-25 R54-OP helper capability and records
whether it can be reused as-is for the 2026-06-26 actual review basis.
R54-EV-02 refreezes the 2026-06-26 operation-current refs as the only actual
review basis without rewriting the existing 2026-06-25 helper module.
R54-EV-03 re-intakes the R55 hold decision against that 2026-06-26 basis.
R54-EV-04 confirms the local-only preflight implementation boundary against the
2026-06-26 basis.
R54-EV-05 refreezes the body-free 24-case manifest after a ready preflight without
materializing local body-full packets.
R54-EV-06 materializes only the body-free request refs for later local-only
body-full packet generation.
R54-EV-07 freezes the local operation boundary instruction without generating
packets, running review, or storing local paths.
R54-EV-08 freezes the reviewer selection-only form.
R54-EV-09 intakes sanitized body-free review result rows when external local
selection rows are supplied, without normalizing rating rows or completing review.
R54-EV-10 normalizes those sanitized rows into body-free rating rows.
R54-EV-11 ingests readfeel and execution blockers separately from those rating rows.
R54-EV-12 normalizes body-free question-need observation rows from the same
sanitary reviewer selection rows, without creating question text or P8 logic.
R54-EV-13 guards rating/question consistency so P5 repair signals are not
promoted into P8 material candidates.
R54-EV-14 freezes the body-free pause / abort / expiration protocol before
any disposal handoff.
R54-EV-15 materializes only a body-free purge / disposal receipt from externally
verified local deletion refs; it does not delete local files itself.
R54-EV-16 summarizes rating / blocker / question / disposal evidence as body-free counts.
R54-EV-17 separates P5 decision candidates without finalizing P5, starting P6/P8,
or allowing release.
R54-EV-18 materializes only a P6 limited human readfeel candidate handoff; it
keeps P6 start blocked.
R54-EV-19 materializes only a P8 question-design material candidate handoff; it
keeps P8 start, question text, and implementation blocked.
R54-EV-20 performs final no-body-leak / no-question-text / no-touch validation.
R54-EV-21 materializes the R52 re-intake handoff as body-free evidence.
R54-EV-22 materializes the validation command matrix / documentation output
without converting collect-only, RN contract, or helper green into broader claims.

It does not generate body-full packets, run actual human review, perform local
file deletion itself, implement P8 questions, change API/DB/RN/runtime/public
response contracts, start P6/P8, complete P7, or allow release.
"""

from __future__ import annotations

import inspect
from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    body_free_flags,
    clean_identifier,
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
from emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization import (
    P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF,
    P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R55_DEFAULT_DECISION_STATUS_REF,
    P7_R55_DEFAULT_MISSING_EVIDENCE_REFS,
    P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF,
    P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF,
    P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
    P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
    P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF,
    P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
    P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF,
    P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract,
    build_p7_r55_r52_reintake_decision_materialization_bodyfree,
)


P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev00_scope_no_touch_boundary_confirmation.bodyfree.v1"
)
P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev01_existing_helper_capability_inspection.bodyfree.v1"
)
P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev02_operation_current_refs_20260626_refreeze.bodyfree.v1"
)
P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev03_r55_hold_intake_refreeze.bodyfree.v1"
)
P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev04_local_only_preflight_implementation_confirmation.bodyfree.v1"
)
P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev05_24_case_manifest_refreeze.bodyfree.v1"
)

P7_R54_EV_STEP: Final = "R54_actual_review_execution_evidence_materialization_20260626"
P7_R54_EV_SCOPE: Final = "p7_r54_actual_local_review_execution_evidence_materialization"
P7_R54_EV_POLICY_KIND: Final = "r54_actual_review_execution_evidence_bodyfree_boundary"
P7_R54_EV_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r54_actual_review_execution_evidence_materialization_20260626"

P7_R54_EV00_STEP_REF: Final = "R54-EV-00_scope_no_touch_boundary_confirmation"
P7_R54_EV01_STEP_REF: Final = "R54-EV-01_existing_helper_capability_inspection"
P7_R54_EV02_STEP_REF: Final = "R54-EV-02_operation_current_refs_20260626_refreeze"
P7_R54_EV03_STEP_REF: Final = "R54-EV-03_r55_hold_intake_refreeze"
P7_R54_EV04_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-04_local_only_preflight_implementation_confirmation"
P7_R54_EV04_STEP_REF: Final = P7_R54_EV04_NEXT_REQUIRED_STEP_REF
P7_R54_EV05_STEP_REF: Final = "R54-EV-05_24_case_manifest_refreeze"
P7_R54_EV06_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-06_body_full_packet_generation_request_bodyfree_boundary"
P7_R54_EV02_NEXT_REQUIRED_STEP_REF: Final = P7_R54_EV02_STEP_REF
P7_R54_EV03_NEXT_REQUIRED_STEP_REF: Final = P7_R54_EV03_STEP_REF

P7_R54_EV_ACTUAL_REVIEW_BASIS_REF: Final = "operation_current_refs_20260626_only"
P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = "current_20260626_ref_only"

P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(256).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(81).zip",
    "rn_zip_ref": "Cocolon(254).zip",
    "backend_zip_ref": "mashos-api(167).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_RoadmapStageDecision_PreDesignMemo_20260626.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R54ActualLocalReviewOperation_ExecutionEvidenceMaterialization_DetailedDesign_ImplementationOrder_20260626.md",
}

P7_R54_EV00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV00_STEP_REF,)
P7_R54_EV00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_EV01_STEP_REF,
    P7_R54_EV02_NEXT_REQUIRED_STEP_REF,
)
P7_R54_EV01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_EV00_STEP_REF,
    P7_R54_EV01_STEP_REF,
)
P7_R54_EV01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV02_NEXT_REQUIRED_STEP_REF,)
P7_R54_EV02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_EV00_STEP_REF,
    P7_R54_EV01_STEP_REF,
    P7_R54_EV02_STEP_REF,
)
P7_R54_EV02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV03_STEP_REF,)
P7_R54_EV03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_EV00_STEP_REF,
    P7_R54_EV01_STEP_REF,
    P7_R54_EV02_STEP_REF,
    P7_R54_EV03_STEP_REF,
)
P7_R54_EV03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV04_NEXT_REQUIRED_STEP_REF,)
P7_R54_EV04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_EV03_IMPLEMENTED_STEPS,
    P7_R54_EV04_STEP_REF,
)
P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV05_STEP_REF,)
P7_R54_EV05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_EV04_IMPLEMENTED_STEPS,
    P7_R54_EV05_STEP_REF,
)
P7_R54_EV05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV06_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS: Final[tuple[str, ...]] = (
    "build_p7_r54_op01_operation_current_snapshot_refs_refreeze",
    "build_p7_r54_op04_local_only_preflight",
    "build_p7_r54_op05_24_case_manifest_freeze",
    "build_p7_r54_op06_local_only_body_full_packet_generation_request",
    "build_p7_r54_op10_actual_human_review_operation_state_capture",
    "build_p7_r54_op11_sanitized_review_result_capture",
    "build_p7_r54_op12_rating_row_normalization",
    "build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion",
    "build_p7_r54_op14_question_need_observation_normalization",
    "build_p7_r54_op15_rating_question_consistency_guard",
    "build_p7_r54_op17_purge_disposal_receipt",
    "build_p7_r54_op18_bodyfree_post_review_summary",
    "build_p7_r54_op19_p5_decision_candidate_separation",
    "build_p7_r54_op21_p8_material_candidate_handoff",
    "build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation",
    "build_p7_r54_op23_r52_reintake_handoff",
)
P7_R54_EV_SELECTION_ROW_INTAKE_HELPER_REFS: Final[tuple[str, ...]] = (
    "build_p7_r54_op10_actual_human_review_operation_state_capture",
    "build_p7_r54_op11_sanitized_review_result_capture",
)

P7_R54_EV01_CURRENT_REF_OVERRIDE_REJECTION_REF: Final = (
    "existing_op01_override_rejected_by_20260625_operation_current_refs_contract"
)
P7_R54_EV01_HELPER_CAPABILITY_STATUS_REF: Final = "R54_EV01_EXISTING_HELPER_CAPABILITY_INSPECTED"
P7_R54_EV01_HELPER_REUSE_VERDICT_THIN_LAYER_REQUIRED_REF: Final = (
    "R54_EV01_REUSE_EXISTING_HELPER_WITH_THIN_20260626_BOUNDARY_LAYER"
)
P7_R54_EV01_OVERRIDE_REJECTED_REASON_REF: Final = P7_R54_EV01_CURRENT_REF_OVERRIDE_REJECTION_REF
P7_R54_EV01_DOWNSTREAM_CONSTANT_REASON_REF: Final = "existing_downstream_builders_embed_module_current_refs_constant"
P7_R54_EV01_DECISION_THIN_WRAPPER_REQUIRED_REF: Final = "R54_EV01_THIN_WRAPPER_REQUIRED_FOR_20260626_CURRENT_REFS"

P7_R54_EV_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_changed",
    "db_changed",
    "rn_changed",
    "runtime_changed",
    "api_route_changed",
    "db_schema_changed",
    "db_migration_changed",
    "rn_visible_contract_changed",
    "public_response_top_level_key_added",
    "public_response_key_changed",
    "question_implementation_started_here",
    "question_trigger_logic_implemented",
    "p8_question_implementation_spec_finalized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
)

P7_R54_EV_NO_TOUCH_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_EV_FALSE_FLAG_REFS

P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "scope_boundary_confirmed",
    "no_touch_boundary_confirmed",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "allowed_operation_step_refs",
    "out_of_scope_refs",
    "existing_op00_schema_version",
    "existing_op00_material_ref",
    "existing_op00_contract_available",
    "existing_op00_no_touch_boundary_frozen",
    "existing_helper_refs_can_be_used_for_actual_review_basis",
    "operation_current_refs_required_before_actual_review",
    "historical_helper_refs_must_be_separated",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "body_full_generation_requested_here",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "no_touch_boundary_frozen",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev00_schema_version",
    "ev00_material_ref",
    "ev00_next_required_step",
    "inspection_status_ref",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "existing_helper_module_ref",
    "existing_helper_module_imported",
    "existing_op00_scope_no_touch_available",
    "existing_op01_current_refs_refreeze_available",
    "existing_helper_schema_step_ref",
    "existing_helper_current_refs",
    "existing_helper_current_ref_count",
    "expected_20260626_operation_current_refs",
    "expected_20260626_operation_current_ref_count",
    "existing_helper_operation_current_refs",
    "existing_helper_operation_current_ref_count",
    "operation_current_ref_keys",
    "operation_current_ref_key_count",
    "operation_current_ref_keys_match",
    "operation_current_ref_values_match",
    "differing_operation_current_ref_keys",
    "differing_operation_current_ref_key_count",
    "downstream_current_refs_constant_function_refs",
    "downstream_current_refs_constant_function_count",
    "existing_helper_current_refs_match_20260626_snapshot",
    "existing_helper_current_refs_are_historical_here",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_actual_review_basis",
    "required_helper_function_refs",
    "required_helper_function_count",
    "found_helper_function_refs",
    "found_helper_function_count",
    "missing_helper_function_refs",
    "missing_helper_function_count",
    "required_helper_functions_all_present",
    "helper_function_capability_rows",
    "helper_function_capability_row_count",
    "selection_row_intake_helper_count",
    "selection_row_intake_helpers_present",
    "op01_signature_accepts_operation_current_refs",
    "op01_override_20260626_contract_accepted",
    "op01_override_failure_reason_refs",
    "helper_op01_accepts_operation_current_refs_parameter",
    "helper_op01_override_build_attempted_bodyfree",
    "helper_op01_override_build_accepted",
    "helper_op01_override_rejected",
    "helper_op01_override_rejection_ref",
    "current_refs_override_possible_with_existing_helper_only",
    "bodyfree_handoff_possible_with_existing_helper_functions",
    "actual_selection_rows_intake_possible_with_existing_helper_functions",
    "existing_helper_only_sufficient_for_20260626_actual_review_basis",
    "existing_helper_only_sufficient_for_20260626_basis",
    "thin_20260626_boundary_layer_required_next",
    "thin_wrapper_required_next",
    "actual_selection_row_receiver_available",
    "actual_rating_row_normalizer_available",
    "readfeel_execution_blocker_ingestion_available",
    "question_need_observation_normalizer_available",
    "disposal_receipt_receiver_available",
    "bodyfree_post_review_summary_available",
    "p5_decision_candidate_separation_available",
    "p8_material_candidate_handoff_available",
    "final_no_body_no_question_no_touch_validation_available",
    "r52_reintake_handoff_available",
    "row_intake_helper_required_here",
    "capability_decision_ref",
    "capability_reason_refs",
    "new_full_operation_helper_required",
    "helper_capability_status_ref",
    "helper_reuse_verdict_ref",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "body_full_generation_requested_here",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev01_schema_version",
    "ev01_material_ref",
    "ev01_next_required_step",
    "ev01_thin_boundary_layer_required",
    "current_refs_refreeze_status_ref",
    "operation_current_refs",
    "operation_current_ref_count",
    "operation_current_ref_keys",
    "operation_current_ref_key_count",
    "required_operation_current_ref_keys",
    "required_operation_current_ref_key_count",
    "all_required_operation_current_refs_present",
    "operation_current_refs_match_20260626_snapshot",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "historical_helper_refs_separated",
    "historical_helper_refs_used_as_actual_review_basis",
    "old_helper_refs_allowed_as_actual_review_basis",
    "existing_helper_module_ref",
    "existing_helper_schema_step_ref",
    "existing_helper_current_refs",
    "existing_helper_current_ref_count",
    "existing_helper_current_refs_are_historical_here",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_actual_review_basis",
    "existing_helper_current_refs_match_20260626_snapshot",
    "differing_operation_current_ref_keys",
    "differing_operation_current_ref_key_count",
    "current_refs_override_uses_thin_20260626_boundary_layer",
    "existing_op01_override_not_used_as_actual_review_basis",
    "downstream_20260625_constant_not_rewritten",
    "new_full_operation_helper_required",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "body_full_generation_requested_here",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev02_schema_version",
    "ev02_material_ref",
    "ev02_next_required_step",
    "ev02_current_refs_refrozen",
    "r55_hold_intake_status_ref",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "r55_decision_material_schema_version",
    "r55_decision_material_ref",
    "r55_current_received_snapshot_refs",
    "r55_current_received_snapshot_ref_count",
    "r55_current_refs_are_historical_hold_material_here",
    "r55_current_refs_used_as_actual_review_basis",
    "r55_decision_ref",
    "r55_decision_status",
    "r55_next_required_step",
    "r55_existing_r52_decision_equivalent",
    "r55_actual_review_evidence_gap_status_ref",
    "r55_actual_review_evidence_complete",
    "actual_review_evidence_complete",
    "required_case_count",
    "rating_row_count_before_review",
    "question_observation_row_count_before_review",
    "disposal_verified_before_review",
    "missing_evidence_refs",
    "missing_evidence_ref_count",
    "r54_review_operation_state_ref",
    "p5_decision_status_ref",
    "p5_decision_candidate_ref",
    "p6_hold",
    "p8_hold",
    "release_hold",
    "r54_actual_local_only_human_review_operation_required_before_r52_reintake",
    "body_full_generation_blocked_until_later_preflight",
    "body_full_generation_blocked_until_preflight",
    "body_full_generation_requested_here",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev03_schema_version",
    "ev03_material_ref",
    "ev03_next_required_step",
    "ev03_r55_hold_intake_status_ref",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op04_helper_ref",
    "existing_op04_schema_version",
    "existing_op04_operation_current_refs",
    "existing_op04_current_refs_are_historical_here",
    "existing_op04_explicit_allow_token_ref",
    "existing_op04_allow_token_is_historical_here",
    "existing_op04_reused_as_actual_preflight_basis",
    "existing_op04_structural_contract_reused",
    "preflight_implementation_status_ref",
    "local_review_root_env_var",
    "local_review_root_presence_ref",
    "local_review_root_declared",
    "local_review_root_outside_repo_export_scope",
    "local_review_root_path_included",
    "local_review_root_path_materialized_here",
    "explicit_allow_token_ref",
    "explicit_allow_present",
    "explicit_allow_token_body_stored_here",
    "explicit_allow_token_matches_20260626",
    "purge_plan_ref",
    "purge_plan_present",
    "purge_plan_ready",
    "purge_plan_required_before_body_full_generation",
    "purge_plan_required_delete_target_refs",
    "retention_policy_ref",
    "retention_policy_present",
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_finalized_max_hours",
    "delete_trigger_refs",
    "export_denylist_policy_ref",
    "export_denylist_present",
    "export_denylist_patterns",
    "export_denylist_violation_refs",
    "export_denylist_violation_count",
    "preflight_status",
    "preflight_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "body_full_packet_generation_allowed_before_preflight",
    "body_full_packet_generation_allowed_by_preflight",
    "body_full_packet_generation_request_allowed_next",
    "body_full_generation_blocked_until_manifest_freeze",
    "body_full_generation_requested_here",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "actual_review_evidence_complete",
    "r55_hold_preserved",
    "p6_hold",
    "p8_hold",
    "release_hold",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev04_schema_version",
    "ev04_material_ref",
    "ev04_next_required_step",
    "ev04_preflight_status",
    "ev04_preflight_ready",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op05_helper_ref",
    "existing_op05_schema_version",
    "existing_op05_operation_current_refs",
    "existing_op05_current_refs_are_historical_here",
    "existing_op05_reused_as_actual_manifest_basis",
    "existing_op05_structural_contract_reused",
    "r48_case_matrix_schema_version",
    "r48_case_matrix_material_ref",
    "required_case_count",
    "case_distribution",
    "case_distribution_total_count",
    "case_distribution_matches_design",
    "manifest_refreeze_status_ref",
    "manifest_status",
    "manifest_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "case_rows",
    "case_count",
    "family_case_counts",
    "case_role_counts",
    "subscription_tier_ref_counts",
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
    "controller_manifest_rows",
    "reviewer_facing_case_index_rows",
    "controller_manifest_row_count",
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
    "p4_r11_rows_mixed_in",
    "p4_r11_rows_mixed_in_count",
    "body_full_packet_generation_request_allowed_next",
    "body_full_generation_blocked_until_request_step",
    "body_full_generation_requested_here",
    "body_full_packet_zip_inclusion_allowed",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_EV_DEFAULT_REVIEW_SESSION_ID, max_length=220)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_EV_FALSE_FLAG_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {
        "api_changed": False,
        "db_changed": False,
        "rn_changed": False,
        "runtime_changed": False,
        "api_route_changed": False,
        "db_schema_changed": False,
        "db_migration_changed": False,
        "rn_visible_contract_changed": False,
        "public_response_top_level_key_added": False,
        "public_response_key_changed": False,
        "question_implementation_started_here": False,
        "question_trigger_logic_implemented": False,
        "p8_question_implementation_spec_finalized_here": False,
        "release_allowed": False,
    }


def _body_free_markers() -> dict[str, bool]:
    return body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)


def _assert_required_fields(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:8]}")
    extra = sorted(set(data) - set(required))
    if extra:
        raise ValueError(f"{source} has unexpected fields: {extra[:8]}")


def _assert_common_bodyfree_no_touch(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    policy_section: str,
    operation_step_ref: str,
    source: str,
    false_flag_refs: Sequence[str] | None = None,
) -> None:
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R54_EV_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R54_EV_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("policy_kind") != P7_R54_EV_POLICY_KIND:
        raise ValueError(f"{source} policy kind changed")
    if data.get("policy_section") != policy_section or data.get("operation_step_ref") != operation_step_ref:
        raise ValueError(f"{source} operation step changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} source mode changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if safe_mapping(data.get("operation_current_refs")) != P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} must use the 20260626 operation current refs")
    if data.get("operation_current_ref_count") != len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} operation current ref count changed")
    if data.get("actual_review_basis_ref") != P7_R54_EV_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError(f"{source} actual review basis ref changed")
    if data.get("actual_review_basis_allowed") != P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF:
        raise ValueError(f"{source} actual review basis allowed ref changed")
    if data.get("operation_current_refs_are_actual_review_basis") is not True:
        raise ValueError(f"{source} must use 20260626 operation current refs as basis")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if data.get("raw_body_included", False) is not False:
        raise ValueError(f"{source} must not include raw body")
    if data.get("question_text_included") is not False or data.get("draft_question_text_included") is not False:
        raise ValueError(f"{source} must not include question text")
    if data.get("local_path_included") is not False:
        raise ValueError(f"{source} must not include local paths")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r54_ev_no_touch_contract") or {}, source=f"{source}.r54_ev_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    refs_to_check = tuple(false_flag_refs) if false_flag_refs is not None else P7_R54_EV_FALSE_FLAG_REFS
    for key in refs_to_check:
        if data.get(key) is not False:
            raise ValueError(f"{source} must keep {key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _function_params(function_ref: str) -> tuple[str, ...]:
    target = getattr(r54op, function_ref, None)
    if not callable(target):
        return ()
    return tuple(inspect.signature(target).parameters)


def _downstream_current_refs_constant_function_refs() -> list[str]:
    refs: list[str] = []
    for name in sorted(dir(r54op)):
        if not name.startswith("build_p7_r54_op"):
            continue
        if name == "build_p7_r54_op01_operation_current_snapshot_refs_refreeze":
            continue
        target = getattr(r54op, name, None)
        if not callable(target):
            continue
        try:
            source = inspect.getsource(target)
        except (OSError, TypeError):
            continue
        if "P7_R54_OPERATION_CURRENT_REFS" in source:
            refs.append(name)
    return refs


def _helper_capability_row(function_ref: str) -> dict[str, Any]:
    params = _function_params(function_ref)
    return {
        "helper_function_ref": function_ref,
        "present": callable(getattr(r54op, function_ref, None)),
        "accepts_operation_current_refs": "operation_current_refs" in params,
        "accepts_reviewer_selection_rows": "reviewer_selection_rows" in params,
    }


def _helper_rows() -> list[dict[str, Any]]:
    return [_helper_capability_row(function_ref) for function_ref in P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS]


def _op01_override_build_accepted(op00: Mapping[str, Any]) -> bool:
    try:
        r54op.build_p7_r54_op01_operation_current_snapshot_refs_refreeze(
            scope_no_touch_boundary_freeze=op00,
            operation_current_refs=P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS,
            material_id="p7_r54_ev01_op01_20260626_override_probe",
        )
    except ValueError:
        return False
    return True


def build_p7_r54_ev00_scope_no_touch_boundary_confirmation(
    *,
    review_session_id: Any = P7_R54_EV_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r54_ev00_scope_no_touch_boundary_confirmation",
) -> dict[str, Any]:
    """Build EV00 body-free scope / no-touch boundary confirmation."""

    session_id = _safe_review_session_id(review_session_id)
    op00 = r54op.build_p7_r54_op00_scope_no_touch_boundary_freeze(review_session_id=session_id)
    r54op.assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract(op00)
    material = {
        "schema_version": P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV00_STEP_REF,
        "operation_step_ref": P7_R54_EV00_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev00_scope_no_touch_boundary_confirmation", max_length=220),
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "scope_boundary_confirmed": True,
        "no_touch_boundary_confirmed": True,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "allowed_operation_step_refs": [P7_R54_EV00_STEP_REF, P7_R54_EV01_STEP_REF],
        "out_of_scope_refs": [
            "p8_question_design",
            "question_text_or_draft_question_text",
            "api_route_change",
            "db_schema_or_migration_change",
            "rn_ui_or_visible_contract_change",
            "emlis_runtime_surface_change",
            "user_label_connection_runtime_change",
            "body_full_packet_generation",
            "actual_human_review_execution",
            "p6_p8_or_release_promotion",
        ],
        "existing_op00_schema_version": clean_identifier(op00.get("schema_version"), default="", max_length=240),
        "existing_op00_material_ref": clean_identifier(op00.get("material_id"), default="p7_r54_operation_scope_no_touch_boundary_freeze", max_length=240),
        "existing_op00_contract_available": True,
        "existing_op00_no_touch_boundary_frozen": op00.get("no_touch_boundary_frozen") is True,
        "existing_helper_refs_can_be_used_for_actual_review_basis": False,
        "operation_current_refs_required_before_actual_review": True,
        "historical_helper_refs_must_be_separated": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "body_full_generation_requested_here": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "no_touch_boundary_frozen": True,
        "implemented_steps": list(P7_R54_EV00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_EV00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_EV01_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(material)
    return material


def assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS,
        source="p7_r54_ev00_scope_no_touch_boundary_confirmation",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION,
        policy_section=P7_R54_EV00_STEP_REF,
        operation_step_ref=P7_R54_EV00_STEP_REF,
        source="p7_r54_ev00_scope_no_touch_boundary_confirmation",
    )
    if data.get("scope_boundary_confirmed") is not True or data.get("no_touch_boundary_confirmed") is not True:
        raise ValueError("R54 EV00 must confirm scope and no-touch boundaries")
    if data.get("allowed_operation_step_refs") != [P7_R54_EV00_STEP_REF, P7_R54_EV01_STEP_REF]:
        raise ValueError("R54 EV00 allowed operation steps changed")
    if data.get("existing_op00_contract_available") is not True:
        raise ValueError("R54 EV00 must confirm existing OP00 contract availability")
    if data.get("existing_op00_no_touch_boundary_frozen") is not True:
        raise ValueError("R54 EV00 must confirm existing OP00 no-touch boundary")
    if data.get("operation_current_refs_required_before_actual_review") is not True:
        raise ValueError("R54 EV00 must require operation-current refs before actual review")
    if data.get("historical_helper_refs_must_be_separated") is not True:
        raise ValueError("R54 EV00 must separate historical helper refs")
    if data.get("existing_helper_refs_can_be_used_for_actual_review_basis") is not False:
        raise ValueError("R54 EV00 must not use existing helper refs as actual review basis")
    if data.get("body_full_generation_blocked_until_later_preflight") is not True:
        raise ValueError("R54 EV00 must block body-full generation until later preflight")
    if data.get("body_full_generation_blocked_until_preflight") is not True:
        raise ValueError("R54 EV00 must block body-full generation until preflight")
    if data.get("body_full_generation_requested_here") is not False:
        raise ValueError("R54 EV00 must not request body-full generation")
    if data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV00 must block actual human review completion claims")
    if data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV00 must block human review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV00 must block P6/P8/release promotion")
    if data.get("no_touch_boundary_frozen") is not True:
        raise ValueError("R54 EV00 must freeze no-touch boundary")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_EV00_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV00 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_EV01_STEP_REF:
        raise ValueError("R54 EV00 next required step changed")
    return True


def build_p7_r54_ev01_existing_helper_capability_inspection(
    *,
    scope_no_touch_boundary_confirmation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev01_existing_helper_capability_inspection",
) -> dict[str, Any]:
    """Build EV01 body-free existing helper capability inspection material."""

    ev00 = (
        safe_mapping(scope_no_touch_boundary_confirmation)
        if scope_no_touch_boundary_confirmation is not None
        else build_p7_r54_ev00_scope_no_touch_boundary_confirmation()
    )
    assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract(ev00)
    session_id = _safe_review_session_id(ev00.get("review_session_id"))
    op00 = r54op.build_p7_r54_op00_scope_no_touch_boundary_freeze(review_session_id=session_id)
    r54op.assert_p7_r54_op00_scope_no_touch_boundary_freeze_contract(op00)

    helper_rows = _helper_rows()
    found_refs = [row["helper_function_ref"] for row in helper_rows if row.get("present") is True]
    missing_refs = [function_ref for function_ref in P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS if function_ref not in found_refs]
    op01_params = _function_params("build_p7_r54_op01_operation_current_snapshot_refs_refreeze")
    op01_accepts_refs = "operation_current_refs" in op01_params
    override_accepted = _op01_override_build_accepted(op00)
    current_refs_match = r54op.P7_R54_OPERATION_CURRENT_REFS == P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
    bodyfree_handoff_possible = not missing_refs
    selection_intake_present = all(callable(getattr(r54op, function_ref, None)) for function_ref in P7_R54_EV_SELECTION_ROW_INTAKE_HELPER_REFS)
    existing_helper_sufficient = bool(current_refs_match and op01_accepts_refs and override_accepted and bodyfree_handoff_possible)
    expected_keys = tuple(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.keys())
    existing_keys = tuple(r54op.P7_R54_OPERATION_CURRENT_REFS.keys())
    operation_current_ref_keys_match = expected_keys == existing_keys
    differing_operation_current_ref_keys = [
        key for key in expected_keys if r54op.P7_R54_OPERATION_CURRENT_REFS.get(key) != P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.get(key)
    ]
    downstream_constant_refs = _downstream_current_refs_constant_function_refs()
    actual_selection_row_receiver_available = callable(getattr(r54op, "build_p7_r54_op11_sanitized_review_result_capture", None)) and (
        "reviewer_selection_rows" in _function_params("build_p7_r54_op11_sanitized_review_result_capture")
    )
    actual_rating_row_normalizer_available = callable(getattr(r54op, "build_p7_r54_op12_rating_row_normalization", None))
    readfeel_execution_blocker_ingestion_available = callable(getattr(r54op, "build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion", None))
    question_need_observation_normalizer_available = callable(getattr(r54op, "build_p7_r54_op14_question_need_observation_normalization", None))
    disposal_receipt_receiver_available = callable(getattr(r54op, "build_p7_r54_op17_purge_disposal_receipt", None))
    bodyfree_post_review_summary_available = callable(getattr(r54op, "build_p7_r54_op18_bodyfree_post_review_summary", None))
    p5_decision_candidate_separation_available = callable(getattr(r54op, "build_p7_r54_op19_p5_decision_candidate_separation", None))
    p8_material_candidate_handoff_available = callable(getattr(r54op, "build_p7_r54_op21_p8_material_candidate_handoff", None))
    final_no_body_no_question_no_touch_validation_available = callable(getattr(r54op, "build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation", None))
    r52_reintake_handoff_available = callable(getattr(r54op, "build_p7_r54_op23_r52_reintake_handoff", None))
    row_intake_helper_required_here = not all((
        actual_selection_row_receiver_available, actual_rating_row_normalizer_available, readfeel_execution_blocker_ingestion_available,
        question_need_observation_normalizer_available, disposal_receipt_receiver_available, bodyfree_post_review_summary_available,
        p5_decision_candidate_separation_available, p8_material_candidate_handoff_available,
        final_no_body_no_question_no_touch_validation_available, r52_reintake_handoff_available,
    ))

    material = {
        "schema_version": P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV01_STEP_REF,
        "operation_step_ref": P7_R54_EV01_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev01_existing_helper_capability_inspection", max_length=220),
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "inspection_status_ref": P7_R54_EV01_HELPER_CAPABILITY_STATUS_REF,
        "ev00_schema_version": P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION,
        "ev00_material_ref": clean_identifier(ev00.get("material_id"), default="p7_r54_ev00_scope_no_touch_boundary_confirmation", max_length=240),
        "ev00_next_required_step": clean_identifier(ev00.get("next_required_step"), default=P7_R54_EV01_STEP_REF, max_length=220),
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "existing_helper_module_ref": r54op.__name__,
        "existing_helper_module_imported": True,
        "existing_op00_scope_no_touch_available": callable(getattr(r54op, "build_p7_r54_op00_scope_no_touch_boundary_freeze", None)),
        "existing_op01_current_refs_refreeze_available": callable(getattr(r54op, "build_p7_r54_op01_operation_current_snapshot_refs_refreeze", None)),
        "existing_helper_schema_step_ref": r54op.P7_R54_OPERATION_REENTRY_STEP,
        "existing_helper_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_helper_current_ref_count": len(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "expected_20260626_operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "expected_20260626_operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "existing_helper_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_helper_operation_current_ref_count": len(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "operation_current_ref_keys": list(expected_keys),
        "operation_current_ref_key_count": len(expected_keys),
        "operation_current_ref_keys_match": operation_current_ref_keys_match,
        "operation_current_ref_values_match": not differing_operation_current_ref_keys,
        "differing_operation_current_ref_keys": differing_operation_current_ref_keys,
        "differing_operation_current_ref_key_count": len(differing_operation_current_ref_keys),
        "downstream_current_refs_constant_function_refs": downstream_constant_refs,
        "downstream_current_refs_constant_function_count": len(downstream_constant_refs),
        "existing_helper_current_refs_match_20260626_snapshot": current_refs_match,
        "existing_helper_current_refs_are_historical_here": True,
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_actual_review_basis": False,
        "required_helper_function_refs": list(P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS),
        "required_helper_function_count": len(P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS),
        "found_helper_function_refs": found_refs,
        "found_helper_function_count": len(found_refs),
        "missing_helper_function_refs": missing_refs,
        "missing_helper_function_count": len(missing_refs),
        "required_helper_functions_all_present": not missing_refs,
        "helper_function_capability_rows": helper_rows,
        "helper_function_capability_row_count": len(helper_rows),
        "selection_row_intake_helper_count": len(P7_R54_EV_SELECTION_ROW_INTAKE_HELPER_REFS),
        "selection_row_intake_helpers_present": selection_intake_present,
        "op01_signature_accepts_operation_current_refs": op01_accepts_refs,
        "op01_override_20260626_contract_accepted": override_accepted,
        "op01_override_failure_reason_refs": [P7_R54_EV01_OVERRIDE_REJECTED_REASON_REF] if not override_accepted else [],
        "helper_op01_accepts_operation_current_refs_parameter": op01_accepts_refs,
        "helper_op01_override_build_attempted_bodyfree": True,
        "helper_op01_override_build_accepted": override_accepted,
        "helper_op01_override_rejected": not override_accepted,
        "helper_op01_override_rejection_ref": P7_R54_EV01_CURRENT_REF_OVERRIDE_REJECTION_REF if not override_accepted else "",
        "current_refs_override_possible_with_existing_helper_only": bool(op01_accepts_refs and override_accepted),
        "bodyfree_handoff_possible_with_existing_helper_functions": bodyfree_handoff_possible,
        "actual_selection_rows_intake_possible_with_existing_helper_functions": selection_intake_present,
        "existing_helper_only_sufficient_for_20260626_actual_review_basis": existing_helper_sufficient,
        "existing_helper_only_sufficient_for_20260626_basis": existing_helper_sufficient,
        "thin_20260626_boundary_layer_required_next": not existing_helper_sufficient,
        "thin_wrapper_required_next": not existing_helper_sufficient,
        "actual_selection_row_receiver_available": actual_selection_row_receiver_available,
        "actual_rating_row_normalizer_available": actual_rating_row_normalizer_available,
        "readfeel_execution_blocker_ingestion_available": readfeel_execution_blocker_ingestion_available,
        "question_need_observation_normalizer_available": question_need_observation_normalizer_available,
        "disposal_receipt_receiver_available": disposal_receipt_receiver_available,
        "bodyfree_post_review_summary_available": bodyfree_post_review_summary_available,
        "p5_decision_candidate_separation_available": p5_decision_candidate_separation_available,
        "p8_material_candidate_handoff_available": p8_material_candidate_handoff_available,
        "final_no_body_no_question_no_touch_validation_available": final_no_body_no_question_no_touch_validation_available,
        "r52_reintake_handoff_available": r52_reintake_handoff_available,
        "row_intake_helper_required_here": row_intake_helper_required_here,
        "capability_decision_ref": P7_R54_EV01_DECISION_THIN_WRAPPER_REQUIRED_REF if not existing_helper_sufficient else "R54_EV01_EXISTING_HELPER_SUFFICIENT_FOR_20260626_CURRENT_REFS",
        "capability_reason_refs": [P7_R54_EV01_OVERRIDE_REJECTED_REASON_REF, P7_R54_EV01_DOWNSTREAM_CONSTANT_REASON_REF] if not existing_helper_sufficient else [],
        "new_full_operation_helper_required": False,
        "helper_capability_status_ref": P7_R54_EV01_HELPER_CAPABILITY_STATUS_REF,
        "helper_reuse_verdict_ref": P7_R54_EV01_HELPER_REUSE_VERDICT_THIN_LAYER_REQUIRED_REF,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "body_full_generation_requested_here": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_EV01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_EV02_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material)
    return material


def assert_p7_r54_ev01_existing_helper_capability_inspection_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_REQUIRED_FIELD_REFS,
        source="p7_r54_ev01_existing_helper_capability_inspection",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION,
        policy_section=P7_R54_EV01_STEP_REF,
        operation_step_ref=P7_R54_EV01_STEP_REF,
        source="p7_r54_ev01_existing_helper_capability_inspection",
    )
    if data.get("ev00_schema_version") != P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION:
        raise ValueError("R54 EV01 EV00 schema version changed")
    if data.get("ev00_next_required_step") != P7_R54_EV01_STEP_REF:
        raise ValueError("R54 EV01 must follow EV00")
    if data.get("inspection_status_ref") != P7_R54_EV01_HELPER_CAPABILITY_STATUS_REF:
        raise ValueError("R54 EV01 inspection status changed")
    if data.get("existing_helper_module_ref") != r54op.__name__:
        raise ValueError("R54 EV01 existing helper module ref changed")
    if data.get("existing_helper_module_imported") is not True:
        raise ValueError("R54 EV01 must import existing helper module")
    if data.get("existing_op00_scope_no_touch_available") is not True:
        raise ValueError("R54 EV01 existing OP00 helper missing")
    if data.get("existing_op01_current_refs_refreeze_available") is not True:
        raise ValueError("R54 EV01 existing OP01 helper missing")
    if data.get("existing_helper_schema_step_ref") != r54op.P7_R54_OPERATION_REENTRY_STEP:
        raise ValueError("R54 EV01 existing helper schema step ref changed")
    if safe_mapping(data.get("existing_helper_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV01 existing helper current refs changed")
    if data.get("existing_helper_current_ref_count") != len(r54op.P7_R54_OPERATION_CURRENT_REFS):
        raise ValueError("R54 EV01 existing helper current ref count changed")
    if safe_mapping(data.get("expected_20260626_operation_current_refs")) != P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R54 EV01 expected 20260626 operation current refs changed")
    if data.get("expected_20260626_operation_current_ref_count") != len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError("R54 EV01 expected 20260626 ref count changed")
    if safe_mapping(data.get("existing_helper_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV01 existing helper operation refs changed")
    if data.get("existing_helper_operation_current_ref_count") != len(r54op.P7_R54_OPERATION_CURRENT_REFS):
        raise ValueError("R54 EV01 existing helper operation ref count changed")
    differing = tuple(data.get("differing_operation_current_ref_keys") or ())
    if data.get("operation_current_ref_keys_match") is not True:
        raise ValueError("R54 EV01 operation current ref keys must match")
    if data.get("operation_current_ref_values_match") is not False:
        raise ValueError("R54 EV01 operation current ref values must differ")
    if data.get("differing_operation_current_ref_key_count") != len(differing):
        raise ValueError("R54 EV01 differing operation current ref count changed")
    downstream_refs = tuple(data.get("downstream_current_refs_constant_function_refs") or ())
    if data.get("downstream_current_refs_constant_function_count") != len(downstream_refs) or not downstream_refs:
        raise ValueError("R54 EV01 downstream current refs constant functions must be visible")
    if data.get("existing_helper_current_refs_match_20260626_snapshot") is not False:
        raise ValueError("R54 EV01 must record existing helper refs as not matching 20260626")
    if data.get("existing_helper_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV01 must classify existing helper refs as historical here")
    if data.get("existing_helper_refs_can_be_used_for_helper_regression_only") is not True:
        raise ValueError("R54 EV01 must keep existing helper refs regression-only")
    if data.get("existing_helper_refs_can_be_used_for_actual_review_basis") is not False:
        raise ValueError("R54 EV01 must not allow existing helper refs as actual review basis")
    if tuple(data.get("required_helper_function_refs") or ()) != P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS:
        raise ValueError("R54 EV01 required helper function refs changed")
    if data.get("required_helper_function_count") != len(P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS):
        raise ValueError("R54 EV01 required helper function count changed")
    if tuple(data.get("found_helper_function_refs") or ()) != P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS:
        raise ValueError("R54 EV01 found helper function refs changed")
    if data.get("found_helper_function_count") != len(P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS):
        raise ValueError("R54 EV01 found helper function count changed")
    if data.get("missing_helper_function_refs") != [] or data.get("missing_helper_function_count") != 0:
        raise ValueError("R54 EV01 must not have missing helper refs")
    if data.get("required_helper_functions_all_present") is not True:
        raise ValueError("R54 EV01 must find all required helper functions")
    rows = data.get("helper_function_capability_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("R54 EV01 helper function rows must be a sequence")
    if data.get("helper_function_capability_row_count") != len(rows):
        raise ValueError("R54 EV01 helper function row count changed")
    row_refs = [safe_mapping(row).get("helper_function_ref") for row in rows]
    if tuple(row_refs) != P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS:
        raise ValueError("R54 EV01 helper function row refs changed")
    for row in rows:
        item = safe_mapping(row)
        if item.get("present") is not True:
            raise ValueError("R54 EV01 helper row must be present")
        assert_p7_no_body_payload_or_contract_mutation(item, source="p7_r54_ev01.helper_function_capability_row")
    if data.get("selection_row_intake_helper_count") != len(P7_R54_EV_SELECTION_ROW_INTAKE_HELPER_REFS):
        raise ValueError("R54 EV01 selection row intake helper count changed")
    if data.get("selection_row_intake_helpers_present") is not True:
        raise ValueError("R54 EV01 selection row intake helpers must be present")
    if data.get("op01_signature_accepts_operation_current_refs") is not True:
        raise ValueError("R54 EV01 OP01 signature capability changed")
    if data.get("op01_override_20260626_contract_accepted") is not False:
        raise ValueError("R54 EV01 OP01 20260626 override must be rejected")
    if P7_R54_EV01_OVERRIDE_REJECTED_REASON_REF not in tuple(data.get("op01_override_failure_reason_refs") or ()): 
        raise ValueError("R54 EV01 OP01 override rejection reason missing")
    if data.get("helper_op01_accepts_operation_current_refs_parameter") is not True:
        raise ValueError("R54 EV01 OP01 must expose the operation_current_refs parameter")
    if data.get("helper_op01_override_build_attempted_bodyfree") is not True:
        raise ValueError("R54 EV01 must attempt OP01 override as body-free inspection")
    if data.get("helper_op01_override_build_accepted") is not False:
        raise ValueError("R54 EV01 OP01 override must not be accepted by existing helper contract")
    if data.get("helper_op01_override_rejected") is not True:
        raise ValueError("R54 EV01 OP01 override must be rejected")
    if data.get("helper_op01_override_rejection_ref") != P7_R54_EV01_CURRENT_REF_OVERRIDE_REJECTION_REF:
        raise ValueError("R54 EV01 OP01 override rejection ref changed")
    if data.get("current_refs_override_possible_with_existing_helper_only") is not False:
        raise ValueError("R54 EV01 must not allow existing-helper-only current refs override")
    if data.get("bodyfree_handoff_possible_with_existing_helper_functions") is not True:
        raise ValueError("R54 EV01 must preserve existing body-free handoff capability")
    if data.get("actual_selection_rows_intake_possible_with_existing_helper_functions") is not True:
        raise ValueError("R54 EV01 must preserve existing selection row intake capability")
    if data.get("existing_helper_only_sufficient_for_20260626_actual_review_basis") is not False:
        raise ValueError("R54 EV01 existing helper only must not be sufficient for 20260626 basis")
    if data.get("existing_helper_only_sufficient_for_20260626_basis") is not False:
        raise ValueError("R54 EV01 existing helper only must not be sufficient for 20260626 basis alias")
    if data.get("thin_20260626_boundary_layer_required_next") is not True:
        raise ValueError("R54 EV01 must require a thin 20260626 boundary layer next")
    if data.get("thin_wrapper_required_next") is not True:
        raise ValueError("R54 EV01 must require thin wrapper next")
    for capability_key in (
        "actual_selection_row_receiver_available", "actual_rating_row_normalizer_available",
        "readfeel_execution_blocker_ingestion_available", "question_need_observation_normalizer_available",
        "disposal_receipt_receiver_available", "bodyfree_post_review_summary_available",
        "p5_decision_candidate_separation_available", "p8_material_candidate_handoff_available",
        "final_no_body_no_question_no_touch_validation_available", "r52_reintake_handoff_available",
    ):
        if data.get(capability_key) is not True:
            raise ValueError(f"R54 EV01 helper capability missing: {capability_key}")
    if data.get("row_intake_helper_required_here") is not False:
        raise ValueError("R54 EV01 must not require row intake helper here")
    if data.get("capability_decision_ref") != P7_R54_EV01_DECISION_THIN_WRAPPER_REQUIRED_REF:
        raise ValueError("R54 EV01 capability decision ref changed")
    if P7_R54_EV01_DOWNSTREAM_CONSTANT_REASON_REF not in tuple(data.get("capability_reason_refs") or ()): 
        raise ValueError("R54 EV01 downstream constant reason missing")
    if data.get("new_full_operation_helper_required") is not False:
        raise ValueError("R54 EV01 must not require a new full operation helper")
    if data.get("helper_capability_status_ref") != P7_R54_EV01_HELPER_CAPABILITY_STATUS_REF:
        raise ValueError("R54 EV01 helper capability status changed")
    if data.get("helper_reuse_verdict_ref") != P7_R54_EV01_HELPER_REUSE_VERDICT_THIN_LAYER_REQUIRED_REF:
        raise ValueError("R54 EV01 helper reuse verdict changed")
    if data.get("body_full_generation_blocked_until_later_preflight") is not True:
        raise ValueError("R54 EV01 must block body-full generation until later preflight")
    if data.get("body_full_generation_requested_here") is not False:
        raise ValueError("R54 EV01 must not request body-full generation")
    if data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV01 must block actual review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV01 must block P6/P8/release promotion")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_EV01_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV01 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_EV02_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 EV01 next required step changed")
    return True


P7_R54_EV02_CURRENT_REFS_REFREEZE_STATUS_REF: Final = "R54_EV02_OPERATION_CURRENT_REFS_20260626_REFROZEN"
P7_R54_EV03_R55_HOLD_INTAKE_STATUS_REF: Final = "R54_EV03_R55_HOLD_INTAKE_REFROZEN_BEFORE_LOCAL_PREFLIGHT"
P7_R54_EV04_PREFLIGHT_IMPLEMENTATION_STATUS_REF: Final = "R54_EV04_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMED_20260626"
P7_R54_EV05_MANIFEST_REFREEZE_STATUS_REF: Final = "R54_EV05_24_CASE_MANIFEST_REFROZEN_AFTER_20260626_PREFLIGHT"

P7_R54_EV04_PREFLIGHT_READY_STATUS_REF: Final = "PREFLIGHT_READY"
P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF: Final = "PREFLIGHT_BLOCKED"
P7_R54_EV04_ALLOWED_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV04_PREFLIGHT_READY_STATUS_REF,
    P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF,
)
P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF: Final = "local_review_root_declared_outside_repo_export_scope"
P7_R54_EV04_LOCAL_REVIEW_ROOT_MISSING_REF: Final = "missing_local_review_root_presence_ref"
P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF: Final = "R54_ACTUAL_LOCAL_REVIEW_BODY_FULL_PACKET_GENERATION_ALLOWED_20260626"
P7_R54_EV04_PURGE_PLAN_READY_REF: Final = "r54_actual_review_purge_plan_ready_bodyfree_20260626"
P7_R54_EV04_RETENTION_POLICY_READY_REF: Final = "r54_actual_review_retention_policy_ready_bodyfree_20260626"
P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF: Final = "r54_actual_review_export_denylist_policy_ready_bodyfree_20260626"
P7_R54_EV04_PREFLIGHT_READY_REASON_REF: Final = "local_only_preflight_ready_for_24_case_manifest_refreeze_20260626"
P7_R54_EV04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "local_only_preflight_repair_before_r54_ev05_24_case_manifest_refreeze"
P7_R54_EV04_REQUIRED_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    "body_full_packet",
    "reviewer_notes",
    "temporary_form",
)

P7_R54_EV05_MANIFEST_READY_STATUS_REF: Final = "MANIFEST_REFROZEN_READY_FOR_BODYFREE_PACKET_GENERATION_REQUEST"
P7_R54_EV05_MANIFEST_BLOCKED_STATUS_REF: Final = "MANIFEST_BLOCKED_BY_LOCAL_ONLY_PREFLIGHT"
P7_R54_EV05_ALLOWED_MANIFEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV05_MANIFEST_READY_STATUS_REF,
    P7_R54_EV05_MANIFEST_BLOCKED_STATUS_REF,
)
P7_R54_EV05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "local_only_preflight_repair_before_r54_ev05_24_case_manifest_refreeze"
P7_R54_EV05_REVIEWER_IDENTIFIER_POLICY_REF: Final = "reviewer_receives_blind_case_id_only_controller_keeps_case_refs"
P7_R54_EV05_CASE_DISTRIBUTION: Final[dict[str, int]] = {
    "history_line_eligible_input": 4,
    "standard_state_answer_owned_history": 4,
    "self_understanding_owned_history": 3,
    "uncertainty_support_owned_history": 3,
    "change_future_intention_owned_history": 3,
    "relationship_gratitude_recovery_owned_history": 3,
    "low_information_history_not_eligible": 2,
    "free_tier_history_present_not_allowed": 2,
}


def build_p7_r54_ev02_operation_current_refs_20260626_refreeze(
    *,
    existing_helper_capability_inspection: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev02_operation_current_refs_20260626_refreeze",
) -> dict[str, Any]:
    """Build EV02 body-free 2026-06-26 operation-current refs refreeze material."""

    ev01 = (
        safe_mapping(existing_helper_capability_inspection)
        if existing_helper_capability_inspection is not None
        else build_p7_r54_ev01_existing_helper_capability_inspection()
    )
    assert_p7_r54_ev01_existing_helper_capability_inspection_contract(ev01)
    session_id = _safe_review_session_id(ev01.get("review_session_id"))
    current_refs = dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS)
    existing_refs = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    ref_keys = list(current_refs.keys())
    differing_ref_keys = [key for key in ref_keys if existing_refs.get(key) != current_refs.get(key)]
    material = {
        "schema_version": P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV02_STEP_REF,
        "operation_step_ref": P7_R54_EV02_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev02_operation_current_refs_20260626_refreeze", max_length=220),
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev01_schema_version": P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION,
        "ev01_material_ref": clean_identifier(ev01.get("material_id"), default="p7_r54_ev01_existing_helper_capability_inspection", max_length=240),
        "ev01_next_required_step": clean_identifier(ev01.get("next_required_step"), default=P7_R54_EV02_STEP_REF, max_length=220),
        "ev01_thin_boundary_layer_required": ev01.get("thin_20260626_boundary_layer_required_next") is True,
        "current_refs_refreeze_status_ref": P7_R54_EV02_CURRENT_REFS_REFREEZE_STATUS_REF,
        "operation_current_refs": current_refs,
        "operation_current_ref_count": len(current_refs),
        "operation_current_ref_keys": ref_keys,
        "operation_current_ref_key_count": len(ref_keys),
        "required_operation_current_ref_keys": list(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()),
        "required_operation_current_ref_key_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "all_required_operation_current_refs_present": tuple(ref_keys) == tuple(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()),
        "operation_current_refs_match_20260626_snapshot": current_refs == P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS,
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "historical_helper_refs_separated": True,
        "historical_helper_refs_used_as_actual_review_basis": False,
        "old_helper_refs_allowed_as_actual_review_basis": False,
        "existing_helper_module_ref": r54op.__name__,
        "existing_helper_schema_step_ref": r54op.P7_R54_OPERATION_REENTRY_STEP,
        "existing_helper_current_refs": existing_refs,
        "existing_helper_current_ref_count": len(existing_refs),
        "existing_helper_current_refs_are_historical_here": True,
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_actual_review_basis": False,
        "existing_helper_current_refs_match_20260626_snapshot": existing_refs == current_refs,
        "differing_operation_current_ref_keys": differing_ref_keys,
        "differing_operation_current_ref_key_count": len(differing_ref_keys),
        "current_refs_override_uses_thin_20260626_boundary_layer": True,
        "existing_op01_override_not_used_as_actual_review_basis": True,
        "downstream_20260625_constant_not_rewritten": True,
        "new_full_operation_helper_required": False,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "body_full_generation_requested_here": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_EV02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_EV03_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(material)
    return material


def assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_REQUIRED_FIELD_REFS,
        source="p7_r54_ev02_operation_current_refs_20260626_refreeze",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION,
        policy_section=P7_R54_EV02_STEP_REF,
        operation_step_ref=P7_R54_EV02_STEP_REF,
        source="p7_r54_ev02_operation_current_refs_20260626_refreeze",
    )
    if data.get("ev01_schema_version") != P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION:
        raise ValueError("R54 EV02 EV01 schema version changed")
    if data.get("ev01_next_required_step") != P7_R54_EV02_STEP_REF:
        raise ValueError("R54 EV02 must follow EV01")
    if data.get("ev01_thin_boundary_layer_required") is not True:
        raise ValueError("R54 EV02 requires EV01 thin boundary layer decision")
    if data.get("current_refs_refreeze_status_ref") != P7_R54_EV02_CURRENT_REFS_REFREEZE_STATUS_REF:
        raise ValueError("R54 EV02 current refs refreeze status changed")
    if tuple(data.get("operation_current_ref_keys") or ()) != tuple(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()):
        raise ValueError("R54 EV02 operation current ref keys changed")
    if data.get("operation_current_ref_key_count") != len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError("R54 EV02 operation current ref key count changed")
    if tuple(data.get("required_operation_current_ref_keys") or ()) != tuple(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()):
        raise ValueError("R54 EV02 required operation current ref keys changed")
    if data.get("required_operation_current_ref_key_count") != len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError("R54 EV02 required operation current ref key count changed")
    if data.get("all_required_operation_current_refs_present") is not True:
        raise ValueError("R54 EV02 must include all required operation current refs")
    if data.get("operation_current_refs_match_20260626_snapshot") is not True:
        raise ValueError("R54 EV02 operation current refs must match 20260626 snapshot")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV02 must use operation current refs as actual review basis")
    if data.get("historical_helper_refs_separated") is not True:
        raise ValueError("R54 EV02 must keep historical helper refs separated")
    if data.get("historical_helper_refs_used_as_actual_review_basis") is not False:
        raise ValueError("R54 EV02 must not use historical helper refs as basis")
    if data.get("old_helper_refs_allowed_as_actual_review_basis") is not False:
        raise ValueError("R54 EV02 must not allow old helper refs as basis")
    if data.get("existing_helper_module_ref") != r54op.__name__:
        raise ValueError("R54 EV02 existing helper module ref changed")
    if data.get("existing_helper_schema_step_ref") != r54op.P7_R54_OPERATION_REENTRY_STEP:
        raise ValueError("R54 EV02 existing helper schema step changed")
    if safe_mapping(data.get("existing_helper_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV02 existing helper current refs changed")
    if data.get("existing_helper_current_ref_count") != len(r54op.P7_R54_OPERATION_CURRENT_REFS):
        raise ValueError("R54 EV02 existing helper ref count changed")
    if data.get("existing_helper_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV02 must classify existing helper refs as historical")
    if data.get("existing_helper_refs_can_be_used_for_helper_regression_only") is not True:
        raise ValueError("R54 EV02 must keep existing helper refs regression-only")
    if data.get("existing_helper_refs_can_be_used_for_actual_review_basis") is not False:
        raise ValueError("R54 EV02 must not use existing helper refs as actual review basis")
    if data.get("existing_helper_current_refs_match_20260626_snapshot") is not False:
        raise ValueError("R54 EV02 must record existing helper refs as older than 20260626")
    differing = tuple(data.get("differing_operation_current_ref_keys") or ())
    if data.get("differing_operation_current_ref_key_count") != len(differing):
        raise ValueError("R54 EV02 differing ref count changed")
    if "backend_zip_ref" not in differing or "premise_zip_ref" not in differing:
        raise ValueError("R54 EV02 must make the 20260626 snapshot delta visible")
    if data.get("current_refs_override_uses_thin_20260626_boundary_layer") is not True:
        raise ValueError("R54 EV02 must use a thin 20260626 boundary layer")
    if data.get("existing_op01_override_not_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV02 must not use rejected existing OP01 override as basis")
    if data.get("downstream_20260625_constant_not_rewritten") is not True:
        raise ValueError("R54 EV02 must not rewrite the existing helper constant")
    if data.get("new_full_operation_helper_required") is not False:
        raise ValueError("R54 EV02 must not require a new full operation helper")
    if data.get("body_full_generation_blocked_until_later_preflight") is not True:
        raise ValueError("R54 EV02 must block body-full generation until later preflight")
    if data.get("body_full_generation_requested_here") is not False:
        raise ValueError("R54 EV02 must not request body-full generation")
    if data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV02 must block actual review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV02 must block P6/P8/release promotion")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_EV02_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV02 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_EV03_STEP_REF:
        raise ValueError("R54 EV02 next required step changed")
    return True


def build_p7_r54_ev03_r55_hold_intake_refreeze(
    *,
    operation_current_refs_refreeze: Mapping[str, Any] | None = None,
    r55_r52_reintake_decision_material: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev03_r55_hold_intake_refreeze",
) -> dict[str, Any]:
    """Build EV03 body-free R55 hold intake refreeze material."""

    ev02 = (
        safe_mapping(operation_current_refs_refreeze)
        if operation_current_refs_refreeze is not None
        else build_p7_r54_ev02_operation_current_refs_20260626_refreeze()
    )
    assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract(ev02)
    r55_decision = (
        safe_mapping(r55_r52_reintake_decision_material)
        if r55_r52_reintake_decision_material is not None
        else build_p7_r55_r52_reintake_decision_materialization_bodyfree()
    )
    assert_p7_r55_r52_reintake_decision_materialization_bodyfree_contract(r55_decision)
    session_id = _safe_review_session_id(ev02.get("review_session_id"))
    material = {
        "schema_version": P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV03_STEP_REF,
        "operation_step_ref": P7_R54_EV03_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev03_r55_hold_intake_refreeze", max_length=220),
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev02_schema_version": P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION,
        "ev02_material_ref": clean_identifier(ev02.get("material_id"), default="p7_r54_ev02_operation_current_refs_20260626_refreeze", max_length=240),
        "ev02_next_required_step": clean_identifier(ev02.get("next_required_step"), default=P7_R54_EV03_STEP_REF, max_length=220),
        "ev02_current_refs_refrozen": ev02.get("current_refs_refreeze_status_ref") == P7_R54_EV02_CURRENT_REFS_REFREEZE_STATUS_REF,
        "r55_hold_intake_status_ref": P7_R54_EV03_R55_HOLD_INTAKE_STATUS_REF,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "r55_decision_material_schema_version": P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION,
        "r55_decision_material_ref": clean_identifier(r55_decision.get("material_id"), default="p7_r55_r52_reintake_decision_materialization_current_default", max_length=240),
        "r55_current_received_snapshot_refs": dict(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r55_current_received_snapshot_ref_count": len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r55_current_refs_are_historical_hold_material_here": True,
        "r55_current_refs_used_as_actual_review_basis": False,
        "r55_decision_ref": clean_identifier(r55_decision.get("r55_decision_ref"), default=P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF, max_length=180),
        "r55_decision_status": clean_identifier(r55_decision.get("decision_status"), default=P7_R55_DEFAULT_DECISION_STATUS_REF, max_length=80),
        "r55_next_required_step": clean_identifier(r55_decision.get("next_required_step"), default=P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF, max_length=220),
        "r55_existing_r52_decision_equivalent": clean_identifier(r55_decision.get("r52_existing_decision_equivalent"), default=P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF, max_length=180),
        "r55_actual_review_evidence_gap_status_ref": clean_identifier(r55_decision.get("actual_review_evidence_gap_status_ref"), default=P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF, max_length=180),
        "r55_actual_review_evidence_complete": False,
        "actual_review_evidence_complete": False,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count_before_review": 0,
        "question_observation_row_count_before_review": 0,
        "disposal_verified_before_review": False,
        "missing_evidence_refs": list(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "missing_evidence_ref_count": len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS),
        "r54_review_operation_state_ref": P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF,
        "p5_decision_status_ref": P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF,
        "p5_decision_candidate_ref": P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF,
        "p6_hold": True,
        "p8_hold": True,
        "release_hold": True,
        "r54_actual_local_only_human_review_operation_required_before_r52_reintake": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "body_full_generation_blocked_until_preflight": True,
        "body_full_generation_requested_here": False,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_EV03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_EV04_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material)
    return material


def assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r54_ev03_r55_hold_intake_refreeze",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_EV03_STEP_REF,
        operation_step_ref=P7_R54_EV03_STEP_REF,
        source="p7_r54_ev03_r55_hold_intake_refreeze",
    )
    if data.get("ev02_schema_version") != P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION:
        raise ValueError("R54 EV03 EV02 schema version changed")
    if data.get("ev02_next_required_step") != P7_R54_EV03_STEP_REF:
        raise ValueError("R54 EV03 must follow EV02")
    if data.get("ev02_current_refs_refrozen") is not True:
        raise ValueError("R54 EV03 requires EV02 current refs refreeze")
    if data.get("r55_hold_intake_status_ref") != P7_R54_EV03_R55_HOLD_INTAKE_STATUS_REF:
        raise ValueError("R54 EV03 R55 hold intake status changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV03 must keep EV operation refs as actual review basis")
    if data.get("r55_decision_material_schema_version") != P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 EV03 R55 decision material schema version changed")
    if safe_mapping(data.get("r55_current_received_snapshot_refs")) != P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R54 EV03 R55 current snapshot refs changed")
    if data.get("r55_current_received_snapshot_ref_count") != len(P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError("R54 EV03 R55 current snapshot ref count changed")
    if data.get("r55_current_refs_are_historical_hold_material_here") is not True:
        raise ValueError("R54 EV03 must treat R55 refs as historical hold material here")
    if data.get("r55_current_refs_used_as_actual_review_basis") is not False:
        raise ValueError("R54 EV03 must not use R55 refs as 20260626 actual review basis")
    if data.get("r55_decision_ref") != P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF:
        raise ValueError("R54 EV03 must intake R55 return-to-R54 decision")
    if data.get("r55_decision_status") != P7_R55_DEFAULT_DECISION_STATUS_REF:
        raise ValueError("R54 EV03 R55 decision status changed")
    if data.get("r55_next_required_step") != P7_R55_R52_REINTAKE_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 EV03 R55 next required step changed")
    if data.get("r55_existing_r52_decision_equivalent") != P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF:
        raise ValueError("R54 EV03 R55 R52 equivalent changed")
    if data.get("r55_actual_review_evidence_gap_status_ref") != P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF:
        raise ValueError("R54 EV03 must keep actual review evidence missing gap")
    if data.get("r55_actual_review_evidence_complete") is not False or data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 EV03 must not mark actual review evidence complete")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV03 required case count changed")
    if data.get("rating_row_count_before_review") != 0 or data.get("question_observation_row_count_before_review") != 0:
        raise ValueError("R54 EV03 must keep rating/question rows at zero before review")
    if data.get("disposal_verified_before_review") is not False:
        raise ValueError("R54 EV03 must keep disposal unverified before review")
    if tuple(data.get("missing_evidence_refs") or ()) != P7_R55_DEFAULT_MISSING_EVIDENCE_REFS:
        raise ValueError("R54 EV03 missing evidence refs changed")
    if data.get("missing_evidence_ref_count") != len(P7_R55_DEFAULT_MISSING_EVIDENCE_REFS):
        raise ValueError("R54 EV03 missing evidence ref count changed")
    if data.get("r54_review_operation_state_ref") != P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF:
        raise ValueError("R54 EV03 R54 review operation state changed")
    if data.get("p5_decision_status_ref") != P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF:
        raise ValueError("R54 EV03 P5 decision status changed")
    if data.get("p5_decision_candidate_ref") != P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF:
        raise ValueError("R54 EV03 P5 candidate changed")
    if data.get("p6_hold") is not True or data.get("p8_hold") is not True or data.get("release_hold") is not True:
        raise ValueError("R54 EV03 must keep P6/P8/release holds")
    if data.get("r54_actual_local_only_human_review_operation_required_before_r52_reintake") is not True:
        raise ValueError("R54 EV03 must require R54 actual local-only review before R52 re-intake")
    if data.get("body_full_generation_blocked_until_later_preflight") is not True:
        raise ValueError("R54 EV03 must block body-full generation until later preflight")
    if data.get("body_full_generation_requested_here") is not False:
        raise ValueError("R54 EV03 must not request body-full generation")
    if data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV03 must block actual review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV03 must block P6/P8/release promotion")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_EV03_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV03 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_EV04_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R54 EV03 next required step changed")
    return True


def _ev04_preflight_status_and_reasons(
    *,
    local_review_root_declared: bool,
    explicit_allow_present: bool,
    purge_plan_ready: bool,
    retention_policy_present: bool,
    export_denylist_present: bool,
    export_denylist_violation_refs: Sequence[str],
) -> tuple[str, list[str], list[str]]:
    reason_refs: list[str] = []
    blocker_ids: list[str] = []
    if not local_review_root_declared:
        reason_refs.append("local_review_root_not_declared_or_not_bodyfree_ready")
        blocker_ids.append("review_packet_generation_blocked_missing_local_root")
    if not explicit_allow_present:
        reason_refs.append("explicit_allow_token_ref_missing_or_not_20260626")
        blocker_ids.append("review_packet_generation_blocked_missing_explicit_allow")
    if not purge_plan_ready:
        reason_refs.append("purge_plan_not_ready_for_20260626_local_review")
        blocker_ids.append("review_packet_generation_blocked_missing_purge_plan")
    if not retention_policy_present:
        reason_refs.append("retention_policy_missing_for_20260626_local_review")
        blocker_ids.append("review_packet_generation_blocked_missing_retention_policy")
    if not export_denylist_present:
        reason_refs.append("export_denylist_policy_missing_for_20260626_local_review")
        blocker_ids.append("review_packet_generation_blocked_missing_export_denylist")
    if export_denylist_violation_refs:
        reason_refs.append("export_denylist_violation_detected")
        blocker_ids.append("review_packet_generation_blocked_export_denylist_violation")
    if blocker_ids:
        return (
            P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF,
            dedupe_identifiers(reason_refs, limit=40, max_length=180),
            dedupe_identifiers(blocker_ids, limit=40, max_length=180),
        )
    return P7_R54_EV04_PREFLIGHT_READY_STATUS_REF, [P7_R54_EV04_PREFLIGHT_READY_REASON_REF], []


def _ev05_count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = clean_identifier(row.get(key), max_length=180)
        if value:
            counts[value] = counts.get(value, 0) + 1
    return counts


def _ev05_unique_non_empty(values: Sequence[str]) -> bool:
    return bool(values) and all(values) and len(set(values)) == len(values)


def _ev05_case_refs(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    return [clean_identifier(row.get(key), max_length=180) for row in rows]


def _ev05_controller_manifest_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    controller_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source = safe_mapping(row)
        controller_rows.append(
            {
                "controller_row_ref": f"r54ev05-controller-row-{index:03d}",
                "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
                "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
                "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
                "family": clean_identifier(source.get("family"), max_length=180),
                "case_role": clean_identifier(source.get("case_role"), max_length=180),
                "subscription_tier_ref": clean_identifier(source.get("subscription_tier_ref"), max_length=80),
                "expected_boundary_audit_ref": clean_identifier(source.get("expected_boundary_audit_ref"), max_length=180),
                "case_material_status_ref": clean_identifier(source.get("case_material_status_ref"), max_length=180),
                "history_evidence_policy_ref": clean_identifier(source.get("history_evidence_policy_ref"), max_length=180),
                "controller_only": True,
                "reviewer_facing_family_exposed": False,
                "reviewer_facing_tier_exposed": False,
                "reviewer_facing_case_ref_exposed": False,
                "reviewer_facing_packet_ref_exposed": False,
                "reviewer_facing_expected_result_exposed": False,
                "body_free": True,
            }
        )
    return controller_rows


def _ev05_reviewer_facing_case_index_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    reviewer_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source = safe_mapping(row)
        reviewer_rows.append(
            {
                "reviewer_case_order": index,
                "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
                "reviewer_receives_blind_case_id_only": True,
                "family_exposed": False,
                "tier_exposed": False,
                "case_ref_exposed": False,
                "packet_ref_exposed": False,
                "expected_result_exposed": False,
                "hidden_metadata_exposed": False,
                "body_free": True,
            }
        )
    return reviewer_rows


def _assert_ev05_case_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    required = (
        "case_ref_id",
        "blind_case_id",
        "packet_ref_id",
        "family",
        "case_role",
        "subscription_tier_ref",
        "controller_only",
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "expected_boundary_audit_ref",
        "case_material_status_ref",
        "history_evidence_policy_ref",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "body_free",
    )
    _assert_required_fields(data, required=required, source="p7_r54_ev05_case_row")
    if data.get("controller_only") is not True:
        raise ValueError("R54 EV05 case row must remain controller-only")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV05 case row must keep {false_key}=False")
    if data.get("family") not in P7_R54_EV05_CASE_DISTRIBUTION:
        raise ValueError("R54 EV05 case family changed")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV05 case row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev05_case_row")


def _assert_ev05_controller_manifest_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    required = (
        "controller_row_ref",
        "case_ref_id",
        "blind_case_id",
        "packet_ref_id",
        "family",
        "case_role",
        "subscription_tier_ref",
        "expected_boundary_audit_ref",
        "case_material_status_ref",
        "history_evidence_policy_ref",
        "controller_only",
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "body_free",
    )
    _assert_required_fields(data, required=required, source="p7_r54_ev05_controller_manifest_row")
    if data.get("controller_only") is not True:
        raise ValueError("R54 EV05 controller row must remain controller-only")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV05 controller row must keep {false_key}=False")
    if data.get("family") not in P7_R54_EV05_CASE_DISTRIBUTION:
        raise ValueError("R54 EV05 controller row family changed")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV05 controller row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev05_controller_manifest_row")


def _assert_ev05_reviewer_facing_case_index_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    required = (
        "reviewer_case_order",
        "blind_case_id",
        "reviewer_receives_blind_case_id_only",
        "family_exposed",
        "tier_exposed",
        "case_ref_exposed",
        "packet_ref_exposed",
        "expected_result_exposed",
        "hidden_metadata_exposed",
        "body_free",
    )
    _assert_required_fields(data, required=required, source="p7_r54_ev05_reviewer_facing_case_index_row")
    if data.get("reviewer_receives_blind_case_id_only") is not True:
        raise ValueError("R54 EV05 reviewer row must expose blind case id only")
    for false_key in (
        "family_exposed",
        "tier_exposed",
        "case_ref_exposed",
        "packet_ref_exposed",
        "expected_result_exposed",
        "hidden_metadata_exposed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV05 reviewer row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV05 reviewer row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev05_reviewer_facing_case_index_row")


def build_p7_r54_ev04_local_only_preflight_implementation_confirmation(
    *,
    r55_hold_intake_refreeze: Mapping[str, Any] | None = None,
    local_review_root_presence_ref: Any = None,
    explicit_allow_token_ref: Any = None,
    purge_plan_ref: Any = None,
    retention_policy_ref: Any = None,
    export_denylist_policy_ref: Any = None,
    export_denylist_violation_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r54_ev04_local_only_preflight_implementation_confirmation",
) -> dict[str, Any]:
    """Build EV04 body-free local-only preflight confirmation for the 20260626 basis."""

    ev03 = (
        safe_mapping(r55_hold_intake_refreeze)
        if r55_hold_intake_refreeze is not None
        else build_p7_r54_ev03_r55_hold_intake_refreeze()
    )
    assert_p7_r54_ev03_r55_hold_intake_refreeze_contract(ev03)
    root_presence_ref = clean_identifier(
        local_review_root_presence_ref,
        default=P7_R54_EV04_LOCAL_REVIEW_ROOT_MISSING_REF,
        max_length=220,
    )
    explicit_ref = clean_identifier(
        explicit_allow_token_ref,
        default="missing_explicit_allow_token_ref",
        max_length=220,
    )
    purge_ref = clean_identifier(purge_plan_ref, default="missing_purge_plan_ref", max_length=220)
    retention_ref = clean_identifier(retention_policy_ref, default="missing_retention_policy_ref", max_length=220)
    export_policy_ref = clean_identifier(
        export_denylist_policy_ref,
        default="missing_export_denylist_policy_ref",
        max_length=220,
    )
    deny_refs = dedupe_identifiers(export_denylist_violation_refs, limit=40, max_length=180)

    local_root_declared = root_presence_ref == P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF
    explicit_allow_present = explicit_ref == P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF
    purge_ready = purge_ref == P7_R54_EV04_PURGE_PLAN_READY_REF
    retention_present = retention_ref == P7_R54_EV04_RETENTION_POLICY_READY_REF
    export_denylist_present = export_policy_ref == P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF
    preflight_status, reason_refs, blocker_ids = _ev04_preflight_status_and_reasons(
        local_review_root_declared=local_root_declared,
        explicit_allow_present=explicit_allow_present,
        purge_plan_ready=purge_ready,
        retention_policy_present=retention_present,
        export_denylist_present=export_denylist_present,
        export_denylist_violation_refs=deny_refs,
    )
    ready = preflight_status == P7_R54_EV04_PREFLIGHT_READY_STATUS_REF
    material = {
        "schema_version": P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV04_STEP_REF,
        "operation_step_ref": P7_R54_EV04_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev04_local_only_preflight_implementation_confirmation", max_length=220),
        "review_session_id": _safe_review_session_id(ev03.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev03_schema_version": P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION,
        "ev03_material_ref": clean_identifier(ev03.get("material_id"), default="p7_r54_ev03_r55_hold_intake_refreeze", max_length=220),
        "ev03_next_required_step": clean_identifier(ev03.get("next_required_step"), default=P7_R54_EV04_STEP_REF, max_length=180),
        "ev03_r55_hold_intake_status_ref": clean_identifier(ev03.get("r55_hold_intake_status_ref"), default=P7_R54_EV03_R55_HOLD_INTAKE_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op04_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op04_local_only_preflight",
        "existing_op04_schema_version": r54op.P7_R54_OPERATION_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        "existing_op04_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op04_current_refs_are_historical_here": True,
        "existing_op04_explicit_allow_token_ref": r54op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF,
        "existing_op04_allow_token_is_historical_here": True,
        "existing_op04_reused_as_actual_preflight_basis": False,
        "existing_op04_structural_contract_reused": True,
        "preflight_implementation_status_ref": P7_R54_EV04_PREFLIGHT_IMPLEMENTATION_STATUS_REF,
        "local_review_root_env_var": r54op.P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "local_review_root_presence_ref": root_presence_ref,
        "local_review_root_declared": local_root_declared,
        "local_review_root_outside_repo_export_scope": local_root_declared,
        "local_review_root_path_included": False,
        "local_review_root_path_materialized_here": False,
        "explicit_allow_token_ref": explicit_ref,
        "explicit_allow_present": explicit_allow_present,
        "explicit_allow_token_body_stored_here": False,
        "explicit_allow_token_matches_20260626": explicit_allow_present,
        "purge_plan_ref": purge_ref,
        "purge_plan_present": purge_ref != "missing_purge_plan_ref",
        "purge_plan_ready": purge_ready,
        "purge_plan_required_before_body_full_generation": True,
        "purge_plan_required_delete_target_refs": list(P7_R54_EV04_REQUIRED_DELETE_TARGET_REFS),
        "retention_policy_ref": retention_ref,
        "retention_policy_present": retention_present,
        "body_full_packet_retention_max_hours": r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "delete_trigger_refs": list(r54op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "export_denylist_policy_ref": export_policy_ref,
        "export_denylist_present": export_denylist_present,
        "export_denylist_patterns": list(r54op.P7_R47_EXPORT_DENYLIST_PATTERNS),
        "export_denylist_violation_refs": deny_refs,
        "export_denylist_violation_count": len(deny_refs),
        "preflight_status": preflight_status,
        "preflight_reason_refs": reason_refs,
        "execution_blocker_ids": blocker_ids,
        "open_execution_blocker_ids": blocker_ids,
        "body_full_packet_generation_allowed_before_preflight": False,
        "body_full_packet_generation_allowed_by_preflight": ready,
        "body_full_packet_generation_request_allowed_next": ready,
        "body_full_generation_blocked_until_manifest_freeze": True,
        "body_full_generation_requested_here": False,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "actual_review_evidence_complete": False,
        "r55_hold_preserved": True,
        "p6_hold": True,
        "p8_hold": True,
        "release_hold": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_EV05_STEP_REF if ready else P7_R54_EV04_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material)
    return material


def assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_REQUIRED_FIELD_REFS,
        source="p7_r54_ev04_local_only_preflight_implementation_confirmation",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION,
        policy_section=P7_R54_EV04_STEP_REF,
        operation_step_ref=P7_R54_EV04_STEP_REF,
        source="p7_r54_ev04_local_only_preflight_implementation_confirmation",
    )
    if data.get("ev03_schema_version") != P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R54 EV04 EV03 schema reference changed")
    if data.get("ev03_next_required_step") != P7_R54_EV04_STEP_REF:
        raise ValueError("R54 EV04 must be built after EV03")
    if data.get("ev03_r55_hold_intake_status_ref") != P7_R54_EV03_R55_HOLD_INTAKE_STATUS_REF:
        raise ValueError("R54 EV04 must preserve EV03 R55 hold intake status")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV04 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op04_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV04 existing OP04 refs changed")
    if data.get("existing_op04_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV04 must mark existing OP04 refs historical")
    if data.get("existing_op04_explicit_allow_token_ref") != r54op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF:
        raise ValueError("R54 EV04 existing OP04 allow token reference changed")
    if data.get("existing_op04_allow_token_is_historical_here") is not True:
        raise ValueError("R54 EV04 must mark existing OP04 allow token historical")
    if data.get("existing_op04_reused_as_actual_preflight_basis") is not False:
        raise ValueError("R54 EV04 must not reuse 20260625 OP04 as actual preflight basis")
    if data.get("existing_op04_structural_contract_reused") is not True:
        raise ValueError("R54 EV04 must preserve structural reuse of OP04 contract only")
    if data.get("preflight_implementation_status_ref") != P7_R54_EV04_PREFLIGHT_IMPLEMENTATION_STATUS_REF:
        raise ValueError("R54 EV04 implementation status changed")
    if data.get("local_review_root_env_var") != r54op.P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R54 EV04 local review root env var changed")
    if data.get("local_review_root_path_included") is not False or data.get("local_review_root_path_materialized_here") is not False:
        raise ValueError("R54 EV04 must not include or materialize local paths")
    if data.get("explicit_allow_token_body_stored_here") is not False:
        raise ValueError("R54 EV04 must not store explicit allow token body")
    if data.get("purge_plan_required_before_body_full_generation") is not True:
        raise ValueError("R54 EV04 must require purge before body-full generation")
    if tuple(data.get("purge_plan_required_delete_target_refs") or ()) != P7_R54_EV04_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R54 EV04 purge delete target refs changed")
    if data.get("body_full_packet_retention_max_hours") != r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R54 EV04 body-full packet retention changed")
    if data.get("reviewer_notes_retention_after_rating_finalized_max_hours") != r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R54 EV04 reviewer notes retention changed")
    if tuple(data.get("delete_trigger_refs") or ()) != r54op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R54 EV04 delete trigger refs changed")
    if tuple(data.get("export_denylist_patterns") or ()) != r54op.P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R54 EV04 export denylist patterns changed")
    if data.get("preflight_status") not in P7_R54_EV04_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("R54 EV04 preflight status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV04 open blockers must match execution blockers")
    if data.get("body_full_packet_generation_allowed_before_preflight") is not False:
        raise ValueError("R54 EV04 must block body-full generation before preflight")
    if data.get("body_full_generation_requested_here") is not False:
        raise ValueError("R54 EV04 must not request body-full generation")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV04 required case count changed")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV04 must not materialize rating/question rows")
    if data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 EV04 must not mark actual review evidence complete")
    if data.get("r55_hold_preserved") is not True:
        raise ValueError("R54 EV04 must preserve R55 hold")
    if data.get("p6_hold") is not True or data.get("p8_hold") is not True or data.get("release_hold") is not True:
        raise ValueError("R54 EV04 must preserve P6/P8/release holds")
    if data.get("actual_human_review_completion_claim_blocked_here") is not True or data.get("human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV04 must block review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV04 must block P6/P8/release promotion")
    ready = data.get("preflight_status") == P7_R54_EV04_PREFLIGHT_READY_STATUS_REF
    if ready:
        for key in (
            "local_review_root_declared",
            "local_review_root_outside_repo_export_scope",
            "explicit_allow_present",
            "explicit_allow_token_matches_20260626",
            "purge_plan_ready",
            "retention_policy_present",
            "export_denylist_present",
            "body_full_packet_generation_allowed_by_preflight",
            "body_full_packet_generation_request_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"R54 EV04 ready preflight requires {key}=True")
        if data.get("explicit_allow_token_ref") != P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF:
            raise ValueError("R54 EV04 ready preflight requires the 20260626 explicit allow token")
        if data.get("purge_plan_ref") != P7_R54_EV04_PURGE_PLAN_READY_REF:
            raise ValueError("R54 EV04 ready preflight requires 20260626 purge plan ref")
        if data.get("retention_policy_ref") != P7_R54_EV04_RETENTION_POLICY_READY_REF:
            raise ValueError("R54 EV04 ready preflight requires 20260626 retention policy ref")
        if data.get("export_denylist_policy_ref") != P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF:
            raise ValueError("R54 EV04 ready preflight requires 20260626 export denylist ref")
        if data.get("export_denylist_violation_refs") or data.get("export_denylist_violation_count") != 0:
            raise ValueError("R54 EV04 ready preflight must not contain export denylist violations")
        if blockers:
            raise ValueError("R54 EV04 ready preflight must not carry execution blockers")
        if data.get("preflight_reason_refs") != [P7_R54_EV04_PREFLIGHT_READY_REASON_REF]:
            raise ValueError("R54 EV04 ready preflight reason refs changed")
        if data.get("next_required_step") != P7_R54_EV05_STEP_REF:
            raise ValueError("R54 EV04 ready preflight must point to EV05")
    else:
        if data.get("body_full_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("R54 EV04 blocked preflight must not allow body-full generation")
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("R54 EV04 blocked preflight must not allow packet request next")
        if not blockers or not data.get("preflight_reason_refs"):
            raise ValueError("R54 EV04 blocked preflight must carry blockers and reasons")
        if data.get("next_required_step") != P7_R54_EV04_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV04 blocked preflight must point to local-only repair")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_EV04_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R54 EV04 not-yet steps changed")
    return True


def build_p7_r54_ev05_24_case_manifest_refreeze(
    *,
    local_only_preflight_implementation_confirmation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev05_24_case_manifest_refreeze",
) -> dict[str, Any]:
    """Build EV05 body-free 24-case manifest refreeze after a ready EV04 preflight."""

    ev04 = (
        safe_mapping(local_only_preflight_implementation_confirmation)
        if local_only_preflight_implementation_confirmation is not None
        else build_p7_r54_ev04_local_only_preflight_implementation_confirmation()
    )
    assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract(ev04)
    preflight_ready = ev04.get("preflight_status") == P7_R54_EV04_PREFLIGHT_READY_STATUS_REF
    rows: list[dict[str, Any]] = []
    r48_material_ref = "not_materialized_until_preflight_ready"
    if preflight_ready:
        case_matrix = r54op.build_p7_r48_p5_first_formal_review_case_matrix(
            material_id="p7_r54_ev05_r48_first_formal_case_matrix_basis"
        )
        r54op.assert_p7_r48_p5_first_formal_review_case_matrix_contract(case_matrix)
        r48_material_ref = clean_identifier(
            case_matrix.get("material_id"),
            default="p7_r54_ev05_r48_first_formal_case_matrix_basis",
            max_length=220,
        )
        rows = [dict(safe_mapping(row)) for row in (case_matrix.get("case_rows") or [])]
    family_counts = _ev05_count_by(rows, "family")
    role_counts = _ev05_count_by(rows, "case_role")
    tier_counts = _ev05_count_by(rows, "subscription_tier_ref")
    blind_ids = _ev05_case_refs(rows, "blind_case_id")
    case_refs = _ev05_case_refs(rows, "case_ref_id")
    packet_refs = _ev05_case_refs(rows, "packet_ref_id")
    distribution_matches = bool(preflight_ready and family_counts == P7_R54_EV05_CASE_DISTRIBUTION)
    manifest_ready = bool(
        preflight_ready
        and len(rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and distribution_matches
        and _ev05_unique_non_empty(blind_ids)
        and _ev05_unique_non_empty(case_refs)
        and _ev05_unique_non_empty(packet_refs)
    )
    controller_rows = _ev05_controller_manifest_rows(rows) if manifest_ready else []
    reviewer_rows = _ev05_reviewer_facing_case_index_rows(rows) if manifest_ready else []
    execution_blockers = [] if manifest_ready else dedupe_identifiers(
        ["r54_ev05_blocked_until_20260626_local_only_preflight_ready", *(ev04.get("open_execution_blocker_ids") or [])],
        limit=40,
        max_length=180,
    )
    manifest_reason_refs = (
        ["r54_ev05_24_case_manifest_refrozen_bodyfree_20260626"]
        if manifest_ready
        else dedupe_identifiers(
            ["20260626_local_only_preflight_not_ready_for_24_case_manifest_refreeze", *(ev04.get("preflight_reason_refs") or [])],
            limit=40,
            max_length=180,
        )
    )
    material = {
        "schema_version": P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV05_STEP_REF,
        "operation_step_ref": P7_R54_EV05_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev05_24_case_manifest_refreeze", max_length=220),
        "review_session_id": _safe_review_session_id(ev04.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev04_schema_version": P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION,
        "ev04_material_ref": clean_identifier(ev04.get("material_id"), default="p7_r54_ev04_local_only_preflight_implementation_confirmation", max_length=220),
        "ev04_next_required_step": clean_identifier(ev04.get("next_required_step"), default=P7_R54_EV04_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "ev04_preflight_status": clean_identifier(ev04.get("preflight_status"), default=P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF, max_length=80),
        "ev04_preflight_ready": preflight_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op05_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op05_24_case_manifest_freeze",
        "existing_op05_schema_version": r54op.P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "existing_op05_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op05_current_refs_are_historical_here": True,
        "existing_op05_reused_as_actual_manifest_basis": False,
        "existing_op05_structural_contract_reused": True,
        "r48_case_matrix_schema_version": r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION,
        "r48_case_matrix_material_ref": r48_material_ref,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "case_distribution": dict(P7_R54_EV05_CASE_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_EV05_CASE_DISTRIBUTION.values()),
        "case_distribution_matches_design": distribution_matches,
        "manifest_refreeze_status_ref": P7_R54_EV05_MANIFEST_REFREEZE_STATUS_REF,
        "manifest_status": P7_R54_EV05_MANIFEST_READY_STATUS_REF if manifest_ready else P7_R54_EV05_MANIFEST_BLOCKED_STATUS_REF,
        "manifest_reason_refs": manifest_reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "case_rows": rows if manifest_ready else [],
        "case_count": len(rows) if manifest_ready else 0,
        "family_case_counts": family_counts if manifest_ready else {},
        "case_role_counts": role_counts if manifest_ready else {},
        "subscription_tier_ref_counts": tier_counts if manifest_ready else {},
        "boundary_case_count": (family_counts.get("low_information_history_not_eligible", 0) + family_counts.get("free_tier_history_present_not_allowed", 0)) if manifest_ready else 0,
        "low_information_boundary_case_count": family_counts.get("low_information_history_not_eligible", 0) if manifest_ready else 0,
        "free_tier_boundary_case_count": family_counts.get("free_tier_history_present_not_allowed", 0) if manifest_ready else 0,
        "case_ref_ids": case_refs if manifest_ready else [],
        "blind_case_ids": blind_ids if manifest_ready else [],
        "packet_ref_ids": packet_refs if manifest_ready else [],
        "case_ref_ids_unique": _ev05_unique_non_empty(case_refs) if manifest_ready else False,
        "blind_case_ids_unique": _ev05_unique_non_empty(blind_ids) if manifest_ready else False,
        "packet_ref_ids_unique": _ev05_unique_non_empty(packet_refs) if manifest_ready else False,
        "blind_case_id_case_ref_separated": set(blind_ids).isdisjoint(set(case_refs)) if manifest_ready else False,
        "blind_case_id_packet_ref_separated": set(blind_ids).isdisjoint(set(packet_refs)) if manifest_ready else False,
        "case_ref_id_packet_ref_separated": set(case_refs).isdisjoint(set(packet_refs)) if manifest_ready else False,
        "controller_manifest_rows": controller_rows,
        "reviewer_facing_case_index_rows": reviewer_rows,
        "controller_manifest_row_count": len(controller_rows),
        "reviewer_facing_row_count": len(reviewer_rows),
        "reviewer_identifier_policy_ref": P7_R54_EV05_REVIEWER_IDENTIFIER_POLICY_REF,
        "controller_keeps_family_tier_expected_refs": manifest_ready,
        "reviewer_receives_blind_case_id_only": manifest_ready,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_case_ref_exposed": False,
        "reviewer_facing_packet_ref_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "reviewer_facing_hidden_metadata_exposed": False,
        "p4_r11_rows_mixed_in": False,
        "p4_r11_rows_mixed_in_count": 0,
        "body_full_packet_generation_request_allowed_next": manifest_ready,
        "body_full_generation_blocked_until_request_step": True,
        "body_full_generation_requested_here": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV05_IMPLEMENTED_STEPS if manifest_ready else P7_R54_EV04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_EV05_NOT_YET_IMPLEMENTED_STEPS if manifest_ready else P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_EV06_NEXT_REQUIRED_STEP_REF if manifest_ready else P7_R54_EV05_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material)
    return material


def assert_p7_r54_ev05_24_case_manifest_refreeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r54_ev05_24_case_manifest_refreeze",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_EV05_STEP_REF,
        operation_step_ref=P7_R54_EV05_STEP_REF,
        source="p7_r54_ev05_24_case_manifest_refreeze",
    )
    if data.get("ev04_schema_version") != P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION:
        raise ValueError("R54 EV05 EV04 schema reference changed")
    if data.get("ev04_preflight_status") not in P7_R54_EV04_ALLOWED_PREFLIGHT_STATUS_REFS:
        raise ValueError("R54 EV05 EV04 preflight status reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV05 must use 20260626 operation refs as actual review basis")
    if data.get("existing_op05_schema_version") != r54op.P7_R54_OPERATION_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION:
        raise ValueError("R54 EV05 existing OP05 schema version changed")
    if safe_mapping(data.get("existing_op05_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV05 existing OP05 refs changed")
    if data.get("existing_op05_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV05 must mark existing OP05 refs historical")
    if data.get("existing_op05_reused_as_actual_manifest_basis") is not False:
        raise ValueError("R54 EV05 must not reuse 20260625 OP05 as actual manifest basis")
    if data.get("existing_op05_structural_contract_reused") is not True:
        raise ValueError("R54 EV05 must preserve structural reuse of OP05 contract only")
    if data.get("r48_case_matrix_schema_version") != r54op.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION:
        raise ValueError("R54 EV05 R48 case matrix schema version changed")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV05 required case count changed")
    if data.get("case_distribution") != P7_R54_EV05_CASE_DISTRIBUTION:
        raise ValueError("R54 EV05 case distribution changed")
    if data.get("case_distribution_total_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV05 distribution must total 24 cases")
    if data.get("manifest_refreeze_status_ref") != P7_R54_EV05_MANIFEST_REFREEZE_STATUS_REF:
        raise ValueError("R54 EV05 manifest refreeze status changed")
    if data.get("manifest_status") not in P7_R54_EV05_ALLOWED_MANIFEST_STATUS_REFS:
        raise ValueError("R54 EV05 manifest status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV05 open blockers must match execution blockers")
    if data.get("p4_r11_rows_mixed_in") is not False or data.get("p4_r11_rows_mixed_in_count") != 0:
        raise ValueError("R54 EV05 must not mix P4-R11 rows")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_case_ref_exposed",
        "reviewer_facing_packet_ref_exposed",
        "reviewer_facing_expected_result_exposed",
        "reviewer_facing_hidden_metadata_exposed",
        "body_full_generation_requested_here",
        "body_full_packet_zip_inclusion_allowed",
        "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV05 must keep {false_key}=False")
    if data.get("body_full_generation_blocked_until_request_step") is not True:
        raise ValueError("R54 EV05 must block body-full generation until request step")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 EV05 must not claim actual P5 review ran")
    if data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 EV05 must not mark actual review evidence complete")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV05 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV05 must block human review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV05 must block P6/P8/release promotion")
    rows = [safe_mapping(row) for row in (data.get("case_rows") or [])]
    controller_rows = [safe_mapping(row) for row in (data.get("controller_manifest_rows") or [])]
    reviewer_rows = [safe_mapping(row) for row in (data.get("reviewer_facing_case_index_rows") or [])]
    manifest_ready = data.get("manifest_status") == P7_R54_EV05_MANIFEST_READY_STATUS_REF
    if manifest_ready:
        if data.get("ev04_preflight_status") != P7_R54_EV04_PREFLIGHT_READY_STATUS_REF or data.get("ev04_preflight_ready") is not True:
            raise ValueError("R54 EV05 ready manifest requires EV04 ready preflight")
        if data.get("ev04_next_required_step") != P7_R54_EV05_STEP_REF:
            raise ValueError("R54 EV05 ready manifest must be built after EV04 ready next step")
        if data.get("case_distribution_matches_design") is not True:
            raise ValueError("R54 EV05 ready manifest must match design distribution")
        if len(rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV05 ready manifest must freeze exactly 24 cases")
        for row in rows:
            _assert_ev05_case_row(row)
        if data.get("family_case_counts") != _ev05_count_by(rows, "family"):
            raise ValueError("R54 EV05 family counts changed")
        if data.get("family_case_counts") != P7_R54_EV05_CASE_DISTRIBUTION:
            raise ValueError("R54 EV05 family distribution changed")
        if data.get("case_role_counts") != _ev05_count_by(rows, "case_role"):
            raise ValueError("R54 EV05 role counts changed")
        if data.get("subscription_tier_ref_counts") != _ev05_count_by(rows, "subscription_tier_ref"):
            raise ValueError("R54 EV05 tier counts changed")
        if data.get("boundary_case_count") != 4 or data.get("low_information_boundary_case_count") != 2 or data.get("free_tier_boundary_case_count") != 2:
            raise ValueError("R54 EV05 boundary counts changed")
        blind_ids = _ev05_case_refs(rows, "blind_case_id")
        case_refs = _ev05_case_refs(rows, "case_ref_id")
        packet_refs = _ev05_case_refs(rows, "packet_ref_id")
        if data.get("blind_case_ids") != blind_ids or data.get("case_ref_ids") != case_refs or data.get("packet_ref_ids") != packet_refs:
            raise ValueError("R54 EV05 case id refs changed")
        for key, values in (
            ("blind_case_ids_unique", blind_ids),
            ("case_ref_ids_unique", case_refs),
            ("packet_ref_ids_unique", packet_refs),
        ):
            if data.get(key) is not True or not _ev05_unique_non_empty(values):
                raise ValueError(f"R54 EV05 {key} failed")
        if data.get("blind_case_id_case_ref_separated") is not True or not set(blind_ids).isdisjoint(set(case_refs)):
            raise ValueError("R54 EV05 blind case ids and case refs must be separated")
        if data.get("blind_case_id_packet_ref_separated") is not True or not set(blind_ids).isdisjoint(set(packet_refs)):
            raise ValueError("R54 EV05 blind case ids and packet refs must be separated")
        if data.get("case_ref_id_packet_ref_separated") is not True or not set(case_refs).isdisjoint(set(packet_refs)):
            raise ValueError("R54 EV05 case refs and packet refs must be separated")
        if len(controller_rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("controller_manifest_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV05 controller manifest row count changed")
        for row in controller_rows:
            _assert_ev05_controller_manifest_row(row)
        if len(reviewer_rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("reviewer_facing_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV05 reviewer-facing row count changed")
        for row in reviewer_rows:
            _assert_ev05_reviewer_facing_case_index_row(row)
        if data.get("reviewer_identifier_policy_ref") != P7_R54_EV05_REVIEWER_IDENTIFIER_POLICY_REF:
            raise ValueError("R54 EV05 reviewer identifier policy changed")
        if data.get("controller_keeps_family_tier_expected_refs") is not True:
            raise ValueError("R54 EV05 controller must keep family/tier/expected refs")
        if data.get("reviewer_receives_blind_case_id_only") is not True:
            raise ValueError("R54 EV05 reviewer must receive blind case ids only")
        if data.get("body_full_packet_generation_request_allowed_next") is not True:
            raise ValueError("R54 EV05 ready manifest must allow body-free packet generation request next")
        if data.get("implemented_steps") != list(P7_R54_EV05_IMPLEMENTED_STEPS):
            raise ValueError("R54 EV05 ready implemented steps changed")
        if data.get("not_yet_implemented_steps") != list(P7_R54_EV05_NOT_YET_IMPLEMENTED_STEPS):
            raise ValueError("R54 EV05 ready not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV06_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV05 ready next step changed")
        if blockers:
            raise ValueError("R54 EV05 ready manifest must not carry execution blockers")
    else:
        if data.get("ev04_preflight_ready") is not False:
            raise ValueError("R54 EV05 blocked manifest must record EV04 preflight not ready")
        if rows or controller_rows or reviewer_rows:
            raise ValueError("R54 EV05 blocked manifest must not expose case rows")
        if data.get("case_count") != 0 or data.get("controller_manifest_row_count") != 0 or data.get("reviewer_facing_row_count") != 0:
            raise ValueError("R54 EV05 blocked manifest counts must be zero")
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("R54 EV05 blocked manifest must not allow packet generation request next")
        if not blockers or not data.get("manifest_reason_refs"):
            raise ValueError("R54 EV05 blocked manifest must carry blockers and reasons")
        if data.get("implemented_steps") != list(P7_R54_EV04_IMPLEMENTED_STEPS):
            raise ValueError("R54 EV05 blocked implemented steps must stop at EV04")
        if data.get("not_yet_implemented_steps") != list(P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS):
            raise ValueError("R54 EV05 blocked not-yet steps must keep EV05 pending")
        if data.get("next_required_step") != P7_R54_EV05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV05 blocked next step changed")
    return True


P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev06_body_full_packet_generation_request_bodyfree.v1"
)
P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev07_local_operation_boundary_instruction.bodyfree.v1"
)

P7_R54_EV06_STEP_REF: Final = P7_R54_EV06_NEXT_REQUIRED_STEP_REF
P7_R54_EV07_STEP_REF: Final = "R54-EV-07_local_operation_boundary_instruction"
P7_R54_EV08_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-08_reviewer_selection_form_freeze"
P7_R54_EV06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV05_IMPLEMENTED_STEPS, P7_R54_EV06_STEP_REF)
P7_R54_EV06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV07_STEP_REF,)
P7_R54_EV07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV06_IMPLEMENTED_STEPS, P7_R54_EV07_STEP_REF)
P7_R54_EV07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV08_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV06_REQUEST_READY_STATUS_REF: Final = "PACKET_GENERATION_REQUEST_BODYFREE_READY_20260626"
P7_R54_EV06_REQUEST_BLOCKED_STATUS_REF: Final = "PACKET_GENERATION_REQUEST_BLOCKED_BY_EV05_MANIFEST"
P7_R54_EV06_ALLOWED_REQUEST_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV06_REQUEST_READY_STATUS_REF,
    P7_R54_EV06_REQUEST_BLOCKED_STATUS_REF,
)
P7_R54_EV06_PACKET_GENERATION_REQUEST_REF: Final = (
    "r54_ev06_local_only_body_full_packet_generation_request_bodyfree_20260626"
)
P7_R54_EV06_PACKET_GENERATION_REQUEST_POLICY_REF: Final = (
    "packet_generation_request_is_bodyfree_refs_only_no_packet_content_20260626"
)
P7_R54_EV06_ALLOWED_OUTPUT_REF: Final = "local_only_body_full_packet"
P7_R54_EV06_READY_REASON_REF: Final = "r54_ev06_bodyfree_packet_generation_request_ready_after_20260626_manifest"
P7_R54_EV06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev06_blocked_until_ev05_24_case_manifest_ready"
P7_R54_EV06_REQUEST_STATUS_REF: Final = "R54_EV06_BODYFREE_PACKET_GENERATION_REQUEST_REFROZEN"
P7_R54_EV06_FORBIDDEN_OUTPUT_REFS: Final[tuple[str, ...]] = (
    "artifact_zip",
    "release_material",
    "public_meta",
    "repo_docs",
    "test_fixture",
    "premise_materials",
    "implemented_materials",
    "patch_delivery_zip",
)

P7_R54_EV07_INSTRUCTION_READY_STATUS_REF: Final = "LOCAL_OPERATION_BOUNDARY_INSTRUCTION_READY_BODYFREE_20260626"
P7_R54_EV07_INSTRUCTION_BLOCKED_STATUS_REF: Final = "LOCAL_OPERATION_BOUNDARY_INSTRUCTION_BLOCKED_BY_EV06_REQUEST"
P7_R54_EV07_ALLOWED_INSTRUCTION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV07_INSTRUCTION_READY_STATUS_REF,
    P7_R54_EV07_INSTRUCTION_BLOCKED_STATUS_REF,
)
P7_R54_EV07_INSTRUCTION_REF: Final = "r54_ev07_local_operation_boundary_instruction_bodyfree_20260626"
P7_R54_EV07_INSTRUCTION_POLICY_REF: Final = "local_operation_instruction_is_bodyfree_no_paths_no_packet_content_20260626"
P7_R54_EV07_READY_REASON_REF: Final = "r54_ev07_local_operation_boundary_instruction_ready_after_bodyfree_request"
P7_R54_EV07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev07_blocked_until_ev06_bodyfree_packet_generation_request_ready"
P7_R54_EV07_BOUNDARY_STATUS_REF: Final = "R54_EV07_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_FROZEN"
P7_R54_EV07_ALLOWED_LOCAL_OPERATION_SCOPE_REFS: Final[tuple[str, ...]] = (
    "use_external_local_review_root_only",
    "generate_body_full_packets_only_after_ev06_request",
    "use_ev06_packet_ref_ids_without_body_payload_export",
    "keep_reviewer_notes_local_only_until_disposal",
    "record_only_bodyfree_receipt_later",
)
P7_R54_EV07_FORBIDDEN_LOCAL_OPERATION_REFS: Final[tuple[str, ...]] = (
    "write_body_full_packet_to_repo",
    "write_body_full_packet_to_artifact",
    "write_body_full_packet_to_release_material",
    "write_reviewer_notes_to_artifact",
    "store_local_absolute_path_in_evidence",
    "store_body_hash_in_evidence",
    "store_question_text_or_draft_question",
)

P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev05_schema_version",
    "ev05_material_ref",
    "ev05_next_required_step",
    "ev05_manifest_status",
    "ev05_manifest_ready",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op06_helper_ref",
    "existing_op06_schema_version",
    "existing_op06_operation_current_refs",
    "existing_op06_current_refs_are_historical_here",
    "existing_op06_reused_as_actual_request_basis",
    "existing_op06_structural_contract_reused",
    "required_case_count",
    "ev05_case_count",
    "ev05_controller_manifest_row_count",
    "ev05_reviewer_facing_row_count",
    "packet_generation_request_status",
    "packet_generation_request_status_ref",
    "packet_generation_request_ref",
    "packet_generation_request_policy_ref",
    "packet_generation_request_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "packet_request_count",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "packet_generation_request_rows",
    "packet_generation_request_row_count",
    "allowed_output_ref",
    "forbidden_output_refs",
    "forbidden_output_ref_count",
    "export_denylist_policy_ref",
    "export_denylist_patterns",
    "export_denylist_pattern_count",
    "request_is_bodyfree_only",
    "request_contains_packet_content",
    "request_contains_local_path",
    "request_contains_body_hash",
    "request_contains_raw_input",
    "request_contains_returned_body",
    "request_contains_history_surface",
    "request_contains_reviewer_free_text",
    "request_contains_question_text",
    "body_full_packet_generation_request_materialized_here",
    "body_full_packet_generation_local_operation_started_here",
    "body_full_packet_generated_here",
    "body_full_packet_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "reviewer_notes_export_allowed",
    "local_review_root_path_included",
    "local_packet_directory_path_included",
    "body_full_packet_content_included",
    "local_operation_boundary_instruction_allowed_next",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev06_schema_version",
    "ev06_material_ref",
    "ev06_next_required_step",
    "ev06_packet_generation_request_status",
    "ev06_request_ready",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op07_helper_ref",
    "existing_op07_schema_version",
    "existing_op07_operation_current_refs",
    "existing_op07_current_refs_are_historical_here",
    "existing_op07_reused_as_actual_local_operation_basis",
    "existing_op07_structural_contract_reused",
    "required_case_count",
    "local_operation_boundary_instruction_status",
    "local_operation_boundary_status_ref",
    "local_operation_boundary_instruction_ref",
    "local_operation_boundary_instruction_policy_ref",
    "local_operation_boundary_instruction_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "packet_ref_ids_for_local_operation",
    "packet_ref_count_for_local_operation",
    "packet_ref_ids_for_local_operation_unique",
    "local_operation_instruction_rows",
    "local_operation_instruction_row_count",
    "allowed_local_operation_scope_refs",
    "allowed_local_operation_scope_ref_count",
    "forbidden_local_operation_refs",
    "forbidden_local_operation_ref_count",
    "forbidden_output_refs",
    "forbidden_output_ref_count",
    "local_review_root_env_var",
    "local_review_root_path_included",
    "local_review_root_path_materialized_here",
    "local_packet_directory_path_included",
    "local_packet_directory_path_materialized_here",
    "export_denylist_policy_ref",
    "export_denylist_patterns",
    "export_denylist_pattern_count",
    "retention_policy_ref",
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_finalized_max_hours",
    "delete_trigger_refs",
    "delete_trigger_ref_count",
    "body_full_packet_generation_may_be_run_after_this_instruction",
    "body_full_packet_generation_run_here",
    "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here",
    "local_reviewer_payload_materialized_here",
    "local_operation_receipt_materialized_here",
    "local_operation_receipt_required_after_external_run",
    "local_operation_receipt_body_stored_here",
    "body_full_packet_content_included",
    "body_full_packet_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "reviewer_notes_export_allowed",
    "external_local_body_full_packet_generation_required_before_actual_review",
    "body_full_packet_generation_not_performed_by_helper",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev06_packet_ref_ids_from_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return [clean_identifier(row.get("packet_ref_id"), max_length=180) for row in rows]


def _ev06_packet_generation_request_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    request_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        data = safe_mapping(row)
        request_rows.append(
            {
                "packet_request_row_ref": f"r54ev06-packet-request-row-{index:03d}",
                "case_ref_id": clean_identifier(data.get("case_ref_id"), max_length=180),
                "blind_case_id": clean_identifier(data.get("blind_case_id"), max_length=180),
                "packet_ref_id": clean_identifier(data.get("packet_ref_id"), max_length=180),
                "family": clean_identifier(data.get("family"), max_length=120),
                "case_role": clean_identifier(data.get("case_role"), max_length=160),
                "subscription_tier_ref": clean_identifier(data.get("subscription_tier_ref"), max_length=120),
                "case_material_status_ref": clean_identifier(data.get("case_material_status_ref"), default="case_material_bodyfree_ref_ready", max_length=160),
                "packet_generation_requested": True,
                "request_is_bodyfree_only": True,
                "allowed_output_ref": P7_R54_EV06_ALLOWED_OUTPUT_REF,
                "forbidden_output_refs": list(P7_R54_EV06_FORBIDDEN_OUTPUT_REFS),
                "packet_content_included": False,
                "raw_body_included": False,
                "returned_body_included": False,
                "history_surface_included": False,
                "reviewer_free_text_included": False,
                "local_path_included": False,
                "body_hash_included": False,
                "question_text_included": False,
                "body_free": True,
            }
        )
    return request_rows


def _assert_ev06_packet_generation_request_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    required = (
        "packet_request_row_ref",
        "case_ref_id",
        "blind_case_id",
        "packet_ref_id",
        "family",
        "case_role",
        "subscription_tier_ref",
        "case_material_status_ref",
        "packet_generation_requested",
        "request_is_bodyfree_only",
        "allowed_output_ref",
        "forbidden_output_refs",
        "packet_content_included",
        "raw_body_included",
        "returned_body_included",
        "history_surface_included",
        "reviewer_free_text_included",
        "local_path_included",
        "body_hash_included",
        "question_text_included",
        "body_free",
    )
    _assert_required_fields(data, required=required, source="p7_r54_ev06_packet_generation_request_row")
    if data.get("packet_generation_requested") is not True or data.get("request_is_bodyfree_only") is not True:
        raise ValueError("R54 EV06 packet request row must be a body-free request")
    if data.get("allowed_output_ref") != P7_R54_EV06_ALLOWED_OUTPUT_REF:
        raise ValueError("R54 EV06 packet request row output scope changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_EV06_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("R54 EV06 packet request row forbidden outputs changed")
    for false_key in (
        "packet_content_included",
        "raw_body_included",
        "returned_body_included",
        "history_surface_included",
        "reviewer_free_text_included",
        "local_path_included",
        "body_hash_included",
        "question_text_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV06 packet request row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV06 packet request row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev06_packet_generation_request_row")


def build_p7_r54_ev06_body_full_packet_generation_request_bodyfree(
    *,
    case_manifest_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev06_body_full_packet_generation_request_bodyfree",
) -> dict[str, Any]:
    """Build EV06 body-free packet generation request refs without packet content."""

    ev05 = (
        safe_mapping(case_manifest_refreeze)
        if case_manifest_refreeze is not None
        else build_p7_r54_ev05_24_case_manifest_refreeze()
    )
    assert_p7_r54_ev05_24_case_manifest_refreeze_contract(ev05)
    manifest_ready = ev05.get("manifest_status") == P7_R54_EV05_MANIFEST_READY_STATUS_REF
    case_rows = [safe_mapping(row) for row in (ev05.get("case_rows") or [])] if manifest_ready else []
    packet_ref_ids = _ev06_packet_ref_ids_from_rows(case_rows) if manifest_ready else []
    request_rows = _ev06_packet_generation_request_rows(case_rows) if manifest_ready else []
    request_ready = bool(
        manifest_ready
        and ev05.get("body_full_packet_generation_request_allowed_next") is True
        and len(packet_ref_ids) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and _ev05_unique_non_empty(packet_ref_ids)
        and len(request_rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    execution_blockers = [] if request_ready else dedupe_identifiers(
        ["r54_ev06_blocked_until_24_case_manifest_ready", *(ev05.get("open_execution_blocker_ids") or [])],
        limit=40,
        max_length=180,
    )
    reason_refs = [P7_R54_EV06_READY_REASON_REF] if request_ready else dedupe_identifiers(
        ["ev05_manifest_not_ready_for_bodyfree_packet_generation_request", *(ev05.get("manifest_reason_refs") or [])],
        limit=40,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV06_STEP_REF,
        "operation_step_ref": P7_R54_EV06_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev06_body_full_packet_generation_request_bodyfree", max_length=220),
        "review_session_id": _safe_review_session_id(ev05.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev05_schema_version": P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        "ev05_material_ref": clean_identifier(ev05.get("material_id"), default="p7_r54_ev05_24_case_manifest_refreeze", max_length=240),
        "ev05_next_required_step": clean_identifier(ev05.get("next_required_step"), default=P7_R54_EV05_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev05_manifest_status": clean_identifier(ev05.get("manifest_status"), default=P7_R54_EV05_MANIFEST_BLOCKED_STATUS_REF, max_length=160),
        "ev05_manifest_ready": manifest_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op06_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op06_local_only_body_full_packet_generation_request",
        "existing_op06_schema_version": r54op.P7_R54_OPERATION_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "existing_op06_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op06_current_refs_are_historical_here": True,
        "existing_op06_reused_as_actual_request_basis": False,
        "existing_op06_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "ev05_case_count": int(ev05.get("case_count") or 0),
        "ev05_controller_manifest_row_count": int(ev05.get("controller_manifest_row_count") or 0),
        "ev05_reviewer_facing_row_count": int(ev05.get("reviewer_facing_row_count") or 0),
        "packet_generation_request_status": P7_R54_EV06_REQUEST_READY_STATUS_REF if request_ready else P7_R54_EV06_REQUEST_BLOCKED_STATUS_REF,
        "packet_generation_request_status_ref": P7_R54_EV06_REQUEST_STATUS_REF,
        "packet_generation_request_ref": P7_R54_EV06_PACKET_GENERATION_REQUEST_REF if request_ready else "not_requested_until_ev05_manifest_ready",
        "packet_generation_request_policy_ref": P7_R54_EV06_PACKET_GENERATION_REQUEST_POLICY_REF,
        "packet_generation_request_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "packet_request_count": len(packet_ref_ids) if request_ready else 0,
        "packet_ref_ids": packet_ref_ids if request_ready else [],
        "packet_ref_count": len(packet_ref_ids) if request_ready else 0,
        "packet_ref_ids_unique": _ev05_unique_non_empty(packet_ref_ids) if request_ready else False,
        "packet_generation_request_rows": request_rows if request_ready else [],
        "packet_generation_request_row_count": len(request_rows) if request_ready else 0,
        "allowed_output_ref": P7_R54_EV06_ALLOWED_OUTPUT_REF,
        "forbidden_output_refs": list(P7_R54_EV06_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_EV06_FORBIDDEN_OUTPUT_REFS),
        "export_denylist_policy_ref": P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF,
        "export_denylist_patterns": list(r54op.P7_R47_EXPORT_DENYLIST_PATTERNS),
        "export_denylist_pattern_count": len(r54op.P7_R47_EXPORT_DENYLIST_PATTERNS),
        "request_is_bodyfree_only": True,
        "request_contains_packet_content": False,
        "request_contains_local_path": False,
        "request_contains_body_hash": False,
        "request_contains_raw_input": False,
        "request_contains_returned_body": False,
        "request_contains_history_surface": False,
        "request_contains_reviewer_free_text": False,
        "request_contains_question_text": False,
        "body_full_packet_generation_request_materialized_here": request_ready,
        "body_full_packet_generation_local_operation_started_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "local_review_root_path_included": False,
        "local_packet_directory_path_included": False,
        "body_full_packet_content_included": False,
        "local_operation_boundary_instruction_allowed_next": request_ready,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV06_IMPLEMENTED_STEPS if request_ready else (ev05.get("implemented_steps") or P7_R54_EV05_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV06_NOT_YET_IMPLEMENTED_STEPS if request_ready else (ev05.get("not_yet_implemented_steps") or P7_R54_EV05_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV07_STEP_REF if request_ready else P7_R54_EV06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material)
    return material


def assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_REQUIRED_FIELD_REFS,
        source="p7_r54_ev06_body_full_packet_generation_request_bodyfree",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION,
        policy_section=P7_R54_EV06_STEP_REF,
        operation_step_ref=P7_R54_EV06_STEP_REF,
        source="p7_r54_ev06_body_full_packet_generation_request_bodyfree",
    )
    if data.get("ev05_schema_version") != P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R54 EV06 EV05 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV06 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op06_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV06 existing OP06 refs changed")
    if data.get("existing_op06_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV06 must classify existing OP06 refs as historical")
    if data.get("existing_op06_reused_as_actual_request_basis") is not False:
        raise ValueError("R54 EV06 must not reuse 20260625 OP06 as actual request basis")
    if data.get("existing_op06_structural_contract_reused") is not True:
        raise ValueError("R54 EV06 must reuse only OP06 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV06 required case count changed")
    if data.get("packet_generation_request_status") not in P7_R54_EV06_ALLOWED_REQUEST_STATUS_REFS:
        raise ValueError("R54 EV06 request status changed")
    if data.get("packet_generation_request_status_ref") != P7_R54_EV06_REQUEST_STATUS_REF:
        raise ValueError("R54 EV06 request status ref changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV06 open blockers must match execution blockers")
    if data.get("allowed_output_ref") != P7_R54_EV06_ALLOWED_OUTPUT_REF:
        raise ValueError("R54 EV06 allowed output ref changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_EV06_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("R54 EV06 forbidden output refs changed")
    if data.get("forbidden_output_ref_count") != len(P7_R54_EV06_FORBIDDEN_OUTPUT_REFS):
        raise ValueError("R54 EV06 forbidden output ref count changed")
    if data.get("export_denylist_policy_ref") != P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF:
        raise ValueError("R54 EV06 export denylist policy ref changed")
    if tuple(data.get("export_denylist_patterns") or ()) != r54op.P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R54 EV06 export denylist patterns changed")
    if data.get("export_denylist_pattern_count") != len(r54op.P7_R47_EXPORT_DENYLIST_PATTERNS):
        raise ValueError("R54 EV06 export denylist pattern count changed")
    for false_key in (
        "request_contains_packet_content",
        "request_contains_local_path",
        "request_contains_body_hash",
        "request_contains_raw_input",
        "request_contains_returned_body",
        "request_contains_history_surface",
        "request_contains_reviewer_free_text",
        "request_contains_question_text",
        "body_full_packet_generation_local_operation_started_here",
        "body_full_packet_generated_here",
        "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "local_review_root_path_included",
        "local_packet_directory_path_included",
        "body_full_packet_content_included",
        "actual_review_evidence_complete",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV06 must keep {false_key}=False")
    if data.get("request_is_bodyfree_only") is not True:
        raise ValueError("R54 EV06 request must be body-free only")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 EV06 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV06 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV06 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV06 must block P6/P8/release promotion")
    request_ready = data.get("packet_generation_request_status") == P7_R54_EV06_REQUEST_READY_STATUS_REF
    if request_ready:
        if data.get("ev05_manifest_ready") is not True or data.get("ev05_next_required_step") != P7_R54_EV06_STEP_REF:
            raise ValueError("R54 EV06 ready request requires EV05 ready manifest")
        for count_key in ("ev05_case_count", "ev05_controller_manifest_row_count", "ev05_reviewer_facing_row_count"):
            if data.get(count_key) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"R54 EV06 ready request requires {count_key}=24")
        packet_refs = [clean_identifier(item, max_length=180) for item in (data.get("packet_ref_ids") or [])]
        request_rows = [safe_mapping(row) for row in (data.get("packet_generation_request_rows") or [])]
        if data.get("packet_generation_request_ref") != P7_R54_EV06_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("R54 EV06 packet request ref changed")
        if data.get("packet_generation_request_policy_ref") != P7_R54_EV06_PACKET_GENERATION_REQUEST_POLICY_REF:
            raise ValueError("R54 EV06 request policy ref changed")
        if data.get("packet_generation_request_reason_refs") != [P7_R54_EV06_READY_REASON_REF]:
            raise ValueError("R54 EV06 ready reason refs changed")
        if blockers:
            raise ValueError("R54 EV06 ready request must not carry execution blockers")
        if data.get("packet_request_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV06 packet request count changed")
        if data.get("packet_ref_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or len(packet_refs) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV06 packet ref count changed")
        if data.get("packet_ref_ids_unique") is not True or not _ev05_unique_non_empty(packet_refs):
            raise ValueError("R54 EV06 packet refs must be unique")
        if len(request_rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("packet_generation_request_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV06 request row count changed")
        for row in request_rows:
            _assert_ev06_packet_generation_request_row(row)
        if [row.get("packet_ref_id") for row in request_rows] != packet_refs:
            raise ValueError("R54 EV06 request rows must match packet refs")
        if data.get("body_full_packet_generation_request_materialized_here") is not True:
            raise ValueError("R54 EV06 ready request must materialize body-free request refs")
        if data.get("local_operation_boundary_instruction_allowed_next") is not True:
            raise ValueError("R54 EV06 ready request must allow EV07 instruction next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV06_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV07_STEP_REF:
            raise ValueError("R54 EV06 ready request must point to EV07")
    else:
        if data.get("packet_request_count") != 0 or data.get("packet_ref_ids") != [] or data.get("packet_generation_request_rows") != []:
            raise ValueError("R54 EV06 blocked request must not expose packet request refs")
        if data.get("body_full_packet_generation_request_materialized_here") is not False:
            raise ValueError("R54 EV06 blocked request must not materialize request refs")
        if data.get("local_operation_boundary_instruction_allowed_next") is not False:
            raise ValueError("R54 EV06 blocked request must not allow EV07 instruction")
        if not blockers:
            raise ValueError("R54 EV06 blocked request must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV06 blocked request next step changed")
    return True


def _ev07_local_operation_instruction_rows(packet_ref_ids: Sequence[Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(packet_ref_ids, start=1):
        packet_ref = clean_identifier(item, max_length=180)
        rows.append(
            {
                "local_operation_instruction_row_ref": f"r54ev07-local-operation-row-{index:03d}",
                "packet_ref_id": packet_ref,
                "local_operation_scope_ref": "external_local_only_body_full_packet_generation",
                "packet_generation_may_be_run_after_instruction": True,
                "packet_generation_run_here": False,
                "packet_content_included": False,
                "local_path_included": False,
                "body_hash_included": False,
                "question_text_included": False,
                "body_free": True,
            }
        )
    return rows


def _assert_ev07_local_operation_instruction_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    required = (
        "local_operation_instruction_row_ref",
        "packet_ref_id",
        "local_operation_scope_ref",
        "packet_generation_may_be_run_after_instruction",
        "packet_generation_run_here",
        "packet_content_included",
        "local_path_included",
        "body_hash_included",
        "question_text_included",
        "body_free",
    )
    _assert_required_fields(data, required=required, source="p7_r54_ev07_local_operation_instruction_row")
    if data.get("packet_generation_may_be_run_after_instruction") is not True:
        raise ValueError("R54 EV07 instruction row must allow only later local generation")
    for false_key in ("packet_generation_run_here", "packet_content_included", "local_path_included", "body_hash_included", "question_text_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV07 instruction row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV07 instruction row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev07_local_operation_instruction_row")


def build_p7_r54_ev07_local_operation_boundary_instruction(
    *,
    body_full_packet_generation_request_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev07_local_operation_boundary_instruction",
) -> dict[str, Any]:
    """Build EV07 body-free local operation boundary instructions without local paths or packets."""

    ev06 = (
        safe_mapping(body_full_packet_generation_request_bodyfree)
        if body_full_packet_generation_request_bodyfree is not None
        else build_p7_r54_ev06_body_full_packet_generation_request_bodyfree()
    )
    assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract(ev06)
    request_ready = ev06.get("packet_generation_request_status") == P7_R54_EV06_REQUEST_READY_STATUS_REF
    packet_refs = [clean_identifier(item, max_length=180) for item in (ev06.get("packet_ref_ids") or [])] if request_ready else []
    instruction_rows = _ev07_local_operation_instruction_rows(packet_refs) if request_ready else []
    instruction_ready = bool(
        request_ready
        and ev06.get("local_operation_boundary_instruction_allowed_next") is True
        and len(packet_refs) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and _ev05_unique_non_empty(packet_refs)
        and len(instruction_rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    execution_blockers = [] if instruction_ready else dedupe_identifiers(
        ["r54_ev07_blocked_until_ev06_bodyfree_packet_generation_request_ready", *(ev06.get("open_execution_blocker_ids") or [])],
        limit=40,
        max_length=180,
    )
    reason_refs = [P7_R54_EV07_READY_REASON_REF] if instruction_ready else dedupe_identifiers(
        ["ev06_bodyfree_packet_generation_request_not_ready_for_local_operation_instruction", *(ev06.get("packet_generation_request_reason_refs") or [])],
        limit=40,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV07_STEP_REF,
        "operation_step_ref": P7_R54_EV07_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev07_local_operation_boundary_instruction", max_length=220),
        "review_session_id": _safe_review_session_id(ev06.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev06_schema_version": P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION,
        "ev06_material_ref": clean_identifier(ev06.get("material_id"), default="p7_r54_ev06_body_full_packet_generation_request_bodyfree", max_length=240),
        "ev06_next_required_step": clean_identifier(ev06.get("next_required_step"), default=P7_R54_EV06_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev06_packet_generation_request_status": clean_identifier(ev06.get("packet_generation_request_status"), default=P7_R54_EV06_REQUEST_BLOCKED_STATUS_REF, max_length=160),
        "ev06_request_ready": request_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op07_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op07_packet_generation_local_operation",
        "existing_op07_schema_version": r54op.P7_R54_OPERATION_PACKET_GENERATION_LOCAL_OPERATION_SCHEMA_VERSION,
        "existing_op07_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op07_current_refs_are_historical_here": True,
        "existing_op07_reused_as_actual_local_operation_basis": False,
        "existing_op07_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "local_operation_boundary_instruction_status": P7_R54_EV07_INSTRUCTION_READY_STATUS_REF if instruction_ready else P7_R54_EV07_INSTRUCTION_BLOCKED_STATUS_REF,
        "local_operation_boundary_status_ref": P7_R54_EV07_BOUNDARY_STATUS_REF,
        "local_operation_boundary_instruction_ref": P7_R54_EV07_INSTRUCTION_REF if instruction_ready else "not_frozen_until_ev06_request_ready",
        "local_operation_boundary_instruction_policy_ref": P7_R54_EV07_INSTRUCTION_POLICY_REF,
        "local_operation_boundary_instruction_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "packet_ref_ids_for_local_operation": packet_refs if instruction_ready else [],
        "packet_ref_count_for_local_operation": len(packet_refs) if instruction_ready else 0,
        "packet_ref_ids_for_local_operation_unique": _ev05_unique_non_empty(packet_refs) if instruction_ready else False,
        "local_operation_instruction_rows": instruction_rows if instruction_ready else [],
        "local_operation_instruction_row_count": len(instruction_rows) if instruction_ready else 0,
        "allowed_local_operation_scope_refs": list(P7_R54_EV07_ALLOWED_LOCAL_OPERATION_SCOPE_REFS),
        "allowed_local_operation_scope_ref_count": len(P7_R54_EV07_ALLOWED_LOCAL_OPERATION_SCOPE_REFS),
        "forbidden_local_operation_refs": list(P7_R54_EV07_FORBIDDEN_LOCAL_OPERATION_REFS),
        "forbidden_local_operation_ref_count": len(P7_R54_EV07_FORBIDDEN_LOCAL_OPERATION_REFS),
        "forbidden_output_refs": list(P7_R54_EV06_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_EV06_FORBIDDEN_OUTPUT_REFS),
        "local_review_root_env_var": r54op.P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR,
        "local_review_root_path_included": False,
        "local_review_root_path_materialized_here": False,
        "local_packet_directory_path_included": False,
        "local_packet_directory_path_materialized_here": False,
        "export_denylist_policy_ref": P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF,
        "export_denylist_patterns": list(r54op.P7_R47_EXPORT_DENYLIST_PATTERNS),
        "export_denylist_pattern_count": len(r54op.P7_R47_EXPORT_DENYLIST_PATTERNS),
        "retention_policy_ref": P7_R54_EV04_RETENTION_POLICY_READY_REF,
        "body_full_packet_retention_max_hours": r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_finalized_max_hours": r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "delete_trigger_refs": list(r54op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "delete_trigger_ref_count": len(r54op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS),
        "body_full_packet_generation_may_be_run_after_this_instruction": instruction_ready,
        "body_full_packet_generation_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_body_full_packet_generated_here": False,
        "local_reviewer_payload_materialized_here": False,
        "local_operation_receipt_materialized_here": False,
        "local_operation_receipt_required_after_external_run": instruction_ready,
        "local_operation_receipt_body_stored_here": False,
        "body_full_packet_content_included": False,
        "body_full_packet_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "external_local_body_full_packet_generation_required_before_actual_review": instruction_ready,
        "body_full_packet_generation_not_performed_by_helper": True,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV07_IMPLEMENTED_STEPS if instruction_ready else (ev06.get("implemented_steps") or P7_R54_EV06_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV07_NOT_YET_IMPLEMENTED_STEPS if instruction_ready else (ev06.get("not_yet_implemented_steps") or P7_R54_EV06_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV08_NEXT_REQUIRED_STEP_REF if instruction_ready else P7_R54_EV07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material)
    return material


def assert_p7_r54_ev07_local_operation_boundary_instruction_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_REQUIRED_FIELD_REFS,
        source="p7_r54_ev07_local_operation_boundary_instruction",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION,
        policy_section=P7_R54_EV07_STEP_REF,
        operation_step_ref=P7_R54_EV07_STEP_REF,
        source="p7_r54_ev07_local_operation_boundary_instruction",
    )
    if data.get("ev06_schema_version") != P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R54 EV07 EV06 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV07 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op07_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV07 existing OP07 refs changed")
    if data.get("existing_op07_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV07 must classify existing OP07 refs as historical")
    if data.get("existing_op07_reused_as_actual_local_operation_basis") is not False:
        raise ValueError("R54 EV07 must not reuse 20260625 OP07 as actual operation basis")
    if data.get("existing_op07_structural_contract_reused") is not True:
        raise ValueError("R54 EV07 must reuse only OP07 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV07 required case count changed")
    if data.get("local_operation_boundary_instruction_status") not in P7_R54_EV07_ALLOWED_INSTRUCTION_STATUS_REFS:
        raise ValueError("R54 EV07 instruction status changed")
    if data.get("local_operation_boundary_status_ref") != P7_R54_EV07_BOUNDARY_STATUS_REF:
        raise ValueError("R54 EV07 boundary status ref changed")
    if data.get("local_operation_boundary_instruction_policy_ref") != P7_R54_EV07_INSTRUCTION_POLICY_REF:
        raise ValueError("R54 EV07 instruction policy ref changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV07 open blockers must match execution blockers")
    if tuple(data.get("allowed_local_operation_scope_refs") or ()) != P7_R54_EV07_ALLOWED_LOCAL_OPERATION_SCOPE_REFS:
        raise ValueError("R54 EV07 allowed local operation scope refs changed")
    if data.get("allowed_local_operation_scope_ref_count") != len(P7_R54_EV07_ALLOWED_LOCAL_OPERATION_SCOPE_REFS):
        raise ValueError("R54 EV07 local operation scope count changed")
    if tuple(data.get("forbidden_local_operation_refs") or ()) != P7_R54_EV07_FORBIDDEN_LOCAL_OPERATION_REFS:
        raise ValueError("R54 EV07 forbidden local operation refs changed")
    if data.get("forbidden_local_operation_ref_count") != len(P7_R54_EV07_FORBIDDEN_LOCAL_OPERATION_REFS):
        raise ValueError("R54 EV07 forbidden local operation ref count changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_EV06_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("R54 EV07 forbidden output refs changed")
    if data.get("local_review_root_env_var") != r54op.P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR:
        raise ValueError("R54 EV07 local review root env var changed")
    if tuple(data.get("export_denylist_patterns") or ()) != r54op.P7_R47_EXPORT_DENYLIST_PATTERNS:
        raise ValueError("R54 EV07 export denylist patterns changed")
    if data.get("retention_policy_ref") != P7_R54_EV04_RETENTION_POLICY_READY_REF:
        raise ValueError("R54 EV07 retention policy ref changed")
    if data.get("body_full_packet_retention_max_hours") != r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS:
        raise ValueError("R54 EV07 body-full packet retention changed")
    if data.get("reviewer_notes_retention_after_rating_finalized_max_hours") != r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS:
        raise ValueError("R54 EV07 reviewer notes retention changed")
    if tuple(data.get("delete_trigger_refs") or ()) != r54op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS:
        raise ValueError("R54 EV07 delete trigger refs changed")
    for false_key in (
        "local_review_root_path_included",
        "local_review_root_path_materialized_here",
        "local_packet_directory_path_included",
        "local_packet_directory_path_materialized_here",
        "body_full_packet_generation_run_here",
        "body_full_packet_generated_here",
        "actual_body_full_packet_generated_here",
        "local_reviewer_payload_materialized_here",
        "local_operation_receipt_materialized_here",
        "local_operation_receipt_body_stored_here",
        "body_full_packet_content_included",
        "body_full_packet_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "actual_review_evidence_complete",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV07 must keep {false_key}=False")
    if data.get("body_full_packet_generation_not_performed_by_helper") is not True:
        raise ValueError("R54 EV07 must not perform packet generation inside helper")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 EV07 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV07 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV07 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV07 must block P6/P8/release promotion")
    instruction_ready = data.get("local_operation_boundary_instruction_status") == P7_R54_EV07_INSTRUCTION_READY_STATUS_REF
    if instruction_ready:
        if data.get("ev06_request_ready") is not True or data.get("ev06_next_required_step") != P7_R54_EV07_STEP_REF:
            raise ValueError("R54 EV07 ready instruction requires EV06 ready request")
        packet_refs = [clean_identifier(item, max_length=180) for item in (data.get("packet_ref_ids_for_local_operation") or [])]
        instruction_rows = [safe_mapping(row) for row in (data.get("local_operation_instruction_rows") or [])]
        if data.get("ev06_packet_generation_request_status") != P7_R54_EV06_REQUEST_READY_STATUS_REF:
            raise ValueError("R54 EV07 ready instruction requires EV06 request ready status")
        if data.get("local_operation_boundary_instruction_ref") != P7_R54_EV07_INSTRUCTION_REF:
            raise ValueError("R54 EV07 instruction ref changed")
        if data.get("local_operation_boundary_instruction_reason_refs") != [P7_R54_EV07_READY_REASON_REF]:
            raise ValueError("R54 EV07 ready reason refs changed")
        if blockers:
            raise ValueError("R54 EV07 ready instruction must not carry execution blockers")
        if data.get("packet_ref_count_for_local_operation") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or len(packet_refs) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV07 packet ref count changed")
        if data.get("packet_ref_ids_for_local_operation_unique") is not True or not _ev05_unique_non_empty(packet_refs):
            raise ValueError("R54 EV07 packet refs must be unique")
        if len(instruction_rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("local_operation_instruction_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV07 instruction row count changed")
        for row in instruction_rows:
            _assert_ev07_local_operation_instruction_row(row)
        if [row.get("packet_ref_id") for row in instruction_rows] != packet_refs:
            raise ValueError("R54 EV07 instruction rows must match packet refs")
        for key in (
            "body_full_packet_generation_may_be_run_after_this_instruction",
            "local_operation_receipt_required_after_external_run",
            "external_local_body_full_packet_generation_required_before_actual_review",
        ):
            if data.get(key) is not True:
                raise ValueError(f"R54 EV07 ready instruction must keep {key}=True")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV07_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV08_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV07 ready instruction must point to EV08")
    else:
        if data.get("packet_ref_ids_for_local_operation") != [] or data.get("local_operation_instruction_rows") != []:
            raise ValueError("R54 EV07 blocked instruction must not expose local operation rows")
        if data.get("body_full_packet_generation_may_be_run_after_this_instruction") is not False:
            raise ValueError("R54 EV07 blocked instruction must not allow later packet generation")
        if data.get("local_operation_receipt_required_after_external_run") is not False:
            raise ValueError("R54 EV07 blocked instruction must not require receipt")
        if data.get("external_local_body_full_packet_generation_required_before_actual_review") is not False:
            raise ValueError("R54 EV07 blocked instruction must not require external generation")
        if not blockers:
            raise ValueError("R54 EV07 blocked instruction must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV07 blocked instruction next step changed")
    return True

P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev08_reviewer_selection_form_freeze.bodyfree.v1"
)
P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev09_sanitized_review_result_row.bodyfree.v1"
)
P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev09_sanitized_review_result_row_intake.bodyfree.v1"
)

P7_R54_EV08_STEP_REF: Final = P7_R54_EV08_NEXT_REQUIRED_STEP_REF
P7_R54_EV09_STEP_REF: Final = "R54-EV-09_sanitized_review_result_row_intake"
P7_R54_EV10_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-10_rating_row_normalization"
P7_R54_EV08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV07_IMPLEMENTED_STEPS, P7_R54_EV08_STEP_REF)
P7_R54_EV08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV09_STEP_REF,)
P7_R54_EV09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV08_IMPLEMENTED_STEPS, P7_R54_EV09_STEP_REF)
P7_R54_EV09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV10_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV08_FORM_READY_STATUS_REF: Final = "REVIEWER_SELECTION_FORM_FROZEN_BODYFREE_20260626"
P7_R54_EV08_FORM_BLOCKED_STATUS_REF: Final = "REVIEWER_SELECTION_FORM_BLOCKED_BY_EV07_LOCAL_OPERATION_BOUNDARY"
P7_R54_EV08_ALLOWED_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV08_FORM_READY_STATUS_REF,
    P7_R54_EV08_FORM_BLOCKED_STATUS_REF,
)
P7_R54_EV08_REVIEWER_SELECTION_FORM_REF: Final = "r54_ev08_reviewer_selection_form_bodyfree_20260626"
P7_R54_EV08_REVIEWER_SELECTION_FORM_POLICY_REF: Final = (
    "selection_only_bodyfree_no_free_text_no_question_text_no_paths_no_hashes_20260626"
)
P7_R54_EV08_READY_REASON_REF: Final = "r54_ev08_reviewer_selection_form_frozen_after_ev07_boundary"
P7_R54_EV08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev08_blocked_until_ev07_local_operation_boundary_ready"
P7_R54_EV08_REVIEWER_IDENTITY_POLICY_REF: Final = "reviewer_ref_is_pseudonymous_no_name_email_account"
P7_R54_EV08_SELECTION_ONLY_SOURCE_REF: Final = "external_local_actual_reviewer_selection_only_form"
P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS: Final[tuple[str, ...]] = (
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "reviewer_ref",
    "reviewed_at_ref",
    "axis_scores",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
)
P7_R54_EV08_PROHIBITED_SELECTION_FIELD_REFS: Final[tuple[str, ...]] = (
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "raw_input",
    "returned_emlis_body",
    "history_surface",
    "question_text",
    "draft_question_text",
    "local_absolute_path",
    "body_hash",
    "packet_content",
)
P7_R54_EV08_RATING_AXIS_REFS: Final[tuple[str, ...]] = r54op.P7_R54_OP09_RATING_AXIS_REFS
P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(r54op.P7_R54_OP09_RATING_AXIS_TARGET_THRESHOLDS)
P7_R54_EV08_SCORE_OPTION_REFS: Final[tuple[float, ...]] = r54op.P7_R54_OP09_SCORE_OPTION_REFS
P7_R54_EV08_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = (
    "PASS",
    "YELLOW",
    "REPAIR_REQUIRED",
    "RED",
    "NOT_REVIEWABLE",
)
P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = r54op.P7_R54_OP09_BLOCKER_ID_OPTION_REFS
P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = (
    "review_packet_generation_blocked_missing_local_root",
    "review_packet_generation_blocked_invalid_local_root",
    "review_packet_generation_blocked_missing_explicit_allow",
    "review_case_material_missing",
    "review_case_matrix_minimum_not_met",
    "reviewer_not_assigned",
    "review_timeout_unclassified",
    "rating_row_incomplete",
    "question_observation_row_incomplete",
    "body_purge_failed",
    "body_purge_not_verified",
    "body_free_validation_failed",
    "question_text_leak_detected",
    "body_payload_leak_detected",
    "local_path_leak_detected",
    "body_hash_leak_detected",
    "no_touch_violation_detected",
)
P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = r54op.P7_R54_OP09_QUESTION_NEED_PRIMARY_CLASS_REFS
P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = r54op.P7_R54_OP09_AMBIGUITY_KIND_OPTION_REFS
P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = r54op.P7_R54_OP09_ONE_QUESTION_FIT_OPTION_REFS
P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = (
    "no_repair_required",
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
    "p4_current_surface_repair_required",
)
P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = r54op.P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS

P7_R54_EV09_INTAKE_READY_STATUS_REF: Final = "SANITIZED_REVIEW_RESULT_ROWS_INTAKEN_BODYFREE_20260626"
P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF: Final = "SANITIZED_REVIEW_RESULT_ROW_INTAKE_BLOCKED_20260626"
P7_R54_EV09_ALLOWED_INTAKE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV09_INTAKE_READY_STATUS_REF,
    P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF,
)
P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_REF: Final = "r54_ev09_sanitized_review_result_row_intake_bodyfree_20260626"
P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_POLICY_REF: Final = (
    "sanitized_selection_rows_only_no_raw_body_no_question_text_no_paths_no_hashes_20260626"
)
P7_R54_EV09_READY_REASON_REF: Final = "r54_ev09_24_sanitized_selection_rows_intaken_bodyfree"
P7_R54_EV09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev09_blocked_until_24_selection_only_rows_are_available"

P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev07_schema_version",
    "ev07_material_ref",
    "ev07_next_required_step",
    "ev07_local_operation_boundary_instruction_status",
    "ev07_instruction_ready",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op09_helper_ref",
    "existing_op09_schema_version",
    "existing_op09_operation_current_refs",
    "existing_op09_current_refs_are_historical_here",
    "existing_op09_reused_as_actual_form_basis",
    "existing_op09_structural_contract_reused",
    "existing_op09_verdict_options_are_historical_here",
    "required_case_count",
    "packet_ref_ids_for_review",
    "packet_ref_count_for_review",
    "packet_ref_ids_for_review_unique",
    "reviewer_selection_form_status",
    "reviewer_selection_form_ref",
    "reviewer_selection_form_policy_ref",
    "reviewer_selection_form_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "reviewer_identity_policy_ref",
    "reviewer_ref_pseudonymous_required",
    "selection_only_source_ref",
    "required_selection_field_refs",
    "required_selection_field_count",
    "prohibited_selection_field_refs",
    "prohibited_selection_field_count",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "score_option_refs",
    "score_option_count",
    "verdict_option_refs",
    "verdict_option_count",
    "readfeel_blocker_id_option_refs",
    "readfeel_blocker_id_option_count",
    "execution_blocker_id_option_refs",
    "execution_blocker_id_option_count",
    "question_need_primary_class_options",
    "question_need_primary_class_option_count",
    "ambiguity_kind_option_refs",
    "ambiguity_kind_option_count",
    "one_question_fit_option_refs",
    "one_question_fit_option_count",
    "repair_required_option_refs",
    "repair_required_option_count",
    "plan_candidate_flag_refs",
    "plan_candidate_flag_count",
    "selection_form_is_bodyfree_only",
    "selection_form_contains_free_text_field",
    "selection_form_contains_raw_body_copy_field",
    "selection_form_contains_question_text_field",
    "selection_form_contains_local_path_field",
    "selection_form_contains_hash_field",
    "reviewer_free_text_export_allowed",
    "body_full_packet_generation_run_here",
    "actual_body_full_packet_generated_here",
    "actual_human_review_run_here",
    "sanitized_review_result_row_intake_allowed_next",
    "p5_actual_review_still_not_run",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "actual_human_review_completion_claim_blocked_here",
    "human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_result_row_ref",
    "review_session_id",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "family",
    "case_role",
    "reviewer_ref",
    "reviewed_at_ref",
    "axis_scores",
    "axis_score_count",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "selection_only_row",
    "reviewer_free_text_included",
    "raw_body_included",
    "comment_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "source_body_not_materialized_in_row",
    "body_free",
)

P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev08_schema_version",
    "ev08_material_ref",
    "ev08_next_required_step",
    "ev08_reviewer_selection_form_status",
    "ev08_form_ready",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op11_helper_ref",
    "existing_op11_schema_version",
    "existing_op11_operation_current_refs",
    "existing_op11_current_refs_are_historical_here",
    "existing_op11_reused_as_actual_intake_basis",
    "existing_op11_structural_contract_reused",
    "required_case_count",
    "expected_packet_ref_ids",
    "expected_packet_ref_count",
    "incoming_selection_row_count",
    "sanitized_review_result_intake_status",
    "sanitized_review_result_intake_ref",
    "sanitized_review_result_intake_policy_ref",
    "sanitized_review_result_intake_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "sanitized_review_result_rows",
    "sanitized_review_result_row_count",
    "reviewed_case_count",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "case_ref_ids",
    "case_ref_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "reviewer_ref_ids",
    "reviewer_ref_count",
    "family_case_counts",
    "case_role_counts",
    "selection_rows_are_bodyfree_only",
    "sanitized_rows_contain_reviewer_free_text",
    "sanitized_rows_contain_raw_body",
    "sanitized_rows_contain_comment_text",
    "sanitized_rows_contain_question_text",
    "sanitized_rows_contain_local_path",
    "sanitized_rows_contain_body_hash",
    "sanitized_rows_contain_packet_content",
    "sanitized_review_result_rows_materialized_here",
    "rating_row_normalization_allowed_next",
    "actual_human_review_run_by_helper",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


def build_p7_r54_ev08_reviewer_selection_form_freeze(
    *,
    local_operation_boundary_instruction: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev08_reviewer_selection_form_freeze",
) -> dict[str, Any]:
    """Build EV08 body-free reviewer selection form freeze without running review."""

    ev07 = (
        safe_mapping(local_operation_boundary_instruction)
        if local_operation_boundary_instruction is not None
        else build_p7_r54_ev07_local_operation_boundary_instruction()
    )
    assert_p7_r54_ev07_local_operation_boundary_instruction_contract(ev07)
    ev07_ready = bool(
        ev07.get("local_operation_boundary_instruction_status") == P7_R54_EV07_INSTRUCTION_READY_STATUS_REF
        and ev07.get("next_required_step") == P7_R54_EV08_STEP_REF
    )
    packet_refs = [clean_identifier(item, max_length=180) for item in (ev07.get("packet_ref_ids_for_local_operation") or [])] if ev07_ready else []
    form_ready = bool(
        ev07_ready
        and len(packet_refs) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and _ev05_unique_non_empty(packet_refs)
    )
    execution_blockers = [] if form_ready else dedupe_identifiers(
        ["r54_ev08_blocked_until_ev07_local_operation_boundary_ready", *(ev07.get("open_execution_blocker_ids") or [])],
        limit=60,
        max_length=180,
    )
    reason_refs = [P7_R54_EV08_READY_REASON_REF] if form_ready else dedupe_identifiers(
        [P7_R54_EV08_FORM_BLOCKED_STATUS_REF, *execution_blockers],
        limit=60,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV08_STEP_REF,
        "operation_step_ref": P7_R54_EV08_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev08_reviewer_selection_form_freeze", max_length=220),
        "review_session_id": _safe_review_session_id(ev07.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev07_schema_version": P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION,
        "ev07_material_ref": clean_identifier(ev07.get("material_id"), default="p7_r54_ev07_local_operation_boundary_instruction", max_length=220),
        "ev07_next_required_step": clean_identifier(ev07.get("next_required_step"), default=P7_R54_EV07_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev07_local_operation_boundary_instruction_status": clean_identifier(ev07.get("local_operation_boundary_instruction_status"), default=P7_R54_EV07_INSTRUCTION_BLOCKED_STATUS_REF, max_length=180),
        "ev07_instruction_ready": ev07_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op09_helper_ref": "build_p7_r54_op09_reviewer_instruction_rating_form_freeze",
        "existing_op09_schema_version": r54op.P7_R54_OPERATION_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "existing_op09_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op09_current_refs_are_historical_here": True,
        "existing_op09_reused_as_actual_form_basis": False,
        "existing_op09_structural_contract_reused": True,
        "existing_op09_verdict_options_are_historical_here": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "packet_ref_ids_for_review": packet_refs,
        "packet_ref_count_for_review": len(packet_refs),
        "packet_ref_ids_for_review_unique": _ev05_unique_non_empty(packet_refs) if form_ready else False,
        "reviewer_selection_form_status": P7_R54_EV08_FORM_READY_STATUS_REF if form_ready else P7_R54_EV08_FORM_BLOCKED_STATUS_REF,
        "reviewer_selection_form_ref": P7_R54_EV08_REVIEWER_SELECTION_FORM_REF if form_ready else "reviewer_selection_form_not_frozen_until_ev07_boundary_ready",
        "reviewer_selection_form_policy_ref": P7_R54_EV08_REVIEWER_SELECTION_FORM_POLICY_REF,
        "reviewer_selection_form_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "reviewer_identity_policy_ref": P7_R54_EV08_REVIEWER_IDENTITY_POLICY_REF,
        "reviewer_ref_pseudonymous_required": form_ready,
        "selection_only_source_ref": P7_R54_EV08_SELECTION_ONLY_SOURCE_REF,
        "required_selection_field_refs": list(P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS) if form_ready else [],
        "required_selection_field_count": len(P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS) if form_ready else 0,
        "prohibited_selection_field_refs": list(P7_R54_EV08_PROHIBITED_SELECTION_FIELD_REFS) if form_ready else [],
        "prohibited_selection_field_count": len(P7_R54_EV08_PROHIBITED_SELECTION_FIELD_REFS) if form_ready else 0,
        "rating_axis_refs": list(P7_R54_EV08_RATING_AXIS_REFS) if form_ready else [],
        "rating_axis_count": len(P7_R54_EV08_RATING_AXIS_REFS) if form_ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS) if form_ready else {},
        "score_option_refs": list(P7_R54_EV08_SCORE_OPTION_REFS) if form_ready else [],
        "score_option_count": len(P7_R54_EV08_SCORE_OPTION_REFS) if form_ready else 0,
        "verdict_option_refs": list(P7_R54_EV08_VERDICT_OPTION_REFS) if form_ready else [],
        "verdict_option_count": len(P7_R54_EV08_VERDICT_OPTION_REFS) if form_ready else 0,
        "readfeel_blocker_id_option_refs": list(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS) if form_ready else [],
        "readfeel_blocker_id_option_count": len(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS) if form_ready else 0,
        "execution_blocker_id_option_refs": list(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS) if form_ready else [],
        "execution_blocker_id_option_count": len(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS) if form_ready else 0,
        "question_need_primary_class_options": list(P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS) if form_ready else [],
        "question_need_primary_class_option_count": len(P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS) if form_ready else 0,
        "ambiguity_kind_option_refs": list(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS) if form_ready else [],
        "ambiguity_kind_option_count": len(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS) if form_ready else 0,
        "one_question_fit_option_refs": list(P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS) if form_ready else [],
        "one_question_fit_option_count": len(P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS) if form_ready else 0,
        "repair_required_option_refs": list(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS) if form_ready else [],
        "repair_required_option_count": len(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS) if form_ready else 0,
        "plan_candidate_flag_refs": list(P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS) if form_ready else [],
        "plan_candidate_flag_count": len(P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS) if form_ready else 0,
        "selection_form_is_bodyfree_only": True,
        "selection_form_contains_free_text_field": False,
        "selection_form_contains_raw_body_copy_field": False,
        "selection_form_contains_question_text_field": False,
        "selection_form_contains_local_path_field": False,
        "selection_form_contains_hash_field": False,
        "reviewer_free_text_export_allowed": False,
        "body_full_packet_generation_run_here": False,
        "actual_body_full_packet_generated_here": False,
        "actual_human_review_run_here": False,
        "sanitized_review_result_row_intake_allowed_next": form_ready,
        "p5_actual_review_still_not_run": True,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "actual_human_review_completion_claim_blocked_here": True,
        "human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV08_IMPLEMENTED_STEPS if form_ready else (ev07.get("implemented_steps") or P7_R54_EV07_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV08_NOT_YET_IMPLEMENTED_STEPS if form_ready else (ev07.get("not_yet_implemented_steps") or P7_R54_EV07_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV09_STEP_REF if form_ready else P7_R54_EV08_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(material)
    return material


def assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r54_ev08_reviewer_selection_form_freeze",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_EV08_STEP_REF,
        operation_step_ref=P7_R54_EV08_STEP_REF,
        source="p7_r54_ev08_reviewer_selection_form_freeze",
    )
    if data.get("ev07_schema_version") != P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION:
        raise ValueError("R54 EV08 EV07 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV08 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op09_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV08 existing OP09 refs changed")
    if data.get("existing_op09_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV08 must classify existing OP09 refs as historical")
    if data.get("existing_op09_reused_as_actual_form_basis") is not False:
        raise ValueError("R54 EV08 must not reuse 20260625 OP09 as actual form basis")
    if data.get("existing_op09_structural_contract_reused") is not True:
        raise ValueError("R54 EV08 must reuse only OP09 structural contract")
    if data.get("existing_op09_verdict_options_are_historical_here") is not True:
        raise ValueError("R54 EV08 must keep 20260625 OP09 verdict options historical")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV08 required case count changed")
    if data.get("reviewer_selection_form_status") not in P7_R54_EV08_ALLOWED_FORM_STATUS_REFS:
        raise ValueError("R54 EV08 selection form status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV08 open blockers must match execution blockers")
    for false_key in (
        "selection_form_contains_free_text_field",
        "selection_form_contains_raw_body_copy_field",
        "selection_form_contains_question_text_field",
        "selection_form_contains_local_path_field",
        "selection_form_contains_hash_field",
        "reviewer_free_text_export_allowed",
        "body_full_packet_generation_run_here",
        "actual_body_full_packet_generated_here",
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV08 must keep {false_key}=False")
    if data.get("selection_form_is_bodyfree_only") is not True:
        raise ValueError("R54 EV08 selection form must be body-free only")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R54 EV08 must keep P5 actual review not run")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV08 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV08 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV08 must block P6/P8/release promotion")
    form_ready = data.get("reviewer_selection_form_status") == P7_R54_EV08_FORM_READY_STATUS_REF
    if form_ready:
        if data.get("ev07_instruction_ready") is not True or data.get("ev07_next_required_step") != P7_R54_EV08_STEP_REF:
            raise ValueError("R54 EV08 ready form requires EV07 ready boundary")
        packet_refs = [clean_identifier(item, max_length=180) for item in (data.get("packet_ref_ids_for_review") or [])]
        if data.get("packet_ref_count_for_review") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or len(packet_refs) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV08 packet ref count changed")
        if data.get("packet_ref_ids_for_review_unique") is not True or not _ev05_unique_non_empty(packet_refs):
            raise ValueError("R54 EV08 packet refs must be unique")
        if blockers:
            raise ValueError("R54 EV08 ready form must not carry execution blockers")
        if data.get("reviewer_selection_form_ref") != P7_R54_EV08_REVIEWER_SELECTION_FORM_REF:
            raise ValueError("R54 EV08 selection form ref changed")
        if data.get("reviewer_selection_form_policy_ref") != P7_R54_EV08_REVIEWER_SELECTION_FORM_POLICY_REF:
            raise ValueError("R54 EV08 selection form policy changed")
        if data.get("reviewer_selection_form_reason_refs") != [P7_R54_EV08_READY_REASON_REF]:
            raise ValueError("R54 EV08 ready reason refs changed")
        if data.get("reviewer_identity_policy_ref") != P7_R54_EV08_REVIEWER_IDENTITY_POLICY_REF:
            raise ValueError("R54 EV08 reviewer identity policy changed")
        if data.get("reviewer_ref_pseudonymous_required") is not True:
            raise ValueError("R54 EV08 reviewer pseudonymous ref requirement changed")
        option_checks = (
            ("required_selection_field_refs", list(P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS), "required selection fields"),
            ("prohibited_selection_field_refs", list(P7_R54_EV08_PROHIBITED_SELECTION_FIELD_REFS), "prohibited selection fields"),
            ("rating_axis_refs", list(P7_R54_EV08_RATING_AXIS_REFS), "rating axes"),
            ("score_option_refs", list(P7_R54_EV08_SCORE_OPTION_REFS), "score options"),
            ("verdict_option_refs", list(P7_R54_EV08_VERDICT_OPTION_REFS), "verdict options"),
            ("readfeel_blocker_id_option_refs", list(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS), "readfeel blocker options"),
            ("execution_blocker_id_option_refs", list(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS), "execution blocker options"),
            ("question_need_primary_class_options", list(P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS), "question class options"),
            ("ambiguity_kind_option_refs", list(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS), "ambiguity options"),
            ("one_question_fit_option_refs", list(P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS), "one-question-fit options"),
            ("repair_required_option_refs", list(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS), "repair required options"),
            ("plan_candidate_flag_refs", list(P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS), "plan candidate flags"),
        )
        for key, expected, label in option_checks:
            if data.get(key) != expected:
                raise ValueError(f"R54 EV08 {label} changed")
        count_checks = (
            ("required_selection_field_count", len(P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS)),
            ("prohibited_selection_field_count", len(P7_R54_EV08_PROHIBITED_SELECTION_FIELD_REFS)),
            ("rating_axis_count", len(P7_R54_EV08_RATING_AXIS_REFS)),
            ("score_option_count", len(P7_R54_EV08_SCORE_OPTION_REFS)),
            ("verdict_option_count", len(P7_R54_EV08_VERDICT_OPTION_REFS)),
            ("readfeel_blocker_id_option_count", len(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS)),
            ("execution_blocker_id_option_count", len(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS)),
            ("question_need_primary_class_option_count", len(P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS)),
            ("ambiguity_kind_option_count", len(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS)),
            ("one_question_fit_option_count", len(P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS)),
            ("repair_required_option_count", len(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS)),
            ("plan_candidate_flag_count", len(P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS)),
        )
        for key, expected in count_checks:
            if data.get(key) != expected:
                raise ValueError(f"R54 EV08 {key} changed")
        if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("R54 EV08 rating axis thresholds changed")
        if data.get("sanitized_review_result_row_intake_allowed_next") is not True:
            raise ValueError("R54 EV08 ready form must allow EV09 next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV08_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV08 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV08 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV09_STEP_REF:
            raise ValueError("R54 EV08 ready form must point to EV09")
    else:
        if data.get("packet_ref_ids_for_review") != [] or data.get("packet_ref_count_for_review") != 0:
            raise ValueError("R54 EV08 blocked form must not expose packet refs")
        if data.get("sanitized_review_result_row_intake_allowed_next") is not False:
            raise ValueError("R54 EV08 blocked form must not allow EV09 next")
        for key in (
            "required_selection_field_refs",
            "prohibited_selection_field_refs",
            "rating_axis_refs",
            "score_option_refs",
            "verdict_option_refs",
            "readfeel_blocker_id_option_refs",
            "execution_blocker_id_option_refs",
            "question_need_primary_class_options",
            "ambiguity_kind_option_refs",
            "one_question_fit_option_refs",
            "repair_required_option_refs",
            "plan_candidate_flag_refs",
        ):
            if data.get(key) != []:
                raise ValueError("R54 EV08 blocked form must not expose selection options")
        if not blockers:
            raise ValueError("R54 EV08 blocked form must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV08 blocked next step changed")
    return True


def _ev09_plan_candidate_flags(value: Any) -> dict[str, bool]:
    mapping = safe_mapping(value)
    return {key: (bool(mapping.get(key, False)) if key != "p8_implementation_spec_finalized_here" else False) for key in P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS}


def _ev09_axis_scores(value: Any) -> dict[str, float]:
    mapping = safe_mapping(value)
    scores: dict[str, float] = {}
    for axis in P7_R54_EV08_RATING_AXIS_REFS:
        raw = mapping.get(axis)
        if isinstance(raw, bool):
            continue
        try:
            score = float(raw)
        except (TypeError, ValueError):
            continue
        scores[axis] = score
    return scores


def _ev09_normalized_sanitized_review_rows(rows: Sequence[Any], *, review_session_id: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        source = safe_mapping(row)
        assert_p7_no_body_payload_or_contract_mutation(source, source="p7_r54_ev09_input_selection_row")
        normalized.append(
            {
                "schema_version": P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_result_row_ref": clean_identifier(source.get("review_result_row_ref"), default=f"r54ev09-sanitized-review-row-{index:03d}", max_length=180),
                "review_session_id": review_session_id,
                "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
                "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
                "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
                "family": clean_identifier(source.get("family"), max_length=180),
                "case_role": clean_identifier(source.get("case_role"), max_length=180),
                "reviewer_ref": clean_identifier(source.get("reviewer_ref"), max_length=120),
                "reviewed_at_ref": clean_identifier(source.get("reviewed_at_ref"), default="coarse_reviewed_at_ref_20260626", max_length=160),
                "axis_scores": _ev09_axis_scores(source.get("axis_scores")),
                "axis_score_count": len(_ev09_axis_scores(source.get("axis_scores"))),
                "verdict": clean_identifier(source.get("verdict"), max_length=80),
                "sanitized_reason_ids": dedupe_identifiers(source.get("sanitized_reason_ids") or [], limit=20, max_length=160),
                "readfeel_blocker_ids": dedupe_identifiers(source.get("readfeel_blocker_ids") or [], limit=20, max_length=160),
                "execution_blocker_ids": dedupe_identifiers(source.get("execution_blocker_ids") or [], limit=20, max_length=160),
                "question_need_primary_class": clean_identifier(source.get("question_need_primary_class"), max_length=160),
                "ambiguity_kind_refs": dedupe_identifiers(source.get("ambiguity_kind_refs") or [], limit=20, max_length=160),
                "one_question_fit_ref": clean_identifier(source.get("one_question_fit_ref"), max_length=160),
                "repair_required_refs": dedupe_identifiers(source.get("repair_required_refs") or [], limit=20, max_length=160),
                "plan_candidate_flags": _ev09_plan_candidate_flags(source.get("plan_candidate_flags")),
                "selection_only_row": True,
                "reviewer_free_text_included": False,
                "raw_body_included": False,
                "comment_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "local_path_included": False,
                "body_hash_included": False,
                "packet_content_included": False,
                "source_body_not_materialized_in_row": True,
                "body_free": True,
            }
        )
    return normalized


def _assert_p7_r54_ev09_sanitized_review_result_row(row: Mapping[str, Any]) -> None:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_ev09_sanitized_review_result_row",
    )
    if data.get("schema_version") != P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV09 row schema version changed")
    if data.get("selection_only_row") is not True or data.get("body_free") is not True:
        raise ValueError("R54 EV09 row must remain body-free selection-only")
    for field in ("case_ref_id", "blind_case_id", "packet_ref_id", "family", "case_role", "reviewer_ref", "reviewed_at_ref"):
        if not clean_identifier(data.get(field), max_length=180):
            raise ValueError(f"R54 EV09 row missing {field}")
    scores = safe_mapping(data.get("axis_scores"))
    if tuple(scores.keys()) != P7_R54_EV08_RATING_AXIS_REFS:
        raise ValueError("R54 EV09 row axis score keys changed")
    if data.get("axis_score_count") != len(P7_R54_EV08_RATING_AXIS_REFS):
        raise ValueError("R54 EV09 row axis score count changed")
    for axis in P7_R54_EV08_RATING_AXIS_REFS:
        score = scores.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError("R54 EV09 row axis score type invalid")
        if float(score) not in P7_R54_EV08_SCORE_OPTION_REFS:
            raise ValueError("R54 EV09 row axis score must use fixed score options")
    if data.get("verdict") not in P7_R54_EV08_VERDICT_OPTION_REFS:
        raise ValueError("R54 EV09 row verdict option changed")
    if not set(data.get("readfeel_blocker_ids") or []).issubset(set(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS)):
        raise ValueError("R54 EV09 row readfeel blocker outside frozen form options")
    if not set(data.get("execution_blocker_ids") or []).issubset(set(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS)):
        raise ValueError("R54 EV09 row execution blocker outside frozen form options")
    if data.get("question_need_primary_class") not in P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 EV09 row question need class outside frozen options")
    if not set(data.get("ambiguity_kind_refs") or []).issubset(set(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("R54 EV09 row ambiguity refs outside frozen options")
    if data.get("one_question_fit_ref") not in P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 EV09 row one-question-fit option changed")
    repair_refs = data.get("repair_required_refs") or []
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("R54 EV09 row repair refs outside frozen options")
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if tuple(flags.keys()) != P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("R54 EV09 row plan candidate flag keys changed")
    if flags.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R54 EV09 row must not finalize P8 implementation spec")
    for false_key in (
        "reviewer_free_text_included",
        "raw_body_included",
        "comment_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
        "body_hash_included",
        "packet_content_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV09 row must keep {false_key}=False")
    if data.get("source_body_not_materialized_in_row") is not True:
        raise ValueError("R54 EV09 row must mark source body as not materialized")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev09_sanitized_review_result_row")


def _ev09_sanitized_rows_ready(rows: Sequence[Mapping[str, Any]], *, expected_packet_refs: Sequence[str]) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if len(rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("sanitized_review_result_row_count_must_be_24")
    packet_refs = _ev05_case_refs(rows, "packet_ref_id")
    case_refs = _ev05_case_refs(rows, "case_ref_id")
    blind_ids = _ev05_case_refs(rows, "blind_case_id")
    row_refs = _ev05_case_refs(rows, "review_result_row_ref")
    if packet_refs != list(expected_packet_refs):
        blockers.append("sanitized_review_packet_refs_must_match_ev08_packet_refs")
    if not _ev05_unique_non_empty(packet_refs):
        blockers.append("sanitized_review_packet_refs_must_be_unique")
    if not _ev05_unique_non_empty(case_refs):
        blockers.append("sanitized_review_case_refs_must_be_unique")
    if not _ev05_unique_non_empty(blind_ids):
        blockers.append("sanitized_review_blind_case_ids_must_be_unique")
    if not _ev05_unique_non_empty(row_refs):
        blockers.append("sanitized_review_row_refs_must_be_unique")
    try:
        for row in rows:
            _assert_p7_r54_ev09_sanitized_review_result_row(row)
    except ValueError as exc:
        blockers.append(clean_identifier(str(exc), default="sanitized_review_result_row_contract_failed", max_length=180))
    return not blockers, dedupe_identifiers(blockers, limit=100, max_length=180)


def build_p7_r54_ev09_sanitized_review_result_row_intake(
    *,
    reviewer_selection_form_freeze: Mapping[str, Any] | None = None,
    reviewer_selection_rows: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_ev09_sanitized_review_result_row_intake",
) -> dict[str, Any]:
    """Build EV09 body-free sanitized selection-row intake without rating normalization."""

    ev08 = (
        safe_mapping(reviewer_selection_form_freeze)
        if reviewer_selection_form_freeze is not None
        else build_p7_r54_ev08_reviewer_selection_form_freeze()
    )
    assert_p7_r54_ev08_reviewer_selection_form_freeze_contract(ev08)
    form_ready = bool(
        ev08.get("reviewer_selection_form_status") == P7_R54_EV08_FORM_READY_STATUS_REF
        and ev08.get("sanitized_review_result_row_intake_allowed_next") is True
        and ev08.get("next_required_step") == P7_R54_EV09_STEP_REF
    )
    review_session_id = _safe_review_session_id(ev08.get("review_session_id"))
    expected_packet_refs = [clean_identifier(item, max_length=180) for item in (ev08.get("packet_ref_ids_for_review") or [])] if form_ready else []
    incoming_row_count = len(list(reviewer_selection_rows or []))
    normalized_rows = _ev09_normalized_sanitized_review_rows(reviewer_selection_rows or [], review_session_id=review_session_id) if form_ready else []
    rows_ready, row_blockers = _ev09_sanitized_rows_ready(normalized_rows, expected_packet_refs=expected_packet_refs) if form_ready else (False, ["r54_ev09_blocked_until_ev08_selection_form_ready"])
    intake_ready = bool(form_ready and rows_ready)
    rows = normalized_rows if intake_ready else []
    packet_refs = _ev05_case_refs(rows, "packet_ref_id")
    case_refs = _ev05_case_refs(rows, "case_ref_id")
    blind_ids = _ev05_case_refs(rows, "blind_case_id")
    reviewer_refs = _ev05_case_refs(rows, "reviewer_ref")
    family_counts = _ev05_count_by(rows, "family") if intake_ready else {}
    role_counts = _ev05_count_by(rows, "case_role") if intake_ready else {}
    execution_blockers = [] if intake_ready else dedupe_identifiers(
        [*row_blockers, *(ev08.get("open_execution_blocker_ids") or [])],
        limit=100,
        max_length=180,
    )
    reason_refs = [P7_R54_EV09_READY_REASON_REF] if intake_ready else dedupe_identifiers(
        [P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF, *execution_blockers],
        limit=100,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV09_STEP_REF,
        "operation_step_ref": P7_R54_EV09_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev09_sanitized_review_result_row_intake", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev08_schema_version": P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION,
        "ev08_material_ref": clean_identifier(ev08.get("material_id"), default="p7_r54_ev08_reviewer_selection_form_freeze", max_length=220),
        "ev08_next_required_step": clean_identifier(ev08.get("next_required_step"), default=P7_R54_EV08_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev08_reviewer_selection_form_status": clean_identifier(ev08.get("reviewer_selection_form_status"), default=P7_R54_EV08_FORM_BLOCKED_STATUS_REF, max_length=180),
        "ev08_form_ready": form_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op11_helper_ref": "build_p7_r54_op11_sanitized_review_result_capture",
        "existing_op11_schema_version": r54op.P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "existing_op11_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op11_current_refs_are_historical_here": True,
        "existing_op11_reused_as_actual_intake_basis": False,
        "existing_op11_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "expected_packet_ref_ids": expected_packet_refs,
        "expected_packet_ref_count": len(expected_packet_refs),
        "incoming_selection_row_count": incoming_row_count if form_ready else 0,
        "sanitized_review_result_intake_status": P7_R54_EV09_INTAKE_READY_STATUS_REF if intake_ready else P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF,
        "sanitized_review_result_intake_ref": P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_REF if intake_ready else "sanitized_review_result_row_intake_not_ready_bodyfree",
        "sanitized_review_result_intake_policy_ref": P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_POLICY_REF,
        "sanitized_review_result_intake_reason_refs": reason_refs,
        "execution_blocker_ids": execution_blockers,
        "open_execution_blocker_ids": execution_blockers,
        "sanitized_review_result_rows": rows,
        "sanitized_review_result_row_count": len(rows),
        "reviewed_case_count": len(rows),
        "packet_ref_ids": packet_refs,
        "packet_ref_count": len(packet_refs),
        "packet_ref_ids_unique": _ev05_unique_non_empty(packet_refs) if intake_ready else False,
        "case_ref_ids": case_refs,
        "case_ref_count": len(case_refs),
        "case_ref_ids_unique": _ev05_unique_non_empty(case_refs) if intake_ready else False,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": _ev05_unique_non_empty(blind_ids) if intake_ready else False,
        "reviewer_ref_ids": dedupe_identifiers(reviewer_refs, limit=8, max_length=120),
        "reviewer_ref_count": len(dedupe_identifiers(reviewer_refs, limit=8, max_length=120)),
        "family_case_counts": family_counts,
        "case_role_counts": role_counts,
        "selection_rows_are_bodyfree_only": intake_ready,
        "sanitized_rows_contain_reviewer_free_text": False,
        "sanitized_rows_contain_raw_body": False,
        "sanitized_rows_contain_comment_text": False,
        "sanitized_rows_contain_question_text": False,
        "sanitized_rows_contain_local_path": False,
        "sanitized_rows_contain_body_hash": False,
        "sanitized_rows_contain_packet_content": False,
        "sanitized_review_result_rows_materialized_here": intake_ready,
        "rating_row_normalization_allowed_next": intake_ready,
        "actual_human_review_run_by_helper": False,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "rating_row_count": 0,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV09_IMPLEMENTED_STEPS if intake_ready else (ev08.get("implemented_steps") or P7_R54_EV08_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV09_NOT_YET_IMPLEMENTED_STEPS if intake_ready else (ev08.get("not_yet_implemented_steps") or P7_R54_EV08_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV10_NEXT_REQUIRED_STEP_REF if intake_ready else P7_R54_EV09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
    }
    assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material)
    return material


def assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS,
        source="p7_r54_ev09_sanitized_review_result_row_intake",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_EV09_STEP_REF,
        operation_step_ref=P7_R54_EV09_STEP_REF,
        source="p7_r54_ev09_sanitized_review_result_row_intake",
    )
    if data.get("ev08_schema_version") != P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION:
        raise ValueError("R54 EV09 EV08 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV09 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op11_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV09 existing OP11 refs changed")
    if data.get("existing_op11_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV09 must classify existing OP11 refs as historical")
    if data.get("existing_op11_reused_as_actual_intake_basis") is not False:
        raise ValueError("R54 EV09 must not reuse 20260625 OP11 as actual intake basis")
    if data.get("existing_op11_structural_contract_reused") is not True:
        raise ValueError("R54 EV09 must reuse only OP11 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV09 required case count changed")
    if data.get("sanitized_review_result_intake_status") not in P7_R54_EV09_ALLOWED_INTAKE_STATUS_REFS:
        raise ValueError("R54 EV09 intake status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV09 open blockers must match execution blockers")
    for false_key in (
        "sanitized_rows_contain_reviewer_free_text",
        "sanitized_rows_contain_raw_body",
        "sanitized_rows_contain_comment_text",
        "sanitized_rows_contain_question_text",
        "sanitized_rows_contain_local_path",
        "sanitized_rows_contain_body_hash",
        "sanitized_rows_contain_packet_content",
        "actual_human_review_run_by_helper",
        "actual_human_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete",
        "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV09 must keep {false_key}=False")
    if data.get("rating_row_count") != 0 or data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV09 must not materialize rating/question rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV09 must block human-review completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV09 must block P6/P8/release promotion")
    intake_ready = data.get("sanitized_review_result_intake_status") == P7_R54_EV09_INTAKE_READY_STATUS_REF
    if intake_ready:
        if data.get("ev08_form_ready") is not True or data.get("ev08_next_required_step") != P7_R54_EV09_STEP_REF:
            raise ValueError("R54 EV09 ready intake requires EV08 ready form")
        if blockers:
            raise ValueError("R54 EV09 ready intake must not carry execution blockers")
        if data.get("expected_packet_ref_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV09 expected packet ref count changed")
        if data.get("incoming_selection_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV09 incoming selection row count changed")
        if data.get("sanitized_review_result_intake_ref") != P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_REF:
            raise ValueError("R54 EV09 intake ref changed")
        if data.get("sanitized_review_result_intake_policy_ref") != P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_POLICY_REF:
            raise ValueError("R54 EV09 intake policy changed")
        if data.get("sanitized_review_result_intake_reason_refs") != [P7_R54_EV09_READY_REASON_REF]:
            raise ValueError("R54 EV09 ready reason refs changed")
        rows = [safe_mapping(row) for row in (data.get("sanitized_review_result_rows") or [])]
        if data.get("sanitized_review_result_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or len(rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV09 ready intake must contain 24 rows")
        if data.get("reviewed_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV09 reviewed case count changed")
        packet_refs = _ev05_case_refs(rows, "packet_ref_id")
        if packet_refs != list(data.get("expected_packet_ref_ids") or []):
            raise ValueError("R54 EV09 packet refs must match EV08 expected refs")
        if data.get("packet_ref_ids") != packet_refs:
            raise ValueError("R54 EV09 packet refs changed")
        row_refs = _ev05_case_refs(rows, "review_result_row_ref")
        if not _ev05_unique_non_empty(row_refs):
            raise ValueError("R54 EV09 row refs must be unique")
        if data.get("packet_ref_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("case_ref_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("blind_case_id_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV09 ready intake counts changed")
        if data.get("packet_ref_ids_unique") is not True or data.get("case_ref_ids_unique") is not True or data.get("blind_case_ids_unique") is not True:
            raise ValueError("R54 EV09 ready intake must keep unique refs")
        if data.get("reviewer_ref_count", 0) < 1:
            raise ValueError("R54 EV09 ready intake requires pseudonymous reviewer refs")
        if data.get("selection_rows_are_bodyfree_only") is not True:
            raise ValueError("R54 EV09 ready intake rows must be body-free only")
        if data.get("sanitized_review_result_rows_materialized_here") is not True:
            raise ValueError("R54 EV09 ready intake must materialize sanitized rows")
        if data.get("rating_row_normalization_allowed_next") is not True:
            raise ValueError("R54 EV09 ready intake must allow EV10 next")
        for row in rows:
            _assert_p7_r54_ev09_sanitized_review_result_row(row)
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV09_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV09 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV09 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV10_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV09 ready intake must point to EV10")
    else:
        if data.get("sanitized_review_result_intake_status") != P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV09 blocked intake status changed")
        if data.get("sanitized_review_result_rows") != [] or data.get("sanitized_review_result_row_count") != 0:
            raise ValueError("R54 EV09 blocked intake must not materialize sanitized rows")
        if data.get("selection_rows_are_bodyfree_only") is not False or data.get("rating_row_normalization_allowed_next") is not False:
            raise ValueError("R54 EV09 blocked intake must not allow rating normalization")
        if data.get("sanitized_review_result_rows_materialized_here") is not False:
            raise ValueError("R54 EV09 blocked intake must not materialize sanitized rows")
        if not blockers:
            raise ValueError("R54 EV09 blocked intake must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV09 blocked next step changed")
    return True


P7_R54_EV_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev10_rating_row.bodyfree.v1"
)
P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev10_rating_row_normalization.bodyfree.v1"
)
P7_R54_EV_READFEEL_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev11_readfeel_blocker_row.bodyfree.v1"
)
P7_R54_EV_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev11_execution_blocker_row.bodyfree.v1"
)
P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev11_blocker_ingestion.bodyfree.v1"
)

P7_R54_EV10_STEP_REF: Final = P7_R54_EV10_NEXT_REQUIRED_STEP_REF
P7_R54_EV11_STEP_REF: Final = "R54-EV-11_blocker_ingestion"
P7_R54_EV12_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-12_question_need_observation_row_normalization"
P7_R54_EV10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV09_IMPLEMENTED_STEPS, P7_R54_EV10_STEP_REF)
P7_R54_EV10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV11_STEP_REF,)
P7_R54_EV11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV10_IMPLEMENTED_STEPS, P7_R54_EV11_STEP_REF)
P7_R54_EV11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV12_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF: Final = "RATING_ROWS_NORMALIZED_BODYFREE_20260626"
P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF: Final = "RATING_ROW_NORMALIZATION_BLOCKED_20260626"
P7_R54_EV10_ALLOWED_RATING_NORMALIZATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF,
    P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF,
)
P7_R54_EV10_RATING_ROW_NORMALIZATION_REF: Final = "r54_ev10_rating_row_normalization_bodyfree_20260626"
P7_R54_EV10_RATING_ROW_NORMALIZATION_POLICY_REF: Final = (
    "bodyfree_rating_rows_from_ev09_sanitized_selection_rows_no_machine_scoring_20260626"
)
P7_R54_EV10_RATING_ROW_SOURCE_REF: Final = "ev09_sanitized_external_local_reviewer_selection_only"
P7_R54_EV10_READY_REASON_REF: Final = "r54_ev10_24_rating_rows_normalized_bodyfree"
P7_R54_EV10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev10_blocked_until_ev09_sanitized_rows_ready"
P7_R54_EV10_RATING_SCORE_MIN: Final = 0.0
P7_R54_EV10_RATING_SCORE_MAX: Final = 1.0
P7_R54_EV10_VERDICT_BLOCKER_CONSISTENT_REF: Final = "ev10_verdict_blocker_consistency_passed"

P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF: Final = "READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE_20260626"
P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF: Final = "READFEEL_EXECUTION_BLOCKER_INGESTION_BLOCKED_20260626"
P7_R54_EV11_ALLOWED_BLOCKER_INGESTION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF,
    P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF,
)
P7_R54_EV11_BLOCKER_INGESTION_REF: Final = "r54_ev11_readfeel_execution_blocker_ingestion_bodyfree_20260626"
P7_R54_EV11_BLOCKER_INGESTION_POLICY_REF: Final = (
    "readfeel_and_execution_blockers_separated_from_ev10_rating_rows_bodyfree_20260626"
)
P7_R54_EV11_READY_REASON_REF: Final = "r54_ev11_readfeel_and_execution_blockers_separated_bodyfree"
P7_R54_EV11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev11_blocked_until_ev10_rating_rows_ready"
P7_R54_EV11_BLOCKER_STATUS_REFS: Final[tuple[str, ...]] = ("open", "closed")
P7_R54_EV11_READFEEL_BLOCKER_KIND_REF: Final = "p5_history_line_readfeel_blocker"
P7_R54_EV11_EXECUTION_BLOCKER_KIND_REF: Final = "review_execution_boundary_blocker"

P7_R54_EV_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "rating_row_ref",
    "review_result_row_ref",
    "review_session_id",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "reviewer_ref",
    "reviewed_at_ref",
    "axis_scores",
    "axis_score_count",
    "axis_score_average",
    "axis_score_min",
    "axis_score_max",
    "target_thresholds",
    "below_target_axis_refs",
    "below_target_axis_count",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "readfeel_blocker_count",
    "execution_blocker_ids",
    "execution_blocker_count",
    "question_need_primary_class",
    "repair_required_refs",
    "rating_source_ref",
    "verdict_blocker_consistency_ref",
    "pass_requires_no_blocker",
    "red_or_repair_requires_blocker_or_reason",
    "body_removed",
    "rating_row_is_bodyfree",
    "reviewer_free_text_included",
    "raw_body_included",
    "comment_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_EV_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev09_schema_version",
    "ev09_material_ref",
    "ev09_next_required_step",
    "ev09_sanitized_review_result_intake_status",
    "ev09_rating_row_normalization_allowed_next",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op12_helper_ref",
    "existing_op12_schema_version",
    "existing_op12_operation_current_refs",
    "existing_op12_current_refs_are_historical_here",
    "existing_op12_reused_as_actual_rating_basis",
    "existing_op12_reused_as_actual_normalization_basis",
    "existing_op12_structural_contract_reused",
    "required_case_count",
    "sanitized_review_result_row_count",
    "rating_row_normalization_status",
    "rating_row_normalization_ref",
    "rating_row_normalization_policy_ref",
    "rating_row_normalization_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_rows",
    "rating_row_count",
    "reviewed_case_count",
    "rating_row_refs",
    "rating_row_ref_count",
    "rating_row_refs_unique",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "case_ref_ids",
    "case_ref_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "rating_row_schema_version",
    "rating_row_required_field_refs",
    "rating_axis_refs",
    "rating_axis_target_thresholds",
    "rating_score_min",
    "rating_score_max",
    "allowed_verdict_refs",
    "score_option_refs",
    "readfeel_blocker_id_refs",
    "readfeel_blocker_id_option_refs",
    "execution_blocker_id_refs",
    "execution_blocker_id_option_refs",
    "sanitized_reason_ids_only",
    "blocker_ids_only",
    "missing_axis_scores_pass_allowed",
    "extra_rating_axis_allowed",
    "machine_auto_score_allowed",
    "machine_metrics_used_for_readfeel_allowed",
    "reviewer_free_text_bodyfree_allowed",
    "execution_blocker_not_mixed_into_readfeel_verdict",
    "red_or_repair_requires_blocker_or_reason",
    "blocked_or_not_reviewable_must_use_execution_blocker_row",
    "pass_requires_targets_and_no_blockers",
    "rating_rows_are_bodyfree",
    "all_axes_present",
    "axis_score_range_valid",
    "verdict_allowed",
    "all_required_rating_rows_present",
    "rating_case_ref_sets_match_sanitized_intake",
    "verdict_counts",
    "axis_score_averages",
    "rating_consistency_issue_rows",
    "rating_consistency_issue_count",
    "pass_with_any_blocker_detected",
    "pass_below_axis_target_detected",
    "red_or_repair_without_blocker_or_reason_detected",
    "readfeel_blocker_row_candidate_count",
    "execution_blocker_row_candidate_count",
    "readfeel_blocker_execution_blocker_ingestion_allowed_next",
    "blocker_ingestion_allowed_next",
    "rating_rows_normalized_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "question_observation_row_count",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "blocker_row_ref",
    "review_session_id",
    "rating_row_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "reviewer_ref",
    "readfeel_blocker_id",
    "blocker_kind_ref",
    "blocker_status_ref",
    "source_verdict",
    "raw_body_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_EV_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "execution_blocker_row_ref",
    "review_session_id",
    "source_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "execution_blocker_id",
    "execution_blocker_kind_ref",
    "execution_blocker_status_ref",
    "execution_blocker_does_not_assign_readfeel_verdict",
    "raw_body_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_EV_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev10_schema_version",
    "ev10_material_ref",
    "ev10_next_required_step",
    "ev10_rating_row_normalization_status",
    "ev10_blocker_ingestion_allowed_next",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op13_helper_ref",
    "existing_op13_schema_version",
    "existing_op13_operation_current_refs",
    "existing_op13_current_refs_are_historical_here",
    "existing_op13_reused_as_actual_blocker_ingestion_basis",
    "existing_op13_reused_as_actual_ingestion_basis",
    "existing_op13_structural_contract_reused",
    "required_case_count",
    "rating_row_count",
    "blocker_ingestion_status",
    "blocker_ingestion_ref",
    "blocker_ingestion_policy_ref",
    "blocker_ingestion_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "readfeel_blocker_row_schema_version",
    "execution_blocker_row_schema_version",
    "readfeel_blocker_row_required_field_refs",
    "execution_blocker_row_required_field_refs",
    "readfeel_blocker_id_refs",
    "execution_blocker_id_refs",
    "blocker_status_refs",
    "readfeel_blocker_rows",
    "execution_blocker_rows",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "readfeel_blocker_counts",
    "execution_blocker_counts",
    "rating_packet_ref_ids",
    "rating_case_ref_ids",
    "rating_blind_case_ids",
    "readfeel_blocker_rows_normalized",
    "execution_blocker_rows_normalized",
    "readfeel_and_execution_blockers_separated",
    "execution_blockers_do_not_assign_readfeel_verdict",
    "execution_blocker_rows_do_not_assign_readfeel_verdict",
    "execution_blocker_not_mixed_into_readfeel_verdict",
    "execution_blocker_cases_do_not_promote_p5_confirmed_candidate",
    "execution_blocker_open_blocks_p5_confirmed_candidate",
    "p5_confirmed_candidate_blocked_by_open_execution_blockers",
    "rating_missing_maps_to_execution_blocker_not_red",
    "local_root_missing_maps_to_execution_blocker_not_red",
    "disposal_failed_maps_to_execution_blocker_not_red",
    "body_free_leak_maps_to_execution_blocker_not_red",
    "readfeel_blocker_row_builder_ready",
    "execution_blocker_row_builder_ready",
    "rating_rows_preserved_from_ev10",
    "rating_row_refs_preserved",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "question_observation_row_count",
    "disposal_verified",
    "question_need_observation_row_normalization_allowed_next",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev10_false_flag_refs() -> tuple[str, ...]:
    return tuple(key for key in P7_R54_EV_FALSE_FLAG_REFS if key != "actual_rating_rows_materialized_here")


def _ev11_false_flag_refs() -> tuple[str, ...]:
    return tuple(key for key in P7_R54_EV_FALSE_FLAG_REFS if key != "actual_rating_rows_materialized_here")


def _ev10_axis_average(scores: Mapping[str, Any]) -> float:
    numeric_scores = [float(safe_mapping(scores).get(axis, 0.0)) for axis in P7_R54_EV08_RATING_AXIS_REFS]
    return round(sum(numeric_scores) / len(P7_R54_EV08_RATING_AXIS_REFS), 4)


def _ev10_axis_score_extreme(scores: Mapping[str, Any], *, kind: str) -> float:
    numeric_scores = [float(safe_mapping(scores).get(axis, 0.0)) for axis in P7_R54_EV08_RATING_AXIS_REFS]
    return round(min(numeric_scores) if kind == "min" else max(numeric_scores), 4)


def _ev10_below_target_axis_refs(scores: Mapping[str, Any]) -> list[str]:
    mapping = safe_mapping(scores)
    refs: list[str] = []
    for axis in P7_R54_EV08_RATING_AXIS_REFS:
        try:
            score = float(mapping.get(axis))
        except (TypeError, ValueError):
            refs.append(axis)
            continue
        if score < float(P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS[axis]):
            refs.append(axis)
    return refs


def _ev10_verdict_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {verdict: 0 for verdict in P7_R54_EV08_VERDICT_OPTION_REFS}
    for row in rows:
        verdict = clean_identifier(safe_mapping(row).get("verdict"), max_length=80)
        if verdict in counts:
            counts[verdict] += 1
    return counts


def _ev10_axis_score_averages(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not rows:
        return {axis: 0.0 for axis in P7_R54_EV08_RATING_AXIS_REFS}
    totals = {axis: 0.0 for axis in P7_R54_EV08_RATING_AXIS_REFS}
    for row in rows:
        scores = safe_mapping(safe_mapping(row).get("axis_scores"))
        for axis in P7_R54_EV08_RATING_AXIS_REFS:
            totals[axis] += float(scores.get(axis, 0.0))
    return {axis: round(total / len(rows), 4) for axis, total in totals.items()}


def _build_p7_r54_ev10_rating_row_from_sanitized_row(row: Mapping[str, Any]) -> dict[str, Any]:
    source = safe_mapping(row)
    _assert_p7_r54_ev09_sanitized_review_result_row(source)
    scores = safe_mapping(source.get("axis_scores"))
    below_target_axis_refs = _ev10_below_target_axis_refs(scores)
    readfeel_blocker_ids = dedupe_identifiers(source.get("readfeel_blocker_ids") or [], limit=20, max_length=160)
    execution_blocker_ids = dedupe_identifiers(source.get("execution_blocker_ids") or [], limit=20, max_length=160)
    verdict = clean_identifier(source.get("verdict"), max_length=80)
    sanitized_reason_ids = dedupe_identifiers(source.get("sanitized_reason_ids") or [], limit=20, max_length=160)
    rating_row = {
        "schema_version": P7_R54_EV_RATING_ROW_SCHEMA_VERSION,
        "rating_row_ref": f"r54ev10-rating-row-{clean_identifier(source.get('review_result_row_ref'), default='review-row', max_length=140)}",
        "review_result_row_ref": clean_identifier(source.get("review_result_row_ref"), max_length=180),
        "review_session_id": _safe_review_session_id(source.get("review_session_id")),
        "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
        "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
        "family": clean_identifier(source.get("family"), max_length=180),
        "case_role": clean_identifier(source.get("case_role"), max_length=180),
        "reviewer_ref": clean_identifier(source.get("reviewer_ref"), max_length=120),
        "reviewed_at_ref": clean_identifier(source.get("reviewed_at_ref"), default="coarse_reviewed_at_ref_20260626", max_length=160),
        "axis_scores": {axis: float(scores.get(axis)) for axis in P7_R54_EV08_RATING_AXIS_REFS},
        "axis_score_count": len(P7_R54_EV08_RATING_AXIS_REFS),
        "axis_score_average": _ev10_axis_average(scores),
        "axis_score_min": _ev10_axis_score_extreme(scores, kind="min"),
        "axis_score_max": _ev10_axis_score_extreme(scores, kind="max"),
        "target_thresholds": dict(P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": below_target_axis_refs,
        "below_target_axis_count": len(below_target_axis_refs),
        "verdict": verdict,
        "sanitized_reason_ids": sanitized_reason_ids,
        "readfeel_blocker_ids": readfeel_blocker_ids,
        "readfeel_blocker_count": len(readfeel_blocker_ids),
        "execution_blocker_ids": execution_blocker_ids,
        "execution_blocker_count": len(execution_blocker_ids),
        "question_need_primary_class": clean_identifier(source.get("question_need_primary_class"), max_length=160),
        "repair_required_refs": dedupe_identifiers(source.get("repair_required_refs") or [], limit=20, max_length=160),
        "rating_source_ref": P7_R54_EV10_RATING_ROW_SOURCE_REF,
        "verdict_blocker_consistency_ref": P7_R54_EV10_VERDICT_BLOCKER_CONSISTENT_REF,
        "pass_requires_no_blocker": True,
        "red_or_repair_requires_blocker_or_reason": True,
        "body_removed": source.get("body_removed") is True,
        "rating_row_is_bodyfree": True,
        "reviewer_free_text_included": False,
        "raw_body_included": False,
        "comment_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_ev10_rating_row_bodyfree_contract(rating_row)
    return rating_row


def assert_p7_r54_ev10_rating_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_EV_RATING_ROW_REQUIRED_FIELD_REFS, source="p7_r54_ev10_rating_row")
    if data.get("schema_version") != P7_R54_EV_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV10 rating row schema version changed")
    if data.get("rating_row_is_bodyfree") is not True or data.get("body_free") is not True:
        raise ValueError("R54 EV10 rating row must be body-free")
    scores = safe_mapping(data.get("axis_scores"))
    if tuple(scores.keys()) != P7_R54_EV08_RATING_AXIS_REFS:
        raise ValueError("R54 EV10 rating row axis keys changed")
    if data.get("axis_score_count") != len(P7_R54_EV08_RATING_AXIS_REFS):
        raise ValueError("R54 EV10 rating row axis count changed")
    for axis in P7_R54_EV08_RATING_AXIS_REFS:
        score = scores.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError("R54 EV10 rating score type invalid")
        if not P7_R54_EV10_RATING_SCORE_MIN <= float(score) <= P7_R54_EV10_RATING_SCORE_MAX:
            raise ValueError("R54 EV10 rating score out of range")
    if safe_mapping(data.get("target_thresholds")) != P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("R54 EV10 target thresholds changed")
    below_target = _ev10_below_target_axis_refs(scores)
    if data.get("below_target_axis_refs") != below_target or data.get("below_target_axis_count") != len(below_target):
        raise ValueError("R54 EV10 below-target axis refs changed")
    if data.get("verdict") not in P7_R54_EV08_VERDICT_OPTION_REFS:
        raise ValueError("R54 EV10 rating row verdict option changed")
    readfeel_blockers = dedupe_identifiers(data.get("readfeel_blocker_ids") or [], limit=20, max_length=160)
    execution_blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=20, max_length=160)
    if not set(readfeel_blockers).issubset(set(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS)):
        raise ValueError("R54 EV10 readfeel blocker outside frozen EV08 options")
    if not set(execution_blockers).issubset(set(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS)):
        raise ValueError("R54 EV10 execution blocker outside frozen EV08 options")
    if data.get("readfeel_blocker_count") != len(readfeel_blockers) or data.get("execution_blocker_count") != len(execution_blockers):
        raise ValueError("R54 EV10 blocker counts changed")
    if data.get("rating_source_ref") != P7_R54_EV10_RATING_ROW_SOURCE_REF:
        raise ValueError("R54 EV10 rating source ref changed")
    if data.get("pass_requires_no_blocker") is not True or data.get("red_or_repair_requires_blocker_or_reason") is not True:
        raise ValueError("R54 EV10 verdict/blocker guard changed")
    for false_key in (
        "reviewer_free_text_included",
        "raw_body_included",
        "comment_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
        "body_hash_included",
        "packet_content_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV10 rating row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev10_rating_row")
    return True


def _ev10_rating_consistency_issue_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        data = safe_mapping(row)
        rating_row_ref = clean_identifier(data.get("rating_row_ref"), default="rating_row", max_length=180)
        verdict = clean_identifier(data.get("verdict"), max_length=80)
        readfeel_blockers = list(data.get("readfeel_blocker_ids") or [])
        execution_blockers = list(data.get("execution_blocker_ids") or [])
        below_target_axis_refs = list(data.get("below_target_axis_refs") or [])
        reason_ids = list(data.get("sanitized_reason_ids") or [])
        if verdict == "PASS" and (readfeel_blockers or execution_blockers):
            issues.append({"issue_id": "r54_ev10_pass_with_any_blocker_detected", "rating_row_ref": rating_row_ref})
        if verdict == "PASS" and below_target_axis_refs:
            issues.append({"issue_id": "r54_ev10_pass_below_axis_target_detected", "rating_row_ref": rating_row_ref})
        if verdict in {"REPAIR_REQUIRED", "RED"} and not readfeel_blockers and not reason_ids:
            issues.append({"issue_id": "r54_ev10_red_or_repair_without_blocker_or_reason_detected", "rating_row_ref": rating_row_ref})
    return issues


def build_p7_r54_ev10_rating_row_normalization(
    *,
    sanitized_review_result_row_intake: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev10_rating_row_normalization",
) -> dict[str, Any]:
    """Build EV10 body-free rating row normalization from EV09 sanitized rows."""

    ev09 = (
        safe_mapping(sanitized_review_result_row_intake)
        if sanitized_review_result_row_intake is not None
        else build_p7_r54_ev09_sanitized_review_result_row_intake()
    )
    assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(ev09)
    ev09_allows_next = bool(
        ev09.get("sanitized_review_result_intake_status") == P7_R54_EV09_INTAKE_READY_STATUS_REF
        and ev09.get("rating_row_normalization_allowed_next") is True
        and ev09.get("next_required_step") == P7_R54_EV10_STEP_REF
    )
    review_session_id = _safe_review_session_id(ev09.get("review_session_id"))
    normalized_rows = [
        _build_p7_r54_ev10_rating_row_from_sanitized_row(safe_mapping(row))
        for row in (ev09.get("sanitized_review_result_rows") or [])
    ] if ev09_allows_next else []
    blockers: list[str] = []
    if not ev09_allows_next:
        blockers.append("ev09_sanitized_review_result_rows_not_ready_for_rating_normalization")
    if ev09_allows_next and len(normalized_rows) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("rating_row_count_must_be_24")
    if ev09_allows_next and _ev05_case_refs(normalized_rows, "case_ref_id") != list(ev09.get("case_ref_ids") or []):
        blockers.append("rating_row_case_refs_must_match_ev09_sanitized_intake")
    if ev09_allows_next and _ev05_case_refs(normalized_rows, "packet_ref_id") != list(ev09.get("packet_ref_ids") or []):
        blockers.append("rating_row_packet_refs_must_match_ev09_sanitized_intake")
    consistency_issues = _ev10_rating_consistency_issue_rows(normalized_rows) if ev09_allows_next else []
    if consistency_issues:
        blockers.append("rating_row_verdict_blocker_consistency_failed")
    execution_blockers = dedupe_identifiers([*blockers, *(ev09.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    ready = bool(ev09_allows_next and len(normalized_rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT and not execution_blockers)
    rows = normalized_rows if ready else []
    rating_row_refs = _ev05_case_refs(rows, "rating_row_ref")
    packet_refs = _ev05_case_refs(rows, "packet_ref_id")
    case_refs = _ev05_case_refs(rows, "case_ref_id")
    blind_ids = _ev05_case_refs(rows, "blind_case_id")
    reason_refs = [P7_R54_EV10_READY_REASON_REF] if ready else dedupe_identifiers(
        [P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF, *execution_blockers], limit=100, max_length=180
    )
    material = {
        "schema_version": P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV10_STEP_REF,
        "operation_step_ref": P7_R54_EV10_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev10_rating_row_normalization", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev09_schema_version": P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        "ev09_material_ref": clean_identifier(ev09.get("material_id"), default="p7_r54_ev09_sanitized_review_result_row_intake", max_length=220),
        "ev09_next_required_step": clean_identifier(ev09.get("next_required_step"), default=P7_R54_EV09_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev09_sanitized_review_result_intake_status": clean_identifier(ev09.get("sanitized_review_result_intake_status"), default=P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF, max_length=180),
        "ev09_rating_row_normalization_allowed_next": ev09_allows_next,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op12_helper_ref": "build_p7_r54_op12_rating_row_normalization",
        "existing_op12_schema_version": r54op.P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "existing_op12_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op12_current_refs_are_historical_here": True,
        "existing_op12_reused_as_actual_rating_basis": False,
        "existing_op12_reused_as_actual_normalization_basis": False,
        "existing_op12_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "sanitized_review_result_row_count": int(ev09.get("sanitized_review_result_row_count") or 0) if ev09_allows_next else 0,
        "rating_row_normalization_status": P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF if ready else P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF,
        "rating_row_normalization_ref": P7_R54_EV10_RATING_ROW_NORMALIZATION_REF if ready else "rating_row_normalization_not_ready_bodyfree_20260626",
        "rating_row_normalization_policy_ref": P7_R54_EV10_RATING_ROW_NORMALIZATION_POLICY_REF,
        "rating_row_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else execution_blockers,
        "open_execution_blocker_ids": [] if ready else execution_blockers,
        "rating_rows": rows,
        "rating_row_count": len(rows),
        "reviewed_case_count": len(rows),
        "rating_row_refs": rating_row_refs,
        "rating_row_ref_count": len(rating_row_refs),
        "rating_row_refs_unique": _ev05_unique_non_empty(rating_row_refs) if ready else False,
        "packet_ref_ids": packet_refs,
        "packet_ref_count": len(packet_refs),
        "packet_ref_ids_unique": _ev05_unique_non_empty(packet_refs) if ready else False,
        "case_ref_ids": case_refs,
        "case_ref_count": len(case_refs),
        "case_ref_ids_unique": _ev05_unique_non_empty(case_refs) if ready else False,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": _ev05_unique_non_empty(blind_ids) if ready else False,
        "rating_row_schema_version": P7_R54_EV_RATING_ROW_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R54_EV_RATING_ROW_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(P7_R54_EV08_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS),
        "rating_score_min": P7_R54_EV10_RATING_SCORE_MIN,
        "rating_score_max": P7_R54_EV10_RATING_SCORE_MAX,
        "allowed_verdict_refs": list(P7_R54_EV08_VERDICT_OPTION_REFS),
        "score_option_refs": list(P7_R54_EV08_SCORE_OPTION_REFS),
        "readfeel_blocker_id_refs": list(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS),
        "readfeel_blocker_id_option_refs": list(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_refs": list(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_option_refs": list(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "sanitized_reason_ids_only": True,
        "blocker_ids_only": True,
        "missing_axis_scores_pass_allowed": False,
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "machine_metrics_used_for_readfeel_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "execution_blocker_not_mixed_into_readfeel_verdict": True,
        "red_or_repair_requires_blocker_or_reason": True,
        "blocked_or_not_reviewable_must_use_execution_blocker_row": True,
        "pass_requires_targets_and_no_blockers": True,
        "rating_rows_are_bodyfree": ready,
        "all_axes_present": bool(ready and all(set(safe_mapping(row.get("axis_scores")).keys()) == set(P7_R54_EV08_RATING_AXIS_REFS) for row in rows)),
        "axis_score_range_valid": bool(ready and all(P7_R54_EV10_RATING_SCORE_MIN <= float(safe_mapping(row.get("axis_scores")).get(axis, -1.0)) <= P7_R54_EV10_RATING_SCORE_MAX for row in rows for axis in P7_R54_EV08_RATING_AXIS_REFS)),
        "verdict_allowed": bool(ready and all(safe_mapping(row).get("verdict") in P7_R54_EV08_VERDICT_OPTION_REFS for row in rows)),
        "all_required_rating_rows_present": ready,
        "rating_case_ref_sets_match_sanitized_intake": ready,
        "verdict_counts": _ev10_verdict_counts(rows),
        "axis_score_averages": _ev10_axis_score_averages(rows),
        "rating_consistency_issue_rows": consistency_issues if ev09_allows_next else [],
        "rating_consistency_issue_count": len(consistency_issues) if ev09_allows_next else 0,
        "pass_with_any_blocker_detected": any(safe_mapping(row).get("issue_id") == "r54_ev10_pass_with_any_blocker_detected" for row in consistency_issues) if ev09_allows_next else False,
        "pass_below_axis_target_detected": any(safe_mapping(row).get("issue_id") == "r54_ev10_pass_below_axis_target_detected" for row in consistency_issues) if ev09_allows_next else False,
        "red_or_repair_without_blocker_or_reason_detected": any(safe_mapping(row).get("issue_id") == "r54_ev10_red_or_repair_without_blocker_or_reason_detected" for row in consistency_issues) if ev09_allows_next else False,
        "readfeel_blocker_row_candidate_count": sum(1 for row in rows if safe_mapping(row).get("readfeel_blocker_ids")),
        "execution_blocker_row_candidate_count": sum(1 for row in rows if safe_mapping(row).get("execution_blocker_ids")),
        "readfeel_blocker_execution_blocker_ingestion_allowed_next": ready,
        "blocker_ingestion_allowed_next": ready,
        "rating_rows_normalized_here": ready,
        "actual_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV10_IMPLEMENTED_STEPS if ready else (ev09.get("implemented_steps") or P7_R54_EV09_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV10_NOT_YET_IMPLEMENTED_STEPS if ready else (ev09.get("not_yet_implemented_steps") or P7_R54_EV09_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV11_STEP_REF if ready else P7_R54_EV10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": ready,
    }
    assert_p7_r54_ev10_rating_row_normalization_contract(material)
    return material


def assert_p7_r54_ev10_rating_row_normalization_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS, source="p7_r54_ev10_rating_row_normalization")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_EV10_STEP_REF,
        operation_step_ref=P7_R54_EV10_STEP_REF,
        source="p7_r54_ev10_rating_row_normalization",
        false_flag_refs=_ev10_false_flag_refs(),
    )
    if data.get("ev09_schema_version") != P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION:
        raise ValueError("R54 EV10 EV09 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV10 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op12_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV10 existing OP12 refs changed")
    if data.get("existing_op12_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV10 must classify existing OP12 refs as historical")
    if data.get("existing_op12_reused_as_actual_rating_basis") is not False:
        raise ValueError("R54 EV10 must not reuse 20260625 OP12 as actual rating basis")
    if data.get("existing_op12_reused_as_actual_normalization_basis") is not False:
        raise ValueError("R54 EV10 must not reuse 20260625 OP12 as actual normalization basis")
    if data.get("existing_op12_structural_contract_reused") is not True:
        raise ValueError("R54 EV10 must reuse only OP12 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV10 required case count changed")
    if data.get("score_option_refs") != list(P7_R54_EV08_SCORE_OPTION_REFS):
        raise ValueError("R54 EV10 score option refs changed")
    if data.get("readfeel_blocker_id_option_refs") != list(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS):
        raise ValueError("R54 EV10 readfeel blocker option refs changed")
    if data.get("execution_blocker_id_option_refs") != list(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS):
        raise ValueError("R54 EV10 execution blocker option refs changed")
    if data.get("rating_row_normalization_status") not in P7_R54_EV10_ALLOWED_RATING_NORMALIZATION_STATUS_REFS:
        raise ValueError("R54 EV10 normalization status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV10 open blockers must match execution blockers")
    for row in data.get("rating_rows") or []:
        assert_p7_r54_ev10_rating_row_bodyfree_contract(safe_mapping(row))
    for true_key in (
        "sanitized_reason_ids_only",
        "blocker_ids_only",
        "execution_blocker_not_mixed_into_readfeel_verdict",
        "red_or_repair_requires_blocker_or_reason",
        "blocked_or_not_reviewable_must_use_execution_blocker_row",
        "pass_requires_targets_and_no_blockers",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV10 must keep {true_key}=True")
    for false_key in (
        "missing_axis_scores_pass_allowed",
        "extra_rating_axis_allowed",
        "machine_auto_score_allowed",
        "machine_metrics_used_for_readfeel_allowed",
        "reviewer_free_text_bodyfree_allowed",
        "actual_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete",
        "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV10 must keep {false_key}=False")
    if data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV10 must not normalize question observation rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV10 must block completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV10 must block P6/P8/release promotion")
    if data.get("rating_row_schema_version") != P7_R54_EV_RATING_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV10 rating row schema reference changed")
    if tuple(data.get("rating_row_required_field_refs") or ()) != P7_R54_EV_RATING_ROW_REQUIRED_FIELD_REFS:
        raise ValueError("R54 EV10 rating row required fields changed")
    if tuple(data.get("rating_axis_refs") or ()) != P7_R54_EV08_RATING_AXIS_REFS:
        raise ValueError("R54 EV10 rating axes changed")
    if safe_mapping(data.get("rating_axis_target_thresholds")) != P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("R54 EV10 rating thresholds changed")
    if data.get("rating_score_min") != P7_R54_EV10_RATING_SCORE_MIN or data.get("rating_score_max") != P7_R54_EV10_RATING_SCORE_MAX:
        raise ValueError("R54 EV10 score bounds changed")
    ready = data.get("rating_row_normalization_status") == P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
    if data.get("actual_rating_rows_materialized_here") is not ready:
        raise ValueError("R54 EV10 rating row materialized flag must match readiness")
    if data.get("rating_consistency_issue_count") != len(data.get("rating_consistency_issue_rows") or []):
        raise ValueError("R54 EV10 consistency issue count mismatch")
    if ready:
        if data.get("ev09_rating_row_normalization_allowed_next") is not True or data.get("ev09_next_required_step") != P7_R54_EV10_STEP_REF:
            raise ValueError("R54 EV10 ready normalization requires EV09 allowance")
        if blockers:
            raise ValueError("R54 EV10 ready normalization must not carry blockers")
        if data.get("rating_row_normalization_ref") != P7_R54_EV10_RATING_ROW_NORMALIZATION_REF:
            raise ValueError("R54 EV10 normalization ref changed")
        if data.get("rating_row_normalization_policy_ref") != P7_R54_EV10_RATING_ROW_NORMALIZATION_POLICY_REF:
            raise ValueError("R54 EV10 normalization policy changed")
        if data.get("rating_row_normalization_reason_refs") != [P7_R54_EV10_READY_REASON_REF]:
            raise ValueError("R54 EV10 ready reason refs changed")
        if data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("reviewed_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV10 ready normalization must contain 24 rating rows")
        if data.get("rating_row_refs_unique") is not True or data.get("packet_ref_ids_unique") is not True or data.get("case_ref_ids_unique") is not True or data.get("blind_case_ids_unique") is not True:
            raise ValueError("R54 EV10 ready normalization must preserve unique refs")
        if data.get("rating_rows_are_bodyfree") is not True or data.get("all_required_rating_rows_present") is not True or data.get("rating_case_ref_sets_match_sanitized_intake") is not True:
            raise ValueError("R54 EV10 ready normalization must keep body-free complete rating rows")
        if data.get("all_axes_present") is not True or data.get("axis_score_range_valid") is not True or data.get("verdict_allowed") is not True:
            raise ValueError("R54 EV10 ready normalization must prove axes/range/verdict validity")
        if data.get("rating_consistency_issue_rows") != []:
            raise ValueError("R54 EV10 ready normalization must not carry rating consistency issues")
        if data.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is not True or data.get("blocker_ingestion_allowed_next") is not True:
            raise ValueError("R54 EV10 ready normalization must allow EV11 next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV10_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV10 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV11_STEP_REF:
            raise ValueError("R54 EV10 ready normalization must point to EV11")
    else:
        if data.get("rating_row_normalization_status") != P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV10 blocked status changed")
        if data.get("rating_rows") != [] or data.get("rating_row_count") != 0:
            raise ValueError("R54 EV10 blocked normalization must not materialize rating rows")
        if data.get("actual_rating_rows_materialized_here") is not False:
            raise ValueError("R54 EV10 blocked normalization must not materialize rating rows")
        if data.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is not False or data.get("blocker_ingestion_allowed_next") is not False:
            raise ValueError("R54 EV10 blocked normalization must not allow EV11")
        if not blockers:
            raise ValueError("R54 EV10 blocked normalization must carry blockers")
        if data.get("next_required_step") != P7_R54_EV10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV10 blocked normalization must point to repair")
    return True


def _ev11_single_id_counts(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        item = clean_identifier(safe_mapping(row).get(key), max_length=180)
        if item:
            counts[item] = counts.get(item, 0) + 1
    return counts


def build_p7_r54_ev11_readfeel_blocker_row_bodyfree(*, rating_row: Mapping[str, Any], blocker_id: Any, blocker_status_ref: Any = "open") -> dict[str, Any]:
    row = safe_mapping(rating_row)
    assert_p7_r54_ev10_rating_row_bodyfree_contract(row)
    blocker_ref = clean_identifier(blocker_id, default="", max_length=160)
    if blocker_ref not in P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS:
        raise ValueError("R54 EV11 readfeel blocker row must use frozen EV08 blocker id")
    status_ref = clean_identifier(blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_EV11_BLOCKER_STATUS_REFS:
        raise ValueError("R54 EV11 readfeel blocker row status changed")
    out = {
        "schema_version": P7_R54_EV_READFEEL_BLOCKER_ROW_SCHEMA_VERSION,
        "blocker_row_ref": f"r54ev11-readfeel-blocker-{clean_identifier(row.get('rating_row_ref'), default='rating-row', max_length=120)}-{blocker_ref}",
        "review_session_id": _safe_review_session_id(row.get("review_session_id")),
        "rating_row_ref": clean_identifier(row.get("rating_row_ref"), max_length=180),
        "packet_ref_id": clean_identifier(row.get("packet_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(row.get("blind_case_id"), max_length=180),
        "case_ref_id": clean_identifier(row.get("case_ref_id"), max_length=180),
        "family": clean_identifier(row.get("family"), max_length=180),
        "case_role": clean_identifier(row.get("case_role"), max_length=180),
        "reviewer_ref": clean_identifier(row.get("reviewer_ref"), max_length=120),
        "readfeel_blocker_id": blocker_ref,
        "blocker_kind_ref": P7_R54_EV11_READFEEL_BLOCKER_KIND_REF,
        "blocker_status_ref": status_ref,
        "source_verdict": clean_identifier(row.get("verdict"), max_length=80),
        "raw_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_ev11_readfeel_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_ev11_readfeel_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_EV_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="p7_r54_ev11_readfeel_blocker_row")
    if data.get("schema_version") != P7_R54_EV_READFEEL_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV11 readfeel blocker row schema version changed")
    if data.get("readfeel_blocker_id") not in P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS:
        raise ValueError("R54 EV11 readfeel blocker id outside frozen EV08 options")
    if data.get("blocker_kind_ref") != P7_R54_EV11_READFEEL_BLOCKER_KIND_REF:
        raise ValueError("R54 EV11 readfeel blocker kind changed")
    if data.get("blocker_status_ref") not in P7_R54_EV11_BLOCKER_STATUS_REFS:
        raise ValueError("R54 EV11 readfeel blocker status changed")
    for false_key in (
        "raw_body_included",
        "comment_text_included",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
        "body_hash_included",
        "packet_content_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV11 readfeel blocker row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV11 readfeel blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev11_readfeel_blocker_row")
    return True


def build_p7_r54_ev11_execution_blocker_row_bodyfree(
    *,
    source_ref: Any,
    execution_blocker_id: Any,
    review_session_id: Any = P7_R54_EV_DEFAULT_REVIEW_SESSION_ID,
    packet_ref_id: Any = "execution_blocker_no_packet_ref",
    blind_case_id: Any = "execution_blocker_no_blind_case_id",
    case_ref_id: Any = "execution_blocker_no_case_ref_id",
    family: Any = "operation_execution_boundary",
    case_role: Any = "operation_execution_boundary",
    execution_blocker_status_ref: Any = "open",
) -> dict[str, Any]:
    blocker_ref = clean_identifier(execution_blocker_id, default="", max_length=180)
    if blocker_ref not in P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS:
        raise ValueError("R54 EV11 execution blocker row must use frozen EV08 execution blocker id")
    status_ref = clean_identifier(execution_blocker_status_ref, default="open", max_length=40)
    if status_ref not in P7_R54_EV11_BLOCKER_STATUS_REFS:
        raise ValueError("R54 EV11 execution blocker row status changed")
    src = clean_identifier(source_ref, default="operation_execution_blocker", max_length=180)
    out = {
        "schema_version": P7_R54_EV_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION,
        "execution_blocker_row_ref": f"r54ev11-execution-blocker-{src}-{blocker_ref}",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_ref": src,
        "packet_ref_id": clean_identifier(packet_ref_id, default="execution_blocker_no_packet_ref", max_length=180),
        "blind_case_id": clean_identifier(blind_case_id, default="execution_blocker_no_blind_case_id", max_length=180),
        "case_ref_id": clean_identifier(case_ref_id, default="execution_blocker_no_case_ref_id", max_length=180),
        "family": clean_identifier(family, default="operation_execution_boundary", max_length=180),
        "case_role": clean_identifier(case_role, default="operation_execution_boundary", max_length=180),
        "execution_blocker_id": blocker_ref,
        "execution_blocker_kind_ref": P7_R54_EV11_EXECUTION_BLOCKER_KIND_REF,
        "execution_blocker_status_ref": status_ref,
        "execution_blocker_does_not_assign_readfeel_verdict": True,
        "raw_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_ev11_execution_blocker_row_bodyfree_contract(out)
    return out


def assert_p7_r54_ev11_execution_blocker_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(data, required=P7_R54_EV_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="p7_r54_ev11_execution_blocker_row")
    if data.get("schema_version") != P7_R54_EV_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV11 execution blocker row schema version changed")
    if data.get("execution_blocker_id") not in P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS:
        raise ValueError("R54 EV11 execution blocker id outside frozen EV08 options")
    if data.get("execution_blocker_kind_ref") != P7_R54_EV11_EXECUTION_BLOCKER_KIND_REF:
        raise ValueError("R54 EV11 execution blocker kind changed")
    if data.get("execution_blocker_status_ref") not in P7_R54_EV11_BLOCKER_STATUS_REFS:
        raise ValueError("R54 EV11 execution blocker status changed")
    if data.get("execution_blocker_does_not_assign_readfeel_verdict") is not True:
        raise ValueError("R54 EV11 execution blocker must not assign readfeel verdict")
    for false_key in (
        "raw_body_included",
        "comment_text_included",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
        "body_hash_included",
        "packet_content_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV11 execution blocker row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV11 execution blocker row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev11_execution_blocker_row")
    return True


def _ev11_blocker_rows_from_rating_rows(rating_rows: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    readfeel_rows: list[dict[str, Any]] = []
    execution_rows: list[dict[str, Any]] = []
    for rating_row in rating_rows:
        row = safe_mapping(rating_row)
        assert_p7_r54_ev10_rating_row_bodyfree_contract(row)
        for blocker_id in row.get("readfeel_blocker_ids") or []:
            readfeel_rows.append(build_p7_r54_ev11_readfeel_blocker_row_bodyfree(rating_row=row, blocker_id=blocker_id))
        for blocker_id in row.get("execution_blocker_ids") or []:
            execution_rows.append(
                build_p7_r54_ev11_execution_blocker_row_bodyfree(
                    source_ref=clean_identifier(row.get("rating_row_ref"), default="rating_row", max_length=180),
                    execution_blocker_id=blocker_id,
                    review_session_id=row.get("review_session_id"),
                    packet_ref_id=row.get("packet_ref_id"),
                    blind_case_id=row.get("blind_case_id"),
                    case_ref_id=row.get("case_ref_id"),
                    family=row.get("family"),
                    case_role=row.get("case_role"),
                )
            )
    return readfeel_rows, execution_rows


def build_p7_r54_ev11_blocker_ingestion(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev11_blocker_ingestion",
) -> dict[str, Any]:
    """Build EV11 body-free readfeel/execution blocker ingestion from EV10 rows."""

    ev10 = (
        safe_mapping(rating_row_normalization)
        if rating_row_normalization is not None
        else build_p7_r54_ev10_rating_row_normalization()
    )
    assert_p7_r54_ev10_rating_row_normalization_contract(ev10)
    ev10_ready = bool(
        ev10.get("rating_row_normalization_status") == P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
        and ev10.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is True
        and ev10.get("blocker_ingestion_allowed_next") is True
        and ev10.get("next_required_step") == P7_R54_EV11_STEP_REF
    )
    rating_rows = [safe_mapping(row) for row in (ev10.get("rating_rows") or [])] if ev10_ready else []
    readfeel_rows, execution_rows = _ev11_blocker_rows_from_rating_rows(rating_rows) if ev10_ready else ([], [])
    blockers = [] if ev10_ready else dedupe_identifiers(
        ["rating_row_normalization_not_ready_for_blocker_ingestion", *(ev10.get("open_execution_blocker_ids") or [])],
        limit=100,
        max_length=180,
    )
    open_readfeel_count = sum(1 for row in readfeel_rows if row.get("blocker_status_ref") == "open")
    open_execution_count = sum(1 for row in execution_rows if row.get("execution_blocker_status_ref") == "open")
    ready = bool(ev10_ready)
    reason_refs = [P7_R54_EV11_READY_REASON_REF] if ready else dedupe_identifiers(
        [P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF, *blockers], limit=100, max_length=180
    )
    material = {
        "schema_version": P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV11_STEP_REF,
        "operation_step_ref": P7_R54_EV11_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev11_blocker_ingestion", max_length=220),
        "review_session_id": _safe_review_session_id(ev10.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev10_schema_version": P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "ev10_material_ref": clean_identifier(ev10.get("material_id"), default="p7_r54_ev10_rating_row_normalization", max_length=220),
        "ev10_next_required_step": clean_identifier(ev10.get("next_required_step"), default=P7_R54_EV10_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev10_rating_row_normalization_status": clean_identifier(ev10.get("rating_row_normalization_status"), default=P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "ev10_blocker_ingestion_allowed_next": ev10_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op13_helper_ref": "build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion",
        "existing_op13_schema_version": r54op.P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "existing_op13_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op13_current_refs_are_historical_here": True,
        "existing_op13_reused_as_actual_blocker_ingestion_basis": False,
        "existing_op13_reused_as_actual_ingestion_basis": False,
        "existing_op13_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": len(rating_rows),
        "blocker_ingestion_status": P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF if ready else P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF,
        "blocker_ingestion_ref": P7_R54_EV11_BLOCKER_INGESTION_REF if ready else "blocker_ingestion_not_ready_bodyfree_20260626",
        "blocker_ingestion_policy_ref": P7_R54_EV11_BLOCKER_INGESTION_POLICY_REF,
        "blocker_ingestion_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "readfeel_blocker_row_schema_version": P7_R54_EV_READFEEL_BLOCKER_ROW_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R54_EV_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION,
        "readfeel_blocker_row_required_field_refs": list(P7_R54_EV_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R54_EV_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS),
        "execution_blocker_id_refs": list(P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS),
        "blocker_status_refs": list(P7_R54_EV11_BLOCKER_STATUS_REFS),
        "readfeel_blocker_rows": readfeel_rows,
        "execution_blocker_rows": execution_rows,
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": open_readfeel_count,
        "open_execution_blocker_count": open_execution_count,
        "readfeel_blocker_counts": _ev11_single_id_counts(readfeel_rows, "readfeel_blocker_id"),
        "execution_blocker_counts": _ev11_single_id_counts(execution_rows, "execution_blocker_id"),
        "rating_packet_ref_ids": _ev05_case_refs(rating_rows, "packet_ref_id"),
        "rating_case_ref_ids": _ev05_case_refs(rating_rows, "case_ref_id"),
        "rating_blind_case_ids": _ev05_case_refs(rating_rows, "blind_case_id"),
        "readfeel_blocker_rows_normalized": ready,
        "execution_blocker_rows_normalized": ready,
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "execution_blocker_rows_do_not_assign_readfeel_verdict": True,
        "execution_blocker_not_mixed_into_readfeel_verdict": True,
        "execution_blocker_cases_do_not_promote_p5_confirmed_candidate": True,
        "execution_blocker_open_blocks_p5_confirmed_candidate": True,
        "p5_confirmed_candidate_blocked_by_open_execution_blockers": open_execution_count > 0,
        "rating_missing_maps_to_execution_blocker_not_red": True,
        "local_root_missing_maps_to_execution_blocker_not_red": True,
        "disposal_failed_maps_to_execution_blocker_not_red": True,
        "body_free_leak_maps_to_execution_blocker_not_red": True,
        "readfeel_blocker_row_builder_ready": ready,
        "execution_blocker_row_builder_ready": ready,
        "rating_rows_preserved_from_ev10": ready,
        "rating_row_refs_preserved": ready,
        "actual_blocker_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_review_evidence_complete": False,
        "question_observation_row_count": 0,
        "disposal_verified": False,
        "question_need_observation_row_normalization_allowed_next": ready,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV11_IMPLEMENTED_STEPS if ready else (ev10.get("implemented_steps") or P7_R54_EV10_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV11_NOT_YET_IMPLEMENTED_STEPS if ready else (ev10.get("not_yet_implemented_steps") or P7_R54_EV10_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV12_NEXT_REQUIRED_STEP_REF if ready else P7_R54_EV11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ready and ev10.get("actual_rating_rows_materialized_here") is True),
    }
    assert_p7_r54_ev11_blocker_ingestion_contract(material)
    return material


def assert_p7_r54_ev11_blocker_ingestion_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV_BLOCKER_INGESTION_REQUIRED_FIELD_REFS, source="p7_r54_ev11_blocker_ingestion")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION,
        policy_section=P7_R54_EV11_STEP_REF,
        operation_step_ref=P7_R54_EV11_STEP_REF,
        source="p7_r54_ev11_blocker_ingestion",
        false_flag_refs=_ev11_false_flag_refs(),
    )
    if data.get("ev10_schema_version") != P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 EV11 EV10 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV11 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op13_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV11 existing OP13 refs changed")
    if data.get("existing_op13_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV11 must classify existing OP13 refs as historical")
    if data.get("existing_op13_reused_as_actual_blocker_ingestion_basis") is not False:
        raise ValueError("R54 EV11 must not reuse 20260625 OP13 as actual blocker ingestion basis")
    if data.get("existing_op13_reused_as_actual_ingestion_basis") is not False:
        raise ValueError("R54 EV11 must not reuse 20260625 OP13 as actual ingestion basis")
    if data.get("existing_op13_structural_contract_reused") is not True:
        raise ValueError("R54 EV11 must reuse only OP13 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV11 required case count changed")
    if data.get("blocker_ingestion_status") not in P7_R54_EV11_ALLOWED_BLOCKER_INGESTION_STATUS_REFS:
        raise ValueError("R54 EV11 blocker ingestion status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV11 open execution blockers must match materialization blockers")
    for row in data.get("readfeel_blocker_rows") or []:
        assert_p7_r54_ev11_readfeel_blocker_row_bodyfree_contract(safe_mapping(row))
    for row in data.get("execution_blocker_rows") or []:
        assert_p7_r54_ev11_execution_blocker_row_bodyfree_contract(safe_mapping(row))
    if data.get("readfeel_blocker_row_count") != len(data.get("readfeel_blocker_rows") or []):
        raise ValueError("R54 EV11 readfeel blocker row count mismatch")
    if data.get("execution_blocker_row_count") != len(data.get("execution_blocker_rows") or []):
        raise ValueError("R54 EV11 execution blocker row count mismatch")
    if data.get("open_readfeel_blocker_count") != sum(1 for row in data.get("readfeel_blocker_rows") or [] if safe_mapping(row).get("blocker_status_ref") == "open"):
        raise ValueError("R54 EV11 open readfeel blocker count mismatch")
    if data.get("open_execution_blocker_count") != sum(1 for row in data.get("execution_blocker_rows") or [] if safe_mapping(row).get("execution_blocker_status_ref") == "open"):
        raise ValueError("R54 EV11 open execution blocker count mismatch")
    for true_key in (
        "readfeel_and_execution_blockers_separated",
        "execution_blockers_do_not_assign_readfeel_verdict",
        "execution_blocker_rows_do_not_assign_readfeel_verdict",
        "execution_blocker_not_mixed_into_readfeel_verdict",
        "execution_blocker_cases_do_not_promote_p5_confirmed_candidate",
        "execution_blocker_open_blocks_p5_confirmed_candidate",
        "rating_missing_maps_to_execution_blocker_not_red",
        "local_root_missing_maps_to_execution_blocker_not_red",
        "disposal_failed_maps_to_execution_blocker_not_red",
        "body_free_leak_maps_to_execution_blocker_not_red",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV11 must keep {true_key}=True")
    if data.get("p5_confirmed_candidate_blocked_by_open_execution_blockers") is not (data.get("open_execution_blocker_count") > 0):
        raise ValueError("R54 EV11 P5-confirmed blocker flag must reflect open execution blockers")
    for false_key in (
        "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete",
        "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV11 must keep {false_key}=False")
    if data.get("question_observation_row_count") != 0:
        raise ValueError("R54 EV11 must not normalize question observation rows")
    if data.get("human_review_completion_claim_blocked_here") is not True or data.get("actual_human_review_completion_claim_blocked_here") is not True:
        raise ValueError("R54 EV11 must block completion claims")
    if data.get("p6_p8_release_promotion_blocked_here") is not True:
        raise ValueError("R54 EV11 must block P6/P8/release promotion")
    ready = data.get("blocker_ingestion_status") == P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF
    if data.get("actual_blocker_rows_materialized_here") is not ready:
        raise ValueError("R54 EV11 blocker materialization flag must match readiness")
    if ready:
        if data.get("ev10_blocker_ingestion_allowed_next") is not True or data.get("ev10_next_required_step") != P7_R54_EV11_STEP_REF:
            raise ValueError("R54 EV11 ready ingestion requires EV10 allowance")
        if blockers:
            raise ValueError("R54 EV11 ready ingestion must not carry materialization blockers")
        if data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV11 ready ingestion requires 24 rating rows")
        if len(data.get("rating_packet_ref_ids") or []) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or len(data.get("rating_case_ref_ids") or []) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or len(data.get("rating_blind_case_ids") or []) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV11 ready ingestion must preserve 24 rating case refs")
        if data.get("actual_rating_rows_materialized_here") is not True or data.get("actual_blocker_rows_materialized_here") is not True:
            raise ValueError("R54 EV11 ready ingestion must preserve rating rows and materialize blocker rows")
        if data.get("readfeel_blocker_row_builder_ready") is not True or data.get("execution_blocker_row_builder_ready") is not True or data.get("rating_rows_preserved_from_ev10") is not True or data.get("rating_row_refs_preserved") is not True:
            raise ValueError("R54 EV11 ready ingestion builder flags changed")
        if data.get("readfeel_blocker_rows_normalized") is not True or data.get("execution_blocker_rows_normalized") is not True:
            raise ValueError("R54 EV11 ready ingestion must normalize blocker rows")
        if data.get("blocker_ingestion_ref") != P7_R54_EV11_BLOCKER_INGESTION_REF:
            raise ValueError("R54 EV11 blocker ingestion ref changed")
        if data.get("blocker_ingestion_policy_ref") != P7_R54_EV11_BLOCKER_INGESTION_POLICY_REF:
            raise ValueError("R54 EV11 blocker ingestion policy changed")
        if data.get("blocker_ingestion_reason_refs") != [P7_R54_EV11_READY_REASON_REF]:
            raise ValueError("R54 EV11 ready reason refs changed")
        if data.get("question_need_observation_row_normalization_allowed_next") is not True:
            raise ValueError("R54 EV11 ready ingestion must allow EV12 next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV11_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV12_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV11 ready ingestion must point to EV12")
    else:
        if data.get("blocker_ingestion_status") != P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV11 blocked ingestion status changed")
        if data.get("actual_blocker_rows_materialized_here") is not False:
            raise ValueError("R54 EV11 blocked ingestion must not materialize blocker rows")
        if data.get("readfeel_blocker_row_builder_ready") is not False or data.get("execution_blocker_row_builder_ready") is not False:
            raise ValueError("R54 EV11 blocked ingestion must not claim row builders ready")
        if data.get("question_need_observation_row_normalization_allowed_next") is not False:
            raise ValueError("R54 EV11 blocked ingestion must not allow EV12")
        if not blockers or data.get("next_required_step") != P7_R54_EV11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV11 blocked ingestion must point to repair")
    return True


P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev12_question_need_observation_row.bodyfree.v1"
)
P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev12_question_need_observation_row_normalization.bodyfree.v1"
)
P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev13_rating_question_consistency_issue_row.bodyfree.v1"
)
P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev13_rating_question_consistency_guard.bodyfree.v1"
)

P7_R54_EV12_STEP_REF: Final = P7_R54_EV12_NEXT_REQUIRED_STEP_REF
P7_R54_EV13_STEP_REF: Final = "R54-EV-13_rating_question_consistency_guard"
P7_R54_EV14_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-14_pause_abort_expiration_protocol"
P7_R54_EV12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV11_IMPLEMENTED_STEPS, P7_R54_EV12_STEP_REF)
P7_R54_EV12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV13_STEP_REF,)
P7_R54_EV13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV12_IMPLEMENTED_STEPS, P7_R54_EV13_STEP_REF)
P7_R54_EV13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV14_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF: Final = (
    "QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE_20260626"
)
P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF: Final = (
    "QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_BLOCKED_20260626"
)
P7_R54_EV12_ALLOWED_NORMALIZATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF,
    P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF,
)
P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_REF: Final = (
    "r54_ev12_question_need_observation_row_normalization_bodyfree_20260626"
)
P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_POLICY_REF: Final = (
    "bodyfree_question_need_observation_rows_no_question_text_no_p8_logic_20260626"
)
P7_R54_EV12_READY_REASON_REF: Final = "r54_ev12_24_question_need_observation_rows_normalized_bodyfree"
P7_R54_EV12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "r54_ev12_blocked_until_ev11_ev10_ev09_ready_for_question_observation_rows"
)
P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "no_question_needed_emlis_can_observe",
    "question_may_reduce_overread_risk",
    "question_would_make_immediate_observation_heavy",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_EV12_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)

P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF: Final = (
    "RATING_QUESTION_CONSISTENCY_GUARD_READY_BODYFREE_20260626"
)
P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF: Final = (
    "RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED_20260626"
)
P7_R54_EV13_ALLOWED_CONSISTENCY_GUARD_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF,
    P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF,
)
P7_R54_EV13_CONSISTENCY_GUARD_REF: Final = "r54_ev13_rating_question_consistency_guard_bodyfree_20260626"
P7_R54_EV13_CONSISTENCY_GUARD_POLICY_REF: Final = (
    "rating_question_consistency_guard_prevents_p5_repair_escape_to_p8_material_20260626"
)
P7_R54_EV13_READY_REASON_REF: Final = "r54_ev13_rating_question_consistency_guard_passed_bodyfree"
P7_R54_EV13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "r54_ev13_blocked_until_rating_question_consistency_repair_before_pause_abort_protocol"
)
P7_R54_EV13_CONSISTENCY_ISSUE_ID_REFS: Final[tuple[str, ...]] = (
    "r54_ev13_red_or_repair_with_no_question_needed_observation",
    "r54_ev13_repair_required_with_p8_material_candidate",
    "r54_ev13_pass_with_not_question_repair_required",
    "r54_ev13_insufficient_material_with_pass_or_no_execution_blocker",
    "r54_ev13_rating_question_case_ref_set_mismatch",
)
P7_R54_EV13_CONSISTENCY_ISSUE_KIND_REFS: Final[tuple[str, ...]] = (
    "rating_question_observation_semantic_mismatch",
    "p5_repair_hidden_by_question_candidate",
    "p5_inconclusive_or_execution_boundary_mismatch",
    "rating_question_case_integrity_issue",
)
P7_R54_EV13_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "continue_after_consistency_guard",
    "p5_repair_return_required_later",
    "r54_operation_inconclusive_required_later",
    "rating_question_row_repair_required",
)

P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "question_observation_row_ref",
    "review_session_id",
    "review_result_row_ref",
    "rating_row_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "family",
    "case_role",
    "reviewer_ref",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    "p8_material_candidate_requested",
    "p8_material_candidate_allowed",
    "p8_material_candidate_safe_for_handoff",
    "not_question_repair_required",
    "insufficient_material_execution_blocker",
    "question_observation_row_is_bodyfree",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_free_text_included",
    "raw_body_included",
    "comment_text_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev11_schema_version",
    "ev11_material_ref",
    "ev11_next_required_step",
    "ev11_blocker_ingestion_status",
    "ev11_question_observation_normalization_allowed_next",
    "ev10_schema_version",
    "ev10_material_ref",
    "ev10_rating_row_normalization_status",
    "ev09_schema_version",
    "ev09_material_ref",
    "ev09_sanitized_review_result_intake_status",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op14_helper_ref",
    "existing_op14_schema_version",
    "existing_op14_operation_current_refs",
    "existing_op14_current_refs_are_historical_here",
    "existing_op14_reused_as_actual_question_observation_basis",
    "existing_op14_reused_as_actual_normalization_basis",
    "existing_op14_structural_contract_reused",
    "required_case_count",
    "question_observation_normalization_status",
    "question_observation_normalization_ref",
    "question_observation_normalization_policy_ref",
    "question_observation_normalization_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "sanitized_review_result_row_count",
    "rating_row_count",
    "blocker_ingestion_ready_for_question_rows",
    "question_observation_rows",
    "question_observation_row_count",
    "question_observation_row_refs",
    "question_observation_row_ref_count",
    "question_observation_row_refs_unique",
    "case_ref_ids",
    "case_ref_count",
    "case_ref_ids_unique",
    "packet_ref_ids",
    "packet_ref_count",
    "packet_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "question_observation_row_schema_version",
    "question_observation_row_required_field_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "plan_candidate_flag_refs",
    "p8_material_candidate_primary_class_refs",
    "not_question_repair_primary_class_refs",
    "question_need_observation_rows_are_bodyfree",
    "question_text_absent_for_all_rows",
    "draft_question_text_absent_for_all_rows",
    "reviewer_free_text_absent_for_all_rows",
    "raw_body_absent_for_all_rows",
    "comment_text_absent_for_all_rows",
    "local_path_absent_for_all_rows",
    "body_hash_absent_for_all_rows",
    "question_text_included_allowed",
    "draft_question_text_included_allowed",
    "reviewer_free_text_included_allowed",
    "raw_body_allowed",
    "comment_text_allowed",
    "local_path_allowed",
    "body_hash_allowed",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "row_case_ref_sets_match_review_intake",
    "row_case_ref_sets_match_rating_rows",
    "all_required_question_need_observation_rows_present",
    "primary_class_ambiguity_one_question_fit_are_canonical_refs",
    "question_text_or_draft_text_saved_here",
    "question_need_primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "p8_material_candidate_requested_row_count",
    "p8_material_candidate_allowed_row_count",
    "p8_material_candidate_allowed_primary_class_counts",
    "not_question_repair_required_count",
    "insufficient_material_execution_blocker_count",
    "rating_rows_preserved_from_ev10",
    "blocker_rows_preserved_from_ev11",
    "rating_question_consistency_guard_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "consistency_issue_row_ref",
    "review_session_id",
    "rating_row_ref",
    "question_observation_row_ref",
    "packet_ref_id",
    "blind_case_id",
    "case_ref_id",
    "issue_id",
    "issue_kind_ref",
    "decision_direction_ref",
    "issue_status_ref",
    "raw_body_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    "body_hash_included",
    "packet_content_included",
    "machine_auto_score_used",
    "machine_metrics_used_for_readfeel",
    "body_free",
)

P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev12_schema_version",
    "ev12_material_ref",
    "ev12_next_required_step",
    "ev12_question_observation_normalization_status",
    "ev12_consistency_guard_allowed_next",
    "ev10_schema_version",
    "ev10_material_ref",
    "ev10_rating_row_normalization_status",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op15_helper_ref",
    "existing_op15_schema_version",
    "existing_op15_operation_current_refs",
    "existing_op15_current_refs_are_historical_here",
    "existing_op15_reused_as_actual_consistency_guard_basis",
    "existing_op15_structural_contract_reused",
    "required_case_count",
    "rating_question_consistency_guard_status",
    "rating_question_consistency_guard_ref",
    "rating_question_consistency_guard_policy_ref",
    "rating_question_consistency_guard_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_row_count",
    "question_observation_row_count",
    "rating_question_case_ref_sets_match",
    "all_required_rating_and_question_rows_present",
    "rating_question_consistency_issue_row_schema_version",
    "rating_question_consistency_issue_row_required_field_refs",
    "rating_question_consistency_issue_rows",
    "consistency_issue_count",
    "consistency_issue_id_refs",
    "consistency_issue_kind_refs",
    "decision_direction_refs",
    "red_or_repair_with_no_question_needed_count",
    "repair_required_with_p8_material_candidate_count",
    "pass_with_not_question_repair_required_count",
    "insufficient_material_with_pass_or_no_execution_blocker_count",
    "case_ref_set_mismatch_count",
    "consistency_issue_direction_counts",
    "p5_confirmed_candidate_blocked_by_consistency_issues",
    "p5_decision_candidate_not_materialized_here",
    "issues_route_to_p5_repair_return_or_inconclusive_later",
    "p8_material_candidates_do_not_hide_p5_repair_here",
    "p5_surface_repair_not_promoted_to_p8_material",
    "not_question_repair_not_promoted_to_p8_material",
    "ready_for_pause_abort_expiration_protocol",
    "rating_rows_preserved_from_ev10",
    "question_observation_rows_preserved_from_ev12",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_verified",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev12_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_EV_FALSE_FLAG_REFS
        if key not in {"actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}
    )


def _ev13_false_flag_refs() -> tuple[str, ...]:
    return _ev12_false_flag_refs()


def _ev12_question_plan_flags(value: Any) -> dict[str, bool]:
    flags = safe_mapping(value)
    return {
        flag: (bool(flags.get(flag, False)) if flag != "p8_implementation_spec_finalized_here" else False)
        for flag in P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS
    }


def _ev12_question_row_flags(primary_class: str, repair_required_refs: Sequence[str], plan_candidate_flags: Mapping[str, Any]) -> tuple[bool, bool, bool, bool]:
    repair_refs = set(dedupe_identifiers(repair_required_refs, limit=20, max_length=160))
    repair_without_no_repair = repair_refs - {"no_repair_required"}
    not_question_repair = bool(primary_class in P7_R54_EV12_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS or repair_without_no_repair)
    insufficient = primary_class == "insufficient_material_execution_blocker"
    p8_requested = bool(safe_mapping(plan_candidate_flags).get("p8_design_material_candidate") is True)
    p8_allowed = bool(
        p8_requested
        and primary_class in P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS
        and not not_question_repair
        and not insufficient
    )
    return p8_requested, p8_allowed, not_question_repair, insufficient


def _ev12_p8_material_candidate_allowed_primary_class_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        data = safe_mapping(row)
        if data.get("p8_material_candidate_allowed") is not True:
            continue
        primary_class_ref = clean_identifier(data.get("question_need_primary_class"), max_length=160)
        if primary_class_ref not in P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS:
            continue
        counts[primary_class_ref] = counts.get(primary_class_ref, 0) + 1
    return counts


def _ev12_question_need_observation_row_from_sanitized_row(
    row: Mapping[str, Any],
    *,
    rating_row_ref: Any,
) -> dict[str, Any]:
    source = safe_mapping(row)
    _assert_p7_r54_ev09_sanitized_review_result_row(source)
    primary_class = clean_identifier(source.get("question_need_primary_class"), max_length=160)
    if primary_class not in P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 EV12 question observation primary class outside frozen options")
    ambiguity_refs = dedupe_identifiers(source.get("ambiguity_kind_refs") or [], limit=20, max_length=160)
    if not ambiguity_refs or not set(ambiguity_refs).issubset(set(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("R54 EV12 ambiguity refs outside frozen options")
    one_question_fit = clean_identifier(source.get("one_question_fit_ref"), max_length=160)
    if one_question_fit not in P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 EV12 one-question fit ref outside frozen options")
    repair_refs = dedupe_identifiers(source.get("repair_required_refs") or [], limit=20, max_length=160)
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("R54 EV12 repair refs outside frozen options")
    plan_flags = _ev12_question_plan_flags(source.get("plan_candidate_flags"))
    p8_requested, p8_allowed, not_question_repair, insufficient = _ev12_question_row_flags(
        primary_class, repair_refs, plan_flags
    )
    question_row = {
        "schema_version": P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "question_observation_row_ref": f"r54ev12-question-row-{clean_identifier(source.get('review_result_row_ref'), default='review-row', max_length=140)}",
        "review_session_id": _safe_review_session_id(source.get("review_session_id")),
        "review_result_row_ref": clean_identifier(source.get("review_result_row_ref"), max_length=180),
        "rating_row_ref": clean_identifier(rating_row_ref, default="rating_row_ref", max_length=180),
        "packet_ref_id": clean_identifier(source.get("packet_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(source.get("blind_case_id"), max_length=180),
        "case_ref_id": clean_identifier(source.get("case_ref_id"), max_length=180),
        "family": clean_identifier(source.get("family"), max_length=180),
        "case_role": clean_identifier(source.get("case_role"), max_length=180),
        "reviewer_ref": clean_identifier(source.get("reviewer_ref"), max_length=120),
        "question_need_primary_class": primary_class,
        "ambiguity_kind_refs": ambiguity_refs,
        "one_question_fit_ref": one_question_fit,
        "repair_required_refs": repair_refs,
        "plan_candidate_flags": plan_flags,
        "p8_material_candidate_requested": p8_requested,
        "p8_material_candidate_allowed": p8_allowed,
        "p8_material_candidate_safe_for_handoff": p8_allowed,
        "not_question_repair_required": not_question_repair,
        "insufficient_material_execution_blocker": insufficient,
        "question_observation_row_is_bodyfree": True,
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "raw_body_included": False,
        "comment_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_ev12_question_need_observation_row_bodyfree_contract(question_row)
    return question_row


def assert_p7_r54_ev12_question_need_observation_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_ev12_question_need_observation_row",
    )
    if data.get("schema_version") != P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV12 question observation row schema version changed")
    if data.get("question_observation_row_is_bodyfree") is not True or data.get("body_free") is not True:
        raise ValueError("R54 EV12 question observation row must remain body-free")
    if data.get("question_need_primary_class") not in P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 EV12 primary class outside frozen refs")
    if not set(data.get("ambiguity_kind_refs") or []).issubset(set(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS)):
        raise ValueError("R54 EV12 ambiguity refs outside frozen refs")
    if data.get("one_question_fit_ref") not in P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 EV12 one-question fit outside frozen refs")
    repair_refs = data.get("repair_required_refs") or []
    if not repair_refs or not set(repair_refs).issubset(set(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS)):
        raise ValueError("R54 EV12 repair refs outside frozen refs")
    flags = safe_mapping(data.get("plan_candidate_flags"))
    if tuple(flags.keys()) != P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("R54 EV12 plan candidate flag keys changed")
    if flags.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R54 EV12 must not finalize P8 implementation spec")
    p8_requested, p8_allowed, not_question_repair, insufficient = _ev12_question_row_flags(
        clean_identifier(data.get("question_need_primary_class"), max_length=160),
        repair_refs,
        flags,
    )
    if data.get("p8_material_candidate_requested") is not p8_requested:
        raise ValueError("R54 EV12 P8 material requested flag mismatch")
    if data.get("p8_material_candidate_allowed") is not p8_allowed:
        raise ValueError("R54 EV12 P8 material allowed flag mismatch")
    if data.get("p8_material_candidate_safe_for_handoff") is not p8_allowed:
        raise ValueError("R54 EV12 P8 material safe handoff flag mismatch")
    if data.get("not_question_repair_required") is not not_question_repair:
        raise ValueError("R54 EV12 not-question repair flag mismatch")
    if data.get("insufficient_material_execution_blocker") is not insufficient:
        raise ValueError("R54 EV12 insufficient material flag mismatch")
    for false_key in (
        "question_text_included",
        "draft_question_text_included",
        "reviewer_free_text_included",
        "raw_body_included",
        "comment_text_included",
        "local_path_included",
        "body_hash_included",
        "packet_content_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV12 question row must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev12_question_need_observation_row")
    return True


def _ev12_single_id_counts(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = row.get(key)
        if isinstance(value, (list, tuple)):
            for item in value:
                ident = clean_identifier(item, max_length=180)
                if ident:
                    counts[ident] = counts.get(ident, 0) + 1
        else:
            ident = clean_identifier(value, max_length=180)
            if ident:
                counts[ident] = counts.get(ident, 0) + 1
    return counts


def build_p7_r54_ev12_question_need_observation_row_normalization(
    *,
    blocker_ingestion: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    sanitized_review_result_row_intake: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev12_question_need_observation_row_normalization",
) -> dict[str, Any]:
    """Build EV12 body-free question need observation rows without question text."""

    ev11 = safe_mapping(blocker_ingestion) if blocker_ingestion is not None else build_p7_r54_ev11_blocker_ingestion()
    assert_p7_r54_ev11_blocker_ingestion_contract(ev11)
    ev10 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else build_p7_r54_ev10_rating_row_normalization()
    assert_p7_r54_ev10_rating_row_normalization_contract(ev10)
    ev09 = safe_mapping(sanitized_review_result_row_intake) if sanitized_review_result_row_intake is not None else build_p7_r54_ev09_sanitized_review_result_row_intake()
    assert_p7_r54_ev09_sanitized_review_result_row_intake_contract(ev09)

    ev11_ready = bool(
        ev11.get("blocker_ingestion_status") == P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF
        and ev11.get("question_need_observation_row_normalization_allowed_next") is True
        and ev11.get("next_required_step") == P7_R54_EV12_STEP_REF
    )
    ev10_ready = bool(
        ev10.get("rating_row_normalization_status") == P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
        and ev10.get("rating_row_count") == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and ev10.get("readfeel_blocker_execution_blocker_ingestion_allowed_next") is True
    )
    ev09_ready = bool(
        ev09.get("sanitized_review_result_intake_status") == P7_R54_EV09_INTAKE_READY_STATUS_REF
        and ev09.get("sanitized_review_result_row_count") == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and ev09.get("rating_row_normalization_allowed_next") is True
    )
    blockers: list[str] = []
    if not ev11_ready:
        blockers.append("blocker_ingestion_not_ready_for_question_need_observation_rows")
    if not ev10_ready:
        blockers.append("rating_row_normalization_not_ready_for_question_need_observation_rows")
    if not ev09_ready:
        blockers.append("sanitized_review_result_rows_not_ready_for_question_need_observation_rows")

    rating_rows = [safe_mapping(row) for row in (ev10.get("rating_rows") or [])] if ev10_ready else []
    sanitized_rows = [safe_mapping(row) for row in (ev09.get("sanitized_review_result_rows") or [])] if ev09_ready else []
    rating_by_review_result_ref = {
        clean_identifier(row.get("review_result_row_ref"), default="", max_length=180): clean_identifier(row.get("rating_row_ref"), default="", max_length=180)
        for row in rating_rows
    }
    question_rows: list[dict[str, Any]] = []
    if ev11_ready and ev10_ready and ev09_ready:
        for row in sanitized_rows:
            review_result_ref = clean_identifier(row.get("review_result_row_ref"), default="", max_length=180)
            question_rows.append(
                _ev12_question_need_observation_row_from_sanitized_row(
                    row,
                    rating_row_ref=rating_by_review_result_ref.get(review_result_ref, ""),
                )
            )
    row_case_ref_sets_match_review_intake = bool(_ev05_case_refs(question_rows, "case_ref_id") == list(ev09.get("case_ref_ids") or [])) if question_rows else False
    row_case_ref_sets_match_rating_rows = bool(_ev05_case_refs(question_rows, "case_ref_id") == list(ev10.get("case_ref_ids") or [])) if question_rows else False
    all_required = bool(
        len(question_rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and row_case_ref_sets_match_review_intake
        and row_case_ref_sets_match_rating_rows
    )
    canonical = all(
        row.get("question_need_primary_class") in P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS
        and set(row.get("ambiguity_kind_refs") or []).issubset(set(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS))
        and row.get("one_question_fit_ref") in P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS
        and set(row.get("repair_required_refs") or []).issubset(set(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS))
        for row in question_rows
    ) if question_rows else False
    if question_rows and not all_required:
        blockers.append("question_observation_row_count_or_case_ref_set_mismatch")
    if question_rows and not canonical:
        blockers.append("question_observation_canonical_refs_failed")
    blockers = dedupe_identifiers(blockers, limit=100, max_length=180)
    ready = bool(ev11_ready and ev10_ready and ev09_ready and all_required and canonical and not blockers)
    rows = question_rows if ready else []
    reason_refs = [P7_R54_EV12_READY_REASON_REF] if ready else dedupe_identifiers(
        [P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, *blockers],
        limit=100,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV12_STEP_REF,
        "operation_step_ref": P7_R54_EV12_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev12_question_need_observation_row_normalization", max_length=220),
        "review_session_id": _safe_review_session_id(ev11.get("review_session_id") or ev10.get("review_session_id") or ev09.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev11_schema_version": P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION,
        "ev11_material_ref": clean_identifier(ev11.get("material_id"), default="p7_r54_ev11_blocker_ingestion", max_length=220),
        "ev11_next_required_step": clean_identifier(ev11.get("next_required_step"), default=P7_R54_EV11_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev11_blocker_ingestion_status": clean_identifier(ev11.get("blocker_ingestion_status"), default=P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF, max_length=180),
        "ev11_question_observation_normalization_allowed_next": ev11_ready,
        "ev10_schema_version": P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "ev10_material_ref": clean_identifier(ev10.get("material_id"), default="p7_r54_ev10_rating_row_normalization", max_length=220),
        "ev10_rating_row_normalization_status": clean_identifier(ev10.get("rating_row_normalization_status"), default=P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "ev09_schema_version": P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        "ev09_material_ref": clean_identifier(ev09.get("material_id"), default="p7_r54_ev09_sanitized_review_result_row_intake", max_length=220),
        "ev09_sanitized_review_result_intake_status": clean_identifier(ev09.get("sanitized_review_result_intake_status"), default=P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op14_helper_ref": "build_p7_r54_op14_question_need_observation_normalization",
        "existing_op14_schema_version": r54op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "existing_op14_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op14_current_refs_are_historical_here": True,
        "existing_op14_reused_as_actual_question_observation_basis": False,
        "existing_op14_reused_as_actual_normalization_basis": False,
        "existing_op14_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "question_observation_normalization_status": P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF if ready else P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF,
        "question_observation_normalization_ref": P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_REF if ready else "question_observation_normalization_not_ready_bodyfree_20260626",
        "question_observation_normalization_policy_ref": P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_POLICY_REF,
        "question_observation_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "sanitized_review_result_row_count": len(sanitized_rows) if ev09_ready else 0,
        "rating_row_count": len(rating_rows) if ev10_ready else 0,
        "blocker_ingestion_ready_for_question_rows": ev11_ready,
        "question_observation_rows": rows,
        "question_observation_row_count": len(rows),
        "question_observation_row_refs": _ev05_case_refs(rows, "question_observation_row_ref"),
        "question_observation_row_ref_count": len(rows),
        "question_observation_row_refs_unique": (_ev05_unique_non_empty(_ev05_case_refs(rows, "question_observation_row_ref")) and len(_ev05_case_refs(rows, "question_observation_row_ref")) == len(rows)) if rows else False,
        "case_ref_ids": _ev05_case_refs(rows, "case_ref_id"),
        "case_ref_count": len(rows),
        "case_ref_ids_unique": (_ev05_unique_non_empty(_ev05_case_refs(rows, "case_ref_id")) and len(_ev05_case_refs(rows, "case_ref_id")) == len(rows)) if rows else False,
        "packet_ref_ids": _ev05_case_refs(rows, "packet_ref_id"),
        "packet_ref_count": len(rows),
        "packet_ref_ids_unique": (_ev05_unique_non_empty(_ev05_case_refs(rows, "packet_ref_id")) and len(_ev05_case_refs(rows, "packet_ref_id")) == len(rows)) if rows else False,
        "blind_case_ids": _ev05_case_refs(rows, "blind_case_id"),
        "blind_case_id_count": len(rows),
        "blind_case_ids_unique": (_ev05_unique_non_empty(_ev05_case_refs(rows, "blind_case_id")) and len(_ev05_case_refs(rows, "blind_case_id")) == len(rows)) if rows else False,
        "question_observation_row_schema_version": P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
        "question_observation_row_required_field_refs": list(P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS),
        "question_need_primary_class_refs": list(P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS),
        "ambiguity_kind_refs": list(P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS),
        "one_question_fit_refs": list(P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS),
        "repair_required_ref_refs": list(P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS),
        "plan_candidate_flag_refs": list(P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS),
        "p8_material_candidate_primary_class_refs": list(P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS),
        "not_question_repair_primary_class_refs": list(P7_R54_EV12_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS),
        "question_need_observation_rows_are_bodyfree": True,
        "question_text_absent_for_all_rows": True,
        "draft_question_text_absent_for_all_rows": True,
        "reviewer_free_text_absent_for_all_rows": True,
        "raw_body_absent_for_all_rows": True,
        "comment_text_absent_for_all_rows": True,
        "local_path_absent_for_all_rows": True,
        "body_hash_absent_for_all_rows": True,
        "question_text_included_allowed": False,
        "draft_question_text_included_allowed": False,
        "reviewer_free_text_included_allowed": False,
        "raw_body_allowed": False,
        "comment_text_allowed": False,
        "local_path_allowed": False,
        "body_hash_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_storage_schema_implemented": False,
        "question_answer_persistence_implemented": False,
        "question_plan_guard_implemented": False,
        "row_case_ref_sets_match_review_intake": bool(ready and row_case_ref_sets_match_review_intake),
        "row_case_ref_sets_match_rating_rows": bool(ready and row_case_ref_sets_match_rating_rows),
        "all_required_question_need_observation_rows_present": bool(ready and all_required),
        "primary_class_ambiguity_one_question_fit_are_canonical_refs": bool(ready and canonical),
        "question_text_or_draft_text_saved_here": False,
        "question_need_primary_class_counts": _ev12_single_id_counts(rows, "question_need_primary_class"),
        "ambiguity_kind_counts": _ev12_single_id_counts(rows, "ambiguity_kind_refs"),
        "one_question_fit_counts": _ev12_single_id_counts(rows, "one_question_fit_ref"),
        "repair_required_counts": _ev12_single_id_counts(rows, "repair_required_refs"),
        "plan_candidate_flag_counts": {flag: sum(1 for row in rows if safe_mapping(row.get("plan_candidate_flags")).get(flag) is True) for flag in P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS},
        "p8_material_candidate_requested_row_count": sum(1 for row in rows if row.get("p8_material_candidate_requested") is True),
        "p8_material_candidate_allowed_row_count": sum(1 for row in rows if row.get("p8_material_candidate_allowed") is True),
        "p8_material_candidate_allowed_primary_class_counts": _ev12_p8_material_candidate_allowed_primary_class_counts(rows),
        "not_question_repair_required_count": sum(1 for row in rows if row.get("not_question_repair_required") is True),
        "insufficient_material_execution_blocker_count": sum(1 for row in rows if row.get("insufficient_material_execution_blocker") is True),
        "rating_rows_preserved_from_ev10": bool(ready and ev10.get("actual_rating_rows_materialized_here") is True),
        "blocker_rows_preserved_from_ev11": bool(ready and ev11.get("actual_blocker_rows_materialized_here") is True),
        "rating_question_consistency_guard_allowed_next": ready,
        "actual_rating_rows_materialized_here": bool(ready and ev10.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and ev11.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV12_IMPLEMENTED_STEPS if ready else (ev11.get("implemented_steps") or P7_R54_EV11_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV12_NOT_YET_IMPLEMENTED_STEPS if ready else (ev11.get("not_yet_implemented_steps") or P7_R54_EV11_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV13_STEP_REF if ready else P7_R54_EV12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ready and ev10.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and ev11.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
    }
    assert_p7_r54_ev12_question_need_observation_row_normalization_contract(material)
    return material


def assert_p7_r54_ev12_question_need_observation_row_normalization_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="p7_r54_ev12_question_need_observation_row_normalization",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_EV12_STEP_REF,
        operation_step_ref=P7_R54_EV12_STEP_REF,
        source="p7_r54_ev12_question_need_observation_row_normalization",
        false_flag_refs=_ev12_false_flag_refs(),
    )
    if data.get("ev11_schema_version") != P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION:
        raise ValueError("R54 EV12 EV11 schema reference changed")
    if data.get("ev10_schema_version") != P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 EV12 EV10 schema reference changed")
    if data.get("ev09_schema_version") != P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION:
        raise ValueError("R54 EV12 EV09 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV12 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op14_operation_current_refs")) != safe_mapping(r54op.P7_R54_OPERATION_CURRENT_REFS):
        raise ValueError("R54 EV12 existing OP14 refs changed")
    if data.get("existing_op14_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV12 must classify existing OP14 refs as historical")
    if data.get("existing_op14_reused_as_actual_question_observation_basis") is not False:
        raise ValueError("R54 EV12 must not reuse 20260625 OP14 as actual question observation basis")
    if data.get("existing_op14_reused_as_actual_normalization_basis") is not False:
        raise ValueError("R54 EV12 must not reuse 20260625 OP14 as actual normalization basis")
    if data.get("existing_op14_structural_contract_reused") is not True:
        raise ValueError("R54 EV12 must reuse only OP14 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV12 required case count changed")
    if data.get("question_observation_normalization_status") not in P7_R54_EV12_ALLOWED_NORMALIZATION_STATUS_REFS:
        raise ValueError("R54 EV12 normalization status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV12 open blockers must match materialization blockers")
    rows = [safe_mapping(row) for row in (data.get("question_observation_rows") or [])]
    for row in rows:
        assert_p7_r54_ev12_question_need_observation_row_bodyfree_contract(row)
    if data.get("question_observation_row_count") != len(rows):
        raise ValueError("R54 EV12 question row count mismatch")
    if data.get("question_observation_row_ref_count") != len(data.get("question_observation_row_refs") or []):
        raise ValueError("R54 EV12 question row ref count mismatch")
    row_refs = list(data.get("question_observation_row_refs") or [])
    case_refs = list(data.get("case_ref_ids") or [])
    row_ref_unique = len(row_refs) == len(set(row_refs))
    case_ref_unique = len(case_refs) == len(set(case_refs))
    if rows and data.get("question_observation_row_refs_unique") is not row_ref_unique:
        raise ValueError("R54 EV12 question row ref uniqueness flag mismatch")
    if rows and data.get("case_ref_ids_unique") is not case_ref_unique:
        raise ValueError("R54 EV12 case ref uniqueness flag mismatch")
    if tuple(data.get("question_need_primary_class_refs") or ()) != P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS:
        raise ValueError("R54 EV12 primary class refs changed")
    if tuple(data.get("ambiguity_kind_refs") or ()) != P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS:
        raise ValueError("R54 EV12 ambiguity refs changed")
    if tuple(data.get("one_question_fit_refs") or ()) != P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS:
        raise ValueError("R54 EV12 one-question refs changed")
    if tuple(data.get("repair_required_ref_refs") or ()) != P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS:
        raise ValueError("R54 EV12 repair refs changed")
    if tuple(data.get("plan_candidate_flag_refs") or ()) != P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS:
        raise ValueError("R54 EV12 plan candidate flag refs changed")
    if tuple(data.get("p8_material_candidate_primary_class_refs") or ()) != P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS:
        raise ValueError("R54 EV12 P8 material candidate primary refs changed")
    if tuple(data.get("not_question_repair_primary_class_refs") or ()) != P7_R54_EV12_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS:
        raise ValueError("R54 EV12 not-question repair refs changed")
    for true_key in (
        "question_need_observation_rows_are_bodyfree",
        "question_text_absent_for_all_rows",
        "draft_question_text_absent_for_all_rows",
        "reviewer_free_text_absent_for_all_rows",
        "raw_body_absent_for_all_rows",
        "comment_text_absent_for_all_rows",
        "local_path_absent_for_all_rows",
        "body_hash_absent_for_all_rows",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV12 must keep {true_key}=True")
    for false_key in (
        "question_text_included_allowed",
        "draft_question_text_included_allowed",
        "reviewer_free_text_included_allowed",
        "raw_body_allowed",
        "comment_text_allowed",
        "local_path_allowed",
        "body_hash_allowed",
        "question_text_or_draft_text_saved_here",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_storage_schema_implemented",
        "question_answer_persistence_implemented",
        "question_plan_guard_implemented",
        "actual_review_evidence_complete",
        "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV12 must keep {false_key}=False")
    if data.get("p8_material_candidate_requested_row_count") != sum(1 for row in rows if row.get("p8_material_candidate_requested") is True):
        raise ValueError("R54 EV12 P8 material requested count mismatch")
    if data.get("p8_material_candidate_allowed_row_count") != sum(1 for row in rows if row.get("p8_material_candidate_allowed") is True):
        raise ValueError("R54 EV12 P8 material allowed count mismatch")
    if safe_mapping(data.get("p8_material_candidate_allowed_primary_class_counts")) != _ev12_p8_material_candidate_allowed_primary_class_counts(rows):
        raise ValueError("R54 EV12 P8 material allowed primary class counts mismatch")
    if data.get("not_question_repair_required_count") != sum(1 for row in rows if row.get("not_question_repair_required") is True):
        raise ValueError("R54 EV12 not-question repair count mismatch")
    if data.get("insufficient_material_execution_blocker_count") != sum(1 for row in rows if row.get("insufficient_material_execution_blocker") is True):
        raise ValueError("R54 EV12 insufficient material count mismatch")
    ready = data.get("question_observation_normalization_status") == P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    if data.get("actual_question_need_observation_rows_materialized_here") is not ready:
        raise ValueError("R54 EV12 question row materialization flag must match readiness")
    if ready:
        if data.get("ev11_question_observation_normalization_allowed_next") is not True or data.get("ev11_next_required_step") != P7_R54_EV12_STEP_REF:
            raise ValueError("R54 EV12 ready normalization requires EV11 allowance")
        if blockers:
            raise ValueError("R54 EV12 ready normalization must not carry materialization blockers")
        if data.get("sanitized_review_result_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV12 ready normalization requires 24 sanitized and rating rows")
        if data.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV12 ready normalization requires 24 question rows")
        if data.get("question_observation_row_refs_unique") is not True or data.get("case_ref_ids_unique") is not True:
            raise ValueError("R54 EV12 ready normalization requires unique question and case refs")
        if data.get("all_required_question_need_observation_rows_present") is not True or data.get("primary_class_ambiguity_one_question_fit_are_canonical_refs") is not True:
            raise ValueError("R54 EV12 ready normalization requires all canonical rows")
        if data.get("row_case_ref_sets_match_review_intake") is not True or data.get("row_case_ref_sets_match_rating_rows") is not True:
            raise ValueError("R54 EV12 ready normalization requires matching case refs")
        if data.get("rating_rows_preserved_from_ev10") is not True or data.get("blocker_rows_preserved_from_ev11") is not True:
            raise ValueError("R54 EV12 ready normalization must preserve EV10/EV11 materialization")
        if data.get("rating_question_consistency_guard_allowed_next") is not True:
            raise ValueError("R54 EV12 ready normalization must allow EV13 next")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV12_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV12 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV13_STEP_REF:
            raise ValueError("R54 EV12 ready normalization must point to EV13")
    else:
        if data.get("question_observation_normalization_status") != P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV12 blocked normalization status changed")
        if data.get("question_observation_rows") != [] or data.get("question_observation_row_count") != 0:
            raise ValueError("R54 EV12 blocked normalization must not materialize rows")
        if data.get("rating_question_consistency_guard_allowed_next") is not False:
            raise ValueError("R54 EV12 blocked normalization must not allow EV13")
        if not blockers or data.get("next_required_step") != P7_R54_EV12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV12 blocked normalization must point to repair")
    return True


def _ev13_question_by_case_ref(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {clean_identifier(row.get("case_ref_id"), default="", max_length=180): row for row in rows}


def build_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree(
    *,
    rating_row: Mapping[str, Any],
    question_observation_row: Mapping[str, Any],
    issue_id: str,
    issue_kind_ref: str,
    decision_direction_ref: str,
) -> dict[str, Any]:
    rating = safe_mapping(rating_row)
    question = safe_mapping(question_observation_row)
    assert_p7_r54_ev10_rating_row_bodyfree_contract(rating)
    assert_p7_r54_ev12_question_need_observation_row_bodyfree_contract(question)
    if issue_id not in P7_R54_EV13_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 EV13 issue id must be canonical")
    if issue_kind_ref not in P7_R54_EV13_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 EV13 issue kind must be canonical")
    if decision_direction_ref not in P7_R54_EV13_DECISION_DIRECTION_REFS:
        raise ValueError("R54 EV13 issue direction must be canonical")
    row = {
        "schema_version": P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "consistency_issue_row_ref": f"r54ev13-consistency-issue-{issue_id}-{clean_identifier(rating.get('case_ref_id'), default='case', max_length=120)}",
        "review_session_id": _safe_review_session_id(rating.get("review_session_id") or question.get("review_session_id")),
        "rating_row_ref": clean_identifier(rating.get("rating_row_ref"), max_length=180),
        "question_observation_row_ref": clean_identifier(question.get("question_observation_row_ref"), max_length=180),
        "packet_ref_id": clean_identifier(rating.get("packet_ref_id") or question.get("packet_ref_id"), max_length=180),
        "blind_case_id": clean_identifier(rating.get("blind_case_id") or question.get("blind_case_id"), max_length=180),
        "case_ref_id": clean_identifier(rating.get("case_ref_id") or question.get("case_ref_id"), max_length=180),
        "issue_id": issue_id,
        "issue_kind_ref": issue_kind_ref,
        "decision_direction_ref": decision_direction_ref,
        "issue_status_ref": "open",
        "raw_body_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        "body_hash_included": False,
        "packet_content_included": False,
        "machine_auto_score_used": False,
        "machine_metrics_used_for_readfeel": False,
        "body_free": True,
    }
    assert_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree_contract(row)
    return row


def assert_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_ev13_rating_question_consistency_issue_row",
    )
    if data.get("schema_version") != P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV13 issue row schema version changed")
    if data.get("issue_id") not in P7_R54_EV13_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 EV13 issue id outside canonical refs")
    if data.get("issue_kind_ref") not in P7_R54_EV13_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 EV13 issue kind outside canonical refs")
    if data.get("decision_direction_ref") not in P7_R54_EV13_DECISION_DIRECTION_REFS:
        raise ValueError("R54 EV13 issue direction outside canonical refs")
    if data.get("issue_status_ref") != "open":
        raise ValueError("R54 EV13 issue row status must remain open")
    for false_key in (
        "raw_body_included",
        "comment_text_included",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_path_included",
        "body_hash_included",
        "packet_content_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV13 issue row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV13 issue row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev13_rating_question_consistency_issue_row")
    return True


def _ev13_rating_question_consistency_issue_rows(
    *,
    rating_rows: Sequence[Mapping[str, Any]],
    question_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    question_by_case_ref = _ev13_question_by_case_ref(question_rows)
    rating_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in rating_rows}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in question_rows}
    if rating_case_refs != question_case_refs:
        sample_rating = safe_mapping(rating_rows[0]) if rating_rows else {}
        sample_question = safe_mapping(question_rows[0]) if question_rows else {}
        if sample_rating and sample_question:
            issues.append(build_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree(
                rating_row=sample_rating,
                question_observation_row=sample_question,
                issue_id="r54_ev13_rating_question_case_ref_set_mismatch",
                issue_kind_ref="rating_question_case_integrity_issue",
                decision_direction_ref="rating_question_row_repair_required",
            ))
        return issues
    for rating in rating_rows:
        rating_row = safe_mapping(rating)
        question = safe_mapping(question_by_case_ref.get(clean_identifier(rating_row.get("case_ref_id"), default="", max_length=180)))
        if not question:
            continue
        verdict = clean_identifier(rating_row.get("verdict"), max_length=80)
        primary_class = clean_identifier(question.get("question_need_primary_class"), max_length=160)
        repair_refs = set(dedupe_identifiers(question.get("repair_required_refs") or [], limit=20, max_length=160))
        repair_without_no_repair = repair_refs - {"no_repair_required"}
        p8_requested = question.get("p8_material_candidate_requested") is True or safe_mapping(question.get("plan_candidate_flags")).get("p8_design_material_candidate") is True
        not_question_repair = question.get("not_question_repair_required") is True
        insufficient = question.get("insufficient_material_execution_blocker") is True
        execution_blockers = dedupe_identifiers(rating_row.get("execution_blocker_ids") or [], limit=20, max_length=160)
        if verdict in {"REPAIR_REQUIRED", "RED"} and primary_class == "no_question_needed_emlis_can_observe":
            issues.append(build_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_ev13_red_or_repair_with_no_question_needed_observation",
                issue_kind_ref="rating_question_observation_semantic_mismatch",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if (verdict in {"REPAIR_REQUIRED", "RED"} or repair_without_no_repair or not_question_repair) and p8_requested:
            issues.append(build_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_ev13_repair_required_with_p8_material_candidate",
                issue_kind_ref="p5_repair_hidden_by_question_candidate",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if verdict == "PASS" and not_question_repair:
            issues.append(build_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_ev13_pass_with_not_question_repair_required",
                issue_kind_ref="rating_question_observation_semantic_mismatch",
                decision_direction_ref="p5_repair_return_required_later",
            ))
        if insufficient and (verdict == "PASS" or not execution_blockers):
            issues.append(build_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree(
                rating_row=rating_row,
                question_observation_row=question,
                issue_id="r54_ev13_insufficient_material_with_pass_or_no_execution_blocker",
                issue_kind_ref="p5_inconclusive_or_execution_boundary_mismatch",
                decision_direction_ref="r54_operation_inconclusive_required_later",
            ))
    return issues


def build_p7_r54_ev13_rating_question_consistency_guard(
    *,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev13_rating_question_consistency_guard",
) -> dict[str, Any]:
    """Build EV13 body-free rating/question consistency guard."""

    ev12 = safe_mapping(question_need_observation_row_normalization) if question_need_observation_row_normalization is not None else build_p7_r54_ev12_question_need_observation_row_normalization()
    assert_p7_r54_ev12_question_need_observation_row_normalization_contract(ev12)
    ev10 = safe_mapping(rating_row_normalization) if rating_row_normalization is not None else build_p7_r54_ev10_rating_row_normalization()
    assert_p7_r54_ev10_rating_row_normalization_contract(ev10)

    ev12_ready = bool(
        ev12.get("question_observation_normalization_status") == P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
        and ev12.get("rating_question_consistency_guard_allowed_next") is True
        and ev12.get("next_required_step") == P7_R54_EV13_STEP_REF
    )
    ev10_ready = bool(
        ev10.get("rating_row_normalization_status") == P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
        and ev10.get("rating_row_count") == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    blockers: list[str] = []
    if not ev12_ready:
        blockers.append("question_observation_normalization_not_ready_for_rating_question_consistency_guard")
    if not ev10_ready:
        blockers.append("rating_row_normalization_not_ready_for_rating_question_consistency_guard")
    rating_rows = [safe_mapping(row) for row in (ev10.get("rating_rows") or [])] if ev10_ready else []
    question_rows = [safe_mapping(row) for row in (ev12.get("question_observation_rows") or [])] if ev12_ready else []
    rating_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in rating_rows}
    question_case_refs = {clean_identifier(row.get("case_ref_id"), default="", max_length=180) for row in question_rows}
    case_sets_match = bool(rating_rows and question_rows and rating_case_refs == question_case_refs)
    all_required = bool(
        len(rating_rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and len(question_rows) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and case_sets_match
    )
    issue_rows = _ev13_rating_question_consistency_issue_rows(
        rating_rows=rating_rows,
        question_rows=question_rows,
    ) if ev12_ready and ev10_ready else []
    if ev12_ready and ev10_ready and not all_required:
        blockers.append("rating_question_case_ref_set_mismatch")
    blockers = dedupe_identifiers([*blockers, *(ev12.get("open_execution_blocker_ids") or [])], limit=100, max_length=180)
    issue_count = len(issue_rows)
    ready = bool(ev12_ready and ev10_ready and all_required and issue_count == 0 and not blockers)
    direction_counts = _ev12_single_id_counts(issue_rows, "decision_direction_ref")
    reason_refs = [P7_R54_EV13_READY_REASON_REF] if ready else dedupe_identifiers(
        [P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, *blockers, *(row.get("issue_id") for row in issue_rows)],
        limit=100,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV13_STEP_REF,
        "operation_step_ref": P7_R54_EV13_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev13_rating_question_consistency_guard", max_length=220),
        "review_session_id": _safe_review_session_id(ev12.get("review_session_id") or ev10.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev12_schema_version": P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "ev12_material_ref": clean_identifier(ev12.get("material_id"), default="p7_r54_ev12_question_need_observation_row_normalization", max_length=220),
        "ev12_next_required_step": clean_identifier(ev12.get("next_required_step"), default=P7_R54_EV12_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev12_question_observation_normalization_status": clean_identifier(ev12.get("question_observation_normalization_status"), default=P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "ev12_consistency_guard_allowed_next": ev12_ready,
        "ev10_schema_version": P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "ev10_material_ref": clean_identifier(ev10.get("material_id"), default="p7_r54_ev10_rating_row_normalization", max_length=220),
        "ev10_rating_row_normalization_status": clean_identifier(ev10.get("rating_row_normalization_status"), default=P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op15_helper_ref": "build_p7_r54_op15_rating_question_consistency_guard",
        "existing_op15_schema_version": r54op.P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "existing_op15_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op15_current_refs_are_historical_here": True,
        "existing_op15_reused_as_actual_consistency_guard_basis": False,
        "existing_op15_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_question_consistency_guard_status": P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF if ready else P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF,
        "rating_question_consistency_guard_ref": P7_R54_EV13_CONSISTENCY_GUARD_REF if ready else "rating_question_consistency_guard_not_ready_bodyfree_20260626",
        "rating_question_consistency_guard_policy_ref": P7_R54_EV13_CONSISTENCY_GUARD_POLICY_REF,
        "rating_question_consistency_guard_reason_refs": reason_refs,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "rating_row_count": len(rating_rows) if ev10_ready else 0,
        "question_observation_row_count": len(question_rows) if ev12_ready else 0,
        "rating_question_case_ref_sets_match": bool(case_sets_match),
        "all_required_rating_and_question_rows_present": bool(all_required),
        "rating_question_consistency_issue_row_schema_version": P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
        "rating_question_consistency_issue_row_required_field_refs": list(P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS),
        "rating_question_consistency_issue_rows": issue_rows,
        "consistency_issue_count": issue_count,
        "consistency_issue_id_refs": list(P7_R54_EV13_CONSISTENCY_ISSUE_ID_REFS),
        "consistency_issue_kind_refs": list(P7_R54_EV13_CONSISTENCY_ISSUE_KIND_REFS),
        "decision_direction_refs": list(P7_R54_EV13_DECISION_DIRECTION_REFS),
        "red_or_repair_with_no_question_needed_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_ev13_red_or_repair_with_no_question_needed_observation"),
        "repair_required_with_p8_material_candidate_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_ev13_repair_required_with_p8_material_candidate"),
        "pass_with_not_question_repair_required_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_ev13_pass_with_not_question_repair_required"),
        "insufficient_material_with_pass_or_no_execution_blocker_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_ev13_insufficient_material_with_pass_or_no_execution_blocker"),
        "case_ref_set_mismatch_count": sum(1 for row in issue_rows if row.get("issue_id") == "r54_ev13_rating_question_case_ref_set_mismatch"),
        "consistency_issue_direction_counts": direction_counts,
        "p5_confirmed_candidate_blocked_by_consistency_issues": issue_count > 0,
        "p5_decision_candidate_not_materialized_here": True,
        "issues_route_to_p5_repair_return_or_inconclusive_later": issue_count > 0,
        "p8_material_candidates_do_not_hide_p5_repair_here": True,
        "p5_surface_repair_not_promoted_to_p8_material": sum(1 for row in issue_rows if row.get("issue_id") == "r54_ev13_repair_required_with_p8_material_candidate") == 0,
        "not_question_repair_not_promoted_to_p8_material": sum(1 for row in issue_rows if row.get("issue_id") == "r54_ev13_pass_with_not_question_repair_required") == 0,
        "ready_for_pause_abort_expiration_protocol": ready,
        "rating_rows_preserved_from_ev10": bool(ev10_ready and ev10.get("actual_rating_rows_materialized_here") is True),
        "question_observation_rows_preserved_from_ev12": bool(ev12_ready and ev12.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_rating_rows_materialized_here": bool(ev10_ready and ev10.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ev12.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(ev12_ready and ev12.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV13_IMPLEMENTED_STEPS if ev12_ready and ev10_ready else (ev12.get("implemented_steps") or P7_R54_EV12_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV13_NOT_YET_IMPLEMENTED_STEPS if ev12_ready and ev10_ready else (ev12.get("not_yet_implemented_steps") or P7_R54_EV12_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_EV14_NEXT_REQUIRED_STEP_REF if ready else P7_R54_EV13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ev10_ready and ev10.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ev12.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(ev12_ready and ev12.get("actual_question_need_observation_rows_materialized_here") is True),
    }
    assert_p7_r54_ev13_rating_question_consistency_guard_contract(material)
    return material


def assert_p7_r54_ev13_rating_question_consistency_guard_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS,
        source="p7_r54_ev13_rating_question_consistency_guard",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        policy_section=P7_R54_EV13_STEP_REF,
        operation_step_ref=P7_R54_EV13_STEP_REF,
        source="p7_r54_ev13_rating_question_consistency_guard",
        false_flag_refs=_ev13_false_flag_refs(),
    )
    if data.get("ev12_schema_version") != P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 EV13 EV12 schema reference changed")
    if data.get("ev10_schema_version") != P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("R54 EV13 EV10 schema reference changed")
    if data.get("operation_current_refs_used_as_actual_review_basis") is not True:
        raise ValueError("R54 EV13 must use 20260626 operation refs as actual review basis")
    if safe_mapping(data.get("existing_op15_operation_current_refs")) != safe_mapping(r54op.P7_R54_OPERATION_CURRENT_REFS):
        raise ValueError("R54 EV13 existing OP15 refs changed")
    if data.get("existing_op15_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV13 must classify existing OP15 refs as historical")
    if data.get("existing_op15_reused_as_actual_consistency_guard_basis") is not False:
        raise ValueError("R54 EV13 must not reuse 20260625 OP15 as actual consistency guard basis")
    if data.get("existing_op15_structural_contract_reused") is not True:
        raise ValueError("R54 EV13 must reuse only OP15 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV13 required case count changed")
    if data.get("rating_question_consistency_guard_status") not in P7_R54_EV13_ALLOWED_CONSISTENCY_GUARD_STATUS_REFS:
        raise ValueError("R54 EV13 consistency guard status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV13 open blockers must match materialization blockers")
    rows = [safe_mapping(row) for row in (data.get("rating_question_consistency_issue_rows") or [])]
    for row in rows:
        assert_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree_contract(row)
    if data.get("consistency_issue_count") != len(rows):
        raise ValueError("R54 EV13 issue count mismatch")
    if tuple(data.get("consistency_issue_id_refs") or ()) != P7_R54_EV13_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R54 EV13 issue id refs changed")
    if tuple(data.get("consistency_issue_kind_refs") or ()) != P7_R54_EV13_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R54 EV13 issue kind refs changed")
    if tuple(data.get("decision_direction_refs") or ()) != P7_R54_EV13_DECISION_DIRECTION_REFS:
        raise ValueError("R54 EV13 decision direction refs changed")
    if data.get("red_or_repair_with_no_question_needed_count") != sum(1 for row in rows if row.get("issue_id") == "r54_ev13_red_or_repair_with_no_question_needed_observation"):
        raise ValueError("R54 EV13 red/no-question issue count mismatch")
    if data.get("repair_required_with_p8_material_candidate_count") != sum(1 for row in rows if row.get("issue_id") == "r54_ev13_repair_required_with_p8_material_candidate"):
        raise ValueError("R54 EV13 repair/P8 issue count mismatch")
    if data.get("pass_with_not_question_repair_required_count") != sum(1 for row in rows if row.get("issue_id") == "r54_ev13_pass_with_not_question_repair_required"):
        raise ValueError("R54 EV13 pass/not-question issue count mismatch")
    if data.get("insufficient_material_with_pass_or_no_execution_blocker_count") != sum(1 for row in rows if row.get("issue_id") == "r54_ev13_insufficient_material_with_pass_or_no_execution_blocker"):
        raise ValueError("R54 EV13 insufficient/pass issue count mismatch")
    if data.get("case_ref_set_mismatch_count") != sum(1 for row in rows if row.get("issue_id") == "r54_ev13_rating_question_case_ref_set_mismatch"):
        raise ValueError("R54 EV13 case mismatch issue count mismatch")
    for true_key in (
        "p5_decision_candidate_not_materialized_here",
        "p8_material_candidates_do_not_hide_p5_repair_here",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV13 must keep {true_key}=True")
    for false_key in (
        "actual_review_evidence_complete",
        "disposal_verified",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV13 must keep {false_key}=False")
    ready = data.get("rating_question_consistency_guard_status") == P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF
    if ready:
        if data.get("ev12_consistency_guard_allowed_next") is not True or data.get("ev12_next_required_step") != P7_R54_EV13_STEP_REF:
            raise ValueError("R54 EV13 ready guard requires EV12 allowance")
        if data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV13 ready guard requires 24 rating and question rows")
        if data.get("rating_question_case_ref_sets_match") is not True or data.get("all_required_rating_and_question_rows_present") is not True:
            raise ValueError("R54 EV13 ready guard requires matching complete rating/question case refs")
        if data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("R54 EV13 ready guard requires EV12 question rows to be materialized")
        if data.get("consistency_issue_count") != 0 or rows:
            raise ValueError("R54 EV13 ready guard must have zero issues")
        if blockers:
            raise ValueError("R54 EV13 ready guard must not carry materialization blockers")
        if data.get("ready_for_pause_abort_expiration_protocol") is not True:
            raise ValueError("R54 EV13 ready guard must allow EV14 next")
        if data.get("p5_surface_repair_not_promoted_to_p8_material") is not True or data.get("not_question_repair_not_promoted_to_p8_material") is not True:
            raise ValueError("R54 EV13 ready guard must prevent P5 repair escape to P8")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV13_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV13 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV14_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV13 ready guard must point to EV14")
    else:
        if data.get("rating_question_consistency_guard_status") != P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV13 blocked guard status changed")
        if data.get("ready_for_pause_abort_expiration_protocol") is not False:
            raise ValueError("R54 EV13 blocked guard must not allow EV14")
        if not blockers and not rows:
            raise ValueError("R54 EV13 blocked guard must carry blockers or issue rows")
        if data.get("next_required_step") != P7_R54_EV13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV13 blocked guard must point to repair")
    return True


P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev14_pause_abort_expiration_protocol.bodyfree.v1"
)
P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev15_purge_disposal_receipt.bodyfree.v1"
)

P7_R54_EV14_STEP_REF: Final = P7_R54_EV14_NEXT_REQUIRED_STEP_REF
P7_R54_EV15_STEP_REF: Final = "R54-EV-15_purge_disposal_receipt"
P7_R54_EV16_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-16_bodyfree_post_review_summary"
P7_R54_EV14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV13_IMPLEMENTED_STEPS, P7_R54_EV14_STEP_REF)
P7_R54_EV14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV15_STEP_REF,)
P7_R54_EV15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV14_IMPLEMENTED_STEPS, P7_R54_EV15_STEP_REF)
P7_R54_EV15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV16_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV14_PROTOCOL_READY_STATUS_REF: Final = "READY_FOR_PURGE_DISPOSAL_RECEIPT"
P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF: Final = "PAUSED_NO_HANDOFF_LOCAL_ONLY"
P7_R54_EV14_PROTOCOL_ABORTED_STATUS_REF: Final = "ABORTED_PURGE_REQUIRED"
P7_R54_EV14_PROTOCOL_EXPIRED_STATUS_REF: Final = "EXPIRED_PURGE_REQUIRED"
P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF: Final = "RATING_INCOMPLETE_PURGE_REQUIRED"
P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF: Final = "BLOCKED_BY_CONSISTENCY_GUARD"
P7_R54_EV14_PROTOCOL_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV14_PROTOCOL_READY_STATUS_REF,
    P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF,
    P7_R54_EV14_PROTOCOL_ABORTED_STATUS_REF,
    P7_R54_EV14_PROTOCOL_EXPIRED_STATUS_REF,
    P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
    P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF,
)
P7_R54_EV14_PROTOCOL_REF: Final = "r54_ev14_pause_abort_expiration_protocol_bodyfree_20260626"
P7_R54_EV14_PROTOCOL_POLICY_REF: Final = "pause_abort_expiration_requires_disposal_before_any_handoff_20260626"
P7_R54_EV14_READY_REASON_REF: Final = "r54_ev14_ready_for_purge_disposal_receipt_bodyfree"
P7_R54_EV14_PAUSED_REASON_REF: Final = "r54_ev14_paused_no_handoff_local_only_bodyfree"
P7_R54_EV14_ABORTED_REASON_REF: Final = "r54_ev14_aborted_purge_required_bodyfree"
P7_R54_EV14_EXPIRED_REASON_REF: Final = "r54_ev14_expired_purge_required_bodyfree"
P7_R54_EV14_RATING_INCOMPLETE_REASON_REF: Final = "r54_ev14_rating_or_question_incomplete_purge_required_bodyfree"
P7_R54_EV14_BLOCKED_REASON_REF: Final = "r54_ev14_blocked_by_ev13_consistency_guard_bodyfree"
P7_R54_EV14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev14_blocked_until_consistency_guard_repair_before_purge_disposal_receipt"
P7_R54_EV14_PAUSED_NEXT_REQUIRED_STEP_REF: Final = "resume_or_abort_r54_ev14_paused_local_only_review_before_purge_disposal_receipt"
P7_R54_EV14_REVIEW_OPERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    r54op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    r54op.P7_R54_OP10_REVIEW_PAUSED_STATUS_REF,
    r54op.P7_R54_OP10_REVIEW_ABORTED_STATUS_REF,
    r54op.P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF,
    "REVIEW_RATING_INCOMPLETE",
    "rating_incomplete_purge_required",
)
P7_R54_EV14_REQUIRED_LOCAL_DELETE_TARGET_REFS: Final[tuple[str, ...]] = (
    "body_full_packet",
    "reviewer_notes",
    "temporary_form",
)
P7_R54_EV14_PURGE_TRIGGER_REFS: Final[tuple[str, ...]] = (
    "rating_rows_finalized",
    "blocker_rows_finalized",
    "question_observation_rows_finalized",
    "review_session_cancelled",
    "review_session_aborted",
    "retention_deadline_reached",
)
P7_R54_EV14_P5_DECISION_DIRECTION_REFS: Final[tuple[str, ...]] = (
    "continue_after_purge_disposal_receipt",
    "no_p5_decision_materialized_here",
    "pause_no_handoff_local_only",
    "r54_operation_inconclusive_required_later",
    "p5_inconclusive_due_to_consistency_guard_not_ready",
)
P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF: Final = "DISPOSAL_VERIFIED"
P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL"
P7_R54_EV15_ALLOWED_DISPOSAL_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF,
    P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF,
)
P7_R54_EV15_DISPOSAL_RECEIPT_REF: Final = "r54_ev15_bodyfree_purge_disposal_receipt_verified_20260626"
P7_R54_EV15_DISPOSAL_RECEIPT_POLICY_REF: Final = "bodyfree_receipt_only_after_external_local_purge_verification_no_body_hash_no_path_20260626"
P7_R54_EV15_READY_REASON_REF: Final = "r54_ev15_purge_disposal_receipt_verified_bodyfree"
P7_R54_EV15_BLOCKED_REASON_REF: Final = "r54_ev15_purge_disposal_receipt_blocked_bodyfree"
P7_R54_EV15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev15_blocked_until_purge_disposal_receipt_repair_before_bodyfree_summary"
P7_R54_EV15_REMOVAL_TARGET_REFS: Final[tuple[str, ...]] = P7_R54_EV14_REQUIRED_LOCAL_DELETE_TARGET_REFS

P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "ev13_schema_version", "ev13_material_ref", "ev13_next_required_step", "ev13_consistency_guard_status",
    "ev13_ready_for_pause_abort_expiration_protocol", "ev13_consistency_issue_count", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "operation_current_refs_used_as_actual_review_basis",
    "existing_op16_helper_ref", "existing_op16_schema_version", "existing_op16_operation_current_refs",
    "existing_op16_current_refs_are_historical_here", "existing_op16_reused_as_actual_pause_abort_basis",
    "existing_op16_reused_as_actual_protocol_basis", "existing_op16_structural_contract_reused",
    "required_case_count", "rating_row_count", "question_observation_row_count", "consistency_issue_count",
    "pause_abort_expiration_protocol_status", "pause_abort_expiration_protocol_ref",
    "pause_abort_expiration_protocol_policy_ref", "pause_abort_expiration_protocol_reason_refs",
    "review_operation_status_ref", "review_operation_status_refs", "review_operation_status_allowed",
    "purge_trigger_refs", "purge_trigger_ref_count", "review_session_cancelled_is_purge_trigger",
    "review_session_aborted_is_purge_trigger", "retention_deadline_reached_is_purge_trigger",
    "required_local_delete_target_refs", "required_local_delete_target_ref_count", "body_full_packet_retention_hours",
    "reviewer_notes_retention_after_rating_hours", "body_full_material_must_not_remain_after_cancel_or_deadline",
    "reviewer_notes_must_not_remain_after_cancel_or_deadline", "temporary_form_must_not_remain_after_cancel_or_deadline",
    "purge_before_handoff_required", "handoff_allowed_before_purge", "r52_reintake_handoff_allowed_before_purge",
    "review_paused_without_handoff", "review_aborted_or_expired", "review_rating_or_question_incomplete",
    "p5_decision_direction_ref", "p5_decision_direction_refs", "p5_decision_materialized_here",
    "p5_inconclusive_direction_only_not_decision_materialized", "ready_for_purge_disposal_receipt",
    "purge_disposal_receipt_allowed_next", "disposal_receipt_allowed_next", "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete", "disposal_verified", "actual_disposal_receipt_materialized_here",
    "human_review_completion_claim_blocked_here", "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here", "execution_blocker_ids", "open_execution_blocker_ids",
    "implemented_steps", "not_yet_implemented_steps", "next_required_step", "public_contract",
    "r54_ev_no_touch_contract", "body_free_markers", "body_free", "raw_body_included",
    "question_text_included", "draft_question_text_included", "local_path_included", *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "ev14_schema_version", "ev14_material_ref", "ev14_next_required_step", "ev14_pause_abort_expiration_protocol_status",
    "ev14_purge_disposal_receipt_allowed_next", "ev14_ready_for_purge_disposal_receipt", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "operation_current_refs_used_as_actual_review_basis",
    "existing_op17_helper_ref", "existing_op17_schema_version", "existing_op17_operation_current_refs",
    "existing_op17_current_refs_are_historical_here", "existing_op17_reused_as_actual_disposal_basis", "existing_op17_reused_as_actual_disposal_receipt_basis",
    "existing_op17_structural_contract_reused", "required_case_count", "rating_row_count",
    "question_observation_row_count", "purge_disposal_receipt_status", "purge_disposal_receipt_ref",
    "purge_disposal_receipt_policy_ref", "purge_disposal_receipt_reason_refs", "removal_target_refs",
    "removal_target_ref_count", "body_removed", "reviewer_notes_removed", "temporary_form_removed",
    "all_required_local_targets_removed", "local_packet_exported", "content_hash_of_body_stored",
    "body_full_packet_zip_inclusion_allowed", "reviewer_notes_export_allowed", "body_full_packet_export_allowed",
    "disposal_verified", "actual_disposal_receipt_materialized_here", "actual_disposal_run_here",
    "disposal_failure_decision_ref", "body_free_post_review_summary_allowed_next", "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete", "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here",
    "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps",
    "next_required_step", "public_contract", "r54_ev_no_touch_contract", "body_free_markers", "body_free",
    "raw_body_included", "question_text_included", "draft_question_text_included", "local_path_included", *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev14_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_EV_FALSE_FLAG_REFS
        if key not in {"actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here"}
    )


def _ev15_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_EV_FALSE_FLAG_REFS
        if key not in {
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
        }
    )


def _ev14_protocol_decision(
    review_status: str,
    *,
    ev13_ready: bool,
    rating_row_count: int,
    question_observation_row_count: int,
) -> tuple[str, str, str, bool, bool, bool, bool]:
    if not ev13_ready:
        return (
            P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF,
            P7_R54_EV14_BLOCKED_REASON_REF,
            "ev13_consistency_guard_not_ready_for_pause_abort_expiration_protocol",
            False,
            False,
            False,
            False,
        )
    if review_status == r54op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF:
        if rating_row_count != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or question_observation_row_count != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            return (
                P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
                P7_R54_EV14_RATING_INCOMPLETE_REASON_REF,
                "",
                True,
                False,
                True,
                True,
            )
        return (P7_R54_EV14_PROTOCOL_READY_STATUS_REF, P7_R54_EV14_READY_REASON_REF, "", True, False, False, False)
    if review_status == r54op.P7_R54_OP10_REVIEW_PAUSED_STATUS_REF:
        return (P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF, P7_R54_EV14_PAUSED_REASON_REF, "", False, True, False, False)
    if review_status == r54op.P7_R54_OP10_REVIEW_ABORTED_STATUS_REF:
        return (P7_R54_EV14_PROTOCOL_ABORTED_STATUS_REF, P7_R54_EV14_ABORTED_REASON_REF, "", True, False, True, False)
    if review_status == r54op.P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF:
        return (P7_R54_EV14_PROTOCOL_EXPIRED_STATUS_REF, P7_R54_EV14_EXPIRED_REASON_REF, "", True, False, True, False)
    if review_status in ("rating_incomplete_purge_required", "REVIEW_RATING_INCOMPLETE"):
        return (
            P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF,
            P7_R54_EV14_RATING_INCOMPLETE_REASON_REF,
            "",
            True,
            False,
            True,
            True,
        )
    return (
        P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF,
        P7_R54_EV14_BLOCKED_REASON_REF,
        "review_operation_status_not_allowed_for_ev14_pause_abort_expiration_protocol",
        False,
        False,
        False,
        False,
    )


def build_p7_r54_ev14_pause_abort_expiration_protocol(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_operation_status_ref: Any = r54op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
    session_event_status_ref: Any | None = None,
    material_id: Any = "p7_r54_ev14_pause_abort_expiration_protocol",
) -> dict[str, Any]:
    """Build EV14 body-free pause / abort / expiration protocol."""

    ev13 = safe_mapping(rating_question_consistency_guard) if rating_question_consistency_guard is not None else build_p7_r54_ev13_rating_question_consistency_guard()
    assert_p7_r54_ev13_rating_question_consistency_guard_contract(ev13)
    if session_event_status_ref is not None:
        review_operation_status_ref = session_event_status_ref
    review_status = clean_identifier(review_operation_status_ref, default="", max_length=180)
    review_status_allowed = review_status in P7_R54_EV14_REVIEW_OPERATION_STATUS_REFS
    ev13_ready = bool(
        ev13.get("rating_question_consistency_guard_status") == P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF
        and ev13.get("ready_for_pause_abort_expiration_protocol") is True
        and ev13.get("next_required_step") == P7_R54_EV14_STEP_REF
        and not ev13.get("open_execution_blocker_ids")
    )
    rating_row_count = int(ev13.get("rating_row_count") or 0) if ev13_ready else 0
    question_row_count = int(ev13.get("question_observation_row_count") or 0) if ev13_ready else 0
    status, reason_ref, blocker_ref, purge_allowed, paused, abort_or_expired, incomplete = _ev14_protocol_decision(
        review_status,
        ev13_ready=ev13_ready and review_status_allowed,
        rating_row_count=rating_row_count,
        question_observation_row_count=question_row_count,
    )
    blockers = dedupe_identifiers([blocker_ref] if blocker_ref else [], limit=100, max_length=180)
    p5_decision_direction_ref = "continue_after_purge_disposal_receipt"
    if status == P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF:
        p5_decision_direction_ref = "pause_no_handoff_local_only"
    elif status in (P7_R54_EV14_PROTOCOL_ABORTED_STATUS_REF, P7_R54_EV14_PROTOCOL_EXPIRED_STATUS_REF, P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF):
        p5_decision_direction_ref = "r54_operation_inconclusive_required_later"
    elif status == P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF:
        p5_decision_direction_ref = "rating_question_consistency_repair_required"
    ready_for_disposal = bool(purge_allowed and not blockers)
    implemented_steps = P7_R54_EV14_IMPLEMENTED_STEPS if ev13_ready and review_status_allowed else tuple(ev13.get("implemented_steps") or P7_R54_EV13_IMPLEMENTED_STEPS)
    not_yet_steps = P7_R54_EV14_NOT_YET_IMPLEMENTED_STEPS if ev13_ready and review_status_allowed else tuple(ev13.get("not_yet_implemented_steps") or P7_R54_EV13_NOT_YET_IMPLEMENTED_STEPS)
    material = {
        "schema_version": P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV14_STEP_REF,
        "operation_step_ref": P7_R54_EV14_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev14_pause_abort_expiration_protocol", max_length=220),
        "review_session_id": _safe_review_session_id(ev13.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev13_schema_version": P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "ev13_material_ref": clean_identifier(ev13.get("material_id"), default="p7_r54_ev13_rating_question_consistency_guard", max_length=220),
        "ev13_next_required_step": clean_identifier(ev13.get("next_required_step"), default=P7_R54_EV13_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=220),
        "ev13_consistency_guard_status": clean_identifier(ev13.get("rating_question_consistency_guard_status"), default=P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, max_length=180),
        "ev13_ready_for_pause_abort_expiration_protocol": ev13_ready,
        "ev13_consistency_issue_count": int(ev13.get("consistency_issue_count") or 0),
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op16_helper_ref": "build_p7_r54_op16_pause_abort_expiration_protocol",
        "existing_op16_schema_version": r54op.P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "existing_op16_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op16_current_refs_are_historical_here": True,
        "existing_op16_reused_as_actual_pause_abort_basis": False,
        "existing_op16_reused_as_actual_protocol_basis": False,
        "existing_op16_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": rating_row_count,
        "question_observation_row_count": question_row_count,
        "consistency_issue_count": int(ev13.get("consistency_issue_count") or 0),
        "pause_abort_expiration_protocol_status": status,
        "pause_abort_expiration_protocol_ref": P7_R54_EV14_PROTOCOL_REF if status != P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF else "pause_abort_expiration_protocol_not_ready_bodyfree_20260626",
        "pause_abort_expiration_protocol_policy_ref": P7_R54_EV14_PROTOCOL_POLICY_REF,
        "pause_abort_expiration_protocol_reason_refs": dedupe_identifiers([reason_ref, *blockers], limit=100, max_length=180),
        "review_operation_status_ref": review_status,
        "review_operation_status_refs": list(P7_R54_EV14_REVIEW_OPERATION_STATUS_REFS),
        "review_operation_status_allowed": review_status_allowed,
        "purge_trigger_refs": list(P7_R54_EV14_PURGE_TRIGGER_REFS),
        "purge_trigger_ref_count": len(P7_R54_EV14_PURGE_TRIGGER_REFS),
        "review_session_cancelled_is_purge_trigger": "review_session_cancelled" in P7_R54_EV14_PURGE_TRIGGER_REFS,
        "review_session_aborted_is_purge_trigger": "review_session_aborted" in P7_R54_EV14_PURGE_TRIGGER_REFS,
        "retention_deadline_reached_is_purge_trigger": "retention_deadline_reached" in P7_R54_EV14_PURGE_TRIGGER_REFS,
        "required_local_delete_target_refs": list(P7_R54_EV14_REQUIRED_LOCAL_DELETE_TARGET_REFS),
        "required_local_delete_target_ref_count": len(P7_R54_EV14_REQUIRED_LOCAL_DELETE_TARGET_REFS),
        "body_full_packet_retention_hours": r54op.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
        "reviewer_notes_retention_after_rating_hours": r54op.P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
        "body_full_material_must_not_remain_after_cancel_or_deadline": True,
        "reviewer_notes_must_not_remain_after_cancel_or_deadline": True,
        "temporary_form_must_not_remain_after_cancel_or_deadline": True,
        "purge_before_handoff_required": True,
        "handoff_allowed_before_purge": False,
        "r52_reintake_handoff_allowed_before_purge": False,
        "review_paused_without_handoff": paused,
        "review_aborted_or_expired": abort_or_expired,
        "review_rating_or_question_incomplete": incomplete,
        "p5_decision_direction_ref": p5_decision_direction_ref,
        "p5_decision_direction_refs": list(P7_R54_EV14_P5_DECISION_DIRECTION_REFS),
        "p5_decision_materialized_here": False,
        "p5_inconclusive_direction_only_not_decision_materialized": p5_decision_direction_ref != "continue_after_purge_disposal_receipt",
        "ready_for_purge_disposal_receipt": ready_for_disposal,
        "purge_disposal_receipt_allowed_next": ready_for_disposal,
        "disposal_receipt_allowed_next": ready_for_disposal,
        "actual_rating_rows_materialized_here": bool(ev13.get("actual_rating_rows_materialized_here") is True) if ev13_ready else False,
        "actual_blocker_rows_materialized_here": bool(ev13.get("actual_blocker_rows_materialized_here") is True) if ev13_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev13.get("actual_question_need_observation_rows_materialized_here") is True) if ev13_ready else False,
        "actual_review_evidence_complete": False,
        "disposal_verified": False,
        "actual_disposal_receipt_materialized_here": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_EV15_STEP_REF if ready_for_disposal else (P7_R54_EV14_PAUSED_NEXT_REQUIRED_STEP_REF if paused else P7_R54_EV14_BLOCKED_NEXT_REQUIRED_STEP_REF),
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ev13.get("actual_rating_rows_materialized_here") is True) if ev13_ready else False,
        "actual_blocker_rows_materialized_here": bool(ev13.get("actual_blocker_rows_materialized_here") is True) if ev13_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev13.get("actual_question_need_observation_rows_materialized_here") is True) if ev13_ready else False,
    }
    assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(material)
    return material


def assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS, source="p7_r54_ev14_pause_abort_expiration_protocol")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        policy_section=P7_R54_EV14_STEP_REF,
        operation_step_ref=P7_R54_EV14_STEP_REF,
        source="p7_r54_ev14_pause_abort_expiration_protocol",
        false_flag_refs=_ev14_false_flag_refs(),
    )
    if data.get("ev13_schema_version") != P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("R54 EV14 EV13 schema reference changed")
    if safe_mapping(data.get("existing_op16_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV14 existing OP16 refs changed")
    if data.get("existing_op16_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV14 must classify existing OP16 refs as historical")
    if data.get("existing_op16_reused_as_actual_pause_abort_basis") is not False or data.get("existing_op16_reused_as_actual_protocol_basis") is not False:
        raise ValueError("R54 EV14 must not reuse 20260625 OP16 as actual pause/abort basis")
    if data.get("existing_op16_structural_contract_reused") is not True:
        raise ValueError("R54 EV14 must reuse only OP16 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV14 required case count changed")
    if data.get("pause_abort_expiration_protocol_status") not in P7_R54_EV14_PROTOCOL_STATUS_REFS:
        raise ValueError("R54 EV14 protocol status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV14 open execution blockers must match materialization blockers")
    if tuple(data.get("review_operation_status_refs") or ()) != P7_R54_EV14_REVIEW_OPERATION_STATUS_REFS:
        raise ValueError("R54 EV14 review operation status refs changed")
    if tuple(data.get("purge_trigger_refs") or ()) != P7_R54_EV14_PURGE_TRIGGER_REFS:
        raise ValueError("R54 EV14 purge trigger refs changed")
    if tuple(data.get("required_local_delete_target_refs") or ()) != P7_R54_EV14_REQUIRED_LOCAL_DELETE_TARGET_REFS:
        raise ValueError("R54 EV14 required delete target refs changed")
    if tuple(data.get("p5_decision_direction_refs") or ()) != P7_R54_EV14_P5_DECISION_DIRECTION_REFS:
        raise ValueError("R54 EV14 P5 direction refs changed")
    for true_key in (
        "operation_current_refs_used_as_actual_review_basis",
        "review_session_cancelled_is_purge_trigger",
        "review_session_aborted_is_purge_trigger",
        "retention_deadline_reached_is_purge_trigger",
        "body_full_material_must_not_remain_after_cancel_or_deadline",
        "reviewer_notes_must_not_remain_after_cancel_or_deadline",
        "temporary_form_must_not_remain_after_cancel_or_deadline",
        "purge_before_handoff_required",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV14 must keep {true_key}=True")
    for false_key in (
        "handoff_allowed_before_purge",
        "r52_reintake_handoff_allowed_before_purge",
        "p5_decision_materialized_here",
        "actual_review_evidence_complete",
        "disposal_verified",
        "actual_disposal_receipt_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV14 must keep {false_key}=False")
    status = data.get("pause_abort_expiration_protocol_status")
    if status == P7_R54_EV14_PROTOCOL_READY_STATUS_REF:
        if data.get("ev13_ready_for_pause_abort_expiration_protocol") is not True:
            raise ValueError("R54 EV14 ready protocol requires EV13 ready guard")
        if data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV14 ready protocol requires 24 rating and question rows")
        if data.get("ready_for_purge_disposal_receipt") is not True or data.get("purge_disposal_receipt_allowed_next") is not True:
            raise ValueError("R54 EV14 ready must allow EV15 only")
        if data.get("next_required_step") != P7_R54_EV15_STEP_REF:
            raise ValueError("R54 EV14 ready must point to EV15")
        if blockers:
            raise ValueError("R54 EV14 ready must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV14_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV14 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV14 not-yet steps changed")
    elif status in (P7_R54_EV14_PROTOCOL_ABORTED_STATUS_REF, P7_R54_EV14_PROTOCOL_EXPIRED_STATUS_REF, P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF):
        if data.get("ready_for_purge_disposal_receipt") is not True or data.get("next_required_step") != P7_R54_EV15_STEP_REF:
            raise ValueError("R54 EV14 abort/expire/incomplete must route to EV15 disposal")
        if data.get("p5_inconclusive_direction_only_not_decision_materialized") is not True:
            raise ValueError("R54 EV14 abort/expire/incomplete must mark inconclusive direction only")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV14_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV14 abort/expire/incomplete implemented steps changed")
    elif status == P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF:
        if data.get("review_paused_without_handoff") is not True:
            raise ValueError("R54 EV14 paused must remain without handoff")
        if data.get("ready_for_purge_disposal_receipt") is not False or data.get("next_required_step") != P7_R54_EV14_PAUSED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV14 paused next step changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV14_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV14 paused implemented steps changed")
    else:
        if status != P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV14 unknown protocol status")
        if data.get("ready_for_purge_disposal_receipt") is not False or data.get("next_required_step") != P7_R54_EV14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV14 blocked next step changed")
        if not blockers:
            raise ValueError("R54 EV14 blocked must carry execution blockers")
    return True


def build_p7_r54_ev15_purge_disposal_receipt(
    *,
    pause_abort_expiration_protocol: Mapping[str, Any] | None = None,
    body_removed: bool = False,
    reviewer_notes_removed: bool = False,
    temporary_form_removed: bool = False,
    local_packet_exported: bool = False,
    content_hash_of_body_stored: bool = False,
    disposal_receipt_ref: Any = "",
    material_id: Any = "p7_r54_ev15_purge_disposal_receipt",
) -> dict[str, Any]:
    """Build EV15 body-free purge / disposal receipt after external local verification."""

    ev14 = safe_mapping(pause_abort_expiration_protocol) if pause_abort_expiration_protocol is not None else build_p7_r54_ev14_pause_abort_expiration_protocol()
    assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(ev14)
    ev14_ready = bool(
        ev14.get("ready_for_purge_disposal_receipt") is True
        and ev14.get("purge_disposal_receipt_allowed_next") is True
        and ev14.get("next_required_step") == P7_R54_EV15_STEP_REF
        and not ev14.get("open_execution_blocker_ids")
    )
    receipt_ref = clean_identifier(disposal_receipt_ref, default="", max_length=220)
    blockers: list[str] = []
    if not ev14_ready:
        blockers.append("pause_abort_expiration_protocol_not_ready_for_ev15_disposal_receipt")
    if not body_removed:
        blockers.append("body_full_packet_not_removed")
    if not reviewer_notes_removed:
        blockers.append("reviewer_notes_not_removed")
    if not temporary_form_removed:
        blockers.append("temporary_form_not_removed")
    if local_packet_exported:
        blockers.append("local_packet_exported_during_disposal")
    if content_hash_of_body_stored:
        blockers.append("content_hash_of_body_stored_during_disposal")
    if receipt_ref != P7_R54_EV15_DISPOSAL_RECEIPT_REF:
        blockers.append("bodyfree_disposal_receipt_ref_missing_or_unexpected")
    blockers = dedupe_identifiers(blockers, limit=100, max_length=180)
    ready = bool(ev14_ready and not blockers)
    implemented_steps = P7_R54_EV15_IMPLEMENTED_STEPS if ev14_ready else tuple(ev14.get("implemented_steps") or P7_R54_EV14_IMPLEMENTED_STEPS)
    not_yet_steps = P7_R54_EV15_NOT_YET_IMPLEMENTED_STEPS if ev14_ready else tuple(ev14.get("not_yet_implemented_steps") or P7_R54_EV14_NOT_YET_IMPLEMENTED_STEPS)
    material = {
        "schema_version": P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV15_STEP_REF,
        "operation_step_ref": P7_R54_EV15_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev15_purge_disposal_receipt", max_length=220),
        "review_session_id": _safe_review_session_id(ev14.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev14_schema_version": P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "ev14_material_ref": clean_identifier(ev14.get("material_id"), default="p7_r54_ev14_pause_abort_expiration_protocol", max_length=220),
        "ev14_next_required_step": clean_identifier(ev14.get("next_required_step"), default="", max_length=220),
        "ev14_pause_abort_expiration_protocol_status": clean_identifier(ev14.get("pause_abort_expiration_protocol_status"), default=P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF, max_length=180),
        "ev14_purge_disposal_receipt_allowed_next": ev14_ready,
        "ev14_ready_for_purge_disposal_receipt": ev14_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op17_helper_ref": "build_p7_r54_op17_purge_disposal_receipt",
        "existing_op17_schema_version": r54op.P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "existing_op17_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op17_current_refs_are_historical_here": True,
        "existing_op17_reused_as_actual_disposal_basis": False,
        "existing_op17_reused_as_actual_disposal_receipt_basis": False,
        "existing_op17_reused_as_actual_disposal_basis": False,
        "existing_op17_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "rating_row_count": int(ev14.get("rating_row_count") or 0) if ev14_ready else 0,
        "question_observation_row_count": int(ev14.get("question_observation_row_count") or 0) if ev14_ready else 0,
        "purge_disposal_receipt_status": P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF if ready else P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF,
        "purge_disposal_receipt_ref": receipt_ref if ready else "purge_disposal_receipt_not_verified_bodyfree_20260626",
        "purge_disposal_receipt_policy_ref": P7_R54_EV15_DISPOSAL_RECEIPT_POLICY_REF,
        "purge_disposal_receipt_reason_refs": [P7_R54_EV15_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_EV15_BLOCKED_REASON_REF, *blockers], limit=100, max_length=180),
        "removal_target_refs": list(P7_R54_EV15_REMOVAL_TARGET_REFS),
        "removal_target_ref_count": len(P7_R54_EV15_REMOVAL_TARGET_REFS),
        "body_removed": bool(body_removed),
        "reviewer_notes_removed": bool(reviewer_notes_removed),
        "temporary_form_removed": bool(temporary_form_removed),
        "all_required_local_targets_removed": bool(body_removed and reviewer_notes_removed and temporary_form_removed),
        "local_packet_exported": bool(local_packet_exported),
        "content_hash_of_body_stored": bool(content_hash_of_body_stored),
        "body_full_packet_zip_inclusion_allowed": False,
        "reviewer_notes_export_allowed": False,
        "body_full_packet_export_allowed": False,
        "disposal_verified": ready,
        "actual_disposal_receipt_materialized_here": ready,
        "actual_disposal_run_here": False,
        "disposal_failure_decision_ref": "" if ready else P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF,
        "body_free_post_review_summary_allowed_next": ready,
        "actual_rating_rows_materialized_here": bool(ev14.get("actual_rating_rows_materialized_here") is True) if ev14_ready else False,
        "actual_blocker_rows_materialized_here": bool(ev14.get("actual_blocker_rows_materialized_here") is True) if ev14_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev14.get("actual_question_need_observation_rows_materialized_here") is True) if ev14_ready else False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(implemented_steps),
        "not_yet_implemented_steps": list(not_yet_steps),
        "next_required_step": P7_R54_EV16_NEXT_REQUIRED_STEP_REF if ready else P7_R54_EV15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ev14.get("actual_rating_rows_materialized_here") is True) if ev14_ready else False,
        "actual_blocker_rows_materialized_here": bool(ev14.get("actual_blocker_rows_materialized_here") is True) if ev14_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev14.get("actual_question_need_observation_rows_materialized_here") is True) if ev14_ready else False,
        "actual_disposal_receipt_materialized_here": ready,
        "disposal_verified": ready,
    }
    assert_p7_r54_ev15_purge_disposal_receipt_contract(material)
    return material


def assert_p7_r54_ev15_purge_disposal_receipt_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS, source="p7_r54_ev15_purge_disposal_receipt")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        policy_section=P7_R54_EV15_STEP_REF,
        operation_step_ref=P7_R54_EV15_STEP_REF,
        source="p7_r54_ev15_purge_disposal_receipt",
        false_flag_refs=_ev15_false_flag_refs(),
    )
    if data.get("ev14_schema_version") != P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION:
        raise ValueError("R54 EV15 EV14 schema reference changed")
    if safe_mapping(data.get("existing_op17_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV15 existing OP17 refs changed")
    if data.get("existing_op17_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV15 must classify existing OP17 refs as historical")
    if data.get("existing_op17_reused_as_actual_disposal_basis") is not False or data.get("existing_op17_reused_as_actual_disposal_receipt_basis") is not False:
        raise ValueError("R54 EV15 must not reuse 20260625 OP17 as actual disposal basis")
    if data.get("existing_op17_structural_contract_reused") is not True:
        raise ValueError("R54 EV15 must reuse only OP17 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV15 required case count changed")
    if data.get("purge_disposal_receipt_status") not in P7_R54_EV15_ALLOWED_DISPOSAL_STATUS_REFS:
        raise ValueError("R54 EV15 disposal status changed")
    if tuple(data.get("removal_target_refs") or ()) != P7_R54_EV15_REMOVAL_TARGET_REFS:
        raise ValueError("R54 EV15 removal target refs changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=100, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R54 EV15 open execution blockers must match materialization blockers")
    for true_key in (
        "operation_current_refs_used_as_actual_review_basis",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV15 must keep {true_key}=True")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "body_full_packet_zip_inclusion_allowed",
        "reviewer_notes_export_allowed",
        "body_full_packet_export_allowed",
        "actual_disposal_run_here",
        "actual_review_evidence_complete",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV15 must keep {false_key}=False")
    ready = data.get("purge_disposal_receipt_status") == P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF
    if ready:
        for true_key in (
            "ev14_purge_disposal_receipt_allowed_next",
            "ev14_ready_for_purge_disposal_receipt",
            "body_removed",
            "reviewer_notes_removed",
            "temporary_form_removed",
            "all_required_local_targets_removed",
            "disposal_verified",
            "actual_disposal_receipt_materialized_here",
            "body_free_post_review_summary_allowed_next",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 EV15 ready must keep {true_key}=True")
        if data.get("purge_disposal_receipt_ref") != P7_R54_EV15_DISPOSAL_RECEIPT_REF:
            raise ValueError("R54 EV15 ready receipt ref changed")
        if blockers:
            raise ValueError("R54 EV15 ready must not carry open execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV15_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV15 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV16_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV15 ready must point to EV16")
    else:
        if data.get("purge_disposal_receipt_status") != P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV15 blocked status changed")
        if data.get("disposal_verified") is not False or data.get("actual_disposal_receipt_materialized_here") is not False:
            raise ValueError("R54 EV15 blocked must not verify disposal")
        if data.get("body_free_post_review_summary_allowed_next") is not False:
            raise ValueError("R54 EV15 blocked must not allow EV16")
        if data.get("disposal_failure_decision_ref") != P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV15 blocked decision ref changed")
        if not blockers:
            raise ValueError("R54 EV15 blocked must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV15 blocked must point to repair")
    return True



P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev16_bodyfree_post_review_summary.bodyfree.v1"
)
P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev17_p5_decision_candidate_separation.bodyfree.v1"
)

P7_R54_EV16_STEP_REF: Final = P7_R54_EV16_NEXT_REQUIRED_STEP_REF
P7_R54_EV17_STEP_REF: Final = "R54-EV-17_p5_decision_candidate_separation"
P7_R54_EV18_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-18_p6_candidate_only_handoff"
P7_R54_EV16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV15_IMPLEMENTED_STEPS, P7_R54_EV16_STEP_REF)
P7_R54_EV16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV17_STEP_REF,)
P7_R54_EV17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV16_IMPLEMENTED_STEPS, P7_R54_EV17_STEP_REF)
P7_R54_EV17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV18_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV16_SUMMARY_READY_STATUS_REF: Final = "BODYFREE_POST_REVIEW_SUMMARY_READY_20260626"
P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF: Final = "BODYFREE_POST_REVIEW_SUMMARY_BLOCKED_20260626"
P7_R54_EV16_ALLOWED_SUMMARY_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV16_SUMMARY_READY_STATUS_REF,
    P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF,
)
P7_R54_EV16_SUMMARY_REF: Final = "r54_ev16_bodyfree_post_review_summary_20260626"
P7_R54_EV16_SUMMARY_POLICY_REF: Final = "rating_blocker_question_disposal_counts_only_no_body_no_question_text_20260626"
P7_R54_EV16_READY_REASON_REF: Final = "r54_ev16_rating_blocker_question_disposal_summary_ready_bodyfree"
P7_R54_EV16_BLOCKED_REASON_REF: Final = "r54_ev16_bodyfree_post_review_summary_blocked"
P7_R54_EV16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev16_blocked_until_bodyfree_summary_inputs_repaired_before_p5_decision_candidate_separation"

P7_R54_EV17_DECISION_SEPARATION_READY_STATUS_REF: Final = "P5_DECISION_CANDIDATE_SEPARATED_BODYFREE_20260626"
P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF: Final = "P5_DECISION_CANDIDATE_SEPARATION_BLOCKED_20260626"
P7_R54_EV17_ALLOWED_DECISION_SEPARATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV17_DECISION_SEPARATION_READY_STATUS_REF,
    P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF,
)
P7_R54_EV17_DECISION_SEPARATION_REF: Final = "r54_ev17_p5_decision_candidate_separation_bodyfree_20260626"
P7_R54_EV17_DECISION_SEPARATION_POLICY_REF: Final = "p5_candidate_p5_repair_p4_r12_inconclusive_separated_no_p6_p8_release_start_20260626"
P7_R54_EV17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev17_blocked_until_p5_decision_candidate_separation_repaired_before_p6_candidate_handoff"
P7_R54_EV17_P5_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "p5_repair_return_required_before_p6_candidate_handoff"
P7_R54_EV17_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "p4_r12_targeted_current_only_surface_repair_required_before_p6_candidate_handoff"
P7_R54_EV17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "r54_operation_inconclusive_retry_or_r52_reintake_before_p6_candidate_handoff"
P7_R54_EV17_NEXT_WORK_AFTER_EV16_REF: Final = "r54_ev17_p5_decision_candidate_separation_after_bodyfree_post_review_summary"
P7_R54_EV17_NEXT_WORK_AFTER_EV17_REF: Final = "r54_ev18_p6_candidate_only_handoff_after_p5_decision_candidate_separation"

P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF: Final = "P5_CONFIRMED_CANDIDATE"
P7_R54_EV17_P5_REPAIR_RETURN_REF: Final = "P5_REPAIR_RETURN"
P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF: Final = "P4_R12_TARGETED_CURRENT_ONLY_SURFACE_REPAIR"
P7_R54_EV17_INCONCLUSIVE_REF: Final = "R54_OPERATION_INCONCLUSIVE"
P7_R54_EV17_BLOCKED_PREFLIGHT_REF: Final = "R54_OPERATION_BLOCKED_PREFLIGHT"
P7_R54_EV17_BLOCKED_DISPOSAL_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL"
P7_R54_EV17_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF: Final = "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_EV17_BLOCKED_NO_TOUCH_VIOLATION_REF: Final = "R54_OPERATION_BLOCKED_NO_TOUCH_VIOLATION"
P7_R54_EV17_DECISION_CANDIDATE_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF,
    P7_R54_EV17_P5_REPAIR_RETURN_REF,
    P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF,
    P7_R54_EV17_INCONCLUSIVE_REF,
    P7_R54_EV17_BLOCKED_PREFLIGHT_REF,
    P7_R54_EV17_BLOCKED_DISPOSAL_REF,
    P7_R54_EV17_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
    P7_R54_EV17_BLOCKED_NO_TOUCH_VIOLATION_REF,
)
P7_R54_EV17_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R54_EV17_REPAIR_REQUIRED_REFS: Final[tuple[str, ...]] = (
    "emlis_readfeel_repair_required",
    "p5_surface_repair_required",
    "gate_boundary_repair_required",
    "p4_current_surface_repair_required",
)

P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev15_schema_version",
    "ev15_material_ref",
    "ev15_next_required_step",
    "ev15_purge_disposal_receipt_status",
    "ev15_bodyfree_summary_allowed_next",
    "ev13_schema_version",
    "ev13_material_ref",
    "ev13_next_required_step",
    "ev13_consistency_guard_status",
    "ev12_schema_version",
    "ev12_material_ref",
    "ev12_question_observation_normalization_status",
    "ev11_schema_version",
    "ev11_material_ref",
    "ev11_blocker_ingestion_status",
    "ev10_schema_version",
    "ev10_material_ref",
    "ev10_rating_row_normalization_status",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op18_helper_ref",
    "existing_op18_schema_version",
    "existing_op18_operation_current_refs",
    "existing_op18_current_refs_are_historical_here",
    "existing_op18_reused_as_actual_summary_basis",
    "existing_op18_reused_as_actual_post_review_summary_basis",
    "existing_op18_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "bodyfree_post_review_summary_status",
    "bodyfree_post_review_summary_ref",
    "bodyfree_post_review_summary_policy_ref",
    "bodyfree_post_review_summary_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "summary_blocker_ids",
    "summary_blocker_count",
    "verdict_counts",
    "axis_score_averages",
    "rating_axis_target_thresholds",
    "below_target_axis_refs",
    "below_target_axis_count",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "readfeel_blocker_counts",
    "execution_blocker_counts",
    "primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "p8_material_candidate_row_count",
    "p8_material_candidate_allowed_primary_class_counts",
    "not_question_repair_required_count",
    "insufficient_material_execution_blocker_count",
    "consistency_issue_count",
    "consistency_issue_direction_counts",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "temporary_form_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "all_required_review_counts_present",
    "all_required_summary_inputs_ready",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "p5_decision_candidate_separation_allowed_next",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev16_schema_version",
    "ev16_material_ref",
    "ev16_next_required_step",
    "ev16_bodyfree_post_review_summary_status",
    "ev16_decision_separation_allowed_next",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op19_helper_ref",
    "existing_op19_schema_version",
    "existing_op19_operation_current_refs",
    "existing_op19_current_refs_are_historical_here",
    "existing_op19_reused_as_actual_decision_basis",
    "existing_op19_reused_as_actual_decision_candidate_basis",
    "existing_op19_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "decision_candidate_separation_status",
    "decision_candidate_separation_ref",
    "decision_candidate_separation_policy_ref",
    "decision_candidate_separation_reason_refs",
    "decision_candidate_allowed_refs",
    "p5_decision_candidate_ref",
    "p5_decision_candidate_materialized_here",
    "p5_decision_candidate_reason_refs",
    "p5_decision_repair_reason_refs",
    "p5_decision_inconclusive_reason_refs",
    "p4_current_only_surface_issue_refs",
    "p5_confirmed_candidate_conditions_met",
    "p5_repair_return_required",
    "p4_r12_targeted_current_only_surface_repair_required",
    "r54_operation_inconclusive_required",
    "verdict_counts",
    "axis_score_averages",
    "rating_axis_target_thresholds",
    "below_target_axis_refs",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "primary_class_counts",
    "repair_required_counts",
    "p8_material_candidate_row_count",
    "p8_material_candidate_allowed_primary_class_counts",
    "not_question_repair_required_count",
    "insufficient_material_execution_blocker_count",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "temporary_form_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
    "p5_final_confirmation_blocked_here",
    "p6_start_blocked_here",
    "p8_start_blocked_here",
    "release_blocked_here",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev16_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_EV_FALSE_FLAG_REFS
        if key not in {
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
        }
    )


def _ev17_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_EV_FALSE_FLAG_REFS
        if key not in {
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
        }
    )


def _ev16_below_target_axis_refs(axis_averages: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    averages = safe_mapping(axis_averages)
    for axis, target in P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS.items():
        score = averages.get(axis)
        if not isinstance(score, (int, float)) or isinstance(score, bool) or float(score) < float(target):
            refs.append(axis)
    return refs


def _ev16_summary_inputs_ready(
    *,
    ev15: Mapping[str, Any],
    ev13: Mapping[str, Any],
    ev12: Mapping[str, Any],
    ev11: Mapping[str, Any],
    ev10: Mapping[str, Any],
) -> tuple[bool, list[str]]:
    blockers: list[str] = []
    if not (
        ev15.get("purge_disposal_receipt_status") == P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF
        and ev15.get("body_free_post_review_summary_allowed_next") is True
        and ev15.get("disposal_verified") is True
        and ev15.get("actual_disposal_receipt_materialized_here") is True
        and not ev15.get("open_execution_blocker_ids")
    ):
        blockers.append("ev15_disposal_receipt_not_verified_for_bodyfree_summary")
    if not (
        ev13.get("rating_question_consistency_guard_status") == P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF
        and int(ev13.get("consistency_issue_count") or 0) == 0
        and ev13.get("next_required_step") == P7_R54_EV14_STEP_REF
        and not ev13.get("open_execution_blocker_ids")
    ):
        blockers.append("ev13_consistency_guard_not_ready_for_bodyfree_summary")
    if not (
        ev12.get("question_observation_normalization_status") == P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
        and int(ev12.get("question_observation_row_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and ev12.get("actual_question_need_observation_rows_materialized_here") is True
        and not ev12.get("open_execution_blocker_ids")
    ):
        blockers.append("ev12_question_observation_rows_not_ready_for_bodyfree_summary")
    if not (
        ev11.get("blocker_ingestion_status") == P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF
        and ev11.get("actual_blocker_rows_materialized_here") is True
        and not ev11.get("open_execution_blocker_ids")
    ):
        blockers.append("ev11_blocker_ingestion_not_ready_for_bodyfree_summary")
    if not (
        ev10.get("rating_row_normalization_status") == P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
        and int(ev10.get("rating_row_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and ev10.get("actual_rating_rows_materialized_here") is True
        and not ev10.get("open_execution_blocker_ids")
    ):
        blockers.append("ev10_rating_rows_not_ready_for_bodyfree_summary")
    return (not blockers, blockers)


def build_p7_r54_ev16_bodyfree_post_review_summary(
    *,
    purge_disposal_receipt: Mapping[str, Any] | None = None,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization: Mapping[str, Any] | None = None,
    blocker_ingestion: Mapping[str, Any] | None = None,
    rating_row_normalization: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev16_bodyfree_post_review_summary",
) -> dict[str, Any]:
    """Build EV16 body-free post-review summary from rating/blocker/question/disposal evidence."""
    ev15 = safe_mapping(purge_disposal_receipt)
    if ev15:
        assert_p7_r54_ev15_purge_disposal_receipt_contract(ev15)
    ev13 = safe_mapping(rating_question_consistency_guard)
    if ev13:
        assert_p7_r54_ev13_rating_question_consistency_guard_contract(ev13)
    ev12 = safe_mapping(question_need_observation_row_normalization)
    if ev12:
        assert_p7_r54_ev12_question_need_observation_row_normalization_contract(ev12)
    ev11 = safe_mapping(blocker_ingestion)
    if ev11:
        assert_p7_r54_ev11_blocker_ingestion_contract(ev11)
    ev10 = safe_mapping(rating_row_normalization)
    if ev10:
        assert_p7_r54_ev10_rating_row_normalization_contract(ev10)

    inputs_ready, input_blockers = _ev16_summary_inputs_ready(ev15=ev15, ev13=ev13, ev12=ev12, ev11=ev11, ev10=ev10)
    verdict_counts = safe_mapping(ev10.get("verdict_counts")) if inputs_ready else {}
    axis_score_averages = safe_mapping(ev10.get("axis_score_averages")) if inputs_ready else {}
    below_target_axis_refs = _ev16_below_target_axis_refs(axis_score_averages) if inputs_ready else []
    open_execution_blockers = dedupe_identifiers(
        [
            *input_blockers,
            *(ev15.get("open_execution_blocker_ids") or []),
            *(ev13.get("open_execution_blocker_ids") or []),
            *(ev12.get("open_execution_blocker_ids") or []),
            *(ev11.get("open_execution_blocker_ids") or []),
            *(ev10.get("open_execution_blocker_ids") or []),
        ],
        limit=120,
        max_length=180,
    )
    counts_ready = bool(
        int(ev10.get("reviewed_case_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(ev10.get("rating_row_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(ev12.get("question_observation_row_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    no_body_leak_validation_passed = bool(
        inputs_ready
        and ev15.get("local_packet_exported") is False
        and ev15.get("content_hash_of_body_stored") is False
        and ev12.get("raw_body_absent_for_all_rows") is True
        and ev12.get("comment_text_absent_for_all_rows") is True
        and ev12.get("local_path_absent_for_all_rows") is True
        and ev12.get("body_hash_absent_for_all_rows") is True
    )
    no_question_text_validation_passed = bool(
        inputs_ready
        and ev12.get("question_text_absent_for_all_rows") is True
        and ev12.get("draft_question_text_absent_for_all_rows") is True
        and ev12.get("question_text_or_draft_text_saved_here") is False
    )
    no_touch_validation_passed = bool(
        inputs_ready
        and _no_touch_contract().get("api_changed") is False
        and _no_touch_contract().get("db_changed") is False
        and _no_touch_contract().get("rn_changed") is False
        and _no_touch_contract().get("runtime_changed") is False
        and _no_touch_contract().get("release_allowed") is False
    )
    summary_ready = bool(
        inputs_ready
        and counts_ready
        and not open_execution_blockers
        and no_body_leak_validation_passed
        and no_question_text_validation_passed
        and no_touch_validation_passed
        and int(ev13.get("consistency_issue_count") or 0) == 0
        and ev15.get("disposal_verified") is True
    )
    reason_refs = [P7_R54_EV16_READY_REASON_REF] if summary_ready else dedupe_identifiers(
        [P7_R54_EV16_BLOCKED_REASON_REF, *open_execution_blockers],
        limit=120,
        max_length=180,
    )
    material = {
        "schema_version": P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV16_STEP_REF,
        "operation_step_ref": P7_R54_EV16_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev16_bodyfree_post_review_summary", max_length=220),
        "review_session_id": _safe_review_session_id(ev15.get("review_session_id") or ev13.get("review_session_id") or ev10.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev15_schema_version": P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "ev15_material_ref": clean_identifier(ev15.get("material_id"), default="p7_r54_ev15_purge_disposal_receipt", max_length=220),
        "ev15_next_required_step": clean_identifier(ev15.get("next_required_step"), default="", max_length=180),
        "ev15_purge_disposal_receipt_status": clean_identifier(ev15.get("purge_disposal_receipt_status"), default=P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF, max_length=180),
        "ev15_bodyfree_summary_allowed_next": ev15.get("body_free_post_review_summary_allowed_next") is True,
        "ev13_schema_version": P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "ev13_material_ref": clean_identifier(ev13.get("material_id"), default="p7_r54_ev13_rating_question_consistency_guard", max_length=220),
        "ev13_next_required_step": clean_identifier(ev13.get("next_required_step"), default="", max_length=180),
        "ev13_consistency_guard_status": clean_identifier(ev13.get("rating_question_consistency_guard_status"), default=P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF, max_length=180),
        "ev12_schema_version": P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "ev12_material_ref": clean_identifier(ev12.get("material_id"), default="p7_r54_ev12_question_need_observation_row_normalization", max_length=220),
        "ev12_question_observation_normalization_status": clean_identifier(ev12.get("question_observation_normalization_status"), default=P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "ev11_schema_version": P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION,
        "ev11_material_ref": clean_identifier(ev11.get("material_id"), default="p7_r54_ev11_blocker_ingestion", max_length=220),
        "ev11_blocker_ingestion_status": clean_identifier(ev11.get("blocker_ingestion_status"), default=P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF, max_length=180),
        "ev10_schema_version": P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "ev10_material_ref": clean_identifier(ev10.get("material_id"), default="p7_r54_ev10_rating_row_normalization", max_length=220),
        "ev10_rating_row_normalization_status": clean_identifier(ev10.get("rating_row_normalization_status"), default=P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op18_helper_ref": "build_p7_r54_op18_bodyfree_post_review_summary",
        "existing_op18_schema_version": r54op.P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "existing_op18_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op18_current_refs_are_historical_here": True,
        "existing_op18_reused_as_actual_summary_basis": False,
        "existing_op18_reused_as_actual_post_review_summary_basis": False,
        "existing_op18_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(ev10.get("reviewed_case_count") or 0) if inputs_ready else 0,
        "rating_row_count": int(ev10.get("rating_row_count") or 0) if inputs_ready else 0,
        "question_observation_row_count": int(ev12.get("question_observation_row_count") or 0) if inputs_ready else 0,
        "bodyfree_post_review_summary_status": P7_R54_EV16_SUMMARY_READY_STATUS_REF if summary_ready else P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF,
        "bodyfree_post_review_summary_ref": P7_R54_EV16_SUMMARY_REF if summary_ready else "r54_ev16_bodyfree_post_review_summary_not_ready",
        "bodyfree_post_review_summary_policy_ref": P7_R54_EV16_SUMMARY_POLICY_REF,
        "bodyfree_post_review_summary_reason_refs": reason_refs,
        "execution_blocker_ids": [] if summary_ready else open_execution_blockers,
        "open_execution_blocker_ids": [] if summary_ready else open_execution_blockers,
        "summary_blocker_ids": [] if summary_ready else open_execution_blockers,
        "summary_blocker_count": 0 if summary_ready else len(open_execution_blockers),
        "verdict_counts": dict(verdict_counts),
        "axis_score_averages": dict(axis_score_averages),
        "rating_axis_target_thresholds": dict(P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": below_target_axis_refs,
        "below_target_axis_count": len(below_target_axis_refs),
        "open_readfeel_blocker_count": int(ev11.get("open_readfeel_blocker_count") or 0) if inputs_ready else 0,
        "open_execution_blocker_count": int(ev11.get("open_execution_blocker_count") or 0) if inputs_ready else len(open_execution_blockers),
        "readfeel_blocker_counts": dict(safe_mapping(ev11.get("readfeel_blocker_counts"))) if inputs_ready else {},
        "execution_blocker_counts": dict(safe_mapping(ev11.get("execution_blocker_counts"))) if inputs_ready else {},
        "primary_class_counts": dict(safe_mapping(ev12.get("question_need_primary_class_counts"))) if inputs_ready else {},
        "ambiguity_kind_counts": dict(safe_mapping(ev12.get("ambiguity_kind_counts"))) if inputs_ready else {},
        "one_question_fit_counts": dict(safe_mapping(ev12.get("one_question_fit_counts"))) if inputs_ready else {},
        "repair_required_counts": dict(safe_mapping(ev12.get("repair_required_counts"))) if inputs_ready else {},
        "plan_candidate_flag_counts": dict(safe_mapping(ev12.get("plan_candidate_flag_counts"))) if inputs_ready else {},
        "p8_material_candidate_row_count": int(ev12.get("p8_material_candidate_allowed_row_count") or 0) if inputs_ready else 0,
        "p8_material_candidate_allowed_primary_class_counts": dict(safe_mapping(ev12.get("p8_material_candidate_allowed_primary_class_counts"))) if inputs_ready else {},
        "not_question_repair_required_count": int(ev12.get("not_question_repair_required_count") or 0) if inputs_ready else 0,
        "insufficient_material_execution_blocker_count": int(ev12.get("insufficient_material_execution_blocker_count") or 0) if inputs_ready else 0,
        "consistency_issue_count": int(ev13.get("consistency_issue_count") or 0) if inputs_ready else 0,
        "consistency_issue_direction_counts": dict(safe_mapping(ev13.get("consistency_issue_direction_counts"))) if inputs_ready else {},
        "disposal_verified": ev15.get("disposal_verified") is True if inputs_ready else False,
        "body_removed": ev15.get("body_removed") is True if inputs_ready else False,
        "reviewer_notes_removed": ev15.get("reviewer_notes_removed") is True if inputs_ready else False,
        "temporary_form_removed": ev15.get("temporary_form_removed") is True if inputs_ready else False,
        "local_packet_exported": ev15.get("local_packet_exported") is True,
        "content_hash_of_body_stored": ev15.get("content_hash_of_body_stored") is True,
        "all_required_review_counts_present": counts_ready,
        "all_required_summary_inputs_ready": inputs_ready,
        "no_body_leak_validation_passed": no_body_leak_validation_passed,
        "no_question_text_validation_passed": no_question_text_validation_passed,
        "no_touch_validation_passed": no_touch_validation_passed,
        "p5_decision_candidate_separation_allowed_next": summary_ready,
        "actual_rating_rows_materialized_here": bool(ev10.get("actual_rating_rows_materialized_here") is True) if inputs_ready else False,
        "actual_blocker_rows_materialized_here": bool(ev11.get("actual_blocker_rows_materialized_here") is True) if inputs_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev12.get("actual_question_need_observation_rows_materialized_here") is True) if inputs_ready else False,
        "actual_disposal_receipt_materialized_here": bool(ev15.get("actual_disposal_receipt_materialized_here") is True) if inputs_ready else False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "implemented_steps": list(P7_R54_EV16_IMPLEMENTED_STEPS if summary_ready else tuple(ev15.get("implemented_steps") or P7_R54_EV15_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV16_NOT_YET_IMPLEMENTED_STEPS if summary_ready else tuple(ev15.get("not_yet_implemented_steps") or P7_R54_EV15_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_EV17_NEXT_WORK_AFTER_EV16_REF if summary_ready else P7_R54_EV16_NEXT_REQUIRED_STEP_REF,
        "next_required_step": P7_R54_EV17_STEP_REF if summary_ready else P7_R54_EV16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ev10.get("actual_rating_rows_materialized_here") is True) if inputs_ready else False,
        "actual_blocker_rows_materialized_here": bool(ev11.get("actual_blocker_rows_materialized_here") is True) if inputs_ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev12.get("actual_question_need_observation_rows_materialized_here") is True) if inputs_ready else False,
        "actual_disposal_receipt_materialized_here": bool(ev15.get("actual_disposal_receipt_materialized_here") is True) if inputs_ready else False,
        "disposal_verified": ev15.get("disposal_verified") is True if inputs_ready else False,
    }
    assert_p7_r54_ev16_bodyfree_post_review_summary_contract(material)
    return material


def assert_p7_r54_ev16_bodyfree_post_review_summary_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS, source="p7_r54_ev16_bodyfree_post_review_summary")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        policy_section=P7_R54_EV16_STEP_REF,
        operation_step_ref=P7_R54_EV16_STEP_REF,
        source="p7_r54_ev16_bodyfree_post_review_summary",
        false_flag_refs=_ev16_false_flag_refs(),
    )
    if data.get("ev15_schema_version") != P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION:
        raise ValueError("R54 EV16 EV15 schema reference changed")
    if data.get("ev13_schema_version") != P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("R54 EV16 EV13 schema reference changed")
    if safe_mapping(data.get("existing_op18_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV16 existing OP18 refs changed")
    if data.get("existing_op18_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV16 must classify existing OP18 refs as historical")
    if data.get("existing_op18_reused_as_actual_summary_basis") is not False or data.get("existing_op18_reused_as_actual_post_review_summary_basis") is not False:
        raise ValueError("R54 EV16 must not reuse 20260625 OP18 as actual summary basis")
    if data.get("existing_op18_structural_contract_reused") is not True:
        raise ValueError("R54 EV16 must reuse only OP18 structural contract")
    if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("R54 EV16 required case count changed")
    if data.get("bodyfree_post_review_summary_status") not in P7_R54_EV16_ALLOWED_SUMMARY_STATUS_REFS:
        raise ValueError("R54 EV16 summary status changed")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=120, max_length=180)
    if data.get("open_execution_blocker_ids") != blockers or data.get("summary_blocker_ids") != blockers:
        raise ValueError("R54 EV16 open execution blockers must match summary blockers")
    for true_key in (
        "operation_current_refs_used_as_actual_review_basis",
        "human_review_completion_claim_blocked_here",
        "actual_human_review_completion_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV16 must keep {true_key}=True")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "actual_review_evidence_complete",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV16 must keep {false_key}=False")
    ready = data.get("bodyfree_post_review_summary_status") == P7_R54_EV16_SUMMARY_READY_STATUS_REF
    if data.get("p5_decision_candidate_separation_allowed_next") is not ready:
        raise ValueError("R54 EV16 decision separation allowance must match readiness")
    p8_material_counts = safe_mapping(data.get("p8_material_candidate_allowed_primary_class_counts"))
    if data.get("p8_material_candidate_row_count") != sum(int(value or 0) for value in p8_material_counts.values()):
        raise ValueError("R54 EV16 P8 material candidate row count must match primary class counts")
    if not set(p8_material_counts).issubset(set(P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS)):
        raise ValueError("R54 EV16 P8 material primary class counts outside frozen refs")
    if ready:
        if data.get("bodyfree_post_review_summary_ref") != P7_R54_EV16_SUMMARY_REF:
            raise ValueError("R54 EV16 summary ref changed")
        if data.get("bodyfree_post_review_summary_reason_refs") != [P7_R54_EV16_READY_REASON_REF]:
            raise ValueError("R54 EV16 ready reason refs changed")
        if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("reviewed_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV16 ready summary must preserve 24 reviewed cases")
        if data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV16 ready summary must preserve 24 rating/question rows")
        for true_key in (
            "all_required_review_counts_present",
            "all_required_summary_inputs_ready",
            "disposal_verified",
            "body_removed",
            "reviewer_notes_removed",
            "temporary_form_removed",
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 EV16 ready summary must keep {true_key}=True")
        if data.get("open_execution_blocker_ids") != [] or data.get("summary_blocker_count") != 0 or data.get("consistency_issue_count") != 0:
            raise ValueError("R54 EV16 ready summary must not carry open execution blockers or consistency issues")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV16_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV16 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV17_STEP_REF:
            raise ValueError("R54 EV16 ready summary must point to EV17")
    else:
        if data.get("bodyfree_post_review_summary_status") != P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV16 blocked status changed")
        if data.get("disposal_verified") is not False:
            raise ValueError("R54 EV16 blocked summary must not verify disposal")
        if data.get("p5_decision_candidate_separation_allowed_next") is not False:
            raise ValueError("R54 EV16 blocked summary must not allow EV17")
        if not blockers:
            raise ValueError("R54 EV16 blocked summary must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV16 blocked summary must point to repair")
    return True


def _ev17_p5_repair_reason_refs(summary: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(summary)
    reasons: list[str] = []
    verdict_counts = safe_mapping(data.get("verdict_counts"))
    for verdict_ref in ("RED", "REPAIR_REQUIRED", "YELLOW"):
        if int(verdict_counts.get(verdict_ref) or 0) > 0:
            reasons.append(f"{verdict_ref.lower()}_verdict_present")
    readfeel_counts = safe_mapping(data.get("readfeel_blocker_counts"))
    for blocker_id in P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS:
        if int(readfeel_counts.get(blocker_id) or 0) > 0:
            reasons.append(f"readfeel_blocker:{blocker_id}")
    for axis in data.get("below_target_axis_refs") or []:
        reasons.append(f"axis_below_target:{clean_identifier(axis, max_length=120)}")
    primary_counts = safe_mapping(data.get("primary_class_counts"))
    for primary_class_ref in P7_R54_EV17_NOT_QUESTION_REPAIR_PRIMARY_CLASS_REFS:
        if int(primary_counts.get(primary_class_ref) or 0) > 0:
            reasons.append(f"not_question_repair_primary_class:{primary_class_ref}")
    repair_counts = safe_mapping(data.get("repair_required_counts"))
    for repair_ref in P7_R54_EV17_REPAIR_REQUIRED_REFS:
        if int(repair_counts.get(repair_ref) or 0) > 0:
            reasons.append(f"repair_required_ref:{repair_ref}")
    if int(data.get("not_question_repair_required_count") or 0) > 0:
        reasons.append("not_question_repair_required_row_present")
    return dedupe_identifiers(reasons, limit=100, max_length=180)


def _ev17_p5_inconclusive_reason_refs(summary: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(summary)
    reasons: list[str] = []
    if data.get("bodyfree_post_review_summary_status") != P7_R54_EV16_SUMMARY_READY_STATUS_REF:
        reasons.append("ev16_bodyfree_post_review_summary_not_ready")
    if int(data.get("open_execution_blocker_count") or 0) > 0:
        reasons.append("open_execution_blocker_present")
    if int(data.get("insufficient_material_execution_blocker_count") or 0) > 0:
        reasons.append("insufficient_material_execution_blocker_present")
    if int(data.get("consistency_issue_count") or 0) > 0:
        reasons.append("rating_question_consistency_issue_present")
    if data.get("disposal_verified") is not True:
        reasons.append("disposal_not_verified")
    if data.get("no_body_leak_validation_passed") is not True:
        reasons.append("no_body_leak_validation_not_passed")
    if data.get("no_question_text_validation_passed") is not True:
        reasons.append("no_question_text_validation_not_passed")
    if data.get("no_touch_validation_passed") is not True:
        reasons.append("no_touch_validation_not_passed")
    if int(data.get("reviewed_case_count") or 0) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        reasons.append("reviewed_case_count_not_24")
    if int(data.get("rating_row_count") or 0) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        reasons.append("rating_row_count_not_24")
    if int(data.get("question_observation_row_count") or 0) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        reasons.append("question_observation_row_count_not_24")
    return dedupe_identifiers(reasons, limit=100, max_length=180)


def _ev17_confirmed_candidate_conditions_met(summary: Mapping[str, Any]) -> bool:
    data = safe_mapping(summary)
    verdict_counts = safe_mapping(data.get("verdict_counts"))
    return bool(
        data.get("bodyfree_post_review_summary_status") == P7_R54_EV16_SUMMARY_READY_STATUS_REF
        and int(data.get("reviewed_case_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(data.get("rating_row_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(data.get("question_observation_row_count") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(verdict_counts.get("PASS") or 0) == P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and int(verdict_counts.get("YELLOW") or 0) == 0
        and int(verdict_counts.get("REPAIR_REQUIRED") or 0) == 0
        and int(verdict_counts.get("RED") or 0) == 0
        and int(verdict_counts.get("NOT_REVIEWABLE") or 0) == 0
        and int(data.get("open_readfeel_blocker_count") or 0) == 0
        and int(data.get("open_execution_blocker_count") or 0) == 0
        and int(data.get("below_target_axis_count") or 0) == 0
        and int(data.get("not_question_repair_required_count") or 0) == 0
        and int(data.get("insufficient_material_execution_blocker_count") or 0) == 0
        and data.get("disposal_verified") is True
        and data.get("body_removed") is True
        and data.get("reviewer_notes_removed") is True
        and data.get("temporary_form_removed") is True
        and data.get("local_packet_exported") is False
        and data.get("content_hash_of_body_stored") is False
        and data.get("no_body_leak_validation_passed") is True
        and data.get("no_question_text_validation_passed") is True
        and data.get("no_touch_validation_passed") is True
        and not _ev17_p5_repair_reason_refs(data)
        and not _ev17_p5_inconclusive_reason_refs(data)
    )


def build_p7_r54_ev17_p5_decision_candidate_separation(
    *,
    bodyfree_post_review_summary: Mapping[str, Any] | None = None,
    p4_current_only_surface_issue_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_ev17_p5_decision_candidate_separation",
) -> dict[str, Any]:
    """Build EV17 body-free P5 decision candidate separation without final/start/release promotion."""
    ev16 = safe_mapping(bodyfree_post_review_summary)
    if ev16:
        assert_p7_r54_ev16_bodyfree_post_review_summary_contract(ev16)
    ev16_ready = bool(
        ev16.get("bodyfree_post_review_summary_status") == P7_R54_EV16_SUMMARY_READY_STATUS_REF
        and ev16.get("p5_decision_candidate_separation_allowed_next") is True
        and ev16.get("next_required_step") == P7_R54_EV17_STEP_REF
    )
    p4_issue_refs = dedupe_identifiers(p4_current_only_surface_issue_refs or [], limit=24, max_length=180)
    repair_reasons = _ev17_p5_repair_reason_refs(ev16) if ev16_ready else []
    inconclusive_reasons = _ev17_p5_inconclusive_reason_refs(ev16) if ev16_ready else ["ev16_bodyfree_post_review_summary_not_ready"]
    confirmed_conditions_met = bool(ev16_ready and not p4_issue_refs and _ev17_confirmed_candidate_conditions_met(ev16))
    if not ev16_ready:
        decision = P7_R54_EV17_INCONCLUSIVE_REF
    elif p4_issue_refs:
        decision = P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF
    elif repair_reasons:
        decision = P7_R54_EV17_P5_REPAIR_RETURN_REF
    elif confirmed_conditions_met:
        decision = P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF
    else:
        decision = P7_R54_EV17_INCONCLUSIVE_REF
        if not inconclusive_reasons:
            inconclusive_reasons = ["p5_confirmed_candidate_conditions_not_all_met"]
    separation_ready = bool(ev16_ready)
    if decision == P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF:
        decision_reason_refs = ["p5_confirmed_candidate_conditions_met_bodyfree"]
        next_step = P7_R54_EV18_NEXT_REQUIRED_STEP_REF
    elif decision == P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF:
        decision_reason_refs = ["current_only_surface_issue_requires_p4_r12_targeted_repair"]
        next_step = P7_R54_EV17_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF
    elif decision == P7_R54_EV17_P5_REPAIR_RETURN_REF:
        decision_reason_refs = ["p5_repair_return_required_by_bodyfree_review_summary"]
        next_step = P7_R54_EV17_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    elif separation_ready:
        decision_reason_refs = ["r54_operation_inconclusive_by_bodyfree_review_summary"]
        next_step = P7_R54_EV17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF
    else:
        decision_reason_refs = ["p5_decision_candidate_separation_blocked_by_ev16_summary"]
        next_step = P7_R54_EV17_BLOCKED_NEXT_REQUIRED_STEP_REF
    material = {
        "schema_version": P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV17_STEP_REF,
        "operation_step_ref": P7_R54_EV17_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev17_p5_decision_candidate_separation", max_length=220),
        "review_session_id": _safe_review_session_id(ev16.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev16_schema_version": P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "ev16_material_ref": clean_identifier(ev16.get("material_id"), default="p7_r54_ev16_bodyfree_post_review_summary", max_length=220),
        "ev16_next_required_step": clean_identifier(ev16.get("next_required_step"), default="", max_length=180),
        "ev16_bodyfree_post_review_summary_status": clean_identifier(ev16.get("bodyfree_post_review_summary_status"), default=P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF, max_length=180),
        "ev16_decision_separation_allowed_next": ev16_ready,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op19_helper_ref": "build_p7_r54_op19_p5_decision_candidate_separation",
        "existing_op19_schema_version": r54op.P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "existing_op19_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op19_current_refs_are_historical_here": True,
        "existing_op19_reused_as_actual_decision_basis": False,
        "existing_op19_reused_as_actual_decision_candidate_basis": False,
        "existing_op19_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(ev16.get("reviewed_case_count") or 0),
        "rating_row_count": int(ev16.get("rating_row_count") or 0),
        "question_observation_row_count": int(ev16.get("question_observation_row_count") or 0),
        "decision_candidate_separation_status": P7_R54_EV17_DECISION_SEPARATION_READY_STATUS_REF if separation_ready else P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF,
        "decision_candidate_separation_ref": P7_R54_EV17_DECISION_SEPARATION_REF if separation_ready else "r54_ev17_p5_decision_candidate_separation_not_ready",
        "decision_candidate_separation_policy_ref": P7_R54_EV17_DECISION_SEPARATION_POLICY_REF,
        "decision_candidate_separation_reason_refs": ["p5_decision_candidate_separation_ready_bodyfree"] if separation_ready else ["ev16_summary_not_ready_for_p5_decision_candidate_separation"],
        "decision_candidate_allowed_refs": list(P7_R54_EV17_DECISION_CANDIDATE_REFS),
        "p5_decision_candidate_ref": decision,
        "p5_decision_candidate_materialized_here": separation_ready,
        "p5_decision_candidate_reason_refs": decision_reason_refs,
        "p5_decision_repair_reason_refs": repair_reasons,
        "p5_decision_inconclusive_reason_refs": inconclusive_reasons if decision == P7_R54_EV17_INCONCLUSIVE_REF else [],
        "p4_current_only_surface_issue_refs": p4_issue_refs,
        "p5_confirmed_candidate_conditions_met": confirmed_conditions_met,
        "p5_repair_return_required": decision == P7_R54_EV17_P5_REPAIR_RETURN_REF,
        "p4_r12_targeted_current_only_surface_repair_required": decision == P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF,
        "r54_operation_inconclusive_required": decision == P7_R54_EV17_INCONCLUSIVE_REF,
        "verdict_counts": dict(safe_mapping(ev16.get("verdict_counts"))),
        "axis_score_averages": dict(safe_mapping(ev16.get("axis_score_averages"))),
        "rating_axis_target_thresholds": dict(P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": list(ev16.get("below_target_axis_refs") or []),
        "open_readfeel_blocker_count": int(ev16.get("open_readfeel_blocker_count") or 0),
        "open_execution_blocker_count": int(ev16.get("open_execution_blocker_count") or 0),
        "primary_class_counts": dict(safe_mapping(ev16.get("primary_class_counts"))),
        "repair_required_counts": dict(safe_mapping(ev16.get("repair_required_counts"))),
        "p8_material_candidate_row_count": int(ev16.get("p8_material_candidate_row_count") or 0),
        "p8_material_candidate_allowed_primary_class_counts": dict(safe_mapping(ev16.get("p8_material_candidate_allowed_primary_class_counts"))),
        "not_question_repair_required_count": int(ev16.get("not_question_repair_required_count") or 0),
        "insufficient_material_execution_blocker_count": int(ev16.get("insufficient_material_execution_blocker_count") or 0),
        "disposal_verified": ev16.get("disposal_verified") is True,
        "body_removed": ev16.get("body_removed") is True,
        "reviewer_notes_removed": ev16.get("reviewer_notes_removed") is True,
        "temporary_form_removed": ev16.get("temporary_form_removed") is True,
        "local_packet_exported": ev16.get("local_packet_exported") is True,
        "content_hash_of_body_stored": ev16.get("content_hash_of_body_stored") is True,
        "no_body_leak_validation_passed": ev16.get("no_body_leak_validation_passed") is True,
        "no_question_text_validation_passed": ev16.get("no_question_text_validation_passed") is True,
        "no_touch_validation_passed": ev16.get("no_touch_validation_passed") is True,
        "p5_human_blind_qa_confirmed_candidate": decision == P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "p5_final_confirmation_blocked_here": True,
        "p6_start_blocked_here": True,
        "p8_start_blocked_here": True,
        "release_blocked_here": True,
        "actual_review_evidence_complete": False,
        "actual_rating_rows_materialized_here": bool(ev16.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ev16.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(ev16.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_disposal_receipt_materialized_here": bool(ev16.get("actual_disposal_receipt_materialized_here") is True),
        "implemented_steps": list(P7_R54_EV17_IMPLEMENTED_STEPS if separation_ready else tuple(ev16.get("implemented_steps") or P7_R54_EV16_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV17_NOT_YET_IMPLEMENTED_STEPS if separation_ready else tuple(ev16.get("not_yet_implemented_steps") or P7_R54_EV16_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_EV17_NEXT_WORK_AFTER_EV17_REF if separation_ready else P7_R54_EV17_NEXT_WORK_AFTER_EV16_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ev16.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ev16.get("actual_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(ev16.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_disposal_receipt_materialized_here": bool(ev16.get("actual_disposal_receipt_materialized_here") is True),
        "disposal_verified": ev16.get("disposal_verified") is True,
        "p5_human_blind_qa_confirmed_candidate": decision == P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF,
    }
    assert_p7_r54_ev17_p5_decision_candidate_separation_contract(material)
    return material


def assert_p7_r54_ev17_p5_decision_candidate_separation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS, source="p7_r54_ev17_p5_decision_candidate_separation")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        policy_section=P7_R54_EV17_STEP_REF,
        operation_step_ref=P7_R54_EV17_STEP_REF,
        source="p7_r54_ev17_p5_decision_candidate_separation",
        false_flag_refs=_ev17_false_flag_refs(),
    )
    if data.get("ev16_schema_version") != P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION:
        raise ValueError("R54 EV17 EV16 schema reference changed")
    if safe_mapping(data.get("existing_op19_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV17 existing OP19 refs changed")
    if data.get("existing_op19_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV17 must classify existing OP19 refs as historical")
    if data.get("existing_op19_reused_as_actual_decision_basis") is not False or data.get("existing_op19_reused_as_actual_decision_candidate_basis") is not False:
        raise ValueError("R54 EV17 must not reuse 20260625 OP19 as actual decision basis")
    if data.get("existing_op19_structural_contract_reused") is not True:
        raise ValueError("R54 EV17 must reuse only OP19 structural contract")
    if data.get("p5_decision_candidate_ref") not in P7_R54_EV17_DECISION_CANDIDATE_REFS:
        raise ValueError("R54 EV17 decision candidate ref outside allowed refs")
    if data.get("decision_candidate_separation_status") not in P7_R54_EV17_ALLOWED_DECISION_SEPARATION_STATUS_REFS:
        raise ValueError("R54 EV17 separation status changed")
    separation_ready = data.get("decision_candidate_separation_status") == P7_R54_EV17_DECISION_SEPARATION_READY_STATUS_REF
    if data.get("p5_decision_candidate_materialized_here") is not separation_ready:
        raise ValueError("R54 EV17 materialized flag must match separation readiness")
    if data.get("p5_human_blind_qa_confirmed_final") is not False or data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        raise ValueError("R54 EV17 must not finalize P5 or start P6/P8/release")
    p8_material_counts = safe_mapping(data.get("p8_material_candidate_allowed_primary_class_counts"))
    if data.get("p8_material_candidate_row_count") != sum(int(value or 0) for value in p8_material_counts.values()):
        raise ValueError("R54 EV17 P8 material candidate row count must match primary class counts")
    if not set(p8_material_counts).issubset(set(P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS)):
        raise ValueError("R54 EV17 P8 material primary class counts outside frozen refs")
    for true_key in (
        "operation_current_refs_used_as_actual_review_basis",
        "p5_final_confirmation_blocked_here",
        "p6_start_blocked_here",
        "p8_start_blocked_here",
        "release_blocked_here",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R54 EV17 must keep {true_key}=True")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "actual_review_evidence_complete",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV17 must keep {false_key}=False")
    if separation_ready:
        if data.get("decision_candidate_separation_ref") != P7_R54_EV17_DECISION_SEPARATION_REF:
            raise ValueError("R54 EV17 separation ref changed")
        if data.get("decision_candidate_separation_reason_refs") != ["p5_decision_candidate_separation_ready_bodyfree"]:
            raise ValueError("R54 EV17 ready reason refs changed")
        if data.get("required_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV17 ready separation must carry 24-case evidence counts")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV17_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV17 not-yet steps changed")
        if data.get("p5_decision_candidate_ref") == P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF:
            if data.get("p5_human_blind_qa_confirmed_candidate") is not True or data.get("p5_confirmed_candidate_conditions_met") is not True:
                raise ValueError("R54 EV17 P5 confirmed candidate must be candidate-only and condition-backed")
            if data.get("next_required_step") != P7_R54_EV18_NEXT_REQUIRED_STEP_REF:
                raise ValueError("R54 EV17 P5 confirmed candidate must point to EV18 candidate-only handoff")
        else:
            if data.get("p5_human_blind_qa_confirmed_candidate") is not False:
                raise ValueError("R54 EV17 non-confirmed decision must not set P5 candidate flag")
            if data.get("p5_decision_candidate_ref") == P7_R54_EV17_P5_REPAIR_RETURN_REF and data.get("next_required_step") != P7_R54_EV17_P5_REPAIR_NEXT_REQUIRED_STEP_REF:
                raise ValueError("R54 EV17 P5 repair decision next step changed")
            if data.get("p5_decision_candidate_ref") == P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF and data.get("next_required_step") != P7_R54_EV17_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF:
                raise ValueError("R54 EV17 P4-R12 decision next step changed")
            if data.get("p5_decision_candidate_ref") == P7_R54_EV17_INCONCLUSIVE_REF and data.get("next_required_step") != P7_R54_EV17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF:
                raise ValueError("R54 EV17 inconclusive decision next step changed")
    else:
        if data.get("decision_candidate_separation_status") != P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV17 blocked status changed")
        if data.get("p5_decision_candidate_ref") != P7_R54_EV17_INCONCLUSIVE_REF:
            raise ValueError("R54 EV17 blocked decision must be inconclusive")
        if data.get("next_required_step") != P7_R54_EV17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV17 blocked separation must point to repair")
    return True



# ---------------------------------------------------------------------------
# R54-EV-18 / R54-EV-19: candidate-only handoffs.
# These steps intentionally create candidate handoffs only. They do not start
# P6/P8, do not finalize P5, and do not create question text or runtime/API/DB/RN
# mutations.
# ---------------------------------------------------------------------------

P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev18_p6_candidate_only_handoff.bodyfree.v1"
)
P7_R54_EV_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev19_p8_material_candidate_only_handoff.bodyfree.v1"
)

P7_R54_EV18_STEP_REF: Final = P7_R54_EV18_NEXT_REQUIRED_STEP_REF
P7_R54_EV19_STEP_REF: Final = "R54-EV-19_p8_material_candidate_only_handoff"
P7_R54_EV20_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-20_final_no_body_leak_no_question_text_no_touch_validation"

P7_R54_EV18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV17_IMPLEMENTED_STEPS, P7_R54_EV18_STEP_REF)
P7_R54_EV18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV19_STEP_REF,)
P7_R54_EV19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV18_IMPLEMENTED_STEPS, P7_R54_EV19_STEP_REF)
P7_R54_EV19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV20_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV18_P6_CANDIDATE_HANDOFF_READY_STATUS_REF: Final = "P6_CANDIDATE_ONLY_HANDOFF_READY_BODYFREE_20260626"
P7_R54_EV18_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF: Final = "P6_CANDIDATE_ONLY_HANDOFF_BLOCKED_20260626"
P7_R54_EV18_ALLOWED_P6_CANDIDATE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV18_P6_CANDIDATE_HANDOFF_READY_STATUS_REF,
    P7_R54_EV18_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF,
)
P7_R54_EV18_P6_CANDIDATE_HANDOFF_REF: Final = "R54_EV18_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_ONLY_HANDOFF_20260626"
P7_R54_EV18_P6_CANDIDATE_REF: Final = "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_FROM_EV17_P5_CONFIRMED_CANDIDATE_BODYFREE"
P7_R54_EV18_READY_REASON_REF: Final = "r54_ev18_p6_candidate_only_handoff_ready_from_p5_confirmed_candidate_bodyfree"
P7_R54_EV18_BLOCKED_REASON_REF: Final = "r54_ev18_p6_candidate_only_handoff_blocked_until_ev17_p5_confirmed_candidate"
P7_R54_EV18_CANDIDATE_ONLY_POLICY_REF: Final = "p6_candidate_only_handoff_start_allowed_false_20260626"
P7_R54_EV18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev18_blocked_until_ev17_p5_confirmed_candidate_before_p6_candidate_handoff"
P7_R54_EV18_NEXT_WORK_AFTER_EV17_REF: Final = "r54_ev18_p6_candidate_only_handoff_after_p5_decision_candidate_separation"
P7_R54_EV18_NEXT_WORK_AFTER_EV18_REF: Final = "r54_ev19_p8_material_candidate_only_handoff_after_p6_candidate_handoff"

P7_R54_EV19_P8_MATERIAL_HANDOFF_READY_STATUS_REF: Final = "P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_READY_BODYFREE_20260626"
P7_R54_EV19_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF: Final = "P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_BLOCKED_20260626"
P7_R54_EV19_ALLOWED_P8_MATERIAL_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV19_P8_MATERIAL_HANDOFF_READY_STATUS_REF,
    P7_R54_EV19_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF,
)
P7_R54_EV19_P8_MATERIAL_HANDOFF_REF: Final = "R54_EV19_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_ONLY_HANDOFF_20260626"
P7_R54_EV19_P8_MATERIAL_CANDIDATE_REF: Final = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_FROM_R54_EV_BODYFREE_OBSERVATION"
P7_R54_EV19_READY_REASON_REF: Final = "r54_ev19_p8_material_candidate_only_handoff_ready_from_question_observation_rows_bodyfree"
P7_R54_EV19_NO_MATERIAL_REASON_REF: Final = "r54_ev19_p8_material_candidate_only_handoff_ready_no_question_material_rows_bodyfree"
P7_R54_EV19_BLOCKED_REASON_REF: Final = "r54_ev19_p8_material_candidate_only_handoff_blocked_until_ev18_p6_candidate_handoff_ready"
P7_R54_EV19_CANDIDATE_ONLY_POLICY_REF: Final = "p8_material_candidate_only_start_allowed_false_question_implementation_false_20260626"
P7_R54_EV19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev19_blocked_until_ev18_p6_candidate_handoff_before_p8_material_handoff"
P7_R54_EV19_NEXT_WORK_AFTER_EV19_REF: Final = "r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_after_p8_material_candidate_handoff"

P7_R54_EV18_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev17_schema_version",
    "ev17_material_ref",
    "ev17_next_required_step",
    "ev17_decision_candidate_separation_status",
    "ev17_p5_decision_candidate_ref",
    "ev17_p5_confirmed_candidate_conditions_met",
    "ev17_p5_human_blind_qa_confirmed_candidate",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op20_helper_ref",
    "existing_op20_schema_version",
    "existing_op20_operation_current_refs",
    "existing_op20_current_refs_are_historical_here",
    "existing_op20_reused_as_actual_p6_candidate_basis",
    "existing_op20_reused_as_actual_p6_candidate_handoff_basis",
    "existing_op20_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "p6_candidate_handoff_status",
    "p6_candidate_handoff_ref",
    "p6_candidate_handoff_policy_ref",
    "p6_candidate_handoff_reason_refs",
    "p6_limited_human_readfeel_candidate_ref",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_candidate_basis_ref",
    "p6_candidate_only_policy_ref",
    "p6_candidate_only_not_start",
    "p6_start_blocked_here",
    "p6_candidate_handoff_materialized_here",
    "p8_material_candidate_handoff_allowed_next",
    "p8_material_candidate_row_count",
    "p8_material_candidate_allowed_primary_class_counts",
    "p8_material_candidate_primary_class_refs",
    "primary_class_counts",
    "verdict_counts",
    "axis_score_averages",
    "rating_axis_target_thresholds",
    "below_target_axis_refs",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "disposal_verified",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "question_implementation_started_here",
    "p8_implementation_spec_finalized_here",
    "release_allowed",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_path_included",
    *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
    "ev18_schema_version",
    "ev18_material_ref",
    "ev18_next_required_step",
    "ev18_p6_candidate_handoff_status",
    "ev18_p6_limited_human_readfeel_candidate",
    "ev18_p6_limited_human_readfeel_start_allowed",
    "operation_current_refs",
    "operation_current_ref_count",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis",
    "operation_current_refs_used_as_actual_review_basis",
    "existing_op21_helper_ref",
    "existing_op21_schema_version",
    "existing_op21_operation_current_refs",
    "existing_op21_current_refs_are_historical_here",
    "existing_op21_reused_as_actual_p8_material_basis",
    "existing_op21_reused_as_actual_p8_material_handoff_basis",
    "existing_op21_structural_contract_reused",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "p8_material_candidate_handoff_status",
    "p8_material_candidate_handoff_ref",
    "p8_material_candidate_handoff_policy_ref",
    "p8_material_candidate_handoff_reason_refs",
    "question_need_observation_rows_aggregated",
    "question_need_observation_rows_aggregated_count",
    "p8_material_candidate_primary_class_refs",
    "p8_material_candidate_allowed_primary_class_counts",
    "p8_material_candidate_row_count",
    "p8_question_design_material_candidate",
    "p8_question_design_material_candidate_ref",
    "p8_design_material_candidate_only_not_start",
    "p8_candidate_only_policy_ref",
    "p8_start_allowed",
    "question_implementation_started_here",
    "p8_implementation_spec_finalized_here",
    "question_trigger_logic_implemented",
    "question_answer_persistence_implemented",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_plan_guard_implemented",
    "question_storage_schema_implemented",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "question_text_included",
    "draft_question_text_included",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "release_allowed",
    "actual_review_evidence_complete",
    "human_review_completion_claim_blocked_here",
    "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r54_ev_no_touch_contract",
    "body_free_markers",
    "body_free",
    "raw_body_included",
    "local_path_included",
    "disposal_verified",
    *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev18_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_EV_FALSE_FLAG_REFS
        if key not in {
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
        }
    )


def _ev19_false_flag_refs() -> tuple[str, ...]:
    return _ev18_false_flag_refs()


def _ev18_p6_candidate_blocker_refs(ev17: Mapping[str, Any]) -> list[str]:
    data = safe_mapping(ev17)
    blockers: list[str] = []
    if data.get("decision_candidate_separation_status") != P7_R54_EV17_DECISION_SEPARATION_READY_STATUS_REF:
        blockers.append("ev17_p5_decision_candidate_separation_not_ready_for_p6_handoff")
    if data.get("p5_decision_candidate_ref") != P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF:
        blockers.append("p5_confirmed_candidate_not_available_for_ev18_p6_candidate_handoff")
    if data.get("p5_confirmed_candidate_conditions_met") is not True:
        blockers.append("p5_confirmed_candidate_conditions_not_met_for_ev18_p6_candidate_handoff")
    if data.get("p5_human_blind_qa_confirmed_candidate") is not True:
        blockers.append("p5_human_blind_qa_confirmed_candidate_flag_not_true_for_ev18_p6_handoff")
    if data.get("next_required_step") != P7_R54_EV18_STEP_REF:
        blockers.append("ev17_next_required_step_not_ev18_p6_candidate_handoff")
    if data.get("p5_human_blind_qa_confirmed_final") is not False:
        blockers.append("p5_final_confirmation_must_not_precede_ev18_p6_candidate_handoff")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        blockers.append("ev17_must_not_allow_p6_p8_or_release_before_ev18")
    if int(data.get("rating_row_count") or 0) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("rating_row_count_not_24_for_ev18_p6_candidate_handoff")
    if int(data.get("question_observation_row_count") or 0) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("question_observation_row_count_not_24_for_ev18_p6_candidate_handoff")
    if int(data.get("open_readfeel_blocker_count") or 0) != 0 or int(data.get("open_execution_blocker_count") or 0) != 0:
        blockers.append("open_blocker_count_not_zero_for_ev18_p6_candidate_handoff")
    if data.get("disposal_verified") is not True:
        blockers.append("disposal_not_verified_for_ev18_p6_candidate_handoff")
    if data.get("no_body_leak_validation_passed") is not True or data.get("no_question_text_validation_passed") is not True or data.get("no_touch_validation_passed") is not True:
        blockers.append("final_bodyfree_no_touch_validation_not_ready_for_ev18")
    return dedupe_identifiers(blockers, limit=80, max_length=180)


def build_p7_r54_ev18_p6_candidate_only_handoff(
    *,
    p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev18_p6_candidate_only_handoff",
) -> dict[str, Any]:
    """Build EV18 body-free P6 candidate-only handoff, not P6 start."""
    ev17 = safe_mapping(p5_decision_candidate_separation) if p5_decision_candidate_separation is not None else build_p7_r54_ev17_p5_decision_candidate_separation()
    assert_p7_r54_ev17_p5_decision_candidate_separation_contract(ev17)
    blockers = _ev18_p6_candidate_blocker_refs(ev17)
    ready = not blockers
    p8_material_counts = dict(safe_mapping(ev17.get("p8_material_candidate_allowed_primary_class_counts"))) if ready else {}
    p8_candidate_row_count = sum(int(value or 0) for value in p8_material_counts.values()) if ready else 0
    material = {
        "schema_version": P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV18_STEP_REF,
        "operation_step_ref": P7_R54_EV18_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev18_p6_candidate_only_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(ev17.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev17_schema_version": P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "ev17_material_ref": clean_identifier(ev17.get("material_id"), default="p7_r54_ev17_p5_decision_candidate_separation", max_length=220),
        "ev17_next_required_step": clean_identifier(ev17.get("next_required_step"), default="", max_length=180),
        "ev17_decision_candidate_separation_status": clean_identifier(ev17.get("decision_candidate_separation_status"), default=P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF, max_length=180),
        "ev17_p5_decision_candidate_ref": clean_identifier(ev17.get("p5_decision_candidate_ref"), default=P7_R54_EV17_INCONCLUSIVE_REF, max_length=180),
        "ev17_p5_confirmed_candidate_conditions_met": ev17.get("p5_confirmed_candidate_conditions_met") is True,
        "ev17_p5_human_blind_qa_confirmed_candidate": ev17.get("p5_human_blind_qa_confirmed_candidate") is True,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op20_helper_ref": "build_p7_r54_op20_p6_candidate_handoff",
        "existing_op20_schema_version": r54op.P7_R54_OPERATION_P6_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "existing_op20_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op20_current_refs_are_historical_here": True,
        "existing_op20_reused_as_actual_p6_candidate_basis": False,
        "existing_op20_reused_as_actual_p6_candidate_handoff_basis": False,
        "existing_op20_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(ev17.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(ev17.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(ev17.get("question_observation_row_count") or 0) if ready else 0,
        "p6_candidate_handoff_status": P7_R54_EV18_P6_CANDIDATE_HANDOFF_READY_STATUS_REF if ready else P7_R54_EV18_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF,
        "p6_candidate_handoff_ref": P7_R54_EV18_P6_CANDIDATE_HANDOFF_REF if ready else "p6_candidate_handoff_not_ready_bodyfree_20260626",
        "p6_candidate_handoff_policy_ref": P7_R54_EV18_CANDIDATE_ONLY_POLICY_REF,
        "p6_candidate_handoff_reason_refs": [P7_R54_EV18_READY_REASON_REF] if ready else dedupe_identifiers([P7_R54_EV18_BLOCKED_REASON_REF, *blockers], limit=80, max_length=180),
        "p6_limited_human_readfeel_candidate_ref": P7_R54_EV18_P6_CANDIDATE_REF if ready else "",
        "p6_limited_human_readfeel_candidate": ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_candidate_basis_ref": "ev17_p5_confirmed_candidate_conditions_bodyfree_review_summary" if ready else "ev17_p5_confirmed_candidate_required_before_p6_candidate",
        "p6_candidate_only_policy_ref": P7_R54_EV18_CANDIDATE_ONLY_POLICY_REF,
        "p6_candidate_only_not_start": True,
        "p6_start_blocked_here": True,
        "p6_candidate_handoff_materialized_here": ready,
        "p8_material_candidate_handoff_allowed_next": ready,
        "p8_material_candidate_row_count": p8_candidate_row_count,
        "p8_material_candidate_allowed_primary_class_counts": p8_material_counts,
        "p8_material_candidate_primary_class_refs": list(p8_material_counts.keys()),
        "primary_class_counts": dict(safe_mapping(ev17.get("primary_class_counts"))) if ready else {},
        "verdict_counts": dict(safe_mapping(ev17.get("verdict_counts"))) if ready else {},
        "axis_score_averages": dict(safe_mapping(ev17.get("axis_score_averages"))) if ready else {},
        "rating_axis_target_thresholds": dict(P7_R54_EV08_RATING_AXIS_TARGET_THRESHOLDS),
        "below_target_axis_refs": list(ev17.get("below_target_axis_refs") or []) if ready else [],
        "open_readfeel_blocker_count": int(ev17.get("open_readfeel_blocker_count") or 0) if ready else 0,
        "open_execution_blocker_count": int(ev17.get("open_execution_blocker_count") or 0) if ready else len(blockers),
        "disposal_verified": ev17.get("disposal_verified") is True and ready,
        "no_body_leak_validation_passed": ev17.get("no_body_leak_validation_passed") is True and ready,
        "no_question_text_validation_passed": ev17.get("no_question_text_validation_passed") is True and ready,
        "no_touch_validation_passed": ev17.get("no_touch_validation_passed") is True and ready,
        "p5_human_blind_qa_confirmed_candidate": ev17.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "release_allowed": False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "actual_rating_rows_materialized_here": bool(ev17.get("actual_rating_rows_materialized_here") is True) if ready else False,
        "actual_blocker_rows_materialized_here": bool(ev17.get("actual_blocker_rows_materialized_here") is True) if ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev17.get("actual_question_need_observation_rows_materialized_here") is True) if ready else False,
        "actual_disposal_receipt_materialized_here": bool(ev17.get("actual_disposal_receipt_materialized_here") is True) if ready else False,
        "execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "open_execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "implemented_steps": list(P7_R54_EV18_IMPLEMENTED_STEPS if ready else tuple(ev17.get("implemented_steps") or P7_R54_EV17_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV18_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ev17.get("not_yet_implemented_steps") or P7_R54_EV17_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_EV18_NEXT_WORK_AFTER_EV18_REF if ready else P7_R54_EV18_NEXT_WORK_AFTER_EV17_REF,
        "next_required_step": P7_R54_EV19_STEP_REF if ready else P7_R54_EV18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ev17.get("actual_rating_rows_materialized_here") is True) if ready else False,
        "actual_blocker_rows_materialized_here": bool(ev17.get("actual_blocker_rows_materialized_here") is True) if ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev17.get("actual_question_need_observation_rows_materialized_here") is True) if ready else False,
        "actual_disposal_receipt_materialized_here": bool(ev17.get("actual_disposal_receipt_materialized_here") is True) if ready else False,
        "disposal_verified": ev17.get("disposal_verified") is True and ready,
        "p5_human_blind_qa_confirmed_candidate": ev17.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
    }
    assert_p7_r54_ev18_p6_candidate_only_handoff_contract(material)
    return material


def assert_p7_r54_ev18_p6_candidate_only_handoff_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV18_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_ev18_p6_candidate_only_handoff")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_EV18_STEP_REF,
        operation_step_ref=P7_R54_EV18_STEP_REF,
        source="p7_r54_ev18_p6_candidate_only_handoff",
        false_flag_refs=_ev18_false_flag_refs(),
    )
    if data.get("ev17_schema_version") != P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION:
        raise ValueError("R54 EV18 EV17 schema reference changed")
    if safe_mapping(data.get("existing_op20_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV18 existing OP20 refs changed")
    if data.get("existing_op20_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV18 must classify existing OP20 refs as historical")
    if data.get("existing_op20_reused_as_actual_p6_candidate_basis") is not False or data.get("existing_op20_reused_as_actual_p6_candidate_handoff_basis") is not False:
        raise ValueError("R54 EV18 must not reuse 20260625 OP20 as actual P6 candidate basis")
    if data.get("existing_op20_structural_contract_reused") is not True:
        raise ValueError("R54 EV18 must reuse only OP20 structural contract")
    if data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        raise ValueError("R54 EV18 must not start P6/P8 or release")
    if data.get("p5_human_blind_qa_confirmed_final") is not False or data.get("actual_review_evidence_complete") is not False:
        raise ValueError("R54 EV18 must not finalize P5 or actual review evidence")
    if data.get("p8_question_design_material_candidate") is not False or data.get("question_implementation_started_here") is not False or data.get("p8_implementation_spec_finalized_here") is not False:
        raise ValueError("R54 EV18 must not create P8 material candidate or implementation")
    if data.get("p6_candidate_only_not_start") is not True or data.get("p6_start_blocked_here") is not True:
        raise ValueError("R54 EV18 must explicitly block P6 start")
    ready = data.get("p6_candidate_handoff_status") == P7_R54_EV18_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
    if data.get("p6_candidate_handoff_status") not in P7_R54_EV18_ALLOWED_P6_CANDIDATE_HANDOFF_STATUS_REFS:
        raise ValueError("R54 EV18 P6 candidate status changed")
    if data.get("p6_limited_human_readfeel_candidate") is not ready:
        raise ValueError("R54 EV18 P6 candidate flag must match readiness")
    if data.get("p6_candidate_handoff_materialized_here") is not ready:
        raise ValueError("R54 EV18 materialization flag must match readiness")
    if data.get("p8_material_candidate_handoff_allowed_next") is not ready:
        raise ValueError("R54 EV18 P8 material handoff allowance must match readiness")
    p8_material_counts = safe_mapping(data.get("p8_material_candidate_allowed_primary_class_counts"))
    if data.get("p8_material_candidate_row_count") != sum(int(value or 0) for value in p8_material_counts.values()):
        raise ValueError("R54 EV18 P8 material row count must match primary class counts")
    if tuple(data.get("p8_material_candidate_primary_class_refs") or ()) != tuple(p8_material_counts.keys()):
        raise ValueError("R54 EV18 P8 material primary refs must match count keys")
    if not set(p8_material_counts).issubset(set(P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS)):
        raise ValueError("R54 EV18 P8 material counts outside frozen primary class refs")
    if ready:
        if data.get("p6_candidate_handoff_ref") != P7_R54_EV18_P6_CANDIDATE_HANDOFF_REF:
            raise ValueError("R54 EV18 ready handoff ref changed")
        if data.get("p6_limited_human_readfeel_candidate_ref") != P7_R54_EV18_P6_CANDIDATE_REF:
            raise ValueError("R54 EV18 P6 candidate ref changed")
        if data.get("p6_candidate_handoff_reason_refs") != [P7_R54_EV18_READY_REASON_REF]:
            raise ValueError("R54 EV18 ready reason refs changed")
        if data.get("ev17_p5_decision_candidate_ref") != P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF or data.get("ev17_p5_confirmed_candidate_conditions_met") is not True:
            raise ValueError("R54 EV18 ready requires EV17 P5 confirmed candidate")
        if data.get("ev17_p5_human_blind_qa_confirmed_candidate") is not True or data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R54 EV18 ready must retain P5 candidate basis as body-free")
        if data.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV18 ready must preserve 24 rating/question rows")
        if data.get("open_readfeel_blocker_count") != 0 or data.get("open_execution_blocker_count") != 0 or data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV18 ready must not carry open blockers")
        if data.get("disposal_verified") is not True:
            raise ValueError("R54 EV18 ready must preserve verified disposal receipt")
        for true_key in (
            "no_body_leak_validation_passed",
            "no_question_text_validation_passed",
            "no_touch_validation_passed",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 EV18 ready must keep {true_key}=True")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV18_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV18 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV18 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV19_STEP_REF:
            raise ValueError("R54 EV18 ready must point to EV19")
    else:
        if data.get("p6_candidate_handoff_status") != P7_R54_EV18_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV18 blocked status changed")
        if data.get("p6_candidate_handoff_ref") != "p6_candidate_handoff_not_ready_bodyfree_20260626":
            raise ValueError("R54 EV18 blocked handoff ref changed")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV18 blocked must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV18 blocked must point to repair")
    return True


def build_p7_r54_ev19_p8_material_candidate_only_handoff(
    *,
    p6_candidate_only_handoff: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r54_ev19_p8_material_candidate_only_handoff",
) -> dict[str, Any]:
    """Build EV19 body-free P8 material candidate-only handoff, not P8 start."""
    ev18 = safe_mapping(p6_candidate_only_handoff) if p6_candidate_only_handoff is not None else build_p7_r54_ev18_p6_candidate_only_handoff()
    assert_p7_r54_ev18_p6_candidate_only_handoff_contract(ev18)
    ready = bool(
        ev18.get("p6_candidate_handoff_status") == P7_R54_EV18_P6_CANDIDATE_HANDOFF_READY_STATUS_REF
        and ev18.get("p8_material_candidate_handoff_allowed_next") is True
        and ev18.get("next_required_step") == P7_R54_EV19_STEP_REF
    )
    blockers = [] if ready else [P7_R54_EV19_BLOCKED_REASON_REF, "ev18_p6_candidate_handoff_not_ready_for_p8_material_candidate_handoff"]
    p8_material_counts = dict(safe_mapping(ev18.get("p8_material_candidate_allowed_primary_class_counts"))) if ready else {}
    p8_candidate_row_count = sum(int(value or 0) for value in p8_material_counts.values()) if ready else 0
    p8_candidate = bool(ready and p8_candidate_row_count > 0)
    material = {
        "schema_version": P7_R54_EV_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV19_STEP_REF,
        "operation_step_ref": P7_R54_EV19_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev19_p8_material_candidate_only_handoff", max_length=220),
        "review_session_id": _safe_review_session_id(ev18.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev18_schema_version": P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        "ev18_material_ref": clean_identifier(ev18.get("material_id"), default="p7_r54_ev18_p6_candidate_only_handoff", max_length=220),
        "ev18_next_required_step": clean_identifier(ev18.get("next_required_step"), default="", max_length=180),
        "ev18_p6_candidate_handoff_status": clean_identifier(ev18.get("p6_candidate_handoff_status"), default=P7_R54_EV18_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF, max_length=180),
        "ev18_p6_limited_human_readfeel_candidate": ev18.get("p6_limited_human_readfeel_candidate") is True,
        "ev18_p6_limited_human_readfeel_start_allowed": ev18.get("p6_limited_human_readfeel_start_allowed") is True,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op21_helper_ref": "build_p7_r54_op21_p8_material_candidate_handoff",
        "existing_op21_schema_version": r54op.P7_R54_OPERATION_P8_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "existing_op21_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op21_current_refs_are_historical_here": True,
        "existing_op21_reused_as_actual_p8_material_basis": False,
        "existing_op21_reused_as_actual_p8_material_handoff_basis": False,
        "existing_op21_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(ev18.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(ev18.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(ev18.get("question_observation_row_count") or 0) if ready else 0,
        "p8_material_candidate_handoff_status": P7_R54_EV19_P8_MATERIAL_HANDOFF_READY_STATUS_REF if ready else P7_R54_EV19_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF,
        "p8_material_candidate_handoff_ref": P7_R54_EV19_P8_MATERIAL_HANDOFF_REF if ready else "p8_material_candidate_handoff_not_ready_bodyfree_20260626",
        "p8_material_candidate_handoff_policy_ref": P7_R54_EV19_CANDIDATE_ONLY_POLICY_REF,
        "p8_material_candidate_handoff_reason_refs": (
            [P7_R54_EV19_READY_REASON_REF] if p8_candidate else [P7_R54_EV19_NO_MATERIAL_REASON_REF]
        ) if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "question_need_observation_rows_aggregated": ready,
        "question_need_observation_rows_aggregated_count": int(ev18.get("question_observation_row_count") or 0) if ready else 0,
        "p8_material_candidate_primary_class_refs": list(p8_material_counts.keys()),
        "p8_material_candidate_allowed_primary_class_counts": p8_material_counts,
        "p8_material_candidate_row_count": p8_candidate_row_count,
        "p8_question_design_material_candidate": p8_candidate,
        "p8_question_design_material_candidate_ref": P7_R54_EV19_P8_MATERIAL_CANDIDATE_REF if p8_candidate else "",
        "p8_design_material_candidate_only_not_start": True,
        "p8_candidate_only_policy_ref": P7_R54_EV19_CANDIDATE_ONLY_POLICY_REF,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented": False,
        "question_answer_persistence_implemented": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_plan_guard_implemented": False,
        "question_storage_schema_implemented": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "api_db_rn_response_key_changed_here": False,
        "runtime_changed_here": False,
        "p5_human_blind_qa_confirmed_candidate": ev18.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": ev18.get("p6_limited_human_readfeel_candidate") is True if ready else False,
        "p6_limited_human_readfeel_start_allowed": False,
        "release_allowed": False,
        "actual_review_evidence_complete": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "actual_rating_rows_materialized_here": bool(ev18.get("actual_rating_rows_materialized_here") is True) if ready else False,
        "actual_blocker_rows_materialized_here": bool(ev18.get("actual_blocker_rows_materialized_here") is True) if ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev18.get("actual_question_need_observation_rows_materialized_here") is True) if ready else False,
        "actual_disposal_receipt_materialized_here": bool(ev18.get("actual_disposal_receipt_materialized_here") is True) if ready else False,
        "execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "open_execution_blocker_ids": [] if ready else dedupe_identifiers(blockers, limit=80, max_length=180),
        "implemented_steps": list(P7_R54_EV19_IMPLEMENTED_STEPS if ready else tuple(ev18.get("implemented_steps") or P7_R54_EV18_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV19_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ev18.get("not_yet_implemented_steps") or P7_R54_EV18_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_EV19_NEXT_WORK_AFTER_EV19_REF if ready else P7_R54_EV18_NEXT_WORK_AFTER_EV18_REF,
        "next_required_step": P7_R54_EV20_NEXT_REQUIRED_STEP_REF if ready else P7_R54_EV19_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": bool(ev18.get("actual_rating_rows_materialized_here") is True) if ready else False,
        "actual_blocker_rows_materialized_here": bool(ev18.get("actual_blocker_rows_materialized_here") is True) if ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(ev18.get("actual_question_need_observation_rows_materialized_here") is True) if ready else False,
        "actual_disposal_receipt_materialized_here": bool(ev18.get("actual_disposal_receipt_materialized_here") is True) if ready else False,
        "disposal_verified": ev18.get("disposal_verified") is True and ready,
        "p5_human_blind_qa_confirmed_candidate": ev18.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented": False,
    }
    assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract(material)
    return material


def assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS, source="p7_r54_ev19_p8_material_candidate_only_handoff")
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION,
        policy_section=P7_R54_EV19_STEP_REF,
        operation_step_ref=P7_R54_EV19_STEP_REF,
        source="p7_r54_ev19_p8_material_candidate_only_handoff",
        false_flag_refs=_ev19_false_flag_refs(),
    )
    if data.get("ev18_schema_version") != P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION:
        raise ValueError("R54 EV19 EV18 schema reference changed")
    if safe_mapping(data.get("existing_op21_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV19 existing OP21 refs changed")
    if data.get("existing_op21_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV19 must classify existing OP21 refs as historical")
    if data.get("existing_op21_reused_as_actual_p8_material_basis") is not False or data.get("existing_op21_reused_as_actual_p8_material_handoff_basis") is not False:
        raise ValueError("R54 EV19 must not reuse 20260625 OP21 as actual P8 material basis")
    if data.get("existing_op21_structural_contract_reused") is not True:
        raise ValueError("R54 EV19 must reuse only OP21 structural contract")
    if data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        raise ValueError("R54 EV19 must not start P8 or release")
    for false_key in (
        "question_implementation_started_here",
        "p8_implementation_spec_finalized_here",
        "question_trigger_logic_implemented",
        "question_answer_persistence_implemented",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_plan_guard_implemented",
        "question_storage_schema_implemented",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "api_db_rn_response_key_changed_here",
        "runtime_changed_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV19 must keep {false_key}=False")
    if data.get("p8_design_material_candidate_only_not_start") is not True:
        raise ValueError("R54 EV19 must be candidate-only, not P8 start")
    if data.get("actual_review_evidence_complete") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False:
        raise ValueError("R54 EV19 must not finalize P5 or actual review evidence")
    ready = data.get("p8_material_candidate_handoff_status") == P7_R54_EV19_P8_MATERIAL_HANDOFF_READY_STATUS_REF
    if data.get("p8_material_candidate_handoff_status") not in P7_R54_EV19_ALLOWED_P8_MATERIAL_HANDOFF_STATUS_REFS:
        raise ValueError("R54 EV19 P8 material status changed")
    if data.get("question_need_observation_rows_aggregated") is not ready:
        raise ValueError("R54 EV19 aggregation flag must match readiness")
    p8_material_counts = safe_mapping(data.get("p8_material_candidate_allowed_primary_class_counts"))
    candidate_count = sum(int(value or 0) for value in p8_material_counts.values())
    if data.get("p8_material_candidate_row_count") != candidate_count:
        raise ValueError("R54 EV19 P8 material candidate count mismatch")
    if tuple(data.get("p8_material_candidate_primary_class_refs") or ()) != tuple(p8_material_counts.keys()):
        raise ValueError("R54 EV19 P8 material primary refs must match count keys")
    if not set(p8_material_counts).issubset(set(P7_R54_EV12_P8_MATERIAL_CANDIDATE_PRIMARY_CLASS_REFS)):
        raise ValueError("R54 EV19 P8 material counts outside frozen primary class refs")
    if data.get("p8_question_design_material_candidate") is not bool(ready and candidate_count > 0):
        raise ValueError("R54 EV19 P8 candidate flag must match material row count")
    if ready:
        if data.get("p8_material_candidate_handoff_ref") != P7_R54_EV19_P8_MATERIAL_HANDOFF_REF:
            raise ValueError("R54 EV19 ready handoff ref changed")
        expected_reason_refs = [P7_R54_EV19_READY_REASON_REF] if candidate_count > 0 else [P7_R54_EV19_NO_MATERIAL_REASON_REF]
        if data.get("p8_material_candidate_handoff_reason_refs") != expected_reason_refs:
            raise ValueError("R54 EV19 ready/no-material reason refs changed")
        if data.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or data.get("question_need_observation_rows_aggregated_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("R54 EV19 ready must aggregate 24 question observation rows")
        if data.get("ev18_p6_limited_human_readfeel_candidate") is not True or data.get("p6_limited_human_readfeel_candidate") is not True:
            raise ValueError("R54 EV19 ready must retain P6 candidate basis")
        if data.get("ev18_p6_limited_human_readfeel_start_allowed") is not False or data.get("p6_limited_human_readfeel_start_allowed") is not False:
            raise ValueError("R54 EV19 must keep P6 start blocked")
        if data.get("disposal_verified") is not True:
            raise ValueError("R54 EV19 ready must preserve verified disposal receipt")
        for true_key in (
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R54 EV19 ready must keep {true_key}=True")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV19_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV19 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV19 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV20_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV19 ready must point to EV20")
        if data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV19 ready must not carry open execution blockers")
    else:
        if data.get("p8_material_candidate_handoff_status") != P7_R54_EV19_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF:
            raise ValueError("R54 EV19 blocked status changed")
        if data.get("p8_material_candidate_handoff_ref") != "p8_material_candidate_handoff_not_ready_bodyfree_20260626":
            raise ValueError("R54 EV19 blocked handoff ref changed")
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("R54 EV19 blocked must not set P8 material candidate")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV19 blocked must carry execution blockers")
        if data.get("next_required_step") != P7_R54_EV19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV19 blocked must point to repair")
    return True

# EV18/EV19 detailed-design wording aliases.
P7_R54_EV18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
P7_R54_EV19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION: Final = P7_R54_EV_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION
P7_R54_EV18_REQUIRED_FIELD_REFS: Final = P7_R54_EV18_P6_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS
P7_R54_EV19_REQUIRED_FIELD_REFS: Final = P7_R54_EV19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_REQUIRED_FIELD_REFS
build_p7_r54_ev18_p6_candidate_only_handoff_bodyfree = build_p7_r54_ev18_p6_candidate_only_handoff
assert_p7_r54_ev18_p6_candidate_only_handoff_bodyfree_contract = assert_p7_r54_ev18_p6_candidate_only_handoff_contract
build_p7_r54_ev19_p8_material_candidate_only_handoff_bodyfree = build_p7_r54_ev19_p8_material_candidate_only_handoff
assert_p7_r54_ev19_p8_material_candidate_only_handoff_bodyfree_contract = assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract

# EV14/EV15 detailed-design wording aliases.
P7_R54_EV14_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
P7_R54_EV15_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION
P7_R54_EV14_REQUIRED_FIELD_REFS: Final = P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS
P7_R54_EV15_REQUIRED_FIELD_REFS: Final = P7_R54_EV_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS
build_p7_r54_ev14_pause_abort_expiration_protocol_bodyfree = build_p7_r54_ev14_pause_abort_expiration_protocol
assert_p7_r54_ev14_pause_abort_expiration_protocol_bodyfree_contract = assert_p7_r54_ev14_pause_abort_expiration_protocol_contract
build_p7_r54_ev15_purge_disposal_receipt_bodyfree = build_p7_r54_ev15_purge_disposal_receipt
assert_p7_r54_ev15_purge_disposal_receipt_bodyfree_contract = assert_p7_r54_ev15_purge_disposal_receipt_contract
P7_R54_EV16_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION
P7_R54_EV17_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION
P7_R54_EV16_REQUIRED_FIELD_REFS: Final = P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS
P7_R54_EV17_REQUIRED_FIELD_REFS: Final = P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS
build_p7_r54_ev16_bodyfree_post_review_summary_bodyfree = build_p7_r54_ev16_bodyfree_post_review_summary
assert_p7_r54_ev16_bodyfree_post_review_summary_bodyfree_contract = assert_p7_r54_ev16_bodyfree_post_review_summary_contract
build_p7_r54_ev17_p5_decision_candidate_separation_bodyfree = build_p7_r54_ev17_p5_decision_candidate_separation
assert_p7_r54_ev17_p5_decision_candidate_separation_bodyfree_contract = assert_p7_r54_ev17_p5_decision_candidate_separation_contract

# Compatibility aliases for the EV00/EV01 detailed-design wording.
P7_R54_EV00_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION: Final = P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION
P7_R54_EV01_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION: Final = P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION
P7_R54_EV02_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION: Final = P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION
P7_R54_EV03_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION: Final = P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION
P7_R54_EV04_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION: Final = P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION
P7_R54_EV05_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION: Final = P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
P7_R54_EV06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION: Final = P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION
P7_R54_EV07_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION: Final = P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION
P7_R54_EV08_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION: Final = P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION
P7_R54_EV09_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION
P7_R54_EV09_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION: Final = P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION
P7_R54_EV10_RATING_ROW_SCHEMA_VERSION: Final = P7_R54_EV_RATING_ROW_SCHEMA_VERSION
P7_R54_EV10_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
P7_R54_EV11_READFEEL_BLOCKER_ROW_SCHEMA_VERSION: Final = P7_R54_EV_READFEEL_BLOCKER_ROW_SCHEMA_VERSION
P7_R54_EV11_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION: Final = P7_R54_EV_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION
P7_R54_EV11_BLOCKER_INGESTION_SCHEMA_VERSION: Final = P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION
P7_R54_EV12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
P7_R54_EV12_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION: Final = P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
P7_R54_EV13_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION
P7_R54_EV13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
P7_R54_EV_OPERATION_CURRENT_REFS_20260626: Final = P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS
P7_R54_EV00_REQUIRED_FIELD_REFS: Final = P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS
P7_R54_EV01_REQUIRED_FIELD_REFS: Final = P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_REQUIRED_FIELD_REFS
P7_R54_EV02_REQUIRED_FIELD_REFS: Final = P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_REQUIRED_FIELD_REFS
P7_R54_EV03_REQUIRED_FIELD_REFS: Final = P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_REQUIRED_FIELD_REFS
P7_R54_EV04_REQUIRED_FIELD_REFS: Final = P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_REQUIRED_FIELD_REFS
P7_R54_EV05_REQUIRED_FIELD_REFS: Final = P7_R54_EV_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS
P7_R54_EV06_REQUIRED_FIELD_REFS: Final = P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_REQUIRED_FIELD_REFS
P7_R54_EV07_REQUIRED_FIELD_REFS: Final = P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_REQUIRED_FIELD_REFS
P7_R54_EV08_REQUIRED_FIELD_REFS: Final = P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS
P7_R54_EV09_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS
P7_R54_EV09_REQUIRED_FIELD_REFS: Final = P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS
P7_R54_EV10_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_EV_RATING_ROW_REQUIRED_FIELD_REFS
P7_R54_EV10_REQUIRED_FIELD_REFS: Final = P7_R54_EV_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS
P7_R54_EV11_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_EV_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS
P7_R54_EV11_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_EV_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS
P7_R54_EV11_REQUIRED_FIELD_REFS: Final = P7_R54_EV_BLOCKER_INGESTION_REQUIRED_FIELD_REFS
P7_R54_EV12_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS
P7_R54_EV12_REQUIRED_FIELD_REFS: Final = P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS
P7_R54_EV13_ISSUE_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS
P7_R54_EV13_REQUIRED_FIELD_REFS: Final = P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS

__all__ = (
    "P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION",
    "P7_R54_EV00_SCOPE_NO_TOUCH_BOUNDARY_CONFIRMATION_SCHEMA_VERSION",
    "P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION",
    "P7_R54_EV01_EXISTING_HELPER_CAPABILITY_INSPECTION_SCHEMA_VERSION",
    "P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION",
    "P7_R54_EV02_OPERATION_CURRENT_REFS_REFREEZE_20260626_SCHEMA_VERSION",
    "P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION",
    "P7_R54_EV03_R55_HOLD_INTAKE_REFREEZE_SCHEMA_VERSION",
    "P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION",
    "P7_R54_EV04_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_SCHEMA_VERSION",
    "P7_R54_EV_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION",
    "P7_R54_EV05_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION",
    "P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION",
    "P7_R54_EV06_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_SCHEMA_VERSION",
    "P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION",
    "P7_R54_EV07_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_SCHEMA_VERSION",
    "P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION",
    "P7_R54_EV08_REVIEWER_SELECTION_FORM_FREEZE_SCHEMA_VERSION",
    "P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION",
    "P7_R54_EV09_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION",
    "P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION",
    "P7_R54_EV09_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION",
    "P7_R54_EV_RATING_ROW_SCHEMA_VERSION",
    "P7_R54_EV10_RATING_ROW_SCHEMA_VERSION",
    "P7_R54_EV_RATING_ROW_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_EV10_RATING_ROW_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_EV_READFEEL_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_EV11_READFEEL_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_EV_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_EV11_EXECUTION_BLOCKER_ROW_SCHEMA_VERSION",
    "P7_R54_EV_BLOCKER_INGESTION_SCHEMA_VERSION",
    "P7_R54_EV11_BLOCKER_INGESTION_SCHEMA_VERSION",
    "P7_R54_EV_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION",
    "P7_R54_EV12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION",
    "P7_R54_EV_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_EV12_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION",
    "P7_R54_EV_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION",
    "P7_R54_EV13_RATING_QUESTION_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION",
    "P7_R54_EV_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION",
    "P7_R54_EV13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION",
    "P7_R54_EV_STEP",
    "P7_R54_EV_SCOPE",
    "P7_R54_EV_POLICY_KIND",
    "P7_R54_EV_DEFAULT_REVIEW_SESSION_ID",
    "P7_R54_EV00_STEP_REF",
    "P7_R54_EV01_STEP_REF",
    "P7_R54_EV02_STEP_REF",
    "P7_R54_EV03_STEP_REF",
    "P7_R54_EV04_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV04_STEP_REF",
    "P7_R54_EV05_STEP_REF",
    "P7_R54_EV06_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV06_STEP_REF",
    "P7_R54_EV07_STEP_REF",
    "P7_R54_EV08_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV08_STEP_REF",
    "P7_R54_EV09_STEP_REF",
    "P7_R54_EV10_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV10_STEP_REF",
    "P7_R54_EV11_STEP_REF",
    "P7_R54_EV12_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV12_STEP_REF",
    "P7_R54_EV13_STEP_REF",
    "P7_R54_EV14_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV02_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV03_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV_ACTUAL_REVIEW_BASIS_REF",
    "P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF",
    "P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS",
    "P7_R54_EV_OPERATION_CURRENT_REFS_20260626",
    "P7_R54_EV00_IMPLEMENTED_STEPS",
    "P7_R54_EV00_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV01_IMPLEMENTED_STEPS",
    "P7_R54_EV01_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV02_IMPLEMENTED_STEPS",
    "P7_R54_EV02_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV03_IMPLEMENTED_STEPS",
    "P7_R54_EV03_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV04_IMPLEMENTED_STEPS",
    "P7_R54_EV04_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV05_IMPLEMENTED_STEPS",
    "P7_R54_EV05_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV06_IMPLEMENTED_STEPS",
    "P7_R54_EV06_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV07_IMPLEMENTED_STEPS",
    "P7_R54_EV07_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV08_IMPLEMENTED_STEPS",
    "P7_R54_EV08_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV09_IMPLEMENTED_STEPS",
    "P7_R54_EV09_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV10_IMPLEMENTED_STEPS",
    "P7_R54_EV10_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV11_IMPLEMENTED_STEPS",
    "P7_R54_EV11_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV12_IMPLEMENTED_STEPS",
    "P7_R54_EV12_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV13_IMPLEMENTED_STEPS",
    "P7_R54_EV13_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV_REQUIRED_HELPER_FUNCTION_REFS",
    "P7_R54_EV_SELECTION_ROW_INTAKE_HELPER_REFS",
    "P7_R54_EV01_CURRENT_REF_OVERRIDE_REJECTION_REF",
    "P7_R54_EV01_OVERRIDE_REJECTED_REASON_REF",
    "P7_R54_EV01_DOWNSTREAM_CONSTANT_REASON_REF",
    "P7_R54_EV01_DECISION_THIN_WRAPPER_REQUIRED_REF",
    "P7_R54_EV01_HELPER_CAPABILITY_STATUS_REF",
    "P7_R54_EV01_HELPER_REUSE_VERDICT_THIN_LAYER_REQUIRED_REF",
    "P7_R54_EV02_CURRENT_REFS_REFREEZE_STATUS_REF",
    "P7_R54_EV03_R55_HOLD_INTAKE_STATUS_REF",
    "P7_R54_EV04_PREFLIGHT_IMPLEMENTATION_STATUS_REF",
    "P7_R54_EV05_MANIFEST_REFREEZE_STATUS_REF",
    "P7_R54_EV04_PREFLIGHT_READY_STATUS_REF",
    "P7_R54_EV04_PREFLIGHT_BLOCKED_STATUS_REF",
    "P7_R54_EV04_ALLOWED_PREFLIGHT_STATUS_REFS",
    "P7_R54_EV04_LOCAL_REVIEW_ROOT_READY_REF",
    "P7_R54_EV04_EXPLICIT_ALLOW_TOKEN_REF",
    "P7_R54_EV04_PURGE_PLAN_READY_REF",
    "P7_R54_EV04_RETENTION_POLICY_READY_REF",
    "P7_R54_EV04_EXPORT_DENYLIST_POLICY_READY_REF",
    "P7_R54_EV04_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV05_MANIFEST_READY_STATUS_REF",
    "P7_R54_EV05_MANIFEST_BLOCKED_STATUS_REF",
    "P7_R54_EV05_ALLOWED_MANIFEST_STATUS_REFS",
    "P7_R54_EV05_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV05_REVIEWER_IDENTIFIER_POLICY_REF",
    "P7_R54_EV05_CASE_DISTRIBUTION",
    "P7_R54_EV06_REQUEST_READY_STATUS_REF",
    "P7_R54_EV06_REQUEST_BLOCKED_STATUS_REF",
    "P7_R54_EV06_PACKET_GENERATION_REQUEST_REF",
    "P7_R54_EV06_PACKET_GENERATION_REQUEST_POLICY_REF",
    "P7_R54_EV06_ALLOWED_OUTPUT_REF",
    "P7_R54_EV06_FORBIDDEN_OUTPUT_REFS",
    "P7_R54_EV06_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV07_INSTRUCTION_READY_STATUS_REF",
    "P7_R54_EV07_INSTRUCTION_BLOCKED_STATUS_REF",
    "P7_R54_EV07_INSTRUCTION_REF",
    "P7_R54_EV07_INSTRUCTION_POLICY_REF",
    "P7_R54_EV07_ALLOWED_LOCAL_OPERATION_SCOPE_REFS",
    "P7_R54_EV07_FORBIDDEN_LOCAL_OPERATION_REFS",
    "P7_R54_EV07_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV08_FORM_READY_STATUS_REF",
    "P7_R54_EV08_FORM_BLOCKED_STATUS_REF",
    "P7_R54_EV08_ALLOWED_FORM_STATUS_REFS",
    "P7_R54_EV08_REVIEWER_SELECTION_FORM_REF",
    "P7_R54_EV08_REVIEWER_SELECTION_FORM_POLICY_REF",
    "P7_R54_EV08_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV08_REQUIRED_SELECTION_FIELD_REFS",
    "P7_R54_EV08_PROHIBITED_SELECTION_FIELD_REFS",
    "P7_R54_EV08_RATING_AXIS_REFS",
    "P7_R54_EV08_SCORE_OPTION_REFS",
    "P7_R54_EV08_VERDICT_OPTION_REFS",
    "P7_R54_EV08_READFEEL_BLOCKER_ID_OPTION_REFS",
    "P7_R54_EV08_EXECUTION_BLOCKER_ID_OPTION_REFS",
    "P7_R54_EV08_QUESTION_NEED_PRIMARY_CLASS_REFS",
    "P7_R54_EV08_AMBIGUITY_KIND_OPTION_REFS",
    "P7_R54_EV08_ONE_QUESTION_FIT_OPTION_REFS",
    "P7_R54_EV08_REPAIR_REQUIRED_OPTION_REFS",
    "P7_R54_EV08_PLAN_CANDIDATE_FLAG_REFS",
    "P7_R54_EV09_INTAKE_READY_STATUS_REF",
    "P7_R54_EV09_INTAKE_BLOCKED_STATUS_REF",
    "P7_R54_EV09_ALLOWED_INTAKE_STATUS_REFS",
    "P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_REF",
    "P7_R54_EV09_SANITIZED_REVIEW_RESULT_INTAKE_POLICY_REF",
    "P7_R54_EV09_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF",
    "P7_R54_EV10_RATING_NORMALIZATION_BLOCKED_STATUS_REF",
    "P7_R54_EV10_ALLOWED_RATING_NORMALIZATION_STATUS_REFS",
    "P7_R54_EV10_RATING_ROW_NORMALIZATION_REF",
    "P7_R54_EV10_RATING_ROW_NORMALIZATION_POLICY_REF",
    "P7_R54_EV10_RATING_ROW_SOURCE_REF",
    "P7_R54_EV10_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF",
    "P7_R54_EV11_BLOCKER_INGESTION_BLOCKED_STATUS_REF",
    "P7_R54_EV11_ALLOWED_BLOCKER_INGESTION_STATUS_REFS",
    "P7_R54_EV11_BLOCKER_INGESTION_REF",
    "P7_R54_EV11_BLOCKER_INGESTION_POLICY_REF",
    "P7_R54_EV11_BLOCKED_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV_FALSE_FLAG_REFS",
    "P7_R54_EV_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS",
    "P7_R54_EV00_REQUIRED_FIELD_REFS",
    "P7_R54_EV_EXISTING_HELPER_CAPABILITY_INSPECTION_REQUIRED_FIELD_REFS",
    "P7_R54_EV01_REQUIRED_FIELD_REFS",
    "P7_R54_EV_OPERATION_CURRENT_REFS_REFREEZE_20260626_REQUIRED_FIELD_REFS",
    "P7_R54_EV02_REQUIRED_FIELD_REFS",
    "P7_R54_EV_R55_HOLD_INTAKE_REFREEZE_REQUIRED_FIELD_REFS",
    "P7_R54_EV03_REQUIRED_FIELD_REFS",
    "P7_R54_EV_LOCAL_ONLY_PREFLIGHT_IMPLEMENTATION_CONFIRMATION_REQUIRED_FIELD_REFS",
    "P7_R54_EV04_REQUIRED_FIELD_REFS",
    "P7_R54_EV_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS",
    "P7_R54_EV_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_REQUIRED_FIELD_REFS",
    "P7_R54_EV_LOCAL_OPERATION_BOUNDARY_INSTRUCTION_REQUIRED_FIELD_REFS",
    "P7_R54_EV05_REQUIRED_FIELD_REFS",
    "P7_R54_EV06_REQUIRED_FIELD_REFS",
    "P7_R54_EV07_REQUIRED_FIELD_REFS",
    "P7_R54_EV_REVIEWER_SELECTION_FORM_FREEZE_REQUIRED_FIELD_REFS",
    "P7_R54_EV08_REQUIRED_FIELD_REFS",
    "P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV09_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS",
    "P7_R54_EV09_REQUIRED_FIELD_REFS",
    "P7_R54_EV_RATING_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV10_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS",
    "P7_R54_EV10_REQUIRED_FIELD_REFS",
    "P7_R54_EV_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV11_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV11_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV_BLOCKER_INGESTION_REQUIRED_FIELD_REFS",
    "P7_R54_EV11_REQUIRED_FIELD_REFS",
    "P7_R54_EV12_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV12_REQUIRED_FIELD_REFS",
    "P7_R54_EV13_ISSUE_ROW_REQUIRED_FIELD_REFS",
    "P7_R54_EV13_REQUIRED_FIELD_REFS",
    "build_p7_r54_ev00_scope_no_touch_boundary_confirmation",
    "assert_p7_r54_ev00_scope_no_touch_boundary_confirmation_contract",
    "build_p7_r54_ev01_existing_helper_capability_inspection",
    "assert_p7_r54_ev01_existing_helper_capability_inspection_contract",
    "build_p7_r54_ev02_operation_current_refs_20260626_refreeze",
    "assert_p7_r54_ev02_operation_current_refs_20260626_refreeze_contract",
    "build_p7_r54_ev03_r55_hold_intake_refreeze",
    "assert_p7_r54_ev03_r55_hold_intake_refreeze_contract",
    "build_p7_r54_ev04_local_only_preflight_implementation_confirmation",
    "assert_p7_r54_ev04_local_only_preflight_implementation_confirmation_contract",
    "build_p7_r54_ev05_24_case_manifest_refreeze",
    "assert_p7_r54_ev05_24_case_manifest_refreeze_contract",
    "build_p7_r54_ev06_body_full_packet_generation_request_bodyfree",
    "assert_p7_r54_ev06_body_full_packet_generation_request_bodyfree_contract",
    "build_p7_r54_ev07_local_operation_boundary_instruction",
    "assert_p7_r54_ev07_local_operation_boundary_instruction_contract",
    "build_p7_r54_ev08_reviewer_selection_form_freeze",
    "assert_p7_r54_ev08_reviewer_selection_form_freeze_contract",
    "build_p7_r54_ev09_sanitized_review_result_row_intake",
    "assert_p7_r54_ev09_sanitized_review_result_row_intake_contract",
    "assert_p7_r54_ev10_rating_row_bodyfree_contract",
    "build_p7_r54_ev10_rating_row_normalization",
    "assert_p7_r54_ev10_rating_row_normalization_contract",
    "build_p7_r54_ev11_readfeel_blocker_row_bodyfree",
    "assert_p7_r54_ev11_readfeel_blocker_row_bodyfree_contract",
    "build_p7_r54_ev11_execution_blocker_row_bodyfree",
    "assert_p7_r54_ev11_execution_blocker_row_bodyfree_contract",
    "build_p7_r54_ev11_blocker_ingestion",
    "assert_p7_r54_ev11_blocker_ingestion_contract",
    "build_p7_r54_ev12_question_need_observation_row_normalization",
    "assert_p7_r54_ev12_question_need_observation_row_bodyfree_contract",
    "assert_p7_r54_ev12_question_need_observation_row_normalization_contract",
    "build_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree",
    "assert_p7_r54_ev13_rating_question_consistency_issue_row_bodyfree_contract",
    "build_p7_r54_ev13_rating_question_consistency_guard",
    "assert_p7_r54_ev13_rating_question_consistency_guard_contract",
)

__all__ = (
    *__all__,
    "P7_R54_EV_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION",
    "P7_R54_EV_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION",
    "P7_R54_EV14_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION",
    "P7_R54_EV15_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION",
    "P7_R54_EV14_STEP_REF",
    "P7_R54_EV15_STEP_REF",
    "P7_R54_EV16_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV14_PROTOCOL_READY_STATUS_REF",
    "P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF",
    "P7_R54_EV14_PROTOCOL_ABORTED_STATUS_REF",
    "P7_R54_EV14_PROTOCOL_EXPIRED_STATUS_REF",
    "P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF",
    "P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF",
    "P7_R54_EV14_REVIEW_OPERATION_STATUS_REFS",
    "P7_R54_EV14_REQUIRED_LOCAL_DELETE_TARGET_REFS",
    "P7_R54_EV14_PURGE_TRIGGER_REFS",
    "P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF",
    "P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF",
    "P7_R54_EV15_DISPOSAL_RECEIPT_REF",
    "P7_R54_EV15_REMOVAL_TARGET_REFS",
    "P7_R54_EV14_REQUIRED_FIELD_REFS",
    "P7_R54_EV15_REQUIRED_FIELD_REFS",
    "build_p7_r54_ev14_pause_abort_expiration_protocol",
    "assert_p7_r54_ev14_pause_abort_expiration_protocol_contract",
    "build_p7_r54_ev15_purge_disposal_receipt",
    "assert_p7_r54_ev15_purge_disposal_receipt_contract",
    "P7_R54_EV_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION",
    "P7_R54_EV_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION",
    "P7_R54_EV16_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION",
    "P7_R54_EV17_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION",
    "P7_R54_EV16_STEP_REF",
    "P7_R54_EV17_STEP_REF",
    "P7_R54_EV18_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV16_IMPLEMENTED_STEPS",
    "P7_R54_EV16_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV17_IMPLEMENTED_STEPS",
    "P7_R54_EV17_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION",
    "P7_R54_EV_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION",
    "P7_R54_EV18_P6_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION",
    "P7_R54_EV19_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION",
    "P7_R54_EV18_STEP_REF",
    "P7_R54_EV19_STEP_REF",
    "P7_R54_EV20_NEXT_REQUIRED_STEP_REF",
    "P7_R54_EV18_IMPLEMENTED_STEPS",
    "P7_R54_EV18_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV19_IMPLEMENTED_STEPS",
    "P7_R54_EV19_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV18_P6_CANDIDATE_HANDOFF_READY_STATUS_REF",
    "P7_R54_EV18_P6_CANDIDATE_HANDOFF_BLOCKED_STATUS_REF",
    "P7_R54_EV18_P6_CANDIDATE_HANDOFF_REF",
    "P7_R54_EV18_P6_CANDIDATE_REF",
    "P7_R54_EV18_CANDIDATE_ONLY_POLICY_REF",
    "P7_R54_EV19_P8_MATERIAL_HANDOFF_READY_STATUS_REF",
    "P7_R54_EV19_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF",
    "P7_R54_EV19_P8_MATERIAL_HANDOFF_REF",
    "P7_R54_EV19_P8_MATERIAL_CANDIDATE_REF",
    "P7_R54_EV19_CANDIDATE_ONLY_POLICY_REF",
    "P7_R54_EV18_REQUIRED_FIELD_REFS",
    "P7_R54_EV19_REQUIRED_FIELD_REFS",
    "build_p7_r54_ev18_p6_candidate_only_handoff",
    "assert_p7_r54_ev18_p6_candidate_only_handoff_contract",
    "build_p7_r54_ev19_p8_material_candidate_only_handoff",
    "assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract",
    "P7_R54_EV16_SUMMARY_READY_STATUS_REF",
    "P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF",
    "P7_R54_EV16_SUMMARY_REF",
    "P7_R54_EV17_DECISION_SEPARATION_READY_STATUS_REF",
    "P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF",
    "P7_R54_EV17_DECISION_SEPARATION_REF",
    "P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF",
    "P7_R54_EV17_P5_REPAIR_RETURN_REF",
    "P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF",
    "P7_R54_EV17_INCONCLUSIVE_REF",
    "P7_R54_EV17_DECISION_CANDIDATE_REFS",
    "P7_R54_EV16_REQUIRED_FIELD_REFS",
    "P7_R54_EV17_REQUIRED_FIELD_REFS",
    "build_p7_r54_ev16_bodyfree_post_review_summary",
    "assert_p7_r54_ev16_bodyfree_post_review_summary_contract",
    "build_p7_r54_ev17_p5_decision_candidate_separation",
    "assert_p7_r54_ev17_p5_decision_candidate_separation_contract",
)

# ---------------------------------------------------------------------------
# R54-EV-20 / R54-EV-21: final validation and R52 re-intake handoff.
# ---------------------------------------------------------------------------

P7_R54_EV_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev20_final_no_body_leak_no_question_text_no_touch_validation.bodyfree.v1"
)
P7_R54_EV_R52_REINTAKE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev21_r52_reintake_handoff.bodyfree.v1"
)

P7_R54_EV20_STEP_REF: Final = P7_R54_EV20_NEXT_REQUIRED_STEP_REF
P7_R54_EV21_STEP_REF: Final = "R54-EV-21_r52_reintake_handoff"
P7_R54_EV22_NEXT_REQUIRED_STEP_REF: Final = "R54-EV-22_validation_command_matrix_documentation_output"
P7_R54_EV20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV19_IMPLEMENTED_STEPS, P7_R54_EV20_STEP_REF)
P7_R54_EV20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV21_STEP_REF,)
P7_R54_EV21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV20_IMPLEMENTED_STEPS, P7_R54_EV21_STEP_REF)
P7_R54_EV21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_EV22_NEXT_REQUIRED_STEP_REF,)

P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF: Final = "FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_READY_BODYFREE_20260626"
P7_R54_EV20_FINAL_VALIDATION_BLOCKED_STATUS_REF: Final = "FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_BLOCKED_20260626"
P7_R54_EV20_BODY_LEAK_BLOCKED_STATUS_REF: Final = "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_EV20_NO_TOUCH_BLOCKED_STATUS_REF: Final = "R54_OPERATION_BLOCKED_NO_TOUCH_VIOLATION"
P7_R54_EV20_ALLOWED_FINAL_VALIDATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF,
    P7_R54_EV20_FINAL_VALIDATION_BLOCKED_STATUS_REF,
    P7_R54_EV20_BODY_LEAK_BLOCKED_STATUS_REF,
    P7_R54_EV20_NO_TOUCH_BLOCKED_STATUS_REF,
)
P7_R54_EV20_FINAL_VALIDATION_REF: Final = "R54_EV20_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_BODYFREE_20260626"
P7_R54_EV20_READY_DECISION_REF: Final = "R54_EV20_FINAL_BODYFREE_VALIDATION_READY"
P7_R54_EV20_BLOCKED_DECISION_REF: Final = "R54_EV20_FINAL_BODYFREE_VALIDATION_BLOCKED"
P7_R54_EV20_READY_REASON_REF: Final = "r54_ev20_final_validation_ready_bodyfree"
P7_R54_EV20_INPUT_BLOCKED_REASON_REF: Final = "r54_ev20_blocked_until_ev19_p8_material_candidate_handoff_ready"
P7_R54_EV20_BODY_LEAK_BLOCKED_REASON_REF: Final = "r54_ev20_body_leak_or_question_text_detected_bodyfree"
P7_R54_EV20_NO_TOUCH_BLOCKED_REASON_REF: Final = "r54_ev20_no_touch_contract_mutation_detected_bodyfree"
P7_R54_EV20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r54_ev20_final_validation_repair_before_r52_reintake_handoff"
P7_R54_EV20_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "body_leak_or_question_text_repair_before_r52_reintake_handoff"
P7_R54_EV20_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "no_touch_boundary_repair_before_r52_reintake_handoff"
P7_R54_EV20_NEXT_WORK_AFTER_EV20_REF: Final = "r54_ev21_r52_reintake_handoff_after_final_validation"

P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF: Final = "R54_R52_REINTAKE_HANDOFF_READY"
P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING"
P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_DISPOSAL"
P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT"
P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION"
P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF: Final = "R54_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE"
P7_R54_EV21_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF,
    P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF,
    P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF,
    P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF,
    P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF,
    P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF,
)
P7_R54_EV21_R52_REINTAKE_HANDOFF_REF: Final = "R54_EV21_R52_REINTAKE_HANDOFF_BODYFREE_20260626"
P7_R54_EV21_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF: Final = "R54_EV21_BODYFREE_ACTUAL_REVIEW_EVIDENCE_READY_FOR_R52_REINTAKE_20260626"
P7_R54_EV21_R52_REINTAKE_DECISION_REF: Final = "R52_REINTAKE_REQUIRED"
P7_R54_EV21_R52_REINTAKE_REQUIRED_REF: Final = "R52_REINTAKE_REQUIRED_AFTER_R54_ACTUAL_LOCAL_REVIEW_BODYFREE_20260626"
P7_R54_EV21_READY_REASON_REF: Final = "r54_ev21_r52_reintake_handoff_ready_bodyfree_actual_review_evidence"
P7_R54_EV21_EVIDENCE_MISSING_REASON_REF: Final = "r54_ev21_actual_review_evidence_missing_or_incomplete"
P7_R54_EV21_DISPOSAL_BLOCKED_REASON_REF: Final = "r54_ev21_disposal_not_verified"
P7_R54_EV21_BODY_LEAK_BLOCKED_REASON_REF: Final = "r54_ev21_blocked_by_body_leak_or_question_text_validation"
P7_R54_EV21_NO_TOUCH_BLOCKED_REASON_REF: Final = "r54_ev21_blocked_by_no_touch_validation"
P7_R54_EV21_INCONCLUSIVE_REASON_REF: Final = "r54_ev21_operation_inconclusive_before_r52_reintake"
P7_R54_EV21_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "r52_reintake_handoff_blocked_until_bodyfree_actual_review_evidence_ready"
P7_R54_EV21_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "disposal_receipt_repair_before_r52_reintake_handoff"
P7_R54_EV21_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = P7_R54_EV20_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF
P7_R54_EV21_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = P7_R54_EV20_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF
P7_R54_EV21_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "r54_operation_inconclusive_retry_or_r52_reintake_repair"
P7_R54_EV21_NEXT_WORK_AFTER_EV21_REF: Final = "r54_ev22_validation_command_matrix_documentation_output_after_r52_handoff"

P7_R54_EV20_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked", "ev19_schema_version", "ev19_material_ref", "ev19_next_required_step", "ev19_p8_material_candidate_handoff_status", "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis", "operation_current_refs_used_as_actual_review_basis", "existing_op22_helper_ref", "existing_op22_schema_version", "existing_op22_operation_current_refs", "existing_op22_current_refs_are_historical_here", "existing_op22_reused_as_actual_final_validation_basis", "existing_op22_structural_contract_reused",
    "required_case_count", "reviewed_case_count", "rating_row_count", "question_observation_row_count", "question_need_observation_rows_aggregated_count", "disposal_verified", "p5_decision_candidate_ref", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_question_design_material_candidate", "p8_material_candidate_row_count", "p8_start_allowed", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "release_allowed",
    "validation_evidence_ref", "final_validation_status", "final_validation_ref", "final_validation_decision_ref", "final_validation_reason_refs", "final_validation_issue_refs", "final_validation_issue_count", "final_validation_failure_class_ref", "body_leak_violation_refs", "body_leak_violation_count", "question_text_violation_refs", "question_text_violation_count", "no_touch_violation_refs", "no_touch_violation_count", "body_leak_or_question_text_violation_detected", "no_touch_violation_detected", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_touch_validation_passed", "final_validation_passed", "r52_reintake_handoff_allowed_next",
    "actual_review_evidence_complete", "human_review_completion_claim_blocked_here", "actual_human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_ev_no_touch_contract", "body_free_markers", "body_free", "raw_body_included", "question_text_included", "draft_question_text_included", "local_path_included", *P7_R54_EV_FALSE_FLAG_REFS,
)

P7_R54_EV21_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref", "current_phase",
    "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked", "ev20_schema_version", "ev20_material_ref", "ev20_next_required_step", "ev20_final_validation_status", "ev20_r52_reintake_handoff_allowed_next", "operation_current_refs", "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed", "operation_current_refs_are_actual_review_basis", "operation_current_refs_used_as_actual_review_basis", "existing_op23_helper_ref", "existing_op23_schema_version", "existing_op23_operation_current_refs", "existing_op23_current_refs_are_historical_here", "existing_op23_reused_as_actual_r52_handoff_basis", "existing_op23_structural_contract_reused",
    "required_case_count", "reviewed_case_count", "rating_row_count", "question_observation_row_count", "handoff_status", "handoff_ref", "handoff_reason_refs", "r52_reintake_decision_ref", "r52_reintake_handoff_ready", "r52_reintake_handoff_status", "r52_reintake_handoff_ref", "r52_reintake_handoff_reason_refs", "r52_reintake_required_ref", "actual_review_evidence_complete", "actual_review_evidence_complete_from_bodyfree_receipts", "r52_bodyfree_actual_review_evidence_complete", "r52_bodyfree_evidence_handoff_ready", "actual_human_review_run_here", "actual_manual_review_run_here", "rating_rows_bodyfree_handoff_count", "question_observation_rows_bodyfree_handoff_count", "disposal_verified", "no_body_leak_validation_passed", "no_question_text_validation_passed", "no_touch_validation_passed",
    "p5_decision_candidate", "p5_decision_candidate_ref", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final", "p6_candidate_only", "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed", "p8_material_candidate_only", "p8_question_design_material_candidate", "p8_material_candidate_row_count", "p8_design_material_candidate_only_not_start", "p8_start_allowed", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "question_text_materialized_here", "draft_question_text_materialized_here", "question_trigger_logic_implemented", "question_answer_persistence_implemented", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_plan_guard_implemented", "question_storage_schema_implemented", "question_text_included", "draft_question_text_included", "api_db_rn_response_key_changed_here", "runtime_changed_here", "release_allowed", "p7_complete",
    "body_free_evidence_handoff_materialized_here", "r52_reintake_required", "body_free_actual_review_evidence_ref", "body_free_result_handoff_ref", "handoff_evidence_refs", "handoff_evidence_ref_count", "r52_handoff_preserves_candidate_only_boundaries", "r52_handoff_contains_body_full_packet", "r52_handoff_contains_question_text", "r52_handoff_contains_local_path", "r52_handoff_contains_payload_hash", "r52_handoff_contains_reviewer_free_text", "r52_handoff_contains_raw_payload", "human_review_completion_claim_blocked_here", "actual_human_review_completion_claim_blocked_here", "p6_p8_release_promotion_blocked_here", "actual_rating_rows_materialized_here", "actual_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "execution_blocker_ids", "open_execution_blocker_ids", "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step", "public_contract", "r54_ev_no_touch_contract", "body_free_markers", "body_free", "raw_body_included", "local_path_included", *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev20_false_flag_refs() -> tuple[str, ...]:
    return tuple(key for key in P7_R54_EV_FALSE_FLAG_REFS if key not in {"actual_rating_rows_materialized_here", "actual_question_need_observation_rows_materialized_here", "actual_disposal_receipt_materialized_here", "disposal_verified", "p5_human_blind_qa_confirmed_candidate"})


def _ev21_false_flag_refs() -> tuple[str, ...]:
    return _ev20_false_flag_refs()


def _ev20_mapping_all_false(value: Mapping[str, Any] | None) -> bool:
    return all(child is False for child in safe_mapping(value).values())


def _ev20_probe_refs(validation_evidence: Mapping[str, Any] | None) -> tuple[list[str], list[str], list[str]]:
    data = safe_mapping(validation_evidence)
    body_refs = [key for key in ("body_full_packet_artifact_detected", "body_full_packet_content_detected", "reviewer_notes_artifact_detected", "raw_payload_artifact_detected", "local_path_artifact_detected", "body_hash_artifact_detected") if data.get(key) is True]
    question_refs = [key for key in ("question_text_artifact_detected", "draft_question_text_artifact_detected", "p8_question_text_artifact_detected") if data.get(key) is True]
    no_touch_refs = [key for key in ("api_changed_detected", "db_changed_detected", "rn_changed_detected", "runtime_changed_detected", "public_response_key_changed_detected", "question_trigger_logic_detected") if data.get(key) is True]
    return (dedupe_identifiers(body_refs, limit=80, max_length=180), dedupe_identifiers(question_refs, limit=80, max_length=180), dedupe_identifiers(no_touch_refs, limit=80, max_length=180))


def _ev20_prior_refs(ev19: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    prior: list[str] = []
    leak: list[str] = []
    no_touch: list[str] = []
    if ev19.get("p8_material_candidate_handoff_status") != P7_R54_EV19_P8_MATERIAL_HANDOFF_READY_STATUS_REF:
        prior.append(P7_R54_EV20_INPUT_BLOCKED_REASON_REF)
    if ev19.get("next_required_step") != P7_R54_EV20_STEP_REF:
        prior.append("ev19_next_required_step_not_ev20")
    prior.extend(ev19.get("open_execution_blocker_ids") or [])
    if ev19.get("body_free") is not True or ev19.get("raw_body_included") is not False or ev19.get("local_path_included") is not False:
        leak.append("ev19_bodyfree_boundary_not_clean")
    if ev19.get("question_text_included") is not False or ev19.get("draft_question_text_included") is not False or ev19.get("question_text_materialized_here") is True or ev19.get("draft_question_text_materialized_here") is True:
        leak.append("ev19_question_text_boundary_not_clean")
    if not _ev20_mapping_all_false(ev19.get("public_contract")) or not _ev20_mapping_all_false(ev19.get("r54_ev_no_touch_contract")):
        no_touch.append("ev19_no_touch_contract_marker_true")
    for key in ("api_changed", "db_changed", "rn_changed", "runtime_changed", "api_db_rn_response_key_changed_here", "runtime_changed_here", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_trigger_logic_implemented", "question_answer_persistence_implemented", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "p8_start_allowed", "p6_limited_human_readfeel_start_allowed", "release_allowed", "p7_complete"):
        if ev19.get(key) is True:
            no_touch.append(f"{key}_must_remain_false")
    return (dedupe_identifiers(prior, limit=100, max_length=180), dedupe_identifiers(leak, limit=100, max_length=180), dedupe_identifiers(no_touch, limit=100, max_length=180))


def _ev20_status_next_reason(prior_refs: Sequence[str], body_refs: Sequence[str], question_refs: Sequence[str], no_touch_refs: Sequence[str]) -> tuple[str, str, str, list[str]]:
    if body_refs or question_refs:
        return (P7_R54_EV20_BODY_LEAK_BLOCKED_STATUS_REF, P7_R54_EV20_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, "body_or_question_text", dedupe_identifiers([P7_R54_EV20_BODY_LEAK_BLOCKED_REASON_REF, *body_refs, *question_refs], limit=120, max_length=180))
    if no_touch_refs:
        return (P7_R54_EV20_NO_TOUCH_BLOCKED_STATUS_REF, P7_R54_EV20_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF, "no_touch", dedupe_identifiers([P7_R54_EV20_NO_TOUCH_BLOCKED_REASON_REF, *no_touch_refs], limit=120, max_length=180))
    if prior_refs:
        return (P7_R54_EV20_FINAL_VALIDATION_BLOCKED_STATUS_REF, P7_R54_EV20_BLOCKED_NEXT_REQUIRED_STEP_REF, "ev19_not_ready", dedupe_identifiers([P7_R54_EV20_INPUT_BLOCKED_REASON_REF, *prior_refs], limit=120, max_length=180))
    return (P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF, P7_R54_EV21_STEP_REF, "none", [P7_R54_EV20_READY_REASON_REF])


def build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation(*, p8_material_candidate_only_handoff: Mapping[str, Any] | None = None, validation_evidence: Mapping[str, Any] | None = None, validation_evidence_ref: Any = "r54_ev20_final_validation_bodyfree_evidence_ref", material_id: Any = "p7_r54_ev20_final_validation") -> dict[str, Any]:
    ev19 = safe_mapping(p8_material_candidate_only_handoff) if p8_material_candidate_only_handoff is not None else build_p7_r54_ev19_p8_material_candidate_only_handoff()
    assert_p7_r54_ev19_p8_material_candidate_only_handoff_contract(ev19)
    prior_refs, prior_leak_refs, prior_no_touch_refs = _ev20_prior_refs(ev19)
    probe_body_refs, probe_question_refs, probe_no_touch_refs = _ev20_probe_refs(validation_evidence)
    body_refs = dedupe_identifiers([*prior_leak_refs, *probe_body_refs], limit=100, max_length=180)
    question_refs = dedupe_identifiers(probe_question_refs, limit=100, max_length=180)
    no_touch_refs = dedupe_identifiers([*prior_no_touch_refs, *probe_no_touch_refs], limit=100, max_length=180)
    status, next_step, failure_class, reason_refs = _ev20_status_next_reason(prior_refs, body_refs, question_refs, no_touch_refs)
    ready = status == P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF
    issue_refs = dedupe_identifiers([*prior_refs, *body_refs, *question_refs, *no_touch_refs], limit=120, max_length=180)
    blockers = [] if ready else dedupe_identifiers([*reason_refs, *issue_refs], limit=120, max_length=180)
    material = {
        "schema_version": P7_R54_EV_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION,
        "phase": P7_PHASE, "step": P7_R54_EV_STEP, "scope": P7_R54_EV_SCOPE, "policy_kind": P7_R54_EV_POLICY_KIND, "policy_section": P7_R54_EV20_STEP_REF, "operation_step_ref": P7_R54_EV20_STEP_REF, "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev20_final_validation", max_length=220), "review_session_id": _safe_review_session_id(ev19.get("review_session_id")), "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "ev19_schema_version": P7_R54_EV_P8_MATERIAL_CANDIDATE_ONLY_HANDOFF_SCHEMA_VERSION, "ev19_material_ref": clean_identifier(ev19.get("material_id"), default="p7_r54_ev19_p8_material_candidate_only_handoff", max_length=220), "ev19_next_required_step": clean_identifier(ev19.get("next_required_step"), default="", max_length=180), "ev19_p8_material_candidate_handoff_status": clean_identifier(ev19.get("p8_material_candidate_handoff_status"), default=P7_R54_EV19_P8_MATERIAL_HANDOFF_BLOCKED_STATUS_REF, max_length=180),
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS), "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS), "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF, "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF, "operation_current_refs_are_actual_review_basis": True, "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op22_helper_ref": "build_p7_r54_op22_final_no_body_leak_no_question_text_no_touch_validation", "existing_op22_schema_version": r54op.P7_R54_OPERATION_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION, "existing_op22_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS), "existing_op22_current_refs_are_historical_here": True, "existing_op22_reused_as_actual_final_validation_basis": False, "existing_op22_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT, "reviewed_case_count": int(ev19.get("reviewed_case_count") or 0) if ready else 0, "rating_row_count": int(ev19.get("rating_row_count") or 0) if ready else 0, "question_observation_row_count": int(ev19.get("question_observation_row_count") or 0) if ready else 0, "question_need_observation_rows_aggregated_count": int(ev19.get("question_need_observation_rows_aggregated_count") or 0) if ready else 0,
        "disposal_verified": ev19.get("disposal_verified") is True and ready, "p5_decision_candidate_ref": P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF if ev19.get("p5_human_blind_qa_confirmed_candidate") is True and ready else P7_R54_EV17_INCONCLUSIVE_REF, "p5_human_blind_qa_confirmed_candidate": ev19.get("p5_human_blind_qa_confirmed_candidate") is True and ready, "p5_human_blind_qa_confirmed_final": False, "p6_limited_human_readfeel_candidate": ev19.get("p6_limited_human_readfeel_candidate") is True and ready, "p6_limited_human_readfeel_start_allowed": False, "p8_question_design_material_candidate": ev19.get("p8_question_design_material_candidate") is True and ready, "p8_material_candidate_row_count": int(ev19.get("p8_material_candidate_row_count") or 0) if ready else 0, "p8_start_allowed": False, "question_implementation_started_here": False, "p8_implementation_spec_finalized_here": False, "release_allowed": False,
        "validation_evidence_ref": clean_identifier(validation_evidence_ref, default="r54_ev20_final_validation_bodyfree_evidence_ref", max_length=220), "final_validation_status": status, "final_validation_ref": P7_R54_EV20_FINAL_VALIDATION_REF if ready else "ev20_final_validation_not_ready_bodyfree_20260626", "final_validation_decision_ref": P7_R54_EV20_READY_DECISION_REF if ready else P7_R54_EV20_BLOCKED_DECISION_REF, "final_validation_reason_refs": reason_refs, "final_validation_issue_refs": issue_refs, "final_validation_issue_count": len(issue_refs), "final_validation_failure_class_ref": failure_class,
        "body_leak_violation_refs": body_refs, "body_leak_violation_count": len(body_refs), "question_text_violation_refs": question_refs, "question_text_violation_count": len(question_refs), "no_touch_violation_refs": no_touch_refs, "no_touch_violation_count": len(no_touch_refs), "body_leak_or_question_text_violation_detected": bool(body_refs or question_refs), "no_touch_violation_detected": bool(no_touch_refs), "no_body_leak_validation_passed": ready, "no_question_text_validation_passed": ready, "no_touch_validation_passed": ready, "final_validation_passed": ready, "r52_reintake_handoff_allowed_next": ready,
        "actual_review_evidence_complete": False, "human_review_completion_claim_blocked_here": True, "actual_human_review_completion_claim_blocked_here": True, "p6_p8_release_promotion_blocked_here": True, "actual_rating_rows_materialized_here": ev19.get("actual_rating_rows_materialized_here") is True and ready, "actual_blocker_rows_materialized_here": ev19.get("actual_blocker_rows_materialized_here") is True and ready, "actual_question_need_observation_rows_materialized_here": ev19.get("actual_question_need_observation_rows_materialized_here") is True and ready, "actual_disposal_receipt_materialized_here": ev19.get("actual_disposal_receipt_materialized_here") is True and ready,
        "execution_blocker_ids": blockers, "open_execution_blocker_ids": blockers, "implemented_steps": list(P7_R54_EV20_IMPLEMENTED_STEPS if ready else tuple(ev19.get("implemented_steps") or P7_R54_EV19_IMPLEMENTED_STEPS)), "not_yet_implemented_steps": list(P7_R54_EV20_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ev19.get("not_yet_implemented_steps") or P7_R54_EV19_NOT_YET_IMPLEMENTED_STEPS)), "first_next_work_ref": P7_R54_EV20_NEXT_WORK_AFTER_EV20_REF if ready else P7_R54_EV19_NEXT_WORK_AFTER_EV19_REF, "next_required_step": next_step,
        "public_contract": public_contract_flags(), "r54_ev_no_touch_contract": _no_touch_contract(), "body_free_markers": _body_free_markers(), "body_free": True, "raw_body_included": False, "question_text_included": False, "draft_question_text_included": False, "local_path_included": False,
        **_false_flags(),
        "actual_rating_rows_materialized_here": ev19.get("actual_rating_rows_materialized_here") is True and ready, "actual_blocker_rows_materialized_here": ev19.get("actual_blocker_rows_materialized_here") is True and ready, "actual_question_need_observation_rows_materialized_here": ev19.get("actual_question_need_observation_rows_materialized_here") is True and ready, "actual_disposal_receipt_materialized_here": ev19.get("actual_disposal_receipt_materialized_here") is True and ready, "disposal_verified": ev19.get("disposal_verified") is True and ready, "p5_human_blind_qa_confirmed_candidate": ev19.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
    }
    assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract(material)
    return material


def assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV20_REQUIRED_FIELD_REFS, source="p7_r54_ev20_final_validation")
    _assert_common_bodyfree_no_touch(data, schema_version=P7_R54_EV_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION, policy_section=P7_R54_EV20_STEP_REF, operation_step_ref=P7_R54_EV20_STEP_REF, source="p7_r54_ev20_final_validation", false_flag_refs=_ev20_false_flag_refs())
    if safe_mapping(data.get("existing_op22_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS or data.get("existing_op22_current_refs_are_historical_here") is not True or data.get("existing_op22_reused_as_actual_final_validation_basis") is not False:
        raise ValueError("R54 EV20 must keep existing OP22 historical-only")
    if data.get("final_validation_status") not in P7_R54_EV20_ALLOWED_FINAL_VALIDATION_STATUS_REFS:
        raise ValueError("R54 EV20 final validation status outside allowed refs")
    ready = data.get("final_validation_status") == P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF
    if data.get("final_validation_passed") is not ready or data.get("r52_reintake_handoff_allowed_next") is not ready:
        raise ValueError("R54 EV20 readiness flags must match status")
    if data.get("actual_review_evidence_complete") is not False or data.get("p5_human_blind_qa_confirmed_final") is not False or data.get("p6_limited_human_readfeel_start_allowed") is not False or data.get("p8_start_allowed") is not False or data.get("release_allowed") is not False:
        raise ValueError("R54 EV20 must not promote P5/P6/P8/release")
    for false_key in ("question_implementation_started_here", "p8_implementation_spec_finalized_here", "question_text_included", "draft_question_text_included", "raw_body_included", "local_path_included"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV20 must keep {false_key}=False")
    if ready:
        if data.get("final_validation_ref") != P7_R54_EV20_FINAL_VALIDATION_REF or data.get("final_validation_reason_refs") != [P7_R54_EV20_READY_REASON_REF]:
            raise ValueError("R54 EV20 ready validation refs changed")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count", "question_need_observation_rows_aggregated_count"):
            if data.get(count_key) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"R54 EV20 ready must preserve 24 {count_key}")
        if data.get("disposal_verified") is not True or data.get("p5_human_blind_qa_confirmed_candidate") is not True or data.get("p6_limited_human_readfeel_candidate") is not True:
            raise ValueError("R54 EV20 ready must preserve candidate evidence")
        if data.get("open_execution_blocker_ids") or data.get("final_validation_issue_refs"):
            raise ValueError("R54 EV20 ready must not carry blockers or issues")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV20_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV20_NOT_YET_IMPLEMENTED_STEPS or data.get("next_required_step") != P7_R54_EV21_STEP_REF:
            raise ValueError("R54 EV20 ready step pointers changed")
    else:
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV20 blocked must carry blockers")
        if data.get("next_required_step") not in {P7_R54_EV20_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_EV20_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_EV20_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF}:
            raise ValueError("R54 EV20 blocked next step changed")
    return True


def _ev21_status_next_reason(ev20: Mapping[str, Any]) -> tuple[str, str, list[str]]:
    if ev20.get("final_validation_status") == P7_R54_EV20_BODY_LEAK_BLOCKED_STATUS_REF or ev20.get("body_leak_or_question_text_violation_detected") is True:
        return (P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF, P7_R54_EV21_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_EV21_BODY_LEAK_BLOCKED_REASON_REF])
    if ev20.get("final_validation_status") == P7_R54_EV20_NO_TOUCH_BLOCKED_STATUS_REF or ev20.get("no_touch_violation_detected") is True:
        return (P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF, P7_R54_EV21_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_EV21_NO_TOUCH_BLOCKED_REASON_REF])
    if ev20.get("final_validation_status") != P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF or ev20.get("r52_reintake_handoff_allowed_next") is not True:
        return (P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF, P7_R54_EV21_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_EV21_EVIDENCE_MISSING_REASON_REF])
    if ev20.get("disposal_verified") is not True:
        return (P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF, P7_R54_EV21_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_EV21_DISPOSAL_BLOCKED_REASON_REF])
    if ev20.get("reviewed_case_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or ev20.get("rating_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT or ev20.get("question_observation_row_count") != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        return (P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF, P7_R54_EV21_BLOCKED_NEXT_REQUIRED_STEP_REF, [P7_R54_EV21_EVIDENCE_MISSING_REASON_REF])
    if ev20.get("p5_human_blind_qa_confirmed_candidate") is not True:
        return (P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF, P7_R54_EV21_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF, [P7_R54_EV21_INCONCLUSIVE_REASON_REF])
    return (P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF, P7_R54_EV22_NEXT_REQUIRED_STEP_REF, [P7_R54_EV21_READY_REASON_REF])


def build_p7_r54_ev21_r52_reintake_handoff(*, final_validation: Mapping[str, Any] | None = None, material_id: Any = "p7_r54_ev21_r52_reintake_handoff") -> dict[str, Any]:
    ev20 = safe_mapping(final_validation) if final_validation is not None else build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation()
    assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract(ev20)
    status, next_step, reason_refs = _ev21_status_next_reason(ev20)
    ready = status == P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    blockers = [] if ready else dedupe_identifiers([*reason_refs, *(ev20.get("open_execution_blocker_ids") or [])], limit=120, max_length=180)
    p5_candidate_ref = clean_identifier(ev20.get("p5_decision_candidate_ref"), default=P7_R54_EV17_INCONCLUSIVE_REF, max_length=180)
    handoff_refs = ("ev10_rating_rows_bodyfree", "ev11_blocker_rows_bodyfree", "ev12_question_observation_rows_bodyfree", "ev15_disposal_receipt_bodyfree", "ev16_post_review_summary_bodyfree", "ev17_p5_decision_candidate_bodyfree", "ev18_p6_candidate_only_handoff_bodyfree", "ev19_p8_material_candidate_only_handoff_bodyfree", "ev20_final_validation_bodyfree")
    material = {
        "schema_version": P7_R54_EV_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, "phase": P7_PHASE, "step": P7_R54_EV_STEP, "scope": P7_R54_EV_SCOPE, "policy_kind": P7_R54_EV_POLICY_KIND, "policy_section": P7_R54_EV21_STEP_REF, "operation_step_ref": P7_R54_EV21_STEP_REF, "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev21_r52_reintake_handoff", max_length=220), "review_session_id": _safe_review_session_id(ev20.get("review_session_id")), "source_mode": P7_SOURCE_MODE, "git_connection_required": False, "git_checked": False,
        "ev20_schema_version": P7_R54_EV_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION, "ev20_material_ref": clean_identifier(ev20.get("material_id"), default="p7_r54_ev20_final_validation", max_length=220), "ev20_next_required_step": clean_identifier(ev20.get("next_required_step"), default="", max_length=180), "ev20_final_validation_status": clean_identifier(ev20.get("final_validation_status"), default=P7_R54_EV20_FINAL_VALIDATION_BLOCKED_STATUS_REF, max_length=180), "ev20_r52_reintake_handoff_allowed_next": ev20.get("r52_reintake_handoff_allowed_next") is True,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS), "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS), "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF, "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF, "operation_current_refs_are_actual_review_basis": True, "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op23_helper_ref": "build_p7_r54_op23_r52_reintake_handoff", "existing_op23_schema_version": r54op.P7_R54_OPERATION_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, "existing_op23_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS), "existing_op23_current_refs_are_historical_here": True, "existing_op23_reused_as_actual_r52_handoff_basis": False, "existing_op23_structural_contract_reused": True,
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT, "reviewed_case_count": int(ev20.get("reviewed_case_count") or 0) if ready else 0, "rating_row_count": int(ev20.get("rating_row_count") or 0) if ready else 0, "question_observation_row_count": int(ev20.get("question_observation_row_count") or 0) if ready else 0,
        "handoff_status": status, "handoff_ref": P7_R54_EV21_R52_REINTAKE_HANDOFF_REF if ready else "r52_reintake_handoff_not_ready_bodyfree_20260626", "handoff_reason_refs": reason_refs if ready else blockers, "r52_reintake_decision_ref": P7_R54_EV21_R52_REINTAKE_DECISION_REF if ready else "R52_REINTAKE_HELD", "r52_reintake_handoff_ready": ready, "r52_reintake_handoff_status": status, "r52_reintake_handoff_ref": P7_R54_EV21_R52_REINTAKE_HANDOFF_REF if ready else "r52_reintake_handoff_not_ready_bodyfree_20260626", "r52_reintake_handoff_reason_refs": reason_refs if ready else blockers, "r52_reintake_required_ref": P7_R54_EV21_R52_REINTAKE_REQUIRED_REF if ready else "R52_REINTAKE_HELD",
        "actual_review_evidence_complete": ready, "actual_review_evidence_complete_from_bodyfree_receipts": ready, "r52_bodyfree_actual_review_evidence_complete": ready, "r52_bodyfree_evidence_handoff_ready": ready, "actual_human_review_run_here": False, "actual_manual_review_run_here": False, "rating_rows_bodyfree_handoff_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT if ready else 0, "question_observation_rows_bodyfree_handoff_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT if ready else 0, "disposal_verified": ev20.get("disposal_verified") is True and ready, "no_body_leak_validation_passed": ev20.get("no_body_leak_validation_passed") is True and ready, "no_question_text_validation_passed": ev20.get("no_question_text_validation_passed") is True and ready, "no_touch_validation_passed": ev20.get("no_touch_validation_passed") is True and ready,
        "p5_decision_candidate": p5_candidate_ref if ready else P7_R54_EV17_INCONCLUSIVE_REF, "p5_decision_candidate_ref": p5_candidate_ref if ready else P7_R54_EV17_INCONCLUSIVE_REF, "p5_human_blind_qa_confirmed_candidate": ev20.get("p5_human_blind_qa_confirmed_candidate") is True and ready, "p5_human_blind_qa_confirmed_final": False, "p6_candidate_only": ev20.get("p6_limited_human_readfeel_candidate") is True and ready, "p6_limited_human_readfeel_candidate": ev20.get("p6_limited_human_readfeel_candidate") is True and ready, "p6_limited_human_readfeel_start_allowed": False, "p8_material_candidate_only": ev20.get("p8_question_design_material_candidate") is True and ready, "p8_question_design_material_candidate": ev20.get("p8_question_design_material_candidate") is True and ready, "p8_material_candidate_row_count": int(ev20.get("p8_material_candidate_row_count") or 0) if ready else 0, "p8_design_material_candidate_only_not_start": True, "p8_start_allowed": False,
        "question_implementation_started_here": False, "p8_implementation_spec_finalized_here": False, "question_text_materialized_here": False, "draft_question_text_materialized_here": False, "question_trigger_logic_implemented": False, "question_answer_persistence_implemented": False, "question_api_implemented": False, "question_db_schema_implemented": False, "question_rn_ui_implemented": False, "question_response_key_implemented": False, "question_plan_guard_implemented": False, "question_storage_schema_implemented": False, "question_text_included": False, "draft_question_text_included": False, "api_db_rn_response_key_changed_here": False, "runtime_changed_here": False, "release_allowed": False, "p7_complete": False,
        "body_free_evidence_handoff_materialized_here": ready, "r52_reintake_required": ready, "body_free_actual_review_evidence_ref": P7_R54_EV21_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF if ready else "bodyfree_actual_review_evidence_not_ready_20260626", "body_free_result_handoff_ref": P7_R54_EV21_R52_REINTAKE_HANDOFF_REF if ready else "bodyfree_result_handoff_not_ready_20260626", "handoff_evidence_refs": list(handoff_refs) if ready else [], "handoff_evidence_ref_count": len(handoff_refs) if ready else 0, "r52_handoff_preserves_candidate_only_boundaries": True, "r52_handoff_contains_body_full_packet": False, "r52_handoff_contains_question_text": False, "r52_handoff_contains_local_path": False, "r52_handoff_contains_payload_hash": False, "r52_handoff_contains_reviewer_free_text": False, "r52_handoff_contains_raw_payload": False,
        "human_review_completion_claim_blocked_here": True, "actual_human_review_completion_claim_blocked_here": True, "p6_p8_release_promotion_blocked_here": True, "actual_rating_rows_materialized_here": ev20.get("actual_rating_rows_materialized_here") is True and ready, "actual_blocker_rows_materialized_here": ev20.get("actual_blocker_rows_materialized_here") is True and ready, "actual_question_need_observation_rows_materialized_here": ev20.get("actual_question_need_observation_rows_materialized_here") is True and ready, "actual_disposal_receipt_materialized_here": ev20.get("actual_disposal_receipt_materialized_here") is True and ready,
        "execution_blocker_ids": blockers, "open_execution_blocker_ids": blockers, "implemented_steps": list(P7_R54_EV21_IMPLEMENTED_STEPS if ready else tuple(ev20.get("implemented_steps") or P7_R54_EV20_IMPLEMENTED_STEPS)), "not_yet_implemented_steps": list(P7_R54_EV21_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ev20.get("not_yet_implemented_steps") or P7_R54_EV20_NOT_YET_IMPLEMENTED_STEPS)), "first_next_work_ref": P7_R54_EV21_NEXT_WORK_AFTER_EV21_REF if ready else P7_R54_EV20_NEXT_WORK_AFTER_EV20_REF, "next_required_step": next_step,
        "public_contract": public_contract_flags(), "r54_ev_no_touch_contract": _no_touch_contract(), "body_free_markers": _body_free_markers(), "body_free": True, "raw_body_included": False, "local_path_included": False,
        **_false_flags(), "actual_rating_rows_materialized_here": ev20.get("actual_rating_rows_materialized_here") is True and ready, "actual_blocker_rows_materialized_here": ev20.get("actual_blocker_rows_materialized_here") is True and ready, "actual_question_need_observation_rows_materialized_here": ev20.get("actual_question_need_observation_rows_materialized_here") is True and ready, "actual_disposal_receipt_materialized_here": ev20.get("actual_disposal_receipt_materialized_here") is True and ready, "disposal_verified": ev20.get("disposal_verified") is True and ready, "p5_human_blind_qa_confirmed_candidate": ev20.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
    }
    assert_p7_r54_ev21_r52_reintake_handoff_contract(material)
    return material


def assert_p7_r54_ev21_r52_reintake_handoff_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R54_EV21_REQUIRED_FIELD_REFS, source="p7_r54_ev21_r52_reintake_handoff")
    _assert_common_bodyfree_no_touch(data, schema_version=P7_R54_EV_R52_REINTAKE_HANDOFF_SCHEMA_VERSION, policy_section=P7_R54_EV21_STEP_REF, operation_step_ref=P7_R54_EV21_STEP_REF, source="p7_r54_ev21_r52_reintake_handoff", false_flag_refs=_ev21_false_flag_refs())
    if safe_mapping(data.get("existing_op23_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS or data.get("existing_op23_current_refs_are_historical_here") is not True or data.get("existing_op23_reused_as_actual_r52_handoff_basis") is not False:
        raise ValueError("R54 EV21 must keep existing OP23 historical-only")
    if data.get("handoff_status") != data.get("r52_reintake_handoff_status") or data.get("handoff_status") not in P7_R54_EV21_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS:
        raise ValueError("R54 EV21 status aliases changed")
    ready = data.get("handoff_status") == P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF
    if data.get("actual_review_evidence_complete") is not ready or data.get("r52_reintake_handoff_ready") is not ready:
        raise ValueError("R54 EV21 readiness flags must match status")
    for false_key in ("actual_human_review_run_here", "actual_manual_review_run_here", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed", "p8_start_allowed", "release_allowed", "p7_complete", "question_implementation_started_here", "p8_implementation_spec_finalized_here", "question_trigger_logic_implemented", "question_answer_persistence_implemented", "question_api_implemented", "question_db_schema_implemented", "question_rn_ui_implemented", "question_response_key_implemented", "question_plan_guard_implemented", "question_storage_schema_implemented", "question_text_materialized_here", "draft_question_text_materialized_here", "question_text_included", "draft_question_text_included", "raw_body_included", "local_path_included", "r52_handoff_contains_body_full_packet", "r52_handoff_contains_question_text", "r52_handoff_contains_local_path", "r52_handoff_contains_payload_hash", "r52_handoff_contains_reviewer_free_text", "r52_handoff_contains_raw_payload"):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV21 must keep {false_key}=False")
    if ready:
        if data.get("handoff_ref") != P7_R54_EV21_R52_REINTAKE_HANDOFF_REF or data.get("r52_reintake_handoff_ref") != P7_R54_EV21_R52_REINTAKE_HANDOFF_REF or data.get("handoff_reason_refs") != [P7_R54_EV21_READY_REASON_REF]:
            raise ValueError("R54 EV21 ready handoff refs changed")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count", "rating_rows_bodyfree_handoff_count", "question_observation_rows_bodyfree_handoff_count"):
            if data.get(count_key) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"R54 EV21 ready must preserve 24 {count_key}")
        if data.get("p5_decision_candidate") != P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF or data.get("p5_human_blind_qa_confirmed_candidate") is not True or data.get("body_free_evidence_handoff_materialized_here") is not True or data.get("r52_reintake_required") is not True:
            raise ValueError("R54 EV21 ready must materialize body-free R52 evidence")
        if data.get("open_execution_blocker_ids") or data.get("handoff_evidence_ref_count") != len(data.get("handoff_evidence_refs") or ()): 
            raise ValueError("R54 EV21 ready evidence refs or blockers changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV21_IMPLEMENTED_STEPS or tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV21_NOT_YET_IMPLEMENTED_STEPS or data.get("next_required_step") != P7_R54_EV22_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV21 ready step pointers changed")
    else:
        if data.get("body_free_evidence_handoff_materialized_here") is not False or data.get("r52_reintake_required") is not False or not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV21 blocked must not materialize evidence and must carry blockers")
        if data.get("next_required_step") not in {P7_R54_EV21_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_EV21_DISPOSAL_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_EV21_BODY_LEAK_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_EV21_NO_TOUCH_BLOCKED_NEXT_REQUIRED_STEP_REF, P7_R54_EV21_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF}:
            raise ValueError("R54 EV21 blocked next step changed")
    return True




# ---------------------------------------------------------------------------
# R54-EV-22: validation command matrix / documentation output.
# ---------------------------------------------------------------------------

P7_R54_EV_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev22_validation_command_matrix_row.bodyfree.v1"
)
P7_R54_EV_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.actual_review_execution.ev22_validation_command_matrix_documentation_output.bodyfree.v1"
)

P7_R54_EV22_STEP_REF: Final = P7_R54_EV22_NEXT_REQUIRED_STEP_REF
P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "r54_ev22_validation_command_matrix_documentation_output_repair_before_r52_reintake_consumption"
)
P7_R54_EV22_NEXT_WORK_AFTER_EV22_REF: Final = (
    "r52_reintake_consumes_r54_bodyfree_evidence_after_ev22_validation_documentation_output"
)
P7_R54_EV22_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (*P7_R54_EV21_IMPLEMENTED_STEPS, P7_R54_EV22_STEP_REF)
P7_R54_EV22_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = tuple()

P7_R54_EV22_DOCUMENTATION_OUTPUT_READY_STATUS_REF: Final = "EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_READY_BODYFREE_20260626"
P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF: Final = "EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_20260626"
P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_EV21_STATUS_REF: Final = (
    "EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_R52_REINTAKE_HANDOFF_20260626"
)
P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF: Final = (
    "EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_20260626"
)
P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF: Final = (
    "EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED_BY_GREEN_CLAIM_OVERREACH_20260626"
)
P7_R54_EV22_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV22_DOCUMENTATION_OUTPUT_READY_STATUS_REF,
    P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF,
    P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_EV21_STATUS_REF,
    P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
    P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF,
)
P7_R54_EV22_DOCUMENTATION_OUTPUT_REF: Final = "R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BODYFREE_20260626"
P7_R54_EV22_DOCUMENTATION_OUTPUT_FILE_REF: Final = "R54_EV22_Result_20260626.md"
P7_R54_EV22_READY_REASON_REF: Final = "r54_ev22_validation_command_matrix_documentation_output_ready_bodyfree"
P7_R54_EV22_BLOCKED_BY_EV21_REASON_REF: Final = "r54_ev22_blocked_until_r52_reintake_handoff_ready"
P7_R54_EV22_COMMAND_MATRIX_MISSING_REASON_REF: Final = "r54_ev22_validation_command_matrix_rows_missing"
P7_R54_EV22_COMMAND_MATRIX_FAILED_REASON_REF: Final = "r54_ev22_validation_command_matrix_has_failed_result_refs"
P7_R54_EV22_COMMAND_MATRIX_NOT_EXECUTED_ONLY_REASON_REF: Final = "r54_ev22_validation_command_matrix_has_no_executed_rows"
P7_R54_EV22_GREEN_CLAIM_OVERREACH_REASON_REF: Final = "r54_ev22_green_claim_scope_overreach_detected_bodyfree"
P7_R54_EV22_CLAIM_BOUNDARY_POLICY_REF: Final = "ev22_bodyfree_validation_claim_scope_boundary_20260626"

P7_R54_EV22_COMMAND_RESULT_PASSED_REF: Final = "PASSED"
P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF: Final = "COLLECTED_ONLY_NOT_FULL_SUITE_GREEN"
P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF: Final = "NOT_EXECUTED"
P7_R54_EV22_COMMAND_RESULT_FAILED_REF: Final = "FAILED"
P7_R54_EV22_ALLOWED_COMMAND_RESULT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_EV22_COMMAND_RESULT_PASSED_REF,
    P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF,
    P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF,
    P7_R54_EV22_COMMAND_RESULT_FAILED_REF,
)
P7_R54_EV22_CLAIM_BOUNDARY_GUARD_REFS: Final[tuple[str, ...]] = (
    "collect_only_not_full_suite_green",
    "rn_contract_not_real_device_modal_verification",
    "r54_helper_green_not_actual_human_review_complete",
    "selected_regression_not_full_backend_suite_green",
    "compileall_not_runtime_product_readfeel",
    "r52_reintake_handoff_not_p5_final_confirmation",
    "validation_matrix_not_release_permission",
)
P7_R54_EV22_DEFAULT_NOT_EXECUTED_VALIDATION_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite_not_executed_in_ev22",
    "rn_contract_not_executed_in_ev22",
    "real_device_modal_not_executed_in_ev22",
    "actual_human_review_operation_not_executed_in_ev22",
    "local_file_deletion_not_executed_by_ev22_helper",
)
P7_R54_EV22_BLOCKED_GREEN_CLAIM_TOKEN_REFS: Final[tuple[str, ...]] = (
    "backend_full_suite_green",
    "full_backend_suite_green",
    "real_device_modal_verified",
    "actual_human_review_complete",
    "release_allowed",
    "p8_start_allowed",
    "p6_start_allowed",
    "p5_final_confirmed",
    "p7_complete",
)

P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "validation_command_row_ref", "review_session_id", "command_ref", "command_group_ref",
    "command_kind_ref", "result_status_ref", "result_scope_ref", "passed_count", "collected_count",
    "warning_count", "failure_count", "green_claim_allowed", "collection_only_claim_allowed",
    "full_suite_claim_allowed", "real_device_claim_allowed", "actual_human_review_claim_allowed",
    "p5_final_claim_allowed", "p6_start_claim_allowed", "p8_start_claim_allowed", "release_claim_allowed",
    "result_summary_ref", "command_result_body_stored_here", "terminal_output_stored_here",
    "command_string_included", "body_free", "raw_body_included", "question_text_included",
    "draft_question_text_included", "local_path_included",
)
P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version", "phase", "step", "scope", "policy_kind", "policy_section", "operation_step_ref",
    "current_phase", "material_id", "review_session_id", "source_mode", "git_connection_required", "git_checked",
    "ev21_schema_version", "ev21_material_ref", "ev21_next_required_step", "ev21_handoff_status",
    "ev21_r52_reintake_handoff_ready", "ev21_actual_review_evidence_complete", "operation_current_refs",
    "operation_current_ref_count", "actual_review_basis_ref", "actual_review_basis_allowed",
    "operation_current_refs_are_actual_review_basis", "operation_current_refs_used_as_actual_review_basis",
    "existing_op24_helper_ref", "existing_op24_schema_version", "existing_op24_operation_current_refs",
    "existing_op24_current_refs_are_historical_here", "existing_op24_reused_as_actual_validation_documentation_basis",
    "existing_op24_reused_as_actual_documentation_output_basis", "existing_op24_structural_contract_reused", "required_case_count", "reviewed_case_count", "rating_row_count",
    "question_observation_row_count", "disposal_verified", "actual_review_evidence_complete",
    "body_free_evidence_handoff_materialized_here", "r52_reintake_handoff_ready", "r52_reintake_required",
    "p5_decision_candidate", "p5_human_blind_qa_confirmed_candidate", "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_candidate", "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate", "p8_material_candidate_row_count", "p8_start_allowed",
    "question_implementation_started_here", "p8_implementation_spec_finalized_here",
    "p8_question_implementation_spec_finalized_here", "release_allowed", "p7_complete",
    "documentation_output_status", "documentation_output_ref", "documentation_output_file_ref",
    "documentation_output_file_bodyfree", "documentation_output_file_contains_terminal_output_body",
    "documentation_output_reason_refs",
    "documentation_output_issue_refs", "documentation_output_issue_count", "documentation_output_materialized_here",
    "validation_command_row_schema_version", "validation_command_row_required_field_refs", "validation_command_rows",
    "validation_command_row_count", "executed_validation_command_refs", "executed_validation_command_count",
    "passed_validation_command_count", "collected_only_validation_command_count", "failed_validation_command_count",
    "not_executed_validation_command_count", "not_executed_validation_refs", "not_executed_validation_ref_count",
    "green_claim_scope_refs", "green_claim_scope_count", "collection_only_scope_refs", "collection_only_scope_count",
    "blocked_green_claim_refs", "blocked_green_claim_count", "claim_boundary_guard_refs", "claim_boundary_guard_count",
    "claim_boundary_policy_ref", "collect_only_claimed_as_full_suite_green",
    "rn_contract_claimed_as_real_device_modal_verified", "r54_helper_green_claimed_as_actual_human_review_complete",
    "full_backend_suite_green_claimed", "real_device_modal_verified_claimed",
    "actual_human_review_complete_claimed_by_helper", "p5_final_confirmation_claimed_from_validation_matrix",
    "release_claimed_from_validation_matrix",
    "command_result_body_stored_here", "terminal_output_stored_here", "command_string_included",
    "human_review_completion_claim_blocked_here", "actual_human_review_completion_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here", "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here", "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here", "execution_blocker_ids", "open_execution_blocker_ids",
    "implemented_steps", "not_yet_implemented_steps", "first_next_work_ref", "next_required_step",
    "public_contract", "r54_ev_no_touch_contract", "body_free_markers", "body_free", "raw_body_included",
    "question_text_included", "draft_question_text_included", "local_path_included", *P7_R54_EV_FALSE_FLAG_REFS,
)


def _ev22_false_flag_refs() -> tuple[str, ...]:
    return tuple(
        key for key in P7_R54_EV_FALSE_FLAG_REFS
        if key not in {
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "disposal_verified",
            "p5_human_blind_qa_confirmed_candidate",
        }
    )


def _ev22_contains_blocked_claim_ref(value: str) -> bool:
    lowered = value.lower()
    for token in P7_R54_EV22_BLOCKED_GREEN_CLAIM_TOKEN_REFS:
        if f"not_{token}" in lowered or f"not-{token}" in lowered:
            continue
        if token in lowered:
            return True
    return False


def build_p7_r54_ev22_validation_command_matrix_row(
    *,
    command_ref: Any,
    command_group_ref: Any = "r54_ev22_validation",
    command_kind_ref: Any = "pytest_target",
    result_status_ref: Any = P7_R54_EV22_COMMAND_RESULT_PASSED_REF,
    result_scope_ref: Any = "selected_target_only",
    passed_count: Any = 0,
    collected_count: Any = 0,
    warning_count: Any = 0,
    failure_count: Any = 0,
    result_summary_ref: Any = "bodyfree_result_summary_ref",
    review_session_id: Any = None,
) -> dict[str, Any]:
    status = clean_identifier(result_status_ref, default=P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF, max_length=120)
    invalid_status = status not in P7_R54_EV22_ALLOWED_COMMAND_RESULT_STATUS_REFS
    if invalid_status:
        status = P7_R54_EV22_COMMAND_RESULT_FAILED_REF
    scope_ref = clean_identifier(result_scope_ref, default="selected_target_only", max_length=180)
    command_id = clean_identifier(command_ref, default="validation_command_ref_missing", max_length=220)
    row_ref = f"r54_ev22_validation_command_row__{command_id}"[:260]
    passed = max(0, int(passed_count or 0))
    collected = max(0, int(collected_count or 0))
    warnings = max(0, int(warning_count or 0))
    failures = max(0, int(failure_count or 0))
    if invalid_status and failures == 0:
        failures = 1
    green_claim_allowed = (
        status == P7_R54_EV22_COMMAND_RESULT_PASSED_REF
        and not _ev22_contains_blocked_claim_ref(scope_ref)
    )
    row = {
        "schema_version": P7_R54_EV_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION,
        "validation_command_row_ref": row_ref,
        "review_session_id": _safe_review_session_id(review_session_id),
        "command_ref": command_id,
        "command_group_ref": clean_identifier(command_group_ref, default="r54_ev22_validation", max_length=180),
        "command_kind_ref": clean_identifier(command_kind_ref, default="pytest_target", max_length=160),
        "result_status_ref": status,
        "result_scope_ref": scope_ref,
        "passed_count": passed,
        "collected_count": collected,
        "warning_count": warnings,
        "failure_count": failures if status == P7_R54_EV22_COMMAND_RESULT_FAILED_REF else 0,
        "green_claim_allowed": green_claim_allowed,
        "collection_only_claim_allowed": status == P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF,
        "full_suite_claim_allowed": False,
        "real_device_claim_allowed": False,
        "actual_human_review_claim_allowed": False,
        "p5_final_claim_allowed": False,
        "p6_start_claim_allowed": False,
        "p8_start_claim_allowed": False,
        "release_claim_allowed": False,
        "result_summary_ref": clean_identifier(result_summary_ref, default="bodyfree_result_summary_ref", max_length=220),
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "command_string_included": False,
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
    }
    assert_p7_r54_ev22_validation_command_matrix_row_contract(row)
    return row


def assert_p7_r54_ev22_validation_command_matrix_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS,
        source="p7_r54_ev22_validation_command_matrix_row",
    )
    if data.get("schema_version") != P7_R54_EV_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION:
        raise ValueError("R54 EV22 command row schema version changed")
    if data.get("result_status_ref") not in P7_R54_EV22_ALLOWED_COMMAND_RESULT_STATUS_REFS:
        raise ValueError("R54 EV22 command row result status outside allowed refs")
    if data.get("body_free") is not True:
        raise ValueError("R54 EV22 command row must be body-free")
    for false_key in (
        "full_suite_claim_allowed", "real_device_claim_allowed", "actual_human_review_claim_allowed",
        "p5_final_claim_allowed", "p6_start_claim_allowed", "p8_start_claim_allowed", "release_claim_allowed",
        "command_result_body_stored_here", "terminal_output_stored_here", "command_string_included",
        "raw_body_included", "question_text_included", "draft_question_text_included", "local_path_included",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV22 command row must keep {false_key}=False")
    if data.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF:
        if data.get("collection_only_claim_allowed") is not True:
            raise ValueError("R54 EV22 collect-only row must keep collection-only claim explicit")
        if data.get("green_claim_allowed") is not False:
            raise ValueError("R54 EV22 collect-only row must not be claimed as green")
    if data.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_FAILED_REF and int(data.get("failure_count") or 0) <= 0:
        raise ValueError("R54 EV22 failed row must carry failure_count")
    if data.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_PASSED_REF and int(data.get("failure_count") or 0) != 0:
        raise ValueError("R54 EV22 passed row must not carry failures")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r54_ev22_validation_command_matrix_row")
    return True


def _ev22_command_rows_from_input(rows: Sequence[Mapping[str, Any]] | None, *, review_session_id: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, raw_row in enumerate(rows or ()):  # type: ignore[arg-type]
        row_data = safe_mapping(raw_row)
        if not row_data:
            continue
        out.append(
            build_p7_r54_ev22_validation_command_matrix_row(
                command_ref=row_data.get("command_ref") or row_data.get("validation_command_row_ref") or f"validation_command_{index}",
                command_group_ref=row_data.get("command_group_ref", "r54_ev22_validation"),
                command_kind_ref=row_data.get("command_kind_ref", "pytest_target"),
                result_status_ref=row_data.get("result_status_ref", P7_R54_EV22_COMMAND_RESULT_PASSED_REF),
                result_scope_ref=row_data.get("result_scope_ref", "selected_target_only"),
                passed_count=row_data.get("passed_count", 0),
                collected_count=row_data.get("collected_count", 0),
                warning_count=row_data.get("warning_count", 0),
                failure_count=row_data.get("failure_count", 0),
                result_summary_ref=row_data.get("result_summary_ref", "bodyfree_result_summary_ref"),
                review_session_id=review_session_id,
            )
        )
    return out


def _ev22_claim_scope_refs(rows: Sequence[Mapping[str, Any]], supplied: Sequence[Any] | None) -> tuple[list[str], list[str], list[str]]:
    safe_claims: list[str] = []
    collection_claims: list[str] = []
    blocked_claims: list[str] = []
    for row in rows:
        command_ref = clean_identifier(row.get("command_ref"), default="validation_command_ref", max_length=220)
        scope_ref = clean_identifier(row.get("result_scope_ref"), default="selected_target_only", max_length=180)
        if row.get("green_claim_allowed") is True:
            safe_claims.append(f"{command_ref}__{scope_ref}__green_claim_scope")
        elif row.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_PASSED_REF and _ev22_contains_blocked_claim_ref(scope_ref):
            blocked_claims.append(f"{command_ref}__{scope_ref}")
        if row.get("collection_only_claim_allowed") is True:
            collection_claims.append(f"{command_ref}__{scope_ref}__collection_only_not_full_suite")
    for claim in supplied or ():
        clean = clean_identifier(claim, max_length=220)
        if not clean:
            continue
        if _ev22_contains_blocked_claim_ref(clean):
            blocked_claims.append(clean)
        else:
            safe_claims.append(clean)
    return (
        dedupe_identifiers(safe_claims, limit=160, max_length=240),
        dedupe_identifiers(collection_claims, limit=160, max_length=240),
        dedupe_identifiers(blocked_claims, limit=160, max_length=240),
    )


def _ev22_status_next_reason(
    ev21: Mapping[str, Any],
    rows: Sequence[Mapping[str, Any]],
    blocked_claim_refs: Sequence[str],
) -> tuple[str, str, list[str]]:
    if ev21.get("handoff_status") != P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF or ev21.get("next_required_step") != P7_R54_EV22_STEP_REF:
        reasons = dedupe_identifiers(
            [P7_R54_EV22_BLOCKED_BY_EV21_REASON_REF, *(ev21.get("open_execution_blocker_ids") or [])],
            limit=160,
            max_length=240,
        )
        return (P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_EV21_STATUS_REF, P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF, reasons)
    if not rows:
        return (
            P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_EV22_COMMAND_MATRIX_MISSING_REASON_REF],
        )
    executed_rows = [row for row in rows if row.get("result_status_ref") != P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF]
    if not executed_rows:
        return (
            P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF,
            [P7_R54_EV22_COMMAND_MATRIX_NOT_EXECUTED_ONLY_REASON_REF],
        )
    failed_rows = [
        clean_identifier(row.get("command_ref"), default="validation_command_failed", max_length=220)
        for row in rows
        if row.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_FAILED_REF
    ]
    if failed_rows:
        return (
            P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF,
            P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_EV22_COMMAND_MATRIX_FAILED_REASON_REF, *failed_rows], limit=160, max_length=240),
        )
    if blocked_claim_refs:
        return (
            P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF,
            P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF,
            dedupe_identifiers([P7_R54_EV22_GREEN_CLAIM_OVERREACH_REASON_REF, *blocked_claim_refs], limit=160, max_length=240),
        )
    return (P7_R54_EV22_DOCUMENTATION_OUTPUT_READY_STATUS_REF, P7_R54_EV22_NEXT_WORK_AFTER_EV22_REF, [P7_R54_EV22_READY_REASON_REF])


def build_p7_r54_ev22_validation_command_matrix_documentation_output(
    *,
    r52_reintake_handoff: Mapping[str, Any] | None = None,
    validation_command_rows: Sequence[Mapping[str, Any]] | None = None,
    not_executed_validation_refs: Sequence[Any] | None = None,
    green_claim_scope_refs: Sequence[Any] | None = None,
    material_id: Any = "p7_r54_ev22_validation_command_matrix_documentation_output",
) -> dict[str, Any]:
    ev21 = safe_mapping(r52_reintake_handoff) if r52_reintake_handoff is not None else build_p7_r54_ev21_r52_reintake_handoff()
    assert_p7_r54_ev21_r52_reintake_handoff_contract(ev21)
    review_session_id = _safe_review_session_id(ev21.get("review_session_id"))
    rows = _ev22_command_rows_from_input(validation_command_rows, review_session_id=review_session_id)
    safe_claim_refs, collection_claim_refs, blocked_claim_refs = _ev22_claim_scope_refs(rows, green_claim_scope_refs)
    status, next_step, reason_refs = _ev22_status_next_reason(ev21, rows, blocked_claim_refs)
    ready = status == P7_R54_EV22_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    not_executed_refs = dedupe_identifiers(
        not_executed_validation_refs or P7_R54_EV22_DEFAULT_NOT_EXECUTED_VALIDATION_REFS,
        limit=100,
        max_length=220,
    )
    failed_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_FAILED_REF)
    collected_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF)
    passed_count = sum(1 for row in rows if row.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_PASSED_REF)
    executed_rows = [row for row in rows if row.get("result_status_ref") != P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF]
    issue_refs = [] if ready else dedupe_identifiers([*reason_refs, *blocked_claim_refs], limit=180, max_length=240)
    material = {
        "schema_version": P7_R54_EV_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_EV_STEP,
        "scope": P7_R54_EV_SCOPE,
        "policy_kind": P7_R54_EV_POLICY_KIND,
        "policy_section": P7_R54_EV22_STEP_REF,
        "operation_step_ref": P7_R54_EV22_STEP_REF,
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r54_ev22_validation_command_matrix_documentation_output", max_length=220),
        "review_session_id": review_session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "ev21_schema_version": P7_R54_EV_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "ev21_material_ref": clean_identifier(ev21.get("material_id"), default="p7_r54_ev21_r52_reintake_handoff", max_length=220),
        "ev21_next_required_step": clean_identifier(ev21.get("next_required_step"), default="", max_length=180),
        "ev21_handoff_status": clean_identifier(ev21.get("handoff_status"), default=P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF, max_length=180),
        "ev21_r52_reintake_handoff_ready": ev21.get("r52_reintake_handoff_ready") is True,
        "ev21_actual_review_evidence_complete": ev21.get("actual_review_evidence_complete") is True,
        "operation_current_refs": dict(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "operation_current_ref_count": len(P7_R54_EV_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "actual_review_basis_ref": P7_R54_EV_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_EV_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
        "operation_current_refs_are_actual_review_basis": True,
        "operation_current_refs_used_as_actual_review_basis": True,
        "existing_op24_helper_ref": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625.build_p7_r54_op24_validation_command_matrix_documentation_output",
        "existing_op24_schema_version": r54op.P7_R54_OPERATION_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "existing_op24_operation_current_refs": dict(r54op.P7_R54_OPERATION_CURRENT_REFS),
        "existing_op24_current_refs_are_historical_here": True,
        "existing_op24_reused_as_actual_validation_documentation_basis": False,
        "existing_op24_reused_as_actual_documentation_output_basis": False,
        "existing_op24_structural_contract_reused": True,
        **_false_flags(),
        "required_case_count": P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(ev21.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(ev21.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(ev21.get("question_observation_row_count") or 0) if ready else 0,
        "disposal_verified": ev21.get("disposal_verified") is True and ready,
        "actual_review_evidence_complete": ev21.get("actual_review_evidence_complete") is True and ready,
        "body_free_evidence_handoff_materialized_here": ev21.get("body_free_evidence_handoff_materialized_here") is True and ready,
        "r52_reintake_handoff_ready": ev21.get("r52_reintake_handoff_ready") is True and ready,
        "r52_reintake_required": ev21.get("r52_reintake_required") is True and ready,
        "p5_decision_candidate": clean_identifier(ev21.get("p5_decision_candidate"), default=P7_R54_EV17_INCONCLUSIVE_REF, max_length=180),
        "p5_human_blind_qa_confirmed_candidate": ev21.get("p5_human_blind_qa_confirmed_candidate") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_candidate": ev21.get("p6_limited_human_readfeel_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": ev21.get("p8_question_design_material_candidate") is True and ready,
        "p8_material_candidate_row_count": int(ev21.get("p8_material_candidate_row_count") or 0) if ready else 0,
        "p8_start_allowed": False,
        "question_implementation_started_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "release_allowed": False,
        "p7_complete": False,
        "documentation_output_status": status,
        "documentation_output_ref": P7_R54_EV22_DOCUMENTATION_OUTPUT_REF if ready else "ev22_validation_command_matrix_documentation_output_not_ready_bodyfree_20260626",
        "documentation_output_file_ref": P7_R54_EV22_DOCUMENTATION_OUTPUT_FILE_REF if ready else "R54_EV22_Result_NotReady_20260626.md",
        "documentation_output_file_bodyfree": True,
        "documentation_output_file_contains_terminal_output_body": False,
        "documentation_output_reason_refs": reason_refs,
        "documentation_output_issue_refs": issue_refs,
        "documentation_output_issue_count": len(issue_refs),
        "documentation_output_materialized_here": ready,
        "validation_command_row_schema_version": P7_R54_EV_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION,
        "validation_command_row_required_field_refs": list(P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS),
        "validation_command_rows": rows,
        "validation_command_row_count": len(rows),
        "executed_validation_command_refs": [clean_identifier(row.get("command_ref"), default="validation_command", max_length=220) for row in executed_rows] if ready else [],
        "executed_validation_command_count": len(executed_rows) if ready else 0,
        "passed_validation_command_count": passed_count if ready else 0,
        "collected_only_validation_command_count": collected_count if ready else 0,
        "failed_validation_command_count": failed_count,
        "not_executed_validation_command_count": sum(1 for row in rows if row.get("result_status_ref") == P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF),
        "not_executed_validation_refs": not_executed_refs,
        "not_executed_validation_ref_count": len(not_executed_refs),
        "green_claim_scope_refs": safe_claim_refs if ready else [],
        "green_claim_scope_count": len(safe_claim_refs) if ready else 0,
        "collection_only_scope_refs": collection_claim_refs if ready else [],
        "collection_only_scope_count": len(collection_claim_refs) if ready else 0,
        "blocked_green_claim_refs": blocked_claim_refs,
        "blocked_green_claim_count": len(blocked_claim_refs),
        "claim_boundary_guard_refs": list(P7_R54_EV22_CLAIM_BOUNDARY_GUARD_REFS),
        "claim_boundary_guard_count": len(P7_R54_EV22_CLAIM_BOUNDARY_GUARD_REFS),
        "claim_boundary_policy_ref": P7_R54_EV22_CLAIM_BOUNDARY_POLICY_REF,
        "collect_only_claimed_as_full_suite_green": False,
        "rn_contract_claimed_as_real_device_modal_verified": False,
        "r54_helper_green_claimed_as_actual_human_review_complete": False,
        "full_backend_suite_green_claimed": False,
        "real_device_modal_verified_claimed": False,
        "actual_human_review_complete_claimed_by_helper": False,
        "p5_final_confirmation_claimed_from_validation_matrix": False,
        "release_claimed_from_validation_matrix": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "command_string_included": False,
        "human_review_completion_claim_blocked_here": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "actual_rating_rows_materialized_here": ev21.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_blocker_rows_materialized_here": ev21.get("actual_blocker_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": ev21.get("actual_question_need_observation_rows_materialized_here") is True and ready,
        "actual_disposal_receipt_materialized_here": ev21.get("actual_disposal_receipt_materialized_here") is True and ready,
        "execution_blocker_ids": issue_refs,
        "open_execution_blocker_ids": issue_refs,
        "implemented_steps": list(P7_R54_EV22_IMPLEMENTED_STEPS if ready else tuple(ev21.get("implemented_steps") or P7_R54_EV21_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_EV22_NOT_YET_IMPLEMENTED_STEPS if ready else tuple(ev21.get("not_yet_implemented_steps") or P7_R54_EV21_NOT_YET_IMPLEMENTED_STEPS)),
        "first_next_work_ref": P7_R54_EV22_NEXT_WORK_AFTER_EV22_REF if ready else P7_R54_EV21_NEXT_WORK_AFTER_EV21_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_ev_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        "raw_body_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_path_included": False,
    }
    assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract(material)
    return material


def assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS,
        source="p7_r54_ev22_validation_command_matrix_documentation_output",
    )
    _assert_common_bodyfree_no_touch(
        data,
        schema_version=P7_R54_EV_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        policy_section=P7_R54_EV22_STEP_REF,
        operation_step_ref=P7_R54_EV22_STEP_REF,
        source="p7_r54_ev22_validation_command_matrix_documentation_output",
        false_flag_refs=_ev22_false_flag_refs(),
    )
    if safe_mapping(data.get("existing_op24_operation_current_refs")) != r54op.P7_R54_OPERATION_CURRENT_REFS:
        raise ValueError("R54 EV22 existing OP24 historical refs changed")
    if data.get("existing_op24_current_refs_are_historical_here") is not True:
        raise ValueError("R54 EV22 must keep existing OP24 refs historical-only")
    if data.get("existing_op24_reused_as_actual_validation_documentation_basis") is not False:
        raise ValueError("R54 EV22 must not reuse existing OP24 as actual basis")
    if data.get("existing_op24_reused_as_actual_documentation_output_basis") is not False:
        raise ValueError("R54 EV22 must keep existing OP24 documentation output historical-only")
    if data.get("documentation_output_status") not in P7_R54_EV22_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS:
        raise ValueError("R54 EV22 documentation output status outside allowed refs")
    ready = data.get("documentation_output_status") == P7_R54_EV22_DOCUMENTATION_OUTPUT_READY_STATUS_REF
    if data.get("documentation_output_materialized_here") is not ready:
        raise ValueError("R54 EV22 documentation materialization flag must match status")
    if data.get("documentation_output_file_bodyfree") is not True:
        raise ValueError("R54 EV22 documentation output file ref must be body-free")
    if data.get("documentation_output_file_contains_terminal_output_body") is not False:
        raise ValueError("R54 EV22 documentation output must not contain terminal output body")
    for row in data.get("validation_command_rows") or ():
        assert_p7_r54_ev22_validation_command_matrix_row_contract(row)
    for false_key in (
        "collect_only_claimed_as_full_suite_green", "rn_contract_claimed_as_real_device_modal_verified",
        "r54_helper_green_claimed_as_actual_human_review_complete", "full_backend_suite_green_claimed",
        "real_device_modal_verified_claimed", "actual_human_review_complete_claimed_by_helper",
        "p5_final_confirmation_claimed_from_validation_matrix",
        "release_claimed_from_validation_matrix", "documentation_output_file_contains_terminal_output_body",
        "command_result_body_stored_here", "terminal_output_stored_here",
        "command_string_included", "documentation_output_file_contains_terminal_output_body", "p5_human_blind_qa_confirmed_final", "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed", "question_implementation_started_here", "p8_implementation_spec_finalized_here",
        "p8_question_implementation_spec_finalized_here", "release_allowed", "p7_complete", "raw_body_included",
        "question_text_included", "draft_question_text_included", "local_path_included",
        "actual_human_review_run_here", "actual_manual_review_run_here", "body_full_packet_generated_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R54 EV22 must keep {false_key}=False")
    if data.get("blocked_green_claim_count") != len(data.get("blocked_green_claim_refs") or ()): 
        raise ValueError("R54 EV22 blocked green claim count changed")
    if data.get("collection_only_scope_count") != len(data.get("collection_only_scope_refs") or ()): 
        raise ValueError("R54 EV22 collection-only scope count changed")
    if data.get("green_claim_scope_count") != len(data.get("green_claim_scope_refs") or ()): 
        raise ValueError("R54 EV22 green claim scope count changed")
    if data.get("not_executed_validation_ref_count") != len(data.get("not_executed_validation_refs") or ()): 
        raise ValueError("R54 EV22 not-executed validation count changed")
    if ready:
        if data.get("ev21_handoff_status") != P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF or data.get("ev21_r52_reintake_handoff_ready") is not True:
            raise ValueError("R54 EV22 ready must be based on EV21 R52 handoff ready")
        if data.get("actual_review_evidence_complete") is not True or data.get("r52_reintake_handoff_ready") is not True:
            raise ValueError("R54 EV22 ready must preserve EV21 body-free evidence completion")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_key) != P7_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"R54 EV22 ready must preserve 24 {count_key}")
        if data.get("validation_command_row_count") <= 0 or data.get("executed_validation_command_count") <= 0:
            raise ValueError("R54 EV22 ready requires executed validation command refs")
        if data.get("failed_validation_command_count") != 0 or data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV22 ready must not carry failed validation rows or blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_EV22_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV22 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_EV22_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R54 EV22 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_EV22_NEXT_WORK_AFTER_EV22_REF:
            raise ValueError("R54 EV22 ready next required step changed")
    else:
        if data.get("actual_review_evidence_complete") is not False or data.get("r52_reintake_handoff_ready") is not False:
            raise ValueError("R54 EV22 blocked must not expose evidence completion")
        if not data.get("open_execution_blocker_ids"):
            raise ValueError("R54 EV22 blocked must carry blocker refs")
        if data.get("next_required_step") != P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R54 EV22 blocked next step changed")
    return True


P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION: Final = P7_R54_EV_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION
P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = P7_R54_EV_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
build_p7_r54_ev22_validation_command_matrix_documentation_output_bodyfree = build_p7_r54_ev22_validation_command_matrix_documentation_output
assert_p7_r54_ev22_validation_command_matrix_documentation_output_bodyfree_contract = assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract


# EV22 detailed-design wording aliases and previous result-memo compatibility refs.
P7_R54_EV22_REQUIRED_FIELD_REFS: Final = P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS
P7_R54_EV22_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final = P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS
P7_R54_EV22_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS: Final = P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS
P7_R54_EV_NEXT_WORK_AFTER_EV22_REF: Final = P7_R54_EV22_NEXT_WORK_AFTER_EV22_REF
P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_R52_HANDOFF_STATUS_REF: Final = P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_EV21_STATUS_REF
P7_R54_EV22_BLOCKED_BY_R52_HANDOFF_REASON_REF: Final = P7_R54_EV22_BLOCKED_BY_EV21_REASON_REF

P7_R54_EV20_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = P7_R54_EV_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION
P7_R54_EV21_R52_REINTAKE_HANDOFF_SCHEMA_VERSION: Final = P7_R54_EV_R52_REINTAKE_HANDOFF_SCHEMA_VERSION
build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_bodyfree = build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation
assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract = assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract
build_p7_r54_ev21_r52_reintake_handoff_bodyfree = build_p7_r54_ev21_r52_reintake_handoff
assert_p7_r54_ev21_r52_reintake_handoff_bodyfree_contract = assert_p7_r54_ev21_r52_reintake_handoff_contract

__all__ = (
    *__all__,
    "P7_R54_EV_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION", "P7_R54_EV_R52_REINTAKE_HANDOFF_SCHEMA_VERSION",
    "P7_R54_EV20_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION", "P7_R54_EV21_R52_REINTAKE_HANDOFF_SCHEMA_VERSION",
    "P7_R54_EV20_STEP_REF", "P7_R54_EV21_STEP_REF", "P7_R54_EV22_NEXT_REQUIRED_STEP_REF", "P7_R54_EV20_IMPLEMENTED_STEPS", "P7_R54_EV20_NOT_YET_IMPLEMENTED_STEPS", "P7_R54_EV21_IMPLEMENTED_STEPS", "P7_R54_EV21_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV20_FINAL_VALIDATION_READY_STATUS_REF", "P7_R54_EV20_FINAL_VALIDATION_BLOCKED_STATUS_REF", "P7_R54_EV20_BODY_LEAK_BLOCKED_STATUS_REF", "P7_R54_EV20_NO_TOUCH_BLOCKED_STATUS_REF", "P7_R54_EV20_FINAL_VALIDATION_REF", "P7_R54_EV20_READY_REASON_REF", "P7_R54_EV20_REQUIRED_FIELD_REFS",
    "P7_R54_EV21_R52_REINTAKE_HANDOFF_READY_STATUS_REF", "P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_ACTUAL_REVIEW_EVIDENCE_MISSING_STATUS_REF", "P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_DISPOSAL_STATUS_REF", "P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_BODY_LEAK_OR_QUESTION_TEXT_STATUS_REF", "P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_NO_TOUCH_VIOLATION_STATUS_REF", "P7_R54_EV21_R52_REINTAKE_BLOCKED_BY_INCONCLUSIVE_STATUS_REF", "P7_R54_EV21_ALLOWED_R52_REINTAKE_HANDOFF_STATUS_REFS", "P7_R54_EV21_R52_REINTAKE_HANDOFF_REF", "P7_R54_EV21_BODY_FREE_ACTUAL_REVIEW_EVIDENCE_REF", "P7_R54_EV21_READY_REASON_REF", "P7_R54_EV21_REQUIRED_FIELD_REFS",
    "build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation", "assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_contract", "build_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_bodyfree", "assert_p7_r54_ev20_final_no_body_leak_no_question_text_no_touch_validation_bodyfree_contract",
    "build_p7_r54_ev21_r52_reintake_handoff", "assert_p7_r54_ev21_r52_reintake_handoff_contract", "build_p7_r54_ev21_r52_reintake_handoff_bodyfree", "assert_p7_r54_ev21_r52_reintake_handoff_bodyfree_contract",
)



__all__ = (
    *__all__,
    "P7_R54_EV_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION", "P7_R54_EV_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION",
    "P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_SCHEMA_VERSION", "P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION",
    "P7_R54_EV22_STEP_REF", "P7_R54_EV22_BLOCKED_NEXT_REQUIRED_STEP_REF", "P7_R54_EV22_NEXT_WORK_AFTER_EV22_REF", "P7_R54_EV22_IMPLEMENTED_STEPS", "P7_R54_EV22_NOT_YET_IMPLEMENTED_STEPS",
    "P7_R54_EV22_DOCUMENTATION_OUTPUT_READY_STATUS_REF", "P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_STATUS_REF", "P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_EV21_STATUS_REF", "P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_COMMAND_MATRIX_STATUS_REF", "P7_R54_EV22_DOCUMENTATION_OUTPUT_BLOCKED_BY_CLAIM_OVERREACH_STATUS_REF", "P7_R54_EV22_ALLOWED_DOCUMENTATION_OUTPUT_STATUS_REFS", "P7_R54_EV22_DOCUMENTATION_OUTPUT_REF", "P7_R54_EV22_DOCUMENTATION_OUTPUT_FILE_REF", "P7_R54_EV22_READY_REASON_REF", "P7_R54_EV22_BLOCKED_BY_EV21_REASON_REF", "P7_R54_EV22_COMMAND_MATRIX_MISSING_REASON_REF", "P7_R54_EV22_COMMAND_MATRIX_FAILED_REASON_REF", "P7_R54_EV22_COMMAND_MATRIX_NOT_EXECUTED_ONLY_REASON_REF", "P7_R54_EV22_GREEN_CLAIM_OVERREACH_REASON_REF",
    "P7_R54_EV22_COMMAND_RESULT_PASSED_REF", "P7_R54_EV22_COMMAND_RESULT_COLLECTED_ONLY_REF", "P7_R54_EV22_COMMAND_RESULT_NOT_EXECUTED_REF", "P7_R54_EV22_COMMAND_RESULT_FAILED_REF", "P7_R54_EV22_ALLOWED_COMMAND_RESULT_STATUS_REFS", "P7_R54_EV22_CLAIM_BOUNDARY_GUARD_REFS", "P7_R54_EV22_DEFAULT_NOT_EXECUTED_VALIDATION_REFS", "P7_R54_EV22_BLOCKED_GREEN_CLAIM_TOKEN_REFS",
    "P7_R54_EV22_VALIDATION_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS", "P7_R54_EV22_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS", "P7_R54_EV22_REQUIRED_FIELD_REFS", "P7_R54_EV22_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS", "P7_R54_EV22_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS",
    "build_p7_r54_ev22_validation_command_matrix_row", "assert_p7_r54_ev22_validation_command_matrix_row_contract",
    "build_p7_r54_ev22_validation_command_matrix_documentation_output", "assert_p7_r54_ev22_validation_command_matrix_documentation_output_contract", "build_p7_r54_ev22_validation_command_matrix_documentation_output_bodyfree", "assert_p7_r54_ev22_validation_command_matrix_documentation_output_bodyfree_contract",
)
