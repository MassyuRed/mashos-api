# -*- coding: utf-8 -*-
"""R54-AHR-CS current snapshot actual review re-entry helper.

CS00-CS18 are intentionally thin and body-free:

* CS00 freezes the scope / no-touch boundary.
* CS01 freezes the current 262/84/257/170 basis envelope.
* CS02 reconciles historical helper refs as structural / regression context only.
* CS03 records that direct 260/83/256/169 -> 262/84/257/170 diff evidence is
  not available here and therefore current manifest refreeze remains required.
* CS04 refreezes the current 24-case manifest as body-free refs only.
* CS05 freezes local-only preflight before any later packet generation request.
* CS06 records the packet generation request / receipt bridge as body-free refs only.
* CS07 records packet completeness and export denylist scan evidence as body-free refs only.
* CS08 freezes the reviewer selection form as a current-compatible selection-only contract.
* CS09 intakes an actual human review operation receipt as body-free refs only.
* CS10 intakes sanitized selection-only review result rows as body-free refs only.
* CS11 normalizes rating rows from sanitized rows as body-free refs only.
* CS12 normalizes blocker rows and question-need observation rows as body-free refs only.
* CS13 guards rating/question consistency without creating question text.
* CS14 intakes pause / abort / expiration / disposal receipt refs without body content.
* CS15 summarizes post-review body-free evidence and only then marks evidence complete.
* CS16 separates P5 decision candidates from P5 final / repair / blocked outcomes.
* CS17 builds P6/P8 candidate-only and R52 handoff envelopes without executing them.
* CS18 records final no-leak/no-question/no-touch validation and command-matrix documentation.

The existing 2026-06-27 R54-AHR helper is not rewritten.  Its
260/83/256/169 basis remains historical / structural / regression context and
must not be relabelled as current actual-review evidence.

No body-full packet content is generated or exported here.  No API, DB, RN,
runtime, public response contract, P8 question implementation, P6 start, P5
finalization, R52 execution, P7 completion, or release permission is performed
here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Final

from emlis_ai_p7_contracts import (
    P7_PHASE,
    P7_SOURCE_MODE,
    assert_false_markers,
    assert_p7_no_body_payload_or_contract_mutation,
    clean_identifier,
    public_contract_flags,
)
import emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627 as historical_ahr


P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs00_scope_no_touch_boundary_freeze.bodyfree.v1"
)
P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs01_current_snapshot_basis_refreeze.bodyfree.v1"
)
P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs02_historical_helper_refs_reconcile.bodyfree.v1"
)
P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs03_manifest_packet_evidence_impact_assessment.bodyfree.v1"
)
P7_R54_AHR_CS_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
)
P7_R54_AHR_CS_CURRENT_SNAPSHOT_BASIS_ENVELOPE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION
)
P7_R54_AHR_CS_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION
)
P7_R54_AHR_CS_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION
)
P7_R54_AHR_CS_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION
)
P7_R54_AHR_CS_CURRENT_BASIS_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.current_262_84_257_170_basis_envelope.bodyfree.v1"
)

P7_R54_AHR_CS_STEP: Final = "R54-AHR-CS_CurrentSnapshotActualReviewReentry_20260628"
P7_R54_AHR_CS_SCOPE: Final = "p5_user_label_connection_current_snapshot_actual_review_reentry"
P7_R54_AHR_CS_POLICY_KIND: Final = "r54_ahr_current_snapshot_actual_review_reentry_boundary"
P7_R54_AHR_CS_CURRENT_PHASE: Final = P7_PHASE
P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID: Final = (
    "p7_r54_ahr_current_snapshot_actual_review_reentry_20260628"
)

P7_R54_AHR_CS00_STEP_REF: Final = "R54-AHR-CS00_scope_no_touch_boundary_freeze"
P7_R54_AHR_CS01_STEP_REF: Final = "R54-AHR-CS01_current_262_84_257_170_basis_envelope"
P7_R54_AHR_CS02_STEP_REF: Final = "R54-AHR-CS02_historical_helper_refs_reconcile"
P7_R54_AHR_CS03_STEP_REF: Final = "R54-AHR-CS03_manifest_packet_evidence_impact_assessment"
P7_R54_AHR_CS04_STEP_REF: Final = "R54-AHR-CS04_current_24_case_manifest_refreeze"
P7_R54_AHR_CS05_STEP_REF: Final = "R54-AHR-CS05_local_only_preflight"
P7_R54_AHR_CS06_STEP_REF: Final = "R54-AHR-CS06_packet_generation_request_receipt_bridge"
P7_R54_AHR_CS07_STEP_REF: Final = "R54-AHR-CS07_packet_completeness_export_denylist_scan"
P7_R54_AHR_CS08_STEP_REF: Final = "R54-AHR-CS08_reviewer_selection_form_current_compatibility"
P7_R54_AHR_CS09_STEP_REF: Final = "R54-AHR-CS09_actual_human_review_operation_receipt_intake"
P7_R54_AHR_CS10_STEP_REF: Final = "R54-AHR-CS10_sanitized_review_result_row_intake"
P7_R54_AHR_CS11_STEP_REF: Final = "R54-AHR-CS11_rating_row_normalization"
P7_R54_AHR_CS12_STEP_REF: Final = "R54-AHR-CS12_blocker_question_need_observation_normalization"
P7_R54_AHR_CS13_STEP_REF: Final = "R54-AHR-CS13_rating_question_consistency_guard"
P7_R54_AHR_CS14_STEP_REF: Final = "R54-AHR-CS14_pause_abort_expiration_disposal_receipt"
P7_R54_AHR_CS15_STEP_REF: Final = "R54-AHR-CS15_bodyfree_post_review_summary_evidence_complete"
P7_R54_AHR_CS16_STEP_REF: Final = "R54-AHR-CS16_p5_decision_candidate_separation"
P7_R54_AHR_CS17_STEP_REF: Final = "R54-AHR-CS17_p6_p8_candidate_only_r52_handoff_envelope"
P7_R54_AHR_CS18_STEP_REF: Final = "R54-AHR-CS18_final_validation_command_matrix_documentation_output"

P7_R54_AHR_CS_STEP_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS00_STEP_REF,
    P7_R54_AHR_CS01_STEP_REF,
    P7_R54_AHR_CS02_STEP_REF,
    P7_R54_AHR_CS03_STEP_REF,
    P7_R54_AHR_CS04_STEP_REF,
    P7_R54_AHR_CS05_STEP_REF,
    P7_R54_AHR_CS06_STEP_REF,
    P7_R54_AHR_CS07_STEP_REF,
    P7_R54_AHR_CS08_STEP_REF,
    P7_R54_AHR_CS09_STEP_REF,
    P7_R54_AHR_CS10_STEP_REF,
    P7_R54_AHR_CS11_STEP_REF,
    P7_R54_AHR_CS12_STEP_REF,
    P7_R54_AHR_CS13_STEP_REF,
    P7_R54_AHR_CS14_STEP_REF,
    P7_R54_AHR_CS15_STEP_REF,
    P7_R54_AHR_CS16_STEP_REF,
    P7_R54_AHR_CS17_STEP_REF,
    P7_R54_AHR_CS18_STEP_REF,
)
P7_R54_AHR_CS00_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (P7_R54_AHR_CS00_STEP_REF,)
P7_R54_AHR_CS00_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[1:]
P7_R54_AHR_CS01_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS00_STEP_REF,
    P7_R54_AHR_CS01_STEP_REF,
)
P7_R54_AHR_CS01_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[2:]
P7_R54_AHR_CS02_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS01_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS02_STEP_REF,
)
P7_R54_AHR_CS02_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[3:]
P7_R54_AHR_CS03_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS02_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS03_STEP_REF,
)
P7_R54_AHR_CS03_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[4:]

P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF: Final = "current_received_snapshot_262_84_257_170"
P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_ALLOWED_REF: Final = "current_received_snapshot_262_84_257_170_only"
P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF: Final = historical_ahr.P7_R54_AHR_ACTUAL_EXECUTION_BASIS_REF
P7_R54_AHR_CS_EXISTING_AHR_BASIS_ALLOWED_REF: Final = historical_ahr.P7_R54_AHR_ACTUAL_EXECUTION_BASIS_ALLOWED_REF
P7_R54_AHR_CS_CURRENT_BASIS_STATUS_REF: Final = (
    "CURRENT_262_84_257_170_BASIS_REFROZEN_FOR_R54_AHR_CS_REENTRY"
)
P7_R54_AHR_CS_CURRENT_BASIS_REFREEZE_STATUS_REF: Final = P7_R54_AHR_CS_CURRENT_BASIS_STATUS_REF

P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(262).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(84).zip",
    "rn_zip_ref": "Cocolon(257).zip",
    "backend_zip_ref": "mashos-api(170).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619.md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R54AHR_CurrentSnapshotActualReview_PreDesignMemo_20260628.md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R54AHR_CurrentSnapshotActualReview_Reentry_DetailedDesign_ImplementationOrder_20260628.md",
}
P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS: Final[tuple[str, ...]] = tuple(
    P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS.keys()
)
P7_R54_AHR_CS_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS: Final[tuple[str, ...]] = (
    "premise_zip_ref",
    "implemented_materials_zip_ref",
    "rn_zip_ref",
    "backend_zip_ref",
    "roadmap_ref",
    "pre_design_memo_ref",
    "detailed_design_ref",
)
P7_R54_AHR_CS_EXISTING_AHR_BASIS_REFS: Final[dict[str, str]] = dict(
    historical_ahr.P7_R54_AHR_CURRENT_EXECUTION_BASIS_REFS
)

P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS: Final[tuple[str, ...]] = (
    *historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_REF_GROUP_REFS,
    "r54_ahr_20260627",
)
P7_R54_AHR_CS_HISTORICAL_HELPER_REFS: Final[dict[str, dict[str, str]]] = {
    **{key: dict(value) for key, value in historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_REFS.items()},
    "r54_ahr_20260627": dict(P7_R54_AHR_CS_EXISTING_AHR_BASIS_REFS),
}
P7_R54_AHR_CS_HISTORICAL_HELPER_MODULE_REFS: Final[dict[str, str]] = {
    "r52_20260621": "emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate",
    "r54_bodyfree_handoff_20260622": "emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff",
    "r55_20260623": "emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization",
    "r54_op_20260625": "emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625",
    "r54_ev_20260626": "emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626",
    "r54_clr_20260627": "emlis_ai_p7_r54_current_snapshot_local_review_run_20260627",
    "r54_ahr_20260627": "emlis_ai_p7_r54_actual_human_review_execution_bodyfree_intake_20260627",
}
P7_R54_AHR_CS_HISTORICAL_HELPER_ROLE_REFS: Final[dict[str, str]] = {
    **dict(historical_ahr.P7_R54_AHR_HISTORICAL_HELPER_ROLE_REFS),
    "r54_ahr_20260627": "actual_human_review_bodyfree_intake_historical_contract",
}
P7_R54_AHR_CS_HISTORICAL_HELPER_CLASSIFICATION_REFS: Final[dict[str, str]] = {
    group_ref: "historical_structural_regression_ref_only"
    for group_ref in P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS
}
P7_R54_AHR_CS_HISTORICAL_HELPER_BASIS_REFS: Final[dict[str, str]] = {
    group_ref: f"historical_helper_snapshot_refs_{group_ref}"
    for group_ref in P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS
}
P7_R54_AHR_CS_HISTORICAL_HELPER_BASIS_REFS["r54_ahr_20260627"] = P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF
P7_R54_AHR_CS_HISTORICAL_HELPER_RECONCILE_STATUS_REF: Final = (
    "HISTORICAL_HELPER_REFS_RECONCILED_AS_STRUCTURAL_REGRESSION_ONLY_FOR_CURRENT_262_84_257_170"
)
P7_R54_AHR_CS_HISTORICAL_HELPER_GREEN_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "helper_green_is_contract_boundary_only",
    "helper_green_is_not_actual_human_review_complete",
    "historical_helper_refs_are_not_current_actual_review_basis",
    "synthetic_bodyfree_rows_are_not_actual_review_rows",
    "r52_handoff_ready_contract_is_not_actual_r52_reintake_execution",
    "existing_ahr_260_83_256_169_is_not_current_262_84_257_170_evidence",
)

P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF: Final = (
    "DIRECT_DIFF_NOT_AVAILABLE_CURRENT_MANIFEST_REFREEZE_REQUIRED"
)
P7_R54_AHR_CS03_DIFF_IMPACT_STATUS_REFS: Final[tuple[str, ...]] = (
    "NO_REVIEW_MANIFEST_IMPACT",
    "REVIEW_MANIFEST_IMPACT_PRESENT",
    "DIFF_INCONCLUSIVE",
    P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF,
)
P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_REASON_REF: Final = (
    "historical_260_83_256_169_source_zip_set_not_available_in_current_reentry_workspace"
)
P7_R54_AHR_CS03_IMPACT_TARGET_REFS: Final[tuple[str, ...]] = (
    "current_24_case_manifest",
    "local_only_packet_boundary",
    "bodyfree_evidence_rows",
    "actual_review_receipt_chain",
    "r52_reintake_handoff_candidate_envelope",
)

P7_R54_AHR_CS_OUT_OF_SCOPE_REFS: Final[tuple[str, ...]] = (
    "p8_question_api_db_rn_trigger_storage_or_text_generation",
    "api_route_or_request_response_key_change",
    "db_schema_or_migration_change",
    "rn_production_ui_or_display_condition_change",
    "runtime_generation_or_gate_threshold_change",
    "public_response_key_change",
    "p6_limited_human_readfeel_start",
    "r52_reintake_actual_execution",
    "p5_finalization",
    "p7_completion",
    "release_decision",
    "body_full_packet_generation_or_export",
)

P7_R54_AHR_CS_NO_TOUCH_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "api_route_changed",
    "request_response_key_changed",
    "db_schema_changed",
    "db_physical_schema_changed",
    "db_migration_created",
    "rn_ui_changed",
    "rn_production_ui_changed",
    "rn_display_condition_changed",
    "runtime_generation_changed",
    "user_label_connection_runtime_changed",
    "gate_threshold_changed",
    "public_response_key_changed",
    "public_response_top_level_key_changed",
    "p8_question_implementation_started",
    "p8_question_api_created",
    "p8_question_db_schema_created",
    "p8_question_rn_ui_created",
    "p8_question_trigger_logic_created",
    "question_answer_persistence_created",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "release_decision_layer_changed",
)
P7_R54_AHR_CS_BODY_FREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_body_included",
    "current_input_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "comment_text_body_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "raw_question_answer_included",
    "body_full_packet_content_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
)
P7_R54_AHR_CS_OPERATION_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_generation_requested_here",
    "body_full_packet_generated_here",
    "body_full_packet_exported_here",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "actual_r52_reintake_execution_confirmed",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "full_backend_suite_green_confirmed",
    "rn_real_device_modal_verified",
)
P7_R54_AHR_CS_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_NO_TOUCH_FALSE_FLAG_REFS,
    *P7_R54_AHR_CS_BODY_FREE_FALSE_FLAG_REFS,
    *P7_R54_AHR_CS_OPERATION_FALSE_FLAG_REFS,
)

P7_R54_AHR_CS_FORBIDDEN_BODY_OR_QUESTION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "raw_body",
        "current_input_body",
        "returned_emlis_body",
        "history_surface",
        "comment_text",
        "comment_text_body",
        "reviewer_free_text",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_notes_body",
        "question_text",
        "draft_question_text",
        "raw_question_answer",
        "body_full_packet_content",
        "packet_content",
        "local_path",
        "local_absolute_path",
        "body_hash",
        "terminal_output_body",
        "stdout_body",
        "stderr_body",
        "traceback_body",
    }
)

P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
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
P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS: Final[tuple[str, ...]] = (
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "current_received_snapshot_ref_keys",
    "required_current_received_snapshot_ref_keys",
    "all_required_current_received_snapshot_refs_present",
    "current_received_snapshot_refs_are_actual_review_basis",
    "current_received_snapshot_refs_used_as_actual_review_basis",
    "actual_review_basis_ref",
    "actual_review_basis_allowed",
)
P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS: Final[tuple[str, ...]] = (
    "existing_ahr_basis_ref",
    "existing_ahr_basis_allowed",
    "existing_ahr_basis_refs",
    "existing_ahr_basis_matches_current",
    "existing_ahr_can_be_used_as_current_actual_review_evidence",
    "existing_ahr_used_as_current_actual_review_evidence",
    "existing_ahr_helper_rewritten",
    "existing_ahr_helper_preserved_as_historical_structural_regression_ref",
    "current_basis_does_not_rewrite_existing_ahr_helper",
    "old_260_83_256_169_not_relabelled_as_current",
)
P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS: Final[tuple[str, ...]] = (
    "public_contract",
    "r54_ahr_cs_no_touch_contract",
    "body_free_markers",
    "body_free",
)
P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "scope_boundary_confirmed",
    "no_touch_boundary_confirmed",
    "no_touch_boundary_frozen",
    "current_snapshot_actual_review_reentry_selected",
    "r54_ahr_cs_prefix_used",
    "p7_r54_ahr_line_preserved",
    "existing_ahr_helper_direct_rewrite_out_of_scope",
    "current_basis_refreeze_required_next",
    "current_basis_refrozen_here",
    "cs00_does_not_claim_current_basis_complete",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "p8_p6_r52_p5_release_out_of_scope",
    "api_db_rn_runtime_public_contract_no_touch_boundary_frozen",
    "body_full_generation_blocked_until_later_preflight",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "out_of_scope_refs",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs00_schema_version",
    "cs00_material_ref",
    "cs00_next_required_step",
    "cs00_scope_boundary_confirmed",
    "cs00_no_touch_boundary_confirmed",
    "current_basis_status_ref",
    "current_basis_refrozen_here",
    "current_basis_refrozen_for_actual_review_reentry",
    "current_received_snapshot_refs_match_262_84_257_170",
    "current_262_84_257_170_does_not_claim_actual_review_complete",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_wrapper_only",
    "new_full_operation_helper_required_here",
    "body_full_generation_blocked_until_later_preflight",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CS_CURRENT_SNAPSHOT_BASIS_ENVELOPE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CS_CURRENT_SNAPSHOT_BASIS_REFREEZE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REQUIRED_FIELD_REFS
)
P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs01_schema_version",
    "cs01_material_ref",
    "cs01_next_required_step",
    "cs01_current_basis_refrozen_here",
    "cs01_current_basis_status_ref",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "historical_helper_refs_reconcile_status_ref",
    "historical_helper_refs_separated",
    "historical_helper_ref_groups",
    "historical_helper_ref_group_count",
    "historical_helper_refs",
    "historical_helper_ref_rows",
    "historical_helper_ref_row_count",
    "historical_helper_module_refs",
    "historical_helper_role_refs",
    "historical_helper_classification_refs",
    "historical_helper_basis_refs",
    "historical_helper_refs_match_current_basis_262_84_257_170",
    "historical_helper_differing_current_basis_ref_keys",
    "historical_helper_differing_current_basis_ref_key_counts",
    "differing_current_basis_ref_group_count",
    "historical_helper_green_claim_boundary_refs",
    "historical_helper_refs_are_historical_here",
    "historical_helper_refs_are_structural_refs_only",
    "historical_helper_refs_are_contract_refs_only",
    "historical_helper_refs_can_be_used_for_helper_regression_only",
    "existing_helper_refs_can_be_used_for_helper_regression_only",
    "historical_helper_refs_can_be_used_for_actual_review_basis",
    "historical_helper_refs_used_as_actual_review_basis",
    "historical_helper_refs_can_be_used_for_current_actual_review_evidence",
    "historical_helper_refs_used_as_current_actual_review_evidence",
    "historical_helper_output_used_as_current_actual_evidence",
    "helper_green_not_actual_human_review_complete",
    "synthetic_contract_rows_not_actual_review_rows",
    "r52_handoff_ready_contract_not_actual_r52_reintake_execution",
    "reconcile_does_not_modify_helper_modules",
    "existing_helper_constants_not_rewritten",
    "existing_helper_constants_rewritten",
    "existing_helper_refs_preserved_as_received",
    "current_refs_override_uses_thin_current_reentry_boundary_layer",
    "new_thin_boundary_helper_only",
    "new_full_operation_helper_required_here",
    "body_full_generation_blocked_until_later_preflight",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs02_schema_version",
    "cs02_material_ref",
    "cs02_next_required_step",
    "cs02_historical_helper_refs_separated",
    "cs02_historical_helper_refs_used_as_current_actual_review_evidence",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "historical_helper_refs_reconciled_before_impact_assessment",
    "manifest_packet_evidence_impact_assessed_here",
    "impact_target_refs",
    "impact_target_ref_count",
    "direct_file_diff_available",
    "direct_file_diff_executed",
    "direct_file_diff_not_available_reason_ref",
    "diff_impact_status_ref",
    "diff_impact_status_allowed_refs",
    "direct_diff_cannot_claim_no_impact",
    "diff_unavailable_does_not_equal_no_impact",
    "review_manifest_impact_unknown_until_current_manifest_refreeze",
    "current_manifest_refreeze_required",
    "current_manifest_refreeze_required_reason_ref",
    "old_manifest_allowed_as_current_manifest",
    "old_manifest_allowed_as_structural_ref",
    "old_manifest_unconditional_adoption_blocked",
    "old_packet_boundary_allowed_as_current_packet_boundary",
    "old_evidence_rows_allowed_as_current_actual_review_rows",
    "current_24_case_manifest_must_be_refrozen_next",
    "body_full_diff_content_included",
    "raw_diff_body_included",
    "local_file_path_included",
    "terminal_output_body_included",
    "body_full_generation_blocked_until_later_preflight",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID, max_length=120)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_CS_FALSE_FLAG_REFS}


def _no_touch_contract() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_CS_NO_TOUCH_FALSE_FLAG_REFS}


def _body_free_markers() -> dict[str, bool]:
    return {key: False for key in P7_R54_AHR_CS_BODY_FREE_FALSE_FLAG_REFS}


def _contains_forbidden_body_or_question_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in P7_R54_AHR_CS_FORBIDDEN_BODY_OR_QUESTION_KEYS:
                return True
            if _contains_forbidden_body_or_question_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_body_or_question_key(child) for child in value)
    return False


def _assert_required_fields(data: Mapping[str, Any], *, required: tuple[str, ...], source: str) -> None:
    actual = set(data.keys())
    expected = set(required)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise ValueError(f"{source} fields changed: missing={missing}, extra={extra}")


def _assert_all_false(flags: Mapping[str, Any], *, source: str) -> None:
    assert_false_markers(flags, source=source)
    for key, value in flags.items():
        if value is not False:
            raise ValueError(f"{source} {key} must remain false")


def _assert_bodyfree_no_touch_base(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, operation_step_ref: str, source: str
) -> None:
    expected_base = {
        "schema_version": schema_version,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": policy_section,
        "operation_step_ref": operation_step_ref,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "source_mode": P7_SOURCE_MODE,
    }
    for key, expected in expected_base.items():
        if data.get(key) != expected:
            raise ValueError(f"{source} {key} changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} Git connection flags must remain false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if _contains_forbidden_body_or_question_key(data):
        raise ValueError(f"{source} contains a forbidden body/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    for key in P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"{source} {key} must remain false")
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        flags = data.get(flag_map_key)
        if not isinstance(flags, Mapping):
            raise ValueError(f"{source} {flag_map_key} must be a mapping")
        _assert_all_false(flags, source=f"{source} {flag_map_key}")


def _assert_true_fields(data: Mapping[str, Any], *, keys: tuple[str, ...], source: str) -> None:
    for key in keys:
        if data.get(key) is not True:
            raise ValueError(f"{source} {key} must remain true")


def _assert_false_fields(data: Mapping[str, Any], *, keys: tuple[str, ...], source: str) -> None:
    for key in keys:
        if data.get(key) is not False:
            raise ValueError(f"{source} {key} must remain false")


def _snapshot_fields(*, actual_basis: bool) -> dict[str, Any]:
    return {
        "current_received_snapshot_refs": dict(P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_keys": list(P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "required_current_received_snapshot_ref_keys": list(P7_R54_AHR_CS_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS),
        "all_required_current_received_snapshot_refs_present": True,
        "current_received_snapshot_refs_are_actual_review_basis": actual_basis,
        "current_received_snapshot_refs_used_as_actual_review_basis": actual_basis,
        "actual_review_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "actual_review_basis_allowed": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_ALLOWED_REF,
    }


def _existing_ahr_fields() -> dict[str, Any]:
    return {
        "existing_ahr_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "existing_ahr_basis_allowed": P7_R54_AHR_CS_EXISTING_AHR_BASIS_ALLOWED_REF,
        "existing_ahr_basis_refs": dict(P7_R54_AHR_CS_EXISTING_AHR_BASIS_REFS),
        "existing_ahr_basis_matches_current": False,
        "existing_ahr_can_be_used_as_current_actual_review_evidence": False,
        "existing_ahr_used_as_current_actual_review_evidence": False,
        "existing_ahr_helper_rewritten": False,
        "existing_ahr_helper_preserved_as_historical_structural_regression_ref": True,
        "current_basis_does_not_rewrite_existing_ahr_helper": True,
        "old_260_83_256_169_not_relabelled_as_current": True,
    }


def _assert_snapshot_fields(data: Mapping[str, Any], *, actual_basis: bool, source: str) -> None:
    for key, expected in _snapshot_fields(actual_basis=actual_basis).items():
        if data.get(key) != expected:
            raise ValueError(f"{source} {key} changed")
    if tuple(data.get("current_received_snapshot_ref_keys") or ()) != P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS:
        raise ValueError(f"{source} current snapshot ref keys changed")
    if tuple(data.get("required_current_received_snapshot_ref_keys") or ()) != (
        P7_R54_AHR_CS_REQUIRED_CURRENT_RECEIVED_SNAPSHOT_REF_KEYS
    ):
        raise ValueError(f"{source} required current snapshot ref keys changed")


def _assert_existing_ahr_fields(data: Mapping[str, Any], *, source: str) -> None:
    for key, expected in _existing_ahr_fields().items():
        if data.get(key) != expected:
            raise ValueError(f"{source} {key} changed")




def _historical_helper_differing_current_basis_ref_keys() -> dict[str, list[str]]:
    current = P7_R54_AHR_CS_CURRENT_RECEIVED_SNAPSHOT_REFS
    differing: dict[str, list[str]] = {}
    for group_ref, refs in P7_R54_AHR_CS_HISTORICAL_HELPER_REFS.items():
        keys = sorted(set(current) | set(refs))
        differing[group_ref] = [key for key in keys if refs.get(key) != current.get(key)]
    return differing


def _historical_helper_ref_rows() -> list[dict[str, Any]]:
    differing = _historical_helper_differing_current_basis_ref_keys()
    rows: list[dict[str, Any]] = []
    for group_ref in P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS:
        refs = dict(P7_R54_AHR_CS_HISTORICAL_HELPER_REFS[group_ref])
        rows.append(
            {
                "schema_version": "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.historical_helper_ref_row.bodyfree.v1",
                "helper_group_ref": group_ref,
                "helper_module_ref": P7_R54_AHR_CS_HISTORICAL_HELPER_MODULE_REFS[group_ref],
                "helper_basis_ref": P7_R54_AHR_CS_HISTORICAL_HELPER_BASIS_REFS[group_ref],
                "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                "helper_snapshot_refs": refs,
                "helper_snapshot_ref_count": len(refs),
                "differing_current_basis_ref_keys": list(differing[group_ref]),
                "differing_current_basis_ref_key_count": len(differing[group_ref]),
                "matches_current_basis": False,
                "allowed_as_structural_ref": True,
                "allowed_as_regression_ref": True,
                "allowed_as_current_actual_review_evidence": False,
                "used_as_current_actual_review_evidence": False,
                "helper_green_can_claim_actual_review_complete": False,
                "rewritten_here": False,
                "body_free": True,
            }
        )
    return rows


def _assert_historical_helper_reconcile_fields(data: Mapping[str, Any], *, source: str) -> None:
    if data.get("historical_helper_refs_reconcile_status_ref") != P7_R54_AHR_CS_HISTORICAL_HELPER_RECONCILE_STATUS_REF:
        raise ValueError(f"{source} historical helper reconcile status changed")
    if tuple(data.get("historical_helper_ref_groups") or ()) != P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS:
        raise ValueError(f"{source} historical helper groups changed")
    if data.get("historical_helper_ref_group_count") != len(P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError(f"{source} historical helper group count changed")
    if data.get("historical_helper_refs") != P7_R54_AHR_CS_HISTORICAL_HELPER_REFS:
        raise ValueError(f"{source} historical helper refs changed")
    if data.get("historical_helper_module_refs") != P7_R54_AHR_CS_HISTORICAL_HELPER_MODULE_REFS:
        raise ValueError(f"{source} historical helper module refs changed")
    if data.get("historical_helper_role_refs") != P7_R54_AHR_CS_HISTORICAL_HELPER_ROLE_REFS:
        raise ValueError(f"{source} historical helper role refs changed")
    if data.get("historical_helper_classification_refs") != P7_R54_AHR_CS_HISTORICAL_HELPER_CLASSIFICATION_REFS:
        raise ValueError(f"{source} historical helper classification refs changed")
    if data.get("historical_helper_basis_refs") != P7_R54_AHR_CS_HISTORICAL_HELPER_BASIS_REFS:
        raise ValueError(f"{source} historical helper basis refs changed")
    match_map = data.get("historical_helper_refs_match_current_basis_262_84_257_170")
    if not isinstance(match_map, Mapping):
        raise ValueError(f"{source} historical helper match map must be a mapping")
    if set(match_map) != set(P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS) or any(match_map.values()):
        raise ValueError(f"{source} historical helper match map changed")
    differing = data.get("historical_helper_differing_current_basis_ref_keys")
    if differing != _historical_helper_differing_current_basis_ref_keys():
        raise ValueError(f"{source} differing current basis ref keys changed")
    differing_counts = data.get("historical_helper_differing_current_basis_ref_key_counts")
    expected_counts = {group_ref: len(keys) for group_ref, keys in _historical_helper_differing_current_basis_ref_keys().items()}
    if differing_counts != expected_counts:
        raise ValueError(f"{source} differing current basis counts changed")
    if data.get("differing_current_basis_ref_group_count") != len(P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError(f"{source} differing current basis group count changed")
    if tuple(data.get("historical_helper_green_claim_boundary_refs") or ()) != (
        P7_R54_AHR_CS_HISTORICAL_HELPER_GREEN_CLAIM_BOUNDARY_REFS
    ):
        raise ValueError(f"{source} helper green claim boundary refs changed")
    rows = data.get("historical_helper_ref_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError(f"{source} historical helper rows must be a sequence")
    if list(rows) != _historical_helper_ref_rows():
        raise ValueError(f"{source} historical helper rows changed")
    if data.get("historical_helper_ref_row_count") != len(P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS):
        raise ValueError(f"{source} historical helper row count changed")
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"{source} historical helper row must be a mapping")
        if row.get("allowed_as_current_actual_review_evidence") is not False:
            raise ValueError(f"{source} historical helper row cannot be current actual review evidence")
        if row.get("used_as_current_actual_review_evidence") is not False:
            raise ValueError(f"{source} historical helper row cannot be used as current actual review evidence")
        if row.get("helper_green_can_claim_actual_review_complete") is not False:
            raise ValueError(f"{source} helper green cannot claim actual review complete")
        if row.get("rewritten_here") is not False:
            raise ValueError(f"{source} historical helper row cannot rewrite refs")
        if row.get("body_free") is not True:
            raise ValueError(f"{source} historical helper row must be body-free")


def build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze(
    *, review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID
) -> dict[str, Any]:
    """Build CS00 body-free scope / no-touch boundary material."""

    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS00_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS00_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_20260628",
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "scope_boundary_confirmed": True,
        "no_touch_boundary_confirmed": True,
        "no_touch_boundary_frozen": True,
        "current_snapshot_actual_review_reentry_selected": True,
        "r54_ahr_cs_prefix_used": True,
        "p7_r54_ahr_line_preserved": True,
        "existing_ahr_helper_direct_rewrite_out_of_scope": True,
        "current_basis_refreeze_required_next": True,
        "current_basis_refrozen_here": False,
        "cs00_does_not_claim_current_basis_complete": True,
        **_snapshot_fields(actual_basis=False),
        **_existing_ahr_fields(),
        "p8_p6_r52_p5_release_out_of_scope": True,
        "api_db_rn_runtime_public_contract_no_touch_boundary_frozen": True,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "out_of_scope_refs": list(P7_R54_AHR_CS_OUT_OF_SCOPE_REFS),
        "implemented_steps": list(P7_R54_AHR_CS00_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS00_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS01_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS00 scope/no-touch boundary",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS00_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS00_STEP_REF,
        source="P7-R54-AHR-CS00 scope/no-touch boundary",
    )
    _assert_snapshot_fields(data, actual_basis=False, source="P7-R54-AHR-CS00 scope/no-touch boundary")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS00 scope/no-touch boundary")
    _assert_true_fields(
        data,
        keys=(
            "scope_boundary_confirmed",
            "no_touch_boundary_confirmed",
            "no_touch_boundary_frozen",
            "current_snapshot_actual_review_reentry_selected",
            "r54_ahr_cs_prefix_used",
            "p7_r54_ahr_line_preserved",
            "existing_ahr_helper_direct_rewrite_out_of_scope",
            "current_basis_refreeze_required_next",
            "cs00_does_not_claim_current_basis_complete",
            "p8_p6_r52_p5_release_out_of_scope",
            "api_db_rn_runtime_public_contract_no_touch_boundary_frozen",
            "body_full_generation_blocked_until_later_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CS00 scope/no-touch boundary",
    )
    _assert_false_fields(data, keys=("current_basis_refrozen_here",), source="P7-R54-AHR-CS00 scope/no-touch boundary")
    if tuple(data.get("out_of_scope_refs") or ()) != P7_R54_AHR_CS_OUT_OF_SCOPE_REFS:
        raise ValueError("P7-R54-AHR-CS00 out-of-scope refs changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS00_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS00 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS00_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS00 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CS01_STEP_REF:
        raise ValueError("P7-R54-AHR-CS00 next required step changed")
    return True


def build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze(
    *,
    scope_no_touch_boundary_freeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CS01 body-free current 262/84/257/170 basis envelope."""

    cs00 = dict(scope_no_touch_boundary_freeze or build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze())
    assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract(cs00)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS01_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS01_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs01_current_262_84_257_170_basis_refreeze_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cs00.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs00_schema_version": cs00["schema_version"],
        "cs00_material_ref": cs00["material_id"],
        "cs00_next_required_step": cs00["next_required_step"],
        "cs00_scope_boundary_confirmed": cs00["scope_boundary_confirmed"],
        "cs00_no_touch_boundary_confirmed": cs00["no_touch_boundary_confirmed"],
        "current_basis_status_ref": P7_R54_AHR_CS_CURRENT_BASIS_STATUS_REF,
        "current_basis_refrozen_here": True,
        "current_basis_refrozen_for_actual_review_reentry": True,
        "current_received_snapshot_refs_match_262_84_257_170": True,
        "current_262_84_257_170_does_not_claim_actual_review_complete": True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_wrapper_only": True,
        "new_full_operation_helper_required_here": False,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CS01_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS01_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS02_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS01 current 262/84/257/170 basis refreeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS01_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS01_STEP_REF,
        source="P7-R54-AHR-CS01 current 262/84/257/170 basis refreeze",
    )
    if data.get("cs00_schema_version") != P7_R54_AHR_CS00_SCOPE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS01 CS00 schema version changed")
    if data.get("cs00_next_required_step") != P7_R54_AHR_CS01_STEP_REF:
        raise ValueError("P7-R54-AHR-CS01 CS00 next required step changed")
    if data.get("cs00_scope_boundary_confirmed") is not True or data.get("cs00_no_touch_boundary_confirmed") is not True:
        raise ValueError("P7-R54-AHR-CS01 CS00 boundary confirmation changed")
    if data.get("current_basis_status_ref") != P7_R54_AHR_CS_CURRENT_BASIS_STATUS_REF:
        raise ValueError("P7-R54-AHR-CS01 current basis status ref changed")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS01 current basis refreeze")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS01 current basis refreeze")
    _assert_true_fields(
        data,
        keys=(
            "current_basis_refrozen_here",
            "current_basis_refrozen_for_actual_review_reentry",
            "current_received_snapshot_refs_match_262_84_257_170",
            "current_262_84_257_170_does_not_claim_actual_review_complete",
            "current_basis_wrapper_only",
            "body_full_generation_blocked_until_later_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CS01 current basis refreeze",
    )
    _assert_false_fields(
        data,
        keys=(
            "new_full_operation_helper_required_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CS01 current basis refreeze",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS01_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS01 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS01_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS01 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CS02_STEP_REF:
        raise ValueError("P7-R54-AHR-CS01 next required step changed")
    return True




def build_p7_r54_ahr_cs02_historical_helper_refs_reconcile(
    *,
    current_snapshot_basis_refreeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CS02 body-free historical helper refs reconcile material."""

    cs01 = dict(current_snapshot_basis_refreeze or build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze())
    assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract(cs01)
    differing = _historical_helper_differing_current_basis_ref_keys()
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS02_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS02_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs02_historical_helper_refs_reconcile_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cs01.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs01_schema_version": cs01["schema_version"],
        "cs01_material_ref": cs01["material_id"],
        "cs01_next_required_step": cs01["next_required_step"],
        "cs01_current_basis_refrozen_here": cs01["current_basis_refrozen_here"],
        "cs01_current_basis_status_ref": cs01["current_basis_status_ref"],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "historical_helper_refs_reconcile_status_ref": P7_R54_AHR_CS_HISTORICAL_HELPER_RECONCILE_STATUS_REF,
        "historical_helper_refs_separated": True,
        "historical_helper_ref_groups": list(P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_ref_group_count": len(P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_refs": {key: dict(value) for key, value in P7_R54_AHR_CS_HISTORICAL_HELPER_REFS.items()},
        "historical_helper_ref_rows": _historical_helper_ref_rows(),
        "historical_helper_ref_row_count": len(P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS),
        "historical_helper_module_refs": dict(P7_R54_AHR_CS_HISTORICAL_HELPER_MODULE_REFS),
        "historical_helper_role_refs": dict(P7_R54_AHR_CS_HISTORICAL_HELPER_ROLE_REFS),
        "historical_helper_classification_refs": dict(P7_R54_AHR_CS_HISTORICAL_HELPER_CLASSIFICATION_REFS),
        "historical_helper_basis_refs": dict(P7_R54_AHR_CS_HISTORICAL_HELPER_BASIS_REFS),
        "historical_helper_refs_match_current_basis_262_84_257_170": {
            group_ref: False for group_ref in P7_R54_AHR_CS_HISTORICAL_HELPER_REF_GROUP_REFS
        },
        "historical_helper_differing_current_basis_ref_keys": differing,
        "historical_helper_differing_current_basis_ref_key_counts": {
            group_ref: len(keys) for group_ref, keys in differing.items()
        },
        "differing_current_basis_ref_group_count": len(differing),
        "historical_helper_green_claim_boundary_refs": list(
            P7_R54_AHR_CS_HISTORICAL_HELPER_GREEN_CLAIM_BOUNDARY_REFS
        ),
        "historical_helper_refs_are_historical_here": True,
        "historical_helper_refs_are_structural_refs_only": True,
        "historical_helper_refs_are_contract_refs_only": True,
        "historical_helper_refs_can_be_used_for_helper_regression_only": True,
        "existing_helper_refs_can_be_used_for_helper_regression_only": True,
        "historical_helper_refs_can_be_used_for_actual_review_basis": False,
        "historical_helper_refs_used_as_actual_review_basis": False,
        "historical_helper_refs_can_be_used_for_current_actual_review_evidence": False,
        "historical_helper_refs_used_as_current_actual_review_evidence": False,
        "historical_helper_output_used_as_current_actual_evidence": False,
        "helper_green_not_actual_human_review_complete": True,
        "synthetic_contract_rows_not_actual_review_rows": True,
        "r52_handoff_ready_contract_not_actual_r52_reintake_execution": True,
        "reconcile_does_not_modify_helper_modules": True,
        "existing_helper_constants_not_rewritten": True,
        "existing_helper_constants_rewritten": False,
        "existing_helper_refs_preserved_as_received": True,
        "current_refs_override_uses_thin_current_reentry_boundary_layer": True,
        "new_thin_boundary_helper_only": True,
        "new_full_operation_helper_required_here": False,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CS02_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS02_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS03_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS02 historical helper refs reconcile",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS02_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS02_STEP_REF,
        source="P7-R54-AHR-CS02 historical helper refs reconcile",
    )
    if data.get("cs01_schema_version") != P7_R54_AHR_CS01_CURRENT_SNAPSHOT_BASIS_REFREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS02 CS01 schema version changed")
    if data.get("cs01_next_required_step") != P7_R54_AHR_CS02_STEP_REF:
        raise ValueError("P7-R54-AHR-CS02 must follow CS01")
    if data.get("cs01_current_basis_refrozen_here") is not True:
        raise ValueError("P7-R54-AHR-CS02 CS01 current basis refreeze must be true")
    if data.get("cs01_current_basis_status_ref") != P7_R54_AHR_CS_CURRENT_BASIS_STATUS_REF:
        raise ValueError("P7-R54-AHR-CS02 CS01 current basis status changed")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS02 historical helper refs reconcile")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS02 historical helper refs reconcile")
    _assert_historical_helper_reconcile_fields(data, source="P7-R54-AHR-CS02 historical helper refs reconcile")
    _assert_true_fields(
        data,
        keys=(
            "historical_helper_refs_separated",
            "historical_helper_refs_are_historical_here",
            "historical_helper_refs_are_structural_refs_only",
            "historical_helper_refs_are_contract_refs_only",
            "historical_helper_refs_can_be_used_for_helper_regression_only",
            "existing_helper_refs_can_be_used_for_helper_regression_only",
            "helper_green_not_actual_human_review_complete",
            "synthetic_contract_rows_not_actual_review_rows",
            "r52_handoff_ready_contract_not_actual_r52_reintake_execution",
            "reconcile_does_not_modify_helper_modules",
            "existing_helper_constants_not_rewritten",
            "existing_helper_refs_preserved_as_received",
            "current_refs_override_uses_thin_current_reentry_boundary_layer",
            "new_thin_boundary_helper_only",
            "body_full_generation_blocked_until_later_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CS02 historical helper refs reconcile",
    )
    _assert_false_fields(
        data,
        keys=(
            "historical_helper_refs_can_be_used_for_actual_review_basis",
            "historical_helper_refs_used_as_actual_review_basis",
            "historical_helper_refs_can_be_used_for_current_actual_review_evidence",
            "historical_helper_refs_used_as_current_actual_review_evidence",
            "historical_helper_output_used_as_current_actual_evidence",
            "existing_helper_constants_rewritten",
            "new_full_operation_helper_required_here",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CS02 historical helper refs reconcile",
    )
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS02_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS02 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS02_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS02 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CS03_STEP_REF:
        raise ValueError("P7-R54-AHR-CS02 next required step changed")
    return True


def build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment(
    *,
    historical_helper_refs_reconcile: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CS03 body-free manifest / packet / evidence impact assessment material."""

    cs02 = dict(historical_helper_refs_reconcile or build_p7_r54_ahr_cs02_historical_helper_refs_reconcile())
    assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract(cs02)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS03_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS03_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cs02.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs02_schema_version": cs02["schema_version"],
        "cs02_material_ref": cs02["material_id"],
        "cs02_next_required_step": cs02["next_required_step"],
        "cs02_historical_helper_refs_separated": cs02["historical_helper_refs_separated"],
        "cs02_historical_helper_refs_used_as_current_actual_review_evidence": cs02[
            "historical_helper_refs_used_as_current_actual_review_evidence"
        ],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "historical_helper_refs_reconciled_before_impact_assessment": True,
        "manifest_packet_evidence_impact_assessed_here": True,
        "impact_target_refs": list(P7_R54_AHR_CS03_IMPACT_TARGET_REFS),
        "impact_target_ref_count": len(P7_R54_AHR_CS03_IMPACT_TARGET_REFS),
        "direct_file_diff_available": False,
        "direct_file_diff_executed": False,
        "direct_file_diff_not_available_reason_ref": P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_REASON_REF,
        "diff_impact_status_ref": P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF,
        "diff_impact_status_allowed_refs": list(P7_R54_AHR_CS03_DIFF_IMPACT_STATUS_REFS),
        "direct_diff_cannot_claim_no_impact": True,
        "diff_unavailable_does_not_equal_no_impact": True,
        "review_manifest_impact_unknown_until_current_manifest_refreeze": True,
        "current_manifest_refreeze_required": True,
        "current_manifest_refreeze_required_reason_ref": P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF,
        "old_manifest_allowed_as_current_manifest": False,
        "old_manifest_allowed_as_structural_ref": True,
        "old_manifest_unconditional_adoption_blocked": True,
        "old_packet_boundary_allowed_as_current_packet_boundary": False,
        "old_evidence_rows_allowed_as_current_actual_review_rows": False,
        "current_24_case_manifest_must_be_refrozen_next": True,
        "body_full_diff_content_included": False,
        "raw_diff_body_included": False,
        "local_file_path_included": False,
        "terminal_output_body_included": False,
        "body_full_generation_blocked_until_later_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CS03_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS03_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS04_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS03 manifest/packet/evidence impact assessment",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS03_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS03_STEP_REF,
        source="P7-R54-AHR-CS03 manifest/packet/evidence impact assessment",
    )
    if data.get("cs02_schema_version") != P7_R54_AHR_CS02_HISTORICAL_HELPER_REFS_RECONCILE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS03 CS02 schema version changed")
    if data.get("cs02_next_required_step") != P7_R54_AHR_CS03_STEP_REF:
        raise ValueError("P7-R54-AHR-CS03 must follow CS02")
    if data.get("cs02_historical_helper_refs_separated") is not True:
        raise ValueError("P7-R54-AHR-CS03 CS02 separated flag changed")
    if data.get("cs02_historical_helper_refs_used_as_current_actual_review_evidence") is not False:
        raise ValueError("P7-R54-AHR-CS03 cannot use historical refs as current actual evidence")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS03 impact assessment")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS03 impact assessment")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS03 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS03 historical basis ref changed")
    if tuple(data.get("impact_target_refs") or ()) != P7_R54_AHR_CS03_IMPACT_TARGET_REFS:
        raise ValueError("P7-R54-AHR-CS03 impact target refs changed")
    if data.get("impact_target_ref_count") != len(P7_R54_AHR_CS03_IMPACT_TARGET_REFS):
        raise ValueError("P7-R54-AHR-CS03 impact target count changed")
    _assert_true_fields(
        data,
        keys=(
            "historical_helper_refs_reconciled_before_impact_assessment",
            "manifest_packet_evidence_impact_assessed_here",
            "direct_diff_cannot_claim_no_impact",
            "diff_unavailable_does_not_equal_no_impact",
            "review_manifest_impact_unknown_until_current_manifest_refreeze",
            "current_manifest_refreeze_required",
            "old_manifest_allowed_as_structural_ref",
            "old_manifest_unconditional_adoption_blocked",
            "current_24_case_manifest_must_be_refrozen_next",
            "body_full_generation_blocked_until_later_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CS03 impact assessment",
    )
    _assert_false_fields(
        data,
        keys=(
            "direct_file_diff_available",
            "direct_file_diff_executed",
            "old_manifest_allowed_as_current_manifest",
            "old_packet_boundary_allowed_as_current_packet_boundary",
            "old_evidence_rows_allowed_as_current_actual_review_rows",
            "body_full_diff_content_included",
            "raw_diff_body_included",
            "local_file_path_included",
            "terminal_output_body_included",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CS03 impact assessment",
    )
    if data.get("direct_file_diff_not_available_reason_ref") != P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_REASON_REF:
        raise ValueError("P7-R54-AHR-CS03 direct diff unavailable reason changed")
    if data.get("diff_impact_status_ref") != P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF:
        raise ValueError("P7-R54-AHR-CS03 diff impact status changed")
    if tuple(data.get("diff_impact_status_allowed_refs") or ()) != P7_R54_AHR_CS03_DIFF_IMPACT_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS03 diff impact allowed refs changed")
    if data.get("current_manifest_refreeze_required_reason_ref") != P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF:
        raise ValueError("P7-R54-AHR-CS03 manifest refreeze reason changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS03_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS03 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS03_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS03 not-yet implemented steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CS04_STEP_REF:
        raise ValueError("P7-R54-AHR-CS03 next required step changed")
    return True


# Compatibility aliases for the user-facing CS01 title and prior design wording.
build_p7_r54_ahr_cs01_current_262_84_257_170_basis_envelope = build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze
assert_p7_r54_ahr_cs01_current_262_84_257_170_basis_envelope_contract = (
    assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_scope_no_touch_boundary_freeze_bodyfree = (
    build_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_scope_no_touch_boundary_freeze_bodyfree_contract = (
    assert_p7_r54_ahr_cs00_scope_no_touch_boundary_freeze_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_current_snapshot_basis_refreeze_bodyfree = (
    build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_current_snapshot_basis_refreeze_bodyfree_contract = (
    assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_current_basis_envelope_bodyfree = (
    build_p7_r54_ahr_cs01_current_snapshot_basis_refreeze
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_current_basis_envelope_bodyfree_contract = (
    assert_p7_r54_ahr_cs01_current_snapshot_basis_refreeze_contract
)


# Compatibility aliases for CS02/CS03 design wording.
build_p7_r54_ahr_current_snapshot_actual_review_reentry_historical_helper_refs_reconcile_bodyfree = (
    build_p7_r54_ahr_cs02_historical_helper_refs_reconcile
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_historical_helper_refs_reconcile_bodyfree_contract = (
    assert_p7_r54_ahr_cs02_historical_helper_refs_reconcile_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_manifest_packet_evidence_impact_assessment_bodyfree = (
    build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_manifest_packet_evidence_impact_assessment_bodyfree_contract = (
    assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract
)


# CS04/CS05 current-snapshot re-entry materialization.
# These helpers are intentionally appended as a thin current wrapper so that the
# existing 2026-06-27 AHR helper remains a historical / structural / regression
# reference and is not rewritten or relabelled as current evidence.
P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs04_current_24_case_manifest_refreeze.bodyfree.v1"
)
P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs05_local_only_preflight.bodyfree.v1"
)
P7_R54_AHR_CS_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION
)
P7_R54_AHR_CS_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION: Final = P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION

P7_R54_AHR_CS04_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS03_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS04_STEP_REF,
)
P7_R54_AHR_CS04_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[5:]
P7_R54_AHR_CS05_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS04_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS05_STEP_REF,
)
P7_R54_AHR_CS05_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[6:]

P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT: Final = historical_ahr.P7_R54_AHR_R55_REQUIRED_ACTUAL_REVIEW_CASE_COUNT

P7_R54_AHR_CS04_MANIFEST_REFROZEN_STATUS_REF: Final = (
    "CURRENT_24_CASE_MANIFEST_REFROZEN_BODYFREE_READY_FOR_LOCAL_ONLY_PREFLIGHT"
)
P7_R54_AHR_CS04_MANIFEST_BLOCKED_STATUS_REF: Final = (
    "CURRENT_24_CASE_MANIFEST_BLOCKED_BY_CURRENT_BASIS_OR_ROW_CONTRACT"
)
P7_R54_AHR_CS04_READY_REASON_REF: Final = (
    "r54_ahr_cs_current_24_case_manifest_refrozen_bodyfree_for_current_262_84_257_170"
)
P7_R54_AHR_CS04_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS04_repair_current_24_case_manifest_refreeze_before_local_only_preflight"
)
P7_R54_AHR_CS04_MANIFEST_SOURCE_KIND_REF: Final = (
    "current_262_84_257_170_bodyfree_manifest_refreeze_from_r54_ahr_structural_distribution"
)
P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF: Final = "r54_ahr_p5_history_line_6_axis_profile_current_20260628"
P7_R54_AHR_CS04_CASE_DISTRIBUTION: Final[dict[str, int]] = dict(historical_ahr.P7_R54_AHR05_CASE_DISTRIBUTION)
P7_R54_AHR_CS04_CASE_ROLE_BY_FAMILY: Final[dict[str, str]] = dict(historical_ahr.P7_R54_AHR05_CASE_ROLE_BY_FAMILY)
P7_R54_AHR_CS04_CURRENT_ONLY_BOUNDARY_FAMILY_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR05_CURRENT_ONLY_BOUNDARY_FAMILY_REFS
)
P7_R54_AHR_CS04_RATING_AXIS_REFS: Final[tuple[str, ...]] = tuple(historical_ahr.P7_R54_AHR05_RATING_AXIS_REFS)
P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS: Final[dict[str, float]] = dict(
    historical_ahr.P7_R54_AHR05_RATING_AXIS_TARGET_THRESHOLDS
)
P7_R54_AHR_CS04_CASE_MANIFEST_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs04_case_manifest_row.bodyfree.v1"
)
P7_R54_AHR_CS04_CASE_MANIFEST_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "case_index",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "subscription_tier_ref",
    "history_evidence_policy_ref",
    "review_axis_profile_ref",
    "current_basis_ref",
    "historical_manifest_allowed_as_structural_ref",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "requires_history_line_review",
    "current_only_boundary_case",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_free",
)

P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF: Final = (
    "LOCAL_ONLY_PREFLIGHT_READY_FOR_PACKET_GENERATION_REQUEST_BRIDGE"
)
P7_R54_AHR_CS05_PREFLIGHT_BLOCKED_STATUS_REF: Final = (
    "LOCAL_ONLY_PREFLIGHT_BLOCKED_BEFORE_PACKET_GENERATION_REQUEST_BRIDGE"
)
P7_R54_AHR_CS05_ALLOWED_PREFLIGHT_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF,
    P7_R54_AHR_CS05_PREFLIGHT_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS05_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS05_repair_local_only_preflight_before_packet_generation_request"
)
P7_R54_AHR_CS05_READY_REASON_REF: Final = (
    "r54_ahr_cs_local_only_preflight_ready_for_packet_generation_request_boundary"
)
P7_R54_AHR_CS05_EXPLICIT_LOCAL_ONLY_ALLOW_REF: Final = "R54_AHR_CS_EXPLICIT_LOCAL_ONLY_ALLOW_PRESENT"
P7_R54_AHR_CS05_LOCAL_REVIEW_ROOT_AVAILABLE_REF: Final = "R54_AHR_CS_LOCAL_REVIEW_ROOT_AVAILABLE_REF_ONLY"
P7_R54_AHR_CS05_EXPORT_DENYLIST_READY_REF: Final = "R54_AHR_CS_EXPORT_DENYLIST_READY"
P7_R54_AHR_CS05_PURGE_PLAN_READY_REF: Final = "R54_AHR_CS_BODY_FULL_PACKET_PURGE_PLAN_READY"
P7_R54_AHR_CS05_REVIEW_SESSION_PRESENT_REF: Final = "R54_AHR_CS_REVIEW_SESSION_ID_PRESENT"
P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS: Final[tuple[str, ...]] = tuple(historical_ahr.P7_R54_AHR04_EXPORT_DENYLIST_REFS)
P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS: Final[tuple[str, ...]] = tuple(historical_ahr.P7_R54_AHR04_FORBIDDEN_OUTPUT_REFS)

P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs03_schema_version",
    "cs03_material_ref",
    "cs03_next_required_step",
    "cs03_current_manifest_refreeze_required",
    "cs03_old_manifest_allowed_as_current_manifest",
    "cs03_diff_impact_status_ref",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "manifest_source_kind_ref",
    "manifest_refreeze_status_ref",
    "manifest_refreeze_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "required_case_count",
    "manifest_row_count",
    "case_distribution",
    "case_distribution_total_count",
    "case_distribution_matches_design",
    "case_manifest_rows",
    "case_manifest_rows_bodyfree_only",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "blind_case_id_case_ref_separated",
    "blind_case_id_packet_ref_separated",
    "case_ref_id_packet_ref_separated",
    "case_family_counts",
    "case_role_counts",
    "subscription_tier_ref_counts",
    "history_evidence_policy_ref_counts",
    "review_axis_profile_ref",
    "rating_axis_refs",
    "rating_axis_count",
    "required_rating_axis_count",
    "rating_axis_target_thresholds",
    "all_case_rows_current_basis_ref",
    "requires_history_line_review_count",
    "current_only_boundary_case_count",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "current_24_case_manifest_refrozen_here",
    "current_24_case_manifest_frozen",
    "current_manifest_refreeze_uses_current_262_84_257_170_basis",
    "old_manifest_used_as_current_manifest",
    "historical_manifest_used_as_current_manifest",
    "body_full_packet_generation_request_allowed_next",
    "body_full_generation_blocked_until_local_only_preflight",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs04_schema_version",
    "cs04_material_ref",
    "cs04_next_required_step",
    "cs04_manifest_refreeze_status_ref",
    "cs04_current_24_case_manifest_frozen",
    "cs04_manifest_row_count",
    "cs04_case_ref_ids_unique",
    "cs04_blind_case_ids_unique",
    "cs04_packet_ref_ids_unique",
    "cs04_body_full_packet_materialized_here",
    "cs04_local_reviewer_payload_materialized_here",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "current_24_case_manifest_frozen",
    "required_case_count",
    "manifest_row_count",
    "case_ref_id_count",
    "blind_case_id_count",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "review_session_id_present_ref",
    "review_session_id_present",
    "explicit_local_only_allow_ref",
    "explicit_local_only_allow_present",
    "local_review_root_available_ref",
    "local_review_root_available_ref_present",
    "local_review_root_is_ref_only",
    "export_denylist_ready_ref",
    "export_denylist_ready",
    "export_denylist_refs",
    "export_denylist_ref_count",
    "forbidden_output_refs",
    "forbidden_output_ref_count",
    "purge_plan_ready_ref",
    "purge_plan_ready",
    "local_only",
    "must_not_export",
    "disposal_required",
    "local_only_preflight_status_ref",
    "local_only_preflight_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "local_only_preflight_ready",
    "body_full_packet_generation_blocked_before_preflight",
    "body_full_generation_blocked_until_preflight_ready",
    "body_full_packet_generation_allowed_before_preflight",
    "body_full_packet_generation_allowed_by_preflight",
    "body_full_packet_generation_request_allowed_next",
    "body_full_packet_generation_performed_here",
    "body_full_packet_exported_here_ref",
    "body_full_packet_content_included_in_preflight",
    "actual_review_execution_blocked_until_packet_generation_receipt",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS
)


def _cs_unique_non_empty(values: Sequence[Any], *, required_count: int) -> bool:
    cleaned = [clean_identifier(value, max_length=180) for value in values]
    return len(cleaned) == required_count and all(cleaned) and len(set(cleaned)) == required_count


def _cs_count_by(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        item = clean_identifier(row.get(key), max_length=180)
        counts[item] = counts.get(item, 0) + 1
    return counts


def _cs_dedupe_identifiers(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _cs04_subscription_tier_ref(case_family_ref: str) -> str:
    if case_family_ref == "free_tier_history_present_not_allowed":
        return "tier_free_history_not_exposed_boundary"
    if case_family_ref == "low_information_history_not_eligible":
        return "tier_hidden_current_only_boundary"
    return "tier_paid_or_premium_owned_history_context_ref"


def _cs04_history_evidence_policy_ref(case_family_ref: str) -> str:
    if case_family_ref == "free_tier_history_present_not_allowed":
        return "owned_history_present_but_not_allowed_by_tier_boundary"
    if case_family_ref == "low_information_history_not_eligible":
        return "history_not_eligible_current_only_boundary"
    return "bounded_owned_history_local_only_review_surface"


def _cs04_default_case_manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 1
    for case_family_ref, count in P7_R54_AHR_CS04_CASE_DISTRIBUTION.items():
        case_role_ref = P7_R54_AHR_CS04_CASE_ROLE_BY_FAMILY[case_family_ref]
        for _ in range(count):
            current_only = case_family_ref in P7_R54_AHR_CS04_CURRENT_ONLY_BOUNDARY_FAMILY_REFS
            rows.append(
                {
                    "schema_version": P7_R54_AHR_CS04_CASE_MANIFEST_ROW_SCHEMA_VERSION,
                    "case_index": index,
                    "case_ref_id": f"r54_ahr_cs_case_{index:03d}",
                    "blind_case_id": f"r54_ahr_cs_blind_case_{index:03d}",
                    "packet_ref_id": f"r54_ahr_cs_packet_ref_{index:03d}",
                    "case_family_ref": case_family_ref,
                    "case_role_ref": case_role_ref,
                    "subscription_tier_ref": _cs04_subscription_tier_ref(case_family_ref),
                    "history_evidence_policy_ref": _cs04_history_evidence_policy_ref(case_family_ref),
                    "review_axis_profile_ref": P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF,
                    "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                    "historical_manifest_allowed_as_structural_ref": True,
                    "reviewer_facing_family_exposed": False,
                    "reviewer_facing_tier_exposed": False,
                    "requires_history_line_review": not current_only,
                    "current_only_boundary_case": current_only,
                    "body_full_packet_materialized_here": False,
                    "local_reviewer_payload_materialized_here": False,
                    "body_free": True,
                }
            )
            index += 1
    return rows


def _assert_cs04_case_manifest_row(row: Mapping[str, Any], *, expected_index: int) -> None:
    _assert_required_fields(
        row,
        required=P7_R54_AHR_CS04_CASE_MANIFEST_ROW_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS04 case manifest row",
    )
    expected_case_ref_id = f"r54_ahr_cs_case_{expected_index:03d}"
    expected_blind_case_id = f"r54_ahr_cs_blind_case_{expected_index:03d}"
    expected_packet_ref_id = f"r54_ahr_cs_packet_ref_{expected_index:03d}"
    if row.get("schema_version") != P7_R54_AHR_CS04_CASE_MANIFEST_ROW_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS04 row schema version changed")
    if row.get("case_index") != expected_index:
        raise ValueError("P7-R54-AHR-CS04 case index changed")
    if row.get("case_ref_id") != expected_case_ref_id:
        raise ValueError("P7-R54-AHR-CS04 case ref id changed")
    if row.get("blind_case_id") != expected_blind_case_id:
        raise ValueError("P7-R54-AHR-CS04 blind case id changed")
    if row.get("packet_ref_id") != expected_packet_ref_id:
        raise ValueError("P7-R54-AHR-CS04 packet ref id changed")
    case_family_ref = clean_identifier(row.get("case_family_ref"), max_length=180)
    if case_family_ref not in P7_R54_AHR_CS04_CASE_DISTRIBUTION:
        raise ValueError("P7-R54-AHR-CS04 unknown case family ref")
    if row.get("case_role_ref") != P7_R54_AHR_CS04_CASE_ROLE_BY_FAMILY[case_family_ref]:
        raise ValueError("P7-R54-AHR-CS04 case role ref changed")
    if row.get("subscription_tier_ref") != _cs04_subscription_tier_ref(case_family_ref):
        raise ValueError("P7-R54-AHR-CS04 tier ref changed")
    if row.get("history_evidence_policy_ref") != _cs04_history_evidence_policy_ref(case_family_ref):
        raise ValueError("P7-R54-AHR-CS04 history policy ref changed")
    if row.get("review_axis_profile_ref") != P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF:
        raise ValueError("P7-R54-AHR-CS04 review axis profile changed")
    if row.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS04 row current basis ref changed")
    if row.get("historical_manifest_allowed_as_structural_ref") is not True:
        raise ValueError("P7-R54-AHR-CS04 row must keep historical manifest structural-only")
    current_only = case_family_ref in P7_R54_AHR_CS04_CURRENT_ONLY_BOUNDARY_FAMILY_REFS
    if row.get("requires_history_line_review") is not (not current_only):
        raise ValueError("P7-R54-AHR-CS04 history-line review flag changed")
    if row.get("current_only_boundary_case") is not current_only:
        raise ValueError("P7-R54-AHR-CS04 current-only boundary flag changed")
    for key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
    ):
        if row.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS04 row must keep {key}=False")
    if row.get("body_free") is not True:
        raise ValueError("P7-R54-AHR-CS04 row must remain body-free")
    if _contains_forbidden_body_or_question_key(row):
        raise ValueError("P7-R54-AHR-CS04 row contains forbidden body/question/path/hash key")


def build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze(
    *,
    manifest_packet_evidence_impact_assessment: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CS04 current 24-case manifest refreeze body-free material."""

    cs03 = dict(
        manifest_packet_evidence_impact_assessment
        or build_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment()
    )
    assert_p7_r54_ahr_cs03_manifest_packet_evidence_impact_assessment_contract(cs03)
    rows = _cs04_default_case_manifest_rows()
    case_refs = [row["case_ref_id"] for row in rows]
    blind_ids = [row["blind_case_id"] for row in rows]
    packet_refs = [row["packet_ref_id"] for row in rows]
    required_count = P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    case_family_counts = _cs_count_by(rows, "case_family_ref")
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS04_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS04_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs04_current_24_case_manifest_refreeze_20260628",
        "review_session_id": _safe_review_session_id(review_session_id or cs03.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs03_schema_version": cs03["schema_version"],
        "cs03_material_ref": cs03["material_id"],
        "cs03_next_required_step": cs03["next_required_step"],
        "cs03_current_manifest_refreeze_required": cs03["current_manifest_refreeze_required"],
        "cs03_old_manifest_allowed_as_current_manifest": cs03["old_manifest_allowed_as_current_manifest"],
        "cs03_diff_impact_status_ref": cs03["diff_impact_status_ref"],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "manifest_source_kind_ref": P7_R54_AHR_CS04_MANIFEST_SOURCE_KIND_REF,
        "manifest_refreeze_status_ref": P7_R54_AHR_CS04_MANIFEST_REFROZEN_STATUS_REF,
        "manifest_refreeze_reason_refs": [P7_R54_AHR_CS04_READY_REASON_REF],
        "execution_blocker_ids": [],
        "open_execution_blocker_ids": [],
        "required_case_count": required_count,
        "manifest_row_count": len(rows),
        "case_distribution": dict(P7_R54_AHR_CS04_CASE_DISTRIBUTION),
        "case_distribution_total_count": sum(P7_R54_AHR_CS04_CASE_DISTRIBUTION.values()),
        "case_distribution_matches_design": case_family_counts == P7_R54_AHR_CS04_CASE_DISTRIBUTION,
        "case_manifest_rows": rows,
        "case_manifest_rows_bodyfree_only": all(row.get("body_free") is True for row in rows),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": _cs_unique_non_empty(case_refs, required_count=required_count),
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": _cs_unique_non_empty(blind_ids, required_count=required_count),
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": _cs_unique_non_empty(packet_refs, required_count=required_count),
        "blind_case_id_case_ref_separated": set(blind_ids).isdisjoint(case_refs),
        "blind_case_id_packet_ref_separated": set(blind_ids).isdisjoint(packet_refs),
        "case_ref_id_packet_ref_separated": set(case_refs).isdisjoint(packet_refs),
        "case_family_counts": case_family_counts,
        "case_role_counts": _cs_count_by(rows, "case_role_ref"),
        "subscription_tier_ref_counts": _cs_count_by(rows, "subscription_tier_ref"),
        "history_evidence_policy_ref_counts": _cs_count_by(rows, "history_evidence_policy_ref"),
        "review_axis_profile_ref": P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF,
        "rating_axis_refs": list(P7_R54_AHR_CS04_RATING_AXIS_REFS),
        "rating_axis_count": len(P7_R54_AHR_CS04_RATING_AXIS_REFS),
        "required_rating_axis_count": 6,
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS),
        "all_case_rows_current_basis_ref": all(
            row.get("current_basis_ref") == P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF for row in rows
        ),
        "requires_history_line_review_count": sum(1 for row in rows if row["requires_history_line_review"] is True),
        "current_only_boundary_case_count": sum(1 for row in rows if row["current_only_boundary_case"] is True),
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "current_24_case_manifest_refrozen_here": True,
        "current_24_case_manifest_frozen": True,
        "current_manifest_refreeze_uses_current_262_84_257_170_basis": True,
        "old_manifest_used_as_current_manifest": False,
        "historical_manifest_used_as_current_manifest": False,
        "body_full_packet_generation_request_allowed_next": False,
        "body_full_generation_blocked_until_local_only_preflight": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CS04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS04_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS05_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS04 current 24-case manifest refreeze",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS04_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS04_STEP_REF,
        source="P7-R54-AHR-CS04 current 24-case manifest refreeze",
    )
    if data.get("cs03_schema_version") != P7_R54_AHR_CS03_MANIFEST_PACKET_EVIDENCE_IMPACT_ASSESSMENT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS04 CS03 schema version changed")
    if data.get("cs03_next_required_step") != P7_R54_AHR_CS04_STEP_REF:
        raise ValueError("P7-R54-AHR-CS04 must follow CS03")
    if data.get("cs03_current_manifest_refreeze_required") is not True:
        raise ValueError("P7-R54-AHR-CS04 requires CS03 manifest refreeze requirement")
    if data.get("cs03_old_manifest_allowed_as_current_manifest") is not False:
        raise ValueError("P7-R54-AHR-CS04 cannot adopt old manifest")
    if data.get("cs03_diff_impact_status_ref") != P7_R54_AHR_CS03_DIRECT_DIFF_NOT_AVAILABLE_STATUS_REF:
        raise ValueError("P7-R54-AHR-CS04 CS03 diff status changed")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS04 manifest refreeze")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS04 manifest refreeze")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS04 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS04 historical basis ref changed")
    if data.get("manifest_source_kind_ref") != P7_R54_AHR_CS04_MANIFEST_SOURCE_KIND_REF:
        raise ValueError("P7-R54-AHR-CS04 manifest source kind changed")
    if data.get("manifest_refreeze_status_ref") != P7_R54_AHR_CS04_MANIFEST_REFROZEN_STATUS_REF:
        raise ValueError("P7-R54-AHR-CS04 manifest refreeze status changed")
    if data.get("manifest_refreeze_reason_refs") != [P7_R54_AHR_CS04_READY_REASON_REF]:
        raise ValueError("P7-R54-AHR-CS04 manifest reason refs changed")
    if data.get("execution_blocker_ids") != [] or data.get("open_execution_blocker_ids") != []:
        raise ValueError("P7-R54-AHR-CS04 must not carry execution blockers")
    if data.get("required_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS04 required case count changed")
    if data.get("manifest_row_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS04 manifest row count changed")
    if data.get("case_distribution") != P7_R54_AHR_CS04_CASE_DISTRIBUTION:
        raise ValueError("P7-R54-AHR-CS04 case distribution changed")
    if data.get("case_distribution_total_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS04 case distribution total changed")
    rows = data.get("case_manifest_rows")
    if not isinstance(rows, list) or len(rows) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS04 case manifest rows changed")
    for expected_index, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-CS04 case manifest row must be a mapping")
        _assert_cs04_case_manifest_row(row, expected_index=expected_index)
    case_refs = [row["case_ref_id"] for row in rows]
    blind_ids = [row["blind_case_id"] for row in rows]
    packet_refs = [row["packet_ref_id"] for row in rows]
    if data.get("case_ref_ids") != case_refs:
        raise ValueError("P7-R54-AHR-CS04 case ref list changed")
    if data.get("blind_case_ids") != blind_ids:
        raise ValueError("P7-R54-AHR-CS04 blind id list changed")
    if data.get("packet_ref_ids") != packet_refs:
        raise ValueError("P7-R54-AHR-CS04 packet ref list changed")
    if data.get("case_family_counts") != _cs_count_by(rows, "case_family_ref"):
        raise ValueError("P7-R54-AHR-CS04 case family counts changed")
    if data.get("case_role_counts") != _cs_count_by(rows, "case_role_ref"):
        raise ValueError("P7-R54-AHR-CS04 case role counts changed")
    if data.get("subscription_tier_ref_counts") != _cs_count_by(rows, "subscription_tier_ref"):
        raise ValueError("P7-R54-AHR-CS04 tier counts changed")
    if data.get("history_evidence_policy_ref_counts") != _cs_count_by(rows, "history_evidence_policy_ref"):
        raise ValueError("P7-R54-AHR-CS04 history policy counts changed")
    _assert_true_fields(
        data,
        keys=(
            "case_distribution_matches_design",
            "case_manifest_rows_bodyfree_only",
            "case_ref_ids_unique",
            "blind_case_ids_unique",
            "packet_ref_ids_unique",
            "blind_case_id_case_ref_separated",
            "blind_case_id_packet_ref_separated",
            "case_ref_id_packet_ref_separated",
            "all_case_rows_current_basis_ref",
            "current_24_case_manifest_refrozen_here",
            "current_24_case_manifest_frozen",
            "current_manifest_refreeze_uses_current_262_84_257_170_basis",
            "body_full_generation_blocked_until_local_only_preflight",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CS04 manifest refreeze",
    )
    _assert_false_fields(
        data,
        keys=(
            "reviewer_facing_family_exposed",
            "reviewer_facing_tier_exposed",
            "body_full_packet_materialized_here",
            "local_reviewer_payload_materialized_here",
            "old_manifest_used_as_current_manifest",
            "historical_manifest_used_as_current_manifest",
            "body_full_packet_generation_request_allowed_next",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CS04 manifest refreeze",
    )
    if data.get("case_ref_id_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS04 case ref count changed")
    if data.get("blind_case_id_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS04 blind case id count changed")
    if data.get("packet_ref_id_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS04 packet ref count changed")
    if tuple(data.get("rating_axis_refs") or ()) != P7_R54_AHR_CS04_RATING_AXIS_REFS:
        raise ValueError("P7-R54-AHR-CS04 rating axis refs changed")
    if data.get("rating_axis_count") != 6 or data.get("required_rating_axis_count") != 6:
        raise ValueError("P7-R54-AHR-CS04 rating axis count changed")
    if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS:
        raise ValueError("P7-R54-AHR-CS04 rating axis thresholds changed")
    if data.get("requires_history_line_review_count") != 20:
        raise ValueError("P7-R54-AHR-CS04 history-line count changed")
    if data.get("current_only_boundary_case_count") != 4:
        raise ValueError("P7-R54-AHR-CS04 current-only count changed")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS04_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS04 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS04_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS04 not-yet steps changed")
    if data.get("next_required_step") != P7_R54_AHR_CS05_STEP_REF:
        raise ValueError("P7-R54-AHR-CS04 next required step changed")
    return True


def _cs05_preflight_status_and_blockers(
    *,
    explicit_local_only_allow_present: bool,
    local_review_root_available_ref_present: bool,
    export_denylist_ready: bool,
    purge_plan_ready: bool,
    review_session_id_present: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not explicit_local_only_allow_present:
        blockers.append("explicit_local_only_allow_missing")
    if not local_review_root_available_ref_present:
        blockers.append("local_review_root_ref_missing")
    if not export_denylist_ready:
        blockers.append("export_denylist_not_ready")
    if not purge_plan_ready:
        blockers.append("purge_plan_not_ready")
    if not review_session_id_present:
        blockers.append("review_session_id_missing")
    if blockers:
        return P7_R54_AHR_CS05_PREFLIGHT_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF, [P7_R54_AHR_CS05_READY_REASON_REF], []


def build_p7_r54_ahr_cs05_local_only_preflight(
    *,
    current_24_case_manifest_refreeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    explicit_local_only_allow_ref: Any = None,
    local_review_root_available_ref: Any = None,
    export_denylist_ready_ref: Any = None,
    purge_plan_ready_ref: Any = None,
) -> dict[str, Any]:
    """Build CS05 local-only preflight body-free material."""

    cs04 = dict(current_24_case_manifest_refreeze or build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze())
    assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(cs04)
    session_id = _safe_review_session_id(review_session_id or cs04.get("review_session_id"))
    explicit_allow_ref = clean_identifier(
        explicit_local_only_allow_ref or P7_R54_AHR_CS05_EXPLICIT_LOCAL_ONLY_ALLOW_REF,
        max_length=180,
    )
    local_root_ref = clean_identifier(
        local_review_root_available_ref or P7_R54_AHR_CS05_LOCAL_REVIEW_ROOT_AVAILABLE_REF,
        max_length=180,
    )
    export_ready_ref = clean_identifier(
        export_denylist_ready_ref or P7_R54_AHR_CS05_EXPORT_DENYLIST_READY_REF,
        max_length=180,
    )
    purge_ready_ref = clean_identifier(
        purge_plan_ready_ref or P7_R54_AHR_CS05_PURGE_PLAN_READY_REF,
        max_length=180,
    )
    explicit_present = explicit_allow_ref == P7_R54_AHR_CS05_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    local_root_present = local_root_ref == P7_R54_AHR_CS05_LOCAL_REVIEW_ROOT_AVAILABLE_REF
    export_ready = export_ready_ref == P7_R54_AHR_CS05_EXPORT_DENYLIST_READY_REF
    purge_ready = purge_ready_ref == P7_R54_AHR_CS05_PURGE_PLAN_READY_REF
    session_present = bool(session_id)
    status_ref, reason_or_blocker_refs, blockers = _cs05_preflight_status_and_blockers(
        explicit_local_only_allow_present=explicit_present,
        local_review_root_available_ref_present=local_root_present,
        export_denylist_ready=export_ready,
        purge_plan_ready=purge_ready,
        review_session_id_present=session_present,
    )
    preflight_ready = status_ref == P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS05_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS05_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs05_local_only_preflight_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs04_schema_version": cs04["schema_version"],
        "cs04_material_ref": cs04["material_id"],
        "cs04_next_required_step": cs04["next_required_step"],
        "cs04_manifest_refreeze_status_ref": cs04["manifest_refreeze_status_ref"],
        "cs04_current_24_case_manifest_frozen": cs04["current_24_case_manifest_frozen"],
        "cs04_manifest_row_count": cs04["manifest_row_count"],
        "cs04_case_ref_ids_unique": cs04["case_ref_ids_unique"],
        "cs04_blind_case_ids_unique": cs04["blind_case_ids_unique"],
        "cs04_packet_ref_ids_unique": cs04["packet_ref_ids_unique"],
        "cs04_body_full_packet_materialized_here": cs04["body_full_packet_materialized_here"],
        "cs04_local_reviewer_payload_materialized_here": cs04["local_reviewer_payload_materialized_here"],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "current_24_case_manifest_frozen": True,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "manifest_row_count": cs04["manifest_row_count"],
        "case_ref_id_count": cs04["case_ref_id_count"],
        "blind_case_id_count": cs04["blind_case_id_count"],
        "packet_ref_id_count": cs04["packet_ref_id_count"],
        "packet_ref_ids_unique": cs04["packet_ref_ids_unique"],
        "review_session_id_present_ref": P7_R54_AHR_CS05_REVIEW_SESSION_PRESENT_REF,
        "review_session_id_present": session_present,
        "explicit_local_only_allow_ref": explicit_allow_ref,
        "explicit_local_only_allow_present": explicit_present,
        "local_review_root_available_ref": local_root_ref,
        "local_review_root_available_ref_present": local_root_present,
        "local_review_root_is_ref_only": True,
        "export_denylist_ready_ref": export_ready_ref,
        "export_denylist_ready": export_ready,
        "export_denylist_refs": list(P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS),
        "forbidden_output_refs": list(P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS),
        "purge_plan_ready_ref": purge_ready_ref,
        "purge_plan_ready": purge_ready,
        "local_only": True,
        "must_not_export": True,
        "disposal_required": True,
        "local_only_preflight_status_ref": status_ref,
        "local_only_preflight_reason_refs": reason_or_blocker_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "local_only_preflight_ready": preflight_ready,
        "body_full_packet_generation_blocked_before_preflight": True,
        "body_full_generation_blocked_until_preflight_ready": True,
        "body_full_packet_generation_allowed_before_preflight": False,
        "body_full_packet_generation_allowed_by_preflight": preflight_ready,
        "body_full_packet_generation_request_allowed_next": preflight_ready,
        "body_full_packet_generation_performed_here": False,
        "body_full_packet_exported_here_ref": "BODY_FULL_PACKET_NOT_EXPORTED_HERE",
        "body_full_packet_content_included_in_preflight": False,
        "actual_review_execution_blocked_until_packet_generation_receipt": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CS05_IMPLEMENTED_STEPS if preflight_ready else P7_R54_AHR_CS04_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CS05_NOT_YET_IMPLEMENTED_STEPS if preflight_ready else P7_R54_AHR_CS04_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CS06_STEP_REF if preflight_ready else P7_R54_AHR_CS05_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs05_local_only_preflight_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS05 local-only preflight",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS05_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS05_STEP_REF,
        source="P7-R54-AHR-CS05 local-only preflight",
    )
    if data.get("cs04_schema_version") != P7_R54_AHR_CS04_CURRENT_24_CASE_MANIFEST_REFREEZE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS05 CS04 schema changed")
    if data.get("cs04_next_required_step") != P7_R54_AHR_CS05_STEP_REF:
        raise ValueError("P7-R54-AHR-CS05 must follow CS04")
    if data.get("cs04_manifest_refreeze_status_ref") != P7_R54_AHR_CS04_MANIFEST_REFROZEN_STATUS_REF:
        raise ValueError("P7-R54-AHR-CS05 requires frozen CS04 manifest status")
    if data.get("cs04_current_24_case_manifest_frozen") is not True:
        raise ValueError("P7-R54-AHR-CS05 requires CS04 current manifest frozen")
    if data.get("cs04_manifest_row_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS05 CS04 manifest count changed")
    for key in ("cs04_case_ref_ids_unique", "cs04_blind_case_ids_unique", "cs04_packet_ref_ids_unique"):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-CS05 requires {key}=True")
    if data.get("cs04_body_full_packet_materialized_here") is not False:
        raise ValueError("P7-R54-AHR-CS05 requires CS04 no body-full packet materialization")
    if data.get("cs04_local_reviewer_payload_materialized_here") is not False:
        raise ValueError("P7-R54-AHR-CS05 requires CS04 no reviewer payload materialization")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS05 local-only preflight")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS05 local-only preflight")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS05 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS05 historical basis ref changed")
    if data.get("required_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS05 required case count changed")
    for key in ("manifest_row_count", "case_ref_id_count", "blind_case_id_count", "packet_ref_id_count"):
        if data.get(key) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError(f"P7-R54-AHR-CS05 {key} changed")
    if data.get("packet_ref_ids_unique") is not True:
        raise ValueError("P7-R54-AHR-CS05 packet refs must remain unique")
    if data.get("review_session_id_present_ref") != P7_R54_AHR_CS05_REVIEW_SESSION_PRESENT_REF:
        raise ValueError("P7-R54-AHR-CS05 review session ref changed")
    if data.get("local_review_root_is_ref_only") is not True:
        raise ValueError("P7-R54-AHR-CS05 local review root must be ref-only")
    if data.get("export_denylist_ready_ref") != P7_R54_AHR_CS05_EXPORT_DENYLIST_READY_REF:
        raise ValueError("P7-R54-AHR-CS05 export denylist ready ref changed")
    if tuple(data.get("export_denylist_refs") or ()) != P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-AHR-CS05 export denylist refs changed")
    if data.get("export_denylist_ref_count") != len(P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS):
        raise ValueError("P7-R54-AHR-CS05 export denylist count changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("P7-R54-AHR-CS05 forbidden output refs changed")
    if data.get("forbidden_output_ref_count") != len(P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS):
        raise ValueError("P7-R54-AHR-CS05 forbidden output count changed")
    if data.get("body_full_packet_exported_here_ref") != "BODY_FULL_PACKET_NOT_EXPORTED_HERE":
        raise ValueError("P7-R54-AHR-CS05 body-full export marker changed")
    _assert_true_fields(
        data,
        keys=(
            "current_24_case_manifest_frozen",
            "local_review_root_is_ref_only",
            "local_only",
            "must_not_export",
            "disposal_required",
            "body_full_packet_generation_blocked_before_preflight",
            "body_full_generation_blocked_until_preflight_ready",
            "actual_review_execution_blocked_until_packet_generation_receipt",
            "actual_human_review_completion_claim_blocked_here",
            "actual_rating_or_question_rows_claim_blocked_here",
            "disposal_receipt_claim_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ),
        source="P7-R54-AHR-CS05 local-only preflight",
    )
    _assert_false_fields(
        data,
        keys=(
            "body_full_packet_generation_allowed_before_preflight",
            "body_full_packet_generation_performed_here",
            "body_full_packet_content_included_in_preflight",
            "actual_human_review_complete",
            "actual_review_evidence_complete",
            "actual_r52_reintake_execution_confirmed",
            "p5_confirmed_final",
            "p6_start_allowed",
            "p8_start_allowed",
            "p7_complete",
            "release_allowed",
        ),
        source="P7-R54-AHR-CS05 local-only preflight",
    )
    status_ref = data.get("local_only_preflight_status_ref")
    if status_ref == P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF:
        _assert_true_fields(
            data,
            keys=(
                "review_session_id_present",
                "explicit_local_only_allow_present",
                "local_review_root_available_ref_present",
                "export_denylist_ready",
                "purge_plan_ready",
                "local_only_preflight_ready",
                "body_full_packet_generation_allowed_by_preflight",
                "body_full_packet_generation_request_allowed_next",
            ),
            source="P7-R54-AHR-CS05 ready local-only preflight",
        )
        if data.get("explicit_local_only_allow_ref") != P7_R54_AHR_CS05_EXPLICIT_LOCAL_ONLY_ALLOW_REF:
            raise ValueError("P7-R54-AHR-CS05 explicit local-only allow ref changed")
        if data.get("local_review_root_available_ref") != P7_R54_AHR_CS05_LOCAL_REVIEW_ROOT_AVAILABLE_REF:
            raise ValueError("P7-R54-AHR-CS05 local review root ref changed")
        if data.get("purge_plan_ready_ref") != P7_R54_AHR_CS05_PURGE_PLAN_READY_REF:
            raise ValueError("P7-R54-AHR-CS05 purge plan ref changed")
        if data.get("local_only_preflight_reason_refs") != [P7_R54_AHR_CS05_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS05 ready preflight reason changed")
        if data.get("execution_blocker_ids") != [] or data.get("open_execution_blocker_ids") != []:
            raise ValueError("P7-R54-AHR-CS05 ready preflight must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS05_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS05 ready implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS05_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS05 ready not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS06_STEP_REF:
            raise ValueError("P7-R54-AHR-CS05 ready next step changed")
    elif status_ref == P7_R54_AHR_CS05_PREFLIGHT_BLOCKED_STATUS_REF:
        if data.get("local_only_preflight_ready") is not False:
            raise ValueError("P7-R54-AHR-CS05 blocked preflight cannot be ready")
        if data.get("body_full_packet_generation_allowed_by_preflight") is not False:
            raise ValueError("P7-R54-AHR-CS05 blocked preflight cannot allow generation")
        if data.get("body_full_packet_generation_request_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-CS05 blocked preflight cannot allow packet request")
        blockers = data.get("execution_blocker_ids")
        if not isinstance(blockers, list) or not blockers:
            raise ValueError("P7-R54-AHR-CS05 blocked preflight must carry blockers")
        if data.get("open_execution_blocker_ids") != blockers:
            raise ValueError("P7-R54-AHR-CS05 blocked preflight open blockers changed")
        if data.get("local_only_preflight_reason_refs") != blockers:
            raise ValueError("P7-R54-AHR-CS05 blocked preflight reason refs must equal blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS04_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS05 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS04_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS05 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS05_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS05 blocked next step changed")
    else:
        raise ValueError("P7-R54-AHR-CS05 unknown preflight status")
    return True


# Compatibility aliases for CS04/CS05 design wording.
build_p7_r54_ahr_current_snapshot_actual_review_reentry_current_24_case_manifest_refreeze_bodyfree = (
    build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_current_24_case_manifest_refreeze_bodyfree_contract = (
    assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_local_only_preflight_bodyfree = (
    build_p7_r54_ahr_cs05_local_only_preflight
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_local_only_preflight_bodyfree_contract = (
    assert_p7_r54_ahr_cs05_local_only_preflight_contract
)
# CS06/CS07 packet bridge and export denylist scan.
#
# These steps deliberately remain body-free.  CS06 records a request / receipt
# bridge for a local-only body-full packet operation without generating,
# exporting, hashing, pathing, or embedding packet content here.  CS07 scans the
# resulting body-free receipt refs for completeness / export-denylist status
# before any reviewer-selection form can be frozen in CS08.
# ---------------------------------------------------------------------------

P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs06_packet_generation_request_receipt_bridge.bodyfree.v1"
)
P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION
)
P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs07_packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R54_AHR_CS_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION
)
P7_R54_AHR_CS_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
)

P7_R54_AHR_CS06_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS05_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS06_STEP_REF,
)
P7_R54_AHR_CS06_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[7:]
P7_R54_AHR_CS07_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS06_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS07_STEP_REF,
)
P7_R54_AHR_CS07_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[8:]

P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF: Final = (
    "LOCAL_ONLY_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_READY_BODYFREE_NOT_EXPORTED"
)
P7_R54_AHR_CS06_BRIDGE_BLOCKED_STATUS_REF: Final = (
    "LOCAL_ONLY_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_BLOCKED"
)
P7_R54_AHR_CS06_ALLOWED_BRIDGE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF,
    P7_R54_AHR_CS06_BRIDGE_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS06_READY_REASON_REF: Final = (
    "r54_ahr_cs_packet_generation_request_receipt_bridge_bodyfree_ready"
)
P7_R54_AHR_CS06_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS06_repair_packet_generation_request_receipt_bridge_before_packet_scan"
)
P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_REF: Final = (
    "R54_AHR_CS_BODY_FULL_PACKET_GENERATION_REQUEST_BODYFREE_ONLY"
)
P7_R54_AHR_CS06_LOCAL_PACKET_GENERATION_OPERATION_REF: Final = (
    "R54_AHR_CS_LOCAL_ONLY_PACKET_GENERATION_OPERATION_REF"
)
P7_R54_AHR_CS06_REQUEST_STATUS_READY_REF: Final = (
    "PACKET_GENERATION_REQUEST_RECORDED_BODYFREE_READY"
)
P7_R54_AHR_CS06_RECEIPT_STATUS_READY_REF: Final = (
    "LOCAL_PACKET_GENERATION_RECEIPT_INTAKEN_BODYFREE_READY_NOT_EXPORTED"
)
P7_R54_AHR_CS06_REQUEST_STATUS_BLOCKED_REF: Final = "PACKET_GENERATION_REQUEST_RECORDED_BODYFREE_BLOCKED"
P7_R54_AHR_CS06_RECEIPT_STATUS_BLOCKED_REF: Final = "LOCAL_PACKET_GENERATION_RECEIPT_INTAKE_BLOCKED"
P7_R54_AHR_CS06_FORBIDDEN_RECEIPT_FLAG_REFS: Final[tuple[str, ...]] = (
    "content_included",
    "absolute_path_included",
    "hash_included",
    "packet_content_included",
    "body_full_packet_content_included",
    "raw_input_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
)

P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF: Final = (
    "PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_PASSED_BODYFREE"
)
P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF: Final = (
    "PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_BLOCKED"
)
P7_R54_AHR_CS07_ALLOWED_SCAN_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF,
    P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS07_READY_REASON_REF: Final = (
    "r54_ahr_cs_packet_completeness_export_denylist_scan_passed_bodyfree"
)
P7_R54_AHR_CS07_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS07_repair_packet_completeness_export_denylist_scan_before_reviewer_selection_form"
)
P7_R54_AHR_CS07_SCAN_TARGET_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR08_SCAN_TARGET_REFS
)
P7_R54_AHR_CS07_FORBIDDEN_SCAN_FLAG_REFS: Final[tuple[str, ...]] = (
    "packet_content_included",
    "body_full_packet_content_included",
    "raw_input_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
)

P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs05_schema_version",
    "cs05_material_ref",
    "cs05_next_required_step",
    "cs05_local_only_preflight_status_ref",
    "cs05_local_only_preflight_ready",
    "cs05_body_full_packet_generation_request_allowed_next",
    "cs05_required_case_count",
    "cs05_manifest_row_count",
    "cs05_packet_ref_id_count",
    "cs05_packet_ref_ids_unique",
    "cs05_local_only",
    "cs05_must_not_export",
    "cs05_purge_plan_ready",
    "cs04_material_ref",
    "cs04_current_24_case_manifest_frozen",
    "cs04_case_ref_ids_unique",
    "cs04_blind_case_ids_unique",
    "cs04_packet_ref_ids_unique",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "packet_generation_bridge_status_ref",
    "packet_generation_bridge_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "request_ready_for_bridge",
    "current_manifest_ready_for_packet_generation_request",
    "local_only_preflight_ready_for_packet_generation_request",
    "packet_generation_request_ref",
    "packet_generation_request_ref_present",
    "packet_generation_request_is_ref_only",
    "local_packet_generation_operation_ref",
    "local_packet_generation_operation_ref_only",
    "packet_generation_request_status_ref",
    "packet_generation_receipt_status_ref",
    "packet_generation_request_bodyfree_evidence_recorded",
    "packet_generation_requested_as_bodyfree_evidence_only",
    "packet_generation_request_does_not_include_packet_content",
    "local_packet_generation_operation_receipt_required",
    "local_packet_generation_operation_receipt_intaken",
    "packet_generation_receipt_intaken",
    "packet_generation_operation_receipt_only",
    "required_case_count",
    "expected_generated_case_count",
    "expected_generated_packet_count",
    "generated_case_count",
    "generated_packet_count",
    "generated_counts_match_expected",
    "case_ref_ids",
    "case_ref_id_count",
    "blind_case_ids",
    "blind_case_id_count",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "generated_packet_refs_match_expected_count",
    "local_only",
    "must_not_export",
    "exported",
    "local_packet_exported",
    "content_included",
    "absolute_path_included",
    "hash_included",
    "terminal_output_included",
    "body_full_packet_generation_performed_here",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_full_packet_generation_request_allowed_next",
    "packet_completeness_export_denylist_scan_allowed_next",
    "actual_review_execution_allowed_next",
    "actual_review_execution_blocked_until_packet_completeness_scan",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *P7_R54_AHR_CS06_FORBIDDEN_RECEIPT_FLAG_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_BODYFREE_EVIDENCE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs06_schema_version",
    "cs06_material_ref",
    "cs06_next_required_step",
    "cs06_packet_generation_bridge_status_ref",
    "cs06_packet_generation_receipt_intaken",
    "cs06_packet_completeness_export_denylist_scan_allowed_next",
    "cs06_required_case_count",
    "cs06_generated_case_count",
    "cs06_generated_packet_count",
    "cs06_packet_ref_ids",
    "cs06_packet_ref_id_count",
    "cs06_packet_ref_ids_unique",
    "cs06_exported",
    "cs06_local_packet_exported",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "scan_status_ref",
    "scan_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "receipt_ready_for_packet_scan",
    "local_only",
    "must_not_export",
    "exported",
    "local_packet_exported",
    "required_case_count",
    "expected_packet_count",
    "scanned_case_count",
    "scanned_packet_count",
    "scanned_packet_ref_ids",
    "scanned_packet_ref_id_count",
    "scanned_packet_refs_unique",
    "packet_count_complete",
    "packet_completeness_passed",
    "packet_completeness_bodyfree_only",
    "export_denylist_scan_target_refs",
    "export_denylist_scan_target_count",
    "export_denylist_refs",
    "export_denylist_ref_count",
    "export_denylist_scan_passed",
    "forbidden_output_refs",
    "forbidden_output_ref_count",
    "forbidden_key_findings",
    "forbidden_key_findings_count",
    "forbidden_export_flag_count",
    "forbidden_key_scan_passed",
    "packet_completeness_export_denylist_scan_completed",
    "packet_completeness_export_denylist_scan_bodyfree_evidence_only",
    "packet_completeness_export_denylist_scan_passed",
    "packet_content_not_included_in_scan_evidence",
    "local_absolute_path_not_included_in_scan_evidence",
    "body_hash_not_included_in_scan_evidence",
    "terminal_output_not_included_in_scan_evidence",
    "reviewer_selection_form_freeze_allowed_next",
    "actual_review_execution_allowed_next",
    "actual_review_execution_blocked_until_reviewer_selection_form",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    *P7_R54_AHR_CS07_FORBIDDEN_SCAN_FLAG_REFS,
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)


def _cs06_status_and_blockers(
    *,
    preflight_ready: bool,
    request_ref: str,
    operation_ref: str,
    expected_count: int,
    generated_case_count: int,
    generated_packet_count: int,
    packet_ref_ids_unique: bool,
    local_only: bool,
    must_not_export: bool,
    exported: bool,
    local_packet_exported: bool,
    content_included: bool,
    absolute_path_included: bool,
    hash_included: bool,
    terminal_output_included: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not preflight_ready:
        blockers.append("cs05_local_only_preflight_not_ready")
    if expected_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("expected_case_count_not_24")
    if generated_case_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("generated_case_count_not_24")
    if generated_packet_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("generated_packet_count_not_24")
    if not packet_ref_ids_unique:
        blockers.append("packet_ref_ids_not_unique")
    if request_ref != P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_REF:
        blockers.append("packet_generation_request_ref_missing_or_unexpected")
    if operation_ref != P7_R54_AHR_CS06_LOCAL_PACKET_GENERATION_OPERATION_REF:
        blockers.append("local_packet_generation_operation_ref_missing_or_unexpected")
    if not local_only:
        blockers.append("local_only_not_confirmed")
    if not must_not_export:
        blockers.append("must_not_export_not_confirmed")
    if exported:
        blockers.append("receipt_marked_exported")
    if local_packet_exported:
        blockers.append("local_packet_exported")
    if content_included:
        blockers.append("packet_content_included")
    if absolute_path_included:
        blockers.append("absolute_path_included")
    if hash_included:
        blockers.append("body_hash_included")
    if terminal_output_included:
        blockers.append("terminal_output_body_included")
    blockers = _cs_dedupe_identifiers(blockers)
    if blockers:
        return P7_R54_AHR_CS06_BRIDGE_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF, [P7_R54_AHR_CS06_READY_REASON_REF], []


def build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge(
    *,
    local_only_preflight: Mapping[str, Any] | None = None,
    current_24_case_manifest_refreeze: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    packet_generation_request_ref: Any = P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_REF,
    local_packet_generation_operation_ref: Any = P7_R54_AHR_CS06_LOCAL_PACKET_GENERATION_OPERATION_REF,
    generated_case_count: int = P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    generated_packet_count: int = P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
    local_only: bool = True,
    must_not_export: bool = True,
    exported: bool = False,
    local_packet_exported: bool = False,
    content_included: bool = False,
    absolute_path_included: bool = False,
    hash_included: bool = False,
    terminal_output_included: bool = False,
) -> dict[str, Any]:
    """Build CS06 packet generation request / receipt bridge body-free material."""

    cs05 = dict(local_only_preflight or build_p7_r54_ahr_cs05_local_only_preflight())
    assert_p7_r54_ahr_cs05_local_only_preflight_contract(cs05)
    cs04 = dict(current_24_case_manifest_refreeze or build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze())
    assert_p7_r54_ahr_cs04_current_24_case_manifest_refreeze_contract(cs04)
    session_id = _safe_review_session_id(review_session_id or cs05.get("review_session_id") or cs04.get("review_session_id"))
    case_ref_ids = [clean_identifier(value, max_length=180) for value in (cs04.get("case_ref_ids") or [])]
    blind_case_ids = [clean_identifier(value, max_length=180) for value in (cs04.get("blind_case_ids") or [])]
    packet_ref_ids = [clean_identifier(value, max_length=180) for value in (cs04.get("packet_ref_ids") or [])]
    packet_unique = _cs_unique_non_empty(
        packet_ref_ids, required_count=P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    request_ref = clean_identifier(packet_generation_request_ref, max_length=220)
    operation_ref = clean_identifier(local_packet_generation_operation_ref, max_length=220)
    preflight_ready = (
        cs05.get("local_only_preflight_status_ref") == P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF
        and cs05.get("body_full_packet_generation_request_allowed_next") is True
        and cs05.get("local_only_preflight_ready") is True
    )
    status_ref, reason_refs, blockers = _cs06_status_and_blockers(
        preflight_ready=preflight_ready,
        request_ref=request_ref,
        operation_ref=operation_ref,
        expected_count=len(packet_ref_ids),
        generated_case_count=int(generated_case_count),
        generated_packet_count=int(generated_packet_count),
        packet_ref_ids_unique=packet_unique,
        local_only=local_only,
        must_not_export=must_not_export,
        exported=exported,
        local_packet_exported=local_packet_exported,
        content_included=content_included,
        absolute_path_included=absolute_path_included,
        hash_included=hash_included,
        terminal_output_included=terminal_output_included,
    )
    ready = status_ref == P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS06_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS06_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs05_schema_version": cs05["schema_version"],
        "cs05_material_ref": cs05["material_id"],
        "cs05_next_required_step": cs05["next_required_step"],
        "cs05_local_only_preflight_status_ref": cs05["local_only_preflight_status_ref"],
        "cs05_local_only_preflight_ready": cs05["local_only_preflight_ready"],
        "cs05_body_full_packet_generation_request_allowed_next": cs05[
            "body_full_packet_generation_request_allowed_next"
        ],
        "cs05_required_case_count": cs05["required_case_count"],
        "cs05_manifest_row_count": cs05["manifest_row_count"],
        "cs05_packet_ref_id_count": cs05["packet_ref_id_count"],
        "cs05_packet_ref_ids_unique": cs05["packet_ref_ids_unique"],
        "cs05_local_only": cs05["local_only"],
        "cs05_must_not_export": cs05["must_not_export"],
        "cs05_purge_plan_ready": cs05["purge_plan_ready"],
        "cs04_material_ref": cs04["material_id"],
        "cs04_current_24_case_manifest_frozen": cs04["current_24_case_manifest_frozen"],
        "cs04_case_ref_ids_unique": cs04["case_ref_ids_unique"],
        "cs04_blind_case_ids_unique": cs04["blind_case_ids_unique"],
        "cs04_packet_ref_ids_unique": cs04["packet_ref_ids_unique"],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "packet_generation_bridge_status_ref": status_ref,
        "packet_generation_bridge_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "request_ready_for_bridge": preflight_ready,
        "current_manifest_ready_for_packet_generation_request": cs04.get("current_24_case_manifest_frozen") is True,
        "local_only_preflight_ready_for_packet_generation_request": preflight_ready,
        "packet_generation_request_ref": request_ref,
        "packet_generation_request_ref_present": request_ref == P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_REF,
        "packet_generation_request_is_ref_only": request_ref == P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_REF,
        "local_packet_generation_operation_ref": operation_ref,
        "local_packet_generation_operation_ref_only": operation_ref == P7_R54_AHR_CS06_LOCAL_PACKET_GENERATION_OPERATION_REF,
        "packet_generation_request_status_ref": (
            P7_R54_AHR_CS06_REQUEST_STATUS_READY_REF if ready else P7_R54_AHR_CS06_REQUEST_STATUS_BLOCKED_REF
        ),
        "packet_generation_receipt_status_ref": (
            P7_R54_AHR_CS06_RECEIPT_STATUS_READY_REF if ready else P7_R54_AHR_CS06_RECEIPT_STATUS_BLOCKED_REF
        ),
        "packet_generation_request_bodyfree_evidence_recorded": ready,
        "packet_generation_requested_as_bodyfree_evidence_only": ready,
        "packet_generation_request_does_not_include_packet_content": True,
        "local_packet_generation_operation_receipt_required": ready,
        "local_packet_generation_operation_receipt_intaken": ready,
        "packet_generation_receipt_intaken": ready,
        "packet_generation_operation_receipt_only": True,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "expected_generated_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "expected_generated_packet_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "generated_case_count": int(generated_case_count),
        "generated_packet_count": int(generated_packet_count),
        "generated_counts_match_expected": ready,
        "case_ref_ids": case_ref_ids if ready else [],
        "case_ref_id_count": len(case_ref_ids) if ready else 0,
        "blind_case_ids": blind_case_ids if ready else [],
        "blind_case_id_count": len(blind_case_ids) if ready else 0,
        "packet_ref_ids": packet_ref_ids if ready else [],
        "packet_ref_id_count": len(packet_ref_ids) if ready else 0,
        "packet_ref_ids_unique": packet_unique if ready else False,
        "generated_packet_refs_match_expected_count": ready,
        "local_only": local_only,
        "must_not_export": must_not_export,
        "exported": False,
        "local_packet_exported": False,
        "content_included": False,
        "absolute_path_included": False,
        "hash_included": False,
        "terminal_output_included": False,
        "body_full_packet_generation_performed_here": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_full_packet_generation_request_allowed_next": False,
        "packet_completeness_export_denylist_scan_allowed_next": ready,
        "actual_review_execution_allowed_next": False,
        "actual_review_execution_blocked_until_packet_completeness_scan": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **{key: False for key in P7_R54_AHR_CS06_FORBIDDEN_RECEIPT_FLAG_REFS},
        "implemented_steps": list(P7_R54_AHR_CS06_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS05_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CS06_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS05_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CS07_STEP_REF if ready else P7_R54_AHR_CS06_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS06 packet generation request / receipt bridge",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS06_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS06_STEP_REF,
        source="P7-R54-AHR-CS06 packet generation request / receipt bridge",
    )
    if data.get("cs05_schema_version") != P7_R54_AHR_CS05_LOCAL_ONLY_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS06 CS05 schema changed")
    if data.get("cs05_next_required_step") == P7_R54_AHR_CS06_STEP_REF:
        if data.get("cs05_local_only_preflight_status_ref") != P7_R54_AHR_CS05_PREFLIGHT_READY_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS06 ready predecessor must be CS05 ready")
    elif data.get("cs05_next_required_step") != P7_R54_AHR_CS05_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CS06 must follow CS05")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS06 packet bridge")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS06 packet bridge")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS06 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS06 historical basis ref changed")
    if data.get("packet_generation_bridge_status_ref") not in P7_R54_AHR_CS06_ALLOWED_BRIDGE_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS06 bridge status changed")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=220) for value in data.get("execution_blocker_ids") or []])
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR-CS06 open blockers must match blockers")
    for key in (
        "packet_generation_request_does_not_include_packet_content",
        "packet_generation_operation_receipt_only",
        "actual_review_execution_blocked_until_packet_completeness_scan",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-CS06 must keep {key}=True")
    for key in (
        "exported",
        "local_packet_exported",
        "content_included",
        "absolute_path_included",
        "hash_included",
        "terminal_output_included",
        "body_full_packet_generation_performed_here",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "body_full_packet_generation_request_allowed_next",
        "actual_review_execution_allowed_next",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS06 must keep {key}=False")
    for key in P7_R54_AHR_CS06_FORBIDDEN_RECEIPT_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS06 forbidden receipt flag {key} must remain false")
    if data.get("required_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS06 required case count changed")
    if data.get("expected_generated_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS06 expected generated case count changed")
    if data.get("expected_generated_packet_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS06 expected generated packet count changed")
    ready = data.get("packet_generation_bridge_status_ref") == P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS06 ready bridge must not carry blockers")
        for key in (
            "request_ready_for_bridge",
            "current_manifest_ready_for_packet_generation_request",
            "local_only_preflight_ready_for_packet_generation_request",
            "packet_generation_request_ref_present",
            "packet_generation_request_is_ref_only",
            "local_packet_generation_operation_ref_only",
            "packet_generation_request_bodyfree_evidence_recorded",
            "packet_generation_requested_as_bodyfree_evidence_only",
            "local_packet_generation_operation_receipt_required",
            "local_packet_generation_operation_receipt_intaken",
            "packet_generation_receipt_intaken",
            "generated_counts_match_expected",
            "generated_packet_refs_match_expected_count",
            "packet_ref_ids_unique",
            "local_only",
            "must_not_export",
            "packet_completeness_export_denylist_scan_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS06 ready bridge must keep {key}=True")
        if data.get("packet_generation_request_ref") != P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_REF:
            raise ValueError("P7-R54-AHR-CS06 request ref changed")
        if data.get("local_packet_generation_operation_ref") != P7_R54_AHR_CS06_LOCAL_PACKET_GENERATION_OPERATION_REF:
            raise ValueError("P7-R54-AHR-CS06 local operation ref changed")
        if data.get("packet_generation_request_status_ref") != P7_R54_AHR_CS06_REQUEST_STATUS_READY_REF:
            raise ValueError("P7-R54-AHR-CS06 request status changed")
        if data.get("packet_generation_receipt_status_ref") != P7_R54_AHR_CS06_RECEIPT_STATUS_READY_REF:
            raise ValueError("P7-R54-AHR-CS06 receipt status changed")
        if data.get("packet_generation_bridge_reason_refs") != [P7_R54_AHR_CS06_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS06 ready reason changed")
        for key in (
            "generated_case_count",
            "generated_packet_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
        ):
            if data.get(key) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CS06 {key} changed")
        if not _cs_unique_non_empty(data.get("packet_ref_ids") or [], required_count=P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT):
            raise ValueError("P7-R54-AHR-CS06 packet refs must remain unique")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS06_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS06 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS06_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS06 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS07_STEP_REF:
            raise ValueError("P7-R54-AHR-CS06 next step changed")
    else:
        if data.get("packet_generation_bridge_status_ref") != P7_R54_AHR_CS06_BRIDGE_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS06 blocked bridge status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS06 blocked bridge must carry blockers")
        for key in (
            "packet_generation_request_bodyfree_evidence_recorded",
            "packet_generation_requested_as_bodyfree_evidence_only",
            "local_packet_generation_operation_receipt_required",
            "local_packet_generation_operation_receipt_intaken",
            "packet_generation_receipt_intaken",
            "generated_counts_match_expected",
            "generated_packet_refs_match_expected_count",
            "packet_completeness_export_denylist_scan_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-CS06 blocked bridge must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR_CS06_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS06 blocked next step changed")
    return True


def _cs07_status_and_blockers(
    *,
    receipt_ready: bool,
    required_case_count: int,
    expected_packet_count: int,
    scanned_case_count: int,
    scanned_packet_count: int,
    packet_ref_ids_unique: bool,
    exported: bool,
    local_packet_exported: bool,
    forbidden_key_findings: Sequence[str],
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not receipt_ready:
        blockers.append("cs06_packet_generation_receipt_not_ready")
    if required_case_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("required_case_count_not_24")
    if expected_packet_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("expected_packet_count_not_24")
    if scanned_case_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("scanned_case_count_not_24")
    if scanned_packet_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("scanned_packet_count_not_24")
    if not packet_ref_ids_unique:
        blockers.append("scanned_packet_refs_not_unique")
    if exported:
        blockers.append("exported_flag_present")
    if local_packet_exported:
        blockers.append("local_packet_exported")
    if forbidden_key_findings:
        blockers.extend(forbidden_key_findings)
    blockers = _cs_dedupe_identifiers(blockers)
    if blockers:
        return P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF, [P7_R54_AHR_CS07_READY_REASON_REF], []


def build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan(
    *,
    packet_generation_request_receipt_bridge: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    scanned_case_count: int | None = None,
    scanned_packet_count: int | None = None,
    exported: bool = False,
    local_packet_exported: bool = False,
    forbidden_key_findings: Sequence[str] = (),
) -> dict[str, Any]:
    """Build CS07 packet completeness / export denylist scan body-free material."""

    cs06 = dict(
        packet_generation_request_receipt_bridge or build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge()
    )
    assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract(cs06)
    session_id = _safe_review_session_id(review_session_id or cs06.get("review_session_id"))
    packet_refs = [clean_identifier(value, max_length=180) for value in (cs06.get("packet_ref_ids") or [])]
    receipt_ready = (
        cs06.get("packet_generation_bridge_status_ref") == P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF
        and cs06.get("packet_completeness_export_denylist_scan_allowed_next") is True
        and cs06.get("packet_generation_receipt_intaken") is True
    )
    scan_case_count = int(scanned_case_count if scanned_case_count is not None else cs06.get("generated_case_count") or 0)
    scan_packet_count = int(scanned_packet_count if scanned_packet_count is not None else cs06.get("generated_packet_count") or 0)
    findings = _cs_dedupe_identifiers([clean_identifier(value, max_length=220) for value in forbidden_key_findings])
    packet_unique = _cs_unique_non_empty(packet_refs, required_count=P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT)
    status_ref, reason_refs, blockers = _cs07_status_and_blockers(
        receipt_ready=receipt_ready,
        required_case_count=int(cs06.get("required_case_count") or 0),
        expected_packet_count=len(packet_refs),
        scanned_case_count=scan_case_count,
        scanned_packet_count=scan_packet_count,
        packet_ref_ids_unique=packet_unique,
        exported=exported or cs06.get("exported") is True,
        local_packet_exported=local_packet_exported or cs06.get("local_packet_exported") is True,
        forbidden_key_findings=findings,
    )
    ready = status_ref == P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS07_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS07_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs06_schema_version": cs06["schema_version"],
        "cs06_material_ref": cs06["material_id"],
        "cs06_next_required_step": cs06["next_required_step"],
        "cs06_packet_generation_bridge_status_ref": cs06["packet_generation_bridge_status_ref"],
        "cs06_packet_generation_receipt_intaken": cs06["packet_generation_receipt_intaken"],
        "cs06_packet_completeness_export_denylist_scan_allowed_next": cs06[
            "packet_completeness_export_denylist_scan_allowed_next"
        ],
        "cs06_required_case_count": cs06["required_case_count"],
        "cs06_generated_case_count": cs06["generated_case_count"],
        "cs06_generated_packet_count": cs06["generated_packet_count"],
        "cs06_packet_ref_ids": packet_refs,
        "cs06_packet_ref_id_count": cs06["packet_ref_id_count"],
        "cs06_packet_ref_ids_unique": cs06["packet_ref_ids_unique"],
        "cs06_exported": cs06["exported"],
        "cs06_local_packet_exported": cs06["local_packet_exported"],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "scan_status_ref": status_ref,
        "scan_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "receipt_ready_for_packet_scan": receipt_ready,
        "local_only": cs06.get("local_only") is True,
        "must_not_export": cs06.get("must_not_export") is True,
        "exported": False,
        "local_packet_exported": False,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "expected_packet_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "scanned_case_count": scan_case_count,
        "scanned_packet_count": scan_packet_count,
        "scanned_packet_ref_ids": packet_refs if ready else [],
        "scanned_packet_ref_id_count": len(packet_refs) if ready else 0,
        "scanned_packet_refs_unique": packet_unique if ready else False,
        "packet_count_complete": ready,
        "packet_completeness_passed": ready,
        "packet_completeness_bodyfree_only": ready,
        "export_denylist_scan_target_refs": list(P7_R54_AHR_CS07_SCAN_TARGET_REFS),
        "export_denylist_scan_target_count": len(P7_R54_AHR_CS07_SCAN_TARGET_REFS),
        "export_denylist_refs": list(P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS),
        "export_denylist_ref_count": len(P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS),
        "export_denylist_scan_passed": ready,
        "forbidden_output_refs": list(P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS),
        "forbidden_output_ref_count": len(P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS),
        "forbidden_key_findings": [] if ready else findings,
        "forbidden_key_findings_count": 0 if ready else len(findings),
        "forbidden_export_flag_count": 0 if ready else len([value for value in (exported, local_packet_exported) if value]),
        "forbidden_key_scan_passed": ready,
        "packet_completeness_export_denylist_scan_completed": ready,
        "packet_completeness_export_denylist_scan_bodyfree_evidence_only": ready,
        "packet_completeness_export_denylist_scan_passed": ready,
        "packet_content_not_included_in_scan_evidence": True,
        "local_absolute_path_not_included_in_scan_evidence": True,
        "body_hash_not_included_in_scan_evidence": True,
        "terminal_output_not_included_in_scan_evidence": True,
        "reviewer_selection_form_freeze_allowed_next": ready,
        "actual_review_execution_allowed_next": False,
        "actual_review_execution_blocked_until_reviewer_selection_form": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        **{key: False for key in P7_R54_AHR_CS07_FORBIDDEN_SCAN_FLAG_REFS},
        "implemented_steps": list(P7_R54_AHR_CS07_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS06_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CS07_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS06_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CS08_STEP_REF if ready else P7_R54_AHR_CS07_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS07 packet completeness / export denylist scan",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS07_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS07_STEP_REF,
        source="P7-R54-AHR-CS07 packet completeness / export denylist scan",
    )
    if data.get("cs06_schema_version") != P7_R54_AHR_CS06_PACKET_GENERATION_REQUEST_RECEIPT_BRIDGE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS07 must follow CS06")
    if data.get("cs06_packet_generation_bridge_status_ref") == P7_R54_AHR_CS06_BRIDGE_READY_STATUS_REF:
        if data.get("cs06_next_required_step") != P7_R54_AHR_CS07_STEP_REF:
            raise ValueError("P7-R54-AHR-CS07 must follow CS06 next step")
    elif data.get("cs06_next_required_step") != P7_R54_AHR_CS06_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CS07 blocked predecessor must preserve CS06 repair next step")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS07 packet scan")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS07 packet scan")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS07 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS07 historical basis ref changed")
    if data.get("scan_status_ref") not in P7_R54_AHR_CS07_ALLOWED_SCAN_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS07 scan status changed")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=220) for value in data.get("execution_blocker_ids") or []])
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR-CS07 open blockers must match blockers")
    if data.get("required_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS07 required case count changed")
    if data.get("expected_packet_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        raise ValueError("P7-R54-AHR-CS07 expected packet count changed")
    if tuple(data.get("export_denylist_scan_target_refs") or ()) != P7_R54_AHR_CS07_SCAN_TARGET_REFS:
        raise ValueError("P7-R54-AHR-CS07 scan target refs changed")
    if data.get("export_denylist_scan_target_count") != len(P7_R54_AHR_CS07_SCAN_TARGET_REFS):
        raise ValueError("P7-R54-AHR-CS07 scan target count changed")
    if tuple(data.get("export_denylist_refs") or ()) != P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS:
        raise ValueError("P7-R54-AHR-CS07 export denylist refs changed")
    if data.get("export_denylist_ref_count") != len(P7_R54_AHR_CS05_EXPORT_DENYLIST_REFS):
        raise ValueError("P7-R54-AHR-CS07 export denylist count changed")
    if tuple(data.get("forbidden_output_refs") or ()) != P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS:
        raise ValueError("P7-R54-AHR-CS07 forbidden output refs changed")
    if data.get("forbidden_output_ref_count") != len(P7_R54_AHR_CS05_FORBIDDEN_OUTPUT_REFS):
        raise ValueError("P7-R54-AHR-CS07 forbidden output count changed")
    if data.get("forbidden_key_findings_count") != len(data.get("forbidden_key_findings") or []):
        raise ValueError("P7-R54-AHR-CS07 finding count changed")
    for key in P7_R54_AHR_CS07_FORBIDDEN_SCAN_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS07 forbidden scan flag {key} must remain false")
    for key in (
        "packet_content_not_included_in_scan_evidence",
        "local_absolute_path_not_included_in_scan_evidence",
        "body_hash_not_included_in_scan_evidence",
        "terminal_output_not_included_in_scan_evidence",
        "actual_review_execution_blocked_until_reviewer_selection_form",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-CS07 must keep {key}=True")
    for key in ("exported", "local_packet_exported", "actual_review_execution_allowed_next"):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS07 must keep {key}=False")
    ready = data.get("scan_status_ref") == P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS07 passed scan must not carry blockers")
        for key in (
            "receipt_ready_for_packet_scan",
            "local_only",
            "must_not_export",
            "packet_count_complete",
            "packet_completeness_passed",
            "packet_completeness_bodyfree_only",
            "export_denylist_scan_passed",
            "forbidden_key_scan_passed",
            "packet_completeness_export_denylist_scan_completed",
            "packet_completeness_export_denylist_scan_bodyfree_evidence_only",
            "packet_completeness_export_denylist_scan_passed",
            "reviewer_selection_form_freeze_allowed_next",
            "scanned_packet_refs_unique",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS07 passed scan must keep {key}=True")
        if data.get("scanned_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CS07 scanned case count changed")
        if data.get("scanned_packet_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CS07 scanned packet count changed")
        if data.get("scanned_packet_ref_id_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CS07 scanned packet ref count changed")
        if not _cs_unique_non_empty(
            data.get("scanned_packet_ref_ids") or [],
            required_count=P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        ):
            raise ValueError("P7-R54-AHR-CS07 scanned packet refs must remain unique")
        if data.get("forbidden_key_findings") != []:
            raise ValueError("P7-R54-AHR-CS07 passed scan must have no forbidden findings")
        if data.get("forbidden_export_flag_count") != 0:
            raise ValueError("P7-R54-AHR-CS07 passed scan must have zero forbidden export flags")
        if data.get("scan_reason_refs") != [P7_R54_AHR_CS07_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS07 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS07_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS07 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS07_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS07 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS08_STEP_REF:
            raise ValueError("P7-R54-AHR-CS07 next step changed")
    else:
        if data.get("scan_status_ref") != P7_R54_AHR_CS07_SCAN_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS07 blocked scan status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS07 blocked scan must carry blockers")
        for key in (
            "packet_count_complete",
            "packet_completeness_passed",
            "packet_completeness_bodyfree_only",
            "export_denylist_scan_passed",
            "forbidden_key_scan_passed",
            "packet_completeness_export_denylist_scan_completed",
            "packet_completeness_export_denylist_scan_bodyfree_evidence_only",
            "packet_completeness_export_denylist_scan_passed",
            "reviewer_selection_form_freeze_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-CS07 blocked scan must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR_CS07_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS07 blocked next step changed")
    return True


# Compatibility aliases for CS06/CS07 design wording.
build_p7_r54_ahr_cs06_packet_generation_request_bodyfree_evidence = (
    build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge
)
build_p7_r54_ahr_cs06_local_packet_generation_receipt_intake = (
    build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge
)
assert_p7_r54_ahr_cs06_packet_generation_bridge_contract = (
    assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract
)
assert_p7_r54_ahr_cs06_packet_generation_request_bodyfree_evidence_contract = (
    assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract
)
assert_p7_r54_ahr_cs06_local_packet_generation_receipt_intake_contract = (
    assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_generation_request_receipt_bridge_bodyfree = (
    build_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_generation_request_receipt_bridge_bodyfree_contract = (
    assert_p7_r54_ahr_cs06_packet_generation_request_receipt_bridge_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_completeness_export_denylist_scan_bodyfree = (
    build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_packet_completeness_export_denylist_scan_bodyfree_contract = (
    assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract
)


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# CS08/CS09 reviewer selection form and actual review operation receipt intake.
#
# CS08 freezes a current-basis selection-only reviewer form after the CS07
# packet completeness / export-denylist scan.  It intentionally does not create
# reviewer free text, question text, local path, body hash, or any body-full
# payload material.
#
# CS09 intakes a body-free operation receipt for a person-run local-only review.
# The helper does not run the review and does not materialize sanitized rows,
# question observations, disposal receipt, R52 execution, P5 final,
# P6 start, P8 start, P7 complete, or release readiness.
# ---------------------------------------------------------------------------

P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs08_reviewer_selection_form_current_compatibility.bodyfree.v1"
)
P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs09_actual_human_review_operation_receipt_intake.bodyfree.v1"
)
P7_R54_AHR_CS_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION
)
P7_R54_AHR_CS_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION
)

P7_R54_AHR_CS08_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS07_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS08_STEP_REF,
)
P7_R54_AHR_CS08_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[9:]
P7_R54_AHR_CS09_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS08_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS09_STEP_REF,
)
P7_R54_AHR_CS09_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[10:]

P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_REVIEWER_SELECTION_FORM_FROZEN_BODYFREE_READY"
)
P7_R54_AHR_CS08_FORM_BLOCKED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_REVIEWER_SELECTION_FORM_BLOCKED_BY_PACKET_SCAN"
)
P7_R54_AHR_CS08_ALLOWED_FORM_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF,
    P7_R54_AHR_CS08_FORM_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS08_READY_REASON_REF: Final = (
    "r54_ahr_cs_reviewer_selection_form_current_compatibility_frozen_bodyfree"
)
P7_R54_AHR_CS08_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS08_repair_reviewer_selection_form_current_compatibility_before_operation_receipt"
)

P7_R54_AHR_CS08_SCORE_OPTION_REFS: Final[tuple[float, ...]] = tuple(historical_ahr.P7_R54_AHR09_SCORE_OPTION_REFS)
P7_R54_AHR_CS08_VERDICT_OPTION_REFS: Final[tuple[str, ...]] = tuple(historical_ahr.P7_R54_AHR09_VERDICT_OPTION_REFS)
P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_SANITIZED_REASON_ID_OPTION_REFS
)
P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_READFEEL_BLOCKER_ID_OPTION_REFS
)
P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_EXECUTION_BLOCKER_ID_OPTION_REFS
)
P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_QUESTION_NEED_PRIMARY_CLASS_REFS
)
P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_AMBIGUITY_KIND_OPTION_REFS
)
P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_ONE_QUESTION_FIT_OPTION_REFS
)
P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_REPAIR_REQUIRED_OPTION_REFS
)
P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS: Final[tuple[str, ...]] = tuple(
    historical_ahr.P7_R54_AHR09_PLAN_CANDIDATE_FLAG_REFS
)
P7_R54_AHR_CS08_PROHIBITED_FORM_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "free_text_export_allowed",
    "reviewer_free_text_field_present",
    "reviewer_free_text_export_allowed",
    "reviewer_free_text_field_exported_to_bodyfree_evidence",
    "free_text_note_field_exported_to_bodyfree_evidence",
    "reviewer_notes_body_field_present",
    "question_text_input_allowed",
    "draft_question_text_input_allowed",
    "question_text_or_draft_text_field_present",
    "raw_body_copy_field_present",
    "history_surface_copy_field_present",
    "raw_body_copy_field_allowed",
    "history_surface_copy_field_allowed",
    "local_path_field_present",
    "body_hash_field_present",
    "packet_content_copy_field_present",
    "body_full_packet_content_included",
    "packet_content_included",
    "local_absolute_path_included",
    "body_hash_included",
    "question_text_included",
    "draft_question_text_included",
    "reviewer_selection_form_file_materialized_here",
    "local_reviewer_payload_materialized_here",
    "actual_review_execution_allowed_here",
    "actual_review_execution_allowed_next",
    "actual_human_review_run_here",
    "sanitized_review_result_rows_materialized_here",
    "rating_rows_materialized_here",
    "question_need_observation_rows_materialized_here",
    "disposal_receipt_materialized_here",
    "p8_implementation_spec_finalized_here",
)

P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKEN_BODYFREE"
)
P7_R54_AHR_CS09_OPERATION_BLOCKED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_BLOCKED"
)
P7_R54_AHR_CS09_ALLOWED_OPERATION_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF,
    P7_R54_AHR_CS09_OPERATION_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS09_READY_REASON_REF: Final = (
    "r54_ahr_cs_actual_human_review_operation_receipt_intaken_bodyfree"
)
P7_R54_AHR_CS09_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS09_repair_actual_human_review_operation_receipt_before_sanitized_rows"
)
P7_R54_AHR_CS09_OPERATION_RECEIPT_REF: Final = (
    "R54_AHR_CS_ACTUAL_HUMAN_REVIEW_LOCAL_ONLY_OPERATION_RECEIPT_REF"
)
P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT: Final = "reviewer_person_ref_001"
P7_R54_AHR_CS09_REVIEW_STARTED_AT_BUCKET_REF_DEFAULT: Final = "review_started_at_bucket_ref"
P7_R54_AHR_CS09_REVIEW_COMPLETED_AT_BUCKET_REF_DEFAULT: Final = "review_completed_at_bucket_ref"
P7_R54_AHR_CS09_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
)
P7_R54_AHR_CS09_BODYFREE_RECEIPT_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_content_included",
    "raw_input_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
    "terminal_output_body_included",
)

P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs07_schema_version",
    "cs07_material_ref",
    "cs07_next_required_step",
    "cs07_scan_status_ref",
    "cs07_packet_completeness_passed",
    "cs07_export_denylist_scan_passed",
    "cs07_forbidden_key_scan_passed",
    "cs07_reviewer_selection_form_freeze_allowed_next",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "selection_form_status_ref",
    "selection_form_status",
    "selection_form_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "packet_scan_ready_for_form_freeze",
    "selection_only",
    "selection_only_form",
    "selection_form_current_compatibility_checked",
    "selection_form_structure_frozen",
    "selection_form_bodyfree_only",
    "local_only",
    "must_not_export",
    "body_full_packet_content_available_to_local_reviewer_only",
    "rating_axis_profile_ref",
    "rating_axis_refs",
    "rating_axis_count",
    "rating_axis_target_thresholds",
    "score_option_refs",
    "score_option_count",
    "verdict_option_refs",
    "verdict_option_count",
    "sanitized_reason_id_option_refs",
    "sanitized_reason_id_option_count",
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
    *P7_R54_AHR_CS08_PROHIBITED_FORM_FALSE_FLAG_REFS,
    "actual_human_review_operation_receipt_intake_allowed_next",
    "actual_review_execution_blocked_until_operation_receipt",
    "actual_human_review_completion_claim_blocked_here",
    "actual_rating_or_question_rows_claim_blocked_here",
    "disposal_receipt_claim_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs08_schema_version",
    "cs08_material_ref",
    "cs08_next_required_step",
    "cs08_selection_form_status_ref",
    "cs08_actual_human_review_operation_receipt_intake_allowed_next",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "operation_status_ref",
    "operation_receipt_status_ref",
    "operation_receipt_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "selection_form_ready_for_operation_receipt_intake",
    "operation_receipt_ref",
    "operation_receipt_ref_present",
    "operation_receipt_bodyfree_only",
    "reviewer_person_ref",
    "reviewer_person_ref_present",
    "reviewer_is_person",
    "reviewer_person_confirmed",
    "reviewer_local_only_read_receipt_present",
    "review_started_at_bucket_ref",
    "review_completed_at_bucket_ref",
    "review_time_bucket_refs_present",
    "required_case_count",
    "reviewed_case_count",
    "selection_row_count",
    "reviewed_case_count_complete",
    "selection_row_count_complete",
    "selection_form_used",
    "local_only",
    "must_not_export",
    "selection_only",
    "body_full_packet_read_local_only",
    "body_full_packet_content_available_to_local_reviewer_only",
    *P7_R54_AHR_CS09_BODYFREE_RECEIPT_FALSE_FLAG_REFS,
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_operation_receipt_intaken_here",
    "actual_human_review_operation_receipt_bodyfree_only",
    "actual_human_review_operation_complete",
    "actual_human_review_complete",
    "actual_review_evidence_complete",
    "sanitized_review_result_row_intake_allowed_next",
    "sanitized_review_result_rows_materialized_here",
    "rating_rows_materialized_here",
    "question_need_observation_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS
)


def _false_flags_allowing(*, allowed_true_refs: tuple[str, ...] = ()) -> dict[str, bool]:
    allowed = set(allowed_true_refs)
    return {key: False for key in P7_R54_AHR_CS_FALSE_FLAG_REFS if key not in allowed}


def _add_false_flags_preserving_allowed(material: dict[str, Any], *, allowed_true_refs: tuple[str, ...] = ()) -> None:
    allowed = set(allowed_true_refs)
    for key in P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if key not in allowed:
            material.setdefault(key, False)


def _assert_bodyfree_no_touch_base_allowing_actual_review_receipt(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, operation_step_ref: str, source: str
) -> None:
    expected_base = {
        "schema_version": schema_version,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": policy_section,
        "operation_step_ref": operation_step_ref,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "source_mode": P7_SOURCE_MODE,
    }
    for key, expected in expected_base.items():
        if data.get(key) != expected:
            raise ValueError(f"{source} {key} changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} Git connection flags must remain false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if _contains_forbidden_body_or_question_key(data):
        raise ValueError(f"{source} contains a forbidden body/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    for key in P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if key not in P7_R54_AHR_CS09_ALLOWED_TRUE_FALSE_FLAG_REFS and data.get(key) is not False:
            raise ValueError(f"{source} {key} must remain false")
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        flags = data.get(flag_map_key)
        if not isinstance(flags, Mapping):
            raise ValueError(f"{source} {flag_map_key} must be a mapping")
        _assert_all_false(flags, source=f"{source} {flag_map_key}")


def _cs08_status_and_blockers(
    *,
    scan_ready: bool,
    packet_completeness_passed: bool,
    export_denylist_scan_passed: bool,
    forbidden_key_scan_passed: bool,
    reviewer_selection_allowed: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not scan_ready:
        blockers.append("cs07_packet_scan_not_ready")
    if not packet_completeness_passed:
        blockers.append("cs07_packet_completeness_not_passed")
    if not export_denylist_scan_passed:
        blockers.append("cs07_export_denylist_scan_not_passed")
    if not forbidden_key_scan_passed:
        blockers.append("cs07_forbidden_key_scan_not_passed")
    if not reviewer_selection_allowed:
        blockers.append("cs07_reviewer_selection_form_freeze_not_allowed")
    blockers = _cs_dedupe_identifiers(blockers)
    if blockers:
        return P7_R54_AHR_CS08_FORM_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF, [P7_R54_AHR_CS08_READY_REASON_REF], []


def build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility(
    *,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Build CS08 selection-only reviewer form current compatibility material."""

    cs07 = dict(
        packet_completeness_export_denylist_scan or build_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan()
    )
    assert_p7_r54_ahr_cs07_packet_completeness_export_denylist_scan_contract(cs07)
    session_id = _safe_review_session_id(review_session_id or cs07.get("review_session_id"))
    scan_ready = (
        cs07.get("scan_status_ref") == P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF
        and cs07.get("next_required_step") == P7_R54_AHR_CS08_STEP_REF
        and cs07.get("reviewer_selection_form_freeze_allowed_next") is True
    )
    status_ref, reason_refs, blockers = _cs08_status_and_blockers(
        scan_ready=scan_ready,
        packet_completeness_passed=cs07.get("packet_completeness_passed") is True,
        export_denylist_scan_passed=cs07.get("export_denylist_scan_passed") is True,
        forbidden_key_scan_passed=cs07.get("forbidden_key_scan_passed") is True,
        reviewer_selection_allowed=cs07.get("reviewer_selection_form_freeze_allowed_next") is True,
    )
    ready = status_ref == P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS08_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS08_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs07_schema_version": cs07["schema_version"],
        "cs07_material_ref": cs07["material_id"],
        "cs07_next_required_step": cs07["next_required_step"],
        "cs07_scan_status_ref": cs07["scan_status_ref"],
        "cs07_packet_completeness_passed": cs07["packet_completeness_passed"],
        "cs07_export_denylist_scan_passed": cs07["export_denylist_scan_passed"],
        "cs07_forbidden_key_scan_passed": cs07["forbidden_key_scan_passed"],
        "cs07_reviewer_selection_form_freeze_allowed_next": cs07["reviewer_selection_form_freeze_allowed_next"],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "selection_form_status_ref": status_ref,
        "selection_form_status": status_ref,
        "selection_form_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "packet_scan_ready_for_form_freeze": scan_ready,
        "selection_only": ready,
        "selection_only_form": ready,
        "selection_form_current_compatibility_checked": ready,
        "selection_form_structure_frozen": ready,
        "selection_form_bodyfree_only": ready,
        "local_only": cs07.get("local_only") is True,
        "must_not_export": cs07.get("must_not_export") is True,
        "body_full_packet_content_available_to_local_reviewer_only": ready,
        "rating_axis_profile_ref": P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF if ready else "",
        "rating_axis_refs": list(P7_R54_AHR_CS04_RATING_AXIS_REFS) if ready else [],
        "rating_axis_count": len(P7_R54_AHR_CS04_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS) if ready else {},
        "score_option_refs": list(P7_R54_AHR_CS08_SCORE_OPTION_REFS) if ready else [],
        "score_option_count": len(P7_R54_AHR_CS08_SCORE_OPTION_REFS) if ready else 0,
        "verdict_option_refs": list(P7_R54_AHR_CS08_VERDICT_OPTION_REFS) if ready else [],
        "verdict_option_count": len(P7_R54_AHR_CS08_VERDICT_OPTION_REFS) if ready else 0,
        "sanitized_reason_id_option_refs": list(P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS) if ready else [],
        "sanitized_reason_id_option_count": len(P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS) if ready else 0,
        "readfeel_blocker_id_option_refs": list(P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS) if ready else [],
        "readfeel_blocker_id_option_count": len(P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS) if ready else 0,
        "execution_blocker_id_option_refs": list(P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS) if ready else [],
        "execution_blocker_id_option_count": len(P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS) if ready else 0,
        "question_need_primary_class_options": list(P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS) if ready else [],
        "question_need_primary_class_option_count": len(P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS) if ready else 0,
        "ambiguity_kind_option_refs": list(P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS) if ready else [],
        "ambiguity_kind_option_count": len(P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS) if ready else 0,
        "one_question_fit_option_refs": list(P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS) if ready else [],
        "one_question_fit_option_count": len(P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS) if ready else 0,
        "repair_required_option_refs": list(P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS) if ready else [],
        "repair_required_option_count": len(P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS) if ready else 0,
        "plan_candidate_flag_refs": list(P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS) if ready else [],
        "plan_candidate_flag_count": len(P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS) if ready else 0,
        **{key: False for key in P7_R54_AHR_CS08_PROHIBITED_FORM_FALSE_FLAG_REFS},
        "actual_human_review_operation_receipt_intake_allowed_next": ready,
        "actual_review_execution_blocked_until_operation_receipt": True,
        "actual_human_review_completion_claim_blocked_here": True,
        "actual_rating_or_question_rows_claim_blocked_here": True,
        "disposal_receipt_claim_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CS08_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS07_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CS08_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS07_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CS09_STEP_REF if ready else P7_R54_AHR_CS08_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    material.update(_false_flags())
    return material


def assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS08 reviewer selection form current compatibility",
    )
    _assert_bodyfree_no_touch_base(
        data,
        schema_version=P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS08_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS08_STEP_REF,
        source="P7-R54-AHR-CS08 reviewer selection form current compatibility",
    )
    if data.get("cs07_schema_version") != P7_R54_AHR_CS07_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS08 must follow CS07 packet scan")
    if data.get("cs07_scan_status_ref") == P7_R54_AHR_CS07_SCAN_PASSED_STATUS_REF:
        if data.get("cs07_next_required_step") != P7_R54_AHR_CS08_STEP_REF:
            raise ValueError("P7-R54-AHR-CS08 must follow CS07 next step")
    elif data.get("cs07_next_required_step") != P7_R54_AHR_CS07_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CS08 blocked predecessor must preserve CS07 repair next step")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS08 reviewer form")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS08 reviewer form")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS08 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS08 historical basis ref changed")
    if data.get("selection_form_status_ref") not in P7_R54_AHR_CS08_ALLOWED_FORM_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS08 selection form status changed")
    if data.get("selection_form_status") != data.get("selection_form_status_ref"):
        raise ValueError("P7-R54-AHR-CS08 selection form status alias changed")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=220) for value in data.get("execution_blocker_ids") or []])
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR-CS08 open blockers must match blockers")
    for key in P7_R54_AHR_CS08_PROHIBITED_FORM_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS08 must keep {key}=False")
    for key in (
        "local_only",
        "must_not_export",
        "actual_review_execution_blocked_until_operation_receipt",
        "actual_human_review_completion_claim_blocked_here",
        "actual_rating_or_question_rows_claim_blocked_here",
        "disposal_receipt_claim_blocked_here",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-CS08 must keep {key}=True")
    ready = data.get("selection_form_status_ref") == P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS08 ready form must not carry blockers")
        for key in (
            "packet_scan_ready_for_form_freeze",
            "selection_only",
            "selection_only_form",
            "selection_form_current_compatibility_checked",
            "selection_form_structure_frozen",
            "selection_form_bodyfree_only",
            "body_full_packet_content_available_to_local_reviewer_only",
            "actual_human_review_operation_receipt_intake_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS08 ready form must keep {key}=True")
        expected_options: tuple[tuple[str, Sequence[Any] | Mapping[str, Any], str], ...] = (
            ("rating_axis_refs", P7_R54_AHR_CS04_RATING_AXIS_REFS, "rating axes"),
            ("score_option_refs", P7_R54_AHR_CS08_SCORE_OPTION_REFS, "score options"),
            ("verdict_option_refs", P7_R54_AHR_CS08_VERDICT_OPTION_REFS, "verdict options"),
            ("sanitized_reason_id_option_refs", P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS, "reason options"),
            ("readfeel_blocker_id_option_refs", P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS, "readfeel blockers"),
            ("execution_blocker_id_option_refs", P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS, "execution blockers"),
            ("question_need_primary_class_options", P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS, "question classes"),
            ("ambiguity_kind_option_refs", P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS, "ambiguity options"),
            ("one_question_fit_option_refs", P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS, "one-question fit options"),
            ("repair_required_option_refs", P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS, "repair options"),
            ("plan_candidate_flag_refs", P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS, "plan flags"),
        )
        for field, expected, label in expected_options:
            if list(data.get(field) or []) != list(expected):
                raise ValueError(f"P7-R54-AHR-CS08 {label} changed")
        if data.get("rating_axis_profile_ref") != P7_R54_AHR_CS04_REVIEW_AXIS_PROFILE_REF:
            raise ValueError("P7-R54-AHR-CS08 rating axis profile changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-CS08 thresholds changed")
        expected_counts = (
            ("rating_axis_count", len(P7_R54_AHR_CS04_RATING_AXIS_REFS)),
            ("score_option_count", len(P7_R54_AHR_CS08_SCORE_OPTION_REFS)),
            ("verdict_option_count", len(P7_R54_AHR_CS08_VERDICT_OPTION_REFS)),
            ("sanitized_reason_id_option_count", len(P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS)),
            ("readfeel_blocker_id_option_count", len(P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS)),
            ("execution_blocker_id_option_count", len(P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS)),
            ("question_need_primary_class_option_count", len(P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS)),
            ("ambiguity_kind_option_count", len(P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS)),
            ("one_question_fit_option_count", len(P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS)),
            ("repair_required_option_count", len(P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS)),
            ("plan_candidate_flag_count", len(P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS)),
        )
        for field, expected in expected_counts:
            if data.get(field) != expected:
                raise ValueError(f"P7-R54-AHR-CS08 {field} changed")
        if data.get("selection_form_reason_refs") != [P7_R54_AHR_CS08_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS08 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS08_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS08 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS08_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS08 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS09_STEP_REF:
            raise ValueError("P7-R54-AHR-CS08 next step changed")
    else:
        if data.get("selection_form_status_ref") != P7_R54_AHR_CS08_FORM_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS08 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS08 blocked form must carry blockers")
        for key in (
            "selection_only",
            "selection_only_form",
            "selection_form_current_compatibility_checked",
            "selection_form_structure_frozen",
            "selection_form_bodyfree_only",
            "body_full_packet_content_available_to_local_reviewer_only",
            "actual_human_review_operation_receipt_intake_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-CS08 blocked form must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR_CS08_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS08 blocked next step changed")
    return True


def _cs09_status_and_blockers(
    *,
    form_ready: bool,
    operation_receipt_ref: str,
    reviewer_person_ref: str,
    reviewer_is_person: bool,
    reviewer_person_confirmed: bool,
    reviewer_local_only_read_receipt_present: bool,
    actual_human_review_operation_run: bool,
    actual_human_review_executed_by_person: bool,
    review_started_at_bucket_ref: str,
    review_completed_at_bucket_ref: str,
    reviewed_case_count: int,
    selection_row_count: int,
    selection_form_used: bool,
    local_only: bool,
    must_not_export: bool,
    selection_only: bool,
    body_full_packet_content_included: bool,
    raw_input_included: bool,
    raw_body_included: bool,
    returned_emlis_body_included: bool,
    history_surface_included: bool,
    comment_text_included: bool,
    reviewer_free_text_included: bool,
    reviewer_notes_body_included: bool,
    question_text_included: bool,
    draft_question_text_included: bool,
    local_absolute_path_included: bool,
    body_hash_included: bool,
    packet_content_included: bool,
    terminal_output_body_included: bool,
) -> tuple[str, list[str], list[str]]:
    blockers: list[str] = []
    if not form_ready:
        blockers.append("cs08_reviewer_selection_form_not_ready")
    if operation_receipt_ref != P7_R54_AHR_CS09_OPERATION_RECEIPT_REF:
        blockers.append("operation_receipt_ref_missing_or_unexpected")
    if not reviewer_person_ref:
        blockers.append("reviewer_person_ref_missing")
    if not reviewer_is_person:
        blockers.append("reviewer_is_not_person")
    if not reviewer_person_confirmed:
        blockers.append("reviewer_person_not_confirmed")
    if not reviewer_local_only_read_receipt_present:
        blockers.append("reviewer_local_only_read_receipt_missing")
    if not actual_human_review_operation_run:
        blockers.append("actual_human_review_operation_run_not_confirmed")
    if not actual_human_review_executed_by_person:
        blockers.append("actual_human_review_executed_by_person_not_confirmed")
    if not review_started_at_bucket_ref or not review_completed_at_bucket_ref:
        blockers.append("review_time_bucket_refs_missing")
    if reviewed_case_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("reviewed_case_count_not_24")
    if selection_row_count != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("selection_row_count_not_24")
    if not selection_form_used:
        blockers.append("selection_form_not_used")
    if not local_only:
        blockers.append("local_only_not_confirmed")
    if not must_not_export:
        blockers.append("must_not_export_not_confirmed")
    if not selection_only:
        blockers.append("selection_only_not_confirmed")
    forbidden_flags = {
        "body_full_packet_content_included": body_full_packet_content_included,
        "raw_input_included": raw_input_included,
        "raw_body_included": raw_body_included,
        "returned_emlis_body_included": returned_emlis_body_included,
        "history_surface_included": history_surface_included,
        "comment_text_included": comment_text_included,
        "reviewer_free_text_included": reviewer_free_text_included,
        "reviewer_notes_body_included": reviewer_notes_body_included,
        "question_text_included": question_text_included,
        "draft_question_text_included": draft_question_text_included,
        "local_absolute_path_included": local_absolute_path_included,
        "body_hash_included": body_hash_included,
        "packet_content_included": packet_content_included,
        "terminal_output_body_included": terminal_output_body_included,
    }
    blockers.extend([key for key, value in forbidden_flags.items() if value is True])
    blockers = _cs_dedupe_identifiers(blockers)
    if blockers:
        return P7_R54_AHR_CS09_OPERATION_BLOCKED_STATUS_REF, blockers, blockers
    return P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF, [P7_R54_AHR_CS09_READY_REASON_REF], []


def build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake(
    *,
    reviewer_selection_form_current_compatibility: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
    operation_receipt_ref: Any = "",
    reviewer_person_ref: Any = "",
    reviewer_is_person: bool = False,
    reviewer_person_confirmed: bool = False,
    reviewer_local_only_read_receipt_present: bool = False,
    actual_human_review_operation_run: bool = False,
    actual_human_review_executed_by_person: bool = False,
    review_started_at_bucket_ref: Any = "",
    review_completed_at_bucket_ref: Any = "",
    reviewed_case_count: int = 0,
    selection_row_count: int = 0,
    selection_form_used: bool = True,
    local_only: bool = True,
    must_not_export: bool = True,
    selection_only: bool = True,
    body_full_packet_content_included: bool = False,
    raw_input_included: bool = False,
    raw_body_included: bool = False,
    returned_emlis_body_included: bool = False,
    history_surface_included: bool = False,
    comment_text_included: bool = False,
    reviewer_free_text_included: bool = False,
    reviewer_notes_body_included: bool = False,
    question_text_included: bool = False,
    draft_question_text_included: bool = False,
    local_absolute_path_included: bool = False,
    body_hash_included: bool = False,
    packet_content_included: bool = False,
    terminal_output_body_included: bool = False,
) -> dict[str, Any]:
    """Intake a body-free CS09 operation receipt without running the review."""

    form = dict(
        reviewer_selection_form_current_compatibility
        or build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility()
    )
    assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract(form)
    session_id = _safe_review_session_id(review_session_id or form.get("review_session_id"))
    receipt_ref = clean_identifier(operation_receipt_ref, default="", max_length=220)
    reviewer_ref = clean_identifier(reviewer_person_ref, default="", max_length=160)
    started_ref = clean_identifier(review_started_at_bucket_ref, default="", max_length=160)
    completed_ref = clean_identifier(review_completed_at_bucket_ref, default="", max_length=160)
    form_ready = (
        form.get("selection_form_status_ref") == P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF
        and form.get("actual_human_review_operation_receipt_intake_allowed_next") is True
        and form.get("next_required_step") == P7_R54_AHR_CS09_STEP_REF
    )
    status_ref, reason_refs, blockers = _cs09_status_and_blockers(
        form_ready=form_ready,
        operation_receipt_ref=receipt_ref,
        reviewer_person_ref=reviewer_ref,
        reviewer_is_person=bool(reviewer_is_person),
        reviewer_person_confirmed=bool(reviewer_person_confirmed),
        reviewer_local_only_read_receipt_present=bool(reviewer_local_only_read_receipt_present),
        actual_human_review_operation_run=bool(actual_human_review_operation_run),
        actual_human_review_executed_by_person=bool(actual_human_review_executed_by_person),
        review_started_at_bucket_ref=started_ref,
        review_completed_at_bucket_ref=completed_ref,
        reviewed_case_count=int(reviewed_case_count),
        selection_row_count=int(selection_row_count),
        selection_form_used=bool(selection_form_used),
        local_only=bool(local_only),
        must_not_export=bool(must_not_export),
        selection_only=bool(selection_only),
        body_full_packet_content_included=bool(body_full_packet_content_included),
        raw_input_included=bool(raw_input_included),
        raw_body_included=bool(raw_body_included),
        returned_emlis_body_included=bool(returned_emlis_body_included),
        history_surface_included=bool(history_surface_included),
        comment_text_included=bool(comment_text_included),
        reviewer_free_text_included=bool(reviewer_free_text_included),
        reviewer_notes_body_included=bool(reviewer_notes_body_included),
        question_text_included=bool(question_text_included),
        draft_question_text_included=bool(draft_question_text_included),
        local_absolute_path_included=bool(local_absolute_path_included),
        body_hash_included=bool(body_hash_included),
        packet_content_included=bool(packet_content_included),
        terminal_output_body_included=bool(terminal_output_body_included),
    )
    ready = status_ref == P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS09_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS09_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs08_schema_version": form["schema_version"],
        "cs08_material_ref": form["material_id"],
        "cs08_next_required_step": form["next_required_step"],
        "cs08_selection_form_status_ref": form["selection_form_status_ref"],
        "cs08_actual_human_review_operation_receipt_intake_allowed_next": form[
            "actual_human_review_operation_receipt_intake_allowed_next"
        ],
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "operation_status_ref": status_ref,
        "operation_receipt_status_ref": status_ref,
        "operation_receipt_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "selection_form_ready_for_operation_receipt_intake": form_ready,
        "operation_receipt_ref": receipt_ref if ready else "",
        "operation_receipt_ref_present": receipt_ref == P7_R54_AHR_CS09_OPERATION_RECEIPT_REF,
        "operation_receipt_bodyfree_only": True,
        "reviewer_person_ref": reviewer_ref if reviewer_ref else "",
        "reviewer_person_ref_present": bool(reviewer_ref),
        "reviewer_is_person": bool(reviewer_is_person),
        "reviewer_person_confirmed": bool(reviewer_person_confirmed),
        "reviewer_local_only_read_receipt_present": bool(reviewer_local_only_read_receipt_present),
        "review_started_at_bucket_ref": started_ref if started_ref else "",
        "review_completed_at_bucket_ref": completed_ref if completed_ref else "",
        "review_time_bucket_refs_present": bool(started_ref and completed_ref),
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(reviewed_case_count),
        "selection_row_count": int(selection_row_count),
        "reviewed_case_count_complete": int(reviewed_case_count) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "selection_row_count_complete": int(selection_row_count) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "selection_form_used": bool(selection_form_used),
        "local_only": bool(local_only),
        "must_not_export": bool(must_not_export),
        "selection_only": bool(selection_only),
        "body_full_packet_read_local_only": ready,
        "body_full_packet_content_available_to_local_reviewer_only": ready,
        **{key: False for key in P7_R54_AHR_CS09_BODYFREE_RECEIPT_FALSE_FLAG_REFS},
        "actual_human_review_operation_run": bool(actual_human_review_operation_run) and ready,
        "actual_human_review_executed_by_person": bool(actual_human_review_executed_by_person and reviewer_is_person) and ready,
        "actual_human_review_run_here": False,
        "actual_human_review_operation_receipt_intaken_here": ready,
        "actual_human_review_operation_receipt_bodyfree_only": True,
        "actual_human_review_operation_complete": ready,
        "actual_human_review_complete": False,
        "actual_review_evidence_complete": False,
        "sanitized_review_result_row_intake_allowed_next": ready,
        "sanitized_review_result_rows_materialized_here": False,
        "rating_rows_materialized_here": False,
        "question_need_observation_rows_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CS09_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS08_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(
            P7_R54_AHR_CS09_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS08_NOT_YET_IMPLEMENTED_STEPS
        ),
        "next_required_step": P7_R54_AHR_CS10_STEP_REF if ready else P7_R54_AHR_CS09_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS09_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract(
    data: Mapping[str, Any]
) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS09 actual human review operation receipt intake",
    )
    _assert_bodyfree_no_touch_base_allowing_actual_review_receipt(
        data,
        schema_version=P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS09_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS09_STEP_REF,
        source="P7-R54-AHR-CS09 actual human review operation receipt intake",
    )
    if data.get("cs08_schema_version") != P7_R54_AHR_CS08_REVIEWER_SELECTION_FORM_CURRENT_COMPATIBILITY_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS09 must follow CS08 reviewer selection form")
    if data.get("cs08_selection_form_status_ref") == P7_R54_AHR_CS08_FORM_FROZEN_STATUS_REF:
        if data.get("cs08_next_required_step") != P7_R54_AHR_CS09_STEP_REF:
            raise ValueError("P7-R54-AHR-CS09 must follow CS08 next step")
    elif data.get("cs08_next_required_step") != P7_R54_AHR_CS08_BLOCKED_NEXT_REQUIRED_STEP_REF:
        raise ValueError("P7-R54-AHR-CS09 blocked predecessor must preserve CS08 repair next step")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS09 operation receipt")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS09 operation receipt")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS09 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS09 historical basis ref changed")
    if data.get("operation_status_ref") not in P7_R54_AHR_CS09_ALLOWED_OPERATION_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS09 operation status changed")
    if data.get("operation_receipt_status_ref") != data.get("operation_status_ref"):
        raise ValueError("P7-R54-AHR-CS09 operation status alias changed")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=220) for value in data.get("execution_blocker_ids") or []])
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("P7-R54-AHR-CS09 open blockers must match blockers")
    for key in P7_R54_AHR_CS09_BODYFREE_RECEIPT_FALSE_FLAG_REFS:
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS09 must keep {key}=False")
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "actual_review_evidence_complete",
        "sanitized_review_result_rows_materialized_here",
        "rating_rows_materialized_here",
        "question_need_observation_rows_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "p5_confirmed_final",
        "p6_start_allowed",
        "p7_complete",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS09 must keep {key}=False")
    for key in (
        "operation_receipt_bodyfree_only",
        "actual_human_review_operation_receipt_bodyfree_only",
        "r52_reintake_claim_blocked_here",
        "p6_p8_release_promotion_blocked_here",
        "p5_finalization_blocked_here",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-CS09 must keep {key}=True")
    ready = data.get("operation_status_ref") == P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS09 ready receipt must not carry blockers")
        for key in (
            "selection_form_ready_for_operation_receipt_intake",
            "operation_receipt_ref_present",
            "reviewer_person_ref_present",
            "reviewer_is_person",
            "reviewer_person_confirmed",
            "reviewer_local_only_read_receipt_present",
            "review_time_bucket_refs_present",
            "reviewed_case_count_complete",
            "selection_row_count_complete",
            "selection_form_used",
            "local_only",
            "must_not_export",
            "selection_only",
            "body_full_packet_read_local_only",
            "body_full_packet_content_available_to_local_reviewer_only",
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "actual_human_review_operation_receipt_intaken_here",
            "actual_human_review_operation_complete",
            "sanitized_review_result_row_intake_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS09 ready receipt must keep {key}=True")
        if data.get("operation_receipt_ref") != P7_R54_AHR_CS09_OPERATION_RECEIPT_REF:
            raise ValueError("P7-R54-AHR-CS09 operation receipt ref changed")
        if data.get("reviewed_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CS09 reviewed case count changed")
        if data.get("selection_row_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CS09 selection row count changed")
        if data.get("operation_receipt_reason_refs") != [P7_R54_AHR_CS09_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS09 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS09_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS09 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS09_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS09 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS10_STEP_REF:
            raise ValueError("P7-R54-AHR-CS09 next step changed")
    else:
        if data.get("operation_status_ref") != P7_R54_AHR_CS09_OPERATION_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS09 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS09 blocked receipt must carry blockers")
        for key in (
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "actual_human_review_operation_receipt_intaken_here",
            "actual_human_review_operation_complete",
            "sanitized_review_result_row_intake_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-CS09 blocked receipt must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR_CS09_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS09 blocked next step changed")
    return True


# Compatibility aliases for CS08/CS09 design wording.
build_p7_r54_ahr_cs08_reviewer_selection_form_freeze = (
    build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility
)
assert_p7_r54_ahr_cs08_reviewer_selection_form_freeze_contract = (
    assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_reviewer_selection_form_current_compatibility_bodyfree = (
    build_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_reviewer_selection_form_current_compatibility_bodyfree_contract = (
    assert_p7_r54_ahr_cs08_reviewer_selection_form_current_compatibility_contract
)
build_p7_r54_ahr_cs09_actual_human_review_local_only_operation_receipt_intake = (
    build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake
)
assert_p7_r54_ahr_cs09_actual_human_review_local_only_operation_receipt_intake_contract = (
    assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_actual_human_review_operation_receipt_intake_bodyfree = (
    build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_actual_human_review_operation_receipt_intake_bodyfree_contract = (
    assert_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake_contract
)



# ---------------------------------------------------------------------------
# CS10 / CS11 sanitized review result row intake and rating row normalization.
#
# CS10 accepts only selection-only, body-free rows that are explicitly tied to
# the CS09 local-only operation receipt and current 262/84/257/170 manifest refs.
# CS11 derives body-free rating rows / aggregate stats from CS10 rows.  Neither
# step creates question text, question observations, disposal receipt, R52
# execution, P5 final, P6/P8 start, P7 completion, or release readiness.
# ---------------------------------------------------------------------------

P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs10_sanitized_review_result_row_intake.bodyfree.v1"
)
P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs11_rating_row_normalization.bodyfree.v1"
)
P7_R54_AHR_CS_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION
)
P7_R54_AHR_CS_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
)

P7_R54_AHR_CS10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS09_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS10_STEP_REF,
)
P7_R54_AHR_CS10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[11:]
P7_R54_AHR_CS11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS10_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS11_STEP_REF,
)
P7_R54_AHR_CS11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[12:]

P7_R54_AHR_CS10_INTAKE_READY_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_SANITIZED_REVIEW_RESULT_ROW_INTAKE_READY_BODYFREE"
)
P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_SANITIZED_REVIEW_RESULT_ROW_INTAKE_BLOCKED"
)
P7_R54_AHR_CS10_ALLOWED_INTAKE_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS10_INTAKE_READY_STATUS_REF,
    P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS10_READY_REASON_REF: Final = (
    "r54_ahr_cs_sanitized_review_result_rows_intaken_bodyfree_current_snapshot"
)
P7_R54_AHR_CS10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS10_repair_sanitized_review_result_rows_before_rating_row_normalization"
)
P7_R54_AHR_CS10_REVIEW_RESULT_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs10_sanitized_review_result_row.bodyfree.v1"
)

P7_R54_AHR_CS11_NORMALIZED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_RATING_ROW_NORMALIZATION_READY_BODYFREE"
)
P7_R54_AHR_CS11_BLOCKED_STATUS_REF: Final = "CURRENT_SNAPSHOT_RATING_ROW_NORMALIZATION_BLOCKED"
P7_R54_AHR_CS11_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS11_NORMALIZED_STATUS_REF,
    P7_R54_AHR_CS11_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS11_READY_REASON_REF: Final = (
    "r54_ahr_cs_rating_rows_normalized_bodyfree_from_sanitized_review_results"
)
P7_R54_AHR_CS11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS11_repair_rating_row_normalization_before_blocker_question_observation_normalization"
)
P7_R54_AHR_CS11_RATING_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs11_rating_row.bodyfree.v1"
)

P7_R54_AHR_CS10_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
)
P7_R54_AHR_CS11_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS10_ALLOWED_TRUE_FALSE_FLAG_REFS,
    "actual_rating_rows_materialized_here",
)
P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_content_included",
    "reviewer_free_text_included",
    "reviewer_notes_body_included",
    "raw_body_included",
    "returned_emlis_body_included",
    "history_surface_included",
    "comment_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_hash_included",
    "packet_content_included",
)
P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS
)

P7_R54_AHR_CS10_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_result_row_ref",
    "review_session_id",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "subscription_tier_ref",
    "history_evidence_policy_ref",
    "current_basis_ref",
    "source_operation_receipt_ref",
    "reviewer_person_ref",
    "reviewed_at_bucket_ref",
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
    *P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_CS11_RATING_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "current_basis_ref",
    "axis_scores",
    "axis_score_count",
    "axis_targets",
    "below_target_axis_refs",
    "below_target_axis_count",
    "verdict",
    "sanitized_reason_ids",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "one_question_fit_ref",
    "repair_required_refs",
    "plan_candidate_flags",
    *P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs09_schema_version",
    "cs09_material_ref",
    "cs09_next_required_step",
    "cs09_operation_status_ref",
    "cs09_actual_human_review_operation_run",
    "cs09_actual_human_review_executed_by_person",
    "cs09_reviewed_case_count",
    "cs09_selection_row_count",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "sanitized_review_result_row_intake_status_ref",
    "sanitized_review_result_row_intake_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "operation_ready_for_sanitized_result_intake",
    "required_case_count",
    "received_review_result_row_count",
    "review_result_row_count",
    "sanitized_review_result_row_count",
    "reviewed_case_count",
    "selection_row_count",
    "review_result_rows",
    "review_result_row_refs",
    "review_result_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "reviewer_person_refs",
    "reviewer_person_ref_count",
    "reviewed_at_bucket_refs_present",
    "axis_refs",
    "axis_count",
    "axis_score_count_per_row",
    "rating_axis_target_thresholds",
    "verdict_counts",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "question_need_primary_class_counts",
    "rows_match_current_24_case_manifest",
    "case_ref_ids_match_manifest",
    "rows_bodyfree_only",
    "rows_selection_only",
    "rows_have_required_axis_scores",
    "all_scores_in_allowed_options",
    "all_verdicts_in_allowed_options",
    "all_reason_ids_in_allowed_options",
    "rows_have_allowed_question_observation_refs",
    "rows_have_no_body_or_question_or_path_or_hash",
    "sanitized_review_result_rows_intaken_here",
    "actual_sanitized_review_result_rows_intaken_here",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "rating_row_normalization_allowed_next",
    "rating_rows_materialized_here",
    "question_need_observation_rows_materialized_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs10_schema_version",
    "cs10_material_ref",
    "cs10_next_required_step",
    "cs10_sanitized_review_result_row_intake_status_ref",
    "cs10_rating_row_normalization_allowed_next",
    "cs10_sanitized_review_result_row_count",
    "cs10_review_result_row_count",
    "cs10_case_ref_id_count",
    "cs10_actual_human_review_operation_run",
    "cs10_actual_human_review_executed_by_person",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "rating_row_normalization_status_ref",
    "rating_row_normalization_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "sanitized_review_result_rows_ready_for_rating_normalization",
    "required_case_count",
    "source_sanitized_review_result_row_count",
    "rating_row_count",
    "rating_rows",
    "rating_row_refs",
    "rating_row_ref_count",
    "source_review_result_row_refs",
    "source_review_result_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "blind_case_ids",
    "blind_case_id_count",
    "blind_case_ids_unique",
    "packet_ref_ids",
    "packet_ref_id_count",
    "packet_ref_ids_unique",
    "axis_refs",
    "axis_count",
    "rating_axis_target_thresholds",
    "axis_averages",
    "rating_rows_bodyfree_only",
    "rating_rows_match_sanitized_review_result_case_refs",
    "rating_rows_have_required_axis_scores",
    "rating_scores_in_range",
    "rating_rows_have_allowed_verdict_refs",
    "below_target_axis_refs_by_case",
    "below_target_axis_ref_counts",
    "below_target_axis_counts",
    "below_target_case_count",
    "verdict_counts",
    "pass_case_count",
    "yellow_case_count",
    "repair_required_case_count",
    "red_case_count",
    "blocked_case_count",
    "not_reviewable_case_count",
    "readfeel_blocker_id_counts",
    "execution_blocker_id_counts",
    "readfeel_blocker_row_source_count",
    "execution_blocker_row_source_count",
    "rating_rows_normalized_here",
    "actual_rating_rows_materialized_here",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_review_evidence_complete",
    "blocker_question_need_observation_normalization_allowed_next",
    "question_need_observation_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS
)


def _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
    data: Mapping[str, Any], *, schema_version: str, policy_section: str, operation_step_ref: str, source: str,
    allowed_true_refs: tuple[str, ...]
) -> None:
    expected_base = {
        "schema_version": schema_version,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": policy_section,
        "operation_step_ref": operation_step_ref,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "source_mode": P7_SOURCE_MODE,
    }
    for key, expected in expected_base.items():
        if data.get(key) != expected:
            raise ValueError(f"{source} {key} changed")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} Git connection flags must remain false")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must remain body-free")
    if _contains_forbidden_body_or_question_key(data):
        raise ValueError(f"{source} contains a forbidden body/question/path/hash key")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)
    allowed = set(allowed_true_refs)
    for key in P7_R54_AHR_CS_FALSE_FLAG_REFS:
        if key not in allowed and data.get(key) is not False:
            raise ValueError(f"{source} {key} must remain false")
    for flag_map_key in ("public_contract", "r54_ahr_cs_no_touch_contract", "body_free_markers"):
        flags = data.get(flag_map_key)
        if not isinstance(flags, Mapping):
            raise ValueError(f"{source} {flag_map_key} must be a mapping")
        _assert_all_false(flags, source=f"{source} {flag_map_key}")


def _cs_manifest_rows_by_case_ref() -> dict[str, dict[str, Any]]:
    manifest = build_p7_r54_ahr_cs04_current_24_case_manifest_refreeze()
    return {str(row.get("case_ref_id")): dict(row) for row in manifest.get("case_manifest_rows", [])}


def _cs_clean_identifier_list(values: Any, *, limit: int = 40, max_length: int = 160) -> list[str]:
    if values is None:
        raw_values: list[Any] = []
    elif isinstance(values, Mapping):
        raw_values = list(values.values())
    elif isinstance(values, (str, bytes, bytearray)):
        raw_values = [values]
    elif isinstance(values, Sequence):
        raw_values = list(values)
    else:
        raw_values = [values]
    out: list[str] = []
    seen: set[str] = set()
    for value in raw_values:
        text = clean_identifier(value, max_length=max_length)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _cs_plan_candidate_flags(value: Any) -> dict[str, bool]:
    flags = {key: False for key in P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS}
    if isinstance(value, Mapping):
        for key in P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS:
            flags[key] = bool(value.get(key, False))
    flags["p8_implementation_spec_finalized_here"] = False
    return flags


def _cs_validate_and_sanitize_review_result_rows(
    rows: Sequence[Any], *, review_session_id: str, reviewer_person_ref: str, operation_receipt_ref: str
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    sanitized_rows: list[dict[str, Any]] = []
    expected_by_case_ref = _cs_manifest_rows_by_case_ref()
    if len(rows) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("review_result_row_count_not_24")
    seen_case_refs: set[str] = set()
    seen_blind_ids: set[str] = set()
    seen_packet_refs: set[str] = set()
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"review_result_row_{index:02d}_not_mapping")
            continue
        if _contains_forbidden_body_or_question_key(raw_row):
            blockers.append(f"review_result_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
            continue
        row = {str(key): value for key, value in raw_row.items()}
        case_ref_id = clean_identifier(row.get("case_ref_id"), default="", max_length=160)
        blind_case_id = clean_identifier(row.get("blind_case_id"), default="", max_length=160)
        packet_ref_id = clean_identifier(row.get("packet_ref_id"), default="", max_length=160)
        expected = expected_by_case_ref.get(case_ref_id)
        if not expected:
            blockers.append(f"review_result_row_{index:02d}_case_ref_not_in_current_manifest")
            continue
        if blind_case_id != expected.get("blind_case_id"):
            blockers.append(f"review_result_row_{index:02d}_blind_case_id_mismatch")
        if packet_ref_id != expected.get("packet_ref_id"):
            blockers.append(f"review_result_row_{index:02d}_packet_ref_id_mismatch")
        for field in ("case_family_ref", "case_role_ref", "subscription_tier_ref", "history_evidence_policy_ref"):
            if row.get(field) not in (None, "") and row.get(field) != expected.get(field):
                blockers.append(f"review_result_row_{index:02d}_{field}_mismatch")
        seen_case_refs.add(case_ref_id)
        seen_blind_ids.add(blind_case_id)
        seen_packet_refs.add(packet_ref_id)
        axis_scores_raw = row.get("axis_scores") if isinstance(row.get("axis_scores"), Mapping) else {}
        axis_scores: dict[str, float] = {}
        if set(axis_scores_raw) != set(P7_R54_AHR_CS04_RATING_AXIS_REFS):
            blockers.append(f"review_result_row_{index:02d}_axis_refs_mismatch")
        for axis_ref in P7_R54_AHR_CS04_RATING_AXIS_REFS:
            try:
                score = float(axis_scores_raw.get(axis_ref))
            except (TypeError, ValueError):
                blockers.append(f"review_result_row_{index:02d}_{axis_ref}_score_not_number")
                score = -1.0
            if score not in P7_R54_AHR_CS08_SCORE_OPTION_REFS:
                blockers.append(f"review_result_row_{index:02d}_{axis_ref}_score_not_allowed_option")
            if score < 0.0 or score > 1.0:
                blockers.append(f"review_result_row_{index:02d}_{axis_ref}_score_out_of_range")
            axis_scores[axis_ref] = score
        if row.get("axis_score_count") != len(P7_R54_AHR_CS04_RATING_AXIS_REFS):
            blockers.append(f"review_result_row_{index:02d}_axis_score_count_not_6")
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR_CS08_VERDICT_OPTION_REFS:
            blockers.append(f"review_result_row_{index:02d}_verdict_not_allowed")
        sanitized_reason_ids = _cs_clean_identifier_list(row.get("sanitized_reason_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS for item in sanitized_reason_ids):
            blockers.append(f"review_result_row_{index:02d}_sanitized_reason_id_not_allowed")
        readfeel_blocker_ids = _cs_clean_identifier_list(row.get("readfeel_blocker_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS for item in readfeel_blocker_ids):
            blockers.append(f"review_result_row_{index:02d}_readfeel_blocker_id_not_allowed")
        execution_blocker_ids = _cs_clean_identifier_list(row.get("execution_blocker_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS for item in execution_blocker_ids):
            blockers.append(f"review_result_row_{index:02d}_execution_blocker_id_not_allowed")
        question_need_primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=180)
        if question_need_primary_class not in P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS:
            blockers.append(f"review_result_row_{index:02d}_question_need_primary_class_not_allowed")
        ambiguity_kind_refs = _cs_clean_identifier_list(row.get("ambiguity_kind_refs") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS for item in ambiguity_kind_refs):
            blockers.append(f"review_result_row_{index:02d}_ambiguity_kind_ref_not_allowed")
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=180)
        if one_question_fit_ref not in P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append(f"review_result_row_{index:02d}_one_question_fit_ref_not_allowed")
        repair_required_refs = _cs_clean_identifier_list(row.get("repair_required_refs") or (), limit=20, max_length=180)
        if any(item not in P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS for item in repair_required_refs):
            blockers.append(f"review_result_row_{index:02d}_repair_required_ref_not_allowed")
        raw_plan_candidate_flags = row.get("plan_candidate_flags") if isinstance(row.get("plan_candidate_flags"), Mapping) else {}
        if raw_plan_candidate_flags.get("p8_implementation_spec_finalized_here") is True:
            blockers.append(f"review_result_row_{index:02d}_p8_implementation_spec_finalized_flag_true")
        plan_candidate_flags = _cs_plan_candidate_flags(row.get("plan_candidate_flags"))
        for flag_ref in P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS:
            if row.get(flag_ref) is not False:
                blockers.append(f"review_result_row_{index:02d}_{flag_ref}_not_false")
        if row.get("selection_only_row") is not True:
            blockers.append(f"review_result_row_{index:02d}_selection_only_row_not_true")
        if row.get("body_free") is not True:
            blockers.append(f"review_result_row_{index:02d}_body_free_not_true")
        if row.get("review_session_id") != review_session_id:
            blockers.append(f"review_result_row_{index:02d}_review_session_id_mismatch")
        if row.get("reviewer_person_ref") != reviewer_person_ref:
            blockers.append(f"review_result_row_{index:02d}_reviewer_person_ref_mismatch")
        reviewed_at_ref = clean_identifier(row.get("reviewed_at_bucket_ref"), default="", max_length=180)
        if not reviewed_at_ref:
            blockers.append(f"review_result_row_{index:02d}_reviewed_at_bucket_ref_missing")
        if row.get("current_basis_ref") not in (None, "", P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF):
            blockers.append(f"review_result_row_{index:02d}_current_basis_ref_mismatch")
        sanitized_rows.append(
            {
                "schema_version": P7_R54_AHR_CS10_REVIEW_RESULT_ROW_SCHEMA_VERSION,
                "review_result_row_ref": clean_identifier(
                    row.get("review_result_row_ref"), default=f"review_result_row_{index:03d}", max_length=160
                ),
                "review_session_id": review_session_id,
                "case_ref_id": case_ref_id,
                "blind_case_id": blind_case_id,
                "packet_ref_id": packet_ref_id,
                "case_family_ref": expected.get("case_family_ref"),
                "case_role_ref": expected.get("case_role_ref"),
                "subscription_tier_ref": expected.get("subscription_tier_ref"),
                "history_evidence_policy_ref": expected.get("history_evidence_policy_ref"),
                "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                "source_operation_receipt_ref": operation_receipt_ref,
                "reviewer_person_ref": reviewer_person_ref,
                "reviewed_at_bucket_ref": reviewed_at_ref,
                "axis_scores": axis_scores,
                "axis_score_count": len(P7_R54_AHR_CS04_RATING_AXIS_REFS),
                "verdict": verdict,
                "sanitized_reason_ids": sanitized_reason_ids,
                "readfeel_blocker_ids": readfeel_blocker_ids,
                "execution_blocker_ids": execution_blocker_ids,
                "question_need_primary_class": question_need_primary_class,
                "ambiguity_kind_refs": ambiguity_kind_refs,
                "one_question_fit_ref": one_question_fit_ref,
                "repair_required_refs": repair_required_refs,
                "plan_candidate_flags": plan_candidate_flags,
                "selection_only_row": True,
                **{key: False for key in P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS},
                "body_free": True,
            }
        )
    if len(seen_case_refs) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("case_ref_ids_not_unique_or_not_24")
    if len(seen_blind_ids) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("blind_case_ids_not_unique_or_not_24")
    if len(seen_packet_refs) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("packet_ref_ids_not_unique_or_not_24")
    if set(seen_case_refs) != set(expected_by_case_ref):
        blockers.append("case_ref_ids_do_not_match_current_24_case_manifest")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    if blockers:
        return [], blockers
    return sanitized_rows, []


def _cs_count_values(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        key = clean_identifier(row.get(field), max_length=180)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _cs_count_ids(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for item in row.get(field) or []:
            key = clean_identifier(item, max_length=180)
            if key:
                counts[key] = counts.get(key, 0) + 1
    return counts


def build_p7_r54_ahr_cs10_sanitized_review_result_row_intake(
    *,
    actual_human_review_operation_receipt_intake: Mapping[str, Any] | None = None,
    review_result_rows: Sequence[Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Intake CS10 sanitized selection-only review result rows as body-free refs."""

    operation = dict(actual_human_review_operation_receipt_intake or build_p7_r54_ahr_cs09_actual_human_review_operation_receipt_intake())
    session_id = _safe_review_session_id(review_session_id or operation.get("review_session_id"))
    rows_input = list(review_result_rows or [])
    operation_ready = operation.get("operation_status_ref") == P7_R54_AHR_CS09_OPERATION_RECEIPT_INTAKEN_STATUS_REF
    reviewer_person_ref = clean_identifier(
        operation.get("reviewer_person_ref"), default=P7_R54_AHR_CS09_REVIEWER_PERSON_REF_DEFAULT, max_length=160
    )
    operation_receipt_ref = clean_identifier(operation.get("operation_receipt_ref"), default="", max_length=220)
    sanitized_rows, row_blockers = _cs_validate_and_sanitize_review_result_rows(
        rows_input,
        review_session_id=session_id,
        reviewer_person_ref=reviewer_person_ref,
        operation_receipt_ref=operation_receipt_ref,
    )
    blockers: list[str] = []
    if not operation_ready:
        blockers.append("cs09_actual_human_review_operation_receipt_not_ready")
    if operation.get("next_required_step") != P7_R54_AHR_CS10_STEP_REF:
        blockers.append("cs09_next_step_not_sanitized_review_result_row_intake")
    if operation.get("actual_human_review_operation_run") is not True:
        blockers.append("cs09_actual_human_review_operation_run_not_confirmed")
    if operation.get("actual_human_review_executed_by_person") is not True:
        blockers.append("cs09_actual_human_review_executed_by_person_not_confirmed")
    if operation.get("reviewed_case_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("cs09_reviewed_case_count_not_24")
    if operation.get("selection_row_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("cs09_selection_row_count_not_24")
    blockers.extend(row_blockers)
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    ready = not blockers
    status_ref = P7_R54_AHR_CS10_INTAKE_READY_STATUS_REF if ready else P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR_CS10_READY_REASON_REF] if ready else blockers
    rows_for_output = sanitized_rows if ready else []
    row_refs = [str(row.get("review_result_row_ref")) for row in rows_for_output]
    case_refs = [str(row.get("case_ref_id")) for row in rows_for_output]
    blind_ids = [str(row.get("blind_case_id")) for row in rows_for_output]
    packet_refs = [str(row.get("packet_ref_id")) for row in rows_for_output]
    reviewer_refs = _cs_clean_identifier_list([row.get("reviewer_person_ref") for row in rows_for_output], limit=24, max_length=160)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS10_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS10_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs10_sanitized_review_result_row_intake_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs09_schema_version": operation.get("schema_version"),
        "cs09_material_ref": operation.get("material_id"),
        "cs09_next_required_step": operation.get("next_required_step"),
        "cs09_operation_status_ref": operation.get("operation_status_ref"),
        "cs09_actual_human_review_operation_run": operation.get("actual_human_review_operation_run") is True,
        "cs09_actual_human_review_executed_by_person": operation.get("actual_human_review_executed_by_person") is True,
        "cs09_reviewed_case_count": int(operation.get("reviewed_case_count") or 0),
        "cs09_selection_row_count": int(operation.get("selection_row_count") or 0),
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "sanitized_review_result_row_intake_status_ref": status_ref,
        "sanitized_review_result_row_intake_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "operation_ready_for_sanitized_result_intake": operation_ready,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "received_review_result_row_count": len(rows_input),
        "review_result_row_count": len(rows_for_output),
        "sanitized_review_result_row_count": len(rows_for_output),
        "reviewed_case_count": int(operation.get("reviewed_case_count") or 0) if operation_ready else 0,
        "selection_row_count": int(operation.get("selection_row_count") or 0) if operation_ready else 0,
        "review_result_rows": rows_for_output,
        "review_result_row_refs": row_refs,
        "review_result_row_ref_count": len(row_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewer_person_refs": reviewer_refs,
        "reviewer_person_ref_count": len(reviewer_refs),
        "reviewed_at_bucket_refs_present": ready,
        "axis_refs": list(P7_R54_AHR_CS04_RATING_AXIS_REFS),
        "axis_count": len(P7_R54_AHR_CS04_RATING_AXIS_REFS),
        "axis_score_count_per_row": len(P7_R54_AHR_CS04_RATING_AXIS_REFS) if ready else 0,
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS),
        "verdict_counts": _cs_count_values(rows_for_output, "verdict") if ready else {},
        "readfeel_blocker_row_count": sum(1 for row in rows_for_output if row.get("readfeel_blocker_ids")),
        "execution_blocker_row_count": sum(1 for row in rows_for_output if row.get("execution_blocker_ids")),
        "question_need_primary_class_counts": _cs_count_values(rows_for_output, "question_need_primary_class") if ready else {},
        "rows_match_current_24_case_manifest": ready,
        "case_ref_ids_match_manifest": ready,
        "rows_bodyfree_only": ready,
        "rows_selection_only": ready,
        "rows_have_required_axis_scores": ready,
        "all_scores_in_allowed_options": ready,
        "all_verdicts_in_allowed_options": ready,
        "all_reason_ids_in_allowed_options": ready,
        "rows_have_allowed_question_observation_refs": ready,
        "rows_have_no_body_or_question_or_path_or_hash": ready,
        "sanitized_review_result_rows_intaken_here": ready,
        "actual_sanitized_review_result_rows_intaken_here": ready,
        "actual_human_review_operation_run": operation.get("actual_human_review_operation_run") is True and ready,
        "actual_human_review_executed_by_person": operation.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "rating_row_normalization_allowed_next": ready,
        "rating_rows_materialized_here": False,
        "question_need_observation_rows_materialized_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CS10_IMPLEMENTED_STEPS if ready else (P7_R54_AHR_CS09_IMPLEMENTED_STEPS if operation_ready else P7_R54_AHR_CS08_IMPLEMENTED_STEPS)),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS10_NOT_YET_IMPLEMENTED_STEPS if ready else (P7_R54_AHR_CS09_NOT_YET_IMPLEMENTED_STEPS if operation_ready else P7_R54_AHR_CS08_NOT_YET_IMPLEMENTED_STEPS)),
        "next_required_step": P7_R54_AHR_CS11_STEP_REF if ready else P7_R54_AHR_CS10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS10_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS10 sanitized review result row intake",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS10_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS10_STEP_REF,
        source="P7-R54-AHR-CS10 sanitized review result row intake",
        allowed_true_refs=P7_R54_AHR_CS10_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs09_schema_version") != P7_R54_AHR_CS09_ACTUAL_HUMAN_REVIEW_OPERATION_RECEIPT_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS10 must follow CS09 operation receipt intake")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS10 sanitized rows")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS10 sanitized rows")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS10 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS10 historical basis ref changed")
    if data.get("sanitized_review_result_row_intake_status_ref") not in P7_R54_AHR_CS10_ALLOWED_INTAKE_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS10 intake status changed")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("execution_blocker_ids") or []])
    if blockers != _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("open_execution_blocker_ids") or []]):
        raise ValueError("P7-R54-AHR-CS10 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "rating_rows_materialized_here",
        "question_need_observation_rows_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS10 must keep {key}=False")
    ready = data.get("sanitized_review_result_row_intake_status_ref") == P7_R54_AHR_CS10_INTAKE_READY_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS10 ready intake must not carry blockers")
        for key in (
            "operation_ready_for_sanitized_result_intake",
            "rows_match_current_24_case_manifest",
            "case_ref_ids_match_manifest",
            "rows_bodyfree_only",
            "rows_selection_only",
            "rows_have_required_axis_scores",
            "all_scores_in_allowed_options",
            "all_verdicts_in_allowed_options",
            "all_reason_ids_in_allowed_options",
            "rows_have_allowed_question_observation_refs",
            "rows_have_no_body_or_question_or_path_or_hash",
            "sanitized_review_result_rows_intaken_here",
            "actual_sanitized_review_result_rows_intaken_here",
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "rating_row_normalization_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS10 ready intake must keep {key}=True")
        for field in (
            "review_result_row_count",
            "sanitized_review_result_row_count",
            "reviewed_case_count",
            "selection_row_count",
            "review_result_row_ref_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CS10 {field} changed")
        if data.get("axis_score_count_per_row") != len(P7_R54_AHR_CS04_RATING_AXIS_REFS):
            raise ValueError("P7-R54-AHR-CS10 axis score count changed")
        if tuple(data.get("axis_refs") or ()) != P7_R54_AHR_CS04_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR-CS10 axis refs changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-CS10 axis thresholds changed")
        for row in data.get("review_result_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CS10 review row must be mapping")
            _assert_required_fields(row, required=P7_R54_AHR_CS10_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-CS10 review row")
            if row.get("schema_version") != P7_R54_AHR_CS10_REVIEW_RESULT_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CS10 review row schema changed")
            if row.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
                raise ValueError("P7-R54-AHR-CS10 review row current basis changed")
            for key in P7_R54_AHR_CS10_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-CS10 review row must keep {key}=False")
            if row.get("selection_only_row") is not True or row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CS10 row must remain selection-only body-free")
            plan_flags = row.get("plan_candidate_flags") if isinstance(row.get("plan_candidate_flags"), Mapping) else {}
            if set(plan_flags) != set(P7_R54_AHR_CS08_PLAN_CANDIDATE_FLAG_REFS):
                raise ValueError("P7-R54-AHR-CS10 plan flag refs changed")
            if plan_flags.get("p8_implementation_spec_finalized_here") is not False:
                raise ValueError("P7-R54-AHR-CS10 must not finalize P8 implementation")
        if data.get("sanitized_review_result_row_intake_reason_refs") != [P7_R54_AHR_CS10_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS10 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS10_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS10 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS11_STEP_REF:
            raise ValueError("P7-R54-AHR-CS10 next step changed")
    else:
        if data.get("sanitized_review_result_row_intake_status_ref") != P7_R54_AHR_CS10_INTAKE_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS10 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS10 blocked intake must carry blockers")
        for key in (
            "rows_match_current_24_case_manifest",
            "case_ref_ids_match_manifest",
            "rows_bodyfree_only",
            "rows_selection_only",
            "rows_have_required_axis_scores",
            "all_scores_in_allowed_options",
            "all_verdicts_in_allowed_options",
            "all_reason_ids_in_allowed_options",
            "rows_have_allowed_question_observation_refs",
            "rows_have_no_body_or_question_or_path_or_hash",
            "sanitized_review_result_rows_intaken_here",
            "actual_sanitized_review_result_rows_intaken_here",
            "rating_row_normalization_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-CS10 blocked intake must keep {key}=False")
        if data.get("review_result_rows") != []:
            raise ValueError("P7-R54-AHR-CS10 blocked intake must not carry rows")
        if data.get("next_required_step") != P7_R54_AHR_CS10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS10 blocked next step changed")
    return True


def _cs_normalize_rating_rows_from_sanitized_results(
    rows: Sequence[Any], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    rating_rows: list[dict[str, Any]] = []
    expected_case_refs = set(_cs_manifest_rows_by_case_ref())
    seen_case_refs: set[str] = set()
    for index, raw_row in enumerate(rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"rating_source_row_{index:02d}_not_mapping")
            continue
        if _contains_forbidden_body_or_question_key(raw_row):
            blockers.append(f"rating_source_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
            continue
        row = {str(key): value for key, value in raw_row.items()}
        if row.get("schema_version") != P7_R54_AHR_CS10_REVIEW_RESULT_ROW_SCHEMA_VERSION:
            blockers.append(f"rating_source_row_{index:02d}_schema_version_changed")
        case_ref_id = clean_identifier(row.get("case_ref_id"), default="", max_length=160)
        if case_ref_id not in expected_case_refs:
            blockers.append(f"rating_source_row_{index:02d}_case_ref_not_in_current_manifest")
        seen_case_refs.add(case_ref_id)
        axis_scores_raw = row.get("axis_scores") if isinstance(row.get("axis_scores"), Mapping) else {}
        axis_scores: dict[str, float] = {}
        if set(axis_scores_raw) != set(P7_R54_AHR_CS04_RATING_AXIS_REFS):
            blockers.append(f"rating_source_row_{index:02d}_axis_refs_mismatch")
        for axis_ref in P7_R54_AHR_CS04_RATING_AXIS_REFS:
            try:
                score = float(axis_scores_raw.get(axis_ref))
            except (TypeError, ValueError):
                blockers.append(f"rating_source_row_{index:02d}_{axis_ref}_score_not_number")
                score = -1.0
            if score < 0.0 or score > 1.0:
                blockers.append(f"rating_source_row_{index:02d}_{axis_ref}_score_out_of_range")
            axis_scores[axis_ref] = score
        if row.get("axis_score_count") != len(P7_R54_AHR_CS04_RATING_AXIS_REFS):
            blockers.append(f"rating_source_row_{index:02d}_axis_score_count_not_6")
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR_CS08_VERDICT_OPTION_REFS:
            blockers.append(f"rating_source_row_{index:02d}_verdict_not_allowed")
        sanitized_reason_ids = _cs_clean_identifier_list(row.get("sanitized_reason_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_SANITIZED_REASON_ID_OPTION_REFS for item in sanitized_reason_ids):
            blockers.append(f"rating_source_row_{index:02d}_sanitized_reason_id_not_allowed")
        readfeel_blocker_ids = _cs_clean_identifier_list(row.get("readfeel_blocker_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS for item in readfeel_blocker_ids):
            blockers.append(f"rating_source_row_{index:02d}_readfeel_blocker_id_not_allowed")
        execution_blocker_ids = _cs_clean_identifier_list(row.get("execution_blocker_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS for item in execution_blocker_ids):
            blockers.append(f"rating_source_row_{index:02d}_execution_blocker_id_not_allowed")
        question_need_primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=180)
        if question_need_primary_class not in P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS:
            blockers.append(f"rating_source_row_{index:02d}_question_need_primary_class_not_allowed")
        ambiguity_kind_refs = _cs_clean_identifier_list(row.get("ambiguity_kind_refs") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS for item in ambiguity_kind_refs):
            blockers.append(f"rating_source_row_{index:02d}_ambiguity_kind_ref_not_allowed")
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=180)
        if one_question_fit_ref not in P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append(f"rating_source_row_{index:02d}_one_question_fit_ref_not_allowed")
        repair_required_refs = _cs_clean_identifier_list(row.get("repair_required_refs") or (), limit=20, max_length=180)
        if any(item not in P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS for item in repair_required_refs):
            blockers.append(f"rating_source_row_{index:02d}_repair_required_ref_not_allowed")
        plan_candidate_flags = _cs_plan_candidate_flags(row.get("plan_candidate_flags"))
        below_target_axis_refs = [
            axis_ref
            for axis_ref, score in axis_scores.items()
            if score < P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS[axis_ref]
        ]
        for flag_ref in P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS:
            if row.get(flag_ref) is not False:
                blockers.append(f"rating_source_row_{index:02d}_{flag_ref}_not_false")
        rating_rows.append(
            {
                "schema_version": P7_R54_AHR_CS11_RATING_ROW_SCHEMA_VERSION,
                "review_session_id": review_session_id,
                "rating_row_ref": f"rating_row_{index:03d}",
                "source_review_result_row_ref": clean_identifier(row.get("review_result_row_ref"), default="", max_length=160),
                "case_ref_id": case_ref_id,
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=160),
                "case_family_ref": clean_identifier(row.get("case_family_ref"), default="", max_length=160),
                "case_role_ref": clean_identifier(row.get("case_role_ref"), default="", max_length=160),
                "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                "axis_scores": axis_scores,
                "axis_score_count": len(P7_R54_AHR_CS04_RATING_AXIS_REFS),
                "axis_targets": dict(P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS),
                "below_target_axis_refs": below_target_axis_refs,
                "below_target_axis_count": len(below_target_axis_refs),
                "verdict": verdict,
                "sanitized_reason_ids": sanitized_reason_ids,
                "readfeel_blocker_ids": readfeel_blocker_ids,
                "execution_blocker_ids": execution_blocker_ids,
                "question_need_primary_class": question_need_primary_class,
                "ambiguity_kind_refs": ambiguity_kind_refs,
                "one_question_fit_ref": one_question_fit_ref,
                "repair_required_refs": repair_required_refs,
                "plan_candidate_flags": plan_candidate_flags,
                **{key: False for key in P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS},
                "body_free": True,
            }
        )
    if len(rows) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("rating_source_row_count_not_24")
    if len(seen_case_refs) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("rating_case_ref_ids_not_unique_or_not_24")
    if set(seen_case_refs) != expected_case_refs:
        blockers.append("rating_case_ref_ids_do_not_match_current_manifest")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    if blockers:
        return [], blockers
    return rating_rows, []


def _cs_axis_averages(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    if not rows:
        return {}
    averages: dict[str, float] = {}
    for axis_ref in P7_R54_AHR_CS04_RATING_AXIS_REFS:
        total = sum(float((row.get("axis_scores") or {}).get(axis_ref, 0.0)) for row in rows)
        averages[axis_ref] = round(total / len(rows), 6)
    return averages


def _cs_below_target_axis_counts(rows: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {axis_ref: 0 for axis_ref in P7_R54_AHR_CS04_RATING_AXIS_REFS}
    for row in rows:
        for axis_ref in row.get("below_target_axis_refs") or []:
            if axis_ref in counts:
                counts[axis_ref] += 1
    return counts


def build_p7_r54_ahr_cs11_rating_row_normalization(
    *,
    sanitized_review_result_row_intake: Mapping[str, Any] | None = None,
    review_session_id: Any = None,
) -> dict[str, Any]:
    """Normalize CS11 body-free rating rows from CS10 sanitized review result rows."""

    cs10 = dict(sanitized_review_result_row_intake or build_p7_r54_ahr_cs10_sanitized_review_result_row_intake())
    session_id = _safe_review_session_id(review_session_id or cs10.get("review_session_id"))
    cs10_ready = (
        cs10.get("sanitized_review_result_row_intake_status_ref") == P7_R54_AHR_CS10_INTAKE_READY_STATUS_REF
        and cs10.get("rating_row_normalization_allowed_next") is True
        and cs10.get("sanitized_review_result_row_count") == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    )
    rating_rows, row_blockers = _cs_normalize_rating_rows_from_sanitized_results(
        cs10.get("review_result_rows") or [], review_session_id=session_id
    ) if cs10_ready else ([], ["cs10_sanitized_review_result_rows_not_ready"])
    ready = cs10_ready and not row_blockers
    blockers = [] if ready else _cs_dedupe_identifiers(row_blockers or ["rating_row_normalization_not_ready"])
    status_ref = P7_R54_AHR_CS11_NORMALIZED_STATUS_REF if ready else P7_R54_AHR_CS11_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR_CS11_READY_REASON_REF] if ready else blockers
    rating_refs = [str(row.get("rating_row_ref")) for row in rating_rows]
    source_refs = [str(row.get("source_review_result_row_ref")) for row in rating_rows]
    case_refs = [str(row.get("case_ref_id")) for row in rating_rows]
    blind_ids = [str(row.get("blind_case_id")) for row in rating_rows]
    packet_refs = [str(row.get("packet_ref_id")) for row in rating_rows]
    below_counts = _cs_below_target_axis_counts(rating_rows) if ready else {}
    verdict_counts = _cs_count_values(rating_rows, "verdict") if ready else {}
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS11_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS11_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs11_rating_row_normalization_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs10_schema_version": cs10.get("schema_version"),
        "cs10_material_ref": cs10.get("material_id"),
        "cs10_next_required_step": cs10.get("next_required_step"),
        "cs10_sanitized_review_result_row_intake_status_ref": cs10.get("sanitized_review_result_row_intake_status_ref"),
        "cs10_rating_row_normalization_allowed_next": cs10.get("rating_row_normalization_allowed_next") is True,
        "cs10_sanitized_review_result_row_count": int(cs10.get("sanitized_review_result_row_count") or 0),
        "cs10_review_result_row_count": int(cs10.get("review_result_row_count") or 0),
        "cs10_case_ref_id_count": int(cs10.get("case_ref_id_count") or 0),
        "cs10_actual_human_review_operation_run": cs10.get("actual_human_review_operation_run") is True,
        "cs10_actual_human_review_executed_by_person": cs10.get("actual_human_review_executed_by_person") is True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "rating_row_normalization_status_ref": status_ref,
        "rating_row_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "sanitized_review_result_rows_ready_for_rating_normalization": cs10_ready,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "source_sanitized_review_result_row_count": int(cs10.get("sanitized_review_result_row_count") or 0) if cs10_ready else 0,
        "rating_row_count": len(rating_rows),
        "rating_rows": rating_rows,
        "rating_row_refs": rating_refs,
        "rating_row_ref_count": len(rating_refs),
        "source_review_result_row_refs": source_refs,
        "source_review_result_row_ref_count": len(source_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(set(case_refs)) == len(case_refs) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "blind_case_ids": blind_ids,
        "blind_case_id_count": len(blind_ids),
        "blind_case_ids_unique": len(set(blind_ids)) == len(blind_ids) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "packet_ref_ids": packet_refs,
        "packet_ref_id_count": len(packet_refs),
        "packet_ref_ids_unique": len(set(packet_refs)) == len(packet_refs) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "axis_refs": list(P7_R54_AHR_CS04_RATING_AXIS_REFS),
        "axis_count": len(P7_R54_AHR_CS04_RATING_AXIS_REFS),
        "rating_axis_target_thresholds": dict(P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS),
        "axis_averages": _cs_axis_averages(rating_rows) if ready else {},
        "rating_rows_bodyfree_only": ready,
        "rating_rows_match_sanitized_review_result_case_refs": ready,
        "rating_rows_have_required_axis_scores": ready,
        "rating_scores_in_range": ready,
        "rating_rows_have_allowed_verdict_refs": ready,
        "below_target_axis_refs_by_case": {
            str(row.get("case_ref_id")): list(row.get("below_target_axis_refs") or []) for row in rating_rows
        } if ready else {},
        "below_target_axis_ref_counts": below_counts,
        "below_target_axis_counts": below_counts,
        "below_target_case_count": sum(1 for row in rating_rows if row.get("below_target_axis_count")),
        "verdict_counts": verdict_counts,
        "pass_case_count": verdict_counts.get("PASS", 0),
        "yellow_case_count": verdict_counts.get("YELLOW", 0),
        "repair_required_case_count": verdict_counts.get("REPAIR_REQUIRED", 0),
        "red_case_count": verdict_counts.get("RED", 0),
        "blocked_case_count": verdict_counts.get("BLOCKED", 0),
        "not_reviewable_case_count": verdict_counts.get("NOT_REVIEWABLE", 0),
        "readfeel_blocker_id_counts": _cs_count_ids(rating_rows, "readfeel_blocker_ids") if ready else {},
        "execution_blocker_id_counts": _cs_count_ids(rating_rows, "execution_blocker_ids") if ready else {},
        "readfeel_blocker_row_source_count": sum(1 for row in rating_rows if row.get("readfeel_blocker_ids")),
        "execution_blocker_row_source_count": sum(1 for row in rating_rows if row.get("execution_blocker_ids")),
        "rating_rows_normalized_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_human_review_operation_run": cs10.get("actual_human_review_operation_run") is True and ready,
        "actual_human_review_executed_by_person": cs10.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_review_evidence_complete": False,
        "blocker_question_need_observation_normalization_allowed_next": ready,
        "question_need_observation_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CS11_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS10_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS10_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS12_STEP_REF if ready else P7_R54_AHR_CS11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS11_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs11_rating_row_normalization_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS11 rating row normalization",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS11_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS11_STEP_REF,
        source="P7-R54-AHR-CS11 rating row normalization",
        allowed_true_refs=P7_R54_AHR_CS11_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs10_schema_version") != P7_R54_AHR_CS10_SANITIZED_REVIEW_RESULT_ROW_INTAKE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS11 must follow CS10 sanitized row intake")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS11 rating rows")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS11 rating rows")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS11 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS11 historical basis ref changed")
    if data.get("rating_row_normalization_status_ref") not in P7_R54_AHR_CS11_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS11 status changed")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("execution_blocker_ids") or []])
    if blockers != _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("open_execution_blocker_ids") or []]):
        raise ValueError("P7-R54-AHR-CS11 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_review_evidence_complete",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS11 must keep {key}=False")
    ready = data.get("rating_row_normalization_status_ref") == P7_R54_AHR_CS11_NORMALIZED_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS11 ready material must not carry blockers")
        for key in (
            "sanitized_review_result_rows_ready_for_rating_normalization",
            "rating_rows_bodyfree_only",
            "rating_rows_match_sanitized_review_result_case_refs",
            "rating_rows_have_required_axis_scores",
            "rating_scores_in_range",
            "rating_rows_have_allowed_verdict_refs",
            "rating_rows_normalized_here",
            "actual_rating_rows_materialized_here",
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "blocker_question_need_observation_normalization_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS11 ready material must keep {key}=True")
        for field in (
            "source_sanitized_review_result_row_count",
            "rating_row_count",
            "rating_row_ref_count",
            "source_review_result_row_ref_count",
            "case_ref_id_count",
            "blind_case_id_count",
            "packet_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CS11 {field} changed")
        if tuple(data.get("axis_refs") or ()) != P7_R54_AHR_CS04_RATING_AXIS_REFS:
            raise ValueError("P7-R54-AHR-CS11 axis refs changed")
        if data.get("axis_count") != len(P7_R54_AHR_CS04_RATING_AXIS_REFS):
            raise ValueError("P7-R54-AHR-CS11 axis count changed")
        if data.get("rating_axis_target_thresholds") != P7_R54_AHR_CS04_RATING_AXIS_TARGET_THRESHOLDS:
            raise ValueError("P7-R54-AHR-CS11 axis thresholds changed")
        if set(data.get("axis_averages") or {}) != set(P7_R54_AHR_CS04_RATING_AXIS_REFS):
            raise ValueError("P7-R54-AHR-CS11 axis averages changed")
        if data.get("below_target_axis_counts") != data.get("below_target_axis_ref_counts"):
            raise ValueError("P7-R54-AHR-CS11 below-target axis count aliases changed")
        for row in data.get("rating_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CS11 rating row must be mapping")
            _assert_required_fields(row, required=P7_R54_AHR_CS11_RATING_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-CS11 rating row")
            if row.get("schema_version") != P7_R54_AHR_CS11_RATING_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CS11 rating row schema changed")
            if row.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
                raise ValueError("P7-R54-AHR-CS11 rating row current basis changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CS11 rating row must be body-free")
            for key in P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-CS11 rating row must keep {key}=False")
        if data.get("rating_row_normalization_reason_refs") != [P7_R54_AHR_CS11_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS11 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS11_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS11 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS12_STEP_REF:
            raise ValueError("P7-R54-AHR-CS11 next step changed")
    else:
        if data.get("rating_row_normalization_status_ref") != P7_R54_AHR_CS11_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS11 blocked status changed")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS11 blocked material must carry blockers")
        for key in (
            "rating_rows_bodyfree_only",
            "rating_rows_match_sanitized_review_result_case_refs",
            "rating_rows_have_required_axis_scores",
            "rating_scores_in_range",
            "rating_rows_have_allowed_verdict_refs",
            "rating_rows_normalized_here",
            "actual_rating_rows_materialized_here",
            "blocker_question_need_observation_normalization_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-CS11 blocked material must keep {key}=False")
        if data.get("rating_rows") != [] or data.get("rating_row_count") != 0:
            raise ValueError("P7-R54-AHR-CS11 blocked material must not carry rating rows")
        if data.get("next_required_step") != P7_R54_AHR_CS11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS11 blocked next step changed")
    return True


# Compatibility aliases for CS10/CS11 design wording.
build_p7_r54_ahr_cs10_sanitized_review_result_row_intake_bodyfree = (
    build_p7_r54_ahr_cs10_sanitized_review_result_row_intake
)
assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_bodyfree_contract = (
    assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_sanitized_review_result_row_intake_bodyfree = (
    build_p7_r54_ahr_cs10_sanitized_review_result_row_intake
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_sanitized_review_result_row_intake_bodyfree_contract = (
    assert_p7_r54_ahr_cs10_sanitized_review_result_row_intake_contract
)
build_p7_r54_ahr_cs11_rating_row_normalization_bodyfree = build_p7_r54_ahr_cs11_rating_row_normalization
assert_p7_r54_ahr_cs11_rating_row_normalization_bodyfree_contract = (
    assert_p7_r54_ahr_cs11_rating_row_normalization_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_row_normalization_bodyfree = (
    build_p7_r54_ahr_cs11_rating_row_normalization
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_row_normalization_bodyfree_contract = (
    assert_p7_r54_ahr_cs11_rating_row_normalization_contract
)

# ---------------------------------------------------------------------------
# CS12 / CS13 blocker-question observation normalization and consistency guard.
#
# CS12 derives readfeel/execution blocker rows and question-need observation rows
# from CS11 rating rows only.  It keeps those rows body-free and treats them as
# P8 material candidates only; it does not create question text, draft question
# text, P8 implementation specs, storage, triggers, UI, P5 final, R52 execution,
# P7 completion, or release readiness.
#
# CS13 guards the normalized rows against rating/question contradictions.  Passing
# this guard only permits the next CS14 lifecycle/disposal receipt boundary; it is
# still not actual review complete and not R52/P5/P6/P8/release approval.
# ---------------------------------------------------------------------------

P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs12_blocker_question_need_observation_normalization.bodyfree.v1"
)
P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs13_rating_question_consistency_guard.bodyfree.v1"
)
P7_R54_AHR_CS_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
)
P7_R54_AHR_CS_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
)

P7_R54_AHR_CS12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS11_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS12_STEP_REF,
)
P7_R54_AHR_CS12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[13:]
P7_R54_AHR_CS13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS12_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS13_STEP_REF,
)
P7_R54_AHR_CS13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[14:]

P7_R54_AHR_CS12_NORMALIZED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZED_BODYFREE"
)
P7_R54_AHR_CS12_BLOCKED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_BLOCKED"
)
P7_R54_AHR_CS12_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS12_NORMALIZED_STATUS_REF,
    P7_R54_AHR_CS12_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS12_READY_REASON_REF: Final = (
    "r54_ahr_cs_blocker_and_question_need_observation_rows_normalized_bodyfree"
)
P7_R54_AHR_CS12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS12_repair_blocker_question_need_observation_normalization_before_consistency_guard"
)

P7_R54_AHR_CS13_PASSED_STATUS_REF: Final = "CURRENT_SNAPSHOT_RATING_QUESTION_CONSISTENCY_GUARD_PASSED_BODYFREE"
P7_R54_AHR_CS13_BLOCKED_STATUS_REF: Final = "CURRENT_SNAPSHOT_RATING_QUESTION_CONSISTENCY_GUARD_BLOCKED"
P7_R54_AHR_CS13_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS13_PASSED_STATUS_REF,
    P7_R54_AHR_CS13_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS13_READY_REASON_REF: Final = (
    "r54_ahr_cs_rating_question_consistency_guard_passed_bodyfree"
)
P7_R54_AHR_CS13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS13_repair_rating_question_consistency_before_disposal_receipt"
)
P7_R54_AHR_CS13_CONSISTENCY_ROUTE_REF: Final = (
    "R54_AHR_CS_RATING_QUESTION_CONSISTENCY_REPAIR"
)

P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs12_question_need_observation_row.bodyfree.v1"
)
P7_R54_AHR_CS12_BLOCKER_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs12_blocker_row.bodyfree.v1"
)
P7_R54_AHR_CS13_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs13_rating_question_consistency_issue_row.bodyfree.v1"
)

P7_R54_AHR_CS12_READFEEL_BLOCKER_KIND_REF: Final = "READFEEL_BLOCKER"
P7_R54_AHR_CS12_EXECUTION_BLOCKER_KIND_REF: Final = "EXECUTION_BLOCKER"
P7_R54_AHR_CS12_BLOCKER_STATUS_OPEN_REF: Final = "OPEN"
P7_R54_AHR_CS12_READFEEL_BLOCKER_ROUTE_REF: Final = "P5_REPAIR_RETURN_REQUIRED"
P7_R54_AHR_CS12_EXECUTION_BLOCKER_ROUTE_REF: Final = "R54_OPERATION_BLOCKED_EVIDENCE_REPAIR"

P7_R54_AHR_CS12_P8_MATERIAL_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)
P7_R54_AHR_CS12_P5_REPAIR_PRIMARY_CLASS_REFS: Final[tuple[str, ...]] = (
    "not_question_emlis_readfeel_repair_required",
    "not_question_p5_surface_repair_required",
    "not_question_gate_boundary_required",
)
P7_R54_AHR_CS12_P8_MATERIAL_ONE_QUESTION_FIT_REFS: Final[tuple[str, ...]] = (
    "fits_one_question",
    "needs_more_than_one_question_not_p7",
)
P7_R54_AHR_CS12_NO_REPAIR_REF: Final = "no_repair_required"
P7_R54_AHR_CS12_EXECUTION_BLOCKER_PRIMARY_CLASS_REF: Final = "insufficient_material_execution_blocker"
P7_R54_AHR_CS12_NOT_QUESTION_REPAIR_FIT_REFS: Final[tuple[str, ...]] = (
    "repair_required_not_question",
    "unsafe_or_boundary_not_question",
    "insufficient_material",
)

P7_R54_AHR_CS12_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)
P7_R54_AHR_CS13_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CS12_ALLOWED_TRUE_FALSE_FLAG_REFS
P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS
)
P7_R54_AHR_CS13_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS
)

P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "question_observation_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "case_family_ref",
    "case_role_ref",
    "current_basis_ref",
    "verdict",
    "question_need_primary_class",
    "ambiguity_kind_refs",
    "ambiguity_kind_ref_count",
    "one_question_fit_ref",
    "repair_required_refs",
    "repair_required_ref_count",
    "plan_candidate_flags",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
    "p8_design_material_candidate",
    "p8_implementation_spec_finalized_here",
    "p5_repair_required",
    "p4_current_surface_repair_required",
    "gate_boundary_repair_required",
    "emlis_readfeel_repair_required",
    "execution_blocker_present",
    "readfeel_blocker_present",
    "readfeel_blocker_ids",
    "execution_blocker_ids",
    *P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_CS12_BLOCKER_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "blocker_row_ref",
    "source_rating_row_ref",
    "source_review_result_row_ref",
    "case_ref_id",
    "blind_case_id",
    "packet_ref_id",
    "current_basis_ref",
    "blocker_kind",
    "blocker_id",
    "blocker_status",
    "routes_to",
    *P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS,
    "body_free",
)
P7_R54_AHR_CS13_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "review_session_id",
    "consistency_issue_row_ref",
    "source_question_observation_row_ref",
    "source_rating_row_ref",
    "case_ref_id",
    "current_basis_ref",
    "issue_id",
    "issue_kind",
    "routes_to",
    *P7_R54_AHR_CS13_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS,
    "body_free",
)

P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs11_schema_version",
    "cs11_material_ref",
    "cs11_next_required_step",
    "cs11_rating_row_normalization_status_ref",
    "cs11_blocker_question_need_observation_normalization_allowed_next",
    "cs11_rating_row_count",
    "cs11_actual_rating_rows_materialized_here",
    "cs11_actual_human_review_operation_run",
    "cs11_actual_human_review_executed_by_person",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "blocker_question_need_observation_normalization_status_ref",
    "blocker_question_need_observation_normalization_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_rows_ready_for_blocker_question_observation_normalization",
    "required_case_count",
    "source_rating_row_count",
    "blocker_row_count",
    "blocker_rows",
    "blocker_row_refs",
    "blocker_row_ref_count",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "question_need_observation_row_count",
    "actual_question_need_observation_row_count",
    "question_need_observation_rows",
    "question_need_observation_row_refs",
    "question_need_observation_row_ref_count",
    "source_rating_row_refs",
    "source_rating_row_ref_count",
    "case_ref_ids",
    "case_ref_id_count",
    "case_ref_ids_unique",
    "question_need_primary_class_counts",
    "ambiguity_kind_ref_counts",
    "one_question_fit_ref_counts",
    "repair_required_ref_counts",
    "readfeel_blocker_id_counts",
    "execution_blocker_id_counts",
    "p8_material_candidate_row_count",
    "plus_single_question_candidate_row_count",
    "premium_deep_dive_candidate_row_count",
    "p5_repair_required_observation_row_count",
    "p4_current_surface_repair_required_row_count",
    "gate_boundary_repair_required_row_count",
    "emlis_readfeel_repair_required_row_count",
    "execution_blocker_observation_row_count",
    "readfeel_blocker_observation_row_count",
    "blocker_rows_bodyfree_only",
    "blocker_rows_from_rating_rows_only",
    "question_observation_rows_bodyfree_only",
    "question_observation_rows_from_actual_review_only",
    "question_observation_rows_have_allowed_primary_class_refs",
    "question_observation_rows_have_allowed_ambiguity_kind_refs",
    "question_observation_rows_have_allowed_one_question_fit_refs",
    "question_observation_rows_have_allowed_repair_required_refs",
    "question_text_included",
    "draft_question_text_included",
    "question_text_materialized_here",
    "draft_question_text_materialized_here",
    "p8_implementation_spec_finalized_here",
    "p8_question_text_created_here",
    "p8_trigger_logic_created_here",
    "p8_storage_or_ui_created_here",
    "p5_repair_required_rows_excluded_from_p8_material",
    "p4_current_surface_repair_rows_excluded_from_p8_material",
    "execution_blocker_rows_excluded_from_p8_material",
    "readfeel_blocker_rows_excluded_from_p8_material",
    "question_need_observation_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "rating_question_consistency_guard_allowed_next",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs12_schema_version",
    "cs12_material_ref",
    "cs12_next_required_step",
    "cs12_blocker_question_need_observation_normalization_status_ref",
    "cs12_rating_question_consistency_guard_allowed_next",
    "cs12_question_need_observation_row_count",
    "cs12_actual_question_need_observation_rows_materialized_here",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "consistency_guard_status_ref",
    "consistency_guard_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "question_rows_ready_for_consistency_guard",
    "required_case_count",
    "question_need_observation_row_count",
    "question_need_observation_row_refs",
    "question_need_observation_row_ref_count",
    "consistency_issue_rows",
    "consistency_issue_row_count",
    "consistency_issue_ids",
    "consistency_issue_id_count",
    "open_consistency_issue_count",
    "rating_question_consistency_guard_passed",
    "question_text_absent",
    "draft_question_text_absent",
    "p8_implementation_spec_not_finalized_here",
    "p5_repair_rows_excluded_from_p8_material",
    "p4_current_surface_repair_rows_excluded_from_p8_material",
    "execution_blocker_rows_excluded_from_p8_material",
    "readfeel_blocker_rows_excluded_from_p8_material",
    "red_or_repair_rows_excluded_from_p8_material",
    "p8_material_candidate_row_count",
    "p5_repair_required_observation_row_count",
    "p4_current_surface_repair_required_row_count",
    "execution_blocker_observation_row_count",
    "readfeel_blocker_observation_row_count",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_review_evidence_complete",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "pause_abort_expiration_disposal_receipt_allowed_next",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS
)


def _cs_count_nested_ids(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    return _cs_count_ids(rows, field)


def _cs_question_need_observation_and_blocker_rows_from_rating_rows(
    rating_rows: Sequence[Any], *, review_session_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    blockers: list[str] = []
    question_rows: list[dict[str, Any]] = []
    blocker_rows: list[dict[str, Any]] = []
    expected_case_refs = set(_cs_manifest_rows_by_case_ref())
    seen_case_refs: set[str] = set()
    if len(rating_rows) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("source_rating_row_count_not_24")
    blocker_index = 0
    for index, raw_row in enumerate(rating_rows, start=1):
        if not isinstance(raw_row, Mapping):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_not_mapping")
            continue
        if _contains_forbidden_body_or_question_key(raw_row):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_contains_forbidden_body_question_path_hash_key")
            continue
        row = {str(key): value for key, value in raw_row.items()}
        if row.get("body_free") is not True:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_body_free_not_true")
        for flag_ref in P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS:
            if row.get(flag_ref) is not False:
                blockers.append(f"question_observation_source_rating_row_{index:02d}_{flag_ref}_not_false")
        if row.get("schema_version") != P7_R54_AHR_CS11_RATING_ROW_SCHEMA_VERSION:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_schema_version_changed")
        if row.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_current_basis_ref_mismatch")
        if row.get("body_free") is not True:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_body_free_not_true")
        for flag_ref in P7_R54_AHR_CS11_RATING_ROW_BODYFREE_FALSE_FLAG_REFS:
            if row.get(flag_ref) is not False:
                blockers.append(f"question_observation_source_rating_row_{index:02d}_{flag_ref}_not_false")
        case_ref_id = clean_identifier(row.get("case_ref_id"), default="", max_length=160)
        if case_ref_id not in expected_case_refs:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_case_ref_not_in_current_manifest")
        seen_case_refs.add(case_ref_id)
        primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=180)
        if primary_class not in P7_R54_AHR_CS08_QUESTION_NEED_PRIMARY_CLASS_REFS:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_primary_class_not_allowed")
        ambiguity_kind_refs = _cs_clean_identifier_list(row.get("ambiguity_kind_refs") or (), limit=20, max_length=160)
        if not ambiguity_kind_refs:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_ambiguity_kind_refs_missing")
        if any(item not in P7_R54_AHR_CS08_AMBIGUITY_KIND_OPTION_REFS for item in ambiguity_kind_refs):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_ambiguity_kind_ref_not_allowed")
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=180)
        if one_question_fit_ref not in P7_R54_AHR_CS08_ONE_QUESTION_FIT_OPTION_REFS:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_one_question_fit_ref_not_allowed")
        repair_required_refs = _cs_clean_identifier_list(row.get("repair_required_refs") or (), limit=20, max_length=180)
        if not repair_required_refs:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_repair_required_refs_missing")
        if any(item not in P7_R54_AHR_CS08_REPAIR_REQUIRED_OPTION_REFS for item in repair_required_refs):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_repair_required_ref_not_allowed")
        plan_candidate_flags = _cs_plan_candidate_flags(row.get("plan_candidate_flags"))
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        if verdict not in P7_R54_AHR_CS08_VERDICT_OPTION_REFS:
            blockers.append(f"question_observation_source_rating_row_{index:02d}_verdict_not_allowed")
        readfeel_blocker_ids = _cs_clean_identifier_list(row.get("readfeel_blocker_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_READFEEL_BLOCKER_ID_OPTION_REFS for item in readfeel_blocker_ids):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_readfeel_blocker_id_not_allowed")
        execution_blocker_ids = _cs_clean_identifier_list(row.get("execution_blocker_ids") or (), limit=20, max_length=160)
        if any(item not in P7_R54_AHR_CS08_EXECUTION_BLOCKER_ID_OPTION_REFS for item in execution_blocker_ids):
            blockers.append(f"question_observation_source_rating_row_{index:02d}_execution_blocker_id_not_allowed")
        p5_repair_required = any(
            ref in repair_required_refs for ref in ("emlis_readfeel_repair_required", "p5_surface_repair_required")
        ) or primary_class in (
            "not_question_emlis_readfeel_repair_required",
            "not_question_p5_surface_repair_required",
        )
        p4_current_repair_required = "p4_current_surface_repair_required" in repair_required_refs
        gate_boundary_repair_required = "gate_boundary_repair_required" in repair_required_refs or primary_class == "not_question_gate_boundary_required"
        emlis_readfeel_repair_required = "emlis_readfeel_repair_required" in repair_required_refs or primary_class == "not_question_emlis_readfeel_repair_required"
        execution_blocker_present = bool(execution_blocker_ids) or primary_class == P7_R54_AHR_CS12_EXECUTION_BLOCKER_PRIMARY_CLASS_REF
        readfeel_blocker_present = bool(readfeel_blocker_ids)
        plus_candidate = (
            primary_class == "plus_single_question_candidate_later"
            and plan_candidate_flags.get("plus_single_question_candidate_later") is True
            and one_question_fit_ref == "fits_one_question"
            and not p5_repair_required
            and not p4_current_repair_required
            and not gate_boundary_repair_required
            and not execution_blocker_present
            and not readfeel_blocker_present
            and verdict not in {"RED", "REPAIR_REQUIRED", "BLOCKED", "NOT_REVIEWABLE"}
        )
        premium_candidate = (
            primary_class == "premium_deep_dive_candidate_later"
            and plan_candidate_flags.get("premium_deep_dive_candidate_later") is True
            and one_question_fit_ref in P7_R54_AHR_CS12_P8_MATERIAL_ONE_QUESTION_FIT_REFS
            and not p5_repair_required
            and not p4_current_repair_required
            and not gate_boundary_repair_required
            and not execution_blocker_present
            and not readfeel_blocker_present
            and verdict not in {"RED", "REPAIR_REQUIRED", "BLOCKED", "NOT_REVIEWABLE"}
        )
        p8_material_candidate = (
            plan_candidate_flags.get("p8_design_material_candidate") is True
            and primary_class in P7_R54_AHR_CS12_P8_MATERIAL_PRIMARY_CLASS_REFS
            and one_question_fit_ref in P7_R54_AHR_CS12_P8_MATERIAL_ONE_QUESTION_FIT_REFS
            and (plus_candidate or premium_candidate)
        )
        source_rating_row_ref = clean_identifier(row.get("rating_row_ref"), default=f"rating_row_{index:03d}", max_length=160)
        source_review_result_row_ref = clean_identifier(
            row.get("source_review_result_row_ref"), default=f"review_result_row_{index:03d}", max_length=160
        )
        for blocker_id in readfeel_blocker_ids:
            blocker_index += 1
            blocker_rows.append(
                {
                    "schema_version": P7_R54_AHR_CS12_BLOCKER_ROW_SCHEMA_VERSION,
                    "review_session_id": review_session_id,
                    "blocker_row_ref": f"blocker_row_{blocker_index:03d}",
                    "source_rating_row_ref": source_rating_row_ref,
                    "source_review_result_row_ref": source_review_result_row_ref,
                    "case_ref_id": case_ref_id,
                    "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=160),
                    "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=160),
                    "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                    "blocker_kind": P7_R54_AHR_CS12_READFEEL_BLOCKER_KIND_REF,
                    "blocker_id": blocker_id,
                    "blocker_status": P7_R54_AHR_CS12_BLOCKER_STATUS_OPEN_REF,
                    "routes_to": P7_R54_AHR_CS12_READFEEL_BLOCKER_ROUTE_REF,
                    **{key: False for key in P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS},
                    "body_free": True,
                }
            )
        for blocker_id in execution_blocker_ids:
            blocker_index += 1
            blocker_rows.append(
                {
                    "schema_version": P7_R54_AHR_CS12_BLOCKER_ROW_SCHEMA_VERSION,
                    "review_session_id": review_session_id,
                    "blocker_row_ref": f"blocker_row_{blocker_index:03d}",
                    "source_rating_row_ref": source_rating_row_ref,
                    "source_review_result_row_ref": source_review_result_row_ref,
                    "case_ref_id": case_ref_id,
                    "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=160),
                    "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=160),
                    "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                    "blocker_kind": P7_R54_AHR_CS12_EXECUTION_BLOCKER_KIND_REF,
                    "blocker_id": blocker_id,
                    "blocker_status": P7_R54_AHR_CS12_BLOCKER_STATUS_OPEN_REF,
                    "routes_to": P7_R54_AHR_CS12_EXECUTION_BLOCKER_ROUTE_REF,
                    **{key: False for key in P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS},
                    "body_free": True,
                }
            )
        question_rows.append(
            {
                "schema_version": P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION,
                "review_session_id": review_session_id,
                "question_observation_row_ref": f"question_observation_row_{index:03d}",
                "source_rating_row_ref": source_rating_row_ref,
                "source_review_result_row_ref": source_review_result_row_ref,
                "case_ref_id": case_ref_id,
                "blind_case_id": clean_identifier(row.get("blind_case_id"), default="", max_length=160),
                "packet_ref_id": clean_identifier(row.get("packet_ref_id"), default="", max_length=160),
                "case_family_ref": clean_identifier(row.get("case_family_ref"), default="", max_length=160),
                "case_role_ref": clean_identifier(row.get("case_role_ref"), default="", max_length=160),
                "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                "verdict": verdict,
                "question_need_primary_class": primary_class,
                "ambiguity_kind_refs": ambiguity_kind_refs,
                "ambiguity_kind_ref_count": len(ambiguity_kind_refs),
                "one_question_fit_ref": one_question_fit_ref,
                "repair_required_refs": repair_required_refs,
                "repair_required_ref_count": len(repair_required_refs),
                "plan_candidate_flags": plan_candidate_flags,
                "plus_single_question_candidate_later": plus_candidate,
                "premium_deep_dive_candidate_later": premium_candidate,
                "p8_design_material_candidate": p8_material_candidate,
                "p8_implementation_spec_finalized_here": False,
                "p5_repair_required": p5_repair_required,
                "p4_current_surface_repair_required": p4_current_repair_required,
                "gate_boundary_repair_required": gate_boundary_repair_required,
                "emlis_readfeel_repair_required": emlis_readfeel_repair_required,
                "execution_blocker_present": execution_blocker_present,
                "readfeel_blocker_present": readfeel_blocker_present,
                "readfeel_blocker_ids": readfeel_blocker_ids,
                "execution_blocker_ids": execution_blocker_ids,
                **{key: False for key in P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS},
                "body_free": True,
            }
        )
    if len(seen_case_refs) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
        blockers.append("question_observation_case_ref_ids_not_unique_or_not_24")
    if seen_case_refs != expected_case_refs:
        blockers.append("question_observation_rows_do_not_match_current_24_case_manifest")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    if blockers:
        return [], [], blockers
    return question_rows, blocker_rows, []


def build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization(
    *,
    rating_row_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Normalize blocker rows and question-need observations as body-free refs."""

    rating_material = dict(rating_row_normalization or build_p7_r54_ahr_cs11_rating_row_normalization())
    session_id = _safe_review_session_id(review_session_id)
    rating_ready = (
        rating_material.get("rating_row_normalization_status_ref") == P7_R54_AHR_CS11_NORMALIZED_STATUS_REF
        and rating_material.get("blocker_question_need_observation_normalization_allowed_next") is True
        and rating_material.get("next_required_step") == P7_R54_AHR_CS12_STEP_REF
        and rating_material.get("rating_row_count") == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and rating_material.get("actual_rating_rows_materialized_here") is True
        and rating_material.get("actual_human_review_operation_run") is True
        and rating_material.get("actual_human_review_executed_by_person") is True
    )
    question_rows, blocker_rows, row_blockers = (
        _cs_question_need_observation_and_blocker_rows_from_rating_rows(
            rating_material.get("rating_rows") or [], review_session_id=session_id
        )
        if rating_ready
        else ([], [], [])
    )
    blockers: list[str] = []
    if not rating_ready:
        blockers.append("cs11_rating_row_normalization_not_ready_for_blocker_question_observation")
    blockers.extend(row_blockers)
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    ready = not blockers
    status_ref = P7_R54_AHR_CS12_NORMALIZED_STATUS_REF if ready else P7_R54_AHR_CS12_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR_CS12_READY_REASON_REF] if ready else blockers
    question_rows_for_counts = question_rows if ready else []
    blocker_rows_for_counts = blocker_rows if ready else []
    question_row_refs = [str(row.get("question_observation_row_ref")) for row in question_rows_for_counts]
    source_rating_refs = [str(row.get("source_rating_row_ref")) for row in question_rows_for_counts]
    case_refs = [str(row.get("case_ref_id")) for row in question_rows_for_counts]
    blocker_row_refs = [str(row.get("blocker_row_ref")) for row in blocker_rows_for_counts]
    p8_material_count = sum(1 for row in question_rows_for_counts if row.get("p8_design_material_candidate") is True)
    plus_count = sum(1 for row in question_rows_for_counts if row.get("plus_single_question_candidate_later") is True)
    premium_count = sum(1 for row in question_rows_for_counts if row.get("premium_deep_dive_candidate_later") is True)
    p5_repair_count = sum(1 for row in question_rows_for_counts if row.get("p5_repair_required") is True)
    p4_repair_count = sum(1 for row in question_rows_for_counts if row.get("p4_current_surface_repair_required") is True)
    gate_repair_count = sum(1 for row in question_rows_for_counts if row.get("gate_boundary_repair_required") is True)
    emlis_repair_count = sum(1 for row in question_rows_for_counts if row.get("emlis_readfeel_repair_required") is True)
    execution_count = sum(1 for row in question_rows_for_counts if row.get("execution_blocker_present") is True)
    readfeel_count = sum(1 for row in question_rows_for_counts if row.get("readfeel_blocker_present") is True)
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS12_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS12_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs12_blocker_question_need_observation_normalization_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs11_schema_version": rating_material.get("schema_version"),
        "cs11_material_ref": rating_material.get("material_id", ""),
        "cs11_next_required_step": rating_material.get("next_required_step", ""),
        "cs11_rating_row_normalization_status_ref": rating_material.get("rating_row_normalization_status_ref", ""),
        "cs11_blocker_question_need_observation_normalization_allowed_next": rating_material.get(
            "blocker_question_need_observation_normalization_allowed_next"
        ) is True,
        "cs11_rating_row_count": int(rating_material.get("rating_row_count") or 0),
        "cs11_actual_rating_rows_materialized_here": rating_material.get("actual_rating_rows_materialized_here") is True,
        "cs11_actual_human_review_operation_run": rating_material.get("actual_human_review_operation_run") is True,
        "cs11_actual_human_review_executed_by_person": rating_material.get("actual_human_review_executed_by_person") is True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "blocker_question_need_observation_normalization_status_ref": status_ref,
        "blocker_question_need_observation_normalization_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "rating_rows_ready_for_blocker_question_observation_normalization": rating_ready and ready,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "source_rating_row_count": int(rating_material.get("rating_row_count") or 0) if rating_ready else 0,
        "blocker_row_count": len(blocker_rows_for_counts),
        "blocker_rows": blocker_rows_for_counts,
        "blocker_row_refs": blocker_row_refs,
        "blocker_row_ref_count": len(blocker_row_refs),
        "readfeel_blocker_row_count": sum(1 for row in blocker_rows_for_counts if row.get("blocker_kind") == P7_R54_AHR_CS12_READFEEL_BLOCKER_KIND_REF),
        "execution_blocker_row_count": sum(1 for row in blocker_rows_for_counts if row.get("blocker_kind") == P7_R54_AHR_CS12_EXECUTION_BLOCKER_KIND_REF),
        "question_need_observation_row_count": len(question_rows_for_counts),
        "actual_question_need_observation_row_count": len(question_rows_for_counts),
        "question_need_observation_rows": question_rows_for_counts,
        "question_need_observation_row_refs": question_row_refs,
        "question_need_observation_row_ref_count": len(question_row_refs),
        "source_rating_row_refs": source_rating_refs,
        "source_rating_row_ref_count": len(source_rating_refs),
        "case_ref_ids": case_refs,
        "case_ref_id_count": len(case_refs),
        "case_ref_ids_unique": len(case_refs) == len(set(case_refs)) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "question_need_primary_class_counts": _cs_count_values(question_rows_for_counts, "question_need_primary_class"),
        "ambiguity_kind_ref_counts": _cs_count_nested_ids(question_rows_for_counts, "ambiguity_kind_refs"),
        "one_question_fit_ref_counts": _cs_count_values(question_rows_for_counts, "one_question_fit_ref"),
        "repair_required_ref_counts": _cs_count_nested_ids(question_rows_for_counts, "repair_required_refs"),
        "readfeel_blocker_id_counts": _cs_count_nested_ids(question_rows_for_counts, "readfeel_blocker_ids"),
        "execution_blocker_id_counts": _cs_count_nested_ids(question_rows_for_counts, "execution_blocker_ids"),
        "p8_material_candidate_row_count": p8_material_count,
        "plus_single_question_candidate_row_count": plus_count,
        "premium_deep_dive_candidate_row_count": premium_count,
        "p5_repair_required_observation_row_count": p5_repair_count,
        "p4_current_surface_repair_required_row_count": p4_repair_count,
        "gate_boundary_repair_required_row_count": gate_repair_count,
        "emlis_readfeel_repair_required_row_count": emlis_repair_count,
        "execution_blocker_observation_row_count": execution_count,
        "readfeel_blocker_observation_row_count": readfeel_count,
        "blocker_rows_bodyfree_only": ready,
        "blocker_rows_from_rating_rows_only": ready,
        "question_observation_rows_bodyfree_only": ready,
        "question_observation_rows_from_actual_review_only": ready,
        "question_observation_rows_have_allowed_primary_class_refs": ready,
        "question_observation_rows_have_allowed_ambiguity_kind_refs": ready,
        "question_observation_rows_have_allowed_one_question_fit_refs": ready,
        "question_observation_rows_have_allowed_repair_required_refs": ready,
        "question_text_included": False,
        "draft_question_text_included": False,
        "question_text_materialized_here": False,
        "draft_question_text_materialized_here": False,
        "p8_implementation_spec_finalized_here": False,
        "p8_question_text_created_here": False,
        "p8_trigger_logic_created_here": False,
        "p8_storage_or_ui_created_here": False,
        "p5_repair_required_rows_excluded_from_p8_material": ready,
        "p4_current_surface_repair_rows_excluded_from_p8_material": ready,
        "execution_blocker_rows_excluded_from_p8_material": ready,
        "readfeel_blocker_rows_excluded_from_p8_material": ready,
        "question_need_observation_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_human_review_operation_run": rating_material.get("actual_human_review_operation_run") is True and ready,
        "actual_human_review_executed_by_person": rating_material.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": rating_material.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_review_evidence_complete": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "rating_question_consistency_guard_allowed_next": ready,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CS12_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS11_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS13_STEP_REF if ready else P7_R54_AHR_CS12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS12_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS12 blocker / question need observation normalization",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS12_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS12_STEP_REF,
        source="P7-R54-AHR-CS12 blocker / question need observation normalization",
        allowed_true_refs=P7_R54_AHR_CS12_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs11_schema_version") != P7_R54_AHR_CS11_RATING_ROW_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS12 must follow CS11 rating row normalization")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS12 blocker question observation")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS12 blocker question observation")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS12 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS12 historical basis ref changed")
    if data.get("blocker_question_need_observation_normalization_status_ref") not in P7_R54_AHR_CS12_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS12 status changed")
    step_blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("execution_blocker_ids") or []])
    if step_blockers != _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("open_execution_blocker_ids") or []]):
        raise ValueError("P7-R54-AHR-CS12 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
        "question_text_included",
        "draft_question_text_included",
        "question_text_materialized_here",
        "draft_question_text_materialized_here",
        "p8_implementation_spec_finalized_here",
        "p8_question_text_created_here",
        "p8_trigger_logic_created_here",
        "p8_storage_or_ui_created_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS12 must keep {key}=False")
    ready = data.get("blocker_question_need_observation_normalization_status_ref") == P7_R54_AHR_CS12_NORMALIZED_STATUS_REF
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR-CS12 ready material must not carry step blockers")
        for key in (
            "rating_rows_ready_for_blocker_question_observation_normalization",
            "blocker_rows_bodyfree_only",
            "blocker_rows_from_rating_rows_only",
            "question_observation_rows_bodyfree_only",
            "question_observation_rows_from_actual_review_only",
            "question_observation_rows_have_allowed_primary_class_refs",
            "question_observation_rows_have_allowed_ambiguity_kind_refs",
            "question_observation_rows_have_allowed_one_question_fit_refs",
            "question_observation_rows_have_allowed_repair_required_refs",
            "p5_repair_required_rows_excluded_from_p8_material",
            "p4_current_surface_repair_rows_excluded_from_p8_material",
            "execution_blocker_rows_excluded_from_p8_material",
            "readfeel_blocker_rows_excluded_from_p8_material",
            "question_need_observation_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "rating_question_consistency_guard_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS12 ready material must keep {key}=True")
        for field in (
            "source_rating_row_count",
            "question_need_observation_row_count",
            "actual_question_need_observation_row_count",
            "question_need_observation_row_ref_count",
            "source_rating_row_ref_count",
            "case_ref_id_count",
        ):
            if data.get(field) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CS12 {field} changed")
        if data.get("case_ref_ids_unique") is not True:
            raise ValueError("P7-R54-AHR-CS12 case refs must be unique")
        for row in data.get("question_need_observation_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CS12 question observation row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-CS12 question observation row",
            )
            if row.get("schema_version") != P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CS12 question observation row schema changed")
            if row.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
                raise ValueError("P7-R54-AHR-CS12 question observation row current basis changed")
            if row.get("body_free") is not True or row.get("p8_implementation_spec_finalized_here") is not False:
                raise ValueError("P7-R54-AHR-CS12 question observation row boundary changed")
            for key in P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-CS12 question observation row must keep {key}=False")
        for row in data.get("blocker_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CS12 blocker row must be mapping")
            _assert_required_fields(row, required=P7_R54_AHR_CS12_BLOCKER_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-CS12 blocker row")
            if row.get("schema_version") != P7_R54_AHR_CS12_BLOCKER_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CS12 blocker row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CS12 blocker row must be body-free")
            for key in P7_R54_AHR_CS12_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-CS12 blocker row must keep {key}=False")
            if row.get("blocker_kind") == P7_R54_AHR_CS12_READFEEL_BLOCKER_KIND_REF:
                if row.get("routes_to") != P7_R54_AHR_CS12_READFEEL_BLOCKER_ROUTE_REF:
                    raise ValueError("P7-R54-AHR-CS12 readfeel blocker route changed")
            elif row.get("blocker_kind") == P7_R54_AHR_CS12_EXECUTION_BLOCKER_KIND_REF:
                if row.get("routes_to") != P7_R54_AHR_CS12_EXECUTION_BLOCKER_ROUTE_REF:
                    raise ValueError("P7-R54-AHR-CS12 execution blocker route changed")
            else:
                raise ValueError("P7-R54-AHR-CS12 blocker kind changed")
        if data.get("blocker_question_need_observation_normalization_reason_refs") != [P7_R54_AHR_CS12_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS12 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS12_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS12 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS13_STEP_REF:
            raise ValueError("P7-R54-AHR-CS12 next step changed")
    else:
        if data.get("blocker_question_need_observation_normalization_status_ref") != P7_R54_AHR_CS12_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS12 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR-CS12 blocked material must carry blockers")
        if data.get("question_need_observation_rows") != [] or data.get("question_need_observation_row_count") != 0:
            raise ValueError("P7-R54-AHR-CS12 blocked material must not carry question observation rows")
        if data.get("blocker_rows") != [] or data.get("blocker_row_count") != 0:
            raise ValueError("P7-R54-AHR-CS12 blocked material must not carry blocker rows")
        for key in (
            "blocker_rows_bodyfree_only",
            "blocker_rows_from_rating_rows_only",
            "question_observation_rows_bodyfree_only",
            "question_observation_rows_from_actual_review_only",
            "question_need_observation_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "rating_question_consistency_guard_allowed_next",
        ):
            if data.get(key) is not False:
                raise ValueError(f"P7-R54-AHR-CS12 blocked material must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR_CS12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS12 blocked next step changed")
    return True


def _cs_rating_question_consistency_issue_rows(
    question_rows: Sequence[Any], *, review_session_id: str
) -> list[dict[str, Any]]:
    issue_rows: list[dict[str, Any]] = []

    def add_issue(row: Mapping[str, Any], issue_id: str, issue_kind: str) -> None:
        issue_rows.append(
            {
                "schema_version": P7_R54_AHR_CS13_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION,
                "review_session_id": review_session_id,
                "consistency_issue_row_ref": f"consistency_issue_row_{len(issue_rows) + 1:03d}",
                "source_question_observation_row_ref": clean_identifier(
                    row.get("question_observation_row_ref"), default="unknown_question_observation_row", max_length=160
                ),
                "source_rating_row_ref": clean_identifier(row.get("source_rating_row_ref"), default="unknown_rating_row", max_length=160),
                "case_ref_id": clean_identifier(row.get("case_ref_id"), default="unknown_case_ref", max_length=160),
                "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
                "issue_id": issue_id,
                "issue_kind": issue_kind,
                "routes_to": P7_R54_AHR_CS13_CONSISTENCY_ROUTE_REF,
                **{key: False for key in P7_R54_AHR_CS13_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS},
                "body_free": True,
            }
        )

    for index, raw_row in enumerate(question_rows, start=1):
        if not isinstance(raw_row, Mapping):
            add_issue({"case_ref_id": f"invalid_row_{index:02d}"}, "question_observation_row_not_mapping", "contract_violation")
            continue
        row = {str(key): value for key, value in raw_row.items()}
        if _contains_forbidden_body_or_question_key(row):
            add_issue(row, "question_observation_row_contains_forbidden_body_or_question_key", "bodyfree_boundary_leak")
        if row.get("schema_version") != P7_R54_AHR_CS12_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION:
            add_issue(row, "question_observation_row_schema_version_changed", "contract_violation")
        if row.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
            add_issue(row, "question_observation_row_current_basis_ref_changed", "basis_boundary_violation")
        if row.get("p8_implementation_spec_finalized_here") is not False:
            add_issue(row, "p8_implementation_spec_finalized_here", "p8_boundary_violation")
        primary_class = clean_identifier(row.get("question_need_primary_class"), default="", max_length=180)
        one_question_fit_ref = clean_identifier(row.get("one_question_fit_ref"), default="", max_length=180)
        repair_refs = set(_cs_clean_identifier_list(row.get("repair_required_refs") or (), limit=20, max_length=180))
        verdict = clean_identifier(row.get("verdict"), default="", max_length=80)
        p8_candidate = row.get("p8_design_material_candidate") is True
        plus_or_premium_candidate = (
            row.get("plus_single_question_candidate_later") is True
            or row.get("premium_deep_dive_candidate_later") is True
            or p8_candidate
        )
        if verdict in {"RED", "REPAIR_REQUIRED", "BLOCKED", "NOT_REVIEWABLE"} and p8_candidate:
            add_issue(row, "red_repair_or_blocked_verdict_routed_to_p8_material", "rating_question_contradiction")
        if row.get("readfeel_blocker_present") is True and plus_or_premium_candidate:
            add_issue(row, "readfeel_blocker_routed_to_question_candidate", "rating_question_contradiction")
        if row.get("execution_blocker_present") is True and p8_candidate:
            add_issue(row, "execution_blocker_routed_to_p8_material", "rating_question_contradiction")
        if row.get("p5_repair_required") is True and p8_candidate:
            add_issue(row, "p5_repair_row_routed_to_p8_material", "rating_question_contradiction")
        if row.get("p4_current_surface_repair_required") is True and p8_candidate:
            add_issue(row, "p4_current_surface_repair_row_routed_to_p8_material", "rating_question_contradiction")
        if row.get("gate_boundary_repair_required") is True and p8_candidate:
            add_issue(row, "gate_boundary_repair_row_routed_to_p8_material", "rating_question_contradiction")
        if repair_refs - {P7_R54_AHR_CS12_NO_REPAIR_REF} and p8_candidate:
            add_issue(row, "repair_required_row_routed_to_p8_material", "rating_question_contradiction")
        if primary_class in P7_R54_AHR_CS12_P5_REPAIR_PRIMARY_CLASS_REFS and plus_or_premium_candidate:
            add_issue(row, "p5_repair_primary_class_routed_to_question_candidate", "rating_question_contradiction")
        if primary_class in P7_R54_AHR_CS12_P8_MATERIAL_PRIMARY_CLASS_REFS and one_question_fit_ref not in P7_R54_AHR_CS12_P8_MATERIAL_ONE_QUESTION_FIT_REFS:
            add_issue(row, "p8_material_primary_class_without_allowed_question_fit", "rating_question_contradiction")
        if primary_class == "question_would_make_immediate_observation_heavy" and p8_candidate:
            add_issue(row, "heavy_immediate_observation_case_promoted_to_p8_material", "rating_question_contradiction")
    return issue_rows


def build_p7_r54_ahr_cs13_rating_question_consistency_guard(
    *,
    blocker_question_need_observation_normalization: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Guard rating rows and question observations for body-free consistency."""

    question_material = dict(
        blocker_question_need_observation_normalization
        or build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization()
    )
    session_id = _safe_review_session_id(review_session_id)
    question_ready = (
        question_material.get("blocker_question_need_observation_normalization_status_ref") == P7_R54_AHR_CS12_NORMALIZED_STATUS_REF
        and question_material.get("rating_question_consistency_guard_allowed_next") is True
        and question_material.get("question_need_observation_row_count") == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and question_material.get("actual_question_need_observation_rows_materialized_here") is True
    )
    issue_rows = _cs_rating_question_consistency_issue_rows(
        question_material.get("question_need_observation_rows") or [], review_session_id=session_id
    ) if question_ready else []
    blockers: list[str] = []
    if not question_ready:
        blockers.append("cs12_blocker_question_need_observation_normalization_not_ready")
    blockers.extend(str(row.get("issue_id")) for row in issue_rows)
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    ready = question_ready and not issue_rows and not blockers
    status_ref = P7_R54_AHR_CS13_PASSED_STATUS_REF if ready else P7_R54_AHR_CS13_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR_CS13_READY_REASON_REF] if ready else blockers
    question_rows = list(question_material.get("question_need_observation_rows") or []) if question_ready else []
    question_row_refs = [str(row.get("question_observation_row_ref")) for row in question_rows]
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS13_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS13_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs13_rating_question_consistency_guard_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs12_schema_version": question_material.get("schema_version"),
        "cs12_material_ref": question_material.get("material_id", ""),
        "cs12_next_required_step": question_material.get("next_required_step", ""),
        "cs12_blocker_question_need_observation_normalization_status_ref": question_material.get(
            "blocker_question_need_observation_normalization_status_ref", ""
        ),
        "cs12_rating_question_consistency_guard_allowed_next": question_material.get("rating_question_consistency_guard_allowed_next") is True,
        "cs12_question_need_observation_row_count": int(question_material.get("question_need_observation_row_count") or 0),
        "cs12_actual_question_need_observation_rows_materialized_here": question_material.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "consistency_guard_status_ref": status_ref,
        "consistency_guard_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "question_rows_ready_for_consistency_guard": question_ready,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "question_need_observation_row_count": len(question_rows),
        "question_need_observation_row_refs": question_row_refs,
        "question_need_observation_row_ref_count": len(question_row_refs),
        "consistency_issue_rows": issue_rows,
        "consistency_issue_row_count": len(issue_rows),
        "consistency_issue_ids": _cs_dedupe_identifiers([str(row.get("issue_id")) for row in issue_rows]),
        "consistency_issue_id_count": len(_cs_dedupe_identifiers([str(row.get("issue_id")) for row in issue_rows])),
        "open_consistency_issue_count": len(issue_rows),
        "rating_question_consistency_guard_passed": ready,
        "question_text_absent": ready,
        "draft_question_text_absent": ready,
        "p8_implementation_spec_not_finalized_here": ready,
        "p5_repair_rows_excluded_from_p8_material": ready,
        "p4_current_surface_repair_rows_excluded_from_p8_material": ready,
        "execution_blocker_rows_excluded_from_p8_material": ready,
        "readfeel_blocker_rows_excluded_from_p8_material": ready,
        "red_or_repair_rows_excluded_from_p8_material": ready,
        "p8_material_candidate_row_count": int(question_material.get("p8_material_candidate_row_count") or 0) if question_ready else 0,
        "p5_repair_required_observation_row_count": int(question_material.get("p5_repair_required_observation_row_count") or 0) if question_ready else 0,
        "p4_current_surface_repair_required_row_count": int(question_material.get("p4_current_surface_repair_required_row_count") or 0) if question_ready else 0,
        "execution_blocker_observation_row_count": int(question_material.get("execution_blocker_observation_row_count") or 0) if question_ready else 0,
        "readfeel_blocker_observation_row_count": int(question_material.get("readfeel_blocker_observation_row_count") or 0) if question_ready else 0,
        "actual_human_review_operation_run": question_material.get("actual_human_review_operation_run") is True and question_ready,
        "actual_human_review_executed_by_person": question_material.get("actual_human_review_executed_by_person") is True and question_ready,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": question_material.get("actual_rating_rows_materialized_here") is True and question_ready,
        "actual_question_need_observation_rows_materialized_here": question_material.get("actual_question_need_observation_rows_materialized_here") is True and question_ready,
        "actual_review_evidence_complete": False,
        "disposal_receipt_materialized_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "pause_abort_expiration_disposal_receipt_allowed_next": ready,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CS13_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS12_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS13_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS12_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS14_STEP_REF if ready else P7_R54_AHR_CS13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS13_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS13 rating / question consistency guard",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS13_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS13_STEP_REF,
        source="P7-R54-AHR-CS13 rating / question consistency guard",
        allowed_true_refs=P7_R54_AHR_CS13_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs12_schema_version") != P7_R54_AHR_CS12_BLOCKER_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS13 must follow CS12 blocker/question observation normalization")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS13 rating question guard")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS13 rating question guard")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS13 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS13 historical basis ref changed")
    if data.get("consistency_guard_status_ref") not in P7_R54_AHR_CS13_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS13 status changed")
    step_blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("execution_blocker_ids") or []])
    if step_blockers != _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("open_execution_blocker_ids") or []]):
        raise ValueError("P7-R54-AHR-CS13 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS13 must keep {key}=False")
    ready = data.get("consistency_guard_status_ref") == P7_R54_AHR_CS13_PASSED_STATUS_REF
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR-CS13 ready material must not carry blockers")
        if data.get("consistency_issue_rows") != [] or data.get("consistency_issue_row_count") != 0:
            raise ValueError("P7-R54-AHR-CS13 passed material must not carry consistency issues")
        for key in (
            "question_rows_ready_for_consistency_guard",
            "rating_question_consistency_guard_passed",
            "question_text_absent",
            "draft_question_text_absent",
            "p8_implementation_spec_not_finalized_here",
            "p5_repair_rows_excluded_from_p8_material",
            "p4_current_surface_repair_rows_excluded_from_p8_material",
            "execution_blocker_rows_excluded_from_p8_material",
            "readfeel_blocker_rows_excluded_from_p8_material",
            "red_or_repair_rows_excluded_from_p8_material",
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "pause_abort_expiration_disposal_receipt_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS13 ready material must keep {key}=True")
        if data.get("question_need_observation_row_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CS13 question observation row count changed")
        if data.get("question_need_observation_row_ref_count") != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
            raise ValueError("P7-R54-AHR-CS13 question observation row ref count changed")
        if data.get("consistency_guard_reason_refs") != [P7_R54_AHR_CS13_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS13 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS13_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS13 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS14_STEP_REF:
            raise ValueError("P7-R54-AHR-CS13 next step changed")
    else:
        if data.get("consistency_guard_status_ref") != P7_R54_AHR_CS13_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS13 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR-CS13 blocked material must carry blockers")
        if data.get("rating_question_consistency_guard_passed") is not False:
            raise ValueError("P7-R54-AHR-CS13 blocked material must not pass guard")
        if data.get("pause_abort_expiration_disposal_receipt_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-CS13 blocked material must not allow CS14")
        for row in data.get("consistency_issue_rows") or []:
            if not isinstance(row, Mapping):
                raise ValueError("P7-R54-AHR-CS13 issue row must be mapping")
            _assert_required_fields(
                row,
                required=P7_R54_AHR_CS13_CONSISTENCY_ISSUE_ROW_REQUIRED_FIELD_REFS,
                source="P7-R54-AHR-CS13 consistency issue row",
            )
            if row.get("schema_version") != P7_R54_AHR_CS13_CONSISTENCY_ISSUE_ROW_SCHEMA_VERSION:
                raise ValueError("P7-R54-AHR-CS13 issue row schema changed")
            if row.get("body_free") is not True:
                raise ValueError("P7-R54-AHR-CS13 issue row must be body-free")
            for key in P7_R54_AHR_CS13_ISSUE_ROW_BODYFREE_FALSE_FLAG_REFS:
                if row.get(key) is not False:
                    raise ValueError(f"P7-R54-AHR-CS13 issue row must keep {key}=False")
        if data.get("next_required_step") != P7_R54_AHR_CS13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS13 blocked next step changed")
    return True


# ---------------------------------------------------------------------------
# CS14 / CS15 disposal receipt and post-review evidence summary.
# ---------------------------------------------------------------------------
# CS14 closes the body-full local-only packet lifecycle by receiving a body-free
# disposal receipt.  It does not mark review evidence complete by itself.  CS15
# is the first step that may set actual_review_evidence_complete=True, and even
# then it must not promote P5 final, P6, P8, R52 execution, P7 complete, or release.

P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs14_pause_abort_expiration_disposal_receipt.bodyfree.v1"
)
P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs15_bodyfree_post_review_summary_evidence_complete.bodyfree.v1"
)
P7_R54_AHR_CS14_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_SCHEMA_VERSION
)
P7_R54_AHR_CS15_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_SCHEMA_VERSION
)

P7_R54_AHR_CS14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS13_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS14_STEP_REF,
)
P7_R54_AHR_CS14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[15:]
P7_R54_AHR_CS15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS14_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS15_STEP_REF,
)
P7_R54_AHR_CS15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[16:]

P7_R54_AHR_CS14_VERIFIED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
)
P7_R54_AHR_CS14_BLOCKED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_BLOCKED"
)
P7_R54_AHR_CS14_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS14_VERIFIED_STATUS_REF,
    P7_R54_AHR_CS14_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS14_READY_REASON_REF: Final = (
    "r54_ahr_cs_disposal_receipt_verified_bodyfree_current_snapshot"
)
P7_R54_AHR_CS14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS14_repair_disposal_receipt_before_post_review_summary"
)
P7_R54_AHR_CS14_DISPOSAL_RECEIPT_REF_DEFAULT: Final = (
    "R54_AHR_CS_BODY_FULL_PACKET_PURGE_DISPOSAL_RECEIPT_REF"
)
P7_R54_AHR_CS14_PACKET_LIFECYCLE_STATUS_CLOSED_REF: Final = (
    "BODY_FULL_PACKET_LIFECYCLE_CLOSED_BODYFREE"
)
P7_R54_AHR_CS14_PACKET_LIFECYCLE_STATUS_BLOCKED_REF: Final = (
    "BODY_FULL_PACKET_LIFECYCLE_DISPOSAL_RECEIPT_BLOCKED"
)
P7_R54_AHR_CS14_PAUSE_ABORT_STATUS_NOT_APPLICABLE_REF: Final = "pause_abort_not_applicable"
P7_R54_AHR_CS14_EXPIRATION_STATUS_COMPLETED_BEFORE_EXPIRATION_REF: Final = (
    "completed_before_expiration"
)

P7_R54_AHR_CS15_COMPLETE_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_POST_REVIEW_BODYFREE_EVIDENCE_COMPLETE"
)
P7_R54_AHR_CS15_INCOMPLETE_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_POST_REVIEW_BODYFREE_EVIDENCE_INCOMPLETE"
)
P7_R54_AHR_CS15_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS15_COMPLETE_STATUS_REF,
    P7_R54_AHR_CS15_INCOMPLETE_STATUS_REF,
)
P7_R54_AHR_CS15_COMPLETE_REASON_REF: Final = (
    "r54_ahr_cs_actual_review_evidence_complete_bodyfree_post_review_summary"
)
P7_R54_AHR_CS15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS15_repair_post_review_evidence_before_p5_decision_candidate_separation"
)

P7_R54_AHR_CS14_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS13_ALLOWED_TRUE_FALSE_FLAG_REFS,
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
)
P7_R54_AHR_CS15_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS14_ALLOWED_TRUE_FALSE_FLAG_REFS,
    "actual_review_evidence_complete",
)

P7_R54_AHR_CS14_DISPOSAL_REQUIRED_TRUE_FIELD_REFS: Final[tuple[str, ...]] = (
    "disposal_receipt_present",
    "disposal_verified",
    "body_full_packet_deleted_or_purged_ref",
    "reviewer_notes_deleted_or_not_created_ref",
    "packet_lifecycle_closed_bodyfree",
    "disposal_receipt_bodyfree_only",
    "disposal_receipt_refs_only",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
)
P7_R54_AHR_CS15_EVIDENCE_COMPLETE_REQUIRED_TRUE_FIELD_REFS: Final[tuple[str, ...]] = (
    "actual_review_evidence_complete",
    "review_counts_complete",
    "rating_counts_complete",
    "question_observation_counts_complete",
    "disposal_evidence_complete",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
)

P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs13_schema_version",
    "cs13_material_ref",
    "cs13_next_required_step",
    "cs13_consistency_guard_status_ref",
    "cs13_pause_abort_expiration_disposal_receipt_allowed_next",
    "cs13_rating_question_consistency_guard_passed",
    "cs13_question_need_observation_row_count",
    "cs13_actual_rating_rows_materialized_here",
    "cs13_actual_question_need_observation_rows_materialized_here",
    "cs13_actual_human_review_operation_run",
    "cs13_actual_human_review_executed_by_person",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "disposal_receipt_status_ref",
    "disposal_receipt_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "rating_question_consistency_guard_ready_for_disposal",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_receipt_ref",
    "disposal_receipt_ref_present",
    "disposal_receipt_present",
    "disposal_verified",
    "body_full_packet_deleted_or_purged_ref",
    "reviewer_notes_deleted_or_not_created_ref",
    "pause_or_abort_status_ref",
    "expiration_status_ref",
    "packet_lifecycle_status_ref",
    "packet_lifecycle_closed_bodyfree",
    "disposal_receipt_bodyfree_only",
    "disposal_receipt_refs_only",
    "body_full_packet_content_included",
    "reviewer_notes_body_included",
    "local_path_included",
    "local_absolute_path_included",
    "body_hash_included",
    "terminal_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
    "bodyfree_post_review_summary_allowed_next",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS14_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs14_schema_version",
    "cs14_material_ref",
    "cs14_next_required_step",
    "cs14_disposal_receipt_status_ref",
    "cs14_disposal_verified",
    "cs14_actual_disposal_receipt_materialized_here",
    "cs14_bodyfree_post_review_summary_allowed_next",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "post_review_summary_status_ref",
    "post_review_summary_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "disposal_verified",
    "review_counts_complete",
    "rating_counts_complete",
    "question_observation_counts_complete",
    "disposal_evidence_complete",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "actual_review_evidence_complete",
    "actual_human_review_complete",
    "p5_confirmed_candidate_not_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p6_limited_human_readfeel_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "actual_r52_reintake_execution_confirmed",
    "r52_reintake_handoff_ready_here",
    "p5_finalization_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "r52_reintake_claim_blocked_here",
    "p5_decision_candidate_separation_allowed_next",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS15_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_REQUIRED_FIELD_REFS
)


def _cs_bool(value: Any) -> bool:
    return value is True


def _cs14_disposal_input_blockers(
    *,
    disposal_receipt_ref: str,
    disposal_receipt_present: bool,
    disposal_verified: bool,
    body_full_packet_deleted_or_purged_ref: bool,
    reviewer_notes_deleted_or_not_created_ref: bool,
    packet_lifecycle_closed_bodyfree: bool,
    body_full_packet_content_included: bool,
    reviewer_notes_body_included: bool,
    local_path_included: bool,
    local_absolute_path_included: bool,
    body_hash_included: bool,
    terminal_output_body_included: bool,
    stdout_body_included: bool,
    stderr_body_included: bool,
    traceback_body_included: bool,
) -> list[str]:
    blockers: list[str] = []
    if not disposal_receipt_ref:
        blockers.append("disposal_receipt_ref_missing")
    if disposal_receipt_present is not True:
        blockers.append("disposal_receipt_present_not_true")
    if disposal_verified is not True:
        blockers.append("disposal_verified_not_true")
    if body_full_packet_deleted_or_purged_ref is not True:
        blockers.append("body_full_packet_deleted_or_purged_ref_not_true")
    if reviewer_notes_deleted_or_not_created_ref is not True:
        blockers.append("reviewer_notes_deleted_or_not_created_ref_not_true")
    if packet_lifecycle_closed_bodyfree is not True:
        blockers.append("packet_lifecycle_closed_bodyfree_not_true")
    leak_flags = {
        "body_full_packet_content_included": body_full_packet_content_included,
        "reviewer_notes_body_included": reviewer_notes_body_included,
        "local_path_included": local_path_included,
        "local_absolute_path_included": local_absolute_path_included,
        "body_hash_included": body_hash_included,
        "terminal_output_body_included": terminal_output_body_included,
        "stdout_body_included": stdout_body_included,
        "stderr_body_included": stderr_body_included,
        "traceback_body_included": traceback_body_included,
    }
    for flag_ref, flag_value in leak_flags.items():
        if flag_value is True:
            blockers.append(f"{flag_ref}_must_remain_false")
    return blockers


def build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt(
    *,
    rating_question_consistency_guard: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
    disposal_receipt_ref: Any = P7_R54_AHR_CS14_DISPOSAL_RECEIPT_REF_DEFAULT,
    disposal_receipt_present: bool = False,
    disposal_verified: bool = False,
    body_full_packet_deleted_or_purged_ref: bool = False,
    reviewer_notes_deleted_or_not_created_ref: bool = False,
    packet_lifecycle_closed_bodyfree: bool = False,
    pause_or_abort_status_ref: Any = P7_R54_AHR_CS14_PAUSE_ABORT_STATUS_NOT_APPLICABLE_REF,
    expiration_status_ref: Any = P7_R54_AHR_CS14_EXPIRATION_STATUS_COMPLETED_BEFORE_EXPIRATION_REF,
    body_full_packet_content_included: bool = False,
    reviewer_notes_body_included: bool = False,
    local_path_included: bool = False,
    local_absolute_path_included: bool = False,
    body_hash_included: bool = False,
    terminal_output_body_included: bool = False,
    stdout_body_included: bool = False,
    stderr_body_included: bool = False,
    traceback_body_included: bool = False,
) -> dict[str, Any]:
    """Intake a body-free disposal receipt after CS13 without completing evidence."""

    consistency_material = dict(
        rating_question_consistency_guard or build_p7_r54_ahr_cs13_rating_question_consistency_guard()
    )
    session_id = _safe_review_session_id(review_session_id)
    safe_receipt_ref = clean_identifier(
        disposal_receipt_ref,
        default=P7_R54_AHR_CS14_DISPOSAL_RECEIPT_REF_DEFAULT,
        max_length=180,
    )
    consistency_ready = (
        consistency_material.get("schema_version") == P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
        and consistency_material.get("consistency_guard_status_ref") == P7_R54_AHR_CS13_PASSED_STATUS_REF
        and consistency_material.get("pause_abort_expiration_disposal_receipt_allowed_next") is True
        and consistency_material.get("next_required_step") == P7_R54_AHR_CS14_STEP_REF
        and int(consistency_material.get("question_need_observation_row_count") or 0) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
        and consistency_material.get("actual_human_review_operation_run") is True
        and consistency_material.get("actual_human_review_executed_by_person") is True
        and consistency_material.get("actual_rating_rows_materialized_here") is True
        and consistency_material.get("actual_question_need_observation_rows_materialized_here") is True
    )
    blockers: list[str] = []
    if not consistency_ready:
        blockers.append("cs13_rating_question_consistency_guard_not_ready_for_disposal_receipt")
    blockers.extend(
        _cs14_disposal_input_blockers(
            disposal_receipt_ref=safe_receipt_ref,
            disposal_receipt_present=disposal_receipt_present,
            disposal_verified=disposal_verified,
            body_full_packet_deleted_or_purged_ref=body_full_packet_deleted_or_purged_ref,
            reviewer_notes_deleted_or_not_created_ref=reviewer_notes_deleted_or_not_created_ref,
            packet_lifecycle_closed_bodyfree=packet_lifecycle_closed_bodyfree,
            body_full_packet_content_included=body_full_packet_content_included,
            reviewer_notes_body_included=reviewer_notes_body_included,
            local_path_included=local_path_included,
            local_absolute_path_included=local_absolute_path_included,
            body_hash_included=body_hash_included,
            terminal_output_body_included=terminal_output_body_included,
            stdout_body_included=stdout_body_included,
            stderr_body_included=stderr_body_included,
            traceback_body_included=traceback_body_included,
        )
    )
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    ready = consistency_ready and not blockers
    status_ref = P7_R54_AHR_CS14_VERIFIED_STATUS_REF if ready else P7_R54_AHR_CS14_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR_CS14_READY_REASON_REF] if ready else blockers
    source_case_count = P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT if consistency_ready else 0
    question_count = int(consistency_material.get("question_need_observation_row_count") or 0) if consistency_ready else 0
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS14_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS14_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs13_schema_version": consistency_material.get("schema_version"),
        "cs13_material_ref": consistency_material.get("material_id", ""),
        "cs13_next_required_step": consistency_material.get("next_required_step", ""),
        "cs13_consistency_guard_status_ref": consistency_material.get("consistency_guard_status_ref", ""),
        "cs13_pause_abort_expiration_disposal_receipt_allowed_next": consistency_material.get(
            "pause_abort_expiration_disposal_receipt_allowed_next"
        ) is True,
        "cs13_rating_question_consistency_guard_passed": consistency_material.get("rating_question_consistency_guard_passed") is True,
        "cs13_question_need_observation_row_count": int(consistency_material.get("question_need_observation_row_count") or 0),
        "cs13_actual_rating_rows_materialized_here": consistency_material.get("actual_rating_rows_materialized_here") is True,
        "cs13_actual_question_need_observation_rows_materialized_here": consistency_material.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True,
        "cs13_actual_human_review_operation_run": consistency_material.get("actual_human_review_operation_run") is True,
        "cs13_actual_human_review_executed_by_person": consistency_material.get("actual_human_review_executed_by_person") is True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "disposal_receipt_status_ref": status_ref,
        "disposal_receipt_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "rating_question_consistency_guard_ready_for_disposal": consistency_ready,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": source_case_count,
        "rating_row_count": source_case_count,
        "question_observation_row_count": question_count,
        "disposal_receipt_ref": safe_receipt_ref,
        "disposal_receipt_ref_present": bool(safe_receipt_ref),
        "disposal_receipt_present": disposal_receipt_present is True,
        "disposal_verified": ready,
        "body_full_packet_deleted_or_purged_ref": ready,
        "reviewer_notes_deleted_or_not_created_ref": ready,
        "pause_or_abort_status_ref": clean_identifier(
            pause_or_abort_status_ref,
            default=P7_R54_AHR_CS14_PAUSE_ABORT_STATUS_NOT_APPLICABLE_REF,
            max_length=120,
        ),
        "expiration_status_ref": clean_identifier(
            expiration_status_ref,
            default=P7_R54_AHR_CS14_EXPIRATION_STATUS_COMPLETED_BEFORE_EXPIRATION_REF,
            max_length=120,
        ),
        "packet_lifecycle_status_ref": (
            P7_R54_AHR_CS14_PACKET_LIFECYCLE_STATUS_CLOSED_REF
            if ready
            else P7_R54_AHR_CS14_PACKET_LIFECYCLE_STATUS_BLOCKED_REF
        ),
        "packet_lifecycle_closed_bodyfree": ready,
        "disposal_receipt_bodyfree_only": ready,
        "disposal_receipt_refs_only": ready,
        "body_full_packet_content_included": False,
        "reviewer_notes_body_included": False,
        "local_path_included": False,
        "local_absolute_path_included": False,
        "body_hash_included": False,
        "terminal_output_body_included": False,
        "stdout_body_included": False,
        "stderr_body_included": False,
        "traceback_body_included": False,
        "no_body_leak_validation_passed": ready,
        "no_question_text_validation_passed": ready,
        "no_touch_validation_passed": ready,
        "actual_human_review_operation_run": consistency_material.get("actual_human_review_operation_run") is True and ready,
        "actual_human_review_executed_by_person": consistency_material.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": consistency_material.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": consistency_material.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and ready,
        "actual_disposal_receipt_materialized_here": ready,
        "actual_review_evidence_complete": False,
        "bodyfree_post_review_summary_allowed_next": ready,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CS14_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS14_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS13_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS15_STEP_REF if ready else P7_R54_AHR_CS14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS14_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS14 pause/abort/expiration/disposal receipt",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS14_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS14_STEP_REF,
        source="P7-R54-AHR-CS14 disposal receipt",
        allowed_true_refs=P7_R54_AHR_CS14_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs13_schema_version") != P7_R54_AHR_CS13_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS14 must follow CS13 rating-question consistency guard")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS14 disposal receipt")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS14 disposal receipt")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS14 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS14 historical basis ref changed")
    if data.get("disposal_receipt_status_ref") not in P7_R54_AHR_CS14_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS14 status changed")
    step_blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("execution_blocker_ids") or []])
    if step_blockers != _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("open_execution_blocker_ids") or []]):
        raise ValueError("P7-R54-AHR-CS14 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_review_evidence_complete",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS14 must keep {key}=False")
    ready = data.get("disposal_receipt_status_ref") == P7_R54_AHR_CS14_VERIFIED_STATUS_REF
    if ready:
        if step_blockers:
            raise ValueError("P7-R54-AHR-CS14 verified material must not carry blockers")
        for key in P7_R54_AHR_CS14_DISPOSAL_REQUIRED_TRUE_FIELD_REFS:
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS14 verified material must keep {key}=True")
        for key in (
            "rating_question_consistency_guard_ready_for_disposal",
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "bodyfree_post_review_summary_allowed_next",
            "r52_reintake_claim_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "p5_finalization_blocked_here",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS14 verified material must keep {key}=True")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_key) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CS14 {count_key} changed")
        if data.get("disposal_receipt_reason_refs") != [P7_R54_AHR_CS14_READY_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS14 ready reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS14_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS14 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS14 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS15_STEP_REF:
            raise ValueError("P7-R54-AHR-CS14 next step changed")
    else:
        if data.get("disposal_receipt_status_ref") != P7_R54_AHR_CS14_BLOCKED_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS14 blocked status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR-CS14 blocked material must carry blockers")
        if data.get("disposal_verified") is not False:
            raise ValueError("P7-R54-AHR-CS14 blocked material must not verify disposal")
        if data.get("actual_disposal_receipt_materialized_here") is not False:
            raise ValueError("P7-R54-AHR-CS14 blocked material must not materialize actual disposal receipt")
        if data.get("bodyfree_post_review_summary_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-CS14 blocked material must not allow CS15")
        if data.get("next_required_step") != P7_R54_AHR_CS14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS14 blocked next step changed")
    return True


def build_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete(
    *,
    pause_abort_expiration_disposal_receipt: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
) -> dict[str, Any]:
    """Summarize body-free post-review evidence and decide evidence completeness."""

    disposal_material = dict(
        pause_abort_expiration_disposal_receipt
        or build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt()
    )
    session_id = _safe_review_session_id(review_session_id)
    review_counts_complete = int(disposal_material.get("reviewed_case_count") or 0) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    rating_counts_complete = int(disposal_material.get("rating_row_count") or 0) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    question_counts_complete = int(disposal_material.get("question_observation_row_count") or 0) == P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT
    disposal_complete = (
        disposal_material.get("disposal_receipt_status_ref") == P7_R54_AHR_CS14_VERIFIED_STATUS_REF
        and disposal_material.get("bodyfree_post_review_summary_allowed_next") is True
        and disposal_material.get("disposal_verified") is True
        and disposal_material.get("actual_disposal_receipt_materialized_here") is True
        and disposal_material.get("next_required_step") == P7_R54_AHR_CS15_STEP_REF
    )
    no_body = disposal_material.get("no_body_leak_validation_passed") is True
    no_question = disposal_material.get("no_question_text_validation_passed") is True
    no_touch = disposal_material.get("no_touch_validation_passed") is True
    blockers: list[str] = []
    if not disposal_complete:
        blockers.append("cs14_disposal_receipt_not_verified_for_post_review_summary")
    if not review_counts_complete:
        blockers.append("reviewed_case_count_not_24")
    if not rating_counts_complete:
        blockers.append("rating_row_count_not_24")
    if not question_counts_complete:
        blockers.append("question_observation_row_count_not_24")
    if not no_body:
        blockers.append("no_body_leak_validation_not_passed")
    if not no_question:
        blockers.append("no_question_text_validation_not_passed")
    if not no_touch:
        blockers.append("no_touch_validation_not_passed")
    blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in blockers])
    complete = not blockers
    status_ref = P7_R54_AHR_CS15_COMPLETE_STATUS_REF if complete else P7_R54_AHR_CS15_INCOMPLETE_STATUS_REF
    reason_refs = [P7_R54_AHR_CS15_COMPLETE_REASON_REF] if complete else blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS15_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS15_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs14_schema_version": disposal_material.get("schema_version"),
        "cs14_material_ref": disposal_material.get("material_id", ""),
        "cs14_next_required_step": disposal_material.get("next_required_step", ""),
        "cs14_disposal_receipt_status_ref": disposal_material.get("disposal_receipt_status_ref", ""),
        "cs14_disposal_verified": disposal_material.get("disposal_verified") is True,
        "cs14_actual_disposal_receipt_materialized_here": disposal_material.get("actual_disposal_receipt_materialized_here") is True,
        "cs14_bodyfree_post_review_summary_allowed_next": disposal_material.get("bodyfree_post_review_summary_allowed_next") is True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "post_review_summary_status_ref": status_ref,
        "post_review_summary_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(disposal_material.get("reviewed_case_count") or 0) if disposal_complete else 0,
        "rating_row_count": int(disposal_material.get("rating_row_count") or 0) if disposal_complete else 0,
        "question_observation_row_count": int(disposal_material.get("question_observation_row_count") or 0) if disposal_complete else 0,
        "disposal_verified": disposal_complete,
        "review_counts_complete": review_counts_complete and disposal_complete,
        "rating_counts_complete": rating_counts_complete and disposal_complete,
        "question_observation_counts_complete": question_counts_complete and disposal_complete,
        "disposal_evidence_complete": disposal_complete,
        "no_body_leak_validation_passed": no_body and disposal_complete,
        "no_question_text_validation_passed": no_question and disposal_complete,
        "no_touch_validation_passed": no_touch and disposal_complete,
        "actual_human_review_operation_run": disposal_material.get("actual_human_review_operation_run") is True and complete,
        "actual_human_review_executed_by_person": disposal_material.get("actual_human_review_executed_by_person") is True and complete,
        "actual_human_review_run_here": False,
        "actual_rating_rows_materialized_here": disposal_material.get("actual_rating_rows_materialized_here") is True and complete,
        "actual_question_need_observation_rows_materialized_here": disposal_material.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and complete,
        "actual_disposal_receipt_materialized_here": disposal_material.get("actual_disposal_receipt_materialized_here") is True and complete,
        "actual_review_evidence_complete": complete,
        "actual_human_review_complete": False,
        "p5_confirmed_candidate_not_finalized_here": complete,
        "p5_human_blind_qa_confirmed_final": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "actual_r52_reintake_execution_confirmed": False,
        "r52_reintake_handoff_ready_here": False,
        "p5_finalization_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "r52_reintake_claim_blocked_here": True,
        "p5_decision_candidate_separation_allowed_next": complete,
        "implemented_steps": list(P7_R54_AHR_CS15_IMPLEMENTED_STEPS if complete else P7_R54_AHR_CS14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS15_NOT_YET_IMPLEMENTED_STEPS if complete else P7_R54_AHR_CS14_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS16_STEP_REF if complete else P7_R54_AHR_CS15_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS15_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS15 body-free post-review summary",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS15_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS15_STEP_REF,
        source="P7-R54-AHR-CS15 body-free post-review summary",
        allowed_true_refs=P7_R54_AHR_CS15_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs14_schema_version") != P7_R54_AHR_CS14_PAUSE_ABORT_EXPIRATION_DISPOSAL_RECEIPT_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS15 must follow CS14 disposal receipt")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS15 post-review summary")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS15 post-review summary")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS15 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS15 historical basis ref changed")
    if data.get("post_review_summary_status_ref") not in P7_R54_AHR_CS15_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS15 status changed")
    step_blockers = _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("execution_blocker_ids") or []])
    if step_blockers != _cs_dedupe_identifiers([clean_identifier(value, max_length=240) for value in data.get("open_execution_blocker_ids") or []]):
        raise ValueError("P7-R54-AHR-CS15 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "p5_human_blind_qa_confirmed_final",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "actual_r52_reintake_execution_confirmed",
        "r52_reintake_handoff_ready_here",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS15 must keep {key}=False")
    complete = data.get("post_review_summary_status_ref") == P7_R54_AHR_CS15_COMPLETE_STATUS_REF
    if complete:
        if step_blockers:
            raise ValueError("P7-R54-AHR-CS15 complete material must not carry blockers")
        for key in P7_R54_AHR_CS15_EVIDENCE_COMPLETE_REQUIRED_TRUE_FIELD_REFS:
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS15 complete material must keep {key}=True")
        for key in (
            "actual_human_review_operation_run",
            "actual_human_review_executed_by_person",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "p5_confirmed_candidate_not_finalized_here",
            "p5_finalization_blocked_here",
            "p6_p8_release_promotion_blocked_here",
            "r52_reintake_claim_blocked_here",
            "p5_decision_candidate_separation_allowed_next",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS15 complete material must keep {key}=True")
        for count_key in ("reviewed_case_count", "rating_row_count", "question_observation_row_count"):
            if data.get(count_key) != P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT:
                raise ValueError(f"P7-R54-AHR-CS15 {count_key} changed")
        if data.get("post_review_summary_reason_refs") != [P7_R54_AHR_CS15_COMPLETE_REASON_REF]:
            raise ValueError("P7-R54-AHR-CS15 complete reason changed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS15 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS16_STEP_REF:
            raise ValueError("P7-R54-AHR-CS15 next step changed")
    else:
        if data.get("post_review_summary_status_ref") != P7_R54_AHR_CS15_INCOMPLETE_STATUS_REF:
            raise ValueError("P7-R54-AHR-CS15 incomplete status changed")
        if not step_blockers:
            raise ValueError("P7-R54-AHR-CS15 incomplete material must carry blockers")
        if data.get("actual_review_evidence_complete") is not False:
            raise ValueError("P7-R54-AHR-CS15 incomplete material must not complete evidence")
        if data.get("p5_decision_candidate_separation_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-CS15 incomplete material must not allow CS16")
        if data.get("next_required_step") != P7_R54_AHR_CS15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS15 blocked next step changed")
    return True


# ---------------------------------------------------------------------------
# CS16 / CS17 P5 decision candidate separation and candidate-only handoff.
# ---------------------------------------------------------------------------
# CS16 is allowed only after CS15 body-free evidence is complete.  It separates
# a P5_CONFIRMED_CANDIDATE from repair / blocked / inconclusive outcomes, but it
# never turns that candidate into P5 final.  CS17 may then build body-free
# candidate-only envelopes for P6/P8 and an R52 handoff ref.  CS17 must still not
# start P6, start P8, execute R52 re-intake, complete P7, or allow release.

P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs16_p5_decision_candidate_separation.bodyfree.v1"
)
P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs17_p6_p8_candidate_only_r52_handoff_envelope.bodyfree.v1"
)
P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION
)
P7_R54_AHR_CS17_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_SCHEMA_VERSION
)

P7_R54_AHR_CS16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS15_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS16_STEP_REF,
)
P7_R54_AHR_CS16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[17:]
P7_R54_AHR_CS17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS16_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS17_STEP_REF,
)
P7_R54_AHR_CS17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R54_AHR_CS_STEP_REFS[18:]

P7_R54_AHR_CS16_DECISION_P5_CONFIRMED_CANDIDATE_REF: Final = "P5_CONFIRMED_CANDIDATE"
P7_R54_AHR_CS16_DECISION_P5_REPAIR_RETURN_REQUIRED_REF: Final = "P5_REPAIR_RETURN_REQUIRED"
P7_R54_AHR_CS16_DECISION_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF: Final = "P4_CURRENT_ONLY_REPAIR_REQUIRED"
P7_R54_AHR_CS16_DECISION_R54_OPERATION_INCONCLUSIVE_REF: Final = "R54_OPERATION_INCONCLUSIVE"
P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION_REF: Final = (
    "R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION"
)
P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF: Final = "R54_OPERATION_BLOCKED_DISPOSAL"
P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF: Final = (
    "R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT"
)
P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_NO_TOUCH_REF: Final = "R54_OPERATION_BLOCKED_NO_TOUCH"
P7_R54_AHR_CS16_ALLOWED_DECISION_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS16_DECISION_P5_CONFIRMED_CANDIDATE_REF,
    P7_R54_AHR_CS16_DECISION_P5_REPAIR_RETURN_REQUIRED_REF,
    P7_R54_AHR_CS16_DECISION_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF,
    P7_R54_AHR_CS16_DECISION_R54_OPERATION_INCONCLUSIVE_REF,
    P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION_REF,
    P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF,
    P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
    P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_NO_TOUCH_REF,
)
P7_R54_AHR_CS16_READY_REASON_REF: Final = (
    "r54_ahr_cs_p5_confirmed_candidate_separated_candidate_only_not_final"
)
P7_R54_AHR_CS16_P5_REPAIR_REASON_REF: Final = "r54_ahr_cs_p5_repair_return_required_before_candidate_handoff"
P7_R54_AHR_CS16_P4_REPAIR_REASON_REF: Final = "r54_ahr_cs_p4_current_only_repair_required_before_candidate_handoff"
P7_R54_AHR_CS16_INCONCLUSIVE_REASON_REF: Final = "r54_ahr_cs_operation_inconclusive_before_candidate_handoff"
P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS16_repair_or_complete_evidence_before_p5_decision_candidate_separation"
)
P7_R54_AHR_CS16_P5_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "return_to_P5_repair_before_R52_handoff"
P7_R54_AHR_CS16_P4_REPAIR_NEXT_REQUIRED_STEP_REF: Final = "return_to_P4_current_only_repair_before_R52_handoff"
P7_R54_AHR_CS16_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "recheck_R54_actual_review_evidence_before_R52_handoff"

P7_R54_AHR_CS17_READY_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_READY"
)
P7_R54_AHR_CS17_BLOCKED_STATUS_REF: Final = (
    "CURRENT_SNAPSHOT_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_BLOCKED"
)
P7_R54_AHR_CS17_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS17_READY_STATUS_REF,
    P7_R54_AHR_CS17_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS17_READY_REASON_REF: Final = (
    "r54_ahr_cs_candidate_only_handoff_ready_without_r52_execution_or_p8_start"
)
P7_R54_AHR_CS17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "R54-AHR-CS17_repair_p5_decision_candidate_before_candidate_only_handoff"
)
P7_R54_AHR_CS17_R52_HANDOFF_REF_DEFAULT: Final = (
    "R54_AHR_CS17_R52_REINTAKE_HANDOFF_READY_BODYFREE_REF"
)
P7_R54_AHR_CS17_DEFAULT_P8_MATERIAL_CANDIDATE_REFS: Final[tuple[str, ...]] = ()
P7_R54_AHR_CS17_ALLOWED_P8_MATERIAL_CANDIDATE_CLASS_REFS: Final[tuple[str, ...]] = (
    "question_may_reduce_overread_risk",
    "plus_single_question_candidate_later",
    "premium_deep_dive_candidate_later",
)

P7_R54_AHR_CS16_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CS15_ALLOWED_TRUE_FALSE_FLAG_REFS
P7_R54_AHR_CS17_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CS16_ALLOWED_TRUE_FALSE_FLAG_REFS

P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs15_schema_version",
    "cs15_material_ref",
    "cs15_next_required_step",
    "cs15_post_review_summary_status_ref",
    "cs15_actual_review_evidence_complete",
    "cs15_p5_decision_candidate_separation_allowed_next",
    "cs15_reviewed_case_count",
    "cs15_rating_row_count",
    "cs15_question_observation_row_count",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "p5_decision_candidate_status_ref",
    "p5_decision_candidate_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "cs15_ready_for_p5_decision_candidate_separation",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "actual_review_evidence_complete",
    "review_counts_complete",
    "rating_counts_complete",
    "question_observation_counts_complete",
    "disposal_evidence_complete",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "p5_decision_candidate_separation_reached",
    "p5_decision_candidate_separated_here",
    "p5_confirmed_candidate",
    "p5_confirmed_candidate_not_finalized_here",
    "p5_repair_return_required",
    "p4_current_only_repair_required",
    "r54_operation_inconclusive",
    "r54_operation_blocked",
    "operation_blocked_by_preflight_or_execution",
    "operation_blocked_by_disposal",
    "operation_blocked_by_body_leak_or_question_text",
    "operation_blocked_by_no_touch",
    "p6_p8_candidate_only_r52_handoff_allowed_next",
    "actual_r52_reintake_execution_confirmed",
    "r52_reintake_handoff_ready_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS
)

P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs16_schema_version",
    "cs16_material_ref",
    "cs16_next_required_step",
    "cs16_p5_decision_candidate_status_ref",
    "cs16_p5_confirmed_candidate",
    "cs16_actual_review_evidence_complete",
    "cs16_p6_p8_candidate_only_r52_handoff_allowed_next",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "candidate_handoff_status_ref",
    "candidate_handoff_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "actual_review_evidence_complete",
    "review_counts_complete",
    "rating_counts_complete",
    "question_observation_counts_complete",
    "disposal_evidence_complete",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "p5_confirmed_candidate",
    "p5_confirmed_candidate_not_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_candidate_only_handoff_built",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_material_candidate_only_handoff_built",
    "p8_question_design_material_candidate",
    "p8_material_candidate_refs",
    "p8_material_candidate_ref_count",
    "p8_material_candidate_source_ref",
    "p8_material_candidate_source_observation_row_count",
    "p8_material_candidate_allowed_class_refs",
    "p8_material_candidate_classes_are_allowed",
    "p8_material_candidate_question_text_included",
    "p8_material_candidate_draft_question_text_included",
    "p8_material_candidate_question_answer_persistence_started",
    "p8_material_candidate_excludes_p5_repair_required_cases",
    "p8_material_candidate_excludes_p4_current_only_repair_required_cases",
    "p8_material_candidate_excludes_execution_blocker_cases",
    "p8_start_allowed",
    "r52_reintake_handoff_envelope_built",
    "r52_reintake_handoff_ref",
    "r52_reintake_handoff_ready",
    "r52_reintake_handoff_ready_here",
    "actual_r52_reintake_execution_confirmed",
    "r52_reintake_execution_requested_here",
    "r52_reintake_claim_blocked_here",
    "p6_p8_release_promotion_blocked_here",
    "p5_finalization_blocked_here",
    "p7_complete",
    "release_allowed",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS17_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final = (
    P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_REQUIRED_FIELD_REFS
)


def _cs16_classify_incomplete_summary(blockers: Sequence[Any]) -> str:
    blocker_refs = {clean_identifier(value, max_length=240) for value in blockers}
    if any("disposal" in ref for ref in blocker_refs):
        return P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF
    if any("no_body" in ref or "body_leak" in ref or "question_text" in ref for ref in blocker_refs):
        return P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF
    if any("no_touch" in ref for ref in blocker_refs):
        return P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_NO_TOUCH_REF
    return P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION_REF


def _cs16_decision_values(
    *,
    cs15_ready: bool,
    cs15_blockers: Sequence[Any],
    p5_repair_return_required: bool,
    p4_current_only_repair_required: bool,
    r54_operation_inconclusive: bool,
    operation_blocked_preflight_or_execution: bool,
    operation_blocked_disposal: bool,
    operation_blocked_body_leak_or_question_text: bool,
    operation_blocked_no_touch: bool,
    decision_reason_refs: Sequence[Any] | None,
) -> tuple[str, list[str], list[str], str]:
    reasons = _cs_clean_identifier_list(decision_reason_refs, limit=24, max_length=220)
    blockers: list[str] = []
    if not cs15_ready:
        decision_ref = _cs16_classify_incomplete_summary(cs15_blockers)
        blockers = _cs_clean_identifier_list(cs15_blockers, limit=40, max_length=240) or ["cs15_actual_review_evidence_not_complete"]
        return decision_ref, reasons or blockers, blockers, P7_R54_AHR_CS15_BLOCKED_NEXT_REQUIRED_STEP_REF
    if operation_blocked_body_leak_or_question_text:
        decision_ref = P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF
        blockers = ["r54_operation_blocked_body_leak_or_question_text"]
        return decision_ref, reasons or blockers, blockers, P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF
    if operation_blocked_no_touch:
        decision_ref = P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_NO_TOUCH_REF
        blockers = ["r54_operation_blocked_no_touch"]
        return decision_ref, reasons or blockers, blockers, P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF
    if operation_blocked_disposal:
        decision_ref = P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF
        blockers = ["r54_operation_blocked_disposal"]
        return decision_ref, reasons or blockers, blockers, P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF
    if operation_blocked_preflight_or_execution:
        decision_ref = P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION_REF
        blockers = ["r54_operation_blocked_preflight_or_execution"]
        return decision_ref, reasons or blockers, blockers, P7_R54_AHR_CS16_BLOCKED_NEXT_REQUIRED_STEP_REF
    if p5_repair_return_required:
        return (
            P7_R54_AHR_CS16_DECISION_P5_REPAIR_RETURN_REQUIRED_REF,
            reasons or [P7_R54_AHR_CS16_P5_REPAIR_REASON_REF],
            [],
            P7_R54_AHR_CS16_P5_REPAIR_NEXT_REQUIRED_STEP_REF,
        )
    if p4_current_only_repair_required:
        return (
            P7_R54_AHR_CS16_DECISION_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF,
            reasons or [P7_R54_AHR_CS16_P4_REPAIR_REASON_REF],
            [],
            P7_R54_AHR_CS16_P4_REPAIR_NEXT_REQUIRED_STEP_REF,
        )
    if r54_operation_inconclusive:
        return (
            P7_R54_AHR_CS16_DECISION_R54_OPERATION_INCONCLUSIVE_REF,
            reasons or [P7_R54_AHR_CS16_INCONCLUSIVE_REASON_REF],
            [],
            P7_R54_AHR_CS16_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF,
        )
    return (
        P7_R54_AHR_CS16_DECISION_P5_CONFIRMED_CANDIDATE_REF,
        reasons or [P7_R54_AHR_CS16_READY_REASON_REF],
        [],
        P7_R54_AHR_CS17_STEP_REF,
    )


def build_p7_r54_ahr_cs16_p5_decision_candidate_separation(
    *,
    bodyfree_post_review_summary: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
    p5_repair_return_required: bool = False,
    p4_current_only_repair_required: bool = False,
    r54_operation_inconclusive: bool = False,
    operation_blocked_preflight_or_execution: bool = False,
    operation_blocked_disposal: bool = False,
    operation_blocked_body_leak_or_question_text: bool = False,
    operation_blocked_no_touch: bool = False,
    decision_reason_refs: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Separate P5 decision candidates without promoting P5 final or later phases."""

    summary = dict(
        bodyfree_post_review_summary
        or build_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete()
    )
    session_id = _safe_review_session_id(review_session_id)
    cs15_ready = (
        summary.get("post_review_summary_status_ref") == P7_R54_AHR_CS15_COMPLETE_STATUS_REF
        and summary.get("actual_review_evidence_complete") is True
        and summary.get("p5_decision_candidate_separation_allowed_next") is True
        and summary.get("next_required_step") == P7_R54_AHR_CS16_STEP_REF
    )
    cs15_blockers = _cs_clean_identifier_list(summary.get("execution_blocker_ids"), limit=40, max_length=240)
    decision_ref, reason_refs, blockers, next_step = _cs16_decision_values(
        cs15_ready=cs15_ready,
        cs15_blockers=cs15_blockers,
        p5_repair_return_required=p5_repair_return_required,
        p4_current_only_repair_required=p4_current_only_repair_required,
        r54_operation_inconclusive=r54_operation_inconclusive,
        operation_blocked_preflight_or_execution=operation_blocked_preflight_or_execution,
        operation_blocked_disposal=operation_blocked_disposal,
        operation_blocked_body_leak_or_question_text=operation_blocked_body_leak_or_question_text,
        operation_blocked_no_touch=operation_blocked_no_touch,
        decision_reason_refs=decision_reason_refs,
    )
    confirmed = cs15_ready and decision_ref == P7_R54_AHR_CS16_DECISION_P5_CONFIRMED_CANDIDATE_REF
    separation_reached = cs15_ready
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS16_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS16_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs16_p5_decision_candidate_separation_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs15_schema_version": summary.get("schema_version"),
        "cs15_material_ref": summary.get("material_id", ""),
        "cs15_next_required_step": summary.get("next_required_step", ""),
        "cs15_post_review_summary_status_ref": summary.get("post_review_summary_status_ref", ""),
        "cs15_actual_review_evidence_complete": summary.get("actual_review_evidence_complete") is True,
        "cs15_p5_decision_candidate_separation_allowed_next": summary.get("p5_decision_candidate_separation_allowed_next") is True,
        "cs15_reviewed_case_count": int(summary.get("reviewed_case_count") or 0),
        "cs15_rating_row_count": int(summary.get("rating_row_count") or 0),
        "cs15_question_observation_row_count": int(summary.get("question_observation_row_count") or 0),
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "p5_decision_candidate_status_ref": decision_ref,
        "p5_decision_candidate_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "cs15_ready_for_p5_decision_candidate_separation": cs15_ready,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(summary.get("reviewed_case_count") or 0) if cs15_ready else 0,
        "rating_row_count": int(summary.get("rating_row_count") or 0) if cs15_ready else 0,
        "question_observation_row_count": int(summary.get("question_observation_row_count") or 0) if cs15_ready else 0,
        "actual_review_evidence_complete": cs15_ready,
        "review_counts_complete": summary.get("review_counts_complete") is True and cs15_ready,
        "rating_counts_complete": summary.get("rating_counts_complete") is True and cs15_ready,
        "question_observation_counts_complete": summary.get("question_observation_counts_complete") is True and cs15_ready,
        "disposal_evidence_complete": summary.get("disposal_evidence_complete") is True and cs15_ready,
        "no_body_leak_validation_passed": summary.get("no_body_leak_validation_passed") is True and cs15_ready,
        "no_question_text_validation_passed": summary.get("no_question_text_validation_passed") is True and cs15_ready,
        "no_touch_validation_passed": summary.get("no_touch_validation_passed") is True and cs15_ready,
        "actual_human_review_operation_run": summary.get("actual_human_review_operation_run") is True and cs15_ready,
        "actual_human_review_executed_by_person": summary.get("actual_human_review_executed_by_person") is True and cs15_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
        "actual_rating_rows_materialized_here": summary.get("actual_rating_rows_materialized_here") is True and cs15_ready,
        "actual_question_need_observation_rows_materialized_here": summary.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and cs15_ready,
        "actual_disposal_receipt_materialized_here": summary.get("actual_disposal_receipt_materialized_here") is True and cs15_ready,
        "disposal_verified": summary.get("disposal_verified") is True and cs15_ready,
        "p5_decision_candidate_separation_reached": separation_reached,
        "p5_decision_candidate_separated_here": separation_reached,
        "p5_confirmed_candidate": confirmed,
        "p5_confirmed_candidate_not_finalized_here": confirmed,
        "p5_repair_return_required": cs15_ready and decision_ref == P7_R54_AHR_CS16_DECISION_P5_REPAIR_RETURN_REQUIRED_REF,
        "p4_current_only_repair_required": cs15_ready and decision_ref == P7_R54_AHR_CS16_DECISION_P4_CURRENT_ONLY_REPAIR_REQUIRED_REF,
        "r54_operation_inconclusive": cs15_ready and decision_ref == P7_R54_AHR_CS16_DECISION_R54_OPERATION_INCONCLUSIVE_REF,
        "r54_operation_blocked": decision_ref in {
            P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION_REF,
            P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF,
            P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
            P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_NO_TOUCH_REF,
        },
        "operation_blocked_by_preflight_or_execution": decision_ref == P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_PREFLIGHT_OR_EXECUTION_REF,
        "operation_blocked_by_disposal": decision_ref == P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_DISPOSAL_REF,
        "operation_blocked_by_body_leak_or_question_text": decision_ref == P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_BODY_LEAK_OR_QUESTION_TEXT_REF,
        "operation_blocked_by_no_touch": decision_ref == P7_R54_AHR_CS16_DECISION_R54_OPERATION_BLOCKED_NO_TOUCH_REF,
        "p6_p8_candidate_only_r52_handoff_allowed_next": confirmed,
        "actual_r52_reintake_execution_confirmed": False,
        "r52_reintake_handoff_ready_here": False,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "implemented_steps": list(P7_R54_AHR_CS16_IMPLEMENTED_STEPS if separation_reached else P7_R54_AHR_CS15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS16_NOT_YET_IMPLEMENTED_STEPS if separation_reached else P7_R54_AHR_CS15_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS16_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS16 P5 decision candidate separation",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS16_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS16_STEP_REF,
        source="P7-R54-AHR-CS16 P5 decision candidate separation",
        allowed_true_refs=P7_R54_AHR_CS16_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs15_schema_version") != P7_R54_AHR_CS15_BODYFREE_POST_REVIEW_SUMMARY_EVIDENCE_COMPLETE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS16 must follow CS15 post-review summary")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS16 P5 decision candidate separation")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS16 P5 decision candidate separation")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS16 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS16 historical basis ref changed")
    if data.get("p5_decision_candidate_status_ref") not in P7_R54_AHR_CS16_ALLOWED_DECISION_REFS:
        raise ValueError("P7-R54-AHR-CS16 decision ref changed")
    blockers = _cs_clean_identifier_list(data.get("execution_blocker_ids"), limit=40, max_length=240)
    if blockers != _cs_clean_identifier_list(data.get("open_execution_blocker_ids"), limit=40, max_length=240):
        raise ValueError("P7-R54-AHR-CS16 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "actual_r52_reintake_execution_confirmed",
        "r52_reintake_handoff_ready_here",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS16 must keep {key}=False")
    cs15_ready = data.get("cs15_ready_for_p5_decision_candidate_separation") is True
    decision_ref = data.get("p5_decision_candidate_status_ref")
    confirmed = decision_ref == P7_R54_AHR_CS16_DECISION_P5_CONFIRMED_CANDIDATE_REF
    if not cs15_ready:
        if data.get("p5_confirmed_candidate") is not False:
            raise ValueError("P7-R54-AHR-CS16 must not create candidate without CS15 complete evidence")
        if data.get("actual_review_evidence_complete") is not False:
            raise ValueError("P7-R54-AHR-CS16 blocked material must not complete evidence")
        if data.get("p6_p8_candidate_only_r52_handoff_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-CS16 blocked material must not allow CS17")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS16 blocked material must carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS15_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS16 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS16 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS16 blocked next step changed")
        return True
    for key in P7_R54_AHR_CS15_EVIDENCE_COMPLETE_REQUIRED_TRUE_FIELD_REFS:
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-CS16 ready path must keep {key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS16_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS16 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS16_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("P7-R54-AHR-CS16 not-yet steps changed")
    if confirmed:
        if blockers:
            raise ValueError("P7-R54-AHR-CS16 confirmed candidate must not carry blockers")
        if data.get("p5_confirmed_candidate") is not True or data.get("p5_confirmed_candidate_not_finalized_here") is not True:
            raise ValueError("P7-R54-AHR-CS16 confirmed candidate flags changed")
        if data.get("p6_p8_candidate_only_r52_handoff_allowed_next") is not True:
            raise ValueError("P7-R54-AHR-CS16 confirmed candidate must allow CS17")
        if data.get("next_required_step") != P7_R54_AHR_CS17_STEP_REF:
            raise ValueError("P7-R54-AHR-CS16 confirmed candidate next step changed")
    else:
        if data.get("p5_confirmed_candidate") is not False:
            raise ValueError("P7-R54-AHR-CS16 non-confirmed material must not create candidate")
        if data.get("p6_p8_candidate_only_r52_handoff_allowed_next") is not False:
            raise ValueError("P7-R54-AHR-CS16 non-confirmed material must not allow CS17")
        if data.get("next_required_step") == P7_R54_AHR_CS17_STEP_REF:
            raise ValueError("P7-R54-AHR-CS16 non-confirmed material must not point to CS17")
    return True


def build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope(
    *,
    p5_decision_candidate_separation: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
    p8_material_candidate_refs: Sequence[Any] | None = P7_R54_AHR_CS17_DEFAULT_P8_MATERIAL_CANDIDATE_REFS,
    r52_reintake_handoff_ref: Any = P7_R54_AHR_CS17_R52_HANDOFF_REF_DEFAULT,
) -> dict[str, Any]:
    """Build candidate-only P6/P8 and R52 handoff envelope without execution."""

    cs16 = dict(
        p5_decision_candidate_separation
        or build_p7_r54_ahr_cs16_p5_decision_candidate_separation()
    )
    session_id = _safe_review_session_id(review_session_id)
    candidate_ready = (
        cs16.get("p5_decision_candidate_status_ref") == P7_R54_AHR_CS16_DECISION_P5_CONFIRMED_CANDIDATE_REF
        and cs16.get("p5_confirmed_candidate") is True
        and cs16.get("p6_p8_candidate_only_r52_handoff_allowed_next") is True
        and cs16.get("actual_review_evidence_complete") is True
        and cs16.get("next_required_step") == P7_R54_AHR_CS17_STEP_REF
    )
    p8_refs = _cs_clean_identifier_list(p8_material_candidate_refs, limit=24, max_length=180) if candidate_ready else []
    handoff_ref = clean_identifier(r52_reintake_handoff_ref, default=P7_R54_AHR_CS17_R52_HANDOFF_REF_DEFAULT, max_length=180)
    blockers = [] if candidate_ready else _cs_clean_identifier_list(
        ["cs16_p5_confirmed_candidate_not_ready_for_candidate_only_handoff", *(cs16.get("execution_blocker_ids") or [])],
        limit=40,
        max_length=240,
    )
    status_ref = P7_R54_AHR_CS17_READY_STATUS_REF if candidate_ready else P7_R54_AHR_CS17_BLOCKED_STATUS_REF
    reason_refs = [P7_R54_AHR_CS17_READY_REASON_REF] if candidate_ready else blockers
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS17_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS17_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs16_schema_version": cs16.get("schema_version"),
        "cs16_material_ref": cs16.get("material_id", ""),
        "cs16_next_required_step": cs16.get("next_required_step", ""),
        "cs16_p5_decision_candidate_status_ref": cs16.get("p5_decision_candidate_status_ref", ""),
        "cs16_p5_confirmed_candidate": cs16.get("p5_confirmed_candidate") is True,
        "cs16_actual_review_evidence_complete": cs16.get("actual_review_evidence_complete") is True,
        "cs16_p6_p8_candidate_only_r52_handoff_allowed_next": cs16.get("p6_p8_candidate_only_r52_handoff_allowed_next") is True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "candidate_handoff_status_ref": status_ref,
        "candidate_handoff_reason_refs": reason_refs,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(cs16.get("reviewed_case_count") or 0) if candidate_ready else 0,
        "rating_row_count": int(cs16.get("rating_row_count") or 0) if candidate_ready else 0,
        "question_observation_row_count": int(cs16.get("question_observation_row_count") or 0) if candidate_ready else 0,
        "actual_review_evidence_complete": candidate_ready,
        "review_counts_complete": cs16.get("review_counts_complete") is True and candidate_ready,
        "rating_counts_complete": cs16.get("rating_counts_complete") is True and candidate_ready,
        "question_observation_counts_complete": cs16.get("question_observation_counts_complete") is True and candidate_ready,
        "disposal_evidence_complete": cs16.get("disposal_evidence_complete") is True and candidate_ready,
        "no_body_leak_validation_passed": cs16.get("no_body_leak_validation_passed") is True and candidate_ready,
        "no_question_text_validation_passed": cs16.get("no_question_text_validation_passed") is True and candidate_ready,
        "no_touch_validation_passed": cs16.get("no_touch_validation_passed") is True and candidate_ready,
        "actual_human_review_operation_run": cs16.get("actual_human_review_operation_run") is True and candidate_ready,
        "actual_human_review_executed_by_person": cs16.get("actual_human_review_executed_by_person") is True and candidate_ready,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
        "actual_rating_rows_materialized_here": cs16.get("actual_rating_rows_materialized_here") is True and candidate_ready,
        "actual_question_need_observation_rows_materialized_here": cs16.get(
            "actual_question_need_observation_rows_materialized_here"
        ) is True and candidate_ready,
        "actual_disposal_receipt_materialized_here": cs16.get("actual_disposal_receipt_materialized_here") is True and candidate_ready,
        "disposal_verified": cs16.get("disposal_verified") is True and candidate_ready,
        "p5_confirmed_candidate": candidate_ready,
        "p5_confirmed_candidate_not_finalized_here": candidate_ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_candidate_only_handoff_built": candidate_ready,
        "p6_limited_human_readfeel_start_allowed_candidate": candidate_ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_material_candidate_only_handoff_built": candidate_ready,
        "p8_question_design_material_candidate": candidate_ready and bool(p8_refs),
        "p8_material_candidate_refs": p8_refs,
        "p8_material_candidate_ref_count": len(p8_refs),
        "p8_material_candidate_source_ref": "actual_review_question_need_observation_rows_bodyfree" if candidate_ready else "",
        "p8_material_candidate_source_observation_row_count": int(cs16.get("question_observation_row_count") or 0) if candidate_ready else 0,
        "p8_material_candidate_allowed_class_refs": list(P7_R54_AHR_CS17_ALLOWED_P8_MATERIAL_CANDIDATE_CLASS_REFS),
        "p8_material_candidate_classes_are_allowed": all(
            candidate_ref in P7_R54_AHR_CS17_ALLOWED_P8_MATERIAL_CANDIDATE_CLASS_REFS for candidate_ref in p8_refs
        ),
        "p8_material_candidate_question_text_included": False,
        "p8_material_candidate_draft_question_text_included": False,
        "p8_material_candidate_question_answer_persistence_started": False,
        "p8_material_candidate_excludes_p5_repair_required_cases": candidate_ready,
        "p8_material_candidate_excludes_p4_current_only_repair_required_cases": candidate_ready,
        "p8_material_candidate_excludes_execution_blocker_cases": candidate_ready,
        "p8_start_allowed": False,
        "r52_reintake_handoff_envelope_built": candidate_ready,
        "r52_reintake_handoff_ref": handoff_ref if candidate_ready else "",
        "r52_reintake_handoff_ready": candidate_ready,
        "r52_reintake_handoff_ready_here": candidate_ready,
        "actual_r52_reintake_execution_confirmed": False,
        "r52_reintake_execution_requested_here": False,
        "r52_reintake_claim_blocked_here": True,
        "p6_p8_release_promotion_blocked_here": True,
        "p5_finalization_blocked_here": True,
        "p7_complete": False,
        "release_allowed": False,
        "implemented_steps": list(P7_R54_AHR_CS17_IMPLEMENTED_STEPS if candidate_ready else P7_R54_AHR_CS16_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS17_NOT_YET_IMPLEMENTED_STEPS if candidate_ready else P7_R54_AHR_CS16_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS18_STEP_REF if candidate_ready else P7_R54_AHR_CS17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS17_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS17 P6/P8 candidate-only R52 handoff envelope",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS17_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS17_STEP_REF,
        source="P7-R54-AHR-CS17 P6/P8 candidate-only R52 handoff envelope",
        allowed_true_refs=P7_R54_AHR_CS17_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs16_schema_version") != P7_R54_AHR_CS16_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS17 must follow CS16 P5 decision candidate separation")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS17 candidate handoff")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS17 candidate handoff")
    if data.get("current_basis_ref") != P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS17 current basis ref changed")
    if data.get("historical_basis_ref") != P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF:
        raise ValueError("P7-R54-AHR-CS17 historical basis ref changed")
    if data.get("candidate_handoff_status_ref") not in P7_R54_AHR_CS17_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS17 status changed")
    blockers = _cs_clean_identifier_list(data.get("execution_blocker_ids"), limit=40, max_length=240)
    if blockers != _cs_clean_identifier_list(data.get("open_execution_blocker_ids"), limit=40, max_length=240):
        raise ValueError("P7-R54-AHR-CS17 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_start_allowed",
        "actual_r52_reintake_execution_confirmed",
        "r52_reintake_execution_requested_here",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS17 must keep {key}=False")
    if data.get("p8_material_candidate_question_text_included") is not False:
        raise ValueError("P7-R54-AHR-CS17 must not include P8 question text")
    if data.get("p8_material_candidate_draft_question_text_included") is not False:
        raise ValueError("P7-R54-AHR-CS17 must not include P8 draft question text")
    if data.get("p8_material_candidate_question_answer_persistence_started") is not False:
        raise ValueError("P7-R54-AHR-CS17 must not start question answer persistence")
    ready = data.get("candidate_handoff_status_ref") == P7_R54_AHR_CS17_READY_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS17 ready material must not carry blockers")
        for key in P7_R54_AHR_CS15_EVIDENCE_COMPLETE_REQUIRED_TRUE_FIELD_REFS:
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS17 ready material must keep {key}=True")
        for key in (
            "p5_confirmed_candidate",
            "p5_confirmed_candidate_not_finalized_here",
            "p6_candidate_only_handoff_built",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_material_candidate_only_handoff_built",
            "r52_reintake_handoff_envelope_built",
            "r52_reintake_handoff_ready",
            "r52_reintake_handoff_ready_here",
            "p8_material_candidate_excludes_p5_repair_required_cases",
            "p8_material_candidate_excludes_p4_current_only_repair_required_cases",
            "p8_material_candidate_excludes_execution_blocker_cases",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS17 ready material must keep {key}=True")
        if data.get("r52_reintake_handoff_ref") != P7_R54_AHR_CS17_R52_HANDOFF_REF_DEFAULT:
            raise ValueError("P7-R54-AHR-CS17 handoff ref changed")
        if data.get("p8_material_candidate_ref_count") != len(data.get("p8_material_candidate_refs") or []):
            raise ValueError("P7-R54-AHR-CS17 P8 candidate ref count changed")
        if data.get("p8_material_candidate_classes_are_allowed") is not True:
            raise ValueError("P7-R54-AHR-CS17 P8 candidate classes must be allowed")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS17 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS18_STEP_REF:
            raise ValueError("P7-R54-AHR-CS17 next step changed")
    else:
        if data.get("r52_reintake_handoff_ready") is not False or data.get("r52_reintake_handoff_ready_here") is not False:
            raise ValueError("P7-R54-AHR-CS17 blocked material must not create R52 handoff ready")
        if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False:
            raise ValueError("P7-R54-AHR-CS17 blocked material must not create P6 candidate")
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("P7-R54-AHR-CS17 blocked material must not create P8 candidate")
        if not blockers:
            raise ValueError("P7-R54-AHR-CS17 blocked material must carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS16_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS17 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS17 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS17 blocked next step changed")
    return True




# ---------------------------------------------------------------------------
# CS18 final validation / command matrix / documentation output.
# ---------------------------------------------------------------------------

P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r54.ahr.current_snapshot_reentry.cs18_final_validation_command_matrix_documentation_output.bodyfree.v1"
)
P7_R54_AHR_CS18_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATION_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
)
P7_R54_AHR_CS18_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION: Final = (
    P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION
)
P7_R54_AHR_CS18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS17_IMPLEMENTED_STEPS,
    P7_R54_AHR_CS18_STEP_REF,
)
P7_R54_AHR_CS18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()
P7_R54_AHR_CS18_READY_STATUS_REF: Final = "CURRENT_SNAPSHOT_REENTRY_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_READY"
P7_R54_AHR_CS18_BLOCKED_STATUS_REF: Final = "CURRENT_SNAPSHOT_REENTRY_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_BLOCKED"
P7_R54_AHR_CS18_ALLOWED_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS18_READY_STATUS_REF,
    P7_R54_AHR_CS18_BLOCKED_STATUS_REF,
)
P7_R54_AHR_CS18_READY_REASON_REF: Final = "r54_ahr_cs18_final_validation_documented_bodyfree_without_auto_promotion"
P7_R54_AHR_CS18_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "R54-AHR-CS18_wait_for_ready_CS17_candidate_handoff"
P7_R54_AHR_CS18_READY_NEXT_REQUIRED_STEP_REF: Final = "R54-AHR-CS18_documented_manual_decision_required_without_auto_promotion"
P7_R54_AHR_CS18_DOCUMENTATION_OUTPUT_REF_DEFAULT: Final = "R54_AHR_CS18_BODYFREE_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REF"

P7_R54_AHR_CS18_COMMAND_STATUS_PASSED_REF: Final = "PASSED"
P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF: Final = "NOT_EXECUTED"
P7_R54_AHR_CS18_COMMAND_STATUS_FAILED_REF: Final = "FAILED"
P7_R54_AHR_CS18_COMMAND_STATUS_TIMEOUT_REF: Final = "TIMEOUT"
P7_R54_AHR_CS18_COMMAND_STATUS_KILLED_REF: Final = "KILLED"
P7_R54_AHR_CS18_COMMAND_STATUS_INTERRUPTED_REF: Final = "INTERRUPTED"
P7_R54_AHR_CS18_ALLOWED_COMMAND_STATUS_REFS: Final[tuple[str, ...]] = (
    P7_R54_AHR_CS18_COMMAND_STATUS_PASSED_REF,
    P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF,
    P7_R54_AHR_CS18_COMMAND_STATUS_FAILED_REF,
    P7_R54_AHR_CS18_COMMAND_STATUS_TIMEOUT_REF,
    P7_R54_AHR_CS18_COMMAND_STATUS_KILLED_REF,
    P7_R54_AHR_CS18_COMMAND_STATUS_INTERRUPTED_REF,
)
P7_R54_AHR_CS18_COMMAND_REFS: Final[tuple[str, ...]] = (
    "compileall_services_ai_inference_tests",
    "target_r54_ahr_cs00_cs18_split",
    "selected_existing_ahr_regression",
    "selected_r55_regression",
    "selected_r52_regression",
    "full_backend_suite",
    "rn_contract",
    "rn_real_device_modal",
)
P7_R54_AHR_CS18_COMMAND_GREEN_EVIDENCE_ACCEPTABLE_REFS: Final[tuple[str, ...]] = (
    "compileall_services_ai_inference_tests",
    "target_r54_ahr_cs00_cs18_split",
    "selected_existing_ahr_regression",
    "selected_r55_regression",
    "selected_r52_regression",
)
P7_R54_AHR_CS18_COMMAND_NOT_FULL_SCOPE_REFS: Final[tuple[str, ...]] = (
    "full_backend_suite",
    "rn_contract",
    "rn_real_device_modal",
)
P7_R54_AHR_CS18_CLAIM_BOUNDARY_REFS: Final[tuple[str, ...]] = (
    "CS_helper_green_is_not_actual_human_review_complete",
    "existing_AHR_helper_green_is_not_current_actual_review_complete",
    "selected_regression_green_is_not_full_backend_suite_green",
    "RN_contract_green_is_not_RN_real_device_modal_verified",
    "R52_handoff_ready_is_not_R52_reintake_executed",
    "P8_material_candidate_only_is_not_P8_start_allowed",
    "P5_confirmed_candidate_is_not_P5_final",
)
P7_R54_AHR_CS18_ALLOWED_TRUE_FALSE_FLAG_REFS: Final[tuple[str, ...]] = P7_R54_AHR_CS17_ALLOWED_TRUE_FALSE_FLAG_REFS
P7_R54_AHR_CS18_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "command_ref",
    "command_status_ref",
    "command_executed",
    "command_passed",
    "command_failed",
    "command_timeout",
    "command_killed",
    "command_interrupted",
    "command_green_evidence_accepted",
    "command_green_evidence_scope_ref",
    "command_output_body_included",
    "stdout_body_included",
    "stderr_body_included",
    "traceback_body_included",
    "terminal_output_body_included",
    "local_absolute_path_included",
    "body_hash_included",
    "body_free",
)
P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    *P7_R54_AHR_CS_BASE_REQUIRED_FIELD_REFS,
    "cs17_schema_version",
    "cs17_material_ref",
    "cs17_next_required_step",
    "cs17_candidate_handoff_status_ref",
    "cs17_r52_reintake_handoff_ready",
    "cs17_actual_review_evidence_complete",
    "cs17_p5_confirmed_candidate",
    *P7_R54_AHR_CS_CURRENT_SNAPSHOT_FIELD_REFS,
    *P7_R54_AHR_CS_EXISTING_AHR_FIELD_REFS,
    "current_basis_ref",
    "historical_basis_ref",
    "final_validation_status_ref",
    "final_validation_reason_refs",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "candidate_handoff_ready_for_final_validation",
    "required_case_count",
    "reviewed_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "actual_review_evidence_complete",
    "review_counts_complete",
    "rating_counts_complete",
    "question_observation_counts_complete",
    "disposal_evidence_complete",
    "no_body_leak_validation_passed",
    "no_question_text_validation_passed",
    "no_touch_validation_passed",
    "final_no_body_leak_validation_passed",
    "final_no_question_text_validation_passed",
    "final_no_touch_validation_passed",
    "actual_human_review_operation_run",
    "actual_human_review_executed_by_person",
    "actual_human_review_run_here",
    "actual_human_review_complete",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "disposal_verified",
    "p5_confirmed_candidate",
    "p5_confirmed_candidate_not_finalized_here",
    "p5_human_blind_qa_confirmed_final",
    "p5_confirmed_final",
    "p5_final_allowed",
    "p6_candidate_only_handoff_built",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_start_allowed",
    "p8_material_candidate_only_handoff_built",
    "p8_question_design_material_candidate",
    "p8_material_candidate_refs",
    "p8_material_candidate_ref_count",
    "p8_material_candidate_question_text_included",
    "p8_material_candidate_draft_question_text_included",
    "p8_material_candidate_question_answer_persistence_started",
    "p8_start_allowed",
    "r52_reintake_handoff_envelope_built",
    "r52_reintake_handoff_ref",
    "r52_reintake_handoff_ready",
    "r52_reintake_handoff_ready_here",
    "r52_reintake_execution_requested_here",
    "actual_r52_reintake_execution_confirmed",
    "p7_complete",
    "release_allowed",
    "command_matrix_rows",
    "command_matrix_row_count",
    "command_matrix_command_refs",
    "command_matrix_allowed_status_refs",
    "command_matrix_passed_refs",
    "command_matrix_green_evidence_accepted_refs",
    "command_matrix_not_executed_refs",
    "command_matrix_failed_refs",
    "command_matrix_timeout_killed_interrupted_refs",
    "command_matrix_output_body_included_refs",
    "command_matrix_bodyfree_only",
    "command_matrix_no_unexecuted_passed_claim",
    "command_matrix_no_timeout_kill_interrupted_green_claim",
    "command_matrix_no_output_body_included",
    "full_backend_suite_green_confirmed",
    "rn_contract_green_confirmed",
    "rn_real_device_modal_verified",
    "selected_regression_green_not_full_backend_suite_green",
    "rn_contract_green_not_real_device_modal_verified",
    "claim_boundary_refs",
    "claim_boundary_ref_count",
    "documentation_output_ref",
    "documentation_output_bodyfree_only",
    "documentation_output_ready",
    "documentation_output_claims_no_auto_promotion",
    "implemented_steps",
    "not_yet_implemented_steps",
    "next_required_step",
    *P7_R54_AHR_CS_NO_TOUCH_MATERIAL_FIELD_REFS,
    *P7_R54_AHR_CS_FALSE_FLAG_REFS,
)
P7_R54_AHR_CS18_FINAL_VALIDATION_REQUIRED_FIELD_REFS: Final = P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS
P7_R54_AHR_CS18_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final = P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS
P7_R54_AHR_CS18_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS: Final = P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS


def _cs18_normalize_command_status(value: Any) -> tuple[str, bool]:
    explicit_executed: Any = None
    if isinstance(value, Mapping):
        raw_status = value.get("command_status_ref") or value.get("status_ref") or value.get("status")
        explicit_executed = value.get("command_executed", value.get("executed", None))
        if raw_status is None:
            if value.get("command_killed") is True or value.get("killed") is True:
                raw_status = P7_R54_AHR_CS18_COMMAND_STATUS_KILLED_REF
            elif value.get("command_timeout") is True or value.get("timeout") is True:
                raw_status = P7_R54_AHR_CS18_COMMAND_STATUS_TIMEOUT_REF
            elif value.get("command_interrupted") is True or value.get("interrupted") is True:
                raw_status = P7_R54_AHR_CS18_COMMAND_STATUS_INTERRUPTED_REF
            elif value.get("command_failed") is True or value.get("failed") is True:
                raw_status = P7_R54_AHR_CS18_COMMAND_STATUS_FAILED_REF
            elif value.get("command_passed") is True or value.get("passed") is True:
                raw_status = P7_R54_AHR_CS18_COMMAND_STATUS_PASSED_REF
            else:
                raw_status = P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF
    else:
        raw_status = value
    normalized = clean_identifier(raw_status, default=P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF, max_length=120)
    lower = normalized.lower()
    if lower in {"passed", "pass", "green", "ok", P7_R54_AHR_CS18_COMMAND_STATUS_PASSED_REF.lower()}:
        status_ref = P7_R54_AHR_CS18_COMMAND_STATUS_PASSED_REF
    elif lower in {"timeout", "timed_out", P7_R54_AHR_CS18_COMMAND_STATUS_TIMEOUT_REF.lower()}:
        status_ref = P7_R54_AHR_CS18_COMMAND_STATUS_TIMEOUT_REF
    elif lower in {"killed", "kill", P7_R54_AHR_CS18_COMMAND_STATUS_KILLED_REF.lower()}:
        status_ref = P7_R54_AHR_CS18_COMMAND_STATUS_KILLED_REF
    elif lower in {"interrupted", "cancelled", "canceled", P7_R54_AHR_CS18_COMMAND_STATUS_INTERRUPTED_REF.lower()}:
        status_ref = P7_R54_AHR_CS18_COMMAND_STATUS_INTERRUPTED_REF
    elif lower in {"failed", "fail", "error", P7_R54_AHR_CS18_COMMAND_STATUS_FAILED_REF.lower()}:
        status_ref = P7_R54_AHR_CS18_COMMAND_STATUS_FAILED_REF
    elif lower in {"not_executed", "not_run", "skipped", "unconfirmed", P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF.lower()}:
        status_ref = P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF
    else:
        status_ref = P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF
    executed = bool(explicit_executed) if explicit_executed is not None else status_ref != P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF
    return status_ref, executed


def _cs18_command_matrix_rows(command_results: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    results = command_results or {}
    rows: list[dict[str, Any]] = []
    for command_ref in P7_R54_AHR_CS18_COMMAND_REFS:
        status_ref, executed = _cs18_normalize_command_status(results.get(command_ref))
        passed = status_ref == P7_R54_AHR_CS18_COMMAND_STATUS_PASSED_REF
        failed = status_ref == P7_R54_AHR_CS18_COMMAND_STATUS_FAILED_REF
        timeout = status_ref == P7_R54_AHR_CS18_COMMAND_STATUS_TIMEOUT_REF
        killed = status_ref == P7_R54_AHR_CS18_COMMAND_STATUS_KILLED_REF
        interrupted = status_ref == P7_R54_AHR_CS18_COMMAND_STATUS_INTERRUPTED_REF
        green = command_ref in P7_R54_AHR_CS18_COMMAND_GREEN_EVIDENCE_ACCEPTABLE_REFS and executed and passed and not (failed or timeout or killed or interrupted)
        rows.append(
            {
                "command_ref": command_ref,
                "command_status_ref": status_ref,
                "command_executed": executed,
                "command_passed": passed,
                "command_failed": failed,
                "command_timeout": timeout,
                "command_killed": killed,
                "command_interrupted": interrupted,
                "command_green_evidence_accepted": green,
                "command_green_evidence_scope_ref": "selected_or_target_command_green_evidence" if green else "not_green_evidence_for_current_claim_boundary",
                "command_output_body_included": False,
                "stdout_body_included": False,
                "stderr_body_included": False,
                "traceback_body_included": False,
                "terminal_output_body_included": False,
                "local_absolute_path_included": False,
                "body_hash_included": False,
                "body_free": True,
            }
        )
    return rows


def _cs18_refs_with(rows: Sequence[Mapping[str, Any]], key: str) -> list[str]:
    return [str(row.get("command_ref")) for row in rows if row.get(key) is True]


def build_p7_r54_ahr_cs18_validation_command_matrix_documentation_output(
    *,
    candidate_handoff_envelope: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R54_AHR_CS_DEFAULT_REVIEW_SESSION_ID,
    command_result_rows: Mapping[str, Any] | None = None,
    command_execution_results: Mapping[str, Any] | None = None,
    documentation_output_ref: Any = P7_R54_AHR_CS18_DOCUMENTATION_OUTPUT_REF_DEFAULT,
) -> dict[str, Any]:
    """Build CS18 final validation, command matrix, and documentation output."""

    cs17 = dict(candidate_handoff_envelope or build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope())
    session_id = _safe_review_session_id(review_session_id or cs17.get("review_session_id"))
    command_results = command_execution_results if command_execution_results is not None else command_result_rows
    rows = _cs18_command_matrix_rows(command_results)
    passed_refs = _cs18_refs_with(rows, "command_passed")
    green_refs = _cs18_refs_with(rows, "command_green_evidence_accepted")
    not_executed_refs = [row["command_ref"] for row in rows if row["command_status_ref"] == P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF]
    failed_refs = _cs18_refs_with(rows, "command_failed")
    bad_runtime_refs = [row["command_ref"] for row in rows if row["command_timeout"] is True or row["command_killed"] is True or row["command_interrupted"] is True]
    output_body_refs = [
        row["command_ref"]
        for row in rows
        if row["command_output_body_included"] is True
        or row["stdout_body_included"] is True
        or row["stderr_body_included"] is True
        or row["traceback_body_included"] is True
        or row["terminal_output_body_included"] is True
        or row["local_absolute_path_included"] is True
        or row["body_hash_included"] is True
        or row["body_free"] is not True
    ]
    unexecuted_passed = [row["command_ref"] for row in rows if row["command_passed"] is True and row["command_executed"] is not True]
    timeout_green = [row["command_ref"] for row in rows if row["command_green_evidence_accepted"] is True and (row["command_timeout"] or row["command_killed"] or row["command_interrupted"])]
    candidate_ready = (
        cs17.get("schema_version") == P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_SCHEMA_VERSION
        and cs17.get("candidate_handoff_status_ref") == P7_R54_AHR_CS17_READY_STATUS_REF
        and cs17.get("r52_reintake_handoff_ready") is True
        and cs17.get("actual_review_evidence_complete") is True
        and cs17.get("next_required_step") == P7_R54_AHR_CS18_STEP_REF
    )
    missing_required_green_refs = [
        command_ref
        for command_ref in P7_R54_AHR_CS18_COMMAND_GREEN_EVIDENCE_ACCEPTABLE_REFS
        if command_ref not in green_refs
    ]
    command_matrix_ok = (
        not unexecuted_passed
        and not timeout_green
        and not output_body_refs
        and not failed_refs
        and not bad_runtime_refs
        and not missing_required_green_refs
    )
    blockers = [] if candidate_ready and command_matrix_ok else _cs_clean_identifier_list(
        [
            *(cs17.get("execution_blocker_ids") or []),
            *( ["cs17_candidate_handoff_not_ready_for_final_validation_documentation"] if not candidate_ready else [] ),
            *( ["command_matrix_contains_unexecuted_passed_claim"] if unexecuted_passed else [] ),
            *( ["command_matrix_contains_timeout_killed_interrupted_green_claim"] if timeout_green else [] ),
            *( ["command_matrix_has_failed_refs"] if failed_refs else [] ),
            *( ["command_matrix_has_timeout_killed_or_interrupted_refs"] if bad_runtime_refs else [] ),
            *( ["command_matrix_missing_required_green_evidence_refs"] if missing_required_green_refs else [] ),
            *( ["command_matrix_contains_output_body_or_path_hash"] if output_body_refs else [] ),
        ],
        limit=60,
        max_length=240,
    )
    ready = candidate_ready and command_matrix_ok
    status_ref = P7_R54_AHR_CS18_READY_STATUS_REF if ready else P7_R54_AHR_CS18_BLOCKED_STATUS_REF
    material: dict[str, Any] = {
        "schema_version": P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R54_AHR_CS_STEP,
        "scope": P7_R54_AHR_CS_SCOPE,
        "policy_kind": P7_R54_AHR_CS_POLICY_KIND,
        "policy_section": P7_R54_AHR_CS18_STEP_REF,
        "operation_step_ref": P7_R54_AHR_CS18_STEP_REF,
        "current_phase": P7_R54_AHR_CS_CURRENT_PHASE,
        "material_id": "p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_20260628",
        "review_session_id": session_id,
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "cs17_schema_version": cs17.get("schema_version", ""),
        "cs17_material_ref": cs17.get("material_id", ""),
        "cs17_next_required_step": cs17.get("next_required_step", ""),
        "cs17_candidate_handoff_status_ref": cs17.get("candidate_handoff_status_ref", ""),
        "cs17_r52_reintake_handoff_ready": cs17.get("r52_reintake_handoff_ready") is True,
        "cs17_actual_review_evidence_complete": cs17.get("actual_review_evidence_complete") is True,
        "cs17_p5_confirmed_candidate": cs17.get("p5_confirmed_candidate") is True,
        **_snapshot_fields(actual_basis=True),
        **_existing_ahr_fields(),
        "current_basis_ref": P7_R54_AHR_CS_ACTUAL_REVIEW_BASIS_REF,
        "historical_basis_ref": P7_R54_AHR_CS_EXISTING_AHR_BASIS_REF,
        "final_validation_status_ref": status_ref,
        "final_validation_reason_refs": [P7_R54_AHR_CS18_READY_REASON_REF] if ready else blockers,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "candidate_handoff_ready_for_final_validation": candidate_ready,
        "required_case_count": P7_R54_AHR_CS_REQUIRED_ACTUAL_REVIEW_CASE_COUNT,
        "reviewed_case_count": int(cs17.get("reviewed_case_count") or 0) if ready else 0,
        "rating_row_count": int(cs17.get("rating_row_count") or 0) if ready else 0,
        "question_observation_row_count": int(cs17.get("question_observation_row_count") or 0) if ready else 0,
        "actual_review_evidence_complete": cs17.get("actual_review_evidence_complete") is True and ready,
        "review_counts_complete": cs17.get("review_counts_complete") is True and ready,
        "rating_counts_complete": cs17.get("rating_counts_complete") is True and ready,
        "question_observation_counts_complete": cs17.get("question_observation_counts_complete") is True and ready,
        "disposal_evidence_complete": cs17.get("disposal_evidence_complete") is True and ready,
        "no_body_leak_validation_passed": cs17.get("no_body_leak_validation_passed") is True and ready,
        "no_question_text_validation_passed": cs17.get("no_question_text_validation_passed") is True and ready,
        "no_touch_validation_passed": cs17.get("no_touch_validation_passed") is True and ready,
        "final_no_body_leak_validation_passed": cs17.get("no_body_leak_validation_passed") is True and ready,
        "final_no_question_text_validation_passed": cs17.get("no_question_text_validation_passed") is True and ready,
        "final_no_touch_validation_passed": cs17.get("no_touch_validation_passed") is True and ready,
        "actual_human_review_operation_run": cs17.get("actual_human_review_operation_run") is True and ready,
        "actual_human_review_executed_by_person": cs17.get("actual_human_review_executed_by_person") is True and ready,
        "actual_human_review_run_here": False,
        "actual_human_review_complete": False,
        "actual_rating_rows_materialized_here": cs17.get("actual_rating_rows_materialized_here") is True and ready,
        "actual_question_need_observation_rows_materialized_here": cs17.get("actual_question_need_observation_rows_materialized_here") is True and ready,
        "actual_disposal_receipt_materialized_here": cs17.get("actual_disposal_receipt_materialized_here") is True and ready,
        "disposal_verified": cs17.get("disposal_verified") is True and ready,
        "p5_confirmed_candidate": cs17.get("p5_confirmed_candidate") is True and ready,
        "p5_confirmed_candidate_not_finalized_here": cs17.get("p5_confirmed_candidate_not_finalized_here") is True and ready,
        "p5_human_blind_qa_confirmed_final": False,
        "p5_confirmed_final": False,
        "p5_final_allowed": False,
        "p6_candidate_only_handoff_built": cs17.get("p6_candidate_only_handoff_built") is True and ready,
        "p6_limited_human_readfeel_start_allowed_candidate": cs17.get("p6_limited_human_readfeel_start_allowed_candidate") is True and ready,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_start_allowed": False,
        "p8_material_candidate_only_handoff_built": cs17.get("p8_material_candidate_only_handoff_built") is True and ready,
        "p8_question_design_material_candidate": cs17.get("p8_question_design_material_candidate") is True and ready,
        "p8_material_candidate_refs": list(cs17.get("p8_material_candidate_refs") or []) if ready else [],
        "p8_material_candidate_ref_count": int(cs17.get("p8_material_candidate_ref_count") or 0) if ready else 0,
        "p8_material_candidate_question_text_included": False,
        "p8_material_candidate_draft_question_text_included": False,
        "p8_material_candidate_question_answer_persistence_started": False,
        "p8_start_allowed": False,
        "r52_reintake_handoff_envelope_built": cs17.get("r52_reintake_handoff_envelope_built") is True and ready,
        "r52_reintake_handoff_ref": cs17.get("r52_reintake_handoff_ref", "") if ready else "",
        "r52_reintake_handoff_ready": cs17.get("r52_reintake_handoff_ready") is True and ready,
        "r52_reintake_handoff_ready_here": cs17.get("r52_reintake_handoff_ready_here") is True and ready,
        "r52_reintake_execution_requested_here": False,
        "actual_r52_reintake_execution_confirmed": False,
        "p7_complete": False,
        "release_allowed": False,
        "command_matrix_rows": rows,
        "command_matrix_row_count": len(rows),
        "command_matrix_command_refs": list(P7_R54_AHR_CS18_COMMAND_REFS),
        "command_matrix_allowed_status_refs": list(P7_R54_AHR_CS18_ALLOWED_COMMAND_STATUS_REFS),
        "command_matrix_passed_refs": passed_refs,
        "command_matrix_green_evidence_accepted_refs": green_refs,
        "command_matrix_not_executed_refs": not_executed_refs,
        "command_matrix_failed_refs": failed_refs,
        "command_matrix_timeout_killed_interrupted_refs": bad_runtime_refs,
        "command_matrix_output_body_included_refs": output_body_refs,
        "command_matrix_bodyfree_only": not output_body_refs,
        "command_matrix_no_unexecuted_passed_claim": not unexecuted_passed,
        "command_matrix_no_timeout_kill_interrupted_green_claim": not timeout_green,
        "command_matrix_no_output_body_included": not output_body_refs,
        "full_backend_suite_green_confirmed": False,
        "rn_contract_green_confirmed": False,
        "rn_real_device_modal_verified": False,
        "selected_regression_green_not_full_backend_suite_green": True,
        "rn_contract_green_not_real_device_modal_verified": True,
        "claim_boundary_refs": list(P7_R54_AHR_CS18_CLAIM_BOUNDARY_REFS),
        "claim_boundary_ref_count": len(P7_R54_AHR_CS18_CLAIM_BOUNDARY_REFS),
        "documentation_output_ref": clean_identifier(documentation_output_ref, default=P7_R54_AHR_CS18_DOCUMENTATION_OUTPUT_REF_DEFAULT, max_length=180),
        "documentation_output_bodyfree_only": ready,
        "documentation_output_ready": ready,
        "documentation_output_claims_no_auto_promotion": True,
        "implemented_steps": list(P7_R54_AHR_CS18_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS17_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R54_AHR_CS18_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R54_AHR_CS17_NOT_YET_IMPLEMENTED_STEPS),
        "next_required_step": P7_R54_AHR_CS18_READY_NEXT_REQUIRED_STEP_REF if ready else P7_R54_AHR_CS18_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r54_ahr_cs_no_touch_contract": _no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    _add_false_flags_preserving_allowed(material, allowed_true_refs=P7_R54_AHR_CS18_ALLOWED_TRUE_FALSE_FLAG_REFS)
    return material


def assert_p7_r54_ahr_cs18_validation_command_matrix_documentation_output_contract(data: Mapping[str, Any]) -> bool:
    _assert_required_fields(
        data,
        required=P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_REQUIRED_FIELD_REFS,
        source="P7-R54-AHR-CS18 final validation command matrix documentation output",
    )
    _cs_assert_bodyfree_no_touch_base_allowing_true_flags(
        data,
        schema_version=P7_R54_AHR_CS18_FINAL_VALIDATION_COMMAND_MATRIX_DOCUMENTATION_OUTPUT_SCHEMA_VERSION,
        policy_section=P7_R54_AHR_CS18_STEP_REF,
        operation_step_ref=P7_R54_AHR_CS18_STEP_REF,
        source="P7-R54-AHR-CS18 final validation command matrix documentation output",
        allowed_true_refs=P7_R54_AHR_CS18_ALLOWED_TRUE_FALSE_FLAG_REFS,
    )
    if data.get("cs17_schema_version") != P7_R54_AHR_CS17_P6_P8_CANDIDATE_ONLY_R52_HANDOFF_ENVELOPE_SCHEMA_VERSION:
        raise ValueError("P7-R54-AHR-CS18 must follow CS17 candidate-only handoff envelope")
    _assert_snapshot_fields(data, actual_basis=True, source="P7-R54-AHR-CS18 final validation")
    _assert_existing_ahr_fields(data, source="P7-R54-AHR-CS18 final validation")
    if data.get("final_validation_status_ref") not in P7_R54_AHR_CS18_ALLOWED_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS18 final validation status changed")
    blockers = _cs_clean_identifier_list(data.get("execution_blocker_ids"), limit=60, max_length=240)
    if blockers != _cs_clean_identifier_list(data.get("open_execution_blocker_ids"), limit=60, max_length=240):
        raise ValueError("P7-R54-AHR-CS18 open blockers must match blockers")
    for key in (
        "actual_human_review_run_here",
        "actual_human_review_complete",
        "p5_human_blind_qa_confirmed_final",
        "p5_confirmed_final",
        "p5_final_allowed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_start_allowed",
        "p8_material_candidate_question_text_included",
        "p8_material_candidate_draft_question_text_included",
        "p8_material_candidate_question_answer_persistence_started",
        "p8_start_allowed",
        "r52_reintake_execution_requested_here",
        "actual_r52_reintake_execution_confirmed",
        "p7_complete",
        "release_allowed",
        "full_backend_suite_green_confirmed",
        "rn_contract_green_confirmed",
        "rn_real_device_modal_verified",
    ):
        if data.get(key) is not False:
            raise ValueError(f"P7-R54-AHR-CS18 must keep {key}=False")
    rows = data.get("command_matrix_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        raise ValueError("P7-R54-AHR-CS18 command matrix rows must be a sequence")
    if tuple(data.get("command_matrix_command_refs") or ()) != P7_R54_AHR_CS18_COMMAND_REFS:
        raise ValueError("P7-R54-AHR-CS18 command refs changed")
    if tuple(data.get("command_matrix_allowed_status_refs") or ()) != P7_R54_AHR_CS18_ALLOWED_COMMAND_STATUS_REFS:
        raise ValueError("P7-R54-AHR-CS18 command statuses changed")
    if len(rows) != len(P7_R54_AHR_CS18_COMMAND_REFS) or data.get("command_matrix_row_count") != len(P7_R54_AHR_CS18_COMMAND_REFS):
        raise ValueError("P7-R54-AHR-CS18 command matrix row count changed")
    passed_refs: list[str] = []
    green_refs: list[str] = []
    not_executed_refs: list[str] = []
    failed_refs: list[str] = []
    bad_runtime_refs: list[str] = []
    output_body_refs: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError("P7-R54-AHR-CS18 command row must be a mapping")
        _assert_required_fields(row, required=P7_R54_AHR_CS18_COMMAND_MATRIX_ROW_REQUIRED_FIELD_REFS, source="P7-R54-AHR-CS18 command row")
        expected_ref = P7_R54_AHR_CS18_COMMAND_REFS[index]
        if row.get("command_ref") != expected_ref:
            raise ValueError("P7-R54-AHR-CS18 command row order changed")
        if row.get("command_status_ref") not in P7_R54_AHR_CS18_ALLOWED_COMMAND_STATUS_REFS:
            raise ValueError("P7-R54-AHR-CS18 command status changed")
        executed = row.get("command_executed") is True
        passed = row.get("command_passed") is True
        failed = row.get("command_failed") is True
        runtime_bad = row.get("command_timeout") is True or row.get("command_killed") is True or row.get("command_interrupted") is True
        if passed and not executed:
            raise ValueError("P7-R54-AHR-CS18 command cannot pass without execution")
        if runtime_bad and (passed or row.get("command_green_evidence_accepted") is True):
            raise ValueError("P7-R54-AHR-CS18 runtime-bad command cannot be green evidence")
        for body_flag in ("command_output_body_included", "stdout_body_included", "stderr_body_included", "traceback_body_included", "terminal_output_body_included", "local_absolute_path_included", "body_hash_included"):
            if row.get(body_flag) is not False:
                raise ValueError("P7-R54-AHR-CS18 command output/path/hash body must not be included")
        if row.get("body_free") is not True:
            raise ValueError("P7-R54-AHR-CS18 command row must remain body-free")
        if passed:
            passed_refs.append(expected_ref)
        if row.get("command_green_evidence_accepted") is True:
            if expected_ref not in P7_R54_AHR_CS18_COMMAND_GREEN_EVIDENCE_ACCEPTABLE_REFS:
                raise ValueError("P7-R54-AHR-CS18 command outside selected scope cannot be green evidence")
            green_refs.append(expected_ref)
        if row.get("command_status_ref") == P7_R54_AHR_CS18_COMMAND_STATUS_NOT_EXECUTED_REF:
            not_executed_refs.append(expected_ref)
        if failed:
            failed_refs.append(expected_ref)
        if runtime_bad:
            bad_runtime_refs.append(expected_ref)
    if data.get("command_matrix_passed_refs") != passed_refs:
        raise ValueError("P7-R54-AHR-CS18 command passed refs changed")
    if data.get("command_matrix_green_evidence_accepted_refs") != green_refs:
        raise ValueError("P7-R54-AHR-CS18 command green refs changed")
    if data.get("command_matrix_not_executed_refs") != not_executed_refs:
        raise ValueError("P7-R54-AHR-CS18 command not-executed refs changed")
    if data.get("command_matrix_failed_refs") != failed_refs:
        raise ValueError("P7-R54-AHR-CS18 command failed refs changed")
    if data.get("command_matrix_timeout_killed_interrupted_refs") != bad_runtime_refs:
        raise ValueError("P7-R54-AHR-CS18 command runtime-bad refs changed")
    for key in (
        "command_matrix_bodyfree_only",
        "command_matrix_no_unexecuted_passed_claim",
        "command_matrix_no_timeout_kill_interrupted_green_claim",
        "command_matrix_no_output_body_included",
        "selected_regression_green_not_full_backend_suite_green",
        "rn_contract_green_not_real_device_modal_verified",
        "documentation_output_claims_no_auto_promotion",
    ):
        if data.get(key) is not True:
            raise ValueError(f"P7-R54-AHR-CS18 must keep {key}=True")
    if tuple(data.get("claim_boundary_refs") or ()) != P7_R54_AHR_CS18_CLAIM_BOUNDARY_REFS:
        raise ValueError("P7-R54-AHR-CS18 claim boundary refs changed")
    ready = data.get("final_validation_status_ref") == P7_R54_AHR_CS18_READY_STATUS_REF
    if ready:
        if blockers:
            raise ValueError("P7-R54-AHR-CS18 ready material must not carry blockers")
        for key in P7_R54_AHR_CS15_EVIDENCE_COMPLETE_REQUIRED_TRUE_FIELD_REFS:
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS18 ready material must preserve {key}=True")
        for key in (
            "candidate_handoff_ready_for_final_validation",
            "p5_confirmed_candidate",
            "p5_confirmed_candidate_not_finalized_here",
            "p6_candidate_only_handoff_built",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "p8_material_candidate_only_handoff_built",
            "p8_question_design_material_candidate",
            "r52_reintake_handoff_envelope_built",
            "r52_reintake_handoff_ready",
            "r52_reintake_handoff_ready_here",
            "documentation_output_bodyfree_only",
            "documentation_output_ready",
        ):
            if data.get(key) is not True:
                raise ValueError(f"P7-R54-AHR-CS18 ready material must keep {key}=True")
        if tuple(data.get("command_matrix_green_evidence_accepted_refs") or ()) != P7_R54_AHR_CS18_COMMAND_GREEN_EVIDENCE_ACCEPTABLE_REFS:
            raise ValueError("P7-R54-AHR-CS18 ready material must include all selected green evidence refs")
        if data.get("command_matrix_failed_refs") or data.get("command_matrix_timeout_killed_interrupted_refs") or data.get("command_matrix_output_body_included_refs"):
            raise ValueError("P7-R54-AHR-CS18 ready material must not carry failed/runtime-bad/body-output command refs")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS18_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS18 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS18_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS18 not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS18_READY_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS18 next step changed")
    else:
        if not blockers:
            raise ValueError("P7-R54-AHR-CS18 blocked material must carry blockers")
        if data.get("documentation_output_ready") is not False:
            raise ValueError("P7-R54-AHR-CS18 blocked material must not be documentation-ready")
        if tuple(data.get("implemented_steps") or ()) != P7_R54_AHR_CS17_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS18 blocked implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R54_AHR_CS17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("P7-R54-AHR-CS18 blocked not-yet steps changed")
        if data.get("next_required_step") != P7_R54_AHR_CS18_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("P7-R54-AHR-CS18 blocked next step changed")
    return True


# Compatibility aliases for CS18 design wording.
build_p7_r54_ahr_cs18_final_no_body_leak_no_question_text_no_touch_validation = build_p7_r54_ahr_cs18_validation_command_matrix_documentation_output
build_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output = build_p7_r54_ahr_cs18_validation_command_matrix_documentation_output
assert_p7_r54_ahr_cs18_final_no_body_leak_no_question_text_no_touch_validation_contract = assert_p7_r54_ahr_cs18_validation_command_matrix_documentation_output_contract
assert_p7_r54_ahr_cs18_final_validation_command_matrix_documentation_output_contract = assert_p7_r54_ahr_cs18_validation_command_matrix_documentation_output_contract
build_p7_r54_ahr_current_snapshot_actual_review_reentry_final_validation_documentation_bodyfree = build_p7_r54_ahr_cs18_validation_command_matrix_documentation_output
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_final_validation_documentation_bodyfree_contract = assert_p7_r54_ahr_cs18_validation_command_matrix_documentation_output_contract

# Compatibility aliases for CS16/CS17 design wording.
build_p7_r54_ahr_cs16_p5_decision_candidate_separation_bodyfree = (
    build_p7_r54_ahr_cs16_p5_decision_candidate_separation
)
assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_bodyfree_contract = (
    assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_p5_decision_candidate_separation_bodyfree = (
    build_p7_r54_ahr_cs16_p5_decision_candidate_separation
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_p5_decision_candidate_separation_bodyfree_contract = (
    assert_p7_r54_ahr_cs16_p5_decision_candidate_separation_contract
)
build_p7_r54_ahr_cs17_p6_candidate_only_handoff = (
    build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope
)
build_p7_r54_ahr_cs17_p8_material_candidate_only_handoff = (
    build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope
)
build_p7_r54_ahr_cs17_r52_reintake_handoff_envelope = (
    build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope
)
assert_p7_r54_ahr_cs17_candidate_handoff_contract = (
    assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract
)
assert_p7_r54_ahr_cs17_p6_candidate_only_handoff_contract = (
    assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract
)
assert_p7_r54_ahr_cs17_p8_material_candidate_only_handoff_contract = (
    assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract
)
assert_p7_r54_ahr_cs17_r52_reintake_handoff_envelope_contract = (
    assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_candidate_handoff_bodyfree = (
    build_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_candidate_handoff_bodyfree_contract = (
    assert_p7_r54_ahr_cs17_p6_p8_candidate_only_r52_handoff_envelope_contract
)




# Compatibility aliases for CS14/CS15 design wording.
build_p7_r54_ahr_cs14_pause_abort_expiration_protocol = build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt
build_p7_r54_ahr_cs14_purge_disposal_receipt_intake = build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt
build_p7_r54_ahr_cs14_disposal_receipt_intake_bodyfree = build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt
assert_p7_r54_ahr_cs14_disposal_contract = assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract
assert_p7_r54_ahr_cs14_pause_abort_expiration_protocol_contract = assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract
assert_p7_r54_ahr_cs14_purge_disposal_receipt_intake_contract = assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract
build_p7_r54_ahr_current_snapshot_actual_review_reentry_disposal_receipt_bodyfree = (
    build_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_disposal_receipt_bodyfree_contract = (
    assert_p7_r54_ahr_cs14_pause_abort_expiration_disposal_receipt_contract
)
build_p7_r54_ahr_cs15_bodyfree_post_review_summary = (
    build_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete
)
assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_contract = (
    assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_post_review_summary_bodyfree = (
    build_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_post_review_summary_bodyfree_contract = (
    assert_p7_r54_ahr_cs15_bodyfree_post_review_summary_evidence_complete_contract
)


# Compatibility aliases for CS12/CS13 design wording.
build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_bodyfree = (
    build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization
)
assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_bodyfree_contract = (
    assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_blocker_question_need_observation_normalization_bodyfree = (
    build_p7_r54_ahr_cs12_blocker_question_need_observation_normalization
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_blocker_question_need_observation_normalization_bodyfree_contract = (
    assert_p7_r54_ahr_cs12_blocker_question_need_observation_normalization_contract
)
build_p7_r54_ahr_cs13_rating_question_consistency_guard_bodyfree = (
    build_p7_r54_ahr_cs13_rating_question_consistency_guard
)
assert_p7_r54_ahr_cs13_rating_question_consistency_guard_bodyfree_contract = (
    assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract
)
build_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_question_consistency_guard_bodyfree = (
    build_p7_r54_ahr_cs13_rating_question_consistency_guard
)
assert_p7_r54_ahr_current_snapshot_actual_review_reentry_rating_question_consistency_guard_bodyfree_contract = (
    assert_p7_r54_ahr_cs13_rating_question_consistency_guard_contract
)

