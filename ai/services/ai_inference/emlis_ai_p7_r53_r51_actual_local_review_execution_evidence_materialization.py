# -*- coding: utf-8 -*-
"""P7-R53 R51 actual local-only review evidence materialization helpers.

R53-0 refreezes the current received local snapshot for the R53 work session.
R53-1 freezes the delta between the historical R51/R52 helper refs and the
R53 current received snapshot so those older refs cannot be reused as the
actual-review basis.
R53-2 freezes validation evidence and keeps the R49 wildcard timeout visible
instead of turning it into green evidence.
R53-3 adopts the existing R51 R0/R1 builders with the R53 current snapshot
override, while still blocking any body-full/local review progression when
validation evidence is incomplete.
R53-4 wraps the existing R51 local-root / explicit-allow / purge-plan
preflight in an R53 body-free materialization layer.
R53-5 wraps the existing R51 actual-review session envelope in an R53
body-free controller-material layer.
R53-6 wraps the existing R51 24-case manifest freeze while separating the
controller manifest from the reviewer-facing blind case index.
R53-7 wraps the existing R51 local-only body-full packet generation request and
keeps the optional writer boundary explicit but not executed here.
R53-8 wraps the existing R51 packet-completeness/export-denylist scan while
keeping packet bodies, local paths, and hashes outside exported evidence.
R53-9 wraps the existing R51 reviewer instruction/rating-form freeze without
running review or materializing rating/question rows.
R53-10 captures sanitized body-free human review selections only when supplied.
R53-11 normalizes those captured selections into R51-compatible body-free rating
rows.
R53-12 separates readfeel blockers from execution blockers without turning
execution blockers into readfeel verdicts.
R53-13 normalizes body-free question-need observation rows while keeping
question text/draft text/API/DB/RN/P8 implementation closed.
R53-14 guards rating/question consistency so P5 weakness cannot be routed into
question candidates.
R53-15 freezes pause / abort / expiration protocol before purge/disposal.
R53-16 materializes body-free purge verification and disposal receipt evidence.
R53-17 builds a body-free post-review summary from finalized rows and receipt.
R53-18 separates P5 confirmed candidate / repair return / inconclusive.
R53-19 creates a P6 limited human readfeel candidate handoff without allowing P6 start.
R53-20 creates a P8 question design material candidate handoff from body-free
question-observation counts without starting P8 or finalizing question specs.
R53-21 validates no body leak / no question text / no-touch boundaries and
materializes a body-free R52 re-intake handoff without auto-allowing P6/P8.

This module intentionally implements only R53-0 through R53-21.  It does not run
an actual human review, generate local-only body-full packets in exported
artifacts, write question text or draft question text, execute local file delete
operations by itself, modify API/DB/RN/runtime contracts, start P6/P8, complete
P7, or claim release readiness.
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
    dedupe_identifiers,
    public_contract_flags,
    safe_mapping,
)
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import (
    P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
    P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
    P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS,
    P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
    P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
    P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
    P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR,
    P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
    P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
    P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
    P7_R51_PACKET_KIND,
    P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS,
    P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION,
    P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION,
    P7_R51_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
    P7_R51_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION,
    P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION,
    P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    P7_R51_P5_DECISION_STATUS_REFS,
    P7_R51_P6_CANDIDATE_HANDOFF_STATUS_REFS,
    P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
    P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS,
    P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
    P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS,
    P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS,
    P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS,
    P7_R51_R19_NEXT_REQUIRED_STEP_REF,
    P7_R51_R19_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R20_NEXT_REQUIRED_STEP_REF,
    P7_R51_R20_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R20_ALLOWED_ACTUAL_TOUCHED_FILE_REFS,
    P7_R51_R20_EXPECTED_TOUCHED_FILE_REFS,
    P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS,
    P7_R51_R20_EXPLICIT_NO_TOUCH_AREA_REFS,
    P7_R51_R20_BOUNDARY_STATUS_REFS,
    P7_R51_R17_CONFIRMED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R17_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF,
    P7_R51_R17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF,
    P7_R51_R18_NEXT_REQUIRED_STEP_REF,
    P7_R51_R18_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R14_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R14_NEXT_REQUIRED_STEP_REF,
    P7_R51_R15_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R15_NEXT_REQUIRED_STEP_REF,
    P7_R51_R16_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R16_NEXT_REQUIRED_STEP_REF,
    P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R1_NEXT_REQUIRED_STEP_REF,
    P7_R51_R2_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R2_NEXT_REQUIRED_STEP_REF,
    P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R3_NEXT_REQUIRED_STEP_REF,
    P7_R51_R4_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R4_NEXT_REQUIRED_STEP_REF,
    P7_R51_R5_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R5_NEXT_REQUIRED_STEP_REF,
    P7_R51_REQUIRED_CASE_COUNT,
    P7_R51_REVIEW_KIND,
    P7_R51_REVIEW_PROMPT_VERSION,
    P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
    P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION,
    P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS,
    P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R51_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
    P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
    P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS,
    P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
    P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
    P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_SCHEMA_VERSION,
    P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ID_REFS,
    P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_KIND_REFS,
    P7_R51_PAUSE_ABORT_EXPIRATION_ACTION_REFS,
    P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
    P7_R51_ACTUAL_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS,
    P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R6_NEXT_REQUIRED_STEP_REF,
    P7_R51_R7_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R7_NEXT_REQUIRED_STEP_REF,
    P7_R51_R8_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R8_NEXT_REQUIRED_STEP_REF,
    P7_R51_R9_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R9_NEXT_REQUIRED_STEP_REF,
    P7_R51_R10_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R10_NEXT_REQUIRED_STEP_REF,
    P7_R51_R11_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R11_NEXT_REQUIRED_STEP_REF,
    P7_R51_R12_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R12_NEXT_REQUIRED_STEP_REF,
    P7_R51_R13_BLOCKED_NEXT_REQUIRED_STEP_REF,
    P7_R51_R13_NEXT_REQUIRED_STEP_REF,
    P7_R51_R13_PAUSED_NEXT_REQUIRED_STEP_REF,
    P7_R51_SCOPE,
    P7_R51_SOURCE_SNAPSHOT_REFS,
    P7_R51_STEP,
    P7_R51_VALIDATION_EVIDENCE_GROUP_REFS,
    P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
    P7_R51_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS,
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract,
    assert_p7_r51_actual_review_session_envelope_bodyfree_contract,
    assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract,
    assert_p7_r51_current_source_r50_handoff_refreeze_contract,
    assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract,
    assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract,
    assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract,
    assert_p7_r51_actual_human_review_run_bodyfree_contract,
    assert_p7_r51_rating_row_bodyfree_contract,
    assert_p7_r51_rating_row_normalizer_bodyfree_contract,
    assert_p7_r51_readfeel_blocker_row_bodyfree_contract,
    assert_p7_r51_execution_blocker_row_bodyfree_contract,
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract,
    assert_p7_r51_question_need_observation_row_bodyfree_contract,
    assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract,
    assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract,
    assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract,
    assert_p7_r51_purge_evidence_row_bodyfree_contract,
    assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract,
    assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract,
    assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract,
    assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract,
    assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract,
    assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract,
    assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract,
    assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract,
    build_p7_r51_24_case_manifest_freeze_bodyfree,
    build_p7_r51_actual_review_session_envelope_bodyfree,
    build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree,
    build_p7_r51_current_source_r50_handoff_refreeze,
    build_p7_r51_default_local_only_purge_plan_bodyfree,
    build_p7_r51_local_only_body_full_packet_generation_request_bodyfree,
    build_p7_r51_local_root_explicit_allow_purge_plan_preflight,
    build_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree,
    build_p7_r51_actual_human_review_run_bodyfree,
    build_p7_r51_rating_row_normalizer_bodyfree,
    build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree,
    build_p7_r51_question_need_observation_row_normalizer_bodyfree,
    build_p7_r51_rating_question_observation_consistency_guard_bodyfree,
    build_p7_r51_pause_abort_expiration_protocol_bodyfree,
    build_p7_r51_purge_evidence_row_bodyfree,
    build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree,
    build_p7_r51_disposal_receipt_builder_verifier_bodyfree,
    build_p7_r51_body_free_post_review_summary_builder_bodyfree,
    build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree,
    build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree,
    build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree,
    build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree,
    build_p7_r51_validation_evidence_r49_timeout_handling_freeze,
)
from emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate import (
    P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
    P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS,
    P7_R52_SCOPE,
    P7_R52_STEP,
    P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION,
)


P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.current_received_snapshot_refreeze.bodyfree.v1"
)
P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.r51_r52_source_delta_freeze.bodyfree.v1"
)
P7_R53_SOURCE_DELTA_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.source_delta_row.bodyfree.v1"
)

P7_R53_STEP: Final = "R53_R51ActualLocalReviewExecutionEvidenceMaterialization_20260621"
P7_R53_SCOPE: Final = "r51_actual_local_review_execution_evidence_materialization"
P7_R53_POLICY_KIND: Final = "r51_actual_local_review_execution_evidence_materialization_policy"
P7_R53_DEFAULT_REVIEW_SESSION_ID: Final = "p7_r53_r51_actual_local_review_session"

P7_R53_R0_NEXT_REQUIRED_STEP_REF: Final = "R53-1_r51_r52_helper_source_delta_freeze"
P7_R53_R1_NEXT_REQUIRED_STEP_REF: Final = "R53-2_r49_timeout_validation_evidence_preflight"
P7_R53_FIRST_NEXT_WORK_REF: Final = "r51_actual_local_review_materialization_without_p8_or_release_promotion"

P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS: Final[dict[str, str]] = {
    "premise_zip_ref": "Cocolon_前提資料(245).zip",
    "implemented_materials_zip_ref": "EmlisAIの実装済み資料(75).zip",
    "rn_zip_ref": "Cocolon(248).zip",
    "backend_zip_ref": "mashos-api(161).zip",
    "roadmap_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(6).md",
    "pre_design_memo_ref": "Cocolon_EmlisAI_P7_R53Candidate_R51ActualLocalReview_PreDesignMemo_20260621(1).md",
    "detailed_design_ref": "Cocolon_EmlisAI_P7_R53_R51ActualLocalReviewExecutionEvidenceMaterialization_DetailedDesign_ImplementationOrder_20260621.md",
}

P7_R53_R0_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-0_scope_current_received_snapshot_refreeze",
)
P7_R53_FUTURE_STEPS_AFTER_R1: Final[tuple[str, ...]] = (
    "R53-2_r49_timeout_validation_evidence_preflight",
    "R53-3_r51_r0_r1_adoption_with_current_snapshot_override",
    "R53-4_explicit_allow_local_root_purge_plan_preflight",
    "R53-5_actual_review_session_envelope",
    "R53-6_24_case_manifest_freeze",
    "R53-7_local_only_body_full_packet_generation_request_optional_writer",
    "R53-8_packet_completeness_export_denylist_scan",
    "R53-9_reviewer_instruction_rating_form_freeze",
    "R53-10_actual_human_review_result_capture",
    "R53-11_rating_row_normalization",
    "R53-12_readfeel_blocker_execution_blocker_ingestion",
    "R53-13_question_need_observation_row_normalization",
    "R53-14_rating_question_consistency_guard",
    "R53-15_pause_abort_expiration_protocol",
    "R53-16_purge_disposal_receipt",
    "R53-17_body_free_post_review_summary",
    "R53-18_p5_decision_candidate_separation",
    "R53-19_p6_limited_human_readfeel_candidate_handoff",
    "R53-20_p8_question_design_material_candidate_handoff",
    "R53-21_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff",
)
P7_R53_R0_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-1_r51_r52_helper_source_delta_freeze",
    *P7_R53_FUTURE_STEPS_AFTER_R1,
)
P7_R53_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R0_IMPLEMENTED_STEPS,
    "R53-1_r51_r52_helper_source_delta_freeze",
)
P7_R53_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R1

P7_R53_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "p8_question_implementation_spec_finalized_here",
    "question_implementation_started_here",
)
P7_R53_REVIEW_RELEASE_CLOSED_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_body_full_packet_generated_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "local_root_preflight_passed_here",
    "explicit_allow_present_here",
    "purge_plan_verified_here",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_human_blind_qa_confirmed_final",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "hold004_close_allowed",
)
P7_R53_SCHEMA_MUTATION_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "json_schema_file_created_here",
    "schema_files_materialized_here",
    "api_db_rn_response_key_changed_here",
    "runtime_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "rn_visible_contract_changed_here",
    "public_response_top_level_key_added_here",
    "public_response_key_changed_here",
)
P7_R53_EXPORT_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "body_full_packet_export_allowed",
    "reviewer_notes_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "local_absolute_path_materialized_here",
    "body_content_hash_materialized_here",
    "packet_content_hash_materialized_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "full_backend_suite_green_confirmed",
    "backend_collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
)
P7_R53_R0_R1_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R53_QUESTION_IMPLEMENTATION_FALSE_KEY_REFS,
    *P7_R53_REVIEW_RELEASE_CLOSED_KEY_REFS,
    *P7_R53_SCHEMA_MUTATION_FALSE_KEY_REFS,
    *P7_R53_EXPORT_FALSE_KEY_REFS,
)

P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_helper_source_snapshot_refs",
    "r51_helper_source_snapshot_ref_count",
    "r52_helper_current_received_snapshot_refs",
    "r52_helper_current_received_snapshot_ref_count",
    "r51_helper_refs_are_current_received_refs",
    "r52_helper_refs_are_current_received_refs",
    "old_refs_allowed_as_actual_review_basis",
    "r51_builder_snapshot_override_required",
    "current_snapshot_can_override_r51_builder_snapshot_refs",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_SOURCE_DELTA_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "helper_ref_group",
    "helper_step",
    "helper_scope",
    "helper_refreeze_schema_version",
    "helper_validation_schema_version",
    "helper_snapshot_refs",
    "helper_snapshot_ref_count",
    "r53_current_received_snapshot_refs",
    "same_as_r53_current_received_refs",
    "actual_review_basis_allowed",
    "regression_helper_context_allowed",
    "snapshot_override_required_for_actual_review",
    "source_delta_reason_refs",
    "body_free",
)

P7_R53_R51_R52_SOURCE_DELTA_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r0_refreeze_schema_version",
    "r0_refreeze_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_helper_source_snapshot_refs",
    "r51_helper_source_snapshot_ref_count",
    "r52_helper_current_received_snapshot_refs",
    "r52_helper_current_received_snapshot_ref_count",
    "source_delta_rows",
    "source_delta_row_count",
    "r51_helper_refs_are_current_received_refs",
    "r52_helper_refs_are_current_received_refs",
    "r53_current_received_refs_frozen",
    "old_refs_allowed_as_actual_review_basis",
    "r51_old_refs_allowed_as_actual_review_basis",
    "r52_old_refs_allowed_as_actual_review_basis",
    "r51_builder_snapshot_override_required",
    "current_snapshot_can_override_r51_builder_snapshot_refs",
    "r51_helper_refs_can_be_used_for_helper_regression_only",
    "r52_helper_refs_can_be_used_for_helper_regression_only",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def _false_flags() -> dict[str, bool]:
    return {key: False for key in P7_R53_R0_R1_FALSE_KEY_REFS}


def _safe_review_session_id(value: Any) -> str:
    return clean_identifier(value, default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140)


def _snapshot_refs(base: Mapping[str, str], overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    refs = dict(base)
    for key, value in safe_mapping(overrides).items():
        if key in refs:
            refs[key] = clean_identifier(value, default=refs[key], max_length=260)
    return refs


def _current_received_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS, overrides)


def _r51_helper_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R51_SOURCE_SNAPSHOT_REFS, overrides)


def _r52_helper_snapshot_refs(overrides: Mapping[str, Any] | None = None) -> dict[str, str]:
    return _snapshot_refs(P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS, overrides)


def _refs_match(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return bool(left) and bool(right) and {str(k): str(v) for k, v in left.items()} == {str(k): str(v) for k, v in right.items()}


def _body_free_markers() -> dict[str, bool]:
    return body_free_flags(include_history=True, include_reviewer=True, include_terminal=True)


def _public_no_touch_contract() -> dict[str, bool]:
    return {
        "api_route_changed_here": False,
        "db_schema_changed_here": False,
        "db_migration_changed_here": False,
        "rn_visible_contract_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "runtime_changed_here": False,
        "p8_question_implementation_changed_here": False,
        "release_material_changed_here": False,
    }


def _assert_required_fields(data: Mapping[str, Any], *, required: Sequence[str], source: str) -> None:
    missing = [field for field in required if field not in data]
    if missing:
        raise ValueError(f"{source} missing required fields: {missing[:6]}")
    extra = sorted(set(data) - set(required))
    if extra:
        raise ValueError(f"{source} has unexpected fields: {extra[:6]}")


def _assert_body_free_common(data: Mapping[str, Any], *, schema_version: str, source: str) -> None:
    _assert_body_free_common_allowing(
        data,
        schema_version=schema_version,
        source=source,
        allowed_true_false_key_refs=(),
    )


def _assert_body_free_common_allowing(
    data: Mapping[str, Any],
    *,
    schema_version: str,
    source: str,
    allowed_true_false_key_refs: Sequence[str] = (),
) -> None:
    """R53 remains body-free while selected evidence flags may become true
    after sanitized, body-free review results exist.
    """
    if data.get("schema_version") != schema_version:
        raise ValueError(f"{source} schema version changed")
    if data.get("phase") != P7_PHASE:
        raise ValueError(f"{source} phase changed")
    if data.get("step") != P7_R53_STEP:
        raise ValueError(f"{source} step changed")
    if data.get("scope") != P7_R53_SCOPE:
        raise ValueError(f"{source} scope changed")
    if data.get("source_mode") != P7_SOURCE_MODE:
        raise ValueError(f"{source} must remain local snapshot")
    if data.get("git_connection_required") is not False or data.get("git_checked") is not False:
        raise ValueError(f"{source} must not require or perform Git checks")
    if data.get("body_free") is not True:
        raise ValueError(f"{source} must be body-free")
    allowed = set(allowed_true_false_key_refs or ())
    unexpected = sorted(allowed - set(P7_R53_R0_R1_FALSE_KEY_REFS))
    if unexpected:
        raise ValueError(f"{source} cannot allow non-R53 review/release closed flags: {unexpected[:4]}")
    assert_false_markers(data.get("public_contract") or {}, source=f"{source}.public_contract")
    assert_false_markers(data.get("r53_public_no_touch_contract") or {}, source=f"{source}.r53_public_no_touch_contract")
    assert_false_markers(data.get("body_free_markers") or {}, source=f"{source}.body_free_markers")
    for false_key in P7_R53_R0_R1_FALSE_KEY_REFS:
        if false_key in allowed:
            if data.get(false_key) is not True:
                raise ValueError(f"{source} must set allowed evidence flag {false_key}=True")
            continue
        if data.get(false_key) is not False:
            raise ValueError(f"{source} must keep {false_key}=False")
    assert_p7_no_body_payload_or_contract_mutation(data, source=source)


def _assert_current_refs(data: Mapping[str, Any], *, source: str) -> None:
    current_refs = safe_mapping(data.get("current_received_snapshot_refs"))
    r51_refs = safe_mapping(data.get("r51_helper_source_snapshot_refs"))
    r52_refs = safe_mapping(data.get("r52_helper_current_received_snapshot_refs"))
    if current_refs != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} current received snapshot refs changed")
    if r51_refs != P7_R51_SOURCE_SNAPSHOT_REFS:
        raise ValueError(f"{source} R51 helper source refs changed")
    if r52_refs != P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError(f"{source} R52 helper current refs changed")
    if data.get("current_received_snapshot_ref_count") != len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} current received snapshot ref count changed")
    if data.get("r51_helper_source_snapshot_ref_count") != len(P7_R51_SOURCE_SNAPSHOT_REFS):
        raise ValueError(f"{source} R51 helper source ref count changed")
    if data.get("r52_helper_current_received_snapshot_ref_count") != len(P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS):
        raise ValueError(f"{source} R52 helper current ref count changed")
    if _refs_match(r51_refs, current_refs) or data.get("r51_helper_refs_are_current_received_refs") is not False:
        raise ValueError(f"{source} must not treat R51 helper refs as current received refs")
    if _refs_match(r52_refs, current_refs) or data.get("r52_helper_refs_are_current_received_refs") is not False:
        raise ValueError(f"{source} must not treat R52 helper refs as current received refs")


def _source_delta_row(
    *,
    helper_ref_group: str,
    helper_step: str,
    helper_scope: str,
    helper_refreeze_schema_version: str,
    helper_validation_schema_version: str,
    helper_snapshot_refs: Mapping[str, Any],
    current_received_snapshot_refs: Mapping[str, Any],
) -> dict[str, Any]:
    helper_refs = {str(key): str(value) for key, value in helper_snapshot_refs.items()}
    current_refs = {str(key): str(value) for key, value in current_received_snapshot_refs.items()}
    same_as_current = _refs_match(helper_refs, current_refs)
    row = {
        "schema_version": P7_R53_SOURCE_DELTA_ROW_SCHEMA_VERSION,
        "helper_ref_group": clean_identifier(helper_ref_group, default="helper_refs", max_length=120),
        "helper_step": clean_identifier(helper_step, default="helper_step", max_length=180),
        "helper_scope": clean_identifier(helper_scope, default="helper_scope", max_length=180),
        "helper_refreeze_schema_version": clean_identifier(helper_refreeze_schema_version, default="helper_refreeze_schema", max_length=220),
        "helper_validation_schema_version": clean_identifier(helper_validation_schema_version, default="helper_validation_schema", max_length=220),
        "helper_snapshot_refs": helper_refs,
        "helper_snapshot_ref_count": len(helper_refs),
        "r53_current_received_snapshot_refs": current_refs,
        "same_as_r53_current_received_refs": same_as_current,
        "actual_review_basis_allowed": False,
        "regression_helper_context_allowed": True,
        "snapshot_override_required_for_actual_review": True,
        "source_delta_reason_refs": [
            "historical_helper_refs_must_not_be_relabelled_as_r53_current_received_snapshot",
            "r53_actual_review_basis_requires_current_received_snapshot_refreeze",
        ],
        "body_free": True,
    }
    assert_p7_r53_source_delta_row_contract(row)
    return row


def assert_p7_r53_source_delta_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R53_SOURCE_DELTA_ROW_REQUIRED_FIELD_REFS,
        source="p7_r53_source_delta_row",
    )
    if data.get("schema_version") != P7_R53_SOURCE_DELTA_ROW_SCHEMA_VERSION:
        raise ValueError("R53 source delta row schema version changed")
    helper_group = data.get("helper_ref_group")
    if helper_group not in {"r51_helper_source_snapshot_refs", "r52_helper_current_received_snapshot_refs"}:
        raise ValueError("R53 source delta row helper group is not canonical")
    helper_refs = safe_mapping(data.get("helper_snapshot_refs"))
    current_refs = safe_mapping(data.get("r53_current_received_snapshot_refs"))
    if current_refs != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 source delta row current refs changed")
    expected_refs = P7_R51_SOURCE_SNAPSHOT_REFS if helper_group == "r51_helper_source_snapshot_refs" else P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS
    if helper_refs != expected_refs:
        raise ValueError("R53 source delta row helper refs changed")
    if data.get("helper_snapshot_ref_count") != len(expected_refs):
        raise ValueError("R53 source delta row helper ref count changed")
    if data.get("same_as_r53_current_received_refs") is not False:
        raise ValueError("R53 source delta row must keep helper refs distinct from current refs")
    if data.get("actual_review_basis_allowed") is not False:
        raise ValueError("R53 source delta row must not allow old refs as actual review basis")
    if data.get("regression_helper_context_allowed") is not True:
        raise ValueError("R53 source delta row should preserve old refs only as helper regression context")
    if data.get("snapshot_override_required_for_actual_review") is not True:
        raise ValueError("R53 source delta row must require current snapshot override for actual review")
    if data.get("body_free") is not True:
        raise ValueError("R53 source delta row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_source_delta_row")
    return True


def build_p7_r53_current_received_snapshot_refreeze(
    *,
    current_received_snapshot_refs: Mapping[str, Any] | None = None,
    r51_helper_source_snapshot_refs: Mapping[str, Any] | None = None,
    r52_helper_current_received_snapshot_refs: Mapping[str, Any] | None = None,
    review_session_id: Any = P7_R53_DEFAULT_REVIEW_SESSION_ID,
    material_id: Any = "p7_r53_current_received_snapshot_refreeze",
) -> dict[str, Any]:
    """Build R53-0 body-free scope/current received snapshot refreeze."""

    current_refs = _current_received_snapshot_refs(current_received_snapshot_refs)
    r51_refs = _r51_helper_snapshot_refs(r51_helper_source_snapshot_refs)
    r52_refs = _r52_helper_snapshot_refs(r52_helper_current_received_snapshot_refs)
    r51_is_current = _refs_match(r51_refs, current_refs)
    r52_is_current = _refs_match(r52_refs, current_refs)
    refreeze = {
        "schema_version": P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-0_scope_current_received_snapshot_refreeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_current_received_snapshot_refreeze", max_length=180),
        "review_session_id": _safe_review_session_id(review_session_id),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r51_helper_source_snapshot_refs": r51_refs,
        "r51_helper_source_snapshot_ref_count": len(r51_refs),
        "r52_helper_current_received_snapshot_refs": r52_refs,
        "r52_helper_current_received_snapshot_ref_count": len(r52_refs),
        "r51_helper_refs_are_current_received_refs": r51_is_current,
        "r52_helper_refs_are_current_received_refs": r52_is_current,
        "old_refs_allowed_as_actual_review_basis": False,
        "r51_builder_snapshot_override_required": True,
        "current_snapshot_can_override_r51_builder_snapshot_refs": True,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": False,
        "implemented_steps": list(P7_R53_R0_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R0_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R0_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_current_received_snapshot_refreeze_contract(refreeze)
    return refreeze


def assert_p7_r53_current_received_snapshot_refreeze_contract(refreeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(refreeze)
    _assert_required_fields(
        data,
        required=P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS,
        source="p7_r53_r0_current_received_snapshot_refreeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        source="p7_r53_r0_current_received_snapshot_refreeze",
    )
    if data.get("policy_section") != "R53-0_scope_current_received_snapshot_refreeze":
        raise ValueError("R53 R0 policy section changed")
    _assert_current_refs(data, source="p7_r53_r0_current_received_snapshot_refreeze")
    if data.get("old_refs_allowed_as_actual_review_basis") is not False:
        raise ValueError("R53 R0 must not allow old refs as actual review basis")
    if data.get("r51_builder_snapshot_override_required") is not True:
        raise ValueError("R53 R0 must require R51 builder snapshot override")
    if data.get("current_snapshot_can_override_r51_builder_snapshot_refs") is not True:
        raise ValueError("R53 R0 must allow current snapshot to override R51 builder refs")
    if data.get("r53_0_scope_current_received_snapshot_refrozen") is not True:
        raise ValueError("R53 R0 must mark current received snapshot refrozen")
    if data.get("r53_1_r51_r52_helper_source_delta_frozen") is not False:
        raise ValueError("R53 R0 must not claim R53-1")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R0_IMPLEMENTED_STEPS:
        raise ValueError("R53 R0 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R0_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R0 not-yet steps changed")
    if data.get("next_required_step") != P7_R53_R0_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R53 R0 must point to R53-1")
    return True


def build_p7_r53_r51_r52_helper_source_delta_freeze(
    *,
    current_received_snapshot_refreeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_r51_r52_helper_source_delta_freeze",
) -> dict[str, Any]:
    """Build R53-1 body-free R51/R52 helper source delta freeze."""

    r0 = safe_mapping(current_received_snapshot_refreeze) if current_received_snapshot_refreeze is not None else build_p7_r53_current_received_snapshot_refreeze()
    assert_p7_r53_current_received_snapshot_refreeze_contract(r0)
    current_refs = safe_mapping(r0.get("current_received_snapshot_refs"))
    r51_refs = safe_mapping(r0.get("r51_helper_source_snapshot_refs"))
    r52_refs = safe_mapping(r0.get("r52_helper_current_received_snapshot_refs"))
    rows = [
        _source_delta_row(
            helper_ref_group="r51_helper_source_snapshot_refs",
            helper_step=P7_R51_STEP,
            helper_scope=P7_R51_SCOPE,
            helper_refreeze_schema_version=P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
            helper_validation_schema_version=P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
            helper_snapshot_refs=r51_refs,
            current_received_snapshot_refs=current_refs,
        ),
        _source_delta_row(
            helper_ref_group="r52_helper_current_received_snapshot_refs",
            helper_step=P7_R52_STEP,
            helper_scope=P7_R52_SCOPE,
            helper_refreeze_schema_version=P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
            helper_validation_schema_version=P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION,
            helper_snapshot_refs=r52_refs,
            current_received_snapshot_refs=current_refs,
        ),
    ]
    freeze = {
        "schema_version": P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-1_r51_r52_helper_source_delta_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_r51_r52_helper_source_delta_freeze", max_length=180),
        "review_session_id": _safe_review_session_id(r0.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r0_refreeze_schema_version": P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION,
        "r0_refreeze_material_ref": clean_identifier(r0.get("material_id"), default="p7_r53_current_received_snapshot_refreeze", max_length=180),
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r51_helper_source_snapshot_refs": r51_refs,
        "r51_helper_source_snapshot_ref_count": len(r51_refs),
        "r52_helper_current_received_snapshot_refs": r52_refs,
        "r52_helper_current_received_snapshot_ref_count": len(r52_refs),
        "source_delta_rows": rows,
        "source_delta_row_count": len(rows),
        "r51_helper_refs_are_current_received_refs": False,
        "r52_helper_refs_are_current_received_refs": False,
        "r53_current_received_refs_frozen": True,
        "old_refs_allowed_as_actual_review_basis": False,
        "r51_old_refs_allowed_as_actual_review_basis": False,
        "r52_old_refs_allowed_as_actual_review_basis": False,
        "r51_builder_snapshot_override_required": True,
        "current_snapshot_can_override_r51_builder_snapshot_refs": True,
        "r51_helper_refs_can_be_used_for_helper_regression_only": True,
        "r52_helper_refs_can_be_used_for_helper_regression_only": True,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "implemented_steps": list(P7_R53_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R1_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_r51_r52_helper_source_delta_freeze_contract(freeze)
    return freeze


def assert_p7_r53_r51_r52_helper_source_delta_freeze_contract(freeze: Mapping[str, Any]) -> bool:
    data = safe_mapping(freeze)
    _assert_required_fields(
        data,
        required=P7_R53_R51_R52_SOURCE_DELTA_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r53_r1_r51_r52_helper_source_delta_freeze",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION,
        source="p7_r53_r1_r51_r52_helper_source_delta_freeze",
    )
    if data.get("policy_section") != "R53-1_r51_r52_helper_source_delta_freeze":
        raise ValueError("R53 R1 policy section changed")
    if data.get("r0_refreeze_schema_version") != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION:
        raise ValueError("R53 R1 R0 schema reference changed")
    _assert_current_refs(data, source="p7_r53_r1_r51_r52_helper_source_delta_freeze")
    rows = data.get("source_delta_rows")
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("R53 R1 source delta rows changed")
    for row in rows:
        assert_p7_r53_source_delta_row_contract(safe_mapping(row))
    if [row.get("helper_ref_group") for row in rows] != [
        "r51_helper_source_snapshot_refs",
        "r52_helper_current_received_snapshot_refs",
    ]:
        raise ValueError("R53 R1 source delta row order changed")
    if data.get("source_delta_row_count") != 2:
        raise ValueError("R53 R1 source delta row count changed")
    for false_key in (
        "old_refs_allowed_as_actual_review_basis",
        "r51_old_refs_allowed_as_actual_review_basis",
        "r52_old_refs_allowed_as_actual_review_basis",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R1 must keep {false_key}=False")
    for true_key in (
        "r53_current_received_refs_frozen",
        "r51_builder_snapshot_override_required",
        "current_snapshot_can_override_r51_builder_snapshot_refs",
        "r51_helper_refs_can_be_used_for_helper_regression_only",
        "r52_helper_refs_can_be_used_for_helper_regression_only",
        "r53_0_scope_current_received_snapshot_refrozen",
        "r53_1_r51_r52_helper_source_delta_frozen",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R1 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_IMPLEMENTED_STEPS:
        raise ValueError("R53 R1 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R1 not-yet steps changed")
    if data.get("next_required_step") != P7_R53_R1_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R53 R1 must point to R53-2")
    return True

# Compatibility aliases matching the shorter R53-1 design wording.
build_p7_r53_r51_r52_source_delta_freeze = build_p7_r53_r51_r52_helper_source_delta_freeze
assert_p7_r53_r51_r52_source_delta_freeze_contract = assert_p7_r53_r51_r52_helper_source_delta_freeze_contract


P7_R53_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.validation_evidence_row.bodyfree.v1"
)
P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.validation_evidence_r49_timeout_preflight.bodyfree.v1"
)
P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.r51_r0_r1_adoption_current_snapshot_override.bodyfree.v1"
)

P7_R53_R2_NEXT_REQUIRED_STEP_REF: Final = "R53-3_r51_r0_r1_adoption_with_current_snapshot_override"
P7_R53_R3_NEXT_REQUIRED_STEP_REF: Final = "R53-4_explicit_allow_local_root_purge_plan_preflight"
P7_R53_R3_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-2_validation_evidence_before_R53-4_preflight"

P7_R53_R2_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_IMPLEMENTED_STEPS,
    "R53-2_r49_timeout_validation_evidence_preflight",
)
P7_R53_FUTURE_STEPS_AFTER_R3: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R1
    if step
    not in {
        "R53-2_r49_timeout_validation_evidence_preflight",
        "R53-3_r51_r0_r1_adoption_with_current_snapshot_override",
    }
)
P7_R53_R2_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-3_r51_r0_r1_adoption_with_current_snapshot_override",
    *P7_R53_FUTURE_STEPS_AFTER_R3,
)
P7_R53_R3_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R2_IMPLEMENTED_STEPS,
    "R53-3_r51_r0_r1_adoption_with_current_snapshot_override",
)
P7_R53_R3_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R3

P7_R53_R49_SPLIT_MATRIX_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r0_r1_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r2_r3_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r4_r5_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r6_r7_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r8_r9_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r10_r11_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r12_r13_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r14_r15_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r16_r17_20260619.py",
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r18_20260619.py",
)
P7_R53_R49_WILDCARD_BULK_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_*.py",
)
P7_R53_R50_TARGET_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_*.py",
)
P7_R53_R51_TARGET_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run_*.py",
)
P7_R53_R52_TARGET_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "tests/test_emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate_*.py",
)
P7_R53_RN_CONTRACT_TEST_FILE_REFS: Final[tuple[str, ...]] = (
    "Cocolon/tests/rn-screen-contracts.test.js",
)

P7_R53_VALIDATION_EVIDENCE_GROUP_REFS: Final[tuple[str, ...]] = (
    "r53_r0_r1_current_snapshot_source_delta",
    "r50_target",
    "r51_target",
    "r52_target",
    "r49_split_matrix",
    "r49_wildcard_bulk",
    "r48_regression",
    "r47_regression",
    "r46_display_p5_core_subset",
    "backend_collect_only",
    "rn_no_touch_optional",
)
P7_R53_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS: Final[tuple[str, ...]] = tuple(
    group_ref for group_ref in P7_R53_VALIDATION_EVIDENCE_GROUP_REFS if group_ref != "r49_wildcard_bulk"
)
P7_R53_OPTIONAL_VALIDATION_EVIDENCE_GROUP_REFS: Final[tuple[str, ...]] = (
    "r49_wildcard_bulk",
)

P7_R53_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "evidence_group_ref",
    "evidence_status_ref",
    "evidence_present",
    "passed_count",
    "collected_count",
    "warning_count",
    "timeout_unclassified",
    "required_for_actual_review_preflight",
    "optional",
    "test_file_refs",
    "evidence_source_ref",
    "claim_boundary_ref",
    "evidence_created_here",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "body_free",
)

P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r1_source_delta_schema_version",
    "r1_source_delta_material_ref",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_helper_source_snapshot_refs",
    "r51_helper_source_snapshot_ref_count",
    "r52_helper_current_received_snapshot_refs",
    "r52_helper_current_received_snapshot_ref_count",
    "r51_helper_refs_are_current_received_refs",
    "r52_helper_refs_are_current_received_refs",
    "validation_evidence_group_refs",
    "validation_evidence_required_group_refs",
    "validation_evidence_optional_group_refs",
    "validation_evidence_rows",
    "validation_evidence_row_count",
    "validation_evidence_required_groups_present",
    "r50_target_green_evidence_present",
    "r51_target_green_evidence_present",
    "r52_target_green_evidence_present",
    "r49_split_matrix_green_evidence_present",
    "r49_split_matrix_green_required_for_actual_review_preflight",
    "r49_wildcard_bulk_timeout_unclassified",
    "r49_wildcard_green_claim_allowed",
    "r49_wildcard_green_claimed",
    "r49_wildcard_bulk_required_for_actual_review_preflight",
    "r49_timeout_handling_claim_boundary_ref",
    "r48_regression_green_evidence_present",
    "r47_regression_green_evidence_present",
    "r46_display_p5_core_green_evidence_present",
    "rn_contract_green_evidence_present",
    "backend_collect_only_evidence_present",
    "full_backend_suite_green_confirmed",
    "backend_collect_only_claimed_as_full_backend_green",
    "rn_contract_claimed_as_real_device_modal_readfeel",
    "validation_commands_executed_here",
    "command_result_body_stored_here",
    "terminal_output_stored_here",
    "actual_review_generation_allowed_after_r53_2",
    "body_full_packet_generation_allowed_after_r53_2",
    "r51_2_local_root_preflight_allowed_after_r53_2",
    "r51_r0_r1_adoption_with_current_snapshot_override_allowed",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "preflight_status",
    "validation_evidence_ready_for_r51_2_preflight",
    "execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r2_preflight_schema_version",
    "r2_preflight_material_ref",
    "r2_preflight_status",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_default_source_snapshot_refs",
    "r51_default_source_snapshot_ref_count",
    "r51_current_source_refreeze_schema_version",
    "r51_validation_evidence_schema_version",
    "r51_r0_material_ref",
    "r51_r1_material_ref",
    "r51_r0_source_snapshot_refs",
    "r51_r0_source_snapshot_ref_count",
    "r51_r0_uses_r53_current_snapshot_refs",
    "r51_r0_uses_r51_default_source_refs",
    "r51_default_source_refs_allowed_as_actual_review_basis",
    "r51_r0_current_snapshot_override_applied",
    "r51_r1_validation_evidence_required_groups_present",
    "r51_r1_r49_split_matrix_green_evidence_present",
    "r51_r1_r49_wildcard_bulk_timeout_unclassified",
    "r51_r1_r49_wildcard_green_claim_allowed",
    "r51_r1_full_backend_suite_green_confirmed",
    "r51_r1_collect_only_claimed_as_full_backend_green",
    "r51_r1_validation_evidence_ready_for_r51_2_preflight",
    "r51_r1_execution_blocker_ids",
    "r51_r1_next_required_step",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "adoption_status",
    "r51_2_local_root_preflight_allowed_after_r53_3",
    "body_full_packet_generation_allowed_after_r53_3",
    "actual_review_generation_allowed_after_r53_3",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def _safe_non_negative_int_r53(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed >= 0 else 0


def _safe_bool_r53(value: Any, *, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _r53_evidence_row(
    *,
    evidence_group_ref: str,
    evidence_status_ref: str,
    evidence_present: bool,
    passed_count: int = 0,
    collected_count: int = 0,
    warning_count: int = 0,
    timeout_unclassified: bool = False,
    required_for_actual_review_preflight: bool = True,
    optional: bool = False,
    test_file_refs: Sequence[Any] = (),
    evidence_source_ref: str = "p7_r53_validation_evidence_preflight",
    claim_boundary_ref: str = "validation evidence only",
) -> dict[str, Any]:
    row = {
        "schema_version": P7_R53_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION,
        "evidence_group_ref": clean_identifier(evidence_group_ref, default="unknown_evidence_group", max_length=140),
        "evidence_status_ref": clean_identifier(evidence_status_ref, default="UNKNOWN", max_length=120),
        "evidence_present": bool(evidence_present),
        "passed_count": _safe_non_negative_int_r53(passed_count),
        "collected_count": _safe_non_negative_int_r53(collected_count),
        "warning_count": _safe_non_negative_int_r53(warning_count),
        "timeout_unclassified": bool(timeout_unclassified),
        "required_for_actual_review_preflight": bool(required_for_actual_review_preflight),
        "optional": bool(optional),
        "test_file_refs": dedupe_identifiers(test_file_refs, limit=90, max_length=300),
        "evidence_source_ref": clean_identifier(evidence_source_ref, default="p7_r53_validation_evidence_preflight", max_length=260),
        "claim_boundary_ref": clean_identifier(claim_boundary_ref, default="validation evidence only", max_length=300),
        "evidence_created_here": False,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "body_free": True,
    }
    assert_p7_r53_validation_evidence_row_contract(row)
    return row


def _default_r53_validation_evidence_rows() -> list[dict[str, Any]]:
    return [
        _r53_evidence_row(
            evidence_group_ref="r53_r0_r1_current_snapshot_source_delta",
            evidence_status_ref="PASSED_BODYFREE_TARGET",
            evidence_present=True,
            passed_count=42,
            test_file_refs=("tests/test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r0_r1_20260621.py",),
            evidence_source_ref="R53_R0_R1_current_received_snapshot_and_delta_target",
            claim_boundary_ref="R53-0/R53-1 body-free helper target only; not actual review or product value",
        ),
        _r53_evidence_row(
            evidence_group_ref="r50_target",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=99,
            test_file_refs=P7_R53_R50_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R53_pre_design_memo_and_local_regression_evidence",
            claim_boundary_ref="R50 target helper only; not P5 actual human review completion",
        ),
        _r53_evidence_row(
            evidence_group_ref="r51_target",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=125,
            test_file_refs=P7_R53_R51_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R53_pre_design_memo_and_local_regression_evidence",
            claim_boundary_ref="R51 target helper only; actual body-full review still not run",
        ),
        _r53_evidence_row(
            evidence_group_ref="r52_target",
            evidence_status_ref="PASSED",
            evidence_present=True,
            passed_count=219,
            test_file_refs=P7_R53_R52_TARGET_TEST_FILE_REFS,
            evidence_source_ref="R53_pre_design_memo_and_local_regression_evidence",
            claim_boundary_ref="R52 decision gate helper only; not P6/P8 start or release readiness",
        ),
        _r53_evidence_row(
            evidence_group_ref="r49_split_matrix",
            evidence_status_ref="MISSING_CURRENT_SESSION_COMPLETE_GREEN_EVIDENCE",
            evidence_present=False,
            passed_count=0,
            test_file_refs=P7_R53_R49_SPLIT_MATRIX_TEST_FILE_REFS,
            evidence_source_ref="R53_current_session_split_recheck_timeout_unclassified",
            claim_boundary_ref="R49 split matrix must be complete green before body-full generation; partial dots or timeout are not green evidence",
        ),
        _r53_evidence_row(
            evidence_group_ref="r49_wildcard_bulk",
            evidence_status_ref="TIMEOUT_UNCLASSIFIED",
            evidence_present=True,
            passed_count=0,
            timeout_unclassified=True,
            required_for_actual_review_preflight=False,
            optional=True,
            test_file_refs=P7_R53_R49_WILDCARD_BULK_TEST_FILE_REFS,
            evidence_source_ref="R53_current_session_wildcard_timeout_unclassified",
            claim_boundary_ref="wildcard bulk timeout remains visible uncertainty; never a green claim",
        ),
        _r53_evidence_row(
            evidence_group_ref="r48_regression",
            evidence_status_ref="PASSED_PRIOR_R51_EVIDENCE",
            evidence_present=True,
            passed_count=82,
            test_file_refs=("tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_*.py",),
            evidence_source_ref="R51_prior_validation_evidence_reused_as_regression_context_only",
            claim_boundary_ref="R48 regression context only; not current actual review evidence",
        ),
        _r53_evidence_row(
            evidence_group_ref="r47_regression",
            evidence_status_ref="PASSED_PRIOR_R51_EVIDENCE",
            evidence_present=True,
            passed_count=275,
            test_file_refs=("tests/test_emlis_ai_p7_r47_local_review_packet_policy_*.py",),
            evidence_source_ref="R51_prior_validation_evidence_reused_as_regression_context_only",
            claim_boundary_ref="R47 local-only policy regression context only",
        ),
        _r53_evidence_row(
            evidence_group_ref="r46_display_p5_core_subset",
            evidence_status_ref="PASSED_WITH_KNOWN_WARNING_PRIOR_R51_EVIDENCE",
            evidence_present=True,
            passed_count=94,
            warning_count=1,
            test_file_refs=(
                "tests/test_emlis_ai_p7_r46_display_contract_p5p6_return_*.py",
                "tests/test_emlis_ai_display_contract.py",
                "tests/test_emlis_ai_user_label_connection_*.py",
            ),
            evidence_source_ref="R51_prior_validation_evidence_reused_as_regression_context_only",
            claim_boundary_ref="display/P5 core regression context only; not real-device modal readfeel",
        ),
        _r53_evidence_row(
            evidence_group_ref="backend_collect_only",
            evidence_status_ref="COLLECT_ONLY_PASSED_WITH_KNOWN_WARNING",
            evidence_present=True,
            collected_count=3810,
            warning_count=1,
            test_file_refs=("pytest --collect-only -q",),
            evidence_source_ref="R53_pre_design_memo_collect_only_evidence",
            claim_boundary_ref="collect-only only; must not be claimed as full backend suite execution green",
        ),
        _r53_evidence_row(
            evidence_group_ref="rn_no_touch_optional",
            evidence_status_ref="PASSED_OPTIONAL_NO_TOUCH",
            evidence_present=True,
            passed_count=36,
            optional=False,
            test_file_refs=P7_R53_RN_CONTRACT_TEST_FILE_REFS,
            evidence_source_ref="R53_pre_design_memo_rn_contract_evidence",
            claim_boundary_ref="RN contract only; not real-device modal readfeel",
        ),
    ]


def _r53_validation_evidence_rows_with_overrides(overrides: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows = _default_r53_validation_evidence_rows()
    override_map = safe_mapping(overrides)
    if not override_map:
        return rows
    out: list[dict[str, Any]] = []
    for row in rows:
        group_ref = str(row["evidence_group_ref"])
        patch = safe_mapping(override_map.get(group_ref))
        if not patch:
            out.append(row)
            continue
        merged = dict(row)
        for key in (
            "evidence_status_ref",
            "evidence_present",
            "passed_count",
            "collected_count",
            "warning_count",
            "timeout_unclassified",
            "required_for_actual_review_preflight",
            "optional",
            "test_file_refs",
            "evidence_source_ref",
            "claim_boundary_ref",
        ):
            if key in patch:
                merged[key] = patch[key]
        refs = merged.get("test_file_refs")
        out.append(
            _r53_evidence_row(
                evidence_group_ref=group_ref,
                evidence_status_ref=clean_identifier(merged.get("evidence_status_ref"), default="UNKNOWN", max_length=120),
                evidence_present=_safe_bool_r53(merged.get("evidence_present")),
                passed_count=_safe_non_negative_int_r53(merged.get("passed_count")),
                collected_count=_safe_non_negative_int_r53(merged.get("collected_count")),
                warning_count=_safe_non_negative_int_r53(merged.get("warning_count")),
                timeout_unclassified=_safe_bool_r53(merged.get("timeout_unclassified")),
                required_for_actual_review_preflight=_safe_bool_r53(merged.get("required_for_actual_review_preflight"), default=True),
                optional=_safe_bool_r53(merged.get("optional")),
                test_file_refs=refs if isinstance(refs, Sequence) else row["test_file_refs"],
                evidence_source_ref=clean_identifier(merged.get("evidence_source_ref"), default="p7_r53_validation_evidence_preflight", max_length=260),
                claim_boundary_ref=clean_identifier(merged.get("claim_boundary_ref"), default="validation evidence only", max_length=300),
            )
        )
    return out


def _r53_validation_flags(rows: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    by_group = {str(row.get("evidence_group_ref")): row for row in rows}
    required_present = all(
        by_group.get(group_ref, {}).get("evidence_present") is True
        for group_ref in P7_R53_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS
    )
    return {
        "validation_evidence_required_groups_present": required_present,
        "r50_target_green_evidence_present": by_group.get("r50_target", {}).get("evidence_present") is True,
        "r51_target_green_evidence_present": by_group.get("r51_target", {}).get("evidence_present") is True,
        "r52_target_green_evidence_present": by_group.get("r52_target", {}).get("evidence_present") is True,
        "r49_split_matrix_green_evidence_present": by_group.get("r49_split_matrix", {}).get("evidence_present") is True,
        "r49_wildcard_bulk_timeout_unclassified": by_group.get("r49_wildcard_bulk", {}).get("timeout_unclassified") is True,
        "r48_regression_green_evidence_present": by_group.get("r48_regression", {}).get("evidence_present") is True,
        "r47_regression_green_evidence_present": by_group.get("r47_regression", {}).get("evidence_present") is True,
        "r46_display_p5_core_green_evidence_present": by_group.get("r46_display_p5_core_subset", {}).get("evidence_present") is True,
        "rn_contract_green_evidence_present": by_group.get("rn_no_touch_optional", {}).get("evidence_present") is True,
        "backend_collect_only_evidence_present": by_group.get("backend_collect_only", {}).get("evidence_present") is True,
        "full_backend_suite_green_confirmed": False,
        "backend_collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
    }


def _r53_validation_execution_blockers(flags: Mapping[str, Any]) -> list[str]:
    blockers: list[str] = []
    if flags.get("r50_target_green_evidence_present") is not True:
        blockers.append("r53_missing_r50_target_green_evidence")
    if flags.get("r51_target_green_evidence_present") is not True:
        blockers.append("r53_missing_r51_target_green_evidence")
    if flags.get("r52_target_green_evidence_present") is not True:
        blockers.append("r53_missing_r52_target_green_evidence")
    if flags.get("r49_split_matrix_green_evidence_present") is not True:
        blockers.append("r53_missing_r49_split_green_evidence")
    if flags.get("r48_regression_green_evidence_present") is not True:
        blockers.append("r53_missing_r48_regression_green_evidence")
    if flags.get("r47_regression_green_evidence_present") is not True:
        blockers.append("r53_missing_r47_regression_green_evidence")
    if flags.get("r46_display_p5_core_green_evidence_present") is not True:
        blockers.append("r53_missing_r46_display_p5_core_green_evidence")
    if flags.get("backend_collect_only_evidence_present") is not True:
        blockers.append("r53_missing_backend_collect_only_evidence")
    if flags.get("rn_contract_green_evidence_present") is not True:
        blockers.append("r53_missing_rn_contract_green_evidence")
    return blockers


def _r53_evidence_row_by_group(preflight: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = preflight.get("validation_evidence_rows")
    if not isinstance(rows, list):
        return {}
    return {str(safe_mapping(row).get("evidence_group_ref")): safe_mapping(row) for row in rows}


def _r51_validation_overrides_from_r53_preflight(preflight: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows_by_group = _r53_evidence_row_by_group(preflight)

    def patch_from(group_ref: str) -> dict[str, Any]:
        row = safe_mapping(rows_by_group.get(group_ref))
        return {
            "evidence_status_ref": row.get("evidence_status_ref", "UNKNOWN"),
            "evidence_present": row.get("evidence_present", False),
            "passed_count": row.get("passed_count", 0),
            "collected_count": row.get("collected_count", 0),
            "warning_count": row.get("warning_count", 0),
            "timeout_unclassified": row.get("timeout_unclassified", False),
            "required_for_r51_2_preflight": row.get("required_for_actual_review_preflight", True),
            "optional": row.get("optional", False),
            "test_file_refs": row.get("test_file_refs", ()),
            "evidence_source_ref": row.get("evidence_source_ref", "p7_r53_validation_evidence_preflight"),
            "claim_boundary_ref": row.get("claim_boundary_ref", "validation evidence only"),
        }

    overrides: dict[str, dict[str, Any]] = {
        "r51_r0_current_source_r50_handoff": {
            "evidence_status_ref": "REFROZEN_BODYFREE_WITH_R53_CURRENT_SNAPSHOT_OVERRIDE",
            "evidence_present": True,
            "passed_count": 0,
            "test_file_refs": ("tests/test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r2_r3_20260621.py",),
            "evidence_source_ref": "R53_R3_current_snapshot_override_adoption",
            "claim_boundary_ref": "R51-0 builder adopted with R53 current snapshot; not actual review or product value",
        },
        "r50_target": patch_from("r50_target"),
        "r49_split_matrix": patch_from("r49_split_matrix"),
        "r49_wildcard_bulk": patch_from("r49_wildcard_bulk"),
        "r48_regression": patch_from("r48_regression"),
        "r47_regression": patch_from("r47_regression"),
        "r46_display_p5_core_subset": patch_from("r46_display_p5_core_subset"),
        "backend_collect_only": patch_from("backend_collect_only"),
        "rn_no_touch_optional": patch_from("rn_no_touch_optional"),
    }
    return {group_ref: overrides[group_ref] for group_ref in P7_R51_VALIDATION_EVIDENCE_GROUP_REFS}


def assert_p7_r53_validation_evidence_row_contract(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R53_VALIDATION_EVIDENCE_ROW_REQUIRED_FIELD_REFS,
        source="p7_r53_validation_evidence_row",
    )
    if data.get("schema_version") != P7_R53_VALIDATION_EVIDENCE_ROW_SCHEMA_VERSION:
        raise ValueError("R53 validation evidence row schema version changed")
    group_ref = data.get("evidence_group_ref")
    if group_ref not in P7_R53_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R53 validation evidence group ref is not canonical")
    for int_key in ("passed_count", "collected_count", "warning_count"):
        if not isinstance(data.get(int_key), int) or data[int_key] < 0:
            raise ValueError(f"R53 validation evidence row must keep non-negative {int_key}")
    for bool_key in (
        "evidence_present",
        "timeout_unclassified",
        "required_for_actual_review_preflight",
        "optional",
        "evidence_created_here",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "body_free",
    ):
        if not isinstance(data.get(bool_key), bool):
            raise ValueError(f"R53 validation evidence row must keep boolean {bool_key}")
    if group_ref == "r49_wildcard_bulk":
        if data.get("timeout_unclassified") is not True:
            raise ValueError("R53 R49 wildcard bulk row must preserve timeout_unclassified=True")
        if data.get("required_for_actual_review_preflight") is not False:
            raise ValueError("R53 R49 wildcard bulk timeout must not be required for actual review preflight")
        if data.get("evidence_status_ref") != "TIMEOUT_UNCLASSIFIED":
            raise ValueError("R53 R49 wildcard bulk status must remain TIMEOUT_UNCLASSIFIED")
    else:
        if data.get("timeout_unclassified") is not False:
            raise ValueError("R53 non-wildcard rows must not carry timeout_unclassified")
    if group_ref in P7_R53_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS and data.get("optional") is not False:
        raise ValueError("R53 required validation rows must not be optional")
    if group_ref in P7_R53_OPTIONAL_VALIDATION_EVIDENCE_GROUP_REFS and data.get("optional") is not True:
        raise ValueError("R53 optional validation rows must be optional")
    for false_key in ("evidence_created_here", "validation_commands_executed_here", "command_result_body_stored_here", "terminal_output_stored_here"):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 validation evidence row must keep {false_key}=False")
    if data.get("body_free") is not True:
        raise ValueError("R53 validation evidence row must be body-free")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_validation_evidence_row")
    return True


def build_p7_r53_validation_evidence_r49_timeout_preflight(
    *,
    source_delta_freeze: Mapping[str, Any] | None = None,
    r51_r52_source_delta_freeze: Mapping[str, Any] | None = None,
    validation_evidence_overrides: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_validation_evidence_r49_timeout_preflight",
) -> dict[str, Any]:
    """Build R53-2 validation-evidence preflight with R49 timeout kept visible."""

    if source_delta_freeze is not None and r51_r52_source_delta_freeze is not None:
        raise ValueError("provide only one R53-1 source delta freeze value")
    r1 = (
        safe_mapping(source_delta_freeze)
        if source_delta_freeze is not None
        else safe_mapping(r51_r52_source_delta_freeze)
        if r51_r52_source_delta_freeze is not None
        else build_p7_r53_r51_r52_helper_source_delta_freeze()
    )
    assert_p7_r53_r51_r52_helper_source_delta_freeze_contract(r1)
    current_refs = safe_mapping(r1.get("current_received_snapshot_refs"))
    rows = _r53_validation_evidence_rows_with_overrides(validation_evidence_overrides)
    flags = _r53_validation_flags(rows)
    blockers = _r53_validation_execution_blockers(flags)
    ready_for_r51_2 = flags["validation_evidence_required_groups_present"] and not blockers
    preflight = {
        "schema_version": P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-2_r49_timeout_validation_evidence_preflight",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_validation_evidence_r49_timeout_preflight", max_length=180),
        "review_session_id": _safe_review_session_id(r1.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r1_source_delta_schema_version": P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION,
        "r1_source_delta_material_ref": clean_identifier(r1.get("material_id"), default="p7_r53_r51_r52_helper_source_delta_freeze", max_length=180),
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r51_helper_source_snapshot_refs": safe_mapping(r1.get("r51_helper_source_snapshot_refs")),
        "r51_helper_source_snapshot_ref_count": len(safe_mapping(r1.get("r51_helper_source_snapshot_refs"))),
        "r52_helper_current_received_snapshot_refs": safe_mapping(r1.get("r52_helper_current_received_snapshot_refs")),
        "r52_helper_current_received_snapshot_ref_count": len(safe_mapping(r1.get("r52_helper_current_received_snapshot_refs"))),
        "r51_helper_refs_are_current_received_refs": False,
        "r52_helper_refs_are_current_received_refs": False,
        "validation_evidence_group_refs": list(P7_R53_VALIDATION_EVIDENCE_GROUP_REFS),
        "validation_evidence_required_group_refs": list(P7_R53_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS),
        "validation_evidence_optional_group_refs": list(P7_R53_OPTIONAL_VALIDATION_EVIDENCE_GROUP_REFS),
        "validation_evidence_rows": rows,
        "validation_evidence_row_count": len(rows),
        "validation_evidence_required_groups_present": flags["validation_evidence_required_groups_present"],
        "r50_target_green_evidence_present": flags["r50_target_green_evidence_present"],
        "r51_target_green_evidence_present": flags["r51_target_green_evidence_present"],
        "r52_target_green_evidence_present": flags["r52_target_green_evidence_present"],
        "r49_split_matrix_green_evidence_present": flags["r49_split_matrix_green_evidence_present"],
        "r49_split_matrix_green_required_for_actual_review_preflight": True,
        "r49_wildcard_bulk_timeout_unclassified": flags["r49_wildcard_bulk_timeout_unclassified"],
        "r49_wildcard_green_claim_allowed": False,
        "r49_wildcard_green_claimed": False,
        "r49_wildcard_bulk_required_for_actual_review_preflight": False,
        "r49_timeout_handling_claim_boundary_ref": "r49_split_green_required_wildcard_timeout_visible_not_green_claim",
        "r48_regression_green_evidence_present": flags["r48_regression_green_evidence_present"],
        "r47_regression_green_evidence_present": flags["r47_regression_green_evidence_present"],
        "r46_display_p5_core_green_evidence_present": flags["r46_display_p5_core_green_evidence_present"],
        "rn_contract_green_evidence_present": flags["rn_contract_green_evidence_present"],
        "backend_collect_only_evidence_present": flags["backend_collect_only_evidence_present"],
        "full_backend_suite_green_confirmed": False,
        "backend_collect_only_claimed_as_full_backend_green": False,
        "rn_contract_claimed_as_real_device_modal_readfeel": False,
        "validation_commands_executed_here": False,
        "command_result_body_stored_here": False,
        "terminal_output_stored_here": False,
        "actual_review_generation_allowed_after_r53_2": False,
        "body_full_packet_generation_allowed_after_r53_2": False,
        "r51_2_local_root_preflight_allowed_after_r53_2": ready_for_r51_2,
        "r51_r0_r1_adoption_with_current_snapshot_override_allowed": True,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "preflight_status": "PASSED" if ready_for_r51_2 else "BLOCKED",
        "validation_evidence_ready_for_r51_2_preflight": ready_for_r51_2,
        "execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R53_R2_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R2_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R2_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(preflight)
    return preflight


def assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(preflight: Mapping[str, Any]) -> bool:
    data = safe_mapping(preflight)
    _assert_required_fields(
        data,
        required=P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="p7_r53_r2_validation_evidence_r49_timeout_preflight",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_SCHEMA_VERSION,
        source="p7_r53_r2_validation_evidence_r49_timeout_preflight",
    )
    if data.get("policy_section") != "R53-2_r49_timeout_validation_evidence_preflight":
        raise ValueError("R53 R2 policy section changed")
    if data.get("r1_source_delta_schema_version") != P7_R53_R51_R52_SOURCE_DELTA_FREEZE_SCHEMA_VERSION:
        raise ValueError("R53 R2 R1 schema reference changed")
    _assert_current_refs(data, source="p7_r53_r2_validation_evidence_r49_timeout_preflight")
    rows = data.get("validation_evidence_rows")
    if not isinstance(rows, list) or len(rows) != len(P7_R53_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R53 R2 validation evidence rows changed")
    for row in rows:
        assert_p7_r53_validation_evidence_row_contract(safe_mapping(row))
    if [row.get("evidence_group_ref") for row in rows] != list(P7_R53_VALIDATION_EVIDENCE_GROUP_REFS):
        raise ValueError("R53 R2 validation evidence row order changed")
    if tuple(data.get("validation_evidence_group_refs") or ()) != P7_R53_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R53 R2 validation evidence group refs changed")
    if tuple(data.get("validation_evidence_required_group_refs") or ()) != P7_R53_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS:
        raise ValueError("R53 R2 required evidence group refs changed")
    if tuple(data.get("validation_evidence_optional_group_refs") or ()) != P7_R53_OPTIONAL_VALIDATION_EVIDENCE_GROUP_REFS:
        raise ValueError("R53 R2 optional evidence group refs changed")
    flags = _r53_validation_flags([safe_mapping(row) for row in rows])
    for key, value in flags.items():
        if data.get(key) is not value:
            raise ValueError(f"R53 R2 top-level flag mismatch for {key}")
    blockers = _r53_validation_execution_blockers(flags)
    if tuple(data.get("execution_blocker_ids") or ()) != tuple(blockers):
        raise ValueError("R53 R2 execution blockers do not match validation flags")
    ready = flags["validation_evidence_required_groups_present"] and not blockers
    if data.get("validation_evidence_ready_for_r51_2_preflight") is not ready:
        raise ValueError("R53 R2 readiness does not match validation evidence")
    if data.get("preflight_status") != ("PASSED" if ready else "BLOCKED"):
        raise ValueError("R53 R2 preflight status does not match readiness")
    if data.get("r51_2_local_root_preflight_allowed_after_r53_2") is not ready:
        raise ValueError("R53 R2 local-root preflight allowance must match readiness")
    if data.get("r51_r0_r1_adoption_with_current_snapshot_override_allowed") is not True:
        raise ValueError("R53 R2 must allow R51 R0/R1 adoption materialization")
    for false_key in (
        "r49_wildcard_green_claim_allowed",
        "r49_wildcard_green_claimed",
        "r49_wildcard_bulk_required_for_actual_review_preflight",
        "full_backend_suite_green_confirmed",
        "backend_collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "validation_commands_executed_here",
        "command_result_body_stored_here",
        "terminal_output_stored_here",
        "actual_review_generation_allowed_after_r53_2",
        "body_full_packet_generation_allowed_after_r53_2",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R2 must keep {false_key}=False")
    for true_key in (
        "r49_split_matrix_green_required_for_actual_review_preflight",
        "r49_wildcard_bulk_timeout_unclassified",
        "r53_0_scope_current_received_snapshot_refrozen",
        "r53_1_r51_r52_helper_source_delta_frozen",
        "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R2 must keep {true_key}=True")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R2_IMPLEMENTED_STEPS:
        raise ValueError("R53 R2 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R2_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R2 not-yet steps changed")
    if data.get("next_required_step") != P7_R53_R2_NEXT_REQUIRED_STEP_REF:
        raise ValueError("R53 R2 must point to R53-3")
    return True


def build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override(
    *,
    validation_evidence_preflight: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_r51_r0_r1_adoption_with_current_snapshot_override",
) -> dict[str, Any]:
    """Build R53-3 by adopting R51 R0/R1 with the R53 current snapshot override."""

    r2 = safe_mapping(validation_evidence_preflight) if validation_evidence_preflight is not None else build_p7_r53_validation_evidence_r49_timeout_preflight()
    assert_p7_r53_validation_evidence_r49_timeout_preflight_contract(r2)
    current_refs = safe_mapping(r2.get("current_received_snapshot_refs"))
    r51_r0 = build_p7_r51_current_source_r50_handoff_refreeze(
        snapshot_refs=current_refs,
        review_session_id=_safe_review_session_id(r2.get("review_session_id")),
        material_id="p7_r53_adopted_r51_r0_current_snapshot_override",
    )
    assert_p7_r51_current_source_r50_handoff_refreeze_contract(r51_r0)
    r51_r1 = build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
        current_source_r50_handoff_refreeze=r51_r0,
        validation_evidence_overrides=_r51_validation_overrides_from_r53_preflight(r2),
        material_id="p7_r53_adopted_r51_r1_validation_evidence_with_current_snapshot_override",
    )
    assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract(r51_r1)
    ready_for_r51_2 = r51_r1.get("validation_evidence_ready_for_r51_2_preflight") is True
    adoption = {
        "schema_version": P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-3_r51_r0_r1_adoption_with_current_snapshot_override",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_r51_r0_r1_adoption_with_current_snapshot_override", max_length=180),
        "review_session_id": _safe_review_session_id(r2.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r2_preflight_schema_version": P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_SCHEMA_VERSION,
        "r2_preflight_material_ref": clean_identifier(r2.get("material_id"), default="p7_r53_validation_evidence_r49_timeout_preflight", max_length=180),
        "r2_preflight_status": clean_identifier(r2.get("preflight_status"), default="BLOCKED", max_length=80),
        "current_received_snapshot_refs": current_refs,
        "current_received_snapshot_ref_count": len(current_refs),
        "r51_default_source_snapshot_refs": dict(P7_R51_SOURCE_SNAPSHOT_REFS),
        "r51_default_source_snapshot_ref_count": len(P7_R51_SOURCE_SNAPSHOT_REFS),
        "r51_current_source_refreeze_schema_version": P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION,
        "r51_validation_evidence_schema_version": P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION,
        "r51_r0_material_ref": clean_identifier(r51_r0.get("material_id"), default="p7_r53_adopted_r51_r0_current_snapshot_override", max_length=180),
        "r51_r1_material_ref": clean_identifier(r51_r1.get("material_id"), default="p7_r53_adopted_r51_r1_validation_evidence_with_current_snapshot_override", max_length=180),
        "r51_r0_source_snapshot_refs": safe_mapping(r51_r0.get("source_snapshot_refs")),
        "r51_r0_source_snapshot_ref_count": len(safe_mapping(r51_r0.get("source_snapshot_refs"))),
        "r51_r0_uses_r53_current_snapshot_refs": _refs_match(safe_mapping(r51_r0.get("source_snapshot_refs")), current_refs),
        "r51_r0_uses_r51_default_source_refs": _refs_match(safe_mapping(r51_r0.get("source_snapshot_refs")), P7_R51_SOURCE_SNAPSHOT_REFS),
        "r51_default_source_refs_allowed_as_actual_review_basis": False,
        "r51_r0_current_snapshot_override_applied": True,
        "r51_r1_validation_evidence_required_groups_present": r51_r1.get("validation_evidence_required_groups_present") is True,
        "r51_r1_r49_split_matrix_green_evidence_present": r51_r1.get("r49_split_matrix_green_evidence_present") is True,
        "r51_r1_r49_wildcard_bulk_timeout_unclassified": r51_r1.get("r49_wildcard_bulk_timeout_unclassified") is True,
        "r51_r1_r49_wildcard_green_claim_allowed": r51_r1.get("r49_wildcard_green_claim_allowed") is True,
        "r51_r1_full_backend_suite_green_confirmed": r51_r1.get("full_backend_suite_green_confirmed") is True,
        "r51_r1_collect_only_claimed_as_full_backend_green": r51_r1.get("collect_only_claimed_as_full_backend_green") is True,
        "r51_r1_validation_evidence_ready_for_r51_2_preflight": ready_for_r51_2,
        "r51_r1_execution_blocker_ids": list(r51_r1.get("execution_blocker_ids") or []),
        "r51_r1_next_required_step": clean_identifier(r51_r1.get("next_required_step"), default=P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "adoption_status": "ADOPTED_READY_FOR_R53_4_PREFLIGHT" if ready_for_r51_2 else "ADOPTED_BLOCKED_BY_VALIDATION_EVIDENCE",
        "r51_2_local_root_preflight_allowed_after_r53_3": ready_for_r51_2,
        "body_full_packet_generation_allowed_after_r53_3": False,
        "actual_review_generation_allowed_after_r53_3": False,
        "implemented_steps": list(P7_R53_R3_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R3_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R3_NEXT_REQUIRED_STEP_REF if ready_for_r51_2 else P7_R53_R3_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption)
    return adoption


def assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(adoption: Mapping[str, Any]) -> bool:
    data = safe_mapping(adoption)
    _assert_required_fields(
        data,
        required=P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_REQUIRED_FIELD_REFS,
        source="p7_r53_r3_r51_r0_r1_adoption_current_snapshot_override",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_SCHEMA_VERSION,
        source="p7_r53_r3_r51_r0_r1_adoption_current_snapshot_override",
    )
    if data.get("policy_section") != "R53-3_r51_r0_r1_adoption_with_current_snapshot_override":
        raise ValueError("R53 R3 policy section changed")
    if data.get("r2_preflight_schema_version") != P7_R53_VALIDATION_EVIDENCE_R49_TIMEOUT_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("R53 R3 R2 schema reference changed")
    current_refs = safe_mapping(data.get("current_received_snapshot_refs"))
    if current_refs != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R3 current refs changed")
    r51_r0_refs = safe_mapping(data.get("r51_r0_source_snapshot_refs"))
    if r51_r0_refs != current_refs:
        raise ValueError("R53 R3 must adopt R51 R0 with R53 current snapshot refs")
    if r51_r0_refs == P7_R51_SOURCE_SNAPSHOT_REFS:
        raise ValueError("R53 R3 must not use R51 default source refs as actual-review basis")
    if safe_mapping(data.get("r51_default_source_snapshot_refs")) != P7_R51_SOURCE_SNAPSHOT_REFS:
        raise ValueError("R53 R3 R51 default source refs changed")
    for true_key in (
        "r51_r0_uses_r53_current_snapshot_refs",
        "r51_r0_current_snapshot_override_applied",
        "r51_r1_r49_wildcard_bulk_timeout_unclassified",
        "r53_0_scope_current_received_snapshot_refrozen",
        "r53_1_r51_r52_helper_source_delta_frozen",
        "r53_2_r49_timeout_validation_evidence_preflight_frozen",
        "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R3 must keep {true_key}=True")
    for false_key in (
        "r51_r0_uses_r51_default_source_refs",
        "r51_default_source_refs_allowed_as_actual_review_basis",
        "r51_r1_r49_wildcard_green_claim_allowed",
        "r51_r1_full_backend_suite_green_confirmed",
        "r51_r1_collect_only_claimed_as_full_backend_green",
        "body_full_packet_generation_allowed_after_r53_3",
        "actual_review_generation_allowed_after_r53_3",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R3 must keep {false_key}=False")
    ready = data.get("r51_r1_validation_evidence_ready_for_r51_2_preflight") is True
    if data.get("r51_2_local_root_preflight_allowed_after_r53_3") is not ready:
        raise ValueError("R53 R3 local-root preflight allowance must match R51 R1 readiness")
    if ready:
        if data.get("r51_r1_execution_blocker_ids"):
            raise ValueError("R53 R3 ready adoption must not keep R51 execution blockers open")
        if data.get("r51_r1_validation_evidence_required_groups_present") is not True:
            raise ValueError("R53 R3 ready adoption requires R51 required validation groups present")
        if data.get("r51_r1_r49_split_matrix_green_evidence_present") is not True:
            raise ValueError("R53 R3 ready adoption requires R49 split green evidence")
        if data.get("adoption_status") != "ADOPTED_READY_FOR_R53_4_PREFLIGHT":
            raise ValueError("R53 R3 ready adoption status changed")
        if data.get("r51_r1_next_required_step") != P7_R51_R1_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R3 ready R51 R1 must point to R51-2")
        if data.get("next_required_step") != P7_R53_R3_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R3 ready adoption must point to R53-4")
    else:
        if data.get("adoption_status") != "ADOPTED_BLOCKED_BY_VALIDATION_EVIDENCE":
            raise ValueError("R53 R3 blocked adoption status changed")
        if data.get("r51_r1_next_required_step") != P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R3 blocked R51 R1 must point to validation resolution")
        if data.get("next_required_step") != P7_R53_R3_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R3 blocked adoption must point to R53-2 validation resolution")
        if not data.get("r51_r1_execution_blocker_ids"):
            raise ValueError("R53 R3 blocked adoption must keep R51 execution blockers visible")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R3_IMPLEMENTED_STEPS:
        raise ValueError("R53 R3 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R3_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R3 not-yet steps changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r3_r51_r0_r1_adoption_current_snapshot_override")
    return True


# Compatibility aliases matching the shorter R53-2/R53-3 design wording.
build_p7_r53_r49_timeout_validation_evidence_preflight = build_p7_r53_validation_evidence_r49_timeout_preflight
assert_p7_r53_r49_timeout_validation_evidence_preflight_contract = assert_p7_r53_validation_evidence_r49_timeout_preflight_contract
build_p7_r53_r51_r0_r1_current_snapshot_override_adoption = build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override
assert_p7_r53_r51_r0_r1_current_snapshot_override_adoption_contract = assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract


P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.local_root_explicit_allow_purge_plan_preflight.bodyfree.v1"
)
P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.actual_review_session_envelope.bodyfree.v1"
)

P7_R53_R4_NEXT_REQUIRED_STEP_REF: Final = "R53-5_actual_review_session_envelope"
P7_R53_R4_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-4_explicit_allow_local_root_purge_plan_preflight"
P7_R53_R5_NEXT_REQUIRED_STEP_REF: Final = "R53-6_24_case_manifest_freeze"
P7_R53_R5_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-4_explicit_allow_local_root_purge_plan_preflight_before_R53-5_envelope"

P7_R53_R4_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R3_IMPLEMENTED_STEPS,
    "R53-4_explicit_allow_local_root_purge_plan_preflight",
)
P7_R53_FUTURE_STEPS_AFTER_R5: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R3
    if step
    not in {
        "R53-4_explicit_allow_local_root_purge_plan_preflight",
        "R53-5_actual_review_session_envelope",
    }
)
P7_R53_R4_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-5_actual_review_session_envelope",
    *P7_R53_FUTURE_STEPS_AFTER_R5,
)
P7_R53_R5_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R4_IMPLEMENTED_STEPS,
    "R53-5_actual_review_session_envelope",
)
P7_R53_R5_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R5

P7_R53_R51_TO_R53_PREFLIGHT_BLOCKER_MAP: Final[dict[str, str]] = {
    "r51_missing_r50_target_green_evidence": "r53_missing_r50_target_green_evidence",
    "r51_missing_r49_split_green_evidence": "r53_missing_r49_split_green_evidence",
    "r51_missing_r48_regression_green_evidence": "r53_missing_r48_regression_green_evidence",
    "r51_missing_r47_regression_green_evidence": "r53_missing_r47_regression_green_evidence",
    "r51_missing_r46_display_p5_core_green_evidence": "r53_missing_r46_display_p5_core_green_evidence",
    "r51_missing_rn_contract_green_evidence": "r53_missing_rn_contract_green_evidence",
    "r51_missing_backend_collect_only_evidence": "r53_missing_backend_collect_only_evidence",
    "r51_validation_evidence_not_ready": "r53_validation_evidence_not_ready",
    "r51_local_review_root_missing": "r53_local_review_root_missing",
    "r51_local_review_root_invalid": "r53_local_review_root_invalid",
    "r51_explicit_allow_missing": "r53_explicit_allow_missing",
    "r51_disposal_plan_missing": "r53_disposal_plan_missing",
    "r51_body_full_packet_export_violation": "r53_export_denylist_violation",
    "r51_body_free_leak_detected": "r53_body_free_leak_detected",
}

P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r3_adoption_schema_version",
    "r3_adoption_material_ref",
    "r3_adoption_status",
    "r3_validation_ready_for_local_root_preflight",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_default_source_snapshot_refs",
    "r51_default_source_snapshot_ref_count",
    "r51_r0_source_snapshot_refs",
    "r51_r0_source_snapshot_ref_count",
    "r51_r0_uses_r53_current_snapshot_refs",
    "r51_default_source_refs_allowed_as_actual_review_basis",
    "r51_r2_preflight_schema_version",
    "r51_r2_preflight_material_ref",
    "r51_r2_preflight_bodyfree",
    "r51_r2_preflight_status",
    "r51_r2_next_required_step",
    "r51_r2_execution_blocker_ids",
    "required_case_count",
    "local_review_root_env_var",
    "local_review_root_source",
    "local_review_root_configured",
    "local_review_root_valid",
    "storage_root_ref",
    "root_path_exposed",
    "local_absolute_path_included",
    "explicit_allow_env_var",
    "explicit_allow_token_ref",
    "explicit_allow_present",
    "explicit_allow_token_body_stored_here",
    "purge_plan_ref",
    "purge_plan_present",
    "purge_plan_status",
    "purge_plan_ready",
    "purge_plan_reason_refs",
    "purge_plan_required_before_body_full_generation",
    "purge_plan_delete_target_refs",
    "purge_plan_required_delete_target_refs",
    "export_candidate_refs_checked_count",
    "export_denylist_violation_refs",
    "denied_export_candidate_count",
    "export_candidate_refs_stored_here",
    "export_candidate_body_stored_here",
    "body_full_packet_export_allowed",
    "reviewer_notes_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "premise_or_implemented_docs_inclusion_allowed",
    "local_only_body_full_generation_allowed_before_preflight",
    "local_only_body_full_generation_allowed_after_preflight",
    "local_only_body_full_generation_allowed",
    "actual_review_session_envelope_allowed_after_r53_4",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "preflight_status",
    "preflight_reason_refs",
    "manual_run_decision",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r4_preflight_schema_version",
    "r4_preflight_material_ref",
    "r4_preflight_status",
    "r4_preflight_ready_for_envelope",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r3_envelope_schema_version",
    "r51_r3_envelope_material_ref",
    "r51_r3_envelope_bodyfree",
    "r51_r3_envelope_status",
    "r51_r3_next_required_step",
    "r51_r3_execution_blocker_ids",
    "review_session_status",
    "envelope_status",
    "envelope_reason_refs",
    "required_case_count",
    "review_prompt_version",
    "reviewer_ref",
    "reviewer_ref_pseudonymous",
    "reviewer_blind_policy",
    "reviewer_visible_field_refs",
    "reviewer_hidden_field_refs",
    "local_root_ref",
    "root_path_exposed",
    "local_absolute_path_included",
    "body_full_generation_allowed",
    "local_only_body_full_generation_allowed",
    "body_full_packet_export_allowed",
    "reviewer_notes_export_allowed",
    "body_full_packet_zip_inclusion_allowed",
    "disposal_plan_ref",
    "disposal_plan_ready",
    "session_controller_material_refs",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "actual_review_session_envelope_bodyfree_materialized_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def build_p7_r53_default_local_only_purge_plan_bodyfree(
    *,
    purge_plan_ref: Any = "p7_r53_local_only_actual_review_purge_plan",
) -> dict[str, Any]:
    """Return an R53-scoped body-free purge plan descriptor; no files are created."""

    plan = build_p7_r51_default_local_only_purge_plan_bodyfree(
        purge_plan_ref=clean_identifier(purge_plan_ref, default="p7_r53_local_only_actual_review_purge_plan", max_length=180)
    )
    plan["purge_plan_ref"] = clean_identifier(plan.get("purge_plan_ref"), default="p7_r53_local_only_actual_review_purge_plan", max_length=180)
    assert_p7_no_body_payload_or_contract_mutation(plan, source="p7_r53_default_local_only_purge_plan_bodyfree")
    return plan


def _r53_map_r51_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (P7_R53_R51_TO_R53_PREFLIGHT_BLOCKER_MAP.get(str(blocker), str(blocker).replace("r51_", "r53_", 1)) for blocker in blocker_ids),
        limit=40,
        max_length=140,
    )


def _r53_preflight_reason_refs_from_r51(r51_reason_refs: Sequence[Any], r53_blocker_ids: Sequence[Any]) -> list[str]:
    reason_refs = [f"r53_{clean_identifier(ref, default='preflight_blocked', max_length=120)}" for ref in r51_reason_refs]
    if r53_blocker_ids and "r53_preflight_blockers_visible" not in reason_refs:
        reason_refs.append("r53_preflight_blockers_visible")
    if not reason_refs:
        reason_refs.append("r53_local_root_explicit_allow_purge_plan_preflight_passed")
    return dedupe_identifiers(reason_refs, limit=40, max_length=140)


def _r51_validation_overrides_from_r53_r3_adoption(adoption: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    split_green = adoption.get("r51_r1_r49_split_matrix_green_evidence_present") is True
    return {
        "r51_r0_current_source_r50_handoff": {
            "evidence_status_ref": "REFROZEN_BODYFREE_WITH_R53_CURRENT_SNAPSHOT_OVERRIDE",
            "evidence_present": True,
            "passed_count": 0,
            "test_file_refs": ("tests/test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r2_r3_20260621.py",),
            "evidence_source_ref": "R53_R3_current_snapshot_override_adoption_for_R53_R4",
            "claim_boundary_ref": "R51-0 builder adopted with R53 current snapshot; not actual review or product value",
        },
        "r50_target": {
            "evidence_status_ref": "PASSED",
            "evidence_present": True,
            "passed_count": 99,
            "test_file_refs": P7_R53_R50_TARGET_TEST_FILE_REFS,
            "evidence_source_ref": "R53_R4_preflight_regression_context",
            "claim_boundary_ref": "R50 target helper only; not P5 actual human review completion",
        },
        "r49_split_matrix": {
            "evidence_status_ref": "PASSED_BY_R53_CURRENT_SPLIT_EVIDENCE" if split_green else "MISSING_CURRENT_SESSION_COMPLETE_GREEN_EVIDENCE",
            "evidence_present": split_green,
            "passed_count": 76 if split_green else 0,
            "test_file_refs": P7_R53_R49_SPLIT_MATRIX_TEST_FILE_REFS,
            "evidence_source_ref": "R53_R3_split_green_override" if split_green else "R53_R3_split_green_missing",
            "claim_boundary_ref": "R49 split matrix green required before body-full generation; wildcard timeout is not green",
        },
        "r49_wildcard_bulk": {
            "evidence_status_ref": "TIMEOUT_UNCLASSIFIED",
            "evidence_present": True,
            "passed_count": 0,
            "timeout_unclassified": True,
            "required_for_r51_2_preflight": False,
            "optional": True,
            "test_file_refs": P7_R53_R49_WILDCARD_BULK_TEST_FILE_REFS,
            "evidence_source_ref": "R53_R4_wildcard_timeout_visible",
            "claim_boundary_ref": "wildcard bulk timeout remains visible uncertainty; never a green claim",
        },
        "r48_regression": {
            "evidence_status_ref": "PASSED_PRIOR_R51_EVIDENCE",
            "evidence_present": True,
            "passed_count": 82,
            "test_file_refs": ("tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_*.py",),
            "evidence_source_ref": "R51_prior_validation_evidence_reused_as_regression_context_only",
            "claim_boundary_ref": "R48 regression context only; not current actual review evidence",
        },
        "r47_regression": {
            "evidence_status_ref": "PASSED_PRIOR_R51_EVIDENCE",
            "evidence_present": True,
            "passed_count": 275,
            "test_file_refs": ("tests/test_emlis_ai_p7_r47_local_review_packet_policy_*.py",),
            "evidence_source_ref": "R51_prior_validation_evidence_reused_as_regression_context_only",
            "claim_boundary_ref": "R47 local-only policy regression context only",
        },
        "r46_display_p5_core_subset": {
            "evidence_status_ref": "PASSED_WITH_KNOWN_WARNING_PRIOR_R51_EVIDENCE",
            "evidence_present": True,
            "passed_count": 94,
            "warning_count": 1,
            "test_file_refs": ("tests/test_emlis_ai_p7_r46_display_contract_p5p6_return_*.py",),
            "evidence_source_ref": "R51_prior_validation_evidence_reused_as_regression_context_only",
            "claim_boundary_ref": "display/P5 core regression context only; not real-device modal readfeel",
        },
        "backend_collect_only": {
            "evidence_status_ref": "COLLECT_ONLY_PASSED_WITH_KNOWN_WARNING",
            "evidence_present": True,
            "collected_count": 3810,
            "warning_count": 1,
            "test_file_refs": ("pytest --collect-only -q",),
            "evidence_source_ref": "R53_R4_preflight_collect_only_context",
            "claim_boundary_ref": "collect-only only; must not be claimed as full backend suite execution green",
        },
        "rn_no_touch_optional": {
            "evidence_status_ref": "PASSED_OPTIONAL_NO_TOUCH",
            "evidence_present": True,
            "passed_count": 36,
            "optional": False,
            "test_file_refs": P7_R53_RN_CONTRACT_TEST_FILE_REFS,
            "evidence_source_ref": "R53_R4_preflight_rn_contract_context",
            "claim_boundary_ref": "RN contract only; not real-device modal readfeel",
        },
    }


def _r51_r1_from_r53_r3_adoption(adoption: Mapping[str, Any]) -> dict[str, Any]:
    r51_r0 = build_p7_r51_current_source_r50_handoff_refreeze(
        snapshot_refs=P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS,
        review_session_id=_safe_review_session_id(adoption.get("review_session_id")),
        material_id="p7_r53_r4_adopted_r51_r0_current_snapshot_override",
    )
    assert_p7_r51_current_source_r50_handoff_refreeze_contract(r51_r0)
    r51_r1 = build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
        current_source_r50_handoff_refreeze=r51_r0,
        validation_evidence_overrides=_r51_validation_overrides_from_r53_r3_adoption(adoption),
        material_id="p7_r53_r4_adopted_r51_r1_validation_evidence_with_current_snapshot_override",
    )
    assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract(r51_r1)
    return r51_r1


def build_p7_r53_local_root_explicit_allow_purge_plan_preflight(
    *,
    current_snapshot_override_adoption: Mapping[str, Any] | None = None,
    r51_r0_r1_current_snapshot_override_adoption: Mapping[str, Any] | None = None,
    local_review_root: Any = None,
    repo_roots: Sequence[Any] | None = None,
    export_roots: Sequence[Any] | None = None,
    explicit_allow_token: Any = None,
    purge_plan: Mapping[str, Any] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r53_local_root_explicit_allow_purge_plan_preflight",
) -> dict[str, Any]:
    """Build R53-4 body-free explicit allow / local root / purge-plan preflight."""

    if current_snapshot_override_adoption is not None and r51_r0_r1_current_snapshot_override_adoption is not None:
        raise ValueError("provide only one R53-3 current snapshot override adoption value")
    r3 = (
        safe_mapping(current_snapshot_override_adoption)
        if current_snapshot_override_adoption is not None
        else safe_mapping(r51_r0_r1_current_snapshot_override_adoption)
        if r51_r0_r1_current_snapshot_override_adoption is not None
        else build_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override()
    )
    assert_p7_r53_r51_r0_r1_adoption_with_current_snapshot_override_contract(r3)
    r51_r1 = _r51_r1_from_r53_r3_adoption(r3)
    r51_r2 = build_p7_r51_local_root_explicit_allow_purge_plan_preflight(
        validation_evidence_r49_timeout_handling_freeze=r51_r1,
        local_review_root=local_review_root,
        repo_roots=repo_roots,
        export_roots=export_roots,
        explicit_allow_token=explicit_allow_token,
        purge_plan=purge_plan,
        export_candidate_refs=export_candidate_refs,
        material_id="p7_r53_adopted_r51_r2_local_root_explicit_allow_purge_plan_preflight",
    )
    assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(r51_r2)

    r51_blockers = dedupe_identifiers(r51_r2.get("execution_blocker_ids") or [], limit=40, max_length=140)
    r53_blockers = _r53_map_r51_blockers(r51_blockers)
    ready = r51_r2.get("preflight_status") == "PASSED"
    preflight = {
        "schema_version": P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-4_explicit_allow_local_root_purge_plan_preflight",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_local_root_explicit_allow_purge_plan_preflight", max_length=180),
        "review_session_id": _safe_review_session_id(r3.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r3_adoption_schema_version": P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_SCHEMA_VERSION,
        "r3_adoption_material_ref": clean_identifier(r3.get("material_id"), default="p7_r53_r51_r0_r1_adoption_with_current_snapshot_override", max_length=180),
        "r3_adoption_status": clean_identifier(r3.get("adoption_status"), default="ADOPTED_BLOCKED_BY_VALIDATION_EVIDENCE", max_length=100),
        "r3_validation_ready_for_local_root_preflight": r3.get("r51_2_local_root_preflight_allowed_after_r53_3") is True,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_default_source_snapshot_refs": dict(P7_R51_SOURCE_SNAPSHOT_REFS),
        "r51_default_source_snapshot_ref_count": len(P7_R51_SOURCE_SNAPSHOT_REFS),
        "r51_r0_source_snapshot_refs": safe_mapping(r3.get("r51_r0_source_snapshot_refs")),
        "r51_r0_source_snapshot_ref_count": len(safe_mapping(r3.get("r51_r0_source_snapshot_refs"))),
        "r51_r0_uses_r53_current_snapshot_refs": r3.get("r51_r0_uses_r53_current_snapshot_refs") is True,
        "r51_default_source_refs_allowed_as_actual_review_basis": False,
        "r51_r2_preflight_schema_version": P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
        "r51_r2_preflight_material_ref": clean_identifier(r51_r2.get("material_id"), default="p7_r53_adopted_r51_r2_local_root_explicit_allow_purge_plan_preflight", max_length=180),
        "r51_r2_preflight_bodyfree": r51_r2,
        "r51_r2_preflight_status": clean_identifier(r51_r2.get("preflight_status"), default="BLOCKED", max_length=40),
        "r51_r2_next_required_step": clean_identifier(r51_r2.get("next_required_step"), default=P7_R51_R2_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r2_execution_blocker_ids": r51_blockers,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "local_review_root_env_var": "COCOLON_EMLIS_LOCAL_REVIEW_ROOT",
        "local_review_root_source": clean_identifier(r51_r2.get("local_review_root_source"), default="missing", max_length=80),
        "local_review_root_configured": r51_r2.get("local_review_root_configured") is True,
        "local_review_root_valid": r51_r2.get("local_review_root_valid") is True,
        "storage_root_ref": clean_identifier(r51_r2.get("storage_root_ref"), default="not_configured_or_invalid", max_length=120),
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "explicit_allow_env_var": P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR,
        "explicit_allow_token_ref": P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        "explicit_allow_present": r51_r2.get("explicit_allow_present") is True,
        "explicit_allow_token_body_stored_here": False,
        "purge_plan_ref": clean_identifier(r51_r2.get("purge_plan_ref"), default="missing_purge_plan", max_length=180),
        "purge_plan_present": r51_r2.get("purge_plan_present") is True,
        "purge_plan_status": clean_identifier(r51_r2.get("purge_plan_status"), default="MISSING", max_length=80),
        "purge_plan_ready": r51_r2.get("purge_plan_ready") is True,
        "purge_plan_reason_refs": dedupe_identifiers(r51_r2.get("purge_plan_reason_refs") or [], limit=40, max_length=140),
        "purge_plan_required_before_body_full_generation": True,
        "purge_plan_delete_target_refs": dedupe_identifiers(r51_r2.get("purge_plan_delete_target_refs") or [], limit=20, max_length=160),
        "purge_plan_required_delete_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "export_candidate_refs_checked_count": r51_r2.get("export_candidate_refs_checked_count", 0),
        "export_denylist_violation_refs": dedupe_identifiers(r51_r2.get("export_denylist_violation_refs") or [], limit=40, max_length=140),
        "denied_export_candidate_count": r51_r2.get("denied_export_candidate_count", 0),
        "export_candidate_refs_stored_here": False,
        "export_candidate_body_stored_here": False,
        "body_full_packet_export_allowed": False,
        "reviewer_notes_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "premise_or_implemented_docs_inclusion_allowed": False,
        "local_only_body_full_generation_allowed_before_preflight": False,
        "local_only_body_full_generation_allowed_after_preflight": ready,
        "local_only_body_full_generation_allowed": ready,
        "actual_review_session_envelope_allowed_after_r53_4": ready,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "preflight_status": "PASSED" if ready else "BLOCKED",
        "preflight_reason_refs": _r53_preflight_reason_refs_from_r51(r51_r2.get("preflight_reason_refs") or [], r53_blockers),
        "manual_run_decision": clean_identifier(r51_r2.get("manual_run_decision"), default="BLOCKED_BY_EXECUTION_BLOCKER", max_length=120),
        "execution_blocker_ids": r53_blockers,
        "open_execution_blocker_ids": r53_blockers,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "implemented_steps": list(P7_R53_R4_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R4_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R4_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R4_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(preflight)
    return preflight


def assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(preflight: Mapping[str, Any]) -> bool:
    data = safe_mapping(preflight)
    _assert_required_fields(
        data,
        required=P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_REQUIRED_FIELD_REFS,
        source="p7_r53_r4_local_root_explicit_allow_purge_plan_preflight",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
        source="p7_r53_r4_local_root_explicit_allow_purge_plan_preflight",
    )
    if data.get("policy_section") != "R53-4_explicit_allow_local_root_purge_plan_preflight":
        raise ValueError("R53 R4 policy section changed")
    if data.get("r3_adoption_schema_version") != P7_R53_R51_R0_R1_ADOPTION_CURRENT_SNAPSHOT_OVERRIDE_SCHEMA_VERSION:
        raise ValueError("R53 R4 R3 schema reference changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R4 current refs changed")
    if safe_mapping(data.get("r51_default_source_snapshot_refs")) != P7_R51_SOURCE_SNAPSHOT_REFS:
        raise ValueError("R53 R4 R51 default refs changed")
    if safe_mapping(data.get("r51_r0_source_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R4 must preserve R51 R0 current snapshot override")
    if data.get("r51_r0_uses_r53_current_snapshot_refs") is not True:
        raise ValueError("R53 R4 must preserve R51 R0 current snapshot marker")
    if data.get("r51_default_source_refs_allowed_as_actual_review_basis") is not False:
        raise ValueError("R53 R4 must not allow R51 default refs as actual-review basis")
    r51_r2 = safe_mapping(data.get("r51_r2_preflight_bodyfree"))
    assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(r51_r2)
    if data.get("r51_r2_preflight_schema_version") != P7_R51_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("R53 R4 R51 R2 schema reference changed")
    if data.get("r51_r2_preflight_status") != r51_r2.get("preflight_status"):
        raise ValueError("R53 R4 R51 R2 status mismatch")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R53 R4 required case count changed")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "explicit_allow_token_body_stored_here",
        "export_candidate_refs_stored_here",
        "export_candidate_body_stored_here",
        "body_full_packet_export_allowed",
        "reviewer_notes_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
        "premise_or_implemented_docs_inclusion_allowed",
        "local_only_body_full_generation_allowed_before_preflight",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R4 must keep {false_key}=False")
    if data.get("explicit_allow_env_var") != P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR:
        raise ValueError("R53 R4 explicit allow env var changed")
    if data.get("explicit_allow_token_ref") != P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF:
        raise ValueError("R53 R4 explicit allow token ref changed")
    if data.get("purge_plan_required_before_body_full_generation") is not True:
        raise ValueError("R53 R4 must require purge plan before body-full generation")
    if tuple(data.get("purge_plan_required_delete_target_refs") or ()) != P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS:
        raise ValueError("R53 R4 purge target refs changed")
    status = data.get("preflight_status")
    if status not in {"PASSED", "BLOCKED"}:
        raise ValueError("R53 R4 preflight status changed")
    ready = status == "PASSED"
    if data.get("local_only_body_full_generation_allowed_after_preflight") is not ready:
        raise ValueError("R53 R4 after-preflight authorization must match status")
    if data.get("local_only_body_full_generation_allowed") is not ready:
        raise ValueError("R53 R4 local-only authorization must match status")
    if data.get("actual_review_session_envelope_allowed_after_r53_4") is not ready:
        raise ValueError("R53 R4 envelope allowance must match status")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R4 open blockers must match execution blockers")
    if data.get("r51_r2_execution_blocker_ids") != dedupe_identifiers(r51_r2.get("execution_blocker_ids") or [], limit=40, max_length=140):
        raise ValueError("R53 R4 R51 blocker list mismatch")
    if ready:
        for true_key in (
            "r3_validation_ready_for_local_root_preflight",
            "local_review_root_configured",
            "local_review_root_valid",
            "explicit_allow_present",
            "purge_plan_present",
            "purge_plan_ready",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R4 PASSED requires {true_key}=True")
        if blockers:
            raise ValueError("R53 R4 PASSED must not carry blockers")
        if data.get("denied_export_candidate_count") != 0 or data.get("export_denylist_violation_refs"):
            raise ValueError("R53 R4 PASSED must have no export denylist violations")
        if data.get("manual_run_decision") != "GO_FOR_LOCAL_MANUAL_REVIEW":
            raise ValueError("R53 R4 PASSED must preserve R51 GO decision")
        if data.get("r51_r2_next_required_step") != P7_R51_R2_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R4 ready R51 R2 must point to R51-3")
        if data.get("next_required_step") != P7_R53_R4_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R4 PASSED must point to R53-5")
    else:
        if not data.get("preflight_reason_refs") or not blockers:
            raise ValueError("R53 R4 BLOCKED must carry reasons and blockers")
        if data.get("r51_r2_next_required_step") != P7_R51_R2_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R4 blocked R51 R2 must point to R51 preflight resolution")
        if data.get("next_required_step") != P7_R53_R4_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R4 BLOCKED must point to R53 preflight resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R4_IMPLEMENTED_STEPS:
        raise ValueError("R53 R4 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R4_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R4 not-yet steps changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r4_local_root_explicit_allow_purge_plan_preflight")
    return True


def build_p7_r53_actual_review_session_envelope_bodyfree(
    *,
    local_root_explicit_allow_purge_plan_preflight: Mapping[str, Any] | None = None,
    r4_local_root_explicit_allow_purge_plan_preflight: Mapping[str, Any] | None = None,
    reviewer_ref: Any = "pseudonymous_reviewer_r53_local_manual_run",
    material_id: Any = "p7_r53_actual_review_session_envelope_bodyfree",
) -> dict[str, Any]:
    """Build R53-5 body-free actual-review session envelope; no review is run."""

    if local_root_explicit_allow_purge_plan_preflight is not None and r4_local_root_explicit_allow_purge_plan_preflight is not None:
        raise ValueError("provide only one R53-4 local root preflight value")
    r4 = (
        safe_mapping(local_root_explicit_allow_purge_plan_preflight)
        if local_root_explicit_allow_purge_plan_preflight is not None
        else safe_mapping(r4_local_root_explicit_allow_purge_plan_preflight)
        if r4_local_root_explicit_allow_purge_plan_preflight is not None
        else build_p7_r53_local_root_explicit_allow_purge_plan_preflight()
    )
    assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract(r4)
    r51_r2 = safe_mapping(r4.get("r51_r2_preflight_bodyfree"))
    assert_p7_r51_local_root_explicit_allow_purge_plan_preflight_contract(r51_r2)
    r51_r3 = build_p7_r51_actual_review_session_envelope_bodyfree(
        local_root_explicit_allow_purge_plan_preflight=r51_r2,
        snapshot_refs=P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS,
        reviewer_ref=reviewer_ref,
        material_id="p7_r53_adopted_r51_r3_actual_review_session_envelope_bodyfree",
    )
    assert_p7_r51_actual_review_session_envelope_bodyfree_contract(r51_r3)
    ready = r51_r3.get("envelope_status") == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    blockers = _r53_map_r51_blockers(r51_r3.get("execution_blocker_ids") or [])
    envelope = {
        "schema_version": P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-5_actual_review_session_envelope",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_actual_review_session_envelope_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r4.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r4_preflight_schema_version": P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION,
        "r4_preflight_material_ref": clean_identifier(r4.get("material_id"), default="p7_r53_local_root_explicit_allow_purge_plan_preflight", max_length=180),
        "r4_preflight_status": clean_identifier(r4.get("preflight_status"), default="BLOCKED", max_length=40),
        "r4_preflight_ready_for_envelope": r4.get("actual_review_session_envelope_allowed_after_r53_4") is True,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r3_envelope_schema_version": P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "r51_r3_envelope_material_ref": clean_identifier(r51_r3.get("material_id"), default="p7_r53_adopted_r51_r3_actual_review_session_envelope_bodyfree", max_length=180),
        "r51_r3_envelope_bodyfree": r51_r3,
        "r51_r3_envelope_status": clean_identifier(r51_r3.get("envelope_status"), default="BLOCKED_BY_R51_2_PREFLIGHT", max_length=100),
        "r51_r3_next_required_step": clean_identifier(r51_r3.get("next_required_step"), default=P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r3_execution_blocker_ids": dedupe_identifiers(r51_r3.get("execution_blocker_ids") or [], limit=40, max_length=140),
        "review_session_status": clean_identifier(r51_r3.get("review_session_status"), default="PRECHECK_BLOCKED", max_length=100),
        "envelope_status": "READY_FOR_24_CASE_MANIFEST_FREEZE" if ready else "BLOCKED_BY_R53_4_PREFLIGHT",
        "envelope_reason_refs": ["actual_review_session_envelope_ready"] if ready else ["r53_4_preflight_not_passed"],
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_prompt_version": clean_identifier(r51_r3.get("review_prompt_version"), default="p7_r51_p5_human_blind_qa_actual_review_prompt_v1", max_length=180),
        "reviewer_ref": clean_identifier(r51_r3.get("reviewer_ref"), default="pseudonymous_reviewer_r53_local_manual_run", max_length=120),
        "reviewer_ref_pseudonymous": r51_r3.get("reviewer_ref_pseudonymous") is True,
        "reviewer_blind_policy": safe_mapping(r51_r3.get("reviewer_blind_policy")),
        "reviewer_visible_field_refs": list(r51_r3.get("reviewer_visible_field_refs") or []),
        "reviewer_hidden_field_refs": list(r51_r3.get("reviewer_hidden_field_refs") or []),
        "local_root_ref": clean_identifier(r51_r3.get("local_root_ref"), default="not_configured_or_invalid", max_length=120),
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "body_full_generation_allowed": ready,
        "local_only_body_full_generation_allowed": ready,
        "body_full_packet_export_allowed": False,
        "reviewer_notes_export_allowed": False,
        "body_full_packet_zip_inclusion_allowed": False,
        "disposal_plan_ref": clean_identifier(r51_r3.get("disposal_plan_ref"), default="missing_purge_plan", max_length=180),
        "disposal_plan_ready": r51_r3.get("disposal_plan_ready") is True,
        "session_controller_material_refs": list(r51_r3.get("session_controller_material_refs") or []),
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "actual_review_session_envelope_bodyfree_materialized_here": True,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "implemented_steps": list(P7_R53_R5_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R5_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R5_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R5_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_actual_review_session_envelope_bodyfree_contract(envelope)
    return envelope


def assert_p7_r53_actual_review_session_envelope_bodyfree_contract(envelope: Mapping[str, Any]) -> bool:
    data = safe_mapping(envelope)
    _assert_required_fields(
        data,
        required=P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS,
        source="p7_r53_r5_actual_review_session_envelope_bodyfree",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        source="p7_r53_r5_actual_review_session_envelope_bodyfree",
    )
    if data.get("policy_section") != "R53-5_actual_review_session_envelope":
        raise ValueError("R53 R5 policy section changed")
    if data.get("r4_preflight_schema_version") != P7_R53_LOCAL_ROOT_EXPLICIT_ALLOW_PURGE_PLAN_PREFLIGHT_SCHEMA_VERSION:
        raise ValueError("R53 R5 R4 schema reference changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R5 current refs changed")
    r51_r3 = safe_mapping(data.get("r51_r3_envelope_bodyfree"))
    assert_p7_r51_actual_review_session_envelope_bodyfree_contract(r51_r3)
    if data.get("r51_r3_envelope_schema_version") != P7_R51_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION:
        raise ValueError("R53 R5 R51 R3 schema reference changed")
    if data.get("r51_r3_envelope_status") != r51_r3.get("envelope_status"):
        raise ValueError("R53 R5 R51 R3 envelope status mismatch")
    if data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
        raise ValueError("R53 R5 required case count changed")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packet_export_allowed",
        "reviewer_notes_export_allowed",
        "body_full_packet_zip_inclusion_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R5 must keep {false_key}=False")
    if data.get("actual_review_session_envelope_bodyfree_materialized_here") is not True:
        raise ValueError("R53 R5 must mark only the body-free envelope as materialized")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R53 R5 must not claim P5 actual review ran")
    ready = data.get("envelope_status") == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    if data.get("body_full_generation_allowed") is not ready:
        raise ValueError("R53 R5 body-full generation authorization must match envelope readiness")
    if data.get("local_only_body_full_generation_allowed") is not ready:
        raise ValueError("R53 R5 local-only generation authorization must match envelope readiness")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R5 open blockers must match execution blockers")
    if data.get("r51_r3_execution_blocker_ids") != dedupe_identifiers(r51_r3.get("execution_blocker_ids") or [], limit=40, max_length=140):
        raise ValueError("R53 R5 R51 blocker list mismatch")
    reviewer_policy = safe_mapping(data.get("reviewer_blind_policy"))
    if reviewer_policy.get("reviewer_faces_blind_case_id_only") is not True:
        raise ValueError("R53 R5 reviewer must face blind case id only")
    if reviewer_policy.get("family_hidden_from_reviewer") is not True:
        raise ValueError("R53 R5 reviewer family must remain hidden")
    if reviewer_policy.get("question_text_created_here") is not False:
        raise ValueError("R53 R5 must not create question text")
    if data.get("reviewer_ref_pseudonymous") is not True:
        raise ValueError("R53 R5 reviewer ref must remain pseudonymous")
    if ready:
        if data.get("r4_preflight_ready_for_envelope") is not True:
            raise ValueError("R53 R5 ready envelope requires R4 ready preflight")
        if data.get("review_session_status") != "ACTUAL_REVIEW_SESSION_ENVELOPE_READY":
            raise ValueError("R53 R5 ready review session status changed")
        if blockers:
            raise ValueError("R53 R5 ready envelope must not carry blockers")
        if data.get("disposal_plan_ready") is not True:
            raise ValueError("R53 R5 ready envelope requires ready disposal plan")
        if data.get("r51_r3_next_required_step") != P7_R51_R3_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R5 ready R51 R3 must point to R51-4")
        if data.get("next_required_step") != P7_R53_R5_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R5 ready envelope must point to R53-6")
    else:
        if data.get("review_session_status") != "PRECHECK_BLOCKED":
            raise ValueError("R53 R5 blocked envelope must use PRECHECK_BLOCKED")
        if data.get("r51_r3_next_required_step") != P7_R51_R3_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R5 blocked R51 R3 must point to preflight resolution")
        if data.get("next_required_step") != P7_R53_R5_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R5 blocked envelope must point to R53 preflight resolution")
        if not blockers:
            raise ValueError("R53 R5 blocked envelope must keep blockers visible")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R5_IMPLEMENTED_STEPS:
        raise ValueError("R53 R5 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R5_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R5 not-yet steps changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r5_actual_review_session_envelope_bodyfree")
    return True


P7_R53_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.24_case_manifest_freeze.bodyfree.v1"
)
P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.local_only_body_full_packet_generation_request.bodyfree.v1"
)

P7_R53_R6_NEXT_REQUIRED_STEP_REF: Final = "R53-7_local_only_body_full_packet_generation_request_optional_writer"
P7_R53_R6_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-5_actual_review_session_envelope_before_R53-6_manifest"
P7_R53_R7_NEXT_REQUIRED_STEP_REF: Final = "R53-8_packet_completeness_export_denylist_scan"
P7_R53_R7_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-6_24_case_manifest_before_R53-7_packet_generation_request"

P7_R53_R6_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R5_IMPLEMENTED_STEPS,
    "R53-6_24_case_manifest_freeze",
)
P7_R53_FUTURE_STEPS_AFTER_R7: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R5
    if step
    not in {
        "R53-6_24_case_manifest_freeze",
        "R53-7_local_only_body_full_packet_generation_request_optional_writer",
    }
)
P7_R53_R6_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-7_local_only_body_full_packet_generation_request_optional_writer",
    *P7_R53_FUTURE_STEPS_AFTER_R7,
)
P7_R53_R7_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R6_IMPLEMENTED_STEPS,
    "R53-7_local_only_body_full_packet_generation_request_optional_writer",
)
P7_R53_R7_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R7

P7_R53_R51_TO_R53_MANIFEST_OR_PACKET_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_PREFLIGHT_BLOCKER_MAP,
    "r51_case_manifest_incomplete": "r53_case_manifest_incomplete",
    "r51_blind_case_id_case_ref_boundary_violation": "r53_blind_case_id_case_ref_boundary_violation",
    "r51_reviewer_facing_manifest_leak_detected": "r53_reviewer_facing_manifest_leak_detected",
    "r51_body_full_packet_generation_request_blocked": "r53_body_full_packet_generation_request_blocked",
    "r51_case_material_missing": "r53_case_manifest_incomplete",
}

P7_R53_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r5_envelope_schema_version",
    "r5_envelope_material_ref",
    "r5_envelope_status",
    "r5_envelope_ready_for_manifest",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r4_manifest_schema_version",
    "r51_r4_manifest_material_ref",
    "r51_r4_manifest_bodyfree",
    "r51_r4_manifest_status",
    "r51_r4_next_required_step",
    "r51_r4_execution_blocker_ids",
    "review_session_status",
    "manifest_status",
    "manifest_reason_refs",
    "required_case_count",
    "case_count",
    "case_rows",
    "controller_manifest_rows",
    "reviewer_facing_case_index_rows",
    "family_case_counts",
    "case_role_counts",
    "subscription_tier_ref_counts",
    "owned_history_positive_case_count",
    "boundary_case_count",
    "low_information_boundary_case_count",
    "free_tier_boundary_case_count",
    "minimums_satisfied",
    "blind_case_ids_unique",
    "case_ref_ids_unique",
    "packet_ref_ids_unique",
    "blind_case_id_case_ref_separated",
    "reviewer_receives_blind_case_id_only",
    "controller_keeps_family_tier_expected_refs",
    "reviewer_facing_family_exposed",
    "reviewer_facing_tier_exposed",
    "reviewer_facing_expected_result_exposed",
    "body_full_packet_materialized_here",
    "local_reviewer_payload_materialized_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_6_24_case_manifest_frozen",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r6_manifest_schema_version",
    "r6_manifest_material_ref",
    "r6_manifest_status",
    "r6_manifest_ready_for_packet_generation_request",
    "r6_manifest_ready_for_generation_request",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r5_generation_request_schema_version",
    "r51_r5_generation_request_material_ref",
    "r51_r5_generation_request_bodyfree",
    "r51_r5_generation_request_status",
    "r51_r5_next_required_step",
    "r51_r5_execution_blocker_ids",
    "review_session_status",
    "generation_request_status",
    "generation_request_reason_refs",
    "required_case_count",
    "case_count",
    "packet_generation_request_case_count",
    "packet_generation_request_row_count",
    "packet_generation_request_rows",
    "requested_packet_ref_count",
    "blind_case_id_count",
    "packet_ref_ids_unique",
    "case_ref_ids_unique",
    "body_full_reviewer_packet_local_only_schema_version_ref",
    "body_full_packet_local_only_required_field_refs",
    "packet_kind",
    "review_kind",
    "review_prompt_version",
    "reviewer_visible_field_refs",
    "reviewer_hidden_field_refs",
    "local_root_ref",
    "root_path_exposed",
    "local_absolute_path_included",
    "disposal_plan_ref",
    "disposal_plan_ready",
    "local_only_required",
    "must_not_export",
    "disposal_required",
    "local_only_body_full_generation_allowed",
    "local_only_body_full_packet_generation_request_created_here",
    "body_full_packet_generation_request_created_here",
    "actual_body_full_packet_generated_here",
    "local_file_ops_helper_created_here",
    "body_full_packet_writer_created_here",
    "body_full_packet_local_only_schema_file_created_here",
    "generation_event_bodyfree_only",
    "optional_writer_boundary_materialized_here",
    "optional_writer_decision_ref",
    "optional_writer_allowed_to_be_added_later_under_local_only_guard",
    "optional_writer_execution_supported_later",
    "optional_writer_executed_here",
    "optional_writer_public_runtime_callable",
    "optional_writer_requires_explicit_allow_local_root_purge_plan",
    "writer_requires_explicit_allow_local_root_purge_plan",
    "writer_requires_r53_8_completion_scan_after_execution",
    "writer_execution_requires_body_full_material_not_in_patch_zip",
    "optional_writer_result_bodyfree_only",
    "optional_writer_local_root_path_included",
    "optional_writer_body_content_included_here",
    "optional_writer_body_content_hash_stored_here",
    "local_only_writer_created_here",
    "local_only_writer_executed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "packet_body_included_here",
    "local_packet_exported_allowed",
    "content_hash_of_body_stored_allowed",
    "export_candidate_refs_stored_here",
    "export_candidate_body_stored_here",
    "question_text_created_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def _r53_map_r51_manifest_or_packet_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_MANIFEST_OR_PACKET_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=40,
        max_length=140,
    )


def _r53_reason_refs_from_r51(prefix: str, r51_reason_refs: Sequence[Any], blocker_ids: Sequence[Any]) -> list[str]:
    """Convert adopted R51 R4/R5 reason refs to R53 body-free reason refs."""

    reason_refs = [
        f"{clean_identifier(prefix, default='r53_reason', max_length=80)}_{clean_identifier(ref, default='blocked', max_length=120)}"
        for ref in r51_reason_refs
    ]
    if blocker_ids and f"{prefix}_blockers_visible" not in reason_refs:
        reason_refs.append(f"{prefix}_blockers_visible")
    if not reason_refs:
        reason_refs.append(f"{prefix}_blocked")
    return dedupe_identifiers(reason_refs, limit=40, max_length=160)


def build_p7_r53_24_case_manifest_freeze_bodyfree(
    *,
    actual_review_session_envelope: Mapping[str, Any] | None = None,
    r5_actual_review_session_envelope: Mapping[str, Any] | None = None,
    case_matrix: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_24_case_manifest_freeze_bodyfree",
) -> dict[str, Any]:
    """Build R53-6 body-free 24-case manifest freeze.

    Controller-only case refs and reviewer-facing blind case ids are kept
    separated.  No body-full packet, reviewer payload, path, hash, rating row,
    or question text is materialized here.
    """

    if actual_review_session_envelope is not None and r5_actual_review_session_envelope is not None:
        raise ValueError("provide only one R53-5 envelope value")
    r5 = (
        safe_mapping(actual_review_session_envelope)
        if actual_review_session_envelope is not None
        else safe_mapping(r5_actual_review_session_envelope)
        if r5_actual_review_session_envelope is not None
        else build_p7_r53_actual_review_session_envelope_bodyfree()
    )
    assert_p7_r53_actual_review_session_envelope_bodyfree_contract(r5)
    r51_r3 = safe_mapping(r5.get("r51_r3_envelope_bodyfree"))
    assert_p7_r51_actual_review_session_envelope_bodyfree_contract(r51_r3)
    r51_r4 = build_p7_r51_24_case_manifest_freeze_bodyfree(
        actual_review_session_envelope=r51_r3,
        case_matrix=case_matrix,
        material_id="p7_r53_adopted_r51_r4_24_case_manifest_freeze_bodyfree",
    )
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(r51_r4)
    r5_ready = r5.get("envelope_status") == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    r51_ready = r51_r4.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    ready = r5_ready and r51_ready
    blockers = _r53_map_r51_manifest_or_packet_blockers(
        [*(r5.get("execution_blocker_ids") or []), *(r51_r4.get("execution_blocker_ids") or [])]
    )
    if not r5_ready and "r53_5_actual_review_session_envelope_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_5_actual_review_session_envelope_not_ready"], limit=40, max_length=140)
    if not r5_ready and "r53_5_actual_review_session_envelope_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_5_actual_review_session_envelope_not_ready"], limit=40, max_length=140)
    if r5_ready and not r51_ready and "r53_case_manifest_incomplete" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_case_manifest_incomplete"], limit=40, max_length=140)
    rows = [safe_mapping(row) for row in (r51_r4.get("case_rows") or [])] if ready else []
    controller_rows = [safe_mapping(row) for row in (r51_r4.get("controller_manifest_rows") or [])] if ready else []
    reviewer_rows = [safe_mapping(row) for row in (r51_r4.get("reviewer_facing_case_index_rows") or [])] if ready else []
    manifest = {
        "schema_version": P7_R53_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-6_24_case_manifest_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_24_case_manifest_freeze_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r5.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r5_envelope_schema_version": P7_R53_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION,
        "r5_envelope_material_ref": clean_identifier(r5.get("material_id"), default="p7_r53_actual_review_session_envelope_bodyfree", max_length=180),
        "r5_envelope_status": clean_identifier(r5.get("envelope_status"), default="BLOCKED_BY_R53_4_PREFLIGHT", max_length=120),
        "r5_envelope_ready_for_manifest": r5_ready,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r4_manifest_schema_version": P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "r51_r4_manifest_material_ref": clean_identifier(r51_r4.get("material_id"), default="p7_r53_adopted_r51_r4_24_case_manifest_freeze_bodyfree", max_length=180),
        "r51_r4_manifest_bodyfree": r51_r4,
        "r51_r4_manifest_status": clean_identifier(r51_r4.get("manifest_status"), default="BLOCKED_BY_R51_3_ENVELOPE", max_length=120),
        "r51_r4_next_required_step": clean_identifier(r51_r4.get("next_required_step"), default=P7_R51_R4_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r4_execution_blocker_ids": dedupe_identifiers(r51_r4.get("execution_blocker_ids") or [], limit=40, max_length=140),
        "review_session_status": "R53_24_CASE_MANIFEST_READY" if ready else "PRECHECK_BLOCKED",
        "manifest_status": "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST" if ready else "BLOCKED_BY_R53_5_ENVELOPE",
        "manifest_reason_refs": ["r53_24_case_manifest_ready_for_local_only_packet_generation_request"] if ready else _r53_preflight_reason_refs_from_r51(r51_r4.get("manifest_reason_refs") or [], blockers),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "case_count": len(rows),
        "case_rows": rows,
        "controller_manifest_rows": controller_rows,
        "reviewer_facing_case_index_rows": reviewer_rows,
        "family_case_counts": safe_mapping(r51_r4.get("family_case_counts")) if ready else {},
        "case_role_counts": safe_mapping(r51_r4.get("case_role_counts")) if ready else {},
        "subscription_tier_ref_counts": safe_mapping(r51_r4.get("subscription_tier_ref_counts")) if ready else {},
        "owned_history_positive_case_count": r51_r4.get("owned_history_positive_case_count") if ready else 0,
        "boundary_case_count": r51_r4.get("boundary_case_count") if ready else 0,
        "low_information_boundary_case_count": r51_r4.get("low_information_boundary_case_count") if ready else 0,
        "free_tier_boundary_case_count": r51_r4.get("free_tier_boundary_case_count") if ready else 0,
        "minimums_satisfied": ready and r51_r4.get("minimums_satisfied") is True,
        "blind_case_ids_unique": ready and r51_r4.get("blind_case_ids_unique") is True,
        "case_ref_ids_unique": ready and r51_r4.get("case_ref_ids_unique") is True,
        "packet_ref_ids_unique": ready and r51_r4.get("packet_ref_ids_unique") is True,
        "blind_case_id_case_ref_separated": ready and r51_r4.get("blind_case_id_case_ref_separated") is True,
        "reviewer_receives_blind_case_id_only": ready and r51_r4.get("reviewer_receives_blind_case_id_only") is True,
        "controller_keeps_family_tier_expected_refs": ready and r51_r4.get("controller_keeps_family_tier_expected_refs") is True,
        "reviewer_facing_family_exposed": False,
        "reviewer_facing_tier_exposed": False,
        "reviewer_facing_expected_result_exposed": False,
        "body_full_packet_materialized_here": False,
        "local_reviewer_payload_materialized_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": ready,
        "r53_6_24_case_manifest_frozen": ready,
        "implemented_steps": list(P7_R53_R6_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R6_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R6_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R6_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(manifest)
    return manifest


def assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(manifest: Mapping[str, Any]) -> bool:
    data = safe_mapping(manifest)
    _assert_required_fields(
        data,
        required=P7_R53_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r53_r6_24_case_manifest_freeze_bodyfree",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        source="p7_r53_r6_24_case_manifest_freeze_bodyfree",
    )
    if data.get("policy_section") != "R53-6_24_case_manifest_freeze":
        raise ValueError("R53 R6 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R6 current refs changed")
    r51_manifest = safe_mapping(data.get("r51_r4_manifest_bodyfree"))
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(r51_manifest)
    if data.get("r51_r4_manifest_schema_version") != P7_R51_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION:
        raise ValueError("R53 R6 R51 manifest schema reference changed")
    if data.get("r51_r4_manifest_status") != r51_manifest.get("manifest_status"):
        raise ValueError("R53 R6 R51 manifest status mismatch")
    for false_key in (
        "reviewer_facing_family_exposed",
        "reviewer_facing_tier_exposed",
        "reviewer_facing_expected_result_exposed",
        "body_full_packet_materialized_here",
        "local_reviewer_payload_materialized_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R6 must keep {false_key}=False")
    if data.get("p5_actual_review_still_not_run") is not True:
        raise ValueError("R53 R6 must not claim P5 actual review ran")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R6 open blockers must match execution blockers")
    ready = data.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    rows = [safe_mapping(row) for row in (data.get("case_rows") or [])]
    controller_rows = [safe_mapping(row) for row in (data.get("controller_manifest_rows") or [])]
    reviewer_rows = [safe_mapping(row) for row in (data.get("reviewer_facing_case_index_rows") or [])]
    if data.get("r53_6_24_case_manifest_freeze_built") is not ready:
        raise ValueError("R53 R6 built flag must match manifest readiness")
    if data.get("r53_6_24_case_manifest_frozen") is not ready:
        raise ValueError("R53 R6 frozen flag must match manifest readiness")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R6_IMPLEMENTED_STEPS:
        raise ValueError("R53 R6 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R6_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R6 not-yet steps changed")
    if ready:
        if data.get("r5_envelope_ready_for_manifest") is not True:
            raise ValueError("R53 R6 ready manifest requires ready R5 envelope")
        if data.get("r51_r4_next_required_step") != P7_R51_R4_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R6 ready R51 manifest must point to R51-5")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or len(controller_rows) != P7_R51_REQUIRED_CASE_COUNT or len(reviewer_rows) != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R6 ready manifest must contain exactly 24 body-free case rows")
        for true_key in (
            "minimums_satisfied",
            "blind_case_ids_unique",
            "case_ref_ids_unique",
            "packet_ref_ids_unique",
            "blind_case_id_case_ref_separated",
            "reviewer_receives_blind_case_id_only",
            "controller_keeps_family_tier_expected_refs",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R6 ready manifest requires {true_key}=True")
        if data.get("case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("required_case_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R6 case count changed")
        if data.get("low_information_boundary_case_count") != 2 or data.get("free_tier_boundary_case_count") != 2:
            raise ValueError("R53 R6 boundary case distribution changed")
        for row in reviewer_rows:
            for key in ("family", "subscription_tier_ref", "expected_result_ref", "case_ref_id"):
                if key in row:
                    raise ValueError("R53 R6 reviewer-facing row leaked controller-only fields")
            if row.get("reviewer_identifier_kind") != "blind_case_id_only":
                raise ValueError("R53 R6 reviewer row must be blind-id only")
            for hidden_key in ("case_ref_hidden", "family_hidden", "tier_hidden", "expected_result_hidden"):
                if row.get(hidden_key) is not True:
                    raise ValueError("R53 R6 reviewer row must keep controller identifiers hidden")
        if blockers:
            raise ValueError("R53 R6 ready manifest must not carry blockers")
        if data.get("next_required_step") != P7_R53_R6_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R6 ready manifest must point to R53-7")
    else:
        if rows or controller_rows or reviewer_rows or data.get("case_count") != 0:
            raise ValueError("R53 R6 blocked manifest must not expose case rows")
        if data.get("next_required_step") != P7_R53_R6_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R6 blocked manifest must point to envelope resolution")
        if not blockers:
            raise ValueError("R53 R6 blocked manifest must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r6_24_case_manifest_freeze_bodyfree")
    return True


def build_p7_r53_local_only_body_full_packet_generation_request_bodyfree(
    *,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    r6_24_case_manifest_freeze: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_local_only_body_full_packet_generation_request_bodyfree",
) -> dict[str, Any]:
    """Build R53-7 body-free packet generation request and optional-writer boundary.

    This creates request rows only.  It does not write local-only body-full
    packets, create a public/runtime writer, expose local paths, store body
    hashes, or run review.
    """

    if case_manifest_freeze is not None and r6_24_case_manifest_freeze is not None:
        raise ValueError("provide only one R53-6 manifest value")
    r6 = (
        safe_mapping(case_manifest_freeze)
        if case_manifest_freeze is not None
        else safe_mapping(r6_24_case_manifest_freeze)
        if r6_24_case_manifest_freeze is not None
        else build_p7_r53_24_case_manifest_freeze_bodyfree()
    )
    assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(r6)
    r51_manifest = safe_mapping(r6.get("r51_r4_manifest_bodyfree"))
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(r51_manifest)
    r51_request = build_p7_r51_local_only_body_full_packet_generation_request_bodyfree(
        case_manifest_freeze=r51_manifest,
        material_id="p7_r53_adopted_r51_r5_local_only_body_full_packet_generation_request_bodyfree",
    )
    assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(r51_request)
    r6_ready = r6.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    r51_ready = r51_request.get("generation_request_status") == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    ready = r6_ready and r51_ready
    blockers = _r53_map_r51_manifest_or_packet_blockers(
        [*(r6.get("execution_blocker_ids") or []), *(r51_request.get("execution_blocker_ids") or [])]
    )
    if not ready and "r53_body_full_packet_generation_request_blocked" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_body_full_packet_generation_request_blocked"], limit=40, max_length=140)
    rows = [safe_mapping(row) for row in (r51_request.get("packet_generation_request_rows") or [])] if ready else []
    request = {
        "schema_version": P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-7_local_only_body_full_packet_generation_request_optional_writer",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_local_only_body_full_packet_generation_request_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r6.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r6_manifest_schema_version": P7_R53_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "r6_manifest_material_ref": clean_identifier(r6.get("material_id"), default="p7_r53_24_case_manifest_freeze_bodyfree", max_length=180),
        "r6_manifest_status": clean_identifier(r6.get("manifest_status"), default="BLOCKED_BY_R53_5_ENVELOPE", max_length=120),
        "r6_manifest_ready_for_packet_generation_request": r6_ready,
        "r6_manifest_ready_for_generation_request": r6_ready,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r5_generation_request_schema_version": P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "r51_r5_generation_request_material_ref": clean_identifier(r51_request.get("material_id"), default="p7_r53_adopted_r51_r5_generation_request", max_length=180),
        "r51_r5_generation_request_bodyfree": r51_request,
        "r51_r5_generation_request_status": clean_identifier(r51_request.get("generation_request_status"), default="BLOCKED_BY_R51_4_MANIFEST", max_length=120),
        "r51_r5_next_required_step": clean_identifier(r51_request.get("next_required_step"), default=P7_R51_R5_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r5_execution_blocker_ids": dedupe_identifiers(r51_request.get("execution_blocker_ids") or [], limit=40, max_length=140),
        "review_session_status": "R53_BODY_FULL_PACKET_GENERATION_REQUEST_READY" if ready else "PRECHECK_BLOCKED",
        "generation_request_status": "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION" if ready else "BLOCKED_BY_R53_6_MANIFEST",
        "generation_request_reason_refs": ["r53_local_only_body_full_packet_generation_request_ready_not_generated"] if ready else _r53_preflight_reason_refs_from_r51(r51_request.get("generation_request_reason_refs") or [], blockers),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "case_count": len(rows),
        "packet_generation_request_case_count": len(rows),
        "packet_generation_request_row_count": len(rows),
        "packet_generation_request_rows": rows,
        "requested_packet_ref_count": len(rows),
        "blind_case_id_count": len(rows),
        "packet_ref_ids_unique": ready and r51_request.get("packet_ref_ids_unique") is True,
        "case_ref_ids_unique": ready and r51_request.get("case_ref_ids_unique") is True,
        "body_full_reviewer_packet_local_only_schema_version_ref": P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "body_full_packet_local_only_required_field_refs": list(P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS),
        "packet_kind": P7_R51_PACKET_KIND,
        "review_kind": P7_R51_REVIEW_KIND,
        "review_prompt_version": P7_R51_REVIEW_PROMPT_VERSION,
        "reviewer_visible_field_refs": list(r51_request.get("reviewer_visible_field_refs") or []),
        "reviewer_hidden_field_refs": list(r51_request.get("reviewer_hidden_field_refs") or []),
        "local_root_ref": clean_identifier(r51_request.get("local_root_ref"), default="not_authorized", max_length=120),
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "disposal_plan_ref": clean_identifier(r51_request.get("disposal_plan_ref"), default="not_ready", max_length=180),
        "disposal_plan_ready": ready and r51_request.get("disposal_plan_ready") is True,
        "local_only_required": ready and r51_request.get("local_only_required") is True,
        "must_not_export": ready and r51_request.get("must_not_export") is True,
        "disposal_required": ready and r51_request.get("disposal_required") is True,
        "local_only_body_full_generation_allowed": ready and r51_request.get("local_only_body_full_generation_allowed") is True,
        "local_only_body_full_packet_generation_request_created_here": ready and r51_request.get("local_only_body_full_packet_generation_request_created_here") is True,
        "body_full_packet_generation_request_created_here": ready and r51_request.get("body_full_packet_generation_request_created_here") is True,
        "actual_body_full_packet_generated_here": False,
        "local_file_ops_helper_created_here": False,
        "body_full_packet_writer_created_here": False,
        "body_full_packet_local_only_schema_file_created_here": False,
        "generation_event_bodyfree_only": True,
        "optional_writer_boundary_materialized_here": True,
        "optional_writer_decision_ref": "REQUEST_READY_OPTIONAL_WRITER_NOT_CREATED_HERE" if ready else "REQUEST_BLOCKED_OPTIONAL_WRITER_NOT_CREATED_HERE",
        "optional_writer_allowed_to_be_added_later_under_local_only_guard": ready,
        "optional_writer_execution_supported_later": ready,
        "optional_writer_executed_here": False,
        "optional_writer_public_runtime_callable": False,
        "optional_writer_requires_explicit_allow_local_root_purge_plan": True,
        "writer_requires_explicit_allow_local_root_purge_plan": True,
        "writer_requires_r53_8_completion_scan_after_execution": True,
        "writer_execution_requires_body_full_material_not_in_patch_zip": True,
        "optional_writer_result_bodyfree_only": True,
        "optional_writer_local_root_path_included": False,
        "optional_writer_body_content_included_here": False,
        "optional_writer_body_content_hash_stored_here": False,
        "local_only_writer_created_here": False,
        "local_only_writer_executed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "packet_body_included_here": False,
        "local_packet_exported_allowed": False,
        "content_hash_of_body_stored_allowed": False,
        "export_candidate_refs_stored_here": False,
        "export_candidate_body_stored_here": False,
        "question_text_created_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r6.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": ready,
        "implemented_steps": list(P7_R53_R7_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R7_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R7_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R7_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract(request)
    return request


def assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract(request: Mapping[str, Any]) -> bool:
    data = safe_mapping(request)
    _assert_required_fields(
        data,
        required=P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_REQUIRED_FIELD_REFS,
        source="p7_r53_r7_local_only_body_full_packet_generation_request_bodyfree",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        source="p7_r53_r7_local_only_body_full_packet_generation_request_bodyfree",
    )
    if data.get("policy_section") != "R53-7_local_only_body_full_packet_generation_request_optional_writer":
        raise ValueError("R53 R7 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R7 current refs changed")
    r51_request = safe_mapping(data.get("r51_r5_generation_request_bodyfree"))
    assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(r51_request)
    if data.get("r51_r5_generation_request_schema_version") != P7_R51_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION:
        raise ValueError("R53 R7 R51 request schema reference changed")
    if data.get("r51_r5_generation_request_status") != r51_request.get("generation_request_status"):
        raise ValueError("R53 R7 R51 request status mismatch")
    if data.get("body_full_reviewer_packet_local_only_schema_version_ref") != P7_R51_BODY_FULL_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION:
        raise ValueError("R53 R7 packet schema version ref changed")
    if tuple(data.get("body_full_packet_local_only_required_field_refs") or ()) != P7_R51_BODY_FULL_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS:
        raise ValueError("R53 R7 local-only packet required field refs changed")
    if data.get("packet_kind") != P7_R51_PACKET_KIND or data.get("review_kind") != P7_R51_REVIEW_KIND:
        raise ValueError("R53 R7 packet/review kind changed")
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "actual_body_full_packet_generated_here",
        "local_file_ops_helper_created_here",
        "body_full_packet_writer_created_here",
        "body_full_packet_local_only_schema_file_created_here",
        "optional_writer_executed_here",
        "optional_writer_public_runtime_callable",
        "local_only_writer_created_here",
        "local_only_writer_executed_here",
        "optional_writer_local_root_path_included",
        "optional_writer_body_content_included_here",
        "optional_writer_body_content_hash_stored_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "packet_body_included_here",
        "local_packet_exported_allowed",
        "content_hash_of_body_stored_allowed",
        "export_candidate_refs_stored_here",
        "export_candidate_body_stored_here",
        "question_text_created_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R7 must keep {false_key}=False")
    for true_key in (
        "optional_writer_boundary_materialized_here",
        "optional_writer_requires_explicit_allow_local_root_purge_plan",
        "writer_requires_explicit_allow_local_root_purge_plan",
        "writer_requires_r53_8_completion_scan_after_execution",
        "writer_execution_requires_body_full_material_not_in_patch_zip",
        "optional_writer_result_bodyfree_only",
        "generation_event_bodyfree_only",
        "p5_actual_review_still_not_run",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R7 must keep {true_key}=True")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R7 open blockers must match execution blockers")
    ready = data.get("generation_request_status") == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    rows = [safe_mapping(row) for row in (data.get("packet_generation_request_rows") or [])]
    if data.get("r53_7_local_only_body_full_packet_generation_request_built") is not ready:
        raise ValueError("R53 R7 built flag must match request readiness")
    if data.get("optional_writer_execution_supported_later") is not ready:
        raise ValueError("R53 R7 optional writer future support must match request readiness")
    if data.get("optional_writer_allowed_to_be_added_later_under_local_only_guard") is not ready:
        raise ValueError("R53 R7 optional writer allow flag must match request readiness")
    expected_optional_writer_decision = "REQUEST_READY_OPTIONAL_WRITER_NOT_CREATED_HERE" if ready else "REQUEST_BLOCKED_OPTIONAL_WRITER_NOT_CREATED_HERE"
    if data.get("optional_writer_decision_ref") != expected_optional_writer_decision:
        raise ValueError("R53 R7 optional writer decision ref mismatch")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R7_IMPLEMENTED_STEPS:
        raise ValueError("R53 R7 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R7_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R7 not-yet steps changed")
    if ready:
        if data.get("r6_manifest_ready_for_packet_generation_request") is not True or data.get("r6_manifest_ready_for_generation_request") is not True:
            raise ValueError("R53 R7 ready request requires ready R6 manifest")
        if data.get("r51_r5_next_required_step") != P7_R51_R5_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R7 ready R51 request must point to R51-6")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_generation_request_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R7 ready request must contain 24 packet request rows")
        for row in rows:
            for true_key in ("local_only_required", "must_not_export", "disposal_required", "body_free"):
                if row.get(true_key) is not True:
                    raise ValueError("R53 R7 packet request row local-only markers changed")
            for false_key in ("body_full_packet_materialized_here", "local_file_written_here", "local_absolute_path_included", "body_content_hash_stored_here"):
                if row.get(false_key) is not False:
                    raise ValueError("R53 R7 packet request row must remain request-only body-free")
        for true_key in (
            "local_only_required",
            "must_not_export",
            "disposal_required",
            "local_only_body_full_generation_allowed",
            "local_only_body_full_packet_generation_request_created_here",
            "body_full_packet_generation_request_created_here",
            "disposal_plan_ready",
            "packet_ref_ids_unique",
            "case_ref_ids_unique",
            "r53_6_24_case_manifest_freeze_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R7 ready request requires {true_key}=True")
        if data.get("case_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("requested_packet_ref_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("blind_case_id_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R7 ready request id counts changed")
        if blockers:
            raise ValueError("R53 R7 ready request must not carry blockers")
        if data.get("next_required_step") != P7_R53_R7_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R7 ready request must point to R53-8")
    else:
        if rows or data.get("packet_generation_request_row_count") != 0:
            raise ValueError("R53 R7 blocked request must not create packet request rows")
        if data.get("local_only_body_full_packet_generation_request_created_here") is not False:
            raise ValueError("R53 R7 blocked request must not claim request creation")
        if data.get("body_full_packet_generation_request_created_here") is not False:
            raise ValueError("R53 R7 blocked request must not claim body-full generation request creation")
        if data.get("next_required_step") != P7_R53_R7_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R7 blocked request must point to manifest/request resolution")
        if not blockers:
            raise ValueError("R53 R7 blocked request must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r7_local_only_body_full_packet_generation_request_bodyfree")
    return True



P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.packet_completeness_export_denylist_scan.bodyfree.v1"
)
P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.reviewer_instruction_rating_form_freeze.bodyfree.v1"
)

P7_R53_R8_NEXT_REQUIRED_STEP_REF: Final = "R53-9_reviewer_instruction_rating_form_freeze"
P7_R53_R8_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-8_packet_completeness_export_denylist_scan"
P7_R53_R9_NEXT_REQUIRED_STEP_REF: Final = "R53-10_actual_human_review_result_capture"
P7_R53_R9_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-8_packet_completeness_scan_before_R53-9_reviewer_instruction_rating_form"

P7_R53_R8_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R7_IMPLEMENTED_STEPS,
    "R53-8_packet_completeness_export_denylist_scan",
)
P7_R53_FUTURE_STEPS_AFTER_R9: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R7
    if step
    not in {
        "R53-8_packet_completeness_export_denylist_scan",
        "R53-9_reviewer_instruction_rating_form_freeze",
    }
)
P7_R53_R8_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-9_reviewer_instruction_rating_form_freeze",
    *P7_R53_FUTURE_STEPS_AFTER_R9,
)
P7_R53_R9_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R8_IMPLEMENTED_STEPS,
    "R53-9_reviewer_instruction_rating_form_freeze",
)
P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R9

P7_R53_R51_TO_R53_PACKET_SCAN_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_MANIFEST_OR_PACKET_BLOCKER_MAP,
    "r51_body_full_packet_generation_request_blocked": "r53_body_full_packet_generation_request_blocked",
    "r51_body_full_packet_generation_failed": "r53_packet_completeness_scan_failed",
    "r51_case_material_missing": "r53_packet_completion_evidence_missing",
    "r51_body_full_packet_export_violation": "r53_export_denylist_violation",
}
P7_R53_R51_TO_R53_REVIEWER_FORM_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_PACKET_SCAN_BLOCKER_MAP,
    "r51_body_full_packet_generation_request_blocked": "r53_body_full_packet_generation_request_blocked",
    "r51_body_full_packet_generation_failed": "r53_packet_completeness_scan_failed",
}

P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r7_generation_request_schema_version",
    "r7_generation_request_material_ref",
    "r7_generation_request_status",
    "r7_generation_request_ready_for_packet_scan",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r6_packet_completeness_scan_schema_version",
    "r51_r6_packet_completeness_scan_material_ref",
    "r51_r6_packet_completeness_scan_bodyfree",
    "r51_r6_packet_completeness_scan_status",
    "r51_r6_next_required_step",
    "r51_r6_execution_blocker_ids",
    "review_session_status",
    "packet_completeness_scan_status",
    "packet_completeness_scan_reason_refs",
    "required_case_count",
    "request_row_count",
    "packet_scan_row_count",
    "packet_scan_rows",
    "expected_packet_ref_count",
    "present_packet_ref_count",
    "missing_packet_ref_count",
    "incomplete_packet_ref_count",
    "required_packet_refs_count",
    "present_packet_refs_count",
    "blind_case_id_count",
    "case_ref_id_count",
    "packet_ref_ids_unique",
    "case_ref_ids_unique",
    "blind_case_ids_unique",
    "all_required_packets_present",
    "all_required_fields_present",
    "all_local_only_markers_present",
    "all_must_not_export_markers_present",
    "all_disposal_required_markers_present",
    "body_full_packet_completeness_verified",
    "export_denylist_patterns",
    "export_candidate_refs_checked_count",
    "denied_export_candidate_count",
    "export_denylist_violation_refs",
    "row_export_denylist_violation_count",
    "body_full_packet_export_violation_detected",
    "root_path_exposed",
    "local_absolute_path_included",
    "body_content_hash_stored_here",
    "packet_body_included_here",
    "packet_body_copied_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_packet_exported_allowed",
    "content_hash_of_body_stored_allowed",
    "export_candidate_refs_stored_here",
    "export_candidate_body_stored_here",
    "question_text_created_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r8_packet_completeness_scan_schema_version",
    "r8_packet_completeness_scan_material_ref",
    "r8_packet_completeness_scan_status",
    "r8_packet_completeness_ready_for_reviewer_instruction_rating_form",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r7_instruction_rating_form_schema_version",
    "r51_r7_instruction_rating_form_material_ref",
    "r51_r7_instruction_rating_form_bodyfree",
    "r51_r7_instruction_form_status",
    "r51_r7_next_required_step",
    "r51_r7_execution_blocker_ids",
    "review_session_status",
    "instruction_form_status",
    "instruction_form_reason_refs",
    "required_case_count",
    "packet_scan_row_count",
    "review_prompt_version",
    "reviewer_instruction_version",
    "rating_form_version",
    "reviewer_check_item_refs",
    "required_reviewer_check_label_refs",
    "reviewer_visible_field_refs",
    "reviewer_hidden_field_refs",
    "rating_row_schema_version_ref",
    "rating_row_required_field_refs",
    "rating_axis_refs",
    "rating_axis_target_refs",
    "rating_axis_count",
    "rating_score_min",
    "rating_score_max",
    "rating_score_canonical_refs",
    "extra_rating_axis_allowed",
    "machine_auto_score_allowed",
    "rating_row_required_for_each_case",
    "verdict_refs",
    "readfeel_blocker_id_refs",
    "red_or_repair_requires_blocker",
    "execution_blocker_is_not_readfeel_verdict",
    "question_need_observation_selection_required",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "repair_required_ref_refs",
    "question_text_required",
    "draft_question_text_allowed",
    "reviewer_free_text_local_only",
    "reviewer_free_text_bodyfree_export_allowed",
    "reviewer_free_text_to_sanitized_reason_ids_required",
    "p5_weakness_must_not_be_hidden_by_question_candidate",
    "body_full_reader_protocol_local_only",
    "blind_case_id_required",
    "case_ref_hidden_from_reviewer",
    "family_hidden_from_reviewer",
    "subscription_tier_hidden_from_reviewer",
    "controller_expected_result_hidden_from_reviewer",
    "gate_expected_result_hidden_from_reviewer",
    "p5_confirmed_conditions_hidden_from_reviewer",
    "p8_material_candidate_conditions_hidden_from_reviewer",
    "reviewer_instruction_materialized_for_actual_review_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "body_full_packet_completeness_verified",
    "local_only_body_full_generation_allowed",
    "p5_actual_review_still_not_run",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def _r53_map_r51_packet_scan_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_PACKET_SCAN_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=40,
        max_length=140,
    )


def _r53_map_r51_reviewer_form_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_REVIEWER_FORM_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=40,
        max_length=140,
    )


def _r53_packet_completion_reason_refs_from_r51(r51_reason_refs: Sequence[Any], blocker_ids: Sequence[Any]) -> list[str]:
    reason_refs = [
        f"r53_{clean_identifier(ref, default='packet_scan_blocked', max_length=120)}"
        for ref in r51_reason_refs
    ]
    if blocker_ids and "r53_packet_scan_blockers_visible" not in reason_refs:
        reason_refs.append("r53_packet_scan_blockers_visible")
    if not reason_refs:
        reason_refs.append("r53_packet_completeness_export_denylist_scan_blocked")
    return dedupe_identifiers(reason_refs, limit=40, max_length=160)


def build_p7_r53_packet_completeness_export_denylist_scan_bodyfree(
    *,
    local_only_body_full_packet_generation_request: Mapping[str, Any] | None = None,
    r7_local_only_body_full_packet_generation_request: Mapping[str, Any] | None = None,
    packet_completion_rows: Sequence[Mapping[str, Any]] | None = None,
    export_candidate_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r53_packet_completeness_export_denylist_scan_bodyfree",
) -> dict[str, Any]:
    """Build R53-8 body-free packet-completeness/export-denylist scan evidence.

    R53-7 intentionally does not write body-full packets.  Therefore this
    builder requires explicit body-free packet completion rows to claim the
    packets are present.  If rows are omitted, the scan is materialized as a
    truthful BLOCKED evidence object rather than inferring packet presence from
    the generation request alone.
    """

    if local_only_body_full_packet_generation_request is not None and r7_local_only_body_full_packet_generation_request is not None:
        raise ValueError("provide only one R53-7 packet generation request value")
    r7 = (
        safe_mapping(local_only_body_full_packet_generation_request)
        if local_only_body_full_packet_generation_request is not None
        else safe_mapping(r7_local_only_body_full_packet_generation_request)
        if r7_local_only_body_full_packet_generation_request is not None
        else build_p7_r53_local_only_body_full_packet_generation_request_bodyfree()
    )
    assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract(r7)
    r51_r5 = safe_mapping(r7.get("r51_r5_generation_request_bodyfree"))
    assert_p7_r51_local_only_body_full_packet_generation_request_bodyfree_contract(r51_r5)
    r7_ready = r7.get("generation_request_status") == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    r51_r6 = build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=r51_r5,
        packet_completion_rows=[] if packet_completion_rows is None else packet_completion_rows,
        export_candidate_refs=export_candidate_refs,
        material_id="p7_r53_adopted_r51_r6_packet_completeness_export_denylist_scan_bodyfree",
    )
    assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(r51_r6)
    r51_ready = r51_r6.get("packet_completeness_scan_status") == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    ready = r7_ready and r51_ready
    blockers = _r53_map_r51_packet_scan_blockers(
        [*(r7.get("execution_blocker_ids") or []), *(r51_r6.get("execution_blocker_ids") or [])]
    )
    if not r7_ready and "r53_7_packet_generation_request_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_7_packet_generation_request_not_ready"], limit=40, max_length=140)
    if r7_ready and packet_completion_rows is None and "r53_packet_completion_evidence_missing" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_packet_completion_evidence_missing"], limit=40, max_length=140)
    if r7_ready and not r51_ready and "r53_packet_completeness_scan_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_packet_completeness_scan_not_ready"], limit=40, max_length=140)
    if blockers:
        ready = False
    scan_status = (
        "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
        if ready
        else "BLOCKED_BY_R53_7_GENERATION_REQUEST"
        if not r7_ready
        else "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST"
    )
    scan = {
        "schema_version": P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-8_packet_completeness_export_denylist_scan",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_packet_completeness_export_denylist_scan_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r7.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r7_generation_request_schema_version": P7_R53_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION_REQUEST_SCHEMA_VERSION,
        "r7_generation_request_material_ref": clean_identifier(r7.get("material_id"), default="p7_r53_local_only_body_full_packet_generation_request_bodyfree", max_length=180),
        "r7_generation_request_status": clean_identifier(r7.get("generation_request_status"), default="BLOCKED_BY_R53_6_MANIFEST", max_length=120),
        "r7_generation_request_ready_for_packet_scan": r7_ready,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r6_packet_completeness_scan_schema_version": P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "r51_r6_packet_completeness_scan_material_ref": clean_identifier(r51_r6.get("material_id"), default="p7_r53_adopted_r51_r6_packet_scan", max_length=180),
        "r51_r6_packet_completeness_scan_bodyfree": r51_r6,
        "r51_r6_packet_completeness_scan_status": clean_identifier(r51_r6.get("packet_completeness_scan_status"), default="BLOCKED_BY_R51_5_GENERATION_REQUEST", max_length=120),
        "r51_r6_next_required_step": clean_identifier(r51_r6.get("next_required_step"), default=P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r6_execution_blocker_ids": dedupe_identifiers(r51_r6.get("execution_blocker_ids") or [], limit=40, max_length=140),
        "review_session_status": "R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_READY" if ready else "PRECHECK_BLOCKED",
        "packet_completeness_scan_status": scan_status,
        "packet_completeness_scan_reason_refs": ["r53_packet_completeness_export_denylist_verified_bodyfree"] if ready else _r53_packet_completion_reason_refs_from_r51(r51_r6.get("packet_completeness_scan_reason_refs") or [], blockers),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "request_row_count": _safe_non_negative_int_r53(r51_r6.get("request_row_count")),
        "packet_scan_row_count": _safe_non_negative_int_r53(r51_r6.get("packet_scan_row_count")),
        "packet_scan_rows": list(r51_r6.get("packet_scan_rows") or []),
        "expected_packet_ref_count": _safe_non_negative_int_r53(r51_r6.get("expected_packet_ref_count")),
        "present_packet_ref_count": _safe_non_negative_int_r53(r51_r6.get("present_packet_ref_count")),
        "missing_packet_ref_count": _safe_non_negative_int_r53(r51_r6.get("missing_packet_ref_count")),
        "incomplete_packet_ref_count": _safe_non_negative_int_r53(r51_r6.get("incomplete_packet_ref_count")),
        "required_packet_refs_count": _safe_non_negative_int_r53(r51_r6.get("required_packet_refs_count")),
        "present_packet_refs_count": _safe_non_negative_int_r53(r51_r6.get("present_packet_refs_count")),
        "blind_case_id_count": _safe_non_negative_int_r53(r51_r6.get("blind_case_id_count")),
        "case_ref_id_count": _safe_non_negative_int_r53(r51_r6.get("case_ref_id_count")),
        "packet_ref_ids_unique": r51_r6.get("packet_ref_ids_unique") is True,
        "case_ref_ids_unique": r51_r6.get("case_ref_ids_unique") is True,
        "blind_case_ids_unique": r51_r6.get("blind_case_ids_unique") is True,
        "all_required_packets_present": r51_r6.get("all_required_packets_present") is True,
        "all_required_fields_present": r51_r6.get("all_required_fields_present") is True,
        "all_local_only_markers_present": r51_r6.get("all_local_only_markers_present") is True,
        "all_must_not_export_markers_present": r51_r6.get("all_must_not_export_markers_present") is True,
        "all_disposal_required_markers_present": r51_r6.get("all_disposal_required_markers_present") is True,
        "body_full_packet_completeness_verified": ready,
        "export_denylist_patterns": list(r51_r6.get("export_denylist_patterns") or []),
        "export_candidate_refs_checked_count": _safe_non_negative_int_r53(r51_r6.get("export_candidate_refs_checked_count")),
        "denied_export_candidate_count": _safe_non_negative_int_r53(r51_r6.get("denied_export_candidate_count")),
        "export_denylist_violation_refs": dedupe_identifiers(r51_r6.get("export_denylist_violation_refs") or [], limit=40, max_length=160),
        "row_export_denylist_violation_count": _safe_non_negative_int_r53(r51_r6.get("row_export_denylist_violation_count")),
        "body_full_packet_export_violation_detected": r51_r6.get("body_full_packet_export_violation_detected") is True,
        "root_path_exposed": False,
        "local_absolute_path_included": False,
        "body_content_hash_stored_here": False,
        "packet_body_included_here": False,
        "packet_body_copied_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_packet_exported_allowed": False,
        "content_hash_of_body_stored_allowed": False,
        "export_candidate_refs_stored_here": False,
        "export_candidate_body_stored_here": False,
        "question_text_created_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "p5_actual_review_still_not_run": True,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r7.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r7.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": ready,
        "implemented_steps": list(P7_R53_R8_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R8_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R8_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R8_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract(scan)
    return scan


def assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract(scan: Mapping[str, Any]) -> bool:
    data = safe_mapping(scan)
    _assert_required_fields(
        data,
        required=P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS,
        source="p7_r53_r8_packet_completeness_export_denylist_scan_bodyfree",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        source="p7_r53_r8_packet_completeness_export_denylist_scan_bodyfree",
    )
    if data.get("policy_section") != "R53-8_packet_completeness_export_denylist_scan":
        raise ValueError("R53 R8 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R8 current refs changed")
    r51_r6 = safe_mapping(data.get("r51_r6_packet_completeness_scan_bodyfree"))
    assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(r51_r6)
    if data.get("r51_r6_packet_completeness_scan_schema_version") != P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION:
        raise ValueError("R53 R8 R51 R6 schema reference changed")
    if data.get("r51_r6_packet_completeness_scan_status") != r51_r6.get("packet_completeness_scan_status"):
        raise ValueError("R53 R8 R51 R6 status mismatch")
    rows = [safe_mapping(row) for row in (data.get("packet_scan_rows") or [])]
    for false_key in (
        "root_path_exposed",
        "local_absolute_path_included",
        "body_content_hash_stored_here",
        "packet_body_included_here",
        "packet_body_copied_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "local_packet_exported_allowed",
        "content_hash_of_body_stored_allowed",
        "export_candidate_refs_stored_here",
        "export_candidate_body_stored_here",
        "question_text_created_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R8 must keep {false_key}=False")
    for row in rows:
        for false_key in (
            "body_full_packet_materialized_here",
            "body_full_packet_body_copied_here",
            "local_absolute_path_included",
            "body_content_hash_stored_here",
        ):
            if row.get(false_key) is not False:
                raise ValueError("R53 R8 packet scan rows must not expose body/path/hash")
        if row.get("body_free") is not True:
            raise ValueError("R53 R8 packet scan rows must remain body-free")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R8 open blockers must match execution blockers")
    ready = data.get("packet_completeness_scan_status") == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    if data.get("body_full_packet_completeness_verified") is not ready:
        raise ValueError("R53 R8 completeness verified flag must match scan readiness")
    if data.get("r53_8_packet_completeness_export_denylist_scan_built") is not ready:
        raise ValueError("R53 R8 built flag must match scan readiness")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R8_IMPLEMENTED_STEPS:
        raise ValueError("R53 R8 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R8_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R8 not-yet steps changed")
    if ready:
        if data.get("r7_generation_request_ready_for_packet_scan") is not True:
            raise ValueError("R53 R8 ready scan requires ready R7 generation request")
        if data.get("r51_r6_next_required_step") != P7_R51_R6_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R8 ready R51 R6 must point to R51-7")
        if len(rows) != P7_R51_REQUIRED_CASE_COUNT or data.get("packet_scan_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R8 ready scan must have 24 body-free scan rows")
        for true_key in (
            "packet_ref_ids_unique",
            "case_ref_ids_unique",
            "blind_case_ids_unique",
            "all_required_packets_present",
            "all_required_fields_present",
            "all_local_only_markers_present",
            "all_must_not_export_markers_present",
            "all_disposal_required_markers_present",
            "p5_actual_review_still_not_run",
            "r53_7_local_only_body_full_packet_generation_request_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R8 ready scan requires {true_key}=True")
        if data.get("body_full_packet_export_violation_detected") is not False or data.get("denied_export_candidate_count") != 0:
            raise ValueError("R53 R8 ready scan must have no export denylist violation")
        if blockers:
            raise ValueError("R53 R8 ready scan must not carry blockers")
        if data.get("next_required_step") != P7_R53_R8_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R8 ready scan must point to R53-9")
    else:
        if data.get("next_required_step") != P7_R53_R8_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R8 blocked scan must point to scan resolution")
        if data.get("r51_r6_next_required_step") != P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R8 blocked R51 R6 must point to packet scan resolution")
        if not blockers:
            raise ValueError("R53 R8 blocked scan must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r8_packet_completeness_export_denylist_scan_bodyfree")
    return True


def build_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree(
    *,
    packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    r8_packet_completeness_export_denylist_scan: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_reviewer_instruction_rating_form_freeze_bodyfree",
) -> dict[str, Any]:
    """Build R53-9 body-free reviewer instruction/rating-form freeze.

    This freezes reviewer instructions, rating axes, verdict refs, and question
    observation selection refs.  It does not run review, create reviewer notes,
    materialize rating rows, or finalize P8 question implementation specs.
    """

    if packet_completeness_export_denylist_scan is not None and r8_packet_completeness_export_denylist_scan is not None:
        raise ValueError("provide only one R53-8 packet scan value")
    r8 = (
        safe_mapping(packet_completeness_export_denylist_scan)
        if packet_completeness_export_denylist_scan is not None
        else safe_mapping(r8_packet_completeness_export_denylist_scan)
        if r8_packet_completeness_export_denylist_scan is not None
        else build_p7_r53_packet_completeness_export_denylist_scan_bodyfree()
    )
    assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract(r8)
    r51_r6 = safe_mapping(r8.get("r51_r6_packet_completeness_scan_bodyfree"))
    assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(r51_r6)
    r51_r7 = build_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree(
        body_full_packet_completeness_export_denylist_scan=r51_r6,
        material_id="p7_r53_adopted_r51_r7_reviewer_instruction_rating_form_freeze_bodyfree",
    )
    assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(r51_r7)
    r8_ready = r8.get("packet_completeness_scan_status") == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    r51_ready = r51_r7.get("instruction_form_status") == "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN"
    ready = r8_ready and r51_ready
    blockers = _r53_map_r51_reviewer_form_blockers(
        [*(r8.get("execution_blocker_ids") or []), *(r51_r7.get("execution_blocker_ids") or [])]
    )
    if not r8_ready and "r53_8_packet_completeness_scan_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_8_packet_completeness_scan_not_ready"], limit=40, max_length=140)
    if r8_ready and not r51_ready and "r53_reviewer_instruction_rating_form_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_reviewer_instruction_rating_form_not_ready"], limit=40, max_length=140)
    if blockers:
        ready = False
    form = {
        "schema_version": P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-9_reviewer_instruction_rating_form_freeze",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_reviewer_instruction_rating_form_freeze_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r8.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r8_packet_completeness_scan_schema_version": P7_R53_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION,
        "r8_packet_completeness_scan_material_ref": clean_identifier(r8.get("material_id"), default="p7_r53_packet_completeness_export_denylist_scan_bodyfree", max_length=180),
        "r8_packet_completeness_scan_status": clean_identifier(r8.get("packet_completeness_scan_status"), default="BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST", max_length=120),
        "r8_packet_completeness_ready_for_reviewer_instruction_rating_form": r8_ready,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r7_instruction_rating_form_schema_version": P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "r51_r7_instruction_rating_form_material_ref": clean_identifier(r51_r7.get("material_id"), default="p7_r53_adopted_r51_r7_reviewer_instruction_rating_form", max_length=180),
        "r51_r7_instruction_rating_form_bodyfree": r51_r7,
        "r51_r7_instruction_form_status": clean_identifier(r51_r7.get("instruction_form_status"), default="BLOCKED_BY_R51_6_PACKET_COMPLETENESS_SCAN", max_length=120),
        "r51_r7_next_required_step": clean_identifier(r51_r7.get("next_required_step"), default=P7_R51_R7_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r7_execution_blocker_ids": dedupe_identifiers(r51_r7.get("execution_blocker_ids") or [], limit=40, max_length=140),
        "review_session_status": "R53_REVIEWER_INSTRUCTION_RATING_FORM_READY" if ready else "PRECHECK_BLOCKED",
        "instruction_form_status": "READY_FOR_ACTUAL_REVIEW_RESULT_CAPTURE" if ready else "BLOCKED_BY_R53_8_PACKET_COMPLETENESS_SCAN",
        "instruction_form_reason_refs": ["r53_reviewer_instruction_rating_form_frozen_without_running_review"] if ready else dedupe_identifiers([*r51_r7.get("instruction_form_reason_refs", []), *blockers], limit=40, max_length=160),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "packet_scan_row_count": _safe_non_negative_int_r53(r51_r7.get("packet_scan_row_count")),
        "review_prompt_version": clean_identifier(r51_r7.get("review_prompt_version"), default=P7_R51_REVIEW_PROMPT_VERSION, max_length=180),
        "reviewer_instruction_version": clean_identifier(r51_r7.get("reviewer_instruction_version"), default="p7_reviewer_instruction", max_length=180),
        "rating_form_version": clean_identifier(r51_r7.get("rating_form_version"), default="p7_rating_form", max_length=180),
        "reviewer_check_item_refs": list(r51_r7.get("reviewer_check_item_refs") or []),
        "required_reviewer_check_label_refs": list(r51_r7.get("required_reviewer_check_label_refs") or []),
        "reviewer_visible_field_refs": list(r51_r7.get("reviewer_visible_field_refs") or []),
        "reviewer_hidden_field_refs": list(r51_r7.get("reviewer_hidden_field_refs") or []),
        "rating_row_schema_version_ref": clean_identifier(r51_r7.get("rating_row_schema_version_ref"), default="rating_row_schema", max_length=220),
        "rating_row_required_field_refs": list(r51_r7.get("rating_row_required_field_refs") or []),
        "rating_axis_refs": list(r51_r7.get("rating_axis_refs") or []),
        "rating_axis_target_refs": dict(safe_mapping(r51_r7.get("rating_axis_target_refs"))),
        "rating_axis_count": _safe_non_negative_int_r53(r51_r7.get("rating_axis_count")),
        "rating_score_min": r51_r7.get("rating_score_min"),
        "rating_score_max": r51_r7.get("rating_score_max"),
        "rating_score_canonical_refs": list(r51_r7.get("rating_score_canonical_refs") or []),
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "rating_row_required_for_each_case": r51_r7.get("rating_row_required_for_each_case") is True,
        "verdict_refs": list(r51_r7.get("verdict_refs") or []),
        "readfeel_blocker_id_refs": list(r51_r7.get("readfeel_blocker_id_refs") or []),
        "red_or_repair_requires_blocker": r51_r7.get("red_or_repair_requires_blocker") is True,
        "execution_blocker_is_not_readfeel_verdict": r51_r7.get("execution_blocker_is_not_readfeel_verdict") is True,
        "question_need_observation_selection_required": r51_r7.get("question_need_observation_selection_required") is True,
        "question_need_primary_class_refs": list(r51_r7.get("question_need_primary_class_refs") or []),
        "ambiguity_kind_refs": list(r51_r7.get("ambiguity_kind_refs") or []),
        "one_question_fit_refs": list(r51_r7.get("one_question_fit_refs") or []),
        "repair_required_ref_refs": list(r51_r7.get("repair_required_ref_refs") or []),
        "question_text_required": False,
        "draft_question_text_allowed": False,
        "reviewer_free_text_local_only": r51_r7.get("reviewer_free_text_local_only") is True,
        "reviewer_free_text_bodyfree_export_allowed": False,
        "reviewer_free_text_to_sanitized_reason_ids_required": r51_r7.get("reviewer_free_text_to_sanitized_reason_ids_required") is True,
        "p5_weakness_must_not_be_hidden_by_question_candidate": r51_r7.get("p5_weakness_must_not_be_hidden_by_question_candidate") is True,
        "body_full_reader_protocol_local_only": r51_r7.get("body_full_reader_protocol_local_only") is True,
        "blind_case_id_required": r51_r7.get("blind_case_id_required") is True,
        "case_ref_hidden_from_reviewer": r51_r7.get("case_ref_hidden_from_reviewer") is True,
        "family_hidden_from_reviewer": r51_r7.get("family_hidden_from_reviewer") is True,
        "subscription_tier_hidden_from_reviewer": r51_r7.get("subscription_tier_hidden_from_reviewer") is True,
        "controller_expected_result_hidden_from_reviewer": r51_r7.get("controller_expected_result_hidden_from_reviewer") is True,
        "gate_expected_result_hidden_from_reviewer": r51_r7.get("gate_expected_result_hidden_from_reviewer") is True,
        "p5_confirmed_conditions_hidden_from_reviewer": r51_r7.get("p5_confirmed_conditions_hidden_from_reviewer") is True,
        "p8_material_candidate_conditions_hidden_from_reviewer": r51_r7.get("p8_material_candidate_conditions_hidden_from_reviewer") is True,
        "reviewer_instruction_materialized_for_actual_review_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_human_review_run_here": False,
        "actual_manual_review_run_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "body_full_packet_completeness_verified": r8.get("body_full_packet_completeness_verified") is True and r51_r7.get("body_full_packet_completeness_verified") is True,
        "local_only_body_full_generation_allowed": ready,
        "p5_actual_review_still_not_run": True,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r8.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r8.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r8.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R53_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R9_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R9_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    assert_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree_contract(form)
    return form


def assert_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree_contract(form: Mapping[str, Any]) -> bool:
    data = safe_mapping(form)
    _assert_required_fields(
        data,
        required=P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS,
        source="p7_r53_r9_reviewer_instruction_rating_form_freeze_bodyfree",
    )
    _assert_body_free_common(
        data,
        schema_version=P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        source="p7_r53_r9_reviewer_instruction_rating_form_freeze_bodyfree",
    )
    if data.get("policy_section") != "R53-9_reviewer_instruction_rating_form_freeze":
        raise ValueError("R53 R9 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R9 current refs changed")
    r51_r7 = safe_mapping(data.get("r51_r7_instruction_rating_form_bodyfree"))
    assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(r51_r7)
    if data.get("r51_r7_instruction_rating_form_schema_version") != P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION:
        raise ValueError("R53 R9 R51 R7 schema reference changed")
    if data.get("r51_r7_instruction_form_status") != r51_r7.get("instruction_form_status"):
        raise ValueError("R53 R9 R51 R7 status mismatch")
    for false_key in (
        "extra_rating_axis_allowed",
        "machine_auto_score_allowed",
        "question_text_required",
        "draft_question_text_allowed",
        "reviewer_free_text_bodyfree_export_allowed",
        "reviewer_instruction_materialized_for_actual_review_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R9 must keep {false_key}=False")
    for true_key in (
        "rating_row_required_for_each_case",
        "red_or_repair_requires_blocker",
        "execution_blocker_is_not_readfeel_verdict",
        "question_need_observation_selection_required",
        "reviewer_free_text_local_only",
        "reviewer_free_text_to_sanitized_reason_ids_required",
        "p5_weakness_must_not_be_hidden_by_question_candidate",
        "body_full_reader_protocol_local_only",
        "blind_case_id_required",
        "case_ref_hidden_from_reviewer",
        "family_hidden_from_reviewer",
        "subscription_tier_hidden_from_reviewer",
        "controller_expected_result_hidden_from_reviewer",
        "gate_expected_result_hidden_from_reviewer",
        "p5_confirmed_conditions_hidden_from_reviewer",
        "p8_material_candidate_conditions_hidden_from_reviewer",
        "p5_actual_review_still_not_run",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R9 must keep {true_key}=True")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R9 open blockers must match execution blockers")
    if tuple(data.get("rating_axis_refs") or ()) != tuple(r51_r7.get("rating_axis_refs") or ()):  # preserves P5 six-axis form through R51 contract
        raise ValueError("R53 R9 rating axes must match adopted R51 R7 axes")
    if data.get("rating_axis_count") != 6:
        raise ValueError("R53 R9 must keep the six P5 rating axes")
    if data.get("rating_score_min") != 0.0 or data.get("rating_score_max") != 1.0:
        raise ValueError("R53 R9 rating score bounds changed")
    ready = data.get("instruction_form_status") == "READY_FOR_ACTUAL_REVIEW_RESULT_CAPTURE"
    if data.get("r53_9_reviewer_instruction_rating_form_freeze_built") is not ready:
        raise ValueError("R53 R9 built flag must match instruction form readiness")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R9_IMPLEMENTED_STEPS:
        raise ValueError("R53 R9 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R9 not-yet steps changed")
    if ready:
        if data.get("r8_packet_completeness_ready_for_reviewer_instruction_rating_form") is not True:
            raise ValueError("R53 R9 ready form requires R8 packet scan readiness")
        if data.get("r51_r7_next_required_step") != P7_R51_R7_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R9 ready R51 R7 must point to R51-8")
        if data.get("body_full_packet_completeness_verified") is not True:
            raise ValueError("R53 R9 ready form requires body-free packet completeness verification")
        if data.get("local_only_body_full_generation_allowed") is not True:
            raise ValueError("R53 R9 ready form preserves local-only review permission")
        if blockers:
            raise ValueError("R53 R9 ready form must not carry blockers")
        if data.get("next_required_step") != P7_R53_R9_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R9 ready form must point to R53-10")
    else:
        if data.get("local_only_body_full_generation_allowed") is not False:
            raise ValueError("R53 R9 blocked form must not preserve local-only review permission")
        if data.get("r51_r7_next_required_step") != P7_R51_R7_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R9 blocked R51 R7 must point to packet scan resolution")
        if data.get("next_required_step") != P7_R53_R9_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R9 blocked form must point to R53-8 resolution")
        if not blockers:
            raise ValueError("R53 R9 blocked form must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r9_reviewer_instruction_rating_form_freeze_bodyfree")
    return True





# ---------------------------------------------------------------------------
# R53-10 / R53-11: sanitized actual review capture and rating-row normalization
# ---------------------------------------------------------------------------

P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.actual_human_review_result_capture.bodyfree.v1"
)
P7_R53_RATING_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.rating_row_normalization.bodyfree.v1"
)

P7_R53_R10_NEXT_REQUIRED_STEP_REF: Final = "R53-11_rating_row_normalization"
P7_R53_R10_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-9_reviewer_instruction_rating_form_before_R53-10_actual_review_capture"
)
P7_R53_R11_NEXT_REQUIRED_STEP_REF: Final = "R53-12_readfeel_blocker_execution_blocker_ingestion"
P7_R53_R11_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-10_actual_review_result_capture_before_R53-11_rating_row_normalization"
)

P7_R53_R10_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R9_IMPLEMENTED_STEPS,
    "R53-10_actual_human_review_result_capture",
)
P7_R53_FUTURE_STEPS_AFTER_R11: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R9
    if step
    not in {
        "R53-10_actual_human_review_result_capture",
        "R53-11_rating_row_normalization",
    }
)
P7_R53_R10_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-11_rating_row_normalization",
    *P7_R53_FUTURE_STEPS_AFTER_R11,
)
P7_R53_R11_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R10_IMPLEMENTED_STEPS,
    "R53-11_rating_row_normalization",
)
P7_R53_R11_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R11

P7_R53_R51_TO_R53_ACTUAL_REVIEW_CAPTURE_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_REVIEWER_FORM_BLOCKER_MAP,
    "r51_reviewer_instruction_rating_form_not_ready": "r53_reviewer_instruction_rating_form_not_ready",
    "r51_actual_review_not_run": "r53_actual_review_result_rows_missing",
    "r51_review_result_rows_incomplete": "r53_actual_review_result_rows_incomplete",
    "r51_rating_rows_incomplete": "r53_actual_review_result_rows_incomplete",
    "r51_case_manifest_incomplete": "r53_case_manifest_material_missing",
}
P7_R53_R51_TO_R53_RATING_ROW_NORMALIZATION_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_ACTUAL_REVIEW_CAPTURE_BLOCKER_MAP,
    "r51_actual_review_not_run": "r53_actual_review_capture_not_ready",
    "r51_review_result_rows_incomplete": "r53_actual_review_capture_rows_incomplete",
    "r51_actual_review_result_rows_not_complete": "r53_actual_review_capture_rows_incomplete",
    "r51_actual_review_result_case_set_mismatch": "r53_actual_review_result_case_set_mismatch",
    "r51_rating_rows_incomplete": "r53_rating_rows_incomplete",
}

P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r9_reviewer_instruction_schema_version",
    "r9_reviewer_instruction_material_ref",
    "r9_instruction_form_status",
    "r9_ready_for_actual_review_capture",
    "r6_manifest_schema_version",
    "r6_manifest_material_ref",
    "r6_manifest_status",
    "r6_manifest_ready_for_actual_review_capture",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r8_actual_human_review_run_schema_version",
    "r51_r8_actual_human_review_run_material_ref",
    "r51_r8_actual_human_review_run_bodyfree",
    "r51_r8_actual_review_run_status",
    "r51_r8_next_required_step",
    "r51_r8_execution_blocker_ids",
    "review_session_status",
    "actual_review_run_status",
    "actual_review_run_reason_refs",
    "review_prompt_version",
    "reviewer_instruction_version",
    "rating_form_version",
    "reviewer_ref",
    "reviewed_at_ref",
    "review_result_capture_row_field_refs",
    "review_result_capture_rows",
    "review_result_capture_row_count",
    "reviewed_blind_case_id_count",
    "reviewed_case_ref_id_count",
    "reviewed_packet_ref_id_count",
    "all_24_cases_reviewed",
    "rating_selections_captured_bodyfree",
    "question_need_observation_selections_captured_bodyfree",
    "body_full_reader_protocol_local_only",
    "reviewer_free_text_local_only",
    "reviewer_free_text_bodyfree_export_allowed",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "raw_input_or_returned_surface_included",
    "machine_auto_score_allowed",
    "machine_metrics_used_for_readfeel",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_review_result_rows_captured_here",
    "actual_rating_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "p5_actual_review_still_not_run",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r10_actual_review_capture_schema_version",
    "r10_actual_review_capture_material_ref",
    "r10_actual_review_run_status",
    "r10_actual_review_capture_ready_for_rating_normalization",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r9_rating_row_normalizer_schema_version",
    "r51_r9_rating_row_normalizer_material_ref",
    "r51_r9_rating_row_normalizer_bodyfree",
    "r51_r9_rating_row_normalizer_status",
    "r51_r9_next_required_step",
    "r51_r9_execution_blocker_ids",
    "review_session_status",
    "rating_row_normalizer_status",
    "rating_row_normalizer_reason_refs",
    "required_case_count",
    "review_result_capture_row_count",
    "rating_row_count",
    "rating_rows",
    "rating_row_schema_version",
    "r51_rating_row_schema_version_ref",
    "rating_row_required_field_refs",
    "rating_axis_refs",
    "rating_axis_target_refs",
    "rating_score_min",
    "rating_score_max",
    "missing_axis_scores_pass_allowed",
    "extra_rating_axis_allowed",
    "machine_auto_score_allowed",
    "machine_metrics_used_for_readfeel_allowed",
    "reviewer_free_text_bodyfree_allowed",
    "sanitized_reason_ids_only",
    "blocker_ids_only",
    "allowed_verdict_refs",
    "readfeel_blocker_id_refs",
    "blocked_or_not_reviewable_must_use_execution_blocker_row",
    "red_or_repair_requires_blocker",
    "pass_requires_targets_and_no_blockers",
    "body_removed_may_be_false_before_disposal",
    "rating_rows_are_bodyfree",
    "all_required_rating_rows_present",
    "rating_case_ref_sets_match_review_capture",
    "verdict_counts",
    "blocker_row_candidate_count",
    "execution_blocker_row_candidate_count",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "p5_actual_review_still_not_run",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_R10_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
)
P7_R53_R11_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
)


def _r53_map_r51_actual_review_capture_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_ACTUAL_REVIEW_CAPTURE_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=40,
        max_length=140,
    )


def _r53_map_r51_rating_row_normalizer_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_RATING_ROW_NORMALIZATION_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=40,
        max_length=140,
    )


def _r53_prefixed_reason_refs(reason_refs: Sequence[Any], *, default: str, blocker_ids: Sequence[Any]) -> list[str]:
    refs = [f"r53_{clean_identifier(ref, default=default, max_length=120)}" for ref in reason_refs]
    if blocker_ids:
        refs.append(f"{default}_blockers_visible")
    if not refs:
        refs.append(default)
    return dedupe_identifiers(refs, limit=40, max_length=160)


def _assert_r53_actual_review_capture_row_bodyfree(row: Mapping[str, Any]) -> bool:
    data = safe_mapping(row)
    _assert_required_fields(
        data,
        required=P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS,
        source="p7_r53_r10_actual_review_capture_row",
    )
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r10_actual_review_capture_row")
    if data.get("body_free") is not True:
        raise ValueError("R53 R10 capture rows must be body-free")
    for false_key in (
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "machine_auto_score_used",
        "machine_metrics_used_for_readfeel",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R10 capture row must keep {false_key}=False")
    if data.get("body_removed") is not False:
        raise ValueError("R53 R10 capture row must keep body_removed=False before R53-16 disposal")
    return True


def build_p7_r53_actual_human_review_result_capture_bodyfree(
    *,
    reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    r9_reviewer_instruction_rating_form_freeze: Mapping[str, Any] | None = None,
    case_manifest_freeze: Mapping[str, Any] | None = None,
    r6_24_case_manifest_freeze: Mapping[str, Any] | None = None,
    review_result_rows: Sequence[Mapping[str, Any]] | None = None,
    reviewer_ref: Any = "pseudonymous_reviewer_r53_local_manual_run",
    reviewed_at: Any = "local_review_time_ref_only",
    material_id: Any = "p7_r53_actual_human_review_result_capture_bodyfree",
) -> dict[str, Any]:
    """Build R53-10 body-free capture of sanitized actual human review selections."""

    if reviewer_instruction_rating_form_freeze is not None and r9_reviewer_instruction_rating_form_freeze is not None:
        raise ValueError("provide only one R53-9 reviewer instruction form value")
    if case_manifest_freeze is not None and r6_24_case_manifest_freeze is not None:
        raise ValueError("provide only one R53-6 manifest value")
    r9 = (
        safe_mapping(reviewer_instruction_rating_form_freeze)
        if reviewer_instruction_rating_form_freeze is not None
        else safe_mapping(r9_reviewer_instruction_rating_form_freeze)
        if r9_reviewer_instruction_rating_form_freeze is not None
        else build_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree()
    )
    assert_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree_contract(r9)
    r6 = (
        safe_mapping(case_manifest_freeze)
        if case_manifest_freeze is not None
        else safe_mapping(r6_24_case_manifest_freeze)
        if r6_24_case_manifest_freeze is not None
        else build_p7_r53_24_case_manifest_freeze_bodyfree()
    )
    assert_p7_r53_24_case_manifest_freeze_bodyfree_contract(r6)
    r51_r7 = safe_mapping(r9.get("r51_r7_instruction_rating_form_bodyfree"))
    assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(r51_r7)
    r51_r4 = safe_mapping(r6.get("r51_r4_manifest_bodyfree"))
    assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(r51_r4)

    r9_ready = r9.get("instruction_form_status") == "READY_FOR_ACTUAL_REVIEW_RESULT_CAPTURE" and not r9.get("execution_blocker_ids")
    r6_ready = r6.get("manifest_status") == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST" and not r6.get("execution_blocker_ids")
    # R53 accepts only sanitized selection rows. Body hashes are body-full
    # derived material, so R53 rejects them before delegating to R51 R8.
    for row in review_result_rows or ():
        row_data = safe_mapping(row)
        for forbidden_hash_key in (
            "body_hash",
            "body_content_hash",
            "packet_hash",
            "packet_content_hash",
            "content_hash",
        ):
            if forbidden_hash_key in row_data:
                raise ValueError("R53 R10 review capture rows must not include body or packet hashes")
    r51_r8 = build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=r51_r7,
        case_manifest_freeze=r51_r4,
        review_result_rows=[] if review_result_rows is None else review_result_rows,
        reviewer_ref=reviewer_ref,
        reviewed_at=reviewed_at,
        material_id="p7_r53_adopted_r51_r8_actual_human_review_run_bodyfree",
    )
    r51_ready = r51_r8.get("actual_review_run_status") == "READY_FOR_RATING_ROW_NORMALIZATION" and not r51_r8.get("execution_blocker_ids")
    assert_p7_r51_actual_human_review_run_bodyfree_contract(
        r51_r8,
        allowed_true_false_key_refs=P7_R53_R10_ALLOWED_TRUE_FALSE_KEY_REFS if r51_ready else (),
    )
    blockers = _r53_map_r51_actual_review_capture_blockers(
        [*(r9.get("execution_blocker_ids") or []), *(r6.get("execution_blocker_ids") or []), *(r51_r8.get("execution_blocker_ids") or [])]
    )
    if not r9_ready:
        blockers = dedupe_identifiers([*blockers, "r53_reviewer_instruction_rating_form_not_ready"], limit=40, max_length=140)
    if not r6_ready:
        blockers = dedupe_identifiers([*blockers, "r53_case_manifest_material_missing"], limit=40, max_length=140)
    if r9_ready and r6_ready and review_result_rows is None:
        blockers = dedupe_identifiers([*blockers, "r53_actual_review_result_rows_missing"], limit=40, max_length=140)
    if r9_ready and r6_ready and not r51_ready:
        blockers = dedupe_identifiers([*blockers, "r53_actual_review_result_rows_incomplete"], limit=40, max_length=140)
    ready = r9_ready and r6_ready and r51_ready and not blockers
    capture_rows = [safe_mapping(row) for row in (r51_r8.get("review_result_capture_rows") or [])] if ready else []
    for row in capture_rows:
        _assert_r53_actual_review_capture_row_bodyfree(row)
    capture = {
        "schema_version": P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-10_actual_human_review_result_capture",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_actual_human_review_result_capture_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r9.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r9_reviewer_instruction_schema_version": P7_R53_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION,
        "r9_reviewer_instruction_material_ref": clean_identifier(r9.get("material_id"), default="p7_r53_reviewer_instruction_rating_form_freeze_bodyfree", max_length=180),
        "r9_instruction_form_status": clean_identifier(r9.get("instruction_form_status"), default="BLOCKED_BY_R53_8_PACKET_COMPLETENESS_SCAN", max_length=120),
        "r9_ready_for_actual_review_capture": r9_ready,
        "r6_manifest_schema_version": P7_R53_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION,
        "r6_manifest_material_ref": clean_identifier(r6.get("material_id"), default="p7_r53_24_case_manifest_freeze_bodyfree", max_length=180),
        "r6_manifest_status": clean_identifier(r6.get("manifest_status"), default="BLOCKED_BY_R53_5_ENVELOPE", max_length=120),
        "r6_manifest_ready_for_actual_review_capture": r6_ready,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r8_actual_human_review_run_schema_version": P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION,
        "r51_r8_actual_human_review_run_material_ref": clean_identifier(r51_r8.get("material_id"), default="p7_r53_adopted_r51_r8_actual_human_review_run_bodyfree", max_length=180),
        "r51_r8_actual_human_review_run_bodyfree": r51_r8,
        "r51_r8_actual_review_run_status": clean_identifier(r51_r8.get("actual_review_run_status"), default="BLOCKED_BY_R51_7_REVIEWER_INSTRUCTION_RATING_FORM", max_length=120),
        "r51_r8_next_required_step": clean_identifier(r51_r8.get("next_required_step"), default=P7_R51_R8_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r8_execution_blocker_ids": dedupe_identifiers(r51_r8.get("execution_blocker_ids") or [], limit=40, max_length=140),
        "review_session_status": "R53_ACTUAL_REVIEW_RESULT_CAPTURE_READY" if ready else "PRECHECK_BLOCKED",
        "actual_review_run_status": "READY_FOR_RATING_ROW_NORMALIZATION" if ready else "BLOCKED_BY_R53_9_OR_MISSING_SANITIZED_REVIEW_RESULTS",
        "actual_review_run_reason_refs": ["r53_actual_human_review_results_captured_bodyfree"] if ready else _r53_prefixed_reason_refs(r51_r8.get("actual_review_run_reason_refs") or [], default="r53_actual_review_result_capture_blocked", blocker_ids=blockers),
        "review_prompt_version": clean_identifier(r51_r8.get("review_prompt_version"), default=P7_R51_REVIEW_PROMPT_VERSION, max_length=180),
        "reviewer_instruction_version": clean_identifier(r51_r8.get("reviewer_instruction_version"), default="p7_reviewer_instruction", max_length=180),
        "rating_form_version": clean_identifier(r51_r8.get("rating_form_version"), default="p7_rating_form", max_length=180),
        "reviewer_ref": clean_identifier(reviewer_ref, default="pseudonymous_reviewer_r53_local_manual_run", max_length=120),
        "reviewed_at_ref": clean_identifier(reviewed_at, default="local_review_time_ref_only", max_length=120),
        "review_result_capture_row_field_refs": list(P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS),
        "review_result_capture_rows": capture_rows,
        "review_result_capture_row_count": len(capture_rows),
        "reviewed_blind_case_id_count": _safe_non_negative_int_r53(r51_r8.get("reviewed_blind_case_id_count")) if ready else 0,
        "reviewed_case_ref_id_count": _safe_non_negative_int_r53(r51_r8.get("reviewed_case_ref_id_count")) if ready else 0,
        "reviewed_packet_ref_id_count": _safe_non_negative_int_r53(r51_r8.get("reviewed_packet_ref_id_count")) if ready else 0,
        "all_24_cases_reviewed": ready,
        "rating_selections_captured_bodyfree": ready,
        "question_need_observation_selections_captured_bodyfree": ready,
        "body_full_reader_protocol_local_only": True,
        "reviewer_free_text_local_only": True,
        "reviewer_free_text_bodyfree_export_allowed": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "raw_input_or_returned_surface_included": False,
        "machine_auto_score_allowed": False,
        "machine_metrics_used_for_readfeel": False,
        **_false_flags(),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": ready,
        "actual_manual_review_run_here": ready,
        "actual_review_result_rows_captured_here": ready,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r6_ready,
        "r53_7_local_only_body_full_packet_generation_request_built": r9.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r9.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r9.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": ready,
        "implemented_steps": list(P7_R53_R10_IMPLEMENTED_STEPS if ready else P7_R53_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R10_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R10_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R10_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_actual_human_review_result_capture_bodyfree_contract(capture)
    return capture


def assert_p7_r53_actual_human_review_result_capture_bodyfree_contract(capture: Mapping[str, Any]) -> bool:
    data = safe_mapping(capture)
    _assert_required_fields(data, required=P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS, source="p7_r53_r10_actual_human_review_result_capture_bodyfree")
    ready = data.get("actual_review_run_status") == "READY_FOR_RATING_ROW_NORMALIZATION"
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        source="p7_r53_r10_actual_human_review_result_capture_bodyfree",
        allowed_true_false_key_refs=P7_R53_R10_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("policy_section") != "R53-10_actual_human_review_result_capture":
        raise ValueError("R53 R10 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R10 current refs changed")
    r51_r8 = safe_mapping(data.get("r51_r8_actual_human_review_run_bodyfree"))
    assert_p7_r51_actual_human_review_run_bodyfree_contract(
        r51_r8,
        allowed_true_false_key_refs=P7_R53_R10_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("r51_r8_actual_human_review_run_schema_version") != P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION:
        raise ValueError("R53 R10 R51 R8 schema reference changed")
    if data.get("r51_r8_actual_review_run_status") != r51_r8.get("actual_review_run_status"):
        raise ValueError("R53 R10 R51 R8 status mismatch")
    for row in data.get("review_result_capture_rows") or []:
        _assert_r53_actual_review_capture_row_bodyfree(safe_mapping(row))
    for true_key in ("body_full_reader_protocol_local_only", "reviewer_free_text_local_only"):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R10 must keep {true_key}=True")
    for false_key in (
        "reviewer_free_text_bodyfree_export_allowed",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "raw_input_or_returned_surface_included",
        "machine_auto_score_allowed",
        "machine_metrics_used_for_readfeel",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_reviewer_notes_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R10 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R10 open blockers must match execution blockers")
    if data.get("r53_10_actual_human_review_result_capture_built") is not ready:
        raise ValueError("R53 R10 built flag must match readiness")
    if ready:
        if data.get("r9_ready_for_actual_review_capture") is not True or data.get("r6_manifest_ready_for_actual_review_capture") is not True:
            raise ValueError("R53 R10 ready capture requires ready R9 form and R6 manifest")
        if data.get("r51_r8_next_required_step") != P7_R51_R8_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R10 ready R51 R8 must point to R51-9")
        if data.get("review_result_capture_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R10 ready capture must contain 24 capture rows")
        if data.get("all_24_cases_reviewed") is not True:
            raise ValueError("R53 R10 ready capture must mark all 24 cases reviewed")
        if data.get("rating_selections_captured_bodyfree") is not True or data.get("question_need_observation_selections_captured_bodyfree") is not True:
            raise ValueError("R53 R10 ready capture must capture rating and question selections body-free")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R53 R10 ready capture must mark actual body-free review result capture")
        if data.get("actual_review_result_rows_captured_here") is not True:
            raise ValueError("R53 R10 ready capture must mark body-free result rows captured")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R53 R10 ready capture must not say review is still unrun")
        if blockers:
            raise ValueError("R53 R10 ready capture must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R10_IMPLEMENTED_STEPS:
            raise ValueError("R53 R10 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R10_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R10 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R10_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R10 ready capture must point to R53-11")
    else:
        if data.get("actual_human_review_run_here") is not False or data.get("actual_manual_review_run_here") is not False:
            raise ValueError("R53 R10 blocked capture must not mark review captured")
        if data.get("actual_review_result_rows_captured_here") is not False:
            raise ValueError("R53 R10 blocked capture must not capture rows")
        if data.get("p5_actual_review_still_not_run") is not True:
            raise ValueError("R53 R10 blocked capture must keep review as unrun")
        if data.get("next_required_step") != P7_R53_R10_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R10 blocked capture must point to R53-9 resolution")
        if not blockers:
            raise ValueError("R53 R10 blocked capture must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r10_actual_human_review_result_capture_bodyfree")
    return True


def build_p7_r53_rating_row_normalization_bodyfree(
    *,
    actual_human_review_result_capture: Mapping[str, Any] | None = None,
    r10_actual_human_review_result_capture: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_rating_row_normalization_bodyfree",
) -> dict[str, Any]:
    """Build R53-11 body-free R51-compatible rating row normalization."""

    if actual_human_review_result_capture is not None and r10_actual_human_review_result_capture is not None:
        raise ValueError("provide only one R53-10 actual review capture value")
    r10 = (
        safe_mapping(actual_human_review_result_capture)
        if actual_human_review_result_capture is not None
        else safe_mapping(r10_actual_human_review_result_capture)
        if r10_actual_human_review_result_capture is not None
        else build_p7_r53_actual_human_review_result_capture_bodyfree()
    )
    assert_p7_r53_actual_human_review_result_capture_bodyfree_contract(r10)
    r51_r8 = safe_mapping(r10.get("r51_r8_actual_human_review_run_bodyfree"))
    r10_ready = r10.get("actual_review_run_status") == "READY_FOR_RATING_ROW_NORMALIZATION" and not r10.get("execution_blocker_ids")
    assert_p7_r51_actual_human_review_run_bodyfree_contract(
        r51_r8,
        allowed_true_false_key_refs=P7_R53_R10_ALLOWED_TRUE_FALSE_KEY_REFS if r10_ready else (),
    )
    r51_r9 = build_p7_r51_rating_row_normalizer_bodyfree(
        actual_human_review_run=r51_r8,
        material_id="p7_r53_adopted_r51_r9_rating_row_normalizer_bodyfree",
    )
    r51_ready = r51_r9.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r51_r9.get("execution_blocker_ids")
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(
        r51_r9,
        allowed_true_false_key_refs=P7_R53_R11_ALLOWED_TRUE_FALSE_KEY_REFS if r51_ready else (),
    )
    blockers = _r53_map_r51_rating_row_normalizer_blockers([*(r10.get("execution_blocker_ids") or []), *(r51_r9.get("execution_blocker_ids") or [])])
    if not r10_ready:
        blockers = dedupe_identifiers([*blockers, "r53_actual_review_result_capture_not_ready"], limit=40, max_length=140)
    if r10_ready and not r51_ready:
        blockers = dedupe_identifiers([*blockers, "r53_rating_rows_incomplete"], limit=40, max_length=140)
    ready = r10_ready and r51_ready and not blockers
    rating_rows = [safe_mapping(row) for row in (r51_r9.get("rating_rows") or [])] if ready else []
    for row in rating_rows:
        assert_p7_r51_rating_row_bodyfree_contract(row)
    normalization = {
        "schema_version": P7_R53_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-11_rating_row_normalization",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_rating_row_normalization_bodyfree", max_length=180),
        "review_session_id": _safe_review_session_id(r10.get("review_session_id")),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r10_actual_review_capture_schema_version": P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "r10_actual_review_capture_material_ref": clean_identifier(r10.get("material_id"), default="p7_r53_actual_human_review_result_capture_bodyfree", max_length=180),
        "r10_actual_review_run_status": clean_identifier(r10.get("actual_review_run_status"), default="BLOCKED_BY_R53_9_OR_MISSING_SANITIZED_REVIEW_RESULTS", max_length=120),
        "r10_actual_review_capture_ready_for_rating_normalization": r10_ready,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r9_rating_row_normalizer_schema_version": P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r51_r9_rating_row_normalizer_material_ref": clean_identifier(r51_r9.get("material_id"), default="p7_r53_adopted_r51_r9_rating_row_normalizer_bodyfree", max_length=180),
        "r51_r9_rating_row_normalizer_bodyfree": r51_r9,
        "r51_r9_rating_row_normalizer_status": clean_identifier(r51_r9.get("rating_row_normalizer_status"), default="BLOCKED_BY_R51_8_ACTUAL_HUMAN_REVIEW_RUN", max_length=120),
        "r51_r9_next_required_step": clean_identifier(r51_r9.get("next_required_step"), default=P7_R51_R9_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r9_execution_blocker_ids": dedupe_identifiers(r51_r9.get("execution_blocker_ids") or [], limit=40, max_length=140),
        "review_session_status": "R53_RATING_ROW_NORMALIZATION_READY" if ready else "PRECHECK_BLOCKED",
        "rating_row_normalizer_status": "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" if ready else "BLOCKED_BY_R53_10_ACTUAL_REVIEW_RESULT_CAPTURE",
        "rating_row_normalizer_reason_refs": ["r53_rating_rows_normalized_bodyfree"] if ready else _r53_prefixed_reason_refs(r51_r9.get("rating_row_normalizer_reason_refs") or [], default="r53_rating_row_normalization_blocked", blocker_ids=blockers),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_result_capture_row_count": _safe_non_negative_int_r53(r10.get("review_result_capture_row_count")) if ready else 0,
        "rating_row_count": len(rating_rows),
        "rating_rows": rating_rows,
        "rating_row_schema_version": P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "r51_rating_row_schema_version_ref": P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION,
        "rating_row_required_field_refs": list(P7_R51_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "rating_axis_refs": list(r51_r9.get("rating_axis_refs") or []),
        "rating_axis_target_refs": dict(safe_mapping(r51_r9.get("rating_axis_target_refs"))),
        "rating_score_min": r51_r9.get("rating_score_min"),
        "rating_score_max": r51_r9.get("rating_score_max"),
        "missing_axis_scores_pass_allowed": False,
        "extra_rating_axis_allowed": False,
        "machine_auto_score_allowed": False,
        "machine_metrics_used_for_readfeel_allowed": False,
        "reviewer_free_text_bodyfree_allowed": False,
        "sanitized_reason_ids_only": True,
        "blocker_ids_only": True,
        "allowed_verdict_refs": list(r51_r9.get("allowed_verdict_refs") or []),
        "readfeel_blocker_id_refs": list(r51_r9.get("readfeel_blocker_id_refs") or []),
        "blocked_or_not_reviewable_must_use_execution_blocker_row": True,
        "red_or_repair_requires_blocker": True,
        "pass_requires_targets_and_no_blockers": True,
        "body_removed_may_be_false_before_disposal": True,
        "rating_rows_are_bodyfree": True,
        "all_required_rating_rows_present": ready,
        "rating_case_ref_sets_match_review_capture": ready and r51_r9.get("rating_case_ref_sets_match_review_capture") is True,
        "verdict_counts": safe_mapping(r51_r9.get("verdict_counts")),
        "blocker_row_candidate_count": _safe_non_negative_int_r53(r51_r9.get("blocker_row_candidate_count")) if ready else 0,
        "execution_blocker_row_candidate_count": 0 if ready else len(blockers),
        **_false_flags(),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": ready,
        "actual_manual_review_run_here": ready,
        "actual_rating_rows_materialized_here": ready,
        "actual_blocker_rows_materialized_here": False,
        "actual_execution_blocker_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r10.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r10.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r10.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r10.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r10.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R53_R11_IMPLEMENTED_STEPS if ready else P7_R53_R10_IMPLEMENTED_STEPS if r10_ready else P7_R53_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R11_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R53_R10_NOT_YET_IMPLEMENTED_STEPS if r10_ready else P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R11_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R11_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_rating_row_normalization_bodyfree_contract(normalization)
    return normalization


def assert_p7_r53_rating_row_normalization_bodyfree_contract(normalization: Mapping[str, Any]) -> bool:
    data = safe_mapping(normalization)
    _assert_required_fields(data, required=P7_R53_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS, source="p7_r53_r11_rating_row_normalization_bodyfree")
    ready = data.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        source="p7_r53_r11_rating_row_normalization_bodyfree",
        allowed_true_false_key_refs=P7_R53_R11_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("policy_section") != "R53-11_rating_row_normalization":
        raise ValueError("R53 R11 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R11 current refs changed")
    r51_r9 = safe_mapping(data.get("r51_r9_rating_row_normalizer_bodyfree"))
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(
        r51_r9,
        allowed_true_false_key_refs=P7_R53_R11_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("r51_r9_rating_row_normalizer_schema_version") != P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R53 R11 R51 R9 schema reference changed")
    if data.get("r51_r9_rating_row_normalizer_status") != r51_r9.get("rating_row_normalizer_status"):
        raise ValueError("R53 R11 R51 R9 status mismatch")
    for row in data.get("rating_rows") or []:
        assert_p7_r51_rating_row_bodyfree_contract(safe_mapping(row))
    for true_key in (
        "sanitized_reason_ids_only",
        "blocker_ids_only",
        "blocked_or_not_reviewable_must_use_execution_blocker_row",
        "red_or_repair_requires_blocker",
        "pass_requires_targets_and_no_blockers",
        "body_removed_may_be_false_before_disposal",
        "rating_rows_are_bodyfree",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R11 must keep {true_key}=True")
    for false_key in (
        "missing_axis_scores_pass_allowed",
        "extra_rating_axis_allowed",
        "machine_auto_score_allowed",
        "machine_metrics_used_for_readfeel_allowed",
        "reviewer_free_text_bodyfree_allowed",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R11 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R11 open blockers must match execution blockers")
    if data.get("r53_11_rating_row_normalization_built") is not ready:
        raise ValueError("R53 R11 built flag must match readiness")
    if ready:
        if data.get("r10_actual_review_capture_ready_for_rating_normalization") is not True:
            raise ValueError("R53 R11 ready normalization requires ready R10 capture")
        if data.get("r51_r9_next_required_step") != P7_R51_R9_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R11 ready R51 R9 must point to R51-10")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R11 ready normalization must carry 24 rating rows")
        if data.get("all_required_rating_rows_present") is not True or data.get("rating_case_ref_sets_match_review_capture") is not True:
            raise ValueError("R53 R11 ready normalization must be complete and case-set matched")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R53 R11 ready normalization must preserve actual review capture")
        if data.get("actual_rating_rows_materialized_here") is not True:
            raise ValueError("R53 R11 ready normalization must materialize body-free rating rows")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R53 R11 ready normalization must not say review is still unrun")
        if blockers:
            raise ValueError("R53 R11 ready normalization must not carry blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R11_IMPLEMENTED_STEPS:
            raise ValueError("R53 R11 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R11_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R11 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R11_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R11 ready normalization must point to R53-12")
    else:
        if data.get("actual_rating_rows_materialized_here") is not False:
            raise ValueError("R53 R11 blocked normalization must not materialize rating rows")
        if data.get("r53_11_rating_row_normalization_built") is not False:
            raise ValueError("R53 R11 blocked normalization must not claim built")
        if data.get("p5_actual_review_still_not_run") is not True:
            raise ValueError("R53 R11 blocked normalization must keep review as unrun")
        if data.get("next_required_step") != P7_R53_R11_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R11 blocked normalization must point to R53-10 resolution")
        if not blockers:
            raise ValueError("R53 R11 blocked normalization must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r11_rating_row_normalization_bodyfree")
    return True




# ---------------------------------------------------------------------------
# R53-12 / R53-13: blocker ingestion and question observation normalization
# ---------------------------------------------------------------------------

P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.readfeel_execution_blocker_ingestion.bodyfree.v1"
)
P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.question_need_observation_row_normalization.bodyfree.v1"
)

P7_R53_R12_NEXT_REQUIRED_STEP_REF: Final = "R53-13_question_need_observation_row_normalization"
P7_R53_R12_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-11_rating_row_normalization_before_R53-12_readfeel_blocker_execution_blocker_ingestion"
)
P7_R53_R13_NEXT_REQUIRED_STEP_REF: Final = "R53-14_rating_question_consistency_guard"
P7_R53_R13_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-12_readfeel_blocker_execution_blocker_ingestion_before_R53-13_question_need_observation_row_normalization"
)

P7_R53_FUTURE_STEPS_AFTER_R13: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R11
    if step
    not in {
        "R53-12_readfeel_blocker_execution_blocker_ingestion",
        "R53-13_question_need_observation_row_normalization",
    }
)
P7_R53_R12_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R11_IMPLEMENTED_STEPS,
    "R53-12_readfeel_blocker_execution_blocker_ingestion",
)
P7_R53_R12_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-13_question_need_observation_row_normalization",
    *P7_R53_FUTURE_STEPS_AFTER_R13,
)
P7_R53_R13_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R12_IMPLEMENTED_STEPS,
    "R53-13_question_need_observation_row_normalization",
)
P7_R53_R13_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R13

P7_R53_R51_TO_R53_BLOCKER_INGESTION_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_RATING_ROW_NORMALIZATION_BLOCKER_MAP,
    "r51_rating_rows_incomplete": "r53_rating_rows_not_ready_for_blocker_ingestion",
    "r51_question_need_observation_rows_incomplete": "r53_question_observation_rows_not_ready",
    "r51_body_free_leak_detected": "r53_body_free_leak_detected",
}
P7_R53_R51_TO_R53_QUESTION_OBSERVATION_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_BLOCKER_INGESTION_BLOCKER_MAP,
    "r51_10_blocker_ingestion_not_ready": "r53_blocker_ingestion_not_ready",
    "r51_question_need_observation_rows_incomplete": "r53_question_need_observation_rows_incomplete",
    "r51_rating_question_observation_inconsistent": "r53_rating_question_observation_inconsistent",
}

P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r11_rating_row_normalization_schema_version",
    "r11_rating_row_normalization_material_ref",
    "r11_rating_row_normalizer_status",
    "r11_rating_rows_ready_for_blocker_ingestion",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r10_blocker_ingestion_schema_version",
    "r51_r10_blocker_ingestion_material_ref",
    "r51_r10_readfeel_execution_blocker_ingestion_bodyfree",
    "r51_r10_blocker_ingestion_status",
    "r51_r10_next_required_step",
    "r51_r10_execution_blocker_ids",
    "review_session_status",
    "blocker_ingestion_status",
    "blocker_ingestion_reason_refs",
    "required_case_count",
    "rating_row_count",
    "readfeel_blocker_row_schema_version",
    "execution_blocker_row_schema_version",
    "readfeel_blocker_row_required_field_refs",
    "execution_blocker_row_required_field_refs",
    "readfeel_blocker_id_refs",
    "execution_blocker_id_refs",
    "readfeel_blocker_kind_refs",
    "readfeel_blocker_status_refs",
    "execution_blocker_kind_refs",
    "execution_blocker_status_refs",
    "readfeel_blocker_rows",
    "execution_blocker_rows",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "readfeel_blocker_counts",
    "execution_blocker_counts",
    "readfeel_and_execution_blockers_separated",
    "execution_blockers_do_not_assign_readfeel_verdict",
    "execution_blocker_cases_do_not_create_rating_rows",
    "rating_missing_maps_to_execution_blocker_not_red",
    "local_root_missing_maps_to_execution_blocker_not_red",
    "disposal_failed_maps_to_execution_blocker_not_red",
    "body_free_leak_maps_to_execution_blocker_not_red",
    "readfeel_blocker_row_builder_ready",
    "execution_blocker_row_builder_ready",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "p5_actual_review_still_not_run",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r12_blocker_ingestion_schema_version",
    "r12_blocker_ingestion_material_ref",
    "r12_blocker_ingestion_status",
    "r12_ready_for_question_need_observation_row_normalization",
    "r10_actual_review_capture_schema_version",
    "r10_actual_review_capture_material_ref",
    "r10_actual_review_run_status",
    "r10_actual_review_capture_ready_for_question_observation",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r11_question_need_observation_row_normalizer_schema_version",
    "r51_r11_question_need_observation_row_normalizer_material_ref",
    "r51_r11_question_need_observation_row_normalizer_bodyfree",
    "r51_r11_question_observation_normalizer_status",
    "r51_r11_next_required_step",
    "r51_r11_execution_blocker_ids",
    "review_session_status",
    "question_observation_normalizer_status",
    "question_observation_normalizer_reason_refs",
    "required_case_count",
    "review_result_capture_row_count",
    "rating_row_count",
    "question_observation_row_count",
    "question_need_observation_rows",
    "question_need_observation_row_schema_version",
    "question_need_observation_row_required_field_refs",
    "question_need_observation_row_forbidden_field_refs",
    "question_need_primary_class_refs",
    "ambiguity_kind_refs",
    "one_question_fit_refs",
    "plan_candidate_flag_refs",
    "repair_required_ref_refs",
    "question_need_observation_stage_ref",
    "review_kind",
    "question_need_observation_rows_must_be_bodyfree",
    "question_text_absent_for_all_rows",
    "draft_question_text_absent_for_all_rows",
    "reviewer_free_text_absent_for_all_rows",
    "raw_input_absent_for_all_rows",
    "returned_surface_absent_for_all_rows",
    "local_path_absent_for_all_rows",
    "body_hash_absent_for_all_rows",
    "question_text_included_allowed",
    "draft_question_text_included_allowed",
    "reviewer_free_text_included_allowed",
    "raw_input_allowed",
    "returned_surface_allowed",
    "local_path_allowed",
    "body_hash_allowed",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_storage_schema_implemented",
    "row_case_ref_sets_match_review_capture",
    "row_case_ref_sets_match_rating_rows",
    "all_required_question_need_observation_rows_present",
    "primary_class_ambiguity_one_question_fit_are_canonical_refs",
    "p5_weakness_not_hidden_by_question_candidates_here",
    "question_text_or_draft_text_saved_here",
    "question_need_primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p5_actual_review_still_not_run",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_R12_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
)
P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
)


def _r53_map_r51_blocker_ingestion_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_BLOCKER_INGESTION_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=40,
        max_length=140,
    )


def _r53_map_r51_question_observation_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_QUESTION_OBSERVATION_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=40,
        max_length=140,
    )


def build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(
    *,
    rating_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    r11_rating_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree",
) -> dict[str, Any]:
    """Build R53-12 body-free readfeel/execution blocker ingestion.

    This adopts the R51 R10 blocker separation only after R53 R11 rating rows
    are available.  Execution blockers remain execution blockers and are never
    converted into readfeel verdict rows.
    """

    if rating_row_normalization_bodyfree is not None and r11_rating_row_normalization_bodyfree is not None:
        raise ValueError("provide only one R53-11 rating row normalization value")
    r11 = (
        safe_mapping(rating_row_normalization_bodyfree)
        if rating_row_normalization_bodyfree is not None
        else safe_mapping(r11_rating_row_normalization_bodyfree)
        if r11_rating_row_normalization_bodyfree is not None
        else build_p7_r53_rating_row_normalization_bodyfree()
    )
    assert_p7_r53_rating_row_normalization_bodyfree_contract(r11)
    r11_ready = r11.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r11.get("execution_blocker_ids")
    r51_r9 = safe_mapping(r11.get("r51_r9_rating_row_normalizer_bodyfree"))
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(
        r51_r9,
        allowed_true_false_key_refs=P7_R53_R11_ALLOWED_TRUE_FALSE_KEY_REFS if r11_ready else (),
    )
    r51_r10 = build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=r51_r9,
        material_id="p7_r53_adopted_r51_r10_readfeel_execution_blocker_ingestion_bodyfree",
    )
    r51_ready = r51_r10.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r51_r10.get("execution_blocker_ids")
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(
        r51_r10,
        allowed_true_false_key_refs=P7_R53_R12_ALLOWED_TRUE_FALSE_KEY_REFS if r51_ready else (),
    )
    r51_blockers = dedupe_identifiers(r51_r10.get("execution_blocker_ids") or [], limit=40, max_length=140)
    blockers = _r53_map_r51_blocker_ingestion_blockers(r51_blockers)
    if not r11_ready and not blockers:
        blockers = ["r53_rating_row_normalization_not_ready"]
    ready = bool(r11_ready and r51_ready and not blockers)
    reason_refs = ["r53_readfeel_execution_blockers_separated_bodyfree"] if ready else _r53_prefixed_reason_refs(
        r51_r10.get("blocker_ingestion_reason_refs") or [],
        default="r53_readfeel_execution_blocker_ingestion_blocked",
        blocker_ids=blockers,
    )
    readfeel_rows = [safe_mapping(row) for row in r51_r10.get("readfeel_blocker_rows") or []]
    execution_rows = [safe_mapping(row) for row in r51_r10.get("execution_blocker_rows") or []]
    ingestion = {
        "schema_version": P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-12_readfeel_blocker_execution_blocker_ingestion",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r11.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r11_rating_row_normalization_schema_version": P7_R53_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r11_rating_row_normalization_material_ref": clean_identifier(r11.get("material_id"), default="p7_r53_rating_row_normalization_bodyfree", max_length=180),
        "r11_rating_row_normalizer_status": clean_identifier(r11.get("rating_row_normalizer_status"), default="BLOCKED_BY_R53_10_ACTUAL_REVIEW_RESULT_CAPTURE", max_length=120),
        "r11_rating_rows_ready_for_blocker_ingestion": bool(r11_ready),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r10_blocker_ingestion_schema_version": P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION,
        "r51_r10_blocker_ingestion_material_ref": clean_identifier(r51_r10.get("material_id"), default="p7_r53_adopted_r51_r10_readfeel_execution_blocker_ingestion_bodyfree", max_length=180),
        "r51_r10_readfeel_execution_blocker_ingestion_bodyfree": r51_r10,
        "r51_r10_blocker_ingestion_status": clean_identifier(r51_r10.get("blocker_ingestion_status"), default="BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER", max_length=120),
        "r51_r10_next_required_step": clean_identifier(r51_r10.get("next_required_step"), default=P7_R51_R10_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r10_execution_blocker_ids": r51_blockers,
        "review_session_status": "R53_READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "blocker_ingestion_status": "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" if ready else "BLOCKED_BY_R53_11_RATING_ROW_NORMALIZATION",
        "blocker_ingestion_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int_r53(r51_r10.get("rating_row_count")),
        "readfeel_blocker_row_schema_version": P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "execution_blocker_row_schema_version": P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION,
        "readfeel_blocker_row_required_field_refs": list(P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "execution_blocker_row_required_field_refs": list(P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "readfeel_blocker_id_refs": list(r51_r10.get("readfeel_blocker_id_refs") or []),
        "execution_blocker_id_refs": list(r51_r10.get("execution_blocker_id_refs") or []),
        "readfeel_blocker_kind_refs": list(r51_r10.get("readfeel_blocker_kind_refs") or []),
        "readfeel_blocker_status_refs": list(r51_r10.get("readfeel_blocker_status_refs") or []),
        "execution_blocker_kind_refs": list(r51_r10.get("execution_blocker_kind_refs") or []),
        "execution_blocker_status_refs": list(r51_r10.get("execution_blocker_status_refs") or []),
        "readfeel_blocker_rows": readfeel_rows,
        "execution_blocker_rows": execution_rows,
        "readfeel_blocker_row_count": len(readfeel_rows),
        "execution_blocker_row_count": len(execution_rows),
        "open_readfeel_blocker_count": _safe_non_negative_int_r53(r51_r10.get("open_readfeel_blocker_count")),
        "open_execution_blocker_count": _safe_non_negative_int_r53(r51_r10.get("open_execution_blocker_count")),
        "readfeel_blocker_counts": dict(safe_mapping(r51_r10.get("readfeel_blocker_counts"))),
        "execution_blocker_counts": dict(safe_mapping(r51_r10.get("execution_blocker_counts"))),
        "readfeel_and_execution_blockers_separated": True,
        "execution_blockers_do_not_assign_readfeel_verdict": True,
        "execution_blocker_cases_do_not_create_rating_rows": True,
        "rating_missing_maps_to_execution_blocker_not_red": True,
        "local_root_missing_maps_to_execution_blocker_not_red": True,
        "disposal_failed_maps_to_execution_blocker_not_red": True,
        "body_free_leak_maps_to_execution_blocker_not_red": True,
        "readfeel_blocker_row_builder_ready": ready,
        "execution_blocker_row_builder_ready": ready,
        **_false_flags(),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(ready and r11.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(ready and r11.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(ready and r11.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": ready,
        "actual_execution_blocker_rows_materialized_here": ready,
        "actual_question_need_observation_rows_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r11.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r11.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r11.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r11.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r11.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r11.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R53_R12_IMPLEMENTED_STEPS if ready else P7_R53_R11_IMPLEMENTED_STEPS if r11_ready else P7_R53_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R12_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R53_R11_NOT_YET_IMPLEMENTED_STEPS if r11_ready else P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R12_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R12_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion)
    return ingestion


def assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion: Mapping[str, Any]) -> bool:
    data = safe_mapping(ingestion)
    _assert_required_fields(data, required=P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS, source="p7_r53_r12_readfeel_execution_blocker_ingestion_bodyfree")
    ready = data.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        source="p7_r53_r12_readfeel_execution_blocker_ingestion_bodyfree",
        allowed_true_false_key_refs=P7_R53_R12_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("policy_section") != "R53-12_readfeel_blocker_execution_blocker_ingestion":
        raise ValueError("R53 R12 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R12 current refs changed")
    r51_r10 = safe_mapping(data.get("r51_r10_readfeel_execution_blocker_ingestion_bodyfree"))
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(
        r51_r10,
        allowed_true_false_key_refs=P7_R53_R12_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("r51_r10_blocker_ingestion_schema_version") != P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R53 R12 R51 R10 schema reference changed")
    if data.get("r51_r10_blocker_ingestion_status") != r51_r10.get("blocker_ingestion_status"):
        raise ValueError("R53 R12 R51 R10 status mismatch")
    if tuple(data.get("readfeel_blocker_row_required_field_refs") or ()) != P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R53 R12 readfeel blocker row fields changed")
    if tuple(data.get("execution_blocker_row_required_field_refs") or ()) != P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R53 R12 execution blocker row fields changed")
    for row in data.get("readfeel_blocker_rows") or []:
        assert_p7_r51_readfeel_blocker_row_bodyfree_contract(safe_mapping(row))
    for row in data.get("execution_blocker_rows") or []:
        assert_p7_r51_execution_blocker_row_bodyfree_contract(safe_mapping(row))
    if data.get("readfeel_blocker_row_count") != len(data.get("readfeel_blocker_rows") or []):
        raise ValueError("R53 R12 readfeel blocker row count mismatch")
    if data.get("execution_blocker_row_count") != len(data.get("execution_blocker_rows") or []):
        raise ValueError("R53 R12 execution blocker row count mismatch")
    for true_key in (
        "readfeel_and_execution_blockers_separated",
        "execution_blockers_do_not_assign_readfeel_verdict",
        "execution_blocker_cases_do_not_create_rating_rows",
        "rating_missing_maps_to_execution_blocker_not_red",
        "local_root_missing_maps_to_execution_blocker_not_red",
        "disposal_failed_maps_to_execution_blocker_not_red",
        "body_free_leak_maps_to_execution_blocker_not_red",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R12 must keep {true_key}=True")
    for false_key in (
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_question_need_observation_rows_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R12 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R12 open blockers must match execution blockers")
    if data.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is not ready:
        raise ValueError("R53 R12 built flag must match readiness")
    if ready:
        if data.get("r11_rating_rows_ready_for_blocker_ingestion") is not True:
            raise ValueError("R53 R12 ready ingestion requires ready R11 rating rows")
        if data.get("r51_r10_next_required_step") != P7_R51_R10_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R12 ready R51 R10 must point to R51-11")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R12 ready ingestion requires 24 rating rows")
        if data.get("readfeel_blocker_row_builder_ready") is not True or data.get("execution_blocker_row_builder_ready") is not True:
            raise ValueError("R53 R12 ready ingestion requires blocker row builders ready")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R53 R12 ready ingestion must preserve actual review evidence")
        if data.get("actual_rating_rows_materialized_here") is not True:
            raise ValueError("R53 R12 ready ingestion must preserve rating rows")
        if data.get("actual_blocker_rows_materialized_here") is not True or data.get("actual_execution_blocker_rows_materialized_here") is not True:
            raise ValueError("R53 R12 ready ingestion must materialize body-free blocker rows")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R53 R12 ready ingestion must not say review is still unrun")
        if blockers:
            raise ValueError("R53 R12 ready ingestion must not carry open execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R12_IMPLEMENTED_STEPS:
            raise ValueError("R53 R12 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R12_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R12 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R12_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R12 ready ingestion must point to R53-13")
    else:
        if data.get("actual_blocker_rows_materialized_here") is not False or data.get("actual_execution_blocker_rows_materialized_here") is not False:
            raise ValueError("R53 R12 blocked ingestion must not materialize blocker rows")
        if data.get("readfeel_blocker_row_builder_ready") is not False or data.get("execution_blocker_row_builder_ready") is not False:
            raise ValueError("R53 R12 blocked ingestion must keep row builders disabled")
        if data.get("next_required_step") != P7_R53_R12_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R12 blocked ingestion must point to R53-11 resolution")
        if not blockers:
            raise ValueError("R53 R12 blocked ingestion must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r12_readfeel_execution_blocker_ingestion_bodyfree")
    return True


def build_p7_r53_question_need_observation_row_normalization_bodyfree(
    *,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    r12_readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    actual_human_review_result_capture: Mapping[str, Any] | None = None,
    r10_actual_human_review_result_capture_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_question_need_observation_row_normalization_bodyfree",
) -> dict[str, Any]:
    """Build R53-13 body-free question-need observation row normalization.

    This stage records canonical observation selections only.  It never stores
    question text, draft question text, reviewer free text, raw input, returned
    surface, local path, body hash, API/DB/RN changes, or P8 implementation
    decisions.
    """

    if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None and r12_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None:
        raise ValueError("provide only one R53-12 blocker ingestion value")
    if actual_human_review_result_capture is not None and r10_actual_human_review_result_capture_bodyfree is not None:
        raise ValueError("provide only one R53-10 actual review capture value")
    r12 = (
        safe_mapping(readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else safe_mapping(r12_readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if r12_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree()
    )
    assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r12)
    r10 = (
        safe_mapping(actual_human_review_result_capture)
        if actual_human_review_result_capture is not None
        else safe_mapping(r10_actual_human_review_result_capture_bodyfree)
        if r10_actual_human_review_result_capture_bodyfree is not None
        else build_p7_r53_actual_human_review_result_capture_bodyfree()
    )
    assert_p7_r53_actual_human_review_result_capture_bodyfree_contract(r10)
    r12_ready = r12.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r12.get("execution_blocker_ids")
    r10_ready = r10.get("actual_review_run_status") == "READY_FOR_RATING_ROW_NORMALIZATION" and not r10.get("execution_blocker_ids")
    r51_r10 = safe_mapping(r12.get("r51_r10_readfeel_execution_blocker_ingestion_bodyfree"))
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(
        r51_r10,
        allowed_true_false_key_refs=P7_R53_R12_ALLOWED_TRUE_FALSE_KEY_REFS if r12_ready else (),
    )
    r51_r8 = safe_mapping(r10.get("r51_r8_actual_human_review_run_bodyfree"))
    assert_p7_r51_actual_human_review_run_bodyfree_contract(
        r51_r8,
        allowed_true_false_key_refs=P7_R53_R10_ALLOWED_TRUE_FALSE_KEY_REFS if r10_ready else (),
    )
    r51_r11 = build_p7_r51_question_need_observation_row_normalizer_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r51_r10,
        actual_human_review_run=r51_r8,
        material_id="p7_r53_adopted_r51_r11_question_need_observation_row_normalizer_bodyfree",
    )
    r51_ready = r51_r11.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" and not r51_r11.get("execution_blocker_ids")
    assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(
        r51_r11,
        allowed_true_false_key_refs=P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS if r51_ready else (),
    )
    r51_blockers = dedupe_identifiers(r51_r11.get("execution_blocker_ids") or [], limit=40, max_length=140)
    blockers = _r53_map_r51_question_observation_blockers(r51_blockers)
    if not r12_ready and "r53_blocker_ingestion_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_blocker_ingestion_not_ready"], limit=40, max_length=140)
    if not r10_ready and "r53_actual_review_capture_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_actual_review_capture_not_ready"], limit=40, max_length=140)
    ready = bool(r12_ready and r10_ready and r51_ready and not blockers)
    reason_refs = ["r53_question_need_observation_rows_normalized_bodyfree"] if ready else _r53_prefixed_reason_refs(
        r51_r11.get("question_observation_normalizer_reason_refs") or [],
        default="r53_question_need_observation_row_normalization_blocked",
        blocker_ids=blockers,
    )
    question_rows = [safe_mapping(row) for row in r51_r11.get("question_need_observation_rows") or []]
    normalizer = {
        "schema_version": P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-13_question_need_observation_row_normalization",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_question_need_observation_row_normalization_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r12.get("review_session_id") or r10.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r12_blocker_ingestion_schema_version": P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "r12_blocker_ingestion_material_ref": clean_identifier(r12.get("material_id"), default="p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "r12_blocker_ingestion_status": clean_identifier(r12.get("blocker_ingestion_status"), default="BLOCKED_BY_R53_11_RATING_ROW_NORMALIZATION", max_length=120),
        "r12_ready_for_question_need_observation_row_normalization": bool(r12_ready),
        "r10_actual_review_capture_schema_version": P7_R53_ACTUAL_HUMAN_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION,
        "r10_actual_review_capture_material_ref": clean_identifier(r10.get("material_id"), default="p7_r53_actual_human_review_result_capture_bodyfree", max_length=180),
        "r10_actual_review_run_status": clean_identifier(r10.get("actual_review_run_status"), default="BLOCKED_BY_R53_9_OR_MISSING_SANITIZED_REVIEW_RESULTS", max_length=120),
        "r10_actual_review_capture_ready_for_question_observation": bool(r10_ready),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r11_question_need_observation_row_normalizer_schema_version": P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION,
        "r51_r11_question_need_observation_row_normalizer_material_ref": clean_identifier(r51_r11.get("material_id"), default="p7_r53_adopted_r51_r11_question_need_observation_row_normalizer_bodyfree", max_length=180),
        "r51_r11_question_need_observation_row_normalizer_bodyfree": r51_r11,
        "r51_r11_question_observation_normalizer_status": clean_identifier(r51_r11.get("question_observation_normalizer_status"), default="BLOCKED_BY_R51_10_BLOCKER_INGESTION", max_length=120),
        "r51_r11_next_required_step": clean_identifier(r51_r11.get("next_required_step"), default=P7_R51_R11_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r11_execution_blocker_ids": r51_blockers,
        "review_session_status": "R53_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE" if ready else "PRECHECK_BLOCKED",
        "question_observation_normalizer_status": "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" if ready else "BLOCKED_BY_R53_12_OR_R53_10_PRECHECK",
        "question_observation_normalizer_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "review_result_capture_row_count": _safe_non_negative_int_r53(r51_r11.get("review_result_capture_row_count")),
        "rating_row_count": _safe_non_negative_int_r53(r51_r11.get("rating_row_count")),
        "question_observation_row_count": len(question_rows),
        "question_need_observation_rows": question_rows,
        "question_need_observation_row_schema_version": P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION,
        "question_need_observation_row_required_field_refs": list(P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "question_need_observation_row_forbidden_field_refs": list(P7_R51_ACTUAL_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS),
        "question_need_primary_class_refs": list(r51_r11.get("question_need_primary_class_refs") or []),
        "ambiguity_kind_refs": list(r51_r11.get("ambiguity_kind_refs") or []),
        "one_question_fit_refs": list(r51_r11.get("one_question_fit_refs") or []),
        "plan_candidate_flag_refs": list(r51_r11.get("plan_candidate_flag_refs") or []),
        "repair_required_ref_refs": list(r51_r11.get("repair_required_ref_refs") or []),
        "question_need_observation_stage_ref": clean_identifier(r51_r11.get("question_need_observation_stage_ref"), default="p7_question_need_observation", max_length=160),
        "review_kind": P7_R51_REVIEW_KIND,
        "question_need_observation_rows_must_be_bodyfree": True,
        "question_text_absent_for_all_rows": True,
        "draft_question_text_absent_for_all_rows": True,
        "reviewer_free_text_absent_for_all_rows": True,
        "raw_input_absent_for_all_rows": True,
        "returned_surface_absent_for_all_rows": True,
        "local_path_absent_for_all_rows": True,
        "body_hash_absent_for_all_rows": True,
        "question_text_included_allowed": False,
        "draft_question_text_included_allowed": False,
        "reviewer_free_text_included_allowed": False,
        "raw_input_allowed": False,
        "returned_surface_allowed": False,
        "local_path_allowed": False,
        "body_hash_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "question_api_implemented": False,
        "question_db_schema_implemented": False,
        "question_rn_ui_implemented": False,
        "question_response_key_implemented": False,
        "question_storage_schema_implemented": False,
        "row_case_ref_sets_match_review_capture": bool(ready and r51_r11.get("row_case_ref_sets_match_review_capture") is True),
        "row_case_ref_sets_match_rating_rows": bool(ready and r51_r11.get("row_case_ref_sets_match_rating_rows") is True),
        "all_required_question_need_observation_rows_present": ready,
        "primary_class_ambiguity_one_question_fit_are_canonical_refs": ready,
        "p5_weakness_not_hidden_by_question_candidates_here": False,
        "question_text_or_draft_text_saved_here": False,
        "question_need_primary_class_counts": dict(safe_mapping(r51_r11.get("question_need_primary_class_counts"))),
        "ambiguity_kind_counts": dict(safe_mapping(r51_r11.get("ambiguity_kind_counts"))),
        "one_question_fit_counts": dict(safe_mapping(r51_r11.get("one_question_fit_counts"))),
        "repair_required_counts": dict(safe_mapping(r51_r11.get("repair_required_counts"))),
        "plan_candidate_flag_counts": dict(safe_mapping(r51_r11.get("plan_candidate_flag_counts"))),
        **_false_flags(),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(ready and r10.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(ready and r10.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(ready and r12.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and r12.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(ready and r12.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": ready,
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r12.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r12.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r12.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r12.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r10.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r12.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": r12.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r53_13_question_need_observation_row_normalization_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R53_R13_IMPLEMENTED_STEPS if ready else P7_R53_R12_IMPLEMENTED_STEPS if r12_ready else P7_R53_R11_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R13_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R53_R12_NOT_YET_IMPLEMENTED_STEPS if r12_ready else P7_R53_R11_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R13_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R13_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(normalizer)
    return normalizer


def assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(normalizer: Mapping[str, Any]) -> bool:
    data = safe_mapping(normalizer)
    _assert_required_fields(data, required=P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_REQUIRED_FIELD_REFS, source="p7_r53_r13_question_need_observation_row_normalization_bodyfree")
    ready = data.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        source="p7_r53_r13_question_need_observation_row_normalization_bodyfree",
        allowed_true_false_key_refs=P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("policy_section") != "R53-13_question_need_observation_row_normalization":
        raise ValueError("R53 R13 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R13 current refs changed")
    r51_r11 = safe_mapping(data.get("r51_r11_question_need_observation_row_normalizer_bodyfree"))
    assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(
        r51_r11,
        allowed_true_false_key_refs=P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("r51_r11_question_need_observation_row_normalizer_schema_version") != P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION:
        raise ValueError("R53 R13 R51 R11 schema reference changed")
    if data.get("r51_r11_question_observation_normalizer_status") != r51_r11.get("question_observation_normalizer_status"):
        raise ValueError("R53 R13 R51 R11 status mismatch")
    if tuple(data.get("question_need_observation_row_required_field_refs") or ()) != P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS:
        raise ValueError("R53 R13 question observation row fields changed")
    if tuple(data.get("question_need_observation_row_forbidden_field_refs") or ()) != P7_R51_ACTUAL_REVIEW_RESULT_INPUT_FORBIDDEN_KEY_REFS:
        raise ValueError("R53 R13 question observation forbidden fields changed")
    for row in data.get("question_need_observation_rows") or []:
        assert_p7_r51_question_need_observation_row_bodyfree_contract(safe_mapping(row))
    if data.get("question_observation_row_count") != len(data.get("question_need_observation_rows") or []):
        raise ValueError("R53 R13 question observation row count mismatch")
    for true_key in (
        "question_need_observation_rows_must_be_bodyfree",
        "question_text_absent_for_all_rows",
        "draft_question_text_absent_for_all_rows",
        "reviewer_free_text_absent_for_all_rows",
        "raw_input_absent_for_all_rows",
        "returned_surface_absent_for_all_rows",
        "local_path_absent_for_all_rows",
        "body_hash_absent_for_all_rows",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R13 must keep {true_key}=True")
    for false_key in (
        "question_text_included_allowed",
        "draft_question_text_included_allowed",
        "reviewer_free_text_included_allowed",
        "raw_input_allowed",
        "returned_surface_allowed",
        "local_path_allowed",
        "body_hash_allowed",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_implemented",
        "question_storage_schema_implemented",
        "question_text_or_draft_text_saved_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_question_need_observation_summary_materialized_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R13 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=40, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R13 open blockers must match execution blockers")
    if data.get("r53_13_question_need_observation_row_normalization_built") is not ready:
        raise ValueError("R53 R13 built flag must match readiness")
    if ready:
        if data.get("r12_ready_for_question_need_observation_row_normalization") is not True or data.get("r10_actual_review_capture_ready_for_question_observation") is not True:
            raise ValueError("R53 R13 ready normalizer requires ready R12 blocker ingestion and R10 capture")
        if data.get("r51_r11_next_required_step") != P7_R51_R11_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R13 ready R51 R11 must point to R51-12")
        if data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R13 ready normalizer must carry 24 question rows")
        if data.get("row_case_ref_sets_match_review_capture") is not True or data.get("row_case_ref_sets_match_rating_rows") is not True:
            raise ValueError("R53 R13 ready normalizer must match capture and rating case sets")
        if data.get("all_required_question_need_observation_rows_present") is not True:
            raise ValueError("R53 R13 ready normalizer must mark all question rows present")
        if data.get("primary_class_ambiguity_one_question_fit_are_canonical_refs") is not True:
            raise ValueError("R53 R13 ready normalizer must use canonical question observation refs")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R53 R13 ready normalizer must preserve actual review evidence")
        if data.get("actual_rating_rows_materialized_here") is not True:
            raise ValueError("R53 R13 ready normalizer must preserve rating rows")
        if data.get("actual_blocker_rows_materialized_here") is not True or data.get("actual_execution_blocker_rows_materialized_here") is not True:
            raise ValueError("R53 R13 ready normalizer must preserve blocker rows")
        if data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("R53 R13 ready normalizer must materialize body-free question observation rows")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R53 R13 ready normalizer must not say review is still unrun")
        if blockers:
            raise ValueError("R53 R13 ready normalizer must not carry open execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R13_IMPLEMENTED_STEPS:
            raise ValueError("R53 R13 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R13_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R13 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R13_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R13 ready normalizer must point to R53-14")
    else:
        if data.get("actual_question_need_observation_rows_materialized_here") is not False:
            raise ValueError("R53 R13 blocked normalizer must not materialize question observation rows")
        if data.get("r53_13_question_need_observation_row_normalization_built") is not False:
            raise ValueError("R53 R13 blocked normalizer must not claim built")
        if data.get("next_required_step") != P7_R53_R13_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R13 blocked normalizer must point to R53-12 resolution")
        if not blockers:
            raise ValueError("R53 R13 blocked normalizer must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r13_question_need_observation_row_normalization_bodyfree")
    return True



# ---------------------------------------------------------------------------
# R53-14 / R53-15: consistency guard and pause / abort / expiration protocol
# ---------------------------------------------------------------------------

P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.rating_question_consistency_guard.bodyfree.v1"
)
P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.pause_abort_expiration_protocol.bodyfree.v1"
)

P7_R53_R14_NEXT_REQUIRED_STEP_REF: Final = "R53-15_pause_abort_expiration_protocol"
P7_R53_R14_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-13_question_need_observation_row_normalization_before_R53-14_rating_question_consistency_guard"
)
P7_R53_R15_NEXT_REQUIRED_STEP_REF: Final = "R53-16_purge_disposal_receipt"
P7_R53_R15_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-14_rating_question_consistency_guard_before_R53-15_pause_abort_expiration_protocol"
)
P7_R53_R15_PAUSED_NEXT_REQUIRED_STEP_REF: Final = (
    "resume_or_abort_paused_R53-15_local_review_before_retention_deadline"
)

P7_R53_FUTURE_STEPS_AFTER_R15: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R13
    if step
    not in {
        "R53-14_rating_question_consistency_guard",
        "R53-15_pause_abort_expiration_protocol",
    }
)
P7_R53_R14_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R13_IMPLEMENTED_STEPS,
    "R53-14_rating_question_consistency_guard",
)
P7_R53_R14_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-15_pause_abort_expiration_protocol",
    *P7_R53_FUTURE_STEPS_AFTER_R15,
)
P7_R53_R15_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R14_IMPLEMENTED_STEPS,
    "R53-15_pause_abort_expiration_protocol",
)
P7_R53_R15_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R15

P7_R53_R51_TO_R53_RATING_QUESTION_CONSISTENCY_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_QUESTION_OBSERVATION_BLOCKER_MAP,
    "r51_rating_rows_incomplete": "r53_rating_rows_incomplete_for_consistency_guard",
    "r51_question_need_observation_rows_incomplete": "r53_question_observation_rows_incomplete_for_consistency_guard",
    "r51_rating_question_observation_inconsistent": "r53_rating_question_observation_inconsistent",
    "r51_pass_rating_with_not_question_repair": "r53_pass_rating_with_not_question_repair",
    "r51_red_or_repair_required_routed_to_question_candidate": "r53_red_or_repair_required_routed_to_question_candidate",
    "r51_repair_required_not_question_without_repair_ref": "r53_repair_required_not_question_without_repair_ref",
    "r51_insufficient_material_observation_without_execution_blocker": "r53_insufficient_material_observation_without_execution_blocker",
    "r51_creepy_or_boundary_blocker_routed_to_question_candidate": "r53_creepy_or_boundary_blocker_routed_to_question_candidate",
    "r51_current_input_overridden_by_history_routed_to_question_candidate": "r53_current_input_overridden_by_history_routed_to_question_candidate",
    "r51_rating_question_case_set_mismatch": "r53_rating_question_case_set_mismatch",
    "r51_missing_rating_row_for_question_observation": "r53_missing_rating_row_for_question_observation",
    "r51_missing_question_observation_row_for_rating": "r53_missing_question_observation_row_for_rating",
}
P7_R53_R51_TO_R53_PAUSE_ABORT_EXPIRATION_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_RATING_QUESTION_CONSISTENCY_BLOCKER_MAP,
    "r51_rating_question_observation_inconsistent": "r53_rating_question_observation_inconsistent",
}

P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r11_rating_row_normalization_schema_version",
    "r11_rating_row_normalization_material_ref",
    "r11_rating_row_normalizer_status",
    "r11_ready_for_consistency_guard",
    "r12_blocker_ingestion_schema_version",
    "r12_blocker_ingestion_material_ref",
    "r12_blocker_ingestion_status",
    "r12_ready_for_consistency_guard",
    "r13_question_observation_schema_version",
    "r13_question_observation_material_ref",
    "r13_question_observation_normalizer_status",
    "r13_ready_for_consistency_guard",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r12_consistency_guard_schema_version",
    "r51_r12_consistency_guard_material_ref",
    "r51_r12_rating_question_observation_consistency_guard_bodyfree",
    "r51_r12_rating_question_consistency_guard_status",
    "r51_r12_next_required_step",
    "r51_r12_execution_blocker_ids",
    "review_session_status",
    "rating_question_consistency_guard_status",
    "rating_question_consistency_guard_reason_refs",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "readfeel_blocker_row_count",
    "execution_blocker_row_count",
    "open_readfeel_blocker_count",
    "open_execution_blocker_count",
    "rating_question_case_ref_sets_match",
    "all_required_rows_present",
    "consistency_issue_row_schema_version",
    "consistency_issue_row_required_field_refs",
    "consistency_issue_id_refs",
    "consistency_issue_kind_refs",
    "consistency_issue_rows",
    "consistency_issue_count",
    "consistency_issue_id_counts",
    "consistency_issue_kind_counts",
    "no_red_or_repair_routed_to_p8_question_candidate",
    "no_creepy_or_boundary_blocker_routed_to_p8_question_candidate",
    "no_pass_rating_with_not_question_repair",
    "no_repair_required_not_question_without_repair_ref",
    "insufficient_material_observations_have_execution_blocker",
    "p5_weakness_not_hidden_by_question_candidates",
    "p5_repair_return_required_by_consistency",
    "p8_question_material_candidate_allowed_by_consistency",
    "question_candidate_allowed_case_count",
    "p8_question_material_candidate_case_count",
    "question_text_included_allowed",
    "draft_question_text_included_allowed",
    "reviewer_free_text_included_allowed",
    "raw_input_allowed",
    "returned_surface_allowed",
    "local_path_allowed",
    "body_hash_allowed",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p5_actual_review_still_not_run",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r14_consistency_guard_schema_version",
    "r14_consistency_guard_material_ref",
    "r14_rating_question_consistency_guard_status",
    "r14_ready_for_pause_abort_expiration_protocol",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r13_pause_abort_expiration_protocol_schema_version",
    "r51_r13_pause_abort_expiration_protocol_material_ref",
    "r51_r13_pause_abort_expiration_protocol_bodyfree",
    "r51_r13_pause_abort_expiration_protocol_status",
    "r51_r13_next_required_step",
    "r51_r13_execution_blocker_ids",
    "review_session_status",
    "pause_abort_expiration_protocol_status",
    "pause_abort_expiration_reason_refs",
    "pause_abort_expiration_action_refs",
    "pause_abort_expiration_action_ref",
    "review_lifecycle_status",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "retention_clock_stops_on_pause",
    "review_pause_does_not_stop_retention_deadline",
    "review_abort_requires_purge",
    "expired_requires_purge_even_when_rating_incomplete",
    "body_removed_priority_over_rating_completion_when_expired",
    "body_full_packet_retention_max_hours",
    "reviewer_notes_retention_after_rating_finalized_max_hours",
    "body_full_packet_age_hours",
    "reviewer_notes_age_hours",
    "body_full_packet_retention_expired",
    "reviewer_notes_retention_expired",
    "rating_rows_finalized",
    "question_observation_rows_finalized",
    "body_full_packet_purge_required",
    "reviewer_forms_purge_required",
    "reviewer_notes_purge_required",
    "purge_required_before_summary",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "aborted_or_expired_blocks_p5_confirmed_candidate",
    "p5_confirmed_candidate_allowed_after_protocol",
    "p5_repair_return_candidate_allowed_after_protocol",
    "p5_review_inconclusive_candidate_after_protocol",
    "disposal_receipt_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p5_actual_review_still_not_run",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "r53_15_pause_abort_expiration_protocol_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_R14_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS
P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS


def _r53_map_r51_rating_question_consistency_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_RATING_QUESTION_CONSISTENCY_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=60,
        max_length=140,
    )


def _r53_map_r51_pause_abort_expiration_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_PAUSE_ABORT_EXPIRATION_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=60,
        max_length=140,
    )


def _r53_actual_review_evidence_ready(data: Mapping[str, Any]) -> bool:
    return all(data.get(key) is True for key in P7_R53_R14_ALLOWED_TRUE_FALSE_KEY_REFS)


def _r53_pause_abort_action_for_status(status: str) -> str:
    if status == "PAUSED_RETENTION_CLOCK_STILL_RUNNING":
        return "PAUSE_LOCAL_ONLY_REVIEW"
    if status == "ABORTED_PURGE_REQUIRED":
        return "ABORT_LOCAL_ONLY_REVIEW"
    if status == "EXPIRED_PURGE_REQUIRED":
        return "EXPIRE_LOCAL_ONLY_REVIEW"
    if status == "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE":
        return "CONTINUE_TO_R51_14_PURGE"
    return "RESOLVE_R53_14_CONSISTENCY_GUARD"


def build_p7_r53_rating_question_consistency_guard_bodyfree(
    *,
    rating_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    r11_rating_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    r12_readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    r13_question_need_observation_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_rating_question_consistency_guard_bodyfree",
) -> dict[str, Any]:
    """Build R53-14 body-free guard for rating/question consistency.

    This stage prevents P5 readfeel failures from being reclassified as Plus or
    Premium question candidates.  It adopts the R51 R12 consistency guard with
    R53 current-snapshot and no-touch/no-body-leak evidence around it.
    """

    if rating_row_normalization_bodyfree is not None and r11_rating_row_normalization_bodyfree is not None:
        raise ValueError("provide only one R53-11 rating row normalization value")
    if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None and r12_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None:
        raise ValueError("provide only one R53-12 blocker ingestion value")
    if question_need_observation_row_normalization_bodyfree is not None and r13_question_need_observation_row_normalization_bodyfree is not None:
        raise ValueError("provide only one R53-13 question observation normalization value")

    r11 = (
        safe_mapping(rating_row_normalization_bodyfree)
        if rating_row_normalization_bodyfree is not None
        else safe_mapping(r11_rating_row_normalization_bodyfree)
        if r11_rating_row_normalization_bodyfree is not None
        else build_p7_r53_rating_row_normalization_bodyfree()
    )
    assert_p7_r53_rating_row_normalization_bodyfree_contract(r11)
    r12 = (
        safe_mapping(readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else safe_mapping(r12_readfeel_blocker_execution_blocker_ingestion_bodyfree)
        if r12_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(rating_row_normalization_bodyfree=r11)
    )
    assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r12)
    r13 = (
        safe_mapping(question_need_observation_row_normalization_bodyfree)
        if question_need_observation_row_normalization_bodyfree is not None
        else safe_mapping(r13_question_need_observation_row_normalization_bodyfree)
        if r13_question_need_observation_row_normalization_bodyfree is not None
        else build_p7_r53_question_need_observation_row_normalization_bodyfree(
            readfeel_blocker_execution_blocker_ingestion_bodyfree=r12,
        )
    )
    assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(r13)

    r11_ready = r11.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r11.get("execution_blocker_ids")
    r12_ready = r12.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r12.get("execution_blocker_ids")
    r13_ready = r13.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" and not r13.get("execution_blocker_ids")
    evidence_ready = bool(r11_ready and r12_ready and r13_ready)

    r51_r9 = safe_mapping(r11.get("r51_r9_rating_row_normalizer_bodyfree"))
    r51_r10 = safe_mapping(r12.get("r51_r10_readfeel_execution_blocker_ingestion_bodyfree"))
    r51_r11 = safe_mapping(r13.get("r51_r11_question_need_observation_row_normalizer_bodyfree"))
    assert_p7_r51_rating_row_normalizer_bodyfree_contract(
        r51_r9,
        allowed_true_false_key_refs=P7_R53_R11_ALLOWED_TRUE_FALSE_KEY_REFS if r11_ready else (),
    )
    assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(
        r51_r10,
        allowed_true_false_key_refs=P7_R53_R12_ALLOWED_TRUE_FALSE_KEY_REFS if r12_ready else (),
    )
    assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(
        r51_r11,
        allowed_true_false_key_refs=P7_R53_R13_ALLOWED_TRUE_FALSE_KEY_REFS if r13_ready else (),
    )

    r51_r12 = build_p7_r51_rating_question_observation_consistency_guard_bodyfree(
        rating_row_normalizer_bodyfree=r51_r9,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r51_r10,
        question_need_observation_row_normalizer_bodyfree=r51_r11,
        material_id="p7_r53_adopted_r51_r12_rating_question_consistency_guard_bodyfree",
    )
    r51_guard_ready = r51_r12.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" and not r51_r12.get("execution_blocker_ids")
    assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(
        r51_r12,
        allowed_true_false_key_refs=P7_R53_R14_ALLOWED_TRUE_FALSE_KEY_REFS if evidence_ready else (),
    )

    r51_blockers = dedupe_identifiers(r51_r12.get("execution_blocker_ids") or [], limit=60, max_length=140)
    blockers = _r53_map_r51_rating_question_consistency_blockers(r51_blockers)
    if not r11_ready and "r53_rating_row_normalization_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_rating_row_normalization_not_ready"], limit=60, max_length=140)
    if not r12_ready and "r53_blocker_ingestion_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_blocker_ingestion_not_ready"], limit=60, max_length=140)
    if not r13_ready and "r53_question_observation_rows_not_ready" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_question_observation_rows_not_ready"], limit=60, max_length=140)
    ready = bool(evidence_ready and r51_guard_ready and not blockers)
    reason_refs = ["r53_rating_question_consistency_guard_passed"] if ready else _r53_prefixed_reason_refs(
        r51_r12.get("consistency_guard_reason_refs") or [],
        default="r53_rating_question_consistency_guard_blocked",
        blocker_ids=blockers,
    )
    issue_rows = [safe_mapping(row) for row in r51_r12.get("consistency_issue_rows") or []]
    guard = {
        "schema_version": P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-14_rating_question_consistency_guard",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_rating_question_consistency_guard_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r13.get("review_session_id") or r12.get("review_session_id") or r11.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r11_rating_row_normalization_schema_version": P7_R53_RATING_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r11_rating_row_normalization_material_ref": clean_identifier(r11.get("material_id"), default="p7_r53_rating_row_normalization_bodyfree", max_length=180),
        "r11_rating_row_normalizer_status": clean_identifier(r11.get("rating_row_normalizer_status"), default="BLOCKED_BY_R53_10_ACTUAL_REVIEW_RESULT_CAPTURE", max_length=140),
        "r11_ready_for_consistency_guard": bool(r11_ready),
        "r12_blocker_ingestion_schema_version": P7_R53_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION,
        "r12_blocker_ingestion_material_ref": clean_identifier(r12.get("material_id"), default="p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree", max_length=180),
        "r12_blocker_ingestion_status": clean_identifier(r12.get("blocker_ingestion_status"), default="BLOCKED_BY_R53_11_RATING_ROW_NORMALIZATION", max_length=140),
        "r12_ready_for_consistency_guard": bool(r12_ready),
        "r13_question_observation_schema_version": P7_R53_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION,
        "r13_question_observation_material_ref": clean_identifier(r13.get("material_id"), default="p7_r53_question_need_observation_row_normalization_bodyfree", max_length=180),
        "r13_question_observation_normalizer_status": clean_identifier(r13.get("question_observation_normalizer_status"), default="BLOCKED_BY_R53_12_OR_R53_10_PRECHECK", max_length=140),
        "r13_ready_for_consistency_guard": bool(r13_ready),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r12_consistency_guard_schema_version": P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r51_r12_consistency_guard_material_ref": clean_identifier(r51_r12.get("material_id"), default="p7_r53_adopted_r51_r12_rating_question_consistency_guard_bodyfree", max_length=180),
        "r51_r12_rating_question_observation_consistency_guard_bodyfree": r51_r12,
        "r51_r12_rating_question_consistency_guard_status": clean_identifier(r51_r12.get("rating_question_consistency_guard_status"), default="BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY", max_length=160),
        "r51_r12_next_required_step": clean_identifier(r51_r12.get("next_required_step"), default=P7_R51_R12_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r12_execution_blocker_ids": r51_blockers,
        "review_session_status": "R53_RATING_QUESTION_CONSISTENCY_GUARD_READY" if ready else "PRECHECK_BLOCKED",
        "rating_question_consistency_guard_status": "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" if ready else "BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY",
        "rating_question_consistency_guard_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int_r53(r51_r12.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r53(r51_r12.get("question_observation_row_count")),
        "readfeel_blocker_row_count": _safe_non_negative_int_r53(r51_r12.get("readfeel_blocker_row_count")),
        "execution_blocker_row_count": _safe_non_negative_int_r53(r51_r12.get("execution_blocker_row_count")),
        "open_readfeel_blocker_count": _safe_non_negative_int_r53(r51_r12.get("open_readfeel_blocker_count")),
        "open_execution_blocker_count": _safe_non_negative_int_r53(r51_r12.get("open_execution_blocker_count")),
        "rating_question_case_ref_sets_match": bool(r51_r12.get("rating_question_case_ref_sets_match")),
        "all_required_rows_present": bool(r51_r12.get("all_required_rows_present")),
        "consistency_issue_row_schema_version": P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ROW_BODYFREE_SCHEMA_VERSION,
        "consistency_issue_row_required_field_refs": list(r51_r12.get("consistency_issue_row_required_field_refs") or []),
        "consistency_issue_id_refs": list(P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ID_REFS),
        "consistency_issue_kind_refs": list(P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_KIND_REFS),
        "consistency_issue_rows": issue_rows,
        "consistency_issue_count": len(issue_rows),
        "consistency_issue_id_counts": dict(safe_mapping(r51_r12.get("consistency_issue_id_counts"))),
        "consistency_issue_kind_counts": dict(safe_mapping(r51_r12.get("consistency_issue_kind_counts"))),
        "no_red_or_repair_routed_to_p8_question_candidate": bool(r51_r12.get("no_red_or_repair_routed_to_p8_question_candidate")),
        "no_creepy_or_boundary_blocker_routed_to_p8_question_candidate": bool(r51_r12.get("no_creepy_or_boundary_blocker_routed_to_p8_question_candidate")),
        "no_pass_rating_with_not_question_repair": bool(r51_r12.get("no_pass_rating_with_not_question_repair")),
        "no_repair_required_not_question_without_repair_ref": bool(r51_r12.get("no_repair_required_not_question_without_repair_ref")),
        "insufficient_material_observations_have_execution_blocker": bool(r51_r12.get("insufficient_material_observations_have_execution_blocker")),
        "p5_weakness_not_hidden_by_question_candidates": bool(ready and r51_r12.get("p5_weakness_not_hidden_by_question_candidate") is True),
        "p5_repair_return_required_by_consistency": bool(r51_r12.get("p5_repair_return_required_by_consistency")),
        "p8_question_material_candidate_allowed_by_consistency": bool(ready and r51_r12.get("p8_question_material_candidate_allowed_by_consistency") is True),
        "question_candidate_allowed_case_count": _safe_non_negative_int_r53(r51_r12.get("question_candidate_allowed_case_count")) if ready else 0,
        "p8_question_material_candidate_case_count": _safe_non_negative_int_r53(r51_r12.get("p8_question_material_candidate_case_count")) if ready else 0,
        "question_text_included_allowed": False,
        "draft_question_text_included_allowed": False,
        "reviewer_free_text_included_allowed": False,
        "raw_input_allowed": False,
        "returned_surface_allowed": False,
        "local_path_allowed": False,
        "body_hash_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        **_false_flags(),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(evidence_ready and r13.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(evidence_ready and r13.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(evidence_ready and r13.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(evidence_ready and r13.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(evidence_ready and r13.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(evidence_ready and r13.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": not evidence_ready,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r13.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r13.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r13.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r13.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r13.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r13.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": r13.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r53_13_question_need_observation_row_normalization_built": r13.get("r53_13_question_need_observation_row_normalization_built") is True,
        "r53_14_rating_question_consistency_guard_built": ready,
        "execution_blocker_ids": [] if ready else blockers,
        "open_execution_blocker_ids": [] if ready else blockers,
        "implemented_steps": list(P7_R53_R14_IMPLEMENTED_STEPS if ready else P7_R53_R13_IMPLEMENTED_STEPS if r13_ready else P7_R53_R12_IMPLEMENTED_STEPS if r12_ready else P7_R53_R11_IMPLEMENTED_STEPS if r11_ready else P7_R53_R9_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R14_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R53_R13_NOT_YET_IMPLEMENTED_STEPS if r13_ready else P7_R53_R12_NOT_YET_IMPLEMENTED_STEPS if r12_ready else P7_R53_R11_NOT_YET_IMPLEMENTED_STEPS if r11_ready else P7_R53_R9_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R14_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R14_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(guard)
    return guard


def assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(guard: Mapping[str, Any]) -> bool:
    data = safe_mapping(guard)
    _assert_required_fields(data, required=P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS, source="p7_r53_r14_rating_question_consistency_guard_bodyfree")
    ready = data.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    evidence_ready = _r53_actual_review_evidence_ready(data)
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        source="p7_r53_r14_rating_question_consistency_guard_bodyfree",
        allowed_true_false_key_refs=P7_R53_R14_ALLOWED_TRUE_FALSE_KEY_REFS if evidence_ready else (),
    )
    if data.get("policy_section") != "R53-14_rating_question_consistency_guard":
        raise ValueError("R53 R14 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R14 current refs changed")
    r51_r12 = safe_mapping(data.get("r51_r12_rating_question_observation_consistency_guard_bodyfree"))
    assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(
        r51_r12,
        allowed_true_false_key_refs=P7_R53_R14_ALLOWED_TRUE_FALSE_KEY_REFS if evidence_ready else (),
    )
    if data.get("r51_r12_consistency_guard_schema_version") != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION:
        raise ValueError("R53 R14 R51 R12 schema reference changed")
    if data.get("r51_r12_rating_question_consistency_guard_status") != r51_r12.get("rating_question_consistency_guard_status"):
        raise ValueError("R53 R14 R51 R12 status mismatch")
    if data.get("consistency_issue_count") != len(data.get("consistency_issue_rows") or []):
        raise ValueError("R53 R14 consistency issue count mismatch")
    if tuple(data.get("consistency_issue_id_refs") or ()) != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_ID_REFS:
        raise ValueError("R53 R14 consistency issue ids changed")
    if tuple(data.get("consistency_issue_kind_refs") or ()) != P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_ISSUE_KIND_REFS:
        raise ValueError("R53 R14 consistency issue kinds changed")
    for row in data.get("consistency_issue_rows") or []:
        assert_p7_no_body_payload_or_contract_mutation(safe_mapping(row), source="p7_r53_r14_consistency_issue_row")
    for false_key in (
        "question_text_included_allowed",
        "draft_question_text_included_allowed",
        "reviewer_free_text_included_allowed",
        "raw_input_allowed",
        "returned_surface_allowed",
        "local_path_allowed",
        "body_hash_allowed",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_question_need_observation_summary_materialized_here",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R14 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R14 open blockers must match execution blockers")
    if data.get("r53_14_rating_question_consistency_guard_built") is not ready:
        raise ValueError("R53 R14 built flag must match readiness")
    if ready:
        if data.get("r11_ready_for_consistency_guard") is not True or data.get("r12_ready_for_consistency_guard") is not True or data.get("r13_ready_for_consistency_guard") is not True:
            raise ValueError("R53 R14 ready guard requires ready R11/R12/R13")
        if data.get("r51_r12_next_required_step") != P7_R51_R12_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R14 ready R51 R12 must point to R51-13")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT or data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R14 ready guard requires 24 rating and question rows")
        if data.get("rating_question_case_ref_sets_match") is not True or data.get("all_required_rows_present") is not True:
            raise ValueError("R53 R14 ready guard requires complete matching case sets")
        if data.get("consistency_issue_count") != 0 or blockers:
            raise ValueError("R53 R14 ready guard must have no consistency issues or blockers")
        if data.get("p5_weakness_not_hidden_by_question_candidates") is not True:
            raise ValueError("R53 R14 must verify P5 weakness is not hidden by question candidates")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R53 R14 ready guard must preserve actual review evidence")
        if data.get("actual_rating_rows_materialized_here") is not True or data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("R53 R14 ready guard must preserve rating/question evidence")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R53 R14 ready guard must not say review is still unrun")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R14_IMPLEMENTED_STEPS:
            raise ValueError("R53 R14 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R14_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R14 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R14_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R14 ready guard must point to R53-15")
    else:
        if data.get("r53_14_rating_question_consistency_guard_built") is not False:
            raise ValueError("R53 R14 blocked guard must not claim built")
        if data.get("next_required_step") != P7_R53_R14_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R14 blocked guard must point to R53-13 resolution")
        if not blockers:
            raise ValueError("R53 R14 blocked guard must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r14_rating_question_consistency_guard_bodyfree")
    return True


def build_p7_r53_pause_abort_expiration_protocol_bodyfree(
    *,
    rating_question_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    r14_rating_question_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    review_lifecycle_status: Any = "REVIEW_COMPLETED",
    body_full_packet_age_hours: Any = 0,
    reviewer_notes_age_hours: Any = 0,
    rating_rows_finalized: Any | None = None,
    question_observation_rows_finalized: Any | None = None,
    material_id: Any = "p7_r53_pause_abort_expiration_protocol_bodyfree",
) -> dict[str, Any]:
    """Build R53-15 body-free pause / abort / expiration protocol.

    The protocol keeps body-full local review material under retention control;
    it never purges or writes a disposal receipt here.  Completed, aborted, or
    expired sessions move to R53-16 purge, while a non-expired pause remains
    paused with the retention clock still running.
    """

    if rating_question_consistency_guard_bodyfree is not None and r14_rating_question_consistency_guard_bodyfree is not None:
        raise ValueError("provide only one R53-14 rating/question consistency guard value")
    r14 = (
        safe_mapping(rating_question_consistency_guard_bodyfree)
        if rating_question_consistency_guard_bodyfree is not None
        else safe_mapping(r14_rating_question_consistency_guard_bodyfree)
        if r14_rating_question_consistency_guard_bodyfree is not None
        else build_p7_r53_rating_question_consistency_guard_bodyfree()
    )
    assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(r14)
    r14_ready = r14.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" and not r14.get("execution_blocker_ids")
    r14_evidence_ready = _r53_actual_review_evidence_ready(r14)
    r51_r12 = safe_mapping(r14.get("r51_r12_rating_question_observation_consistency_guard_bodyfree"))
    assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(
        r51_r12,
        allowed_true_false_key_refs=P7_R53_R14_ALLOWED_TRUE_FALSE_KEY_REFS if r14_evidence_ready else (),
    )
    r51_r13 = build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=r51_r12,
        review_lifecycle_status=review_lifecycle_status,
        body_full_packet_age_hours=body_full_packet_age_hours,
        reviewer_notes_age_hours=reviewer_notes_age_hours,
        rating_rows_finalized=rating_rows_finalized,
        question_observation_rows_finalized=question_observation_rows_finalized,
        material_id="p7_r53_adopted_r51_r13_pause_abort_expiration_protocol_bodyfree",
    )
    protocol_status_r51 = clean_identifier(r51_r13.get("pause_abort_expiration_protocol_status"), default="BLOCKED_BY_R51_12_CONSISTENCY_GUARD", max_length=160)
    protocol_ready_or_paused = protocol_status_r51 in {
        "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE",
        "PAUSED_RETENTION_CLOCK_STILL_RUNNING",
        "ABORTED_PURGE_REQUIRED",
        "EXPIRED_PURGE_REQUIRED",
    }
    assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(
        r51_r13,
        allowed_true_false_key_refs=P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS if r14_evidence_ready and r14_ready else (),
    )
    r51_blockers = dedupe_identifiers(r51_r13.get("execution_blocker_ids") or [], limit=60, max_length=140)
    blockers = _r53_map_r51_pause_abort_expiration_blockers(r51_blockers)
    if not r14_ready and "r53_rating_question_observation_inconsistent" not in blockers:
        blockers = dedupe_identifiers([*blockers, "r53_rating_question_observation_inconsistent"], limit=60, max_length=140)
    protocol_built = bool(r14_ready and protocol_ready_or_paused and not blockers)
    r53_protocol_status = protocol_status_r51 if protocol_built else "BLOCKED_BY_R53_14_CONSISTENCY_GUARD"
    if r53_protocol_status == "PAUSED_RETENTION_CLOCK_STILL_RUNNING":
        next_step = P7_R53_R15_PAUSED_NEXT_REQUIRED_STEP_REF
    elif r53_protocol_status in {"READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", "ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"}:
        next_step = P7_R53_R15_NEXT_REQUIRED_STEP_REF
    else:
        next_step = P7_R53_R15_BLOCKED_NEXT_REQUIRED_STEP_REF
    reason_refs = [
        "r53_pause_abort_expiration_protocol_ready_for_purge"
    ] if r53_protocol_status == "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE" else [
        "r53_pause_abort_expiration_protocol_paused_retention_clock_running"
    ] if r53_protocol_status == "PAUSED_RETENTION_CLOCK_STILL_RUNNING" else [
        "r53_pause_abort_expiration_protocol_aborted_purge_required"
    ] if r53_protocol_status == "ABORTED_PURGE_REQUIRED" else [
        "r53_pause_abort_expiration_protocol_expired_purge_required"
    ] if r53_protocol_status == "EXPIRED_PURGE_REQUIRED" else _r53_prefixed_reason_refs(
        r51_r13.get("pause_abort_expiration_reason_refs") or [],
        default="r53_pause_abort_expiration_protocol_blocked",
        blocker_ids=blockers,
    )
    action_ref = _r53_pause_abort_action_for_status(r53_protocol_status)
    protocol = {
        "schema_version": P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-15_pause_abort_expiration_protocol",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r14.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r14_consistency_guard_schema_version": P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION,
        "r14_consistency_guard_material_ref": clean_identifier(r14.get("material_id"), default="p7_r53_rating_question_consistency_guard_bodyfree", max_length=180),
        "r14_rating_question_consistency_guard_status": clean_identifier(r14.get("rating_question_consistency_guard_status"), default="BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY", max_length=160),
        "r14_ready_for_pause_abort_expiration_protocol": bool(r14_ready),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r13_pause_abort_expiration_protocol_schema_version": P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "r51_r13_pause_abort_expiration_protocol_material_ref": clean_identifier(r51_r13.get("material_id"), default="p7_r53_adopted_r51_r13_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "r51_r13_pause_abort_expiration_protocol_bodyfree": r51_r13,
        "r51_r13_pause_abort_expiration_protocol_status": protocol_status_r51,
        "r51_r13_next_required_step": clean_identifier(r51_r13.get("next_required_step"), default=P7_R51_R13_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r13_execution_blocker_ids": r51_blockers,
        "review_session_status": "R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY" if protocol_built else "PRECHECK_BLOCKED",
        "pause_abort_expiration_protocol_status": r53_protocol_status,
        "pause_abort_expiration_reason_refs": reason_refs,
        "pause_abort_expiration_action_refs": list(P7_R51_PAUSE_ABORT_EXPIRATION_ACTION_REFS),
        "pause_abort_expiration_action_ref": action_ref,
        "review_lifecycle_status": clean_identifier(r51_r13.get("review_lifecycle_status"), default="REVIEW_COMPLETED", max_length=120),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int_r53(r51_r13.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r53(r51_r13.get("question_observation_row_count")),
        "retention_clock_stops_on_pause": False,
        "review_pause_does_not_stop_retention_deadline": True,
        "review_abort_requires_purge": True,
        "expired_requires_purge_even_when_rating_incomplete": True,
        "body_removed_priority_over_rating_completion_when_expired": bool(r51_r13.get("body_removed_priority_over_rating_completion_when_expired")),
        "body_full_packet_retention_max_hours": r51_r13.get("body_full_packet_retention_max_hours"),
        "reviewer_notes_retention_after_rating_finalized_max_hours": r51_r13.get("reviewer_notes_retention_after_rating_finalized_max_hours"),
        "body_full_packet_age_hours": r51_r13.get("body_full_packet_age_hours"),
        "reviewer_notes_age_hours": r51_r13.get("reviewer_notes_age_hours"),
        "body_full_packet_retention_expired": bool(r51_r13.get("body_full_packet_retention_expired")),
        "reviewer_notes_retention_expired": bool(r51_r13.get("reviewer_notes_retention_expired")),
        "rating_rows_finalized": bool(r51_r13.get("rating_rows_finalized")),
        "question_observation_rows_finalized": bool(r51_r13.get("question_observation_rows_finalized")),
        "body_full_packet_purge_required": bool(protocol_built and r51_r13.get("body_full_packet_purge_required") is True),
        "reviewer_forms_purge_required": bool(protocol_built and r51_r13.get("reviewer_forms_purge_required") is True),
        "reviewer_notes_purge_required": bool(protocol_built and r51_r13.get("reviewer_notes_purge_required") is True),
        "purge_required_before_summary": bool(protocol_built and r51_r13.get("purge_required_before_summary") is True),
        "body_removed": False,
        "reviewer_notes_removed": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "aborted_or_expired_blocks_p5_confirmed_candidate": bool(r51_r13.get("aborted_or_expired_blocks_p5_confirmed_candidate")),
        "p5_confirmed_candidate_allowed_after_protocol": False,
        "p5_repair_return_candidate_allowed_after_protocol": False,
        "p5_review_inconclusive_candidate_after_protocol": bool(r51_r13.get("p5_review_inconclusive_candidate_after_protocol")),
        "disposal_receipt_materialized_here": False,
        "actual_disposal_run_here": False,
        "actual_disposal_receipt_materialized_here": False,
        "post_review_summary_materialized_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        **_false_flags(),
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(r14_evidence_ready and r14.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(r14_evidence_ready and r14.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(r14_evidence_ready and r14.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(r14_evidence_ready and r14.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(r14_evidence_ready and r14.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(r14_evidence_ready and r14.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": not r14_evidence_ready,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r14.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r14.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r14.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r14.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r14.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r14.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": r14.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r53_13_question_need_observation_row_normalization_built": r14.get("r53_13_question_need_observation_row_normalization_built") is True,
        "r53_14_rating_question_consistency_guard_built": r14.get("r53_14_rating_question_consistency_guard_built") is True,
        "r53_15_pause_abort_expiration_protocol_built": protocol_built,
        "execution_blocker_ids": [] if protocol_built else blockers,
        "open_execution_blocker_ids": [] if protocol_built else blockers,
        "implemented_steps": list(P7_R53_R15_IMPLEMENTED_STEPS if protocol_built else P7_R53_R14_IMPLEMENTED_STEPS if r14_ready else P7_R53_R13_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R15_NOT_YET_IMPLEMENTED_STEPS if protocol_built else P7_R53_R14_NOT_YET_IMPLEMENTED_STEPS if r14_ready else P7_R53_R13_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": next_step,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_pause_abort_expiration_protocol_bodyfree_contract(protocol)
    return protocol


def assert_p7_r53_pause_abort_expiration_protocol_bodyfree_contract(protocol: Mapping[str, Any]) -> bool:
    data = safe_mapping(protocol)
    _assert_required_fields(data, required=P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS, source="p7_r53_r15_pause_abort_expiration_protocol_bodyfree")
    protocol_built = data.get("r53_15_pause_abort_expiration_protocol_built") is True
    evidence_ready = _r53_actual_review_evidence_ready(data)
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        source="p7_r53_r15_pause_abort_expiration_protocol_bodyfree",
        allowed_true_false_key_refs=P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS if evidence_ready else (),
    )
    if data.get("policy_section") != "R53-15_pause_abort_expiration_protocol":
        raise ValueError("R53 R15 policy section changed")
    if safe_mapping(data.get("current_received_snapshot_refs")) != P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS:
        raise ValueError("R53 R15 current refs changed")
    r51_r13 = safe_mapping(data.get("r51_r13_pause_abort_expiration_protocol_bodyfree"))
    assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(
        r51_r13,
        allowed_true_false_key_refs=P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS if evidence_ready and data.get("r14_ready_for_pause_abort_expiration_protocol") is True else (),
    )
    if data.get("r51_r13_pause_abort_expiration_protocol_schema_version") != P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION:
        raise ValueError("R53 R15 R51 R13 schema reference changed")
    if data.get("r51_r13_pause_abort_expiration_protocol_status") != r51_r13.get("pause_abort_expiration_protocol_status"):
        raise ValueError("R53 R15 R51 R13 status mismatch")
    for false_key in (
        "retention_clock_stops_on_pause",
        "body_removed",
        "reviewer_notes_removed",
        "local_packet_exported",
        "content_hash_of_body_stored",
        "p5_confirmed_candidate_allowed_after_protocol",
        "p5_repair_return_candidate_allowed_after_protocol",
        "disposal_receipt_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "post_review_summary_materialized_here",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_question_need_observation_summary_materialized_here",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R15 must keep {false_key}=False")
    for true_key in (
        "review_pause_does_not_stop_retention_deadline",
        "review_abort_requires_purge",
        "expired_requires_purge_even_when_rating_incomplete",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R15 must keep {true_key}=True")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R15 open blockers must match execution blockers")
    if data.get("pause_abort_expiration_action_ref") not in (*P7_R51_PAUSE_ABORT_EXPIRATION_ACTION_REFS, "RESOLVE_R53_14_CONSISTENCY_GUARD"):
        raise ValueError("R53 R15 action ref changed")
    if tuple(data.get("pause_abort_expiration_action_refs") or ()) != P7_R51_PAUSE_ABORT_EXPIRATION_ACTION_REFS:
        raise ValueError("R53 R15 action refs changed")
    status = data.get("pause_abort_expiration_protocol_status")
    if status == "BLOCKED_BY_R53_14_CONSISTENCY_GUARD":
        if protocol_built is not False:
            raise ValueError("R53 R15 blocked protocol must not claim built")
        if data.get("next_required_step") != P7_R53_R15_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R15 blocked protocol must point to R53-14 resolution")
        if not blockers:
            raise ValueError("R53 R15 blocked protocol must keep blockers visible")
    else:
        if protocol_built is not True:
            raise ValueError("R53 R15 ready/paused protocol must claim built")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R15_IMPLEMENTED_STEPS:
            raise ValueError("R53 R15 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R15_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R15 not-yet steps changed")
        if data.get("actual_human_review_run_here") is not True or data.get("actual_manual_review_run_here") is not True:
            raise ValueError("R53 R15 protocol must preserve actual review evidence once built")
        if data.get("actual_rating_rows_materialized_here") is not True or data.get("actual_question_need_observation_rows_materialized_here") is not True:
            raise ValueError("R53 R15 protocol must preserve rating/question rows once built")
        if data.get("p5_actual_review_still_not_run") is not False:
            raise ValueError("R53 R15 built protocol must not say review is still unrun")
    if status == "PAUSED_RETENTION_CLOCK_STILL_RUNNING":
        if data.get("retention_clock_stops_on_pause") is not False:
            raise ValueError("R53 R15 pause must not stop retention clock")
        if data.get("body_full_packet_purge_required") is not False:
            raise ValueError("R53 R15 non-expired pause must not require purge yet")
        if data.get("next_required_step") != P7_R53_R15_PAUSED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R15 paused protocol must stay in R53-15")
    if status in {"READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", "ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"}:
        for true_key in ("body_full_packet_purge_required", "reviewer_forms_purge_required", "reviewer_notes_purge_required", "purge_required_before_summary"):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R15 purge path must keep {true_key}=True")
        if data.get("next_required_step") != P7_R53_R15_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R15 purge path must point to R53-16")
    if status in {"ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"} and data.get("aborted_or_expired_blocks_p5_confirmed_candidate") is not True:
        raise ValueError("R53 R15 aborted/expired must block P5 confirmed candidate")
    if status == "EXPIRED_PURGE_REQUIRED" and data.get("body_removed_priority_over_rating_completion_when_expired") is not True:
        raise ValueError("R53 R15 expired protocol must prioritize body removal")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r15_pause_abort_expiration_protocol_bodyfree")
    return True


# ---------------------------------------------------------------------------
# R53-16 / R53-17: purge/disposal receipt and body-free post-review summary
# ---------------------------------------------------------------------------

P7_R53_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.purge_disposal_receipt.bodyfree.v1"
)
P7_R53_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.body_free_post_review_summary.bodyfree.v1"
)

P7_R53_R16_NEXT_REQUIRED_STEP_REF: Final = "R53-17_body_free_post_review_summary"
P7_R53_R16_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-16_purge_disposal_receipt_before_R53-17_summary"
)
P7_R53_R17_NEXT_REQUIRED_STEP_REF: Final = "R53-18_p5_decision_candidate_separation"
P7_R53_R17_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-17_body_free_post_review_summary_before_R53-18_p5_decision_candidate_separation"
)

P7_R53_FUTURE_STEPS_AFTER_R17: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R15
    if step
    not in {
        "R53-16_purge_disposal_receipt",
        "R53-17_body_free_post_review_summary",
    }
)
P7_R53_R16_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R15_IMPLEMENTED_STEPS,
    "R53-16_purge_disposal_receipt",
)
P7_R53_R16_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-17_body_free_post_review_summary",
    *P7_R53_FUTURE_STEPS_AFTER_R17,
)
P7_R53_R17_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R16_IMPLEMENTED_STEPS,
    "R53-17_body_free_post_review_summary",
)
P7_R53_R17_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R17

P7_R53_R51_TO_R53_PURGE_DISPOSAL_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_PAUSE_ABORT_EXPIRATION_BLOCKER_MAP,
    "r51_disposal_plan_missing": "r53_disposal_plan_missing",
    "r51_disposal_receipt_missing": "r53_disposal_receipt_missing",
    "r51_disposal_failed": "r53_disposal_failed",
    "r51_disposal_not_verified": "r53_disposal_not_verified",
    "r51_body_full_packet_or_reviewer_notes_purge_not_verified": "r53_body_full_packet_or_reviewer_notes_purge_not_verified",
}
P7_R53_R51_TO_R53_POST_REVIEW_SUMMARY_BLOCKER_MAP: Final[dict[str, str]] = {
    **P7_R53_R51_TO_R53_PURGE_DISPOSAL_BLOCKER_MAP,
    "r51_post_review_summary_incomplete": "r53_post_review_summary_incomplete",
    "r51_rating_rows_incomplete": "r53_rating_rows_incomplete_for_summary",
    "r51_question_need_observation_rows_incomplete": "r53_question_observation_rows_incomplete_for_summary",
    "r51_disposal_not_verified": "r53_disposal_not_verified_before_summary",
}

P7_R53_PURGE_DISPOSAL_RECEIPT_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY",
    "BLOCKED_BY_R53_15_PAUSE_OR_BLOCKED_PROTOCOL",
    "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE",
    "BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION",
)
P7_R53_POST_REVIEW_SUMMARY_STATUS_REFS: Final[tuple[str, ...]] = (
    "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION",
    "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS",
)

P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS,
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
)
P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    "actual_question_need_observation_summary_materialized_here",
    "post_review_summary_materialized_here",
)

P7_R53_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r15_pause_abort_expiration_protocol_schema_version",
    "r15_pause_abort_expiration_protocol_material_ref",
    "r15_pause_abort_expiration_protocol_status",
    "r15_ready_for_purge_disposal_receipt",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r14_purge_schema_version",
    "r51_r14_purge_material_ref",
    "r51_r14_body_full_packet_reviewer_notes_purge_bodyfree",
    "r51_r14_purge_status",
    "r51_r14_next_required_step",
    "r51_r14_execution_blocker_ids",
    "r51_r15_disposal_receipt_schema_version",
    "r51_r15_disposal_receipt_material_ref",
    "r51_r15_disposal_receipt_builder_verifier_bodyfree",
    "r51_r15_disposal_receipt_verifier_status",
    "r51_r15_next_required_step",
    "r51_r15_execution_blocker_ids",
    "review_session_status",
    "purge_disposal_receipt_status",
    "purge_disposal_reason_refs",
    "required_case_count",
    "required_purge_target_refs",
    "purge_evidence_row_schema_version",
    "purge_evidence_row_required_field_refs",
    "purge_evidence_rows",
    "purge_evidence_row_count",
    "purge_target_count",
    "verified_purge_target_count",
    "missing_purge_target_refs",
    "failed_purge_target_refs",
    "not_verified_purge_target_refs",
    "deleted_file_count",
    "purge_started_at_ref",
    "purge_completed_at_ref",
    "disposal_receipt_schema_version",
    "disposal_receipt_required_field_refs",
    "disposal_receipt",
    "disposal_status",
    "disposal_verified",
    "disposal_failed",
    "disposal_receipt_missing",
    "summary_finalize_allowed",
    "body_removed",
    "reviewer_forms_removed",
    "reviewer_notes_removed",
    "body_full_packets_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "receipt_contains_body_full_material",
    "local_absolute_path_included",
    "body_content_hash_included",
    "deleted_body_preview_included",
    "terminal_output_included",
    "local_file_delete_ops_executed_by_helper",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p5_actual_review_still_not_run",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "r53_15_pause_abort_expiration_protocol_built",
    "r53_16_purge_disposal_receipt_built",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_BODY_FREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r16_purge_disposal_receipt_schema_version",
    "r16_purge_disposal_receipt_material_ref",
    "r16_purge_disposal_receipt_status",
    "r16_ready_for_post_review_summary",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r16_post_review_summary_schema_version",
    "r51_r16_post_review_summary_material_ref",
    "r51_r16_body_free_post_review_summary_builder_bodyfree",
    "r51_r16_post_review_summary_status",
    "r51_r16_next_required_step",
    "r51_r16_execution_blocker_ids",
    "review_session_status",
    "post_review_summary_status",
    "post_review_summary_reason_refs",
    "required_case_count",
    "all_24_cases_reviewed",
    "rating_row_count",
    "question_observation_row_count",
    "open_execution_blocker_count",
    "open_readfeel_blocker_count",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "verdict_counts",
    "axis_score_averages",
    "axis_target_refs",
    "axis_target_met_refs",
    "axis_target_missed_refs",
    "all_axis_targets_met",
    "readfeel_blocker_counts",
    "execution_blocker_counts",
    "question_need_primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "red_count",
    "repair_required_count",
    "yellow_count",
    "pass_count",
    "critical_repair_blocker_count",
    "repair_observation_count",
    "disposal_verified",
    "body_removed",
    "reviewer_forms_removed",
    "reviewer_notes_removed",
    "body_free_summary_contains_only_counts_and_refs",
    "raw_input_included",
    "returned_surface_included",
    "comment_text_included",
    "reviewer_free_text_included",
    "question_text_included",
    "draft_question_text_included",
    "local_absolute_path_included",
    "body_content_hash_included",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "p5_confirmed_requirements_met_by_summary",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "hold004_close_allowed",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "p5_actual_review_still_not_run",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "r53_15_pause_abort_expiration_protocol_built",
    "r53_16_purge_disposal_receipt_built",
    "r53_17_body_free_post_review_summary_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def _r53_map_r51_purge_disposal_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_PURGE_DISPOSAL_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=60,
        max_length=140,
    )


def _r53_map_r51_post_review_summary_blockers(blocker_ids: Sequence[Any]) -> list[str]:
    return dedupe_identifiers(
        (
            P7_R53_R51_TO_R53_POST_REVIEW_SUMMARY_BLOCKER_MAP.get(
                str(blocker),
                str(blocker).replace("r51_", "r53_", 1),
            )
            for blocker in blocker_ids
        ),
        limit=60,
        max_length=140,
    )


def _r53_purge_disposal_status(*, r51_r14: Mapping[str, Any], r51_r15: Mapping[str, Any], r15_ready_for_purge: bool) -> str:
    r14_status = clean_identifier(r51_r14.get("purge_status"), default="BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", max_length=180)
    r15_status = clean_identifier(r51_r15.get("disposal_receipt_verifier_status"), default="BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION", max_length=180)
    if not r15_ready_for_purge:
        return "BLOCKED_BY_R53_15_PAUSE_OR_BLOCKED_PROTOCOL"
    if r14_status != "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER":
        return "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    if r15_status != "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER":
        return "BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION"
    return "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY"


def build_p7_r53_purge_evidence_row_bodyfree(
    *,
    review_session_id: Any = P7_R53_DEFAULT_REVIEW_SESSION_ID,
    purge_target_ref: Any,
    purge_target_kind: Any | None = None,
    purge_required: bool = True,
    purge_attempted: bool = True,
    removed: bool = True,
    removed_count: Any = 1,
    verification_status_ref: Any | None = None,
) -> dict[str, Any]:
    """Build an R53-scoped body-free purge evidence row via the R51 row contract."""
    row = build_p7_r51_purge_evidence_row_bodyfree(
        review_session_id=clean_identifier(review_session_id, default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        purge_target_ref=purge_target_ref,
        purge_target_kind=purge_target_kind,
        purge_required=purge_required,
        purge_attempted=purge_attempted,
        removed=removed,
        removed_count=removed_count,
        verification_status_ref=verification_status_ref,
    )
    assert_p7_r51_purge_evidence_row_bodyfree_contract(row)
    assert_p7_no_body_payload_or_contract_mutation(row, source="p7_r53_purge_evidence_row_bodyfree")
    return row


def build_p7_r53_default_verified_purge_evidence_rows_bodyfree(
    *,
    review_session_id: Any = P7_R53_DEFAULT_REVIEW_SESSION_ID,
) -> list[dict[str, Any]]:
    """Return sanitized body-free rows proving all required local-only targets were removed.

    The helper only materializes controller-provided verification rows. It never
    deletes files, lists paths, stores body hashes, or records terminal output.
    """
    return [
        build_p7_r53_purge_evidence_row_bodyfree(
            review_session_id=review_session_id,
            purge_target_ref=target_ref,
            purge_target_kind=target_ref,
            purge_required=True,
            purge_attempted=True,
            removed=True,
            removed_count=P7_R51_REQUIRED_CASE_COUNT,
        )
        for target_ref in P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS
    ]


def build_p7_r53_purge_disposal_receipt_bodyfree(
    *,
    pause_abort_expiration_protocol_bodyfree: Mapping[str, Any] | None = None,
    r15_pause_abort_expiration_protocol_bodyfree: Mapping[str, Any] | None = None,
    purge_evidence_rows: Sequence[Mapping[str, Any]] | None = None,
    purge_started_at_ref: Any = "r53_local_only_purge_started_at_local_controller",
    purge_completed_at_ref: Any = "r53_local_only_purge_completed_at_local_controller",
    material_id: Any = "p7_r53_purge_disposal_receipt_bodyfree",
) -> dict[str, Any]:
    """Build R53-16 body-free purge verification + disposal receipt material.

    This does not perform local file deletion. It adopts R51 R14/R15 body-free
    builders to verify sanitized local-only purge rows and keeps paths, bodies,
    hashes, reviewer notes, and terminal output out of exported evidence.
    """

    if pause_abort_expiration_protocol_bodyfree is not None and r15_pause_abort_expiration_protocol_bodyfree is not None:
        raise ValueError("provide only one R53-15 pause/abort/expiration protocol value")
    r15 = safe_mapping(
        pause_abort_expiration_protocol_bodyfree
        if pause_abort_expiration_protocol_bodyfree is not None
        else r15_pause_abort_expiration_protocol_bodyfree
        if r15_pause_abort_expiration_protocol_bodyfree is not None
        else build_p7_r53_pause_abort_expiration_protocol_bodyfree()
    )
    assert_p7_r53_pause_abort_expiration_protocol_bodyfree_contract(r15)

    r15_ready_for_purge = (
        r15.get("r53_15_pause_abort_expiration_protocol_built") is True
        and r15.get("pause_abort_expiration_protocol_status")
        in {"READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", "ABORTED_PURGE_REQUIRED", "EXPIRED_PURGE_REQUIRED"}
        and r15.get("next_required_step") == P7_R53_R15_NEXT_REQUIRED_STEP_REF
    )
    r51_r13 = safe_mapping(r15.get("r51_r13_pause_abort_expiration_protocol_bodyfree"))
    assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(
        r51_r13,
        allowed_true_false_key_refs=P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS,
    )
    r51_r14 = build_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree(
        r13_pause_abort_expiration_protocol_bodyfree=r51_r13,
        purge_evidence_rows=purge_evidence_rows if r15_ready_for_purge else [],
        purge_started_at_ref=purge_started_at_ref,
        purge_completed_at_ref=purge_completed_at_ref,
        material_id="p7_r53_adopted_r51_r14_body_full_packet_reviewer_notes_purge_bodyfree",
    )
    assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract(
        r51_r14,
        allowed_true_false_key_refs=P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    )
    r51_r15 = build_p7_r51_disposal_receipt_builder_verifier_bodyfree(
        body_full_packet_reviewer_notes_purge_bodyfree=r51_r14,
        material_id="p7_r53_adopted_r51_r15_disposal_receipt_builder_verifier_bodyfree",
    )
    assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(
        r51_r15,
        allowed_true_false_key_refs=P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    )

    status = _r53_purge_disposal_status(r51_r14=r51_r14, r51_r15=r51_r15, r15_ready_for_purge=bool(r15_ready_for_purge))
    ready = status == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY"
    r51_blockers = dedupe_identifiers(
        [*(r51_r14.get("execution_blocker_ids") or []), *(r51_r15.get("execution_blocker_ids") or [])],
        limit=60,
        max_length=140,
    )
    blockers = [] if ready else _r53_map_r51_purge_disposal_blockers(r51_blockers or ["r51_disposal_not_verified"])
    reason_refs = ["r53_purge_disposal_receipt_bodyfree_verified"] if ready else _r53_prefixed_reason_refs(
        [*(r51_r14.get("purge_reason_refs") or []), *(r51_r15.get("disposal_receipt_reason_refs") or [])],
        default="r53_purge_disposal_receipt_blocked",
        blocker_ids=blockers,
    )
    purge_rows = [safe_mapping(row) for row in r51_r14.get("purge_evidence_rows") or []]
    for row in purge_rows:
        assert_p7_r51_purge_evidence_row_bodyfree_contract(row)
    receipt = safe_mapping(r51_r15.get("disposal_receipt"))
    material = {
        "schema_version": P7_R53_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-16_purge_disposal_receipt",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_purge_disposal_receipt_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r15.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r15_pause_abort_expiration_protocol_schema_version": P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION,
        "r15_pause_abort_expiration_protocol_material_ref": clean_identifier(r15.get("material_id"), default="p7_r53_pause_abort_expiration_protocol_bodyfree", max_length=180),
        "r15_pause_abort_expiration_protocol_status": clean_identifier(r15.get("pause_abort_expiration_protocol_status"), default="BLOCKED_BY_R53_14_CONSISTENCY_GUARD", max_length=180),
        "r15_ready_for_purge_disposal_receipt": bool(r15_ready_for_purge),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r14_purge_schema_version": P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION,
        "r51_r14_purge_material_ref": clean_identifier(r51_r14.get("material_id"), default="p7_r53_adopted_r51_r14_body_full_packet_reviewer_notes_purge_bodyfree", max_length=180),
        "r51_r14_body_full_packet_reviewer_notes_purge_bodyfree": r51_r14,
        "r51_r14_purge_status": clean_identifier(r51_r14.get("purge_status"), default="BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE", max_length=180),
        "r51_r14_next_required_step": clean_identifier(r51_r14.get("next_required_step"), default=P7_R51_R14_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r14_execution_blocker_ids": dedupe_identifiers(r51_r14.get("execution_blocker_ids") or [], limit=60, max_length=140),
        "r51_r15_disposal_receipt_schema_version": P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION,
        "r51_r15_disposal_receipt_material_ref": clean_identifier(r51_r15.get("material_id"), default="p7_r53_adopted_r51_r15_disposal_receipt_builder_verifier_bodyfree", max_length=180),
        "r51_r15_disposal_receipt_builder_verifier_bodyfree": r51_r15,
        "r51_r15_disposal_receipt_verifier_status": clean_identifier(r51_r15.get("disposal_receipt_verifier_status"), default="BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION", max_length=180),
        "r51_r15_next_required_step": clean_identifier(r51_r15.get("next_required_step"), default=P7_R51_R15_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r15_execution_blocker_ids": dedupe_identifiers(r51_r15.get("execution_blocker_ids") or [], limit=60, max_length=140),
        "review_session_status": "R53_PURGE_DISPOSAL_RECEIPT_VERIFIED_BODYFREE" if ready else "R53_PURGE_DISPOSAL_RECEIPT_BLOCKED",
        "purge_disposal_receipt_status": status,
        "purge_disposal_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "required_purge_target_refs": list(P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS),
        "purge_evidence_row_schema_version": P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_SCHEMA_VERSION,
        "purge_evidence_row_required_field_refs": list(P7_R51_PURGE_EVIDENCE_ROW_BODYFREE_REQUIRED_FIELD_REFS),
        "purge_evidence_rows": purge_rows if ready else purge_rows,
        "purge_evidence_row_count": len(purge_rows),
        "purge_target_count": _safe_non_negative_int_r53(r51_r14.get("purge_target_count")),
        "verified_purge_target_count": _safe_non_negative_int_r53(r51_r14.get("verified_purge_target_count")),
        "missing_purge_target_refs": dedupe_identifiers(r51_r14.get("missing_purge_target_refs") or [], limit=20, max_length=160),
        "failed_purge_target_refs": dedupe_identifiers(r51_r14.get("failed_purge_target_refs") or [], limit=20, max_length=160),
        "not_verified_purge_target_refs": dedupe_identifiers(r51_r14.get("not_verified_purge_target_refs") or [], limit=20, max_length=160),
        "deleted_file_count": _safe_non_negative_int_r53(r51_r15.get("deleted_file_count")) if ready else _safe_non_negative_int_r53(r51_r14.get("deleted_file_count")),
        "purge_started_at_ref": clean_identifier(r51_r15.get("purge_started_at_ref"), default="r53_local_only_purge_started_at_local_controller", max_length=160),
        "purge_completed_at_ref": clean_identifier(r51_r15.get("purge_completed_at_ref"), default="r53_local_only_purge_completed_at_local_controller", max_length=160),
        "disposal_receipt_schema_version": P7_R51_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
        "disposal_receipt_required_field_refs": list(P7_R51_DISPOSAL_RECEIPT_BODYFREE_REQUIRED_FIELD_REFS),
        "disposal_receipt": receipt,
        "disposal_status": clean_identifier(r51_r15.get("disposal_status"), default="DISPOSAL_FAILED", max_length=160),
        "disposal_verified": bool(ready and r51_r15.get("disposal_verified") is True),
        "disposal_failed": not ready,
        "disposal_receipt_missing": bool(not r51_r15.get("disposal_receipt")),
        "summary_finalize_allowed": bool(ready and r51_r15.get("summary_finalize_allowed") is True),
        "body_removed": bool(ready and r51_r15.get("body_removed") is True),
        "reviewer_forms_removed": bool(ready and r51_r15.get("reviewer_forms_removed") is True),
        "reviewer_notes_removed": bool(ready and r51_r15.get("reviewer_notes_removed") is True),
        "body_full_packets_removed": bool(ready and r51_r14.get("body_full_packets_removed") is True),
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "receipt_contains_body_full_material": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "deleted_body_preview_included": False,
        "terminal_output_included": False,
        "local_file_delete_ops_executed_by_helper": False,
        "actual_disposal_run_here": bool(ready and r51_r15.get("actual_disposal_run_here") is True),
        "disposal_receipt_materialized_here": bool(ready and r51_r15.get("disposal_receipt_materialized_here") is True),
        "actual_disposal_receipt_materialized_here": bool(ready and r51_r15.get("actual_disposal_receipt_materialized_here") is True),
        "post_review_summary_materialized_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(ready and r51_r15.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(ready and r51_r15.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(ready and r51_r15.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(ready and r51_r15.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(ready and r51_r15.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(ready and r51_r15.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": False,
        "p5_actual_review_still_not_run": not ready,
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r15.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r15.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r15.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r15.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r15.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r15.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": r15.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r53_13_question_need_observation_row_normalization_built": r15.get("r53_13_question_need_observation_row_normalization_built") is True,
        "r53_14_rating_question_consistency_guard_built": r15.get("r53_14_rating_question_consistency_guard_built") is True,
        "r53_15_pause_abort_expiration_protocol_built": r15.get("r53_15_pause_abort_expiration_protocol_built") is True,
        "r53_16_purge_disposal_receipt_built": ready,
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "implemented_steps": list(P7_R53_R16_IMPLEMENTED_STEPS if ready else P7_R53_R15_IMPLEMENTED_STEPS if r15_ready_for_purge else P7_R53_R14_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R16_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R53_R15_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R16_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R16_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for key in P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS:
        material[key] = bool(material.get(key))
    # Reinstate R16-specific booleans after the false baseline.
    for key in P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS:
        if key in {"actual_disposal_run_here", "disposal_receipt_materialized_here", "actual_disposal_receipt_materialized_here"}:
            material[key] = bool(ready and r51_r15.get(key) is True)
        elif key in P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS:
            material[key] = bool(ready and r15.get(key) is True)
    material["post_review_summary_materialized_here"] = False
    material["actual_question_need_observation_summary_materialized_here"] = False
    assert_p7_r53_purge_disposal_receipt_bodyfree_contract(material)
    return material


def assert_p7_r53_purge_disposal_receipt_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R53_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS, source="p7_r53_r16_purge_disposal_receipt_bodyfree")
    ready = data.get("purge_disposal_receipt_status") == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY"
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        source="p7_r53_r16_purge_disposal_receipt_bodyfree",
        allowed_true_false_key_refs=P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("policy_section") != "R53-16_purge_disposal_receipt":
        raise ValueError("R53 R16 policy section changed")
    if data.get("purge_disposal_receipt_status") not in P7_R53_PURGE_DISPOSAL_RECEIPT_STATUS_REFS:
        raise ValueError("R53 R16 purge/disposal status changed")
    r51_r14 = safe_mapping(data.get("r51_r14_body_full_packet_reviewer_notes_purge_bodyfree"))
    r51_r15 = safe_mapping(data.get("r51_r15_disposal_receipt_builder_verifier_bodyfree"))
    assert_p7_r51_body_full_packet_reviewer_notes_purge_bodyfree_contract(
        r51_r14,
        allowed_true_false_key_refs=P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    )
    assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(
        r51_r15,
        allowed_true_false_key_refs=P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    )
    if data.get("r51_r14_purge_schema_version") != P7_R51_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE_SCHEMA_VERSION:
        raise ValueError("R53 R16 R51 R14 schema reference changed")
    if data.get("r51_r15_disposal_receipt_schema_version") != P7_R51_DISPOSAL_RECEIPT_BUILDER_VERIFIER_SCHEMA_VERSION:
        raise ValueError("R53 R16 R51 R15 schema reference changed")
    if data.get("r51_r14_purge_status") != r51_r14.get("purge_status"):
        raise ValueError("R53 R16 R51 R14 status mismatch")
    if data.get("r51_r15_disposal_receipt_verifier_status") != r51_r15.get("disposal_receipt_verifier_status"):
        raise ValueError("R53 R16 R51 R15 status mismatch")
    rows = data.get("purge_evidence_rows")
    if not isinstance(rows, list):
        raise ValueError("R53 R16 purge evidence rows must be a list")
    for row in rows:
        assert_p7_r51_purge_evidence_row_bodyfree_contract(safe_mapping(row))
    receipt = safe_mapping(data.get("disposal_receipt"))
    assert_p7_no_body_payload_or_contract_mutation(receipt, source="p7_r53_r16_disposal_receipt_bodyfree")
    if data.get("purge_evidence_row_count") != len(rows):
        raise ValueError("R53 R16 purge evidence row count mismatch")
    for false_key in (
        "local_packet_exported",
        "content_hash_of_body_stored",
        "receipt_contains_body_full_material",
        "local_absolute_path_included",
        "body_content_hash_included",
        "deleted_body_preview_included",
        "terminal_output_included",
        "local_file_delete_ops_executed_by_helper",
        "post_review_summary_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R16 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R16 open blockers must match execution blockers")
    if ready:
        for true_key in (
            "r15_ready_for_purge_disposal_receipt",
            "disposal_verified",
            "summary_finalize_allowed",
            "body_removed",
            "reviewer_forms_removed",
            "reviewer_notes_removed",
            "body_full_packets_removed",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "r53_16_purge_disposal_receipt_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R16 ready material must keep {true_key}=True")
        if data.get("execution_blocker_ids") != []:
            raise ValueError("R53 R16 ready material must not keep execution blockers")
        if data.get("next_required_step") != P7_R53_R16_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R16 ready material must point to R53-17")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R16_IMPLEMENTED_STEPS:
            raise ValueError("R53 R16 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R16_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R16 not-yet steps changed")
    else:
        for false_key in (
            "disposal_verified",
            "summary_finalize_allowed",
            "body_removed",
            "reviewer_forms_removed",
            "reviewer_notes_removed",
            "body_full_packets_removed",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "r53_16_purge_disposal_receipt_built",
        ):
            if data.get(false_key) is not False:
                raise ValueError(f"R53 R16 blocked material must keep {false_key}=False")
        if data.get("next_required_step") != P7_R53_R16_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R16 blocked material must point to R53-16 resolution")
        if not blockers:
            raise ValueError("R53 R16 blocked material must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r16_purge_disposal_receipt_bodyfree")
    return True


def build_p7_r53_body_free_post_review_summary_bodyfree(
    *,
    purge_disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    r16_purge_disposal_receipt_bodyfree: Mapping[str, Any] | None = None,
    rating_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    r11_rating_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    r12_readfeel_blocker_execution_blocker_ingestion_bodyfree: Mapping[str, Any] | None = None,
    question_need_observation_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    r13_question_need_observation_row_normalization_bodyfree: Mapping[str, Any] | None = None,
    rating_question_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    r14_rating_question_consistency_guard_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_body_free_post_review_summary_bodyfree",
) -> dict[str, Any]:
    """Build R53-17 body-free post-review summary counts/refs from finalized evidence."""

    if purge_disposal_receipt_bodyfree is not None and r16_purge_disposal_receipt_bodyfree is not None:
        raise ValueError("provide only one R53-16 purge/disposal receipt value")
    if rating_row_normalization_bodyfree is not None and r11_rating_row_normalization_bodyfree is not None:
        raise ValueError("provide only one R53-11 rating normalization value")
    if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None and r12_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None:
        raise ValueError("provide only one R53-12 blocker ingestion value")
    if question_need_observation_row_normalization_bodyfree is not None and r13_question_need_observation_row_normalization_bodyfree is not None:
        raise ValueError("provide only one R53-13 question observation normalization value")
    if rating_question_consistency_guard_bodyfree is not None and r14_rating_question_consistency_guard_bodyfree is not None:
        raise ValueError("provide only one R53-14 consistency guard value")

    r16 = safe_mapping(
        purge_disposal_receipt_bodyfree
        if purge_disposal_receipt_bodyfree is not None
        else r16_purge_disposal_receipt_bodyfree
        if r16_purge_disposal_receipt_bodyfree is not None
        else build_p7_r53_purge_disposal_receipt_bodyfree()
    )
    assert_p7_r53_purge_disposal_receipt_bodyfree_contract(r16)
    r16_ready = r16.get("purge_disposal_receipt_status") == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY" and not r16.get("execution_blocker_ids")

    r11 = safe_mapping(
        rating_row_normalization_bodyfree
        if rating_row_normalization_bodyfree is not None
        else r11_rating_row_normalization_bodyfree
        if r11_rating_row_normalization_bodyfree is not None
        else build_p7_r53_rating_row_normalization_bodyfree()
    )
    assert_p7_r53_rating_row_normalization_bodyfree_contract(r11)
    r12 = safe_mapping(
        readfeel_blocker_execution_blocker_ingestion_bodyfree
        if readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else r12_readfeel_blocker_execution_blocker_ingestion_bodyfree
        if r12_readfeel_blocker_execution_blocker_ingestion_bodyfree is not None
        else build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(rating_row_normalization_bodyfree=r11)
    )
    assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r12)
    r13 = safe_mapping(
        question_need_observation_row_normalization_bodyfree
        if question_need_observation_row_normalization_bodyfree is not None
        else r13_question_need_observation_row_normalization_bodyfree
        if r13_question_need_observation_row_normalization_bodyfree is not None
        else build_p7_r53_question_need_observation_row_normalization_bodyfree(
            readfeel_blocker_execution_blocker_ingestion_bodyfree=r12,
        )
    )
    assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(r13)
    r14 = safe_mapping(
        rating_question_consistency_guard_bodyfree
        if rating_question_consistency_guard_bodyfree is not None
        else r14_rating_question_consistency_guard_bodyfree
        if r14_rating_question_consistency_guard_bodyfree is not None
        else build_p7_r53_rating_question_consistency_guard_bodyfree(
            rating_row_normalization_bodyfree=r11,
            readfeel_blocker_execution_blocker_ingestion_bodyfree=r12,
            question_need_observation_row_normalization_bodyfree=r13,
        )
    )
    assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(r14)

    r51_r9 = safe_mapping(r11.get("r51_r9_rating_row_normalizer_bodyfree"))
    r51_r10 = safe_mapping(r12.get("r51_r10_readfeel_execution_blocker_ingestion_bodyfree"))
    r51_r11 = safe_mapping(r13.get("r51_r11_question_need_observation_row_normalizer_bodyfree"))
    r51_r12 = safe_mapping(r14.get("r51_r12_rating_question_observation_consistency_guard_bodyfree"))
    r51_r15 = safe_mapping(r16.get("r51_r15_disposal_receipt_builder_verifier_bodyfree"))
    r11_ready = r11.get("rating_row_normalizer_status") == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION" and not r11.get("execution_blocker_ids")
    r12_ready = r12.get("blocker_ingestion_status") == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION" and not r12.get("execution_blocker_ids")
    r13_ready = r13.get("question_observation_normalizer_status") == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD" and not r13.get("execution_blocker_ids")
    r14_ready = r14.get("rating_question_consistency_guard_status") == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL" and not r14.get("execution_blocker_ids")
    summary_inputs_ready = bool(r16_ready and r11_ready and r12_ready and r13_ready and r14_ready)
    # The adopted R51 R16 builder treats disposal_verified=True as a ready-summary-only flag.
    # When R53-17 is intentionally blocked by missing rating/question/guard material,
    # feed R51 a blocked disposal verifier while keeping the real R53-16 receipt on
    # the outer R53 material. This preserves the R53 evidence without misclaiming an
    # R51 ready summary.
    r51_r15_for_summary = r51_r15 if summary_inputs_ready else build_p7_r51_disposal_receipt_builder_verifier_bodyfree(
        material_id="p7_r53_blocked_r51_r15_for_r16_summary_gate_bodyfree",
    )
    r51_r16 = build_p7_r51_body_free_post_review_summary_builder_bodyfree(
        disposal_receipt_builder_verifier_bodyfree=r51_r15_for_summary,
        rating_row_normalizer_bodyfree=r51_r9,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r51_r10,
        question_need_observation_row_normalizer_bodyfree=r51_r11,
        rating_question_observation_consistency_guard_bodyfree=r51_r12,
        material_id="p7_r53_adopted_r51_r16_body_free_post_review_summary_builder_bodyfree",
    )
    summary_ready = r51_r16.get("post_review_summary_status") == "READY_FOR_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION" and not r51_r16.get("execution_blocker_ids") and summary_inputs_ready
    assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(
        r51_r16,
        allowed_true_false_key_refs=P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS if summary_ready else P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    )

    precheck_blockers: list[str] = []
    if not r16_ready:
        precheck_blockers.append("r53_disposal_not_verified_before_summary")
    if not r11_ready:
        precheck_blockers.append("r53_rating_rows_incomplete_for_summary")
    if not r12_ready:
        precheck_blockers.append("r53_blocker_rows_incomplete_for_summary")
    if not r13_ready:
        precheck_blockers.append("r53_question_observation_rows_incomplete_for_summary")
    if not r14_ready:
        precheck_blockers.append("r53_rating_question_consistency_guard_not_ready_for_summary")
    r51_blockers = dedupe_identifiers(r51_r16.get("execution_blocker_ids") or [], limit=60, max_length=140)
    blockers = [] if summary_ready else dedupe_identifiers(
        [*precheck_blockers, *_r53_map_r51_post_review_summary_blockers(r51_blockers or ["r51_post_review_summary_incomplete"])],
        limit=80,
        max_length=140,
    )
    reason_refs = ["r53_body_free_post_review_summary_counts_refs_materialized"] if summary_ready else _r53_prefixed_reason_refs(
        r51_r16.get("post_review_summary_reason_refs") or [],
        default="r53_post_review_summary_blocked",
        blocker_ids=blockers,
    )
    material = {
        "schema_version": P7_R53_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-17_body_free_post_review_summary",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_body_free_post_review_summary_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r16.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r16_purge_disposal_receipt_schema_version": P7_R53_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "r16_purge_disposal_receipt_material_ref": clean_identifier(r16.get("material_id"), default="p7_r53_purge_disposal_receipt_bodyfree", max_length=180),
        "r16_purge_disposal_receipt_status": clean_identifier(r16.get("purge_disposal_receipt_status"), default="BLOCKED_BY_DISPOSAL_RECEIPT_VERIFICATION", max_length=180),
        "r16_ready_for_post_review_summary": bool(r16_ready),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r16_post_review_summary_schema_version": P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION,
        "r51_r16_post_review_summary_material_ref": clean_identifier(r51_r16.get("material_id"), default="p7_r53_adopted_r51_r16_body_free_post_review_summary_builder_bodyfree", max_length=180),
        "r51_r16_body_free_post_review_summary_builder_bodyfree": r51_r16,
        "r51_r16_post_review_summary_status": clean_identifier(r51_r16.get("post_review_summary_status"), default="BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS", max_length=180),
        "r51_r16_next_required_step": clean_identifier(r51_r16.get("next_required_step"), default=P7_R51_R16_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r16_execution_blocker_ids": r51_blockers,
        "review_session_status": "R53_BODY_FREE_POST_REVIEW_SUMMARY_READY" if summary_ready else "R53_BODY_FREE_POST_REVIEW_SUMMARY_BLOCKED",
        "post_review_summary_status": "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION" if summary_ready else "BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS",
        "post_review_summary_reason_refs": reason_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "all_24_cases_reviewed": bool(summary_ready and r51_r16.get("all_24_cases_reviewed") is True),
        "rating_row_count": _safe_non_negative_int_r53(r51_r16.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r53(r51_r16.get("question_observation_row_count")),
        "open_execution_blocker_count": _safe_non_negative_int_r53(r51_r16.get("open_execution_blocker_count")),
        "open_readfeel_blocker_count": _safe_non_negative_int_r53(r51_r16.get("open_readfeel_blocker_count")),
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "verdict_counts": dict(safe_mapping(r51_r16.get("verdict_counts"))),
        "axis_score_averages": dict(safe_mapping(r51_r16.get("axis_score_averages"))),
        "axis_target_refs": dict(safe_mapping(r51_r16.get("axis_target_refs"))),
        "axis_target_met_refs": list(r51_r16.get("axis_target_met_refs") or []),
        "axis_target_missed_refs": list(r51_r16.get("axis_target_missed_refs") or []),
        "all_axis_targets_met": bool(summary_ready and r51_r16.get("all_axis_targets_met") is True),
        "readfeel_blocker_counts": dict(safe_mapping(r51_r16.get("readfeel_blocker_counts"))),
        "execution_blocker_counts": dict(safe_mapping(r51_r16.get("execution_blocker_counts"))),
        "question_need_primary_class_counts": dict(safe_mapping(r51_r16.get("question_need_primary_class_counts"))),
        "ambiguity_kind_counts": dict(safe_mapping(r51_r16.get("ambiguity_kind_counts"))),
        "one_question_fit_counts": dict(safe_mapping(r51_r16.get("one_question_fit_counts"))),
        "repair_required_counts": dict(safe_mapping(r51_r16.get("repair_required_counts"))),
        "red_count": _safe_non_negative_int_r53(r51_r16.get("red_count")),
        "repair_required_count": _safe_non_negative_int_r53(r51_r16.get("repair_required_count")),
        "yellow_count": _safe_non_negative_int_r53(r51_r16.get("yellow_count")),
        "pass_count": _safe_non_negative_int_r53(r51_r16.get("pass_count")),
        "critical_repair_blocker_count": _safe_non_negative_int_r53(r51_r16.get("critical_repair_blocker_count")),
        "repair_observation_count": _safe_non_negative_int_r53(r51_r16.get("repair_observation_count")),
        "disposal_verified": bool(summary_ready and r51_r16.get("disposal_verified") is True),
        "body_removed": bool(summary_ready and r51_r16.get("body_removed") is True),
        "reviewer_forms_removed": bool(summary_ready and r16.get("reviewer_forms_removed") is True),
        "reviewer_notes_removed": bool(summary_ready and r51_r16.get("reviewer_notes_removed") is True),
        "body_free_summary_contains_only_counts_and_refs": bool(summary_ready and r51_r16.get("body_free_summary_contains_only_counts_and_refs") is True),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
        "reviewer_free_text_included": False,
        "question_text_included": False,
        "draft_question_text_included": False,
        "local_absolute_path_included": False,
        "body_content_hash_included": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p5_confirmed_requirements_met_by_summary": bool(summary_ready and r51_r16.get("p5_confirmed_requirements_met_by_summary") is True),
        "p5_human_blind_qa_confirmed_candidate": False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p8_question_design_material_candidate": False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(summary_ready and r51_r16.get("actual_human_review_run_here") is True),
        "actual_manual_review_run_here": bool(summary_ready and r51_r16.get("actual_manual_review_run_here") is True),
        "actual_rating_rows_materialized_here": bool(summary_ready and r51_r16.get("actual_rating_rows_materialized_here") is True),
        "actual_blocker_rows_materialized_here": bool(summary_ready and r51_r16.get("actual_blocker_rows_materialized_here") is True),
        "actual_execution_blocker_rows_materialized_here": bool(summary_ready and r51_r16.get("actual_execution_blocker_rows_materialized_here") is True),
        "actual_question_need_observation_rows_materialized_here": bool(summary_ready and r51_r16.get("actual_question_need_observation_rows_materialized_here") is True),
        "actual_question_need_observation_summary_materialized_here": bool(summary_ready and r51_r16.get("actual_question_need_observation_summary_materialized_here") is True),
        "actual_disposal_run_here": bool(summary_ready and r51_r16.get("actual_disposal_run_here") is True),
        "disposal_receipt_materialized_here": bool(summary_ready and r51_r16.get("disposal_receipt_materialized_here") is True),
        "actual_disposal_receipt_materialized_here": bool(summary_ready and r51_r16.get("actual_disposal_receipt_materialized_here") is True),
        "post_review_summary_materialized_here": bool(summary_ready and r51_r16.get("post_review_summary_materialized_here") is True),
        "p5_actual_review_still_not_run": not summary_ready,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r16.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r16.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r16.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r16.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r16.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r16.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": r16.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r53_13_question_need_observation_row_normalization_built": r16.get("r53_13_question_need_observation_row_normalization_built") is True,
        "r53_14_rating_question_consistency_guard_built": r16.get("r53_14_rating_question_consistency_guard_built") is True,
        "r53_15_pause_abort_expiration_protocol_built": r16.get("r53_15_pause_abort_expiration_protocol_built") is True,
        "r53_16_purge_disposal_receipt_built": r16.get("r53_16_purge_disposal_receipt_built") is True,
        "r53_17_body_free_post_review_summary_built": summary_ready,
        "implemented_steps": list(P7_R53_R17_IMPLEMENTED_STEPS if summary_ready else P7_R53_R16_IMPLEMENTED_STEPS if r16_ready else P7_R53_R15_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R17_NOT_YET_IMPLEMENTED_STEPS if summary_ready else P7_R53_R16_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R17_NEXT_REQUIRED_STEP_REF if summary_ready else P7_R53_R17_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for key in P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS:
        material[key] = bool(material.get(key))
    for key in P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS:
        if key in P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS:
            material[key] = bool(summary_ready and r16.get(key) is True)
        if key in {"actual_question_need_observation_summary_materialized_here", "post_review_summary_materialized_here"}:
            material[key] = bool(summary_ready and r51_r16.get(key) is True)
    assert_p7_r53_body_free_post_review_summary_bodyfree_contract(material)
    return material


def assert_p7_r53_body_free_post_review_summary_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(data, required=P7_R53_BODY_FREE_POST_REVIEW_SUMMARY_REQUIRED_FIELD_REFS, source="p7_r53_r17_body_free_post_review_summary_bodyfree")
    ready = data.get("post_review_summary_status") == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION"
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        source="p7_r53_r17_body_free_post_review_summary_bodyfree",
        allowed_true_false_key_refs=P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS if ready else (),
    )
    if data.get("policy_section") != "R53-17_body_free_post_review_summary":
        raise ValueError("R53 R17 policy section changed")
    if data.get("post_review_summary_status") not in P7_R53_POST_REVIEW_SUMMARY_STATUS_REFS:
        raise ValueError("R53 R17 post-review summary status changed")
    r51_r16 = safe_mapping(data.get("r51_r16_body_free_post_review_summary_builder_bodyfree"))
    assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(
        r51_r16,
        allowed_true_false_key_refs=P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS if ready else P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    )
    if data.get("r51_r16_post_review_summary_schema_version") != P7_R51_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER_SCHEMA_VERSION:
        raise ValueError("R53 R17 R51 R16 schema reference changed")
    if data.get("r51_r16_post_review_summary_status") != r51_r16.get("post_review_summary_status"):
        raise ValueError("R53 R17 R51 R16 status mismatch")
    for false_key in (
        "raw_input_included",
        "returned_surface_included",
        "comment_text_included",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_absolute_path_included",
        "body_content_hash_included",
        "local_packet_exported",
        "content_hash_of_body_stored",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "hold004_close_allowed",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R17 must keep {false_key}=False")
    blockers = dedupe_identifiers(data.get("execution_blocker_ids") or [], limit=60, max_length=140)
    if data.get("open_execution_blocker_ids") != blockers:
        raise ValueError("R53 R17 open blockers must match execution blockers")
    if set(data.get("axis_score_averages") or {}) != set(data.get("axis_target_refs") or {}):
        raise ValueError("R53 R17 axis score averages and target refs must cover the same axes")
    if ready:
        for true_key in (
            "r16_ready_for_post_review_summary",
            "all_24_cases_reviewed",
            "disposal_verified",
            "body_removed",
            "reviewer_forms_removed",
            "reviewer_notes_removed",
            "body_free_summary_contains_only_counts_and_refs",
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "r53_16_purge_disposal_receipt_built",
            "r53_17_body_free_post_review_summary_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R17 ready summary must keep {true_key}=True")
        if data.get("rating_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R17 ready summary must have 24 rating rows")
        if data.get("question_observation_row_count") != P7_R51_REQUIRED_CASE_COUNT:
            raise ValueError("R53 R17 ready summary must have 24 question rows")
        if data.get("execution_blocker_ids") != []:
            raise ValueError("R53 R17 ready summary must not keep execution blockers")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R17_IMPLEMENTED_STEPS:
            raise ValueError("R53 R17 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R17_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R17 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R17_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R17 ready summary must point to R53-18")
    else:
        for false_key in (
            "post_review_summary_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "r53_17_body_free_post_review_summary_built",
            "p5_confirmed_requirements_met_by_summary",
        ):
            if data.get(false_key) is not False:
                raise ValueError(f"R53 R17 blocked summary must keep {false_key}=False")
        if data.get("next_required_step") != P7_R53_R17_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R17 blocked summary must point to R53-17 resolution")
        if not blockers:
            raise ValueError("R53 R17 blocked summary must keep blockers visible")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r17_body_free_post_review_summary_bodyfree")
    return True




# ---------------------------------------------------------------------------
# R53-18 / R53-19: P5 decision separation and P6 candidate handoff
# ---------------------------------------------------------------------------

P7_R53_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.p5_decision_candidate_separation.bodyfree.v1"
)
P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.p6_limited_human_readfeel_candidate_handoff.bodyfree.v1"
)

P7_R53_R18_CONFIRMED_NEXT_REQUIRED_STEP_REF: Final = "R53-19_p6_limited_human_readfeel_candidate_handoff"
P7_R53_R18_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF: Final = "return_to_P5_repair_before_R53-19_p6_candidate_handoff"
P7_R53_R18_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF: Final = "resolve_R53-18_inconclusive_before_P6_P8_candidate_handoff"
P7_R53_R19_NEXT_REQUIRED_STEP_REF: Final = "R53-20_p8_question_design_material_candidate_handoff"
P7_R53_R19_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-19_p6_candidate_handoff_before_R53-20_p8_material_handoff"
)

P7_R53_FUTURE_STEPS_AFTER_R19: Final[tuple[str, ...]] = tuple(
    step
    for step in P7_R53_FUTURE_STEPS_AFTER_R17
    if step
    not in {
        "R53-18_p5_decision_candidate_separation",
        "R53-19_p6_limited_human_readfeel_candidate_handoff",
    }
)
P7_R53_R18_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R17_IMPLEMENTED_STEPS,
    "R53-18_p5_decision_candidate_separation",
)
P7_R53_R18_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-19_p6_limited_human_readfeel_candidate_handoff",
    *P7_R53_FUTURE_STEPS_AFTER_R19,
)
P7_R53_R19_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R18_IMPLEMENTED_STEPS,
    "R53-19_p6_limited_human_readfeel_candidate_handoff",
)
P7_R53_R19_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = P7_R53_FUTURE_STEPS_AFTER_R19

P7_R53_P5_DECISION_STATUS_REFS: Final[tuple[str, ...]] = tuple(P7_R51_P5_DECISION_STATUS_REFS)
P7_R53_P6_CANDIDATE_HANDOFF_STATUS_REFS: Final[tuple[str, ...]] = tuple(P7_R51_P6_CANDIDATE_HANDOFF_STATUS_REFS)

P7_R53_R18_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS,
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
)
P7_R53_R19_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R53_R18_ALLOWED_TRUE_FALSE_KEY_REFS,
    "p6_limited_human_readfeel_candidate",
)

P7_R53_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r17_body_free_post_review_summary_schema_version",
    "r17_body_free_post_review_summary_material_ref",
    "r17_body_free_post_review_summary_status",
    "r17_ready_for_p5_decision_candidate_separation",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r17_p5_decision_schema_version",
    "r51_r17_p5_decision_material_ref",
    "r51_r17_p5_decision_bodyfree",
    "r51_r17_p5_decision_status",
    "r51_r17_next_required_step",
    "r51_r17_execution_blocker_ids",
    "review_session_status",
    "p5_decision_status",
    "p5_decision_reason_refs",
    "p5_decision_blocker_refs",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "open_execution_blocker_count",
    "open_readfeel_blocker_count",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "verdict_counts",
    "axis_score_averages",
    "axis_target_refs",
    "axis_target_met_refs",
    "axis_target_missed_refs",
    "all_axis_targets_met",
    "readfeel_blocker_counts",
    "execution_blocker_counts",
    "question_need_primary_class_counts",
    "repair_required_counts",
    "red_count",
    "repair_required_count",
    "yellow_count",
    "pass_count",
    "critical_repair_blocker_count",
    "repair_observation_count",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "p5_confirmed_candidate_requirements_met",
    "p5_repair_return_requirements_met",
    "p5_review_inconclusive_requirements_met",
    "p5_decision_candidate_only",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "hold004_close_allowed",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "p5_actual_review_still_not_run",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "r53_15_pause_abort_expiration_protocol_built",
    "r53_16_purge_disposal_receipt_built",
    "r53_17_body_free_post_review_summary_built",
    "r53_18_p5_decision_candidate_separation_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r18_p5_decision_candidate_separation_schema_version",
    "r18_p5_decision_candidate_separation_material_ref",
    "p5_decision_status",
    "r18_ready_for_p6_candidate_handoff",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r18_p6_candidate_handoff_schema_version",
    "r51_r18_p6_candidate_handoff_material_ref",
    "r51_r18_p6_candidate_handoff_bodyfree",
    "r51_r18_p6_candidate_handoff_status",
    "r51_r18_next_required_step",
    "r51_r18_execution_blocker_ids",
    "review_session_status",
    "p6_candidate_handoff_status",
    "p6_candidate_reason_refs",
    "p6_candidate_blocker_refs",
    "missing_requirement_refs",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "open_execution_blocker_count",
    "open_readfeel_blocker_count",
    "execution_blocker_ids",
    "open_execution_blocker_ids",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p5_decision_candidate_only",
    "p5_weakness_not_hidden_by_p6",
    "p5_repair_not_compensated_by_p6",
    "p6_limited_family_scope_only",
    "p6_candidate_uses_bodyfree_summary_only",
    "p6_limited_human_readfeel_start_candidate_requirements_met",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "disposal_verified",
    "body_removed",
    "reviewer_notes_removed",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "red_count",
    "repair_required_count",
    "yellow_count",
    "pass_count",
    "critical_repair_blocker_count",
    "repair_observation_count",
    "axis_target_missed_refs",
    "all_axis_targets_met",
    "readfeel_blocker_counts",
    "question_need_primary_class_counts",
    "p5_actual_review_still_not_run",
    "p5_human_blind_qa_confirmed",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "hold004_close_allowed",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_frozen",
    "r53_3_r51_r0_r1_current_snapshot_override_adopted",
    "r53_4_local_root_explicit_allow_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_created",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "r53_15_pause_abort_expiration_protocol_built",
    "r53_16_purge_disposal_receipt_built",
    "r53_17_body_free_post_review_summary_built",
    "r53_18_p5_decision_candidate_separation_built",
    "r53_19_p6_limited_human_readfeel_candidate_handoff_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def _r53_allowed_true_refs_from(data: Mapping[str, Any], refs: Sequence[str]) -> tuple[str, ...]:
    return tuple(ref for ref in refs if data.get(ref) is True)


def _r53_p5_decision_next_step(decision_status: str) -> str:
    if decision_status == "P5_CONFIRMED_CANDIDATE":
        return P7_R53_R18_CONFIRMED_NEXT_REQUIRED_STEP_REF
    if decision_status == "P5_REPAIR_RETURN_CANDIDATE":
        return P7_R53_R18_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF
    return P7_R53_R18_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF


def build_p7_r53_p5_decision_candidate_separation_bodyfree(
    *,
    body_free_post_review_summary_bodyfree: Mapping[str, Any] | None = None,
    r17_body_free_post_review_summary_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_p5_decision_candidate_separation_bodyfree",
) -> dict[str, Any]:
    """Build R53-18 body-free P5 confirmed/repair/inconclusive separation.

    R53 adopts the R51 R17 decision contract but keeps the result as a
    candidate-only material.  It never promotes P5 to final, starts P6/P8, or
    turns P5 weakness into a P6/P8 escape route.
    """

    if body_free_post_review_summary_bodyfree is not None and r17_body_free_post_review_summary_bodyfree is not None:
        raise ValueError("provide only one R53-17 post-review summary value")
    r17 = safe_mapping(
        body_free_post_review_summary_bodyfree
        if body_free_post_review_summary_bodyfree is not None
        else r17_body_free_post_review_summary_bodyfree
        if r17_body_free_post_review_summary_bodyfree is not None
        else build_p7_r53_body_free_post_review_summary_bodyfree()
    )
    assert_p7_r53_body_free_post_review_summary_bodyfree_contract(r17)

    r17_ready = r17.get("post_review_summary_status") == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION"
    r51_r16 = safe_mapping(r17.get("r51_r16_body_free_post_review_summary_builder_bodyfree"))
    assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(
        r51_r16,
        allowed_true_false_key_refs=P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS if r17_ready else P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    )
    r51_r17 = build_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        r16_body_free_post_review_summary_builder_bodyfree=r51_r16,
        material_id="p7_r53_adopted_r51_r17_p5_confirmed_repair_return_inconclusive_decision_bodyfree",
    )
    assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(
        r51_r17,
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p5_repair_return_candidate",
            "p5_review_inconclusive",
        ),
    )

    decision_status = clean_identifier(r51_r17.get("p5_decision_status"), default="P5_REVIEW_INCONCLUSIVE", max_length=120)
    r51_open_execution_blockers = dedupe_identifiers(r51_r17.get("execution_blocker_ids") or [], limit=60, max_length=140)
    blockers = _r53_map_r51_post_review_summary_blockers(r51_open_execution_blockers)
    material = {
        "schema_version": P7_R53_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-18_p5_decision_candidate_separation",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_p5_decision_candidate_separation_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r17.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r17_body_free_post_review_summary_schema_version": P7_R53_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION,
        "r17_body_free_post_review_summary_material_ref": clean_identifier(r17.get("material_id"), default="p7_r53_body_free_post_review_summary_bodyfree", max_length=180),
        "r17_body_free_post_review_summary_status": clean_identifier(r17.get("post_review_summary_status"), default="BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS", max_length=180),
        "r17_ready_for_p5_decision_candidate_separation": bool(r17_ready),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r17_p5_decision_schema_version": P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION,
        "r51_r17_p5_decision_material_ref": clean_identifier(r51_r17.get("material_id"), default="p7_r53_adopted_r51_r17_p5_confirmed_repair_return_inconclusive_decision_bodyfree", max_length=180),
        "r51_r17_p5_decision_bodyfree": r51_r17,
        "r51_r17_p5_decision_status": decision_status,
        "r51_r17_next_required_step": clean_identifier(r51_r17.get("next_required_step"), default=P7_R51_R17_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r17_execution_blocker_ids": dedupe_identifiers(r51_r17.get("execution_blocker_ids") or [], limit=60, max_length=140),
        "review_session_status": f"R53_{decision_status}_SEPARATED_BODYFREE",
        "p5_decision_status": decision_status,
        "p5_decision_reason_refs": list(r51_r17.get("p5_decision_reason_refs") or []),
        "p5_decision_blocker_refs": list(r51_r17.get("p5_decision_blocker_refs") or []),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int_r53(r51_r17.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r53(r51_r17.get("question_observation_row_count")),
        "open_execution_blocker_count": len(blockers),
        "open_readfeel_blocker_count": _safe_non_negative_int_r53(r51_r17.get("open_readfeel_blocker_count")),
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "verdict_counts": dict(safe_mapping(r51_r17.get("verdict_counts"))),
        "axis_score_averages": dict(safe_mapping(r51_r17.get("axis_score_averages"))),
        "axis_target_refs": dict(safe_mapping(r51_r17.get("axis_target_refs"))),
        "axis_target_met_refs": list(r51_r17.get("axis_target_met_refs") or []),
        "axis_target_missed_refs": list(r51_r17.get("axis_target_missed_refs") or []),
        "all_axis_targets_met": bool(r51_r17.get("all_axis_targets_met")),
        "readfeel_blocker_counts": dict(safe_mapping(r51_r17.get("readfeel_blocker_counts"))),
        "execution_blocker_counts": dict(safe_mapping(r51_r17.get("execution_blocker_counts"))),
        "question_need_primary_class_counts": dict(safe_mapping(r51_r17.get("question_need_primary_class_counts"))),
        "repair_required_counts": dict(safe_mapping(r51_r17.get("repair_required_counts"))),
        "red_count": _safe_non_negative_int_r53(r51_r17.get("red_count")),
        "repair_required_count": _safe_non_negative_int_r53(r51_r17.get("repair_required_count")),
        "yellow_count": _safe_non_negative_int_r53(r51_r17.get("yellow_count")),
        "pass_count": _safe_non_negative_int_r53(r51_r17.get("pass_count")),
        "critical_repair_blocker_count": _safe_non_negative_int_r53(r51_r17.get("critical_repair_blocker_count")),
        "repair_observation_count": _safe_non_negative_int_r53(r51_r17.get("repair_observation_count")),
        "disposal_verified": bool(r51_r17.get("disposal_verified")),
        "body_removed": bool(r51_r17.get("body_removed")),
        "reviewer_notes_removed": bool(r51_r17.get("reviewer_notes_removed")),
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "p5_confirmed_candidate_requirements_met": bool(r51_r17.get("p5_confirmed_candidate_requirements_met")),
        "p5_repair_return_requirements_met": bool(r51_r17.get("p5_repair_return_requirements_met")),
        "p5_review_inconclusive_requirements_met": bool(r51_r17.get("p5_review_inconclusive_requirements_met")),
        "p5_decision_candidate_only": True,
        "p5_human_blind_qa_confirmed": False,
        "p5_human_blind_qa_confirmed_candidate": decision_status == "P5_CONFIRMED_CANDIDATE",
        "p5_repair_return_candidate": decision_status == "P5_REPAIR_RETURN_CANDIDATE",
        "p5_review_inconclusive": decision_status == "P5_REVIEW_INCONCLUSIVE",
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_start_allowed_candidate": False,
        "p6_limited_human_readfeel_candidate": False,
        "p8_question_design_material_candidate": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(r51_r17.get("actual_human_review_run_here")),
        "actual_manual_review_run_here": bool(r51_r17.get("actual_manual_review_run_here")),
        "actual_rating_rows_materialized_here": bool(r51_r17.get("actual_rating_rows_materialized_here")),
        "actual_blocker_rows_materialized_here": bool(r51_r17.get("actual_blocker_rows_materialized_here")),
        "actual_execution_blocker_rows_materialized_here": bool(r51_r17.get("actual_execution_blocker_rows_materialized_here")),
        "actual_question_need_observation_rows_materialized_here": bool(r51_r17.get("actual_question_need_observation_rows_materialized_here")),
        "actual_question_need_observation_summary_materialized_here": bool(r51_r17.get("actual_question_need_observation_summary_materialized_here")),
        "actual_disposal_run_here": bool(r51_r17.get("actual_disposal_run_here")),
        "disposal_receipt_materialized_here": bool(r51_r17.get("disposal_receipt_materialized_here")),
        "actual_disposal_receipt_materialized_here": bool(r51_r17.get("actual_disposal_receipt_materialized_here")),
        "post_review_summary_materialized_here": bool(r51_r17.get("post_review_summary_materialized_here")),
        "p5_actual_review_still_not_run": bool(r51_r17.get("p5_actual_review_still_not_run")),
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r17.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r17.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r17.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r17.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r17.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r17.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": r17.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r53_13_question_need_observation_row_normalization_built": r17.get("r53_13_question_need_observation_row_normalization_built") is True,
        "r53_14_rating_question_consistency_guard_built": r17.get("r53_14_rating_question_consistency_guard_built") is True,
        "r53_15_pause_abort_expiration_protocol_built": r17.get("r53_15_pause_abort_expiration_protocol_built") is True,
        "r53_16_purge_disposal_receipt_built": r17.get("r53_16_purge_disposal_receipt_built") is True,
        "r53_17_body_free_post_review_summary_built": r17.get("r53_17_body_free_post_review_summary_built") is True,
        "r53_18_p5_decision_candidate_separation_built": True,
        "implemented_steps": list(P7_R53_R18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R18_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": _r53_p5_decision_next_step(decision_status),
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    # Re-apply fields that are allowed to become true after _false_flags().
    for key in (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "post_review_summary_materialized_here",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
    ):
        material[key] = bool(material.get(key) or r51_r17.get(key) is True)
    assert_p7_r53_p5_decision_candidate_separation_bodyfree_contract(material)
    return material


def assert_p7_r53_p5_decision_candidate_separation_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R53_P5_DECISION_CANDIDATE_SEPARATION_REQUIRED_FIELD_REFS,
        source="p7_r53_r18_p5_decision_candidate_separation_bodyfree",
    )
    allowed = _r53_allowed_true_refs_from(data, P7_R53_R18_ALLOWED_TRUE_FALSE_KEY_REFS)
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        source="p7_r53_r18_p5_decision_candidate_separation_bodyfree",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R53-18_p5_decision_candidate_separation":
        raise ValueError("R53 R18 policy section changed")
    if data.get("p5_decision_status") not in P7_R53_P5_DECISION_STATUS_REFS:
        raise ValueError("R53 R18 decision status changed")
    r51_r17 = safe_mapping(data.get("r51_r17_p5_decision_bodyfree"))
    assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(
        r51_r17,
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p5_repair_return_candidate",
            "p5_review_inconclusive",
        ),
    )
    if data.get("r51_r17_p5_decision_schema_version") != P7_R51_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION_SCHEMA_VERSION:
        raise ValueError("R53 R18 R51 R17 schema reference changed")
    if data.get("r51_r17_p5_decision_status") != r51_r17.get("p5_decision_status"):
        raise ValueError("R53 R18 R51 R17 status mismatch")
    if data.get("p5_decision_status") != data.get("r51_r17_p5_decision_status"):
        raise ValueError("R53 R18 decision status must match adopted R51 decision")
    if data.get("execution_blocker_ids") != data.get("open_execution_blocker_ids"):
        raise ValueError("R53 R18 execution blockers must remain open blockers")
    for false_key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p6_limited_human_readfeel_candidate",
        "p8_question_design_material_candidate",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "hold004_close_allowed",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "local_packet_exported",
        "content_hash_of_body_stored",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R18 must keep {false_key}=False")
    true_candidate_count = sum(
        1
        for key in ("p5_human_blind_qa_confirmed_candidate", "p5_repair_return_candidate", "p5_review_inconclusive")
        if data.get(key) is True
    )
    if true_candidate_count != 1:
        raise ValueError("R53 R18 must set exactly one P5 candidate/repair/inconclusive flag")
    status = data.get("p5_decision_status")
    if status == "P5_CONFIRMED_CANDIDATE":
        if data.get("p5_human_blind_qa_confirmed_candidate") is not True:
            raise ValueError("R53 R18 confirmed status must set confirmed candidate flag")
        if data.get("p5_confirmed_candidate_requirements_met") is not True:
            raise ValueError("R53 R18 confirmed candidate must meet requirements")
        if data.get("next_required_step") != P7_R53_R18_CONFIRMED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R18 confirmed candidate must point to R53-19")
    elif status == "P5_REPAIR_RETURN_CANDIDATE":
        if data.get("p5_repair_return_candidate") is not True:
            raise ValueError("R53 R18 repair status must set repair candidate flag")
        if data.get("p5_repair_return_requirements_met") is not True:
            raise ValueError("R53 R18 repair return must have repair requirements")
        if data.get("next_required_step") != P7_R53_R18_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R18 repair return must point back to P5 repair")
    else:
        if data.get("p5_review_inconclusive") is not True:
            raise ValueError("R53 R18 inconclusive status must set inconclusive flag")
        if data.get("p5_review_inconclusive_requirements_met") is not True:
            raise ValueError("R53 R18 inconclusive must have inconclusive requirements")
        if data.get("next_required_step") != P7_R53_R18_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R18 inconclusive must point to inconclusive resolution")
    if tuple(data.get("implemented_steps") or ()) != P7_R53_R18_IMPLEMENTED_STEPS:
        raise ValueError("R53 R18 implemented steps changed")
    if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R18_NOT_YET_IMPLEMENTED_STEPS:
        raise ValueError("R53 R18 not-yet steps changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r18_p5_decision_candidate_separation_bodyfree")
    return True


def build_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree(
    *,
    p5_decision_candidate_separation_bodyfree: Mapping[str, Any] | None = None,
    r18_p5_decision_candidate_separation_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build R53-19 body-free P6 limited human readfeel candidate handoff.

    This is a candidate handoff only.  It must not set P6 start allowed, P8
    start allowed, P7 complete, release allowed, or any API/DB/RN/runtime change.
    """

    if p5_decision_candidate_separation_bodyfree is not None and r18_p5_decision_candidate_separation_bodyfree is not None:
        raise ValueError("provide only one R53-18 P5 decision value")
    r18 = safe_mapping(
        p5_decision_candidate_separation_bodyfree
        if p5_decision_candidate_separation_bodyfree is not None
        else r18_p5_decision_candidate_separation_bodyfree
        if r18_p5_decision_candidate_separation_bodyfree is not None
        else build_p7_r53_p5_decision_candidate_separation_bodyfree()
    )
    assert_p7_r53_p5_decision_candidate_separation_bodyfree_contract(r18)

    r18_ready = r18.get("p5_decision_status") == "P5_CONFIRMED_CANDIDATE" and r18.get("p5_human_blind_qa_confirmed_candidate") is True
    r51_r17 = safe_mapping(r18.get("r51_r17_p5_decision_bodyfree"))
    assert_p7_r51_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(
        r51_r17,
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p5_repair_return_candidate",
            "p5_review_inconclusive",
        ),
    )
    r51_r18 = build_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        p5_confirmed_repair_return_inconclusive_decision_bodyfree=r51_r17,
        material_id="p7_r53_adopted_r51_r18_p6_limited_human_readfeel_candidate_handoff_bodyfree",
    )
    assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(
        r51_r18,
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p5_repair_return_candidate",
            "p5_review_inconclusive",
            "p6_limited_human_readfeel_start_allowed_candidate",
        ),
    )

    handoff_status = clean_identifier(r51_r18.get("p6_candidate_handoff_status"), default="P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION", max_length=180)
    p6_candidate = bool(handoff_status == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY" and r18_ready)
    r51_open_execution_blockers = dedupe_identifiers(r51_r18.get("execution_blocker_ids") or [], limit=60, max_length=140)
    blockers = _r53_map_r51_post_review_summary_blockers(r51_open_execution_blockers)
    material = {
        "schema_version": P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-19_p6_limited_human_readfeel_candidate_handoff",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r18.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r18_p5_decision_candidate_separation_schema_version": P7_R53_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION,
        "r18_p5_decision_candidate_separation_material_ref": clean_identifier(r18.get("material_id"), default="p7_r53_p5_decision_candidate_separation_bodyfree", max_length=180),
        "p5_decision_status": clean_identifier(r18.get("p5_decision_status"), default="P5_REVIEW_INCONCLUSIVE", max_length=120),
        "r18_ready_for_p6_candidate_handoff": bool(r18_ready),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r18_p6_candidate_handoff_schema_version": P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r51_r18_p6_candidate_handoff_material_ref": clean_identifier(r51_r18.get("material_id"), default="p7_r53_adopted_r51_r18_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "r51_r18_p6_candidate_handoff_bodyfree": r51_r18,
        "r51_r18_p6_candidate_handoff_status": handoff_status,
        "r51_r18_next_required_step": clean_identifier(r51_r18.get("next_required_step"), default=P7_R51_R18_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "r51_r18_execution_blocker_ids": dedupe_identifiers(r51_r18.get("execution_blocker_ids") or [], limit=60, max_length=140),
        "review_session_status": "R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY_BODYFREE" if p6_candidate else "R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BODYFREE",
        "p6_candidate_handoff_status": handoff_status if p6_candidate else "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION",
        "p6_candidate_reason_refs": list(r51_r18.get("p6_candidate_reason_refs") or []),
        "p6_candidate_blocker_refs": list(r51_r18.get("p6_candidate_blocker_refs") or []),
        "missing_requirement_refs": list(r51_r18.get("missing_requirement_refs") or []),
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int_r53(r51_r18.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r53(r51_r18.get("question_observation_row_count")),
        "open_execution_blocker_count": len(blockers),
        "open_readfeel_blocker_count": _safe_non_negative_int_r53(r51_r18.get("open_readfeel_blocker_count")),
        "execution_blocker_ids": blockers,
        "open_execution_blocker_ids": blockers,
        "p5_human_blind_qa_confirmed_candidate": bool(r51_r18.get("p5_human_blind_qa_confirmed_candidate")),
        "p5_repair_return_candidate": bool(r51_r18.get("p5_repair_return_candidate")),
        "p5_review_inconclusive": bool(r51_r18.get("p5_review_inconclusive")),
        "p5_decision_candidate_only": bool(r51_r18.get("p5_decision_candidate_only")),
        "p5_weakness_not_hidden_by_p6": bool(p6_candidate and r51_r18.get("p5_weakness_not_hidden_by_p6") is True),
        "p5_repair_not_compensated_by_p6": bool(p6_candidate and r51_r18.get("p5_repair_not_compensated_by_p6") is True),
        "p6_limited_family_scope_only": True,
        "p6_candidate_uses_bodyfree_summary_only": True,
        "p6_limited_human_readfeel_start_candidate_requirements_met": bool(p6_candidate and r51_r18.get("p6_limited_human_readfeel_start_candidate_requirements_met") is True),
        "p6_limited_human_readfeel_candidate": p6_candidate,
        "p6_limited_human_readfeel_start_allowed": False,
        "p6_limited_human_readfeel_start_allowed_candidate": p6_candidate,
        "p8_question_design_material_candidate": False,
        "disposal_verified": bool(r51_r18.get("disposal_verified")),
        "body_removed": bool(r51_r18.get("body_removed")),
        "reviewer_notes_removed": bool(r51_r18.get("reviewer_notes_removed")),
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "red_count": _safe_non_negative_int_r53(r51_r18.get("red_count")),
        "repair_required_count": _safe_non_negative_int_r53(r51_r18.get("repair_required_count")),
        "yellow_count": _safe_non_negative_int_r53(r51_r18.get("yellow_count")),
        "pass_count": _safe_non_negative_int_r53(r51_r18.get("pass_count")),
        "critical_repair_blocker_count": _safe_non_negative_int_r53(r51_r18.get("critical_repair_blocker_count")),
        "repair_observation_count": _safe_non_negative_int_r53(r51_r18.get("repair_observation_count")),
        "axis_target_missed_refs": list(r51_r18.get("axis_target_missed_refs") or []),
        "all_axis_targets_met": bool(r51_r18.get("all_axis_targets_met")),
        "readfeel_blocker_counts": dict(safe_mapping(r51_r18.get("readfeel_blocker_counts"))),
        "question_need_primary_class_counts": dict(safe_mapping(r51_r18.get("question_need_primary_class_counts"))),
        "p5_actual_review_still_not_run": bool(r51_r18.get("p5_actual_review_still_not_run")),
        "p5_human_blind_qa_confirmed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "actual_human_review_run_here": bool(r51_r18.get("actual_human_review_run_here")),
        "actual_manual_review_run_here": bool(r51_r18.get("actual_manual_review_run_here")),
        "actual_rating_rows_materialized_here": bool(r51_r18.get("actual_rating_rows_materialized_here")),
        "actual_blocker_rows_materialized_here": bool(r51_r18.get("actual_blocker_rows_materialized_here")),
        "actual_execution_blocker_rows_materialized_here": bool(r51_r18.get("actual_execution_blocker_rows_materialized_here")),
        "actual_question_need_observation_rows_materialized_here": bool(r51_r18.get("actual_question_need_observation_rows_materialized_here")),
        "actual_question_need_observation_summary_materialized_here": bool(r51_r18.get("actual_question_need_observation_summary_materialized_here")),
        "actual_disposal_run_here": bool(r51_r18.get("actual_disposal_run_here")),
        "disposal_receipt_materialized_here": bool(r51_r18.get("disposal_receipt_materialized_here")),
        "actual_disposal_receipt_materialized_here": bool(r51_r18.get("actual_disposal_receipt_materialized_here")),
        "post_review_summary_materialized_here": bool(r51_r18.get("post_review_summary_materialized_here")),
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_frozen": True,
        "r53_3_r51_r0_r1_current_snapshot_override_adopted": True,
        "r53_4_local_root_explicit_allow_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_created": True,
        "r53_6_24_case_manifest_freeze_built": r18.get("r53_6_24_case_manifest_freeze_built") is True,
        "r53_7_local_only_body_full_packet_generation_request_built": r18.get("r53_7_local_only_body_full_packet_generation_request_built") is True,
        "r53_8_packet_completeness_export_denylist_scan_built": r18.get("r53_8_packet_completeness_export_denylist_scan_built") is True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": r18.get("r53_9_reviewer_instruction_rating_form_freeze_built") is True,
        "r53_10_actual_human_review_result_capture_built": r18.get("r53_10_actual_human_review_result_capture_built") is True,
        "r53_11_rating_row_normalization_built": r18.get("r53_11_rating_row_normalization_built") is True,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": r18.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built") is True,
        "r53_13_question_need_observation_row_normalization_built": r18.get("r53_13_question_need_observation_row_normalization_built") is True,
        "r53_14_rating_question_consistency_guard_built": r18.get("r53_14_rating_question_consistency_guard_built") is True,
        "r53_15_pause_abort_expiration_protocol_built": r18.get("r53_15_pause_abort_expiration_protocol_built") is True,
        "r53_16_purge_disposal_receipt_built": r18.get("r53_16_purge_disposal_receipt_built") is True,
        "r53_17_body_free_post_review_summary_built": r18.get("r53_17_body_free_post_review_summary_built") is True,
        "r53_18_p5_decision_candidate_separation_built": r18.get("r53_18_p5_decision_candidate_separation_built") is True,
        "r53_19_p6_limited_human_readfeel_candidate_handoff_built": p6_candidate,
        "implemented_steps": list(P7_R53_R19_IMPLEMENTED_STEPS if p6_candidate else P7_R53_R18_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R19_NOT_YET_IMPLEMENTED_STEPS if p6_candidate else P7_R53_R18_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R19_NEXT_REQUIRED_STEP_REF if p6_candidate else P7_R53_R19_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
        **_false_flags(),
    }
    for key in (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "post_review_summary_materialized_here",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
        "p6_limited_human_readfeel_candidate",
    ):
        material[key] = bool(material.get(key) or r51_r18.get(key) is True)
    material["p6_limited_human_readfeel_candidate"] = p6_candidate
    material["p6_limited_human_readfeel_start_allowed_candidate"] = p6_candidate
    material["r53_19_p6_limited_human_readfeel_candidate_handoff_built"] = p6_candidate
    material["implemented_steps"] = list(P7_R53_R19_IMPLEMENTED_STEPS if p6_candidate else P7_R53_R18_IMPLEMENTED_STEPS)
    material["not_yet_implemented_steps"] = list(P7_R53_R19_NOT_YET_IMPLEMENTED_STEPS if p6_candidate else P7_R53_R18_NOT_YET_IMPLEMENTED_STEPS)
    material["next_required_step"] = P7_R53_R19_NEXT_REQUIRED_STEP_REF if p6_candidate else P7_R53_R19_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(material)
    return material


def assert_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS,
        source="p7_r53_r19_p6_limited_human_readfeel_candidate_handoff_bodyfree",
    )
    p6_candidate = data.get("p6_candidate_handoff_status") == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY"
    allowed = _r53_allowed_true_refs_from(data, P7_R53_R19_ALLOWED_TRUE_FALSE_KEY_REFS)
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        source="p7_r53_r19_p6_limited_human_readfeel_candidate_handoff_bodyfree",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R53-19_p6_limited_human_readfeel_candidate_handoff":
        raise ValueError("R53 R19 policy section changed")
    if data.get("p6_candidate_handoff_status") not in P7_R53_P6_CANDIDATE_HANDOFF_STATUS_REFS:
        raise ValueError("R53 R19 P6 candidate handoff status changed")
    r51_r18 = safe_mapping(data.get("r51_r18_p6_candidate_handoff_bodyfree"))
    assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(
        r51_r18,
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p5_repair_return_candidate",
            "p5_review_inconclusive",
            "p6_limited_human_readfeel_start_allowed_candidate",
        ),
    )
    if data.get("r51_r18_p6_candidate_handoff_schema_version") != P7_R51_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("R53 R19 R51 R18 schema reference changed")
    if data.get("r51_r18_p6_candidate_handoff_status") != r51_r18.get("p6_candidate_handoff_status"):
        raise ValueError("R53 R19 R51 R18 status mismatch")
    if data.get("execution_blocker_ids") != data.get("open_execution_blocker_ids"):
        raise ValueError("R53 R19 execution blockers must remain open blockers")
    for false_key in (
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p8_question_design_material_candidate",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "hold004_close_allowed",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "local_packet_exported",
        "content_hash_of_body_stored",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R19 must keep {false_key}=False")
    if p6_candidate:
        for true_key in (
            "r18_ready_for_p6_candidate_handoff",
            "p5_human_blind_qa_confirmed_candidate",
            "p5_decision_candidate_only",
            "p5_weakness_not_hidden_by_p6",
            "p5_repair_not_compensated_by_p6",
            "p6_limited_family_scope_only",
            "p6_candidate_uses_bodyfree_summary_only",
            "p6_limited_human_readfeel_start_candidate_requirements_met",
            "p6_limited_human_readfeel_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "disposal_verified",
            "body_removed",
            "reviewer_notes_removed",
            "all_axis_targets_met",
            "r53_19_p6_limited_human_readfeel_candidate_handoff_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R19 ready handoff must keep {true_key}=True")
        if data.get("p5_repair_return_candidate") is not False or data.get("p5_review_inconclusive") is not False:
            raise ValueError("R53 R19 ready handoff must not carry P5 repair/inconclusive")
        if data.get("missing_requirement_refs"):
            raise ValueError("R53 R19 ready handoff must not have missing requirements")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R19_IMPLEMENTED_STEPS:
            raise ValueError("R53 R19 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R19_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R19 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R19_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R19 ready handoff must point to R53-20")
    else:
        if data.get("p6_limited_human_readfeel_candidate") is not False:
            raise ValueError("R53 R19 blocked handoff must not set P6 candidate")
        if data.get("p6_limited_human_readfeel_start_allowed_candidate") is not False:
            raise ValueError("R53 R19 blocked handoff must not set P6 start candidate")
        if not data.get("missing_requirement_refs"):
            raise ValueError("R53 R19 blocked handoff must explain missing requirements")
        if data.get("next_required_step") != P7_R53_R19_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R19 blocked handoff must point to R53-19 resolution")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R18_IMPLEMENTED_STEPS:
            raise ValueError("R53 R19 blocked handoff must preserve R18 implemented steps")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r19_p6_limited_human_readfeel_candidate_handoff_bodyfree")
    return True

# ---------------------------------------------------------------------------
# R53-20 / R53-21: P8 material candidate and R52 re-intake handoff
# ---------------------------------------------------------------------------

P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.p8_question_design_material_candidate_handoff.bodyfree.v1"
)
P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_R52_REINTAKE_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.final_no_body_leak_no_question_text_no_touch_r52_reintake.bodyfree.v1"
)
P7_R53_R52_REINTAKE_HANDOFF_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p7_r53.r52_reintake_handoff.bodyfree.v1"
)

P7_R53_R20_NEXT_REQUIRED_STEP_REF: Final = (
    "R53-21_final_no_body_leak_no_question_text_no_touch_validation_and_R52_reintake_handoff"
)
P7_R53_R20_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-20_p8_question_design_material_candidate_handoff_before_R53-21_validation"
)
P7_R53_R21_NEXT_REQUIRED_STEP_REF: Final = (
    "R52_reintake_handoff_ready_without_auto_p6_p8_start_or_release"
)
P7_R53_R21_BLOCKED_NEXT_REQUIRED_STEP_REF: Final = (
    "resolve_R53-21_no_body_leak_no_question_text_no_touch_validation_before_R52_reintake"
)

P7_R53_R21_EXPECTED_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = (
    "services/ai_inference/emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization.py",
    "tests/test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r20_r21_20260621.py",
)
P7_R53_R21_ALLOWED_ACTUAL_TOUCHED_FILE_REFS: Final[tuple[str, ...]] = P7_R53_R21_EXPECTED_TOUCHED_FILE_REFS
P7_R53_R21_EXPLICIT_NO_TOUCH_FILE_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            *P7_R51_R20_EXPLICIT_NO_TOUCH_FILE_REFS,
            "services/ai_inference/api_emotion_submit.py",
            "services/ai_inference/emotion_submit_service.py",
            "services/ai_inference/emlis_ai_reply_service.py",
            "services/ai_inference/emlis_ai_public_feedback_meta.py",
            "services/ai_inference/emlis_ai_user_label_connection_material.py",
            "services/ai_inference/emlis_ai_user_label_connection_candidate.py",
            "services/ai_inference/emlis_ai_user_label_connection_gate.py",
            "services/ai_inference/emlis_ai_user_label_connection_surface.py",
            "services/ai_inference/emlis_ai_user_label_connection_public_meta.py",
            "services/ai_inference/emlis_ai_p7_r51_local_review_file_ops.py",
            "Cocolon/screens/InputScreen.js",
            "Cocolon/screens/input/useInputFeedbackModal.js",
            "Cocolon/screens/input/inputFeedbackModel.js",
            "Cocolon/screens/input/InputFeedbackReplyModal.js",
            "Cocolon/tests/rn-screen-contracts.test.js",
        )
    )
)
P7_R53_R21_EXPLICIT_NO_TOUCH_AREA_REFS: Final[tuple[str, ...]] = tuple(
    dict.fromkeys(
        (
            *P7_R51_R20_EXPLICIT_NO_TOUCH_AREA_REFS,
            "api_route",
            "db_schema_or_migration",
            "rn_visible_contract",
            "public_response_key",
            "runtime_flow",
            "p8_question_api_db_rn_response_key_trigger_logic_storage_schema",
            "body_full_packet_artifacts",
            "reviewer_notes_artifacts",
        )
    )
)

P7_R53_R20_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R19_IMPLEMENTED_STEPS,
    "R53-20_p8_question_design_material_candidate_handoff",
)
P7_R53_R20_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    "R53-21_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff",
)
P7_R53_R21_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = (
    *P7_R53_R20_IMPLEMENTED_STEPS,
    "R53-21_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff",
)
P7_R53_R21_NOT_YET_IMPLEMENTED_STEPS: Final[tuple[str, ...]] = ()

P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS: Final[tuple[str, ...]] = tuple(
    P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS
)
P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_STATUS_REFS: Final[tuple[str, ...]] = (
    "R53_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATED_AND_R52_REINTAKE_HANDOFF_READY",
    "BLOCKED_BY_R53_BODY_LEAK_QUESTION_TEXT_NO_TOUCH_OR_R52_REINTAKE_BOUNDARY",
)

P7_R53_R20_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = (
    *P7_R53_R19_ALLOWED_TRUE_FALSE_KEY_REFS,
    "p8_question_design_material_candidate",
)
P7_R53_R21_ALLOWED_TRUE_FALSE_KEY_REFS: Final[tuple[str, ...]] = P7_R53_R20_ALLOWED_TRUE_FALSE_KEY_REFS

P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r19_p6_candidate_handoff_schema_version",
    "r19_p6_candidate_handoff_material_ref",
    "r19_p6_candidate_handoff_status",
    "r19_ready_for_p8_material_candidate_handoff",
    "r17_body_free_post_review_summary_schema_version",
    "r17_body_free_post_review_summary_material_ref",
    "r17_body_free_post_review_summary_status",
    "r17_summary_provided_for_p8_counts",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "r51_r19_p8_question_design_material_candidate_handoff_schema_version",
    "r51_r19_p8_question_design_material_candidate_handoff_material_ref",
    "r51_r19_p8_question_design_material_candidate_handoff_bodyfree",
    "r51_r19_p8_question_design_material_candidate_status",
    "r51_r19_next_required_step",
    "review_session_status",
    "p8_question_design_material_candidate_status",
    "p8_question_design_material_candidate_reason_refs",
    "p8_question_design_material_candidate_blocker_refs",
    "missing_requirement_refs",
    "required_case_count",
    "rating_row_count",
    "question_observation_row_count",
    "question_need_primary_class_counts",
    "ambiguity_kind_counts",
    "one_question_fit_counts",
    "repair_required_counts",
    "plan_candidate_flag_counts",
    "question_observation_rows_complete",
    "body_free_question_observation_material_available",
    "question_text_absent",
    "draft_question_text_absent",
    "raw_input_absent",
    "returned_surface_absent",
    "reviewer_free_text_absent",
    "local_path_absent",
    "body_hash_absent",
    "repair_required_not_question_misclassified_as_p8_candidate",
    "p5_repair_return_material_mixed_into_p8_candidate",
    "p5_weakness_not_hidden_by_question_candidate",
    "question_implementation_not_started",
    "p8_question_design_material_candidate_requirements_met",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "hold004_close_allowed",
    "p8_question_implementation_spec_finalized_here",
    "question_trigger_logic_implemented_here",
    "api_db_rn_response_key_changed_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "local_packet_exported",
    "content_hash_of_body_stored",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "actual_disposal_run_here",
    "disposal_receipt_materialized_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "p5_actual_review_still_not_run",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_built",
    "r53_3_r51_r0_r1_current_snapshot_override_built",
    "r53_4_explicit_allow_local_root_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_built",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "r53_15_pause_abort_expiration_protocol_built",
    "r53_16_purge_disposal_receipt_built",
    "r53_17_body_free_post_review_summary_built",
    "r53_18_p5_decision_candidate_separation_built",
    "r53_19_p6_limited_human_readfeel_candidate_handoff_built",
    "r53_20_p8_question_design_material_candidate_handoff_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)

P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_R52_REINTAKE_REQUIRED_FIELD_REFS: Final[tuple[str, ...]] = (
    "schema_version",
    "phase",
    "step",
    "scope",
    "policy_kind",
    "policy_section",
    "current_phase",
    "material_id",
    "review_session_id",
    "source_mode",
    "git_connection_required",
    "git_checked",
    "r20_p8_question_design_material_candidate_handoff_schema_version",
    "r20_p8_question_design_material_candidate_handoff_material_ref",
    "r20_p8_question_design_material_candidate_status",
    "r20_ready_for_final_validation",
    "r51_r20_no_body_leak_no_question_text_no_touch_schema_version",
    "r51_r20_no_body_leak_no_question_text_no_touch_material_ref",
    "r51_r20_no_body_leak_no_question_text_no_touch_bodyfree",
    "r51_r20_boundary_validation_status",
    "r51_r20_next_required_step",
    "final_boundary_validation_status",
    "final_boundary_validation_reason_refs",
    "missing_requirement_refs",
    "r52_reintake_handoff_schema_version",
    "r52_reintake_handoff_material_ref",
    "r52_reintake_handoff_bodyfree",
    "r51_bodyfree_handoff_components",
    "current_received_snapshot_refs",
    "current_received_snapshot_ref_count",
    "body_free_material_refs_scanned",
    "body_free_material_count_scanned",
    "forbidden_body_key_refs",
    "forbidden_true_flag_refs",
    "detected_forbidden_body_key_paths",
    "detected_forbidden_true_flag_paths",
    "body_payload_key_scan_passed",
    "question_text_key_scan_passed",
    "draft_question_text_key_scan_passed",
    "reviewer_free_text_key_scan_passed",
    "local_path_key_scan_passed",
    "body_hash_key_scan_passed",
    "terminal_output_key_scan_passed",
    "forbidden_true_flag_scan_passed",
    "body_free_no_leak_scan_passed",
    "actual_touched_file_refs",
    "allowed_actual_touched_file_refs",
    "expected_touched_file_refs",
    "explicit_no_touch_file_refs",
    "explicit_no_touch_area_refs",
    "forbidden_actual_touched_file_refs",
    "not_allowed_actual_touched_file_refs",
    "actual_touched_file_refs_checked_here",
    "actual_touched_file_refs_verified_here",
    "actual_touched_file_refs_materialized_here",
    "forbidden_actual_touched_refs_detected_here",
    "allowed_refs_do_not_include_no_touch_refs",
    "expected_touched_refs_are_allowed",
    "no_touch_boundary_validated",
    "rn_no_touch_preserved",
    "api_no_touch_preserved",
    "db_no_touch_preserved",
    "runtime_no_touch_preserved",
    "public_response_no_touch_preserved",
    "p8_question_implementation_not_started",
    "question_text_absent",
    "draft_question_text_absent",
    "question_body_absent",
    "raw_input_absent",
    "returned_surface_absent",
    "reviewer_free_text_absent",
    "local_path_absent",
    "body_hash_absent",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "body_full_writer_created_here",
    "local_reviewer_payload_materialized_here",
    "actual_reviewer_notes_materialized_here",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
    "post_review_summary_materialized_here",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "actual_rating_rows_materialized_here",
    "actual_blocker_rows_materialized_here",
    "actual_execution_blocker_rows_materialized_here",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "p5_human_blind_qa_confirmed_candidate",
    "p5_repair_return_candidate",
    "p5_review_inconclusive",
    "p6_limited_human_readfeel_candidate",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p6_limited_human_readfeel_start_allowed",
    "p8_question_design_material_candidate",
    "p8_start_allowed",
    "p7_complete",
    "release_allowed",
    "hold004_close_allowed",
    "api_db_rn_response_key_changed_here",
    "question_trigger_logic_implemented_here",
    "p8_question_implementation_spec_finalized_here",
    "rn_contract_changed_here",
    "rn_production_files_touched_here",
    "rn_contract_test_files_touched_here",
    "rn_visible_contract_changed_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "emlis_reply_runtime_changed_here",
    "user_label_connection_runtime_changed_here",
    "runtime_changed_here",
    "release_material_changed_here",
    "public_response_top_level_key_added_here",
    "r53_0_scope_current_received_snapshot_refrozen",
    "r53_1_r51_r52_helper_source_delta_frozen",
    "r53_2_r49_timeout_validation_evidence_preflight_built",
    "r53_3_r51_r0_r1_current_snapshot_override_built",
    "r53_4_explicit_allow_local_root_purge_plan_preflight_built",
    "r53_5_actual_review_session_envelope_built",
    "r53_6_24_case_manifest_freeze_built",
    "r53_7_local_only_body_full_packet_generation_request_built",
    "r53_8_packet_completeness_export_denylist_scan_built",
    "r53_9_reviewer_instruction_rating_form_freeze_built",
    "r53_10_actual_human_review_result_capture_built",
    "r53_11_rating_row_normalization_built",
    "r53_12_readfeel_blocker_execution_blocker_ingestion_built",
    "r53_13_question_need_observation_row_normalization_built",
    "r53_14_rating_question_consistency_guard_built",
    "r53_15_pause_abort_expiration_protocol_built",
    "r53_16_purge_disposal_receipt_built",
    "r53_17_body_free_post_review_summary_built",
    "r53_18_p5_decision_candidate_separation_built",
    "r53_19_p6_limited_human_readfeel_candidate_handoff_built",
    "r53_20_p8_question_design_material_candidate_handoff_built",
    "r53_21_final_no_body_leak_no_question_text_no_touch_validation_built",
    "implemented_steps",
    "not_yet_implemented_steps",
    "first_next_work_ref",
    "next_required_step",
    "public_contract",
    "r53_public_no_touch_contract",
    "body_free_markers",
    "body_free",
    *P7_R53_R0_R1_FALSE_KEY_REFS,
)


def _r53_find_forbidden_key_paths(
    value: Any,
    *,
    forbidden_keys: Sequence[str],
    path: str = "material",
) -> list[str]:
    forbidden = set(forbidden_keys)
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in forbidden:
                paths.append(child_path)
            paths.extend(_r53_find_forbidden_key_paths(child, forbidden_keys=forbidden_keys, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_r53_find_forbidden_key_paths(child, forbidden_keys=forbidden_keys, path=f"{path}[{index}]"))
    return paths


def _r53_find_forbidden_true_flag_paths(
    value: Any,
    *,
    forbidden_flags: Sequence[str],
    path: str = "material",
) -> list[str]:
    forbidden = set(forbidden_flags)
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in forbidden and child is True:
                paths.append(child_path)
            paths.extend(_r53_find_forbidden_true_flag_paths(child, forbidden_flags=forbidden_flags, path=child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            paths.extend(_r53_find_forbidden_true_flag_paths(child, forbidden_flags=forbidden_flags, path=f"{path}[{index}]"))
    return paths


def _r53_bodyfree_material_refs(materials: Sequence[Mapping[str, Any]]) -> list[str]:
    refs = [clean_identifier(material.get("material_id"), default=f"r53_bodyfree_material_{index}", max_length=180) for index, material in enumerate(materials)]
    return dedupe_identifiers(refs, limit=120, max_length=180)


def _r53_no_touch_scan(actual_touched_file_refs: Sequence[Any] | Any | None) -> tuple[list[str], list[str], list[str]]:
    touched = dedupe_identifiers(
        actual_touched_file_refs if actual_touched_file_refs is not None else P7_R53_R21_EXPECTED_TOUCHED_FILE_REFS,
        limit=240,
        max_length=260,
    )
    allowed = set(P7_R53_R21_ALLOWED_ACTUAL_TOUCHED_FILE_REFS)
    no_touch = set(P7_R53_R21_EXPLICIT_NO_TOUCH_FILE_REFS)
    touched_set = set(touched)
    forbidden_touched = sorted(touched_set & no_touch)
    not_allowed = sorted(touched_set - allowed)
    return touched, forbidden_touched, not_allowed


def _r53_r20_r51_allowed_true_refs_from_p8(data: Mapping[str, Any]) -> tuple[str, ...]:
    refs = (
        "actual_human_review_run_here",
        "actual_manual_review_run_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "disposal_receipt_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "post_review_summary_materialized_here",
        "p5_human_blind_qa_confirmed_candidate",
        "p5_repair_return_candidate",
        "p5_review_inconclusive",
        "p6_limited_human_readfeel_start_allowed_candidate",
        "p8_question_design_material_candidate",
    )
    return tuple(ref for ref in refs if data.get(ref) is True)


def _r53_r21_reintake_handoff_bodyfree(
    *,
    r20: Mapping[str, Any],
    ready: bool,
) -> dict[str, Any]:
    return {
        "schema_version": P7_R53_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "material_id": "p7_r53_r52_reintake_handoff_bodyfree",
        "review_session_id": clean_identifier(r20.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "r53_current_snapshot_refrozen": True,
        "r51_actual_review_evidence_complete": ready,
        "r51_bodyfree_handoff_components": [
            "post_review_summary",
            "p5_confirmed_repair_return_inconclusive_decision",
            "p6_limited_human_readfeel_candidate_handoff",
            "p8_question_design_material_candidate_handoff",
            "no_body_leak_no_question_text_no_touch_boundary_validation",
        ],
        "p5_human_blind_qa_confirmed_candidate": bool(r20.get("p5_human_blind_qa_confirmed_candidate")) if ready else False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_start_allowed_candidate": bool(r20.get("p6_limited_human_readfeel_start_allowed_candidate")) if ready else False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": bool(r20.get("p8_question_design_material_candidate")) if ready else False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "api_db_rn_response_key_changed_here": False,
        "runtime_changed_here": False,
        "question_implementation_started_here": False,
        "body_free": True,
    }


def build_p7_r53_p8_question_design_material_candidate_handoff_bodyfree(
    *,
    p6_limited_human_readfeel_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    r19_p6_limited_human_readfeel_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    body_free_post_review_summary_bodyfree: Mapping[str, Any] | None = None,
    r17_body_free_post_review_summary_bodyfree: Mapping[str, Any] | None = None,
    material_id: Any = "p7_r53_p8_question_design_material_candidate_handoff_bodyfree",
) -> dict[str, Any]:
    """Build R53-20 body-free P8 question design material candidate handoff.

    This only passes counts and refs collected during P7/P8 Bridge observation.
    It never starts P8, writes question text, finalizes question specs, or uses
    repair-required P5 weakness as question material.
    """

    if p6_limited_human_readfeel_candidate_handoff_bodyfree is not None and r19_p6_limited_human_readfeel_candidate_handoff_bodyfree is not None:
        raise ValueError("provide only one R53-19 P6 handoff value")
    if body_free_post_review_summary_bodyfree is not None and r17_body_free_post_review_summary_bodyfree is not None:
        raise ValueError("provide only one R53-17 post-review summary value")
    r19 = safe_mapping(
        p6_limited_human_readfeel_candidate_handoff_bodyfree
        if p6_limited_human_readfeel_candidate_handoff_bodyfree is not None
        else r19_p6_limited_human_readfeel_candidate_handoff_bodyfree
        if r19_p6_limited_human_readfeel_candidate_handoff_bodyfree is not None
        else build_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree()
    )
    assert_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(r19)

    r17 = safe_mapping(
        body_free_post_review_summary_bodyfree
        if body_free_post_review_summary_bodyfree is not None
        else r17_body_free_post_review_summary_bodyfree
        if r17_body_free_post_review_summary_bodyfree is not None
        else {}
    )
    r17_provided = bool(r17)
    if r17_provided:
        assert_p7_r53_body_free_post_review_summary_bodyfree_contract(r17)

    r51_r18 = safe_mapping(r19.get("r51_r18_p6_candidate_handoff_bodyfree"))
    assert_p7_r51_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract(
        r51_r18,
        allowed_true_false_key_refs=(
            "actual_human_review_run_here",
            "actual_manual_review_run_here",
            "actual_rating_rows_materialized_here",
            "actual_blocker_rows_materialized_here",
            "actual_execution_blocker_rows_materialized_here",
            "actual_question_need_observation_rows_materialized_here",
            "actual_question_need_observation_summary_materialized_here",
            "actual_disposal_run_here",
            "disposal_receipt_materialized_here",
            "actual_disposal_receipt_materialized_here",
            "post_review_summary_materialized_here",
            "p5_human_blind_qa_confirmed_candidate",
            "p5_repair_return_candidate",
            "p5_review_inconclusive",
            "p6_limited_human_readfeel_start_allowed_candidate",
        ),
    )
    r51_r16 = safe_mapping(r17.get("r51_r16_body_free_post_review_summary_builder_bodyfree")) if r17_provided else {}
    if r51_r16:
        assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(
            r51_r16,
            allowed_true_false_key_refs=P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS,
        )
    r51_r19 = build_p7_r51_p8_question_design_material_candidate_handoff_bodyfree(
        r18_p6_limited_human_readfeel_candidate_handoff_bodyfree=r51_r18,
        r16_body_free_post_review_summary_builder_bodyfree=r51_r16 or None,
        material_id="p7_r53_adopted_r51_r19_p8_question_design_material_candidate_handoff_bodyfree",
    )
    assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(
        r51_r19,
        allowed_true_false_key_refs=_r53_r20_r51_allowed_true_refs_from_p8(r51_r19),
    )

    p8_candidate = r51_r19.get("p8_question_design_material_candidate_status") == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    missing_refs = dedupe_identifiers(r51_r19.get("missing_requirement_refs") or [], limit=60, max_length=180)
    if not r17_provided and "bodyfree_question_observation_counts_required" not in missing_refs:
        missing_refs = dedupe_identifiers([*missing_refs, "r53_17_post_review_summary_required_for_bodyfree_question_counts"], limit=60, max_length=180)
        p8_candidate = False
    status = "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY" if p8_candidate else "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS"
    reason_refs = ["p8_question_design_material_candidate_bodyfree_requirements_met"] if p8_candidate else ["p8_question_design_material_candidate_blocked_until_p5_and_bodyfree_material_are_clean"]
    material = {
        **_false_flags(),
        "schema_version": P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-20_p8_question_design_material_candidate_handoff",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r19.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r19_p6_candidate_handoff_schema_version": P7_R53_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r19_p6_candidate_handoff_material_ref": clean_identifier(r19.get("material_id"), default="p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree", max_length=180),
        "r19_p6_candidate_handoff_status": clean_identifier(r19.get("p6_candidate_handoff_status"), default="P6_LIMITED_HUMAN_READFEEL_CANDIDATE_BLOCKED_BY_P5_DECISION", max_length=160),
        "r19_ready_for_p8_material_candidate_handoff": r19.get("p6_candidate_handoff_status") == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_READY",
        "r17_body_free_post_review_summary_schema_version": P7_R53_BODY_FREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION if r17_provided else "not_provided_bodyfree_summary_required_for_ready_material",
        "r17_body_free_post_review_summary_material_ref": clean_identifier(r17.get("material_id"), default="missing_r53_17_body_free_post_review_summary", max_length=180),
        "r17_body_free_post_review_summary_status": clean_identifier(r17.get("post_review_summary_status"), default="BLOCKED_BY_POST_REVIEW_SUMMARY_REQUIREMENTS", max_length=180),
        "r17_summary_provided_for_p8_counts": r17_provided,
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "r51_r19_p8_question_design_material_candidate_handoff_schema_version": P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r51_r19_p8_question_design_material_candidate_handoff_material_ref": clean_identifier(r51_r19.get("material_id"), default="p7_r53_adopted_r51_r19_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "r51_r19_p8_question_design_material_candidate_handoff_bodyfree": r51_r19,
        "r51_r19_p8_question_design_material_candidate_status": clean_identifier(r51_r19.get("p8_question_design_material_candidate_status"), default="P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS", max_length=160),
        "r51_r19_next_required_step": clean_identifier(r51_r19.get("next_required_step"), default=P7_R51_R19_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "review_session_status": "R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY_BODYFREE" if p8_candidate else "PRECHECK_BLOCKED",
        "p8_question_design_material_candidate_status": status,
        "p8_question_design_material_candidate_reason_refs": reason_refs,
        "p8_question_design_material_candidate_blocker_refs": [] if p8_candidate else missing_refs,
        "missing_requirement_refs": [] if p8_candidate else missing_refs,
        "required_case_count": P7_R51_REQUIRED_CASE_COUNT,
        "rating_row_count": _safe_non_negative_int_r53(r51_r19.get("rating_row_count")),
        "question_observation_row_count": _safe_non_negative_int_r53(r51_r19.get("question_observation_row_count")),
        "question_need_primary_class_counts": dict(safe_mapping(r51_r19.get("question_need_primary_class_counts"))),
        "ambiguity_kind_counts": dict(safe_mapping(r51_r19.get("ambiguity_kind_counts"))),
        "one_question_fit_counts": dict(safe_mapping(r51_r19.get("one_question_fit_counts"))),
        "repair_required_counts": dict(safe_mapping(r51_r19.get("repair_required_counts"))),
        "plan_candidate_flag_counts": dict(safe_mapping(r51_r19.get("plan_candidate_flag_counts"))),
        "question_observation_rows_complete": bool(r51_r19.get("question_observation_rows_complete")),
        "body_free_question_observation_material_available": bool(r51_r19.get("body_free_question_observation_material_available")) and r17_provided,
        "question_text_absent": True,
        "draft_question_text_absent": True,
        "raw_input_absent": True,
        "returned_surface_absent": True,
        "reviewer_free_text_absent": True,
        "local_path_absent": True,
        "body_hash_absent": True,
        "repair_required_not_question_misclassified_as_p8_candidate": False,
        "p5_repair_return_material_mixed_into_p8_candidate": False,
        "p5_weakness_not_hidden_by_question_candidate": True,
        "question_implementation_not_started": True,
        "p8_question_design_material_candidate_requirements_met": p8_candidate,
        "p5_human_blind_qa_confirmed_candidate": bool(r51_r19.get("p5_human_blind_qa_confirmed_candidate")) if p8_candidate else bool(r19.get("p5_human_blind_qa_confirmed_candidate")),
        "p5_repair_return_candidate": bool(r51_r19.get("p5_repair_return_candidate")),
        "p5_review_inconclusive": bool(r51_r19.get("p5_review_inconclusive")),
        "p6_limited_human_readfeel_candidate": bool(r19.get("p6_limited_human_readfeel_candidate")) if p8_candidate else False,
        "p6_limited_human_readfeel_start_allowed_candidate": bool(r51_r19.get("p6_limited_human_readfeel_start_allowed_candidate")) if p8_candidate else False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": p8_candidate,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "p8_question_implementation_spec_finalized_here": False,
        "question_trigger_logic_implemented_here": False,
        "api_db_rn_response_key_changed_here": False,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "actual_human_review_run_here": bool(r51_r19.get("actual_human_review_run_here")),
        "actual_manual_review_run_here": bool(r51_r19.get("actual_manual_review_run_here")),
        "actual_rating_rows_materialized_here": bool(r51_r19.get("actual_rating_rows_materialized_here")),
        "actual_blocker_rows_materialized_here": bool(r51_r19.get("actual_blocker_rows_materialized_here")),
        "actual_execution_blocker_rows_materialized_here": bool(r51_r19.get("actual_execution_blocker_rows_materialized_here")),
        "actual_question_need_observation_rows_materialized_here": bool(r51_r19.get("actual_question_need_observation_rows_materialized_here")),
        "actual_question_need_observation_summary_materialized_here": bool(r51_r19.get("actual_question_need_observation_summary_materialized_here")),
        "actual_disposal_run_here": bool(r51_r19.get("actual_disposal_run_here")),
        "disposal_receipt_materialized_here": bool(r51_r19.get("disposal_receipt_materialized_here")),
        "actual_disposal_receipt_materialized_here": bool(r51_r19.get("actual_disposal_receipt_materialized_here")),
        "post_review_summary_materialized_here": bool(r51_r19.get("post_review_summary_materialized_here")),
        "p5_actual_review_still_not_run": bool(r51_r19.get("p5_actual_review_still_not_run")),
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_built": True,
        "r53_3_r51_r0_r1_current_snapshot_override_built": True,
        "r53_4_explicit_allow_local_root_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_built": True,
        "r53_6_24_case_manifest_freeze_built": True,
        "r53_7_local_only_body_full_packet_generation_request_built": True,
        "r53_8_packet_completeness_export_denylist_scan_built": True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": bool(r19.get("r53_9_reviewer_instruction_rating_form_freeze_built")),
        "r53_10_actual_human_review_result_capture_built": bool(r19.get("r53_10_actual_human_review_result_capture_built")),
        "r53_11_rating_row_normalization_built": bool(r19.get("r53_11_rating_row_normalization_built")),
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": bool(r19.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built")),
        "r53_13_question_need_observation_row_normalization_built": bool(r19.get("r53_13_question_need_observation_row_normalization_built")),
        "r53_14_rating_question_consistency_guard_built": bool(r19.get("r53_14_rating_question_consistency_guard_built")),
        "r53_15_pause_abort_expiration_protocol_built": bool(r19.get("r53_15_pause_abort_expiration_protocol_built")),
        "r53_16_purge_disposal_receipt_built": bool(r19.get("r53_16_purge_disposal_receipt_built")),
        "r53_17_body_free_post_review_summary_built": bool(r19.get("r53_17_body_free_post_review_summary_built")),
        "r53_18_p5_decision_candidate_separation_built": bool(r19.get("r53_18_p5_decision_candidate_separation_built")),
        "r53_19_p6_limited_human_readfeel_candidate_handoff_built": bool(r19.get("r53_19_p6_limited_human_readfeel_candidate_handoff_built")),
        "r53_20_p8_question_design_material_candidate_handoff_built": p8_candidate,
        "implemented_steps": list(P7_R53_R20_IMPLEMENTED_STEPS if p8_candidate else P7_R53_R19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R20_NOT_YET_IMPLEMENTED_STEPS if p8_candidate else P7_R53_R19_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R20_NEXT_REQUIRED_STEP_REF if p8_candidate else P7_R53_R20_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_p8_question_design_material_candidate_handoff_bodyfree_contract(material)
    return material


def assert_p7_r53_p8_question_design_material_candidate_handoff_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS,
        source="p7_r53_r20_p8_question_design_material_candidate_handoff_bodyfree",
    )
    p8_candidate = data.get("p8_question_design_material_candidate_status") == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    allowed = _r53_allowed_true_refs_from(data, P7_R53_R20_ALLOWED_TRUE_FALSE_KEY_REFS)
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        source="p7_r53_r20_p8_question_design_material_candidate_handoff_bodyfree",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R53-20_p8_question_design_material_candidate_handoff":
        raise ValueError("R53 R20 policy section changed")
    if data.get("p8_question_design_material_candidate_status") not in P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_STATUS_REFS:
        raise ValueError("R53 R20 P8 material candidate status changed")
    r51_r19 = safe_mapping(data.get("r51_r19_p8_question_design_material_candidate_handoff_bodyfree"))
    assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(
        r51_r19,
        allowed_true_false_key_refs=_r53_r20_r51_allowed_true_refs_from_p8(r51_r19),
    )
    if data.get("r51_r19_p8_question_design_material_candidate_handoff_schema_version") != P7_R51_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("R53 R20 R51 R19 schema reference changed")
    if data.get("r51_r19_p8_question_design_material_candidate_status") != r51_r19.get("p8_question_design_material_candidate_status"):
        raise ValueError("R53 R20 R51 R19 status mismatch")
    for true_key in (
        "question_text_absent",
        "draft_question_text_absent",
        "raw_input_absent",
        "returned_surface_absent",
        "reviewer_free_text_absent",
        "local_path_absent",
        "body_hash_absent",
        "question_implementation_not_started",
        "p5_weakness_not_hidden_by_question_candidate",
    ):
        if data.get(true_key) is not True:
            raise ValueError(f"R53 R20 must keep {true_key}=True")
    for false_key in (
        "repair_required_not_question_misclassified_as_p8_candidate",
        "p5_repair_return_material_mixed_into_p8_candidate",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "hold004_close_allowed",
        "p8_question_implementation_spec_finalized_here",
        "question_trigger_logic_implemented_here",
        "api_db_rn_response_key_changed_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "local_packet_exported",
        "content_hash_of_body_stored",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R20 must keep {false_key}=False")
    if p8_candidate:
        for true_key in (
            "r19_ready_for_p8_material_candidate_handoff",
            "r17_summary_provided_for_p8_counts",
            "p5_human_blind_qa_confirmed_candidate",
            "p6_limited_human_readfeel_candidate",
            "p6_limited_human_readfeel_start_allowed_candidate",
            "question_observation_rows_complete",
            "body_free_question_observation_material_available",
            "p8_question_design_material_candidate_requirements_met",
            "p8_question_design_material_candidate",
            "r53_20_p8_question_design_material_candidate_handoff_built",
        ):
            if data.get(true_key) is not True:
                raise ValueError(f"R53 R20 ready material must keep {true_key}=True")
        if data.get("p5_repair_return_candidate") is not False or data.get("p5_review_inconclusive") is not False:
            raise ValueError("R53 R20 ready material must not carry P5 repair/inconclusive")
        if data.get("missing_requirement_refs"):
            raise ValueError("R53 R20 ready material must not have missing requirements")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R20_IMPLEMENTED_STEPS:
            raise ValueError("R53 R20 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R20_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R20 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R20_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R20 ready material must point to R53-21")
    else:
        if data.get("p8_question_design_material_candidate") is not False:
            raise ValueError("R53 R20 blocked material must not set P8 material candidate")
        if not data.get("missing_requirement_refs"):
            raise ValueError("R53 R20 blocked material must explain missing requirements")
        if data.get("next_required_step") != P7_R53_R20_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R20 blocked material must point to R53-20 resolution")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R19_IMPLEMENTED_STEPS:
            raise ValueError("R53 R20 blocked material must preserve R19 implemented steps")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r20_p8_question_design_material_candidate_handoff_bodyfree")
    return True


def build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree(
    *,
    p8_question_design_material_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    r20_p8_question_design_material_candidate_handoff_bodyfree: Mapping[str, Any] | None = None,
    additional_body_free_materials: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    actual_touched_file_refs: Sequence[Any] | Any | None = None,
    material_id: Any = "p7_r53_final_no_body_leak_no_question_text_no_touch_r52_reintake_bodyfree",
) -> dict[str, Any]:
    """Build R53-21 final no-leak/no-question/no-touch validation.

    The output is the R52 re-intake handoff material.  It does not call R52,
    start P8, start P6, complete P7, mutate runtime, or claim release readiness.
    """

    if p8_question_design_material_candidate_handoff_bodyfree is not None and r20_p8_question_design_material_candidate_handoff_bodyfree is not None:
        raise ValueError("provide only one R53-20 P8 material handoff value")
    r20 = safe_mapping(
        p8_question_design_material_candidate_handoff_bodyfree
        if p8_question_design_material_candidate_handoff_bodyfree is not None
        else r20_p8_question_design_material_candidate_handoff_bodyfree
        if r20_p8_question_design_material_candidate_handoff_bodyfree is not None
        else build_p7_r53_p8_question_design_material_candidate_handoff_bodyfree()
    )
    assert_p7_r53_p8_question_design_material_candidate_handoff_bodyfree_contract(r20)

    r51_r19 = safe_mapping(r20.get("r51_r19_p8_question_design_material_candidate_handoff_bodyfree"))
    assert_p7_r51_p8_question_design_material_candidate_handoff_bodyfree_contract(
        r51_r19,
        allowed_true_false_key_refs=_r53_r20_r51_allowed_true_refs_from_p8(r51_r19),
    )
    r51_r20 = build_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree(
        r19_p8_question_design_material_candidate_handoff_bodyfree=r51_r19,
        material_id="p7_r53_adopted_r51_r20_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree",
    )
    assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(
        r51_r20,
        allowed_true_false_key_refs=_r53_r20_r51_allowed_true_refs_from_p8(r51_r20),
    )

    materials: list[dict[str, Any]] = [r20, r51_r20]
    if additional_body_free_materials is not None:
        if isinstance(additional_body_free_materials, Mapping):
            raw_values = [additional_body_free_materials]
        elif isinstance(additional_body_free_materials, Sequence) and not isinstance(additional_body_free_materials, (str, bytes, bytearray)):
            raw_values = list(additional_body_free_materials)
        else:
            raise ValueError("R53 R21 additional body-free materials must be mappings")
        for item in raw_values:
            mapped = safe_mapping(item)
            if not mapped:
                raise ValueError("R53 R21 additional body-free material must be a mapping")
            materials.append(mapped)

    forbidden_key_refs = tuple(dict.fromkeys((*P7_R51_NO_BODY_LEAK_FORBIDDEN_KEY_REFS, "question_text", "draft_question_text", "local_absolute_path", "packet_content_hash")))
    forbidden_true_refs = tuple(dict.fromkeys((*P7_R51_NO_BODY_LEAK_FORBIDDEN_TRUE_FLAG_REFS, *P7_R51_NO_TOUCH_MUTATION_TRUE_FLAG_REFS)))
    key_paths: list[str] = []
    true_flag_paths: list[str] = []
    for index, item in enumerate(materials):
        key_paths.extend(_r53_find_forbidden_key_paths(item, forbidden_keys=forbidden_key_refs, path=f"r53_bodyfree_materials[{index}]"))
        true_flag_paths.extend(_r53_find_forbidden_true_flag_paths(item, forbidden_flags=forbidden_true_refs, path=f"r53_bodyfree_materials[{index}]"))
    touched_refs, forbidden_touched, not_allowed_touched = _r53_no_touch_scan(actual_touched_file_refs)
    no_body_keys = not key_paths
    no_forbidden_true_flags = not true_flag_paths
    no_body_leak_scan_passed = no_body_keys and no_forbidden_true_flags
    no_touch_boundary_validated = bool(touched_refs and not forbidden_touched and not not_allowed_touched)
    r20_ready = r20.get("p8_question_design_material_candidate_status") == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    r51_r20_ready = r51_r20.get("boundary_validation_status") == "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED"
    ready = bool(r20_ready and r51_r20_ready and no_body_leak_scan_passed and no_touch_boundary_validated)
    status = (
        "R53_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATED_AND_R52_REINTAKE_HANDOFF_READY"
        if ready
        else "BLOCKED_BY_R53_BODY_LEAK_QUESTION_TEXT_NO_TOUCH_OR_R52_REINTAKE_BOUNDARY"
    )
    reason_refs = ["r53_21_no_body_leak_no_question_text_no_touch_validated_for_r52_reintake"] if ready else dedupe_identifiers(
        [
            *([] if r20_ready else ["r20_p8_material_candidate_not_ready"]),
            *([] if r51_r20_ready else ["adopted_r51_r20_no_body_leak_validation_not_ready"]),
            *([] if no_body_leak_scan_passed else ["bodyfree_material_leak_or_question_text_detected"]),
            *([] if no_touch_boundary_validated else ["actual_touched_refs_or_no_touch_boundary_not_validated"]),
        ],
        limit=40,
        max_length=180,
    )
    reintake = _r53_r21_reintake_handoff_bodyfree(r20=r20, ready=ready)
    material = {
        **_false_flags(),
        "schema_version": P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_R52_REINTAKE_SCHEMA_VERSION,
        "phase": P7_PHASE,
        "step": P7_R53_STEP,
        "scope": P7_R53_SCOPE,
        "policy_kind": P7_R53_POLICY_KIND,
        "policy_section": "R53-21_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff",
        "current_phase": "P7",
        "material_id": clean_identifier(material_id, default="p7_r53_final_no_body_leak_no_question_text_no_touch_r52_reintake_bodyfree", max_length=180),
        "review_session_id": clean_identifier(r20.get("review_session_id"), default=P7_R53_DEFAULT_REVIEW_SESSION_ID, max_length=140),
        "source_mode": P7_SOURCE_MODE,
        "git_connection_required": False,
        "git_checked": False,
        "r20_p8_question_design_material_candidate_handoff_schema_version": P7_R53_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION,
        "r20_p8_question_design_material_candidate_handoff_material_ref": clean_identifier(r20.get("material_id"), default="p7_r53_p8_question_design_material_candidate_handoff_bodyfree", max_length=180),
        "r20_p8_question_design_material_candidate_status": clean_identifier(r20.get("p8_question_design_material_candidate_status"), default="P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_BLOCKED_BY_P5_OR_BODYFREE_REQUIREMENTS", max_length=160),
        "r20_ready_for_final_validation": r20_ready,
        "r51_r20_no_body_leak_no_question_text_no_touch_schema_version": P7_R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATION_SCHEMA_VERSION,
        "r51_r20_no_body_leak_no_question_text_no_touch_material_ref": clean_identifier(r51_r20.get("material_id"), default="p7_r53_adopted_r51_r20_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree", max_length=180),
        "r51_r20_no_body_leak_no_question_text_no_touch_bodyfree": r51_r20,
        "r51_r20_boundary_validation_status": clean_identifier(r51_r20.get("boundary_validation_status"), default="BLOCKED_BY_R51_BODY_LEAK_OR_NO_TOUCH_BOUNDARY_VIOLATION", max_length=160),
        "r51_r20_next_required_step": clean_identifier(r51_r20.get("next_required_step"), default=P7_R51_R20_BLOCKED_NEXT_REQUIRED_STEP_REF, max_length=180),
        "final_boundary_validation_status": status,
        "final_boundary_validation_reason_refs": reason_refs,
        "missing_requirement_refs": [] if ready else reason_refs,
        "r52_reintake_handoff_schema_version": P7_R53_R52_REINTAKE_HANDOFF_SCHEMA_VERSION,
        "r52_reintake_handoff_material_ref": reintake["material_id"],
        "r52_reintake_handoff_bodyfree": reintake,
        "r51_bodyfree_handoff_components": list(reintake["r51_bodyfree_handoff_components"]),
        "current_received_snapshot_refs": dict(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "current_received_snapshot_ref_count": len(P7_R53_CURRENT_RECEIVED_SNAPSHOT_REFS),
        "body_free_material_refs_scanned": _r53_bodyfree_material_refs(materials),
        "body_free_material_count_scanned": len(materials),
        "forbidden_body_key_refs": list(forbidden_key_refs),
        "forbidden_true_flag_refs": list(forbidden_true_refs),
        "detected_forbidden_body_key_paths": dedupe_identifiers(key_paths, limit=120, max_length=260),
        "detected_forbidden_true_flag_paths": dedupe_identifiers(true_flag_paths, limit=120, max_length=260),
        "body_payload_key_scan_passed": no_body_keys,
        "question_text_key_scan_passed": not any("question_text" in path for path in key_paths),
        "draft_question_text_key_scan_passed": not any("draft_question_text" in path for path in key_paths),
        "reviewer_free_text_key_scan_passed": not any("reviewer_free_text" in path for path in key_paths),
        "local_path_key_scan_passed": not any("local_path" in path or "local_absolute_path" in path for path in key_paths),
        "body_hash_key_scan_passed": not any("body_hash" in path or "content_hash" in path or "packet_content_hash" in path for path in key_paths),
        "terminal_output_key_scan_passed": not any("terminal_output" in path or "stdout" in path or "stderr" in path or "traceback" in path for path in key_paths),
        "forbidden_true_flag_scan_passed": no_forbidden_true_flags,
        "body_free_no_leak_scan_passed": no_body_leak_scan_passed,
        "actual_touched_file_refs": touched_refs,
        "allowed_actual_touched_file_refs": list(P7_R53_R21_ALLOWED_ACTUAL_TOUCHED_FILE_REFS),
        "expected_touched_file_refs": list(P7_R53_R21_EXPECTED_TOUCHED_FILE_REFS),
        "explicit_no_touch_file_refs": list(P7_R53_R21_EXPLICIT_NO_TOUCH_FILE_REFS),
        "explicit_no_touch_area_refs": list(P7_R53_R21_EXPLICIT_NO_TOUCH_AREA_REFS),
        "forbidden_actual_touched_file_refs": forbidden_touched,
        "not_allowed_actual_touched_file_refs": not_allowed_touched,
        "actual_touched_file_refs_checked_here": True,
        "actual_touched_file_refs_verified_here": no_touch_boundary_validated,
        "actual_touched_file_refs_materialized_here": False,
        "forbidden_actual_touched_refs_detected_here": bool(forbidden_touched or not_allowed_touched),
        "allowed_refs_do_not_include_no_touch_refs": not (set(P7_R53_R21_ALLOWED_ACTUAL_TOUCHED_FILE_REFS) & set(P7_R53_R21_EXPLICIT_NO_TOUCH_FILE_REFS)),
        "expected_touched_refs_are_allowed": set(P7_R53_R21_EXPECTED_TOUCHED_FILE_REFS).issubset(set(P7_R53_R21_ALLOWED_ACTUAL_TOUCHED_FILE_REFS)),
        "no_touch_boundary_validated": no_touch_boundary_validated,
        "rn_no_touch_preserved": not any(ref.startswith("Cocolon/screens/") or ref.startswith("Cocolon/tests/") for ref in touched_refs),
        "api_no_touch_preserved": "services/ai_inference/api_emotion_submit.py" not in touched_refs and "services/ai_inference/emotion_submit_service.py" not in touched_refs,
        "db_no_touch_preserved": not any("migration" in ref or ref.endswith(".sql") for ref in touched_refs),
        "runtime_no_touch_preserved": not any(ref in P7_R53_R21_EXPLICIT_NO_TOUCH_FILE_REFS for ref in touched_refs),
        "public_response_no_touch_preserved": True,
        "p8_question_implementation_not_started": True,
        "question_text_absent": no_body_leak_scan_passed,
        "draft_question_text_absent": no_body_leak_scan_passed,
        "question_body_absent": no_body_leak_scan_passed,
        "raw_input_absent": no_body_leak_scan_passed,
        "returned_surface_absent": no_body_leak_scan_passed,
        "reviewer_free_text_absent": no_body_leak_scan_passed,
        "local_path_absent": no_body_leak_scan_passed,
        "body_hash_absent": no_body_leak_scan_passed,
        "body_full_packet_generated_here": False,
        "body_full_packets_created_local_only": False,
        "body_full_writer_created_here": False,
        "local_reviewer_payload_materialized_here": False,
        "actual_reviewer_notes_materialized_here": False,
        "actual_disposal_run_here": bool(r20.get("actual_disposal_run_here")) if ready else False,
        "actual_disposal_receipt_materialized_here": bool(r20.get("actual_disposal_receipt_materialized_here")) if ready else False,
        "post_review_summary_materialized_here": bool(r20.get("post_review_summary_materialized_here")) if ready else False,
        "actual_human_review_run_here": bool(r20.get("actual_human_review_run_here")) if ready else False,
        "actual_manual_review_run_here": bool(r20.get("actual_manual_review_run_here")) if ready else False,
        "actual_rating_rows_materialized_here": bool(r20.get("actual_rating_rows_materialized_here")) if ready else False,
        "actual_blocker_rows_materialized_here": bool(r20.get("actual_blocker_rows_materialized_here")) if ready else False,
        "actual_execution_blocker_rows_materialized_here": bool(r20.get("actual_execution_blocker_rows_materialized_here")) if ready else False,
        "actual_question_need_observation_rows_materialized_here": bool(r20.get("actual_question_need_observation_rows_materialized_here")) if ready else False,
        "actual_question_need_observation_summary_materialized_here": bool(r20.get("actual_question_need_observation_summary_materialized_here")) if ready else False,
        "p5_human_blind_qa_confirmed_candidate": bool(r20.get("p5_human_blind_qa_confirmed_candidate")) if ready else False,
        "p5_repair_return_candidate": False,
        "p5_review_inconclusive": False,
        "p6_limited_human_readfeel_candidate": bool(r20.get("p6_limited_human_readfeel_candidate")) if ready else False,
        "p6_limited_human_readfeel_start_allowed_candidate": bool(r20.get("p6_limited_human_readfeel_start_allowed_candidate")) if ready else False,
        "p6_limited_human_readfeel_start_allowed": False,
        "p8_question_design_material_candidate": bool(r20.get("p8_question_design_material_candidate")) if ready else False,
        "p8_start_allowed": False,
        "p7_complete": False,
        "release_allowed": False,
        "hold004_close_allowed": False,
        "api_db_rn_response_key_changed_here": False,
        "question_trigger_logic_implemented_here": False,
        "p8_question_implementation_spec_finalized_here": False,
        "rn_contract_changed_here": False,
        "rn_production_files_touched_here": False,
        "rn_contract_test_files_touched_here": False,
        "rn_visible_contract_changed_here": False,
        "api_route_changed_here": False,
        "db_schema_changed_here": False,
        "db_migration_changed_here": False,
        "emlis_reply_runtime_changed_here": False,
        "user_label_connection_runtime_changed_here": False,
        "runtime_changed_here": False,
        "release_material_changed_here": False,
        "public_response_top_level_key_added_here": False,
        "r53_0_scope_current_received_snapshot_refrozen": True,
        "r53_1_r51_r52_helper_source_delta_frozen": True,
        "r53_2_r49_timeout_validation_evidence_preflight_built": True,
        "r53_3_r51_r0_r1_current_snapshot_override_built": True,
        "r53_4_explicit_allow_local_root_purge_plan_preflight_built": True,
        "r53_5_actual_review_session_envelope_built": True,
        "r53_6_24_case_manifest_freeze_built": True,
        "r53_7_local_only_body_full_packet_generation_request_built": True,
        "r53_8_packet_completeness_export_denylist_scan_built": True,
        "r53_9_reviewer_instruction_rating_form_freeze_built": bool(r20.get("r53_9_reviewer_instruction_rating_form_freeze_built")) if ready else False,
        "r53_10_actual_human_review_result_capture_built": bool(r20.get("r53_10_actual_human_review_result_capture_built")) if ready else False,
        "r53_11_rating_row_normalization_built": bool(r20.get("r53_11_rating_row_normalization_built")) if ready else False,
        "r53_12_readfeel_blocker_execution_blocker_ingestion_built": bool(r20.get("r53_12_readfeel_blocker_execution_blocker_ingestion_built")) if ready else False,
        "r53_13_question_need_observation_row_normalization_built": bool(r20.get("r53_13_question_need_observation_row_normalization_built")) if ready else False,
        "r53_14_rating_question_consistency_guard_built": bool(r20.get("r53_14_rating_question_consistency_guard_built")) if ready else False,
        "r53_15_pause_abort_expiration_protocol_built": bool(r20.get("r53_15_pause_abort_expiration_protocol_built")) if ready else False,
        "r53_16_purge_disposal_receipt_built": bool(r20.get("r53_16_purge_disposal_receipt_built")) if ready else False,
        "r53_17_body_free_post_review_summary_built": bool(r20.get("r53_17_body_free_post_review_summary_built")) if ready else False,
        "r53_18_p5_decision_candidate_separation_built": bool(r20.get("r53_18_p5_decision_candidate_separation_built")) if ready else False,
        "r53_19_p6_limited_human_readfeel_candidate_handoff_built": bool(r20.get("r53_19_p6_limited_human_readfeel_candidate_handoff_built")) if ready else False,
        "r53_20_p8_question_design_material_candidate_handoff_built": bool(r20.get("r53_20_p8_question_design_material_candidate_handoff_built")) if ready else False,
        "r53_21_final_no_body_leak_no_question_text_no_touch_validation_built": ready,
        "implemented_steps": list(P7_R53_R21_IMPLEMENTED_STEPS if ready else P7_R53_R20_IMPLEMENTED_STEPS if r20_ready else P7_R53_R19_IMPLEMENTED_STEPS),
        "not_yet_implemented_steps": list(P7_R53_R21_NOT_YET_IMPLEMENTED_STEPS if ready else P7_R53_R21_NOT_YET_IMPLEMENTED_STEPS if r20_ready else P7_R53_R20_NOT_YET_IMPLEMENTED_STEPS),
        "first_next_work_ref": P7_R53_FIRST_NEXT_WORK_REF,
        "next_required_step": P7_R53_R21_NEXT_REQUIRED_STEP_REF if ready else P7_R53_R21_BLOCKED_NEXT_REQUIRED_STEP_REF,
        "public_contract": public_contract_flags(),
        "r53_public_no_touch_contract": _public_no_touch_contract(),
        "body_free_markers": _body_free_markers(),
        "body_free": True,
    }
    assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree_contract(material)
    return material


def assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree_contract(material: Mapping[str, Any]) -> bool:
    data = safe_mapping(material)
    _assert_required_fields(
        data,
        required=P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_R52_REINTAKE_REQUIRED_FIELD_REFS,
        source="p7_r53_r21_final_no_body_leak_no_question_text_no_touch_r52_reintake_bodyfree",
    )
    ready = data.get("final_boundary_validation_status") == "R53_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_VALIDATED_AND_R52_REINTAKE_HANDOFF_READY"
    allowed = _r53_allowed_true_refs_from(data, P7_R53_R21_ALLOWED_TRUE_FALSE_KEY_REFS)
    _assert_body_free_common_allowing(
        data,
        schema_version=P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_R52_REINTAKE_SCHEMA_VERSION,
        source="p7_r53_r21_final_no_body_leak_no_question_text_no_touch_r52_reintake_bodyfree",
        allowed_true_false_key_refs=allowed,
    )
    if data.get("policy_section") != "R53-21_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff":
        raise ValueError("R53 R21 policy section changed")
    if data.get("final_boundary_validation_status") not in P7_R53_FINAL_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_STATUS_REFS:
        raise ValueError("R53 R21 final boundary validation status changed")
    r20 = safe_mapping(data.get("r52_reintake_handoff_bodyfree"))
    if r20.get("schema_version") != P7_R53_R52_REINTAKE_HANDOFF_SCHEMA_VERSION:
        raise ValueError("R53 R21 re-intake handoff schema changed")
    if r20.get("p8_start_allowed") is not False or r20.get("p7_complete") is not False or r20.get("release_allowed") is not False:
        raise ValueError("R53 R21 re-intake handoff must not auto-allow P8/P7/release")
    r51_r20 = safe_mapping(data.get("r51_r20_no_body_leak_no_question_text_no_touch_bodyfree"))
    assert_p7_r51_no_body_leak_no_question_text_no_touch_boundary_validation_bodyfree_contract(
        r51_r20,
        allowed_true_false_key_refs=_r53_r20_r51_allowed_true_refs_from_p8(r51_r20),
    )
    for true_key in (
        "body_payload_key_scan_passed",
        "question_text_key_scan_passed",
        "draft_question_text_key_scan_passed",
        "reviewer_free_text_key_scan_passed",
        "local_path_key_scan_passed",
        "body_hash_key_scan_passed",
        "terminal_output_key_scan_passed",
        "forbidden_true_flag_scan_passed",
        "body_free_no_leak_scan_passed",
        "actual_touched_file_refs_checked_here",
        "allowed_refs_do_not_include_no_touch_refs",
        "expected_touched_refs_are_allowed",
        "rn_no_touch_preserved",
        "api_no_touch_preserved",
        "db_no_touch_preserved",
        "runtime_no_touch_preserved",
        "public_response_no_touch_preserved",
        "p8_question_implementation_not_started",
        "question_text_absent",
        "draft_question_text_absent",
        "question_body_absent",
        "raw_input_absent",
        "returned_surface_absent",
        "reviewer_free_text_absent",
        "local_path_absent",
        "body_hash_absent",
    ):
        if ready and data.get(true_key) is not True:
            raise ValueError(f"R53 R21 ready validation must keep {true_key}=True")
    for false_key in (
        "actual_touched_file_refs_materialized_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "actual_reviewer_notes_materialized_here",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "p7_complete",
        "release_allowed",
        "hold004_close_allowed",
        "api_db_rn_response_key_changed_here",
        "question_trigger_logic_implemented_here",
        "p8_question_implementation_spec_finalized_here",
        "rn_contract_changed_here",
        "rn_production_files_touched_here",
        "rn_contract_test_files_touched_here",
        "rn_visible_contract_changed_here",
        "api_route_changed_here",
        "db_schema_changed_here",
        "db_migration_changed_here",
        "emlis_reply_runtime_changed_here",
        "user_label_connection_runtime_changed_here",
        "runtime_changed_here",
        "release_material_changed_here",
        "public_response_top_level_key_added_here",
    ):
        if data.get(false_key) is not False:
            raise ValueError(f"R53 R21 must keep {false_key}=False")
    actual_touched = tuple(dedupe_identifiers(data.get("actual_touched_file_refs") or [], limit=240, max_length=260))
    allowed_touched = set(P7_R53_R21_ALLOWED_ACTUAL_TOUCHED_FILE_REFS)
    no_touch = set(P7_R53_R21_EXPLICIT_NO_TOUCH_FILE_REFS)
    if not actual_touched:
        raise ValueError("R53 R21 actual touched refs must be present")
    if ready:
        if data.get("r20_p8_question_design_material_candidate_status") != "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY":
            raise ValueError("R53 R21 ready validation requires R53 R20 ready material")
        if data.get("r51_r20_boundary_validation_status") != "R51_NO_BODY_LEAK_NO_QUESTION_TEXT_NO_TOUCH_BOUNDARY_VALIDATED":
            raise ValueError("R53 R21 ready validation requires adopted R51 R20 ready validation")
        if set(actual_touched) & no_touch:
            raise ValueError("R53 R21 actual touched refs include explicit no-touch refs")
        if sorted(set(actual_touched) - allowed_touched):
            raise ValueError("R53 R21 actual touched refs are outside allowed R53-21 patch")
        if data.get("detected_forbidden_body_key_paths") or data.get("detected_forbidden_true_flag_paths"):
            raise ValueError("R53 R21 ready validation must have no leak paths")
        if data.get("forbidden_actual_touched_file_refs") or data.get("not_allowed_actual_touched_file_refs"):
            raise ValueError("R53 R21 ready validation must have no touched-ref violations")
        if data.get("r53_21_final_no_body_leak_no_question_text_no_touch_validation_built") is not True:
            raise ValueError("R53 R21 ready validation must mark R21 built")
        if data.get("r52_reintake_handoff_bodyfree", {}).get("r51_actual_review_evidence_complete") is not True:
            raise ValueError("R53 R21 ready validation must hand off complete R51 actual evidence")
        if tuple(data.get("implemented_steps") or ()) != P7_R53_R21_IMPLEMENTED_STEPS:
            raise ValueError("R53 R21 implemented steps changed")
        if tuple(data.get("not_yet_implemented_steps") or ()) != P7_R53_R21_NOT_YET_IMPLEMENTED_STEPS:
            raise ValueError("R53 R21 not-yet steps changed")
        if data.get("next_required_step") != P7_R53_R21_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R21 ready next step changed")
    else:
        if data.get("r53_21_final_no_body_leak_no_question_text_no_touch_validation_built") is not False:
            raise ValueError("R53 R21 blocked validation must not mark R21 built")
        if not data.get("missing_requirement_refs"):
            raise ValueError("R53 R21 blocked validation must explain missing requirements")
        if data.get("next_required_step") != P7_R53_R21_BLOCKED_NEXT_REQUIRED_STEP_REF:
            raise ValueError("R53 R21 blocked next step changed")
    assert_p7_no_body_payload_or_contract_mutation(data, source="p7_r53_r21_final_no_body_leak_no_question_text_no_touch_r52_reintake_bodyfree")
    return True



# Compatibility aliases matching the shorter R53-20/R53-21 design wording.
build_p7_r53_p8_question_design_material_candidate_handoff = build_p7_r53_p8_question_design_material_candidate_handoff_bodyfree
assert_p7_r53_p8_question_design_material_candidate_handoff_contract = assert_p7_r53_p8_question_design_material_candidate_handoff_bodyfree_contract
build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff = build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree
assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_contract = assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree_contract
build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_re_intake_handoff = build_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree
assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_re_intake_handoff_contract = assert_p7_r53_final_no_body_leak_no_question_text_no_touch_validation_and_r52_reintake_handoff_bodyfree_contract

# Compatibility aliases matching the shorter R53-18/R53-19 design wording.
build_p7_r53_p5_decision_candidate_separation = build_p7_r53_p5_decision_candidate_separation_bodyfree
assert_p7_r53_p5_decision_candidate_separation_contract = assert_p7_r53_p5_decision_candidate_separation_bodyfree_contract
build_p7_r53_p6_limited_human_readfeel_candidate_handoff = build_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree
assert_p7_r53_p6_limited_human_readfeel_candidate_handoff_contract = assert_p7_r53_p6_limited_human_readfeel_candidate_handoff_bodyfree_contract


# Compatibility aliases matching the shorter R53-16/R53-17 design wording.
build_p7_r53_purge_disposal_receipt = build_p7_r53_purge_disposal_receipt_bodyfree
assert_p7_r53_purge_disposal_receipt_contract = assert_p7_r53_purge_disposal_receipt_bodyfree_contract
build_p7_r53_body_free_post_review_summary = build_p7_r53_body_free_post_review_summary_bodyfree
assert_p7_r53_body_free_post_review_summary_contract = assert_p7_r53_body_free_post_review_summary_bodyfree_contract


# Compatibility aliases matching the shorter R53-14/R53-15 design wording.
build_p7_r53_rating_question_consistency_guard = build_p7_r53_rating_question_consistency_guard_bodyfree
assert_p7_r53_rating_question_consistency_guard_contract = assert_p7_r53_rating_question_consistency_guard_bodyfree_contract
build_p7_r53_rating_question_observation_consistency_guard_bodyfree = build_p7_r53_rating_question_consistency_guard_bodyfree
assert_p7_r53_rating_question_observation_consistency_guard_bodyfree_contract = assert_p7_r53_rating_question_consistency_guard_bodyfree_contract
build_p7_r53_pause_abort_expiration_protocol = build_p7_r53_pause_abort_expiration_protocol_bodyfree
assert_p7_r53_pause_abort_expiration_protocol_contract = assert_p7_r53_pause_abort_expiration_protocol_bodyfree_contract


# Compatibility aliases matching the shorter R53-12/R53-13 design wording.
build_p7_r53_readfeel_blocker_execution_blocker_ingestion = build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree
assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_contract = assert_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract
build_p7_r53_question_need_observation_row_normalization = build_p7_r53_question_need_observation_row_normalization_bodyfree
assert_p7_r53_question_need_observation_row_normalization_contract = assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract


# Compatibility aliases matching the shorter R53-10/R53-11 design wording.
build_p7_r53_actual_human_review_result_capture = build_p7_r53_actual_human_review_result_capture_bodyfree
assert_p7_r53_actual_human_review_result_capture_contract = assert_p7_r53_actual_human_review_result_capture_bodyfree_contract
build_p7_r53_rating_row_normalization = build_p7_r53_rating_row_normalization_bodyfree
assert_p7_r53_rating_row_normalization_contract = assert_p7_r53_rating_row_normalization_bodyfree_contract

# Compatibility aliases matching the shorter R53-8/R53-9 design wording.
build_p7_r53_packet_completeness_export_denylist_scan = build_p7_r53_packet_completeness_export_denylist_scan_bodyfree
assert_p7_r53_packet_completeness_export_denylist_scan_contract = assert_p7_r53_packet_completeness_export_denylist_scan_bodyfree_contract
build_p7_r53_reviewer_instruction_rating_form_freeze = build_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree
assert_p7_r53_reviewer_instruction_rating_form_freeze_contract = assert_p7_r53_reviewer_instruction_rating_form_freeze_bodyfree_contract


# Compatibility aliases matching the shorter R53-6/R53-7 design wording.
build_p7_r53_24_case_manifest_freeze = build_p7_r53_24_case_manifest_freeze_bodyfree
assert_p7_r53_24_case_manifest_freeze_contract = assert_p7_r53_24_case_manifest_freeze_bodyfree_contract
build_p7_r53_local_only_body_full_packet_generation_request = build_p7_r53_local_only_body_full_packet_generation_request_bodyfree
assert_p7_r53_local_only_body_full_packet_generation_request_contract = assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract
build_p7_r53_local_only_body_full_packet_generation_request_optional_writer_bodyfree = build_p7_r53_local_only_body_full_packet_generation_request_bodyfree
assert_p7_r53_local_only_body_full_packet_generation_request_optional_writer_bodyfree_contract = assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract
build_p7_r53_local_only_body_full_packet_generation_request_optional_writer = build_p7_r53_local_only_body_full_packet_generation_request_bodyfree
assert_p7_r53_local_only_body_full_packet_generation_request_optional_writer_contract = assert_p7_r53_local_only_body_full_packet_generation_request_bodyfree_contract


# Compatibility aliases matching the shorter R53-4/R53-5 design wording.
build_p7_r53_explicit_allow_local_root_purge_plan_preflight = build_p7_r53_local_root_explicit_allow_purge_plan_preflight
assert_p7_r53_explicit_allow_local_root_purge_plan_preflight_contract = assert_p7_r53_local_root_explicit_allow_purge_plan_preflight_contract
build_p7_r53_actual_review_session_envelope = build_p7_r53_actual_review_session_envelope_bodyfree
assert_p7_r53_actual_review_session_envelope_contract = assert_p7_r53_actual_review_session_envelope_bodyfree_contract
